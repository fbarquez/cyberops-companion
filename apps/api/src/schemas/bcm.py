"""
Business Continuity Management (BCM) Schemas.

Pydantic schemas for API validation and serialization.
Based on BSI Standard 200-4 and ISO 22301.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# ========== Enums ==========

class BCMProcessCriticality(str, Enum):
    """Business process criticality levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BCMProcessStatus(str, Enum):
    """Business process status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"


class BCMImpactLevel(str, Enum):
    """Impact assessment levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BCMBIAStatus(str, Enum):
    """BIA assessment status."""
    DRAFT = "draft"
    COMPLETED = "completed"
    APPROVED = "approved"
    OUTDATED = "outdated"


class BCMScenarioCategory(str, Enum):
    """Risk scenario categories based on BSI 200-4."""
    NATURAL_DISASTER = "natural_disaster"
    TECHNICAL_FAILURE = "technical_failure"
    HUMAN_ERROR = "human_error"
    CYBER_ATTACK = "cyber_attack"
    PANDEMIC = "pandemic"
    SUPPLY_CHAIN = "supply_chain"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class BCMLikelihood(str, Enum):
    """Risk likelihood levels (1-5)."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class BCMImpact(str, Enum):
    """Risk impact levels (1-5)."""
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class BCMControlEffectiveness(str, Enum):
    """Effectiveness of existing controls."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BCMScenarioStatus(str, Enum):
    """Scenario assessment status."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"


class BCMStrategyType(str, Enum):
    """Continuity strategy types."""
    DO_NOTHING = "do_nothing"
    MANUAL_WORKAROUND = "manual_workaround"
    ALTERNATE_SITE = "alternate_site"
    ALTERNATE_SUPPLIER = "alternate_supplier"
    REDUNDANCY = "redundancy"
    OUTSOURCE = "outsource"
    INSURANCE = "insurance"


class BCMStrategyStatus(str, Enum):
    """Strategy implementation status."""
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    APPROVED = "approved"


class BCMPlanType(str, Enum):
    """Emergency plan types."""
    CRISIS_MANAGEMENT = "crisis_management"
    EMERGENCY_RESPONSE = "emergency_response"
    BUSINESS_RECOVERY = "business_recovery"
    IT_DISASTER_RECOVERY = "it_disaster_recovery"
    COMMUNICATION = "communication"
    EVACUATION = "evacuation"


class BCMPlanStatus(str, Enum):
    """Emergency plan status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BCMContactType(str, Enum):
    """Emergency contact types."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    VENDOR = "vendor"
    AUTHORITY = "authority"


class BCMContactAvailability(str, Enum):
    """Contact availability."""
    TWENTY_FOUR_SEVEN = "24x7"
    BUSINESS_HOURS = "business_hours"
    ON_CALL = "on_call"


class BCMExerciseType(str, Enum):
    """Exercise/test types."""
    TABLETOP = "tabletop"
    WALKTHROUGH = "walkthrough"
    SIMULATION = "simulation"
    PARALLEL_TEST = "parallel_test"
    FULL_INTERRUPTION = "full_interruption"


class BCMExerciseStatus(str, Enum):
    """Exercise status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BCMAssessmentStatus(str, Enum):
    """BCM assessment wizard status."""
    DRAFT = "draft"
    PROCESS_INVENTORY = "process_inventory"
    BIA_ANALYSIS = "bia_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_PLANNING = "strategy_planning"
    PLAN_DEVELOPMENT = "plan_development"
    TESTING = "testing"
    COMPLETED = "completed"


# ========== Process Schemas ==========

class ProcessCreate(BaseModel):
    """Create a new business process."""
    process_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = None
    criticality: BCMProcessCriticality = BCMProcessCriticality.MEDIUM
    internal_dependencies: List[str] = []
    external_dependencies: List[str] = []
    it_systems: List[str] = []
    key_personnel: List[str] = []
    status: BCMProcessStatus = BCMProcessStatus.ACTIVE


