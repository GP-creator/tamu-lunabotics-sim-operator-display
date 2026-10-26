import unittest
from autonomy.occupancy import ObstacleMemory, ray_cells
from autonomy.sitl import SIM_CONFIG


class OccupancyTests(unittest.TestCase):
    def test_ray_and_expiry(self):
        self.assertEqual(list(ray_cells((0,0),(3,1))),[(0,0),(1,0),(2,1),(3,1)])
        m = ObstacleMemory(SIM_CONFIG, ttl=2)
        m.update((1,1),[(2,1)],1)
        self.assertEqual(len(m.points(2)),1)
        self.assertEqual(m.points(4),[])

    def test_ray_clears_old_return(self):
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1,1),[(2,1)],1)
        m.update((1,1),[(3,1)],2)
        self.assertEqual(len(m.points(2)),2)  # one clear scan is not enough
        m.update((1,1),[(3,1)],2.1)
        m.update((1,1),[(3,1)],2.2)
        self.assertEqual(len(m.points(2.2)),1)
        self.assertAlmostEqual(m.points(2.2)[0][0],3.05)

    def test_one_frame_keeps_near_and_far_hits(self):
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1,1),[(2,1),(3,1)],1)
        self.assertEqual(len(m.points(1)),2)

    def test_only_observed_ray_cells_are_free(self):
        m = ObstacleMemory(SIM_CONFIG, ttl=2, free_ttl=3)
        m.update((1.0,1.0),[(2.0,1.0)],1)
        self.assertIn(m.cell((1.5,1.0)),m.known_free(1))
        self.assertNotIn(m.cell((2.0,1.0)),m.known_free(1))
        self.assertNotIn(m.cell((1.0,2.0)),m.known_free(1))
        self.assertFalse(m.known_free(5))


if __name__ == '__main__':
    unittest.main()
