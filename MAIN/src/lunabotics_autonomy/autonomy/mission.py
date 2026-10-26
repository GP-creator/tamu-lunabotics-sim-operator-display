"""Deterministic, latched-fault state machine. Outputs are always zero by default."""
import math
from .navigation import (distance, exploratory_route, follow, plan,
                         route_clear, too_close, wrap)
from .types import Config, Observation, Output, Phase


class Mission:
    def __init__(self, cfg: Config):
        cfg.validate()
        self.cfg = cfg
        self.phase = Phase.IDLE
        self.fault = ''
        self.last_observation_time = None
        self.path = []
        self.exploration_goal = None
        self.last_plan_time = -1e9
        self.resume_phase = None
        self.pause_start = None
        self.pause_reason = ''
        self.start_time = None
        self.phase_time = None
        self.last_progress_time = None
        self.last_goal_distance = float('inf')
        self.cycle_start_mass = None
        self.dump_entry_mass = None
        self.placed_kg = 0.0  # inferred from measured hopper loss, NOT measured berm volume
        self.cycles = 0
        self.last_material_progress_time = None
        self.last_material_mass = 0.0

    def start(self, obs: Observation):
        if self.phase != Phase.IDLE:
            return self.tick(obs)
        issue = self._health(obs)
        if issue:
            return self._fault(issue)
        if obs.mass_kg is None or obs.mass_kg > self.cfg.mass_tolerance_kg:
            return self._fault('hopper_not_empty_at_start')
        if not obs.baseline_ready:
            return self._fault('berm_baseline_missing')
        self.start_time = obs.now
        return self._transition(Phase.TO_DIG, obs)

    def reset(self):
        """Manual rearm only; no automatic restart after a fault or completion."""
        self.__init__(self.cfg)

    def _fault(self, cause):
        self.phase, self.fault, self.path = Phase.FAULT, cause, []
        return Output(Phase.FAULT, fault=cause)

    def _pause(self, cause, now):
        if self.phase != Phase.PAUSED:
            self.resume_phase, self.pause_start = self.phase, now
        self.phase, self.pause_reason = Phase.PAUSED, cause
        return Output(Phase.PAUSED, fault=cause)

    def _transition(self, phase, obs):
        self.phase, self.phase_time = phase, obs.now
        self.last_progress_time, self.last_goal_distance = obs.now, float('inf')
        self.path = []
        self.exploration_goal = None
        if phase in (Phase.TO_DIG, Phase.TO_DUMP):
            dest = self.cfg.dig if phase == Phase.TO_DIG else self.cfg.dump
            self._route(obs,dest)
            if not self.path:
                return self._pause('no_safe_path', obs.now)
            self.last_plan_time = obs.now
        if phase == Phase.DIG:
            self.cycle_start_mass = obs.mass_kg
            self.last_material_mass = obs.mass_kg
            self.last_material_progress_time = obs.now
        if phase == Phase.DUMP:
            if obs.mass_kg is None or obs.mass_kg < self.cfg.mass_tolerance_kg:
                return self._fault('no_load_to_dump')
            self.dump_entry_mass = obs.mass_kg
            self.last_material_mass = obs.mass_kg
            self.last_material_progress_time = obs.now
        return Output(phase)

    def _route(self, obs, dest):
        direct = plan(obs.pose,dest,obs.obstacles,self.cfg,obs.known_free)
        if direct:
            self.path,self.exploration_goal = direct,None
        else:
            self.path,self.exploration_goal = exploratory_route(obs.pose,dest,
                obs.obstacles,self.cfg,obs.known_free)
        self.last_plan_time = obs.now

    def _health(self, o):
        c, t = self.cfg, o.now
        required_times = (t,o.estop_time,o.pose_time,o.lidar_time,o.encoder_time,
                          o.mass_time,o.actuator_time,o.battery_time)
        if self.phase == Phase.IDLE:
            required_times += (o.camera_time,)
        if c.require_depth:
            required_times += (o.depth_time,)
        if not all(math.isfinite(v) for v in required_times):
            return 'invalid_timestamp'
        if self.last_observation_time is not None and t < self.last_observation_time:
            return 'clock_regression'
        self.last_observation_time = t
        if o.estop:
            return 'estop'
        if t - o.estop_time > c.estop_timeout or o.estop_time > t + 0.1:
            return 'stale_estop'
        if self.phase == Phase.IDLE and (
                t-o.camera_time > c.camera_timeout or o.camera_time > t+.1):
            return 'stale_initial_tag'
        if o.pose is None or not all(math.isfinite(v) for v in (o.pose.x, o.pose.y, o.pose.yaw)):
            return 'invalid_pose'
        if any(t - stamp > limit or stamp > t + 0.1 for stamp, limit in (
            (o.pose_time, c.pose_timeout),
            (o.lidar_time, c.lidar_timeout), (o.encoder_time, c.encoder_timeout),
            (o.mass_time, c.mass_timeout), (o.actuator_time, c.actuator_timeout),
            (o.battery_time, c.battery_timeout))):
            return 'stale_input'
        if c.require_depth and (t - o.depth_time > c.depth_timeout or o.depth_time > t + 0.1):
            return 'stale_depth'
        if not math.isfinite(o.pose_sigma) or not 0 <= o.pose_sigma <= c.max_pose_sigma:
            return 'pose_uncertain'
        if o.mass_kg is None or not math.isfinite(o.mass_kg) or o.mass_kg < -0.01:
            return 'invalid_mass'
        if o.mass_kg > c.kg_for_liters(c.hopper_limit_l) * 1.01:
            return 'hopper_overfill'
        if o.battery_v is None or not math.isfinite(o.battery_v) or o.battery_v < c.min_battery_v:
            return 'battery_low'
        if o.actuator not in ('raised', 'lowering', 'lowered', 'digging',
                             'raising', 'dumping', 'stopped'):
            return 'actuator_fault'
        clearance = c.robot_radius + c.clearance
        if not (clearance <= o.pose.x <= c.width - clearance and
                clearance <= o.pose.y <= c.height - clearance):
            return 'geofence'
        if too_close(o.pose, o.obstacles, c):
            return 'obstacle_too_close'
        return ''

    def tick(self, o: Observation):
        if self.phase in (Phase.IDLE, Phase.FAULT, Phase.COMPLETE):
            return Output(self.phase, fault=self.fault)
        issue = self._health(o)
        recoverable = ('stale_input', 'stale_estop', 'stale_depth',
                       'pose_uncertain', 'obstacle_too_close')
        if self.phase == Phase.PAUSED:
            if issue and issue not in recoverable:
                return self._fault(issue)
            if o.now-self.pause_start > self.cfg.pause_timeout:
                return self._fault('pause_timeout:' + self.pause_reason)
            if issue:
                return Output(Phase.PAUSED, fault=issue)
            target = self.resume_phase
            if target in (Phase.TO_DIG, Phase.TO_DUMP):
                goal = self.cfg.dig if target == Phase.TO_DIG else self.cfg.dump
                self._route(o,goal)
                if not self.path:
                    return Output(Phase.PAUSED, fault='no_safe_path')
            duration = o.now-self.pause_start
            self.phase = target
            self.last_progress_time += duration
            self.phase_time += duration
            if target in (Phase.DIG, Phase.DUMP):
                self.last_material_progress_time += duration
            self.resume_phase, self.pause_start, self.pause_reason = None, None, ''
            return Output(self.phase)  # resume with a zero-command tick
        if issue:
            if issue in recoverable:
                return self._pause(issue, o.now)
            return self._fault(issue)
        if o.now - self.start_time > self.cfg.mission_timeout:
            return self._fault('mission_timeout')
        if self.phase in (Phase.TO_DIG, Phase.TO_DUMP):
            if o.actuator != 'raised':
                if (self.phase == Phase.TO_DIG and o.actuator == 'dumping' and
                    o.now-self.phase_time <= self.cfg.actuator_transition_timeout):
                    return Output(self.phase)  # await the commanded tool stop
                return self._fault('tool_not_raised_for_travel')
            dest = self.cfg.dig if self.phase == Phase.TO_DIG else self.cfg.dump
            d = distance((o.pose.x, o.pose.y), dest)
            if (self.exploration_goal is not None and
                distance((o.pose.x,o.pose.y),self.exploration_goal)
                    <= self.cfg.goal_tolerance):
                self._route(o,dest)
                if not self.path:
                    return self._pause('no_safe_path',o.now)
                return Output(self.phase)
            if d <= self.cfg.goal_tolerance:
                target_yaw = (self.cfg.dig_yaw if self.phase == Phase.TO_DIG
                              else self.cfg.dump_yaw)
                error = wrap(target_yaw - o.pose.yaw)
                if abs(error) > self.cfg.heading_tolerance:
                    if o.now - self.last_progress_time > self.cfg.stall_timeout:
                        return self._fault('heading_stalled')
                    return Output(self.phase, angular=max(-self.cfg.max_angular,
                        min(self.cfg.max_angular, 1.8*error)))
                return self._transition(Phase.LOWER if self.phase == Phase.TO_DIG else Phase.DUMP, o)
            if d < self.last_goal_distance - 0.04:
                self.last_goal_distance, self.last_progress_time = d, o.now
            if o.now - self.last_progress_time > self.cfg.stall_timeout:
                return self._fault('drive_stalled')
            if (o.now-self.last_plan_time >= self.cfg.replan_interval or
                not route_clear(o.pose, self.path, o.obstacles, self.cfg, o.known_free)):
                self._route(o,dest)
            if not self.path:
                return self._pause('no_safe_path', o.now)
            linear, angular = follow(o.pose, self.path, self.cfg, o.obstacles,
                                     loaded=self.phase == Phase.TO_DUMP)
            return Output(self.phase, linear, angular)
        if self.phase == Phase.LOWER:
            if o.now-self.phase_time > self.cfg.lower_timeout:
                return self._fault('lower_timeout')
            if o.actuator not in ('raised', 'lowering', 'lowered'):
                return self._fault('wrong_lower_feedback')
            if o.actuator == 'lowered':
                return self._transition(Phase.DIG, o)
            return Output(Phase.LOWER, tool='lower')
        if self.phase == Phase.DIG:
            if o.now - self.phase_time > self.cfg.dig_timeout:
                return self._fault('dig_timeout')
            if o.actuator not in ('lowered', 'digging'):
                return self._fault('wrong_dig_feedback')
            if o.now - self.phase_time > 2 and o.actuator != 'digging':
                return self._fault('dig_not_acknowledged')
            fill = o.mass_kg - self.cycle_start_mass
            if fill < -self.cfg.mass_tolerance_kg:
                return self._fault('mass_dropped_during_dig')
            if fill >= self.cfg.kg_for_liters(self.cfg.per_cycle_l) - self.cfg.mass_tolerance_kg:
                return self._transition(Phase.RAISE, o)
            if o.mass_kg-self.last_material_mass >= self.cfg.material_progress_kg:
                self.last_material_mass,self.last_material_progress_time = o.mass_kg,o.now
            if o.now-self.last_material_progress_time > self.cfg.dig_progress_timeout:
                return self._fault('dig_jam')
            return Output(self.phase, tool='dig')
        if self.phase == Phase.RAISE:
            if o.now-self.phase_time > self.cfg.raise_timeout:
                return self._fault('raise_timeout')
            if (o.actuator == 'digging' and
                o.now-self.phase_time <= self.cfg.actuator_transition_timeout):
                # Wait stopped for acknowledgment of the preceding tool stop.
                return Output(Phase.RAISE)
            if o.actuator not in ('lowered', 'raising', 'raised'):
                return self._fault('wrong_raise_feedback')
            if o.actuator == 'raised':
                return self._transition(Phase.TO_DUMP, o)
            return Output(Phase.RAISE, tool='raise')
        if self.phase == Phase.DUMP:
            if o.now - self.phase_time > self.cfg.dump_timeout:
                return self._fault('dump_timeout')
            if o.actuator not in ('raised', 'dumping'):
                return self._fault('wrong_dump_feedback')
            if o.now - self.phase_time > 2 and o.actuator != 'dumping':
                return self._fault('dump_not_acknowledged')
            if o.mass_kg > self.dump_entry_mass + self.cfg.mass_tolerance_kg:
                return self._fault('mass_rose_during_dump')
            if o.mass_kg <= self.cfg.mass_tolerance_kg:
                self.placed_kg += max(0.0, self.dump_entry_mass - o.mass_kg)
                self.cycles += 1
                return self._transition(Phase.VERIFY, o)
            if self.last_material_mass-o.mass_kg >= self.cfg.material_progress_kg:
                self.last_material_mass,self.last_material_progress_time = o.mass_kg,o.now
            if o.now-self.last_material_progress_time > self.cfg.dump_progress_timeout:
                return self._fault('dump_jam')
            return Output(self.phase, tool='dump')
        if self.phase == Phase.VERIFY:
            if o.now-self.phase_time > self.cfg.berm_timeout:
                return self._fault('berm_measurement_timeout')
            if (o.berm_volume_l is None or not math.isfinite(o.berm_time) or
                not self.phase_time < o.berm_time <= o.now + .1 or
                o.now-o.berm_time > self.cfg.berm_timeout or
                not math.isfinite(o.berm_volume_l) or o.berm_volume_l < 0):
                return Output(Phase.VERIFY)
            if o.berm_volume_l >= self.cfg.target_l and self.cycles >= 2:
                self.phase = Phase.COMPLETE
                return Output(Phase.COMPLETE)
            if self.cycles >= self.cfg.max_cycles:
                return self._fault('material_target_unmet')
            return self._transition(Phase.TO_DIG, o)
        return self._fault('unknown_phase')
