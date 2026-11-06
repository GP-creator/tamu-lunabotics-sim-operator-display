# MCAP verification: SIMULATED_pdr_20261104_115721

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_pdr_20261104_115721`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 42.18 |
| File size (MB) | 104.65 |
| Storage rate (MB/min) | 148.87 |
| Chunk compression | none |
| Messages | 30867 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.55 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 21088 | 500.00 | 100 | 0.000 | 0.006 | 0 | 48.0 | FAIL: rate_within_20pct |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 422 | 10.00 | 10 | 0.094 | 0.106 | 0 | 29.5 | PASS |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 422 | 9.99 | 10 | 0.070 | 0.130 | 0 | 18447.0 | PASS |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 822 | 19.50 | 20 | 0.002 | 0.322 | 7 | 8.1 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 4218 | 100.00 | 100 | 0.006 | 0.014 | 0 | 259.2 | PASS |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 84 | 1.98 | 2 | 0.328 | 0.956 | 0 | 57.0 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 1240 | 29.41 | 30 | 0.032 | 0.036 | 0 | 170.3 | PASS |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 84 | 1.98 | 2 | 0.324 | 0.954 | 0 | 2.2 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 422 | 9.99 | 10 | 0.074 | 0.162 | 0 | 466.2 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 822 | 19.50 | 20 | 0.002 | 0.322 | 7 | 40.1 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1240 | 29.41 | — | 0.032 | 0.036 | 0 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | — | — | 0.000 | 0.000 | — | 0.1 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 21088 messages, monotonic: **True**, max |log time − clock| = 0.004 s
- TF root: `odom`; all message frames connected: **True**
  - `/sim/camera/camera_info` frame `camera_link` → root `odom`
  - `/sim/camera/image` frame `camera_link` → root `odom`
  - `/sim/scan` frame `base_scan` → root `odom`
  - `/sim/imu` frame `imu_link` → root `odom`
  - `/sim/odom` frame `odom` → root `odom`
  - `/sim/planned_path` frame `odom` → root `odom`
  - `/sim/obstacle_grid` frame `odom` → root `odom`

## Mission state timeline (`/sim/status`, source `gazebo_simulation`)

| t (s) | State |
| --- | --- |
| 0.05 | waiting_for_sensors |
| 0.37 | navigating |
| 1.33 | waiting_for_sensors |
| 1.53 | navigating |
| 36.90 | complete |

Goal reached: **True**

Distance travelled (odometry): 5.67 m

## Process resources (24 cores; CPU % of one core)

| Process | Samples | CPU mean % | CPU max % | RSS max MB |
| --- | --- | --- | --- | --- |
| gazebo | 45 | 213.8 | 244.4 | 567.6 |
| gz_bridge | 46 | 48.4 | 58.6 | 58.7 |
| navigator | 48 | 65.2 | 96.2 | 78.8 |
| recorder | 46 | 33.6 | 42.7 | 84.6 |
| rosbridge | 48 | 91.9 | 107.9 | 100.7 |

## Link margin (PLACEHOLDER BUDGET)

Required (live Rosbridge, layout topics): **— Mbit/s**. Assumed link: **10.00 Mbit/s** ← placeholder from `pdr/link_budget.json`, replace with Sabu+Robin's measured numbers.

Margin: — Mbit/s; utilisation — %.

## Plots

- `topic_rates.png`
- `xy_path.png`
- `bandwidth_per_topic.png`
- `gap_timeline.png`

## mcap CLI

```
mcap CLI not on PATH; skipped (Python mcap library used instead)
```
