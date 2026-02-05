"""add_attack_path_tables

Create tables for Attack Path Analysis module.
Enables visualization and analysis of potential attack routes through infrastructure.

Tables:
- attack_graphs (Computed attack graphs with nodes/edges)
- attack_paths (Individual paths from entry to crown jewel)
- attack_path_simulations (What-if simulations)
- crown_jewels (Critical target assets)
- entry_points (Potential attacker entry points)

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-02-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, Sequence[str], None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add Attack Path Analysis tables."""

    # First, extend the assets table with network topology fields
    op.add_column('assets', sa.Column('network_zone', sa.String(length=100), nullable=True))
    op.add_column('assets', sa.Column('trust_level', sa.Enum('UNTRUSTED', 'LOW', 'MEDIUM', 'HIGH', 'TRUSTED', name='asset_trust_level_enum'), nullable=True, server_default='MEDIUM'))
    op.add_column('assets', sa.Column('inbound_connections', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('assets', sa.Column('outbound_connections', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('assets', sa.Column('admin_access_from', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('assets', sa.Column('user_access_from', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('assets', sa.Column('service_accounts', sa.JSON(), nullable=True, server_default='[]'))
    op.create_index(op.f('ix_assets_network_zone'), 'assets', ['network_zone'], unique=False)

    # Create attack_graphs table
    op.create_table('attack_graphs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scope_type', sa.Enum('FULL', 'ZONE', 'CUSTOM', name='graph_scope_type_enum'), nullable=False, server_default='FULL'),
        sa.Column('scope_filter', sa.JSON(), nullable=True),
        sa.Column('nodes', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('edges', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('total_nodes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_edges', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('entry_points_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('crown_jewels_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('computed_at', sa.DateTime(), nullable=True),
        sa.Column('computation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('data_sources', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('COMPUTING', 'READY', 'STALE', 'ERROR', name='graph_status_enum'), nullable=False, server_default='COMPUTING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('last_cmdb_sync', sa.DateTime(), nullable=True),
        sa.Column('last_vuln_sync', sa.DateTime(), nullable=True),
        sa.Column('is_stale', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attack_graphs_tenant_id'), 'attack_graphs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_attack_graphs_status'), 'attack_graphs', ['status'], unique=False)
    op.create_index(op.f('ix_attack_graphs_is_stale'), 'attack_graphs', ['is_stale'], unique=False)

    # Create attack_paths table
    op.create_table('attack_paths',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('graph_id', sa.String(length=36), nullable=False),
        sa.Column('path_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('entry_point_id', sa.String(length=36), nullable=False),
        sa.Column('entry_point_name', sa.String(length=255), nullable=False),
        sa.Column('entry_point_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('target_name', sa.String(length=255), nullable=False),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_criticality', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='target_criticality_enum'), nullable=False, server_default='HIGH'),
        sa.Column('path_nodes', sa.JSON(), nullable=False),
        sa.Column('path_edges', sa.JSON(), nullable=False),
        sa.Column('hop_count', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('exploitability_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('vulns_in_path', sa.JSON(), nullable=True),
        sa.Column('exploitable_vulns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chokepoints', sa.JSON(), nullable=True),
        sa.Column('alternative_paths', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('ACTIVE', 'MITIGATED', 'ACCEPTED', 'FALSE_POSITIVE', name='path_status_enum'), nullable=False, server_default='ACTIVE'),
        sa.Column('mitigated_at', sa.DateTime(), nullable=True),
        sa.Column('mitigated_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['graph_id'], ['attack_graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attack_paths_tenant_id'), 'attack_paths', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_attack_paths_graph_id'), 'attack_paths', ['graph_id'], unique=False)
    op.create_index(op.f('ix_attack_paths_risk_score'), 'attack_paths', ['risk_score'], unique=False)
    op.create_index(op.f('ix_attack_paths_status'), 'attack_paths', ['status'], unique=False)
    op.create_index(op.f('ix_attack_paths_entry_point_id'), 'attack_paths', ['entry_point_id'], unique=False)
    op.create_index(op.f('ix_attack_paths_target_id'), 'attack_paths', ['target_id'], unique=False)

    # Create attack_path_simulations table
    op.create_table('attack_path_simulations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('graph_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('simulation_type', sa.Enum('PATCH_VULNERABILITY', 'SEGMENT_NETWORK', 'REMOVE_ACCESS', 'ADD_CONTROL', 'COMPROMISE_ASSET', name='simulation_type_enum'), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('original_paths_count', sa.Integer(), nullable=True),
        sa.Column('resulting_paths_count', sa.Integer(), nullable=True),
        sa.Column('paths_eliminated', sa.Integer(), nullable=True),
        sa.Column('risk_reduction_percent', sa.Float(), nullable=True),
        sa.Column('affected_paths', sa.JSON(), nullable=True),
        sa.Column('new_risk_scores', sa.JSON(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('cost_estimate', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'ERROR', name='simulation_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('computed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['graph_id'], ['attack_graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attack_path_simulations_tenant_id'), 'attack_path_simulations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_attack_path_simulations_graph_id'), 'attack_path_simulations', ['graph_id'], unique=False)
    op.create_index(op.f('ix_attack_path_simulations_status'), 'attack_path_simulations', ['status'], unique=False)

    # Create crown_jewels table
    op.create_table('crown_jewels',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('asset_id', sa.String(length=36), nullable=False),
        sa.Column('jewel_type', sa.Enum('DATA', 'SYSTEM', 'CREDENTIAL', 'NETWORK', 'IDENTITY', name='jewel_type_enum'), nullable=False),
        sa.Column('business_impact', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', name='business_impact_enum'), nullable=False, server_default='HIGH'),
        sa.Column('data_classification', sa.Enum('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', name='data_classification_enum'), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('business_owner', sa.String(length=255), nullable=False),
        sa.Column('data_types', sa.JSON(), nullable=True),
        sa.Column('compliance_scope', sa.JSON(), nullable=True),
        sa.Column('estimated_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crown_jewels_tenant_id'), 'crown_jewels', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_crown_jewels_asset_id'), 'crown_jewels', ['asset_id'], unique=False)
    op.create_index(op.f('ix_crown_jewels_jewel_type'), 'crown_jewels', ['jewel_type'], unique=False)
    op.create_index(op.f('ix_crown_jewels_business_impact'), 'crown_jewels', ['business_impact'], unique=False)
    op.create_index(op.f('ix_crown_jewels_is_active'), 'crown_jewels', ['is_active'], unique=False)

    # Create entry_points table
    op.create_table('entry_points',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('asset_id', sa.String(length=36), nullable=False),
        sa.Column('entry_type', sa.Enum('INTERNET_FACING', 'VPN_ENDPOINT', 'EMAIL_GATEWAY', 'REMOTE_ACCESS', 'PARTNER_CONNECTION', 'PHYSICAL_ACCESS', 'SUPPLY_CHAIN', name='entry_type_enum'), nullable=False),
        sa.Column('exposure_level', sa.Enum('PUBLIC', 'SEMI_PUBLIC', 'INTERNAL', name='exposure_level_enum'), nullable=False, server_default='PUBLIC'),
        sa.Column('protocols_exposed', sa.JSON(), nullable=True),
        sa.Column('ports_exposed', sa.JSON(), nullable=True),
        sa.Column('authentication_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('known_vulnerabilities', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('last_pentest_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entry_points_tenant_id'), 'entry_points', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_entry_points_asset_id'), 'entry_points', ['asset_id'], unique=False)
    op.create_index(op.f('ix_entry_points_entry_type'), 'entry_points', ['entry_type'], unique=False)
    op.create_index(op.f('ix_entry_points_exposure_level'), 'entry_points', ['exposure_level'], unique=False)
    op.create_index(op.f('ix_entry_points_is_active'), 'entry_points', ['is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove Attack Path Analysis tables."""

    # First drop the tables, then remove asset columns

    # Drop entry_points table
    op.drop_index(op.f('ix_entry_points_is_active'), table_name='entry_points')
    op.drop_index(op.f('ix_entry_points_exposure_level'), table_name='entry_points')
    op.drop_index(op.f('ix_entry_points_entry_type'), table_name='entry_points')
    op.drop_index(op.f('ix_entry_points_asset_id'), table_name='entry_points')
    op.drop_index(op.f('ix_entry_points_tenant_id'), table_name='entry_points')
    op.drop_table('entry_points')

    # Drop crown_jewels table
    op.drop_index(op.f('ix_crown_jewels_is_active'), table_name='crown_jewels')
    op.drop_index(op.f('ix_crown_jewels_business_impact'), table_name='crown_jewels')
    op.drop_index(op.f('ix_crown_jewels_jewel_type'), table_name='crown_jewels')
    op.drop_index(op.f('ix_crown_jewels_asset_id'), table_name='crown_jewels')
    op.drop_index(op.f('ix_crown_jewels_tenant_id'), table_name='crown_jewels')
    op.drop_table('crown_jewels')

    # Drop attack_path_simulations table
    op.drop_index(op.f('ix_attack_path_simulations_status'), table_name='attack_path_simulations')
    op.drop_index(op.f('ix_attack_path_simulations_graph_id'), table_name='attack_path_simulations')
    op.drop_index(op.f('ix_attack_path_simulations_tenant_id'), table_name='attack_path_simulations')
    op.drop_table('attack_path_simulations')

    # Drop attack_paths table
    op.drop_index(op.f('ix_attack_paths_target_id'), table_name='attack_paths')
    op.drop_index(op.f('ix_attack_paths_entry_point_id'), table_name='attack_paths')
    op.drop_index(op.f('ix_attack_paths_status'), table_name='attack_paths')
    op.drop_index(op.f('ix_attack_paths_risk_score'), table_name='attack_paths')
    op.drop_index(op.f('ix_attack_paths_graph_id'), table_name='attack_paths')
    op.drop_index(op.f('ix_attack_paths_tenant_id'), table_name='attack_paths')
    op.drop_table('attack_paths')

    # Drop attack_graphs table
    op.drop_index(op.f('ix_attack_graphs_is_stale'), table_name='attack_graphs')
    op.drop_index(op.f('ix_attack_graphs_status'), table_name='attack_graphs')
    op.drop_index(op.f('ix_attack_graphs_tenant_id'), table_name='attack_graphs')
    op.drop_table('attack_graphs')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS entry_type_enum")
    op.execute("DROP TYPE IF EXISTS exposure_level_enum")
    op.execute("DROP TYPE IF EXISTS jewel_type_enum")
    op.execute("DROP TYPE IF EXISTS business_impact_enum")
    op.execute("DROP TYPE IF EXISTS data_classification_enum")
    op.execute("DROP TYPE IF EXISTS simulation_type_enum")
    op.execute("DROP TYPE IF EXISTS simulation_status_enum")
    op.execute("DROP TYPE IF EXISTS path_status_enum")
    op.execute("DROP TYPE IF EXISTS target_criticality_enum")
    op.execute("DROP TYPE IF EXISTS graph_scope_type_enum")
    op.execute("DROP TYPE IF EXISTS graph_status_enum")

    # Remove columns from assets table
    op.drop_index(op.f('ix_assets_network_zone'), table_name='assets')
    op.drop_column('assets', 'service_accounts')
    op.drop_column('assets', 'user_access_from')
    op.drop_column('assets', 'admin_access_from')
    op.drop_column('assets', 'outbound_connections')
    op.drop_column('assets', 'inbound_connections')
    op.drop_column('assets', 'trust_level')
    op.drop_column('assets', 'network_zone')
    op.execute("DROP TYPE IF EXISTS asset_trust_level_enum")
