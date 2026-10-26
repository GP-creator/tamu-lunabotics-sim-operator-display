"""Conservative planar wheel odometry with surveyed fiducial correction.

Owns map->odom and odom->base_link. It produces no global pose until a
surveyed tag is accepted and latches on encoder discontinuities.
"""
import math
from .navigation import wrap
from .types import Pose


class WheelTagEstimator:
    def __init__(self, wheel_radius_m, wheel_track_m, ticks_per_revolution,
                 max_wheel_speed_mps, arena_width, arena_height):
        values = (wheel_radius_m,wheel_track_m,ticks_per_revolution,
                  max_wheel_speed_mps,arena_width,arena_height)
        if not all(math.isfinite(v) and v > 0 for v in values):
            raise ValueError('measured wheel, encoder, and arena calibration required')
        self.meters_per_tick = 2*math.pi*wheel_radius_m/ticks_per_revolution
        self.track = wheel_track_m
        self.max_wheel_speed = max_wheel_speed_mps
        self.width,self.height = arena_width,arena_height
        self.odom = Pose(0.,0.,0.)
        self.alignment = Pose(0.,0.,0.)  # map pose of odom origin
        self.counts = None
        self.count_time = None
        self.last_tag_time = -1e9
        self.distance_since_tag = 0.
        self.turn_since_tag = 0.
        self.position_sigma = float('inf')
        self.yaw_sigma = float('inf')
        self.localized = False
        self.fault = ''
        self.linear = self.angular = 0.

    def accept_counts(self, left, right, now):
        if self.fault or not math.isfinite(now) or not all(
            isinstance(v,int) and -(2**31) <= v < 2**31 for v in (left,right)):
            return False
        if self.counts is None:
            self.counts,self.count_time = (left,right),now
            return True
        dt = now-self.count_time
        if dt <= 0 or dt > .5:
            self.fault = 'encoder_timestamp_gap'
            return False
        delta = [((value-old+2**31) % 2**32)-2**31 for value,old
                 in zip((left,right),self.counts)]
        dl,dr = (v*self.meters_per_tick for v in delta)
        if max(abs(dl),abs(dr)) > self.max_wheel_speed*dt*1.5 + .005:
            self.fault = 'encoder_jump'
            return False
        ds,dtheta = (dl+dr)/2,(dr-dl)/self.track
        mid = self.odom.yaw+dtheta/2
        self.odom = Pose(self.odom.x+ds*math.cos(mid),
                         self.odom.y+ds*math.sin(mid),
                         wrap(self.odom.yaw+dtheta))
        self.counts,self.count_time = (left,right),now
        self.linear,self.angular = ds/dt,dtheta/dt
        self.distance_since_tag += (abs(dl)+abs(dr))/2
        self.turn_since_tag += abs(dtheta)
        return True

    @property
    def pose(self):
        if not self.localized or self.fault:
            return None
        c,s = math.cos(self.alignment.yaw),math.sin(self.alignment.yaw)
        return Pose(self.alignment.x+c*self.odom.x-s*self.odom.y,
                    self.alignment.y+s*self.odom.x+c*self.odom.y,
                    wrap(self.alignment.yaw+self.odom.yaw))

    def accept_tag(self, pose, position_variance, yaw_variance, stamp, now):
        if self.fault or self.counts is None or not all(math.isfinite(v) for v in
            (pose.x,pose.y,pose.yaw,position_variance,yaw_variance,stamp,now)):
            return False
        if (position_variance <= 0 or yaw_variance <= 0 or
            position_variance > .09 or yaw_variance > .09 or
            not (0 <= pose.x <= self.width and 0 <= pose.y <= self.height) or
            abs(now-stamp) > .2 or stamp <= self.last_tag_time or
            abs(now-self.count_time) > .2):
            return False
        current = self.pose
        if current and (math.hypot(current.x-pose.x,current.y-pose.y) > .5 or
                        abs(wrap(current.yaw-pose.yaw)) > .4):
            return False  # outlier must not move map->odom
        angle = wrap(pose.yaw-self.odom.yaw)
        c,s = math.cos(angle),math.sin(angle)
        self.alignment = Pose(pose.x-c*self.odom.x+s*self.odom.y,
                              pose.y-s*self.odom.x-c*self.odom.y,angle)
        self.localized = True
        self.last_tag_time = stamp
        self.distance_since_tag = self.turn_since_tag = 0.
        self.position_sigma = math.sqrt(position_variance)
        self.yaw_sigma = math.sqrt(yaw_variance)
        return True

    @property
    def uncertainty(self):
        # Explicit growth under wheel travel/turn; thresholds are conservative
        # software defaults pending measured wheel-slip calibration.
        return (self.position_sigma + .025*self.distance_since_tag +
                .03*self.turn_since_tag,
                self.yaw_sigma + .02*self.distance_since_tag +
                .02*self.turn_since_tag)
