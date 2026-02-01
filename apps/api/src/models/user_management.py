"""User Management and RBAC models."""
import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean, Integer, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship

from src.db.database import Base
from src.models.mixins import TenantMixin


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid4())


class TeamRole(str, enum.Enum):
    """Roles within a team."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(str, enum.Enum):
    """Status of user invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class SessionStatus(str, enum.Enum):
    """Status of user sessions."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


# Association table for role permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id"), primary_key=True)
)

# Association table for user roles (beyond team roles)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True)
)


class Team(TenantMixin, Base):
    """Team/Department model for grouping users."""
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # Team settings
    color = Column(String)  # For UI display
    icon = Column(String)   # Icon name

    # Hierarchy
    parent_id = Column(String, ForeignKey("teams.id"))

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    parent = relationship("Team", remote_side=[id], backref="children")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(TenantMixin, Base):
    """Team membership with role."""
    __tablename__ = "team_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role within team
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Role(Base):
    """Custom role definition."""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # Role type
    is_system = Column(Boolean, default=False)  # System roles can't be deleted
    is_default = Column(Boolean, default=False)  # Assigned to new users

    # Priority for conflict resolution (higher = more permissions)
    priority = Column(Integer, default=0)

    # Color for UI
    color = Column(String)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="custom_roles")


class Permission(Base):
    """Granular permission definition."""
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Permission identifier (e.g., "incidents:read", "incidents:write")
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Grouping
    category = Column(String)  # incidents, alerts, vulnerabilities, etc.

    # Resource and action
    resource = Column(String)  # incidents, alerts, users, etc.
    action = Column(String)    # read, write, delete, admin

    # System permission (cannot be removed)
    is_system = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class UserSession(Base):
    """User session tracking."""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session details
    token_hash = Column(String)  # Hash of refresh token

    # Device/Client info
    user_agent = Column(String)
    ip_address = Column(String)
    device_type = Column(String)  # desktop, mobile, tablet
    browser = Column(String)
    os = Column(String)

    # Location (if available)
    country = Column(String)
    city = Column(String)

    # Status
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="sessions")


class UserInvitation(Base):
    """User invitations."""
    __tablename__ = "user_invitations"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Invitation details
    email = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)

    # Assigned role/team
    role_id = Column(String, ForeignKey("roles.id"))
    team_id = Column(String, ForeignKey("teams.id"))

    # Status
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Message
    message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)

    # Inviter
    invited_by = Column(String, ForeignKey("users.id"))

    # Created user (after acceptance)
    user_id = Column(String)

    # Relationships
    role = relationship("Role")
    team = relationship("Team")
    inviter = relationship("User", foreign_keys=[invited_by])


class ActivityLog(Base):
    """User activity audit log."""
    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    # Action details
    action = Column(String(50), nullable=False, index=True)  # login, logout, create, update, delete, etc.
    action_category = Column(String(50))  # auth, crud, system

    # Resource
    resource_type = Column(String(50), index=True)  # incident, alert, user, etc.
    resource_id = Column(String)
    resource_name = Column(String)  # For display without join

    # Details
    description = Column(Text)
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(Text)  # "Changed status from 'open' to 'closed'"

    # Request info
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    request_id = Column(String)  # For correlation

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    severity = Column(String(20), default="info")  # info, warning, critical

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="activity_logs")


class APIKey(Base):
    """API keys for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Key details
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False)  # First 8 chars for identification
    key_hash = Column(String, nullable=False)    # Hashed full key

    # Permissions
    scopes = Column(JSON)  # List of allowed scopes
    """
    ["incidents:read", "alerts:read", "alerts:write"]
    """

    # Rate limiting
    rate_limit = Column(Integer)  # Requests per hour

    # Status
    is_active = Column(Boolean, default=True)

    # Usage tracking
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="api_keys")
