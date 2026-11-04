# MCAP verification: SIMULATED_pdr_20261104_112346

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_pdr_20261104_112346`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 42.52 |
| File size (MB) | 105.63 |
| Storage rate (MB/min) | 149.05 |
| Chunk compression | none |
| Messages | 31137 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.57 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 21261 | 500.00 | 100 | 0.000 | 0.006 | 0 | 48.0 | FAIL: rate_within_20pct |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 426 | 10.00 | 10 | 0.094 | 0.106 | 0 | 29.5 | PASS |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 426 | 10.00 | 10 | 0.024 | 0.194 | 0 | 18470.3 | PASS |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 837 | 19.69 | 20 | 0.002 | 0.396 | 6 | 8.2 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 4252 | 100.00 | 100 | 0.008 | 0.012 | 0 | 259.2 | PASS |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 85 | 1.98 | 2 | 0.464 | 0.698 | 0 | 57.3 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 1250 | 29.41 | 30 | 0.034 | 0.034 | 0 | 170.3 | PASS |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 85 | 1.98 | 2 | 0.462 | 0.698 | 0 | 2.2 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 425 | 9.99 | 10 | 0.048 | 0.194 | 0 | 465.7 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 837 | 19.69 | 20 | 0.002 | 0.396 | 6 | 40.6 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1250 | 29.41 | — | 0.034 | 0.034 | 0 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | — | — | 0.000 | 0.000 | — | 0.1 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 21261 messages, monotonic: **True**, max |log time − clock| = 0.004 s
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
| 0.34 | navigating |
| 37.35 | complete |

Goal reached: **True**

Distance travelled (odometry): 5.66 m

## Live vs recording parity (Rosbridge rates vs MCAP rates)

Live window 10.0 s, tolerance ±10 % rate: **PASS**

| Topic | Live Hz | MCAP Hz | Ratio |
| --- | --- | --- | --- |
| `/clock` | 497.97 | 500.00 | 0.996 |
| `/sim/camera/camera_info` | 9.90 | 10.00 | 0.990 |
| `/sim/camera/image` | 9.90 | 10.00 | 0.990 |
| `/sim/cmd_vel` | 19.00 | 19.69 | 0.965 |
| `/sim/obstacle_grid` | 1.90 | 1.98 | 0.960 |
| `/sim/odom` | 28.30 | 29.41 | 0.962 |
| `/sim/planned_path` | 1.90 | 1.98 | 0.960 |
| `/sim/scan` | 9.60 | 9.99 | 0.961 |
| `/sim/status` | 18.80 | 19.69 | 0.955 |
| `/tf` | 28.20 | 29.41 | 0.959 |
| `/tf_static` | 0.30 | — | — |

## Replay parity

ros2 bag play on isolated ROS_DOMAIN_ID=85, re-recorded with ros2 bag record. Criteria: all topics replayed; header stamps identical; header topics lose no messages except within 1 s of either end; header-less topics keep >= 99 % of messages.

Same topics **True**, header stamps identical **True**, no interior losses **True**, header-less counts ≥ 99 % **True** → **PASS**

| Topic | Original | Replayed | Ratio | Stamps identical | Lost at edges | Lost inside |
| --- | --- | --- | --- | --- | --- | --- |
| `/clock` | 21261 | 21261 | 1.000 | — | — | — |
| `/sim/camera/camera_info` | 426 | 426 | 1.000 | 1.000 | 0 | 0 |
| `/sim/camera/image` | 426 | 426 | 1.000 | 1.000 | 0 | 0 |
| `/sim/cmd_vel` | 837 | 837 | 1.000 | — | — | — |
| `/sim/imu` | 4252 | 4252 | 1.000 | 1.000 | 0 | 0 |
| `/sim/obstacle_grid` | 85 | 85 | 1.000 | 1.000 | 0 | 0 |
| `/sim/odom` | 1250 | 1250 | 1.000 | 1.000 | 0 | 0 |
| `/sim/planned_path` | 85 | 85 | 1.000 | 1.000 | 0 | 0 |
| `/sim/scan` | 425 | 425 | 1.000 | 1.000 | 0 | 0 |
| `/sim/status` | 837 | 837 | 1.000 | — | — | — |
| `/tf` | 1250 | 1250 | 1.000 | — | — | — |

## Process resources (24 cores; CPU % of one core)

| Process | Samples | CPU mean % | CPU max % | RSS max MB |
| --- | --- | --- | --- | --- |
| gz_bridge | 45 | 31.8 | 38.8 | 58.5 |
| navigator | 45 | 40.0 | 58.7 | 78.7 |
| recorder | 45 | 22.0 | 38.0 | 84.3 |
| rosbridge | 48 | 14.0 | 71.7 | 99.8 |

## Link margin (PLACEHOLDER BUDGET)

Required (live Rosbridge, layout topics): **19.36 Mbit/s**. Assumed link: **10.00 Mbit/s** ← placeholder from `pdr/link_budget.json`, replace with Sabu+Robin's measured numbers.

Margin: -9.36 Mbit/s; utilisation 194 %.

## Plots

- `topic_rates.png`
- `xy_path.png`
- `bandwidth_per_topic.png`
- `gap_timeline.png`

## mcap CLI

```
mcap CLI not on PATH; skipped (Python mcap library used instead)
```
