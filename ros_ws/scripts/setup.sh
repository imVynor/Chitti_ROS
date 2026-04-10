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
  --skip-rosdep   Skip rosdep update/install
  --skip-venv     Skip local Python venv setup
  -h, --help      Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

set +u
source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
set -u

cd "$WS_DIR"

echo "[INFO] Workspace: $WS_DIR"
echo "[INFO] ROS_DISTRO: $ROS_DISTRO_NAME"

if [[ $SKIP_ROSDEP -eq 0 ]]; then
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
  sudo -H apt-get install -y python3.12-venv python3-nltk

  if [[ ! -d .venv ]]; then
    echo "[INFO] Creating local venv: .venv"
    python3 -m venv .venv
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install -U pip
  python -m pip install pyttsx3 nltk
  python - <<'PY'
import pyttsx3, nltk
print('python_deps_ok')
PY
fi

echo "[OK] Setup complete."
echo "[NEXT] Run: source scripts/setup_cloud_env.sh"
