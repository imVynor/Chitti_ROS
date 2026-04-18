# Chitti Hardware Wiring & Connection Guide

This document is your master checklist for physically building the robot. It covers connecting the Raspberry Pi to your Cytron MDD3A motor drivers, your NEO-6M GPS, your MPU9250 IMU, and ensuring the software matches the physical wires.

> [!CAUTION]
> **Power Supply Rule #1:** NEVER power the motors directly from the Raspberry Pi. The Raspberry Pi must have its own 5V power source (like a power bank). The motors must run off a separate battery (like a 12V LiPo). 
> **However, you MUST connect the Ground (GND) of the Raspberry Pi to the Ground (GND) of the motor drivers.** If they don't share a common ground, the PWM signals will fail!

---

## 1. Motor Drivers (Offloaded to ESP32)

We are offloading all motor PWM generation from the Raspberry Pi to an external ESP32 microcontroller over a Serial connection. This frees up 8 Raspberry Pi GPIO pins!

### 1a. Raspberry Pi -> ESP32 Data Connection
You have two options to connect the Pi to the ESP32 to transmit the `L[pwm]R[pwm]\n` commands:
**Option A (USB Cable):** Plug the ESP32 directly into the Raspberry Pi using a standard Micro-USB/USB-C cable. The Pi will recognize it as `/dev/ttyUSB1` (or similar). This is the easiest and most robust method.
**Option B (Hardware UART):** Connect Pi **TX (GPIO 14)** to ESP32 **RX (Pin 16)**, and Pi **RX (GPIO 15)** to ESP32 **TX (Pin 17)**. Note: if your GPS is using these pins, you must use Option A!

### 1b. ESP32 -> MDD3A Wiring Map
The ESP32 runs our custom `esp32_firmware.ino` sketch which maps to these pins:

*   **MDD3A Board 1 (Left Side)**
    *   **Front-Left Forward (A):** ESP32 Pin `26`
    *   **Front-Left Backward (B):** ESP32 Pin `27`
    *   **Rear-Left Forward (A):** ESP32 Pin `14`
    *   **Rear-Left Backward (B):** ESP32 Pin `12`
*   **MDD3A Board 2 (Right Side)**
    *   **Front-Right Forward (A):** ESP32 Pin `33`
    *   **Front-Right Backward (B):** ESP32 Pin `32`
    *   **Rear-Right Forward (A):** ESP32 Pin `25`
    *   **Rear-Right Backward (B):** ESP32 Pin `4`

> [!IMPORTANT]  
> If you wire them differently, you must open `esp32_firmware.ino` and update the `#define` pin numbers!

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
- [ ] **Elevated Blocks:** The first time you launch, **put the robot on a box so the wheels are not touching the ground!** Send a `/cmd_vel` twisting command and verify the wheels are spinning in the correct directions. If a wheel spins backward when it should go forward, simply flip the Motor A and Motor B wires plugged into the MDD3A green terminal block for that wheel.
