"""Simple kinematic regression harness, explicitly not a physics or ROS certification."""
import json
import math
import random
from collections import deque
from .mission import Mission
from .navigation import wrap
from .types import Config, Observation, Phase, Pose


SIM_CONFIG = Config(hopper_limit_l=16.0, bulk_density_kg_m3=1600.0)


def scenario(failure='', dt=0.1, max_steps=12000, seed=None,
             pose_noise=0.0, slip=0.0, feedback_delay_steps=0):
    if type(feedback_delay_steps) is not int or not 0 <= feedback_delay_steps <= 20:
        raise ValueError('feedback_delay_steps must be an integer in 0..20')
    feedback = deque(['raised']*feedback_delay_steps)
    cfg = SIM_CONFIG
    mission = Mission(cfg)
    pose = Pose(1.1, 2.2, 0.0)
    mass = 0.0
    berm_l = 0.0
    actuator = 'raised'
    tool_lowered = False
    lift_progress = 0.0
    phase_trace = []
    # Fails if obstacle intersects footprint; a layout with no obstacles
    # does not exercise obstacle perception or mapping.
    rng = random.Random(seed)
    obstacles = ([(3.9, 1.15), (3.9, 3.25)] if seed is None else
                 [(rng.uniform(2.5, 5.0), rng.uniform(.8, 1.2)),
                  (rng.uniform(2.5, 5.0), rng.uniform(3.2, 3.6))])
    dig_rate = 0.30 if seed is None else rng.uniform(.27, .36)
    for step in range(max_steps):
        t = step * dt
        measured = (Pose(pose.x+rng.gauss(0,pose_noise),
                         pose.y+rng.gauss(0,pose_noise),
                         wrap(pose.yaw+rng.gauss(0,pose_noise)))
                    if pose_noise else pose)
        visible = list(obstacles)
        if failure == 'moving_obstacle' and 10 < t < 11:
            visible.append((pose.x+0.35,pose.y))
        feedback.append(actuator)
        reported_actuator = feedback.popleft()
        o = Observation(now=t, pose=measured, pose_time=t, camera_time=t,
                        lidar_time=t, encoder_time=t, mass_time=t,
                        actuator_time=t, battery_time=t, battery_v=25.0,
                        estop_time=t,
                        pose_sigma=0.05, mass_kg=mass, actuator=reported_actuator,
                        baseline_ready=True, berm_volume_l=berm_l,
                        berm_time=t,
                        obstacles=visible)
        if failure == 'lidar_loss' and t > 10:
            o.lidar_time = 9.0
        if failure == 'camera_loss' and t > 61:
            o.camera_time = 0.0
            o.pose_sigma = .05+.03*(t-61)
        if failure == 'estop' and t > 10:
            o.estop = True
        if failure == 'mass_sensor' and t > 10:
            o.mass_time = 8.0
        if failure == 'transient_lidar' and 10 < t < 11:
            o.lidar_time = 9.0
        if failure == 'low_battery' and t > 10:
            o.battery_v = 10.0
        if failure == 'bad_pose' and t > 10:
            o.pose_sigma = 1.0
        if failure == 'lost_estop' and t > 10:
            o.estop_time = 9.0
        if failure == 'actuator_jam' and t > 12:
            # Feedback remains active, but hopper mass will cease growing.
            pass
        out = mission.start(o) if step == 0 else mission.tick(o)
        if out.phase == Phase.VERIFY:
            # Synthetic "surface survey" exactly measures deposited material.
            # Real completion requires the independent camera survey node.
            berm_l = (0.0 if failure == 'no_berm' else
                      mission.placed_kg * 1000 / cfg.bulk_density_kg_m3)
        if not phase_trace or out.phase.value != phase_trace[-1]:
            phase_trace.append(out.phase.value)
        if out.phase in (Phase.COMPLETE, Phase.FAULT):
            return {'phase': out.phase.value, 'fault': out.fault,
                    'seconds': round(t, 1), 'cycles': mission.cycles,
                    'inferred_l': round(mission.placed_kg * 1000 / cfg.bulk_density_kg_m3, 2),
                    'measured_berm_l': round(berm_l,2),
                    'trace': phase_trace}
        # Ideal differential drive (no wheel slip, inertia, terrain, dust or latency).
        yaw = wrap(pose.yaw + out.angular * dt)
        ground_scale = 1.0 if seed is None else 1.0-slip*rng.random()
        if failure == 'wheels_stuck' and t > 10:
            ground_scale = 0.0
        pose = Pose(pose.x + ground_scale*out.linear * math.cos(yaw) * dt,
                    pose.y + ground_scale*out.linear * math.sin(yaw) * dt, yaw)
        if any(math.hypot(pose.x - x, pose.y - y) <= cfg.robot_radius for x, y in obstacles):
            raise AssertionError('simulated collision')
        if out.tool == 'dig' and failure != 'actuator_jam':
            mass = min(cfg.kg_for_liters(cfg.hopper_limit_l), mass + dig_rate * dt)
        elif out.tool == 'dump' and failure != 'dump_jam':
            mass = max(0.0, mass - 0.45 * dt)
        if out.tool in ('lower','raise'):
            if failure != 'lift_jam':
                lift_progress += dt
            if lift_progress >= 2.0:
                tool_lowered = out.tool == 'lower'
                actuator = 'lowered' if tool_lowered else 'raised'
            else:
                actuator = 'lowering' if out.tool == 'lower' else 'raising'
        else:
            lift_progress = 0.0
            actuator = {'dig':'digging','dump':'dumping'}.get(
                out.tool,'lowered' if tool_lowered else 'raised')
    raise AssertionError('simulation did not terminate')


def main():
    for name in ('', 'transient_lidar', 'moving_obstacle', 'lidar_loss',
                 'camera_loss', 'estop', 'mass_sensor', 'actuator_jam',
                 'dump_jam', 'lift_jam', 'no_berm', 'wheels_stuck', 'low_battery'):
        print(json.dumps({'scenario': name or 'nominal', **scenario(name)}))


if __name__ == '__main__':
    main()
