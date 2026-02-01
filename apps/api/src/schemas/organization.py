"""Pydantic schemas for organization management."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.organization import (
    OrganizationStatus, OrganizationPlan, OrganizationMemberRole
)


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: OrganizationStatus
    plan: OrganizationPlan
    logo_url: Optional[str] = None
    max_users: int
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationWithRole(BaseModel):
    """Schema for organization with user's role in it."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: str
    plan: str
    logo_url: Optional[str] = None
    org_role: str
    is_default: bool
    joined_at: str


class OrganizationListResponse(BaseModel):
    """Schema for list of user's organizations."""
    organizations: List[OrganizationWithRole]


class MemberInvite(BaseModel):
    """Schema for inviting a member to an organization."""
    user_id: str
    org_role: OrganizationMemberRole = OrganizationMemberRole.MEMBER


class MemberUpdate(BaseModel):
    """Schema for updating a member's role."""
    org_role: Optional[OrganizationMemberRole] = None


class MemberResponse(BaseModel):
    """Schema for organization member response."""
    user_id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    org_role: str
    is_default: bool
    joined_at: str
    invited_by: Optional[str] = None


class MemberListResponse(BaseModel):
    """Schema for paginated member list."""
    items: List[MemberResponse]
    total: int
    page: int
    size: int
    pages: int


class OwnershipTransfer(BaseModel):
    """Schema for transferring organization ownership."""
    new_owner_id: str
