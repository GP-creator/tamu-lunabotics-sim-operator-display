# Test notes: LichtBlick operator display

Date: 2026-10-25. Tester: Gadadhar. **All data simulated (Gazebo). No rover hardware was used or connected.**

## Setup

| Item | Value |
| --- | --- |
| OS | Windows + WSL2 Ubuntu 24.04, kernel 6.18.33.2-microsoft-standard-WSL2 |
| ROS | Jazzy, `ROS_DOMAIN_ID=84`, `HARDWARE_ENABLED=0` (set by `run_simulation.sh`) |
| Rosbridge | `ros-jazzy-rosbridge-server` 2.7.1, `ws://localhost:9090` (started by the sim launch) |
| LichtBlick | Layout written for 1.30.0 (repo pin) and checked against the v1.30.0 source |
| Repo | `main` at `487b03a` + this uncommitted folder |
| Install | `install_dependencies.sh telemetry` **skipped**: `dpkg-query` showed every package it installs was already present |
| Build | `build_team_workspace.py telemetry --execute`: 4 packages built |

## Data used

| Data | Details |
| --- | --- |
| Live simulation | `tools/run_simulation.sh` (Gazebo GUI mode), default goal (6.4, 3.1) |
| Recording | `SIMULATED_gazebo_nav_20261025_183201` made with `tools/record_simulation.sh` (team method; topics from `topics_to_record.txt`), stopped with Ctrl+C. 63.9 s sim time, 46,775 messages, 151 MiB, all 12 listed topics. Details and SHA-256 in `test_output/recording_info.txt` |
| Mission states in recording | `waiting_for_sensors` (0.05 s) → `navigating` (0.39 s) → `waiting_for_sensors` (1.25 s, real LiDAR staleness 0.55 s) → `navigating` (1.41 s) → `complete` (37.1 s) |

## Tests and results

| # | Test | How | Result |
| --- | --- | --- | --- |
| 1 | Panel types valid | Compared every panel ID in the layout with the panel registry in LichtBlick v1.30.0 `packages/suite-base/src/panels/index.ts` | **Pass**: 18 panels, all valid types; no Teleop/Publish/CallService panels |
| 2 | Layout tree consistent | Every panel placed exactly once (Operator and Details tabs) | **Pass** |
| 3 | Every layout topic exists in the recording | Compared topics in the layout and script inputs with `metadata.yaml` | **Pass**: 7 `/sim/*` topics plus `/tf`; 3 `/studio_script/*` topics come from the layout's scripts |
| 4 | User Scripts compile | Scripts copied out of `lichtblick_layout.json`, compiled with TypeScript 5.6.3 `--strict` against LichtBlick 1.30.0's `markers.ts` and `types.ts` | **Pass**: no diagnostics |
| 5 | Script behaviour on recorded data | Compiled scripts run on the recording's `/sim/status`, `/tf`, `/sim/camera/image`, `/sim/odom` in log-time order | **Pass**: state/warning timeline matches the recording, including the real 1.25 s LiDAR-stale event. Output: `test_output/script_test_output.txt` |
| 6 | Fault cases (injected into the test feed only) | Status stops; camera stops; camera never publishes; seek backwards; obstacle_stop, no_observed_path, invalid_clock, paused, scan stale, pose missing, unlabelled source, unreadable JSON; `/tf` only | **Pass**: each shows the matching warning or UNAVAILABLE; status stale detected 0.98 s after last message; camera stale after 1.93 s; no negative ages after seek |
| 7 | Indicator rules cover all values | Navigator states taken from `simulation_navigation.py`; warning codes from the script | **Pass** |
| 8 | Live through Rosbridge | Subscribed to every layout topic at `ws://localhost:9090` with `cbor-raw` (as LichtBlick does) for 8 s | **Pass**: status 19.8/s, cmd_vel 19.9/s, odom 29.1/s, tf 28.9/s, camera 9.9/s, camera_info 10.0/s, scan 9.9/s, grid 1.9/s, path 1.9/s, tf_static latched. 0 new Rosbridge errors |
| 9 | Opens in the LichtBlick app | 2026-11-04: merged layout imported via **View → Import layout from file…** in the LichtBlick 1.30.0 Linux build (SHA-256-verified `.deb`, WSLg, software WebGL) | **Partly done**: imports and renders; with no data every panel shows UNAVAILABLE (`pdr/evidence/LICHTBLICK_APP_layout_import_2026-11-04/`). With live/replay data: pending (Gadadhar, `pdr/shot_list.md`) |

Tests 4–6 run the scripts in Node, not inside LichtBlick. LichtBlick also checks script return types (no unions or nested type literals); the scripts follow those rules, but only test 9 confirms it.

## Second environment: Alice Choi's live test (2026-11-01), SIMULATION

From Alice's PR #4 notes, merged here (her full results: `pdr/merge_review.md`, screenshot in `pdr/evidence/SIMULATION_alice_live_2026-11-01/`). She tested **her five-panel layout**, not the merged one.

