"""add_multi_tenancy_tables

Create organizations and organization_members tables,
add is_super_admin to users, add tenant_id (nullable) to models.

Revision ID: a1b2c3d4e5f6
Revises: 3fdaec0013d5
Create Date: 2026-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3fdaec0013d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that need tenant_id
TENANT_TABLES = [
    'incidents',
    'affected_systems',
    'evidence_entries',
    'soc_alerts',
    'alert_comments',
    'soc_cases',
    'case_tasks',
    'case_timeline',
    'soc_playbooks',
    'playbook_executions',
    'soc_metrics',
    'shift_handovers',
    'assets',
    'vulnerabilities',
    'vulnerability_comments',
    'vulnerability_scans',
    'scan_schedules',
    'risks',
    'risk_controls',
    'risk_assessments',
    'treatment_actions',
    'risk_appetite',
    'teams',
    'team_members',
    'notifications',
    'integrations',
]


def upgrade() -> None:
    """Upgrade schema - add multi-tenancy support."""
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'suspended', 'trial', 'cancelled', name='organizationstatus'), nullable=False),
        sa.Column('plan', sa.Enum('free', 'starter', 'professional', 'enterprise', name='organizationplan'), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # Create organization_members table
    op.create_table('organization_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('org_role', sa.Enum('owner', 'admin', 'member', 'viewer', name='organizationmemberrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('invited_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_user')
    )
    op.create_index(op.f('ix_organization_members_organization_id'), 'organization_members', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_members_user_id'), 'organization_members', ['user_id'], unique=False)

    # Add is_super_admin to users
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Add tenant_id (nullable for now) to all tenant-aware tables
    for table in TENANT_TABLES:
        op.add_column(table, sa.Column('tenant_id', sa.String(length=36), nullable=True))
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove multi-tenancy support."""
    # Remove tenant_id from all tables
    for table in reversed(TENANT_TABLES):
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        op.drop_column(table, 'tenant_id')

    # Remove is_super_admin from users
    op.drop_column('users', 'is_super_admin')

    # Drop organization_members table
    op.drop_index(op.f('ix_organization_members_user_id'), table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_organization_id'), table_name='organization_members')
    op.drop_table('organization_members')

    # Drop organizations table
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS organizationstatus")
    op.execute("DROP TYPE IF EXISTS organizationplan")
    op.execute("DROP TYPE IF EXISTS organizationmemberrole")
