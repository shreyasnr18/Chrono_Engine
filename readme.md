# ChronoEngine Analytics (AetherEdge)

An end-to-end, multi-level telemetry processing and real-time observability platform. ChronoEngine Analytics ingests raw physical microcontroller signals, edge computer vision metrics, and operating system performance indicators, transforming ephemeral hardware feeds into an enterprise-grade, highly resilient time-series telemetry pipeline.

---

# System Architecture

```text
[ Level 0: Physical Hardware ]
  • Arduino UNO / Analog Sensors (Voltage, Temp)
            │
            │ (Serial / USB Communication)
            ▼
[ Level 1: Ingestion & Signal Processing ]
  • Python Serial Drivers (pyserial)
  • Signal Smoothing & ADC Conversion
            │
            │ (Local Frame Streams)
            ▼
[ Level 2: Edge Vision Analytics ]
  • OpenCV Video Processing Loop
  • Frame Rate (FPS) & Latency Calculation (time.perf_counter)
            │
            │ (Unified Multi-Domain Signals)
            ▼
[ Level 3: FastAPI Gateway & Microservice Stack ]
  • FastAPI Async Gateway with Pydantic Validation
  • Automatic COM Port Failover
  • PostgreSQL Storage (aether_db)
  • n8n Webhook Anomaly Dispatcher
  • Docker Compose Orchestration
            │
            │ (Stateless HTTP Prometheus Scrape Endpoint :8000/metrics)
            ▼
[ Level 4: Unified Time-Series & Observability Engine ]
  • Prometheus TSDB (:9090) - High-Throughput Time-Series Engine
  • Grafana Real-Time Dashboards (:3000) with Native PromQL
  • Direct Kernel (psutil), Vision (cv2), and Sensor (pyserial) Metrics
            │
            │ (Audited Session Metrics)
            ▼
[ Level 5: Automated Reporting Engine ]
  • Printable HTML/PDF Engineering Datasheet Generator
```

---

# Detailed Level Breakdown (Level 0 to Level 4)

---

## Level 0: Physical Hardware & Raw Serial Interfaces

### 1. Problem Statement

Raw hardware sensor outputs (voltage dividers, temperature probes) connected to microcontrollers export volatile analog-to-digital converter (ADC) values over serial UART/USB channels. These raw signals are unstructured, prone to noise, lack physical unit formatting, and vanish if not actively read from the hardware serial buffer.

### 2. Reason for Upscaling

Raw serial outputs cannot be consumed directly by analytics tools or web services without structured framing, rate limiting, and driver-level error handling.

### 3. Solution Built

Established a baseline physical interface standard using Arduino UNO microcontrollers. Implemented firmware that samples analog pins (A0, A1), formats readings into structured comma-separated values (CSV), and broadcasts them over USB serial at 9600 baud.

### 4. Justification

Relying on standardized serial string formatting allows downstream Python interfaces to consume raw hardware telemetry deterministically without requiring specialized binary protocol decoders at the lowest layer.

---

## Level 1: Hardware-Level Ingestion & Local Signal Conditioning

### 1. Problem Statement

Serial port streams are unstable. Unplugging a USB cable, experiencing baud rate mismatches, or encountering buffer overruns causes script failures. Furthermore, raw ADC integers must be mathematically converted to physical units (Volts, Celsius) while filtering out electrical noise.

### 2. Reason for Upscaling

Unfiltered sensor noise creates false anomaly triggers, while unhandled serial disconnects crash backend listener loops.

### 3. Solution Built

Developed a Python-based local ingestion driver (`pyserial`) that reads raw serial streams, applies moving-average smoothing algorithms to reduce voltage jitter, and converts ADC steps to real units ($V_{out} = \frac{ADC \times 5.0}{1023}$).

### 4. Justification

Moving processing logic off the microcontroller and onto the host Python driver frees up microcontroller SRAM and allows flexible software-based digital filtering without modifying board firmware.

---

## Level 2: Computer Vision Pipeline & Edge AI Telemetry

