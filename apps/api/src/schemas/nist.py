"""
NIST CSF 2.0 Schemas

Pydantic schemas for NIST API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.nist import (
    NISTFunction,
    NISTImplementationTier,
    NISTAssessmentStatus,
    NISTOutcomeStatus,
    NISTOrganizationType,
    NISTOrganizationSize,
)


# =============================================================================
# Reference Data Schemas
# =============================================================================

class FunctionInfo(BaseModel):
    """Information about a NIST CSF function."""
    id: str
    code: str
    name_en: str
    name_de: str
    description_en: str
    description_de: str
    weight: int
    category_count: int


class CategoryInfo(BaseModel):
    """Information about a NIST CSF category."""
    id: str
    function: str
    code: str
    name_en: str
    name_de: str
    subcategory_count: int


class SubcategoryInfo(BaseModel):
    """Information about a NIST CSF subcategory."""
    id: str
    category: str
    function: str
    name_en: str
    name_de: str
    description_en: str
    weight: int
    priority: int


class TierInfo(BaseModel):
    """Information about an implementation tier."""
    tier: str
    name_en: str
    name_de: str
    description_en: str
    risk_management: str
    integrated_program: str
    external_participation: str


class FunctionListResponse(BaseModel):
    """Response containing list of functions."""
    functions: List[FunctionInfo]
    total: int


class CategoryListResponse(BaseModel):
    """Response containing list of categories."""
    categories: List[CategoryInfo]
    total: int


class SubcategoryListResponse(BaseModel):
    """Response containing list of subcategories."""
    subcategories: List[SubcategoryInfo]
    total: int


class TierListResponse(BaseModel):
    """Response containing list of tiers."""
    tiers: List[TierInfo]


# =============================================================================
# Request Schemas
# =============================================================================

class AssessmentCreate(BaseModel):
    """Request to create a new NIST assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Request to update assessment scope."""
    organization_type: NISTOrganizationType
    organization_size: NISTOrganizationSize
    employee_count: Optional[int] = Field(None, ge=1)
    industry_sector: Optional[str] = None
    current_tier: NISTImplementationTier
    target_tier: NISTImplementationTier
    profile_type: Optional[str] = "organizational"


class SubcategoryResponseCreate(BaseModel):
    """Request to submit a subcategory response."""
    subcategory_id: str
    status: NISTOutcomeStatus
    implementation_level: int = Field(0, ge=0, le=100)
    current_state: Optional[str] = None
    target_state: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = Field(2, ge=1, le=4)
    due_date: Optional[datetime] = None
    responsible: Optional[str] = None


class BulkSubcategoryUpdate(BaseModel):
    """Request to bulk update subcategory responses."""
    responses: List[SubcategoryResponseCreate]


# =============================================================================
# Response Schemas
# =============================================================================

class SubcategoryResponseOut(BaseModel):
    """Response for a subcategory assessment."""
    id: str
    subcategory_id: str
    function_id: str
    category_id: str
    status: NISTOutcomeStatus
    implementation_level: int
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
    status: NISTAssessmentStatus
    organization_type: Optional[NISTOrganizationType]
    organization_size: Optional[NISTOrganizationSize]
    employee_count: Optional[int]
    industry_sector: Optional[str]
    current_tier: Optional[NISTImplementationTier]
    target_tier: Optional[NISTImplementationTier]
    profile_type: Optional[str]
    overall_score: float
    function_scores: Dict[str, float]
    gaps_count: int
    critical_gaps_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    """Detailed assessment response with subcategory responses."""
    responses: List[SubcategoryResponseOut]

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
    subcategory_id: str
    subcategory_name: str
    function_id: str
    function_name: str
    category_id: str
    category_name: str
    status: NISTOutcomeStatus
    implementation_level: int
    current_state: Optional[str]
    target_state: Optional[str]
    priority: int
    weight: int
    impact_score: float
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    due_date: Optional[datetime]


class FunctionSummary(BaseModel):
    """Summary of a function's assessment."""
    function_id: str
    function_name: str
    function_code: str
    subcategory_count: int
    assessed_count: int
    implemented_count: int
    gap_count: int
    score: float


class GapAnalysisResponse(BaseModel):
    """Gap analysis for an assessment."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    gaps_by_function: Dict[str, int]
    gaps_by_priority: Dict[int, int]
    overall_compliance: float
    current_tier: Optional[str]
    target_tier: Optional[str]
    tier_gap: Optional[str]
    gaps: List[GapItem]
    function_summaries: List[FunctionSummary]
    recommendations: List[str]


class ImplementationDistribution(BaseModel):
    """Distribution of implementation statuses."""
    not_evaluated: int
    not_implemented: int
    partially_implemented: int
    largely_implemented: int
    fully_implemented: int
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
    assessments_by_tier: Dict[str, int]
    average_function_scores: Dict[str, float]
    implementation_distribution: ImplementationDistribution
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

class ReportFunctionDetail(BaseModel):
    """Function details for report."""
    function_id: str
    function_name: str
    function_code: str
    subcategory_count: int
    implemented_count: int
    gaps_count: int
    score: float
    status: str  # "compliant", "partial", "non_compliant"


class ProfileComparison(BaseModel):
    """Comparison of current vs target profile."""
    function_id: str
    function_name: str
    current_score: float
    target_score: float
    gap_percentage: float


class AssessmentReportResponse(BaseModel):
    """Full assessment report."""
    assessment_id: str
    organization_name: str
    generated_at: datetime

    # Overview
    organization_type: NISTOrganizationType
    organization_size: NISTOrganizationSize
    industry_sector: Optional[str]
    current_tier: NISTImplementationTier
    target_tier: NISTImplementationTier

    # Summary
    executive_summary: str
    overall_score: float
    compliance_status: str  # "compliant", "partial", "non_compliant"

    # Tier Analysis
    tier_analysis: str
    tier_recommendations: List[str]

    # Details
    function_details: List[ReportFunctionDetail]
    profile_comparison: List[ProfileComparison]
    gaps: List[GapItem]
    implementation_distribution: ImplementationDistribution

    # Key Findings
    key_strengths: List[str]
    critical_findings: List[str]
    recommendations: List[str]
    next_steps: List[str]

    # Priority Areas
    high_priority_areas: List[str]
    quick_wins: List[str]
