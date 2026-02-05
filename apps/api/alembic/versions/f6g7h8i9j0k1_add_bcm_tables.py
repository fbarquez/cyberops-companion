"""add_bcm_tables

Create tables for Business Continuity Management (BCM) module.
Based on BSI Standard 200-4 and ISO 22301.

Tables:
- bcm_processes (Business processes to protect)
- bcm_bia (Business Impact Analysis)
- bcm_risk_scenarios (Risk scenarios)
- bcm_strategies (Continuity strategies)
- bcm_emergency_plans (Emergency plans / Notfallkonzept)
- bcm_contacts (Emergency contacts)
- bcm_exercises (BC tests/exercises)
- bcm_assessments (BCM maturity assessment)

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-02-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add BCM tables."""
    # Note: SQLAlchemy automatically creates enum types when used in sa.Enum()

    # Create bcm_processes table
    op.create_table('bcm_processes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('process_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('criticality', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='bcmprocesscriticality'), nullable=False, server_default='MEDIUM'),
        sa.Column('internal_dependencies', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('external_dependencies', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('it_systems', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('key_personnel', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'UNDER_REVIEW', name='bcmprocessstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_processes_tenant_id'), 'bcm_processes', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_processes_process_id'), 'bcm_processes', ['process_id'], unique=False)
    op.create_index(op.f('ix_bcm_processes_criticality'), 'bcm_processes', ['criticality'], unique=False)

    # Create bcm_bia table
    op.create_table('bcm_bia',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('process_id', sa.String(length=36), nullable=False),
        sa.Column('rto_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('rpo_hours', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('mtpd_hours', sa.Integer(), nullable=False, server_default='72'),
        sa.Column('impact_1h', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='LOW'),
        sa.Column('impact_4h', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='LOW'),
        sa.Column('impact_8h', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='MEDIUM'),
        sa.Column('impact_24h', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='HIGH'),
        sa.Column('impact_72h', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='CRITICAL'),
        sa.Column('impact_1w', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='bcmimpactlevel'), nullable=True, server_default='CRITICAL'),
        sa.Column('financial_impact', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('operational_impact', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('reputational_impact', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('legal_impact', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('safety_impact', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('financial_justification', sa.Text(), nullable=True),
        sa.Column('operational_justification', sa.Text(), nullable=True),
        sa.Column('minimum_staff', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('minimum_workspace', sa.Text(), nullable=True),
        sa.Column('critical_equipment', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('critical_data', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('analysis_date', sa.DateTime(), nullable=False),
        sa.Column('analyst', sa.String(length=255), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'COMPLETED', 'APPROVED', 'OUTDATED', name='bcmbiastatus'), nullable=True, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['bcm_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('process_id')
    )
    op.create_index(op.f('ix_bcm_bia_tenant_id'), 'bcm_bia', ['tenant_id'], unique=False)

    # Create bcm_risk_scenarios table
    op.create_table('bcm_risk_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('scenario_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('NATURAL_DISASTER', 'TECHNICAL_FAILURE', 'HUMAN_ERROR', 'CYBER_ATTACK', 'PANDEMIC', 'SUPPLY_CHAIN', 'INFRASTRUCTURE', 'OTHER', name='bcmscenariocategory'), nullable=False, server_default='OTHER'),
        sa.Column('likelihood', sa.Enum('RARE', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'ALMOST_CERTAIN', name='bcmlikelihood'), nullable=True, server_default='POSSIBLE'),
        sa.Column('impact', sa.Enum('NEGLIGIBLE', 'MINOR', 'MODERATE', 'MAJOR', 'CATASTROPHIC', name='bcmimpact'), nullable=True, server_default='MODERATE'),
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='9'),
        sa.Column('affected_processes', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('single_points_of_failure', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('existing_controls', sa.Text(), nullable=True),
        sa.Column('control_effectiveness', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', name='bcmcontroleffectiveness'), nullable=True, server_default='MEDIUM'),
        sa.Column('status', sa.Enum('IDENTIFIED', 'ASSESSED', 'MITIGATED', 'ACCEPTED', name='bcmscenariostatus'), nullable=True, server_default='IDENTIFIED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('assessed_by', sa.String(length=36), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assessed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_risk_scenarios_tenant_id'), 'bcm_risk_scenarios', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_risk_scenarios_category'), 'bcm_risk_scenarios', ['category'], unique=False)

    # Create bcm_strategies table
    op.create_table('bcm_strategies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('process_id', sa.String(length=36), nullable=False),
        sa.Column('strategy_type', sa.Enum('DO_NOTHING', 'MANUAL_WORKAROUND', 'ALTERNATE_SITE', 'ALTERNATE_SUPPLIER', 'REDUNDANCY', 'OUTSOURCE', 'INSURANCE', name='bcmstrategytype'), nullable=False, server_default='MANUAL_WORKAROUND'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('activation_trigger', sa.Text(), nullable=False),
        sa.Column('activation_procedure', sa.Text(), nullable=False),
        sa.Column('resource_requirements', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('estimated_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('achievable_rto_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('achievable_rpo_hours', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('status', sa.Enum('PLANNED', 'IMPLEMENTED', 'TESTED', 'APPROVED', name='bcmstrategystatus'), nullable=True, server_default='PLANNED'),
        sa.Column('implementation_date', sa.Date(), nullable=True),
        sa.Column('last_test_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['bcm_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_strategies_tenant_id'), 'bcm_strategies', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_strategies_process_id'), 'bcm_strategies', ['process_id'], unique=False)

    # Create bcm_emergency_plans table
    op.create_table('bcm_emergency_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('plan_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan_type', sa.Enum('CRISIS_MANAGEMENT', 'EMERGENCY_RESPONSE', 'BUSINESS_RECOVERY', 'IT_DISASTER_RECOVERY', 'COMMUNICATION', 'EVACUATION', name='bcmplantype'), nullable=False, server_default='BUSINESS_RECOVERY'),
        sa.Column('scope_description', sa.Text(), nullable=False),
        sa.Column('affected_processes', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('affected_locations', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('activation_criteria', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('response_phases', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('procedures', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('roles_responsibilities', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('communication_tree', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('contact_list', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('resources_required', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('activation_checklist', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('recovery_checklist', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('review_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'REVIEW', 'APPROVED', 'ACTIVE', 'ARCHIVED', name='bcmplanstatus'), nullable=True, server_default='DRAFT'),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_emergency_plans_tenant_id'), 'bcm_emergency_plans', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_emergency_plans_plan_type'), 'bcm_emergency_plans', ['plan_type'], unique=False)
    op.create_index(op.f('ix_bcm_emergency_plans_status'), 'bcm_emergency_plans', ['status'], unique=False)

    # Create bcm_contacts table
    op.create_table('bcm_contacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('phone_primary', sa.String(length=50), nullable=False),
        sa.Column('phone_secondary', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('availability', sa.Enum('TWENTY_FOUR_SEVEN', 'BUSINESS_HOURS', 'ON_CALL', name='bcmcontactavailability'), nullable=True, server_default='BUSINESS_HOURS'),
        sa.Column('contact_type', sa.Enum('INTERNAL', 'EXTERNAL', 'VENDOR', 'AUTHORITY', name='bcmcontacttype'), nullable=True, server_default='INTERNAL'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_contacts_tenant_id'), 'bcm_contacts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_contacts_priority'), 'bcm_contacts', ['priority'], unique=False)

    # Create bcm_exercises table
    op.create_table('bcm_exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('exercise_type', sa.Enum('TABLETOP', 'WALKTHROUGH', 'SIMULATION', 'PARALLEL_TEST', 'FULL_INTERRUPTION', name='bcmexercisetype'), nullable=False, server_default='TABLETOP'),
        sa.Column('scenario_id', sa.String(length=36), nullable=True),
        sa.Column('plan_id', sa.String(length=36), nullable=True),
        sa.Column('objectives', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('participants', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('planned_date', sa.Date(), nullable=False),
        sa.Column('planned_duration_hours', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('actual_duration_hours', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='bcmexercisestatus'), nullable=True, server_default='PLANNED'),
        sa.Column('results_summary', sa.Text(), nullable=True),
        sa.Column('objectives_met', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('issues_identified', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('conducted_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['conducted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['bcm_emergency_plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['scenario_id'], ['bcm_risk_scenarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_exercises_tenant_id'), 'bcm_exercises', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_exercises_status'), 'bcm_exercises', ['status'], unique=False)
    op.create_index(op.f('ix_bcm_exercises_planned_date'), 'bcm_exercises', ['planned_date'], unique=False)

    # Create bcm_assessments table
    op.create_table('bcm_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PROCESS_INVENTORY', 'BIA_ANALYSIS', 'RISK_ASSESSMENT', 'STRATEGY_PLANNING', 'PLAN_DEVELOPMENT', 'TESTING', 'COMPLETED', name='bcmassessmentstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('process_coverage_score', sa.Float(), nullable=True),
        sa.Column('bia_completion_score', sa.Float(), nullable=True),
        sa.Column('strategy_coverage_score', sa.Float(), nullable=True),
        sa.Column('plan_coverage_score', sa.Float(), nullable=True),
        sa.Column('test_coverage_score', sa.Float(), nullable=True),
        sa.Column('total_processes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_processes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processes_with_bia', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processes_with_strategy', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processes_with_plan', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('plans_tested_this_year', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bcm_assessments_tenant_id'), 'bcm_assessments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bcm_assessments_status'), 'bcm_assessments', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove BCM tables."""
    # Drop tables in reverse order
    op.drop_index(op.f('ix_bcm_assessments_status'), table_name='bcm_assessments')
    op.drop_index(op.f('ix_bcm_assessments_tenant_id'), table_name='bcm_assessments')
    op.drop_table('bcm_assessments')

    op.drop_index(op.f('ix_bcm_exercises_planned_date'), table_name='bcm_exercises')
    op.drop_index(op.f('ix_bcm_exercises_status'), table_name='bcm_exercises')
    op.drop_index(op.f('ix_bcm_exercises_tenant_id'), table_name='bcm_exercises')
    op.drop_table('bcm_exercises')

    op.drop_index(op.f('ix_bcm_contacts_priority'), table_name='bcm_contacts')
    op.drop_index(op.f('ix_bcm_contacts_tenant_id'), table_name='bcm_contacts')
    op.drop_table('bcm_contacts')

    op.drop_index(op.f('ix_bcm_emergency_plans_status'), table_name='bcm_emergency_plans')
    op.drop_index(op.f('ix_bcm_emergency_plans_plan_type'), table_name='bcm_emergency_plans')
    op.drop_index(op.f('ix_bcm_emergency_plans_tenant_id'), table_name='bcm_emergency_plans')
    op.drop_table('bcm_emergency_plans')

    op.drop_index(op.f('ix_bcm_strategies_process_id'), table_name='bcm_strategies')
    op.drop_index(op.f('ix_bcm_strategies_tenant_id'), table_name='bcm_strategies')
    op.drop_table('bcm_strategies')

    op.drop_index(op.f('ix_bcm_risk_scenarios_category'), table_name='bcm_risk_scenarios')
    op.drop_index(op.f('ix_bcm_risk_scenarios_tenant_id'), table_name='bcm_risk_scenarios')
    op.drop_table('bcm_risk_scenarios')

    op.drop_index(op.f('ix_bcm_bia_tenant_id'), table_name='bcm_bia')
    op.drop_table('bcm_bia')

    op.drop_index(op.f('ix_bcm_processes_criticality'), table_name='bcm_processes')
    op.drop_index(op.f('ix_bcm_processes_process_id'), table_name='bcm_processes')
    op.drop_index(op.f('ix_bcm_processes_tenant_id'), table_name='bcm_processes')
    op.drop_table('bcm_processes')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS bcmassessmentstatus")
    op.execute("DROP TYPE IF EXISTS bcmexercisestatus")
    op.execute("DROP TYPE IF EXISTS bcmexercisetype")
    op.execute("DROP TYPE IF EXISTS bcmcontactavailability")
    op.execute("DROP TYPE IF EXISTS bcmcontacttype")
    op.execute("DROP TYPE IF EXISTS bcmplanstatus")
    op.execute("DROP TYPE IF EXISTS bcmplantype")
    op.execute("DROP TYPE IF EXISTS bcmstrategystatus")
    op.execute("DROP TYPE IF EXISTS bcmstrategytype")
    op.execute("DROP TYPE IF EXISTS bcmscenariostatus")
    op.execute("DROP TYPE IF EXISTS bcmcontroleffectiveness")
    op.execute("DROP TYPE IF EXISTS bcmimpact")
    op.execute("DROP TYPE IF EXISTS bcmlikelihood")
    op.execute("DROP TYPE IF EXISTS bcmscenariocategory")
    op.execute("DROP TYPE IF EXISTS bcmbiastatus")
    op.execute("DROP TYPE IF EXISTS bcmimpactlevel")
    op.execute("DROP TYPE IF EXISTS bcmprocessstatus")
    op.execute("DROP TYPE IF EXISTS bcmprocesscriticality")