class ProcessUpdate(BaseModel):
    """Update a business process."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    owner: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = None
    criticality: Optional[BCMProcessCriticality] = None
    internal_dependencies: Optional[List[str]] = None
    external_dependencies: Optional[List[str]] = None
    it_systems: Optional[List[str]] = None
    key_personnel: Optional[List[str]] = None
    status: Optional[BCMProcessStatus] = None


class ProcessResponse(BaseModel):
    """Business process response."""
    id: str
    process_id: str
    name: str
    description: Optional[str] = None
    owner: str
    department: Optional[str] = None
    criticality: BCMProcessCriticality
    internal_dependencies: List[str] = []
    external_dependencies: List[str] = []
    it_systems: List[str] = []
    key_personnel: List[str] = []
    status: BCMProcessStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    # Include BIA status if exists
    has_bia: bool = False
    bia_status: Optional[BCMBIAStatus] = None

    class Config:
        from_attributes = True


class ProcessListResponse(BaseModel):
    """List of business processes."""
    processes: List[ProcessResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== BIA Schemas ==========

class BIACreate(BaseModel):
    """Create/Update BIA for a process."""
    rto_hours: int = Field(24, ge=0)
    rpo_hours: int = Field(4, ge=0)
    mtpd_hours: int = Field(72, ge=0)
    impact_1h: BCMImpactLevel = BCMImpactLevel.LOW
    impact_4h: BCMImpactLevel = BCMImpactLevel.LOW
    impact_8h: BCMImpactLevel = BCMImpactLevel.MEDIUM
    impact_24h: BCMImpactLevel = BCMImpactLevel.HIGH
    impact_72h: BCMImpactLevel = BCMImpactLevel.CRITICAL
    impact_1w: BCMImpactLevel = BCMImpactLevel.CRITICAL
    financial_impact: int = Field(3, ge=1, le=5)
    operational_impact: int = Field(3, ge=1, le=5)
    reputational_impact: int = Field(3, ge=1, le=5)
    legal_impact: int = Field(3, ge=1, le=5)
    safety_impact: int = Field(3, ge=1, le=5)
    financial_justification: Optional[str] = None
    operational_justification: Optional[str] = None
    minimum_staff: int = Field(1, ge=0)
    minimum_workspace: Optional[str] = None
    critical_equipment: List[str] = []
    critical_data: List[str] = []
    analyst: Optional[str] = None
    next_review_date: Optional[date] = None
    status: BCMBIAStatus = BCMBIAStatus.DRAFT


class BIAResponse(BaseModel):
    """BIA response."""
    id: str
    process_id: str
    rto_hours: int
    rpo_hours: int
    mtpd_hours: int
    impact_1h: BCMImpactLevel
    impact_4h: BCMImpactLevel
    impact_8h: BCMImpactLevel
    impact_24h: BCMImpactLevel
    impact_72h: BCMImpactLevel
    impact_1w: BCMImpactLevel
    financial_impact: int
    operational_impact: int
    reputational_impact: int
    legal_impact: int
    safety_impact: int
    financial_justification: Optional[str] = None
    operational_justification: Optional[str] = None
    minimum_staff: int
    minimum_workspace: Optional[str] = None
    critical_equipment: List[str] = []
    critical_data: List[str] = []
    analysis_date: datetime
    analyst: Optional[str] = None
    next_review_date: Optional[date] = None
    status: BCMBIAStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Process info
    process_name: Optional[str] = None
    process_criticality: Optional[BCMProcessCriticality] = None

    class Config:
        from_attributes = True


class BIASummaryResponse(BaseModel):
    """BIA summary across all processes."""
    total_processes: int
    processes_with_bia: int
    bia_completion_percentage: float
    by_status: Dict[str, int] = {}
    by_criticality: Dict[str, int] = {}
    average_rto_hours: Optional[float] = None
    average_rpo_hours: Optional[float] = None


# ========== Risk Scenario Schemas ==========

class ScenarioCreate(BaseModel):
    """Create a risk scenario."""
    scenario_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    category: BCMScenarioCategory = BCMScenarioCategory.OTHER
    likelihood: BCMLikelihood = BCMLikelihood.POSSIBLE
    impact: BCMImpact = BCMImpact.MODERATE
    affected_processes: List[str] = []
    single_points_of_failure: List[str] = []
    existing_controls: Optional[str] = None
    control_effectiveness: BCMControlEffectiveness = BCMControlEffectiveness.MEDIUM
    status: BCMScenarioStatus = BCMScenarioStatus.IDENTIFIED


class ScenarioUpdate(BaseModel):
    """Update a risk scenario."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[BCMScenarioCategory] = None
    likelihood: Optional[BCMLikelihood] = None
    impact: Optional[BCMImpact] = None
    affected_processes: Optional[List[str]] = None
    single_points_of_failure: Optional[List[str]] = None
    existing_controls: Optional[str] = None
    control_effectiveness: Optional[BCMControlEffectiveness] = None
    status: Optional[BCMScenarioStatus] = None


