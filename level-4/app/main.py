import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psycopg2
from psycopg2.extras import RealDictCursor

from app.kafka_producer import TelemetryStreamProducer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aether_gateway")

# Environment Configuration
DATA_SOURCE = os.getenv("DATA_SOURCE", "real_hardware")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "aether_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "aether")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aetherpass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "telemetry_db")

# Prometheus Telemetry Metrics
FRAMES_PROCESSED = Counter("telemetry_frames_processed_total", "Total telemetry frames processed")
CURRENT_VOLTAGE = Gauge("telemetry_voltage_volts", "Live line voltage reading")
CURRENT_TEMP = Gauge("telemetry_temperature_celsius", "Live temperature reading")

# Ingestion Components
kafka_producer = TelemetryStreamProducer()
sequence_counter = 0


def get_db_connection():
    """Returns a fresh PostgreSQL connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
        cursor_factory=RealDictCursor
    )


def init_db():
    """Ensures PostgreSQL schema exists on startup."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id SERIAL PRIMARY KEY,
                sequence_id INT,
                timestamp DOUBLE PRECISION,
                voltage REAL,
                temperature_c REAL,
                source VARCHAR(50),
                is_simulated_anomaly BOOLEAN
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("PostgreSQL database schema initialized successfully.")
    except Exception as e:
        logger.error(f"PostgreSQL init failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup and shutdown lifecycle management."""
    init_db()
    await kafka_producer.start()
    # Synthetic background loop disabled so only physical hardware telemetry controls the pipeline
    yield
    await kafka_producer.stop()


app = FastAPI(title="ChronoEngine Telemetry Gateway", version="4.0.0", lifespan=lifespan)


@app.get("/healthz")
def health_check():
    return {"status": "healthy", "level": 4, "data_source": DATA_SOURCE}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/telemetry")
async def receive_telemetry(payload: dict):
    """Processes live physical telemetry streaming from the Arduino Uno bridge."""
    global sequence_counter
    sequence_counter += 1

    voltage = float(payload.get("voltage", 0.0))
    temperature_c = float(payload.get("temperature_c", payload.get("temperature", 0.0)))
    device_id = payload.get("device_id", "arduino_uno_01")
    timestamp = time.time()

    # 1. Update Prometheus metrics with real hardware readings
    FRAMES_PROCESSED.inc()
    CURRENT_VOLTAGE.set(voltage)
    CURRENT_TEMP.set(temperature_c)

    frame = {
        "sequence_id": sequence_counter,
        "timestamp": timestamp,
        "voltage": voltage,
        "temperature_c": temperature_c,
        "source": device_id,
        "is_simulated_anomaly": False
    }

    # 2. Publish live frame to Redpanda Kafka Topic 'telemetry.raw'
    try:
        await kafka_producer.send_telemetry(topic="telemetry.raw", data=frame)
    except Exception as k_err:
        logger.error(f"Failed to publish live frame to Redpanda: {k_err}")

    # 3. Save frame into PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO telemetry_logs (sequence_id, timestamp, voltage, temperature_c, source, is_simulated_anomaly)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            frame["sequence_id"],
            frame["timestamp"],
            frame["voltage"],
            frame["temperature_c"],
            frame["source"],
            frame["is_simulated_anomaly"]
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as db_err:
        logger.error(f"Failed to persist live frame to Postgres: {db_err}")

    logger.info(f"[REAL HW: {device_id.upper()}] Frame #{sequence_counter}: Voltage={voltage}V | Temp={temperature_c}°C")

    return {"status": "success", "sequence_id": sequence_counter, "voltage": voltage, "temperature_c": temperature_c}