# Chitti ROS 2 Workspace

ROS 2 workspace for the Chitti campus guide robot stack, including:
- system management
- HMI (touchscreen + voice web interface)
- interaction (NLP/intent/response)
- navigation
- custom interfaces (`chitti_msgs`)

For a minimal runbook, see [QUICK_START.md](QUICK_START.md).
For pre-operation checks before launches, see [PREOPER_README.md](PREOPER_README.md).
For real sensor integration (NEO GPS), see [SENSOR_INTEGRATION.md](SENSOR_INTEGRATION.md).
For GPIO UART setup (direct Pi pins), see [GPIO_UART_SETUP.md](GPIO_UART_SETUP.md).

## Verified Packages

Active packages in `src/`:
- `chitti_bringup`
- `chitti_msgs`
- `chitti_hmi`
- `chitti_interaction`
- `chitti_navigation`
- `chitti_system`

Additional folders (`chitti_control`, `chitti_description`, `chitti_sensors`, `chitti_simulation`) exist for expansion/integration.

## Prerequisites

- Ubuntu Linux
- ROS 2 Jazzy installed at `/opt/ros/jazzy`
- `colcon` and `rosdep`

Install dependencies:

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

## Build

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Run

### 1) Core system only

```bash
ros2 launch chitti_bringup robot.launch.py
```

### 2) Full app stack (HMI + interaction + navigation)

```bash
ros2 launch chitti_bringup hmi_system.launch.py
```

### 3) Navigation debug stack

```bash
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=true use_rviz:=true
```

## Launch Files

In `src/chitti_bringup/launch`:
- `robot.launch.py`: system manager nodes (`chitti_system`)
- `hmi_system.launch.py`: HMI + interaction nodes and includes navigation launch
- `navigation.launch.py`: navigation nodes, optional fake sensors, Nav2 controller server, RViz
- `sensors.launch.py`: placeholder sensor launch

## Navigation: Use and Test

### Start navigation stack

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=true use_rviz:=true
```

### Verify navigation runtime

In a second terminal (after sourcing environment):

```bash
ros2 topic list | grep -E '^/(fix|imu/data|goal_gps|global_path)$'
ros2 service list | grep /navigation/start_to_location
ros2 action list | grep /follow_path
```

### Trigger a manual navigation request

```bash
ros2 service call /navigation/start_to_location chitti_msgs/srv/StartNavigation "{destination_id: 'library', guided_tour_mode: false, waypoints: [], accessibility_route: false}"
```

Watch output path:

```bash
ros2 topic echo /global_path --once
```

### Run automated smoke test

```bash
cd ~/Chitti/ros_ws
bash scripts/smoke_test_nav.sh
```

Optional destination override:

```bash
bash scripts/smoke_test_nav.sh library
```

## Useful Runtime Checks

```bash
# Check discovered packages
ros2 pkg list | grep '^chitti_'

# Check key topics/services/actions
ros2 topic list
ros2 service list
ros2 action list
```

## Troubleshooting

### Rebuild clean

```bash
cd ~/Chitti/ros_ws
rm -rf build install log
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### `package 'chitti_bringup' not found`

```bash
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONPATH ROS_PACKAGE_PATH
source /opt/ros/jazzy/setup.bash
source ~/Chitti/ros_ws/install/setup.bash
ros2 pkg prefix chitti_bringup
```

### Logs

```bash
ls log/latest
```

## Repository Layout

- `src/`: source packages
- `scripts/`: helper scripts (including smoke tests)
- `build/`, `install/`, `log/`: colcon artifacts

## License

Apache License 2.0
