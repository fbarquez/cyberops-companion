"""
Risk Management Schemas.

Pydantic schemas for API validation and serialization.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class RiskCategory(str, Enum):
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"
    TECHNICAL = "technical"
    SECURITY = "security"
    LEGAL = "legal"


class RiskStatus(str, Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    TREATMENT_PLANNED = "treatment_planned"
    TREATMENT_IN_PROGRESS = "treatment_in_progress"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    TRANSFERRED = "transferred"
    CLOSED = "closed"
    MONITORING = "monitoring"


class LikelihoodLevel(str, Enum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class ImpactLevel(str, Enum):
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentType(str, Enum):
    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class ControlType(str, Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    COMPENSATING = "compensating"


class ControlStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    NOT_EFFECTIVE = "not_effective"
    RETIRED = "retired"


# Risk Schemas
class RiskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: RiskCategory
    risk_source: Optional[str] = None
    threat_scenario: Optional[str] = None
    department: Optional[str] = None
    affected_assets: List[str] = []
    affected_processes: List[str] = []
    compliance_frameworks: List[str] = []
    tags: List[str] = []


class RiskCreate(RiskBase):
    # Initial assessment
    inherent_likelihood: Optional[LikelihoodLevel] = None
    inherent_impact: Optional[ImpactLevel] = None
    # Financial impact
    financial_impact: Optional[float] = None
    operational_impact: Optional[str] = None
    # Treatment
    treatment_type: Optional[TreatmentType] = None
    treatment_plan: Optional[str] = None
    treatment_deadline: Optional[datetime] = None
    # Ownership
    risk_owner: Optional[str] = None
    # Related entities
    incident_id: Optional[str] = None


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RiskCategory] = None
    status: Optional[RiskStatus] = None
    risk_source: Optional[str] = None
    threat_scenario: Optional[str] = None
    department: Optional[str] = None
    # Assessment
    inherent_likelihood: Optional[LikelihoodLevel] = None
    inherent_impact: Optional[ImpactLevel] = None
    residual_likelihood: Optional[LikelihoodLevel] = None
    residual_impact: Optional[ImpactLevel] = None
    target_likelihood: Optional[LikelihoodLevel] = None
    target_impact: Optional[ImpactLevel] = None
    # Impact
    financial_impact: Optional[float] = None
    operational_impact: Optional[str] = None
    reputational_impact: Optional[str] = None
    compliance_impact: Optional[str] = None
    # Treatment
    treatment_type: Optional[TreatmentType] = None
    treatment_plan: Optional[str] = None
    treatment_deadline: Optional[datetime] = None
    treatment_cost: Optional[float] = None
    # Ownership
    risk_owner: Optional[str] = None
    # Review
    next_review_date: Optional[datetime] = None
    review_frequency_days: Optional[int] = None
    # Other
    affected_assets: Optional[List[str]] = None
    affected_processes: Optional[List[str]] = None
    compliance_frameworks: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class RiskAssessmentCreate(BaseModel):
    likelihood: LikelihoodLevel
    impact: ImpactLevel
    assessment_type: str = "periodic"
    assessment_notes: Optional[str] = None
    assumptions: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    id: str
    risk_id: str
    assessment_type: str
    likelihood: LikelihoodLevel
    impact: ImpactLevel
    risk_score: float
    risk_level: RiskLevel
    assessment_notes: Optional[str] = None
    assessed_at: datetime
    assessed_by: Optional[str] = None

    class Config:
        from_attributes = True


class RiskAcceptanceRequest(BaseModel):
    acceptance_reason: str
    acceptance_expiry: Optional[datetime] = None


class RiskControlBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    control_type: ControlType
    implementation_details: Optional[str] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0, le=100)
    implementation_cost: Optional[float] = None
    annual_cost: Optional[float] = None
    compliance_frameworks: List[str] = []
    compliance_control_ids: List[str] = []


class RiskControlCreate(RiskControlBase):
    control_owner: Optional[str] = None


class RiskControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    control_type: Optional[ControlType] = None
    status: Optional[ControlStatus] = None
    implementation_details: Optional[str] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0, le=100)
    implementation_cost: Optional[float] = None
    annual_cost: Optional[float] = None
    control_owner: Optional[str] = None
    compliance_frameworks: Optional[List[str]] = None
    compliance_control_ids: Optional[List[str]] = None


class RiskControlResponse(RiskControlBase):
    id: str
    control_id: str
    status: ControlStatus
    implemented_date: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    test_results: Optional[str] = None
    control_owner: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TreatmentActionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    expected_risk_reduction: Optional[str] = None


class TreatmentActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    expected_risk_reduction: Optional[str] = None


class TreatmentActionResponse(BaseModel):
    id: str
    risk_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    expected_risk_reduction: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiskResponse(RiskBase):
    id: str
    risk_id: str
    status: RiskStatus
    # Inherent risk
    inherent_likelihood: Optional[LikelihoodLevel] = None
    inherent_impact: Optional[ImpactLevel] = None
    inherent_risk_score: Optional[float] = None
    inherent_risk_level: Optional[RiskLevel] = None
    # Residual risk
    residual_likelihood: Optional[LikelihoodLevel] = None
    residual_impact: Optional[ImpactLevel] = None
    residual_risk_score: Optional[float] = None
    residual_risk_level: Optional[RiskLevel] = None
    # Target
    target_risk_score: Optional[float] = None
    # Impact
    financial_impact: Optional[float] = None
    operational_impact: Optional[str] = None
    reputational_impact: Optional[str] = None
    compliance_impact: Optional[str] = None
    # Treatment
    treatment_type: Optional[TreatmentType] = None
    treatment_plan: Optional[str] = None
    treatment_deadline: Optional[datetime] = None
    treatment_cost: Optional[float] = None
    # Acceptance
    acceptance_reason: Optional[str] = None
    accepted_at: Optional[datetime] = None
    acceptance_expiry: Optional[datetime] = None
    # Ownership
    risk_owner: Optional[str] = None
    # Review
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    # Timestamps
    identified_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    # Related
    incident_id: Optional[str] = None
    controls: List[RiskControlResponse] = []
    treatment_actions: List[TreatmentActionResponse] = []

    class Config:
        from_attributes = True


class RiskListResponse(BaseModel):
    risks: List[RiskResponse]
    total: int
    page: int
    page_size: int


class RiskControlListResponse(BaseModel):
    controls: List[RiskControlResponse]
    total: int
    page: int
    page_size: int


# Risk Matrix Schema
class RiskMatrixCell(BaseModel):
    likelihood: LikelihoodLevel
    impact: ImpactLevel
    risk_level: RiskLevel
    risk_count: int
    risks: List[Dict[str, Any]] = []


class RiskMatrix(BaseModel):
    cells: List[RiskMatrixCell]
    likelihood_levels: List[str]
    impact_levels: List[str]


# Statistics Schema
class RiskStats(BaseModel):
    total_risks: int
    open_risks: int
    risks_by_category: Dict[str, int]
    risks_by_status: Dict[str, int]
    risks_by_level: Dict[str, int]
    critical_risks: int
    high_risks: int
    overdue_treatments: int
    risks_needing_review: int
    total_controls: int
    effective_controls: int
    average_risk_score: Optional[float] = None
    total_financial_exposure: Optional[float] = None
    recent_risks: List[RiskResponse] = []


# Risk Appetite Schema
class RiskAppetiteCreate(BaseModel):
    category: RiskCategory
    appetite_level: RiskLevel
    tolerance_threshold: float = 0.0
    description: Optional[str] = None
    max_single_loss: Optional[float] = None
    max_annual_loss: Optional[float] = None
    requires_board_approval: bool = False
    requires_executive_approval: bool = False


class RiskAppetiteResponse(BaseModel):
    id: str
    category: RiskCategory
    appetite_level: RiskLevel
    tolerance_threshold: float
    description: Optional[str] = None
    max_single_loss: Optional[float] = None
    max_annual_loss: Optional[float] = None
    requires_board_approval: bool
    requires_executive_approval: bool
    effective_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
