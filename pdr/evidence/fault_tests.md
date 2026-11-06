# Operator-display fault tests

**Status:** Original 2026-11-04 headless fault recording verified; additional live visual tests performed by Alice on 2026-11-06 in macOS LichtBlick + Ubuntu ARM64/UTM simulation. Screenshot evidence and joint Alice + Gadadhar acceptance remain pending.

**Label: SIMULATION.** Tool: `tools/fault_test.sh` (sim + recorder; faults at announced times; each restored).
**Pass criterion:** the operator can recognize lost data; **a frozen value must not look live and healthy.**
**Visual acceptance:** by Alice + Gadadhar in LichtBlick (screenshots below). Script or ROS checks alone do not count as a pass.

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


## Additional live visual verification (2026-11-06, Alice; SIMULATION)

**Environment:** LichtBlick on macOS (Apple Silicon), ROS 2 Jazzy and Gazebo Harmonic on Ubuntu 24.04 ARM64 in UTM, `ROS_DOMAIN_ID=84`, `HARDWARE_ENABLED=0`. Rosbridge connected at `ws://192.168.64.3:9090` (session-specific VM address). These tests used live simulation, not rover hardware or MCAP replay. They are **separate from** the 2026-11-04 headless recording above.

| Case | Live procedure | Observed in LichtBlick | Result |
| --- | --- | --- | --- |
| Baseline | Start simulation and connect Mac LichtBlick to Rosbridge | Camera OK and Status OK green | PASS (observed) |
| A: Rosbridge link loss and recovery | Interrupt Rosbridge, then restart its telemetry launch | Connection failed shown on disconnect; display resumed updating after reconnect | PASS (observed) |
| B: camera staleness and recovery | In a **copied** `Fault B Camera Test` layout, change `camera_health` input **and** its `event.topic` comparison from `/sim/camera/image` to `/fault_test/camera/image`. Relay real `/sim/camera/image` messages to the temporary topic using an `rclpy` Python process; stop and restart the relay while `/tf` continues | Relay verified at ~9.9 Hz. Before interruption, Camera OK green; after stopping relay, Camera STALE red, `camera=STALE`, `camera_age_s > 2.0`; after restart, Camera OK green, `camera=OK`, `camera_age_s < 2.0` | PASS (warning logic and recovery) |
| C: `/sim/status` staleness and recovery | Stop simulated navigator while leaving sensor streams running, then restart it | Status STALE red; STATUS STALE and STATE NOT CURRENT warnings; recovered to Status OK after restart | PASS (observed) |

**Scope and limitations:** The camera test verified the **camera-health script and indicator** with a temporary relayed topic; it did **not** interrupt the original `/sim/camera/image` stream or prove end-to-end hardware-camera failure handling. The original Operator layout and Rosbridge configuration were left unchanged for this camera-relay test. For A, loss of Rosbridge can leave the last values frozen; the connection error is the operator's cue, not a guaranteed red stale light. These observations do not establish replay parity, real-rover operation, or all source/mode labels.

**Evidence still needed:** Capture and archive labeled LichtBlick screenshots of baseline, B stale, C stale, A disconnected, and A recovered (`F0_baseline.png` through `F4_reconnected.png`), plus B recovered if useful. The existing visual-results table above is intentionally preserved as the **original 2026-11-04 checklist**, not silently rewritten as if its screenshots were collected. Joint visual acceptance by Alice + Gadadhar has not been confirmed.
