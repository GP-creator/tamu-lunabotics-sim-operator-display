import dataclasses
import math
import types
import unittest
import numpy as np
from autonomy.berm import BermEstimator
from autonomy.depth import depth_points
from autonomy.lidar import scan_beams
from autonomy.mission import Mission
from autonomy.occupancy import ObstacleMemory
from autonomy.sensor_validation import fresh_frame, rigid_components
from autonomy.sitl import SIM_CONFIG
from autonomy.types import Phase
from test_core import healthy


class SensorValidationTests(unittest.TestCase):
    def test_depth_invalid_intrinsics_and_ranges_rejected(self):
        k=[1.,0.,0.,0.,1.,0.,0.,0.,1.]
        for i in (0,2,4,5):
            invalid=k.copy();invalid[i]=float('nan')
            with self.assertRaises(ValueError):depth_points(b'\xe8\x03',1,1,2,'16UC1',False,invalid,sample=1)
        for extra in ({'near':float('nan')},{'far':float('inf')},{'sample':1.5},{'near':2.,'far':1.}):
            with self.assertRaises(ValueError):depth_points(b'\xe8\x03',1,1,2,'16UC1',False,k,**extra)

    def test_depth_big_endian_padding_and_float_encoding(self):
        k=[1.,0.,0.,0.,1.,0.,0.,0.,1.]
        for encoding,data,step in (('16UC1',b'\x03\xe8xx',4),('32FC1',np.array([1.],dtype='>f4').tobytes()+b'xxxx',8)):
            self.assertEqual(depth_points(data,1,1,step,encoding,True,k,sample=1),[(0.,0.,1.)])

    def test_lidar_nonfinite_filter_parameters_rejected(self):
        for args in ((-.1,.5,float('inf')),(-.1,float('nan'),8.)):
            with self.assertRaises(ValueError):scan_beams([], *args)
        with self.assertRaises(ValueError):scan_beams([],-.1,.5,8.,bins=3.5)

    def test_sensor_frames_require_new_finite_recent_timestamp(self):
        self.assertTrue(fresh_frame(10.,10.1,9.9))
        for stamp,now,previous in ((10.,10.,10.),(9.,10.,8.),(11.,10.,9.),(float('nan'),10.,9.),(float('inf'),10.,9.)):
            self.assertFalse(fresh_frame(stamp,now,previous))

    def test_nonfinite_transform_never_becomes_sensor_health(self):
        q=types.SimpleNamespace(x=0.,y=0.,z=0.,w=2.)
        t=types.SimpleNamespace(x=0.,y=0.,z=0.)
        self.assertEqual(rigid_components(q,t),(0.,0.,0.,1.))
        for value in (float('nan'),float('inf')):
            t.x=value
            with self.assertRaises(ValueError):rigid_components(q,t)
        t.x=0.;q.w=0.
        with self.assertRaises(ValueError):rigid_components(q,t)

    def test_berm_partial_edge_cells_do_not_overcount_area(self):
        b=BermEstimator((0.,0.,.15,.15),cell=.1,min_coverage=1.,vertical_error_m=0.)
        grid=[(x,y,0.) for x in (.05,.125) for y in (.05,.125)]
        b.observe(grid*2,empty=True);b.observe([(x,y,.1) for x,y,z in grid]*2)
        self.assertAlmostEqual(b.lower_volume_l(),2.25)

    def test_nonfinite_berm_and_observation_lifetimes_rejected(self):
        for kwargs in ({'vertical_error_m':float('nan')},{'cell':float('inf')},{'min_samples':1.5}):
            with self.assertRaises(ValueError):BermEstimator((0,0,1,1),**kwargs)
        for kwargs in ({'ttl':float('nan')},{'free_ttl':float('inf')}):
            with self.assertRaises(ValueError):ObstacleMemory(SIM_CONFIG,**kwargs)

    def test_invalid_berm_timestamp_cannot_complete_mission(self):
        for stamp in (float('nan'),float('inf'),11.,8.):
            m=Mission(SIM_CONFIG);m.start(healthy(9.));m.phase=Phase.VERIFY;m.phase_time=9.;m.cycles=2
            out=m.tick(healthy(10.,berm_volume_l=30.,berm_time=stamp))
            self.assertEqual(out.phase,Phase.VERIFY)
        m=Mission(SIM_CONFIG);m.start(healthy(9.));m.phase=Phase.VERIFY;m.phase_time=9.;m.cycles=2
        self.assertEqual(m.tick(healthy(10.,berm_volume_l=30.,berm_time=9.9)).phase,Phase.COMPLETE)

    def test_negative_pose_uncertainty_is_rejected(self):
        self.assertEqual(Mission(SIM_CONFIG).start(healthy(pose_sigma=-1.)).fault,'pose_uncertain')
