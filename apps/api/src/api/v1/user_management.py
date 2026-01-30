"""User Management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import DBSession, CurrentUser
from src.models.user import UserRole
from src.schemas.user_management import (
    UserProfileUpdate, UserAdminUpdate, UserListResponse, UserDetailResponse,
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberAdd, TeamMemberResponse,
    RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse, PermissionResponse,
    InvitationCreate, InvitationResponse, SessionResponse,
    ActivityLogResponse, APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    UserManagementStats
)
from src.services.user_management_service import UserManagementService

router = APIRouter(prefix="/users")


# ============== Users ==============

@router.get("", response_model=dict)
async def list_users(
    db: DBSession,
    current_user: CurrentUser,
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    team_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List all users."""
    if not current_user.has_permission(UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    users, total = await service.list_users(
        search=search,
        role=role,
        is_active=is_active,
        team_id=team_id,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [UserListResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    db: DBSession,
    current_user: CurrentUser
):
    """Get current user's profile."""
    service = UserManagementService(db)
    user_detail = await service.get_user_detail(current_user.id)
    return UserDetailResponse.model_validate(user_detail)


@router.put("/me", response_model=UserDetailResponse)
async def update_current_user_profile(
    data: UserProfileUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update current user's profile."""
    service = UserManagementService(db)
    user = await service.update_user_profile(current_user.id, data)
    user_detail = await service.get_user_detail(current_user.id)
    return UserDetailResponse.model_validate(user_detail)


@router.get("/stats", response_model=UserManagementStats)
async def get_user_stats(
    db: DBSession,
    current_user: CurrentUser
):
    """Get user management statistics."""
    if not current_user.has_permission(UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    return await service.get_stats()


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get a specific user."""
    if not current_user.has_permission(UserRole.MANAGER) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    user_detail = await service.get_user_detail(user_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="User not found")
    return UserDetailResponse.model_validate(user_detail)


@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: str,
    data: UserAdminUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update a user (admin only)."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    user = await service.update_user_admin(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_detail = await service.get_user_detail(user_id)
    return UserDetailResponse.model_validate(user_detail)


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Deactivate a user."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    service = UserManagementService(db)
    success = await service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Activate a user."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    success = await service.activate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User activated"}


# ============== Teams ==============

@router.get("/teams/list", response_model=dict)
async def list_teams(
    db: DBSession,
    current_user: CurrentUser,
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List all teams."""
    service = UserManagementService(db)
    teams, total = await service.list_teams(
        search=search,
        is_active=is_active,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [TeamResponse.model_validate(t) for t in teams],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.post("/teams", response_model=TeamResponse)
async def create_team(
    data: TeamCreate,
    db: DBSession,
    current_user: CurrentUser
):
    """Create a new team."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    team = await service.create_team(data, current_user.id)
    return TeamResponse.model_validate(team)


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get a specific team."""
    service = UserManagementService(db)
    team = await service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.model_validate(team)


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    data: TeamUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update a team."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    team = await service.update_team(team_id, data)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.model_validate(team)


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Delete a team."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    success = await service.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"message": "Team deleted"}


@router.get("/teams/{team_id}/members", response_model=list)
async def get_team_members(
    team_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get team members."""
    service = UserManagementService(db)
    members = await service.get_team_members(team_id)
    return [TeamMemberResponse.model_validate(m) for m in members]


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: str,
    data: TeamMemberAdd,
    db: DBSession,
    current_user: CurrentUser
):
    """Add a member to a team."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    member = await service.add_team_member(team_id, data)
    if not member:
        raise HTTPException(status_code=400, detail="User already in team")

    members = await service.get_team_members(team_id)
    member_data = next((m for m in members if m["user_id"] == data.user_id), None)
    return TeamMemberResponse.model_validate(member_data)


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Remove a member from a team."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    success = await service.remove_team_member(team_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member removed"}


# ============== Roles ==============

@router.get("/roles/list", response_model=dict)
async def list_roles(
    db: DBSession,
    current_user: CurrentUser,
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List all roles."""
    service = UserManagementService(db)
    roles, total = await service.list_roles(
        is_active=is_active,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [RoleResponse.model_validate(r) for r in roles],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    data: RoleCreate,
    db: DBSession,
    current_user: CurrentUser
):
    """Create a new role."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    role = await service.create_role(data)
    return RoleResponse.model_validate(role)


@router.get("/roles/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get a specific role with permissions."""
    service = UserManagementService(db)
    role = await service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role_data = {
        **role.__dict__,
        "permissions": [
            {"id": p.id, "code": p.code, "name": p.name}
            for p in role.permissions
        ]
    }
    return RoleDetailResponse.model_validate(role_data)


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    data: RoleUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update a role."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    role = await service.update_role(role_id, data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found or is system role")
    return RoleResponse.model_validate(role)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Delete a role."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    success = await service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found or is system role")
    return {"message": "Role deleted"}


# ============== Permissions ==============

@router.get("/permissions/list", response_model=list)
async def list_permissions(
    db: DBSession,
    current_user: CurrentUser,
    category: Optional[str] = Query(None)
):
    """List all permissions."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    permissions = await service.list_permissions(category=category)
    return [PermissionResponse.model_validate(p) for p in permissions]


@router.post("/permissions/seed")
async def seed_permissions(
    db: DBSession,
    current_user: CurrentUser
):
    """Seed default permissions."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    permissions = await service.seed_permissions()
    return {"message": f"Created {len(permissions)} permissions"}


# ============== Sessions ==============

@router.get("/sessions/me", response_model=list)
async def get_my_sessions(
    db: DBSession,
    current_user: CurrentUser
):
    """Get current user's sessions."""
    service = UserManagementService(db)
    sessions = await service.get_user_sessions(current_user.id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Revoke a session."""
    service = UserManagementService(db)
    success = await service.revoke_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session revoked"}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    db: DBSession,
    current_user: CurrentUser,
    except_current: Optional[str] = Query(None)
):
    """Revoke all sessions except current."""
    service = UserManagementService(db)
    count = await service.revoke_all_sessions(current_user.id, except_current)
    return {"message": f"Revoked {count} sessions"}


# ============== Invitations ==============

@router.get("/invitations/list", response_model=dict)
async def list_invitations(
    db: DBSession,
    current_user: CurrentUser,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List invitations."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    invitations, total = await service.list_invitations(
        status=status,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [InvitationResponse.model_validate(i) for i in invitations],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    data: InvitationCreate,
    db: DBSession,
    current_user: CurrentUser
):
    """Create a user invitation."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    invitation = await service.create_invitation(data, current_user.id)
    return InvitationResponse.model_validate(invitation)


@router.delete("/invitations/{invitation_id}")
async def revoke_invitation(
    invitation_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Revoke an invitation."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    success = await service.revoke_invitation(invitation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invitation not found or not pending")
    return {"message": "Invitation revoked"}


# ============== Activity Logs ==============

@router.get("/activity/list", response_model=dict)
async def list_activity_logs(
    db: DBSession,
    current_user: CurrentUser,
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500)
):
    """List activity logs."""
    if not current_user.has_permission(UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")

    service = UserManagementService(db)
    logs, total = await service.get_activity_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [ActivityLogResponse.model_validate(l) for l in logs],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


# ============== API Keys ==============

@router.get("/api-keys/me", response_model=list)
async def list_my_api_keys(
    db: DBSession,
    current_user: CurrentUser
):
    """List current user's API keys."""
    service = UserManagementService(db)
    keys = await service.list_api_keys(current_user.id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    data: APIKeyCreate,
    db: DBSession,
    current_user: CurrentUser
):
    """Create an API key."""
    service = UserManagementService(db)
    api_key, full_key = await service.create_api_key(current_user.id, data)

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Revoke an API key."""
    service = UserManagementService(db)
    success = await service.revoke_api_key(key_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}
