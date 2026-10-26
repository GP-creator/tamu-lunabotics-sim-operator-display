#!/usr/bin/env bash
set -euo pipefail
profile="${1:-main}"
case "$profile" in main|interfaces|telemetry|embedded|embedded_hardware) ;; *) echo 'Choose main, interfaces, telemetry, embedded or embedded_hardware.' >&2; exit 2;; esac
source /etc/os-release
if [[ "${ID:-}" != ubuntu ]]; then echo 'Use Ubuntu 24.04 or its WSL distribution.' >&2; exit 2; fi
if [[ "$VERSION_ID" == '24.04' ]]; then distro=jazzy
elif [[ "$VERSION_ID" == '22.04' && "$profile" == embedded_hardware ]]; then distro=humble
else echo 'Simulation uses Ubuntu 24.04. Embedded-only setup also supports Ubuntu 22.04.' >&2; exit 2; fi
if [[ -n "${ROS_DISTRO:-}" && "$ROS_DISTRO" != "$distro" ]]; then echo 'Open a fresh terminal without a different ROS distribution sourced.' >&2; exit 2; fi
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$EUID" == 0 ]]; then elevate=(); else elevate=(sudo); fi
"${elevate[@]}" apt-get update
"${elevate[@]}" apt-get install -y curl ca-certificates python3
if [[ ! -f "/opt/ros/$distro/setup.bash" ]]; then
  installer="$(mktemp --suffix=.deb)"
  trap 'rm -f "$installer"' EXIT
  python3 - "$root/MAIN/dependency-lock.json" "$VERSION_CODENAME" "$installer" <<'PY'
import hashlib,json,pathlib,sys,urllib.request
lock=json.loads(pathlib.Path(sys.argv[1]).read_text())
asset=next(a for a in lock['ros_apt_source']['assets'] if '.'+sys.argv[2]+'_' in a['name'])
data=urllib.request.urlopen(asset['url'],timeout=60).read()
if hashlib.sha256(data).hexdigest()!=asset['sha256']: raise SystemExit('ROS source installer checksum mismatch')
pathlib.Path(sys.argv[3]).write_bytes(data)
PY
  "${elevate[@]}" dpkg -i "$installer"
  "${elevate[@]}" apt-get update
fi
packages=("ros-$distro-ros-base" python3-colcon-common-extensions python3-numpy python3-opencv python3-serial python3-pytest
  "ros-$distro-sensor-msgs-py" "ros-$distro-tf2-ros" "ros-$distro-tf2-msgs" "ros-$distro-std-srvs")
if [[ "$profile" != embedded_hardware ]]; then
  packages+=(python3-websocket "ros-$distro-rosbridge-suite" "ros-$distro-rosbag2-storage-mcap")
fi
if [[ "$profile" != embedded_hardware ]]; then
  packages+=("ros-$distro-ros-gz" libgl1-mesa-dri libegl1 libgl1)
fi
"${elevate[@]}" apt-get install -y --no-install-recommends "${packages[@]}"
mkdir -p "$root/evidence"
dpkg-query -W -f='${Package}\t${Version}\n' 'ros-*' python3-numpy python3-opencv python3-serial > "$root/evidence/installed-packages.tsv"
printf 'Installed %s profile for ROS %s. Package versions: evidence/installed-packages.tsv\n' "$profile" "$distro"