### 1. Problem Statement

Modern industrial and robotic systems do not rely on scalar sensor data alone; they operate alongside real-time computer vision (CV) and machine learning edge models. Measuring camera frame rates, execution latency, and algorithm throughput in parallel with physical hardware metrics requires high-precision non-blocking loops.

### 2. Reason for Upscaling

Single-threaded sensor scripts cannot process video frames simultaneously without causing massive data drops on the serial line due to thread blocking.

### 3. Solution Built

Integrated an OpenCV processing engine using high-precision hardware timers (`time.perf_counter()`). The engine benchmarks live camera frames, applies edge-detection algorithms (Canny/Gaussian blur), and calculates processing latency (milliseconds per frame) and real-time frames per second (FPS).

### 4. Justification

Benchmarking CV algorithms in the same pipeline as physical telemetry provides a complete picture of edge device performance, ensuring frame drops can be correlated directly with CPU load or power fluctuations.

---

## Level 3: Microservice Orchestration, Relational Persistence & Webhook Alerting

### 1. Problem Statement

Running isolated scripts across separate terminal windows introduces environment drift, dependency conflicts, and high operational friction. Storing raw text files lacks schema validation, while polling databases for safety alerts introduces unacceptable latency. Furthermore, a loose physical USB cable crashes the backend.

### 2. Reason for Upscaling

Enterprise deployments require microservice isolation, automated API documentation, structured database persistence, resilient hardware failover, and millisecond-level event-driven alerting.

### 3. Solution Built

Engineered a containerized microservice architecture managed via Docker Compose:

- **FastAPI Gateway:** Async REST API with Pydantic schema validation.
- **Resilient Failover Worker:** Automatically catches physical COM port disconnects and seamlessly switches to an internal driver to maintain gateway availability.
- **PostgreSQL (`aether_db`):** Relational persistence for validated telemetry.
- **n8n Automation Engine:** Event-driven webhook alerting triggering instant HTTP POST payloads upon voltage threshold breaches.
- **Prometheus & Grafana:** Containerized observability stack for service health tracking.

### 4. Justification

Packaging the gateway, database, metrics collector, and automation engine inside a isolated Docker bridge network guarantees zero environment drift, automatic service recovery, and instant anomaly notification without database polling overhead.

---

## Level 4: High-Frequency Prometheus Time-Series Engine & Grafana Observability

### 1. Problem Statement

Storing high-frequency time-series data inside relational engines (PostgreSQL) causes severe performance degradation due to write-ahead log overhead, lock contention, and complex index scans. Furthermore, microcontrollers export 13-digit millisecond epochs while PostgreSQL `to_timestamp()` functions expect 10-digit second epochs. Division inside SQL queries resulted in 32-bit integer overflow, invalid dates (thousands of years in the future), unsupported Grafana SQL macros (`$__unixEpochMsFilter`), and panel rendering failures (`Red Triangle Query Errors`).

### 2. Reason for Upscaling

Relational SQL engines are not built for sub-second time-series streaming. A dedicated time-series database (TSDB) was required to eliminate query latency, remove timestamp math errors, and provide zero-latency live visual dashboards.

### 3. Solution Built

Migrated the level 4 architecture entirely to **Prometheus TSDB** paired with a custom FastAPI Gateway Exporter (`aether_gateway.py`):

- **Stateless Scrape Endpoint:** Exposed a `/metrics` endpoint using `prometheus_client` on port `:8000`.
- **100% Real Data Guarantee:** Sourced live telemetry across all domains—physical hardware (`pyserial`), vision benchmarks (`cv2`), and OS kernel performance (`psutil`).
- **Native PromQL Integration:** Replaced complex SQL queries with native PromQL expressions (`voltage`, `cv_processing_fps`, `host_cpu_usage_percent`).
- **Target Health Monitoring:** Implemented `up{job="aether_gateway"}` mapped to Grafana Stat panels (`1 = ONLINE` in green, `0 = OFFLINE` in red).

