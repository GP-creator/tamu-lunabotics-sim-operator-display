# PDR slides 9–11: LichtBlick (CDH ground station)

Owners: Gadadhar + Alice Choi. ~2 min per slide.

**Labels:** everything here is **SIMULATION** (live Gazebo) or **REPLAY** (MCAP of a SIMULATION run). There is no rover data until Nov 5.

**Sources:** E1 = `pdr/evidence/SIMULATED_pdr_20261104_112346/` (main run), E2 = `…/SIMULATED_pdr_20261104_112151/` (run with the NO PATH event), E3 = `…/SIMULATED_gazebo_nav_20261025_183201/`, E4 = `…/SIMULATED_pdr_20261104_112442/` (timeout test), ENV = `pdr/evidence/environment.txt`.

---

## Slide 9: LichtBlick layout and software specification

**Bullets**
- **Selected design:** LichtBlick 1.30.0 (pinned, SHA-256 checked) with one versioned layout file. Live view over Rosbridge `ws://localhost:9090`; offline replay from MCAP with no ROS needed.
- **Change since SRR:** the SRR trade study chose Dear PyGui (75 pts vs SSH/CLI 61). Reason for moving to LichtBlick: **TBD, confirm with CDH lead**. LichtBlick covers the SRR requirements we tested: ROS 2 topic subscription, image display, auto-reconnect after link loss (retries every 3 s), open source.
- **Panels:** 18 panels / 3 display-only scripts / 12 topics; every topic exists in the sim (layout validator PASS). Mission state + warnings sit in the top row.
- **Warning logic:** from `/sim/status`, LiDAR or pose older than 0.5 s, camera older than 2 s (thresholds from the autonomy code), status silent for over 1 s; obstacle stop, no path, invalid clock. Battery/E-stop/faults show **UNAVAILABLE** (no topic yet).
- **Safe by design:** display only. No Teleop/Publish panels; click-to-publish redirected to inert topics.

**Figures/tables**
- Main: `pdr/figures/layout_diagram.png` (panel → topic → type). Swap in screenshot #1 from `pdr/shot_list.md` once taken, and keep the diagram as backup.
- Small: `pdr/figures/data_path.png` (Gazebo → ros_gz_bridge → ROS 2 → rosbridge ws:9090 → LichtBlick; ROS 2 → MCAP → LichtBlick replay).
- Versions (ENV): Ubuntu 24.04.5, ROS 2 Jazzy (ros-base 0.11.0), Gazebo Harmonic (gz_sim_vendor 0.0.13), ros_gz 1.0.24, rosbridge_server 2.7.1, rosbag2 + MCAP 0.26.11, LichtBlick 1.30.0.

**Speaker notes (~2 min)**
> Our ground station is LichtBlick 1.30.0 with one layout file that we version-control. It connects live over Rosbridge, or opens a recorded MCAP file with no ROS install at all, which is how Vin can review runs on any laptop. At SRR the team picked Dear PyGui; we have since moved to LichtBlick, [reason TBD]. Against the SRR requirements, LichtBlick subscribes to ROS 2 topics directly, shows images, and reconnects on its own after a link drop. The layout puts mission state and warnings across the top, so the operator sees what the rover is doing and whether anything is wrong at a glance. Warnings come from the navigator's own status message, with the same 0.5-second staleness limits the autonomy code uses. Anything we don't have a topic for yet (battery, E-stop, faults) is shown as UNAVAILABLE rather than blank. It's display-only: no panel can send commands, and we redirected the click-to-publish tool so a stray click can't send a goal. This merges Alice's dashboard: her transform preloading, plot settings and her troubleshooting from a live test on macOS.

---

## Slide 10: LichtBlick telemetry and replay

**Bullets**
- **Live load:** LichtBlick pulls **19.36 Mbit/s** over Rosbridge (E1, `rosbridge_bandwidth.json`). The raw camera is **18.26 Mbit/s** of it; everything else is ≈ 1.1 Mbit/s (sum of the non-camera rows).
- **Link margin:** −9.36 Mbit/s against a **PLACEHOLDER 10 Mbit/s** link (E1). The number is a placeholder until Sabu + Robin's network numbers arrive. Either way, the raw camera needs compression or throttling on the rover.
- **Recording:** `ros2 bag record` (MCAP) of 12 topics at **149 MB/min** uncompressed (E1–E4 all 148.8–149.1), ≈ 8.9 GB per hour (149 × 60).
- **Replay is faithful:** replayed on an isolated ROS domain and re-recorded: same 11 topics, header stamps identical, 0 losses (E1). Live rates match the recording within 4.5 % (E1 live parity PASS, ±10 %).
- **What replay gives us:** post-run review, offline operator training on any laptop, debugging from the exact messages.

