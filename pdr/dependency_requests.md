# Dependency requests for PDR slides 9–11 (LichtBlick)

From Gadadhar + Alice. Current numbers are SIMULATION only; sources in `pdr/evidence/`.

## Sabu + Robin (interfaces, network, recording)

1. **Link budget:** measured rover ↔ operator bandwidth (Mbit/s) and latency on the competition radio/network, to replace the **placeholder 10 Mbit/s** in `pdr/link_budget.json`. Our display needs 19.15 Mbit/s live, 18.07 of it the raw camera (`SIMULATED_pdr_20261104_124956/rosbridge_bandwidth.json`).
2. **Camera plan:** will the rover send compressed images (e.g. `sensor_msgs/CompressedImage`) or a lower rate/resolution? We'll switch the Image panel to whatever topic you choose.
3. **Real topic list:** names, types, frames and rates for the Unitree L2 LiDAR, Orbbec camera, odometry/pose and any status topic, so we can fill `02_Ground_Station_Telemetry/deliverables/lichtblick/rover_only_topics.txt` and pass expected rates to `verify_mcap.py`.
4. **`topics.csv` fix:** `/clock` is listed at 100 Hz, but the simulation publishes 500 Hz (all four recordings).
5. **`/rosout` in `topics_to_record.txt`:** without it, a Log panel is empty on replay.
6. **Remote viewing:** the Rosbridge launch binds to `127.0.0.1`. If the operator laptop is a different machine, how will it reach Rosbridge (bind address, SSH forward, VPN)?

## Sameer + Zosia (Jetson compute and storage)

1. **Compute headroom** on the Jetson for `rosbridge_server` and `ros2 bag record`. Laptop measurements (24 cores, CPU % of one core; `SIMULATED_pdr_20261104_124956`): rosbridge ≈ 107 % with LichtBlick connected (≈ 114 % with LichtBlick + measurement probe), 100.6 MB RSS; recorder 35.7 % mean / 43.8 % max, 84.9 MB RSS. At that load Rosbridge delivered `/clock` at 434 of 500 Hz.
2. **Free disk** for recordings. Uncompressed MCAP is ~149 MB/min in simulation (≈ 8.9 GB/hour); rover data rates may differ.
3. **Battery, E-stop and fault signals:** will any be published as ROS topics? Those panels show UNAVAILABLE until then.
4. **Real rover dimensions** (footprint box is 0.65 × 0.45 × 0.16 m from the sim model).

## Vin (lead)

1. **Nov 5 rover recording** (MCAP), with the run type: EXISTING-ROVER MANUAL or EXISTING-ROVER AUTONOMOUS. We'll run `tools/verify_mcap.py` on it for slide 11.
2. **Review of the layout in the LichtBlick app** once screenshots are ready.
