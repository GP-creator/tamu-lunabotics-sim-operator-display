# Merge review: Alice's LichtBlick dashboard → merged operator display

**Sources compared:**
- **Mine:** `02_Ground_Station_Telemetry/deliverables/lichtblick/` at `2105ede`.
- **Alice's:** Alice Choi (Jihye-Choi1210), XpiredRuby/CDH_Jetson_Info PR #4 "Add LichtBlick operator dashboard and documentation", commit `40dc358` (2026-11-01).

**Why PR #4 was closed:** not stated. Alice closed it herself on 2026-11-02; there are no comments or reviews. Her README asks that it not overwrite another person's same-named files without review, which may be the reason.

**Real-rover topics in Alice's layout:** none. All 7 topics are `/sim/*` or TF and the sim publishes all of them (`tools/validate_layout.py`: PASS). So no rover-only panels were carried over; `rover_only_topics.txt` stays empty.

## Layout, panel by panel

| Item | Mine | Alice's | Decision | Reason |
| --- | --- | --- | --- | --- |
| Overall structure | 18 panels, Operator + Details tabs | 5 panels, one screen | **Keep mine** | Superset of Alice's panels, adds mission state, warnings, health, timeline |
| 3D topics | scan, path, grid, footprint script | scan, path, grid | **Keep mine** | Same sim topics; mine adds the rover footprint |
| 3D scan colouring | Flat red, 5 px | `turbo` colormap on `intensity` | **Keep mine** | Every sim scan intensity is 0.0 (checked in the MCAP), so the colormap is one colour. Revisit for real L2 LiDAR |
| 3D TF preloading | not set | `scene.transforms.enablePreloading: true` | **Take Alice's** | Real 1.30.0 setting: loads the whole TF history, so replay scrubbing has transforms immediately and the "preload" info alert goes away |
| 3D view | Fixed on arena (`odom`), whole arena visible | Follows `base_link`, iso view | **Keep mine** | Operator sees whole arena, goal and path without the view moving |
| 3D/Image click-to-publish | Inert `/operator_display/click_disabled/*` | Defaults (`/move_base_simple/goal`, `/clicked_point`, `/initialpose`) | **Keep mine** | Safety: a stray click must not send a goal to a nav stack |
| Camera panel | `/sim/camera/image` + `camera_info` | Same | **Keep mine** | Identical topics; mine adds a "SIMULATED" title |
| Raw status | Details tab | Main screen | **Keep mine** | Mission state is parsed into indicators on the main screen; raw JSON is for debugging |
| Warning panel | Rules for 11 warning codes from `/sim/status` | Placeholder on `/sim/status.data`, no rules | **Keep mine** | Alice's is explicitly a non-functional placeholder (her notes say so) |
| Motion plot | `cmd_vel` linear.x/angular.z | Same | **Combine** | Same data; took Alice's `isSynced: true`, floating legend and axis labels |
| Data age plot | status/LiDAR/pose/camera ages | — | **Keep mine** | Not in Alice's |
| Thresholds | pose/LiDAR 0.5 s, camera 2 s (from autonomy code), status 1 s | none | **Keep mine** | Alice's has no thresholds |
| Message schemas | `std_msgs/String` (JSON), LaserScan, Path, OccupancyGrid, Image, CameraInfo, Twist, Odometry, TF | Same minus Odometry | **Keep mine** | No schema conflicts |

## Docs

| Item | Decision | Reason |
| --- | --- | --- |
| LiDAR "Missing transform base_scan → base_link" fix: reconnect Rosbridge | **Take Alice's** | Real issue she hit and worked around; added to quickstart troubleshooting and test notes, credited |
| Connecting from another computer (`ws://<ubuntu-ip>:9090`) | **Take Alice's**, with a note | Useful; noted that the team launch binds Rosbridge to 127.0.0.1, so remote use needs a launch change |
| "Commanded, not measured" velocity; flat plot after completion is normal | **Take Alice's** | Clear operator wording |
| "Disconnecting LichtBlick only stops viewing, not the sim/rover" | **Take Alice's** | Important for operators |
| Quick-troubleshooting list | **Combine** | Alice's items (no panels, camera blank, LiDAR TF, flat plot) added under my quickstart |
| Live test on macOS + Apple Silicon UTM VM | **Take Alice's** as a second test environment | Only real-app evidence so far; added to test notes, screenshot in `pdr/evidence/SIMULATION_alice_live_2026-11-01/` |
| Ogre/EGL crash workaround on Apple Silicon | **Take Alice's** as a known issue | Not committed by her; documented only |
| Panel descriptions, warnings table, stop/close steps | **Keep mine** | Cover the merged panels |

## Validation of the merged layout

`python3 tools/validate_layout.py` → **PASS**: 18 panels (all valid LichtBlick 1.30.0 types), 3 scripts, 12 topics. Every topic is sim-available or a script output; no orphans; no unused script outputs. The checker also flags likely typos (tested by planting `/sim/planed_path` → "typo of /sim/planned_path?").
