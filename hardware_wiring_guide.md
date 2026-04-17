# Chitti Hardware Wiring Guide

This guide maps out the exact physical pin connections required on your Raspberry Pi to match the custom ROS 2 parameters defined in your software stack.

## 1. Sensor Wiring

**GPS Module (NEO-6M / Serial)**
Defined in: `sensors.launch.py`
The physical module must be connected to the Raspberry Pi over USB (typically over a USB-TTL adapter) such that it mounts as `ttyUSB0`.
- **Tx (GPS)** -> **Rx (USB-TTY)**
- **Rx (GPS)** -> **Tx (USB-TTY)**
- **VCC** -> **3.3V or 5V** (Please check module requirements)
- **GND** -> **GND**
*Software Expects:* `/dev/ttyUSB0` at 9600 baud.

**IMU Module (MPU9250)**
Defined in: `sensors.launch.py` and `mpu9250_node`
The IMU runs over standard I2C connection #1.
- **SDA** -> **Physical Pin 3** (GPIO 2 / I2C1 SDA)
- **SCL** -> **Physical Pin 5** (GPIO 3 / I2C1 SCL)
- **VCC** -> **3.3V** 
- **GND** -> **GND**
*Software Expects:* I2C Bus 1 at Address `0x68`.

---

## 2. Motor Driver Wiring (Cytron MDD10A)

Defined in: `chitti.urdf.xacro` (CytronHardwareInterface params)
Chitti uses a 4-wheel skid-steer configuration driven by 2 Cytron MDD10A dual-channel drivers (or functionally equivalent).

> **Note on GPIO Numbers:** All pin numbers below are BCM (Broadcom chip specifications) GPIO numbers, NOT the physical board pin numbers!

### Motor Driver 1 (Left Side)
Controls the front-left and rear-left wheels.
- **FL PWM Pin:** GPIO 12 
- **FL DIR Pin:** GPIO 5 
- **RL PWM Pin:** GPIO 13 
- **RL DIR Pin:** GPIO 6 

### Motor Driver 2 (Right Side)
Controls the front-right and rear-right wheels.
- **FR PWM Pin:** GPIO 18 
- **FR DIR Pin:** GPIO 16 
- **RR PWM Pin:** GPIO 19 
- **RR DIR Pin:** GPIO 20 

### Motor Driver Grounding
> ⚠️ **CRITICAL SAFETY WARNING** ⚠️
> You MUST wire a common ground! Run a wire bridging the GND terminal of the Raspberry Pi directly to the GND terminal of *both* Cytron motor drivers. Failing to establish a common ground will cause floating PWM signals, resulting in erratic, high-speed runaway motors that can physically injure you.
