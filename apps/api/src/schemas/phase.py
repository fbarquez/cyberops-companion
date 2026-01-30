"""Phase tracking schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.models.phase import IRPhase, PhaseStatus


class PhaseProgressResponse(BaseModel):
    """Schema for phase progress response."""
    incident_id: str
    phase: IRPhase
    status: PhaseStatus
    checklist_total: int
    checklist_completed: int
    mandatory_total: int
    mandatory_completed: int
    decisions_required: int
    decisions_made: int
    evidence_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    progress_percent: float
    can_advance: bool

    class Config:
        from_attributes = True


class PhaseAdvanceRequest(BaseModel):
    """Schema for advancing to next phase."""
    force: bool = False  # Force advance even if checklist incomplete
    notes: Optional[str] = None


class PhaseDefinitionResponse(BaseModel):
    """Schema for phase definition."""
    phase: IRPhase
    name: str
    description: str
    objectives: List[str]
    key_questions: List[str]
    critical_reminders: List[str]
    common_mistakes: List[str]
    forensic_considerations: List[str]
    icon: str
    color: str
    order: int


class PhaseTimelineEntry(BaseModel):
    """Single entry in phase timeline."""
    phase: IRPhase
    status: PhaseStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    evidence_count: int
    decisions_count: int


class PhaseTimelineResponse(BaseModel):
    """Schema for complete phase timeline."""
    incident_id: str
    current_phase: IRPhase
    timeline: List[PhaseTimelineEntry]
    total_duration_seconds: Optional[int] = None
    started_at: Optional[datetime] = None


class OverallProgressResponse(BaseModel):
    """Schema for overall incident progress."""
    incident_id: str
    current_phase: IRPhase
    phases_completed: int
    total_phases: int
    overall_progress: float
    checklist_progress: float
    decisions_progress: float
    estimated_completion: Optional[str] = None
