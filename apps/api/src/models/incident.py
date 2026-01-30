"""Incident model - core entity for incident tracking."""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class IncidentStatus(str, enum.Enum):
    """Incident lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


class IncidentSeverity(str, enum.Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class DetectionSource(str, enum.Enum):
    """How the incident was detected."""
    USER_REPORT = "user_report"
    EDR_ALERT = "edr_alert"
    SIEM_ALERT = "siem_alert"
    ANOMALY_DETECTION = "anomaly_detection"
    EXTERNAL_NOTIFICATION = "external_notification"
    SCHEDULED_SCAN = "scheduled_scan"
    OTHER = "other"


class AffectedSystem(Base):
    """Systems affected by an incident."""
    __tablename__ = "affected_systems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    hostname: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    os_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    criticality: Mapped[str] = mapped_column(String(50), default="medium")
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Incident(Base):
    """Main incident model."""
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity), default=IncidentSeverity.MEDIUM
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.DRAFT
    )

    # Detection information
    detection_source: Mapped[Optional[DetectionSource]] = mapped_column(
        Enum(DetectionSource), nullable=True
    )
    initial_indicator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Phase tracking
    current_phase: Mapped[str] = mapped_column(String(50), default="detection")
    phase_history: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Personnel
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    analyst_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    analyst_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps (all UTC)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    contained_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    eradicated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    affected_systems: Mapped[List["AffectedSystem"]] = relationship(
        "AffectedSystem", backref="incident", lazy="selectin",
        cascade="all, delete-orphan"
    )
    iocs = relationship("IOC", back_populates="incident", lazy="selectin")
