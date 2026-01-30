"""User Management schemas for API validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# ============== Enums ==============

class TeamRole(str, Enum):
    """Roles within a team."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(str, Enum):
    """Status of user invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class SessionStatus(str, Enum):
    """Status of user sessions."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============== User Schemas ==============

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Schema for admin updating a user."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class UserListResponse(BaseModel):
    """Schema for user in list."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    teams: Optional[List[str]] = None

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """Schema for user detail."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    teams: Optional[List[Dict[str, Any]]] = None
    custom_roles: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ============== Team Schemas ==============

class TeamCreate(BaseModel):
    """Schema for creating a team."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class TeamResponse(BaseModel):
    """Schema for team response."""
    id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool
    member_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team."""
    user_id: str
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    role: Optional[TeamRole] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    role: TeamRole
    is_active: bool
    joined_at: datetime

    class Config:
        from_attributes = True


# ============== Role Schemas ==============

class RoleCreate(BaseModel):
    """Schema for creating a role."""
    name: str
    description: Optional[str] = None
    priority: int = 0
    color: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[str]] = None


class RoleResponse(BaseModel):
    """Schema for role response."""
    id: str
    name: str
    description: Optional[str] = None
    is_system: bool
    is_default: bool
    priority: int
    color: Optional[str] = None
    is_active: bool
    permission_count: Optional[int] = 0
    user_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """Schema for role detail with permissions."""
    id: str
    name: str
    description: Optional[str] = None
    is_system: bool
    is_default: bool
    priority: int
    color: Optional[str] = None
    is_active: bool
    permissions: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Permission Schemas ==============

class PermissionCreate(BaseModel):
    """Schema for creating a permission."""
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    id: str
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Session Schemas ==============

class SessionResponse(BaseModel):
    """Schema for session response."""
    id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    status: SessionStatus
    created_at: datetime
    last_active_at: datetime
    expires_at: Optional[datetime] = None
    is_current: bool = False

    class Config:
        from_attributes = True


# ============== Invitation Schemas ==============

class InvitationCreate(BaseModel):
    """Schema for creating an invitation."""
    email: EmailStr
    role_id: Optional[str] = None
    team_id: Optional[str] = None
    message: Optional[str] = None
    expires_in_days: int = 7


class InvitationResponse(BaseModel):
    """Schema for invitation response."""
    id: str
    email: str
    status: InvitationStatus
    role_name: Optional[str] = None
    team_name: Optional[str] = None
    message: Optional[str] = None
    inviter_name: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== Activity Log Schemas ==============

class ActivityLogResponse(BaseModel):
    """Schema for activity log response."""
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== API Key Schemas ==============

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: str
    name: str
    key_prefix: str
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes full key)."""
    id: str
    name: str
    key: str  # Full key - only shown once!
    key_prefix: str
    scopes: Optional[List[str]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


# ============== Stats Schemas ==============

class UserManagementStats(BaseModel):
    """Schema for user management statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    total_teams: int
    total_roles: int
    pending_invitations: int
    active_sessions: int
    users_by_role: Dict[str, int]
    recent_logins: int  # Last 24 hours
    new_users_this_month: int
