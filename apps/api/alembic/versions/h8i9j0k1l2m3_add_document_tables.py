"""add_document_tables

Create tables for Document & Policy Management module.
Enables document lifecycle management, versioning, approval workflows,
acknowledgments, and periodic reviews for ISMS compliance.

Tables:
- documents (Main document records with metadata)
- document_versions (Version history with content snapshots)
- document_approvals (Approval workflow tracking)
- document_acknowledgments (Read confirmation tracking)
- document_reviews (Periodic review history)

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-05 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, Sequence[str], None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add Document Management tables."""

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('POLICY', 'PROCEDURE', 'STANDARD', 'GUIDELINE', 'FORM', 'RECORD', 'MANUAL', 'INSTRUCTION', name='documentcategory'), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED', 'UNDER_REVISION', 'ARCHIVED', name='documentstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('current_version', sa.String(length=20), nullable=False, server_default='0.1'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('attachment_id', sa.String(length=36), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('review_frequency_days', sa.Integer(), nullable=True),
        sa.Column('last_review_date', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('frameworks', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('control_references', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('requires_acknowledgment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledgment_due_days', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('approval_type', sa.Enum('SEQUENTIAL', 'PARALLEL', name='approvaltype'), nullable=True, server_default='SEQUENTIAL'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by', sa.String(length=36), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('custom_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['published_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index(op.f('ix_documents_tenant_id'), 'documents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_documents_document_id'), 'documents', ['document_id'], unique=False)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)
    op.create_index(op.f('ix_documents_category'), 'documents', ['category'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_index(op.f('ix_documents_owner_id'), 'documents', ['owner_id'], unique=False)

    # Create document_versions table
    op.create_table('document_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('version_number', sa.String(length=20), nullable=False),
        sa.Column('version_type', sa.Enum('MAJOR', 'MINOR', 'PATCH', name='versiontype'), nullable=True, server_default='MINOR'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('attachment_id', sa.String(length=36), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('change_summary', sa.String(length=500), nullable=False),
        sa.Column('change_details', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_tenant_id'), 'document_versions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_is_current'), 'document_versions', ['is_current'], unique=False)

    # Create document_approvals table
    op.create_table('document_approvals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('version_id', sa.String(length=36), nullable=True),
        sa.Column('approver_id', sa.String(length=36), nullable=False),
        sa.Column('approval_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CHANGES_REQUESTED', name='approvalstatus'), nullable=False, server_default='PENDING'),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('reminder_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_approvals_tenant_id'), 'document_approvals', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_approvals_document_id'), 'document_approvals', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_approvals_status'), 'document_approvals', ['status'], unique=False)
    op.create_index(op.f('ix_document_approvals_approver_id'), 'document_approvals', ['approver_id'], unique=False)

    # Create document_acknowledgments table
    op.create_table('document_acknowledgments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('version_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACKNOWLEDGED', 'DECLINED', 'EXPIRED', name='acknowledgmentstatus'), nullable=False, server_default='PENDING'),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('decline_reason', sa.Text(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('reminder_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_acknowledgments_tenant_id'), 'document_acknowledgments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_acknowledgments_document_id'), 'document_acknowledgments', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_acknowledgments_user_id'), 'document_acknowledgments', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_acknowledgments_status'), 'document_acknowledgments', ['status'], unique=False)
    op.create_index(op.f('ix_document_acknowledgments_due_date'), 'document_acknowledgments', ['due_date'], unique=False)

    # Create document_reviews table
    op.create_table('document_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('review_date', sa.Date(), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=False),
        sa.Column('outcome', sa.Enum('NO_CHANGES', 'MINOR_UPDATE', 'MAJOR_REVISION', 'RETIRE', name='reviewoutcome'), nullable=False),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('next_review_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reviews_tenant_id'), 'document_reviews', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_reviews_document_id'), 'document_reviews', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_reviews_reviewer_id'), 'document_reviews', ['reviewer_id'], unique=False)
    op.create_index(op.f('ix_document_reviews_review_date'), 'document_reviews', ['review_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove Document Management tables."""

    # Drop document_reviews
    op.drop_index(op.f('ix_document_reviews_review_date'), table_name='document_reviews')
    op.drop_index(op.f('ix_document_reviews_reviewer_id'), table_name='document_reviews')
    op.drop_index(op.f('ix_document_reviews_document_id'), table_name='document_reviews')
    op.drop_index(op.f('ix_document_reviews_tenant_id'), table_name='document_reviews')
    op.drop_table('document_reviews')

    # Drop document_acknowledgments
    op.drop_index(op.f('ix_document_acknowledgments_due_date'), table_name='document_acknowledgments')
    op.drop_index(op.f('ix_document_acknowledgments_status'), table_name='document_acknowledgments')
    op.drop_index(op.f('ix_document_acknowledgments_user_id'), table_name='document_acknowledgments')
    op.drop_index(op.f('ix_document_acknowledgments_document_id'), table_name='document_acknowledgments')
    op.drop_index(op.f('ix_document_acknowledgments_tenant_id'), table_name='document_acknowledgments')
    op.drop_table('document_acknowledgments')

    # Drop document_approvals
    op.drop_index(op.f('ix_document_approvals_approver_id'), table_name='document_approvals')
    op.drop_index(op.f('ix_document_approvals_status'), table_name='document_approvals')
    op.drop_index(op.f('ix_document_approvals_document_id'), table_name='document_approvals')
    op.drop_index(op.f('ix_document_approvals_tenant_id'), table_name='document_approvals')
    op.drop_table('document_approvals')

    # Drop document_versions
    op.drop_index(op.f('ix_document_versions_is_current'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_tenant_id'), table_name='document_versions')
    op.drop_table('document_versions')

    # Drop documents
    op.drop_index(op.f('ix_documents_owner_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_category'), table_name='documents')
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_tenant_id'), table_name='documents')
    op.drop_table('documents')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS reviewoutcome")
    op.execute("DROP TYPE IF EXISTS acknowledgmentstatus")
    op.execute("DROP TYPE IF EXISTS approvalstatus")
    op.execute("DROP TYPE IF EXISTS versiontype")
    op.execute("DROP TYPE IF EXISTS approvaltype")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS documentcategory")
