"""Integration Hub models for external platform connections."""
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


class IntegrationType(str, enum.Enum):
    """Types of integrations."""
    # Security Awareness
    KNOWBE4 = "knowbe4"
    GOPHISH = "gophish"
    PROOFPOINT_AWARENESS = "proofpoint_awareness"

    # SIEM
    SPLUNK = "splunk"
    ELASTIC = "elastic"
    QRADAR = "qradar"
    SENTINEL = "sentinel"

    # EDR/XDR
    CROWDSTRIKE = "crowdstrike"
    CARBON_BLACK = "carbon_black"
    DEFENDER = "defender"
    SENTINELONE = "sentinelone"

    # Ticketing
    JIRA = "jira"
    SERVICENOW = "servicenow"
    ZENDESK = "zendesk"

    # Email Security
    PROOFPOINT = "proofpoint"
    MIMECAST = "mimecast"

    # Vulnerability Scanners
    NESSUS = "nessus"
    QUALYS = "qualys"
    RAPID7 = "rapid7"

    # Threat Intelligence
    MISP = "misp"
    OPENCTI = "opencti"
    OTX = "otx"
    VIRUSTOTAL = "virustotal"

    # Cloud Security
    AWS_SECURITY_HUB = "aws_security_hub"
    AZURE_SENTINEL = "azure_sentinel"
    GCP_SCC = "gcp_scc"

    # Custom/Webhook
    WEBHOOK = "webhook"
    CUSTOM_API = "custom_api"


class IntegrationCategory(str, enum.Enum):
    """Categories of integrations."""
    SECURITY_AWARENESS = "security_awareness"
    SIEM = "siem"
    EDR_XDR = "edr_xdr"
    TICKETING = "ticketing"
    EMAIL_SECURITY = "email_security"
    VULNERABILITY = "vulnerability"
    THREAT_INTEL = "threat_intel"
    CLOUD_SECURITY = "cloud_security"
    CUSTOM = "custom"


