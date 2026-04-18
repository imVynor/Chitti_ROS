import serial
import time

# Set up the serial connection
# Remember to match this with how your ESP32 is plugged in!
PORT = '/dev/serial0' 
BAUD_RATE = 9600 

try:
    esp_serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
    esp_serial.flush()
    print(f"Successfully connected to ESP32 on {PORT} at {BAUD_RATE} baud.")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

print("\n--- Binary Logic Controller ---")
print("Valid Commands: F (Forward), B (Backward), L (Left), R (Right), S (Stop)")
print("Press Ctrl+C to quit.\n")

try:
    while True:
        # Get keyboard input from the user
        user_input = input("Enter command: ").strip().upper()
        
        if user_input in ['F', 'B', 'L', 'R', 'S']:
            esp_serial.write(user_input.encode('utf-8'))
            print(f"--> Sent command: {user_input}")
            time.sleep(0.1) 
        else:
            print("Invalid command! Please use F, B, L, R, or S.")

except KeyboardInterrupt:
    print("\nStopping robot and exiting...")
    esp_serial.write(b'S') 
    esp_serial.close()
