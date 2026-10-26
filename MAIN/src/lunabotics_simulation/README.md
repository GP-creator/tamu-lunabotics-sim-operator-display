# Gazebo simulation

This package starts the arena, rover model, simulated sensors, navigation and telemetry.

Follow the [shared setup guide](../../README.md) to install, build and run it.

| File | What it controls |
| --- | --- |
| `worlds/arena.sdf` | Arena, obstacles, rover geometry and simulated sensors |
| `launch/simulation.launch.py` | Gazebo, ROS bridge, navigation and telemetry startup |

To run without the Gazebo window, use `bash tools/run_simulation.sh headless:=true` from the extracted download's root after sourcing the workspace.

The model publishes camera, LiDAR, IMU and odometry data under `/sim/*`. It currently tests navigation. Its dimensions, mass and friction are development settings; they have not been calibrated to the physical rover.

[Recorded test results](../../VALIDATION.md)
