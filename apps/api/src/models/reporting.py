"""Reporting & Analytics models."""
import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean, Integer, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship

from src.db.database import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid4())


class ReportType(str, enum.Enum):
    """Types of reports."""
    EXECUTIVE_SUMMARY = "executive_summary"
    INCIDENT_REPORT = "incident_report"
    SOC_METRICS = "soc_metrics"
    THREAT_INTEL = "threat_intel"
    VULNERABILITY = "vulnerability"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE = "compliance"
    TPRM = "tprm"
    INTEGRATION_STATUS = "integration_status"
    CUSTOM = "custom"


class ReportFormat(str, enum.Enum):
    """Report export formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ScheduleFrequency(str, enum.Enum):
    """Report schedule frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


class WidgetType(str, enum.Enum):
    """Dashboard widget types."""
    STAT_CARD = "stat_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TIMELINE = "timeline"
    MAP = "map"


class ReportTemplate(Base):
    """Pre-defined report templates."""
    __tablename__ = "report_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False)

    # Template configuration
    config = Column(JSON)
    """
    {
        "sections": [
            {"title": "Executive Summary", "type": "summary"},
            {"title": "Incident Metrics", "type": "metrics", "source": "incidents"},
            {"title": "Top Threats", "type": "table", "source": "threats"}
        ],
        "filters": {
            "date_range": true,
            "severity": true,
            "department": true
        },
        "default_period_days": 30
    }
    """

    # Styling
    logo_url = Column(String)
    header_template = Column(Text)
    footer_template = Column(Text)

    # Supported formats
    supported_formats = Column(JSON)  # ["pdf", "excel", "csv"]

    # Access control
    is_public = Column(Boolean, default=True)
    allowed_roles = Column(JSON)  # ["admin", "analyst"]

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)


class GeneratedReport(Base):
    """Generated report instances."""
    __tablename__ = "generated_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, unique=True)  # RPT-YYYYMMDD-XXXX

    # Report details
    name = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False)
    template_id = Column(String)  # Reference to template

    # Status
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)

    # Time period
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Filters applied
    filters = Column(JSON)
    """
    {
        "severity": ["critical", "high"],
        "department": "IT",
        "status": "open"
    }
    """

    # Generation details
    format = Column(Enum(ReportFormat), default=ReportFormat.PDF)
    file_path = Column(String)
    file_size_bytes = Column(Integer)
    generation_time_seconds = Column(Float)

    # Report data (cached)
    report_data = Column(JSON)
    """
    {
        "summary": {...},
        "metrics": {...},
        "charts": [...],
        "tables": [...]
    }
    """

    # Error tracking
    error_message = Column(Text)

    # Schedule reference
    schedule_id = Column(String)

    # Metadata
    generated_at = Column(DateTime)
    expires_at = Column(DateTime)
    generated_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    distributions = relationship("ReportDistribution", back_populates="report", cascade="all, delete-orphan")


class ReportSchedule(Base):
    """Scheduled report generation."""
    __tablename__ = "report_schedules"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Template reference
    template_id = Column(String, nullable=False)

    # Schedule configuration
    frequency = Column(Enum(ScheduleFrequency), default=ScheduleFrequency.WEEKLY)
    schedule_config = Column(JSON)
    """
    {
        "day_of_week": 1,  # Monday
        "day_of_month": 1,
        "hour": 8,
        "minute": 0,
        "timezone": "Europe/Berlin"
    }
    """

    # Report configuration
    report_config = Column(JSON)
    """
    {
        "format": "pdf",
        "period_days": 7,
        "filters": {...}
    }
    """

    # Distribution
    recipients = Column(JSON)  # ["email1@example.com", "email2@example.com"]
    distribution_config = Column(JSON)
    """
    {
        "send_email": true,
        "email_subject": "Weekly Security Report",
        "email_body": "Please find attached...",
        "attach_report": true,
        "include_summary": true
    }
    """

    # Status
    is_enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    last_status = Column(String)
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)


class ReportDistribution(Base):
    """Report distribution/delivery log."""
    __tablename__ = "report_distributions"

    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, ForeignKey("generated_reports.id"), nullable=False)

    # Distribution details
    recipient = Column(String, nullable=False)  # Email or user ID
    distribution_type = Column(String)  # email, download, api

    # Status
    status = Column(String)  # sent, delivered, failed, downloaded
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Tracking
    opened_at = Column(DateTime)
    downloaded_at = Column(DateTime)

    # Error
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    report = relationship("GeneratedReport", back_populates="distributions")


class Dashboard(Base):
    """Custom dashboards."""
    __tablename__ = "dashboards"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Layout configuration
    layout = Column(JSON)
    """
    {
        "columns": 4,
        "rows": "auto",
        "widgets": [
            {"id": "w1", "x": 0, "y": 0, "w": 2, "h": 1},
            {"id": "w2", "x": 2, "y": 0, "w": 2, "h": 1}
        ]
    }
    """

    # Access control
    is_public = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    owner = Column(String)
    shared_with = Column(JSON)  # ["user1", "user2"] or ["role:admin"]

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Dashboard widget configuration."""
    __tablename__ = "dashboard_widgets"

    id = Column(String, primary_key=True, default=generate_uuid)
    dashboard_id = Column(String, ForeignKey("dashboards.id"), nullable=False)

    # Widget details
    title = Column(String, nullable=False)
    widget_type = Column(Enum(WidgetType), nullable=False)

    # Data source
    data_source = Column(String)  # incidents, alerts, vulnerabilities, risks, etc.
    query_config = Column(JSON)
    """
    {
        "metric": "count",
        "group_by": "severity",
        "filters": {"status": "open"},
        "period_days": 30,
        "aggregation": "daily"
    }
    """

    # Display configuration
    display_config = Column(JSON)
    """
    {
        "colors": ["#ff0000", "#00ff00"],
        "show_legend": true,
        "show_labels": true,
        "format": "percentage"
    }
    """

    # Refresh settings
    refresh_interval_seconds = Column(Integer, default=300)

    # Position (for layout)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=1)
    height = Column(Integer, default=1)

    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    dashboard = relationship("Dashboard", back_populates="widgets")


class MetricSnapshot(Base):
    """Historical metric snapshots for trend analysis."""
    __tablename__ = "metric_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Metric identification
    metric_name = Column(String, nullable=False)
    metric_category = Column(String)  # incidents, soc, vulnerabilities, risks, etc.

    # Snapshot time
    snapshot_date = Column(DateTime, nullable=False)
    period_type = Column(String)  # daily, weekly, monthly

    # Metric values
    value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_percentage = Column(Float)

    # Breakdown
    breakdown = Column(JSON)
    """
    {
        "by_severity": {"critical": 5, "high": 10, "medium": 20},
        "by_status": {"open": 15, "closed": 20},
        "by_department": {"IT": 10, "HR": 5}
    }
    """

    # Context
    extra_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)


class SavedQuery(Base):
    """Saved queries for reports and dashboards."""
    __tablename__ = "saved_queries"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Query definition
    data_source = Column(String, nullable=False)
    query_type = Column(String)  # aggregate, list, trend
    query_config = Column(JSON, nullable=False)
    """
    {
        "select": ["id", "title", "severity", "status"],
        "filters": {"status": "open", "severity": ["critical", "high"]},
        "group_by": ["severity"],
        "order_by": ["-created_at"],
        "limit": 100
    }
    """

    # Access
    is_public = Column(Boolean, default=False)
    owner = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
