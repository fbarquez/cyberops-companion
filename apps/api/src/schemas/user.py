"""User schemas for authentication and authorization."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from src.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.ANALYST


class UserUpdate(BaseModel):
    """Schema for user update."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None  # Optional: specify which tenant to log into


class Token(BaseModel):
    """Schema for JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str  # user_id
    exp: datetime
    role: UserRole
    type: str  # "access" or "refresh"
    # Multi-tenancy fields
    tenant_id: Optional[str] = None
    org_role: Optional[str] = None
    is_super_admin: bool = False
    available_tenants: List[str] = []


class TenantSwitch(BaseModel):
    """Schema for switching active tenant."""
    tenant_id: str
