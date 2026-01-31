"""SSO Service for OAuth2/OIDC authentication."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.config import settings
from src.models.user import User, UserRole
from src.models.sso import SSOProvider, SSOState
from src.schemas.sso import (
    SSOProviderPublic,
    SSOAuthorizeResponse,
    SSOUserInfo,
    SSOCallbackResponse,
    SSOUserResponse,
)
from src.schemas.user import Token
from src.services.auth_service import AuthService


class SSOService:
    """Service for SSO authentication operations."""

    # State token validity (10 minutes)
    STATE_EXPIRY_MINUTES = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)

    async def get_enabled_providers(self) -> List[SSOProviderPublic]:
        """Get list of enabled SSO providers for frontend."""
        result = await self.db.execute(
            select(SSOProvider).where(SSOProvider.enabled == True)
        )
        providers = result.scalars().all()
        return [
            SSOProviderPublic(
                slug=p.slug,
                name=p.name,
                icon=p.icon,
                button_text=p.button_text,
            )
            for p in providers
        ]

    async def get_provider_by_slug(self, slug: str) -> Optional[SSOProvider]:
        """Get SSO provider by slug."""
        result = await self.db.execute(
            select(SSOProvider).where(SSOProvider.slug == slug, SSOProvider.enabled == True)
        )
        return result.scalar_one_or_none()

    async def generate_authorize_url(
        self, provider_slug: str, redirect_uri: str
    ) -> SSOAuthorizeResponse:
        """Generate OAuth2 authorization URL with state token."""
        provider = await self.get_provider_by_slug(provider_slug)
        if not provider:
            raise ValueError(f"Provider '{provider_slug}' not found or disabled")

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in database
        sso_state = SSOState(
            state=state,
            provider_slug=provider_slug,
            redirect_uri=redirect_uri,
            expires_at=datetime.utcnow() + timedelta(minutes=self.STATE_EXPIRY_MINUTES),
        )
        self.db.add(sso_state)
        await self.db.flush()

        # Build authorization URL
        client = AsyncOAuth2Client(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            scope=provider.scopes,
        )

        authorization_url, _ = client.create_authorization_url(
            provider.authorization_url,
            state=state,
            redirect_uri=redirect_uri,
        )

        return SSOAuthorizeResponse(
            authorization_url=authorization_url,
            state=state,
        )

    async def validate_state(self, state: str) -> Optional[SSOState]:
        """Validate state token and return associated data."""
        result = await self.db.execute(
            select(SSOState).where(
                SSOState.state == state,
                SSOState.expires_at > datetime.utcnow(),
            )
        )
        sso_state = result.scalar_one_or_none()

        if sso_state:
            # Delete state after use (one-time use)
            await self.db.execute(
                delete(SSOState).where(SSOState.id == sso_state.id)
            )
            await self.db.flush()

        return sso_state

    async def exchange_code_for_token(
        self, provider: SSOProvider, code: str, redirect_uri: str
    ) -> dict:
        """Exchange authorization code for access token."""
        client = AsyncOAuth2Client(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
        )

        token = await client.fetch_token(
            provider.token_url,
            code=code,
            redirect_uri=redirect_uri,
        )

        return token

    async def get_user_info(self, provider: SSOProvider, access_token: str) -> SSOUserInfo:
        """Fetch user info from SSO provider."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

        # Normalize user info (different providers use different field names)
        return SSOUserInfo(
            sub=data.get("sub") or data.get("id") or data.get("oid"),
            email=data.get("email"),
            email_verified=data.get("email_verified", True),
            name=data.get("name"),
            given_name=data.get("given_name") or data.get("givenName"),
            family_name=data.get("family_name") or data.get("familyName"),
            picture=data.get("picture") or data.get("avatar_url"),
        )

    def validate_email_domain(self, email: str, allowed_domains: Optional[str]) -> bool:
        """Check if email domain is allowed."""
        if not allowed_domains:
            return True

        domains = [d.strip().lower() for d in allowed_domains.split(",")]
        email_domain = email.split("@")[1].lower()
        return email_domain in domains

    async def get_user_by_sso(self, provider_slug: str, sso_id: str) -> Optional[User]:
        """Get user by SSO provider and ID."""
        result = await self.db.execute(
            select(User).where(
                User.sso_provider == provider_slug,
                User.sso_id == sso_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_or_link_user(
        self,
        provider: SSOProvider,
        user_info: SSOUserInfo,
    ) -> tuple[User, bool]:
        """Create new user or link SSO to existing user. Returns (user, is_new)."""
        # First, check if user exists with this SSO ID
        user = await self.get_user_by_sso(provider.slug, user_info.sub)
        if user:
            # Update last login
            user.last_login = datetime.utcnow()
            await self.db.flush()
            return user, False

        # Check if user exists with this email
        user = await self.auth_service.get_user_by_email(user_info.email)
        if user:
            # Link SSO to existing user
            user.sso_provider = provider.slug
            user.sso_id = user_info.sub
            user.sso_email = user_info.email
            user.sso_linked_at = datetime.utcnow()
            user.last_login = datetime.utcnow()

            # Update avatar if not set
            if not user.avatar_url and user_info.picture:
                user.avatar_url = user_info.picture

            await self.db.flush()
            return user, False

        # Create new user (JIT provisioning)
        if not provider.auto_create_users:
            raise ValueError("User not found and auto-creation is disabled")

        # Build full name
        full_name = user_info.name
        if not full_name and (user_info.given_name or user_info.family_name):
            full_name = f"{user_info.given_name or ''} {user_info.family_name or ''}".strip()
        if not full_name:
            full_name = user_info.email.split("@")[0]

        # Create user with random password (SSO users don't use password login)
        user = User(
            id=str(uuid4()),
            email=user_info.email,
            hashed_password=AuthService.hash_password(secrets.token_urlsafe(32)),
            full_name=full_name,
            role=UserRole(provider.default_role),
            is_active=True,
            sso_provider=provider.slug,
            sso_id=user_info.sub,
            sso_email=user_info.email,
            sso_linked_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            avatar_url=user_info.picture,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user, True

    async def handle_callback(
        self,
        provider_slug: str,
        code: str,
        state: str,
    ) -> SSOCallbackResponse:
        """Handle OAuth2 callback and authenticate user."""
        # Validate state
        sso_state = await self.validate_state(state)
        if not sso_state:
            raise ValueError("Invalid or expired state token")

        if sso_state.provider_slug != provider_slug:
            raise ValueError("State token provider mismatch")

        # Get provider
        provider = await self.get_provider_by_slug(provider_slug)
        if not provider:
            raise ValueError(f"Provider '{provider_slug}' not found")

        # Exchange code for token
        redirect_uri = sso_state.redirect_uri or settings.FRONTEND_URL + "/auth/callback"
        token_data = await self.exchange_code_for_token(provider, code, redirect_uri)

        # Get user info
        user_info = await self.get_user_info(provider, token_data["access_token"])

        # Validate email domain
        if not self.validate_email_domain(user_info.email, provider.allowed_domains):
            raise ValueError(f"Email domain not allowed for this provider")

        # Create or link user
        user, is_new = await self.create_or_link_user(provider, user_info)

        # Generate our JWT tokens
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)

        return SSOCallbackResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=SSOUserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                sso_provider=user.sso_provider,
                is_new_user=is_new,
            ),
        )

    async def cleanup_expired_states(self) -> int:
        """Remove expired state tokens. Returns count of deleted records."""
        result = await self.db.execute(
            delete(SSOState).where(SSOState.expires_at < datetime.utcnow())
        )
        await self.db.flush()
        return result.rowcount
