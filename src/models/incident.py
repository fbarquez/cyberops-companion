"""
Incident data model.

Represents a security incident being tracked through the IR process.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class IncidentStatus(str, Enum):
    """Incident lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Incident severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class DetectionSource(str, Enum):
    """How the incident was detected."""
    USER_REPORT = "user_report"
    EDR_ALERT = "edr_alert"
    SIEM_ALERT = "siem_alert"
    ANOMALY_DETECTION = "anomaly_detection"
    EXTERNAL_NOTIFICATION = "external_notification"
    SCHEDULED_SCAN = "scheduled_scan"
    OTHER = "other"


class AffectedSystem(BaseModel):
    """Information about an affected system."""
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    department: Optional[str] = None
    criticality: Optional[str] = None
    notes: Optional[str] = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Incident(BaseModel):
    """
    Core incident model.

    Represents a security incident being managed through the CyberOps Companion.
    All timestamps are stored in UTC ISO 8601 format.
    """

    # Identification
    id: str = Field(default_factory=lambda: f"INC-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}")

    # Classification
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    status: IncidentStatus = Field(default=IncidentStatus.DRAFT)

    # Detection
    detection_source: DetectionSource = Field(default=DetectionSource.OTHER)
    initial_indicator: str = Field(default="")

    # Systems
    affected_systems: List[AffectedSystem] = Field(default_factory=list)

    # Personnel
    analyst_name: str = Field(default="")
    analyst_email: Optional[str] = None

    # Timestamps (UTC)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detected_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    eradicated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Phase tracking
    current_phase: str = Field(default="detection")
    phase_history: List[dict] = Field(default_factory=list)

    # Simulation mode
    is_simulation: bool = Field(default=False)
    simulation_scenario: Optional[str] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    external_references: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def add_affected_system(self, system: AffectedSystem) -> None:
        """Add an affected system to the incident."""
        self.affected_systems.append(system)
        self.updated_at = datetime.now(timezone.utc)

    def transition_phase(self, new_phase: str, reason: str = "") -> None:
        """Record a phase transition."""
        self.phase_history.append({
            "from_phase": self.current_phase,
            "to_phase": new_phase,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        })
        self.current_phase = new_phase
        self.updated_at = datetime.now(timezone.utc)

    def update_status(self, new_status: IncidentStatus) -> None:
        """Update incident status with timestamp tracking."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        # Set phase-specific timestamps
        if new_status == IncidentStatus.CONTAINED:
            self.contained_at = datetime.now(timezone.utc)
        elif new_status == IncidentStatus.ERADICATED:
            self.eradicated_at = datetime.now(timezone.utc)
        elif new_status == IncidentStatus.CLOSED:
            self.closed_at = datetime.now(timezone.utc)

    def get_duration(self) -> Optional[float]:
        """Get incident duration in seconds (if closed)."""
        if self.closed_at:
            return (self.closed_at - self.created_at).total_seconds()
        return None

    def to_summary(self) -> dict:
        """Generate a summary for display purposes."""
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "current_phase": self.current_phase,
            "affected_systems_count": len(self.affected_systems),
            "created_at": self.created_at.isoformat(),
            "is_simulation": self.is_simulation,
        }