class IntegrationStatus(str, enum.Enum):
    """Status of integration connection."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"
    TESTING = "testing"


class SyncDirection(str, enum.Enum):
    """Data sync direction."""
    INBOUND = "inbound"  # Pull data from external system
    OUTBOUND = "outbound"  # Push data to external system
    BIDIRECTIONAL = "bidirectional"


class SyncFrequency(str, enum.Enum):
    """How often to sync data."""
    REALTIME = "realtime"  # Webhook-based
    EVERY_5_MIN = "5min"
    EVERY_15_MIN = "15min"
    EVERY_30_MIN = "30min"
    HOURLY = "hourly"
    EVERY_6_HOURS = "6hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class Integration(TenantMixin, Base):
    """External platform integration configuration."""
    __tablename__ = "integrations"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Integration type
    integration_type = Column(Enum(IntegrationType), nullable=False)
    category = Column(Enum(IntegrationCategory), nullable=False)

    # Status
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.CONFIGURING)
    is_enabled = Column(Boolean, default=False)

    # Connection settings (encrypted in production)
    base_url = Column(String)
    api_key = Column(String)  # Should be encrypted
    api_secret = Column(String)  # Should be encrypted
    username = Column(String)
    password = Column(String)  # Should be encrypted
    oauth_token = Column(Text)  # Should be encrypted
    oauth_refresh_token = Column(Text)  # Should be encrypted
    oauth_expires_at = Column(DateTime)

    # Additional configuration
    config = Column(JSON)  # Platform-specific settings
    """
    Example config:
    {
        "tenant_id": "xxx",
        "region": "us-east-1",
        "verify_ssl": true,
        "timeout_seconds": 30,
        "custom_headers": {},
        "proxy_url": null
    }
    """

    # Sync settings
    sync_direction = Column(Enum(SyncDirection), default=SyncDirection.INBOUND)
    sync_frequency = Column(Enum(SyncFrequency), default=SyncFrequency.HOURLY)
    last_sync_at = Column(DateTime)
    next_sync_at = Column(DateTime)

    # Data mapping
    data_mappings = Column(JSON)
    """
    Maps external fields to internal fields:
    {
        "alerts": {
            "external_field": "internal_field",
            "severity": "severity",
            "timestamp": "created_at"
        }
    }
    """

    # Filters
    sync_filters = Column(JSON)
    """
    Filter what data to sync:
    {
        "severity": ["high", "critical"],
        "status": ["open"],
        "since_days": 30
    }
    """

    # Webhook settings (for inbound webhooks)
    webhook_secret = Column(String)
    webhook_url = Column(String)  # Generated URL for this integration

    # Health monitoring
    last_health_check = Column(DateTime)
    health_status = Column(String)  # ok, degraded, down
    error_message = Column(Text)
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    sync_logs = relationship("IntegrationSyncLog", back_populates="integration", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEvent", back_populates="integration", cascade="all, delete-orphan")


class IntegrationSyncLog(Base):
    """Log of sync operations."""
    __tablename__ = "integration_sync_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=False)

    # Sync details
    sync_type = Column(String)  # full, incremental, manual
    direction = Column(Enum(SyncDirection))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Results
    status = Column(String)  # success, partial, failed
    records_fetched = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    triggered_by = Column(String)  # user_id, scheduler, webhook

    # Relationship
    integration = relationship("Integration", back_populates="sync_logs")


class WebhookEvent(Base):
    """Incoming webhook events."""
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=False)

    # Event details
    event_type = Column(String)  # alert, incident, training_complete, etc.
    event_id = Column(String)  # External event ID
    received_at = Column(DateTime, default=datetime.utcnow)

    # Payload
    headers = Column(JSON)
    payload = Column(JSON)
    raw_body = Column(Text)

    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_result = Column(String)  # success, failed, ignored
    processing_error = Column(Text)

    # Created entities
    created_entities = Column(JSON)  # List of created entity IDs
    """
    {
        "alerts": ["alert-123"],
        "incidents": ["inc-456"]
    }
    """

    # Relationship
    integration = relationship("Integration", back_populates="webhooks")


class IntegrationTemplate(Base):
    """Pre-configured integration templates."""
    __tablename__ = "integration_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    integration_type = Column(Enum(IntegrationType), nullable=False, unique=True)
    category = Column(Enum(IntegrationCategory), nullable=False)

    # Display info
    name = Column(String, nullable=False)
    description = Column(Text)
    vendor = Column(String)
    logo_url = Column(String)
    documentation_url = Column(String)

    # Configuration schema
    config_schema = Column(JSON)
    """
    JSON Schema for configuration:
    {
        "type": "object",
        "required": ["api_key", "base_url"],
        "properties": {
            "api_key": {"type": "string", "title": "API Key"},
            "base_url": {"type": "string", "title": "Base URL", "default": "https://api.example.com"}
        }
    }
    """

    # Default settings
    default_config = Column(JSON)
    default_mappings = Column(JSON)

    # Capabilities
    supports_inbound = Column(Boolean, default=True)
    supports_outbound = Column(Boolean, default=False)
    supports_webhook = Column(Boolean, default=False)
    supported_entities = Column(JSON)  # ["alerts", "incidents", "iocs"]

    # Authentication methods
    auth_methods = Column(JSON)  # ["api_key", "oauth2", "basic"]

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityAwarenessMetrics(Base):
    """Aggregated security awareness metrics from integrated platforms."""
    __tablename__ = "security_awareness_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    integration_id = Column(String, nullable=False)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Training metrics
    total_users = Column(Integer, default=0)
    training_completed = Column(Integer, default=0)
    training_in_progress = Column(Integer, default=0)
    training_overdue = Column(Integer, default=0)
    average_score = Column(Integer)  # 0-100

    # Phishing metrics
    phishing_campaigns_sent = Column(Integer, default=0)
    phishing_emails_sent = Column(Integer, default=0)
    phishing_clicked = Column(Integer, default=0)
    phishing_reported = Column(Integer, default=0)
    phishing_click_rate = Column(Integer)  # Percentage
    phishing_report_rate = Column(Integer)  # Percentage

    # Department breakdown
    department_metrics = Column(JSON)
    """
    {
        "IT": {"users": 50, "score": 85, "click_rate": 5},
        "Sales": {"users": 100, "score": 72, "click_rate": 15}
    }
    """

    # Risk users
    high_risk_users = Column(JSON)  # List of user emails with low scores
    repeat_clickers = Column(JSON)  # Users who clicked multiple phishing tests

    # Trends
    score_trend = Column(String)  # improving, stable, declining
    click_rate_trend = Column(String)

    synced_at = Column(DateTime, default=datetime.utcnow)
