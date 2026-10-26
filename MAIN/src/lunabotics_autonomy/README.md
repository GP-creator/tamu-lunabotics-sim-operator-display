# Autonomy code

Package version: **0.3.1**. This package supports the Jazzy laptop setup and the existing Humble environment.

## Choose the test you need

| Test | What it covers | Start here |
| --- | --- | --- |
| Gazebo navigation | Move around obstacles using simulated odometry and LiDAR | [MAIN setup](../../README.md) |
| Synthetic mission | Exercise excavation, travel, dumping and return logic with generated feedback | Commands below |
| Unit tests | Check individual algorithms and error handling | Commands below |

Gazebo currently runs navigation only. The synthetic mission supplies generated sensor and actuator inputs to test the logic; it does not simulate physical excavation.

## Where to edit

- `autonomy/simulation_navigation.py` and `autonomy/ros_simulation_navigation.py`: laptop navigation.
- `autonomy/mission.py`: mission sequence and completion rules.
- `autonomy/navigation.py` and `autonomy/occupancy.py`: planning and map handling.
- `autonomy/localization.py` and `autonomy/fiducials.py`: position estimation and camera tags.
- `autonomy/lidar_health.py` and `autonomy/ros_lidar_health.py`: validation of real LiDAR data.
- `launch/`: ROS startup files.

Unknown map cells stay blocked until observations clear them. The mission checks fresh sensor feedback and faults when required inputs are missing. The localization code owns `map -> odom -> base_link`; another node must not publish the same transforms.

## Run the unit tests

From this package directory:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -q
```

## Run the synthetic ROS mission

After building and sourcing the workspace, use two Ubuntu terminals:

```bash
ros2 launch lunabotics_autonomy graph_sitl.launch.py
```

In the second terminal, source ROS and the same workspace, then run:

```bash
ROS_DOMAIN_ID=213 ros2 run lunabotics_autonomy graph_acceptance
```

The launch uses domain 213. The acceptance check looks for two cycles, at least 25 L of synthetic berm and map/path telemetry. Keep this test separate from the rover network.

## Optional real LiDAR adapter

`lidar.launch.py` needs the separate `unitree_lidar_ros2` SDK2 driver. That driver is outside the five maintained packages. Confirm the LiDAR/local addresses and source its workspace before using this launch.

The adapter publishes `/unilidar/cloud`, `/unilidar/imu` and `/unilidar/health`. It checks data layout, finite values, timestamps, IMU orientation and freshness. A clock reset requires new data before readiness returns. The mounting transform still needs rover calibration.

## Before using physical hardware

The mission publishes `/autonomy/cmd_vel` and `/autonomy/tool_command`; it does not talk directly to motors. Hardware startup needs measured geometry, calibration, approved settings and the CDH feedback described in [hardware interfaces](../../HARDWARE_INTERFACES.md). Leave the hardware launch disarmed for laptop work.

[Recorded test results](../../VALIDATION.md)
