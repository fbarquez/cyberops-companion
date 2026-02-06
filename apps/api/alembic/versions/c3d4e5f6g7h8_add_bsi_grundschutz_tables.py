"""add_bsi_grundschutz_tables

Create BSI IT-Grundschutz tables for the 111 Bausteine catalog,
Anforderungen (requirements), and tenant-scoped compliance tracking.

Revision ID: c3d4e5f6g7h8
Revises: i9j0k1l2m3n4
Create Date: 2026-02-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add BSI IT-Grundschutz tables."""

    # Create BSI Kategorie enum
    bsi_kategorie = sa.Enum(
        'ISMS', 'ORP', 'CON', 'OPS', 'DER', 'APP', 'SYS', 'NET', 'INF', 'IND',
        name='bsikategorie'
    )

    # Create BSI Anforderung Typ enum
    bsi_anforderung_typ = sa.Enum('MUSS', 'SOLLTE', 'KANN', name='bsianforderungtyp')

    # Create BSI Schutzbedarf enum
    bsi_schutzbedarf = sa.Enum('basis', 'standard', 'hoch', name='bsischutzbedarf')

    # Create BSI Compliance Status enum
    bsi_compliance_status = sa.Enum(
        'not_evaluated', 'compliant', 'partial', 'gap', 'not_applicable',
        name='bsicompliancestatusenum'
    )

    # Create bsi_bausteine table (111 modules)
    op.create_table('bsi_bausteine',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('baustein_id', sa.String(length=20), nullable=False),
        sa.Column('kategorie', bsi_kategorie, nullable=False),
        sa.Column('titel', sa.String(length=500), nullable=False),
        sa.Column('title_en', sa.String(length=500), nullable=True),
        sa.Column('beschreibung', sa.Text(), nullable=True),
        sa.Column('zielsetzung', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='2023'),
        sa.Column('edition', sa.String(length=50), nullable=True),
        sa.Column('ir_phases', sa.JSON(), nullable=True),
        sa.Column('cross_references', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bsi_bausteine_baustein_id'), 'bsi_bausteine', ['baustein_id'], unique=True)
    op.create_index(op.f('ix_bsi_bausteine_kategorie'), 'bsi_bausteine', ['kategorie'], unique=False)
    op.create_index('ix_bsi_baustein_kategorie_order', 'bsi_bausteine', ['kategorie', 'sort_order'], unique=False)

    # Create bsi_anforderungen table (~1000+ requirements)
    op.create_table('bsi_anforderungen',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('baustein_fk', sa.String(length=36), nullable=False),
        sa.Column('anforderung_id', sa.String(length=30), nullable=False),
        sa.Column('typ', bsi_anforderung_typ, nullable=False),
        sa.Column('schutzbedarf', bsi_schutzbedarf, nullable=False),
        sa.Column('titel', sa.String(length=500), nullable=False),
        sa.Column('title_en', sa.String(length=500), nullable=True),
        sa.Column('beschreibung', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('umsetzungshinweise', sa.Text(), nullable=True),
        sa.Column('cross_references', sa.JSON(), nullable=True),
        sa.Column('aufwandsstufe', sa.Integer(), nullable=True),
        sa.Column('oscal_id', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['baustein_fk'], ['bsi_bausteine.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bsi_anforderungen_anforderung_id'), 'bsi_anforderungen', ['anforderung_id'], unique=True)
    op.create_index(op.f('ix_bsi_anforderungen_baustein_fk'), 'bsi_anforderungen', ['baustein_fk'], unique=False)
    op.create_index('ix_bsi_anforderung_baustein_typ', 'bsi_anforderungen', ['baustein_fk', 'typ'], unique=False)
    op.create_index('ix_bsi_anforderung_schutzbedarf', 'bsi_anforderungen', ['schutzbedarf'], unique=False)

    # Create bsi_compliance_status table (tenant-scoped)
    op.create_table('bsi_compliance_status',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('anforderung_fk', sa.String(length=36), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('status', bsi_compliance_status, nullable=False, server_default='not_evaluated'),
        sa.Column('evidence_provided', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('gap_description', sa.Text(), nullable=True),
        sa.Column('remediation_plan', sa.Text(), nullable=True),
        sa.Column('assessed_by', sa.String(length=36), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['anforderung_fk'], ['bsi_anforderungen.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'anforderung_fk', 'incident_id', name='uq_bsi_compliance_tenant_anforderung_incident')
    )
    op.create_index(op.f('ix_bsi_compliance_status_tenant_id'), 'bsi_compliance_status', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bsi_compliance_status_anforderung_fk'), 'bsi_compliance_status', ['anforderung_fk'], unique=False)
    op.create_index(op.f('ix_bsi_compliance_status_incident_id'), 'bsi_compliance_status', ['incident_id'], unique=False)
    op.create_index('ix_bsi_compliance_tenant_status', 'bsi_compliance_status', ['tenant_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove BSI IT-Grundschutz tables."""

    # Drop bsi_compliance_status table
    op.drop_index('ix_bsi_compliance_tenant_status', table_name='bsi_compliance_status')
    op.drop_index(op.f('ix_bsi_compliance_status_incident_id'), table_name='bsi_compliance_status')
    op.drop_index(op.f('ix_bsi_compliance_status_anforderung_fk'), table_name='bsi_compliance_status')
    op.drop_index(op.f('ix_bsi_compliance_status_tenant_id'), table_name='bsi_compliance_status')
    op.drop_table('bsi_compliance_status')

    # Drop bsi_anforderungen table
    op.drop_index('ix_bsi_anforderung_schutzbedarf', table_name='bsi_anforderungen')
    op.drop_index('ix_bsi_anforderung_baustein_typ', table_name='bsi_anforderungen')
    op.drop_index(op.f('ix_bsi_anforderungen_baustein_fk'), table_name='bsi_anforderungen')
    op.drop_index(op.f('ix_bsi_anforderungen_anforderung_id'), table_name='bsi_anforderungen')
    op.drop_table('bsi_anforderungen')

    # Drop bsi_bausteine table
    op.drop_index('ix_bsi_baustein_kategorie_order', table_name='bsi_bausteine')
    op.drop_index(op.f('ix_bsi_bausteine_kategorie'), table_name='bsi_bausteine')
    op.drop_index(op.f('ix_bsi_bausteine_baustein_id'), table_name='bsi_bausteine')
    op.drop_table('bsi_bausteine')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS bsicompliancestatusenum")
    op.execute("DROP TYPE IF EXISTS bsischutzbedarf")
    op.execute("DROP TYPE IF EXISTS bsianforderungtyp")
    op.execute("DROP TYPE IF EXISTS bsikategorie")
