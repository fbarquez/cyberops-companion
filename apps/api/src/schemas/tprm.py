"""Third-Party Risk Management schemas."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from src.models.tprm import (
    VendorStatus, VendorTier, VendorCategory,
    AssessmentStatus, AssessmentType, RiskRating,
    ContractStatus, FindingSeverity, FindingStatus
)


# ============== Vendor Schemas ==============

class VendorBase(BaseModel):
    """Base vendor schema."""
    name: str
    legal_name: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[VendorTier] = VendorTier.TIER_3
    category: Optional[VendorCategory] = VendorCategory.OTHER
    website: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    services_provided: Optional[str] = None
    data_types_shared: Optional[List[str]] = None
    has_pii_access: Optional[bool] = False
    has_phi_access: Optional[bool] = False
    has_pci_access: Optional[bool] = False
    has_network_access: Optional[bool] = False
    has_physical_access: Optional[bool] = False
    certifications: Optional[List[str]] = None
    compliance_frameworks: Optional[List[str]] = None
    business_owner: Optional[str] = None
    risk_owner: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class VendorCreate(VendorBase):
    """Schema for creating a vendor."""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor."""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[VendorStatus] = None
    tier: Optional[VendorTier] = None
    category: Optional[VendorCategory] = None
    website: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    services_provided: Optional[str] = None
    data_types_shared: Optional[List[str]] = None
    has_pii_access: Optional[bool] = None
    has_phi_access: Optional[bool] = None
    has_pci_access: Optional[bool] = None
    has_network_access: Optional[bool] = None
    has_physical_access: Optional[bool] = None
    current_risk_rating: Optional[RiskRating] = None
    inherent_risk_score: Optional[int] = None
    residual_risk_score: Optional[int] = None
    certifications: Optional[List[str]] = None
    compliance_frameworks: Optional[List[str]] = None
    business_owner: Optional[str] = None
    risk_owner: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class VendorResponse(VendorBase):
    """Schema for vendor response."""
    id: str
    vendor_id: str
    status: VendorStatus
    current_risk_rating: Optional[RiskRating] = None
    inherent_risk_score: Optional[int] = None
    residual_risk_score: Optional[int] = None
    last_assessment_date: Optional[datetime] = None
    next_assessment_due: Optional[datetime] = None
    onboarding_date: Optional[datetime] = None
    offboarding_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """Schema for paginated vendor list."""
    items: List[VendorResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Assessment Schemas ==============

class AssessmentBase(BaseModel):
    """Base assessment schema."""
    title: str
    description: Optional[str] = None
    assessment_type: Optional[AssessmentType] = AssessmentType.INITIAL
    questionnaire_template: Optional[str] = None
    questionnaire_due_date: Optional[datetime] = None
    assessor: Optional[str] = None
    reviewer: Optional[str] = None


class AssessmentCreate(AssessmentBase):
    """Schema for creating an assessment."""
    vendor_id: str


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AssessmentStatus] = None
    questionnaire_template: Optional[str] = None
    questionnaire_due_date: Optional[datetime] = None
    questionnaire_responses: Optional[dict] = None
    security_score: Optional[int] = None
    privacy_score: Optional[int] = None
    compliance_score: Optional[int] = None
    operational_score: Optional[int] = None
    overall_score: Optional[int] = None
    inherent_risk: Optional[RiskRating] = None
    control_effectiveness: Optional[int] = None
    residual_risk: Optional[RiskRating] = None
    assessor: Optional[str] = None
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    evidence_documents: Optional[List[str]] = None


