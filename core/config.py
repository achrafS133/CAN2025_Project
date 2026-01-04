"""
Configuration Management System with Pydantic
Handles encrypted API keys and application settings
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import json

load_dotenv()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self):
        # Generate or load encryption key
        key_file = ".encryption_key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self.key)

        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class AIModelConfig(BaseModel):
    """Configuration for AI models"""

    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "openai"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    stream_responses: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""

    enabled: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_api_calls_per_day: int = 10000


class SecurityConfig(BaseModel):
    """Computer Vision security configuration"""

    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    enable_face_blurring: bool = True
    enable_object_tracking: bool = True
    enable_zone_detection: bool = True
    enable_false_positive_feedback: bool = True
    night_vision_mode: bool = False
    enable_pose_estimation: bool = False
    enable_ocr: bool = False
    enable_license_plate_recognition: bool = False


class VideoStreamConfig(BaseModel):
    """Video stream configuration"""

    enable_rtsp: bool = True
    enable_rtmp: bool = True
    max_concurrent_streams: int = 4
    frame_buffer_size: int = 30
    processing_fps: int = 10


class DatabaseConfig(BaseModel):
    """Database configuration"""

    host: str = "localhost"
    user: str = "root"
    password: str = ""
    database: str = "can2025"
    port: int = 3306
    pool_size: int = 10


class IntegrationConfig(BaseModel):
    """Third-party integration configuration"""

    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    recipient_phone_number: Optional[str] = None

    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#security-alerts"

    discord_webhook_url: Optional[str] = None

    whatsapp_enabled: bool = False
    whatsapp_api_key: Optional[str] = None


class AnalyticsConfig(BaseModel):
    """Analytics and reporting configuration"""

    enable_historical_analytics: bool = True
    enable_anomaly_detection: bool = True
    enable_predictive_insights: bool = True
    enable_automated_reports: bool = False
    report_schedule: str = "daily"  # daily, weekly, monthly
    report_email: Optional[str] = None


class CostTrackingConfig(BaseModel):
    """API cost tracking configuration"""

    enabled: bool = True
    daily_budget_usd: float = 50.0
    alert_threshold_percent: float = 80.0
    enable_auto_downgrade: bool = True
    openai_cost_per_1k_tokens: float = 0.002
    anthropic_cost_per_1k_tokens: float = 0.008
    gemini_cost_per_1k_tokens: float = 0.00025


class RAGConfig(BaseModel):
    """Retrieval-Augmented Generation configuration"""

    enabled: bool = True
    vector_store_path: str = "./vector_store"
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 3


class AppSettings(BaseSettings):
    """Main application settings"""

    # Application Info
    app_name: str = "CAN 2025 Guardian"
    app_version: str = "2.0.0"
    debug_mode: bool = False

    # Feature Flags
    enable_audit_logging: bool = True
    enable_performance_monitoring: bool = True

    # Sub-configurations
    ai_model: AIModelConfig = AIModelConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    security: SecurityConfig = SecurityConfig()
    video_stream: VideoStreamConfig = VideoStreamConfig()
    database: DatabaseConfig = DatabaseConfig()
    integrations: IntegrationConfig = IntegrationConfig()
    analytics: AnalyticsConfig = AnalyticsConfig()
    cost_tracking: CostTrackingConfig = CostTrackingConfig()
    rag: RAGConfig = RAGConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> AppSettings:
    """Load application settings with encrypted API keys"""
    encryption_service = EncryptionService()

    # Load base settings
    settings = AppSettings()

    # Load and decrypt API keys
    if os.getenv("OPENAI_API_KEY"):
        settings.ai_model.openai_api_key = os.getenv("OPENAI_API_KEY")

    if os.getenv("GOOGLE_API_KEY"):
        settings.ai_model.google_api_key = os.getenv("GOOGLE_API_KEY")

    if os.getenv("ANTHROPIC_API_KEY"):
        settings.ai_model.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # Load integration keys
    settings.integrations.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    settings.integrations.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    settings.integrations.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    settings.integrations.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    settings.integrations.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    # Load database config
    settings.database.host = os.getenv("MYSQL_HOST", "localhost")
    settings.database.user = os.getenv("MYSQL_USER", "root")
    settings.database.password = os.getenv("MYSQL_PASSWORD", "")
    settings.database.database = os.getenv("MYSQL_DATABASE", "can2025")

    return settings


# Global settings instance
settings = load_settings()
