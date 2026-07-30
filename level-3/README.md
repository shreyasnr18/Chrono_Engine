# Level 3: FastAPI Gateway, Persistence & Observability - ChronoEngine Analytics (AetherEdge)

An end-to-end, fault-tolerant telemetry processing system. It ingests
continuous hardware signals, detects dangerous voltage anomalies in real
time, logs metrics to PostgreSQL, exposes Prometheus scraping targets,
and dispatches instant webhook alerts to automated workflows.

------------------------------------------------------------------------

## System Architecture Overview

``` text
[ Arduino / Mock Hardware ] 
            │ (Serial / Mock Stream)
            ▼
┌────────────────────────────────────────────────────────┐
│                 FastAPI Gateway                        │
│   • Resilient Ingestion Stream (COM Failover)          │
│   • Real-Time Anomaly Engine (Pydantic Validation)     │
│   • Prometheus Metrics Endpoint (/metrics)             │
└───────┬────────────────────────┬───────────────────────┘
        │                        │
        │ (Incident Webhook)     │ (Metrics Scrape)
        ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  n8n Engine  │         │  Prometheus  │
│  (Alerting)  │         │  (Dashboard) │
└──────────────┘         └──────────────┘
        │
        ▼
┌──────────────┐
│ PostgreSQL   │
│ (aether_db)  │
└──────────────┘
```

------------------------------------------------------------------------

## Purpose & Problem Solved

Raw telemetry streams flowing through hardware serial connections or
message brokers are ephemeral, unvalidated, and difficult to monitor.
Running isolated scripts across separate terminal windows introduces
configuration errors, dependency clashes, and high operational friction.

Level 3 solves this by packaging the entire ecosystem into an
orchestrated microservice architecture. It introduces a centralized
FastAPI backend for real-time validation, automatic COM port failover,
structured PostgreSQL database persistence, Prometheus metrics scraping,
and automated n8n incident alerting.

------------------------------------------------------------------------

## Algorithm: Asynchronous Ingestion & Persistence Algorithm (AIPA)

### Endpoint Routing & Ingestion

Intercept serial feeds or REST HTTP requests through non-blocking
FastAPI asynchronous route handlers.

### Schema & Anomaly Validation

Pass incoming frames through Pydantic data models to validate sequence
IDs, signal variance, and detect threshold breaches (e.g., voltage
spikes).

### Relational Persistence & Webhook Dispatch

Persist validated telemetry into PostgreSQL (aether_db). If an anomaly
is flagged, immediately dispatch an HTTP POST webhook payload to the n8n
alerting engine.

### Health Check & Metrics Scraping

Expose service health (`/healthz`) and runtime telemetry metrics
(`/metrics`) for continuous scraping by Prometheus every 5 seconds.

------------------------------------------------------------------------

## Core Concepts Used

1.  Asynchronous Web Services: Utilizing FastAPI and Uvicorn for
    non-blocking, high-concurrency request handling.
2.  Microservice Containerization: Isolating services (API, DB,
    Prometheus, n8n) on a dedicated Docker bridge network.
3.  Event-Driven Webhook Dispatch: Replacing slow database polling with
    millisecond-level HTTP POST anomaly alerts.
4.  Full-Stack Observability: Instrumenting custom application metrics
    to track gateway uptime, request duration, and hardware failover
    states.

------------------------------------------------------------------------

## Pipeline Breakdown & Architectural Trade-offs

### 1. Data Parsing & Core Signal Validation

**Problem:** Raw sensor signals can be corrupted or unformatted. If
downstream analytics read broken data directly, the system crashes.

**Our Solution:** A structured Pydantic parsing pipeline validates every
incoming frame before reaching any business logic.

**Alternatives Rejected:** - Processing raw text strings everywhere:
Extremely fragile. A single dropped comma or missing byte crashes the
application. - Batching raw text to log files: Adds significant delay.
Critical voltage spikes require instant action that batch log processing
cannot deliver.

### 2. Stream Ingestion & Resilient Failover

**Problem:** USB cables get unplugged and serial ports change. Relying
100% on a physical connection means a loose cable crashes the backend.

**Our Solution:** An asynchronous worker with an automated Mock Hardware
Driver. If connection to the physical port (e.g., COM4) drops, the
gateway catches the error and instantly switches to simulated data
seamlessly.

**Alternatives Rejected:** - Halting the application on COM
disconnection: Destroying API gateway availability during brief
reconnects breaks live client dashboards. - Basic static checks (if
voltage \> 100): Misses rapid variance shifts and standard deviation
anomalies that occur within standard bounds.

### 3. Containerized Orchestration & Observability

**Problem:** Managing multiple local services manually leads to host
library conflicts and environment drift.

**Our Solution:** Containerizing four core services in Docker Compose: -
FastAPI Gateway: Signal ingestion, validation, and event routing. -
PostgreSQL: Persistent data storage with automated health checks. -
Prometheus: Real-time metrics collection and scraping. - n8n Engine:
Automated workflow engine for incident alerting.

**Alternatives Rejected:** 1. Host-level manual execution: Dependency
mismatches (Python versions, missing libs) break multi-platform
deployments. 2. Polling the database for alerts: Wastes database IOPS
and adds latency compared to direct event webhooks.

------------------------------------------------------------------------

## Architecture Justification

Combining FastAPI, PostgreSQL, Prometheus, and n8n inside Docker Compose
guarantees production-grade reliability. FastAPI provides native async
throughput and automatic OpenAPI docs (`http://localhost:8000/docs`).
Containerizing the stack ensures zero stream loss, fault tolerance
against hardware dropouts, and identical execution across any
environment with a single command.

------------------------------------------------------------------------

## How to Run the Stack?

### Prerequisites

-   Docker Desktop installed and running.

### Launching Services

Navigate to the `level-3` directory and start the stack in detached
mode:

``` bash
docker compose up --build -d
```

### Verifying Service Health

Check the container status and port mappings:

``` bash
docker compose ps
```

------------------------------------------------------------------------

## Service Endpoints

-   FastAPI Gateway Health Check: `http://localhost:8000/healthz`
-   FastAPI Swagger Docs: `http://localhost:8000/docs`
-   Prometheus Metrics UI: `http://localhost:9090`
-   n8n Automation Platform: `http://localhost:5678`

------------------------------------------------------------------------

## Live System Logs

Monitor real-time gateway processing, failover triggers, and webhook
dispatches:

``` bash
docker compose logs -f gateway
```
