# ChronoEngine Analytics (AetherEdge)

An end-to-end, fault-tolerant telemetry processing system. It reads continuous hardware signals, detects dangerous voltage anomalies in real time, logs performance metrics, and automatically sends instant alert payloads to automated workflows.

---

## System Architecture Overview

~~~text
[ Arduino / Mock Hardware ] 
            │ (Serial / Mock Stream)
            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Gateway                      │
│   • Resilient Ingestion Stream (COM Failover)          │
│   • Real-Time Anomaly Engine                           │
│   • Prometheus Metrics Endpoint (/metrics)             │
└───────┬────────────────────────┬───────────────────────┘
        │                        │
        │ (Incident Webhook)     │ (Metrics Scrape)
        ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  n8n Engine  │         │  Prometheus  │
│  (Alerting)  │         │  (Dashboard) │
└──────────────┘         └──────────────┘
~~~

---

## Level Breakdown

### Level 1: Data Parsing & Core Signal Validation

**Problem Statement**
Raw sensor signals coming from hardware can be messy, unformatted, or corrupted. If downstream analytics try to read broken data directly, the entire system crashes or generates incorrect calculations.

**Our Solution & Justification**
We built a structured parsing pipeline that validates every incoming frame into a clear data model (containing sequence ID, raw signal value, and variance). Validating data at the entry point ensures broken frames are filtered before reaching any business logic.

**Alternative Solutions Considered**
* **Processing raw text strings directly everywhere:**
  * *Why it won't work:* Extremely fragile. A single missing comma, unexpected space, or serial drop will cause crashes throughout the application.
* **Saving raw text to log files first and reading them later in batches:**
  * *Why it won't work:* Batching adds significant delay. Critical voltage spikes require instant action, which offline log parsing cannot deliver.

---

### Level 2: Real-Time Stream Ingestion & Resilient Failover

**Problem Statement**
Physical USB cables get unplugged, ports change, and hardware fails. If a telemetry system relies 100% on a physical connection, a loose cable will crash the entire backend service and stop all monitoring.

**Our Solution & Justification**
We engineered an asynchronous worker with an automated **Mock Hardware Driver**. If the system fails to open or loses connection to the assigned port (e.g., `COM4`), the gateway catches the error and instantly switches to simulated data. The stream never dies, and system uptime stays at 100%.

**Alternative Solutions Considered**
* **Stopping the app immediately when the COM port disappears:**
  * *Why it won't work:* Taking down the entire API gateway during brief hardware reconnects destroys backend availability and breaks live client dashboards.
* **Using basic static checks (e.g., `if voltage > 100`):**
  * *Why it won't work:* Static checks miss rapid variance shifts and standard deviation anomalies that occur within acceptable boundaries.

---

### Level 3: Microservice Containerization, Observability & Webhook Alerts

**Problem Statement**
Running multiple individual Python scripts, database servers, and monitoring tools across separate terminal windows on a local computer leads to configuration errors, dependency clashes, and high operational friction.

**Our Solution & Justification**
We packaged the entire ecosystem into a single configuration file orchestrating four containerized services on an isolated bridge network:

1. **FastAPI Gateway:** Ingests signals and triggers events.
2. **PostgreSQL:** Maintains persistent data storage with health checks.
3. **Prometheus:** Automatically scrapes system metrics every 5 seconds.
4. **n8n Engine:** Receives instant HTTP POST webhooks whenever an anomaly occurs.

Using Docker Compose ensures the entire stack runs identically on any system with a single command.

**Alternative Solutions Considered**
* **Running everything directly on the host operating system:**
  * *Why it won't work:* System-level dependency conflicts (such as Python version differences, path issues, or missing libraries) cause startup failures across different environments.
* **Polling the database from n8n every few seconds to look for errors:**
  * *Why it won't work:* Polling wastes server resources with constant empty queries and adds delay. Direct HTTP POST webhooks push data the exact millisecond an anomaly is flagged.

---

## How to Run the Stack

### Prerequisites
* Docker Desktop installed and running.

### Launching the Stack
Open PowerShell in the `level-3` directory and run:

~~~powershell
docker compose up --build -d
~~~

### Checking Status
Verify all services are up and healthy:

~~~powershell
docker compose ps
~~~

### Accessing Dashboards
* **FastAPI Health Check:** `http://localhost:8000/healthz`
* **Prometheus Metrics UI:** `http://localhost:9090`
* **n8n Automation Platform:** `http://localhost:5678`

### Viewing Live Logs
Stream live gateway processing and webhook dispatches:

~~~powershell
docker compose logs -f gateway
~~~