# Level 4: Unified Time-Series Aggregation & Metric Engine

> **REAL-TIME DATA GUARANTEE:** This system is built strictly on **100% live physical telemetry**. No mock generators, fake random values, or simulated streams exist in Level 4. Every metric is pulled directly from active hardware registers, kernel API calls, or real-time vision execution loops.

---

# System Validation Snapshots

## 1. FastAPI Serial Stream

<p align="center">
    <img src="assets/FastAPI Serial Stream.png"
         alt="FastAPI Serial Stream"
         width="1000">
</p>

---

## 2. Grafana Dashboard

<p align="center">
    <img src="./assets/grafana.png" width="1000">
</p>

---

## 3. Prometheus Targets Page

<p align="center">
    <img src="assets/Prometheus Targets Page.png"
         alt="Prometheus Targets Page"
         width="1000">
</p>

---

## 4. Redpanda Console & n8n Alert

<p align="center">
    <img src="assets/Redpanda Console &amp; n8n Alert.png"
         alt="Redpanda Console &amp; n8n Alert"
         width="1000">
</p>

---

## 1. Problem Statement

At Level 4, the primary objective is to ingest, aggregate, and standardize high-frequency telemetry streams originating from heterogeneous sources (hardware microcontrollers, host OS, computer vision loops) into a unified time-series engine for real-time visualization and downstream report generation.

Before achieving stability, the pipeline faced critical architectural bottlenecks:

- **Database & Query Impedance Mismatch:** Relational engines like PostgreSQL introduced massive overhead when handling high-frequency time-series data.
- **Timestamp & Epoch Desynchronization:** Sensor boards (e.g., Arduino) export Unix timestamps in 13-digit millisecond epochs. PostgreSQL `to_timestamp()` functions expect 10-digit second epochs, leading to integer overflow errors, out-of-range dates (thousands of years in the future), and panel rendering failures in Grafana.
- **Macro Dependency Fragility:** Relying on database-specific SQL macros (such as `$__unixEpochMsFilter` or `$__unixEpochFilter`) caused continuous query execution errors (`Panel Error: Red Triangle`) due to plugin syntax incompatibilities.
- **High Query Latency:** Storing raw telemetry rows in SQL tables required complex casting (`BIGINT`, `TIMESTAMP`), explicit filtering, and index scans just to render simple live line graphs.

---

## 2. Solution Justification (Point-Wise Architecture Breakdown)

The pipeline migrated away from relational SQL storage for time-series streaming and transitioned entirely to **Prometheus** as the Level 4 Metric Engine.

- **Ingestion Model**

  - **Relational SQL:** Required heavy, blocking `INSERT INTO` transactions for every metric event, creating disk lock contention.

  - **Prometheus (Level 4):** Utilizes a stateless, high-throughput HTTP `/metrics` pull-scrape endpoint operating asynchronously.

- **Timestamp Handling**

  - **Relational SQL:** Required manual millisecond-to-second conversions (`/1000.0`), complex timezone parsing, and carried integer overflow risks.

  - **Prometheus (Level 4):** Automatically timestamps incoming data at scrape time in memory, removing mathematical transformation errors completely.

- **Query Complexity**

  - **Relational SQL:** Demanded verbose SQL syntax, explicit casting (`::numeric`, `::bigint`), and fragile Grafana macros.

  - **Prometheus (Level 4):** Evaluates clean, native PromQL expressions (such as `voltage` or `up{job="aether_gateway"}`) with zero date-parsing overhead.

- **System Overhead**

  - **Relational SQL:** Incurred database connection pooling overhead, transaction logs, and rigid schema maintenance.

  - **Prometheus (Level 4):** Runs an in-memory time-series buffer backed by chunk-compressed TSDB storage designed specifically for high-frequency telemetry.

- **Target Health Verification**

  - **Relational SQL:** Required manual heartbeat query logic and timestamp freshness comparisons.

  - **Prometheus (Level 4):** Features built-in, instant target state monitoring via the native `up` metric (`1 = ONLINE`, `0 = OFFLINE`).

---

## 3. Architecture & Data Flow


```text
+-----------------------------------------------------------------------------------+
|                                 REAL DATA SOURCES                                 |
+-----------------------------------------------------------------------------------+
| [ Level 1: Hardware ] | [ Level 2: Computer Vision ] | [ Level 3: Host OS ]       |
| Arduino Analog Reads  | OpenCV Canny Benchmark       | psutil Hardware API        |
| (Voltage, Temp)       | (FPS, Latency)               | (CPU, RAM, Temperature)    |
+-----------------------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------------------+
|                 LEVEL 4 : EXPORTER & TIME-SERIES ENGINE                           |
+-----------------------------------------------------------------------------------+
|  Aether Gateway Exporter (FastAPI + Prometheus Client)                            |
|  http://localhost:8000/metrics                                                    |
+-----------------------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------------------+
|                   PROMETHEUS TSDB (localhost:9090)                                |
+-----------------------------------------------------------------------------------+
                                  |
                                  +--------------------+
                                  |                    |
                                  v                    v
                         Grafana Dashboards      Level 5 Report Engine