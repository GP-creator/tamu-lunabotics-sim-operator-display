# LichtBlick quickstart: CDH-S2 display/recorder element

This display shows the rover's mission state, warnings, connection state, LiDAR, camera, map and planned path in LichtBlick. It only displays data. It has no driving or control panels and does not send commands.

All data so far is **SIMULATION** (live Gazebo) or **REPLAY** (a recording of it). Nothing here comes from the real rover yet.

## 0. Versions

| Part | Version | Source |
| --- | --- | --- |
| LichtBlick desktop app | **1.30.0** (pinned, SHA-256 checked) | `MAIN/dependency-lock.json` |
| LichtBlick web (lichtblick-suite.github.io) | **unknown** (not checked; see Help → About) | not pinned; may differ from 1.30.0 |
| Rosbridge (`rosbridge_server`) | 2.7.1 | `pdr/evidence/environment.txt` |
| ROS 2 | Jazzy (ros-base 0.11.0), Ubuntu 24.04 / WSL2 | same |
| Gazebo | Harmonic (gz_sim_vendor 0.0.13), ros_gz 1.0.24 | same |
| Recorder | rosbag2 0.26.11, MCAP storage | same |

The layouts are tested against 1.30.0. If the web app's About shows another version, prefer the desktop app.

## 1. Install LichtBlick (once)

On Windows, open PowerShell in the repo folder and run:

```powershell
py tools/download_lichtblick.py --platform windows
```

Run the installer from your Downloads folder.

## 2. Live connection

**Start-up order** (either order works; LichtBlick retries):

