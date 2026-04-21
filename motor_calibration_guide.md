# Motor Calibration Walkthrough

Because 4-Wheel Skid Steer robots don't have perfect motors (some will naturally spin 5% faster due to manufacturing differences), your robot will constantly veer to the left or right if left uncalibrated. 

To fix this, I previously built 4 independent calibration multipliers directly into your `esp32_firmware.ino`! Here is how you tune them.

## Step 1: Flash the Proportional Firmware
The simple `F/B/L/R` firmware you currently have installed completely ignores the calibration multipliers. You must flash the main production firmware back onto the ESP.
1. Connect the ESP32 to your laptop via USB.
2. Open `/home/anubhav-gupta/Chitti/esp32_firmware/esp32_firmware.ino` in the Arduino IDE.
3. Keep the robot's wheels **suspended in the air**.
4. Click **Upload**.

## Step 2: Use the Test Script
We need to send a constant `L150 R150` signal to the motors so we can visually measure and listen to their RPM to find out which one is spinning too fast.
1. While the ESP32 is still plugged into your laptop (or plugged into your Pi, it doesn't matter), open a terminal.
2. Ensure you have the test script I wrote for you earlier: `/home/anubhav-gupta/Chitti/esp_test.py`. 
   *(Make sure the script's `PORT` matches your USB port, e.g., `/dev/ttyUSB1` or `COM3` if you are running it on a Windows laptop)*.
3. Run `python3 esp_test.py`
4. Type `L150R150` and hit enter. All 4 wheels will start spinning continuously!

## Step 3: Find the Fast Wheel and Tune
Listen to the pitch of the motors, or look at the wheels. One or two of them will probably be spinning noticeably faster than the others.
Let's pretend your **Front Left** wheel is spinning way too fast.
1. In `esp_test.py`, type `L0R0` to stop the wheels.
2. Go back to the Arduino IDE on your laptop.
3. Look at the top of the `esp32_firmware.ino` script. You will see these lines:
   ```cpp
   float CALIB_FL = 1.0;
   float CALIB_RL = 1.0;
   float CALIB_FR = 1.0;
   float CALIB_RR = 1.0;
   ```
4. If the Front Left wheel is too fast, reduce its multiplier! Change `float CALIB_FL = 1.0;` to `0.85;`.
5. Click **Upload** on the Arduino IDE to flash the updated code.
6. Go back to `esp_test.py`, type `L150R150`, and check the wheels again! The Front Left wheel should now be matching the others.

Repeat this process of adjusting the `CALIB_` decimals between `0.5` and `1.0` until all 4 wheels spin perfectly identically!
