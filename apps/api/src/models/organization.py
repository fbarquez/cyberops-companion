"""Organization models for multi-tenancy."""
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Boolean, Text, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class OrganizationStatus(str, enum.Enum):
    """Organization account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class OrganizationPlan(str, enum.Enum):
    """Organization subscription plan."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Organization(Base):
    """Organization model for multi-tenancy."""
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus), default=OrganizationStatus.TRIAL
    )
    plan: Mapped[OrganizationPlan] = mapped_column(
        Enum(OrganizationPlan), default=OrganizationPlan.FREE
    )
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=5)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    memberships: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class OrganizationMemberRole(str, enum.Enum):
    """Role within an organization."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationMember(Base):
    """Membership linking users to organizations."""
    __tablename__ = "organization_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    org_role: Mapped[OrganizationMemberRole] = mapped_column(
        Enum(OrganizationMemberRole), default=OrganizationMemberRole.MEMBER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invited_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_user'),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="memberships"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="organization_memberships"
    )