| Item | Value |
| --- | --- |
| Client | LichtBlick 1.30.0 on macOS (Apple Silicon) |
| Sim | Ubuntu 24.04 ARM64 in UTM, ROS 2 Jazzy, Gazebo Harmonic, domain 84, `HARDWARE_ENABLED=0` |
| Connection | Rosbridge at the VM's address (`ws://192.168.64.3:9090`, session-specific) |
| Passed | Rosbridge connect; camera image; `/sim/status` (`gazebo_simulation`, `complete`); `/sim/scan` 720 ranges in `base_scan`; `tf2_echo base_link base_scan` = (0, 0, 0.42); 3D panel after reconnect |
| Issue | 3D panel first showed `Missing transform from frame <base_scan> to frame <base_link>`; reconnecting Rosbridge cleared it. Cause not confirmed |
| Workarounds | Ogre2/EGL crash on the VM; she used temporary Ogre world/launch files under `/tmp` (not committed). The standard launch was not validated end-to-end on that VM |

## After the merge (2026-11-04)

`tools/validate_layout.py` on the merged layout: **PASS** (18 panels, 3 scripts, 12 topics; no orphans or unknown topics). Changes from Alice: TF preloading on the 3D panel, synced plot axes with floating legends, troubleshooting text.

## PDR verification (2026-11-04), SIMULATION

Four recordings checked with `tools/verify_mcap.py`; full results in `pdr/evidence/` and summarised in `pdr/slides_9_11.md`. All four: layout coverage 100 %, TF tree connected, clock monotonic; live-vs-recording and replay parity PASS where run. Overall FAIL on two real findings:
- `/clock` publishes at 500 Hz; `topics.csv` says 100 Hz.
- Navigator `/sim/cmd_vel` and `/sim/status` gaps up to 0.396 s (20 Hz expected), mostly at start-up; below the display's 1 s stale threshold.

Run `SIMULATED_pdr_20261104_112151` contains a real `no_observed_path` event (19.9–20.2 s) that drives the NO PATH warning. Live Rosbridge load for the layout: 19.36 Mbit/s, 18.26 of it the raw camera.

## Known gaps and observations

1. **Recorded vs live cannot be detected inside the layout.** With `/clock` present, LichtBlick's Rosbridge player stamps messages with sim time, the same as the recording. The display labels data **SIMULATED** from the `source` field. Recorded vs live comes from LichtBlick's data-source name (file name vs `ws://localhost:9090`) and the recording's `SIMULATED_` file name.
2. **Total connection loss freezes the display.** Stale detection needs `/tf` to keep arriving. If Rosbridge or the whole sim stops, all panels keep their last values; the operator must watch LichtBlick's connection indicator.
3. **Battery, E-stop, faults:** no topics exist. They show grey UNAVAILABLE by design.
4. **`/rosout` is not recorded.** `topics_to_record.txt` doesn't list it, so a LichtBlick Log panel would be empty offline. **Suggestion for Robin:** add `/rosout` to `topics_to_record.txt`. (Not changed here.)
5. **A missing input disables that script.** LichtBlick 1.30.0 won't run a User Script if any input topic is missing ("Input … is not yet available"). Scripts were therefore split per topic: a missing camera only greys out the camera light, and mission state still works.
6. **Original layout uses an invalid follow mode.** `layouts/simulation.json` has `"followMode": "follow-frame"`, which isn't a 1.30.0 value (`follow-pose`, `follow-position`, `follow-none`). The new layout uses `follow-pose` on `odom`. The original was left unchanged; Alice may want to fix it.
7. **The 3D/Image panels advertise click-to-publish topics when connected live** (`/move_base_simple/goal`, `/clicked_point`, `/initialpose` by default). The new layout points these at `/operator_display/click_disabled/*`. The original layout still uses the defaults.
8. **Rosbridge mixed-mode error.** A plain-JSON client subscribing to a topic that LichtBlick already receives in `cbor-raw` mode gets nothing; Rosbridge 2.7.1 logs `'bytes' object has no attribute 'get_fields_and_field_types'`. LichtBlick itself is unaffected. This matters for anyone writing JSON test clients while LichtBlick is connected.
9. **`ros2 topic hz` showed camera/scan at about 20 Hz** with real-time factor 1.0. The recording (639 messages / 63.9 s) and Rosbridge both show 10 Hz, matching the SDF. The `hz` reading appears to be a measurement artifact.
10. **Not exercised in real simulation:** obstacle_stop, no_observed_path, invalid_clock and paused did not occur in the default run; they were tested only by injected messages (test 6).
11. **Footprint uses development dimensions** (0.65 × 0.45 × 0.16 m from `arena.sdf`), not the measured rover.
12. **Recording is 63.9 s**, slightly over the 60 s target, because the recorder ran 65 s from sim start.
13. **3D camera angle and colours** were set from source defaults, not seen on screen; adjust during test 9 if needed.
14. The Gazebo log prints `gz_frame_id … not defined in SDF` warnings for the three sensors; frames still come through correctly (`base_scan`, `camera_link`, `imu_link`).

## Layout revision for readability (2026-11-04)

Four health lights combined into one compact row under the top row; Battery/E-stop/Faults moved to the Details tab as "Rover-only (not in simulation)"; map panel enlarged (≈ 42 % of the Operator tab, was ≈ 34 %) with a top-down orthographic default view centred on the arena (3.95, 2.2) at 6 m view height; bottom row limited to three panels (timeline + two plots) with plot legends collapsed by default. Camera settings follow LichtBlick 1.30.0 `CameraStateSettings.ts` (orthographic: distance = visible height); not yet checked on screen. `tools/validate_layout.py`: **PASS** (18 panels, 3 scripts, 12 topics). Panel → topic table regenerated in `panel_topics.md`; slide figure in `pdr/figures/layout_diagram.png`.
