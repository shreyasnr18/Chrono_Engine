import serial
import json
import time

# 1. Configure the connection to match the C++ engine
COM_PORT = 'COM4' # Change this if your Arduino is on a different port
BAUD_RATE = 115200

print(f"Connecting to ChronoEngine on {COM_PORT}...")

try:
    # 2. Open the serial pipeline
    engine_stream = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Give the Arduino 2 seconds to reset upon connection
    print("Connection established. Ingesting telemetry...\n")
    print(f"{'TASK ID':<10} | {'EXPECTED (us)':<15} | {'ACTUAL (us)':<15} | {'JITTER (us)':<15}")
    print("-" * 60)

    # 3. The continuous ingestion loop
    while True:
        if engine_stream.in_waiting > 0:
            # Read the raw byte data and decode it into a string
            raw_data = engine_stream.readline().decode('utf-8').strip()
            
            # Skip the initial "Booting..." message or empty lines
            if not raw_data.startswith("{"):
                continue

            try:
                # 4. Parse the JSON packet
                telemetry = json.loads(raw_data)
                
                task_id = telemetry["id"]
                expected = telemetry["expected"]
                actual = telemetry["actual"]
                
                # 5. Calculate the temporal jitter
                jitter = actual - expected
                
                # Format and print the row
                print(f"Task [{task_id:<2}]  | {expected:<15} | {actual:<15} | +{jitter:<14}")
                
            except json.JSONDecodeError:
                # Sometimes a packet gets corrupted over the wire, just skip it
                pass

except serial.SerialException as e:
    print(f"\n[ERROR] Could not connect to {COM_PORT}.")
    print("Did you forget to close the Serial Monitor in the Arduino IDE?")
except KeyboardInterrupt:
    print("\nAnalytics stream stopped by user.")
finally:
    if 'engine_stream' in locals() and engine_stream.is_open:
        engine_stream.close()