class ScenarioResponse(BaseModel):
    """Risk scenario response."""
    id: str
    scenario_id: str
    name: str
    description: str
    category: BCMScenarioCategory
    likelihood: BCMLikelihood
    impact: BCMImpact
    risk_score: int
    affected_processes: List[str] = []
    single_points_of_failure: List[str] = []
    existing_controls: Optional[str] = None
    control_effectiveness: BCMControlEffectiveness
    status: BCMScenarioStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScenarioListResponse(BaseModel):
    """List of risk scenarios."""
    scenarios: List[ScenarioResponse]
    total: int
    page: int = 1
    page_size: int = 20


class RiskMatrixData(BaseModel):
    """Risk matrix data for visualization."""
    matrix: Dict[str, Dict[str, int]]  # likelihood -> impact -> count
    scenarios_by_cell: Dict[str, List[Dict[str, Any]]]  # "likelihood-impact" -> scenarios


# ========== Strategy Schemas ==========

class StrategyCreate(BaseModel):
    """Create a continuity strategy."""
    strategy_type: BCMStrategyType = BCMStrategyType.MANUAL_WORKAROUND
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    activation_trigger: str
    activation_procedure: str
    resource_requirements: List[str] = []
    estimated_cost: Optional[Decimal] = None
    achievable_rto_hours: int = Field(24, ge=0)
    achievable_rpo_hours: int = Field(4, ge=0)
    status: BCMStrategyStatus = BCMStrategyStatus.PLANNED
    implementation_date: Optional[date] = None
    last_test_date: Optional[date] = None


