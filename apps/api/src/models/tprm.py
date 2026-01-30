"""Third-Party Risk Management models."""
import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer, JSON, Date
from sqlalchemy.orm import relationship

from src.db.database import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid4())


class VendorStatus(str, enum.Enum):
    """Vendor lifecycle status."""
    PROSPECT = "prospect"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    TERMINATED = "terminated"


class VendorTier(str, enum.Enum):
    """Vendor criticality tier based on data access and business impact."""
    TIER_1 = "tier_1"  # Critical - high data access, business critical
    TIER_2 = "tier_2"  # Important - moderate data access
    TIER_3 = "tier_3"  # Standard - limited data access
    TIER_4 = "tier_4"  # Low - minimal/no data access


class VendorCategory(str, enum.Enum):
    """Vendor service category."""
    CLOUD_SERVICES = "cloud_services"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    PROFESSIONAL_SERVICES = "professional_services"
    MANAGED_SERVICES = "managed_services"
    DATA_PROCESSING = "data_processing"
    FINANCIAL_SERVICES = "financial_services"
    TELECOMMUNICATIONS = "telecommunications"
    PHYSICAL_SECURITY = "physical_security"
    OTHER = "other"


class AssessmentStatus(str, enum.Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    QUESTIONNAIRE_SENT = "questionnaire_sent"
    QUESTIONNAIRE_RECEIVED = "questionnaire_received"
    UNDER_REVIEW = "under_review"
    PENDING_REMEDIATION = "pending_remediation"
    COMPLETED = "completed"
    EXPIRED = "expired"


class AssessmentType(str, enum.Enum):
    """Type of vendor assessment."""
    INITIAL = "initial"
    ANNUAL = "annual"
    TRIGGERED = "triggered"  # Event-triggered reassessment
    CONTINUOUS = "continuous"


class RiskRating(str, enum.Enum):
    """Overall risk rating."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ContractStatus(str, enum.Enum):
    """Contract status."""
    DRAFT = "draft"
    UNDER_NEGOTIATION = "under_negotiation"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Vendor(Base):
    """Third-party vendor/supplier."""
    __tablename__ = "tprm_vendors"

    id = Column(String, primary_key=True, default=generate_uuid)
    vendor_id = Column(String, unique=True, nullable=False)  # VND-0001
    name = Column(String, nullable=False)
    legal_name = Column(String)
    description = Column(Text)

    # Classification
    status = Column(Enum(VendorStatus), default=VendorStatus.PROSPECT)
    tier = Column(Enum(VendorTier), default=VendorTier.TIER_3)
    category = Column(Enum(VendorCategory), default=VendorCategory.OTHER)

    # Contact information
    website = Column(String)
    primary_contact_name = Column(String)
    primary_contact_email = Column(String)
    primary_contact_phone = Column(String)
    address = Column(Text)
    country = Column(String)

    # Business relationship
    services_provided = Column(Text)
    data_types_shared = Column(JSON)  # List of data types shared with vendor
    has_pii_access = Column(Boolean, default=False)
    has_phi_access = Column(Boolean, default=False)  # Protected Health Information
    has_pci_access = Column(Boolean, default=False)  # Payment Card Data
    has_network_access = Column(Boolean, default=False)
    has_physical_access = Column(Boolean, default=False)

    # Risk information
    current_risk_rating = Column(Enum(RiskRating))
    inherent_risk_score = Column(Integer)  # 0-100
    residual_risk_score = Column(Integer)  # 0-100
    last_assessment_date = Column(DateTime)
    next_assessment_due = Column(DateTime)

    # Compliance & certifications
    certifications = Column(JSON)  # List of certifications (ISO 27001, SOC 2, etc.)
    compliance_frameworks = Column(JSON)  # Applicable frameworks

    # Internal ownership
    business_owner = Column(String)
    risk_owner = Column(String)

    # Metadata
    onboarding_date = Column(DateTime)
    offboarding_date = Column(DateTime)
    notes = Column(Text)
    tags = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    assessments = relationship("VendorAssessment", back_populates="vendor", cascade="all, delete-orphan")
    contracts = relationship("VendorContract", back_populates="vendor", cascade="all, delete-orphan")
    findings = relationship("AssessmentFinding", back_populates="vendor", cascade="all, delete-orphan")


class VendorAssessment(Base):
    """Security assessment of a vendor."""
    __tablename__ = "tprm_assessments"

    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, unique=True, nullable=False)  # ASM-2024-0001
    vendor_id = Column(String, ForeignKey("tprm_vendors.id"), nullable=False)

    # Assessment details
    assessment_type = Column(Enum(AssessmentType), default=AssessmentType.INITIAL)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    title = Column(String, nullable=False)
    description = Column(Text)

    # Questionnaire
    questionnaire_template = Column(String)  # Template name/ID used
    questionnaire_sent_date = Column(DateTime)
    questionnaire_due_date = Column(DateTime)
    questionnaire_received_date = Column(DateTime)
    questionnaire_responses = Column(JSON)  # Structured responses

    # Scoring
    security_score = Column(Integer)  # 0-100
    privacy_score = Column(Integer)  # 0-100
    compliance_score = Column(Integer)  # 0-100
    operational_score = Column(Integer)  # 0-100
    overall_score = Column(Integer)  # 0-100

    # Risk determination
    inherent_risk = Column(Enum(RiskRating))
    control_effectiveness = Column(Integer)  # 0-100 percentage
    residual_risk = Column(Enum(RiskRating))
    risk_accepted = Column(Boolean, default=False)
    risk_accepted_by = Column(String)
    risk_acceptance_date = Column(DateTime)
    risk_acceptance_expiry = Column(DateTime)

    # Review details
    assessor = Column(String)
    reviewer = Column(String)
    review_notes = Column(Text)

    # Evidence
    evidence_documents = Column(JSON)  # List of document references

    # Dates
    initiated_date = Column(DateTime, default=datetime.utcnow)
    completed_date = Column(DateTime)
    valid_until = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    vendor = relationship("Vendor", back_populates="assessments")
    findings = relationship("AssessmentFinding", back_populates="assessment", cascade="all, delete-orphan")


class FindingSeverity(str, enum.Enum):
    """Finding severity level."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, enum.Enum):
    """Finding remediation status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class AssessmentFinding(Base):
    """Security finding from vendor assessment."""
    __tablename__ = "tprm_findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    finding_id = Column(String, unique=True, nullable=False)  # FND-2024-0001
    assessment_id = Column(String, ForeignKey("tprm_assessments.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("tprm_vendors.id"), nullable=False)

    # Finding details
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(Enum(FindingSeverity), default=FindingSeverity.MEDIUM)
    status = Column(Enum(FindingStatus), default=FindingStatus.OPEN)

    # Categorization
    control_domain = Column(String)  # e.g., "Access Control", "Encryption"
    control_reference = Column(String)  # e.g., "ISO 27001 A.9.1"

    # Risk
    risk_description = Column(Text)
    business_impact = Column(Text)
    likelihood = Column(Integer)  # 1-5
    impact = Column(Integer)  # 1-5
    risk_score = Column(Integer)  # likelihood * impact

    # Remediation
    recommendation = Column(Text)
    vendor_response = Column(Text)
    remediation_plan = Column(Text)
    remediation_due_date = Column(DateTime)
    remediation_completed_date = Column(DateTime)

    # Acceptance (if risk is accepted)
    accepted_by = Column(String)
    acceptance_justification = Column(Text)
    acceptance_expiry = Column(DateTime)

    # Evidence
    evidence = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    assessment = relationship("VendorAssessment", back_populates="findings")
    vendor = relationship("Vendor", back_populates="findings")


class VendorContract(Base):
    """Contract with vendor including security terms."""
    __tablename__ = "tprm_contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, unique=True, nullable=False)  # CTR-2024-0001
    vendor_id = Column(String, ForeignKey("tprm_vendors.id"), nullable=False)

    # Contract details
    title = Column(String, nullable=False)
    description = Column(Text)
    contract_type = Column(String)  # MSA, SLA, DPA, NDA, etc.
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)

    # Dates
    effective_date = Column(Date)
    expiration_date = Column(Date)
    renewal_date = Column(Date)
    auto_renewal = Column(Boolean, default=False)
    notice_period_days = Column(Integer)  # Days notice required for termination

    # Financial
    contract_value = Column(Integer)  # Total value
    annual_value = Column(Integer)
    currency = Column(String, default="USD")

    # Security terms
    has_security_addendum = Column(Boolean, default=False)
    has_dpa = Column(Boolean, default=False)  # Data Processing Agreement
    has_sla = Column(Boolean, default=False)
    has_nda = Column(Boolean, default=False)
    has_right_to_audit = Column(Boolean, default=False)
    has_breach_notification = Column(Boolean, default=False)
    breach_notification_hours = Column(Integer)  # Hours to notify
    has_data_deletion_clause = Column(Boolean, default=False)
    has_subprocessor_restrictions = Column(Boolean, default=False)

    # Insurance
    cyber_insurance_required = Column(Boolean, default=False)
    cyber_insurance_minimum = Column(Integer)
    cyber_insurance_verified = Column(Boolean, default=False)

    # Ownership
    contract_owner = Column(String)
    legal_reviewer = Column(String)
    security_reviewer = Column(String)

    # Documents
    document_url = Column(String)
    related_documents = Column(JSON)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    vendor = relationship("Vendor", back_populates="contracts")


class QuestionnaireTemplate(Base):
    """Reusable security questionnaire template."""
    __tablename__ = "tprm_questionnaire_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    version = Column(String, default="1.0")

    # Template structure
    sections = Column(JSON)  # Structured sections and questions
    """
    sections format:
    [
        {
            "name": "Access Control",
            "description": "Questions about access management",
            "questions": [
                {
                    "id": "AC-1",
                    "question": "Do you have a formal access control policy?",
                    "type": "yes_no",
                    "required": true,
                    "weight": 5,
                    "control_reference": "ISO 27001 A.9"
                }
            ]
        }
    ]
    """

    # Applicability
    applicable_tiers = Column(JSON)  # Which vendor tiers this applies to
    applicable_categories = Column(JSON)  # Which vendor categories

    # Scoring
    total_points = Column(Integer)
    passing_score = Column(Integer)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
