"""Integration Hub schemas."""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from src.models.integrations import (
    IntegrationType, IntegrationCategory, IntegrationStatus,
    SyncDirection, SyncFrequency
)


# ============== Integration Schemas ==============

class IntegrationBase(BaseModel):
    """Base integration schema."""
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    category: IntegrationCategory
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    sync_direction: Optional[SyncDirection] = SyncDirection.INBOUND
    sync_frequency: Optional[SyncFrequency] = SyncFrequency.HOURLY
    data_mappings: Optional[Dict[str, Any]] = None
    sync_filters: Optional[Dict[str, Any]] = None


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration."""
    pass


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration."""
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    sync_direction: Optional[SyncDirection] = None
    sync_frequency: Optional[SyncFrequency] = None
    data_mappings: Optional[Dict[str, Any]] = None
    sync_filters: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class IntegrationResponse(BaseModel):
    """Schema for integration response."""
    id: str
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    category: IntegrationCategory
    status: IntegrationStatus
    is_enabled: bool
    base_url: Optional[str] = None
    # Note: Sensitive fields (api_key, password, etc.) are not returned
    config: Optional[Dict[str, Any]] = None
    sync_direction: SyncDirection
    sync_frequency: SyncFrequency
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    data_mappings: Optional[Dict[str, Any]] = None
    sync_filters: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    health_status: Optional[str] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class IntegrationListResponse(BaseModel):
    """Schema for paginated integration list."""
    items: List[IntegrationResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Sync Log Schemas ==============

class SyncLogResponse(BaseModel):
    """Schema for sync log response."""
    id: str
    integration_id: str
    sync_type: Optional[str] = None
    direction: Optional[SyncDirection] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: Optional[str] = None
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None

    class Config:
        from_attributes = True


class SyncLogListResponse(BaseModel):
    """Schema for paginated sync log list."""
    items: List[SyncLogResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Webhook Event Schemas ==============

class WebhookEventResponse(BaseModel):
    """Schema for webhook event response."""
    id: str
    integration_id: str
    event_type: Optional[str] = None
    event_id: Optional[str] = None
    received_at: datetime
    processed: bool
    processed_at: Optional[datetime] = None
    processing_result: Optional[str] = None
    processing_error: Optional[str] = None
    created_entities: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class WebhookEventListResponse(BaseModel):
    """Schema for paginated webhook event list."""
    items: List[WebhookEventResponse]
    total: int
    page: int
    size: int
    pages: int


# ============== Integration Template Schemas ==============

class IntegrationTemplateResponse(BaseModel):
    """Schema for integration template response."""
    id: str
    integration_type: IntegrationType
    category: IntegrationCategory
    name: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    logo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    default_mappings: Optional[Dict[str, Any]] = None
    supports_inbound: bool = True
    supports_outbound: bool = False
    supports_webhook: bool = False
    supported_entities: Optional[List[str]] = None
    auth_methods: Optional[List[str]] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ============== Security Awareness Metrics Schemas ==============

class SecurityAwarenessMetricsResponse(BaseModel):
    """Schema for security awareness metrics response."""
    id: str
    integration_id: str
    period_start: datetime
    period_end: datetime
    total_users: int = 0
    training_completed: int = 0
    training_in_progress: int = 0
    training_overdue: int = 0
    average_score: Optional[int] = None
    phishing_campaigns_sent: int = 0
    phishing_emails_sent: int = 0
    phishing_clicked: int = 0
    phishing_reported: int = 0
    phishing_click_rate: Optional[int] = None
    phishing_report_rate: Optional[int] = None
    department_metrics: Optional[Dict[str, Any]] = None
    high_risk_users: Optional[List[str]] = None
    repeat_clickers: Optional[List[str]] = None
    score_trend: Optional[str] = None
    click_rate_trend: Optional[str] = None
    synced_at: datetime

    class Config:
        from_attributes = True


# ============== Test Connection Schemas ==============

class TestConnectionRequest(BaseModel):
    """Schema for testing connection."""
    integration_type: IntegrationType
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class TestConnectionResponse(BaseModel):
    """Schema for test connection response."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None


# ============== Manual Sync Schemas ==============

class ManualSyncRequest(BaseModel):
    """Schema for manual sync request."""
    sync_type: str = "incremental"  # full, incremental
    since: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None


class ManualSyncResponse(BaseModel):
    """Schema for manual sync response."""
    sync_log_id: str
    status: str
    message: str


# ============== Dashboard Stats ==============

class IntegrationsDashboardStats(BaseModel):
    """Dashboard statistics for integrations."""
    total_integrations: int
    active_integrations: int
    integrations_with_errors: int
    integrations_by_category: Dict[str, int]
    integrations_by_status: Dict[str, int]

    # Sync stats
    total_syncs_today: int
    successful_syncs_today: int
    failed_syncs_today: int
    records_synced_today: int

    # Webhook stats
    webhooks_received_today: int
    webhooks_processed_today: int
    webhooks_failed_today: int

    # Security Awareness (aggregated from all awareness integrations)
    awareness_metrics: Optional[Dict[str, Any]] = None
    """
    {
        "total_users": 500,
        "average_score": 78,
        "phishing_click_rate": 8,
        "training_completion_rate": 85
    }
    """
