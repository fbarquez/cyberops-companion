"""Organization management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api.deps import CurrentUser, DBSession
from src.services.organization_service import OrganizationService
from src.services.auth_service import AuthService
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationListResponse, OrganizationWithRole,
    MemberInvite, MemberUpdate, MemberResponse, MemberListResponse,
    OwnershipTransfer
)
from src.schemas.user import Token, TenantSwitch


router = APIRouter(prefix="/organizations")


@router.post("", response_model=OrganizationResponse, status_code=HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create a new organization.

    The current user will be set as the owner of the organization.
    """
    service = OrganizationService(db)
    organization = await service.create(data, current_user.id)
    return organization


@router.get("/me", response_model=OrganizationListResponse)
async def get_my_organizations(
    db: DBSession,
    current_user: CurrentUser,
):
    """Get all organizations the current user is a member of."""
    service = OrganizationService(db)
    organizations = await service.get_user_organizations(current_user.id)
    return OrganizationListResponse(
        organizations=[OrganizationWithRole(**org) for org in organizations]
    )


@router.post("/switch", response_model=Token)
async def switch_organization(
    data: TenantSwitch,
    db: DBSession,
    current_user: CurrentUser,
):
    """Switch to a different organization.

    Returns new access and refresh tokens with the new tenant context.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.switch_tenant(current_user.id, data.tenant_id)

    if not tokens:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this organization"
        )

    return tokens


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get organization details.

    User must be a member of the organization to view it.
    """
    service = OrganizationService(db)

    # Check membership
    membership = await service.get_membership(org_id, current_user.id)
    if not membership and not current_user.is_super_admin:
        raise HTTPException(status_code=404, detail="Organization not found")

    organization = await service.get_by_id(org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return organization


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update organization settings.

    Requires admin or owner role in the organization.
    """
    service = OrganizationService(db)
    organization = await service.update(org_id, data, current_user.id)

    if not organization:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this organization"
        )

    return organization


@router.get("/{org_id}/members", response_model=MemberListResponse)
async def list_members(
    org_id: str,
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List organization members.

    User must be a member of the organization to view member list.
    """
    service = OrganizationService(db)

    # Check membership
    membership = await service.get_membership(org_id, current_user.id)
    if not membership and not current_user.is_super_admin:
        raise HTTPException(status_code=404, detail="Organization not found")

    members, total = await service.list_members(org_id, page, size)

    return MemberListResponse(
        items=[MemberResponse(**m) for m in members],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total else 0,
    )


@router.post("/{org_id}/members", response_model=MemberResponse, status_code=HTTP_201_CREATED)
async def invite_member(
    org_id: str,
    data: MemberInvite,
    db: DBSession,
    current_user: CurrentUser,
):
    """Invite/add a user to the organization.

    Requires admin or owner role in the organization.
    """
    service = OrganizationService(db)

    try:
        membership = await service.invite_member(org_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to invite members"
        )

    # Fetch user info for response
    from src.services.auth_service import AuthService
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(data.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return MemberResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        org_role=membership.org_role.value,
        is_default=membership.is_default,
        joined_at=membership.joined_at.isoformat(),
        invited_by=membership.invited_by,
    )


@router.patch("/{org_id}/members/{user_id}", response_model=MemberResponse)
async def update_member(
    org_id: str,
    user_id: str,
    data: MemberUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update a member's role in the organization.

    Requires admin or owner role in the organization.
    """
    service = OrganizationService(db)
    membership = await service.update_member(org_id, user_id, data, current_user.id)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this member"
        )

    # Fetch user info for response
    from src.services.auth_service import AuthService
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    return MemberResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        org_role=membership.org_role.value,
        is_default=membership.is_default,
        joined_at=membership.joined_at.isoformat(),
        invited_by=membership.invited_by,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: str,
    user_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Remove a member from the organization.

    Requires admin or owner role in the organization.
    Owners can only remove themselves if there's another owner.
    """
    service = OrganizationService(db)

    try:
        success = await service.remove_member(org_id, user_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to remove this member"
        )


@router.post("/{org_id}/transfer-ownership", status_code=HTTP_204_NO_CONTENT)
async def transfer_ownership(
    org_id: str,
    data: OwnershipTransfer,
    db: DBSession,
    current_user: CurrentUser,
):
    """Transfer organization ownership to another member.

    Only the current owner can transfer ownership.
    """
    service = OrganizationService(db)
    success = await service.transfer_ownership(
        org_id,
        data.new_owner_id,
        current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to transfer ownership"
        )


@router.post("/{org_id}/set-default", status_code=HTTP_204_NO_CONTENT)
async def set_default_organization(
    org_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Set an organization as the user's default.

    The default organization is used when logging in without specifying a tenant.
    """
    service = OrganizationService(db)
    success = await service.set_default_organization(current_user.id, org_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Organization not found or you're not a member"
        )
