"""
Document & Policy Management Models.

Database models for Document Management, Versioning, Approvals,
Acknowledgments, and Review Cycles.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Date, Text, Integer, Boolean,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base
from src.models.mixins import TenantMixin


class DocumentCategory(str, enum.Enum):
    """Document category classification."""
    POLICY = "policy"              # High-level policies
    PROCEDURE = "procedure"         # Operational procedures
    STANDARD = "standard"           # Technical standards
    GUIDELINE = "guideline"         # Guidelines and recommendations
    FORM = "form"                   # Forms and templates
    RECORD = "record"               # Records
    MANUAL = "manual"               # Manuals
    INSTRUCTION = "instruction"     # Work instructions


class DocumentStatus(str, enum.Enum):
    """Document lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    UNDER_REVISION = "under_revision"
    ARCHIVED = "archived"


class VersionType(str, enum.Enum):
    """Version increment type."""
    MAJOR = "major"    # Breaking changes, complete rewrite
    MINOR = "minor"    # New sections, significant updates
    PATCH = "patch"    # Typos, minor corrections


class ApprovalStatus(str, enum.Enum):
    """Approval workflow status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalType(str, enum.Enum):
    """Approval workflow type."""
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"      # All at once


class AcknowledgmentStatus(str, enum.Enum):
    """Acknowledgment status."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    DECLINED = "declined"
    EXPIRED = "expired"


class ReviewOutcome(str, enum.Enum):
    """Document review outcome."""
    NO_CHANGES = "no_changes"          # Still valid
    MINOR_UPDATE = "minor_update"      # Small changes needed
    MAJOR_REVISION = "major_revision"  # Significant rewrite needed
    RETIRE = "retire"                  # Should be archived


class Document(TenantMixin, Base):
    """Main document record."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    document_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g., POL-001
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    category = mapped_column(SQLEnum(DocumentCategory), nullable=False, index=True)
    status = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT, index=True)

    # Current version
    current_version: Mapped[str] = mapped_column(String(20), default="0.1")

    # Content (markdown or reference to attachment)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Inline content (markdown)
    attachment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("attachments.id"), nullable=True)

    # Ownership
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Review cycle
    review_frequency_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., 365 for annual
    last_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Compliance mapping
    frameworks = mapped_column(JSON, default=[])  # ["iso27001", "nis2", "bsi"]
    control_references = mapped_column(JSON, default=[])  # ["A.5.1", "A.5.2"]

    # Acknowledgment settings
    requires_acknowledgment: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledgment_due_days: Mapped[int] = mapped_column(Integer, default=14)

    # Approval workflow settings
    approval_type = mapped_column(SQLEnum(ApprovalType), default=ApprovalType.SEQUENTIAL)

    # Publishing
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Metadata
    tags = mapped_column(JSON, default=[])
    custom_metadata = mapped_column(JSON, default={})

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    approvals = relationship("DocumentApproval", back_populates="document", cascade="all, delete-orphan")
    acknowledgments = relationship("DocumentAcknowledgment", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("DocumentReview", back_populates="document", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])


class DocumentVersion(TenantMixin, Base):
    """Document version history."""
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)

    # Version info
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)  # "1.0", "1.1", "2.0"
    version_type = mapped_column(SQLEnum(VersionType), default=VersionType.MINOR)

    # Content snapshot
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("attachments.id"), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 for integrity

    # Change tracking
    change_summary: Mapped[str] = mapped_column(String(500), nullable=False)  # What changed
    change_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="versions")


class DocumentApproval(TenantMixin, Base):
    """Document approval workflow records."""
    __tablename__ = "document_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("document_versions.id"), nullable=True)

    # Approver
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approval_order: Mapped[int] = mapped_column(Integer, default=1)  # For sequential approvals

    # Status
    status = mapped_column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)

    # Decision
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reminder tracking
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])


class DocumentAcknowledgment(TenantMixin, Base):
    """Document acknowledgment/read confirmation records."""
    __tablename__ = "document_acknowledgments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("document_versions.id"), nullable=True)

    # User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Status
    status = mapped_column(SQLEnum(AcknowledgmentStatus), default=AcknowledgmentStatus.PENDING, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Confirmation details
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # For audit
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Decline reason (if declined)
    decline_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reminders
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="acknowledgments")
    user = relationship("User", foreign_keys=[user_id])


class DocumentReview(TenantMixin, Base):
    """Document periodic review records."""
    __tablename__ = "document_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)

    # Review info
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    outcome = mapped_column(SQLEnum(ReviewOutcome), nullable=False)

    # Notes
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items = mapped_column(JSON, default=[])  # List of action items

    # Next review
    next_review_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
