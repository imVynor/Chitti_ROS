import serial
import time

# Set up the serial connection
# '/dev/serial0' points to the physical GPIO UART pins.
# If you are using a USB cable instead, change this to '/dev/ttyUSB1' or '/dev/ttyUSB0'
PORT = '/dev/ttyUSB1' 
BAUD_RATE = 115200  # Updated to match the high-speed ROS 2 / ESP32 rate

try:
    esp_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
    esp_serial.flush()
    print(f"Successfully connected to ESP32 on {PORT} at {BAUD_RATE} baud.")
except Exception as e:
    print(f"Error opening serial port: {e}")
    print("If you are using pins, remember to enable Serial hardware in raspi-config.")
    exit()

print("\n--- Calibration Testing Controller ---")
print("This checks the Proportional PWM firmware.")
print("Use WASD keys to control motion:")
print("  W = Forward, S = Backward, A = Left spin, D = Right spin")
print("  X = Stop")
print("Use Q/E to change speed:")
print("  Q = Faster, E = Slower")
print("You can still enter raw values like '150 150' if needed.")
print("Press Ctrl+C to quit.\n")

MAX_PWM = 255
MIN_PWM = 0
SPEED_STEP = 25
current_speed = 120


def clamp(value, low, high):
    return max(low, min(high, value))


def movement_to_pwm(key, speed):
    if key == 'W':
        return speed, speed
    if key == 'S':
        return -speed, -speed
    if key == 'A':
        return -speed, speed
    if key == 'D':
        return speed, -speed
    if key == 'X':
        return 0, 0
    return None

try:
    while True:
        user_input = input(f"Command [W/A/S/D/X, Q/E, or 'L R'] (speed={current_speed}): ").strip()
        if not user_input:
            continue

        key = user_input.upper()

        if key == 'Q':
            old_speed = current_speed
            current_speed = clamp(current_speed + SPEED_STEP, MIN_PWM, MAX_PWM)
            print(f"--> Speed increased: {old_speed} -> {current_speed}")
            continue

        if key == 'E':
            old_speed = current_speed
            current_speed = clamp(current_speed - SPEED_STEP, MIN_PWM, MAX_PWM)
            print(f"--> Speed decreased: {old_speed} -> {current_speed}")
            continue

        pwm_values = movement_to_pwm(key, current_speed)
        if pwm_values is not None:
            left_val, right_val = pwm_values
        else:
            parts = user_input.split()
        
        try:
            if pwm_values is None:
                left_val = int(parts[0])
                right_val = int(parts[1])
                left_val = clamp(left_val, -MAX_PWM, MAX_PWM)
                right_val = clamp(right_val, -MAX_PWM, MAX_PWM)
            
            # Format the continuous string exactly how the ESP32 expects it now!
            command_string = f"L{left_val}R{right_val}\n"
            
            # Send the encoded bytes
            esp_serial.write(command_string.encode('utf-8'))
            print(f"--> Sent raw bytes: {command_string.strip()}")
            
        except ValueError:
            print("Invalid input! Use W/A/S/D/X, Q/E, or two numbers like '100 100'.")
        except IndexError:
            print("You must provide exactly two numbers for raw PWM input!")

except KeyboardInterrupt:
    print("\nStopping robot and exiting...")
    # Send absolute stop
    esp_serial.write(b'L0R0\n') 
    esp_serial.close()
