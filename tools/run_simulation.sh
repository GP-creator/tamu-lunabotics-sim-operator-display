#!/usr/bin/env bash
set -euo pipefail
export HARDWARE_ENABLED=0
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-84}"
export GZ_PARTITION="${GZ_PARTITION:-lunabotics_laptop}"
if [[ "${ROS_DISTRO:-}" != jazzy ]]; then echo 'Source ROS Jazzy and your main workspace first.' >&2; exit 2; fi
if [[ -d /dev/serial/by-id ]] && compgen -G '/dev/serial/by-id/*' >/dev/null; then
  echo 'Disconnect physical rover serial devices before running this simulator profile.' >&2; exit 2
fi
exec ros2 launch lunabotics_simulation simulation.launch.py "$@"
