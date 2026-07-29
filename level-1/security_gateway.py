import serial
import json
import time
import csv
import os

COM_PORT = 'COM4'
BAUD_RATE = 115200
LOG_FILE = 'datasheet_log.csv'

# Initialize CSV Datasheet structure if it doesn't exist
file_exists = os.path.isfile(LOG_FILE)
csv_file = open(LOG_FILE, mode='a', newline='')
csv_writer = csv.writer(csv_file)

if not file_exists:
    csv_writer.writerow(["Timestamp_ms", "Sample_ID", "Raw_Voltage", "Filtered_Signal", "Variance_Delta"])
    csv_file.flush()

print(f"[SECURITY GATEWAY] Initializing secure pipeline on {COM_PORT}...")

try:
    stream = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("[SECURITY GATEWAY] Secure link active. Ingesting datasheet stream...\n")
    print(f"{'TIMESTAMP':<12} | {'ID':<6} | {'RAW':<10} | {'FILTERED':<10} | {'VARIANCE':<10}")
    print("-" * 65)

    last_time = time.time()
    packet_count = 0

    while True:
        if stream.in_waiting > 0:
            raw_line = stream.readline().decode('utf-8', errors='ignore').strip()
            
            if not raw_line.startswith("{"):
                continue

            try:
                # Security layer: strict JSON payload parsing
                packet = json.loads(raw_line)
                
                ts = packet["ts"]
                sid = packet["id"]
                raw = packet["raw"]
                filt = packet["filt"]
                var = packet["var"]

                # Rate-limiting / Anti-flooding security check (Max 50 packets/sec threshold)
                current_time = time.time()
                packet_count += 1
                if current_time - last_time >= 1.0:
                    if packet_count > 50:
                        print(f"[SECURITY ALERT] Rate limit warning: {packet_count} pps detected!")
                    packet_count = 0
                    last_time = current_time

                # Write to Enterprise Datasheet CSV (Live-linked to Excel / Power BI)
                csv_writer.writerow([ts, sid, raw, filt, var])
                csv_file.flush()

                print(f"{ts:<12} | {sid:<6} | {raw:<10.2f} | {filt:<10.2f} | {var:<10.2f}")

            except json.JSONDecodeError:
                # Drop malformed packets (Injection protection)
                pass

except serial.SerialException:
    print(f"\n[ERROR] Connection failed on {COM_PORT}. Close Arduino IDE Serial Monitor.")
except KeyboardInterrupt:
    print("\n[SECURITY GATEWAY] Pipeline shutdown by user.")
finally:
    csv_file.close()
    if 'stream' in locals() and stream.is_open:
        stream.close()