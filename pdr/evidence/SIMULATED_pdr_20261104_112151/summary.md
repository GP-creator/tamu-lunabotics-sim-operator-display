# MCAP verification: SIMULATED_pdr_20261104_112151

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_pdr_20261104_112151`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 58.47 |
| File size (MB) | 145.03 |
| Storage rate (MB/min) | 148.82 |
| Chunk compression | none |
| Messages | 42751 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.55 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 29160 | 498.68 | 100 | 0.000 | 0.164 | 1 | 47.9 | FAIL: rate_within_20pct, no_gap_over_3x_period |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 585 | 10.00 | 10 | 0.000 | 0.912 | 1 | 29.5 | FAIL: no_gap_over_3x_period |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 585 | 10.00 | 10 | 0.000 | 0.352 | 1 | 18444.7 | FAIL: no_gap_over_3x_period |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 1165 | 19.93 | 20 | 0.000 | 0.284 | 3 | 8.3 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 5831 | 99.73 | 100 | 0.000 | 0.262 | 1 | 258.5 | FAIL: no_gap_over_3x_period |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 117 | 1.99 | 2 | 0.464 | 0.582 | 0 | 57.3 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 1719 | 29.41 | 30 | 0.000 | 0.326 | 1 | 170.3 | FAIL: no_gap_over_3x_period |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 117 | 1.99 | 2 | 0.464 | 0.584 | 0 | 1.7 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 585 | 9.99 | 10 | 0.040 | 0.212 | 0 | 466.1 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 1165 | 19.93 | 20 | 0.000 | 0.284 | 3 | 41.0 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1719 | 29.41 | — | 0.000 | 0.326 | 1 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | 1000.00 | — | 0.000 | 0.002 | — | 0.0 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 29160 messages, monotonic: **True**, max |log time − clock| = 0.048 s
- TF root: `odom`; all message frames connected: **True**
  - `/sim/camera/camera_info` frame `camera_link` → root `odom`
  - `/sim/camera/image` frame `camera_link` → root `odom`
  - `/sim/scan` frame `base_scan` → root `odom`
  - `/sim/imu` frame `imu_link` → root `odom`
  - `/sim/odom` frame `odom` → root `odom`
  - `/sim/obstacle_grid` frame `odom` → root `odom`
  - `/sim/planned_path` frame `odom` → root `odom`

## Mission state timeline (`/sim/status`, source `gazebo_simulation`)

| t (s) | State |
| --- | --- |
| 0.04 | waiting_for_sensors |
| 0.33 | navigating |
| 19.92 | no_observed_path |
| 20.21 | navigating |
| 38.20 | complete |

Goal reached: **True**

Distance travelled (odometry): 5.66 m

## Live vs recording parity (Rosbridge rates vs MCAP rates)

Live window 10.0 s, tolerance ±10 % rate: **PASS**

| Topic | Live Hz | MCAP Hz | Ratio |
| --- | --- | --- | --- |
| `/clock` | 499.63 | 498.68 | 1.002 |
| `/sim/camera/camera_info` | 9.90 | 10.00 | 0.990 |
| `/sim/camera/image` | 9.90 | 10.00 | 0.990 |
| `/sim/cmd_vel` | 19.60 | 19.93 | 0.983 |
| `/sim/obstacle_grid` | 1.90 | 1.99 | 0.954 |
| `/sim/odom` | 28.80 | 29.41 | 0.979 |
| `/sim/planned_path` | 1.90 | 1.99 | 0.954 |
| `/sim/scan` | 9.70 | 9.99 | 0.970 |
| `/sim/status` | 19.40 | 19.93 | 0.973 |
| `/tf` | 28.70 | 29.41 | 0.976 |
| `/tf_static` | 0.30 | 1000.00 | 0.000 |

## Replay parity

ros2 bag play on isolated ROS_DOMAIN_ID=85, re-recorded with ros2 bag record. Criteria: all topics replayed; header stamps identical; header topics lose no messages except within 1 s of either end; header-less topics keep >= 99 % of messages.

Same topics **True**, header stamps identical **True**, no interior losses **True**, header-less counts ≥ 99 % **True** → **PASS**

| Topic | Original | Replayed | Ratio | Stamps identical | Lost at edges | Lost inside |
| --- | --- | --- | --- | --- | --- | --- |
| `/clock` | 29160 | 29160 | 1.000 | — | — | — |
| `/sim/camera/camera_info` | 585 | 585 | 1.000 | 1.000 | 0 | 0 |
| `/sim/camera/image` | 585 | 585 | 1.000 | 1.000 | 0 | 0 |
| `/sim/cmd_vel` | 1165 | 1165 | 1.000 | — | — | — |
| `/sim/imu` | 5831 | 5831 | 1.000 | 1.000 | 0 | 0 |
| `/sim/obstacle_grid` | 117 | 117 | 1.000 | 1.000 | 0 | 0 |
| `/sim/odom` | 1719 | 1719 | 1.000 | 1.000 | 0 | 0 |
| `/sim/planned_path` | 117 | 117 | 1.000 | 1.000 | 0 | 0 |
| `/sim/scan` | 585 | 585 | 1.000 | 1.000 | 0 | 0 |
| `/sim/status` | 1165 | 1165 | 1.000 | — | — | — |
| `/tf` | 1719 | 1719 | 1.000 | — | — | — |

## Process resources (24 cores; CPU % of one core)

| Process | Samples | CPU mean % | CPU max % | RSS max MB |
| --- | --- | --- | --- | --- |
| gz_bridge | 61 | 29.4 | 33.9 | 58.8 |
| navigator | 61 | 35.5 | 58.8 | 78.8 |
| recorder | 63 | 19.1 | 33.0 | 85.3 |
| rosbridge | 61 | 9.4 | 68.7 | 93.5 |

## Link margin (PLACEHOLDER BUDGET)

Required (live Rosbridge, layout topics): **19.37 Mbit/s**. Assumed link: **10.00 Mbit/s** ← placeholder from `pdr/link_budget.json`, replace with Sabu+Robin's measured numbers.

Margin: -9.37 Mbit/s; utilisation 194 %.

## Plots

- `topic_rates.png`
- `xy_path.png`
- `bandwidth_per_topic.png`
- `gap_timeline.png`

## mcap CLI

```
mcap CLI not on PATH; skipped (Python mcap library used instead)
```
