"""Checklist model for phase-based task tracking."""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Text, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class ChecklistStatus(str, enum.Enum):
    """Status of a checklist item."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


class ChecklistItem(Base):
    """Individual checklist item for an incident phase."""
    __tablename__ = "checklist_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )

    # Item definition
    item_id: Mapped[str] = mapped_column(String(100))  # Template item ID
    phase: Mapped[str] = mapped_column(String(50), index=True)
    text: Mapped[str] = mapped_column(Text)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    forensic_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Dependencies (JSON arrays of item_ids)
    depends_on: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    blocks: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # State
    status: Mapped[ChecklistStatus] = mapped_column(
        Enum(ChecklistStatus), default=ChecklistStatus.NOT_STARTED
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skip_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ChecklistTemplate(Base):
    """Template for checklist items per phase."""
    __tablename__ = "checklist_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    item_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phase: Mapped[str] = mapped_column(String(50), index=True)
    text: Mapped[str] = mapped_column(Text)
    text_de: Mapped[str] = mapped_column(Text)  # German translation
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    help_text_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warning_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    forensic_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    depends_on: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    blocks: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
