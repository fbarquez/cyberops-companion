"""Reporting & Analytics schemas."""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from src.models.reporting import (
    ReportType, ReportFormat, ReportStatus, ScheduleFrequency, WidgetType
)


# ============== Report Template Schemas ==============

class ReportTemplateCreate(BaseModel):
    """Schema for creating a report template."""
    name: str
    description: Optional[str] = None
    report_type: ReportType
    config: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    supported_formats: Optional[List[str]] = ["pdf", "excel"]
    is_public: bool = True
    allowed_roles: Optional[List[str]] = None


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    supported_formats: Optional[List[str]] = None
    is_public: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ReportTemplateResponse(BaseModel):
    """Schema for report template response."""
    id: str
    name: str
    description: Optional[str] = None
    report_type: ReportType
    config: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    supported_formats: Optional[List[str]] = None
    is_public: bool
    allowed_roles: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============== Generated Report Schemas ==============

class GenerateReportRequest(BaseModel):
    """Schema for generating a report."""
    template_id: Optional[str] = None
    report_type: Optional[ReportType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    format: ReportFormat = ReportFormat.PDF
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    period_days: Optional[int] = 30
    filters: Optional[Dict[str, Any]] = None


class GeneratedReportResponse(BaseModel):
    """Schema for generated report response."""
    id: str
    report_id: str
    name: str
    description: Optional[str] = None
    report_type: ReportType
    template_id: Optional[str] = None
    status: ReportStatus
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    format: ReportFormat
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    generation_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    generated_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedReportListResponse(BaseModel):
    """Schema for paginated report list."""
    items: List[GeneratedReportResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Report Schedule Schemas ==============

class ReportScheduleCreate(BaseModel):
    """Schema for creating a report schedule."""
    name: str
    description: Optional[str] = None
    template_id: str
    frequency: ScheduleFrequency = ScheduleFrequency.WEEKLY
    schedule_config: Optional[Dict[str, Any]] = None
    report_config: Optional[Dict[str, Any]] = None
    recipients: List[str]
    distribution_config: Optional[Dict[str, Any]] = None
    is_enabled: bool = True


class ReportScheduleUpdate(BaseModel):
    """Schema for updating a report schedule."""
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[ScheduleFrequency] = None
    schedule_config: Optional[Dict[str, Any]] = None
    report_config: Optional[Dict[str, Any]] = None
    recipients: Optional[List[str]] = None
    distribution_config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class ReportScheduleResponse(BaseModel):
    """Schema for report schedule response."""
    id: str
    name: str
    description: Optional[str] = None
    template_id: str
    frequency: ScheduleFrequency
    schedule_config: Optional[Dict[str, Any]] = None
    report_config: Optional[Dict[str, Any]] = None
    recipients: List[str]
    distribution_config: Optional[Dict[str, Any]] = None
    is_enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ReportScheduleListResponse(BaseModel):
    """Schema for paginated schedule list."""
    items: List[ReportScheduleResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Dashboard Schemas ==============

class DashboardWidgetCreate(BaseModel):
    """Schema for creating a dashboard widget."""
    title: str
    widget_type: WidgetType
    data_source: str
    query_config: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    refresh_interval_seconds: int = 300
    position_x: int = 0
    position_y: int = 0
    width: int = 1
    height: int = 1


class DashboardWidgetUpdate(BaseModel):
    """Schema for updating a dashboard widget."""
    title: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    refresh_interval_seconds: Optional[int] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_visible: Optional[bool] = None


class DashboardWidgetResponse(BaseModel):
    """Schema for dashboard widget response."""
    id: str
    dashboard_id: str
    title: str
    widget_type: WidgetType
    data_source: str
    query_config: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    refresh_interval_seconds: int
    position_x: int
    position_y: int
    width: int
    height: int
    is_visible: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    """Schema for creating a dashboard."""
    name: str
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    is_public: bool = False
    is_default: bool = False
    shared_with: Optional[List[str]] = None
    widgets: Optional[List[DashboardWidgetCreate]] = None


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard."""
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None
    shared_with: Optional[List[str]] = None


class DashboardResponse(BaseModel):
    """Schema for dashboard response."""
    id: str
    name: str
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    is_public: bool
    is_default: bool
    owner: Optional[str] = None
    shared_with: Optional[List[str]] = None
    widgets: List[DashboardWidgetResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardListResponse(BaseModel):
    """Schema for paginated dashboard list."""
    items: List[DashboardResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Metrics Schemas ==============

class MetricSnapshotResponse(BaseModel):
    """Schema for metric snapshot response."""
    id: str
    metric_name: str
    metric_category: Optional[str] = None
    snapshot_date: datetime
    period_type: Optional[str] = None
    value: float
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TrendDataPoint(BaseModel):
    """Single data point for trend charts."""
    date: datetime
    value: float
    label: Optional[str] = None


class TrendData(BaseModel):
    """Trend data for charts."""
    metric_name: str
    data_points: List[TrendDataPoint]
    total: Optional[float] = None
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    change_percentage: Optional[float] = None


class MetricValue(BaseModel):
    """Single metric value with context."""
    name: str
    value: float
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # up, down, stable
    unit: Optional[str] = None  # count, percentage, hours, etc.
    status: Optional[str] = None  # good, warning, critical


# ============== Executive Dashboard Schemas ==============

class ExecutiveDashboardStats(BaseModel):
    """Executive dashboard statistics."""
    # Overall Security Posture
    security_score: int  # 0-100
    security_score_trend: Optional[str] = None

    # Incidents
    incidents_total: int
    incidents_open: int
    incidents_critical: int
    incidents_mttr_hours: Optional[float] = None
    incidents_trend: Optional[List[TrendDataPoint]] = None

    # SOC
    alerts_today: int
    alerts_critical: int
    cases_open: int
    cases_escalated: int
    mttd_minutes: Optional[float] = None
    mttr_minutes: Optional[float] = None

    # Vulnerabilities
    vulnerabilities_total: int
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_overdue: int
    patch_compliance_rate: Optional[float] = None

    # Risks
    risks_total: int
    risks_critical: int
    risks_high: int
    risk_score_average: Optional[float] = None
    risks_requiring_treatment: int

    # Third-Party
    vendors_total: int
    vendors_high_risk: int
    assessments_pending: int
    findings_open: int

    # Integrations
    integrations_active: int
    integrations_with_errors: int
    syncs_today: int

    # Compliance
    compliance_score: Optional[float] = None
    controls_implemented: Optional[int] = None
    controls_total: Optional[int] = None

    # Trends (last 30 days)
    incident_trend: Optional[List[TrendDataPoint]] = None
    alert_trend: Optional[List[TrendDataPoint]] = None
    vulnerability_trend: Optional[List[TrendDataPoint]] = None


class ReportDataResponse(BaseModel):
    """Report data for rendering."""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    sections: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


# ============== Saved Query Schemas ==============

class SavedQueryCreate(BaseModel):
    """Schema for creating a saved query."""
    name: str
    description: Optional[str] = None
    data_source: str
    query_type: Optional[str] = None
    query_config: Dict[str, Any]
    is_public: bool = False


class SavedQueryResponse(BaseModel):
    """Schema for saved query response."""
    id: str
    name: str
    description: Optional[str] = None
    data_source: str
    query_type: Optional[str] = None
    query_config: Dict[str, Any]
    is_public: bool
    owner: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
