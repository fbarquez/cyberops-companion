"""
Configuration Management Database (CMDB) Models.

Extended models for Asset Management, Configuration Items, Software/Hardware Inventory,
and Asset Relationships.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float, Boolean,
    ForeignKey, Table, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base


class ConfigurationItemType(str, enum.Enum):
    """Type of configuration item."""
    APPLICATION = "application"
    SERVICE = "service"
    DATABASE = "database"
    MIDDLEWARE = "middleware"
    OPERATING_SYSTEM = "operating_system"
    NETWORK = "network"
    STORAGE = "storage"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENT = "document"


class ConfigurationItemStatus(str, enum.Enum):
    """CI lifecycle status."""
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class AssetLifecycleStage(str, enum.Enum):
    """Asset lifecycle stages."""
    PROCUREMENT = "procurement"
    DEPLOYMENT = "deployment"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DECOMMISSIONING = "decommissioning"
    RETIRED = "retired"
    DISPOSED = "disposed"


class RelationshipType(str, enum.Enum):
    """Types of relationships between configuration items."""
    DEPENDS_ON = "depends_on"
    SUPPORTS = "supports"
    CONNECTS_TO = "connects_to"
    RUNS_ON = "runs_on"
    CONTAINS = "contains"
    PART_OF = "part_of"
    MANAGED_BY = "managed_by"
    USED_BY = "used_by"
    BACKUP_OF = "backup_of"
    REPLICATED_TO = "replicated_to"


class ChangeType(str, enum.Enum):
    """Types of changes to assets/CIs."""
    CREATED = "created"
    UPDATED = "updated"
    CONFIGURATION = "configuration"
    PATCH = "patch"
    UPGRADE = "upgrade"
    MIGRATION = "migration"
    MAINTENANCE = "maintenance"
    INCIDENT = "incident"
    DECOMMISSIONED = "decommissioned"


class SoftwareCategory(str, enum.Enum):
    """Software categories."""
    OPERATING_SYSTEM = "operating_system"
    DATABASE = "database"
    WEB_SERVER = "web_server"
    APPLICATION_SERVER = "application_server"
    SECURITY = "security"
    MONITORING = "monitoring"
    BACKUP = "backup"
    DEVELOPMENT = "development"
    PRODUCTIVITY = "productivity"
    UTILITY = "utility"
    CUSTOM = "custom"


class LicenseType(str, enum.Enum):
    """Software license types."""
    PERPETUAL = "perpetual"
    SUBSCRIPTION = "subscription"
    OPEN_SOURCE = "open_source"
    FREEWARE = "freeware"
    TRIAL = "trial"
    OEM = "oem"
    VOLUME = "volume"
    SITE = "site"
    USER = "user"
    DEVICE = "device"


# Association tables
ci_relationship_table = Table(
    'ci_relationships',
    Base.metadata,
    Column('id', String(36), primary_key=True, default=lambda: str(uuid4())),
    Column('source_ci_id', String(36), ForeignKey('configuration_items.id'), nullable=False),
    Column('target_ci_id', String(36), ForeignKey('configuration_items.id'), nullable=False),
    Column('relationship_type', SQLEnum(RelationshipType), nullable=False),
    Column('description', Text, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class ConfigurationItem(Base):
    """Configuration Item (CI) model."""
    __tablename__ = "configuration_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    ci_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g., CI-APP-001
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    ci_type = mapped_column(SQLEnum(ConfigurationItemType), nullable=False, index=True)
    status = mapped_column(SQLEnum(ConfigurationItemStatus), default=ConfigurationItemStatus.PLANNED, index=True)

    # Association with Asset (optional - not all CIs are physical assets)
    asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assets.id"), nullable=True)

    # Version and Configuration
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    configuration: Mapped[Optional[dict]] = mapped_column(JSON, default={})
    baseline_configuration: Mapped[Optional[dict]] = mapped_column(JSON, default={})

    # Business context
    business_service: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_criticality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Ownership
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technical_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Technical details
    documentation_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    support_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Compliance
    compliance_requirements = mapped_column(JSON, default=[])
    data_classification: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    tags = mapped_column(JSON, default=[])
    custom_attributes = mapped_column(JSON, default={})

    # Dates
    go_live_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retirement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_audit_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_audit_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id])
    software_installations = relationship("SoftwareInstallation", back_populates="configuration_item", cascade="all, delete-orphan")
    change_history = relationship("AssetChange", back_populates="configuration_item", cascade="all, delete-orphan")


class SoftwareItem(Base):
    """Software catalog item."""
    __tablename__ = "software_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Classification
    category = mapped_column(SQLEnum(SoftwareCategory), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_prohibited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Licensing
    license_type = mapped_column(SQLEnum(LicenseType), nullable=True)
    license_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Security
    cpe_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Common Platform Enumeration
    known_vulnerabilities: Mapped[int] = mapped_column(Integer, default=0)
    end_of_life_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_of_support_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    tags = mapped_column(JSON, default=[])

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    installations = relationship("SoftwareInstallation", back_populates="software")
    licenses = relationship("SoftwareLicense", back_populates="software", cascade="all, delete-orphan")


class SoftwareInstallation(Base):
    """Software installation on a CI/Asset."""
    __tablename__ = "software_installations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Links
    software_id: Mapped[str] = mapped_column(String(36), ForeignKey("software_items.id"), nullable=False)
    asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assets.id"), nullable=True)
    ci_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("configuration_items.id"), nullable=True)

    # Installation details
    installed_version: Mapped[str] = mapped_column(String(100), nullable=False)
    installation_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    installation_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_update: Mapped[bool] = mapped_column(Boolean, default=False)
    latest_available_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # License
    license_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("software_licenses.id"), nullable=True)

    # Discovery
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discovery_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    software = relationship("SoftwareItem", back_populates="installations")
    asset = relationship("Asset", foreign_keys=[asset_id])
    configuration_item = relationship("ConfigurationItem", back_populates="software_installations")
    license = relationship("SoftwareLicense", foreign_keys=[license_id])


class SoftwareLicense(Base):
    """Software license tracking."""
    __tablename__ = "software_licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Link to software
    software_id: Mapped[str] = mapped_column(String(36), ForeignKey("software_items.id"), nullable=False)

    # License details
    license_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    license_type = mapped_column(SQLEnum(LicenseType), nullable=False)
    license_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Quantities
    total_licenses: Mapped[int] = mapped_column(Integer, default=1)
    used_licenses: Mapped[int] = mapped_column(Integer, default=0)

    # Validity
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Cost
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    renewal_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Vendor details
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_expiration: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Documentation
    contract_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    software = relationship("SoftwareItem", back_populates="licenses")


class HardwareSpec(Base):
    """Hardware specifications for an asset."""
    __tablename__ = "hardware_specs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Link to asset
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, unique=True)

    # General
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    asset_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Form factor
    form_factor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # rack, tower, blade, laptop, etc.
    rack_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rack_unit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # CPU
    cpu_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cpu_cores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_threads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_speed_ghz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Memory
    ram_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ram_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ram_slots_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ram_slots_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Storage
    storage_total_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    storage_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SSD, HDD, NVMe
    storage_details = mapped_column(JSON, default=[])  # Array of storage devices

    # Network
    network_interfaces = mapped_column(JSON, default=[])  # Array of NICs

    # Power
    power_supply_watts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    power_supplies_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Warranty
    warranty_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    warranty_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    warranty_provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Purchase
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    purchase_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purchase_vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    purchase_order: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id], backref="hardware_spec")


class AssetLifecycle(Base):
    """Asset lifecycle tracking."""
    __tablename__ = "asset_lifecycle"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Link to asset
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, unique=True)

    # Current stage
    current_stage = mapped_column(SQLEnum(AssetLifecycleStage), default=AssetLifecycleStage.PROCUREMENT)

    # Stage dates
    procurement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deployment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    operational_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    maintenance_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decommission_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retirement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disposal_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Expected dates
    expected_end_of_life: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_refresh_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Financial
    depreciation_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    depreciation_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    residual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Maintenance
    maintenance_schedule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_maintenance: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_maintenance: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    maintenance_provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    maintenance_contract: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Disposal
    disposal_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    disposal_certificate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_sanitization_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_sanitization_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id], backref="lifecycle")


class AssetRelationship(Base):
    """Relationships between assets."""
    __tablename__ = "asset_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Source and target
    source_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    target_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)

    # Relationship details
    relationship_type = mapped_column(SQLEnum(RelationshipType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Criticality
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

    # Validity
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    source_asset = relationship("Asset", foreign_keys=[source_asset_id], backref="outgoing_relationships")
    target_asset = relationship("Asset", foreign_keys=[target_asset_id], backref="incoming_relationships")


class AssetChange(Base):
    """Asset/CI change history."""
    __tablename__ = "asset_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Links (one of these should be set)
    asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assets.id"), nullable=True)
    ci_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("configuration_items.id"), nullable=True)

    # Change details
    change_type = mapped_column(SQLEnum(ChangeType), nullable=False)
    change_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Before/After state
    previous_state = mapped_column(JSON, default={})
    new_state = mapped_column(JSON, default={})
    changed_fields = mapped_column(JSON, default=[])

    # Change management
    change_ticket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    change_request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Related incident (if change was due to incident)
    incident_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=True)

    # Timestamps
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    changed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id], backref="changes")
    configuration_item = relationship("ConfigurationItem", back_populates="change_history")
