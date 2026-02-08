"""add_evidence_bridge_tables

Create tables for ISMS ↔ SOC evidence bridge.
Links operational activities (incidents, alerts, scans) to compliance controls.

Revision ID: f7g8h9i0j1k2
Revises: e6f7g8h9i0j1
Create Date: 2026-02-08 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, Sequence[str], None] = 'e6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add evidence bridge tables."""

    # Create ActivityType enum
    activity_type = sa.Enum(
        'incident', 'alert', 'case', 'vulnerability_scan', 'vulnerability',
        'threat_ioc', 'playbook_execution', 'risk_assessment', 'bcm_exercise',
        'training_completion', 'document_approval', 'audit_log',
        'vendor_assessment', 'change_request',
        name='activitytype'
    )

    # Create ControlFramework enum
    control_framework = sa.Enum(
        'iso27001', 'dora', 'nis2', 'bsi_grundschutz', 'gdpr', 'tisax',
        name='controlframework'
    )

    # Create LinkType enum
    link_type = sa.Enum(
        'automatic', 'manual', 'rule_based',
        name='linktype'
    )

    # Create EvidenceStrength enum
    evidence_strength = sa.Enum(
        'strong', 'moderate', 'weak',
        name='evidencestrength'
    )

    # Create EffectivenessLevel enum
    effectiveness_level = sa.Enum(
        'not_assessed', 'ineffective', 'partially_effective',
        'largely_effective', 'fully_effective',
        name='effectivenesslevel'
    )

    # Create control_evidence_links table
    op.create_table('control_evidence_links',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Control Reference
        sa.Column('control_framework', control_framework, nullable=False),
        sa.Column('control_id', sa.String(length=50), nullable=False),
        sa.Column('control_name', sa.String(length=255), nullable=True),

        # Activity Reference
        sa.Column('activity_type', activity_type, nullable=False),
        sa.Column('activity_id', sa.String(length=36), nullable=False),
        sa.Column('activity_title', sa.String(length=500), nullable=True),
        sa.Column('activity_date', sa.DateTime(), nullable=True),

        # Link Info
        sa.Column('link_type', link_type, nullable=False, server_default='automatic'),
        sa.Column('evidence_strength', evidence_strength, nullable=False, server_default='moderate'),
        sa.Column('notes', sa.Text(), nullable=True),

        # Metrics captured from activity
        sa.Column('metrics', sa.JSON(), nullable=True),

        # Timestamps
        sa.Column('linked_at', sa.DateTime(), nullable=False),
        sa.Column('linked_by', sa.String(length=36), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'control_framework', 'control_id', 'activity_type', 'activity_id',
                            name='uq_control_evidence_link')
    )
    op.create_index('ix_cev_tenant_id', 'control_evidence_links', ['tenant_id'], unique=False)
    op.create_index('ix_cev_control', 'control_evidence_links', ['tenant_id', 'control_framework', 'control_id'], unique=False)
    op.create_index('ix_cev_activity', 'control_evidence_links', ['tenant_id', 'activity_type', 'activity_id'], unique=False)
    op.create_index('ix_cev_linked_at', 'control_evidence_links', ['linked_at'], unique=False)

    # Create control_effectiveness table
    op.create_table('control_effectiveness',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Control Reference
        sa.Column('control_framework', control_framework, nullable=False),
        sa.Column('control_id', sa.String(length=50), nullable=False),
        sa.Column('control_name', sa.String(length=255), nullable=True),
        sa.Column('control_description', sa.Text(), nullable=True),

        # Effectiveness Score (0-100)
        sa.Column('effectiveness_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('effectiveness_level', effectiveness_level, nullable=False, server_default='not_assessed'),

        # Evidence Counts
        sa.Column('total_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('strong_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('moderate_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weak_evidence_count', sa.Integer(), nullable=False, server_default='0'),

        # Evidence breakdown
        sa.Column('evidence_by_type', sa.JSON(), nullable=True),

        # Operational Metrics
        sa.Column('operational_metrics', sa.JSON(), nullable=True),

        # Last Activity
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        sa.Column('last_activity_type', activity_type, nullable=True),

        # Status
        sa.Column('meets_baseline', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gaps_identified', sa.JSON(), nullable=True),

        # Period
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('calculated_at', sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'control_framework', 'control_id',
                            name='uq_control_effectiveness')
    )
    op.create_index('ix_ce_tenant_id', 'control_effectiveness', ['tenant_id'], unique=False)
    op.create_index('ix_ce_control', 'control_effectiveness', ['tenant_id', 'control_framework', 'control_id'], unique=True)
    op.create_index('ix_ce_score', 'control_effectiveness', ['effectiveness_score'], unique=False)
    op.create_index('ix_ce_level', 'control_effectiveness', ['effectiveness_level'], unique=False)

    # Create evidence_linking_rules table
    op.create_table('evidence_linking_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),

        # Rule Info
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Target Control
        sa.Column('control_framework', control_framework, nullable=False),
        sa.Column('control_id', sa.String(length=50), nullable=False),

        # Source Activity
        sa.Column('activity_type', activity_type, nullable=False),
        sa.Column('activity_filters', sa.JSON(), nullable=True),

        # Linking Config
        sa.Column('evidence_strength', evidence_strength, nullable=False, server_default='moderate'),
        sa.Column('auto_link', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metrics_to_capture', sa.JSON(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),

        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_elr_tenant_id', 'evidence_linking_rules', ['tenant_id'], unique=False)
    op.create_index('ix_elr_control', 'evidence_linking_rules', ['tenant_id', 'control_framework', 'control_id'], unique=False)
    op.create_index('ix_elr_activity', 'evidence_linking_rules', ['tenant_id', 'activity_type'], unique=False)
    op.create_index('ix_elr_active', 'evidence_linking_rules', ['is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove evidence bridge tables."""

    # Drop evidence_linking_rules table
    op.drop_index('ix_elr_active', table_name='evidence_linking_rules')
    op.drop_index('ix_elr_activity', table_name='evidence_linking_rules')
    op.drop_index('ix_elr_control', table_name='evidence_linking_rules')
    op.drop_index('ix_elr_tenant_id', table_name='evidence_linking_rules')
    op.drop_table('evidence_linking_rules')

    # Drop control_effectiveness table
    op.drop_index('ix_ce_level', table_name='control_effectiveness')
    op.drop_index('ix_ce_score', table_name='control_effectiveness')
    op.drop_index('ix_ce_control', table_name='control_effectiveness')
    op.drop_index('ix_ce_tenant_id', table_name='control_effectiveness')
    op.drop_table('control_effectiveness')

    # Drop control_evidence_links table
    op.drop_index('ix_cev_linked_at', table_name='control_evidence_links')
    op.drop_index('ix_cev_activity', table_name='control_evidence_links')
    op.drop_index('ix_cev_control', table_name='control_evidence_links')
    op.drop_index('ix_cev_tenant_id', table_name='control_evidence_links')
    op.drop_table('control_evidence_links')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS effectivenesslevel")
    op.execute("DROP TYPE IF EXISTS evidencestrength")
    op.execute("DROP TYPE IF EXISTS linktype")
    op.execute("DROP TYPE IF EXISTS controlframework")
    op.execute("DROP TYPE IF EXISTS activitytype")
