# Panel → topic → message type

Generated from `lichtblick_layout_gnc2027.json` by `tools/layout_diagram.py`; do not edit by hand. "script X ←" means the panel shows LichtBlick User Script X, which reads the listed ROS topics and publishes nothing to ROS.

| Tab | Panel | Type | Topic → message type |
| --- | --- | --- | --- |
| Operator | GUIDANCE STATE (/guidance/status) | Indicator | /guidance/status → GuidanceStatus |
| Operator | PLANNER STATE (/planning/status) | Indicator | /planning/status → PlannerStatus |
| Operator | CONNECTION: source / live state (built-in) | SourceInfo | LichtBlick data source + connection state (built-in, no topic) |
| Operator | Pose /odometry/filtered | Indicator | script pose_health ←; /odometry/filtered → Odometry; /tf → TFMessage |
| Operator | IMU /imu/data_raw | Indicator | script imu_health ←; /imu/data_raw → Imu; /tf → TFMessage |
| Operator | Map, planned path, guidance (GNC-2027 topics) | 3D | /guidance/collision_arc → Path; /guidance/path → Path; /map → OccupancyGrid; script gnc_footprint ←; /odometry/filtered → Odometry; /tags/markers → MarkerArray |
| Operator | Camera: no image topic in GNC-2027 (CDH camera topic TBD) | Image |  |
| Operator | Guidance and planner state over time | StateTransitions | /guidance/status → GuidanceStatus; /planning/status → PlannerStatus |
| Operator | Guidance tracking (m) | Plot | /guidance/status → GuidanceStatus |
| Operator | Data age (s): pose and IMU, limit 0.5 s | Plot | script imu_health ←; /imu/data_raw → Imu; /tf → TFMessage; script pose_health ←; /odometry/filtered → Odometry |
| Operator | Commanded speed (/cmd_vel TwistStamped from guidance) | Plot | /cmd_vel → TwistStamped |
| Details | Raw /planning/status (reason in .message) | RawMessagesVirtual | /planning/status → PlannerStatus |
| Details | Raw /guidance/status (reason in .message) | RawMessagesVirtual | /guidance/status → GuidanceStatus |
| Details | Data source: topics, types, start/end time | SourceInfo | LichtBlick data source + connection state (built-in, no topic) |
