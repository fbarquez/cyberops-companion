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

    # Frontend URL (for email links, etc.)
    FRONTEND_URL: str = "http://localhost:3000"

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

    # File Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    STORAGE_LOCAL_PATH: str = "uploads"  # Local storage directory
    STORAGE_MAX_FILE_SIZE_MB: int = 50  # Maximum file size in MB
    STORAGE_ALLOWED_EXTENSIONS: List[str] = [
        # Documents
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "json", "xml",
        # Images
        "jpg", "jpeg", "png", "gif", "bmp", "svg", "webp",
        # Archives
        "zip", "tar", "gz", "7z", "rar",
        # Security/Forensics
        "pcap", "pcapng", "log", "evtx", "dmp", "mem",
    ]

    # S3 Storage (when STORAGE_BACKEND = "s3")
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: str = ""  # For S3-compatible services (MinIO, etc.)

    # SSO / OAuth2 Configuration
    # Google OAuth2
    SSO_GOOGLE_ENABLED: bool = False
    SSO_GOOGLE_CLIENT_ID: str = ""
    SSO_GOOGLE_CLIENT_SECRET: str = ""

    # Microsoft Entra ID (Azure AD)
    SSO_AZURE_ENABLED: bool = False
    SSO_AZURE_CLIENT_ID: str = ""
    SSO_AZURE_CLIENT_SECRET: str = ""
    SSO_AZURE_TENANT_ID: str = "common"  # Use "common" for multi-tenant

    # Okta
    SSO_OKTA_ENABLED: bool = False
    SSO_OKTA_CLIENT_ID: str = ""
    SSO_OKTA_CLIENT_SECRET: str = ""
    SSO_OKTA_DOMAIN: str = ""  # e.g., "dev-123456.okta.com"

    # General SSO Settings
    SSO_AUTO_CREATE_USERS: bool = True
    SSO_DEFAULT_ROLE: str = "analyst"
    SSO_ALLOWED_DOMAINS: str = ""  # Comma-separated list of allowed email domains
    SSO_CALLBACK_URL: str = ""  # Override callback URL (defaults to FRONTEND_URL/auth/callback)

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_DB: int = 1  # Separate DB from Celery (DB 0)
    RATE_LIMIT_BYPASS_SUPER_ADMIN: bool = True

    # Per-plan limits (can be overridden via environment)
    RATE_LIMIT_FREE_HOUR: int = 1000
    RATE_LIMIT_FREE_MINUTE: int = 60
    RATE_LIMIT_STARTER_HOUR: int = 5000
    RATE_LIMIT_STARTER_MINUTE: int = 200
    RATE_LIMIT_PROFESSIONAL_HOUR: int = 20000
    RATE_LIMIT_PROFESSIONAL_MINUTE: int = 500
    RATE_LIMIT_ENTERPRISE_HOUR: int = 100000
    RATE_LIMIT_ENTERPRISE_MINUTE: int = 2000

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
