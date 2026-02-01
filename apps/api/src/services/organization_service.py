"""Organization management service."""
import re
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.organization import (
    Organization, OrganizationMember, OrganizationStatus,
    OrganizationPlan, OrganizationMemberRole
)
from src.models.user import User
from src.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, MemberInvite, MemberUpdate
)


class OrganizationService:
    """Service for organization operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from organization name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:100]

    async def _ensure_unique_slug(self, slug: str, exclude_id: Optional[str] = None) -> str:
        """Ensure slug is unique, appending number if necessary."""
        base_slug = slug
        counter = 1

        while True:
            query = select(Organization).where(Organization.slug == slug)
            if exclude_id:
                query = query.where(Organization.id != exclude_id)

            result = await self.db.execute(query)
            if not result.scalar_one_or_none():
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1

    async def create(
        self,
        data: OrganizationCreate,
        owner_id: str
    ) -> Organization:
        """Create a new organization with the creator as owner.

        Args:
            data: Organization creation data
            owner_id: User ID who will be the owner

        Returns:
            Created organization
        """
        # Generate unique slug
        slug = data.slug if data.slug else self._generate_slug(data.name)
        slug = await self._ensure_unique_slug(slug)

        organization = Organization(
            id=str(uuid4()),
            name=data.name,
            slug=slug,
            description=data.description,
            status=OrganizationStatus.TRIAL,
            plan=OrganizationPlan.FREE,
            settings=data.settings or {},
        )
        self.db.add(organization)
        await self.db.flush()

        # Add creator as owner
        membership = OrganizationMember(
            id=str(uuid4()),
            organization_id=organization.id,
            user_id=owner_id,
            org_role=OrganizationMemberRole.OWNER,
            is_default=True,
            is_active=True,
        )
        self.db.add(membership)
        await self.db.flush()
        await self.db.refresh(organization)

        return organization

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_user_organizations(
        self,
        user_id: str,
        include_inactive: bool = False
    ) -> List[dict]:
        """Get all organizations a user is a member of.

        Args:
            user_id: User ID
            include_inactive: Whether to include inactive memberships

        Returns:
            List of organization dicts with membership info
        """
        query = (
            select(Organization, OrganizationMember)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
        )

        if not include_inactive:
            query = query.where(OrganizationMember.is_active == True)

        result = await self.db.execute(query)
        rows = result.all()

        organizations = []
        for org, membership in rows:
            organizations.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "status": org.status.value,
                "plan": org.plan.value,
                "logo_url": org.logo_url,
                "org_role": membership.org_role.value,
                "is_default": membership.is_default,
                "joined_at": membership.joined_at.isoformat(),
            })

        return organizations

    async def update(
        self,
        org_id: str,
        data: OrganizationUpdate,
        user_id: str
    ) -> Optional[Organization]:
        """Update organization settings.

        Args:
            org_id: Organization ID
            data: Update data
            user_id: User making the update (must be admin/owner)

        Returns:
            Updated organization or None if not found/not authorized
        """
        # Check permission
        membership = await self.get_membership(org_id, user_id)
        if not membership or membership.org_role not in [
            OrganizationMemberRole.OWNER,
            OrganizationMemberRole.ADMIN
        ]:
            return None

        organization = await self.get_by_id(org_id)
        if not organization:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle slug uniqueness
        if 'slug' in update_data and update_data['slug']:
            update_data['slug'] = await self._ensure_unique_slug(
                update_data['slug'],
                exclude_id=org_id
            )

        for field, value in update_data.items():
            setattr(organization, field, value)

        await self.db.flush()
        await self.db.refresh(organization)
        return organization

    async def get_membership(
        self,
        org_id: str,
        user_id: str
    ) -> Optional[OrganizationMember]:
        """Get membership for a user in an organization."""
        result = await self.db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_members(
        self,
        org_id: str,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[dict], int]:
        """List organization members with pagination."""
        query = (
            select(User, OrganizationMember)
            .join(OrganizationMember, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == org_id)
            .where(OrganizationMember.is_active == True)
        )

        # Count total
        count_query = select(func.count()).select_from(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .where(OrganizationMember.is_active == True)
            .subquery()
        )
        total = await self.db.scalar(count_query)

        # Paginate
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        rows = result.all()

        members = []
        for user, membership in rows:
            members.append({
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "org_role": membership.org_role.value,
                "is_default": membership.is_default,
                "joined_at": membership.joined_at.isoformat(),
                "invited_by": membership.invited_by,
            })

        return members, total or 0

    async def invite_member(
        self,
        org_id: str,
        data: MemberInvite,
        invited_by_user_id: str
    ) -> Optional[OrganizationMember]:
        """Invite/add a user to an organization.

        Args:
            org_id: Organization ID
            data: Invite data with user_id and role
            invited_by_user_id: User ID of the person inviting

        Returns:
            New membership or None if not authorized
        """
        # Check inviter's permission
        inviter_membership = await self.get_membership(org_id, invited_by_user_id)
        if not inviter_membership or inviter_membership.org_role not in [
            OrganizationMemberRole.OWNER,
            OrganizationMemberRole.ADMIN
        ]:
            return None

        # Can't invite at higher role than yourself (except owner can do anything)
        role_hierarchy = {
            OrganizationMemberRole.OWNER: 4,
            OrganizationMemberRole.ADMIN: 3,
            OrganizationMemberRole.MEMBER: 2,
            OrganizationMemberRole.VIEWER: 1,
        }
        if (inviter_membership.org_role != OrganizationMemberRole.OWNER and
            role_hierarchy.get(data.org_role, 0) >= role_hierarchy.get(inviter_membership.org_role, 0)):
            return None

        # Check if already a member
        existing = await self.get_membership(org_id, data.user_id)
        if existing:
            # Update existing membership instead
            existing.org_role = data.org_role
            existing.is_active = True
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        # Check organization user limit
        org = await self.get_by_id(org_id)
        if not org:
            return None

        member_count = await self.db.scalar(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .where(OrganizationMember.is_active == True)
        )
        if member_count and member_count >= org.max_users:
            raise ValueError("Organization has reached maximum user limit")

        # Create membership
        membership = OrganizationMember(
            id=str(uuid4()),
            organization_id=org_id,
            user_id=data.user_id,
            org_role=data.org_role,
            is_default=False,
            is_active=True,
            invited_by=invited_by_user_id,
        )
        self.db.add(membership)
        await self.db.flush()
        await self.db.refresh(membership)

        return membership

    async def update_member(
        self,
        org_id: str,
        user_id: str,
        data: MemberUpdate,
        updated_by_user_id: str
    ) -> Optional[OrganizationMember]:
        """Update a member's role in an organization.

        Args:
            org_id: Organization ID
            user_id: User ID to update
            data: Update data
            updated_by_user_id: User making the update

        Returns:
            Updated membership or None
        """
        # Check updater's permission
        updater_membership = await self.get_membership(org_id, updated_by_user_id)
        if not updater_membership or updater_membership.org_role not in [
            OrganizationMemberRole.OWNER,
            OrganizationMemberRole.ADMIN
        ]:
            return None

        # Get target membership
        membership = await self.get_membership(org_id, user_id)
        if not membership:
            return None

        # Can't modify owner unless you're also owner
        if (membership.org_role == OrganizationMemberRole.OWNER and
            updater_membership.org_role != OrganizationMemberRole.OWNER):
            return None

        if data.org_role is not None:
            membership.org_role = data.org_role

        await self.db.flush()
        await self.db.refresh(membership)
        return membership

    async def remove_member(
        self,
        org_id: str,
        user_id: str,
        removed_by_user_id: str
    ) -> bool:
        """Remove a member from an organization.

        Args:
            org_id: Organization ID
            user_id: User ID to remove
            removed_by_user_id: User making the removal

        Returns:
            True if removed, False otherwise
        """
        # Check remover's permission
        remover_membership = await self.get_membership(org_id, removed_by_user_id)
        if not remover_membership or remover_membership.org_role not in [
            OrganizationMemberRole.OWNER,
            OrganizationMemberRole.ADMIN
        ]:
            return False

        # Get target membership
        membership = await self.get_membership(org_id, user_id)
        if not membership:
            return False

        # Can't remove owner unless you're the owner removing yourself
        if membership.org_role == OrganizationMemberRole.OWNER:
            if user_id != removed_by_user_id:
                return False
            # If owner is removing themselves, ensure there's another owner
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(OrganizationMember.organization_id == org_id)
                .where(OrganizationMember.org_role == OrganizationMemberRole.OWNER)
                .where(OrganizationMember.is_active == True)
            )
            if owner_count and owner_count <= 1:
                raise ValueError("Cannot remove the last owner. Transfer ownership first.")

        # Soft delete membership
        membership.is_active = False
        await self.db.flush()
        return True

    async def set_default_organization(
        self,
        user_id: str,
        org_id: str
    ) -> bool:
        """Set an organization as the user's default.

        Args:
            user_id: User ID
            org_id: Organization ID to set as default

        Returns:
            True if set successfully
        """
        # Verify membership exists
        membership = await self.get_membership(org_id, user_id)
        if not membership or not membership.is_active:
            return False

        # Unset current default
        await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .where(OrganizationMember.is_default == True)
        )
        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .where(OrganizationMember.is_default == True)
        )
        for m in result.scalars().all():
            m.is_default = False

        # Set new default
        membership.is_default = True
        await self.db.flush()
        return True

    async def transfer_ownership(
        self,
        org_id: str,
        new_owner_id: str,
        current_owner_id: str
    ) -> bool:
        """Transfer organization ownership to another member.

        Args:
            org_id: Organization ID
            new_owner_id: User ID of new owner
            current_owner_id: Current owner making the transfer

        Returns:
            True if transferred successfully
        """
        # Verify current owner
        current_membership = await self.get_membership(org_id, current_owner_id)
        if not current_membership or current_membership.org_role != OrganizationMemberRole.OWNER:
            return False

        # Verify new owner is a member
        new_membership = await self.get_membership(org_id, new_owner_id)
        if not new_membership or not new_membership.is_active:
            return False

        # Transfer
        new_membership.org_role = OrganizationMemberRole.OWNER
        current_membership.org_role = OrganizationMemberRole.ADMIN

        await self.db.flush()
        return True
