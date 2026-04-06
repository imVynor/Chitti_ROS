# Motor Driver & Sensor Integration Walkthrough

## Summary
Implemented the full `ros2_control` hardware interface stack to drive Chitti's 4 motors from Raspberry Pi GPIO via `pigpio`. Additionally, completed the **Sensor Fusion layer**, integrating GPS/IMU standard ROS 2 drivers, fusing physical odometry into the EKF, and building a master controller launcher.

## Files Created / Modified

### 1. Hardware Control layer (`chitti_control`)

| File | Purpose |
|------|---------|
| [cytron_hardware_interface.cpp](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_control/src/cytron_hardware_interface.cpp) | C++ `SystemInterface` plugin for physical wheels. converts rad/s → PWM duty (0-255). |
| [controllers.yaml](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_control/config/controllers.yaml) | Config for `diff_drive_controller` and `joint_state_broadcaster`. |
| [chitti.urdf.xacro](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_description/urdf/chitti.urdf.xacro) | Modified to expose GPIO pins to the controller manager. |
| [hardware.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/hardware.launch.py) | Launches the motor stack. |

### 2. Sensor & Navigation Fusion (`chitti_bringup`)

| File | Change / Purpose |
|------|--------|
| [sensors.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/sensors.launch.py) | Replaced diagnostic placeholders with actual `nmea_navsat_driver` (for GPS over serial) and `mpu9250_node` (for IMU over I2C). Includes parameterized ports. |
| [ekf.yaml](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/config/ekf.yaml) | Added `odom1: /odom` to fuse mathematical wheel spins (XY velocities and Yaw rotation) alongside GPS and IMU. Prevents catastrophic localization failure during brief GPS dropouts. |
| [navigation.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/navigation.launch.py) | Added `is_simulation` flag to conditionally drop the hardcoded `map->odom` static TF lock. This hands spatial tracking power fully to the EKF sensor fusion algorithms. |
| [robot.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/robot.launch.py) | **[NEW]** The absolute Master sequence. Simultaneously manages hardware, sensors, and the Nav2 AI in exactly the right order to ensure system stability. |

## Architecture

```mermaid
graph TD
    subgraph Navigation AI
        N2[Nav2 Route] --> CV[/cmd_vel]
    end

    subgraph Hardware Layer
        CV --> DDC[diff_drive_controller]
        DDC --> CHI[CytronHardwareInterface]
        CHI --> P[GPIO Pins] --> Motors
        DDC --> OD[/odom Velocity]
    end

    subgraph Sensory Layer
        GPS[NEO-6M Serial] --> F[/fix]
        IMU[MPU9250 I2C] --> IMD[/imu/data]
    end

    subgraph EKF Fusion
        F --> EKFnode
        IMD --> EKFnode
        OD --> EKFnode
        EKFnode --> TF[map -> odom -> base_link]
    end
    TF --> N2
```

## How to Run the Real Robot

When deployed to the actual Raspberry Pi, this single command orchestrates everything:

```bash
cd ~/Chitti/ros_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon build --cmake-args -DUSE_PIGPIO=ON
ros2 launch chitti_bringup robot.launch.py
```

## Next Steps Before Raspberry Pi Deployment

> [!WARNING]  
> **1. Update GPS Serial Port:** In [sensors.launch.py](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/launch/sensors.launch.py), I set the port to `/dev/ttyUSB0`. If you plug the GPS natively into Pi headers (like `/dev/serial0`), update that string.
> **2. The IMU node:** The plan currently uses `mpu9250driver`. Depending on exactly how you read your IMU, you may need to use `rosdep install` to get standard packages, or replace that node with a custom python file reading `smbus`.
> **3. Update GPIO Pins:** Change the placeholders in [chitti.urdf.xacro](file:///home/anubhav-gupta/Chitti/ros_ws/src/chitti_description/urdf/chitti.urdf.xacro) to your actual wiring layout!
