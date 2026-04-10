# Chitti Cloud Workspace Pre-Operation README

Use this checklist before any demo, navigation test, or full stack launch.

## Scope

This runbook is for the canonical workspace at `/home/anish/Chitti/ros_ws/ros_ws`.

## 1. Pre-Operation Checklist

Run these checks in order:

1. Workspace path is correct.
2. ROS 2 Jazzy environment is available.
3. Python dependencies are active via local virtual environment.
4. Package dependencies are installed and resolvable.
5. Workspace builds successfully.
6. Required topics, services, and actions are visible after launch.

## 2. One-Time Setup (Cloud Machine)

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source /opt/ros/jazzy/setup.bash

# Install system dependencies from package manifests
rosdep update --rosdistro jazzy
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy

# Local python environment for pip-only deps
sudo apt-get install -y python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install pyttsx3 nltk
```

Notes:
- `ament_python` is a package build type, not a system apt dependency.
- `python3-pyttsx3` is typically not available on Ubuntu apt for this image, so use `.venv`.

## 3. Per-Session Setup

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh
```

Expected output includes:
- Workspace path
- `ROS_DISTRO: jazzy`
- Python executable from `.venv`

## 4. Pre-Launch Validation

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh

# Validate python runtime deps used by interaction/hmi
python3 -c "import pyttsx3, nltk; print('python_deps_ok')"

# Validate package dependency resolution
rosdep check --from-paths src --ignore-src --rosdistro jazzy --skip-keys='ament_python python3-pyttsx3 python3-nltk'

# Build check
colcon build --symlink-install
source install/setup.bash
```

## 5. Launch Commands

Core stack:

```bash
ros2 launch chitti_bringup robot.launch.py
```

Full HMI + interaction + navigation stack:

```bash
ros2 launch chitti_bringup hmi_system.launch.py
```

Navigation debug stack:

```bash
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=true use_rviz:=true
```

## 6. Operational Health Checks

In a second terminal:

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh
source install/setup.bash

ros2 topic list | grep -E '^/(fix|imu/data|goal_gps|global_path)$'
ros2 service list | grep /navigation/start_to_location
ros2 action list | grep /follow_path
```

Optional smoke test:

```bash
bash scripts/smoke_test_nav.sh
```

## 7. Common Failure Recovery

If package resolution or runtime behaves unexpectedly:

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
rm -rf build install log
source scripts/setup_cloud_env.sh
colcon build --symlink-install
source install/setup.bash
```

If ROS package discovery looks stale:

```bash
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONPATH ROS_PACKAGE_PATH
source /opt/ros/jazzy/setup.bash
source /home/anish/Chitti/ros_ws/ros_ws/install/setup.bash
ros2 pkg prefix chitti_bringup
```

## 8. Pre-Demo Go/No-Go

Proceed only if all are true:
- `python_deps_ok` prints successfully.
- `rosdep check` reports system dependencies satisfied.
- `colcon build` succeeds.
- Target launch command starts without missing package/import errors.
- Required navigation interfaces are visible in topic/service/action checks.
