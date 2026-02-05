"""
ISO 27001:2022 Compliance Schemas.

Pydantic schemas for API validation and serialization.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ========== Enums ==========

class ISO27001Theme(str, Enum):
    """ISO 27001:2022 Annex A themes."""
    ORGANIZATIONAL = "A.5"
    PEOPLE = "A.6"
    PHYSICAL = "A.7"
    TECHNOLOGICAL = "A.8"


class ISO27001AssessmentStatus(str, Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    SCOPING = "scoping"
    SOA = "soa"
    ASSESSMENT = "assessment"
    GAP_ANALYSIS = "gap_analysis"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ISO27001Applicability(str, Enum):
    """Control applicability status."""
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    EXCLUDED = "excluded"


class ISO27001ComplianceStatus(str, Enum):
    """Control compliance status."""
    NOT_EVALUATED = "not_evaluated"
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_APPLICABLE = "not_applicable"


# ========== Theme Response ==========

class ThemeInfo(BaseModel):
    """Information about an ISO 27001 theme."""
    theme_id: str = Field(..., description="Theme identifier (e.g., A.5)")
    name: str = Field(..., description="Theme name (e.g., Organizational)")
    control_count: int = Field(..., description="Number of controls in this theme")
    description: Optional[str] = None


class ThemeListResponse(BaseModel):
    """List of ISO 27001 themes."""
    themes: List[ThemeInfo]
    total_controls: int


# ========== Control Schemas ==========

class CrossReferences(BaseModel):
    """Cross-framework references."""
    bsi_grundschutz: List[str] = []
    nis2: List[str] = []
    nist_csf: List[str] = []


class ISO27001ControlResponse(BaseModel):
    """ISO 27001 control response."""
    id: str
    control_id: str
    theme: ISO27001Theme
    sort_order: int
    title_en: str
    title_de: Optional[str] = None
    title_es: Optional[str] = None
    description_en: Optional[str] = None
    description_de: Optional[str] = None
    guidance: Optional[str] = None
    control_type: List[str] = []
    security_properties: List[str] = []
    cross_references: Dict[str, List[str]] = {}

    class Config:
        from_attributes = True


class ControlListResponse(BaseModel):
    """Paginated list of controls."""
    controls: List[ISO27001ControlResponse]
    total: int
    page: int = 1
    page_size: int = 100


# ========== Assessment Schemas ==========

class AssessmentCreate(BaseModel):
    """Create a new assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentScopeUpdate(BaseModel):
    """Update assessment scope."""
    scope_description: Optional[str] = None
    scope_systems: List[str] = []
    scope_locations: List[str] = []
    scope_processes: List[str] = []
    risk_appetite: Optional[str] = Field(None, pattern="^(low|medium|high)$")


class AssessmentResponse(BaseModel):
    """Assessment response."""
    id: str
    name: str
    description: Optional[str] = None
    status: ISO27001AssessmentStatus
    # Scope
    scope_description: Optional[str] = None
    scope_systems: List[str] = []
    scope_locations: List[str] = []
    scope_processes: List[str] = []
    risk_appetite: Optional[str] = None
    # Scores
    overall_score: Optional[float] = None
    organizational_score: Optional[float] = None
    people_score: Optional[float] = None
    physical_score: Optional[float] = None
    technological_score: Optional[float] = None
    # Counts
    applicable_controls: int = 0
    compliant_controls: int = 0
    partial_controls: int = 0
    gap_controls: int = 0
    # Timestamps
    created_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentListResponse(BaseModel):
    """List of assessments."""
    assessments: List[AssessmentResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== Statement of Applicability (SoA) Schemas ==========

class SoAEntryUpdate(BaseModel):
    """Update a single SoA entry."""
    applicability: Optional[ISO27001Applicability] = None
    justification: Optional[str] = None
    status: Optional[ISO27001ComplianceStatus] = None
    implementation_level: Optional[int] = Field(None, ge=0, le=100)
    evidence: Optional[str] = None
    implementation_notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_owner: Optional[str] = None
    remediation_due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=4)


class SoAEntryBulkUpdate(BaseModel):
    """Bulk update SoA entries."""
    entries: Dict[str, SoAEntryUpdate] = Field(..., description="Map of control_id to update data")


