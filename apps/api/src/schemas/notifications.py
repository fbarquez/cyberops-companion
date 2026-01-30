"""Notification schemas for API validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============== Enums ==============

class NotificationType(str, Enum):
    """Types of notifications."""
    INCIDENT_CREATED = "incident_created"
    INCIDENT_ASSIGNED = "incident_assigned"
    INCIDENT_UPDATED = "incident_updated"
    INCIDENT_ESCALATED = "incident_escalated"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_CLOSED = "incident_closed"
    ALERT_CREATED = "alert_created"
    ALERT_CRITICAL = "alert_critical"
    CASE_ASSIGNED = "case_assigned"
    CASE_ESCALATED = "case_escalated"
    VULNERABILITY_DISCOVERED = "vulnerability_discovered"
    VULNERABILITY_CRITICAL = "vulnerability_critical"
    VULNERABILITY_OVERDUE = "vulnerability_overdue"
    RISK_CREATED = "risk_created"
    RISK_CRITICAL = "risk_critical"
    RISK_TREATMENT_DUE = "risk_treatment_due"
    VENDOR_ASSESSMENT_DUE = "vendor_assessment_due"
    VENDOR_HIGH_RISK = "vendor_high_risk"
    FINDING_CREATED = "finding_created"
    INTEGRATION_ERROR = "integration_error"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    REPORT_READY = "report_ready"
    REPORT_FAILED = "report_failed"
    SCHEDULED_REPORT = "scheduled_report"
    SYSTEM_ALERT = "system_alert"
    MAINTENANCE = "maintenance"
    MENTION = "mention"
    COMMENT = "comment"
    TASK_ASSIGNED = "task_assigned"
    TASK_DUE = "task_due"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"


# ============== Notification Schemas ==============

class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[NotificationChannel]] = None
    expires_at: Optional[datetime] = None


class NotificationBulkCreate(BaseModel):
    """Schema for creating notifications for multiple users."""
    user_ids: List[str]
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_archived: bool
    channels_sent: Optional[List[str]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Schema for updating notification."""
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: Optional[List[str]] = None
    mark_all: bool = False


class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    total: int
    unread: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]


# ============== Preference Schemas ==============

class ChannelPreference(BaseModel):
    """Channel preferences for a notification type."""
    notification_type: NotificationType
    channels: List[NotificationChannel]


class CategorySetting(BaseModel):
    """Settings for a notification category."""
    enabled: bool = True
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]


class NotificationPreferenceCreate(BaseModel):
    """Schema for creating notification preferences."""
    notifications_enabled: bool = True
    email_enabled: bool = True
    email_frequency: str = "instant"
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_hours_timezone: str = "UTC"
    channel_preferences: Optional[Dict[str, List[str]]] = None
    min_priority_email: NotificationPriority = NotificationPriority.MEDIUM
    min_priority_sms: NotificationPriority = NotificationPriority.CRITICAL
    category_settings: Optional[Dict[str, CategorySetting]] = None


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    notifications_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    email_frequency: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_hours_timezone: Optional[str] = None
    channel_preferences: Optional[Dict[str, List[str]]] = None
    min_priority_email: Optional[NotificationPriority] = None
    min_priority_sms: Optional[NotificationPriority] = None
    category_settings: Optional[Dict[str, Any]] = None


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response."""
    id: str
    user_id: str
    notifications_enabled: bool
    email_enabled: bool
    email_frequency: str
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_hours_timezone: str
    channel_preferences: Optional[Dict[str, List[str]]] = None
    min_priority_email: NotificationPriority
    min_priority_sms: NotificationPriority
    category_settings: Optional[Dict[str, Any]] = None
    subscriptions: Optional[Dict[str, List[str]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Webhook Subscription Schemas ==============

class WebhookSubscriptionCreate(BaseModel):
    """Schema for creating a webhook subscription."""
    name: str
    description: Optional[str] = None
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    subscribed_events: List[NotificationType]
    filters: Optional[Dict[str, Any]] = None
    is_active: bool = True


class WebhookSubscriptionUpdate(BaseModel):
    """Schema for updating a webhook subscription."""
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    subscribed_events: Optional[List[NotificationType]] = None
    filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WebhookSubscriptionResponse(BaseModel):
    """Schema for webhook subscription response."""
    id: str
    name: str
    description: Optional[str] = None
    url: str
    method: str
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    subscribed_events: List[str]
    filters: Optional[Dict[str, Any]] = None
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    total_deliveries: int
    total_failures: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookTest(BaseModel):
    """Schema for testing a webhook."""
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    test_payload: Optional[Dict[str, Any]] = None


class WebhookTestResult(BaseModel):
    """Result of webhook test."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


# ============== Template Schemas ==============

class NotificationTemplateCreate(BaseModel):
    """Schema for creating a notification template."""
    notification_type: NotificationType
    title_template: str
    message_template: str
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    slack_template: Optional[Dict[str, Any]] = None
    teams_template: Optional[Dict[str, Any]] = None
    available_variables: Optional[List[str]] = None
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    """Schema for updating a notification template."""
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    slack_template: Optional[Dict[str, Any]] = None
    teams_template: Optional[Dict[str, Any]] = None
    available_variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(BaseModel):
    """Schema for notification template response."""
    id: str
    notification_type: NotificationType
    title_template: str
    message_template: str
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    slack_template: Optional[Dict[str, Any]] = None
    teams_template: Optional[Dict[str, Any]] = None
    available_variables: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Real-time Event Schema ==============

class NotificationEvent(BaseModel):
    """Schema for real-time notification events (SSE/WebSocket)."""
    event_type: str  # notification, read, archived, deleted
    notification: Optional[NotificationResponse] = None
    notification_id: Optional[str] = None
    stats: Optional[NotificationStats] = None
