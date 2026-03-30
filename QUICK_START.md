# Quick Start

This guide gets the Chitti workspace running in a few minutes.

## 1) Build Once

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

## 2) Source Environment (Every New Terminal)

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 3) Start the System

### Terminal 1: Core system

```bash
ros2 launch chitti_bringup robot.launch.py
```

### Terminal 2: HMI + interaction + navigation

```bash
ros2 launch chitti_bringup hmi_system.launch.py
```

## 4) Quick Health Checks

```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 action list
```

Check that Nav2 FollowPath is available:

```bash
ros2 action list | grep /follow_path
```

## 5) Navigation-Only Debug Mode (Optional)

```bash
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=true use_rviz:=true
```

## 6) Smoke Test (Optional)

```bash
cd ~/Chitti/ros_ws
bash scripts/smoke_test_nav.sh
```

Run with custom destination id:

```bash
bash scripts/smoke_test_nav.sh library
```

## 7) Common Commands

```bash
# Build only one package
colcon build --packages-select chitti_navigation

# Launch navigation stack only
ros2 launch chitti_bringup navigation.launch.py

# Run a single node directly
ros2 run chitti_navigation destination_manager_node
```

## 8) Troubleshooting

### `package 'chitti_bringup' not found`

```bash
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONPATH ROS_PACKAGE_PATH
source /opt/ros/jazzy/setup.bash
source ~/Chitti/ros_ws/install/setup.bash
ros2 pkg prefix chitti_bringup
```

### Clean rebuild

```bash
cd ~/Chitti/ros_ws
rm -rf build install log
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### View latest colcon logs

```bash
ls -la log/latest
```

For architecture and package details, see [README.md](README.md).
