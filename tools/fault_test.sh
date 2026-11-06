#!/usr/bin/env bash
# Operator-display fault tests (SIMULATION ONLY, HARDWARE_ENABLED=0): runs the simulation and, at
# announced times, triggers
#   B  one missing input   - the Gazebo bridge is replaced by one without the camera topics
#   C  stale data          - the simulated navigator stops, so /sim/status stops; connection stays up
#   A  connection loss     - Rosbridge is killed; the simulation keeps running
# and restores each one, so the operator can screenshot both the fault and the recovery.
# Faults only stop existing processes; recovery restarts the same team components. No command is
# sent to any rover and no control interface is added.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash tools/fault_test.sh [options]
  --headless       run Gazebo without its window
  --auto           no Enter prompts: each phase lasts --hold seconds (for an OBS clip)
  --hold SEC       seconds per phase with --auto (default 20)
  -h, --help       show this help
EOF
}

headless=0; auto=0; hold=20
while (($#)); do
  case "$1" in
    --headless) headless=1 ;;
    --auto) auto=1 ;;
    --hold) hold="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="${LUNABOTICS_WS:-$HOME/lunabotics_telemetry_ws}"
stamp="$(date +%Y%m%d_%H%M%S)"
recording="$HOME/lunabotics_recordings/SIMULATED_faulttest_${stamp}"
logs="${recording}_logs"
mkdir -p "$logs"

