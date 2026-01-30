"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status

from src.api.deps import DBSession, CurrentUser
from src.schemas.user import UserCreate, UserLogin, UserResponse, Token
from src.services.auth_service import AuthService


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DBSession):
    """Register a new user."""
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: DBSession):
    """Authenticate and get JWT tokens."""
    auth_service = AuthService(db)
    tokens = await auth_service.login(data.email, data.password)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str, db: DBSession):
    """Refresh access token."""
    auth_service = AuthService(db)
    tokens = await auth_service.refresh(refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return current_user
