import unittest
from autonomy.berm import BermEstimator


class BermTests(unittest.TestCase):
    def test_survey_measurement_with_error_margin(self):
        b = BermEstimator((0,0,1,1), cell=.1, vertical_error_m=.01)
        baseline = [((i+.5)*.1,(j+.5)*.1,0.0) for i in range(10) for j in range(10)]
        b.observe(baseline*2, empty=True)
        self.assertTrue(b.baseline_ready)
        b.new_survey()
        b.observe([(x,y,.04) for x,y,_ in baseline]*2)
        self.assertAlmostEqual(b.lower_volume_l(),30.0)

    def test_no_empty_baseline_or_partial_survey(self):
        b = BermEstimator((0,0,1,1), cell=.1)
        b.observe([(0.05,0.05,.1)]*2, empty=True)
        self.assertFalse(b.baseline_ready)
        self.assertIsNone(b.lower_volume_l())

    def test_reject_invalid_bounds(self):
        with self.assertRaises(ValueError):
            BermEstimator((1,1,0,0))


if __name__ == '__main__':
    unittest.main()
