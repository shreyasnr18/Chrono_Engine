# Level 4: Unified Time-Series Aggregation & Metric Engine

> **REAL-TIME DATA GUARANTEE:**  
> This system is built strictly on **100% live physical telemetry**. No mock generators, fake random values, or simulated streams exist in Level 4. Every metric is pulled directly from active hardware registers, kernel API calls, or real-time vision execution loops.

---

# System Validation Snapshots

The following screenshots validate the successful deployment and operation of the complete Level 4 telemetry pipeline, including the FastAPI metric exporter, Prometheus target discovery, Grafana real-time dashboards, and Redpanda streaming infrastructure.

---

## 1. FastAPI Serial Stream

The FastAPI Gateway Exporter exposes all live telemetry through the `/metrics` endpoint. This endpoint is continuously scraped by Prometheus and serves as the primary ingestion interface for Level 4.

<p align="center">
    <img src="./assets/FastAPI Serial Stream.png"
         alt="FastAPI Serial Stream"
         width="1000">
</p>

---

## 2. Grafana Dashboard

Grafana visualizes the live Prometheus metrics in real time, displaying voltage, temperature, and exporter health status through continuously updating dashboards.

<p align="center">
    <img src="./assets/Grafana.png"
         alt="Grafana Dashboard"
         width="1000">
</p>

---

## 3. Prometheus Targets Page

The Prometheus Targets page verifies that the FastAPI Gateway Exporter is actively being scraped and that the telemetry endpoint is healthy and online.

<p align="center">
    <img src="./assets/Prometheus Targets Page.png"
         alt="Prometheus Targets Page"
         width="1000">
</p>

---

## 4. Redpanda Console & n8n Alert

The Redpanda Console demonstrates successful event streaming and message persistence, while the integrated n8n workflow enables automated monitoring and alert orchestration.

<p align="center">
    <img src="./assets/Redpanda Console &amp; n8n Alert.png"
         alt="Redpanda Console and n8n Alert"
         width="1000">
</p>

---

# 1. Purpose of Level 4

The primary purpose of Level 4 is to serve as the unified time-series aggregation, standardization, and monitoring layer for the entire ChronoEngine Analytics stack. It centralizes high-frequency, multi-domain telemetry feeds originating from Level 1 (microcontroller sensor signals), Level 2 (computer vision execution loops), and Level 3 (host operating system health) into a single, standardized Prometheus time-series database.

By decoupling metric collection from traditional relational databases, Level 4 enables real-time, sub-second visualization in Grafana and establishes a verified metric store for automated downstream engineering report generation.

---

# 2. Problem Statement

Prior to Level 4, streaming high-frequency hardware metrics into a standard relational backend (PostgreSQL) created significant technical bottlenecks that degraded system stability:

- **Relational Storage IOPS Bottlenecks:** Executing continuous SQL `INSERT INTO` transactions for sub-second telemetry streams generated severe disk lock contention and memory overhead.

- **Timestamp & Epoch Desynchronization:** Hardware microcontrollers (e.g., Arduino) output Unix timestamps in 13-digit millisecond epochs, whereas PostgreSQL `to_timestamp()` functions expect 10-digit second values. Division inside queries caused integer overflow errors, invalid date ranges (pushing timestamps thousands of years into the future), and empty dashboard panels.

- **SQL Macro Incompatibilities:** Relying on database-specific Grafana macros (such as `$__unixEpochMsFilter`) resulted in frequent query execution failures due to plugin syntax limitations.

- **Query Latency:** Fetching time-series lines required explicit type casting (`::numeric`, `::bigint`), index scans, and complex `WHERE` clauses, making live dashboard updates sluggish and error-prone.

---

# 3. Solutions Implemented & Architectural Justification

To resolve these issues, Level 4 completely replaces relational SQL time-series storage with **Prometheus TSDB** paired with a custom **FastAPI Gateway Exporter (`aether_gateway.py`)**.

## Point-Wise Architectural Breakdown

### Ingestion Model

**Relational SQL (Old)**

- Required blocking, heavy write transactions per metric event.

**Prometheus Engine (Level 4)**

- Uses an asynchronous, stateless HTTP `/metrics` pull-scrape endpoint that accepts metric registration without database locks.

---

### Timestamp Handling

**Relational SQL (Old)**

- Required manual millisecond-to-second conversion (`/1000.0`) and timezone parsing.

**Prometheus Engine (Level 4)**

- Automatically timestamps every metric at scrape time, eliminating mathematical transformation errors.

---

### Query Language & Efficiency

**Relational SQL (Old)**

