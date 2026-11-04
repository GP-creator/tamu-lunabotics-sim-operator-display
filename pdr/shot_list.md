# Screenshot shot list: PDR slides 9–11

Take these yourself from the OBS capture or directly in LichtBlick 1.30.0 with the merged `lichtblick_layout.json`. Keep LichtBlick's top bar in frame: it shows the data source (`ws://localhost:9090` = live, file name = replay). That's how the label is proven.

Times below are taken from the verified recordings in `pdr/evidence/`. A new live run will be close but not identical; use the banners and the MISSION STATE panel to time the shots.

| # | File name | Label | Source | Moment | What must be visible | Proves | Slide |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `01_live_navigating_halfway.png` | SIMULATION | Live (OBS run) | Rover about halfway: ~15–20 s after the RECORDING banner. In the verified runs the goal was reached 37 s in | MISSION STATE green NAVIGATING; "No warnings"; DATA ORIGIN SIMULATED; LiDAR dots, orange obstacle cells, cyan planned path, orange rover box; camera image; four green health lights | Whole display working live over Rosbridge | 9 (main figure), 11 |
| 2 | `02_live_goal_reached.png` | SIMULATION | Live (OBS run) | Right after the GOAL REACHED banner | MISSION STATE blue COMPLETE; flat commanded-speed plot; terminal banner visible if possible | Mission state display matches the navigator | 11 |
| 3 | `03_live_terminal_banners.png` | SIMULATION | OBS terminal | After STOPPED | SIM UP / RECORDING / GOAL REACHED / STOPPED banners with timestamps and the recording path | One-command run and clean stop | 10 |
| 4 | `04_replay_timeline_scrubbed.png` | REPLAY | MCAP from the OBS run (File → Open local file(s)…) | Scrub to mid-run and pause | Top bar shows the `.mcap` name; playback bar with the scrub position; same panels as #1 | Offline replay without ROS; timestamps preserved | 10 |
| 5 | `05_replay_no_path_warning.png` | REPLAY | `SIMULATED_pdr_20261104_112151_0.mcap` | Scrub to **19.9–20.2 s** (step frame by frame; the event lasts 0.3 s) | MISSION STATE red NO PATH TO GOAL; WARNINGS red NO PATH; the timeline panel showing the blip | Warning logic on a real (simulated) event, not injected | 9 (warning logic), 11 |
| 6 | `06_replay_waiting_for_sensors.png` | REPLAY | Any recording | 0.0–0.3 s | Yellow WAITING FOR SENSORS; LiDAR light grey NO DATA | Start-up state is shown, not hidden | 11 (optional) |
| 7 | `07_unavailable_panels.png` | — (no data) | No data source, or crop from #1 | Any time | Battery / E-stop / Faults grey UNAVAILABLE | "No input → unavailable" rule | 9 |
| 8 | `08_details_tab.png` | REPLAY or SIMULATION | Either | Any time | Details tab: raw `/sim/status` JSON with `"source": "gazebo_simulation"`, Data source info panel | Source labelling at data level | 10 (optional) |

Already captured (no need to retake):
- `pdr/evidence/LICHTBLICK_APP_layout_import_2026-11-04/merged_layout_no_data_unavailable.png`: merged layout imported in the LichtBlick 1.30.0 app, no data, all panels UNAVAILABLE. Can stand in for #7.
- `pdr/evidence/SIMULATION_alice_live_2026-11-01/lichtblick_dashboard.png`: Alice's live session (her pre-merge layout). Credit Alice if used.

Figures generated from files (no screenshot needed):
- `pdr/figures/layout_diagram.png`: panel type → topic → message type (slide 9).
- `pdr/figures/data_path.png`: live and replay data path (slide 9).
- Plots in `pdr/evidence/<run>/` (slides 10–11).

If the 3D panel shows "Missing transform from frame <base_scan> to frame <base_link>" during the live run, reconnect (File → Open connection… → Rosbridge) before taking #1. This is Alice's workaround.
