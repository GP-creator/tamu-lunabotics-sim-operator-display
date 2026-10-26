#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
destination="${1:-$HOME/lunabotics_recordings/sim_$(date +%Y%m%d_%H%M%S)}"
mapfile -t topics < "$root/02_Ground_Station_Telemetry/src/lunabotics_telemetry/config/topics_to_record.txt"
mkdir -p -- "$(dirname -- "$destination")"
exec ros2 bag record --storage mcap --use-sim-time --output "$destination" "${topics[@]}"
