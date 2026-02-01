"""
SOC (Security Operations Center) Models.

Models for alert management, case management, and playbook automation.
"""
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, JSON, Table
)
from sqlalchemy.orm import relationship
from src.db.database import Base
from src.models.mixins import TenantMixin
import uuid


def generate_uuid():
    return str(uuid.uuid4())


# ==================== Enums ====================

class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AlertStatus(str, enum.Enum):
    """Alert status."""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class AlertSource(str, enum.Enum):
    """Source of alerts."""
    SIEM = "siem"
    EDR = "edr"
    IDS = "ids"
    FIREWALL = "firewall"
    WAF = "waf"
    EMAIL_GATEWAY = "email_gateway"
    CLOUD_SECURITY = "cloud_security"
    VULNERABILITY_SCANNER = "vulnerability_scanner"
    THREAT_INTEL = "threat_intel"
    USER_REPORT = "user_report"
    MANUAL = "manual"
    OTHER = "other"


class CaseStatus(str, enum.Enum):
    """Case status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CasePriority(str, enum.Enum):
    """Case priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlaybookStatus(str, enum.Enum):
    """Playbook status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class PlaybookTriggerType(str, enum.Enum):
    """Playbook trigger types."""
    MANUAL = "manual"
    ALERT_CREATED = "alert_created"
    ALERT_SEVERITY = "alert_severity"
    ALERT_SOURCE = "alert_source"
    CASE_CREATED = "case_created"
    SCHEDULED = "scheduled"
    IOC_MATCH = "ioc_match"


class ActionType(str, enum.Enum):
    """Playbook action types."""
    ENRICH = "enrich"
    NOTIFY = "notify"
    BLOCK = "block"
    ISOLATE = "isolate"
    QUARANTINE = "quarantine"
    CREATE_TICKET = "create_ticket"
    RUN_SCRIPT = "run_script"
    API_CALL = "api_call"
    ASSIGN = "assign"
    ESCALATE = "escalate"
    CLOSE = "close"
    CUSTOM = "custom"


class ExecutionStatus(str, enum.Enum):
    """Playbook execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


# ==================== Association Tables ====================

alert_ioc_association = Table(
    'alert_ioc_association',
    Base.metadata,
    Column('alert_id', String, ForeignKey('soc_alerts.id'), primary_key=True),
    Column('ioc_id', String, ForeignKey('iocs.id'), primary_key=True)
)

case_alert_association = Table(
    'case_alert_association',
    Base.metadata,
    Column('case_id', String, ForeignKey('soc_cases.id'), primary_key=True),
    Column('alert_id', String, ForeignKey('soc_alerts.id'), primary_key=True)
)


# ==================== Models ====================

class SOCAlert(TenantMixin, Base):
    """Security alert from various sources."""
    __tablename__ = "soc_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    alert_id = Column(String, unique=True, nullable=False, index=True)  # External alert ID or auto-generated
    title = Column(String, nullable=False)
    description = Column(Text)

    # Classification
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    status = Column(Enum(AlertStatus), default=AlertStatus.NEW)
    source = Column(Enum(AlertSource), default=AlertSource.OTHER)
    source_ref = Column(String)  # Reference ID in source system

    # Detection details
    detection_rule = Column(String)  # Rule/signature that triggered
    mitre_tactics = Column(JSON)  # List of MITRE tactics
    mitre_techniques = Column(JSON)  # List of MITRE techniques

    # Affected entities
    affected_assets = Column(JSON)  # List of asset IDs or names
    affected_users = Column(JSON)  # List of usernames
    source_ip = Column(String)
    destination_ip = Column(String)

    # Enrichment data
    enrichment_data = Column(JSON)  # IOC enrichment, threat intel, etc.
    risk_score = Column(Float)  # Calculated risk score (0-100)
    confidence = Column(Float)  # Detection confidence (0-100)

    # Assignment
    assigned_to = Column(String)
    assigned_at = Column(DateTime)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)

    # Resolution
    resolution_notes = Column(Text)
    false_positive_reason = Column(Text)

    # Correlation
    correlation_id = Column(String)  # Group related alerts
    parent_alert_id = Column(String, ForeignKey('soc_alerts.id'))

    # Metadata
    tags = Column(JSON)
    raw_event = Column(JSON)  # Original event data
    custom_fields = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    iocs = relationship("IOC", secondary=alert_ioc_association, backref="alerts")
    comments = relationship("AlertComment", back_populates="alert", cascade="all, delete-orphan")
    child_alerts = relationship("SOCAlert", backref="parent_alert", remote_side=[id])
    executions = relationship("PlaybookExecution", back_populates="alert")


