import math
import unittest
import numpy as np
from autonomy.fiducials import tag_object_corners, world_base_pose


def transform(x=0, y=0, z=0, yaw=0):
    c, s = math.cos(yaw), math.sin(yaw)
    m = np.eye(4)
    m[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    m[:3, 3] = [x, y, z]
    return m


class FiducialGeometry(unittest.TestCase):
    def test_world_base_inversion(self):
        base = transform(2, 1, 0, math.pi/2)
        camera = transform(.3, .1, .2)
        world_tag = transform(4, 2, .5, 0)
        camera_tag = np.linalg.inv(base @ camera) @ world_tag
        x, y, yaw = world_base_pose(world_tag, camera_tag, camera)
        self.assertAlmostEqual(x, 2)
        self.assertAlmostEqual(y, 1)
        self.assertAlmostEqual(yaw, math.pi/2)

    def test_reject_bad_transform(self):
        with self.assertRaises(ValueError):
            world_base_pose(np.zeros((4, 4)), np.eye(4), np.eye(4))

    def test_corner_order_and_size(self):
        np.testing.assert_allclose(tag_object_corners(0.2),
            [[-.1, .1, 0], [.1, .1, 0], [.1, -.1, 0], [-.1, -.1, 0]])


if __name__ == '__main__':
    unittest.main()
