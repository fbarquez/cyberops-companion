"""
SOC Module Pydantic Schemas.

Schemas for alert management, case management, and playbook automation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ==================== Enums ====================

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AlertStatus(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class AlertSource(str, Enum):
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


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CasePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class PlaybookTriggerType(str, Enum):
    MANUAL = "manual"
    ALERT_CREATED = "alert_created"
    ALERT_SEVERITY = "alert_severity"
    ALERT_SOURCE = "alert_source"
    CASE_CREATED = "case_created"
    SCHEDULED = "scheduled"
    IOC_MATCH = "ioc_match"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


# ==================== Alert Schemas ====================

class AlertCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    source: AlertSource = AlertSource.OTHER
    source_ref: Optional[str] = None
    detection_rule: Optional[str] = None
    mitre_tactics: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    affected_assets: Optional[List[str]] = None
    affected_users: Optional[List[str]] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    risk_score: Optional[float] = None
    confidence: Optional[float] = None
    detected_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    raw_event: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class AlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    false_positive_reason: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class AlertAssign(BaseModel):
    assigned_to: str
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    resolution_notes: str
    is_false_positive: bool = False
    false_positive_reason: Optional[str] = None


class AlertCommentCreate(BaseModel):
    content: str
    is_internal: bool = True


class AlertCommentResponse(BaseModel):
    id: str
    alert_id: str
    author: str
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    alert_id: str
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    source: AlertSource
    source_ref: Optional[str]
    detection_rule: Optional[str]
    mitre_tactics: Optional[List[str]]
    mitre_techniques: Optional[List[str]]
    affected_assets: Optional[List[str]]
    affected_users: Optional[List[str]]
    source_ip: Optional[str]
    destination_ip: Optional[str]
    enrichment_data: Optional[Dict[str, Any]]
    risk_score: Optional[float]
    confidence: Optional[float]
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    correlation_id: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    comments: Optional[List[AlertCommentResponse]] = None

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AlertBulkCreate(BaseModel):
    alerts: List[AlertCreate]


# ==================== Case Schemas ====================

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: CasePriority = CasePriority.MEDIUM
    case_type: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    due_date: Optional[datetime] = None
    alert_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    due_date: Optional[datetime] = None
    investigation_notes: Optional[str] = None
    root_cause: Optional[str] = None
    impact_assessment: Optional[str] = None
    tags: Optional[List[str]] = None


class CaseEscalate(BaseModel):
    escalated_to: str
    reason: str


class CaseResolve(BaseModel):
    resolution_summary: str
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None


class CaseTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class CaseTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class CaseTaskResponse(BaseModel):
    id: str
    case_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class CaseTimelineCreate(BaseModel):
    event_time: datetime
    event_type: str
    description: str
    evidence_ids: Optional[List[str]] = None


class CaseTimelineResponse(BaseModel):
    id: str
    case_id: str
    event_time: datetime
    event_type: str
    description: str
    author: Optional[str]
    evidence_ids: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str]
    status: CaseStatus
    priority: CasePriority
    case_type: Optional[str]
    assigned_to: Optional[str]
    assigned_team: Optional[str]
    escalated_to: Optional[str]
    escalation_reason: Optional[str]
    opened_at: datetime
    due_date: Optional[datetime]
    escalated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    investigation_notes: Optional[str]
    root_cause: Optional[str]
    impact_assessment: Optional[str]
    resolution_summary: Optional[str]
    lessons_learned: Optional[str]
    time_to_detect: Optional[int]
    time_to_respond: Optional[int]
    time_to_resolve: Optional[int]
    incident_id: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    alert_count: Optional[int] = 0
    task_count: Optional[int] = 0
    tasks: Optional[List[CaseTaskResponse]] = None
    timeline: Optional[List[CaseTimelineResponse]] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== Playbook Schemas ====================

class PlaybookActionConfig(BaseModel):
    action_type: str
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    on_success: Optional[str] = None  # Next action or "continue"
    on_failure: Optional[str] = None  # "stop", "continue", or action name
    timeout_seconds: int = 300
    require_approval: bool = False


class PlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: PlaybookTriggerType = PlaybookTriggerType.MANUAL
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: List[PlaybookActionConfig]
    is_enabled: bool = True
    run_automatically: bool = False
    require_approval: bool = True
    timeout_seconds: int = 3600
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PlaybookStatus] = None
    trigger_type: Optional[PlaybookTriggerType] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[PlaybookActionConfig]] = None
    is_enabled: Optional[bool] = None
    run_automatically: Optional[bool] = None
    require_approval: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class PlaybookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: PlaybookStatus
    version: str
    trigger_type: PlaybookTriggerType
    trigger_conditions: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    is_enabled: bool
    run_automatically: bool
    require_approval: bool
    max_concurrent_runs: int
    timeout_seconds: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_execution_time: Optional[float]
    category: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class PlaybookListResponse(BaseModel):
    items: List[PlaybookResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PlaybookExecutionCreate(BaseModel):
    alert_id: Optional[str] = None
    case_id: Optional[str] = None
    trigger_reason: Optional[str] = None


class PlaybookExecutionResponse(BaseModel):
    id: str
    playbook_id: str
    playbook_name: Optional[str] = None
    alert_id: Optional[str]
    case_id: Optional[str]
    trigger_reason: Optional[str]
    status: ExecutionStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    action_results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    executed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Metrics & Dashboard Schemas ====================

class SOCDashboardStats(BaseModel):
    # Alert stats
    total_alerts_today: int = 0
    new_alerts: int = 0
    in_progress_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0

    # Case stats
    open_cases: int = 0
    escalated_cases: int = 0
    overdue_cases: int = 0

    # Response metrics
    mttd: Optional[float] = None  # Mean Time to Detect (minutes)
    mttr: Optional[float] = None  # Mean Time to Respond (minutes)

    # Trends
    alerts_by_severity: Dict[str, int] = Field(default_factory=dict)
    alerts_by_source: Dict[str, int] = Field(default_factory=dict)
    alerts_by_status: Dict[str, int] = Field(default_factory=dict)
    cases_by_priority: Dict[str, int] = Field(default_factory=dict)
    cases_by_status: Dict[str, int] = Field(default_factory=dict)

    # Playbook stats
    playbook_runs_today: int = 0
    automation_rate: float = 0.0

    # Analyst workload
    alerts_per_analyst: Dict[str, int] = Field(default_factory=dict)


class AlertTrend(BaseModel):
    date: str
    total: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class SOCMetricsResponse(BaseModel):
    period_start: datetime
    period_end: datetime

    # Counts
    total_alerts: int
    total_cases: int
    false_positive_rate: float

    # Response times
    mttd: Optional[float]  # Minutes
    mttr: Optional[float]  # Minutes
    mttc: Optional[float]  # Minutes

    # Distributions
    alerts_by_severity: Dict[str, int]
    alerts_by_source: Dict[str, int]
    cases_by_priority: Dict[str, int]

    # Trends
    alert_trends: List[AlertTrend]

    # Automation
    automation_rate: float
    playbook_success_rate: float


# ==================== Shift Handover Schemas ====================

class ShiftHandoverCreate(BaseModel):
    shift_type: Optional[str] = None
    summary: str
    open_alerts: Optional[List[str]] = None
    open_cases: Optional[List[str]] = None
    pending_actions: Optional[List[str]] = None
    important_notes: Optional[str] = None
    escalations: Optional[str] = None


class ShiftHandoverResponse(BaseModel):
    id: str
    shift_date: datetime
    shift_type: Optional[str]
    outgoing_analyst: str
    incoming_analyst: Optional[str]
    summary: str
    open_alerts: Optional[List[str]]
    open_cases: Optional[List[str]]
    pending_actions: Optional[List[str]]
    important_notes: Optional[str]
    escalations: Optional[str]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
