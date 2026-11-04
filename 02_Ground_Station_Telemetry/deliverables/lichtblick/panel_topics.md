# Panel → topic → message type

Generated from `lichtblick_layout.json` by `tools/layout_diagram.py`; do not edit by hand. "script X ←" means the panel shows LichtBlick User Script X, which reads the listed ROS topics and publishes nothing to ROS.

| Tab | Panel | Type | Topic → message type |
| --- | --- | --- | --- |
| Operator | MISSION STATE | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | WARNINGS | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | DATA ORIGIN | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | CONNECTION: source / live state (built-in) | SourceInfo | LichtBlick data source + connection state (built-in, no topic) |
| Operator | LiDAR /sim/scan | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | Pose /sim/odom | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | Camera /sim/camera/image | Indicator | script camera_health ←; /sim/camera/image → Image; /tf → TFMessage |
| Operator | Status link /sim/status | Indicator | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | Map, planned path, LiDAR (SIMULATED) | 3D | /sim/obstacle_grid → OccupancyGrid; /sim/planned_path → Path; /sim/scan → LaserScan; script rover_footprint ←; /sim/odom → Odometry |
| Operator | Camera (SIMULATED) /sim/camera/image | Image | /sim/camera/camera_info → CameraInfo; /sim/camera/image → Image |
| Operator | Mission state and warnings over time | StateTransitions | script mission_status ←; /sim/status → String; /tf → TFMessage |
| Operator | Data age (s): limits 0.5 s LiDAR/pose, 2 s camera, 1 s status | Plot | script camera_health ←; /sim/camera/image → Image; /tf → TFMessage; script mission_status ←; /sim/status → String |
| Operator | Commanded speed (SIMULATED navigator) | Plot | /sim/cmd_vel → Twist |
| Details | Raw /sim/status (SIMULATED navigator JSON) | RawMessagesVirtual | /sim/status → String |
| Details | Data source: topics, types, start/end time | SourceInfo | LichtBlick data source + connection state (built-in, no topic) |
| Details | Rover-only (not in simulation): Battery | Indicator | no input topic → UNAVAILABLE |
| Details | Rover-only (not in simulation): E-stop | Indicator | no input topic → UNAVAILABLE |
| Details | Rover-only (not in simulation): Faults | Indicator | no input topic → UNAVAILABLE |
