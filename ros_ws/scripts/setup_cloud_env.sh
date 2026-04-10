#!/usr/bin/env bash
set -eo pipefail

# Run this from anywhere; it resolves to the canonical tracked workspace.
WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ROS setup scripts can reference unset vars; avoid nounset errors here.
set +u
source /opt/ros/jazzy/setup.bash
set -u

# Activate local Python dependencies if present.
if [[ -f "$WS_DIR/.venv/bin/activate" ]]; then
  source "$WS_DIR/.venv/bin/activate"
fi

echo "Workspace: $WS_DIR"
echo "ROS_DISTRO: ${ROS_DISTRO:-unset}"
python3 -c "import sys; print('Python:', sys.executable)"
