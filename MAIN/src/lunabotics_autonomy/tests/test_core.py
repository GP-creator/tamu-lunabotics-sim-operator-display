import dataclasses
import math
import unittest

from autonomy.mission import Mission
from autonomy.navigation import plan, too_close, segment_clear
from autonomy.sitl import SIM_CONFIG, scenario
from autonomy.types import Config, Observation, Phase, Pose


def healthy(now=0.0, **changes):
    o = Observation(now=now, pose=Pose(1.1, 2.2, 0), pose_time=now,
                    camera_time=now, lidar_time=now, encoder_time=now,
                    mass_time=now, actuator_time=now, battery_time=now,
                    battery_v=25.0, mass_kg=0.0, pose_sigma=0.05,
                    actuator='raised', estop_time=now, baseline_ready=True)
    for k, v in changes.items():
        setattr(o, k, v)
    return o


class ConfigurationTests(unittest.TestCase):
    def test_requires_measured_capacity(self):
        with self.assertRaises(ValueError):
            Mission(Config())

    def test_rejects_overfilled_cycle(self):
        with self.assertRaises(ValueError):
            Mission(dataclasses.replace(SIM_CONFIG, per_cycle_l=16))


class NavigationTests(unittest.TestCase):
    def test_plan_reaches_goal(self):
        p = plan(Pose(1.1, 2.2, 0), SIM_CONFIG.dig, [], SIM_CONFIG)
        self.assertEqual(p[-1], SIM_CONFIG.dig)

    def test_obstacle_inflation(self):
        p = plan(Pose(1.1, 2.2, 0), SIM_CONFIG.dig,
                 [(3.9, 2.2)], SIM_CONFIG)
        self.assertTrue(p)
        self.assertTrue(all(math.hypot(x - 3.9, y - 2.2) >= 0.58 for x, y in p))

    def test_blocks_close_obstacle(self):
        self.assertTrue(too_close(Pose(1, 1, 0), [(1.3, 1)], SIM_CONFIG))

    def test_no_path_to_blocked_goal(self):
        self.assertEqual(plan(Pose(1.1, 2.2, 0), SIM_CONFIG.dig,
                              [SIM_CONFIG.dig], SIM_CONFIG), [])

    def test_unknown_space_and_shortcuts_are_blocked(self):
        start = Pose(1.1,2.2,0)
        self.assertEqual(plan(start,SIM_CONFIG.dig,[],SIM_CONFIG,set()),[])
        strip = {(i,j) for i in range(1,78) for j in range(11,34)}
        self.assertTrue(plan(start,SIM_CONFIG.dig,[],SIM_CONFIG,strip))
        gap = {cell for cell in strip if cell[0] != 40}
        self.assertEqual(plan(start,SIM_CONFIG.dig,[],SIM_CONFIG,gap),[])
        self.assertFalse(segment_clear((1.1,2.2),(6.9,2.2),[],SIM_CONFIG,gap))

    def test_centerline_only_is_not_enough_for_robot_footprint(self):
        narrow = {(i,j) for i in range(0,79) for j in range(20,25)}
        self.assertEqual(plan(Pose(1.1,2.2,0),SIM_CONFIG.dig,[],
                              SIM_CONFIG,narrow),[])

    def test_unknown_dig_goal_uses_observed_frontier(self):
        known = {(i,j) for i in range(2,42) for j in range(1,43)}
        m = Mission(SIM_CONFIG)
        o = healthy(known_free=known)
        self.assertEqual(m.start(o).phase,Phase.TO_DIG)
        self.assertIsNotNone(m.exploration_goal)
        self.assertLess(m.exploration_goal[0],SIM_CONFIG.dig[0])
        self.assertTrue(m.path)
        expanded = {(i,j) for i in range(0,79) for j in range(0,44)}
        o = healthy(1,known_free=expanded)
        m.tick(o)
        self.assertIsNone(m.exploration_goal)
        self.assertEqual(m.path[-1],SIM_CONFIG.dig)


