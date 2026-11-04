# MCAP verification: SIMULATED_gazebo_nav_20261025_183201

**Run label: SIMULATION**  
Recording: `/home/gadhai3/lunabotics_recordings/SIMULATED_gazebo_nav_20261025_183201`  
Overall: **FAIL**

## Recording

| Item | Value |
| --- | --- |
| Duration (s) | 63.86 |
| File size (MB) | 158.42 |
| Storage rate (MB/min) | 148.84 |
| Chunk compression | none |
| Messages | 46775 |
| Topics | 12 |
| Recorded payload rate (Mbit/s) | 19.55 |
| Time base | simulation time (starts near 0) |

## Per-topic checks

| Topic | Schema | Count | Mean Hz | Expected Hz | Min gap s | Max gap s | Gaps >3x | kbit/s | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | 31931 | 500.00 | 100 | 0.000 | 0.008 | 0 | 48.0 | FAIL: rate_within_20pct |
| `/sim/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 639 | 10.00 | 10 | 0.096 | 0.104 | 0 | 29.5 | PASS |
| `/sim/camera/image` | `sensor_msgs/msg/Image` | 639 | 10.00 | 10 | 0.030 | 0.194 | 0 | 18447.5 | PASS |
| `/sim/cmd_vel` | `geometry_msgs/msg/Twist` | 1263 | 19.78 | 20 | 0.002 | 0.242 | 6 | 8.2 | FAIL: no_gap_over_3x_period |
| `/sim/imu` | `sensor_msgs/msg/Imu` | 6386 | 100.00 | 100 | 0.008 | 0.012 | 0 | 259.2 | PASS |
| `/sim/obstacle_grid` | `nav_msgs/msg/OccupancyGrid` | 128 | 1.99 | 2 | 0.380 | 0.818 | 0 | 57.4 | PASS |
| `/sim/odom` | `nav_msgs/msg/Odometry` | 1878 | 29.41 | 30 | 0.030 | 0.038 | 0 | 170.3 | PASS |
| `/sim/planned_path` | `nav_msgs/msg/Path` | 128 | 1.99 | 2 | 0.380 | 0.818 | 0 | 1.6 | PASS |
| `/sim/scan` | `sensor_msgs/msg/LaserScan` | 639 | 9.99 | 10 | 0.060 | 0.194 | 0 | 466.2 | PASS |
| `/sim/status` | `std_msgs/msg/String` | 1263 | 19.78 | 20 | 0.000 | 0.240 | 6 | 40.8 | FAIL: no_gap_over_3x_period |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1878 | 29.41 | — | 0.030 | 0.038 | 0 | 23.5 | PASS |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 3 | — | — | 0.000 | 0.000 | — | 0.0 | PASS |

First/last timestamps per topic are in `summary.json`.

## Layout coverage

10/10 topics the LichtBlick layout needs are present (**100 %**).

## TF and clock

- `/clock`: 31931 messages, monotonic: **True**, max |log time − clock| = 0.006 s
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
| 0.39 | navigating |
| 1.24 | waiting_for_sensors |
| 1.40 | navigating |
| 37.09 | complete |

Goal reached: **True**

Distance travelled (odometry): 5.66 m

## Replay parity

ros2 bag play on isolated ROS_DOMAIN_ID=85, re-recorded with ros2 bag record. Criteria: all topics replayed; header stamps identical; header topics lose no messages except within 1 s of either end; header-less topics keep >= 99 % of messages.

Same topics **True**, header stamps identical **True**, no interior losses **True**, header-less counts ≥ 99 % **True** → **PASS**

| Topic | Original | Replayed | Ratio | Stamps identical | Lost at edges | Lost inside |
| --- | --- | --- | --- | --- | --- | --- |
| `/clock` | 31931 | 31931 | 1.000 | — | — | — |
| `/sim/camera/camera_info` | 639 | 639 | 1.000 | 1.000 | 0 | 0 |
| `/sim/camera/image` | 639 | 639 | 1.000 | 1.000 | 0 | 0 |
| `/sim/cmd_vel` | 1263 | 1263 | 1.000 | — | — | — |
| `/sim/imu` | 6386 | 6386 | 1.000 | 1.000 | 0 | 0 |
| `/sim/obstacle_grid` | 128 | 128 | 1.000 | 1.000 | 0 | 0 |
| `/sim/odom` | 1878 | 1878 | 1.000 | 1.000 | 0 | 0 |
| `/sim/planned_path` | 128 | 128 | 1.000 | 1.000 | 0 | 0 |
| `/sim/scan` | 639 | 639 | 1.000 | 1.000 | 0 | 0 |
| `/sim/status` | 1263 | 1263 | 1.000 | — | — | — |
| `/tf` | 1878 | 1878 | 1.000 | — | — | — |

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
