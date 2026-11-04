# Screenshot manifest: PDR slides 9–11

**Main run:** `SIMULATED_pdr_20261104_124956` (2026-11-04). The OBS video and the MCAP evidence are the **same run**. It ran with Gazebo GUI + LichtBlick + OBS on one laptop (desktop load). Evidence: `pdr/evidence/SIMULATED_pdr_20261104_124956/`.

Labels: **SIMULATION** = live Gazebo (or its terminal/recording metadata); **REPLAY** = the MCAP played back in LichtBlick. Times in REPLAY rows are recording (simulation) time, 0.004–42.876 s for the main run.

## Video

| File | Run | Label | What it shows / proves | Slide |
| --- | --- | --- | --- | --- |
| OBS video (your file name) | `SIMULATED_pdr_20261104_124956` | SIMULATION | One-command run end to end: checklist, SIM UP 12:50:07, RECORDING 12:50:07, GOAL REACHED 12:50:42, STOPPED + MCAP SAVED 12:50:50; LichtBlick live over `ws://localhost:9090` | 10 (link or backup) |

## Screenshots

| File | Run | Label | Taken from | Moment | Proves | Slide |
| --- | --- | --- | --- | --- | --- | --- |
| `01_live_navigating.png` | 124956 | SIMULATION | OBS video frame | A few seconds after the RECORDING banner (12:50:07–12:50:15), rover driving | Whole display working live over Rosbridge: mission state, warnings, origin, health row, map with LiDAR/path/footprint, camera | 9 (main figure) |
| `02_live_goal_reached.png` | 124956 | SIMULATION | OBS video frame | Just after the GOAL REACHED banner (12:50:42) | MISSION STATE turns COMPLETE live, matching the navigator | 11 (optional) |
| `03_terminal_banners.png` | 124956 | SIMULATION | Terminal: `banners.log` (Step 2) | After the run | Timestamped SIM UP / RECORDING / GOAL REACHED / STOPPED / MCAP SAVED; one command, clean stop | 10 |
| `09_bag_info.png` | 124956 | SIMULATION | Terminal: `ros2 bag info` (Step 3) | After the run | The recording exists: 42.872 s, 31,335 messages, 12 topics, 101.5 MiB MCAP | 10 |
| `04_replay_mid_drive.png` | 124956 | REPLAY | LichtBlick, `SIMULATED_pdr_20261104_124956_0.mcap` (Step 4) | **7.0 s** (6.0–8.0 s): NAVIGATING, 0.34 m/s, 2.69 m planned path visible | Offline replay without ROS, all panels populated, playback bar | 10 |
| `05_replay_goal_reached.png` | 124956 | REPLAY | LichtBlick, same MCAP (Step 4) | **38.0 s** (COMPLETE from 37.65 s; 37.7 s if the cyan path should still show) | Goal reached in the recording; rover stopped at (6.16, 3.10) | 11 |
| `06_replay_no_path_warning.png` | `SIMULATED_pdr_20261104_112151` | REPLAY | LichtBlick, `SIMULATED_pdr_20261104_112151_0.mcap` (Step 5) | **20.05 s** (NO PATH shown 19.926 s to just before 20.212 s) | Warning logic on a real (simulated) planner event: red NO PATH while sensors stay fresh | 9 (also 11) |
| `07_details_rover_only.png` | 124956 | SIMULATION or REPLAY | LichtBlick Details tab (OBS frame or replay) | Any time | Battery / E-stop / Faults shown as **Rover-only (not in simulation): UNAVAILABLE**, not blank | 9 (optional) |
| `08_details_raw_status.png` | 124956 | SIMULATION or REPLAY | LichtBlick Details tab | Any time | Raw `/sim/status` with `"source": "gazebo_simulation"`: source labelled at data level | 10 (optional) |

## Figures and plots (generated from files, no screenshot needed)

| File | Source | Label | Slide |
| --- | --- | --- | --- |
| `pdr/figures/layout_diagram.png` | `lichtblick_layout.json` | — (design) | 9 |
| `pdr/figures/data_path.png` | design | — | 9 |
| `pdr/evidence/SIMULATED_pdr_20261104_124956/bandwidth_per_topic.png` | main run | SIMULATION | 10 |
| `pdr/evidence/SIMULATED_pdr_20261104_124956/xy_path.png` | main run | SIMULATION | 11 |
| `pdr/evidence/SIMULATED_pdr_20261104_124956/topic_rates.png` | main run | SIMULATION | 11 (optional) |
| `pdr/evidence/SIMULATED_pdr_20261104_124956/gap_timeline.png` | main run | SIMULATION | 11 (optional) |

## Other existing images

- `pdr/evidence/LICHTBLICK_APP_layout_import_2026-11-04/merged_layout_no_data_unavailable.png`: no data; taken before the layout revision. Backup only.
- `pdr/evidence/SIMULATION_alice_live_2026-11-01/lichtblick_dashboard.png`: Alice Choi's live session, pre-merge layout (SIMULATION). Credit Alice if used.

## Notes

- `01`/`02` OBS-frame times are wall-clock from `banners.log`. The mapping from wall clock to recording time is approximate: recording time 0 ≈ 12:50:01–12:50:03.
- Desktop load: this run's navigator gaps (up to 0.668 s) and the WAITING FOR SENSORS blip at 15.83–15.92 s happened with GUI + LichtBlick + OBS running. They are not representative of the rover (see slide 11).
- Rosbridge CPU in this run is reported as **LichtBlick + measurement probe** (≈ 114 % of one core while both were connected, ≈ 107 % with LichtBlick alone).
