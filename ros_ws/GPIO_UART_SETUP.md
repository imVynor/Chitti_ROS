# NEO GPS via GPIO UART (No USB Adapter)

Direct GPIO connection for Raspberry Pi UART.

## Wiring (Raspberry Pi GPIO)

```
NEO Module    →  Raspberry Pi GPIO Pins
TX            →  GPIO 10 (RX, physical pin 19)
RX            →  GPIO 8  (TX, physical pin 24)
GND           →  GND (physical pin 25 or 39)
5V            →  5V (physical pin 2 or 4, with 3.3V converter)
```

**IMPORTANT**: NEO modules typically expect 5V input, but GPIO is 3.3V. Use:
- Logic level converter 5V↔3.3V (recommended)
- Or 3.3V voltage divider on RX line if NEO tolerates 3.3V input

## Enable UART on Raspberry Pi

### 1. Disable Serial Console (One-Time Setup)

The default Pi serial interface runs the login console. Disable it:

```bash
# Edit bootloader config
sudo raspi-config

# Navigate to: Interfacing Options → Serial Port
# - Disable login shell over UART (No)
# - Keep UART hardware enabled (Yes)
# Exit and reboot
```

Or manually:

```bash
# Edit boot configuration
sudo nano /boot/firmware/cmdline.txt

# Remove: console=serial0,115200
# Save and reboot

# Verify: should see /dev/ttyS0 or /dev/ttyAMA0
ls -la /dev/ttyS*
```

### 2. Verify GPIO UART Port

```bash
# Check which UART is available
ls -la /dev/ttyS* /dev/ttyAMA*

# For Raspberry Pi 4/5 with Device Tree: /dev/ttyS0
# For older Pi with Device Tree: /dev/ttyAMA0

# Test baud rate
stty -F /dev/ttyS0 9600 && cat /dev/ttyS0 | head -n 3
# Should show NMEA strings like: $GP...
```

## Configure ROS2 Launch for GPIO UART

Edit [ros_ws/src/chitti_bringup/launch/sensors.launch.py](https://github.com/imVynor/Chitti_ROS/blob/master/ros_ws/src/chitti_bringup/launch/sensors.launch.py):

```python
Node(
    package='nmea_navsat_driver',
    executable='nmea_serial_driver',
    name='nmea_navsat_driver',
    output='screen',
    parameters=[{
        'port': '/dev/ttyS0',      # ← Change to /dev/ttyAMA0 if using older Pi
        'baud': 9600,
        'frame_id': 'gps_link',
        'use_rostime': True
    }],
    remappings=[
        ('fix', '/fix')
    ]
),
```

## Test GPIO UART Connection

```bash
# 1. Manual serial test
stty -F /dev/ttyS0 9600 raw -echo
cat /dev/ttyS0

# 2. With ROS2 driver
cd /home/anish/Chitti/ros_ws/ros_ws
source scripts/setup_cloud_env.sh
source install/setup.bash

ros2 launch chitti_bringup sensors.launch.py

# 3. In another terminal, verify GPS fix
source scripts/setup_cloud_env.sh
source install/setup.bash
ros2 topic echo /fix --once
```

## Troubleshooting GPIO UART

**Issue: /dev/ttyS0 not found**
```bash
# Enable UART in Device Tree
sudo raspi-config → Interfacing Options → Serial Port → Yes (keep both options enabled)
sudo reboot
```

**Issue: Permission denied on ttyS0**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
newgrp dialout
```

**Issue: No NMEA data but port opens**
1. Check wiring (TX ↔ RX crossed correctly)
2. Verify 5V→3.3V conversion if needed
3. Test antenna placement (move outdoors/near window)
4. Verify baud rate: `stty -F /dev/ttyS0 115200` (some NEO modules use 115200)

**Issue: Intermittent GPS lock**
- Cold start takes 30-60 seconds initially
- Hot start should be faster (few seconds)
- Ensure clear sky view for satellite acquisition

## Quick Setup Checklist

- [ ] Wire NEO TX→GPIO10, RX→GPIO8, GND, 5V (with converter)
- [ ] Disable serial console: `sudo raspi-config` → Interfacing Options → Serial
- [ ] Verify port: `ls /dev/ttyS*`
- [ ] Test manual read: `stty -F /dev/ttyS0 9600 && cat /dev/ttyS0`
- [ ] Update sensors.launch.py port to `/dev/ttyS0`
- [ ] Build: `bash scripts/build.sh`
- [ ] Launch: `ros2 launch chitti_bringup sensors.launch.py`
- [ ] Verify: `ros2 topic echo /fix --once`

## Reference

- **Raspberry Pi UART Pins**: https://www.raspberrypi.com/documentation/computers/os.html#configure-uart
- **Pi Pinout**: https://pinout.xyz/ (search "UART" or "serial")
- **Logic Level Converter**: Adafruit TXB0104, SparkFun BOB-12009, etc.
