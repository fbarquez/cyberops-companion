"""Incident schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.incident import IncidentStatus, IncidentSeverity, DetectionSource


class AffectedSystemCreate(BaseModel):
    """Schema for adding affected system."""
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    os_type: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=255)
    criticality: str = Field("medium", pattern="^(critical|high|medium|low)$")
    notes: Optional[str] = None


class AffectedSystemResponse(BaseModel):
    """Schema for affected system response."""
    id: str
    hostname: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
    department: Optional[str] = None
    criticality: str
    added_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class IncidentCreate(BaseModel):
    """Schema for creating incident."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    detection_source: Optional[DetectionSource] = None
    initial_indicator: Optional[str] = None
    analyst_name: Optional[str] = None
    analyst_email: Optional[str] = None
    detected_at: Optional[datetime] = None


class IncidentUpdate(BaseModel):
    """Schema for updating incident."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    detection_source: Optional[DetectionSource] = None
    initial_indicator: Optional[str] = None
    analyst_name: Optional[str] = None
    analyst_email: Optional[str] = None
    assigned_to: Optional[str] = None


class IncidentResponse(BaseModel):
    """Schema for incident response."""
    id: str
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity
    status: IncidentStatus
    detection_source: Optional[DetectionSource] = None
    initial_indicator: Optional[str] = None
    current_phase: str
    created_by: str
    assigned_to: Optional[str] = None
    analyst_name: Optional[str] = None
    analyst_email: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    eradicated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    affected_systems: List[AffectedSystemResponse] = []
    phase_history: dict = {}

    class Config:
        from_attributes = True


class IncidentList(BaseModel):
    """Schema for paginated incident list."""
    items: List[IncidentResponse]
    total: int
    page: int
    size: int
    pages: int


class IncidentSummary(BaseModel):
    """Schema for incident executive summary."""
    incident: IncidentResponse
    total_evidence: int
    checklist_progress: dict
    decisions_made: int
    time_in_current_phase: Optional[int] = None  # seconds
    total_duration: Optional[int] = None  # seconds
    compliance_score: Optional[float] = None
