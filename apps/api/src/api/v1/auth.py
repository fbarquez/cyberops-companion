"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status, Request

from src.api.deps import DBSession, CurrentUser
from src.schemas.user import UserCreate, UserLogin, UserResponse, Token
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DBSession, request: Request):
    """Register a new user."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)

    try:
        user = await auth_service.register(data)

        # Log successful registration
        await audit_service.log_action(
            user_id=user.id,
            action="create",
            resource_type="user",
            resource_id=user.id,
            resource_name=user.email,
            description=f"New user registered: {user.email}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
        )

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: DBSession, request: Request):
    """Authenticate and get JWT tokens."""
    auth_service = AuthService(db)
    audit_service = AuditService(db)

    # Get user for audit logging (before login attempt)
    user = await auth_service.get_user_by_email(data.email)

    tokens = await auth_service.login(data.email, data.password, data.tenant_id)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500]

    if not tokens:
        # Log failed login attempt
        await audit_service.log_action(
            user_id=user.id if user else None,
            action="login_failed",
            resource_type="session",
            resource_name=data.email,
            description=f"Failed login attempt for: {data.email}",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid email or password",
            severity="warning",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Log successful login
    await audit_service.log_action(
        user_id=user.id,
        action="login",
        resource_type="session",
        resource_name=user.email,
        description=f"User logged in: {user.email}",
        ip_address=ip_address,
        user_agent=user_agent,
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
