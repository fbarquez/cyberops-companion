"""Notification system models."""
import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from src.db.database import Base
from src.models.mixins import TenantMixin


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid4())


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    # Incidents
    INCIDENT_CREATED = "incident_created"
    INCIDENT_ASSIGNED = "incident_assigned"
    INCIDENT_UPDATED = "incident_updated"
    INCIDENT_ESCALATED = "incident_escalated"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_CLOSED = "incident_closed"

    # SOC Alerts
    ALERT_CREATED = "alert_created"
    ALERT_CRITICAL = "alert_critical"
    CASE_ASSIGNED = "case_assigned"
    CASE_ESCALATED = "case_escalated"

    # Vulnerabilities
    VULNERABILITY_DISCOVERED = "vulnerability_discovered"
    VULNERABILITY_CRITICAL = "vulnerability_critical"
    VULNERABILITY_OVERDUE = "vulnerability_overdue"

    # Risks
    RISK_CREATED = "risk_created"
    RISK_CRITICAL = "risk_critical"
    RISK_TREATMENT_DUE = "risk_treatment_due"

    # TPRM
    VENDOR_ASSESSMENT_DUE = "vendor_assessment_due"
    VENDOR_HIGH_RISK = "vendor_high_risk"
    FINDING_CREATED = "finding_created"

    # Integrations
    INTEGRATION_ERROR = "integration_error"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"

    # Reports
    REPORT_READY = "report_ready"
    REPORT_FAILED = "report_failed"
    SCHEDULED_REPORT = "scheduled_report"

    # System
    SYSTEM_ALERT = "system_alert"
    MAINTENANCE = "maintenance"

    # User
    MENTION = "mention"
    COMMENT = "comment"
    TASK_ASSIGNED = "task_assigned"
    TASK_DUE = "task_due"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, enum.Enum):
    """Delivery channels for notifications."""
    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"


class Notification(TenantMixin, Base):
    """Individual notification records."""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)

    # Recipient
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Notification content
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)

    title = Column(String, nullable=False)
    message = Column(Text)

    # Related entity
    entity_type = Column(String)  # incident, alert, vulnerability, risk, etc.
    entity_id = Column(String)
    entity_url = Column(String)  # Direct link to the entity

    # Additional data
    data = Column(JSON)
    """
    {
        "incident_id": "INC-2024-001",
        "severity": "critical",
        "assigned_to": "John Doe"
    }
    """

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)

    # Delivery tracking
    channels_sent = Column(JSON)  # ["in_app", "email"]
    delivery_status = Column(JSON)
    """
    {
        "in_app": {"status": "delivered", "at": "2024-01-15T10:00:00"},
        "email": {"status": "sent", "at": "2024-01-15T10:00:01"}
    }
    """

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Optional expiration

    # Relationships
    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    # Global settings
    notifications_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    email_frequency = Column(String, default="instant")  # instant, hourly, daily

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String)  # "22:00"
    quiet_hours_end = Column(String)  # "08:00"
    quiet_hours_timezone = Column(String, default="UTC")

    # Channel preferences per notification type
    channel_preferences = Column(JSON)
    """
    {
        "incident_created": ["in_app", "email"],
        "incident_critical": ["in_app", "email", "slack"],
        "alert_critical": ["in_app", "email", "sms"],
        "report_ready": ["in_app"]
    }
    """

    # Priority thresholds
    min_priority_email = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    min_priority_sms = Column(Enum(NotificationPriority), default=NotificationPriority.CRITICAL)

    # Category settings
    category_settings = Column(JSON)
    """
    {
        "incidents": {"enabled": true, "channels": ["in_app", "email"]},
        "alerts": {"enabled": true, "channels": ["in_app"]},
        "vulnerabilities": {"enabled": true, "channels": ["in_app", "email"]},
        "reports": {"enabled": true, "channels": ["in_app"]}
    }
    """

    # Subscriptions to specific entities
    subscriptions = Column(JSON)
    """
    {
        "incidents": ["INC-2024-001", "INC-2024-002"],
        "risks": ["RISK-001"]
    }
    """

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class NotificationTemplate(Base):
    """Templates for notification messages."""
    __tablename__ = "notification_templates"

    id = Column(String, primary_key=True, default=generate_uuid)

    notification_type = Column(Enum(NotificationType), nullable=False, unique=True)

    # Templates for different channels
    title_template = Column(String, nullable=False)
    message_template = Column(Text, nullable=False)

    email_subject_template = Column(String)
    email_body_template = Column(Text)

    slack_template = Column(JSON)  # Slack block kit format
    teams_template = Column(JSON)  # Teams adaptive card format

    # Variables available for this template
    available_variables = Column(JSON)
    """
    ["entity_id", "entity_name", "severity", "assigned_to", "created_by", "timestamp"]
    """

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookSubscription(Base):
    """Webhook subscriptions for external notifications."""
    __tablename__ = "webhook_subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)

    name = Column(String, nullable=False)
    description = Column(Text)

    # Webhook configuration
    url = Column(String, nullable=False)
    method = Column(String, default="POST")  # POST, PUT
    headers = Column(JSON)  # Custom headers

    # Authentication
    auth_type = Column(String)  # none, basic, bearer, hmac
    auth_config = Column(JSON)  # Encrypted credentials

    # Event subscriptions
    subscribed_events = Column(JSON)  # List of NotificationType values
    """
    ["incident_created", "incident_critical", "alert_critical"]
    """

    # Filters
    filters = Column(JSON)
    """
    {
        "severity": ["critical", "high"],
        "entity_types": ["incident", "alert"]
    }
    """

    # Status
    is_active = Column(Boolean, default=True)

    # Tracking
    last_triggered_at = Column(DateTime)
    last_status = Column(String)  # success, failed
    last_error = Column(Text)

    consecutive_failures = Column(Integer, default=0)
    total_deliveries = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)

    # Owner
    created_by = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationLog(Base):
    """Delivery log for notifications."""
    __tablename__ = "notification_logs"

    id = Column(String, primary_key=True, default=generate_uuid)

    notification_id = Column(String, ForeignKey("notifications.id"), nullable=False)

    # Delivery details
    channel = Column(Enum(NotificationChannel), nullable=False)
    recipient = Column(String)  # Email address, webhook URL, etc.

    # Status
    status = Column(String)  # pending, sent, delivered, failed, bounced

    # Timing
    attempted_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)

    # Response
    response_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)

    # Retry tracking
    attempt_number = Column(Integer, default=1)
    next_retry_at = Column(DateTime)

    # Relationship
    notification = relationship("Notification")
