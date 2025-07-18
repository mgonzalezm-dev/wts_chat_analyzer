"""
Application configuration management
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, PostgresDsn, RedisDsn, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "WhatsApp Conversation Reader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/v1"
    PROJECT_NAME: str = "WhatsApp Conversation Reader API"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",  # Vite dev server alternate port
        "http://localhost:8080",  # Production frontend
        "https://localhost:3000",  # HTTPS development
    ]
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_CONNECTION_TIMEOUT: int = 300  # seconds (5 minutes)
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "whatsapp_reader")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        password = values.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    UPLOAD_CHUNK_SIZE: int = 1024 * 1024  # 1MB
    ALLOWED_UPLOAD_EXTENSIONS: set[str] = {".txt", ".json", ".zip"}
    UPLOAD_PATH: str = os.getenv("UPLOAD_PATH", "./uploads")
    
    # Storage
    USE_S3: bool = os.getenv("USE_S3", "false").lower() == "true"
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET", None)
    S3_REGION: Optional[str] = os.getenv("S3_REGION", "us-east-1")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY", None)
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY", None)
    
    # NLP
    SPACY_MODEL: str = "en_core_web_sm"
    NLP_BATCH_SIZE: int = 1000
    NLP_N_PROCESS: int = 4
    
    # Analytics
    ANALYTICS_BATCH_SIZE: int = 100
    ANALYTICS_REFRESH_INTERVAL: int = 15  # minutes
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_FROM: Optional[str] = os.getenv("SMTP_FROM", "noreply@whatsapp-reader.com")
    
    # Background Jobs
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @validator("CELERY_BROKER_URL", pre=True)
    def get_celery_broker(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if v:
            return v
        return values.get("REDIS_URL")
    
    @validator("CELERY_RESULT_BACKEND", pre=True)
    def get_celery_backend(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if v:
            return v
        return values.get("REDIS_URL")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create settings instance
settings = get_settings()