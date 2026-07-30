import json
import logging
import os
import time
import serial

from app.ingestion.digital_twin import DigitalTwinSimulator

logger = logging.getLogger("aether_stream_driver")


class SmartStreamDriver:

    def __init__(self):
        self.digital_twin = DigitalTwinSimulator()
        self.mode = os.getenv("DATA_SOURCE", "auto").lower()
        self.serial_port = os.getenv("SERIAL_PORT", "COM4")
        self.baud_rate = int(os.getenv("BAUD_RATE", "115200"))
        self.serial_conn = None
        self.last_retry = 0

    def _try_connect_serial(self):
        """Attempts to open the serial hardware connection."""
        if time.time() - self.last_retry < 5.0:
            return False

        self.last_retry = time.time()
        try:
            self.serial_conn = serial.Serial(
                port=self.serial_port, baudrate=self.baud_rate, timeout=0.5
            )
            logger.info(
                f"🟢 HARDWARE CONNECTED: Reading live sensors from {self.serial_port}"
            )
            return True
        except Exception as e:
            logger.warning(
                f"🟡 NO HARDWARE DETECTED on {self.serial_port} ({e}). Using Digital Twin simulator."
            )
            self.serial_conn = None
            return False

    def read_frame(self) -> dict:
        """Reads a telemetry frame from physical hardware if available, otherwise uses Digital Twin."""
        # 1. Explicit Digital Twin override
        if self.mode == "digital_twin":
            return self.digital_twin.generate_frame()

        # 2. Attempt Hardware Serial connection if missing
        if self.serial_conn is None or not self.serial_conn.is_open:
            self._try_connect_serial()

        # 3. Read live hardware frame if connected
        if self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline().decode("utf-8").strip()
                if line:
                    data = json.loads(line)
                    data["source"] = "hardware_serial"
                    return data
            except Exception as e:
                logger.error(
                    f"🔴 Hardware communication error: {e}. Falling back to Digital Twin."
                )
                if self.serial_conn:
                    self.serial_conn.close()
                self.serial_conn = None

        # 4. Seamless Fallback to Digital Twin
        frame = self.digital_twin.generate_frame()
        frame["source"] = "digital_twin_fallback"
        return frame