class AlertComment(TenantMixin, Base):
    """Comments on alerts."""
    __tablename__ = "alert_comments"

    id = Column(String, primary_key=True, default=generate_uuid)
    alert_id = Column(String, ForeignKey('soc_alerts.id'), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("SOCAlert", back_populates="comments")


class SOCCase(TenantMixin, Base):
    """Investigation case combining multiple alerts."""
    __tablename__ = "soc_cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_number = Column(String, unique=True, nullable=False, index=True)  # CASE-2024-0001
    title = Column(String, nullable=False)
    description = Column(Text)

    # Classification
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM)
    case_type = Column(String)  # Malware, Phishing, Data Breach, etc.

    # Assignment
    assigned_to = Column(String)
    assigned_team = Column(String)
    escalated_to = Column(String)
    escalation_reason = Column(Text)

    # Timeline
    opened_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    escalated_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Investigation
    investigation_notes = Column(Text)
    root_cause = Column(Text)
    impact_assessment = Column(Text)

    # Resolution
    resolution_summary = Column(Text)
    lessons_learned = Column(Text)

    # Metrics
    time_to_detect = Column(Integer)  # Seconds
    time_to_respond = Column(Integer)  # Seconds
    time_to_resolve = Column(Integer)  # Seconds

    # Links
    incident_id = Column(String, ForeignKey('incidents.id'))

    # Metadata
    tags = Column(JSON)
    custom_fields = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    alerts = relationship("SOCAlert", secondary=case_alert_association, backref="cases")
    tasks = relationship("CaseTask", back_populates="case", cascade="all, delete-orphan")
    timeline_entries = relationship("CaseTimeline", back_populates="case", cascade="all, delete-orphan")


class CaseTask(TenantMixin, Base):
    """Tasks within a case."""
    __tablename__ = "case_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey('soc_cases.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)

    status = Column(String, default="pending")  # pending, in_progress, completed, blocked
    priority = Column(String, default="medium")
    assigned_to = Column(String)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)

    case = relationship("SOCCase", back_populates="tasks")


class CaseTimeline(TenantMixin, Base):
    """Timeline entries for case investigation."""
    __tablename__ = "case_timeline"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey('soc_cases.id'), nullable=False)

    event_time = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False)  # alert, action, note, escalation, etc.
    description = Column(Text, nullable=False)

    author = Column(String)
    evidence_ids = Column(JSON)  # Related evidence

    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("SOCCase", back_populates="timeline_entries")


class SOCPlaybook(TenantMixin, Base):
    """Automated response playbook."""
    __tablename__ = "soc_playbooks"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Status
    status = Column(Enum(PlaybookStatus), default=PlaybookStatus.DRAFT)
    version = Column(String, default="1.0")

    # Trigger configuration
    trigger_type = Column(Enum(PlaybookTriggerType), default=PlaybookTriggerType.MANUAL)
    trigger_conditions = Column(JSON)  # Conditions for auto-trigger

    # Actions
    actions = Column(JSON)  # Ordered list of actions

    # Settings
    is_enabled = Column(Boolean, default=True)
    run_automatically = Column(Boolean, default=False)
    require_approval = Column(Boolean, default=True)
    max_concurrent_runs = Column(Integer, default=5)
    timeout_seconds = Column(Integer, default=3600)

    # Metrics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    avg_execution_time = Column(Float)  # Seconds

    # Metadata
    tags = Column(JSON)
    category = Column(String)  # Enrichment, Response, Remediation, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    executions = relationship("PlaybookExecution", back_populates="playbook")


class PlaybookExecution(TenantMixin, Base):
    """Playbook execution record."""
    __tablename__ = "playbook_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    playbook_id = Column(String, ForeignKey('soc_playbooks.id'), nullable=False)

    # Trigger context
    alert_id = Column(String, ForeignKey('soc_alerts.id'))
    case_id = Column(String, ForeignKey('soc_cases.id'))
    trigger_reason = Column(String)

    # Execution
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Results
    action_results = Column(JSON)  # Results of each action
    error_message = Column(Text)

    # Approval
    approved_by = Column(String)
    approved_at = Column(DateTime)
    rejected_by = Column(String)
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)

    executed_by = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    playbook = relationship("SOCPlaybook", back_populates="executions")
    alert = relationship("SOCAlert", back_populates="executions")


class SOCMetrics(TenantMixin, Base):
    """SOC performance metrics snapshot."""
    __tablename__ = "soc_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String)  # hourly, daily, weekly, monthly

    # Alert metrics
    total_alerts = Column(Integer, default=0)
    alerts_by_severity = Column(JSON)
    alerts_by_source = Column(JSON)
    alerts_by_status = Column(JSON)
    false_positive_rate = Column(Float)

    # Response metrics
    mttd = Column(Float)  # Mean Time to Detect (seconds)
    mttr = Column(Float)  # Mean Time to Respond (seconds)
    mttc = Column(Float)  # Mean Time to Contain (seconds)

    # Case metrics
    total_cases = Column(Integer, default=0)
    cases_by_priority = Column(JSON)
    cases_by_status = Column(JSON)
    avg_case_duration = Column(Float)  # Hours

    # Playbook metrics
    playbook_executions = Column(Integer, default=0)
    playbook_success_rate = Column(Float)
    automation_rate = Column(Float)  # % of alerts handled automatically

    # Analyst metrics
    alerts_per_analyst = Column(JSON)
    cases_per_analyst = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)


class ShiftHandover(TenantMixin, Base):
    """Shift handover notes."""
    __tablename__ = "shift_handovers"

    id = Column(String, primary_key=True, default=generate_uuid)

    shift_date = Column(DateTime, nullable=False)
    shift_type = Column(String)  # morning, afternoon, night

    outgoing_analyst = Column(String, nullable=False)
    incoming_analyst = Column(String)

    # Summary
    summary = Column(Text)
    open_alerts = Column(JSON)  # List of alert IDs requiring attention
    open_cases = Column(JSON)  # List of case IDs requiring attention
    pending_actions = Column(JSON)  # List of pending tasks

    # Notes
    important_notes = Column(Text)
    escalations = Column(Text)

    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
