# Ground station and telemetry

**Alice + Gadadhar:** make the operator display and control instructions easy for Vin to use.

## Where to work

Start in `02_Ground_Station_Telemetry/src/lunabotics_telemetry/`.

| File | Purpose |
| --- | --- |
| `layouts/simulation.json` | Saved LichtBlick display for the simulation |
| `config/topics_to_record.txt` | Topics included in a recording |
| `launch/telemetry.launch.py` | Starts the Rosbridge connection |

## View recordings with LichtBlick

A Windows laptop can open a saved MCAP recording without ROS or Gazebo. In PowerShell, from the extracted folder:

```powershell
py tools/download_lichtblick.py --platform windows
```

Open the verified installer in Downloads, then open LichtBlick and the recording. Import the layout from the path above. If you do not have a sample recording, ask Vin or create one with the included simulation.

## Run your own simulation

Use Ubuntu 24.04. From the extracted folder:

```bash
bash tools/install_dependencies.sh telemetry
source /opt/ros/jazzy/setup.bash
python3 tools/build_team_workspace.py telemetry --execute
source ~/lunabotics_telemetry_ws/install/setup.bash
export ROS_DOMAIN_ID=84
bash tools/run_simulation.sh
```

In LichtBlick, choose **Rosbridge** and connect to `ws://localhost:9090`. Import the layout. Check the camera, LiDAR, map, planned path and status. The launch already starts the bridge.

For pause, recording, replay and troubleshooting, open `MAIN/README.md` inside the download or the [shared setup guide](https://github.com/XpiredRuby/CDH_Jetson_Info/blob/main/MAIN/README.md). In new Ubuntu terminals, source ROS and `~/lunabotics_telemetry_ws/install/setup.bash`, and set domain 84 again.

## Send to Vin

- **Alice:** `lichtblick_layout.json`, `operator_quickstart.md`, a screenshot and test notes.
- **Gadadhar:** `controls.md`, `stop_test_plan.md`, changed code/config files if needed, and test output.
- Include a short README explaining how to open, run and stop your work.

Label simulated and recorded data. If a panel has no input, show it as unavailable. Leave physical control and stopping measurements for Vin at LASR.