1. In LichtBlick: **File → Open connection… → Rosbridge**, enter `ws://localhost:9090`, **Open**. If nothing is running yet it shows "Waiting for connection…" and retries every 3 s.
2. In Ubuntu (WSL), from the repo folder: `bash tools/run_pdr_demo.sh` (add `--headless` if Gazebo's window will not open). Press Enter when asked. The simulation and recorder start together; the rover drives itself to the goal; everything stops by itself. The last line must be the blue **MCAP SAVED** banner.

**Reconnect:** if the connection drops, LichtBlick reconnects by itself every 3 s once Rosbridge is back. To force it: **File → Open connection… → Rosbridge** again.

**Another computer:** `ws://<ubuntu-ip>:9090` only works if Rosbridge listens on that network. The team launch binds `127.0.0.1` (this computer only), so remote viewing needs a launch change. Alice used a temporary bridge on her VM's address for her macOS test.

## 3. Import the layout (once per computer)

1. **View → Import layout from file…**
2. Choose:
   - `lichtblick_layout.json` for the `/sim/*` simulation and its recordings; or
   - `lichtblick_layout_gnc2027.json` for the GNC team's topics (see `HANDOFF_GNC2027_for_Alice.md`).

With the **web** app, copy the file to a normal Windows folder first. The browser refuses to open files from `\\wsl$\…` ("contains system files").

The **Operator** tab opens. The **Details** tab has the raw status message, the topic list and the rover-only indicators.

## 4. What each panel means

**Top row:** check these first.

| Panel | Shows |
| --- | --- |
| **MISSION STATE** | What the navigator is doing: NAVIGATING (green), COMPLETE (blue), PAUSED or WAITING FOR SENSORS (yellow), OBSTACLE STOP, NO PATH, INVALID CLOCK or STATE NOT CURRENT (red). |
| **WARNINGS** | The most important current problem, or "No warnings" (green). See section 5. |
| **DATA ORIGIN** | **SIMULATED (Gazebo)** in purple when the data is labelled as simulated. Yellow means the source is not labelled. |

**Second row:**

| Panel | Shows |
| --- | --- |
| **CONNECTION** | The data source: `ws://localhost:9090` (live) or the `.mcap` file name (replay). Shows **"Waiting for connection…"** when the live link is lost. |
| **LiDAR / Pose / Camera / Status link lights** | Green = fresh, red = stale, grey = no data. |

**Middle:**

| Panel | Shows |
| --- | --- |
| **Map, planned path, LiDAR** | The largest panel: a top-down view of the whole arena (1 m grid). Red dots: LiDAR hits. Orange cells: obstacles seen. Faint green cells: seen free space. Cyan line: planned path. Orange box: rover (simulated chassis size). Scroll to zoom, drag to move; the **3D** button on the panel's right edge tilts the view. |
| **Camera** | The rover's front camera. |

**Bottom:**

| Panel | Shows |
| --- | --- |
| **Mission state and warnings over time** | Timeline of state and warning changes. |
| **Data age** | How old each input is, in seconds. |
| **Commanded speed** | Speed and turn rate the navigator is **commanding**, not measured speed. Flat after COMPLETE is normal. |

The plots start with their legend hidden; click the list icon in the plot's corner to show it.

**Details tab:** raw `/sim/status`, the data source's topic list, and **Rover-only (not in simulation): Battery / E-stop / Faults**, which are always grey UNAVAILABLE because no topic exists yet.

Which topic feeds each panel: `panel_topics.md` (GNC version: `panel_topics_gnc2027.md`).

## 5. Warnings and lost data

| Warning | Meaning | Check |
| --- | --- | --- |
| No warnings | Status, LiDAR and pose are fresh; navigator reports no problem. | — |
| STATUS STALE | No `/sim/status` for over 1 s. Mission state is out of date. | Is the simulation still running? |
| STATUS UNREADABLE | `/sim/status` arrived but could not be read. | Report to CDH. |
| LIDAR STALE/MISSING | No LiDAR scan within 0.5 s. | LiDAR light, Data age. |
| POSE STALE/MISSING | No position update within 0.5 s. | Pose light, Data age. |
| OBSTACLE STOP | Navigator stopped because an obstacle is too close. | Map. |
| NO PATH | Planner cannot find a route to the goal. | Map. |
| INVALID CLOCK | Simulation time is invalid. | Restart the simulation. |
| WAITING | Navigator waiting for its first LiDAR and pose data (normal for ~1 s at start). | — |
| PAUSED | Simulated navigation paused with `/sim/pause`. | — |
| SOURCE NOT LABELLED SIMULATED | Status data does not say it is simulated; treat as unverified. | Data origin. |

**If the whole connection drops, every other panel keeps its last value**, and the lights can stay green. Only the **CONNECTION** panel ("Waiting for connection…") and LichtBlick's app bar (spinner, red error, "Connection failed" alert) show it. **Always check CONNECTION before trusting the lights.** Fault tests: script ready (`tools/fault_test.sh`), visual test PENDING; see `pdr/evidence/fault_tests.md`.

## 6. Recording workflow

- **One command:** `bash tools/run_pdr_demo.sh` records automatically to `~/lunabotics_recordings/SIMULATED_pdr_<time>/`, with logs, resource samples and Rosbridge bandwidth in `…_logs/`. It ends with **MCAP SAVED <path>** or a red **NO MCAP SAVED** banner (exit code 3).
- **By hand** (sim already running, second sourced terminal):
  ```bash
  bash 02_Ground_Station_Telemetry/deliverables/lichtblick/record_replay.sh record ~/lunabotics_recordings/SIMULATED_my_run
  ```
  Ctrl+C stops it. Topics: `topics_to_record.txt` (same list as `02_Ground_Station_Telemetry/src/lunabotics_telemetry/config/topics_to_record.txt`).
- **Check a recording:** `record_replay.sh info <bag>` and `record_replay.sh verify <bag> SIMULATION`.

## 7. Offline replay

**A. Open the file (no ROS needed)**
1. Copy the `.mcap` to a normal Windows folder (the web app cannot read `\\wsl$`).
2. **File → Open local file(s)…** → the `.mcap`. Import the layout if needed.
3. Press play. The clock may show **1 January 1970**: recordings use simulation time, which starts at 0.

**B. Replay through ROS (`ros2 bag play`)**: e.g. to test live-only behaviour. Stop any live simulation first.
```bash
bash 02_Ground_Station_Telemetry/deliverables/lichtblick/record_replay.sh replay ~/lunabotics_recordings/SIMULATED_pdr_20261104_124956
```
This starts Rosbridge and plays the bag with `--clock`. In LichtBlick, connect to `ws://localhost:9090` as in section 2. Ctrl+C stops both.

Where the shared recordings live and how to check their checksums: `pdr/evidence_location.md`.

## 8. Troubleshooting

| Symptom | Do this |
| --- | --- |
| Nothing updates | Look at **CONNECTION**. "Waiting for connection…" means Rosbridge is down: is the simulation running? Otherwise check the address is `ws://localhost:9090`. |
| 3D panel: `Missing transform from frame <base_scan> to frame <base_link>` | Wait a few seconds after start-up, then **File → Open connection… → Rosbridge** again (Alice's workaround; cause not confirmed). |
| Camera frozen or blank | Check the Camera light: red = stale, grey = no data. The image itself does not show staleness. |
| Speed plot flat | Check MISSION STATE; after COMPLETE the rover is meant to stop. |
| "Can't open this file … contains system files" | Web app and `\\wsl$`: copy the file to Downloads first, or use the desktop app. |
| Launcher: "Port 9090 is already in use" | Another simulation or Rosbridge is running; stop it (Ctrl+C in its terminal). |
| Launcher ends with red **NO MCAP SAVED** | That take was not recorded; see `…_logs/recorder.log` and run again. |
| Battery / E-stop / Faults grey (Details tab) | Expected: no input exists yet. |

## 9. Stop and close

1. Close LichtBlick. This only stops **viewing**; it does not stop the simulation or a robot.
2. Simulation: Ctrl+C in its Ubuntu terminal (the launcher stops by itself). This is not an emergency stop for real hardware.

## 10. macOS

- **Replay works directly on a Mac:** install LichtBlick for macOS, then **File → Open local file(s)…** → the `.mcap`, and **View → Import layout from file…**. No ROS needed. `tools/download_lichtblick.py` only pins Windows/Linux installers, so get the macOS build of the same version (1.30.0) from the LichtBlick GitHub releases page; it has no pinned checksum here.
- **The simulation needs Linux** (Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic): a Linux VM (Alice's UTM setup needed Ogre workarounds) or Gadadhar's laptop. View it live from the Mac only if Rosbridge listens on a reachable address (section 2).
- **Checksums:** `shasum -a 256 SIMULATED_pdr_20261104_124956_0.mcap` and compare with `pdr/evidence/<run>/SHA256SUMS`, or run `shasum -a 256 -c SHA256SUMS` in the folder with the `.mcap`.
- **Paths:** Mac paths are normal (`~/Downloads/...`); ignore every `\\wsl$\...` and `C:\Users\...` path in these docs.
- **Scripts:**

  | Script | On macOS |
  | --- | --- |
  | `tools/run_pdr_demo.sh`, `tools/fault_test.sh`, `tools/run_simulation.sh`, `tools/record_simulation.sh`, `record_replay.sh` | **Linux only** (ROS 2 Jazzy, `ss`, `pgrep`, `/opt/ros/jazzy`). Run them on the Linux machine. |
  | `tools/install_dependencies.sh` | **Ubuntu only** (`apt-get`). |
  | `tools/download_lichtblick.py` | No macOS option (Windows/Linux only). |
  | `tools/sample_resources.py` | Runs, but matches Linux process names; meant for the sim machine. |
  | `tools/verify_mcap.py` | **Works** with `python3 -m venv` + `pip install mcap==1.2.2 mcap-ros2-support==0.5.5 matplotlib pyyaml websocket-client cbor2`; `--replay-parity` needs ROS (Linux). |
  | `tools/validate_layout.py`, `tools/layout_diagram.py`, `tools/make_gnc_layout.py`, `tools/write_run_metadata.py` | **Work** with Python 3 + `pyyaml` + `matplotlib`. |
