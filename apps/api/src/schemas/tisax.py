"""
TISAX Compliance Schemas

Pydantic schemas for TISAX API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.tisax import (
    TISAXAssessmentLevel,
    TISAXAssessmentObjective,
    TISAXCompanyType,
    TISAXCompanySize,
    TISAXAssessmentStatus,
    TISAXMaturityLevel,
)


# =============================================================================
# Reference Data Schemas
# =============================================================================

class ChapterInfo(BaseModel):
    """Information about a VDA ISA chapter."""
    id: str
    number: str
    name_en: str
    name_de: str
    description_en: str
    control_count: int


class ControlInfo(BaseModel):
    """Information about a VDA ISA control."""
    id: str
    chapter: str
    number: str
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    objective: str
    weight: int
    must_requirements: List[str]
    should_requirements: List[str]


class AssessmentLevelInfo(BaseModel):
    """Information about a TISAX assessment level."""
    level: TISAXAssessmentLevel
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    audit_type: str
    validity_years: int
    min_maturity: int


class ObjectiveInfo(BaseModel):
    """Information about a TISAX assessment objective."""
    objective: TISAXAssessmentObjective
    name_en: str
    name_de: str
    description_en: str
    assessment_levels: List[TISAXAssessmentLevel]


class ChapterListResponse(BaseModel):
    """Response containing list of chapters."""
    chapters: List[ChapterInfo]
    total: int


class ControlListResponse(BaseModel):
    """Response containing list of controls."""
    controls: List[ControlInfo]
    total: int


class AssessmentLevelListResponse(BaseModel):
    """Response containing assessment levels."""
    levels: List[AssessmentLevelInfo]


class ObjectiveListResponse(BaseModel):
    """Response containing assessment objectives."""
    objectives: List[ObjectiveInfo]


# =============================================================================
# Request Schemas
# =============================================================================

class AssessmentCreate(BaseModel):
    """Request to create a new TISAX assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Request to update assessment scope (wizard step 1)."""
    company_type: TISAXCompanyType
    company_size: TISAXCompanySize
    employee_count: Optional[int] = Field(None, ge=1)
    location_count: Optional[int] = Field(1, ge=1)
    assessment_level: TISAXAssessmentLevel
    objectives: List[TISAXAssessmentObjective]
    oem_requirements: Optional[List[str]] = None
    target_date: Optional[datetime] = None


class ControlResponseCreate(BaseModel):
    """Request to submit a control response."""
    control_id: str
    maturity_level: TISAXMaturityLevel
    target_maturity: Optional[TISAXMaturityLevel] = TISAXMaturityLevel.LEVEL_3
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    must_fulfilled: Optional[List[str]] = None
    should_fulfilled: Optional[List[str]] = None
    priority: Optional[int] = Field(2, ge=1, le=4)
    due_date: Optional[datetime] = None
    responsible: Optional[str] = None


class BulkControlUpdate(BaseModel):
    """Request to bulk update control responses."""
    responses: List[ControlResponseCreate]


# =============================================================================
# Response Schemas
# =============================================================================

class ControlResponseOut(BaseModel):
    """Response for a control assessment."""
    id: str
    control_id: str
    chapter_id: str
    maturity_level: TISAXMaturityLevel
    target_maturity: TISAXMaturityLevel
    evidence: Optional[str]
    notes: Optional[str]
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    must_fulfilled: List[str]
    should_fulfilled: List[str]
    priority: int
    due_date: Optional[datetime]
    responsible: Optional[str]
    assessed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    """Basic assessment response."""
    id: str
    name: str
    description: Optional[str]
    status: TISAXAssessmentStatus
    company_type: Optional[TISAXCompanyType]
    company_size: Optional[TISAXCompanySize]
    assessment_level: Optional[TISAXAssessmentLevel]
    objectives: List[str]
    oem_requirements: List[str]
    overall_score: float
    maturity_level: float
    chapter_scores: Dict[str, float]
    gaps_count: int
    critical_gaps_count: int
    target_date: Optional[datetime]
    audit_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """Detailed assessment response with control responses."""
    employee_count: Optional[int]
    location_count: int
    auditor_name: Optional[str]
    audit_provider: Optional[str]
    responses: List[ControlResponseOut]

    class Config:
        from_attributes = True


class AssessmentListResponse(BaseModel):
    """Paginated list of assessments."""
    items: List[AssessmentResponse]
    total: int
    page: int
    size: int
    pages: int


# =============================================================================
# Analysis Schemas
# =============================================================================

class GapItem(BaseModel):
    """A single gap in the assessment."""
    control_id: str
    control_name: str
    chapter_id: str
    chapter_name: str
    current_maturity: int
    target_maturity: int
    maturity_gap: int
    priority: int
    weight: int
    impact_score: float
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    due_date: Optional[datetime]


class ChapterSummary(BaseModel):
    """Summary of a chapter's assessment."""
    chapter_id: str
    chapter_name: str
    control_count: int
    assessed_count: int
    average_maturity: float
    target_maturity: float
    gap_count: int
    score: float


class GapAnalysisResponse(BaseModel):
    """Gap analysis for an assessment."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    gaps_by_chapter: Dict[str, int]
    gaps_by_priority: Dict[int, int]
    average_maturity: float
    target_maturity: float
    gaps: List[GapItem]
    chapter_summaries: List[ChapterSummary]
    recommendations: List[str]


class MaturityDistribution(BaseModel):
    """Distribution of maturity levels."""
    level_0: int
    level_1: int
    level_2: int
    level_3: int
    level_4: int
    level_5: int


# =============================================================================
# Dashboard Schemas
# =============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    average_score: float
    average_maturity: float
    total_gaps: int
    critical_gaps: int
    assessments_by_level: Dict[str, int]
    assessments_by_objective: Dict[str, int]
    maturity_distribution: MaturityDistribution
    recent_assessments: List[AssessmentResponse]
    upcoming_audits: List[AssessmentResponse]


# =============================================================================
# Wizard State Schema
# =============================================================================

class WizardStep(BaseModel):
    """A single wizard step."""
    id: str
    name: str
    completed: bool
    current: bool


class WizardState(BaseModel):
    """Current wizard navigation state."""
    assessment_id: str
    current_step: int
    total_steps: int
    steps: List[WizardStep]
    can_complete: bool
    completion_percentage: float


# =============================================================================
# Report Schemas
# =============================================================================

class ReportChapterDetail(BaseModel):
    """Chapter details for report."""
    chapter_id: str
    chapter_name: str
    average_maturity: float
    target_maturity: float
    control_count: int
    gaps_count: int
    status: str  # "compliant", "partial", "non_compliant"


class AssessmentReportResponse(BaseModel):
    """Full assessment report."""
    assessment_id: str
    organization_name: str
    generated_at: datetime

    # Overview
    assessment_level: TISAXAssessmentLevel
    objectives: List[str]
    company_type: TISAXCompanyType
    company_size: TISAXCompanySize

    # Summary
    executive_summary: str
    overall_score: float
    average_maturity: float
    target_maturity: float
    compliance_status: str  # "ready", "partial", "not_ready"

    # Details
    chapter_details: List[ReportChapterDetail]
    gaps: List[GapItem]
    maturity_distribution: MaturityDistribution

    # Recommendations
    critical_findings: List[str]
    recommendations: List[str]
    next_steps: List[str]

    # Audit Readiness
    audit_readiness_score: float
    estimated_remediation_effort: str  # "low", "medium", "high"
