"""Authentication service with JWT."""
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, List

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.user import User, UserRole
from src.models.organization import OrganizationMember
from src.schemas.user import UserCreate, Token, TokenPayload


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _prepare_password(password: str) -> str:
    """Prepare password for bcrypt by pre-hashing with SHA-256.

    bcrypt has a 72-byte limit. To handle passwords of any length uniformly,
    we always pre-hash with SHA-256 and encode as base64.
    This is a common pattern (used by Dropbox, etc.).
    """
    password_bytes = password.encode('utf-8')
    # Always pre-hash to handle any password length
    sha256_hash = hashlib.sha256(password_bytes).digest()
    return base64.b64encode(sha256_hash).decode('ascii')


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        prepared = _prepare_password(password)
        return pwd_context.hash(prepared)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        prepared = _prepare_password(plain_password)
        return pwd_context.verify(prepared, hashed_password)

    @staticmethod
    def create_access_token(
        user: User,
        tenant_id: Optional[str] = None,
        org_role: Optional[str] = None,
        available_tenants: Optional[List[str]] = None
    ) -> str:
        """Create access token with tenant information."""
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        payload = {
            "sub": user.id,
            "exp": expire,
            "role": user.role.value,
            "type": "access",
            "tenant_id": tenant_id,
            "org_role": org_role,
            "is_super_admin": user.is_super_admin,
            "available_tenants": available_tenants or [],
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(
        user: User,
        tenant_id: Optional[str] = None,
        available_tenants: Optional[List[str]] = None
    ) -> str:
        """Create refresh token with tenant information."""
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
        payload = {
            "sub": user.id,
            "exp": expire,
            "role": user.role.value,
            "type": "refresh",
            "tenant_id": tenant_id,
            "is_super_admin": user.is_super_admin,
            "available_tenants": available_tenants or [],
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"]),
                role=UserRole(payload["role"]),
                type=payload["type"],
                tenant_id=payload.get("tenant_id"),
                org_role=payload.get("org_role"),
                is_super_admin=payload.get("is_super_admin", False),
                available_tenants=payload.get("available_tenants", []),
            )
        except JWTError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user."""
        # Check if email exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_memberships(self, user_id: str) -> List[OrganizationMember]:
        """Get all organization memberships for a user."""
        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .where(OrganizationMember.is_active == True)
        )
        return list(result.scalars().all())

    async def login(
        self,
        email: str,
        password: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Token]:
        """Authenticate user and return tokens with tenant context.

        Args:
            email: User email
            password: User password
            tenant_id: Optional specific tenant to log into

        Returns:
            Token with access and refresh tokens, or None if auth fails
        """
        user = await self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Get user's organization memberships
        memberships = await self.get_user_memberships(user.id)
        available_tenants = [m.organization_id for m in memberships]

        # Determine which tenant to use
        active_tenant_id = None
        org_role = None

        if tenant_id:
            # User requested specific tenant
            membership = next(
                (m for m in memberships if m.organization_id == tenant_id),
                None
            )
            if not membership and not user.is_super_admin:
                return None  # User doesn't have access to requested tenant
            if membership:
                active_tenant_id = membership.organization_id
                org_role = membership.org_role.value
            elif user.is_super_admin:
                # Super admin can access any tenant
                active_tenant_id = tenant_id
                org_role = "admin"
        elif memberships:
            # Use default tenant or first available
            default_membership = next(
                (m for m in memberships if m.is_default),
                memberships[0]
            )
            active_tenant_id = default_membership.organization_id
            org_role = default_membership.org_role.value

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.flush()

        return Token(
            access_token=self.create_access_token(
                user,
                tenant_id=active_tenant_id,
                org_role=org_role,
                available_tenants=available_tenants
            ),
            refresh_token=self.create_refresh_token(
                user,
                tenant_id=active_tenant_id,
                available_tenants=available_tenants
            ),
        )

    async def refresh(self, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token."""
        payload = self.decode_token(refresh_token)
        if not payload or payload.type != "refresh":
            return None

        user = await self.get_user_by_id(payload.sub)
        if not user or not user.is_active:
            return None

        # Get current memberships (may have changed)
        memberships = await self.get_user_memberships(user.id)
        available_tenants = [m.organization_id for m in memberships]

        # Verify tenant access still valid
        tenant_id = payload.tenant_id
        org_role = None
        if tenant_id:
            membership = next(
                (m for m in memberships if m.organization_id == tenant_id),
                None
            )
            if membership:
                org_role = membership.org_role.value
            elif not user.is_super_admin:
                # User lost access to tenant, use default
                if memberships:
                    default_membership = next(
                        (m for m in memberships if m.is_default),
                        memberships[0]
                    )
                    tenant_id = default_membership.organization_id
                    org_role = default_membership.org_role.value
                else:
                    tenant_id = None
            else:
                org_role = "admin"

        return Token(
            access_token=self.create_access_token(
                user,
                tenant_id=tenant_id,
                org_role=org_role,
                available_tenants=available_tenants
            ),
            refresh_token=self.create_refresh_token(
                user,
                tenant_id=tenant_id,
                available_tenants=available_tenants
            ),
        )

    async def switch_tenant(self, user_id: str, tenant_id: str) -> Optional[Token]:
        """Switch active tenant for a user.

        Args:
            user_id: Current user ID
            tenant_id: Target tenant ID to switch to

        Returns:
            New Token with updated tenant context, or None if not allowed
        """
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None

        memberships = await self.get_user_memberships(user_id)
        available_tenants = [m.organization_id for m in memberships]

        # Check if user has access to target tenant
        membership = next(
            (m for m in memberships if m.organization_id == tenant_id),
            None
        )

        if not membership and not user.is_super_admin:
            return None

        org_role = membership.org_role.value if membership else "admin"

        return Token(
            access_token=self.create_access_token(
                user,
                tenant_id=tenant_id,
                org_role=org_role,
                available_tenants=available_tenants
            ),
            refresh_token=self.create_refresh_token(
                user,
                tenant_id=tenant_id,
                available_tenants=available_tenants
            ),
        )
