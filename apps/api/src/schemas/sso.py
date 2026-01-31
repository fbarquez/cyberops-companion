"""SSO Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Provider Schemas
class SSOProviderPublic(BaseModel):
    """Public SSO provider info for frontend."""
    slug: str
    name: str
    icon: Optional[str] = None
    button_text: Optional[str] = None

    class Config:
        from_attributes = True


class SSOProvidersResponse(BaseModel):
    """List of available SSO providers."""
    providers: List[SSOProviderPublic]


class SSOProviderCreate(BaseModel):
    """Create SSO provider (admin only)."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    provider_type: str = Field(default="oauth2", pattern=r"^(oauth2|saml)$")
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    authorization_url: str
    token_url: str
    userinfo_url: str
    scopes: str = "openid email profile"
    enabled: bool = True
    default_role: str = "analyst"
    allowed_domains: Optional[str] = None
    auto_create_users: bool = True
    icon: Optional[str] = None
    button_text: Optional[str] = None


class SSOProviderUpdate(BaseModel):
    """Update SSO provider (admin only)."""
    name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    scopes: Optional[str] = None
    enabled: Optional[bool] = None
    default_role: Optional[str] = None
    allowed_domains: Optional[str] = None
    auto_create_users: Optional[bool] = None
    icon: Optional[str] = None
    button_text: Optional[str] = None


class SSOProviderFull(BaseModel):
    """Full SSO provider info (admin only)."""
    id: str
    name: str
    slug: str
    provider_type: str
    client_id: str
    authorization_url: str
    token_url: str
    userinfo_url: str
    scopes: str
    enabled: bool
    default_role: str
    allowed_domains: Optional[str]
    auto_create_users: bool
    icon: Optional[str]
    button_text: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Authorization Schemas
class SSOAuthorizeResponse(BaseModel):
    """Response for SSO authorization request."""
    authorization_url: str
    state: str


class SSOCallbackRequest(BaseModel):
    """Request for SSO callback."""
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)


class SSOCallbackResponse(BaseModel):
    """Response for successful SSO authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "SSOUserResponse"


class SSOUserResponse(BaseModel):
    """User info in SSO response."""
    id: str
    email: str
    full_name: str
    role: str
    sso_provider: Optional[str]
    is_new_user: bool = False

    class Config:
        from_attributes = True


# Error Schemas
class SSOErrorResponse(BaseModel):
    """SSO error response."""
    error: str
    error_description: Optional[str] = None


# User Info from Provider
class SSOUserInfo(BaseModel):
    """User info retrieved from SSO provider."""
    sub: str  # Provider's unique user ID
    email: str
    email_verified: Optional[bool] = True
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


# Update forward reference
SSOCallbackResponse.model_rebuild()
