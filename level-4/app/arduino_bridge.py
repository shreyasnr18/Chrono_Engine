import asyncio
import logging
import serial
import requests
from app.kafka_producer import TelemetryStreamProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arduino_bridge")

SERIAL_PORT = "COM4"
BAUD_RATE = 9600
FASTAPI_URL = "http://localhost:8000/telemetry"

async def main():
    producer = TelemetryStreamProducer()
    producer.broker = "localhost:19092"
    await producer.start()

    logger.info(f"Opening Serial connection to Arduino on {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        await asyncio.sleep(2)
        ser.reset_input_buffer()  # Flush startup noise bytes
    except Exception as e:
        logger.error(f"Could not open serial port {SERIAL_PORT}: {e}")
        return

    logger.info("📡 Streaming physical Uno data to FastAPI & Redpanda...")

    while True:
        if ser.in_waiting > 0:
            raw_line = ""
            try:
                raw_bytes = ser.readline()
                raw_line = raw_bytes.decode("utf-8", errors="ignore").strip()

                if raw_line:
                    logger.info(f"RAW SERIAL FROM COM4: {raw_line}")
                    parts = raw_line.split(",")
                    if len(parts) >= 2:
                        voltage_val = float(parts[0])
                        temp_val = float(parts[1])

                        payload = {
                            "device_id": "arduino_uno_01",
                            "voltage": voltage_val,
                            "temperature": temp_val
                        }

                        # 1. Post to FastAPI Gateway
                        try:
                            res = requests.post(FASTAPI_URL, json=payload, timeout=2)
                            logger.info(f"POST to Gateway -> Status {res.status_code}: {res.json()}")
                        except Exception as req_err:
                            logger.error(f"HTTP Post to FastAPI failed: {req_err}")

                        # 2. Publish to Redpanda
                        await producer.send_telemetry("telemetry.raw", payload)

            except ValueError as ve:
                logger.warning(f"Could not parse serial value '{raw_line}': {ve}")
            except Exception as e:
                logger.error(f"Error reading serial line: {e}")

        await asyncio.sleep(0.01)

if __name__ == "__main__":
    asyncio.run(main())