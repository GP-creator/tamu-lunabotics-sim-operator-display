# Shared topic and bridge settings

This package holds settings used by the simulation and the team tools.

| File | Edit it when you need to... |
| --- | --- |
| `config/topics.csv` | Add or check a topic's name, type, frame, units or expected rate |
| `config/gazebo_bridge.yaml` | Pass a topic between Gazebo and ROS |

Use the [top-level README](../../../README.md) for your download's install and build steps. The simulator starts the bridge for you.

After a change, run the simulation, check `ros2 topic list`, and measure the affected topic with `ros2 topic hz`. Tell the telemetry team if a name or type changes. Keep expected rates separate from measured results.

The `/sim/*` topics are for the laptop simulation. Hardware interfaces are described in [MAIN/HARDWARE_INTERFACES.md](../../../MAIN/HARDWARE_INTERFACES.md).