### 4. Justification

Prometheus automatically timestamps incoming telemetry at ingress time in memory, completely eliminating SQL timestamp conversion math, integer overflow risks, and database disk IOPS bottlenecks.

---

# Architectural Evolution & Summary Matrix

| Level | Ingestion Source | Key Technologies | Primary Role | Failure Mode Resolved |
|-------|------------------|------------------|--------------|-----------------------|
| **Level 0** | Microcontroller ADC Pins | Arduino C++, Serial UART | Raw signal generation | Eliminates unstructured binary output |
| **Level 1** | USB Serial Stream | Python, `pyserial` | Signal conversion & digital filtering | Removes voltage jitter and sensor noise |
| **Level 2** | USB Camera / Video Stream | OpenCV, `time.perf_counter()` | Vision benchmarking & FPS tracking | Prevents thread-blocking frame drops |
| **Level 3** | Serial / REST Requests | FastAPI, PostgreSQL, Docker, n8n | Microservice gateway & incident alerting | Resolves COM port disconnect crashes & unvalidated inputs |
| **Level 4** | Unified Multi-Domain Pipeline | Prometheus TSDB, Grafana, `psutil` | High-frequency time-series observability | Resolves SQL epoch math, integer overflow, & IOPS bottlenecks |

---

# Real-World Applications & Utility

1. **Industrial Robotics & Autonomous Rigs:** Real-time monitoring of motor current draw, board supply voltage, thermal states, and control-loop latency during physical operations.

2. **Edge AI & Computer Vision Benchmarking:** Stress-testing neural network models on edge hardware while continuously tracking execution FPS, frame latency, CPU load, and thermal throttling.

3. **Smart IoT Gateway Infrastructures:** Monitoring remote IoT gateway connectivity, tracking uptime via Prometheus health targets, and dispatching instant webhook alerts during power anomalies.

4. **Automated Engineering Compliance & Auditing:** Generating verifiable, non-simulated HTML/PDF datasheets from Prometheus session statistics for academic, industrial, or regulatory evaluation.

---

# Getting Started & Local Execution

## Prerequisites

- Python 3.9+ installed on host machine.
- Docker Desktop installed and running.
- USB Microcontroller (Arduino) or Webcam (Optional; system defaults to active system kernel metrics if hardware is detached).

---

## Deployment Steps

### 1. Clone Repository & Install Python Dependencies

```bash
git clone https://github.com/shreyasnr18/Chrono_Engine.git
cd Chrono_Engine
pip install prometheus_client psutil pyserial opencv-python fastapi uvicorn requests
```

---

### 2. Launch Level 4 Telemetry Gateway

```bash
cd level-4
python aether_gateway.py
```

The gateway will initialize and expose live Prometheus metrics at:

```
http://localhost:8000/metrics
```

---

### 3. Launch Docker Observability Stack

In a separate terminal window, start Prometheus and Grafana:

```bash
cd level-4
docker compose up -d
```

---

### 4. Verify Active Services

- **FastAPI Metrics Endpoint:** `http://localhost:8000/metrics`
- **Prometheus Targets UI:** `http://localhost:9090/targets` (Verify `aether_gateway` is **UP**)
- **Grafana Dashboard:** `http://localhost:3000` (Credentials: `admin` / `admin`)

---

### 5. Generate Level 5 Session Datasheet

Run the automated report generator to pull session averages from Prometheus and build a printable engineering document:

```bash
python generate_datasheet.py
```

Open `telemetry_datasheet.html` in your browser and press `Ctrl + P` to save as PDF.

---

# Conclusion

ChronoEngine Analytics demonstrates the complete lifecycle of telemetry engineering—evolving from raw physical analog voltages into a production-grade, microservice-driven observability engine. By systematically identifying and resolving bottlenecks across relational database storage, timestamp epoch desynchronization, and microservice resilience, the platform delivers a zero-latency, highly scalable architecture suitable for modern edge AI, industrial IoT, and robotic system monitoring.