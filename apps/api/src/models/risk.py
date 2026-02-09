"""
Risk Management Models.

Database models for Risk Register, Risk Assessments, and Treatment Plans.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float, Boolean,
    ForeignKey, Table, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base
from src.models.mixins import TenantMixin


class RiskCategory(str, enum.Enum):
    """Risk category classification."""
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"
    TECHNICAL = "technical"
    SECURITY = "security"
    LEGAL = "legal"


class RiskStatus(str, enum.Enum):
    """Risk lifecycle status."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    TREATMENT_PLANNED = "treatment_planned"
    TREATMENT_IN_PROGRESS = "treatment_in_progress"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    TRANSFERRED = "transferred"
    CLOSED = "closed"
    MONITORING = "monitoring"


class LikelihoodLevel(str, enum.Enum):
    """Likelihood of risk occurrence."""
    RARE = "rare"           # 1 - < 10%
    UNLIKELY = "unlikely"   # 2 - 10-30%
    POSSIBLE = "possible"   # 3 - 30-50%
    LIKELY = "likely"       # 4 - 50-70%
    ALMOST_CERTAIN = "almost_certain"  # 5 - > 70%


class ImpactLevel(str, enum.Enum):
    """Impact if risk materializes."""
    NEGLIGIBLE = "negligible"   # 1
    MINOR = "minor"             # 2
    MODERATE = "moderate"       # 3
    MAJOR = "major"             # 4
    CATASTROPHIC = "catastrophic"  # 5


class RiskLevel(str, enum.Enum):
    """Calculated risk level."""
    LOW = "low"           # 1-4
    MEDIUM = "medium"     # 5-9
    HIGH = "high"         # 10-16
    CRITICAL = "critical" # 17-25


class TreatmentType(str, enum.Enum):
    """Risk treatment approach."""
    MITIGATE = "mitigate"     # Reduce likelihood or impact
    ACCEPT = "accept"         # Accept the risk
    TRANSFER = "transfer"     # Transfer to third party (insurance, outsource)
    AVOID = "avoid"           # Eliminate the risk source


class ControlType(str, enum.Enum):
    """Type of risk control."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    COMPENSATING = "compensating"


class ControlStatus(str, enum.Enum):
    """Control implementation status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    NOT_EFFECTIVE = "not_effective"
    RETIRED = "retired"


# Association tables
risk_control_association = Table(
    'risk_control_association',
    Base.metadata,
    Column('risk_id', String(36), ForeignKey('risks.id'), primary_key=True),
    Column('control_id', String(36), ForeignKey('risk_controls.id'), primary_key=True)
)

risk_vulnerability_association = Table(
    'risk_vulnerability_association',
    Base.metadata,
    Column('risk_id', String(36), ForeignKey('risks.id'), primary_key=True),
    Column('vulnerability_id', String(36), ForeignKey('vulnerabilities.id'), primary_key=True)
)

risk_threat_association = Table(
    'risk_threat_association',
    Base.metadata,
    Column('risk_id', String(36), ForeignKey('risks.id'), primary_key=True),
    Column('threat_actor_id', String(36), ForeignKey('threat_actors.id'), primary_key=True)
)


