"""Phase tracking models aligned with NIST SP 800-61."""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Text, ForeignKey, Integer, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class IRPhase(str, enum.Enum):
    """NIST SP 800-61 aligned incident response phases."""
    DETECTION = "detection"
    ANALYSIS = "analysis"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    POST_INCIDENT = "post_incident"


class PhaseStatus(str, enum.Enum):
    """Status of a phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PhaseProgress(Base):
    """Tracks progress through a phase for an incident."""
    __tablename__ = "phase_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    phase: Mapped[IRPhase] = mapped_column(Enum(IRPhase), index=True)
    status: Mapped[PhaseStatus] = mapped_column(
        Enum(PhaseStatus), default=PhaseStatus.NOT_STARTED
    )

    # Progress tracking
    checklist_total: Mapped[int] = mapped_column(Integer, default=0)
    checklist_completed: Mapped[int] = mapped_column(Integer, default=0)
    mandatory_total: Mapped[int] = mapped_column(Integer, default=0)
    mandatory_completed: Mapped[int] = mapped_column(Integer, default=0)

    # Decisions
    decisions_required: Mapped[int] = mapped_column(Integer, default=0)
    decisions_made: Mapped[int] = mapped_column(Integer, default=0)

    # Evidence
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Duration in seconds (calculated)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PhaseDefinition(Base):
    """Phase definition with guidance and objectives."""
    __tablename__ = "phase_definitions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    phase: Mapped[IRPhase] = mapped_column(Enum(IRPhase), unique=True, index=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(100))
    name_de: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    description_de: Mapped[str] = mapped_column(Text)

    # Objectives (JSON array)
    objectives: Mapped[List[str]] = mapped_column(JSON, default=list)
    objectives_de: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Guidance
    key_questions: Mapped[List[str]] = mapped_column(JSON, default=list)
    key_questions_de: Mapped[List[str]] = mapped_column(JSON, default=list)
    critical_reminders: Mapped[List[str]] = mapped_column(JSON, default=list)
    critical_reminders_de: Mapped[List[str]] = mapped_column(JSON, default=list)
    common_mistakes: Mapped[List[str]] = mapped_column(JSON, default=list)
    common_mistakes_de: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Forensic considerations
    forensic_considerations: Mapped[List[str]] = mapped_column(JSON, default=list)
    forensic_considerations_de: Mapped[List[str]] = mapped_column(JSON, default=list)

    # UI
    icon: Mapped[str] = mapped_column(String(50), default="circle")
    color: Mapped[str] = mapped_column(String(50), default="gray")
    order: Mapped[int] = mapped_column(Integer, default=0)
