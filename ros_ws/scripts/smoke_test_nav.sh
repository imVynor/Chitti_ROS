#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/smoke_test_nav.log"

DESTINATION_ID="${1:-library}"

if [[ ! -f "${ROOT_DIR}/install/setup.bash" ]]; then
  echo "[FAIL] install/setup.bash not found. Build first:"
  echo "       cd ${ROOT_DIR} && colcon build --symlink-install"
  exit 1
fi

set +u
source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
source "${ROOT_DIR}/install/setup.bash"
set -u

required_packages=(
  chitti_bringup
  chitti_navigation
  chitti_msgs
)

for pkg in "${required_packages[@]}"; do
  if ! ros2 pkg prefix "${pkg}" >/dev/null 2>&1; then
    echo "[FAIL] Package not found in sourced environment: ${pkg}"
    exit 1
  fi
done

cleanup() {
  set +e
  if [[ -n "${LAUNCH_PID:-}" ]] && kill -0 "${LAUNCH_PID}" 2>/dev/null; then
    kill "${LAUNCH_PID}" 2>/dev/null
    sleep 1
    kill -9 "${LAUNCH_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

wait_for_service() {
  local service="$1"
  local timeout_s="$2"
  local start
  start="$(date +%s)"
  while true; do
    if ros2 service list 2>/dev/null | grep -Fxq "${service}"; then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_s )); then
      return 1
    fi
    sleep 1
  done
}

wait_for_action() {
  local action_name="$1"
  local timeout_s="$2"
  local start
  start="$(date +%s)"
  while true; do
    if ros2 action list 2>/dev/null | grep -Fxq "${action_name}"; then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_s )); then
      return 1
    fi
    sleep 1
  done
}

wait_for_topic() {
  local topic="$1"
  local timeout_s="$2"
  local start
  start="$(date +%s)"
  while true; do
    if ros2 topic list 2>/dev/null | grep -Fxq "${topic}"; then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_s )); then
      return 1
    fi
    sleep 1
  done
}

wait_for_global_path() {
  local tmp_out
  tmp_out="$(mktemp)"

  timeout 30s ros2 topic echo /global_path --once >"${tmp_out}" 2>&1 &
  local echo_pid=$!
  sleep 0.5

  if ! wait_for_service /navigation/start_to_location 20; then
    echo "[FAIL] Service /navigation/start_to_location did not appear"
    kill "${echo_pid}" 2>/dev/null || true
    rm -f "${tmp_out}"
    return 1
  fi
  sleep 5
  echo "[INFO] Triggering navigation service for destination_id=${DESTINATION_ID}"
  if ! timeout 20s ros2 service call /navigation/start_to_location chitti_msgs/srv/StartNavigation "{destination_id: '${DESTINATION_ID}', guided_tour_mode: false, waypoints: [], accessibility_route: false}" >/dev/null; then
    echo "[FAIL] Service call timed out or failed"
    kill "${echo_pid}" 2>/dev/null || true
    rm -f "${tmp_out}"
    return 1
  fi

  if wait "${echo_pid}"; then
    rm -f "${tmp_out}"
    return 0
  fi

  echo "[DEBUG] /global_path echo output:"
  cat "${tmp_out}" || true
  rm -f "${tmp_out}"
  return 1
}

echo "[INFO] Starting navigation launch... logs: ${LOG_FILE}"
: > "${LOG_FILE}"
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=true >> "${LOG_FILE}" 2>&1 &
LAUNCH_PID=$!

sleep 4

if ! kill -0 "${LAUNCH_PID}" 2>/dev/null; then
  echo "[FAIL] Navigation launch exited early"
  echo "[DEBUG] Last launch log lines:"
  tail -n 80 "${LOG_FILE}" || true
  exit 1
fi

echo "[INFO] Waiting for required topics..."
for topic in /fix /imu/data /goal_gps /global_path; do
  if wait_for_topic "${topic}" 60; then
    echo "[PASS] Topic available: ${topic}"
  else
    echo "[FAIL] Topic not available in time: ${topic}"
    echo "[HINT] Check ${LOG_FILE}"
    exit 1
  fi
done

echo "[INFO] Waiting for Nav2 FollowPath action..."
if wait_for_action /follow_path 45; then
  echo "[PASS] Action available: /follow_path"
else
  echo "[FAIL] Action not available in time: /follow_path"
  echo "[HINT] Check ${LOG_FILE}"
  exit 1
fi

echo "[INFO] Waiting for global path after service call..."
if wait_for_global_path; then
  echo "[PASS] /global_path published after service trigger"
else
  echo "[FAIL] /global_path not received after service trigger"
  echo "[HINT] Check ${LOG_FILE}"
  exit 1
fi

echo "[PASS] Navigation smoke test succeeded"
echo "[INFO] Launch log: ${LOG_FILE}"
