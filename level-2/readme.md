# Level 2: Event Streaming & Message Broker - ChronoEngine Analytics

## Purpose
Level 2 integrates distributed event streaming using Redpanda as a high-throughput message broker. It introduces the `telemetry.raw` topic structure to decouple the data producer from downstream ingestion and processing services.

## Problem Solved
Directly sending high-frequency telemetry data directly to APIs or databases leads to network blocking, lost data packets during spikes, and severe pipeline tight-coupling. Level 2 solves this by inserting an asynchronous event buffer that guarantees zero data loss and absorbs throughput bursts without dropping messages.

## Algorithm: Asynchronous Message Brokering Algorithm (AMBA)
1. **Topic Provisioning**: Configure and instantiate the `telemetry.raw` partition topic with retention and compaction rules inside the Redpanda cluster.
2. **Producer Binding**: Establish a persistent connection between the telemetry producer and the broker using Kafka-compatible protocol APIs.
3. **Partition Queueing**: Receive serialized JSON payloads and append them sequentially to topic partitions with immutable offset tracking.
4. **Stream Verification**: Expose topic throughput, consumer lag, and partition health in real-time via the Redpanda Console interface (`http://localhost:8080`).

## Core Concepts Used
* **Distributed Message Brokering**: Utilizing Redpanda (a C++ based, Kafka-compatible engine) for low-latency streaming.
* **Topic Partitioning & Offset Management**: Organizing incoming telemetry streams into sequential, append-only logs.
* **Asynchronous Decoupling**: Separating data generation rates from consumption rates to protect downstream infrastructure.

## Architecture Justification
Redpanda was chosen over traditional Apache Kafka due to its lightweight single-binary C++ engine, zero JVM memory overhead, and fast startup performance. This makes it ideal for local containerized development while maintaining full compatibility with production Kafka ecosystems.