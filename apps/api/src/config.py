"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "CyberOps Companion"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cyberops_companion"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET: str = "your-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # NVD API (National Vulnerability Database)
    NVD_API_KEY: str = ""  # Optional: increases rate limit from 5 to 50 requests/30s

    # Email / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "CyberOps Companion"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAIL_ENABLED: bool = False  # Set to True when SMTP is configured

    # Forensics
    HASH_ALGORITHM: str = "sha256"
    ENABLE_HASH_CHAIN: bool = True

    # Export
    EXPORT_DIR: str = "exports"
    COMPANY_NAME: str = "Organization"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
