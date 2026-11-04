# MCAP verification: SIMULATED_pdr_20261104_112442

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_pdr_20261104_112442`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 12.10 |
| File size (MB) | 30.06 |
| Storage rate (MB/min) | 149.12 |
| Chunk compression | none |
| Messages | 8846 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.55 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 6048 | 500.00 | 100 | 0.000 | 0.008 | 0 | 48.0 | FAIL: rate_within_20pct |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 121 | 10.00 | 10 | 0.096 | 0.104 | 0 | 29.4 | PASS |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 121 | 9.99 | 10 | 0.090 | 0.116 | 0 | 18442.6 | PASS |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 232 | 19.25 | 20 | 0.002 | 0.230 | 5 | 8.0 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 1210 | 100.00 | 100 | 0.008 | 0.012 | 0 | 259.3 | PASS |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 24 | 1.97 | 2 | 0.498 | 0.550 | 0 | 56.8 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 355 | 29.41 | 30 | 0.032 | 0.036 | 0 | 170.0 | PASS |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 24 | 1.97 | 2 | 0.498 | 0.550 | 0 | 2.9 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 121 | 9.97 | 10 | 0.092 | 0.140 | 0 | 466.1 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 232 | 19.25 | 20 | 0.002 | 0.224 | 5 | 39.3 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 355 | 29.41 | — | 0.034 | 0.034 | 0 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | — | — | 0.000 | 0.000 | — | 0.2 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 6048 messages, monotonic: **True**, max |log time − clock| = 0.004 s
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
| 0.23 | navigating |

Goal reached: **False**

Distance travelled (odometry): 2.26 m

## Process resources (24 cores; CPU % of one core)

| Process | Samples | CPU mean % | CPU max % | RSS max MB |
| --- | --- | --- | --- | --- |
| gz_bridge | 15 | 30.9 | 40.9 | 61.0 |
| navigator | 15 | 42.5 | 59.8 | 79.1 |
| recorder | 15 | 23.2 | 35.0 | 85.0 |
| rosbridge | 17 | 1.2 | 8.0 | 92.8 |

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
