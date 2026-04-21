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
print("Type Left and Right PWM speeds (-255 to 255).")
print("Example: '150 150' goes Forward.")
print("Example: '-100 100' spins Left.")
print("Example: '0 0' Stops.")
print("Press Ctrl+C to quit.\n")

try:
    while True:
        # Get keyboard input from the user
        user_input = input("Enter Left and Right PWM (e.g. '150 150'): ").strip()
        
        try:
            parts = user_input.split()
            if len(parts) == 1 and parts[0].upper() == 'S':
                # Easy shortcut for STOP
                left_val, right_val = 0, 0
            else:
                left_val = int(parts[0])
                right_val = int(parts[1])
            
            # Format the continuous string exactly how the ESP32 expects it now!
            command_string = f"L{left_val}R{right_val}\n"
            
            # Send the encoded bytes
            esp_serial.write(command_string.encode('utf-8'))
            print(f"--> Sent raw bytes: {command_string.strip()}")
            
        except ValueError:
            print("Invalid format! Please type two numbers separated by a space (e.g. '100 100')")
        except IndexError:
            print("You must provide exactly two numbers!")

except KeyboardInterrupt:
    print("\nStopping robot and exiting...")
    # Send absolute stop
    esp_serial.write(b'L0R0\n') 
    esp_serial.close()
