# Level 4: Unified Time-Series Aggregation & Metric Engine

> **REAL-TIME DATA GUARANTEE:** This system is built strictly on **100%
> live physical telemetry**. No mock generators, fake random values, or
> simulated streams exist in Level 4. Every metric is pulled directly
> from active hardware registers, kernel API calls, or real-time vision
> execution loops.

------------------------------------------------------------------------

## 1. Problem Statement

At Level 4, the primary objective is to ingest, aggregate, and
standardize high-frequency telemetry streams originating from
heterogeneous sources (hardware microcontrollers, host OS, computer
vision loops) into a unified time-series engine for real-time
visualization and downstream report generation.

Before achieving stability, the pipeline faced critical architectural
bottlenecks:

-   **Database & Query Impedance Mismatch:** Relational engines like
    PostgreSQL introduced massive overhead when handling high-frequency
    time-series data.
-   **Timestamp & Epoch Desynchronization:** Sensor boards (e.g.,
    Arduino) export Unix timestamps in 13-digit millisecond epochs.
    PostgreSQL `to_timestamp()` functions expect 10-digit second epochs,
    leading to integer overflow errors, out-of-range dates (thousands of
    years in the future), and panel rendering failures in Grafana.
-   **Macro Dependency Fragility:** Relying on database-specific SQL
    macros (such as `$__unixEpochMsFilter` or `$__unixEpochFilter`)
    caused continuous query execution errors
    (`Panel Error: Red Triangle`) due to plugin syntax
    incompatibilities.
-   **High Query Latency:** Storing raw telemetry rows in SQL tables
    required complex casting (`BIGINT`, `TIMESTAMP`), explicit
    filtering, and index scans just to render simple live line graphs.

------------------------------------------------------------------------

## 2. Solution Justification (Point-Wise Architecture Breakdown)

The pipeline migrated away from relational SQL storage for time-series
streaming and transitioned entirely to **Prometheus** as the Level 4
Metric Engine.

-   **Ingestion Model:**

-   *Relational SQL:* Required heavy, blocking `INSERT INTO`
    transactions for every metric event, creating disk lock contention.

-   *Prometheus (Level 4):* Utilizes a stateless, high-throughput HTTP
    `/metrics` pull-scrape endpoint operating asynchronously.

-   **Timestamp Handling:**

-   *Relational SQL:* Required manual millisecond-to-second conversions
    (`/ 1000.0`), complex timezone parsing, and carried integer overflow
    risks.

-   *Prometheus (Level 4):* Automatically timestamps incoming data at
    scrape time in memory, removing mathematical transformation errors
    completely.

-   **Query Complexity:**

-   *Relational SQL:* Demanded verbose SQL syntax, explicit casting
    (`::numeric`, `::bigint`), and fragile Grafana macros.

-   *Prometheus (Level 4):* Evaluates clean, native PromQL expressions
    (such as `voltage` or `up{job="aether_gateway"}`) with zero
    date-parsing overhead.

-   **System Overhead:**

-   *Relational SQL:* Incurred database connection pooling overhead,
    transaction logs, and rigid schema maintenance.

-   *Prometheus (Level 4):* Runs an in-memory time-series buffer backed
    by chunk-compressed TSDB storage designed specifically for
    high-frequency telemetry.

-   **Target Health Verification:**

-   *Relational SQL:* Required manual heartbeat query logic and
    timestamp freshness comparisons.

-   *Prometheus (Level 4):* Features built-in, instant target state
    monitoring via the native `up` metric (`1 = ONLINE`, `0 = OFFLINE`).

------------------------------------------------------------------------

