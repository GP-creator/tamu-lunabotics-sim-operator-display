# Handoff: CDH-S2 display/recorder element (PDR slides 9–11)

From Gadadhar to Alice, 2026-11-04. Branch `pdr-lichtblick` of `GP-creator/tamu-lunabotics-sim-operator-display`. All results so far are **SIMULATION** or **REPLAY**. Raw recordings and screenshots are in the shared Drive package, not GitHub (`pdr/evidence_location.md`).

## Where things are

| What | Path |
| --- | --- |
| Layout (sim) | `02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json` (+ `panel_topics.md`) |
| Layout (GNC-2027 topics) | `…/lichtblick/lichtblick_layout_gnc2027.json`; how it maps: `…/lichtblick/HANDOFF_GNC2027_for_Alice.md` |
| Quickstart (incl. macOS section) | `…/lichtblick/lichtblick_quickstart.md` |
| One-command demo + recording | `tools/run_pdr_demo.sh` (Linux) |
| Fault tests | `tools/fault_test.sh` (Linux); record: `pdr/evidence/fault_tests.md` |
| MCAP verification | `tools/verify_mcap.py` (also on macOS; see quickstart §10) |
| Record / replay wrapper | `…/lichtblick/record_replay.sh` (Linux) |
| Recorded topics | `…/lichtblick/topics_to_record.txt` (symlink to `src/lunabotics_telemetry/config/topics_to_record.txt`) |
| Layout check | `tools/validate_layout.py` |
| Evidence | `pdr/evidence/<run>/` (summary.md, plots, metadata.json, SHA256SUMS); main run `SIMULATED_pdr_20261104_124956`, NO PATH run `SIMULATED_pdr_20261104_112151` |
| Raw MCAPs, checksums, replay steps | `pdr/evidence_location.md` |
| Screenshots list | `pdr/screenshot_manifest.md` |
| Slides text, tables, speaker notes, open actions | `pdr/slides_9_11.md` |
| Merge with your PR #4 | `pdr/merge_review.md` |
| Requests to other pairs | `pdr/dependency_requests.md` |

## Status

- **Done:** layout (validator PASS, seen working in the LichtBlick app); live connection (run 124956); replay (0 losses, identical timestamps; NO PATH shown at 20.03 s of run 112151); recorder fixed and checked (MCAP SAVED / red NO MCAP SAVED); metadata and checksums for 124956 and 112151.
- **Web LichtBlick version:** unknown (not checked); the desktop pin is 1.30.0.

## Open tasks

1. **Fault tests (visual), together:** run `bash tools/fault_test.sh` on the Linux machine with LichtBlick connected; screenshot F0–F4; fill the "Operator saw / Result" columns in `pdr/evidence/fault_tests.md`; update the two "PENDING" rows in slide 11. The script is ready; faults are verified at ROS level only.
2. **GNC topics:** test `lichtblick_layout_gnc2027.json` live against a GNC-2027 run (not done; built from their source only). Ask GNC/CDH for the real LiDAR, camera image and sim/rover source-label topics; add them to the layout and `rover_only_topics.txt`.
3. **Two screenshots for slide 10:** still to be added by hand; candidates in `pdr/screenshot_manifest.md` (`03_terminal_banners.png`, `09_bag_info.png`, `04_replay_mid_drive.png`).
4. **Expected rates column (slide 10 table, `verify_mcap.py`):** expected rates come from `topics.csv`. `/clock` is listed at 100 Hz but runs at 500 Hz, and `/tf` has none. Agree the values with Sabu/Robin, and pass rover rates with `--expected-rates` for Vin's data.
5. **Coordination:**
   - **Sabu/Robin:** canonical `record_replay.sh` / `topics_to_record.txt` names (Robin's T04); measured link bandwidth/latency to replace the 10 Mbit/s placeholder; camera compression plan; `topics.csv` fixes.
   - **Vin/Mrinal:** Nov 5 rover MCAP with the same run ID as the rover footage; run `verify_mcap.py` on it for the slide 11 placeholder; review of the layout.
6. **Shared Drive folder:** create it, upload the share package, put the link in `pdr/evidence_location.md`.
