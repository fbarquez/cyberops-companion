"""Checklist schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.checklist import ChecklistStatus


class ChecklistItemResponse(BaseModel):
    """Schema for checklist item response."""
    id: str
    item_id: str
    phase: str
    text: str
    help_text: Optional[str] = None
    warning: Optional[str] = None
    mandatory: bool
    forensic_critical: bool
    order: int
    depends_on: List[str] = []
    blocks: List[str] = []
    status: ChecklistStatus
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None
    skip_reason: Optional[str] = None
    is_blocked: bool = False  # Computed field
    blockers: List[str] = []  # Computed - which items block this one

    class Config:
        from_attributes = True


class ChecklistPhaseResponse(BaseModel):
    """Schema for checklist phase response."""
    incident_id: str
    phase: str
    items: List[ChecklistItemResponse]
    total_items: int
    completed_items: int
    mandatory_total: int
    mandatory_completed: int
    progress_percent: float
    can_advance: bool
    blocked_items: List[str] = []


class ChecklistItemComplete(BaseModel):
    """Schema for completing a checklist item."""
    notes: Optional[str] = None


class ChecklistItemSkip(BaseModel):
    """Schema for skipping a checklist item."""
    skip_reason: str = Field(..., min_length=1)


class ChecklistProgress(BaseModel):
    """Schema for overall checklist progress."""
    incident_id: str
    phases: dict  # phase -> ChecklistPhaseResponse
    total_items: int
    completed_items: int
    overall_progress: float
