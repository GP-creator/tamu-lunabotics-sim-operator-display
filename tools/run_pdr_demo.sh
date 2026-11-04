#!/usr/bin/env bash
# One-command PDR demo: start the simulation, record it, stop when the simulated rover reaches its goal.
# SIMULATION ONLY: HARDWARE_ENABLED=0, no command is sent to any rover. The simulated navigator drives
# itself to the goal exactly as tools/run_simulation.sh always has.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash tools/run_pdr_demo.sh [options]
  --headless          run Gazebo without its window (sets LIBGL_ALWAYS_SOFTWARE=1)
  --timeout SEC       stop if the goal is not reached in SEC seconds (default 120)
  --yes               do not wait for Enter after the pre-flight checklist
  --measure-bandwidth also measure the Rosbridge bandwidth LichtBlick's layout pulls (adds a client)
  -h, --help          show this help
EOF
}

headless=0; timeout_s=120; wait_enter=1; measure_bw=0
while (($#)); do
  case "$1" in
    --headless) headless=1 ;;
    --timeout) timeout_s="$2"; shift ;;
    --yes) wait_enter=0 ;;
    --measure-bandwidth) measure_bw=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="${LUNABOTICS_WS:-$HOME/lunabotics_telemetry_ws}"
stamp="$(date +%Y%m%d_%H%M%S)"
recording="$HOME/lunabotics_recordings/SIMULATED_pdr_${stamp}"
logs="${recording}_logs"
mkdir -p "$logs"

