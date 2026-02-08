"""add_onboarding_tables

Create onboarding wizard tables for organization profiles and compliance plans.

Revision ID: e6f7g8h9i0j1
Revises: d4e5f6g7h8i9
Create Date: 2026-02-08 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7g8h9i0j1'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add onboarding tables."""

    # Create IndustrySector enum
    industry_sector = sa.Enum(
        'banking', 'insurance', 'investment', 'payment_services', 'crypto_assets',
        'energy', 'water', 'food', 'healthcare', 'transport',
        'digital_infrastructure', 'ict_services', 'space', 'postal',
        'waste_management', 'chemicals', 'manufacturing',
        'automotive', 'automotive_supplier',
        'public_administration', 'retail', 'professional_services', 'technology', 'other',
        name='industrysector'
    )

    # Create CompanySize enum
    company_size = sa.Enum(
        'micro', 'small', 'medium', 'large',
        name='companysize'
    )

    # Create CountryCode enum
    country_code = sa.Enum(
        'DE', 'AT', 'CH', 'FR', 'NL', 'BE', 'LU', 'IT', 'ES', 'PT',
        'PL', 'CZ', 'SK', 'HU', 'RO', 'BG', 'GR', 'SE', 'FI', 'DK', 'IE',
        'OTHER_EU', 'NON_EU',
        name='countrycode'
    )

    # Create OnboardingStatus enum
    onboarding_status = sa.Enum(
        'not_started', 'in_progress', 'completed',
        name='onboardingstatus'
    )

    # Create organization_profiles table
    op.create_table('organization_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Basic Info
        sa.Column('organization_name', sa.String(length=255), nullable=False),
        sa.Column('industry_sector', industry_sector, nullable=False),
        sa.Column('company_size', company_size, nullable=False),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('annual_revenue_eur', sa.Integer(), nullable=True),

        # Location
        sa.Column('headquarters_country', country_code, nullable=False),
        sa.Column('operates_in_eu', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('eu_member_states', sa.JSON(), nullable=True),

        # Special Status
        sa.Column('is_kritis_operator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('kritis_sector', sa.String(length=100), nullable=True),
        sa.Column('is_bafin_regulated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_essential_service', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_important_entity', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supplies_to_oem', sa.Boolean(), nullable=False, server_default='false'),

        # Detected Regulations
        sa.Column('applicable_regulations', sa.JSON(), nullable=True),

        # Selected Baseline
        sa.Column('selected_frameworks', sa.JSON(), nullable=True),

        # Onboarding Status
        sa.Column('onboarding_status', onboarding_status, nullable=False, server_default='not_started'),
        sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),

        # Compliance Plan (JSON)
        sa.Column('compliance_plan', sa.JSON(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', name='uq_organization_profile_tenant')
    )
    op.create_index(op.f('ix_organization_profiles_tenant_id'), 'organization_profiles', ['tenant_id'], unique=True)
    op.create_index('ix_organization_profiles_status', 'organization_profiles', ['onboarding_status'], unique=False)

    # Create compliance_plan_items table
    op.create_table('compliance_plan_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profile_id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Item Details
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),

        # Source
        sa.Column('regulation_id', sa.String(length=50), nullable=True),
        sa.Column('framework_id', sa.String(length=50), nullable=True),
        sa.Column('control_ref', sa.String(length=50), nullable=True),

        # Assignment
        sa.Column('owner_role', sa.String(length=100), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=True),

        # Timeline
        sa.Column('priority', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_effort_days', sa.Integer(), nullable=True),

        # Status
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Evidence
        sa.Column('evidence_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('evidence_type', sa.String(length=100), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.ForeignKeyConstraint(['profile_id'], ['organization_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_plan_items_profile_id'), 'compliance_plan_items', ['profile_id'], unique=False)
    op.create_index(op.f('ix_compliance_plan_items_tenant_id'), 'compliance_plan_items', ['tenant_id'], unique=False)
    op.create_index('ix_compliance_plan_items_category', 'compliance_plan_items', ['category'], unique=False)
    op.create_index('ix_compliance_plan_items_status', 'compliance_plan_items', ['status'], unique=False)
    op.create_index('ix_compliance_plan_items_priority', 'compliance_plan_items', ['priority'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove onboarding tables."""

    # Drop compliance_plan_items table
    op.drop_index('ix_compliance_plan_items_priority', table_name='compliance_plan_items')
    op.drop_index('ix_compliance_plan_items_status', table_name='compliance_plan_items')
    op.drop_index('ix_compliance_plan_items_category', table_name='compliance_plan_items')
    op.drop_index(op.f('ix_compliance_plan_items_tenant_id'), table_name='compliance_plan_items')
    op.drop_index(op.f('ix_compliance_plan_items_profile_id'), table_name='compliance_plan_items')
    op.drop_table('compliance_plan_items')

    # Drop organization_profiles table
    op.drop_index('ix_organization_profiles_status', table_name='organization_profiles')
    op.drop_index(op.f('ix_organization_profiles_tenant_id'), table_name='organization_profiles')
    op.drop_table('organization_profiles')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS onboardingstatus")
    op.execute("DROP TYPE IF EXISTS countrycode")
    op.execute("DROP TYPE IF EXISTS companysize")
    op.execute("DROP TYPE IF EXISTS industrysector")
