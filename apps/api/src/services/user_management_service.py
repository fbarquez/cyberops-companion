"""User Management service."""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User, UserRole
from src.models.user_management import (
    Team, TeamMember, Role, Permission, UserSession,
    UserInvitation, ActivityLog, APIKey,
    TeamRole, InvitationStatus, SessionStatus,
    role_permissions, user_roles
)
from src.schemas.user_management import (
    UserProfileUpdate, UserAdminUpdate, UserListResponse, UserDetailResponse,
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberAdd, TeamMemberResponse,
    RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionResponse,
    InvitationCreate, InvitationResponse, SessionResponse,
    ActivityLogResponse, APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    UserManagementStats
)


class UserManagementService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Users ==============

    async def list_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        team_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[User], int]:
        """List users with filters."""
        query = select(User)

        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )

        if role:
            query = query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        if team_id:
            query = query.join(TeamMember).where(TeamMember.team_id == team_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Paginate
        query = query.order_by(User.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total or 0

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user with full details including teams and roles."""
        user = await self.get_user(user_id)
        if not user:
            return None

        # Get team memberships
        teams_query = select(TeamMember, Team).join(Team).where(
            TeamMember.user_id == user_id
        )
        teams_result = await self.db.execute(teams_query)
        teams = [
            {
                "id": team.id,
                "name": team.name,
                "role": tm.role.value
            }
            for tm, team in teams_result.fetchall()
        ]

        # Get custom roles
        roles_query = select(Role).join(user_roles).where(
            user_roles.c.user_id == user_id
        )
        roles_result = await self.db.execute(roles_query)
        custom_roles = [r.name for r in roles_result.scalars().all()]

        return {
            **user.__dict__,
            "teams": teams,
            "custom_roles": custom_roles
        }

    async def update_user_profile(
        self,
        user_id: str,
        data: UserProfileUpdate
    ) -> Optional[User]:
        """Update user's own profile."""
        user = await self.get_user(user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_admin(
        self,
        user_id: str,
        data: UserAdminUpdate
    ) -> Optional[User]:
        """Admin update of user."""
        user = await self.get_user(user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        user = await self.get_user(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.commit()
        return True

    async def activate_user(self, user_id: str) -> bool:
        """Activate a user."""
        user = await self.get_user(user_id)
        if not user:
            return False

        user.is_active = True
        await self.db.commit()
        return True

    # ============== Teams ==============

    async def list_teams(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Team], int]:
        """List teams."""
        query = select(Team)

        if search:
            query = query.where(Team.name.ilike(f"%{search}%"))

        if is_active is not None:
            query = query.where(Team.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(Team.name)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        teams = list(result.scalars().all())

        # Get member counts
        for team in teams:
            count_result = await self.db.scalar(
                select(func.count()).where(TeamMember.team_id == team.id)
            )
            team.member_count = count_result or 0

        return teams, total or 0

    async def create_team(self, data: TeamCreate, created_by: str) -> Team:
        """Create a new team."""
        team = Team(
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            parent_id=data.parent_id,
            created_by=created_by
        )
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID."""
        result = await self.db.execute(
            select(Team).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    async def update_team(self, team_id: str, data: TeamUpdate) -> Optional[Team]:
        """Update a team."""
        team = await self.get_team(team_id)
        if not team:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)

        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def delete_team(self, team_id: str) -> bool:
        """Delete a team."""
        team = await self.get_team(team_id)
        if not team:
            return False

        await self.db.delete(team)
        await self.db.commit()
        return True

    async def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team members."""
        query = select(TeamMember, User).join(User).where(
            TeamMember.team_id == team_id
        )
        result = await self.db.execute(query)

        members = []
        for tm, user in result.fetchall():
            members.append({
                "id": tm.id,
                "user_id": user.id,
                "user_email": user.email,
                "user_name": user.full_name,
                "user_avatar": user.avatar_url,
                "role": tm.role,
                "is_active": tm.is_active,
                "joined_at": tm.joined_at
            })
        return members

    async def add_team_member(
        self,
        team_id: str,
        data: TeamMemberAdd
    ) -> Optional[TeamMember]:
        """Add a member to a team."""
        # Check if already member
        existing = await self.db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == data.user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return None

        member = TeamMember(
            team_id=team_id,
            user_id=data.user_id,
            role=data.role
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Remove a member from a team."""
        result = await self.db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id
                )
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False

        await self.db.delete(member)
        await self.db.commit()
        return True

    # ============== Roles ==============

    async def list_roles(
        self,
        is_active: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Role], int]:
        """List roles."""
        query = select(Role)

        if is_active is not None:
            query = query.where(Role.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(Role.priority.desc(), Role.name)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        roles = list(result.scalars().all())

        return roles, total or 0

    async def create_role(self, data: RoleCreate) -> Role:
        """Create a new role."""
        role = Role(
            name=data.name,
            description=data.description,
            priority=data.priority,
            color=data.color
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)

        # Add permissions
        if data.permission_ids:
            for perm_id in data.permission_ids:
                await self.db.execute(
                    role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=perm_id
                    )
                )
            await self.db.commit()

        return role

    async def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        result = await self.db.execute(
            select(Role).options(
                selectinload(Role.permissions)
            ).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def update_role(self, role_id: str, data: RoleUpdate) -> Optional[Role]:
        """Update a role."""
        role = await self.get_role(role_id)
        if not role or role.is_system:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={"permission_ids"})
        for field, value in update_data.items():
            setattr(role, field, value)

        # Update permissions if provided
        if data.permission_ids is not None:
            # Remove existing
            await self.db.execute(
                role_permissions.delete().where(
                    role_permissions.c.role_id == role_id
                )
            )
            # Add new
            for perm_id in data.permission_ids:
                await self.db.execute(
                    role_permissions.insert().values(
                        role_id=role_id,
                        permission_id=perm_id
                    )
                )

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete_role(self, role_id: str) -> bool:
        """Delete a role."""
        role = await self.get_role(role_id)
        if not role or role.is_system:
            return False

        await self.db.delete(role)
        await self.db.commit()
        return True

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign a role to a user."""
        await self.db.execute(
            user_roles.insert().values(user_id=user_id, role_id=role_id)
        )
        await self.db.commit()
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Remove a role from a user."""
        await self.db.execute(
            user_roles.delete().where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_id
                )
            )
        )
        await self.db.commit()
        return True

    # ============== Permissions ==============

    async def list_permissions(
        self,
        category: Optional[str] = None
    ) -> List[Permission]:
        """List all permissions."""
        query = select(Permission)
        if category:
            query = query.where(Permission.category == category)
        query = query.order_by(Permission.category, Permission.code)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def seed_permissions(self) -> List[Permission]:
        """Seed default permissions."""
        default_permissions = [
            # Incidents
            ("incidents:read", "Read Incidents", "incidents", "incidents", "read"),
            ("incidents:write", "Create/Update Incidents", "incidents", "incidents", "write"),
            ("incidents:delete", "Delete Incidents", "incidents", "incidents", "delete"),
            ("incidents:admin", "Manage All Incidents", "incidents", "incidents", "admin"),
            # Alerts
            ("alerts:read", "Read Alerts", "alerts", "alerts", "read"),
            ("alerts:write", "Create/Update Alerts", "alerts", "alerts", "write"),
            ("alerts:delete", "Delete Alerts", "alerts", "alerts", "delete"),
            # Vulnerabilities
            ("vulnerabilities:read", "Read Vulnerabilities", "vulnerabilities", "vulnerabilities", "read"),
            ("vulnerabilities:write", "Create/Update Vulnerabilities", "vulnerabilities", "vulnerabilities", "write"),
            ("vulnerabilities:delete", "Delete Vulnerabilities", "vulnerabilities", "vulnerabilities", "delete"),
            # Risks
            ("risks:read", "Read Risks", "risks", "risks", "read"),
            ("risks:write", "Create/Update Risks", "risks", "risks", "write"),
            ("risks:delete", "Delete Risks", "risks", "risks", "delete"),
            # Users
            ("users:read", "Read Users", "users", "users", "read"),
            ("users:write", "Manage Users", "users", "users", "write"),
            ("users:admin", "Admin Users", "users", "users", "admin"),
            # Teams
            ("teams:read", "Read Teams", "teams", "teams", "read"),
            ("teams:write", "Manage Teams", "teams", "teams", "write"),
            # Roles
            ("roles:read", "Read Roles", "roles", "roles", "read"),
            ("roles:write", "Manage Roles", "roles", "roles", "write"),
            # Reports
            ("reports:read", "Read Reports", "reports", "reports", "read"),
            ("reports:write", "Create Reports", "reports", "reports", "write"),
            # Settings
            ("settings:read", "Read Settings", "settings", "settings", "read"),
            ("settings:write", "Manage Settings", "settings", "settings", "write"),
        ]

        permissions = []
        for code, name, category, resource, action in default_permissions:
            existing = await self.db.execute(
                select(Permission).where(Permission.code == code)
            )
            if not existing.scalar_one_or_none():
                perm = Permission(
                    code=code,
                    name=name,
                    category=category,
                    resource=resource,
                    action=action,
                    is_system=True
                )
                self.db.add(perm)
                permissions.append(perm)

        await self.db.commit()
        return permissions

    # ============== Sessions ==============

    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get user's sessions."""
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id
            ).order_by(UserSession.last_active_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a session."""
        result = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.id == session_id,
                    UserSession.user_id == user_id
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return False

        session.status = SessionStatus.REVOKED
        session.revoked_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def revoke_all_sessions(self, user_id: str, except_current: Optional[str] = None) -> int:
        """Revoke all user sessions."""
        query = update(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.status == SessionStatus.ACTIVE
            )
        )
        if except_current:
            query = query.where(UserSession.id != except_current)

        query = query.values(
            status=SessionStatus.REVOKED,
            revoked_at=datetime.utcnow()
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    # ============== Invitations ==============

    async def create_invitation(
        self,
        data: InvitationCreate,
        invited_by: str
    ) -> UserInvitation:
        """Create a user invitation."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)

        invitation = UserInvitation(
            email=data.email,
            token=token,
            role_id=data.role_id,
            team_id=data.team_id,
            message=data.message,
            expires_at=expires_at,
            invited_by=invited_by
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def list_invitations(
        self,
        status: Optional[InvitationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[UserInvitation], int]:
        """List invitations."""
        query = select(UserInvitation)

        if status:
            query = query.where(UserInvitation.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(UserInvitation.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total or 0

    async def revoke_invitation(self, invitation_id: str) -> bool:
        """Revoke an invitation."""
        result = await self.db.execute(
            select(UserInvitation).where(UserInvitation.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()
        if not invitation or invitation.status != InvitationStatus.PENDING:
            return False

        invitation.status = InvitationStatus.REVOKED
        await self.db.commit()
        return True

    # ============== Activity Logs ==============

    async def log_activity(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> ActivityLog:
        """Log an activity."""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.commit()
        return log

    async def get_activity_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[ActivityLog], int]:
        """Get activity logs."""
        query = select(ActivityLog)

        if user_id:
            query = query.where(ActivityLog.user_id == user_id)
        if action:
            query = query.where(ActivityLog.action == action)
        if resource_type:
            query = query.where(ActivityLog.resource_type == resource_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(ActivityLog.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total or 0

    # ============== API Keys ==============

    async def create_api_key(
        self,
        user_id: str,
        data: APIKeyCreate
    ) -> tuple[APIKey, str]:
        """Create an API key. Returns the key object and the full key (only shown once)."""
        # Generate key
        full_key = f"irc_{secrets.token_urlsafe(32)}"
        key_prefix = full_key[:12]
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        expires_at = None
        if data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)

        api_key = APIKey(
            user_id=user_id,
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=data.scopes,
            rate_limit=data.rate_limit,
            expires_at=expires_at
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        return api_key, full_key

    async def list_api_keys(self, user_id: str) -> List[APIKey]:
        """List user's API keys."""
        result = await self.db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id
            ).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key."""
        result = await self.db.execute(
            select(APIKey).where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id
                )
            )
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            return False

        api_key.is_active = False
        await self.db.commit()
        return True

    # ============== Stats ==============

    async def get_stats(self) -> UserManagementStats:
        """Get user management statistics."""
        # User counts
        total_users = await self.db.scalar(select(func.count()).select_from(User))
        active_users = await self.db.scalar(
            select(func.count()).where(User.is_active == True)
        )

        # Other counts
        total_teams = await self.db.scalar(select(func.count()).select_from(Team))
        total_roles = await self.db.scalar(select(func.count()).select_from(Role))

        pending_invitations = await self.db.scalar(
            select(func.count()).where(
                UserInvitation.status == InvitationStatus.PENDING
            )
        )

        active_sessions = await self.db.scalar(
            select(func.count()).where(
                UserSession.status == SessionStatus.ACTIVE
            )
        )

        # Users by role
        role_query = select(User.role, func.count()).group_by(User.role)
        role_result = await self.db.execute(role_query)
        users_by_role = {str(r.value): c for r, c in role_result.fetchall()}

        # Recent logins (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logins = await self.db.scalar(
            select(func.count()).where(User.last_login >= yesterday)
        )

        # New users this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        new_users = await self.db.scalar(
            select(func.count()).where(User.created_at >= month_start)
        )

        return UserManagementStats(
            total_users=total_users or 0,
            active_users=active_users or 0,
            inactive_users=(total_users or 0) - (active_users or 0),
            total_teams=total_teams or 0,
            total_roles=total_roles or 0,
            pending_invitations=pending_invitations or 0,
            active_sessions=active_sessions or 0,
            users_by_role=users_by_role,
            recent_logins=recent_logins or 0,
            new_users_this_month=new_users or 0
        )
