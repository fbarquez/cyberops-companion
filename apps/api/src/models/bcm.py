"""
Business Continuity Management (BCM) Models.

Database models based on BSI Standard 200-4 and ISO 22301.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import (
    Column, String, DateTime, Date, Text, Integer, Float,
    ForeignKey, Enum as SQLEnum, JSON, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base
from src.models.mixins import TenantMixin


# ========== Enums ==========

class BCMProcessCriticality(str, enum.Enum):
    """Business process criticality levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BCMProcessStatus(str, enum.Enum):
    """Business process status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"


class BCMImpactLevel(str, enum.Enum):
    """Impact assessment levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BCMBIAStatus(str, enum.Enum):
    """BIA assessment status."""
    DRAFT = "draft"
    COMPLETED = "completed"
    APPROVED = "approved"
    OUTDATED = "outdated"


class BCMScenarioCategory(str, enum.Enum):
    """Risk scenario categories based on BSI 200-4."""
    NATURAL_DISASTER = "natural_disaster"
    TECHNICAL_FAILURE = "technical_failure"
    HUMAN_ERROR = "human_error"
    CYBER_ATTACK = "cyber_attack"
    PANDEMIC = "pandemic"
    SUPPLY_CHAIN = "supply_chain"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class BCMLikelihood(str, enum.Enum):
    """Risk likelihood levels (1-5)."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class BCMImpact(str, enum.Enum):
    """Risk impact levels (1-5)."""
    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class BCMControlEffectiveness(str, enum.Enum):
    """Effectiveness of existing controls."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BCMScenarioStatus(str, enum.Enum):
    """Scenario assessment status."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"


class BCMStrategyType(str, enum.Enum):
    """Continuity strategy types."""
    DO_NOTHING = "do_nothing"
    MANUAL_WORKAROUND = "manual_workaround"
    ALTERNATE_SITE = "alternate_site"
    ALTERNATE_SUPPLIER = "alternate_supplier"
    REDUNDANCY = "redundancy"
    OUTSOURCE = "outsource"
    INSURANCE = "insurance"


class BCMStrategyStatus(str, enum.Enum):
    """Strategy implementation status."""
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    APPROVED = "approved"


class BCMPlanType(str, enum.Enum):
    """Emergency plan types."""
    CRISIS_MANAGEMENT = "crisis_management"
    EMERGENCY_RESPONSE = "emergency_response"
    BUSINESS_RECOVERY = "business_recovery"
    IT_DISASTER_RECOVERY = "it_disaster_recovery"
    COMMUNICATION = "communication"
    EVACUATION = "evacuation"


class BCMPlanStatus(str, enum.Enum):
    """Emergency plan status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BCMContactType(str, enum.Enum):
    """Emergency contact types."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    VENDOR = "vendor"
    AUTHORITY = "authority"


class BCMContactAvailability(str, enum.Enum):
    """Contact availability."""
    TWENTY_FOUR_SEVEN = "24x7"
    BUSINESS_HOURS = "business_hours"
    ON_CALL = "on_call"


class BCMExerciseType(str, enum.Enum):
    """Exercise/test types."""
    TABLETOP = "tabletop"
    WALKTHROUGH = "walkthrough"
    SIMULATION = "simulation"
    PARALLEL_TEST = "parallel_test"
    FULL_INTERRUPTION = "full_interruption"


class BCMExerciseStatus(str, enum.Enum):
    """Exercise status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BCMAssessmentStatus(str, enum.Enum):
    """BCM assessment wizard status."""
    DRAFT = "draft"
    PROCESS_INVENTORY = "process_inventory"
    BIA_ANALYSIS = "bia_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_PLANNING = "strategy_planning"
    PLAN_DEVELOPMENT = "plan_development"
    TESTING = "testing"
    COMPLETED = "completed"


# ========== Models ==========

