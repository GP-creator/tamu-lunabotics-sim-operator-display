import unittest
import numpy as np
from autonomy.depth import depth_points


class DepthTests(unittest.TestCase):
    def test_metric_depth_projection(self):
        values = np.full((4, 4), 1000, dtype='<u2')
        pts = depth_points(values.tobytes(), 4, 4, 8, '16UC1', False,
                           [100, 0, 2, 0, 100, 2, 0, 0, 1], sample=2)
        self.assertEqual(len(pts), 4)
        self.assertAlmostEqual(pts[0][2], 1.0)

    def test_bad_and_truncated_frames(self):
        with self.assertRaises(ValueError):
            depth_points(b'', 4, 4, 8, '16UC1', False,
                         [100, 0, 2, 0, 100, 2, 0, 0, 1])
        with self.assertRaises(ValueError):
            depth_points(b'01234567', 1, 1, 8, 'unknown', False,
                         [100, 0, 0, 0, 100, 0, 0, 0, 1])


if __name__ == '__main__':
    unittest.main()
