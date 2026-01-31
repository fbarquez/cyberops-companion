"""SSO Provider model for OAuth2/OIDC configuration."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class SSOProvider(Base):
    """SSO Provider configuration for OAuth2/OIDC."""
    __tablename__ = "sso_providers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))  # "Google Workspace"
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # "google"
    provider_type: Mapped[str] = mapped_column(String(20), default="oauth2")  # "oauth2" or "saml"

    # OAuth2 Configuration
    client_id: Mapped[str] = mapped_column(String(255))
    client_secret: Mapped[str] = mapped_column(String(500))
    authorization_url: Mapped[str] = mapped_column(String(500))
    token_url: Mapped[str] = mapped_column(String(500))
    userinfo_url: Mapped[str] = mapped_column(String(500))
    scopes: Mapped[str] = mapped_column(String(500), default="openid email profile")

    # Provider Settings
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_role: Mapped[str] = mapped_column(String(50), default="analyst")
    allowed_domains: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated domains
    auto_create_users: Mapped[bool] = mapped_column(Boolean, default=True)

    # Display
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "google", "microsoft"
    button_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "Sign in with Google"

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )


class SSOState(Base):
    """Temporary storage for OAuth2 state tokens (CSRF protection)."""
    __tablename__ = "sso_states"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    state: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    provider_slug: Mapped[str] = mapped_column(String(50))
    redirect_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)
