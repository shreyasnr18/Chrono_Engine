import asyncio
import json
import logging
import random
import time
from gateway.config import settings

logger = logging.getLogger("AetherEdge.Ingestion")

class ResilientTelemetryStream:
    """Production stream reader with auto-reconnect backoff and hardware fallback."""
    
    def __init__(self, data_queue: asyncio.Queue):
        self.data_queue = data_queue
        self.is_running = False
        self.connection_active = False

    async def start(self):
        self.is_running = True
        logger.info(f"Starting Ingestion Worker on port {settings.SERIAL_PORT}...")
        
        retry_delay = 1.0
        while self.is_running:
            try:
                # Attempt physical serial connection
                import serial
                with serial.Serial(settings.SERIAL_PORT, settings.BAUD_RATE, timeout=1) as ser:
                    self.connection_active = True
                    retry_delay = 1.0  # Reset backoff on success
                    logger.info(f"Successfully linked hardware stream on {settings.SERIAL_PORT}")
                    
                    while self.is_running:
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line.startswith("{"):
                                packet = json.loads(line)
                                await self.data_queue.put(packet)
                        await asyncio.sleep(0.01)

            except Exception as err:
                self.connection_active = False
                logger.warning(f"Hardware connection lost on {settings.SERIAL_PORT}: {err}")
                
                if settings.MOCK_HARDWARE_FALLBACK:
                    logger.info("Engaging Mock Hardware Driver to maintain stream continuity...")
                    await self._run_mock_driver()
                else:
                    logger.info(f"Retrying connection in {retry_delay:.1f} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30.0)  # Exponential backoff max 30s

    async def _run_mock_driver(self):
        """Fallback simulation mode to prevent total service failure during hardware disconnects."""
        sample_id = 0
        while self.is_running and not self.connection_active:
            sample_id += 1
            raw = 512.0 + random.uniform(-50, 50)
            
            # Inject occasional artificial anomaly for diagnostic testing
            if random.random() < 0.05:
                raw += random.choice([-200.0, 200.0])
                
            mock_packet = {
                "ts": int(time.time() * 1000),
                "id": sample_id,
                "raw": round(raw, 2),
                "filt": 512.0,
                "var": round(raw - 512.0, 2)
            }
            await self.data_queue.put(mock_packet)
            await asyncio.sleep(0.2)

    def stop(self):
        self.is_running = False
        logger.info("Ingestion Worker gracefully stopped.")