"""
COBIT 2019 Schemas

Pydantic schemas for COBIT API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.cobit import (
    COBITDomain,
    COBITCapabilityLevel,
    COBITAssessmentStatus,
    COBITProcessStatus,
    COBITOrganizationType,
    COBITOrganizationSize,
)


# =============================================================================
# Reference Data Schemas
# =============================================================================

class DomainInfo(BaseModel):
    """Information about a COBIT domain."""
    id: str
    code: str
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    weight: int
    process_count: int


class ProcessInfo(BaseModel):
    """Information about a COBIT process."""
    id: str
    domain: str
    name_en: str
    name_de: str
    description_en: str
    weight: int
    priority: int


class CapabilityLevelInfo(BaseModel):
    """Information about a capability level."""
    level: str
    name_en: str
    name_de: str
    description_en: str
    score_range: str


class DomainListResponse(BaseModel):
    """Response containing list of domains."""
    domains: List[DomainInfo]
    total: int


class ProcessListResponse(BaseModel):
    """Response containing list of processes."""
    processes: List[ProcessInfo]
    total: int


class CapabilityLevelListResponse(BaseModel):
    """Response containing list of capability levels."""
    levels: List[CapabilityLevelInfo]


# =============================================================================
# Request Schemas
# =============================================================================

class AssessmentCreate(BaseModel):
    """Request to create a new COBIT assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Request to update assessment scope."""
    organization_type: COBITOrganizationType
    organization_size: COBITOrganizationSize
    employee_count: Optional[int] = Field(None, ge=1)
    industry_sector: Optional[str] = None
    current_capability_level: COBITCapabilityLevel
    target_capability_level: COBITCapabilityLevel
    focus_areas: Optional[List[str]] = None


class ProcessResponseCreate(BaseModel):
    """Request to submit a process response."""
    process_id: str
    status: COBITProcessStatus
    capability_level: Optional[COBITCapabilityLevel] = None
    achievement_percentage: int = Field(0, ge=0, le=100)
    current_state: Optional[str] = None
    target_state: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = Field(2, ge=1, le=4)
    due_date: Optional[datetime] = None
    responsible: Optional[str] = None


class BulkProcessUpdate(BaseModel):
    """Request to bulk update process responses."""
    responses: List[ProcessResponseCreate]


# =============================================================================
# Response Schemas
# =============================================================================

class ProcessResponseOut(BaseModel):
    """Response for a process assessment."""
    id: str
    process_id: str
    domain_id: str
    status: COBITProcessStatus
    capability_level: Optional[COBITCapabilityLevel]
    achievement_percentage: int
    current_state: Optional[str]
    target_state: Optional[str]
    evidence: Optional[str]
    notes: Optional[str]
    gap_description: Optional[str]
    remediation_plan: Optional[str]
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
    status: COBITAssessmentStatus
    organization_type: Optional[COBITOrganizationType]
    organization_size: Optional[COBITOrganizationSize]
    employee_count: Optional[int]
    industry_sector: Optional[str]
    current_capability_level: Optional[COBITCapabilityLevel]
    target_capability_level: Optional[COBITCapabilityLevel]
    focus_areas: List[str]
    overall_score: float
    domain_scores: Dict[str, float]
    gaps_count: int
    critical_gaps_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """Detailed assessment response with process responses."""
    responses: List[ProcessResponseOut]

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
    process_id: str
    process_name: str
    domain_id: str
    domain_name: str
    status: COBITProcessStatus
    capability_level: Optional[COBITCapabilityLevel]
    achievement_percentage: int
    current_state: Optional[str]
    target_state: Optional[str]
    priority: int
    weight: int
    impact_score: float
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    due_date: Optional[datetime]


class DomainSummary(BaseModel):
    """Summary of a domain's assessment."""
    domain_id: str
    domain_name: str
    domain_code: str
    process_count: int
    assessed_count: int
    achieved_count: int
    gap_count: int
    score: float
    average_capability: Optional[str]


class GapAnalysisResponse(BaseModel):
    """Gap analysis for an assessment."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    gaps_by_domain: Dict[str, int]
    gaps_by_priority: Dict[int, int]
    overall_compliance: float
    current_level: Optional[str]
    target_level: Optional[str]
    level_gap: Optional[str]
    gaps: List[GapItem]
    domain_summaries: List[DomainSummary]
    recommendations: List[str]


class AchievementDistribution(BaseModel):
    """Distribution of achievement statuses."""
    not_evaluated: int
    not_achieved: int
    partially_achieved: int
    largely_achieved: int
    fully_achieved: int
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
    assessments_by_level: Dict[str, int]
    average_domain_scores: Dict[str, float]
    achievement_distribution: AchievementDistribution
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

class ReportDomainDetail(BaseModel):
    """Domain details for report."""
    domain_id: str
    domain_name: str
    domain_code: str
    process_count: int
    achieved_count: int
    gaps_count: int
    score: float
    capability_level: Optional[str]
    status: str  # "compliant", "partial", "non_compliant"


class CapabilityComparison(BaseModel):
    """Comparison of current vs target capability."""
    domain_id: str
    domain_name: str
    current_level: Optional[str]
    target_level: Optional[str]
    gap_levels: int


class AssessmentReportResponse(BaseModel):
    """Full assessment report."""
    assessment_id: str
    organization_name: str
    generated_at: datetime

    # Overview
    organization_type: COBITOrganizationType
    organization_size: COBITOrganizationSize
    industry_sector: Optional[str]
    current_capability_level: COBITCapabilityLevel
    target_capability_level: COBITCapabilityLevel

    # Summary
    executive_summary: str
    overall_score: float
    compliance_status: str  # "compliant", "partial", "non_compliant"

    # Capability Analysis
    capability_analysis: str
    capability_recommendations: List[str]

    # Details
    domain_details: List[ReportDomainDetail]
    capability_comparison: List[CapabilityComparison]
    gaps: List[GapItem]
    achievement_distribution: AchievementDistribution

    # Key Findings
    key_strengths: List[str]
    critical_findings: List[str]
    recommendations: List[str]
    next_steps: List[str]

    # Priority Areas
    high_priority_areas: List[str]
    quick_wins: List[str]