class SoAEntryResponse(BaseModel):
    """SoA entry response."""
    id: str
    assessment_id: str
    control_id: str
    # Control info (joined)
    control_code: Optional[str] = None
    control_title: Optional[str] = None
    control_theme: Optional[str] = None
    # SoA data
    applicability: ISO27001Applicability
    justification: Optional[str] = None
    status: ISO27001ComplianceStatus
    implementation_level: int = 0
    evidence: Optional[str] = None
    implementation_notes: Optional[str] = None
    # Gap analysis
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_owner: Optional[str] = None
    remediation_due_date: Optional[datetime] = None
    priority: int = 3
    # Audit
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoAListResponse(BaseModel):
    """List of SoA entries for an assessment."""
    entries: List[SoAEntryResponse]
    total: int
    by_theme: Dict[str, int] = {}
    by_status: Dict[str, int] = {}


# ========== Wizard State Schema ==========

class WizardState(BaseModel):
    """Current wizard state for an assessment."""
    assessment_id: str
    current_step: int = Field(..., ge=1, le=6)
    step_name: str
    steps: List[Dict[str, Any]]
    is_complete: bool = False
    can_proceed: bool = True
    validation_errors: List[str] = []


# ========== Dashboard Schema ==========

class ISO27001DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_assessments: int = 0
    active_assessments: int = 0
    completed_assessments: int = 0
    # Control stats
    total_controls: int = 93
    average_compliance_score: Optional[float] = None
    # Theme breakdown
    theme_scores: Dict[str, Optional[float]] = {}
    # Recent assessments
    recent_assessments: List[AssessmentResponse] = []


# ========== Overview Schema ==========

class ThemeOverview(BaseModel):
    """Overview of a theme's compliance status."""
    theme_id: str
    theme_name: str
    total_controls: int
    applicable_controls: int
    compliant_controls: int
    partial_controls: int
    gap_controls: int
    not_evaluated: int
    score: Optional[float] = None


class AssessmentOverview(BaseModel):
    """Detailed overview of an assessment."""
    assessment: AssessmentResponse
    themes: List[ThemeOverview]
    total_applicable: int
    total_compliant: int
    total_partial: int
    total_gap: int
    overall_score: Optional[float] = None
    completion_percentage: float = 0.0


# ========== Gap Analysis Schema ==========

class GapItem(BaseModel):
    """A single gap item."""
    control_id: str
    control_code: str
    control_title: str
    theme: str
    status: ISO27001ComplianceStatus
    implementation_level: int
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_owner: Optional[str] = None
    remediation_due_date: Optional[datetime] = None
    priority: int
    # Cross-references for context
    cross_references: Dict[str, List[str]] = {}


class GapAnalysisResponse(BaseModel):
    """Gap analysis response."""
    assessment_id: str
    assessment_name: str
    total_gaps: int
    gaps_by_priority: Dict[int, int] = {}
    gaps_by_theme: Dict[str, int] = {}
    gaps: List[GapItem]


# ========== Cross-Framework Mapping Schema ==========

class RelatedControl(BaseModel):
    """A related control from another framework."""
    framework: str
    control_id: str
    control_name: Optional[str] = None


class ControlMapping(BaseModel):
    """Cross-framework mapping for a control."""
    control_id: str
    control_code: str
    control_title: str
    theme: str
    status: Optional[ISO27001ComplianceStatus] = None
    related_controls: List[RelatedControl] = []


class CrossFrameworkMappingResponse(BaseModel):
    """Cross-framework mapping response."""
    assessment_id: str
    mappings: List[ControlMapping]
    frameworks_referenced: List[str] = []
    total_bsi_references: int = 0
    total_nis2_references: int = 0
    total_nist_references: int = 0


# ========== Report Schema ==========

class ReportRequest(BaseModel):
    """Request to generate a report."""
    format: str = Field("pdf", pattern="^(pdf|html|json)$")
    include_gaps: bool = True
    include_evidence: bool = False
    language: str = Field("en", pattern="^(en|de|es)$")


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: str
    assessment_id: str
    format: str
    status: str
    download_url: Optional[str] = None
    generated_at: Optional[datetime] = None


# ========== Complete Assessment Schema ==========

class CompleteAssessmentRequest(BaseModel):
    """Request to mark assessment as complete."""
    confirm: bool = Field(..., description="Confirmation flag")
    notes: Optional[str] = None
