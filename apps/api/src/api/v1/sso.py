"""SSO/OAuth2 authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import DBSession, CurrentUser
from src.config import settings
from src.services.sso_service import SSOService
from src.schemas.sso import (
    SSOProvidersResponse,
    SSOAuthorizeResponse,
    SSOCallbackRequest,
    SSOCallbackResponse,
    SSOErrorResponse,
)

router = APIRouter(prefix="/auth/sso", tags=["SSO Authentication"])


@router.get(
    "/providers",
    response_model=SSOProvidersResponse,
    summary="Get available SSO providers",
    description="Returns list of enabled SSO providers for the login page.",
)
async def get_providers(db: DBSession) -> SSOProvidersResponse:
    """Get list of available SSO providers."""
    service = SSOService(db)
    providers = await service.get_enabled_providers()
    return SSOProvidersResponse(providers=providers)


@router.get(
    "/{provider}/authorize",
    response_model=SSOAuthorizeResponse,
    summary="Get authorization URL",
    description="Generate OAuth2 authorization URL for the specified provider.",
    responses={
        404: {"model": SSOErrorResponse, "description": "Provider not found"},
    },
)
async def get_authorize_url(
    provider: str,
    db: DBSession,
    redirect_uri: str = Query(
        default=None,
        description="Callback URL after authentication. Defaults to frontend callback URL.",
    ),
) -> SSOAuthorizeResponse:
    """Generate OAuth2 authorization URL."""
    service = SSOService(db)

    # Use default redirect URI if not provided
    callback_url = redirect_uri or f"{settings.FRONTEND_URL}/auth/callback"

    try:
        return await service.generate_authorize_url(provider, callback_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{provider}/callback",
    response_model=SSOCallbackResponse,
    summary="Handle OAuth2 callback",
    description="Exchange authorization code for tokens and authenticate user.",
    responses={
        400: {"model": SSOErrorResponse, "description": "Invalid request"},
        403: {"model": SSOErrorResponse, "description": "Domain not allowed"},
        404: {"model": SSOErrorResponse, "description": "Provider not found"},
    },
)
async def handle_callback(
    provider: str,
    request: SSOCallbackRequest,
    db: DBSession,
) -> SSOCallbackResponse:
    """Handle OAuth2 callback and return JWT tokens."""
    service = SSOService(db)

    try:
        result = await service.handle_callback(
            provider_slug=provider,
            code=request.code,
            state=request.state,
        )
        await db.commit()
        return result
    except ValueError as e:
        error_msg = str(e)
        if "not allowed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        elif "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSO authentication failed: {str(e)}",
        )


@router.post(
    "/{provider}/unlink",
    summary="Unlink SSO from account",
    description="Remove SSO connection from current user's account.",
    responses={
        400: {"model": SSOErrorResponse, "description": "Cannot unlink"},
    },
)
async def unlink_sso(
    provider: str,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    """Unlink SSO provider from current user's account."""
    if current_user.sso_provider != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account is not linked to {provider}",
        )

    # Clear SSO fields
    current_user.sso_provider = None
    current_user.sso_id = None
    current_user.sso_email = None
    current_user.sso_linked_at = None

    await db.commit()

    return {"message": f"Successfully unlinked {provider} from your account"}
