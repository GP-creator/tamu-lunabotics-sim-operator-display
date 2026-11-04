#!/usr/bin/env bash
# Thin wrapper for recording and replaying operator-display data (SIMULATION/REPLAY only).
# Uses the existing team scripts and topic list; names to be coordinated with Sabu + Robin.
#   record [DEST]          tools/record_simulation.sh (topics from topics_to_record.txt); Ctrl+C stops
#   replay BAG             Rosbridge (lunabotics_telemetry/telemetry.launch.py) + ros2 bag play --clock,
#                          so LichtBlick can connect to ws://localhost:9090 and replay through ROS
#   info BAG               ros2 bag info
#   verify BAG [LABEL]     tools/verify_mcap.py (default label REPLAY)
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
workspace="${LUNABOTICS_WS:-$HOME/lunabotics_telemetry_ws}"
usage() { sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

set +u
source /opt/ros/jazzy/setup.bash
source "$workspace/install/setup.bash"
set -u
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-84}" HARDWARE_ENABLED=0

cmd="${1:-}"; shift || true
case "$cmd" in
  record)
    exec bash "$root/tools/record_simulation.sh" "$@" ;;
  info)
    exec ros2 bag info "${1:?bag folder or .mcap}" ;;
  verify)
    bag="${1:?bag folder or .mcap}"; label="${2:-REPLAY}"
    python="$HOME/.venvs/lunabotics-pdr/bin/python"; [[ -x "$python" ]] || python=python3
    exec "$python" "$root/tools/verify_mcap.py" "$bag" --label "$label" ;;
  replay)
    bag="${1:?bag folder or .mcap}"
    if ss -ltn 2>/dev/null | grep -q ':9090 '; then
      echo "Port 9090 is in use (live simulation or Rosbridge running). Stop it before replaying." >&2; exit 2
    fi
    if timeout 10 ros2 topic list --no-daemon 2>/dev/null | grep -q '^/sim/status$'; then
      echo "Live /sim topics on ROS_DOMAIN_ID=$ROS_DOMAIN_ID. Stop the simulation or set another ROS_DOMAIN_ID." >&2; exit 2
    fi
    set -m
    ros2 launch lunabotics_telemetry telemetry.launch.py </dev/null >/tmp/record_replay_rosbridge.log 2>&1 &
    bridge=$!; player=""
    stop_group() {
      [[ -n "$1" ]] || return 0
      kill -INT -- "-$1" 2>/dev/null || true
      for _ in $(seq 1 20); do kill -0 "$1" 2>/dev/null || return 0; sleep 0.5; done
      kill -KILL -- "-$1" 2>/dev/null || true
    }
    # Stop the player and Rosbridge however this script ends: Ctrl+C, closed terminal (HUP) or
    # normal exit. The player runs in the background so `wait` lets these traps run at once.
    stop_all() { trap - EXIT INT TERM HUP; stop_group "$player"; stop_group "$bridge"; }
    trap stop_all EXIT
    trap 'stop_all; exit 130' INT TERM HUP
    until ss -ltn 2>/dev/null | grep -q ':9090 '; do
      kill -0 "$bridge" 2>/dev/null || { echo "Rosbridge failed; see /tmp/record_replay_rosbridge.log" >&2; exit 1; }
      sleep 0.5
    done
    echo "REPLAY: Rosbridge on ws://localhost:9090. In LichtBlick: File -> Open connection... -> Rosbridge."
    echo "REPLAY: playing $bag with --clock (Ctrl+C to stop)."
    ros2 bag play "$bag" --clock --disable-keyboard-controls </dev/null &
    player=$!
    wait "$player" || true ;;
  -h|--help|"")
    usage ;;
  *)
    usage >&2; exit 2 ;;
esac
