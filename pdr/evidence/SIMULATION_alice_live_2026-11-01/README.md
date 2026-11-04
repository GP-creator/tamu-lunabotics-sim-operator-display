# SIMULATION: Alice's live LichtBlick session (2026-11-01)

**Label: SIMULATION.** Author: Alice Choi (Jihye-Choi1210), from her closed PR XpiredRuby/CDH_Jetson_Info#4, commit `40dc358`.

`lichtblick_dashboard.png`: LichtBlick 1.30.0 on macOS, connected live over Rosbridge (`ws://192.168.64.3:9090`) to the Gazebo sim on Ubuntu 24.04 ARM64 (UTM VM). It shows **Alice's five-panel layout before the merge**, not the merged layout. Visible: 3D arena with LiDAR, obstacle grid and planned path; camera; `/sim/status` with `"state": "complete"`; placeholder warning panel; flat `cmd_vel` plot after completion.

This is the only screenshot so far of the LichtBlick **app itself** rendering live sim data. Per Alice's notes, her VM needed temporary Ogre/launch workarounds under `/tmp` that were not committed.

SHA-256: `6273df40b474e4d976f0791619f19c5b3aeaf51c300ef37a655a3efc9447fed4`