## 3. Architecture & Data Flow

    +-----------------------------------------------------------------------------------+
    |                                 REAL DATA SOURCES                                 |
    +-----------------------------------------------------------------------------------+
    |  [ Level 1: Hardware ]    |  [ Level 2: Computer Vision ]  |  [ Level 3: Host OS ] |
    |  Arduino Analog Reads     |  OpenCV Canny Benchmark        |  psutil Hardware API  |
    |  (Voltage, Temp Sensors)  |  (Live FPS, Latency ms)        |  (CPU %, RAM % Load)  |
    +---------------------------+--------------------------------+----------------------+
                                                |
                                                v  (Live Internal Feeds)
    +-----------------------------------------------------------------------------------+
    |                        LEVEL 4: EXPORTER & TIME-SERIES ENGINE                     |
    +-----------------------------------------------------------------------------------+
    |                                                                                   |
    |   +---------------------------------------------------------------------------+   |
    |   | Aether Gateway Exporter (python: `aether_gateway.py`)                     |   |
    |   | Serves live non-mocked metrics on `http://localhost:8000/metrics`         |   |
    |   +---------------------------------------------------------------------------+   |
    |                                         |                                         |
    |                                         v  (1s Pull Scrape)                       |
    |   +---------------------------------------------------------------------------+   |
    |   | Prometheus Time-Series Database (`localhost:9090`)                        |   |
    |   | Ingests raw metrics, handles retention, executes PromQL queries           |   |
    |   +---------------------------------------------------------------------------+   |
    |                                                                                   |
    +-----------------------------------------------------------------------------------+
                                                |
                             +------------------+------------------+
                             |                                     |
                             v                                     v
    +----------------------------------+ +----------------------------------------------+
    | GRAFANA DASHBOARDS               | | LEVEL 5: REPORT ENGINE                       |
    | Live Time-Series Graphs          | | Automated HTML/PDF Datasheet Generator       |
    | Green `up` Stat Badge (ONLINE)   | | Session statistical averages & peak values   |
    +----------------------------------+ +----------------------------------------------+

------------------------------------------------------------------------

## 4. What Worked vs. What Failed

### What Failed

-   **PostgreSQL Epoch Math:** Dividing millisecond timestamps by
    `1000.0` inside `to_timestamp()` queries caused arithmetic casting
    errors and query timeouts.
-   **Non-existent Grafana SQL Macros:** Invoking
    `$__unixEpochMsFilter()` on PostgreSQL datasources failed because
    the plugin lacks native millisecond macro support.
-   **Histogram Panels for Gauge Data:** Plotting single-value
    continuous gauge metrics (like temperature or voltage) on Histogram
    panels resulted in flat, unrendered graphs.
-   **Relational Storage Overhead:** Using traditional SQL database
    structures for rapid time-series streaming produced unnecessary disk
    I/O and connection bottlenecks.

### What Worked

-   **Prometheus Pull Architecture:** Running a lightweight WSGI HTTP
    server on port `:8000` via `prometheus_client` stabilized all metric
    ingestion.
-   **Native PromQL Execution:** Querying
    `voltage{source="arduino_uno_01"}` or
    `telemetry_temperature_celsius` eliminated all date-parsing errors
    and query exceptions.
-   **`up` Metric for Health Badging:** Passing
    `up{job="aether_gateway"}` into a Grafana **Stat Panel** mapped
    directly to `1` (Green / ONLINE) and `0` (Red / OFFLINE).
-   **Direct Hardware & Kernel Binding:** Connecting host system API
    calls (`psutil`) and high-precision timers (`cv2`) directly to
    Prometheus Gauges provided responsive, non-mocked hardware
    telemetry.

------------------------------------------------------------------------

## 5. Errors, Hurdles & Solution Mapping

-   **Error 1: Grafana "No Data" & Red Triangle Query Error**

-   *Root Cause:* The PostgreSQL query failed because `to_timestamp()`
    received 13-digit millisecond values instead of 10-digit seconds.

-   *Solution Mapped:* Migrated the pipeline to Prometheus. Ingress
    timestamps are auto-generated at scrape time, completely removing
    manual date math.

-   **Error 2: Macro Execution Failure (`$__unixEpochMsFilter`)**

