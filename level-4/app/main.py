import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psycopg2
from psycopg2.extras import RealDictCursor

from app.ingestion.stream_driver import SmartStreamDriver
from app.kafka_producer import TelemetryStreamProducer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aether_gateway")

# Environment Configuration
DATA_SOURCE = os.getenv("DATA_SOURCE", "auto")
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
stream_driver = SmartStreamDriver()


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


async def ingestion_loop():
    logger.info(f"Starting ingestion pipeline in mode: {DATA_SOURCE}")

    while True:
        try:
            # 1. Reads real hardware or auto-falls back to Digital Twin physics
            frame = stream_driver.read_frame()

            # 2. Update Prometheus metrics
            FRAMES_PROCESSED.inc()
            CURRENT_VOLTAGE.set(frame["voltage"])
            CURRENT_TEMP.set(frame["temperature_c"])

            # 3. Publish frame to Redpanda Kafka Topic 'telemetry.raw'
            await kafka_producer.send_telemetry(topic="telemetry.raw", data=frame)

            # 4. Save frame into PostgreSQL
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
                    frame.get("is_simulated_anomaly", False)
                ))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as db_err:
                logger.error(f"Failed to persist frame to Postgres: {db_err}")

            logger.info(f"[{frame['source'].upper()}] Frame #{frame['sequence_id']}: Voltage={frame['voltage']}V | Temp={frame['temperature_c']}°C")

        except Exception as e:
            logger.error(f"Error in ingestion worker loop: {e}")

        # Stream cadence: 1 event every 1 second
        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup and shutdown lifecycle management."""
    init_db()
    await kafka_producer.start()
    ingestion_task = asyncio.create_task(ingestion_loop())
    yield
    ingestion_task.cancel()
    await kafka_producer.stop()


app = FastAPI(title="ChronoEngine Telemetry Gateway", version="4.0.0", lifespan=lifespan)


@app.get("/healthz")
def health_check():
    return {"status": "healthy", "level": 4, "data_source": DATA_SOURCE}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)