banner() { printf '\n\033[1;97;44m ==== [%s] %s ==== \033[0m\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$logs/banners.log"; }
note() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$logs/banners.log"; }

# ROS setup scripts reference unset variables, so source them with nounset off.
set +u
source /opt/ros/jazzy/setup.bash
if [[ ! -f "$workspace/install/setup.bash" ]]; then
  echo "Workspace not built: $workspace. Run: python3 tools/build_team_workspace.py telemetry --execute" >&2; exit 2
fi
source "$workspace/install/setup.bash"
set -u
export ROS_DOMAIN_ID=84 HARDWARE_ENABLED=0
((headless)) && export LIBGL_ALWAYS_SOFTWARE=1

if ss -ltn 2>/dev/null | grep -q ':9090 '; then
  echo "Port 9090 is already in use: another simulation or Rosbridge is running. Stop it first." >&2; exit 2
fi
if timeout 5 ros2 topic list 2>/dev/null | grep -q '^/sim/status$'; then
  echo "A simulation is already publishing on ROS_DOMAIN_ID=84. Stop it first." >&2; exit 2
fi

# Job control: each background job gets its own process group and, unlike plain `&` jobs in a
# script, does not start with SIGINT ignored, so Ctrl+C-style shutdown reaches ros2 launch/bag.
set -m
sim_pid=""; rec_pid=""; res_pid=""
stop_group() {  # SIGINT a process group (like Ctrl+C), then escalate if it does not exit
  local pid="$1" name="$2"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null || return 0
  kill -INT -- "-$pid" 2>/dev/null || true
  for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || { note "$name stopped (Ctrl+C)"; return 0; }; sleep 0.5; done
  note "$name did not stop within 15 s of Ctrl+C; sending SIGTERM"
  kill -TERM -- "-$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || { note "$name stopped (SIGTERM)"; return 0; }; sleep 0.5; done
  note "$name still running; killing it"
  kill -KILL -- "-$pid" 2>/dev/null || true
}
cleanup() {
  trap - EXIT INT TERM
  stop_group "$rec_pid" recorder
  stop_group "$sim_pid" simulation
  [[ -n "$res_pid" ]] && kill -TERM "$res_pid" 2>/dev/null && wait "$res_pid" 2>/dev/null || true
  banner "STOPPED"
}
trap cleanup EXIT
trap 'note "Interrupted"; exit 130' INT TERM

cat <<EOF

=====================================================================
 PDR DEMO PRE-FLIGHT CHECKLIST           (SIMULATION ONLY)
=====================================================================
 Recording will be saved to: $recording
 1. Open LichtBlick on Windows.
 2. View -> Import layout from file... ->
      02_Ground_Station_Telemetry/deliverables/lichtblick/lichtblick_layout.json
 3. File -> Open connection... -> Rosbridge -> ws://localhost:9090 -> Open.
    It will say it cannot connect yet. That is fine: it retries every
    3 s and attaches as soon as the simulation is up.
 4. Arrange LichtBlick and this terminal so OBS captures both.
 5. START OBS RECORDING NOW.
 6. Then press Enter here. Recording starts with the simulation; the
    rover drives itself to the goal and everything stops on its own.
 If the 3D panel says "Missing transform", reconnect in LichtBlick
 (File -> Open connection... -> Rosbridge) once SIM UP appears.
=====================================================================
EOF
((wait_enter)) && read -r -p "Press Enter when OBS is recording... " _

note "Starting simulation (headless=$headless). Log: $logs/simulation.log"
sim_args=(); ((headless)) && sim_args+=(headless:=true)
bash "$root/tools/run_simulation.sh" "${sim_args[@]}" >"$logs/simulation.log" 2>&1 &
sim_pid=$!
python3 "$root/tools/sample_resources.py" --out "$logs/resources.csv" --interval 1 &
res_pid=$!
# Start recording with the simulation so the start of the run is captured; rosbag2 subscribes
# to each listed topic as soon as it appears.
bash "$root/tools/record_simulation.sh" "$recording" >"$logs/recorder.log" 2>&1 &
rec_pid=$!
rec_started="$(date +%H:%M:%S)"

deadline=$((SECONDS+90))
until ss -ltn 2>/dev/null | grep -q ':9090 '; do
  kill -0 "$sim_pid" 2>/dev/null || { note "Simulation exited during startup; see $logs/simulation.log"; exit 1; }
  ((SECONDS < deadline)) || { note "Rosbridge did not open port 9090 within 90 s"; exit 1; }
  sleep 0.5
done
note "Rosbridge listening on ws://localhost:9090"
key_topics=(/clock /tf /sim/status /sim/scan /sim/odom /sim/camera/image)
checks=()
for topic in "${key_topics[@]}"; do
  timeout 30 ros2 topic echo --once --no-arr "$topic" >/dev/null 2>&1 &
  checks+=($!)
done
for i in "${!key_topics[@]}"; do
  wait "${checks[$i]}" || { note "No message on ${key_topics[$i]} within 30 s; see $logs/simulation.log"; exit 1; }
  note "publishing: ${key_topics[$i]}"
done
banner "SIM UP  (Rosbridge ws://localhost:9090, key topics publishing)"

kill -0 "$rec_pid" 2>/dev/null || { note "Recorder exited; see $logs/recorder.log"; exit 1; }
for _ in $(seq 1 40); do compgen -G "$recording/*.mcap" >/dev/null && break; sleep 0.25; done
compgen -G "$recording/*.mcap" >/dev/null || { note "Recorder has not created an MCAP file; see $logs/recorder.log"; exit 1; }
banner "RECORDING  (since $rec_started) -> $recording"

if ((measure_bw)); then
  python3 "$root/tools/measure_rosbridge_bandwidth.py" --seconds 10 --out "$logs/rosbridge_bandwidth.json" \
    >"$logs/rosbridge_bandwidth.log" 2>&1 && note "Rosbridge bandwidth measured ($logs/rosbridge_bandwidth.json)" \
    || note "Rosbridge bandwidth measurement failed; see $logs/rosbridge_bandwidth.log"
fi

# Wait for the simulated navigator to report "complete" (reads /sim/status only).
outcome="$(python3 - "$timeout_s" <<'PY'
import json, sys, time
import rclpy
from std_msgs.msg import String
limit = float(sys.argv[1])
rclpy.init()
node = rclpy.create_node('pdr_demo_goal_watch')
state = {'last': None}
def on_status(msg):
    try:
        state['last'] = json.loads(msg.data).get('state')
    except ValueError:
        pass
node.create_subscription(String, '/sim/status', on_status, 10)
start, previous = time.monotonic(), None
while time.monotonic()-start < limit and state['last'] != 'complete':
    rclpy.spin_once(node, timeout_sec=0.2)
    if state['last'] != previous:
        print(f"[{time.strftime('%H:%M:%S')}] navigator state: {state['last']}", file=sys.stderr, flush=True)
        previous = state['last']
print('complete' if state['last'] == 'complete' else f"timeout (last state: {state['last']})")
node.destroy_node()
rclpy.shutdown()
PY
)" 2> >(tee -a "$logs/banners.log" >&2)

if [[ "$outcome" == complete ]]; then
  banner "GOAL REACHED  (navigator state: complete)"
else
  banner "TIMEOUT after ${timeout_s} s  ($outcome)"
fi
note "Recording 5 s more so the final state is in the file"
sleep 5
stop_group "$rec_pid" recorder; rec_pid=""
ros2 bag info "$recording" >"$logs/bag_info.txt" 2>&1 || true
stop_group "$sim_pid" simulation; sim_pid=""
cleanup
trap - EXIT
cat <<EOF

 Recording: $recording
 Logs:      $logs   (banners.log, simulation.log, recorder.log, resources.csv, bag_info.txt)
 You can stop OBS now.
 Verify:    python3 tools/verify_mcap.py "$recording" --label SIMULATION --resources "$logs/resources.csv"
EOF
[[ "$outcome" == complete ]]