class MissionTests(unittest.TestCase):
    def test_nominal_two_cycles(self):
        result = scenario()
        self.assertEqual(result['phase'], 'complete')
        self.assertGreaterEqual(result['cycles'], 2)
        self.assertGreaterEqual(result['inferred_l'], 25)

    def test_no_autostart_or_restart(self):
        m = Mission(SIM_CONFIG)
        self.assertEqual(m.tick(healthy()).phase, Phase.IDLE)
        m.start(healthy())
        self.assertEqual(m.start(healthy()).phase, Phase.TO_DIG)

    def test_latched_fault(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        self.assertEqual(m.tick(healthy(1, estop=True)).fault, 'estop')
        self.assertEqual(m.tick(healthy(2)).phase, Phase.FAULT)

    def test_stale_inputs(self):
        for name in ('pose_time', 'camera_time', 'lidar_time', 'encoder_time',
                     'mass_time', 'actuator_time', 'battery_time', 'estop_time'):
            with self.subTest(name=name):
                m = Mission(SIM_CONFIG)
                expected = ('stale_estop' if name == 'estop_time' else
                            'stale_initial_tag' if name == 'camera_time' else 'stale_input')
                self.assertEqual(m.start(healthy(100, **{name: 0})).fault, expected)

    def test_tag_can_leave_view_after_initial_localization(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        out = m.tick(healthy(3,camera_time=0))
        self.assertEqual(out.phase,Phase.TO_DIG)
        self.assertEqual(out.fault,'')

    def test_bad_sensors(self):
        examples = {'pose_sigma': 3, 'mass_kg': float('nan'),
                    'battery_v': 0, 'actuator': 'fault',
                    'pose': Pose(-1, 2, 0)}
        for name, value in examples.items():
            with self.subTest(name=name):
                self.assertEqual(Mission(SIM_CONFIG).start(healthy(**{name: value})).phase,
                                 Phase.FAULT)

    def test_failures_stop(self):
        for name in ('lidar_loss', 'camera_loss', 'estop', 'mass_sensor',
                     'actuator_jam', 'dump_jam', 'lift_jam', 'no_berm',
                     'wheels_stuck', 'low_battery', 'bad_pose', 'lost_estop'):
            with self.subTest(name=name):
                self.assertEqual(scenario(name)['phase'], 'fault')

    def test_transient_sensor_and_moving_obstacle_recovery(self):
        for name in ('transient_lidar','moving_obstacle'):
            with self.subTest(name=name):
                result = scenario(name)
                self.assertEqual(result['phase'],'complete')
                self.assertIn('paused',result['trace'])

    def test_seeded_noisy_wheel_slip(self):
        for seed in range(3):
            with self.subTest(seed=seed):
                self.assertEqual(scenario(seed=seed,pose_noise=.01,slip=.07)['phase'],
                                 'complete')

    def test_depth_required_when_enabled(self):
        m = Mission(dataclasses.replace(SIM_CONFIG, require_depth=True))
        self.assertEqual(m.start(healthy()).fault, 'stale_depth')

    def test_brief_sensor_loss_pauses_and_resumes(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        self.assertEqual(m.tick(healthy(1,lidar_time=0)).phase, Phase.PAUSED)
        self.assertEqual(m.tick(healthy(1.5)).phase, Phase.TO_DIG)
        self.assertEqual(m.tick(healthy(1.6)).fault, '')

    def test_obstruction_waits_then_replans(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        blocked = healthy(1,obstacles=[(1.4,2.2)])
        self.assertEqual(m.tick(blocked).phase, Phase.PAUSED)
        self.assertEqual(m.tick(healthy(2)).phase, Phase.TO_DIG)

    def test_dumped_mass_alone_does_not_complete(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        m.phase = Phase.VERIFY
        m.phase_time = 1
        m.cycles = 2
        m.placed_kg = SIM_CONFIG.kg_for_liters(30)
        self.assertEqual(m.tick(healthy(2)).phase, Phase.VERIFY)
        self.assertEqual(m.tick(healthy(17)).fault, 'berm_measurement_timeout')

    def test_goal_requires_heading(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        o = healthy(1, pose=Pose(*SIM_CONFIG.dig, math.pi))
        out = m.tick(o)
        self.assertEqual(out.phase, Phase.TO_DIG)
        self.assertEqual(out.linear, 0)
        self.assertNotEqual(out.angular, 0)

    def test_dig_actuator_ack_timeout(self):
        m = Mission(SIM_CONFIG)
        m.start(healthy())
        o = healthy(1, pose=Pose(*SIM_CONFIG.dig, 0))
        self.assertEqual(m.tick(o).phase, Phase.LOWER)
        o = healthy(2, pose=Pose(*SIM_CONFIG.dig, 0), actuator='lowered')
        self.assertEqual(m.tick(o).phase, Phase.DIG)
        o = healthy(5, pose=Pose(*SIM_CONFIG.dig, 0), actuator='lowered')
        self.assertEqual(m.tick(o).fault, 'dig_not_acknowledged')

    def test_seeded_simple_scenarios(self):
        for seed in range(5):
            with self.subTest(seed=seed):
                self.assertEqual(scenario(seed=seed)['phase'], 'complete')


if __name__ == '__main__':
    unittest.main()
