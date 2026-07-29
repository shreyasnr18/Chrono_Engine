import asyncio
import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, status
from gateway.config import settings
from gateway.ingestion import ResilientTelemetryStream

# 1. Production Structured JSON Logger Setup
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "environment": settings.ENVIRONMENT
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("AetherEdge")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Runtime metrics counters
METRICS = {
    "total_packets_processed": 0,
    "anomalies_detected": 0,
    "start_time": time.time()
}

telemetry_queue = asyncio.Queue(maxsize=1000)
stream_worker = ResilientTelemetryStream(telemetry_queue)

# 2. Lifecycle Context Manager for Graceful Shutdowns
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initiating Production Gateway Service...")
    ingestion_task = asyncio.create_task(stream_worker.start())
    processing_task = asyncio.create_task(process_telemetry_queue())
    yield
    logger.info("Graceful Shutdown Signal Received. Cleaning up resources...")
    stream_worker.stop()
    ingestion_task.cancel()
    processing_task.cancel()
    logger.info("Service successfully terminated.")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

async def process_telemetry_queue():
    last_alert_time = 0
    while True:
        packet = await telemetry_queue.get()
        METRICS["total_packets_processed"] += 1
        
        # Anomaly check logic
        if abs(packet.get("var", 0)) > 150.0:
            METRICS["anomalies_detected"] += 1
            current_time = time.time()
            
            # Rate limiting / Cooldown logic
            if current_time - last_alert_time > settings.AI_ALERT_COOLDOWN_SEC:
                last_alert_time = current_time
                logger.error(f"CRITICAL ANOMALY DETECTED: Sample ID #{packet['id']} | Var: {packet['var']}V")
                # Trigger n8n async webhook (non-blocking)
                asyncio.create_task(dispatch_n8n_alert(packet))
                
        telemetry_queue.task_done()

async def dispatch_n8n_alert(packet: dict):
    import requests
    try:
        payload = {
            "event": "ANOMALY_ALERT",
            "data": packet,
            "agent_diagnostic": f"Variance spike of {packet['var']}V recorded. Grounding check recommended."
        }
        requests.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=2.0)
        logger.info("Successfully dispatched incident event to n8n Docker container.")
    except Exception as e:
        logger.warning(f"Failed to reach n8n workflow engine: {e}")

# 3. Production Health Probes (Liveness & Readiness)
@app.get("/health/liveness", status_code=status.HTTP_200_OK)
def liveness_probe():
    """Confirms the process is running."""
    return {"status": "alive", "timestamp": time.time()}

@app.get("/health/readiness", status_code=status.HTTP_200_OK)
def readiness_probe(response: Response):
    """Confirms the service is healthy enough to handle traffic."""
    is_ready = stream_worker.is_running
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "reason": "Ingestion engine offline"}
    return {"status": "ready", "queue_depth": telemetry_queue.qsize()}

# 4. Prometheus Metrics Endpoint
@app.get("/metrics")
def metrics_endpoint():
    """Exposes telemetry processing metrics for monitoring tools."""
    uptime = time.time() - METRICS["start_time"]
    output = [
        f"# HELP aether_packets_total Total processed packets",
        f"# TYPE aether_packets_total counter",
        f"aether_packets_total {METRICS['total_packets_processed']}",
        f"# HELP aether_anomalies_total Total detected anomalies",
        f"# TYPE aether_anomalies_total counter",
        f"aether_anomalies_total {METRICS['anomalies_detected']}",
        f"# HELP aether_uptime_seconds Total runtime in seconds",
        f"# TYPE aether_uptime_seconds gauge",
        f"aether_uptime_seconds {uptime:.2f}"
    ]
    return Response(content="\n".join(output), media_type="text/plain")