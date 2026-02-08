"""DORA Assessment Wizard schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.dora import (
    DORAPillar, DORAEntityType, DORACompanySize,
    DORAAssessmentStatus, DORARequirementStatus
)


# ============== Reference Data ==============

class PillarInfo(BaseModel):
    """Pillar information for UI display."""
    pillar: DORAPillar
    name_en: str
    name_de: str
    article_range: str
    weight: int
    icon: str
    description_en: str
    requirement_count: int


class PillarListResponse(BaseModel):
    """List of all DORA pillars."""
    pillars: List[PillarInfo]
    total_weight: int


class EntityTypeInfo(BaseModel):
    """Entity type information for UI display."""
    entity_type: DORAEntityType
    name_en: str
    name_de: str
    icon: str
    requires_tlpt: bool
    description_en: str


class EntityTypeListResponse(BaseModel):
    """List of all DORA entity types."""
    entity_types: List[EntityTypeInfo]


class SubRequirement(BaseModel):
    """Sub-requirement within a requirement."""
    name: str
    implemented: bool = False
    notes: Optional[str] = None


class RequirementInfo(BaseModel):
    """Requirement information for reference."""
    id: str
    pillar: DORAPillar
    article: str
    name_en: str
    name_de: str
    description_en: str
    weight: int
    sub_requirements: List[str]


class RequirementsListResponse(BaseModel):
    """List of all DORA requirements."""
    requirements: List[RequirementInfo]
    by_pillar: Dict[str, List[RequirementInfo]]
    total_count: int


# ============== Assessment Creation/Update ==============

class AssessmentCreate(BaseModel):
    """Create a new DORA assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Update assessment scope (Wizard Step 1)."""
    entity_type: DORAEntityType
    company_size: DORACompanySize
    employee_count: Optional[int] = Field(None, ge=0)
    annual_balance_eur: Optional[float] = Field(None, ge=0)
    is_ctpp: bool = False
    operates_in_eu: bool = True
    eu_member_states: Optional[List[str]] = None
    supervised_by: Optional[str] = None
    group_level_assessment: bool = False


class ScopeResult(BaseModel):
    """Result of scope classification."""
    entity_type: DORAEntityType
    entity_type_name: str
    requires_tlpt: bool
    simplified_framework: bool  # Art. 16 microenterprise
    is_ctpp: bool
    applicable_pillars: List[str]
    key_obligations: List[str]
    reporting_timelines: Dict[str, str]


class RequirementResponseCreate(BaseModel):
    """Create/update a requirement response."""
    requirement_id: str
    status: DORARequirementStatus
    implementation_level: int = Field(0, ge=0, le=100)
    sub_requirements_status: Optional[List[SubRequirement]] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    due_date: Optional[datetime] = None


class BulkRequirementUpdate(BaseModel):
    """Bulk update requirement responses (by pillar)."""
    pillar: Optional[DORAPillar] = None
    responses: List[RequirementResponseCreate]


# ============== Assessment Responses ==============

class RequirementResponseResponse(BaseModel):
    """Requirement response in API response."""
    id: str
    requirement_id: str
    pillar: DORAPillar
    status: DORARequirementStatus
    implementation_level: int
    sub_requirements_status: Optional[List[SubRequirement]]
    evidence: Optional[str]
    notes: Optional[str]
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    priority: Optional[int]
    due_date: Optional[datetime]
    assessed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    """Assessment in API response."""
    id: str
    name: str
    description: Optional[str]
    status: DORAAssessmentStatus
    entity_type: Optional[DORAEntityType]
    company_size: Optional[DORACompanySize]
    employee_count: Optional[int]
    annual_balance_eur: Optional[float]
    is_ctpp: bool
    operates_in_eu: bool
    eu_member_states: Optional[List[str]]
    supervised_by: Optional[str]
    group_level_assessment: bool
    simplified_framework: bool
    overall_score: float
    pillar_scores: Optional[Dict[str, float]]
    gaps_count: int
    critical_gaps_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentDetailResponse(BaseModel):
    """Detailed assessment with requirement responses."""
    assessment: AssessmentResponse
    requirement_responses: List[RequirementResponseResponse]
    scope_result: Optional[ScopeResult]
    responses_by_pillar: Dict[str, List[RequirementResponseResponse]]


class AssessmentListResponse(BaseModel):
    """List of assessments."""
    assessments: List[AssessmentResponse]
    total: int
    page: int
    size: int


# ============== Gap Analysis ==============

class GapItem(BaseModel):
    """Single gap identified."""
    requirement_id: str
    requirement_name: str
    pillar: DORAPillar
    article: str
    status: DORARequirementStatus
    implementation_level: int
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    priority: int
    weight: int
    impact_score: float


class PillarGapSummary(BaseModel):
    """Gap summary for a pillar."""
    pillar: DORAPillar
    pillar_name: str
    total_requirements: int
    gaps_count: int
    critical_gaps: int
    score: float
    gap_items: List[GapItem]


class GapAnalysisResponse(BaseModel):
    """Gap analysis results."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    gaps_by_pillar: Dict[str, int]
    pillar_summaries: List[PillarGapSummary]
    all_gaps: List[GapItem]
    recommendations: List[str]


# ============== Report ==============

class PillarSummary(BaseModel):
    """Summary of a pillar in the report."""
    pillar: DORAPillar
    pillar_name: str
    article_range: str
    weight: int
    score: float
    compliance_level: str
    requirements_count: int
    implemented_count: int
    partial_count: int
    gaps_count: int
    key_findings: List[str]


class ReportSection(BaseModel):
    """Section of the assessment report."""
    title: str
    content: str
    score: Optional[float] = None
    status: Optional[str] = None


class AssessmentReportResponse(BaseModel):
    """Full assessment report."""
    assessment_id: str
    organization_name: str
    generated_at: datetime
    executive_summary: str
    entity_type: DORAEntityType
    entity_type_name: str
    is_ctpp: bool
    requires_tlpt: bool
    simplified_framework: bool
    overall_score: float
    compliance_level: str  # "Non-Compliant", "Partially Compliant", "Largely Compliant", "Fully Compliant"
    pillar_summaries: List[PillarSummary]
    gaps: List[GapItem]
    recommendations: List[str]
    next_steps: List[str]
    regulatory_deadlines: Dict[str, str]


# ============== Dashboard ==============

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    draft_assessments: int
    average_score: float
    total_gaps: int
    critical_gaps: int
    # By entity type
    by_entity_type: Dict[str, int]
    # By pillar (average scores)
    pillar_scores: Dict[str, float]
    # Recent assessments
    recent_assessments: List[AssessmentResponse]
    # Compliance trend (last 6 months)
    compliance_trend: List[Dict[str, Any]]


# ============== Wizard State ==============

class WizardState(BaseModel):
    """Current state of the wizard for frontend."""
    current_step: int
    total_steps: int  # 8 steps: Scope, 5 Pillars, Gaps, Report
    assessment_id: str
    can_go_back: bool
    can_go_forward: bool
    is_complete: bool
    steps_completed: List[int]
    step_names: List[str]
