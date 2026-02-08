"""
Evidence Bridge Schemas

Pydantic schemas for the ISMS ↔ SOC evidence bridge API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.evidence_bridge import (
    ActivityType,
    ControlFramework,
    LinkType,
    EvidenceStrength,
    EffectivenessLevel,
)


# =============================================================================
# CONTROL EVIDENCE LINK SCHEMAS
# =============================================================================

class EvidenceLinkCreate(BaseModel):
    """Create a manual evidence link."""
    control_framework: ControlFramework
    control_id: str = Field(..., min_length=1, max_length=50)
    activity_type: ActivityType
    activity_id: str = Field(..., min_length=1, max_length=36)
    evidence_strength: EvidenceStrength = EvidenceStrength.MODERATE
    notes: Optional[str] = None


class EvidenceLinkResponse(BaseModel):
    """Response for an evidence link."""
    id: str
    control_framework: ControlFramework
    control_id: str
    control_name: Optional[str] = None
    activity_type: ActivityType
    activity_id: str
    activity_title: Optional[str] = None
    activity_date: Optional[datetime] = None
    link_type: LinkType
    evidence_strength: EvidenceStrength
    notes: Optional[str] = None
    linked_at: datetime
    linked_by: Optional[str] = None

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    """List of evidence links for a control."""
    control_framework: ControlFramework
    control_id: str
    control_name: Optional[str] = None
    total_count: int
    evidence: List[EvidenceLinkResponse]
    by_type: Dict[str, int]  # {"incident": 47, "alert": 120}
    by_strength: Dict[str, int]  # {"strong": 30, "moderate": 50}


# =============================================================================
# CONTROL EFFECTIVENESS SCHEMAS
# =============================================================================

class ControlEffectivenessResponse(BaseModel):
    """Response for control effectiveness."""
    id: str
    control_framework: ControlFramework
    control_id: str
    control_name: Optional[str] = None
    control_description: Optional[str] = None

    # Effectiveness
    effectiveness_score: float
    effectiveness_level: EffectivenessLevel
    effectiveness_color: str  # For UI display

    # Evidence counts
    total_evidence_count: int
    strong_evidence_count: int
    moderate_evidence_count: int
    weak_evidence_count: int
    evidence_by_type: Optional[Dict[str, int]] = None

    # Operational metrics
    operational_metrics: Optional[Dict[str, Any]] = None

    # Last activity
    last_activity_date: Optional[datetime] = None
    last_activity_type: Optional[ActivityType] = None
    days_since_last_activity: Optional[int] = None

    # Status
    meets_baseline: bool
    gaps_identified: Optional[List[str]] = None
    trend: Optional[str] = None  # "improving", "stable", "declining"

    # Timestamps
    calculated_at: datetime

    class Config:
        from_attributes = True


class ControlEffectivenessSummary(BaseModel):
    """Summary of a control's effectiveness for dashboard."""
    control_id: str
    control_name: str
    effectiveness_score: float
    effectiveness_level: EffectivenessLevel
    effectiveness_color: str
    evidence_count: int
    last_activity_date: Optional[datetime] = None
    trend: Optional[str] = None


class FrameworkEffectivenessResponse(BaseModel):
    """All controls effectiveness for a framework."""
    framework: ControlFramework
    framework_name: str
    overall_score: float
    overall_level: EffectivenessLevel
    controls_assessed: int
    controls_total: int
    controls_meeting_baseline: int

    # By level breakdown
    by_level: Dict[str, int]  # {"fully_effective": 10, "largely_effective": 5, ...}

    # Controls list
    controls: List[ControlEffectivenessSummary]

    # Gaps
    top_gaps: List[Dict[str, Any]]  # Top controls needing attention


# =============================================================================
# DASHBOARD SCHEMAS
# =============================================================================

class EvidenceBridgeDashboard(BaseModel):
    """Main dashboard data for the evidence bridge."""
    # Overall stats
    total_evidence_links: int
    links_last_24h: int
    links_last_7d: int
    links_last_30d: int

    # By framework
    frameworks: List[Dict[str, Any]]
    # [{"framework": "iso27001", "score": 87, "controls": 93, "evidence": 1234}]

    # Activity summary
    activities_linked: Dict[str, int]  # {"incident": 234, "alert": 567}

    # Top controls by evidence
    top_controls: List[ControlEffectivenessSummary]

    # Controls needing attention (low effectiveness)
    controls_needing_attention: List[ControlEffectivenessSummary]

    # Recent evidence
    recent_evidence: List[EvidenceLinkResponse]

    # Trends
    effectiveness_trend: List[Dict[str, Any]]
    # [{"date": "2026-02-01", "score": 82}, {"date": "2026-02-08", "score": 87}]


class ActivityEvidenceInfo(BaseModel):
    """Information about evidence generated by an activity."""
    activity_type: ActivityType
    activity_id: str
    controls_linked: List[Dict[str, Any]]
    # [{"framework": "iso27001", "control_id": "A.5.24", "strength": "strong"}]
    linked_at: datetime


# =============================================================================
# LINKING RULE SCHEMAS
# =============================================================================

class LinkingRuleCreate(BaseModel):
    """Create a custom linking rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    control_framework: ControlFramework
    control_id: str
    activity_type: ActivityType
    activity_filters: Optional[Dict[str, Any]] = None
    evidence_strength: EvidenceStrength = EvidenceStrength.MODERATE
    auto_link: bool = True
    metrics_to_capture: Optional[List[str]] = None


class LinkingRuleResponse(BaseModel):
    """Response for a linking rule."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    control_framework: ControlFramework
    control_id: str
    activity_type: ActivityType
    activity_filters: Optional[Dict[str, Any]] = None
    evidence_strength: EvidenceStrength
    auto_link: bool
    metrics_to_capture: Optional[List[str]] = None
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# AUDITOR VIEW SCHEMAS
# =============================================================================

class ControlAuditView(BaseModel):
    """Comprehensive view of a control for auditors."""
    # Control info
    control_framework: ControlFramework
    control_id: str
    control_name: str
    control_description: Optional[str] = None
    control_category: Optional[str] = None

    # Effectiveness
    effectiveness: ControlEffectivenessResponse

    # All evidence (paginated separately if needed)
    evidence_summary: Dict[str, int]
    recent_evidence: List[EvidenceLinkResponse]

    # Operational metrics
    metrics: Dict[str, Any]
    # {
    #   "incidents_handled": 47,
    #   "avg_response_time": "2.3 hours",
    #   "resolution_rate": "94%",
    #   "trend": "improving"
    # }

    # Audit trail
    assessment_history: List[Dict[str, Any]]

    # Compliance status
    meets_requirements: bool
    gaps: List[str]
    recommendations: List[str]

    # Export info
    exportable: bool = True
    last_exported: Optional[datetime] = None


class AuditExportRequest(BaseModel):
    """Request to export control evidence for audit."""
    framework: ControlFramework
    control_ids: Optional[List[str]] = None  # None = all controls
    include_evidence_details: bool = True
    include_metrics: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = "pdf"  # pdf, excel, json


class AuditExportResponse(BaseModel):
    """Response with export file info."""
    export_id: str
    framework: ControlFramework
    controls_included: int
    evidence_count: int
    generated_at: datetime
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None
