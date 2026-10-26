"""Navigation-only controller for measured simulation odometry and laser scans.

This module has no device access and never produces excavation commands.
"""
import math
from .navigation import plan, exploratory_route, follow, route_clear, too_close
from .occupancy import ObstacleMemory
from .types import Config, Pose


class SimulationNavigator:
    def __init__(self, goal=(6.4, 3.1)):
        self.cfg = Config(robot_radius=.35, clearance=.12, stop_distance=.55,
                          max_linear=.35, max_angular=1.0)
        if (len(goal) != 2 or not all(math.isfinite(x) for x in goal)
                or not (.8 <= goal[0] <= self.cfg.width-.8
                        and .8 <= goal[1] <= self.cfg.height-.8)):
            raise ValueError('goal must be inside the simulation arena')
        self.goal = tuple(goal)
        self.memory = ObstacleMemory(self.cfg)
        self.pose = None
        self.pose_time = self.scan_time = -1e9
        self.last_plan = -1e9
        self.path = []
        self.state = 'waiting_for_sensors'
        self.enabled = True
        self.last_tick = None
        self.complete = False

    def odometry(self, pose, stamp):
        if not all(math.isfinite(x) for x in (pose.x, pose.y, pose.yaw, stamp)):
            return False
        if stamp < self.pose_time:
            self.reset()
        self.pose, self.pose_time = pose, stamp
        return True

    def reset(self):
        self.memory = ObstacleMemory(self.cfg)
        self.path = []
        self.pose = None
        self.pose_time = self.scan_time = self.last_plan = -1e9
        self.last_tick = None
        self.complete = False
        self.state = 'waiting_for_sensors'

    def scan(self, ranges, angle_min, angle_increment, range_min, range_max, stamp):
        if (self.pose is None or stamp <= self.scan_time
                or abs(stamp-self.pose_time) > .25
                or not all(math.isfinite(x) for x in
                           (angle_min, angle_increment, range_min, range_max, stamp))
                or angle_increment <= 0 or not 0 <= range_min < range_max):
            return False
        hits = []
        for index, value in enumerate(ranges):
            # Infinite or invalid returns are not observations of free space.
            if not math.isfinite(value) or not range_min < value <= range_max:
                continue
            angle = self.pose.yaw + angle_min + index*angle_increment
            hits.append((self.pose.x+value*math.cos(angle),
                         self.pose.y+value*math.sin(angle)))
        if len(hits) < 20:
            return False
        self.memory.update((self.pose.x, self.pose.y), hits, stamp)
        self.scan_time = stamp
        return True

    def tick(self, now):
        if not math.isfinite(now):
            self.state = 'invalid_clock'
            return 0., 0.
        if self.last_tick is not None and now < self.last_tick:
            self.reset()
            return 0., 0.
        self.last_tick = now
        if not self.enabled:
            self.state = 'paused'
            return 0., 0.
        if (self.pose is None or not 0 <= now-self.pose_time <= .5
                or not 0 <= now-self.scan_time <= .5):
            self.path = []
            self.state = 'waiting_for_sensors'
            return 0., 0.
        if self.complete or math.hypot(self.pose.x-self.goal[0],
                                       self.pose.y-self.goal[1]) <= .25:
            self.complete = True
            self.state = 'complete'
            self.path = []
            return 0., 0.
        points = self.memory.points(now)
        if too_close(self.pose, points, self.cfg):
            self.state = 'obstacle_stop'
            self.path = []
            return 0., 0.
        known = self.memory.known_free(now)
        if now-self.last_plan >= .5 or not route_clear(
                self.pose, self.path, points, self.cfg, known):
            self.path = plan(self.pose, self.goal, points, self.cfg, known)
            if not self.path:
                self.path, _ = exploratory_route(self.pose, self.goal, points,
                                                  self.cfg, known)
            self.last_plan = now
        while len(self.path) > 1 and math.hypot(
                self.path[0][0]-self.pose.x, self.path[0][1]-self.pose.y) < .25:
            self.path.pop(0)
        if not self.path:
            self.state = 'no_observed_path'
            return 0., 0.
        self.state = 'navigating'
        return follow(self.pose, self.path, self.cfg, points)
