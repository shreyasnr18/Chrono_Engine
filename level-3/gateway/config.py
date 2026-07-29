import os
from pydantic_settings import BaseSettings

class ProductionSettings(BaseSettings):
    # App Config
    APP_NAME: str = "AetherEdge Gateway"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    PORT: int = 8000
    
    # Hardware Telemetry Config
    SERIAL_PORT: str = "COM4"
    BAUD_RATE: int = 115200
    MOCK_HARDWARE_FALLBACK: bool = True  # Auto-fallback if physical board unplugged
    
    # Integration Config
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/aether-incident-stream"
    AI_ALERT_COOLDOWN_SEC: int = 30  # Prevents alert spamming during continuous failures

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = ProductionSettings()