class Risk(TenantMixin, Base):
    """Risk Register entry."""
    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    risk_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g., RISK-2024-001
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    category = mapped_column(SQLEnum(RiskCategory), nullable=False, index=True)
    status = mapped_column(SQLEnum(RiskStatus), default=RiskStatus.IDENTIFIED, index=True)

    # Risk Source
    risk_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    threat_scenario: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Inherent Risk Assessment (before controls)
    inherent_likelihood = mapped_column(SQLEnum(LikelihoodLevel), nullable=True)
    inherent_impact = mapped_column(SQLEnum(ImpactLevel), nullable=True)
    inherent_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inherent_risk_level = mapped_column(SQLEnum(RiskLevel), nullable=True)

    # Residual Risk Assessment (after controls)
    residual_likelihood = mapped_column(SQLEnum(LikelihoodLevel), nullable=True)
    residual_impact = mapped_column(SQLEnum(ImpactLevel), nullable=True)
    residual_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    residual_risk_level = mapped_column(SQLEnum(RiskLevel), nullable=True)

    # Target Risk (desired state)
    target_likelihood = mapped_column(SQLEnum(LikelihoodLevel), nullable=True)
    target_impact = mapped_column(SQLEnum(ImpactLevel), nullable=True)
    target_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Impact Details
    financial_impact: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Estimated $ impact
    operational_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reputational_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Treatment
    treatment_type = mapped_column(SQLEnum(TreatmentType), nullable=True)
    treatment_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    treatment_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    treatment_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Risk Acceptance (if accepted)
    acceptance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acceptance_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Ownership
    risk_owner: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Affected Areas
    affected_assets = mapped_column(JSON, default=[])
    affected_processes = mapped_column(JSON, default=[])
    affected_data_types = mapped_column(JSON, default=[])

    # Compliance mapping
    compliance_frameworks = mapped_column(JSON, default=[])  # ISO27001, NIST, etc.
    compliance_controls = mapped_column(JSON, default=[])

    # Metadata
    tags = mapped_column(JSON, default=[])
    external_refs = mapped_column(JSON, default={})

    # Review
    last_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_frequency_days: Mapped[int] = mapped_column(Integer, default=90)

    # Timestamps
    identified_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # User tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Related incidents
    incident_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=True)

    # Relationships
    controls = relationship(
        "RiskControl",
        secondary=risk_control_association,
        back_populates="risks"
    )
    assessments = relationship("RiskAssessment", back_populates="risk", cascade="all, delete-orphan")
    treatment_actions = relationship("TreatmentAction", back_populates="risk", cascade="all, delete-orphan")
    incident = relationship("Incident", foreign_keys=[incident_id])


class RiskControl(TenantMixin, Base):
    """Risk control/mitigation measure."""
    __tablename__ = "risk_controls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    control_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g., CTRL-001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    control_type = mapped_column(SQLEnum(ControlType), nullable=False)
    status = mapped_column(SQLEnum(ControlStatus), default=ControlStatus.PLANNED)

    # Implementation
    implementation_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    implemented_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Effectiveness
    effectiveness_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100%
    last_tested: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    test_results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost
    implementation_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    annual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Ownership
    control_owner: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Compliance mapping
    compliance_frameworks = mapped_column(JSON, default=[])
    compliance_control_ids = mapped_column(JSON, default=[])

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    risks = relationship(
        "Risk",
        secondary=risk_control_association,
        back_populates="controls"
    )


class RiskAssessment(TenantMixin, Base):
    """Risk assessment history."""
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    risk_id: Mapped[str] = mapped_column(String(36), ForeignKey("risks.id"), nullable=False)

    # Assessment type
    assessment_type: Mapped[str] = mapped_column(String(50), default="periodic")  # initial, periodic, triggered

    # Assessment values
    likelihood = mapped_column(SQLEnum(LikelihoodLevel), nullable=False)
    impact = mapped_column(SQLEnum(ImpactLevel), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level = mapped_column(SQLEnum(RiskLevel), nullable=False)

    # Context
    assessment_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assumptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    assessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assessed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    risk = relationship("Risk", back_populates="assessments")


class TreatmentAction(TenantMixin, Base):
    """Risk treatment action items."""
    __tablename__ = "treatment_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    risk_id: Mapped[str] = mapped_column(String(36), ForeignKey("risks.id"), nullable=False)

    # Action details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical

    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Timeline
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Cost
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Expected outcome
    expected_risk_reduction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    risk = relationship("Risk", back_populates="treatment_actions")


class RiskAppetite(TenantMixin, Base):
    """Organization risk appetite settings."""
    __tablename__ = "risk_appetite"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Category-specific appetite
    category = mapped_column(SQLEnum(RiskCategory), nullable=False, unique=True)

    # Appetite levels
    appetite_level = mapped_column(SQLEnum(RiskLevel), nullable=False)  # Maximum acceptable risk
    tolerance_threshold: Mapped[float] = mapped_column(Float, default=0.0)  # Risk score threshold

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Financial thresholds
    max_single_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_annual_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Approval requirements
    requires_board_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_executive_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
