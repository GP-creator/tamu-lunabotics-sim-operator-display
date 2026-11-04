# LichtBlick operator display

Owner: Gadadhar, merged with Alice Choi's dashboard (PR #4; see `pdr/merge_review.md`). Data: **simulated only** (Gazebo). Not tested on the rover.

| File | What it is |
| --- | --- |
| `lichtblick_layout.json` | LichtBlick 1.30.0 layout. Import with **View → Import layout from file…** |
| `operator_quickstart.md` | Step-by-step guide for Vin: open, read, stop |
| `test_notes.md` | What was tested, how, results, known gaps |
| `screenshots/` | Screenshots; `screenshots/TO_CAPTURE.md` lists what to capture |
| `test_output/` | Script test output and recording details (not named `evidence/`, which the team repo's `.gitignore` excludes) |
| `rover_only_topics.txt` | Topics only the real rover publishes (empty until real topic names are known) |

Check the layout with `python3 tools/validate_layout.py`: every topic must be sim-available, rover-only (listed above) or a script output.

## Open

- **Recording:** LichtBlick → **File → Open local file(s)…** → a `SIMULATED_*.mcap` from `~/lunabotics_recordings/` on Gadadhar's laptop (not in the repo; 100+ MB each). Make a new one with `bash tools/run_pdr_demo.sh`. Verified recordings are listed in `pdr/evidence/`.
- **Live simulation:** start it (below), then **File → Open connection… → Rosbridge →** `ws://localhost:9090`.

Then import `lichtblick_layout.json`. Full steps are in `operator_quickstart.md`.

## Run the simulation (Ubuntu 24.04 / WSL)

From the repo folder:

```bash
source /opt/ros/jazzy/setup.bash
source ~/lunabotics_telemetry_ws/install/setup.bash
export ROS_DOMAIN_ID=84
bash tools/run_simulation.sh
```

First-time setup (install and build) is in `02_Ground_Station_Telemetry/README.md`. To record a new sample, run `bash tools/record_simulation.sh` in a second sourced terminal and press **Ctrl+C** to stop.

## Stop

Close LichtBlick. Press **Ctrl+C** in the simulation terminal.

## How the layout works

The layout includes three LichtBlick User Scripts. They run inside LichtBlick and publish nothing to ROS:

- `mission_status` reads the JSON in `/sim/status` and works out the mission state, data origin and one warning. It uses `/tf` as a heartbeat to detect a silent status topic.
- `camera_health` marks the camera stale after 2 s without an image.
- `rover_footprint` draws the simulated chassis box on `base_link`.

The 3D and camera panels' click-to-publish targets point at unused `/operator_display/click_disabled/*` topics, so a stray click cannot send a navigation goal.

The original `src/lunabotics_telemetry/layouts/simulation.json` is unchanged.