- Required verbose SQL syntax, joins, casting and filtering.

**Prometheus Engine (Level 4)**

- Uses native PromQL expressions such as:

```promql
voltage

host_cpu_usage_percent

up{job="aether_gateway"}
```

---

### Storage Overhead

**Relational SQL (Old)**

- Heavy WAL generation
- Connection pooling
- Table maintenance

**Prometheus Engine (Level 4)**

- Chunk-compressed TSDB
- High-throughput in-memory storage
- Optimized for time-series workloads

---

### Target Health Monitoring

**Relational SQL (Old)**

- Required custom heartbeat logic.

**Prometheus Engine (Level 4)**

- Uses the native `up` metric.

```
1 = ONLINE

0 = OFFLINE
```

---

# 4. Architecture & Data Flow

```text
+-----------------------------------------------------------------------------------+
|                                 REAL DATA SOURCES                                 |
+-----------------------------------------------------------------------------------+
|  [ Level 1: Hardware ]    |  [ Level 2: Computer Vision ]  |  [ Level 3: Host OS ] |
|  Arduino Analog Reads     |  OpenCV Canny Benchmark        |  psutil Hardware API  |
|  (Voltage, Temp)          |  (FPS, Latency)                |  (CPU, RAM)           |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                       LEVEL 4: EXPORTER & TIME-SERIES ENGINE                      |
+-----------------------------------------------------------------------------------+
|  Aether Gateway Exporter (FastAPI + Prometheus Client)                            |
|  http://localhost:8000/metrics                                                    |
+-----------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                    PROMETHEUS TSDB (localhost:9090)                               |
+-----------------------------------------------------------------------------------+
                                            |
                          +------------------+------------------+
                          |                                     |
                          v                                     v
                 Grafana Dashboards                   Level 5 Report Engine
```

---

# 5. What Went Right vs. What Went Wrong

## What Went Right

- Stateless Metric Exporter
- Native PromQL Integration
- System Health Badging
- Direct Hardware & Kernel Binding

## What Went Wrong

- PostgreSQL Division Errors
- Unsupported SQL Macros
- Incorrect Panel Formatting
- 32-bit Integer Overflow

---

# 6. Error Remediation & Solution Mapping

### Error 1 — Grafana "No Data"

**Root Cause**

PostgreSQL received 13-digit millisecond timestamps.

**Solution**

Migrated to Prometheus automatic timestamp management.

---

### Error 2 — Unsupported SQL Macros

**Root Cause**

Grafana PostgreSQL plugin limitations.

**Solution**

Migrated to native PromQL.

---

### Error 3 — Integer Overflow

**Root Cause**

32-bit SQL arithmetic overflow.

**Solution**

Removed SQL filtering.

---

### Error 4 — Blank Histogram Panels

**Root Cause**

Wrong visualization selection.

**Solution**

Standardized dashboard panel types.

---

### Error 5 — Mock Data Risk

**Root Cause**

Random or static metric generators.

**Solution**

Bound all metrics directly to physical hardware and operating system APIs.

---

# 7. Comprehensive Justification of the Level 4 Solution

The combination of the FastAPI Gateway Exporter, Prometheus TSDB, and Grafana provides a robust telemetry architecture because it:

1. Eliminates database write bottlenecks.
2. Standardizes telemetry across hardware, computer vision, and operating system layers.
3. Produces verifiable engineering data for automated Level 5 report generation.

---

# 8. Public Testing & Verification Guide

## Prerequisites

- Python 3.9+
- Docker Desktop
- Arduino (optional)
- Webcam (optional)

---

## Install Dependencies

```bash
pip install prometheus_client psutil pyserial opencv-python
```

---

## Launch Gateway

```bash
python aether_gateway.py
```

Gateway endpoint:

```
http://localhost:8000/metrics
```

---

## Verify Metrics

```bash
curl http://localhost:8000/metrics
```

---

## Start Monitoring Stack

```bash
docker compose up -d
```

---

## Access Services

| Service | URL |
|---------|-----|
| Prometheus Targets | http://localhost:9090/targets |
| Grafana Dashboard | http://localhost:3000 |
| PromQL Test | `up{job="aether_gateway"}` |

---

# 9. Conclusion

Level 4 successfully replaces relational database structures with a dedicated Prometheus telemetry pipeline, eliminating timestamp conversion errors, SQL macro limitations, and high-frequency database bottlenecks. By enforcing 100% real hardware and operating system telemetry, it provides a resilient, low-latency observability layer that powers Grafana dashboards and supplies verified engineering data for automated Level 5 report generation.