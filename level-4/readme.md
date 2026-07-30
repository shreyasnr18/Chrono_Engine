#  ChronoEngine Analytics — Level 4
### Full-Stack Observability, Real-Time Dashboards & Automated Incident Response
### *AetherEdge Engineering Stack*

> **Enterprise-grade telemetry, streaming, and observability platform built using FastAPI, Docker, Prometheus, Grafana, Redpanda, PostgreSQL, and n8n.**

---

##  Overview

Level 4 represents the pinnacle of the **ChronoEngine** ecosystem.

It combines:

- High-frequency hardware telemetry
- Asynchronous event streaming
- Relational persistence
- Time-series monitoring
- Real-time visualization
- Automated incident response

into a single fault-tolerant, containerized infrastructure capable of supporting enterprise-scale robotics and industrial IoT systems.

---

#  System Architecture

```text
               ┌──────────────────────┐
               │ Hardware / Simulator │
               └──────────┬───────────┘
                          │ Serial Stream
                          ▼
┌──────────────────────────────────────────────────┐
│             aether_gateway (FastAPI)             │
│                                                  │
│ • COM Failover                                   │
│ • Anomaly Detection                              │
│ • Metrics Exporter                               │
│ • Producer Interface                             │
└────┬──────────────┬─────────────┬───────────┬────┘
     │ Publish      │ Webhook     │ SQL       │ Metrics
     ▼              ▼             ▼           ▼
┌─────────┐    ┌─────────┐   ┌─────────┐ ┌──────────┐
│Redpanda │    │   n8n   │   │Postgres │ │Prometheus│
│ :19092  │    │ :5678   │   │ :5432   │ │ :9090    │
└────┬────┘    └─────────┘   └─────────┘ └────┬─────┘
     │ Kafka                                  │ PromQL
     ▼                                         ▼
┌─────────┐                              ┌─────────┐
│ Console │                              │ Grafana │
│ :8080   │                              │ :3000   │
└─────────┘                              └─────────┘
```

---

#  Ideation & Purpose

Mission-critical engineering systems cannot rely solely on raw sensor logging.

Modern robotics and industrial systems require continuous awareness of:

- System health
- Processing latency
- Resource utilization
- Sensor variance
- Hardware failures
- Performance bottlenecks

Level 4 transforms ChronoEngine from a **reactive logging platform** into a **proactive observability engine** capable of detecting anomalies, monitoring infrastructure in real time, and dispatching automated alerts before failures become catastrophic.

---

#  Problem Statement

## Limitations of Level 3

Although Level 3 successfully containerized the gateway and database, several operational challenges remained.

### Relational Database Bottleneck

Executing analytical queries such as:

- Rolling averages
- Moving windows
- Standard deviation calculations

directly on PostgreSQL significantly impacts write throughput.

---

### Lack of Operational Visibility

Without dedicated monitoring infrastructure, diagnosing issues required manual inspection of:

- CPU usage
- Memory leaks
- HTTP failures
- Gateway crashes
- Network latency

through SSH logs.

---

### Manual Failure Detection

Hardware outages and telemetry anomalies depended entirely on human observation.

No automated notification system existed.

---

#  Level 4 Solution

Level 4 introduces a modern observability architecture by integrating:

| Component | Purpose |
|-----------|----------|
| **Prometheus** | Time-series metric collection |
| **Grafana** | Live dashboards |
| **Redpanda** | Distributed event streaming |
| **n8n** | Automated incident workflows |

This separates operational analytics from transactional storage while improving scalability and resilience.

---

#  Architectural Design Decisions

## 1. Pull-Based Metrics

### Chosen

**Prometheus**

### Alternative

StatsD / Graphite

### Why?

Prometheus periodically scrapes metrics every five seconds instead of accepting pushed data.

Advantages include:

- Controlled ingestion rate
- Prevents monitoring overload
- Better fault isolation
- Simpler scaling

---

## 2. Event Streaming

### Chosen

**Redpanda**

### Alternative

Direct database writes

### Why?

Writing directly into PostgreSQL tightly couples ingestion with persistence.

Redpanda introduces:

- Append-only event logs
- Buffered ingestion
- Network fault tolerance
- Zero telemetry loss during database downtime

---

## 3. Dashboarding

### Chosen

**Grafana**

### Alternative

Custom frontend dashboards

### Why?

Grafana already provides:

