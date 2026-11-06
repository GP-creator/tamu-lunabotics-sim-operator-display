# MCAP verification: SIMULATED_pdr_20261104_124956

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_pdr_20261104_124956`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 42.87 |
| File size (MB) | 106.37 |
| Storage rate (MB/min) | 148.87 |
| Chunk compression | none |
| Messages | 31335 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.55 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 21436 | 500.00 | 100 | 0.000 | 0.034 | 3 | 48.0 | FAIL: rate_within_20pct, no_gap_over_3x_period |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 429 | 10.00 | 10 | 0.074 | 0.128 | 0 | 29.5 | PASS |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 429 | 9.99 | 10 | 0.086 | 0.124 | 0 | 18448.5 | PASS |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 815 | 19.02 | 20 | 0.000 | 0.668 | 8 | 7.9 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 4287 | 100.00 | 100 | 0.000 | 0.056 | 2 | 259.2 | FAIL: no_gap_over_3x_period |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 85 | 1.98 | 2 | 0.120 | 0.830 | 0 | 56.8 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 1261 | 29.41 | 30 | 0.004 | 0.064 | 0 | 170.4 | PASS |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 85 | 1.98 | 2 | 0.118 | 0.832 | 0 | 2.1 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 429 | 9.98 | 10 | 0.032 | 0.168 | 0 | 466.2 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 815 | 19.02 | 20 | 0.000 | 0.666 | 8 | 39.1 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1261 | 29.41 | — | 0.004 | 0.064 | 0 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | — | — | 0.000 | 0.000 | — | 0.1 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 21436 messages, monotonic: **True**, max |log time − clock| = 0.064 s
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
| 1.86 | navigating |
| 1.87 | waiting_for_sensors |
| 2.21 | navigating |
| 15.83 | waiting_for_sensors |
| 15.92 | navigating |
| 37.65 | complete |

Goal reached: **True**

Distance travelled (odometry): 5.67 m

## Live vs recording parity (Rosbridge rates vs MCAP rates)

Live window 10.0 s, tolerance ±10 % rate: **FAIL**

| Topic | Live Hz | MCAP Hz | Ratio |
| --- | --- | --- | --- |
| `/clock` | 434.12 | 500.00 | 0.868 |
| `/sim/camera/camera_info` | 9.90 | 10.00 | 0.990 |
| `/sim/camera/image` | 9.80 | 9.99 | 0.980 |
| `/sim/cmd_vel` | 18.80 | 19.02 | 0.988 |
| `/sim/obstacle_grid` | 1.90 | 1.98 | 0.961 |
| `/sim/odom` | 28.79 | 29.41 | 0.979 |
| `/sim/planned_path` | 1.90 | 1.98 | 0.961 |
| `/sim/scan` | 9.80 | 9.98 | 0.981 |
| `/sim/status` | 18.80 | 19.02 | 0.988 |
| `/tf` | 28.59 | 29.41 | 0.972 |
| `/tf_static` | 0.10 | — | — |

## Replay parity

ros2 bag play on isolated ROS_DOMAIN_ID=85, re-recorded with ros2 bag record. Criteria: all topics replayed; header stamps identical; header topics lose no messages except within 1 s of either end; header-less topics keep >= 99 % of messages.

Same topics **True**, header stamps identical **True**, no interior losses **True**, header-less counts ≥ 99 % **True** → **PASS**

| Topic | Original | Replayed | Ratio | Stamps identical | Lost at edges | Lost inside |
| --- | --- | --- | --- | --- | --- | --- |
| `/clock` | 21436 | 21436 | 1.000 | — | — | — |
| `/sim/camera/camera_info` | 429 | 429 | 1.000 | 1.000 | 0 | 0 |
| `/sim/camera/image` | 429 | 429 | 1.000 | 1.000 | 0 | 0 |
| `/sim/cmd_vel` | 815 | 815 | 1.000 | — | — | — |
| `/sim/imu` | 4287 | 4287 | 1.000 | 1.000 | 0 | 0 |
| `/sim/obstacle_grid` | 85 | 85 | 1.000 | 1.000 | 0 | 0 |
| `/sim/odom` | 1261 | 1261 | 1.000 | 1.000 | 0 | 0 |
| `/sim/planned_path` | 85 | 85 | 1.000 | 1.000 | 0 | 0 |
| `/sim/scan` | 429 | 429 | 1.000 | 1.000 | 0 | 0 |
| `/sim/status` | 815 | 815 | 1.000 | — | — | — |
| `/tf` | 1261 | 1261 | 1.000 | — | — | — |

## Process resources (24 cores; CPU % of one core)

| Process | Samples | CPU mean % | CPU max % | RSS max MB |
| --- | --- | --- | --- | --- |
| gazebo | 46 | 221.3 | 253.4 | 587.1 |
| gz_bridge | 46 | 50.6 | 59.9 | 60.9 |
| navigator | 46 | 70.5 | 101.2 | 79.2 |
| recorder | 46 | 35.7 | 43.8 | 84.9 |
| rosbridge | 46 | 102.7 | 115.6 | 100.6 |

## Link margin (PLACEHOLDER BUDGET)

Required (live Rosbridge, layout topics): **19.15 Mbit/s**. Assumed link: **10.00 Mbit/s** ← placeholder from `pdr/link_budget.json`, replace with Sabu+Robin's measured numbers.

Margin: -9.15 Mbit/s; utilisation 192 %.

## Plots

- `topic_rates.png`
- `xy_path.png`
- `bandwidth_per_topic.png`
- `gap_timeline.png`

## mcap CLI

```
mcap CLI not on PATH; skipped (Python mcap library used instead)
```
