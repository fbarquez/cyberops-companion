"""migrate_to_multi_tenancy

Create default organization, migrate existing users and data,
make tenant_id NOT NULL with foreign key.

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-01 00:01:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
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
    """Migrate existing data to multi-tenancy and finalize schema."""
    # Generate default organization ID
    default_org_id = str(uuid4())
    now = datetime.utcnow()

    # Create default organization
    organizations = table('organizations',
        column('id', sa.String),
        column('name', sa.String),
        column('slug', sa.String),
        column('description', sa.Text),
        column('status', sa.String),
        column('plan', sa.String),
        column('max_users', sa.Integer),
        column('settings', sa.JSON),
        column('created_at', sa.DateTime),
    )

    op.bulk_insert(organizations, [
        {
            'id': default_org_id,
            'name': 'Default Organization',
            'slug': 'default',
            'description': 'Default organization created during multi-tenancy migration',
            'status': 'active',
            'plan': 'enterprise',
            'max_users': 1000,
            'settings': {},
            'created_at': now,
        }
    ])

    # Link all existing users to default organization as members
    # Using raw SQL for efficiency with existing data
    # Cast role enum to text for comparison
    op.execute(f"""
        INSERT INTO organization_members (id, organization_id, user_id, org_role, is_active, is_default, joined_at)
        SELECT
            gen_random_uuid()::text,
            '{default_org_id}',
            id,
            CASE
                WHEN role::text = 'admin' THEN 'owner'
                WHEN role::text = 'manager' THEN 'admin'
                ELSE 'member'
            END::organizationmemberrole,
            true,
            true,
            COALESCE(created_at, now())
        FROM users
    """)

    # Set first admin user as super admin
    op.execute("""
        UPDATE users
        SET is_super_admin = true
        WHERE id = (
            SELECT id FROM users
            WHERE role::text = 'admin'
            ORDER BY created_at ASC
            LIMIT 1
        )
    """)

    # Assign default org tenant_id to all existing records
    for table_name in TENANT_TABLES:
        op.execute(f"""
            UPDATE {table_name}
            SET tenant_id = '{default_org_id}'
            WHERE tenant_id IS NULL
        """)

    # Now make tenant_id NOT NULL and add foreign keys
    for table_name in TENANT_TABLES:
        op.alter_column(table_name, 'tenant_id', nullable=False)
        op.create_foreign_key(
            f'fk_{table_name}_tenant_id',
            table_name,
            'organizations',
            ['tenant_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """Revert multi-tenancy data migration."""
    # Remove foreign keys and make tenant_id nullable again
    for table_name in reversed(TENANT_TABLES):
        op.drop_constraint(f'fk_{table_name}_tenant_id', table_name, type_='foreignkey')
        op.alter_column(table_name, 'tenant_id', nullable=True)

    # Clear tenant_id values (optional, for clean rollback)
    for table_name in TENANT_TABLES:
        op.execute(f"UPDATE {table_name} SET tenant_id = NULL")

    # Remove organization memberships for default org
    op.execute("""
        DELETE FROM organization_members
        WHERE organization_id IN (
            SELECT id FROM organizations WHERE slug = 'default'
        )
    """)

    # Remove default organization
    op.execute("DELETE FROM organizations WHERE slug = 'default'")

    # Reset super admin flag
    op.execute("UPDATE users SET is_super_admin = false")