- PromQL integration
- Alert rules
- Variables
- Dynamic dashboards
- Enterprise visualization

without maintaining custom charting software.

---

#  Core Algorithms

---

## Algorithm A — Time-Series Metric Aggregation (TSMAA)

Used to instrument gateway health while maintaining minimal request latency.

```text
1. Initialize Prometheus metrics.

2. Receive telemetry frame.

3. Increment:
   http_requests_total

4. Record:
   request_processing_seconds

5. If anomaly detected:
      telemetry_anomalies_total++

6. Expose metrics through:
      /metrics

7. Prometheus scrapes every T seconds.

8. Compute rates:

   rate(http_requests_total[1m])
```

---

## Algorithm B — Resilient Hardware Failover (RHFA)

Ensures uninterrupted gateway operation even when hardware disconnects.

```text
1. Connect to COM4.

2. If successful:
      Read hardware stream
      Parse JSON
      Process telemetry

3. Else:
      Log warning
      Activate mock driver
      Generate synthetic telemetry

4. Continue streaming.

5. Retry hardware connection periodically.
```

---

#  Engineering Concepts Demonstrated

- Time-Series Databases (TSDB)
- PromQL Query Language
- Event-Driven Architecture (EDA)
- Kafka-Compatible Streaming
- Docker Container Networking
- Service Discovery
- COM Port Failover
- Infrastructure Observability
- SLA & SLO Monitoring
- Histogram Metrics
- Counter & Gauge Instrumentation
- Asynchronous Webhook Dispatch
- Distributed Message Queues

---

#  Technology Stack

| Component | Container | Port | Purpose |
|------------|-----------|------|----------|
| FastAPI Gateway | `aether_gateway` | 8000 | Sensor ingestion, failover, metrics |
| PostgreSQL | `aether_db` | 5432 | Persistent telemetry storage |
| Redpanda | `aether_redpanda` | 19092 | Kafka-compatible streaming |
| Redpanda Console | `aether_console` | 8080 | Topic inspection |
| Prometheus | `aether_prometheus` | 9090 | Metrics scraping |
| Grafana | `aether_grafana` | 3000 | Visualization |
| n8n | `n8n` | 5678 | Workflow automation |

---

#  Getting Started

## Prerequisites

- Docker Desktop
- Git
- PowerShell or Terminal

---

## Clone Repository

```bash
git clone <repository-url>

cd level-4
```

---

## Build & Start

```bash
docker compose up --build -d
```

---

## Verify Containers

```bash
docker compose ps
```

---

## Restart Prometheus

If `prometheus.yml` is modified:

```bash
docker compose restart aether_prometheus
```

---

#  Service Endpoints

| Service | URL |
|----------|-----|
| FastAPI Docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Prometheus Targets | http://localhost:9090/targets |
| Grafana | http://localhost:3000 |
| Redpanda Console | http://localhost:8080 |
| n8n | http://localhost:5678 |

---

## Default Grafana Credentials

```text
Username: admin
Password: admin
```

---

#  Verification

## Step 1

Open:

```
http://localhost:9090/targets
```

Verify that:

```
aether_gateway
```

shows:

```
UP
```

with a green status badge.

---

## Step 2

Navigate to the **Graph** page and execute:

```promql
up{job="aether_gateway"}
```

---

## Expected Output

```text
1
```

A returned value of **1** confirms:

- Prometheus successfully scrapes the gateway
- Docker networking is functioning
- Metrics endpoint is operational
- Telemetry processing pipeline is healthy

---

#  Project Highlights

- High-frequency telemetry ingestion
- Kafka-compatible event streaming
- Hardware COM failover
- Time-series observability
- Distributed container architecture
- Automated webhook notifications
- Enterprise-grade dashboards
- Real-time anomaly monitoring
- Fault-tolerant infrastructure
- Production-ready DevOps workflow

---

#  Future Enhancements

- Kubernetes deployment
- Horizontal gateway scaling
- Distributed Prometheus federation
- OpenTelemetry integration
- Loki centralized logging
- Jaeger distributed tracing
- MQTT edge gateway support
- AI-driven anomaly prediction
- Multi-node Redpanda clustering

---

#  License

This project is intended for educational, research, and engineering demonstration purposes.

---

##  ChronoEngine Analytics

**Level 4 — Full-Stack Observability, Streaming & Incident Response**

Building enterprise-grade telemetry infrastructure for robotics, industrial IoT, and mission-critical systems.