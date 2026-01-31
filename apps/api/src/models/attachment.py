"""
Attachment model for file uploads.
Supports multiple entity types: incidents, vulnerabilities, cases, etc.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from src.db.database import Base
from src.models.base import generate_uuid


class AttachmentEntityType(str, enum.Enum):
    """Types of entities that can have attachments."""
    INCIDENT = "incident"
    VULNERABILITY = "vulnerability"
    CASE = "case"
    ALERT = "alert"
    RISK = "risk"
    VENDOR = "vendor"
    ASSET = "asset"
    EVIDENCE = "evidence"
    REPORT = "report"
    GENERAL = "general"


class AttachmentCategory(str, enum.Enum):
    """Categories for organizing attachments."""
    EVIDENCE = "evidence"
    SCREENSHOT = "screenshot"
    LOG_FILE = "log_file"
    DOCUMENT = "document"
    REPORT = "report"
    PCAP = "pcap"
    MEMORY_DUMP = "memory_dump"
    MALWARE_SAMPLE = "malware_sample"
    OTHER = "other"


class Attachment(Base):
    """
    Attachment model for storing file metadata.

    Actual files are stored on the configured storage backend (local/S3).
    This model tracks metadata and provides entity associations.
    """
    __tablename__ = "attachments"

    # Primary key
    id = Column(String, primary_key=True, default=generate_uuid)

    # File metadata
    filename = Column(String(255), nullable=False)  # Original filename
    storage_path = Column(String(512), nullable=False)  # Path in storage backend
    content_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash

    # Classification
    category = Column(
        Enum(AttachmentCategory),
        default=AttachmentCategory.OTHER,
        nullable=False
    )
    description = Column(Text, nullable=True)

    # Entity association (polymorphic)
    entity_type = Column(Enum(AttachmentEntityType), nullable=False)
    entity_id = Column(String, nullable=False)

    # Ownership and tracking
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Soft delete support
    is_deleted = Column(Integer, default=0)  # 0 = active, 1 = deleted
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Access tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])
    deleter = relationship("User", foreign_keys=[deleted_by])

    # Indexes for common queries
    __table_args__ = (
        Index("ix_attachments_entity", "entity_type", "entity_id"),
        Index("ix_attachments_uploaded_by", "uploaded_by"),
        Index("ix_attachments_category", "category"),
        Index("ix_attachments_file_hash", "file_hash"),
    )

    def __repr__(self):
        return f"<Attachment {self.filename} ({self.entity_type.value}:{self.entity_id})>"

    @property
    def file_size_human(self) -> str:
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def extension(self) -> str:
        """Return file extension."""
        if '.' in self.filename:
            return self.filename.rsplit('.', 1)[1].lower()
        return ""

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "file_size_human": self.file_size_human,
            "file_hash": self.file_hash,
            "category": self.category.value,
            "description": self.description,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "download_count": self.download_count,
        }
