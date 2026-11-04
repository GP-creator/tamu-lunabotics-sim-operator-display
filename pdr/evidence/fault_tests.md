# Operator-display fault tests

**Label: SIMULATION.** Tool: `tools/fault_test.sh` (sim + recorder; faults at announced times; each restored).
**Pass criterion:** the operator can recognize lost data; **a frozen value must not look live and healthy.**
**Visual acceptance:** by Gadadhar in LichtBlick (screenshots below). Script or ROS checks alone do not count as a pass.

## Layout review before testing (2026-11-04)

Source: LichtBlick 1.30.0 `RosbridgePlayer.ts`, `DataSourceInfoView.tsx`, `AppBar/DataSource.tsx`.

- **Connection loss (A):** when the socket closes, the player sets `RECONNECTING`, raises a "Connection failed" error alert and stops delivering messages. Time stops advancing. User Scripts only run when a message arrives and a layout cannot run a wall-clock timer, so **every Indicator, plot and the camera keep their last values, and lights can stay green.** Basing staleness on the wall clock is not possible inside the layout for this case.
  **Fix (commit `d812740`):** the built-in **Data source info** panel (shows "Waiting for connection…" on `RECONNECTING`) is now on the Operator tab as **CONNECTION**, at the start of the health-light row, next to every light. The app bar also shows a spinner and a red error.
- **One topic missing (B) / stale topic (C) with the link up:** `/tf` keeps arriving, so the scripts keep running and turn the matching light red (camera > 2 s, status > 1 s → STATUS STALE). **The camera image itself freezes on its last frame**; only the camera light shows staleness.

## ROS-level check (headless, `SIMULATED_faulttest_20261104_132522`)

Fault timing confirmed from the recording (sim time):

| Case | What was done | Recording shows |
| --- | --- | --- |
| B | Bridge replaced by one without `/sim/camera/*` | `/sim/camera/image` gap 9.4 s at 15.42 s; `/clock`, `/tf`, `/sim/scan`, `/sim/odom` no gap > 0.6 s |
| C | Simulated navigator stopped, restarted | `/sim/status` gap 10.36 s at 34.94 s; sensors continuous |
| A | Rosbridge killed, restarted | no ROS gap (only the WebSocket link drops, as intended) |

## Visual results (LichtBlick)

| Case | Operator should see | Operator saw | Result | Screenshot |
| --- | --- | --- | --- | --- |
| Baseline | CONNECTION `ws://localhost:9090`, lights green, "No warnings" | PENDING | PENDING | `F0_baseline.png` |
| B: camera missing | Camera light red STALE within ~2 s; camera age climbing; image frozen | PENDING | PENDING | `F1_camera_missing.png` |
| C: stale status | WARNINGS red STATUS STALE, MISSION STATE red STATE NOT CURRENT, Status link red within ~1 s; CONNECTION still `ws://…` | PENDING | PENDING | `F2_status_stale.png` |
| A: link lost | CONNECTION "Waiting for connection…", app bar spinner + red error; other panels frozen | PENDING | PENDING | `F3_connection_lost.png` |
| A: restored | CONNECTION `ws://…` again; panels update | PENDING | PENDING | `F4_reconnected.png` |