class BCMProcess(TenantMixin, Base):
    """Business processes to protect."""
    __tablename__ = "bcm_processes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Process identification
    process_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "PROC-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)  # Process owner name
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Criticality
    criticality = mapped_column(SQLEnum(BCMProcessCriticality), default=BCMProcessCriticality.MEDIUM, nullable=False)

    # Dependencies (JSON arrays)
    internal_dependencies = mapped_column(JSON, default=[])  # Other process IDs
    external_dependencies = mapped_column(JSON, default=[])  # External services/vendors
    it_systems = mapped_column(JSON, default=[])  # CMDB asset IDs
    key_personnel = mapped_column(JSON, default=[])  # User IDs or names

    # Status
    status = mapped_column(SQLEnum(BCMProcessStatus), default=BCMProcessStatus.ACTIVE, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    bia = relationship("BCMBIA", back_populates="process", cascade="all, delete-orphan", uselist=False)
    strategies = relationship("BCMStrategy", back_populates="process", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class BCMBIA(TenantMixin, Base):
    """Business Impact Analysis for a process."""
    __tablename__ = "bcm_bia"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    process_id: Mapped[str] = mapped_column(String(36), ForeignKey("bcm_processes.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Recovery objectives (in hours)
    rto_hours: Mapped[int] = mapped_column(Integer, default=24)  # Recovery Time Objective
    rpo_hours: Mapped[int] = mapped_column(Integer, default=4)   # Recovery Point Objective
    mtpd_hours: Mapped[int] = mapped_column(Integer, default=72) # Maximum Tolerable Period of Disruption

    # Impact analysis by time period
    impact_1h = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.LOW)
    impact_4h = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.LOW)
    impact_8h = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.MEDIUM)
    impact_24h = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.HIGH)
    impact_72h = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.CRITICAL)
    impact_1w = mapped_column(SQLEnum(BCMImpactLevel), default=BCMImpactLevel.CRITICAL)

    # Impact categories (1-5 scale)
    financial_impact: Mapped[int] = mapped_column(Integer, default=3)
    operational_impact: Mapped[int] = mapped_column(Integer, default=3)
    reputational_impact: Mapped[int] = mapped_column(Integer, default=3)
    legal_impact: Mapped[int] = mapped_column(Integer, default=3)
    safety_impact: Mapped[int] = mapped_column(Integer, default=3)

    # Justifications
    financial_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operational_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Resource requirements for recovery
    minimum_staff: Mapped[int] = mapped_column(Integer, default=1)
    minimum_workspace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    critical_equipment = mapped_column(JSON, default=[])
    critical_data = mapped_column(JSON, default=[])

    # Analysis metadata
    analysis_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analyst: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status = mapped_column(SQLEnum(BCMBIAStatus), default=BCMBIAStatus.DRAFT)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    process = relationship("BCMProcess", back_populates="bia")


class BCMRiskScenario(TenantMixin, Base):
    """Risk scenarios that could disrupt business."""
    __tablename__ = "bcm_risk_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Scenario identification
    scenario_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "SCEN-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Categorization
    category = mapped_column(SQLEnum(BCMScenarioCategory), default=BCMScenarioCategory.OTHER, nullable=False)

    # Risk assessment
    likelihood = mapped_column(SQLEnum(BCMLikelihood), default=BCMLikelihood.POSSIBLE)
    impact = mapped_column(SQLEnum(BCMImpact), default=BCMImpact.MODERATE)
    risk_score: Mapped[int] = mapped_column(Integer, default=9)  # likelihood * impact (1-25)

    # Affected processes (JSON array of process IDs)
    affected_processes = mapped_column(JSON, default=[])

    # Single Points of Failure identified
    single_points_of_failure = mapped_column(JSON, default=[])

    # Existing controls
    existing_controls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    control_effectiveness = mapped_column(SQLEnum(BCMControlEffectiveness), default=BCMControlEffectiveness.MEDIUM)

    # Status
    status = mapped_column(SQLEnum(BCMScenarioStatus), default=BCMScenarioStatus.IDENTIFIED)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assessed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    exercises = relationship("BCMExercise", back_populates="scenario")
    assessor = relationship("User", foreign_keys=[assessed_by])


