import json
import logging
import os
from aiokafka import AIOKafkaProducer

logger = logging.getLogger("aether_kafka")


class TelemetryStreamProducer:

    def __init__(self):
        self.broker = os.getenv("REDPANDA_BROKER", "aether_redpanda:9092")
        self.producer = None

    async def start(self):
        """Initializes the async Kafka/Redpanda producer connection."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        try:
            await self.producer.start()
            logger.info(f"Connected to Redpanda Broker at {self.broker}")
        except Exception as e:
            logger.error(f"Failed to connect to Redpanda broker: {e}")

    async def stop(self):
        """Gracefully shuts down the producer connection."""
        if self.producer:
            await self.producer.stop()

    async def send_telemetry(self, topic: str, data: dict):
        """Publishes a telemetry event frame to the Redpanda event bus."""
        if self.producer:
            try:
                await self.producer.send_and_wait(topic, data)
            except Exception as e:
                logger.error(f"Error publishing message to {topic}: {e}")