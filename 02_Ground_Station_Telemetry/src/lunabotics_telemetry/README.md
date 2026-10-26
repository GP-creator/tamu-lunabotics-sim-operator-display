# LichtBlick and recording settings

This package contains the display layout, recording topic list and Rosbridge launch.

- Edit `layouts/simulation.json` for the LichtBlick panels.
- Edit `config/topics_to_record.txt` for recording topics.
- Check `launch/telemetry.launch.py` for the bridge settings.

Follow your download's [top-level README](../../../README.md) for setup. The Gazebo launch starts Rosbridge automatically. Use that bridge for the default simulation.

The local connection is **Rosbridge** at `ws://localhost:9090`. You can also open an MCAP file in LichtBlick without a live connection. Keep simulated, recorded and live-rover results clearly labelled.