class BCMStrategy(TenantMixin, Base):
    """Continuity strategies for processes."""
    __tablename__ = "bcm_strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    process_id: Mapped[str] = mapped_column(String(36), ForeignKey("bcm_processes.id", ondelete="CASCADE"), nullable=False)

    # Strategy type
    strategy_type = mapped_column(SQLEnum(BCMStrategyType), default=BCMStrategyType.MANUAL_WORKAROUND, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Implementation details
    activation_trigger: Mapped[str] = mapped_column(Text, nullable=False)  # When to activate
    activation_procedure: Mapped[str] = mapped_column(Text, nullable=False)
    resource_requirements = mapped_column(JSON, default=[])
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    # Recovery targets
    achievable_rto_hours: Mapped[int] = mapped_column(Integer, default=24)
    achievable_rpo_hours: Mapped[int] = mapped_column(Integer, default=4)

    # Status
    status = mapped_column(SQLEnum(BCMStrategyStatus), default=BCMStrategyStatus.PLANNED)
    implementation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    process = relationship("BCMProcess", back_populates="strategies")


class BCMEmergencyPlan(TenantMixin, Base):
    """Emergency/contingency plans (Notfallkonzept)."""
    __tablename__ = "bcm_emergency_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Plan identification
    plan_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "PLAN-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Plan type
    plan_type = mapped_column(SQLEnum(BCMPlanType), default=BCMPlanType.BUSINESS_RECOVERY, nullable=False)

    # Scope
    scope_description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_processes = mapped_column(JSON, default=[])  # Process IDs
    affected_locations = mapped_column(JSON, default=[])  # Location names

    # Plan content (structured JSON)
    activation_criteria = mapped_column(JSON, default=[])   # When to activate
    response_phases = mapped_column(JSON, default=[])       # Phase definitions
    procedures = mapped_column(JSON, default=[])            # Step-by-step procedures
    roles_responsibilities = mapped_column(JSON, default=[])  # Team roles
    communication_tree = mapped_column(JSON, default=[])    # Escalation paths
    contact_list = mapped_column(JSON, default=[])          # Emergency contacts
    resources_required = mapped_column(JSON, default=[])    # What's needed

    # Checklists
    activation_checklist = mapped_column(JSON, default=[])
    recovery_checklist = mapped_column(JSON, default=[])

    # Version control
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    effective_date: Mapped[date] = mapped_column(Date, default=date.today)
    review_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Approval
    status = mapped_column(SQLEnum(BCMPlanStatus), default=BCMPlanStatus.DRAFT)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    exercises = relationship("BCMExercise", back_populates="plan")
    creator = relationship("User", foreign_keys=[created_by])


class BCMContact(TenantMixin, Base):
    """Emergency contact list."""
    __tablename__ = "bcm_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Contact info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Crisis Manager"
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Contact methods
    phone_primary: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Availability
    availability = mapped_column(SQLEnum(BCMContactAvailability), default=BCMContactAvailability.BUSINESS_HOURS)

    # Categories
    contact_type = mapped_column(SQLEnum(BCMContactType), default=BCMContactType.INTERNAL)

    # Priority in contact tree
    priority: Mapped[int] = mapped_column(Integer, default=10)  # 1 = first contact

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BCMExercise(TenantMixin, Base):
    """Business continuity exercises/tests."""
    __tablename__ = "bcm_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Exercise identification
    exercise_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "EX-2024-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Type
    exercise_type = mapped_column(SQLEnum(BCMExerciseType), default=BCMExerciseType.TABLETOP, nullable=False)

    # Planning
    scenario_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("bcm_risk_scenarios.id", ondelete="SET NULL"), nullable=True)
    plan_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("bcm_emergency_plans.id", ondelete="SET NULL"), nullable=True)

    objectives = mapped_column(JSON, default=[])  # What we want to test
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    participants = mapped_column(JSON, default=[])  # Who's involved

    # Scheduling
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_duration_hours: Mapped[int] = mapped_column(Integer, default=4)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_duration_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Results
    status = mapped_column(SQLEnum(BCMExerciseStatus), default=BCMExerciseStatus.PLANNED)
    results_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectives_met = mapped_column(JSON, default={})  # Boolean per objective
    issues_identified = mapped_column(JSON, default=[])  # Problems found
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Improvements
    action_items = mapped_column(JSON, default=[])  # Follow-up actions

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conducted_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    scenario = relationship("BCMRiskScenario", back_populates="exercises")
    plan = relationship("BCMEmergencyPlan", back_populates="exercises")
    conductor = relationship("User", foreign_keys=[conducted_by])


class BCMAssessment(TenantMixin, Base):
    """Overall BCM program maturity assessment."""
    __tablename__ = "bcm_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status workflow (wizard steps)
    status = mapped_column(SQLEnum(BCMAssessmentStatus), default=BCMAssessmentStatus.DRAFT, index=True)

    # Scores (0-100)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    process_coverage_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bia_completion_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    strategy_coverage_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    plan_coverage_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_coverage_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Counts
    total_processes: Mapped[int] = mapped_column(Integer, default=0)
    critical_processes: Mapped[int] = mapped_column(Integer, default=0)
    processes_with_bia: Mapped[int] = mapped_column(Integer, default=0)
    processes_with_strategy: Mapped[int] = mapped_column(Integer, default=0)
    processes_with_plan: Mapped[int] = mapped_column(Integer, default=0)
    plans_tested_this_year: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    assessment_date: Mapped[date] = mapped_column(Date, default=date.today)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