banner() { printf '\n\033[1;97;44m ==== [%s] %s ==== \033[0m\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$logs/banners.log"; }
fault() { printf '\n\033[1;97;41m ==== [%s] %s ==== \033[0m\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$logs/banners.log"; }
note() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$logs/banners.log"; }
expect() { printf '  EXPECT IN LICHTBLICK: %s\n' "$*" | tee -a "$logs/banners.log"; }

set +u
source /opt/ros/jazzy/setup.bash
source "$workspace/install/setup.bash"
set -u
export ROS_DOMAIN_ID=84 HARDWARE_ENABLED=0
# Same Gazebo partition as run_simulation.sh, or replacement bridges cannot see the simulation.
export GZ_PARTITION="${GZ_PARTITION:-lunabotics_laptop}"
((headless)) && export LIBGL_ALWAYS_SOFTWARE=1

if ss -ltn 2>/dev/null | grep -q ':9090 '; then
  echo "Port 9090 is already in use: stop the other simulation or Rosbridge first." >&2; exit 2
fi
if timeout 10 ros2 topic list --no-daemon 2>/dev/null | grep -q '^/sim/status$'; then
  echo "A simulation is already publishing on ROS_DOMAIN_ID=84. Stop it first." >&2; exit 2
fi

# Same process handling as run_pdr_demo.sh: own process groups, stdin from /dev/null (a background
# job that reads the terminal is stopped by SIGTTIN).
set -m
pids=()
start() {  # start <log name> <command...>; leaves its pid in $started
  "${@:2}" </dev/null >"$logs/$1.log" 2>&1 &
  started=$!
  pids+=("$started")
}
stop_group() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null || return 0
  kill -INT -- "-$pid" 2>/dev/null || true
  for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || return 0; sleep 0.5; done
  kill -TERM -- "-$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || return 0; sleep 0.5; done
  kill -KILL -- "-$pid" 2>/dev/null || true
}
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  [[ -n "${rec_pid:-}" ]] && stop_group "$rec_pid"
  for ((i=${#pids[@]}-1; i>=0; i--)); do stop_group "${pids[$i]}"; done
  # Nodes started outside the launch (replacement bridge, navigator, Rosbridge) are in pids too.
  banner "STOPPED"
  if compgen -G "$recording/*.mcap" >/dev/null && [[ -f "$recording/metadata.yaml" ]]; then
    banner "MCAP SAVED  $(compgen -G "$recording/*.mcap" | head -n 1)"
  else
    fault "NO MCAP SAVED - see $logs/recorder.log"; status=3
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'note "Interrupted"; exit 130' INT TERM

pause() {  # pause <what the operator should do now>
  if ((auto)); then
    note "$1 (auto: next step in ${hold} s)"; sleep "$hold"
  else
    read -r -p "  >> $1 Then press Enter. " _
  fi
}
proc_pid() { pgrep -f -- "$1" | head -n 1 || true; }
wait_for_message() {
  local topic="$1" until=$((SECONDS+30))
  while ((SECONDS < until)); do
    timeout 10 ros2 topic echo --once --no-arr "$topic" </dev/null >/dev/null 2>&1 && return 0
    sleep 0.5
  done
  return 1
}

cat <<EOF

=====================================================================
 OPERATOR DISPLAY FAULT TESTS            (SIMULATION ONLY)
=====================================================================
 Recording: $recording
 1. Open LichtBlick, import the layout, connect Rosbridge ws://localhost:9090.
 2. Start OBS if you want a clip.
 Order: baseline -> B (camera missing) -> restore -> C (stale status)
        -> restore -> A (connection lost) -> restore -> stop.
=====================================================================
EOF
((auto)) || read -r -p "  >> Press Enter to start the simulation. " _

sim_args=(); ((headless)) && sim_args+=(headless:=true)
start simulation bash "$root/tools/run_simulation.sh" "${sim_args[@]}"; sim_pid=$started
bash "$root/tools/record_simulation.sh" "$recording" </dev/null >"$logs/recorder.log" 2>&1 &
rec_pid=$!
until ss -ltn 2>/dev/null | grep -q ':9090 '; do
  kill -0 "$sim_pid" 2>/dev/null || { note "Simulation exited; see $logs/simulation.log"; exit 1; }
  sleep 0.5
done
for topic in /clock /tf /sim/status /sim/camera/image; do
  wait_for_message "$topic" || { note "No message on $topic within 30 s"; exit 1; }
done
banner "SIM UP  (Rosbridge ws://localhost:9090)"
expect "CONNECTION shows ws://localhost:9090; all four health lights green; WARNINGS 'No warnings'."
pause "BASELINE: screenshot the healthy display."

# ---- B: one missing input (camera) -------------------------------------------------------------
full_bridge="$(ros2 pkg prefix lunabotics_interfaces)/share/lunabotics_interfaces/config/gazebo_bridge.yaml"
no_camera="$logs/gazebo_bridge_no_camera.yaml"
python3 - "$full_bridge" "$no_camera" <<'PY'
import sys, yaml
entries = yaml.safe_load(open(sys.argv[1]))
kept = [e for e in entries if not e['ros_topic_name'].startswith('/sim/camera/')]
yaml.safe_dump(kept, open(sys.argv[2], 'w'), sort_keys=False)
PY
launch_bridge="$(proc_pid 'ros_gz_bridge/parameter_bridge')"
start bridge_no_camera ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$no_camera" -p use_sim_time:=true -r __node:=fault_test_bridge_no_camera
sleep 3
[[ -n "$launch_bridge" ]] && kill -TERM "$launch_bridge" 2>/dev/null || true
fault "FAULT B START: camera input missing (bridge without /sim/camera/*); everything else runs"
expect "Camera light turns red STALE after 2 s; Data age 'camera' climbs; camera image freezes on its last frame;"
expect "LiDAR/Pose/Status stay green (a ~1 s blip is possible while the bridges swap)."
pause "FAULT B: screenshot the camera light + frozen image."
bridge_no_camera=$started
start bridge_full ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$full_bridge" -p use_sim_time:=true -r __node:=fault_test_bridge_full
sleep 3
stop_group "$bridge_no_camera"
banner "RESTORED B: full bridge running again"
expect "Camera light back to green; image moving again."
pause "RESTORED B: screenshot (optional)."

# ---- C: stale data with the connection up (navigator stops) -----------------------------------
navigator="$(proc_pid 'lunabotics_autonomy/simulation_navigator')"
[[ -n "$navigator" ]] && kill -TERM "$navigator" 2>/dev/null || true
fault "FAULT C START: simulated navigator stopped; /sim/status no longer updates; Rosbridge still up"
expect "Within 1 s: WARNINGS red 'STATUS STALE', MISSION STATE red 'STATE NOT CURRENT', Status link light red;"
expect "Data age 'status' climbs; CONNECTION still shows ws://localhost:9090."
pause "FAULT C: screenshot the stale-status warning."
start navigator ros2 run lunabotics_autonomy simulation_navigator --ros-args \
  -p use_sim_time:=true -p simulation_only:=true -p goal_x:=6.4 -p goal_y:=3.1
wait_for_message /sim/status || note "navigator did not restart; see $logs/navigator.log"
banner "RESTORED C: navigator running again"
expect "Status link green; MISSION STATE back to the navigator's state (COMPLETE if the goal was already reached)."
pause "RESTORED C: screenshot (optional)."

# ---- A: complete connection loss (Rosbridge killed, simulation keeps running) -----------------
rosbridge="$(proc_pid 'lib/rosbridge_server/rosbridge_websocket')"
[[ -n "$rosbridge" ]] && kill -KILL "$rosbridge" 2>/dev/null || true
fault "FAULT A START: Rosbridge killed; port 9090 closed; simulation still running"
expect "CONNECTION panel: 'Waiting for connection...'; app bar spinner + red error; 'Connection failed' alert."
expect "Other panels keep their LAST values (lights may still be green): this is the frozen-data case."
pause "FAULT A: screenshot the whole window incl. CONNECTION panel and app bar."
start rosbridge ros2 launch lunabotics_telemetry telemetry.launch.py
until ss -ltn 2>/dev/null | grep -q ':9090 '; do sleep 0.5; done
banner "RESTORED A: Rosbridge back on ws://localhost:9090"
expect "LichtBlick reconnects within ~3 s; CONNECTION shows ws://localhost:9090; panels update again."
expect "If the 3D panel says 'Missing transform', reconnect once (File -> Open connection...)."
pause "RESTORED A: screenshot the recovered display."

note "Stopping the recorder and the simulation"
stop_group "$rec_pid"; rec_pid=""