**Table: telemetry topics** (E1 `summary.md` + `rosbridge_bandwidth.json`)

| Topic | Type | Expected Hz | Recorded Hz | Live kbit/s |
| --- | --- | --- | --- | --- |
| `/sim/camera/image` | Image | 10 | 10.00 | 18,256.7 |
| `/sim/scan` | LaserScan | 10 | 9.99 | 452.1 |
| `/clock` | Clock | 100 (topics.csv) | 500.00 | 278.9 |
| `/sim/odom` | Odometry | 30 | 29.41 | 178.2 |
| `/sim/obstacle_grid` | OccupancyGrid | 2 | 1.98 | 55.5 |
| `/sim/status` | String (JSON) | 20 | 19.69 | 48.4 |
| `/sim/camera/camera_info` | CameraInfo | 10 | 10.00 | 35.2 |
| `/tf` | TFMessage | — | 29.41 | 35.2 |
| `/sim/cmd_vel` | Twist | 20 | 19.69 | 17.8 |
| `/sim/planned_path` | Path | 2 | 1.98 | 4.0 |

Also recorded but not used by the layout: `/sim/imu` (100 Hz, 259.2 kbit/s recorded), `/tf_static` (latched).

**Procedure (3 steps)**
1. `bash tools/run_pdr_demo.sh`: starts the sim and the recorder together and stops both when the goal is reached (SIM UP / RECORDING / GOAL REACHED / STOPPED banners).
2. LichtBlick → **File → Open local file(s)…** → `SIMULATED_pdr_<time>.mcap` → **View → Import layout from file…**.
3. Check it: `python3 tools/verify_mcap.py <recording> --label REPLAY` (or SIMULATION / rover label).

**Figures:** `E1/bandwidth_per_topic.png` (resource budget); screenshot #4 (replay timeline) from the shot list.

**Resources (E1 `resources.csv`, CPU % of one core, mean / max, RSS max):** rosbridge 14.0 / 71.7 %, 99.8 MB; recorder 22.0 / 38.0 %, 84.3 MB. Measured on a 24-core laptop, not the Jetson; the Jetson budget is TBD (Sameer + Zosia).

**Speaker notes (~2 min)**
> This is what the display costs. LichtBlick pulls about 19.4 megabits per second over Rosbridge, and almost all of that, 18.3, is the raw simulated camera. Everything else together is about 1.1. Against a placeholder 10-megabit link we'd be at nearly 200 percent. That number will change when Sabu and Robin give us the measured link, but the conclusion holds: the camera has to be compressed or throttled before it goes over the radio. For comparison, the SRR study budgeted about 1.3 megabits per second for its image option. Recording uses the team's standard ros2 bag recorder at about 149 megabytes a minute. Replay is faithful: we replayed a recording on an isolated ROS network and recorded it again, and every message came back with the same timestamps. That's what lets us review runs afterwards and train operators without the rover. Rosbridge and the recorder each used well under one CPU core on the laptop; we still need the Jetson numbers.

---

## Slide 11: LichtBlick run evidence

**Run metadata** (all SIMULATION; E1–E4 `summary.json`)

| Run | Date | Duration | Size | Messages | Goal | Distance | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 `SIMULATED_pdr_20261104_112346` | 2026-11-04 | 42.5 s | 105.6 MB | 31,137 | reached at 37.35 s | 5.66 m | main run; live + replay parity |
| E2 `SIMULATED_pdr_20261104_112151` | 2026-11-04 | 58.5 s | 145.0 MB | 42,751 | reached at 38.2 s | 5.66 m | real NO PATH event 19.9–20.2 s |
| E3 `SIMULATED_gazebo_nav_20261025_183201` | 2026-10-25 | 63.9 s | 158.4 MB | 46,775 | reached at 37.1 s | 5.66 m | earlier recording; replay parity |
| E4 `SIMULATED_pdr_20261104_112442` | 2026-11-04 | 12.1 s | 30.1 MB | 8,846 | not reached (5 s timeout test) | 2.26 m | launcher timeout path |

**Pass/fail** (verify_mcap.py; overall FAIL in all 4 runs, for the reasons below)

