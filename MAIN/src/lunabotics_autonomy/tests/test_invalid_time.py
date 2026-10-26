import dataclasses
import unittest
from autonomy.mission import Mission
from autonomy.sitl import SIM_CONFIG
from autonomy.types import Phase
from test_core import healthy


class InvalidTimeTests(unittest.TestCase):
    def test_nonfinite_configuration_rejected(self):
        for key in ('robot_radius','min_battery_v','cell','pose_timeout','clearance'):
            with self.subTest(key=key),self.assertRaises(ValueError):
                Mission(dataclasses.replace(SIM_CONFIG,**{key:float('nan')}))

    def test_nonfinite_health_timestamp_faults_without_motion(self):
        for key in ('now','pose_time','lidar_time','mass_time','estop_time','camera_time'):
            for bad in (float('nan'),float('inf')):
                with self.subTest(key=key,bad=bad):
                    out=Mission(SIM_CONFIG).start(healthy(**{key:bad}))
                    self.assertEqual(out.phase,Phase.FAULT)
                    self.assertEqual((out.linear,out.angular,out.tool),(0,0,'stop'))

    def test_clock_regression_latches(self):
        m=Mission(SIM_CONFIG);m.start(healthy(10))
        out=m.tick(healthy(9))
        self.assertEqual(out.fault,'clock_regression')
        self.assertEqual(m.tick(healthy(11)).phase,Phase.FAULT)
