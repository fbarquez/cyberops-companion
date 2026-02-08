"""add_dora_tables

Create DORA (Digital Operational Resilience Act) compliance tables
for financial entity assessments across 5 pillars with 28 requirements.

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add DORA compliance tables."""

    # Create DORA Pillar enum
    dora_pillar = sa.Enum(
        'ict_risk_management',
        'incident_reporting',
        'resilience_testing',
        'third_party_risk',
        'information_sharing',
        name='dorapillar'
    )

    # Create DORA Entity Type enum (20+ financial entity types)
    dora_entity_type = sa.Enum(
        'credit_institution',
        'investment_firm',
        'payment_institution',
        'e_money_institution',
        'insurance_undertaking',
        'reinsurance_undertaking',
        'insurance_intermediary',
        'ucits_manager',
        'aifm',
        'ccp',
        'csd',
        'trading_venue',
        'trade_repository',
        'casp',
        'crowdfunding',
        'cra',
        'pension_fund',
        'drsp',
        'securitisation_repository',
        'ict_provider',
        name='doraentitytype'
    )

    # Create DORA Company Size enum
    dora_company_size = sa.Enum(
        'micro', 'small', 'medium', 'large',
        name='doracompanysize'
    )

    # Create DORA Assessment Status enum
    dora_assessment_status = sa.Enum(
        'draft', 'in_progress', 'completed', 'archived',
        name='doraassessmentstatus'
    )

    # Create DORA Requirement Status enum
    dora_requirement_status = sa.Enum(
        'not_evaluated',
        'not_implemented',
        'partially_implemented',
        'fully_implemented',
        'not_applicable',
        name='dorarequirementstatus'
    )

    # Create dora_assessments table
    op.create_table('dora_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Assessment metadata
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', dora_assessment_status, nullable=False, server_default='draft'),

        # Entity Scope
        sa.Column('entity_type', dora_entity_type, nullable=True),
        sa.Column('company_size', dora_company_size, nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('annual_balance_eur', sa.Float(), nullable=True),
        sa.Column('is_ctpp', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('operates_in_eu', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('eu_member_states', sa.JSON(), nullable=True),

        # Regulatory context
        sa.Column('supervised_by', sa.String(length=255), nullable=True),
        sa.Column('group_level_assessment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('simplified_framework', sa.Boolean(), nullable=False, server_default='false'),

        # Assessment Results
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('pillar_scores', sa.JSON(), nullable=True),
        sa.Column('gaps_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_gaps_count', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_dora_assessment_tenant_name')
    )
    op.create_index(op.f('ix_dora_assessments_tenant_id'), 'dora_assessments', ['tenant_id'], unique=False)
    op.create_index('ix_dora_assessments_status', 'dora_assessments', ['status'], unique=False)
    op.create_index('ix_dora_assessments_entity_type', 'dora_assessments', ['entity_type'], unique=False)
    op.create_index('ix_dora_assessments_tenant_status', 'dora_assessments', ['tenant_id', 'status'], unique=False)

    # Create dora_requirement_responses table
    op.create_table('dora_requirement_responses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('assessment_id', sa.String(length=36), nullable=False),

        # Requirement identification
        sa.Column('requirement_id', sa.String(length=20), nullable=False),
        sa.Column('pillar', dora_pillar, nullable=False),

        # Response
        sa.Column('status', dora_requirement_status, nullable=False, server_default='not_evaluated'),
        sa.Column('implementation_level', sa.Integer(), nullable=False, server_default='0'),

        # Sub-requirements responses (JSON array)
        sa.Column('sub_requirements_status', sa.JSON(), nullable=True),

        # Evidence and notes
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('gap_description', sa.Text(), nullable=True),
        sa.Column('remediation_plan', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('assessed_at', sa.DateTime(), nullable=True),
        sa.Column('assessed_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.ForeignKeyConstraint(['assessment_id'], ['dora_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id', 'requirement_id', name='uq_dora_requirement_assessment')
    )
    op.create_index(op.f('ix_dora_requirement_responses_assessment_id'), 'dora_requirement_responses', ['assessment_id'], unique=False)
    op.create_index('ix_dora_requirement_responses_pillar', 'dora_requirement_responses', ['pillar'], unique=False)
    op.create_index('ix_dora_requirement_responses_status', 'dora_requirement_responses', ['status'], unique=False)
    op.create_index('ix_dora_requirement_assessment_pillar', 'dora_requirement_responses', ['assessment_id', 'pillar'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove DORA compliance tables."""

    # Drop dora_requirement_responses table
    op.drop_index('ix_dora_requirement_assessment_pillar', table_name='dora_requirement_responses')
    op.drop_index('ix_dora_requirement_responses_status', table_name='dora_requirement_responses')
    op.drop_index('ix_dora_requirement_responses_pillar', table_name='dora_requirement_responses')
    op.drop_index(op.f('ix_dora_requirement_responses_assessment_id'), table_name='dora_requirement_responses')
    op.drop_table('dora_requirement_responses')

    # Drop dora_assessments table
    op.drop_index('ix_dora_assessments_tenant_status', table_name='dora_assessments')
    op.drop_index('ix_dora_assessments_entity_type', table_name='dora_assessments')
    op.drop_index('ix_dora_assessments_status', table_name='dora_assessments')
    op.drop_index(op.f('ix_dora_assessments_tenant_id'), table_name='dora_assessments')
    op.drop_table('dora_assessments')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS dorarequirementstatus")
    op.execute("DROP TYPE IF EXISTS doraassessmentstatus")
    op.execute("DROP TYPE IF EXISTS doracompanysize")
    op.execute("DROP TYPE IF EXISTS doraentitytype")
    op.execute("DROP TYPE IF EXISTS dorapillar")
