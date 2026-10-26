from dataclasses import dataclass, field, fields
import math
from enum import Enum


class Phase(str, Enum):
    IDLE = 'idle'
    TO_DIG = 'to_dig'
    LOWER = 'lower'
    DIG = 'dig'
    RAISE = 'raise'
    TO_DUMP = 'to_dump'
    DUMP = 'dump'
    VERIFY = 'verify'
    COMPLETE = 'complete'
    FAULT = 'fault'
    PAUSED = 'paused'


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    yaw: float


@dataclass
class Observation:
    now: float
    pose: Pose | None = None
    pose_time: float = -1e9
    pose_sigma: float = 1e9
    camera_time: float = -1e9
    lidar_time: float = -1e9
    depth_time: float = -1e9
    encoder_time: float = -1e9
    mass_time: float = -1e9
    actuator_time: float = -1e9
    mass_kg: float | None = None
    berm_volume_l: float | None = None
    berm_time: float = -1e9
    baseline_ready: bool = False
    battery_v: float | None = None
    battery_time: float = -1e9
    actuator: str = 'unknown'
    estop: bool = False
    estop_time: float = -1e9
    obstacles: list[tuple[float, float]] = field(default_factory=list)  # map frame
    known_free: set[tuple[int, int]] | None = None  # None only in idealized SITL


@dataclass(frozen=True)
class Output:
    phase: Phase
    linear: float = 0.0
    angular: float = 0.0
    tool: str = 'stop'
    fault: str = ''


@dataclass(frozen=True)
class Config:
    width: float = 7.9
    height: float = 4.4
    robot_radius: float = 0.48
    clearance: float = 0.12
    cell: float = 0.10
    dig: tuple[float, float] = (6.9, 2.2)
    dump: tuple[float, float] = (1.1, 2.2)
    dig_yaw: float = 0.0
    dump_yaw: float = 3.141592653589793
    heading_tolerance: float = 0.20
    target_l: float = 25.0
    per_cycle_l: float = 14.0
    hopper_limit_l: float = 0.0   # require a physical measurement/configuration
    bulk_density_kg_m3: float = 0.0  # require a measured calibration
    max_linear: float = 0.25
    loaded_max_linear: float = 0.18
    max_angular: float = 0.8
    replan_interval: float = 0.5
    pause_timeout: float = 5.0
    min_battery_v: float = 20.0  # illustrative; set for actual battery chemistry
    max_pose_sigma: float = 0.35
    pose_timeout: float = 0.5
    camera_timeout: float = 2.0  # initial surveyed localization, then covariance governs
    lidar_timeout: float = 0.5
    depth_timeout: float = 0.5
    require_depth: bool = False
    encoder_timeout: float = 0.5
    mass_timeout: float = 1.0
    actuator_timeout: float = 1.0
    actuator_transition_timeout: float = 0.5
    battery_timeout: float = 2.0
    estop_timeout: float = 0.5
    stop_distance: float = 0.7
    goal_tolerance: float = 0.30
    mass_tolerance_kg: float = 0.15
    stall_timeout: float = 8.0
    dig_timeout: float = 90.0
    lower_timeout: float = 10.0
    raise_timeout: float = 10.0
    dump_timeout: float = 60.0
    dig_progress_timeout: float = 12.0
    dump_progress_timeout: float = 10.0
    material_progress_kg: float = 0.25
    mission_timeout: float = 900.0
    berm_timeout: float = 15.0
    max_cycles: int = 6

    def validate(self):
        for item in fields(self):
            value = getattr(self,item.name)
            values = value if isinstance(value,tuple) else (value,)
            if any(isinstance(v,(int,float)) and not math.isfinite(v) for v in values):
                raise ValueError('nonfinite configuration: ' + item.name)
        positive = ('max_angular','heading_tolerance','min_battery_v','max_pose_sigma',
            'pose_timeout','camera_timeout','lidar_timeout','depth_timeout',
            'encoder_timeout','mass_timeout','actuator_timeout','actuator_transition_timeout','battery_timeout',
            'estop_timeout','stop_distance','goal_tolerance','mass_tolerance_kg',
            'stall_timeout','dig_timeout','lower_timeout','raise_timeout',
            'dump_timeout','mission_timeout','berm_timeout','material_progress_kg')
        if self.clearance < 0 or any(getattr(self,k) <= 0 for k in positive):
            raise ValueError('positive finite limits and timeouts required')
        if type(self.max_cycles) is not int:
            raise ValueError('max_cycles must be an integer')
        if min(self.width, self.height, self.cell, self.robot_radius,
               self.max_linear, self.target_l, self.per_cycle_l) <= 0:
            raise ValueError('invalid geometry, speed or mission target')
        if self.hopper_limit_l <= 0 or self.bulk_density_kg_m3 <= 0:
            raise ValueError('measured hopper limit and bulk density required')
        if self.per_cycle_l > self.hopper_limit_l * 0.95:
            raise ValueError('cycle fill exceeds 95% of hopper limit')
        if self.loaded_max_linear <= 0 or self.pause_timeout <= 0 or self.replan_interval <= 0:
            raise ValueError('invalid loaded speed or retry timings')
        if self.max_cycles < 2 or self.dig_progress_timeout <= 0 or self.dump_progress_timeout <= 0:
            raise ValueError('invalid material progress parameters')
        for p in (self.dig, self.dump):
            c = self.robot_radius + self.clearance
            if not (c <= p[0] <= self.width - c and c <= p[1] <= self.height - c):
                raise ValueError('goal outside safe arena')

    def kg_for_liters(self, liters):
        return liters * self.bulk_density_kg_m3 / 1000.0
