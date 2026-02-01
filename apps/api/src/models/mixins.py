"""SQLAlchemy mixins for multi-tenancy."""
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class TenantMixin:
    """Mixin to add tenant_id to models for multi-tenancy isolation.

    All models that need tenant isolation should inherit from this mixin.
    The tenant_id will be automatically set from the current tenant context
    when creating new records.
    """

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        """Foreign key to organization for tenant isolation."""
        return mapped_column(
            String(36),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )


class ImmutableTenantMixin(TenantMixin):
    """Mixin for models where tenant_id cannot change after creation.

    Use this for models like Evidence where data integrity is critical
    and tenant association must remain constant.
    """
    pass
