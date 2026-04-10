# Real Sensors Testing Guide - NEO GPS Module

This guide explains how to integrate your u-blox NEO GPS/GNSS module with Chitti and test with real sensors.

## Hardware Setup

### 1. NEO Module Wiring (UART/USB)

**Option A: USB-to-Serial Dongle (Recommended for Pi)**
```
NEO Module    →  USB Adapter    →  Raspberry Pi USB
TX            →  RX
RX            →  TX
GND           →  GND
5V            →   5V (or 3V3 with logic converter)
```

**Option B: Direct UART (Pi GPIO pins)**

See [GPIO_UART_SETUP.md](GPIO_UART_SETUP.md) for detailed GPIO wiring and configuration.

```
NEO Module    →  Raspberry Pi GPIO
TX            →  GPIO 10 (RX, pin 19)
RX            →  GPIO 8 (TX, pin 24)
GND           →  GND (e.g., pin 25)
5V            →  5V (pin 2 or 4, with 3.3V converter if needed)
```

### 2. Detect Serial Port

```bash
# List all connected USB/serial devices
ls -lh /dev/ttyUSB* /dev/ttyACM* /dev/ttyS*

# If using USB adapter, should see /dev/ttyUSB0 (or /dev/ttyUSB1, /dev/ttyACM0, etc.)
# If using UART pins, should see /dev/ttyS0 or /dev/ttyAMA0

# Test connection (UART at 9600 baud, typical for NEO modules)
stty -F /dev/ttyUSB0 9600 && cat /dev/ttyUSB0
# You should see NMEA strings like: $GPGGA,123519,4807.038,N,01131.000,E,...
```

## Configuration

### 1. Update Serial Port in Launch File

Edit [ros_ws/src/chitti_bringup/launch/sensors.launch.py](https://github.com/imVynor/Chitti_ROS/blob/master/ros_ws/src/chitti_bringup/launch/sensors.launch.py):

```python
Node(
    package='nmea_navsat_driver',
    executable='nmea_serial_driver',
    name='nmea_navsat_driver',
    output='screen',
    parameters=[{
        'port': '/dev/ttyUSB0',  # ← Change this to your detected port
        'baud': 9600,             # ← Verify baud rate matches your NEO module
        'frame_id': 'gps_link',
        'use_rostime': True
    }],
    remappings=[
        ('fix', '/fix')
    ]
),
```

Common baud rates:
- **9600**: Default for most u-blox NEO modules
- **115200**: Some newer models default to this
- Check your NEO module datasheet or AT command `AT+IPR?`

### 2. Enable Real Sensors at Launch

Replace `use_fake_sensors:=true` with `use_fake_sensors:=false`:

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh
source install/setup.bash

# Option A: Core system with real sensors only
ros2 launch chitti_bringup robot.launch.py use_fake_sensors:=false

# Option B: Navigation stack with real sensors
ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=false is_simulation:=false use_rviz:=true
```

## Verification

### 1. Check Sensor Topics

In a second terminal:

```bash
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh
source install/setup.bash

# View GPS fix data
ros2 topic echo /fix --once

# Should output (example):
# Header:
#   stamp:
#     sec: 1712745600
#     nanosec: 123456789
#   frame_id: gps_link
# status: 0         # 0 = GPS fix valid
# latitude: 22.1234
# longitude: 79.5678
# altitude: 456.78
# ...

# View IMU data  
ros2 topic echo /imu/data --once
```

### 2. Test Navigation with Real GPS

```bash
# Start navigation with real sensors
ros2 launch chitti_bringup navigation.launch.py \
  use_fake_sensors:=false \
  is_simulation:=false \
  use_rviz:=true

# In another terminal, check EKF fusion
ros2 node list | grep -E 'ekf|navsat'
ros2 topic echo /odometry/filtered --once
```

### 3. Run Navigation Service

```bash
# Get current location
ros2 topic echo /fix --once

# Trigger navigation to a known campus location
ros2 service call /navigation/start_to_location \
  chitti_msgs/srv/StartNavigation \
  "{destination_id: 'library', guided_tour_mode: false, waypoints: [], accessibility_route: false}"

# Check planned path
ros2 topic echo /global_path --once
```

## Troubleshooting

### No GPS Fix (status != 0)

**Symptom**: `/fix` header shows `status: -1` or `status: 1`

**Solutions**:
1. Wait 30-60 seconds for cold start (first power-on)
2. Move outdoors or near a window for satellite lock
3. Check antenna connection and orientation
4. Verify baud rate matches your NEO module

```bash
# Monitor GPS status in real-time
while true; do 
  echo "==== GPS Status ====" 
  ros2 topic echo /fix --once | grep -E 'status|latitude|longitude' 
  sleep 2
done
```

### No Data on /fix Topic

**Symptom**: `ros2 topic echo /fix` times out

**Solutions**:
1. Verify port is correct: `ls /dev/ttyUSB*`
2. Check baud rate: `stty -F /dev/ttyUSB0`
3. View driver logs: `ros2 launch chitti_bringup sensors.launch.py 2>&1 | grep -i error`
4. Manually test serial:
   ```bash
   cat /dev/ttyUSB0 | head -n 5
   # Should show NMEA strings
   ```

### Serial Permission Denied

```bash
# Add user to dialout group (one-time setup)
sudo usermod -a -G dialout $USER
# Log out and back in, or: newgrp dialout
```

## Quick Test Workflow

1. Connect NEO module via USB
2. Detect port: `ls /dev/ttyUSB*`
3. Update [sensors.launch.py](https://github.com/imVynor/Chitti_ROS/blob/master/ros_ws/src/chitti_bringup/launch/sensors.launch.py) with correct port/baud
4. Build: `bash scripts/build.sh`
5. Run:
   ```bash
   source scripts/setup_cloud_env.sh
   source install/setup.bash
   ros2 launch chitti_bringup navigation.launch.py use_fake_sensors:=false is_simulation:=false use_rviz:=true
   ```
6. In another terminal, verify:
   ```bash
   source scripts/setup_cloud_env.sh
   source install/setup.bash
   ros2 topic echo /fix --once
   ```

## Reference

- **NMEA Driver Docs**: http://wiki.ros.org/nmea_navsat_driver
- **u-blox NEO Datasheets**: https://www.u-blox.com/en/product/neo-6-series
- **Common NMEA Sentences**: `$GPGGA` (position), `$GPGSA` (fix status), `$GPGSV` (satellites)
