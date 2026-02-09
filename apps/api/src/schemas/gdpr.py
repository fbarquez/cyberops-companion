"""
GDPR Compliance Schemas

Pydantic schemas for GDPR API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.gdpr import (
    GDPRChapter,
    GDPROrganizationType,
    GDPROrganizationSize,
    GDPRAssessmentStatus,
    GDPRComplianceLevel,
    GDPRDataCategory,
    GDPRLegalBasis,
)


# =============================================================================
# Reference Data Schemas
# =============================================================================

class ChapterInfo(BaseModel):
    """Information about a GDPR chapter."""
    id: str
    number: str
    name_en: str
    name_de: str
    articles: str
    description_en: str
    requirement_count: int


class RequirementInfo(BaseModel):
    """Information about a GDPR requirement."""
    id: str
    chapter: str
    article: str
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    weight: int
    priority: int
    requirements: List[str]


class ChapterListResponse(BaseModel):
    """Response containing list of chapters."""
    chapters: List[ChapterInfo]
    total: int


class RequirementListResponse(BaseModel):
    """Response containing list of requirements."""
    requirements: List[RequirementInfo]
    total: int


# =============================================================================
# Request Schemas
# =============================================================================

class AssessmentCreate(BaseModel):
    """Request to create a new GDPR assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Request to update assessment scope."""
    organization_type: GDPROrganizationType
    organization_size: GDPROrganizationSize
    employee_count: Optional[int] = Field(None, ge=1)
    processes_special_categories: bool = False
    processes_criminal_data: bool = False
    large_scale_processing: bool = False
    systematic_monitoring: bool = False
    cross_border_processing: bool = False
    data_categories: List[GDPRDataCategory]
    legal_bases: List[GDPRLegalBasis]
    eu_countries: Optional[List[str]] = None
    dpo_appointed: bool = False
    dpo_name: Optional[str] = None
    dpo_email: Optional[str] = None
    lead_authority: Optional[str] = None


class RequirementResponseCreate(BaseModel):
    """Request to submit a requirement response."""
    requirement_id: str
    compliance_level: GDPRComplianceLevel
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    requirements_met: Optional[List[str]] = None
    priority: Optional[int] = Field(2, ge=1, le=4)
    due_date: Optional[datetime] = None
    responsible: Optional[str] = None


class BulkRequirementUpdate(BaseModel):
    """Request to bulk update requirement responses."""
    responses: List[RequirementResponseCreate]


# =============================================================================
# Response Schemas
# =============================================================================

class RequirementResponseOut(BaseModel):
    """Response for a requirement assessment."""
    id: str
    requirement_id: str
    chapter_id: str
    compliance_level: GDPRComplianceLevel
    evidence: Optional[str]
    notes: Optional[str]
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    requirements_met: List[str]
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
    status: GDPRAssessmentStatus
    organization_type: Optional[GDPROrganizationType]
    organization_size: Optional[GDPROrganizationSize]
    processes_special_categories: bool
    cross_border_processing: bool
    requires_dpo: bool
    dpo_appointed: bool
    overall_score: float
    chapter_scores: Dict[str, float]
    gaps_count: int
    critical_gaps_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """Detailed assessment response with requirement responses."""
    employee_count: Optional[int]
    data_categories: List[str]
    legal_bases: List[str]
    eu_countries: List[str]
    large_scale_processing: bool
    systematic_monitoring: bool
    processes_criminal_data: bool
    dpo_name: Optional[str]
    dpo_email: Optional[str]
    lead_authority: Optional[str]
    responses: List[RequirementResponseOut]

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
    requirement_id: str
    requirement_name: str
    chapter_id: str
    chapter_name: str
    article: str
    compliance_level: GDPRComplianceLevel
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
    requirement_count: int
    assessed_count: int
    compliant_count: int
    gap_count: int
    score: float


class GapAnalysisResponse(BaseModel):
    """Gap analysis for an assessment."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    gaps_by_chapter: Dict[str, int]
    gaps_by_priority: Dict[int, int]
    overall_compliance: float
    gaps: List[GapItem]
    chapter_summaries: List[ChapterSummary]
    recommendations: List[str]


class ComplianceDistribution(BaseModel):
    """Distribution of compliance levels."""
    not_evaluated: int
    non_compliant: int
    partially_compliant: int
    fully_compliant: int
    not_applicable: int


# =============================================================================
# Dashboard Schemas
# =============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    average_score: float
    total_gaps: int
    critical_gaps: int
    assessments_with_dpo: int
    assessments_with_special_data: int
    compliance_distribution: ComplianceDistribution
    recent_assessments: List[AssessmentResponse]


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
    requirement_count: int
    compliant_count: int
    gaps_count: int
    score: float
    status: str  # "compliant", "partial", "non_compliant"


class AssessmentReportResponse(BaseModel):
    """Full assessment report."""
    assessment_id: str
    organization_name: str
    generated_at: datetime

    # Overview
    organization_type: GDPROrganizationType
    organization_size: GDPROrganizationSize
    dpo_appointed: bool
    lead_authority: Optional[str]

    # Summary
    executive_summary: str
    overall_score: float
    compliance_status: str  # "compliant", "partial", "non_compliant"

    # Details
    chapter_details: List[ReportChapterDetail]
    gaps: List[GapItem]
    compliance_distribution: ComplianceDistribution

    # Key Findings
    key_strengths: List[str]
    critical_findings: List[str]
    recommendations: List[str]
    next_steps: List[str]

    # Risk Areas
    high_risk_areas: List[str]
    data_subject_rights_status: str
    security_measures_status: str
    breach_readiness_status: str
