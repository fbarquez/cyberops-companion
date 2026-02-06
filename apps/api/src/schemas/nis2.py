"""NIS2 Assessment Wizard schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.nis2 import (
    NIS2Sector, NIS2EntityType, NIS2CompanySize,
    NIS2AssessmentStatus, NIS2MeasureStatus
)


# ============== Sector Information ==============

class SectorInfo(BaseModel):
    """Sector information for UI display."""
    sector: NIS2Sector
    name_en: str
    name_de: str
    name_es: str
    icon: str
    subsectors: List[str]
    is_essential: bool


class SectorListResponse(BaseModel):
    """List of all NIS2 sectors."""
    essential_sectors: List[SectorInfo]
    important_sectors: List[SectorInfo]


# ============== Security Measures ==============

class SubRequirement(BaseModel):
    """Sub-requirement within a measure."""
    name: str
    implemented: bool = False
    notes: Optional[str] = None


class SecurityMeasureInfo(BaseModel):
    """Security measure information."""
    id: str
    article: str
    name_en: str
    name_de: str
    name_es: str
    description_en: str
    weight: int
    sub_requirements: List[str]


class MeasuresListResponse(BaseModel):
    """List of all NIS2 security measures."""
    measures: List[SecurityMeasureInfo]
    total_weight: int


# ============== Assessment Creation/Update ==============

class AssessmentCreate(BaseModel):
    """Create a new NIS2 assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Update assessment scope (Wizard Step 1)."""
    sector: NIS2Sector
    subsector: Optional[str] = None
    company_size: NIS2CompanySize
    employee_count: Optional[int] = Field(None, ge=0)
    annual_turnover_eur: Optional[float] = Field(None, ge=0)
    operates_in_eu: bool = True
    eu_countries: Optional[List[str]] = None


class ClassificationResult(BaseModel):
    """Classification result (Wizard Step 2)."""
    entity_type: NIS2EntityType
    classification_reason: str
    applicable_requirements: List[str]
    supervision_level: str
    reporting_obligations: Dict[str, Any]


class MeasureResponseCreate(BaseModel):
    """Create/update a measure response."""
    measure_id: str
    status: NIS2MeasureStatus
    implementation_level: int = Field(0, ge=0, le=100)
    sub_requirements_status: Optional[List[SubRequirement]] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    due_date: Optional[datetime] = None


class BulkMeasureUpdate(BaseModel):
    """Bulk update measure responses."""
    responses: List[MeasureResponseCreate]


# ============== Assessment Responses ==============

class MeasureResponseResponse(BaseModel):
    """Measure response in API response."""
    id: str
    measure_id: str
    status: NIS2MeasureStatus
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
    status: NIS2AssessmentStatus
    sector: Optional[NIS2Sector]
    subsector: Optional[str]
    company_size: Optional[NIS2CompanySize]
    employee_count: Optional[int]
    annual_turnover_eur: Optional[float]
    operates_in_eu: bool
    eu_countries: Optional[List[str]]
    entity_type: Optional[NIS2EntityType]
    classification_reason: Optional[str]
    overall_score: float
    gaps_count: int
    critical_gaps_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentDetailResponse(BaseModel):
    """Detailed assessment with measure responses."""
    assessment: AssessmentResponse
    measure_responses: List[MeasureResponseResponse]
    classification: Optional[ClassificationResult]


class AssessmentListResponse(BaseModel):
    """List of assessments."""
    assessments: List[AssessmentResponse]
    total: int
    page: int
    size: int


# ============== Gap Analysis ==============

class GapItem(BaseModel):
    """Single gap identified."""
    measure_id: str
    measure_name: str
    status: NIS2MeasureStatus
    implementation_level: int
    gap_description: Optional[str]
    remediation_plan: Optional[str]
    priority: int
    weight: int
    impact_score: float


class GapAnalysisResponse(BaseModel):
    """Gap analysis results."""
    assessment_id: str
    total_gaps: int
    critical_gaps: int
    high_priority_gaps: int
    gaps: List[GapItem]
    recommendations: List[str]


# ============== Report ==============

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
    entity_classification: ClassificationResult
    overall_score: float
    compliance_level: str  # "Non-Compliant", "Partially Compliant", "Compliant"
    sections: List[ReportSection]
    gaps: List[GapItem]
    recommendations: List[str]
    next_steps: List[str]


# ============== Wizard State ==============

class WizardState(BaseModel):
    """Current state of the wizard for frontend."""
    current_step: int
    total_steps: int
    assessment_id: str
    can_go_back: bool
    can_go_forward: bool
    is_complete: bool
    steps_completed: List[int]
