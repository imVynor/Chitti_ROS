#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROS_DISTRO_NAME="${ROS_DISTRO:-jazzy}"
SKIP_ROSDEP=0
SKIP_VENV=0

usage() {
  cat <<'EOF'
Usage: bash scripts/setup.sh [options]

One-time bootstrap for Raspberry Pi / cloud machine.

Options:
  --ros-distro NAME  ROS distro to use (default: $ROS_DISTRO or jazzy)
  --skip-rosdep   Skip rosdep update/install
  --skip-venv     Skip local Python venv setup
  -h, --help      Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ros-distro)
      if [[ -z "${2:-}" ]]; then
        echo "[ERROR] --ros-distro requires a value"
        exit 2
      fi
      ROS_DISTRO_NAME="$2"
      shift
      ;;
    --skip-rosdep) SKIP_ROSDEP=1 ;;
    --skip-venv) SKIP_VENV=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1"
      usage
      exit 2
      ;;
  esac
  shift
done

if [[ ! -f "/opt/ros/${ROS_DISTRO_NAME}/setup.bash" ]]; then
  echo "[ERROR] ROS distro '${ROS_DISTRO_NAME}' not found at /opt/ros/${ROS_DISTRO_NAME}"
  exit 1
fi

if [[ ! -d "$WS_DIR/src" ]]; then
  echo "[ERROR] Workspace source folder not found: $WS_DIR/src"
  exit 1
fi

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Required command not found: $cmd"
    exit 1
  fi
}

require_cmd python3

set +u
source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
set -u

cd "$WS_DIR"

echo "[INFO] Workspace: $WS_DIR"
echo "[INFO] ROS_DISTRO: $ROS_DISTRO_NAME"

if [[ $SKIP_ROSDEP -eq 0 ]]; then
  require_cmd rosdep
  echo "[INFO] Installing system dependencies (rosdep)..."
  rosdep update --rosdistro "$ROS_DISTRO_NAME"
  rosdep install \
    --from-paths src \
    --ignore-src \
    -r -y \
    --rosdistro "$ROS_DISTRO_NAME" \
    --skip-keys "ament_python python3-pyttsx3 python3-nltk"
fi

if [[ $SKIP_VENV -eq 0 ]]; then
  echo "[INFO] Ensuring python venv support..."
  require_cmd sudo
  require_cmd apt-get
  PY_MM="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
  VENV_PKG="python${PY_MM}-venv"
  if apt-cache show "$VENV_PKG" >/dev/null 2>&1; then
    sudo -H apt-get install -y "$VENV_PKG" python3-nltk
  else
    sudo -H apt-get install -y python3-venv python3-nltk
  fi

  if [[ ! -d .venv ]]; then
    echo "[INFO] Creating local venv: .venv"
    python3 -m venv .venv
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install -U pip
  python -m pip install pyttsx3 nltk mpu9250-jmdev
  python - <<'PY'
import pyttsx3, nltk, mpu9250_jmdev
print('python_deps_ok')
PY
fi

echo "[OK] Setup complete."
echo "[NEXT] Run: source scripts/setup_cloud_env.sh"
