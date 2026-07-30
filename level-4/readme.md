# Level 4: Full-Stack Observability, Real-Time Dashboards & Automated Incident Response - ChronoEngine Analytics (AetherEdge)

An enterprise-grade, fault-tolerant telemetry, streaming, and observability stack. Level 4 represents the pinnacle of the ChronoEngine ecosystem—combining high-frequency hardware signal parsing, asynchronous event streaming, relational persistence, real-time metrics scraping, visual dashboarding, and automated webhook alerting into a single unified containerized infrastructure.

---

## System Architecture Overview

```text
               ┌──────────────────────┐
               │ Hardware / Simulator │
               └──────────┬───────────┘
                          │ (Serial Stream)
                          ▼
┌──────────────────────────────────────────────────┐
│             aether_gateway (FastAPI)             │
│   • COM Failover       • Anomaly Engine          │
│   • /metrics           • Producer Interface      │
└────┬──────────────┬─────────────┬───────────┬────┘
     │ (Publish)    │ (Webhook)   │ (SQL)     │ (Scrape)
     ▼              ▼             ▼           ▼
┌─────────┐    ┌─────────┐   ┌─────────┐ ┌─────────┐
│Redpanda │    │   n8n   │   │Postgres │ │Prometheus│
│(:19092) │    │ (:5678) │   │ (:5432) │ │ (:9090) │
└────┬────┘    └─────────┘   └─────────┘ └────┬────┘
     │ (Kafka)                                │ (PromQL)
     ▼                                        ▼
┌─────────┐                              ┌─────────┐
│Console  │                              │ Grafana │
│(:8080)  │                              │ (:3000) │
└─────────┘                              └─────────┘
---
```text



## Ideation & Purpose
In mission-critical engineering, robotics, and high-performance mechanical applications, handling raw sensor data is only the first step. Knowing that data is flowing is insufficient; engineers need real-time insight into system health, processing latency, variance anomalies, and failure states.

Level 4 was conceived to bridge the gap between simple data logging and operational intelligence. It transitions the platform from a reactive pipeline (where errors are discovered after reviewing logs) into a proactive observability engine that monitors performance metrics live and dispatches automated alerts before catastrophic hardware failure occurs.


## Why Upscale to Level 4? (The Problem Statement)
The Limitations of Level 3
While Level 3 successfully containerized the API gateway and database, it introduced critical operational blind spots:

Relational Database Strain: Executing high-frequency analytical queries (e.g., calculating 5-minute rolling averages or standard deviation spikes over millions of rows) directly on PostgreSQL degrades database write performance.

Lack of Operational Visibility: Without dedicated time-series monitoring, detecting memory leaks, CPU spikes, or dropped HTTP connections in the gateway required manual SSH log analysis.

Manual Anomaly Inspection: Outages or signal dropouts required active user monitoring rather than automated, multi-channel alerting workflows.

What Level 4 Solves
Level 4 decoupled operational analytics from transactional storage by integrating Prometheus for time-series metric collection and Grafana for rich visual telemetry dashboards. Additionally, it incorporates Redpanda as a distributed message bus to decouple stream production from ingestion, while n8n handles automated incident dispatch.


## Justified Solution & Architecture Trade-offs
Pull-Based Metrics (Prometheus) vs. Push-Based Metrics (StatsD / Graphite)
Chosen Solution: Pull-Based Metrics via Prometheus scraping the /metrics endpoint every 5 seconds.

Justification: Push-based systems can easily overwhelm logging servers if a sensor array experiences a sudden throughput burst. Prometheus's pull model puts the monitoring infrastructure in control of ingestion rates, preventing telemetry overload while maintaining system isolation.

Distributed Streaming (Redpanda) vs. Direct Database Writes
Chosen Solution: Asynchronous event publishing to Redpanda before database insertion.

Justification: Direct database writes create tight coupling and synchronous blocking during network latency. Redpanda buffers incoming telemetry in append-only logs, guaranteeing zero data loss even if the database undergoes temporary maintenance.

Grafana Visualization vs. Custom Frontend Dashboards
Chosen Solution: Grafana connected directly to Prometheus TSDB datasources.

Justification: Building custom web charts requires significant maintenance and lacks dynamic threshold alerting, variable query parameters, and panel customization. Grafana provides enterprise-grade PromQL visualization natively out-of-the-box.


