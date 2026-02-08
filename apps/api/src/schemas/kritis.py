"""
KRITIS Compliance Schemas

Pydantic schemas for KRITIS API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.kritis import (
    KRITISSector,
    KRITISCompanySize,
    KRITISAssessmentStatus,
    KRITISRequirementStatus,
)


# =============================================================================
# Reference Data Schemas
# =============================================================================

class SectorInfo(BaseModel):
    """KRITIS sector information."""
    sector: KRITISSector
    name_en: str
    name_de: str
    icon: str
    description_en: str
    description_de: str
    threshold_info: str
    subsectors: List[str]


class SectorListResponse(BaseModel):
    """List of KRITIS sectors."""
    sectors: List[SectorInfo]
    total: int


class SubRequirementInfo(BaseModel):
    """Sub-requirement information."""
    index: int
    description: str
    fulfilled: bool = False


class RequirementInfo(BaseModel):
    """KRITIS requirement information."""
    id: str
    category: str
    article: str
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    weight: int
    sub_requirements: List[str]


class CategoryInfo(BaseModel):
    """Requirement category information."""
    id: str
    name_en: str
    name_de: str
    weight: int
    requirements_count: int


class RequirementsListResponse(BaseModel):
    """List of KRITIS requirements."""
    requirements: List[RequirementInfo]
    categories: List[CategoryInfo]
    total: int


# =============================================================================
# Assessment Schemas
# =============================================================================

class AssessmentCreate(BaseModel):
    """Create a new KRITIS assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Update assessment scope (wizard step 1)."""
    sector: KRITISSector
    subsector: Optional[str] = None
    company_size: KRITISCompanySize
    employee_count: Optional[int] = None
    annual_revenue_eur: Optional[float] = None
    operates_in_germany: bool = True
    german_states: Optional[List[str]] = None
    bsi_registered: bool = False
    bsi_registration_date: Optional[datetime] = None
    bsi_contact_established: bool = False
    last_audit_date: Optional[datetime] = None
    next_audit_due: Optional[datetime] = None


class RequirementResponseCreate(BaseModel):
    """Create or update a requirement response."""
    requirement_id: str
    status: KRITISRequirementStatus
    implementation_level: int = Field(0, ge=0, le=100)
    sub_requirements_status: Optional[List[bool]] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    due_date: Optional[datetime] = None


class BulkRequirementUpdate(BaseModel):
    """Bulk update requirement responses."""
    responses: List[RequirementResponseCreate]


# =============================================================================
# Response Schemas
# =============================================================================

class RequirementResponseResponse(BaseModel):
    """Requirement response in API response."""
    id: str
    requirement_id: str
    category: str
    status: KRITISRequirementStatus
    implementation_level: int
    sub_requirements_status: Optional[List[bool]] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    """Assessment summary response."""
    id: str
    name: str
    description: Optional[str] = None
    status: KRITISAssessmentStatus
    sector: Optional[KRITISSector] = None
    subsector: Optional[str] = None
    company_size: Optional[KRITISCompanySize] = None
    overall_score: float
    category_scores: Optional[Dict[str, float]] = None
    gaps_count: int
    critical_gaps_count: int
    bsi_registered: bool
    next_audit_due: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """Assessment with full details and responses."""
    employee_count: Optional[int] = None
    annual_revenue_eur: Optional[float] = None
    operates_in_germany: bool = True
    german_states: Optional[List[str]] = None
    bsi_registration_date: Optional[datetime] = None
    bsi_contact_established: bool = False
    last_audit_date: Optional[datetime] = None
    requirement_responses: List[RequirementResponseResponse] = []


class AssessmentListResponse(BaseModel):
    """Paginated list of assessments."""
    items: List[AssessmentResponse]
    total: int
    page: int
    size: int
    pages: int


# =============================================================================
# Gap Analysis Schemas
# =============================================================================

class GapItem(BaseModel):
    """Single gap finding."""
    requirement_id: str
    requirement_name: str
    category: str
    article: str
    status: KRITISRequirementStatus
    implementation_level: int
    gap_description: Optional[str] = None
    priority: int
    weight: int
    impact_score: float
    remediation_plan: Optional[str] = None
    due_date: Optional[datetime] = None


class CategoryGapSummary(BaseModel):
    """Gap summary by category."""
    category: str
    name_en: str
    name_de: str
    total_requirements: int
    fully_implemented: int
    partially_implemented: int
    not_implemented: int
    not_evaluated: int
    score: float


class GapAnalysisResponse(BaseModel):
    """Gap analysis results."""
    assessment_id: str
    assessment_name: str
    sector: Optional[KRITISSector] = None
    overall_score: float
    total_gaps: int
    critical_gaps: int
    gaps_by_category: List[CategoryGapSummary]
    gaps: List[GapItem]
    recommendations: List[str]
    generated_at: datetime


# =============================================================================
# Report Schemas
# =============================================================================

class ReportSection(BaseModel):
    """Report section."""
    title: str
    content: str
    findings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class AssessmentReportResponse(BaseModel):
    """Assessment report."""
    assessment_id: str
    organization_name: str
    sector: Optional[KRITISSector] = None
    sector_name: Optional[str] = None
    generated_at: datetime
    executive_summary: str
    overall_score: float
    compliance_level: str
    category_summaries: List[CategoryGapSummary]
    key_findings: List[str]
    critical_gaps: List[GapItem]
    recommendations: List[str]
    next_steps: List[str]
    audit_readiness: str


# =============================================================================
# Dashboard Schemas
# =============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    average_score: float
    assessments_by_sector: Dict[str, int]
    assessments_by_status: Dict[str, int]
    upcoming_audits: int
    overdue_audits: int
    recent_assessments: List[AssessmentResponse]


# =============================================================================
# Wizard Schemas
# =============================================================================

class WizardState(BaseModel):
    """Wizard navigation state."""
    assessment_id: str
    current_step: int
    total_steps: int
    steps: List[Dict[str, Any]]
    scope_completed: bool
    requirements_completed: Dict[str, bool]
    can_complete: bool
