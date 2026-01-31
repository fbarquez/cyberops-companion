"""Audit logging schemas for API validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AuditAction(str, Enum):
    """Types of audit actions."""
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    # CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    # Special actions
    EXPORT = "export"
    IMPORT = "import"
    ASSIGN = "assign"
    ESCALATE = "escalate"
    STATUS_CHANGE = "status_change"
    ROLE_CHANGE = "role_change"
    CONFIG_CHANGE = "config_change"


class AuditSeverity(str, Enum):
    """Severity levels for audit logs."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditActionCategory(str, Enum):
    """Categories of audit actions."""
    AUTH = "auth"
    CRUD = "crud"
    SYSTEM = "system"
    DATA = "data"


class AuditResourceType(str, Enum):
    """Types of resources that can be audited."""
    INCIDENT = "incident"
    ALERT = "alert"
    USER = "user"
    TEAM = "team"
    ROLE = "role"
    VULNERABILITY = "vulnerability"
    RISK = "risk"
    ASSET = "asset"
    REPORT = "report"
    PLAYBOOK = "playbook"
    CASE = "case"
    IOC = "ioc"
    SETTING = "setting"
    API_KEY = "api_key"
    SESSION = "session"


# ============== Request Schemas ==============

class ActivityLogCreate(BaseModel):
    """Schema for creating an activity log entry."""
    action: str
    action_category: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    severity: str = "info"


class AuditExportRequest(BaseModel):
    """Schema for exporting audit logs."""
    format: str = Field(default="csv", pattern="^(csv|json)$")
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[str] = None


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    user_id: Optional[str] = None
    action: Optional[str] = None
    action_category: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None
    severity: Optional[str] = None
    search: Optional[str] = None


# ============== Response Schemas ==============

class ActivityLogResponse(BaseModel):
    """Schema for activity log response."""
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    action_category: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    changes_summary: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    severity: str = "info"
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogDetailResponse(ActivityLogResponse):
    """Schema for activity log detail with full values."""
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ActivityLogListResponse(BaseModel):
    """Schema for paginated activity log list."""
    items: List[ActivityLogResponse]
    total: int
    page: int
    size: int
    pages: int


class AuditStatsResponse(BaseModel):
    """Schema for audit statistics."""
    total_logs: int
    logs_today: int
    logs_this_week: int
    critical_actions: int
    failed_actions: int
    active_users_today: int
    actions_by_type: Dict[str, int]
    actions_by_resource: Dict[str, int]
    actions_by_severity: Dict[str, int]
    top_users: List[Dict[str, Any]]
    recent_critical: List[ActivityLogResponse]


class AuditExportResponse(BaseModel):
    """Schema for export response."""
    filename: str
    content_type: str
    size: int
    records: int
