#!/usr/bin/env bash
set -euo pipefail

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLEAN=0
FULL=0
PKG_LIST=""
ROS_DISTRO_NAME="${ROS_DISTRO:-jazzy}"
BUILD_TYPE="Release"

usage() {
  cat <<'EOF'
Usage: bash scripts/build.sh [options]

Fast build helper for Raspberry Pi.

Options:
  --ros-distro NAME   ROS distro to use (default: $ROS_DISTRO or jazzy)
  --build-type TYPE   CMake build type (default: Release)
  --clean              Remove build/install/log before building
  --full               Build all packages in src
  --pkg a,b,c          Build selected packages only
  -h, --help           Show this help

Defaults:
  - If --pkg is set: build selected packages.
  - Else if --full is set: build full workspace.
  - Else: build core runtime packages for faster iteration.
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
    --build-type)
      if [[ -z "${2:-}" ]]; then
        echo "[ERROR] --build-type requires a value"
        exit 2
      fi
      BUILD_TYPE="$2"
      shift
      ;;
    --clean) CLEAN=1 ;;
    --full) FULL=1 ;;
    --pkg)
      if [[ -z "${2:-}" ]]; then
        echo "[ERROR] --pkg requires a comma-separated value"
        exit 2
      fi
      PKG_LIST="$2"
      shift
      ;;
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

cd "$WS_DIR"

if [[ ! -f "/opt/ros/${ROS_DISTRO_NAME}/setup.bash" ]]; then
  echo "[ERROR] ROS distro '${ROS_DISTRO_NAME}' not found at /opt/ros/${ROS_DISTRO_NAME}"
  exit 1
fi

if [[ ! -d "$WS_DIR/src" ]]; then
  echo "[ERROR] Workspace source folder not found: $WS_DIR/src"
  exit 1
fi

if ! command -v colcon >/dev/null 2>&1; then
  echo "[ERROR] Required command not found: colcon"
  exit 1
fi

# For builds, prefer ROS system Python (contains rosidl build deps like em).
set +u
source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"
set -u

# If a virtualenv is active, disable it for colcon build steps.
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  deactivate || true
fi

if [[ $CLEAN -eq 1 ]]; then
  echo "[INFO] Cleaning build artifacts..."
  rm -rf build install log
fi

COLCON_ARGS=(
  --symlink-install
  --executor sequential
  --parallel-workers 1
  --event-handlers console_direct+
  --cmake-args
  -DCMAKE_BUILD_TYPE=${BUILD_TYPE}
  -DBUILD_TESTING=OFF
  -DPython3_EXECUTABLE=/usr/bin/python3
  -DPYTHON_EXECUTABLE=/usr/bin/python3
)

if [[ -n "$PKG_LIST" ]]; then
  IFS=',' read -r -a PKGS <<< "$PKG_LIST"
  echo "[INFO] Building selected packages: ${PKGS[*]}"
  colcon build "${COLCON_ARGS[@]}" --packages-select "${PKGS[@]}"
elif [[ $FULL -eq 1 ]]; then
  echo "[INFO] Building full workspace"
  colcon build "${COLCON_ARGS[@]}"
else
  CORE_PKGS=(
    chitti_msgs
    chitti_navigation
    chitti_system
    chitti_bringup
    chitti_interaction
    chitti_hmi
  )
  echo "[INFO] Building core runtime packages for faster iteration"
  colcon build "${COLCON_ARGS[@]}" --packages-up-to "${CORE_PKGS[@]}"
fi

if [[ -f install/setup.bash ]]; then
  # shellcheck disable=SC1091
  set +u
  source install/setup.bash
  set -u
fi

echo "[OK] Build complete."
