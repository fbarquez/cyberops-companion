"""User model for authentication and authorization."""
import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class UserRole(str, enum.Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"  # Full access
    MANAGER = "manager"  # View all, manage team
    LEAD = "lead"  # Manage incidents, approve decisions
    ANALYST = "analyst"  # Create/work incidents


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.ANALYST
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Profile fields
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="UTC")
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="en")

    # SSO fields
    sso_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # google, azure, okta
    sso_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # Provider's unique user ID
    sso_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email from SSO provider
    sso_linked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When SSO was linked

    # Relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    custom_roles = relationship("Role", secondary="user_roles", back_populates="users")

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.LEAD: 2,
            UserRole.ANALYST: 1,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
