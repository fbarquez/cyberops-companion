"""Base service with tenant awareness for multi-tenancy support."""
from typing import TypeVar, Generic, Type, Optional, List, Tuple, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.tenant_context import get_current_tenant, get_current_tenant_id

T = TypeVar('T')


class TenantAwareService(Generic[T]):
    """Base service class with automatic tenant isolation.

    All services that need tenant isolation should inherit from this class.
    It provides:
    - Automatic tenant_id filtering on queries
    - Automatic tenant_id setting on create
    - Super admin bypass for cross-tenant access

    Usage:
        class IncidentService(TenantAwareService[Incident]):
            model_class = Incident

            async def list(self, ...):
                query = self._base_query()  # Automatically filtered by tenant
                ...
    """

    model_class: Type[T]

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    def _get_tenant_id(self) -> str:
        """Get current tenant ID from context.

        Returns:
            Current tenant ID

        Raises:
            ValueError: If tenant context is not set
        """
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context not set. Ensure TenantMiddleware is active.")
        return tenant_id

    def _is_super_admin(self) -> bool:
        """Check if current user is super admin.

        Returns:
            True if user is super admin
        """
        ctx = get_current_tenant()
        return ctx.is_super_admin if ctx else False

    def _base_query(self, model: Type[T] = None):
        """Create base query with tenant filter.

        If the model has a tenant_id field and the user is not a super admin,
        the query will be filtered to only return records for the current tenant.

        Args:
            model: Optional model class (defaults to self.model_class)

        Returns:
            SQLAlchemy select query with tenant filter applied
        """
        m = model or self.model_class
        query = select(m)

        # Apply tenant filter if model has tenant_id and user is not super admin
        if hasattr(m, 'tenant_id') and not self._is_super_admin():
            query = query.where(m.tenant_id == self._get_tenant_id())

        return query

    def _set_tenant_on_create(self, entity: T) -> T:
        """Set tenant_id on entity before creation.

        Args:
            entity: Entity instance to set tenant_id on

        Returns:
            Same entity with tenant_id set
        """
        if hasattr(entity, 'tenant_id'):
            entity.tenant_id = self._get_tenant_id()
        return entity

    def _add_tenant_filter(self, query, model: Type[T] = None):
        """Add tenant filter to an existing query.

        Useful when building complex queries that don't start with _base_query.

        Args:
            query: Existing SQLAlchemy query
            model: Model class to filter on

        Returns:
            Query with tenant filter added
        """
        m = model or self.model_class
        if hasattr(m, 'tenant_id') and not self._is_super_admin():
            query = query.where(m.tenant_id == self._get_tenant_id())
        return query

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID with tenant isolation.

        Args:
            entity_id: Primary key of entity

        Returns:
            Entity if found and accessible, None otherwise
        """
        query = self._base_query().where(self.model_class.id == entity_id)

        # Add soft delete filter if model supports it
        if hasattr(self.model_class, 'is_deleted'):
            query = query.where(self.model_class.is_deleted == False)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        filters: Optional[dict] = None,
        order_by: Optional[Any] = None
    ) -> Tuple[List[T], int]:
        """List entities with pagination and tenant isolation.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            filters: Optional dict of field:value filters
            order_by: Optional column to order by

        Returns:
            Tuple of (list of entities, total count)
        """
        query = self._base_query()

        # Add soft delete filter if model supports it
        if hasattr(self.model_class, 'is_deleted'):
            query = query.where(self.model_class.is_deleted == False)

        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field) and value is not None:
                    query = query.where(getattr(self.model_class, field) == value)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply ordering
        if order_by is not None:
            query = query.order_by(order_by)
        elif hasattr(self.model_class, 'created_at'):
            query = query.order_by(self.model_class.created_at.desc())

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        entities = result.scalars().all()

        return list(entities), total or 0
