# Chitti Robot: Binary Logic Demonstration Guide

This guide is intended for team members who need to safely demonstrate the Chitti robot navigating via simple "Bang-Bang" binary logic (`F`, `B`, `L`, `R`, `S`). In this mode, the robot ignores smooth analog acceleration and simply snaps to a hardcoded speed to execute turns and straight lines.

> [!WARNING]
> **Safety First:** Binary mode snaps the robot to 80% power instantly. **ALWAYS** run your first test with the robot suspended on a box so the wheels are not touching the ground.

---

## Step 1: Prep the ESP32 Hardware

The ESP32 microcontroller must be flashed with the specific firmware that understands ASCII letters instead of Proportional Math.

1. Connect the ESP32 to your laptop using a data-capable USB cable.
2. Open the **Arduino IDE** software.
3. Open the file: `/home/anubhav-gupta/Chitti/esp32_firmware/binary_test_firmware.ino`
4. Select your ESP32 board and COM port in the `Tools` menu.
5. Click **Upload**. 
   - *(If you see "Error Status 2" connecting, hold down the physical `BOOT` button on the ESP32 until the screen says "Writing...").*
6. Once uploaded, unplug the ESP32 from the laptop and plug it into the Raspberry Pi via USB. Complete the wiring to the MDD3A motor drivers.

---

## Step 2: Test 1 - Teleop (Keyboard Control)

Before bringing up the AI pathfinding, we must ensure the C++ Driver correctly translates velocity math into `F/B/L/R` letters over the serial port.

1. Open a terminal on the Raspberry Pi and launch the core robot nodes:
   ```bash
   source /opt/ros/jazzy/setup.bash
   source /home/anubhav-gupta/Chitti/ros_ws/install/setup.bash
   ros2 launch chitti_bringup robot.launch.py
   ```
2. **Open a second terminal window** on the Pi and launch the keyboard controller:
   ```bash
   source /opt/ros/jazzy/setup.bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```
3. Use the keys specified on the screen (usually `i` for Forward, `k` for Stop, `j` for Left) to drive the wheels. The wheels should instantly snap to speed. 

If this works flawlessly, proceed to Step 3. Close the `teleop_twist_keyboard` terminal.

---

## Step 3: Test 2 - Nav2 Autonomous Demonstration

Now that the hardware response is validated, we will command Nav2 to drive the robot. Nav2 will calculate the required trajectory, and our C++ driver will automatically translate that trajectory into the simple binary letters for the ESP32.

1. Keep the first terminal running (`ros2 launch chitti_bringup robot.launch.py`).
2. Open a new terminal on your laptop (or the Pi) to run RViz visualization:
   ```bash
   source /opt/ros/jazzy/setup.bash
   source /home/anubhav-gupta/Chitti/ros_ws/install/setup.bash
   ros2 run rviz2 rviz2 -d /home/anubhav-gupta/Chitti/ros_ws/src/chitti_bringup/rviz/nav2_default_view.rviz
   ```
3. Open your Custom UI Interface.
4. Use your UI to select your destination goal. 
5. The UI will send the coordinates to Nav2, and the robot will immediately start driving! 

*(Note: Although you don't need RViz to drive, you can optionally run `ros2 run rviz2 rviz2` in the background just to watch the AI's "thought process" as it drives!)* 

---

> [!IMPORTANT]
> **Reverting back for Production:**
> If you want to use the sophisticated Proportional Math to achieve smooth cornering and perfect odometry in the future, you must flash `esp32_firmware.ino` back onto the ESP32, and revert the translation logic in the ROS 2 C++ workspace (`cytron_hardware_interface.cpp`).
