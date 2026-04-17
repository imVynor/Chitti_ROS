# Chitti Hardware Wiring & Connection Guide

This document is your master checklist for physically building the robot. It covers connecting the Raspberry Pi to your Cytron MDD10A motor drivers, your NEO-6M GPS, your MPU9250 IMU, and ensuring the software matches the physical wires.

> [!CAUTION]
> **Power Supply Rule #1:** NEVER power the motors directly from the Raspberry Pi. The Raspberry Pi must have its own 5V power source (like a power bank). The motors must run off a separate battery (like a 12V LiPo). 
> **However, you MUST connect the Ground (GND) of the Raspberry Pi to the Ground (GND) of the motor drivers.** If they don't share a common ground, the PWM signals will fail!

---

## 1. Motor Drivers (Cytron MDD10A)

Since Chitti is a 4-wheel drive robot, and the MDD10A is a *dual-channel* driver (supports 2 motors), you will need **two MDD10A boards** to control all 4 wheels independently.

Each MDD10A channel requires 2 GPIO pins from the Pi: a **PWM pin** (Speed) and a **DIR pin** (Direction / Forward-Reverse).

### Recommended Wiring Map
You can use any standard GPIO pins, but `pigpio` prefers pins that don't conflict with I2C/Serial. Here is the layout mapped in your software:

*   **MDD10A Board 1 (Left Side)**
    *   **Front-Left Motor:**
        *   PWM: Pi GPIO `12`
        *   DIR: Pi GPIO `5`
    *   **Rear-Left Motor:**
        *   PWM: Pi GPIO `13`
        *   DIR: Pi GPIO `6`
*   **MDD10A Board 2 (Right Side)**
    *   **Front-Right Motor:**
        *   PWM: Pi GPIO `18`
        *   DIR: Pi GPIO `16`
    *   **Rear-Right Motor:**
        *   PWM: Pi GPIO `19`
        *   DIR: Pi GPIO `20`

> [!IMPORTANT]  
> If you wire them differently, you must open `chitti.urdf.xacro` in your ROS workspace and change the `<param name="fl_pwm_pin">12</param>` numbers to match your real pins!

---

## 2. GPS Module (NEO-6M)

The NEO-6M communicates via **UART (Serial)**. 

### Wiring
1.  **VCC:** Connect to Pi `3.3V` or `5V` (Check your specific NEO-6M module's rating).
2.  **GND:** Connect to Pi `GND`.
3.  **TX (Transmit):** Connect to Pi **RX** (GPIO 15 / UART0 RX) OR to a USB-TTL converter.
4.  **RX (Receive):** Connect to Pi **TX** (GPIO 14 / UART0 TX) OR to a USB-TTL converter.
    *(Note: TX goes to RX, and RX goes to TX!)*

### Software Sync
*   If using direct GPIO pins, enable the Serial Port on your Pi. Run `sudo raspi-config` -> Interfacing Options -> Serial -> *No* to login shell, *Yes* to hardware port.
*   Your GPS will likely appear as `/dev/serial0` (if GPIO) or `/dev/ttyUSB0` (if USB). You need to update `sensors.launch.py` to use `{'port': '/dev/...'}` to match your physical choice.

---

## 3. IMU sensor (MPU9250)

The MPU9250 communicates via **I2C**, which is a high-speed bus.

### Wiring
1.  **VCC:** Connect to Pi `3.3V` (Do NOT use 5V or you will fry the IMU).
2.  **GND:** Connect to Pi `GND`.
3.  **SDA (Data):** Connect to Pi **SDA** (GPIO 2 / Pin 3).
4.  **SCL (Clock):** Connect to Pi **SCL** (GPIO 3 / Pin 5).

### Software Sync
*   You must enable I2C on your Pi. Run `sudo raspi-config` -> Interfacing Options -> I2C -> *Yes*.
*   Run the command `i2cdetect -y 1` in the Pi terminal to verify the IMU is seen. It should show up as address `0x68`.

---

## 4. Raspberry Pi System Checklist

Before you run the master `robot.launch.py` on the physical Pi, check off these 3 things:

- [ ] **Pigpio Daemon:** Because our C++ driver uses `pigpio` to cleanly generate hardware PWM signals, it requires root-level memory access. You may need to run `sudo systemctl enable pigpiod` and `sudo systemctl start pigpiod` on your Pi so the background service is running before ROS starts.
- [ ] **Compile Flag:** When you copy your workspace to the Pi, you MUST build it with the hardware flag turned on so the C++ motor driver actually sends electricity to the pins:
  ```bash
  colcon build --cmake-args -DUSE_PIGPIO=ON
  ```
- [ ] **Elevated Blocks:** The first time you launch, **put the robot on a box so the wheels are not touching the ground!** Send a `/cmd_vel` twisting command and verify the wheels are spinning in the correct directions. If a wheel spins backward when it should go forward, simply flip the Motor A and Motor B wires plugged into the MDD10A green terminal block for that wheel.
