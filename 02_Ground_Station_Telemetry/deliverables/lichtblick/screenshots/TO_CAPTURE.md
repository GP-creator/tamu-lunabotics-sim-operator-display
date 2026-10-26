# Screenshots to capture

Use LichtBlick 1.30.0 with `lichtblick_layout.json` imported. Save as PNG with the names below. Keep the LichtBlick top bar visible so the data source (file name or `ws://localhost:9090`) shows in each image.

| File name | Data source | When | Must show |
| --- | --- | --- | --- |
| `01_recording_navigating.png` | Recording (MCAP) | Playback about 10–30 s | Operator tab: NAVIGATING (green), "No warnings", SIMULATED (Gazebo), LiDAR dots, path, rover box, camera image, four green lights |
| `02_recording_startup_waiting.png` | Recording (MCAP) | Playback 0.0–0.3 s (step frame by frame) | WAITING FOR SENSORS (yellow), WAITING warning, LiDAR light grey "NO DATA" |
| `03_recording_lidar_stale.png` | Recording (MCAP) | Playback about 1.25–1.4 s | Real stale-LiDAR event: WAITING FOR SENSORS state, red "LIDAR STALE/MISSING" warning, LiDAR light red |
| `04_recording_complete.png` | Recording (MCAP) | After 37.1 s | COMPLETE: goal reached (blue); timeline panel shows the whole run |
| `05_unavailable_panels.png` | Either | Any time | Battery / E-stop / Faults all grey UNAVAILABLE (crop to bottom-right is fine) |
| `06_live_rosbridge.png` | Live, `ws://localhost:9090` | While the rover is navigating | Same as 01, but top bar shows `ws://localhost:9090` |
| `07_live_status_stale.png` (optional) | Live | About 2 s after stopping only the navigator (see note) | STATUS STALE warning, STATE NOT CURRENT, Status link light red |
| `08_details_tab.png` | Either | Any time | Details tab: raw `/sim/status` JSON with `"source": "gazebo_simulation"` |

Note for 07: "STATUS STALE" needs `/tf` to keep arriving while `/sim/status` stops. In a second sourced Ubuntu terminal, run `pkill -INT -f simulation_navigator`. This stops only the simulated navigator; Gazebo and `/tf` keep running. Take the screenshot, then Ctrl+C the simulation and start it again. Pausing playback does not work for this: it freezes `/tf` too. Skipping 07 is fine; case A in `../test_output/script_test_output.txt` covers it.
