import serial
import time
import threading

# Set up the serial connection
# Remember to match this with how your ESP32 is plugged in!
PORT = '/dev/ttyUSB1' 
BAUD_RATE = 115200 

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

current_command = 'S'
command_lock = threading.Lock()
stop_event = threading.Event()


def sender_loop():
    while not stop_event.is_set():
        with command_lock:
            cmd = current_command
        esp_serial.write(cmd.encode('utf-8'))
        time.sleep(0.1)


sender_thread = threading.Thread(target=sender_loop, daemon=True)
sender_thread.start()

try:
    while True:
        # Get keyboard input from the user
        user_input = input("Enter command: ").strip().upper()
        
        if user_input in ['F', 'B', 'L', 'R', 'S']:
            with command_lock:
                current_command = user_input
            print(f"--> Active command set to: {user_input} (sending continuously)")
        else:
            print("Invalid command! Please use F, B, L, R, or S.")

except KeyboardInterrupt:
    print("\nStopping robot and exiting...")
    stop_event.set()
    sender_thread.join(timeout=1)
    esp_serial.write(b'S') 
    esp_serial.close()
