import math
import random
import time


class DigitalTwinSimulator:

    def __init__(self):
        self.step_count = 0
        self.base_voltage = 220.0
        self.temperature_c = 45.0

    def generate_frame(self) -> dict:
        self.step_count += 1

        # 1. Simulate natural sinusoidal voltage drift with Gaussian noise
        sine_wave = math.sin(self.step_count * 0.1) * 5.0
        noise = random.gauss(0, 0.5)
        voltage = self.base_voltage + sine_wave + noise

        # 2. Simulate thermal rise under load
        self.temperature_c += random.uniform(-0.1, 0.15)
        self.temperature_c = max(30.0, min(95.0, self.temperature_c))

        # 3. Randomly inject a 3% chance physical anomaly (Voltage Sag or Spike)
        is_anomaly = False
        if random.random() < 0.03:
            is_anomaly = True
            spike = random.choice([-35.0, 45.0])
            voltage += spike

        return {
            "timestamp": time.time(),
            "sequence_id": self.step_count,
            "voltage": round(voltage, 2),
            "temperature_c": round(self.temperature_c, 2),
            "is_simulated_anomaly": is_anomaly,
            "source": "digital_twin_v1",
        }