| Check | E1 | E2 | E3 | E4 |
| --- | --- | --- | --- | --- |
| Layout topics present (coverage) | PASS 100 % | PASS 100 % | PASS 100 % | PASS 100 % |
| TF tree connected, clock monotonic | PASS | PASS | PASS | PASS |
| Live vs recording rates (±10 %) | PASS | PASS | not measured | not measured |
| Replay parity (isolated domain) | PASS | PASS | PASS | not run |
| Per-topic rate within 20 % | FAIL `/clock` only | FAIL `/clock` only | FAIL `/clock` only | FAIL `/clock` only |
| No gap over 3× period | FAIL cmd_vel, status | FAIL clock, camera ×2, imu, odom (all at t ≈ 0) + cmd_vel, status | FAIL cmd_vel, status | FAIL cmd_vel, status |

**What the FAILs mean**
- `/clock` publishes at 500 Hz; `topics.csv` says 100 Hz. The config value is out of date (sent to Sabu), not a data fault.
- `/sim/cmd_vel` and `/sim/status` (20 Hz navigator timer) have gaps up to 0.396 s (E1 at 13.0 s), mostly in the first 3 s. That's below the display's 1 s STATUS STALE threshold, so no false alarm, but it's real jitter (open action).
- E2's sensor gaps all occur at t ≈ 0 (start-up); that run's recorder also logged 93 messages lost on the transport layer.

**Figures:** `E1/xy_path.png` (rover path vs planned path, start/goal), `E1/topic_rates.png`, `E2/gap_timeline.png`; screenshots #2 and #5 from the shot list.

**Nov 5 data from Vin: PLACEHOLDER**
- Label: `EXISTING-ROVER MANUAL` or `EXISTING-ROVER AUTONOMOUS` (TBD by Vin)
- Duration / size / topics / rates / coverage: TBD
- Command (rover topic names differ from `/sim/*`, so pass their expected rates if known):
  ```bash
  source /opt/ros/jazzy/setup.bash
  ~/.venvs/lunabotics-pdr/bin/python tools/verify_mcap.py /path/to/vin_nov5.mcap \
      --label "EXISTING-ROVER MANUAL" --name ROVER_nov5 \
      [--expected-rates rover_rates.csv] [--replay-parity]
  ```
  Expect layout coverage below 100 % until real topic names are added to `rover_only_topics.txt` and the layout.

**Speaker notes (~2 min)**
> Here's the evidence, all from simulation. Four recordings, three of them full runs: the rover reaches the goal at about 37 seconds every time, 5.66 metres travelled. Every topic the layout needs is in every recording, the transform tree is connected, the clock is clean, and replay reproduces the recording exactly. The plot shows the rover's odometry path against the planner's path from start to goal. The checker is strict and marks every run FAIL, for two real reasons we're reporting rather than hiding. First, the topic list says the simulation clock runs at 100 Hz, but it runs at 500. That's a documentation fix. Second, the navigator's 20 Hz status occasionally pauses for up to 0.4 seconds, mostly at start-up. It's below our 1-second stale threshold, but we'll track it. In one run the planner briefly lost its path for 0.3 seconds, and the display turned red with NO PATH, which shows the warning logic on a real event. On Nov 5 Vin gives us real rover data and we rerun the same tool on it; that's this placeholder.

---

## Open actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Take screenshots #1–#8 (shot list) from the OBS run and LichtBlick, and do a visual check of the merged layout with live/replay data in the app (layout import already verified) | Gadadhar |
| 2 | Confirm and state the reason for switching from Dear PyGui (SRR) to LichtBlick | CDH lead (TBD) |
| 3 | Measured rover ↔ operator bandwidth/latency to replace the 10 Mbit/s placeholder (slides 6–8) | Sabu + Robin |
| 4 | Camera compression/throttling plan (raw camera is 18.26 Mbit/s of 19.36) | Sabu + Robin, Gadadhar |
| 5 | Real Unitree L2 LiDAR and Orbbec topic names/types/rates → `rover_only_topics.txt` and layout | Sabu + Robin |
| 6 | Real rover dimensions for the footprint (now 0.65 × 0.45 m sim values) | Vin / Sameer + Zosia |
| 7 | Jetson compute and storage budget (rosbridge + recorder measured only on a laptop) | Sameer + Zosia |
| 8 | Fix `/clock` expected rate in `topics.csv` (100 → measured 500 Hz in sim) | Sabu |
| 9 | Navigator 20 Hz timer jitter (gaps up to 0.396 s) | GNC / MAIN (TBD) |
| 10 | Run `verify_mcap.py` on Vin's Nov 5 data and fill the slide 11 placeholder | Gadadhar + Alice |
| 11 | Keyboard-control prototype (separate from this display-only work) | Gadadhar (later) |
| 12 | Battery, E-stop and fault topics so those panels stop showing UNAVAILABLE | Embedded (TBD) |
