"""
CMDB Schemas.

Pydantic schemas for Configuration Management Database API validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class ConfigurationItemType(str, Enum):
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


class ConfigurationItemStatus(str, Enum):
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class AssetLifecycleStage(str, Enum):
    PROCUREMENT = "procurement"
    DEPLOYMENT = "deployment"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DECOMMISSIONING = "decommissioning"
    RETIRED = "retired"
    DISPOSED = "disposed"


class RelationshipType(str, Enum):
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


class ChangeType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    CONFIGURATION = "configuration"
    PATCH = "patch"
    UPGRADE = "upgrade"
    MIGRATION = "migration"
    MAINTENANCE = "maintenance"
    INCIDENT = "incident"
    DECOMMISSIONED = "decommissioned"


class SoftwareCategory(str, Enum):
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


class LicenseType(str, Enum):
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


# Configuration Item Schemas
class ConfigurationItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = None
    description: Optional[str] = None
    ci_type: ConfigurationItemType
    version: Optional[str] = None
    configuration: Dict[str, Any] = {}
    business_service: Optional[str] = None
    business_criticality: Optional[str] = None
    sla_tier: Optional[str] = None
    owner: Optional[str] = None
    technical_owner: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    vendor: Optional[str] = None
    documentation_url: Optional[str] = None
    support_contact: Optional[str] = None
    compliance_requirements: List[str] = []
    data_classification: Optional[str] = None
    tags: List[str] = []


class ConfigurationItemCreate(ConfigurationItemBase):
    asset_id: Optional[str] = None
    baseline_configuration: Dict[str, Any] = {}
    go_live_date: Optional[datetime] = None


class ConfigurationItemUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    ci_type: Optional[ConfigurationItemType] = None
    status: Optional[ConfigurationItemStatus] = None
    version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    baseline_configuration: Optional[Dict[str, Any]] = None
    business_service: Optional[str] = None
    business_criticality: Optional[str] = None
    sla_tier: Optional[str] = None
    owner: Optional[str] = None
    technical_owner: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    vendor: Optional[str] = None
    documentation_url: Optional[str] = None
    support_contact: Optional[str] = None
    compliance_requirements: Optional[List[str]] = None
    data_classification: Optional[str] = None
    tags: Optional[List[str]] = None
    go_live_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None


class ConfigurationItemResponse(ConfigurationItemBase):
    id: str
    ci_id: str
    status: ConfigurationItemStatus
    asset_id: Optional[str] = None
    baseline_configuration: Dict[str, Any] = {}
    go_live_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfigurationItemListResponse(BaseModel):
    items: List[ConfigurationItemResponse]
    total: int
    page: int
    page_size: int


# Software Item Schemas
class SoftwareItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    vendor: Optional[str] = None
    version: Optional[str] = None
    category: Optional[SoftwareCategory] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    license_type: Optional[LicenseType] = None
    license_required: bool = False
    cpe_id: Optional[str] = None
    tags: List[str] = []


class SoftwareItemCreate(SoftwareItemBase):
    is_approved: bool = False
    is_prohibited: bool = False
    end_of_life_date: Optional[datetime] = None
    end_of_support_date: Optional[datetime] = None


class SoftwareItemUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    category: Optional[SoftwareCategory] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    license_type: Optional[LicenseType] = None
    license_required: Optional[bool] = None
    is_approved: Optional[bool] = None
    is_prohibited: Optional[bool] = None
    cpe_id: Optional[str] = None
    end_of_life_date: Optional[datetime] = None
    end_of_support_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class SoftwareItemResponse(SoftwareItemBase):
    id: str
    is_approved: bool
    is_prohibited: bool
    known_vulnerabilities: int
    end_of_life_date: Optional[datetime] = None
    end_of_support_date: Optional[datetime] = None
    created_at: datetime
    installation_count: int = 0

    class Config:
        from_attributes = True


class SoftwareItemListResponse(BaseModel):
    items: List[SoftwareItemResponse]
    total: int
    page: int
    page_size: int


# Software Installation Schemas
class SoftwareInstallationCreate(BaseModel):
    software_id: str
    asset_id: Optional[str] = None
    ci_id: Optional[str] = None
    installed_version: str
    installation_path: Optional[str] = None
    installation_date: Optional[datetime] = None
    license_id: Optional[str] = None
    discovery_source: Optional[str] = None


class SoftwareInstallationResponse(BaseModel):
    id: str
    software_id: str
    software_name: Optional[str] = None
    asset_id: Optional[str] = None
    ci_id: Optional[str] = None
    installed_version: str
    installation_path: Optional[str] = None
    installation_date: Optional[datetime] = None
    is_active: bool
    needs_update: bool
    latest_available_version: Optional[str] = None
    license_id: Optional[str] = None
    discovered_at: Optional[datetime] = None
    discovery_source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Software License Schemas
class SoftwareLicenseCreate(BaseModel):
    software_id: str
    license_key: Optional[str] = None
    license_type: LicenseType
    license_name: Optional[str] = None
    total_licenses: int = 1
    purchase_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    cost: Optional[float] = None
    currency: str = "USD"
    renewal_cost: Optional[float] = None
    vendor: Optional[str] = None
    support_expiration: Optional[datetime] = None
    contract_reference: Optional[str] = None
    notes: Optional[str] = None


class SoftwareLicenseResponse(BaseModel):
    id: str
    software_id: str
    software_name: Optional[str] = None
    license_key: Optional[str] = None
    license_type: LicenseType
    license_name: Optional[str] = None
    total_licenses: int
    used_licenses: int
    available_licenses: int = 0
    purchase_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_active: bool
    is_expired: bool = False
    cost: Optional[float] = None
    currency: str
    vendor: Optional[str] = None
    support_expiration: Optional[datetime] = None
    contract_reference: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Hardware Spec Schemas
class HardwareSpecCreate(BaseModel):
    asset_id: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    form_factor: Optional[str] = None
    rack_location: Optional[str] = None
    rack_unit: Optional[int] = None
    cpu_model: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_speed_ghz: Optional[float] = None
    ram_gb: Optional[int] = None
    ram_type: Optional[str] = None
    ram_slots_total: Optional[int] = None
    ram_slots_used: Optional[int] = None
    storage_total_gb: Optional[int] = None
    storage_type: Optional[str] = None
    storage_details: List[Dict[str, Any]] = []
    network_interfaces: List[Dict[str, Any]] = []
    power_supply_watts: Optional[int] = None
    power_supplies_count: Optional[int] = None
    warranty_start: Optional[datetime] = None
    warranty_end: Optional[datetime] = None
    warranty_provider: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_cost: Optional[float] = None
    purchase_vendor: Optional[str] = None
    purchase_order: Optional[str] = None


class HardwareSpecUpdate(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    form_factor: Optional[str] = None
    rack_location: Optional[str] = None
    rack_unit: Optional[int] = None
    cpu_model: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_speed_ghz: Optional[float] = None
    ram_gb: Optional[int] = None
    ram_type: Optional[str] = None
    ram_slots_total: Optional[int] = None
    ram_slots_used: Optional[int] = None
    storage_total_gb: Optional[int] = None
    storage_type: Optional[str] = None
    storage_details: Optional[List[Dict[str, Any]]] = None
    network_interfaces: Optional[List[Dict[str, Any]]] = None
    power_supply_watts: Optional[int] = None
    power_supplies_count: Optional[int] = None
    warranty_start: Optional[datetime] = None
    warranty_end: Optional[datetime] = None
    warranty_provider: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_cost: Optional[float] = None
    purchase_vendor: Optional[str] = None
    purchase_order: Optional[str] = None


class HardwareSpecResponse(HardwareSpecCreate):
    id: str
    warranty_status: str = "unknown"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Asset Lifecycle Schemas
class AssetLifecycleCreate(BaseModel):
    asset_id: str
    current_stage: AssetLifecycleStage = AssetLifecycleStage.PROCUREMENT
    procurement_date: Optional[datetime] = None
    expected_end_of_life: Optional[datetime] = None
    expected_refresh_date: Optional[datetime] = None
    depreciation_method: Optional[str] = None
    depreciation_years: Optional[int] = None
    maintenance_schedule: Optional[str] = None
    maintenance_provider: Optional[str] = None
    maintenance_contract: Optional[str] = None
    notes: Optional[str] = None


class AssetLifecycleUpdate(BaseModel):
    current_stage: Optional[AssetLifecycleStage] = None
    procurement_date: Optional[datetime] = None
    deployment_date: Optional[datetime] = None
    operational_date: Optional[datetime] = None
    maintenance_start_date: Optional[datetime] = None
    decommission_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    disposal_date: Optional[datetime] = None
    expected_end_of_life: Optional[datetime] = None
    expected_refresh_date: Optional[datetime] = None
    depreciation_method: Optional[str] = None
    depreciation_years: Optional[int] = None
    current_value: Optional[float] = None
    residual_value: Optional[float] = None
    maintenance_schedule: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    maintenance_provider: Optional[str] = None
    maintenance_contract: Optional[str] = None
    disposal_method: Optional[str] = None
    disposal_certificate: Optional[str] = None
    data_sanitization_date: Optional[datetime] = None
    data_sanitization_method: Optional[str] = None
    notes: Optional[str] = None


class AssetLifecycleResponse(BaseModel):
    id: str
    asset_id: str
    current_stage: AssetLifecycleStage
    procurement_date: Optional[datetime] = None
    deployment_date: Optional[datetime] = None
    operational_date: Optional[datetime] = None
    maintenance_start_date: Optional[datetime] = None
    decommission_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    disposal_date: Optional[datetime] = None
    expected_end_of_life: Optional[datetime] = None
    expected_refresh_date: Optional[datetime] = None
    depreciation_method: Optional[str] = None
    depreciation_years: Optional[int] = None
    current_value: Optional[float] = None
    residual_value: Optional[float] = None
    maintenance_schedule: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    maintenance_provider: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Asset Relationship Schemas
class AssetRelationshipCreate(BaseModel):
    source_asset_id: str
    target_asset_id: str
    relationship_type: RelationshipType
    description: Optional[str] = None
    is_critical: bool = False
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class AssetRelationshipResponse(BaseModel):
    id: str
    source_asset_id: str
    source_asset_name: Optional[str] = None
    target_asset_id: str
    target_asset_name: Optional[str] = None
    relationship_type: RelationshipType
    description: Optional[str] = None
    is_critical: bool
    is_active: bool
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Asset Change Schemas
class AssetChangeCreate(BaseModel):
    asset_id: Optional[str] = None
    ci_id: Optional[str] = None
    change_type: ChangeType
    change_summary: str
    change_description: Optional[str] = None
    previous_state: Dict[str, Any] = {}
    new_state: Dict[str, Any] = {}
    changed_fields: List[str] = []
    change_ticket: Optional[str] = None
    change_request_id: Optional[str] = None
    approved_by: Optional[str] = None
    incident_id: Optional[str] = None


class AssetChangeResponse(BaseModel):
    id: str
    asset_id: Optional[str] = None
    ci_id: Optional[str] = None
    change_type: ChangeType
    change_summary: str
    change_description: Optional[str] = None
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    changed_fields: List[str]
    change_ticket: Optional[str] = None
    change_request_id: Optional[str] = None
    approved_by: Optional[str] = None
    incident_id: Optional[str] = None
    changed_at: datetime
    changed_by: Optional[str] = None

    class Config:
        from_attributes = True


class AssetChangeListResponse(BaseModel):
    changes: List[AssetChangeResponse]
    total: int
    page: int
    page_size: int


# CMDB Statistics
class CMDBStats(BaseModel):
    total_assets: int
    active_assets: int
    total_configuration_items: int
    production_cis: int
    total_software_items: int
    approved_software: int
    prohibited_software: int
    total_licenses: int
    expiring_licenses: int
    total_relationships: int
    assets_by_type: Dict[str, int]
    assets_by_criticality: Dict[str, int]
    assets_by_environment: Dict[str, int]
    cis_by_type: Dict[str, int]
    cis_by_status: Dict[str, int]
    software_by_category: Dict[str, int]
    lifecycle_by_stage: Dict[str, int]
    recent_changes: List[AssetChangeResponse] = []


# Dependency Map
class DependencyNode(BaseModel):
    id: str
    name: str
    type: str
    criticality: Optional[str] = None


class DependencyEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    is_critical: bool


class DependencyMap(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
