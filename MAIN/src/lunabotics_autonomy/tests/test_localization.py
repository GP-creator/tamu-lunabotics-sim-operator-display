import math
import unittest
from autonomy.localization import WheelTagEstimator
from autonomy.types import Pose


def estimator():
    return WheelTagEstimator(.10,.50,1000,1.0,7.9,4.4)


class LocalizationTests(unittest.TestCase):
    def test_requires_calibration_and_valid_tag_before_map_pose(self):
        with self.assertRaises(ValueError):
            WheelTagEstimator(0,.5,1000,1,7.9,4.4)
        e = estimator()
        e.accept_counts(0,0,1)
        self.assertIsNone(e.pose)
        self.assertFalse(e.accept_tag(Pose(10,2,0),.01,.01,1,1))
        self.assertTrue(e.accept_tag(Pose(1,2,0),.01,.01,1,1))
        self.assertAlmostEqual(e.pose.x,1)

    def test_straight_turn_and_map_correction(self):
        e = estimator()
        e.accept_counts(0,0,1)
        e.accept_tag(Pose(1,2,0),.01,.01,1,1)
        self.assertTrue(e.accept_counts(100,100,1.1))
        self.assertAlmostEqual(e.pose.x,1+2*math.pi*.1*.1)
        self.assertAlmostEqual(e.pose.y,2)
        self.assertTrue(e.accept_counts(100,200,1.2))
        self.assertGreater(e.pose.y,2)
        self.assertGreater(e.pose.yaw,0)
        self.assertTrue(e.accept_tag(Pose(e.pose.x+.05,e.pose.y, e.pose.yaw),
                                     .01,.01,1.2,1.2))
        self.assertAlmostEqual(e.pose.x,e.alignment.x+
            math.cos(e.alignment.yaw)*e.odom.x-
            math.sin(e.alignment.yaw)*e.odom.y)
        self.assertAlmostEqual(e.distance_since_tag,0)

    def test_tag_outlier_and_bad_covariance_do_not_shift_tf(self):
        e = estimator()
        e.accept_counts(0,0,1)
        e.accept_tag(Pose(1,2,0),.01,.01,1,1)
        prior = e.alignment
        self.assertFalse(e.accept_tag(Pose(3,2,0),.01,.01,1.1,1.1))
        self.assertFalse(e.accept_tag(Pose(1,2,0),0,.01,1.1,1.1))
        self.assertFalse(e.accept_tag(Pose(1,2,0),.01,.01,2,1.1))
        self.assertEqual(e.alignment,prior)

    def test_encoder_reset_latches_fault_and_stops_global_pose(self):
        e = estimator()
        e.accept_counts(1000,1000,1)
        e.accept_tag(Pose(1,2,0),.01,.01,1,1)
        self.assertFalse(e.accept_counts(0,0,1.1))
        self.assertEqual(e.fault,'encoder_jump')
        self.assertIsNone(e.pose)
        self.assertFalse(e.accept_counts(1001,1001,1.2))

    def test_signed_counter_wrap_does_not_invent_large_motion(self):
        e = estimator()
        e.accept_counts(2**31-5,2**31-5,1)
        self.assertTrue(e.accept_counts(-2**31+5,-2**31+5,1.1))
        self.assertAlmostEqual(e.odom.x,10*e.meters_per_tick)

    def test_stale_encoder_gap_latches_and_uncertainty_grows(self):
        e = estimator()
        e.accept_counts(0,0,1)
        e.accept_tag(Pose(1,2,0),.01,.01,1,1)
        before = e.uncertainty
        e.accept_counts(100,100,1.1)
        self.assertGreater(e.uncertainty[0],before[0])
        self.assertFalse(e.accept_counts(101,101,2))
        self.assertEqual(e.fault,'encoder_timestamp_gap')


if __name__ == '__main__':
    unittest.main()
