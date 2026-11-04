# Operator display quickstart

This display shows the rover's mission state, warnings, LiDAR, camera, map and planned path in LichtBlick. It only displays data. It has no driving or control panels and does not send commands.

All data used so far is **SIMULATED** (Gazebo). Nothing here comes from the real rover.

## 1. Install LichtBlick (once)

On Windows, open PowerShell in the extracted repo folder and run:

```powershell
py tools/download_lichtblick.py --platform windows
```

Run the installer that appears in your Downloads folder. The repo uses LichtBlick **1.30.0**; other versions have not been tested with this layout.

## 2. Open data: choose A or B

**A. Open the recording (no ROS or Gazebo needed)**

1. Copy a recording to the Windows laptop, e.g. `SIMULATED_pdr_20261104_112346_0.mcap` (106 MB, 42.5 s, simulated; recordings are named `SIMULATED_…`).
2. In LichtBlick, choose **File → Open local file(s)…** and select the `.mcap` file.
3. Press the play button at the bottom. The clock reads around **1 January 1970**. This is expected: the recording uses simulation time, which starts at zero.

**B. Connect to a running simulation**

1. In LichtBlick, choose **File → Open connection…**, then **Rosbridge**.
2. Enter `ws://localhost:9090` and choose **Open**. If the simulation isn't running yet, LichtBlick keeps retrying every 3 s.
3. In Ubuntu (WSL), from the repo folder, run `bash tools/run_pdr_demo.sh` and press Enter when asked. The simulation starts, is recorded, and stops by itself when the rover reaches its goal.

To view from **another computer**, use `ws://<ubuntu-ip>:9090`. This only works if Rosbridge listens on that network. The team launch binds it to `127.0.0.1` (this computer only), so remote viewing needs a launch change. Alice used a temporary bridge on her VM's address for her macOS test.

LichtBlick shows the file name or `ws://localhost:9090` at the top of the window. This is how to tell a **recording** from a **live connection**. The display itself cannot tell them apart.

## 3. Import the layout (once per computer)

1. Choose **View → Import layout from file…**.
2. Select `02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json`.

The **Operator** tab opens. The **Details** tab has the raw status message and a list of topics.

## 4. What each panel means

Top row: check these first.

| Panel | Shows |
| --- | --- |
| **MISSION STATE** | What the navigator is doing: NAVIGATING (green), COMPLETE (blue), PAUSED or WAITING FOR SENSORS (yellow), OBSTACLE STOP, NO PATH, INVALID CLOCK or STATE NOT CURRENT (red). |
| **WARNINGS** | The most important current problem, or "No warnings" (green). See section 5. |
| **DATA ORIGIN** | **SIMULATED (Gazebo)** in purple when the data is labelled as simulated. Yellow means the source is not labelled. |

Middle:

| Panel | Shows |
| --- | --- |
| **Map, planned path, LiDAR** | Top view of the arena (1 m grid). Red dots: LiDAR hits. Orange cells: obstacles the rover has seen. Faint green cells: seen free space. Cyan line: planned path. Orange box: rover (simulated chassis size). Drag to rotate; scroll to zoom. |
| **Camera** | The rover's front camera. |
| **LiDAR / Pose / Camera / Status link lights** | Green: fresh. Red: stale. Grey: no data. |

Bottom:

| Panel | Shows |
| --- | --- |
| **Mission state and warnings over time** | A timeline of state and warning changes. |
| **Data age** | How old each input is, in seconds. Higher means older. |
| **Commanded speed** | Speed and turn rate the simulated navigator is **commanding**, not measured speed. A flat line after COMPLETE is normal. |
| **Battery / E-stop / Faults** | Always grey **UNAVAILABLE**. No topic exists for these yet. |

If a panel says **UNAVAILABLE**, **NO DATA** or "Waiting for…", its input is missing. This is not a display fault.

## 5. What the warnings mean

| Warning | Meaning | Check |
| --- | --- | --- |
| No warnings | Status, LiDAR and pose are fresh; navigator reports no problem. | — |
| STATUS STALE | No `/sim/status` for over 1 s. Mission state is out of date. | Is the simulation still running? |
| STATUS UNREADABLE | `/sim/status` arrived but could not be read. | Report to CDH. |
| LIDAR STALE/MISSING | No LiDAR scan within 0.5 s. | LiDAR light, Data age plot. |
| POSE STALE/MISSING | No position update within 0.5 s. | Pose light, Data age plot. |
| OBSTACLE STOP | Navigator stopped because an obstacle is too close. | Map panel. |
| NO PATH | Planner cannot find a route to the goal. | Map panel. |
| INVALID CLOCK | Simulation time is invalid. | Restart the simulation. |
| WAITING | Navigator is waiting for its first LiDAR and pose data. Normal for about 1 s at start. | — |
| PAUSED | Simulated navigation was paused with `/sim/pause`. | — |
| SOURCE NOT LABELLED SIMULATED | Status data does not say it is simulated. Treat it as unverified. | Data origin. |

**Important:** if the whole connection drops, every panel keeps its last value. Check the connection indicator at the top of LichtBlick. A frozen display can look normal.

## 6. If something looks wrong

Troubleshooting from Alice Choi's live test, plus our own.

| Symptom | Do this |
| --- | --- |
| Nothing updates | Is the simulation still running? Is the connection **Rosbridge** at the right address? |
| 3D panel says `Missing transform from frame <base_scan> to frame <base_link>` | Wait a few seconds after the sim starts, then reconnect: **File → Open connection… → Rosbridge** again. This cleared it in Alice's test (workaround; cause not confirmed). |
| Camera blank | Check the Camera light. If it is grey, `/sim/camera/image` isn't publishing; don't change the panel. |
| Speed plot flat | Check MISSION STATE. After COMPLETE the rover is meant to stop. |
| Battery / E-stop / Faults grey | Expected: no input exists yet. |

## 7. Stop and close

1. Close LichtBlick (close the window). This only stops **viewing**; it does not stop the simulation or a robot.
2. If you started the simulation: press **Ctrl+C** in its Ubuntu terminal and wait for it to exit. This is not an emergency stop for real hardware.

The layout stays saved in LichtBlick for next time.
