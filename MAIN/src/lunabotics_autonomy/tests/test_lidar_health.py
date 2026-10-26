import math
import struct
import unittest
from types import SimpleNamespace as O
from autonomy.lidar_health import FrameGate, normalized_xyzw, finite_cloud


class LidarHealthTests(unittest.TestCase):
    def test_zero_stale_future_and_duplicate_frames_do_not_become_fresh(self):
        gate = FrameGate()
        for stamp in (0., 8., 10.1, float('nan'), float('inf')):
            self.assertFalse(gate.accept(stamp, 10.))
        self.assertTrue(gate.accept(9.9, 10.))
        self.assertFalse(gate.accept(9.9, 10.))
        self.assertFalse(gate.accept(9.8, 10.))
        self.assertTrue(gate.accept(10., 10.))

    def test_quaternion_contract_keeps_xyzw_and_supports_explicit_wxyz(self):
        self.assertEqual(normalized_xyzw((0,0,0,.998)), (0,0,0,1))
        self.assertEqual(normalized_xyzw((.998,0,0,0), 'wxyz'), (0,0,0,1))
        for q in ((0,0,0,0), (math.nan,0,0,1), (100,0,0,1)):
            with self.assertRaises(ValueError): normalized_xyzw(q)
        with self.assertRaises(ValueError): normalized_xyzw((0,0,0,1), 'guess')

    def test_readiness_requires_a_real_frame_and_expires(self):
        gate = FrameGate()
        self.assertFalse(gate.fresh(.1))
        self.assertTrue(gate.accept(10., 10.))
        self.assertTrue(gate.fresh(10.2))
        self.assertFalse(gate.fresh(10.6))
        self.assertFalse(gate.fresh(9.9))
        self.assertFalse(gate.fresh(math.nan))

    def test_clock_reset_stops_until_a_new_frame_arrives(self):
        gate = FrameGate()
        self.assertTrue(gate.accept(100., 100.))
        self.assertFalse(gate.accept(1., 1.))
        self.assertFalse(gate.fresh(1.))
        self.assertFalse(gate.accept(100., 1.1))
        self.assertTrue(gate.accept(1.2, 1.2))
        self.assertTrue(gate.fresh(1.3))

    def cloud(self, endian='<', bad=False):
        # Two rows, extra point bytes and row padding.
        data = bytearray(48)
        for row in range(2):
            struct.pack_into(endian+'fff', data, row*24, 1., 2., math.nan if bad else 3.)
        return O(width=1,height=2,point_step=16,row_step=24,data=bytes(data),
            is_bigendian=endian=='>',fields=[O(name=n,offset=i*4,datatype=7,count=1)
                                            for i,n in enumerate(('x','y','z'))])

    def test_pointcloud_padding_endian_nonfinite_and_layout(self):
        for endian in ('<','>'):
            self.assertTrue(finite_cloud(self.cloud(endian)))
            self.assertFalse(finite_cloud(self.cloud(endian, bad=True)))
        msg=self.cloud();msg.data=msg.data[:-1];self.assertFalse(finite_cloud(msg))
        msg=self.cloud();msg.fields[0].offset=15;self.assertFalse(finite_cloud(msg))
        msg=self.cloud();msg.fields.append(msg.fields[0]);self.assertFalse(finite_cloud(msg))
        msg=self.cloud();msg.fields[0].datatype=6;self.assertFalse(finite_cloud(msg))

