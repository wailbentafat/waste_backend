from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # PostgreSQL Configuration
    postgres_url: str = "postgresql://postgres:password@localhost:5432/waste_analytics"
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 30

    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017/waste_bins"
    mongodb_db_name: str = "waste_bins"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # MQTT Configuration
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = "waste_system"
    mqtt_password: str = "your_mqtt_password"
    mqtt_keepalive: int = 60

    # Security
    secret_key: str = "your_super_secret_key_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # File Upload & YOLO
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads/detections"
    yolo_model_path: str = "./ml/models/trash_detection.pt"
    yolo_confidence_threshold: float = 0.6
    yolo_device: str = "cpu"

    # API Configuration
    api_v1_str: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 200

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
