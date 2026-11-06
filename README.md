# TAMU Lunabotics: Gazebo simulation + LichtBlick operator display

A trimmed copy of the TAMU Lunabotics CDH ground-station work. It contains only what's needed to:

1. run the rover's Gazebo simulation (navigation only, simulated LiDAR/camera/IMU), with Rosbridge for LichtBlick;
2. record the simulation to an MCAP file;
3. view it in the LichtBlick operator display (mission state, warnings, LiDAR, map, planned path, camera).

**Everything here is simulation-only.** Hardware stays disabled (`HARDWARE_ENABLED=0`); there is no driving or control code path to the rover. This is a staging copy; the team's main repository is the source of truth.

## What's in here

| Path | What it is |
| --- | --- |
| `02_Ground_Station_Telemetry/deliverables/lichtblick/` | **The operator display:** layout (merged with Alice Choi's dashboard), operator quickstart, test notes |
| `pdr/` | **PDR slides 9–11 package:** slide text, merge review, shot list, evidence per recording, figures |
| `02_Ground_Station_Telemetry/src/lunabotics_telemetry/` | Rosbridge launch, recording topic list, original LichtBlick layout |
| `MAIN/src/lunabotics_simulation/` | Gazebo arena world and simulation launch |
| `MAIN/src/lunabotics_autonomy/` | Autonomy package; provides the simulated navigator node |
| `01_Interfaces_Communication/src/lunabotics_interfaces/` | Gazebo ↔ ROS topic bridge config and topic list |
| `tools/` | Install, build, run and record scripts; PDR demo launcher, layout validator, MCAP verifier |
| `MAIN/profiles.json`, `MAIN/dependency-lock.json` | Build profiles and pinned LichtBlick / ROS installer versions |

Folder names match the team repo so the same commands work in both.

## Requirements

- Ubuntu 24.04 (or WSL2 on Windows) with ROS 2 Jazzy and Gazebo Harmonic
- LichtBlick 1.30.0 (Windows or Linux) for viewing

## Run the simulation

From the repo folder:

```bash
bash tools/install_dependencies.sh telemetry      # once; uses sudo apt
source /opt/ros/jazzy/setup.bash
python3 tools/build_team_workspace.py telemetry --execute   # once; builds ~/lunabotics_telemetry_ws
source ~/lunabotics_telemetry_ws/install/setup.bash
export ROS_DOMAIN_ID=84
bash tools/run_simulation.sh                      # add headless:=true if Gazebo's window won't open
```

The rover drives itself to the goal and stops. Rosbridge starts automatically at `ws://localhost:9090`.

Use the **`telemetry`** build profile. The `main` and `embedded` profiles in `profiles.json` refer to a package not included here.

## Record

**One command (recommended):** after the one-time build above,

```bash
bash tools/run_pdr_demo.sh            # --headless if Gazebo's window won't open
```

It shows a checklist (open LichtBlick, connect, start OBS), then starts the sim and the recorder together, prints SIM UP / RECORDING / GOAL REACHED / STOPPED banners, and stops everything when the rover reaches its goal. The recording goes to `~/lunabotics_recordings/SIMULATED_pdr_<time>/`, with logs and resource samples beside it.

**By hand:** in a second terminal (source both setup files and set `ROS_DOMAIN_ID=84` again):

```bash
bash tools/record_simulation.sh ~/lunabotics_recordings/SIMULATED_my_run
```

Press **Ctrl+C** to stop. Recordings are not stored in this repo (too large for GitHub). Check one with `tools/verify_mcap.py` (see `pdr/README.md`).

## View in LichtBlick

1. Install: `python3 tools/download_lichtblick.py --platform windows` (or `linux-amd64`), then run the installer.
2. Open a recording (**File → Open local file(s)…**) or the live sim (**File → Open connection… → Rosbridge → `ws://localhost:9090`**).
3. **View → Import layout from file…** → `02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json`.

Panel and warning meanings: [lichtblick_quickstart.md](02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_quickstart.md). Test results and known gaps: [test_notes.md](02_Ground_Station_Telemetry/deliverables/lichtblick/test_notes.md).

## Stop

Close LichtBlick. Press **Ctrl+C** in the simulation terminal.

## Status

- Layout validated against the sim topic list, imported in the LichtBlick 1.30.0 app (renders; UNAVAILABLE with no data), and checked against four recordings and live Rosbridge (`pdr/evidence/`). Screenshots of the app with live and replay data are still to be taken.
- The robot model uses development dimensions, not measured rover values.
- Not deployed to or tested on the rover.

Packages are Apache-2.0 (see each `package.xml`).