class StrategyUpdate(BaseModel):
    """Update a continuity strategy."""
    strategy_type: Optional[BCMStrategyType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    activation_trigger: Optional[str] = None
    activation_procedure: Optional[str] = None
    resource_requirements: Optional[List[str]] = None
    estimated_cost: Optional[Decimal] = None
    achievable_rto_hours: Optional[int] = Field(None, ge=0)
    achievable_rpo_hours: Optional[int] = Field(None, ge=0)
    status: Optional[BCMStrategyStatus] = None
    implementation_date: Optional[date] = None
    last_test_date: Optional[date] = None


class StrategyResponse(BaseModel):
    """Strategy response."""
    id: str
    process_id: str
    strategy_type: BCMStrategyType
    name: str
    description: str
    activation_trigger: str
    activation_procedure: str
    resource_requirements: List[str] = []
    estimated_cost: Optional[Decimal] = None
    achievable_rto_hours: int
    achievable_rpo_hours: int
    status: BCMStrategyStatus
    implementation_date: Optional[date] = None
    last_test_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Process info
    process_name: Optional[str] = None

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """List of strategies."""
    strategies: List[StrategyResponse]
    total: int


# ========== Emergency Plan Schemas ==========

class PlanCreate(BaseModel):
    """Create an emergency plan."""
    plan_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    plan_type: BCMPlanType = BCMPlanType.BUSINESS_RECOVERY
    scope_description: str
    affected_processes: List[str] = []
    affected_locations: List[str] = []
    activation_criteria: List[Dict[str, Any]] = []
    response_phases: List[Dict[str, Any]] = []
    procedures: List[Dict[str, Any]] = []
    roles_responsibilities: List[Dict[str, Any]] = []
    communication_tree: List[Dict[str, Any]] = []
    contact_list: List[str] = []
    resources_required: List[str] = []
    activation_checklist: List[Dict[str, Any]] = []
    recovery_checklist: List[Dict[str, Any]] = []
    version: str = "1.0"
    effective_date: date
    review_date: date
    status: BCMPlanStatus = BCMPlanStatus.DRAFT


class PlanUpdate(BaseModel):
    """Update an emergency plan."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    plan_type: Optional[BCMPlanType] = None
    scope_description: Optional[str] = None
    affected_processes: Optional[List[str]] = None
    affected_locations: Optional[List[str]] = None
    activation_criteria: Optional[List[Dict[str, Any]]] = None
    response_phases: Optional[List[Dict[str, Any]]] = None
    procedures: Optional[List[Dict[str, Any]]] = None
    roles_responsibilities: Optional[List[Dict[str, Any]]] = None
    communication_tree: Optional[List[Dict[str, Any]]] = None
    contact_list: Optional[List[str]] = None
    resources_required: Optional[List[str]] = None
    activation_checklist: Optional[List[Dict[str, Any]]] = None
    recovery_checklist: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    status: Optional[BCMPlanStatus] = None


class PlanResponse(BaseModel):
    """Emergency plan response."""
    id: str
    plan_id: str
    name: str
    description: Optional[str] = None
    plan_type: BCMPlanType
    scope_description: str
    affected_processes: List[str] = []
    affected_locations: List[str] = []
    activation_criteria: List[Dict[str, Any]] = []
    response_phases: List[Dict[str, Any]] = []
    procedures: List[Dict[str, Any]] = []
    roles_responsibilities: List[Dict[str, Any]] = []
    communication_tree: List[Dict[str, Any]] = []
    contact_list: List[str] = []
    resources_required: List[str] = []
    activation_checklist: List[Dict[str, Any]] = []
    recovery_checklist: List[Dict[str, Any]] = []
    version: str
    effective_date: date
    review_date: date
    status: BCMPlanStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    """List of emergency plans."""
    plans: List[PlanResponse]
    total: int
    page: int = 1
    page_size: int = 20


class PlanApproveRequest(BaseModel):
    """Request to approve a plan."""
    approved_by: str


# ========== Contact Schemas ==========

class ContactCreate(BaseModel):
    """Create an emergency contact."""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = None
    phone_primary: str = Field(..., min_length=1, max_length=50)
    phone_secondary: Optional[str] = None
    email: str = Field(..., min_length=1, max_length=255)
    availability: BCMContactAvailability = BCMContactAvailability.BUSINESS_HOURS
    contact_type: BCMContactType = BCMContactType.INTERNAL
    priority: int = Field(10, ge=1)


class ContactUpdate(BaseModel):
    """Update an emergency contact."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = None
    phone_primary: Optional[str] = Field(None, min_length=1, max_length=50)
    phone_secondary: Optional[str] = None
    email: Optional[str] = Field(None, min_length=1, max_length=255)
    availability: Optional[BCMContactAvailability] = None
    contact_type: Optional[BCMContactType] = None
    priority: Optional[int] = Field(None, ge=1)


class ContactResponse(BaseModel):
    """Emergency contact response."""
    id: str
    name: str
    role: str
    department: Optional[str] = None
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: str
    availability: BCMContactAvailability
    contact_type: BCMContactType
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """List of emergency contacts."""
    contacts: List[ContactResponse]
    total: int


# ========== Exercise Schemas ==========

class ExerciseCreate(BaseModel):
    """Create a BC exercise."""
    exercise_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    exercise_type: BCMExerciseType = BCMExerciseType.TABLETOP
    scenario_id: Optional[str] = None
    plan_id: Optional[str] = None
    objectives: List[str] = []
    scope: str
    participants: List[str] = []
    planned_date: date
    planned_duration_hours: int = Field(4, ge=1)
    status: BCMExerciseStatus = BCMExerciseStatus.PLANNED


class ExerciseUpdate(BaseModel):
    """Update a BC exercise."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    exercise_type: Optional[BCMExerciseType] = None
    scenario_id: Optional[str] = None
    plan_id: Optional[str] = None
    objectives: Optional[List[str]] = None
    scope: Optional[str] = None
    participants: Optional[List[str]] = None
    planned_date: Optional[date] = None
    planned_duration_hours: Optional[int] = Field(None, ge=1)
    actual_date: Optional[date] = None
    actual_duration_hours: Optional[int] = None
    status: Optional[BCMExerciseStatus] = None
    results_summary: Optional[str] = None
    objectives_met: Optional[Dict[str, bool]] = None
    issues_identified: Optional[List[str]] = None
    lessons_learned: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None


class ExerciseCompleteRequest(BaseModel):
    """Request to complete an exercise with results."""
    actual_date: date
    actual_duration_hours: int = Field(..., ge=1)
    results_summary: str
    objectives_met: Dict[str, bool] = {}
    issues_identified: List[str] = []
    lessons_learned: Optional[str] = None
    action_items: List[Dict[str, Any]] = []


class ExerciseResponse(BaseModel):
    """Exercise response."""
    id: str
    exercise_id: str
    name: str
    description: str
    exercise_type: BCMExerciseType
    scenario_id: Optional[str] = None
    plan_id: Optional[str] = None
    objectives: List[str] = []
    scope: str
    participants: List[str] = []
    planned_date: date
    planned_duration_hours: int
    actual_date: Optional[date] = None
    actual_duration_hours: Optional[int] = None
    status: BCMExerciseStatus
    results_summary: Optional[str] = None
    objectives_met: Dict[str, bool] = {}
    issues_identified: List[str] = []
    lessons_learned: Optional[str] = None
    action_items: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    conducted_by: Optional[str] = None
    # Related info
    scenario_name: Optional[str] = None
    plan_name: Optional[str] = None

    class Config:
        from_attributes = True


class ExerciseListResponse(BaseModel):
    """List of exercises."""
    exercises: List[ExerciseResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== Assessment Schemas ==========

class AssessmentCreate(BaseModel):
    """Create a BCM assessment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AssessmentResponse(BaseModel):
    """BCM assessment response."""
    id: str
    name: str
    description: Optional[str] = None
    status: BCMAssessmentStatus
    overall_score: Optional[float] = None
    process_coverage_score: Optional[float] = None
    bia_completion_score: Optional[float] = None
    strategy_coverage_score: Optional[float] = None
    plan_coverage_score: Optional[float] = None
    test_coverage_score: Optional[float] = None
    total_processes: int = 0
    critical_processes: int = 0
    processes_with_bia: int = 0
    processes_with_strategy: int = 0
    processes_with_plan: int = 0
    plans_tested_this_year: int = 0
    assessment_date: date
    next_review_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentListResponse(BaseModel):
    """List of BCM assessments."""
    assessments: List[AssessmentResponse]
    total: int
    page: int = 1
    page_size: int = 20


class CompleteAssessmentRequest(BaseModel):
    """Request to mark assessment as complete."""
    confirm: bool = Field(..., description="Confirmation flag")


# ========== Dashboard Schemas ==========

class BCMDashboardStats(BaseModel):
    """BCM dashboard statistics."""
    # Process stats
    total_processes: int = 0
    critical_processes: int = 0
    processes_by_criticality: Dict[str, int] = {}
    # BIA stats
    bia_completion_percentage: float = 0.0
    processes_with_bia: int = 0
    average_rto_hours: Optional[float] = None
    # Scenario stats
    total_scenarios: int = 0
    scenarios_by_category: Dict[str, int] = {}
    high_risk_scenarios: int = 0
    # Plan stats
    total_plans: int = 0
    active_plans: int = 0
    plans_by_type: Dict[str, int] = {}
    # Exercise stats
    exercises_this_year: int = 0
    completed_exercises: int = 0
    upcoming_exercises: List[Dict[str, Any]] = []
    # Assessment stats
    total_assessments: int = 0
    latest_assessment_score: Optional[float] = None
    # Recent activity
    recent_activity: List[Dict[str, Any]] = []


# ========== Wizard State Schema ==========

class WizardState(BaseModel):
    """Current wizard state for a BCM assessment."""
    assessment_id: str
    current_step: int = Field(..., ge=1, le=7)
    step_name: str
    steps: List[Dict[str, Any]]
    is_complete: bool = False
    can_proceed: bool = True
    validation_errors: List[str] = []


# ========== Report Schema ==========

class BCMReportData(BaseModel):
    """BCM report data structure."""
    assessment: AssessmentResponse
    processes: List[ProcessResponse] = []
    bia_summary: Optional[BIASummaryResponse] = None
    scenarios: List[ScenarioResponse] = []
    plans: List[PlanResponse] = []
    exercises: List[ExerciseResponse] = []
    generated_at: datetime