-   *Root Cause:* The PostgreSQL Grafana plugin lacks native support for
    `$__unixEpochMsFilter`.

-   *Solution Mapped:* Replaced SQL macros with PromQL expressions.
    PromQL natively respects Grafana's time-picker window without macro
    syntax dependencies.

-   **Error 3: PostgreSQL 32-bit Integer Overflow**

-   *Root Cause:* Multiplying `$__unixEpochFrom()` by `1000` inside SQL
    `WHERE` clauses exceeded standard 32-bit integer limits.

-   *Solution Mapped:* Removed SQL time filters. Prometheus manages time
    windows natively in memory via chunk-compressed TSDB blocks.

-   **Error 4: Empty Panel Rendering**

-   *Root Cause:* Visualization type was set to *Histogram* instead of
    *Time series* for continuous single-value gauge metrics.

-   *Solution Mapped:* Reconfigured panel settings---switched
    visualization to **Time series** for continuous line graphs and
    **Stat** for discrete status indicators.

-   **Error 5: Risk of Simulated / Mocked Data**

-   *Root Cause:* Default metric examples often rely on `random()`
    numbers or static variables, invalidating real hardware testing.

-   *Solution Mapped:* Enforced direct physical and OS bindings across
    all levels (`pyserial` for analog ADC readings,
    `time.perf_counter()` for vision execution timing, and `psutil` for
    host kernel processor calls).

------------------------------------------------------------------------

## 6. Practical Utility, Target Audience & Real-World Applications

### Exact Practical Utility

-   **Zero-Database Latency:** Provides real-time, sub-second monitoring
    of hardware and software pipelines without writing a single row to a
    disk database.
-   **Multi-Layer Synchronization:** Unifies hardware sensor data
    (voltage/temperature), software algorithms (OpenCV/YOLO execution
    speeds), and OS performance metrics into one coherent dashboard.
-   **Automated Engineering Audit Trail:** Feeds directly into Level 5
    report generators to automatically output printable,
    publication-ready physical datasheets based on actual session
    averages.

### Target Audience

-   **Robotics & Embedded Systems Engineers:** Needing real-time
    physical telemetry (power draw, thermal states, sensor voltages)
    straight from microcontrollers during hardware testing.
-   **Computer Vision & Edge AI Developers:** Benchmarking live
    inference speed (FPS), execution latency, and frame-drop rates under
    real processing loads.
-   **DevOps & Infrastructure Engineers:** Monitoring system resource
    limits (CPU core spikes, memory allocation, thermal constraints) on
    host workstations or edge devices.
-   **QA & Field Test Engineers:** Requiring verifiable, non-simulated
    evaluation documents generated automatically at the end of physical
    test runs.

### Real-World Applications

-   **Autonomous Rover & Robotic Rig Evaluation:** Streaming live power
    consumption, motor temperature, and control-loop execution speed
    during physical runs.
-   **Edge AI Model Benchmarking:** Stress-testing object detection
    models across varying video resolutions, lighting conditions, and
    hardware acceleration profiles.
-   **Industrial IoT Gateway Monitoring:** Tracking field-deployed
    gateway health, sensor node stability, and communication channel
    uptime via central status panels.
-   **Automated Physical QA & Compliance Reporting:** Exporting
    timestamped, verifiable HTML/PDF engineering reports for academic,
    client, or organizational evaluation.

------------------------------------------------------------------------

## 7. Executive Synthesis

Level 4 successfully solves the core challenges of time-series ingestion
by eliminating database-level timestamp conversions, SQL macro
dependencies, and high-frequency storage overhead. By replacing
relational database queries with a dedicated Prometheus metric engine,
the pipeline establishes a zero-latency, 100% real-data telemetry
architecture. This foundation ensures that all visual dashboards in
Grafana and downstream physical datasheets in Level 5 reflect exact,
verifiable physical and system performance.