## Key Algorithms Used
Algorithm A: Time-Series Metric Aggregation Algorithm (TSMAA)
Used by the FastAPI gateway to instrument application health without impacting request handling latency.

1. Initialize Prometheus Gauge/Counter metrics in global memory.
2. Intercept incoming telemetry frame via ASGI middleware.
3. Update counter: `http_requests_total{method="POST", status="200"}` increment by 1.
4. Record execution duration: `request_processing_seconds` histogram update.
5. If voltage anomaly > threshold:
     Increment `telemetry_anomalies_total{sensor_type="voltage"}` counter.
6. Expose internal atomic metrics state asynchronously at `/metrics`.
7. Prometheus scrapes `/metrics` at set interval T, computing rate over time:
     rate(http_requests_total[1m])


Algorithm B: Resilient Hardware Failover Algorithm (RHFA)
Guarantees 100% gateway uptime even when physical connections drop.

1. Attempt serial connection to physical interface (e.g., `COM4`).
2. IF connection succeeds:
     Read hardware stream frame -> Parse JSON -> Process.
3. ELSE CATCH (SerialException / FileNotFoundError):
     Log warning: "Hardware unavailable. Triggering Mock Driver."
     Initialize Synthetic Metric Generator (Inject thermal noise & electrical variance).
4. Stream synthetic data frames seamlessly to pipeline.
5. Periodically attempt background probe on `COM4` to re-establish physical link.


## Core Concepts Demonstrated
Dimensional Metrics & PromQL: Utilizing labels (job, instance, status) to filter time-series queries dynamically.

Time-Series Databases (TSDB): Storing data structured by time offsets rather than relational primary keys for ultra-fast range queries.

Event-Driven Architecture (EDA): Asynchronous event streams decoupling data producers, message brokers, persistent storage, and alerting services.

Docker Container Inter-Networking: Managing DNS service discovery (host.docker.internal vs bridge network service names like aether_gateway:8000).

SLA/SLO Operational Monitoring: Tracking error budgets, request latency percentiles (p95, p99), and gateway up states.


## Detailed Technology Stack Breakdown
1. FastAPI Gateway (aether_gateway): Port 8000:8000 — Ingests sensor streams, handles COM failover, exposes /metrics, and dispatches webhooks.

2. Redpanda Broker (aether_redpanda): Port 19092:19092 — C++ based, high-performance, Kafka-compatible distributed event stream buffer.

3. Redpanda Console (aether_console): Port 8080:8080 — Web UI for inspecting topics (telemetry.raw), partition offsets, and message payloads.

4. PostgreSQL Database (aether_db): Port 5432:5432 — Relational store for historical telemetry records, system logs, and persistent configuration.

5. Prometheus (aether_prometheus): Port 9090:9090 — Scrapes /metrics from target services, stores time-series metrics, and evaluates PromQL.

6. Grafana (aether_grafana): Port 3000:3000 — Visual dashboarding engine querying Prometheus to display real-time graphs and alerts.

7. n8n Engine (n8n): Port 5678:5678 — Workflow engine that receives HTTP POST webhooks on anomalies and dispatches external alerts.


## Setup & Operations Guide
Prerequisites
Docker Desktop installed and running.

PowerShell / Terminal with Git access.

Launching the Full Stack
Navigate to the level-4 project root and start all services:
docker compose up --build -d

Verifying Service Deployment
Check that all containerized services are running and healthy:
docker compose ps

Troubleshooting & Restarting Specific Services
If you modify your prometheus.yml scrape configuration, restart the Prometheus container to load changes:
docker compose restart aether_prometheus

Accessing Project Interfaces
Grafana Dashboards: http://localhost:3000 (Default credentials: admin / admin)

Prometheus Metrics Target Page: http://localhost:9090/targets

Redpanda Console: http://localhost:8080

FastAPI Interactive Docs: http://localhost:8000/docs

n8n Automation Console: http://localhost:5678


## Verification & Operational Testing
Open http://localhost:9090/targets in your browser.

Confirm that the aether_gateway scrape job displays a state of UP with a green badge.

Navigate to the Graph tab on Prometheus and execute the following PromQL query to verify metric scraping:
up{job="aether_gateway"}
A returned scalar value of 1 confirms that end-to-end metrics scraping, container networking, and telemetry processing are fully operational.