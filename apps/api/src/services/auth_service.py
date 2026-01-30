"""Authentication service with JWT."""
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config import settings
from src.models.user import User, UserRole
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
    def create_access_token(user: User) -> str:
        """Create access token."""
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        payload = {
            "sub": user.id,
            "exp": expire,
            "role": user.role.value,
            "type": "access",
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user: User) -> str:
        """Create refresh token."""
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
        payload = {
            "sub": user.id,
            "exp": expire,
            "role": user.role.value,
            "type": "refresh",
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

    async def login(self, email: str, password: str) -> Optional[Token]:
        """Authenticate user and return tokens."""
        user = await self.get_user_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.flush()

        return Token(
            access_token=self.create_access_token(user),
            refresh_token=self.create_refresh_token(user),
        )

    async def refresh(self, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token."""
        payload = self.decode_token(refresh_token)
        if not payload or payload.type != "refresh":
            return None

        user = await self.get_user_by_id(payload.sub)
        if not user or not user.is_active:
            return None

        return Token(
            access_token=self.create_access_token(user),
            refresh_token=self.create_refresh_token(user),
        )