class AssessmentResponse(AssessmentBase):
    """Schema for assessment response."""
    id: str
    assessment_id: str
    vendor_id: str
    status: AssessmentStatus
    questionnaire_sent_date: Optional[datetime] = None
    questionnaire_received_date: Optional[datetime] = None
    questionnaire_responses: Optional[dict] = None
    security_score: Optional[int] = None
    privacy_score: Optional[int] = None
    compliance_score: Optional[int] = None
    operational_score: Optional[int] = None
    overall_score: Optional[int] = None
    inherent_risk: Optional[RiskRating] = None
    control_effectiveness: Optional[int] = None
    residual_risk: Optional[RiskRating] = None
    risk_accepted: bool
    risk_accepted_by: Optional[str] = None
    risk_acceptance_date: Optional[datetime] = None
    review_notes: Optional[str] = None
    evidence_documents: Optional[List[str]] = None
    initiated_date: datetime
    completed_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentListResponse(BaseModel):
    """Schema for paginated assessment list."""
    items: List[AssessmentResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Finding Schemas ==============

class FindingBase(BaseModel):
    """Base finding schema."""
    title: str
    description: Optional[str] = None
    severity: Optional[FindingSeverity] = FindingSeverity.MEDIUM
    control_domain: Optional[str] = None
    control_reference: Optional[str] = None
    risk_description: Optional[str] = None
    business_impact: Optional[str] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    recommendation: Optional[str] = None


class FindingCreate(FindingBase):
    """Schema for creating a finding."""
    assessment_id: str
    vendor_id: str


class FindingUpdate(BaseModel):
    """Schema for updating a finding."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[FindingSeverity] = None
    status: Optional[FindingStatus] = None
    control_domain: Optional[str] = None
    control_reference: Optional[str] = None
    risk_description: Optional[str] = None
    business_impact: Optional[str] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    recommendation: Optional[str] = None
    vendor_response: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_due_date: Optional[datetime] = None
    evidence: Optional[List[str]] = None


class FindingResponse(FindingBase):
    """Schema for finding response."""
    id: str
    finding_id: str
    assessment_id: str
    vendor_id: str
    status: FindingStatus
    risk_score: Optional[int] = None
    vendor_response: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_due_date: Optional[datetime] = None
    remediation_completed_date: Optional[datetime] = None
    accepted_by: Optional[str] = None
    acceptance_justification: Optional[str] = None
    acceptance_expiry: Optional[datetime] = None
    evidence: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class FindingListResponse(BaseModel):
    """Schema for paginated finding list."""
    items: List[FindingResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Contract Schemas ==============

class ContractBase(BaseModel):
    """Base contract schema."""
    title: str
    description: Optional[str] = None
    contract_type: Optional[str] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: Optional[bool] = False
    notice_period_days: Optional[int] = None
    contract_value: Optional[int] = None
    annual_value: Optional[int] = None
    currency: Optional[str] = "USD"
    has_security_addendum: Optional[bool] = False
    has_dpa: Optional[bool] = False
    has_sla: Optional[bool] = False
    has_nda: Optional[bool] = False
    has_right_to_audit: Optional[bool] = False
    has_breach_notification: Optional[bool] = False
    breach_notification_hours: Optional[int] = None
    has_data_deletion_clause: Optional[bool] = False
    has_subprocessor_restrictions: Optional[bool] = False
    cyber_insurance_required: Optional[bool] = False
    cyber_insurance_minimum: Optional[int] = None
    contract_owner: Optional[str] = None
    legal_reviewer: Optional[str] = None
    security_reviewer: Optional[str] = None
    document_url: Optional[str] = None
    related_documents: Optional[List[str]] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    """Schema for creating a contract."""
    vendor_id: str


class ContractUpdate(BaseModel):
    """Schema for updating a contract."""
    title: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    status: Optional[ContractStatus] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    notice_period_days: Optional[int] = None
    contract_value: Optional[int] = None
    annual_value: Optional[int] = None
    currency: Optional[str] = None
    has_security_addendum: Optional[bool] = None
    has_dpa: Optional[bool] = None
    has_sla: Optional[bool] = None
    has_nda: Optional[bool] = None
    has_right_to_audit: Optional[bool] = None
    has_breach_notification: Optional[bool] = None
    breach_notification_hours: Optional[int] = None
    has_data_deletion_clause: Optional[bool] = None
    has_subprocessor_restrictions: Optional[bool] = None
    cyber_insurance_required: Optional[bool] = None
    cyber_insurance_minimum: Optional[int] = None
    cyber_insurance_verified: Optional[bool] = None
    contract_owner: Optional[str] = None
    legal_reviewer: Optional[str] = None
    security_reviewer: Optional[str] = None
    document_url: Optional[str] = None
    related_documents: Optional[List[str]] = None
    notes: Optional[str] = None


class ContractResponse(ContractBase):
    """Schema for contract response."""
    id: str
    contract_id: str
    vendor_id: str
    status: ContractStatus
    cyber_insurance_verified: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Schema for paginated contract list."""
    items: List[ContractResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Questionnaire Template Schemas ==============

class QuestionSchema(BaseModel):
    """Schema for a questionnaire question."""
    id: str
    question: str
    type: str  # yes_no, multiple_choice, text, file_upload
    required: bool = True
    weight: int = 1
    options: Optional[List[str]] = None
    control_reference: Optional[str] = None


class SectionSchema(BaseModel):
    """Schema for a questionnaire section."""
    name: str
    description: Optional[str] = None
    questions: List[QuestionSchema]


class QuestionnaireTemplateBase(BaseModel):
    """Base questionnaire template schema."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = "1.0"
    sections: List[SectionSchema]
    applicable_tiers: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    passing_score: Optional[int] = 70


class QuestionnaireTemplateCreate(QuestionnaireTemplateBase):
    """Schema for creating a questionnaire template."""
    pass


class QuestionnaireTemplateUpdate(BaseModel):
    """Schema for updating a questionnaire template."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    sections: Optional[List[SectionSchema]] = None
    applicable_tiers: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    passing_score: Optional[int] = None
    is_active: Optional[bool] = None


class QuestionnaireTemplateResponse(QuestionnaireTemplateBase):
    """Schema for questionnaire template response."""
    id: str
    total_points: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============== Dashboard Stats ==============

class TPRMDashboardStats(BaseModel):
    """Dashboard statistics for TPRM."""
    total_vendors: int
    vendors_by_status: dict
    vendors_by_tier: dict
    vendors_by_risk_rating: dict

    total_assessments: int
    assessments_pending: int
    assessments_overdue: int
    assessments_completed_this_month: int

    total_findings: int
    findings_by_severity: dict
    findings_open: int
    findings_overdue: int

    contracts_expiring_30_days: int
    contracts_expiring_90_days: int

    high_risk_vendors: int
    vendors_requiring_assessment: int
