"""
IR Phase data model.

Defines the NIST-aligned incident response phases.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class IRPhase(str, Enum):
    """NIST SP 800-61 aligned IR phases."""
    DETECTION = "detection"
    ANALYSIS = "analysis"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    POST_INCIDENT = "post_incident"


class PhaseStatus(str, Enum):
    """Status of a phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Phase ordering for progression
PHASE_ORDER = [
    IRPhase.DETECTION,
    IRPhase.ANALYSIS,
    IRPhase.CONTAINMENT,
    IRPhase.ERADICATION,
    IRPhase.RECOVERY,
    IRPhase.POST_INCIDENT,
]


class PhaseDefinition(BaseModel):
    """
    Definition of an IR phase with objectives and guidance.

    Loaded from playbook JSON files.
    """

    # Identification
    id: str
    phase: IRPhase
    name: str
    short_name: str

    # Content
    description: str
    objective: str
    key_questions: List[str] = Field(default_factory=list)

    # Guidance
    critical_reminders: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    forensic_considerations: List[str] = Field(default_factory=list)

    # References
    checklist_ids: List[str] = Field(default_factory=list)
    decision_tree_ids: List[str] = Field(default_factory=list)

    # Phase completion criteria
    completion_criteria: List[str] = Field(default_factory=list)
    required_evidence: List[str] = Field(default_factory=list)

    # Display
    icon: str = Field(default="📋")
    color: str = Field(default="#1f77b4")
    order: int = Field(default=0)

    class Config:
        use_enum_values = True


class PhaseProgress(BaseModel):
    """
    Tracks progress through a phase for a specific incident.
    """

    incident_id: str
    phase: IRPhase

    # Status
    status: PhaseStatus = Field(default=PhaseStatus.NOT_STARTED)

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    checklist_progress: dict = Field(default_factory=dict)
    decisions_made: List[str] = Field(default_factory=list)
    evidence_entries: List[str] = Field(default_factory=list)

    # Completion
    completion_notes: Optional[str] = None
    skip_reason: Optional[str] = None

    class Config:
        use_enum_values = True

    def start(self) -> None:
        """Mark phase as started."""
        self.status = PhaseStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def complete(self, notes: Optional[str] = None) -> None:
        """Mark phase as completed."""
        self.status = PhaseStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.completion_notes = notes

    def skip(self, reason: str) -> None:
        """Skip this phase with reason."""
        self.status = PhaseStatus.SKIPPED
        self.completed_at = datetime.now(timezone.utc)
        self.skip_reason = reason

    def get_duration_seconds(self) -> Optional[float]:
        """Get duration of this phase in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class IncidentPhaseTracker(BaseModel):
    """
    Tracks overall phase progression for an incident.
    """

    incident_id: str
    phases: dict[str, PhaseProgress] = Field(default_factory=dict)
    current_phase: IRPhase = Field(default=IRPhase.DETECTION)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize all phases
        for phase in IRPhase:
            if phase.value not in self.phases:
                self.phases[phase.value] = PhaseProgress(
                    incident_id=self.incident_id, phase=phase
                )

    def get_current_progress(self) -> PhaseProgress:
        """Get progress for current phase."""
        return self.phases[self.current_phase.value]

    def can_advance(self) -> tuple[bool, str]:
        """Check if current phase can be advanced."""
        current = self.get_current_progress()

        if current.status != PhaseStatus.IN_PROGRESS:
            return False, "Current phase is not in progress"

        # Check if there's a next phase
        current_idx = PHASE_ORDER.index(self.current_phase)
        if current_idx >= len(PHASE_ORDER) - 1:
            return False, "Already at final phase"

        return True, ""

    def advance_phase(self, completion_notes: Optional[str] = None) -> IRPhase:
        """Advance to the next phase."""
        can_advance, reason = self.can_advance()
        if not can_advance:
            raise ValueError(f"Cannot advance phase: {reason}")

        # Complete current phase
        self.get_current_progress().complete(completion_notes)

        # Move to next phase
        current_idx = PHASE_ORDER.index(self.current_phase)
        self.current_phase = PHASE_ORDER[current_idx + 1]

        # Start next phase
        self.get_current_progress().start()

        return self.current_phase

    def get_overall_progress(self) -> dict:
        """Get overall incident progress across all phases."""
        total = len(PHASE_ORDER)
        completed = sum(
            1
            for p in self.phases.values()
            if p.status in [PhaseStatus.COMPLETED, PhaseStatus.SKIPPED]
        )

        return {
            "total_phases": total,
            "completed_phases": completed,
            "percentage": round((completed / total) * 100),
            "current_phase": self.current_phase.value,
            "phase_statuses": {
                phase.value: self.phases[phase.value].status for phase in PHASE_ORDER
            },
        }

    def get_timeline(self) -> List[dict]:
        """Get timeline of phase transitions."""
        timeline = []
        for phase in PHASE_ORDER:
            progress = self.phases[phase.value]
            if progress.started_at:
                timeline.append(
                    {
                        "phase": phase.value,
                        "started_at": progress.started_at.isoformat(),
                        "completed_at": (
                            progress.completed_at.isoformat()
                            if progress.completed_at
                            else None
                        ),
                        "duration_seconds": progress.get_duration_seconds(),
                        "status": progress.status,
                    }
                )
        return timeline
