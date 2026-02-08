"""
Onboarding Schemas

Pydantic schemas for the onboarding wizard API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.onboarding import (
    IndustrySector,
    CompanySize,
    CountryCode,
    OnboardingStatus,
)


# =============================================================================
# REFERENCE DATA SCHEMAS
# =============================================================================

class IndustryInfo(BaseModel):
    """Industry sector information."""
    id: str
    name_en: str
    name_de: str
    category: str  # financial, critical_infrastructure, automotive, general
    icon: str


class RegulationInfo(BaseModel):
    """Regulation information."""
    id: str
    name: str
    name_de: str
    description: str
    deadline: Optional[str] = None
    authority: str
    penalties: str
    applies: bool = False
    reason: Optional[str] = None


class FrameworkInfo(BaseModel):
    """Framework recommendation."""
    id: str
    name: str
    priority: int
    reason: str
    controls_count: Optional[int] = None


class BaselineRecommendation(BaseModel):
    """Baseline framework recommendation."""
    frameworks: List[FrameworkInfo]
    controls_focus: List[str]
    estimated_effort_months: int
    recommended_start: str


# =============================================================================
# STEP 1: ORGANIZATION PROFILE
# =============================================================================

class OrganizationProfileCreate(BaseModel):
    """Create organization profile (Step 1)."""
    organization_name: str = Field(..., min_length=2, max_length=255)
    industry_sector: IndustrySector
    company_size: CompanySize
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue_eur: Optional[int] = Field(None, ge=0)  # In thousands
    headquarters_country: CountryCode
    operates_in_eu: bool = True
    eu_member_states: Optional[List[CountryCode]] = None


class OrganizationProfileUpdate(BaseModel):
    """Update organization profile."""
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry_sector: Optional[IndustrySector] = None
    company_size: Optional[CompanySize] = None
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue_eur: Optional[int] = Field(None, ge=0)
    headquarters_country: Optional[CountryCode] = None
    operates_in_eu: Optional[bool] = None
    eu_member_states: Optional[List[CountryCode]] = None


# =============================================================================
# STEP 2: SPECIAL STATUS & REGULATION DETECTION
# =============================================================================

class SpecialStatusUpdate(BaseModel):
    """Update special regulatory status (Step 2)."""
    is_kritis_operator: bool = False
    kritis_sector: Optional[str] = None
    is_bafin_regulated: bool = False
    is_essential_service: bool = False
    is_important_entity: bool = False
    supplies_to_oem: bool = False


class RegulationApplicability(BaseModel):
    """Detected regulation applicability."""
    regulation_id: str
    name: str
    name_de: str
    applies: bool
    reason: str
    mandatory: bool = False
    deadline: Optional[str] = None
    authority: str
    user_confirmed: bool = False


class RegulationDetectionResponse(BaseModel):
    """Response with detected regulations."""
    regulations: List[RegulationApplicability]
    summary: Dict[str, int]  # {mandatory: 2, recommended: 3}


class RegulationConfirmation(BaseModel):
    """User confirmation of applicable regulations."""
    confirmed_regulations: List[str]  # List of regulation IDs


# =============================================================================
# STEP 3: BASELINE FRAMEWORK SELECTION
# =============================================================================

class FrameworkRecommendation(BaseModel):
    """Framework recommendation with details."""
    id: str
    name: str
    description: str
    priority: int
    reason: str
    controls_count: int
    maps_to_regulations: List[str]
    estimated_effort_days: int
    recommended: bool = True


class BaselineRecommendationResponse(BaseModel):
    """Response with framework recommendations."""
    recommendations: List[FrameworkRecommendation]
    controls_focus: List[str]
    total_controls: int
    estimated_effort_months: int


class FrameworkSelection(BaseModel):
    """User selection of frameworks."""
    selected_frameworks: List[str]  # List of framework IDs


# =============================================================================
# STEP 4: COMPLIANCE PLAN GENERATION
# =============================================================================

class PlanItemCreate(BaseModel):
    """Create a plan item."""
    category: str
    title: str
    description: Optional[str] = None
    regulation_id: Optional[str] = None
    framework_id: Optional[str] = None
    control_ref: Optional[str] = None
    owner_role: Optional[str] = None
    priority: int = Field(2, ge=1, le=4)
    due_date: Optional[datetime] = None
    estimated_effort_days: Optional[int] = None
    evidence_required: bool = True
    evidence_type: Optional[str] = None


class PlanItem(BaseModel):
    """Plan item with full details."""
    id: str
    category: str
    title: str
    description: Optional[str] = None
    regulation_id: Optional[str] = None
    regulation_name: Optional[str] = None
    framework_id: Optional[str] = None
    framework_name: Optional[str] = None
    control_ref: Optional[str] = None
    owner_role: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    priority: int
    priority_label: str
    due_date: Optional[datetime] = None
    estimated_effort_days: Optional[int] = None
    status: str
    evidence_required: bool
    evidence_type: Optional[str] = None

    class Config:
        from_attributes = True


class CompliancePlanResponse(BaseModel):
    """Generated compliance plan."""
    profile_id: str
    organization_name: str
    generated_at: datetime
    regulations: List[str]
    frameworks: List[str]
    items_by_category: Dict[str, List[PlanItem]]
    summary: Dict[str, Any]  # Statistics
    timeline: Dict[str, Any]  # Milestones


class PlanCustomization(BaseModel):
    """Customize the generated plan."""
    items_to_add: Optional[List[PlanItemCreate]] = None
    items_to_remove: Optional[List[str]] = None  # Item IDs
    owner_assignments: Optional[Dict[str, str]] = None  # item_id -> owner_id
    deadline_adjustments: Optional[Dict[str, datetime]] = None  # item_id -> new_date


# =============================================================================
# STEP 5: COMPLETE ONBOARDING
# =============================================================================

class OnboardingComplete(BaseModel):
    """Mark onboarding as complete."""
    create_initial_assessments: bool = True
    send_welcome_email: bool = False
    schedule_kickoff: bool = False
    kickoff_date: Optional[datetime] = None


class OnboardingCompletionResponse(BaseModel):
    """Response after completing onboarding."""
    profile_id: str
    organization_name: str
    applicable_regulations: List[str]
    selected_frameworks: List[str]
    plan_items_count: int
    created_assessments: List[Dict[str, str]]  # [{id, name, type}]
    next_steps: List[str]
    dashboard_url: str


# =============================================================================
# ORGANIZATION PROFILE RESPONSE
# =============================================================================

class OrganizationProfileResponse(BaseModel):
    """Full organization profile response."""
    id: str
    tenant_id: str
    organization_name: str
    industry_sector: IndustrySector
    industry_sector_name: str
    company_size: CompanySize
    company_size_name: str
    employee_count: Optional[int] = None
    annual_revenue_eur: Optional[int] = None
    headquarters_country: CountryCode
    headquarters_country_name: str
    operates_in_eu: bool
    eu_member_states: List[str]

    # Special Status
    is_kritis_operator: bool
    kritis_sector: Optional[str] = None
    is_bafin_regulated: bool
    is_essential_service: bool
    is_important_entity: bool
    supplies_to_oem: bool

    # Detected/Confirmed
    applicable_regulations: List[str]
    selected_frameworks: List[str]

    # Status
    onboarding_status: OnboardingStatus
    onboarding_completed_at: Optional[datetime] = None
    current_step: int

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# WIZARD STATE
# =============================================================================

class WizardState(BaseModel):
    """Current wizard state."""
    current_step: int
    total_steps: int = 5
    steps: List[Dict[str, Any]]
    can_proceed: bool
    profile: Optional[OrganizationProfileResponse] = None
