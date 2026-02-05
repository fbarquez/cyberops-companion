"""add_iso27001_tables

Create tables for ISO 27001:2022 compliance module:
- iso27001_controls (global reference data - 93 controls)
- iso27001_assessments (tenant-scoped assessments)
- iso27001_soa_entries (Statement of Applicability entries)

Revision ID: e5f6g7h8i9j0
Revises: b2c3d4e5f6g7
Create Date: 2026-02-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add ISO 27001:2022 tables."""
    # Create iso27001_controls table (global reference data)
    op.create_table('iso27001_controls',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('control_id', sa.String(length=20), nullable=False),
        sa.Column('theme', sa.Enum('A.5', 'A.6', 'A.7', 'A.8', name='iso27001theme'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title_en', sa.String(length=255), nullable=False),
        sa.Column('title_de', sa.String(length=255), nullable=True),
        sa.Column('title_es', sa.String(length=255), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('description_de', sa.Text(), nullable=True),
        sa.Column('guidance', sa.Text(), nullable=True),
        sa.Column('control_type', sa.JSON(), nullable=True),
        sa.Column('security_properties', sa.JSON(), nullable=True),
        sa.Column('cross_references', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iso27001_controls_control_id'), 'iso27001_controls', ['control_id'], unique=True)
    op.create_index(op.f('ix_iso27001_controls_theme'), 'iso27001_controls', ['theme'], unique=False)

    # Create iso27001_assessments table (tenant-scoped)
    op.create_table('iso27001_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'scoping', 'soa', 'assessment', 'gap_analysis', 'completed', 'archived', name='iso27001assessmentstatus'), nullable=False, server_default='draft'),
        sa.Column('scope_description', sa.Text(), nullable=True),
        sa.Column('scope_systems', sa.JSON(), nullable=True),
        sa.Column('scope_locations', sa.JSON(), nullable=True),
        sa.Column('scope_processes', sa.JSON(), nullable=True),
        sa.Column('risk_appetite', sa.String(length=50), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('organizational_score', sa.Float(), nullable=True),
        sa.Column('people_score', sa.Float(), nullable=True),
        sa.Column('physical_score', sa.Float(), nullable=True),
        sa.Column('technological_score', sa.Float(), nullable=True),
        sa.Column('applicable_controls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('compliant_controls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('partial_controls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gap_controls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iso27001_assessments_status'), 'iso27001_assessments', ['status'], unique=False)
    op.create_index(op.f('ix_iso27001_assessments_tenant_id'), 'iso27001_assessments', ['tenant_id'], unique=False)

    # Create iso27001_soa_entries table (Statement of Applicability)
    op.create_table('iso27001_soa_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('assessment_id', sa.String(length=36), nullable=False),
        sa.Column('control_id', sa.String(length=36), nullable=False),
        sa.Column('applicability', sa.Enum('applicable', 'not_applicable', 'excluded', name='iso27001applicability'), nullable=False, server_default='applicable'),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('not_evaluated', 'compliant', 'partial', 'gap', 'not_applicable', name='iso27001compliancestatus'), nullable=False, server_default='not_evaluated'),
        sa.Column('implementation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('implementation_notes', sa.Text(), nullable=True),
        sa.Column('gap_description', sa.Text(), nullable=True),
        sa.Column('remediation_plan', sa.Text(), nullable=True),
        sa.Column('remediation_owner', sa.String(length=255), nullable=True),
        sa.Column('remediation_due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('assessed_by', sa.String(length=36), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assessed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assessment_id'], ['iso27001_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['control_id'], ['iso27001_controls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iso27001_soa_entries_assessment_id'), 'iso27001_soa_entries', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_iso27001_soa_entries_control_id'), 'iso27001_soa_entries', ['control_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove ISO 27001:2022 tables."""
    # Drop iso27001_soa_entries table
    op.drop_index(op.f('ix_iso27001_soa_entries_control_id'), table_name='iso27001_soa_entries')
    op.drop_index(op.f('ix_iso27001_soa_entries_assessment_id'), table_name='iso27001_soa_entries')
    op.drop_table('iso27001_soa_entries')

    # Drop iso27001_assessments table
    op.drop_index(op.f('ix_iso27001_assessments_tenant_id'), table_name='iso27001_assessments')
    op.drop_index(op.f('ix_iso27001_assessments_status'), table_name='iso27001_assessments')
    op.drop_table('iso27001_assessments')

    # Drop iso27001_controls table
    op.drop_index(op.f('ix_iso27001_controls_theme'), table_name='iso27001_controls')
    op.drop_index(op.f('ix_iso27001_controls_control_id'), table_name='iso27001_controls')
    op.drop_table('iso27001_controls')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS iso27001compliancestatus")
    op.execute("DROP TYPE IF EXISTS iso27001applicability")
    op.execute("DROP TYPE IF EXISTS iso27001assessmentstatus")
    op.execute("DROP TYPE IF EXISTS iso27001theme")
