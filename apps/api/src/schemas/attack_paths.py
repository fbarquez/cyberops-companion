"""
Attack Path Analysis Schemas.

Pydantic schemas for API validation and serialization.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# ========== Enums ==========

class GraphScopeType(str, Enum):
    """Scope type for attack graphs."""
    FULL = "full"
    ZONE = "zone"
    CUSTOM = "custom"


class GraphStatus(str, Enum):
    """Status of attack graph computation."""
    COMPUTING = "computing"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"


class PathStatus(str, Enum):
    """Status of an attack path."""
    ACTIVE = "active"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class SimulationType(str, Enum):
    """Type of what-if simulation."""
    PATCH_VULNERABILITY = "patch_vulnerability"
    SEGMENT_NETWORK = "segment_network"
    REMOVE_ACCESS = "remove_access"
    ADD_CONTROL = "add_control"
    COMPROMISE_ASSET = "compromise_asset"


class SimulationStatus(str, Enum):
    """Status of simulation."""
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class JewelType(str, Enum):
    """Type of crown jewel asset."""
    DATA = "data"
    SYSTEM = "system"
    CREDENTIAL = "credential"
    NETWORK = "network"
    IDENTITY = "identity"


class BusinessImpact(str, Enum):
    """Business impact level."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class DataClassification(str, Enum):
    """Data classification level."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class EntryType(str, Enum):
    """Type of entry point."""
    INTERNET_FACING = "internet_facing"
    VPN_ENDPOINT = "vpn_endpoint"
    EMAIL_GATEWAY = "email_gateway"
    REMOTE_ACCESS = "remote_access"
    PARTNER_CONNECTION = "partner_connection"
    PHYSICAL_ACCESS = "physical_access"
    SUPPLY_CHAIN = "supply_chain"


class ExposureLevel(str, Enum):
    """Exposure level of entry point."""
    PUBLIC = "public"
    SEMI_PUBLIC = "semi_public"
    INTERNAL = "internal"


class TargetCriticality(str, Enum):
    """Criticality of attack path target."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ========== Graph Node/Edge Schemas ==========

class GraphNode(BaseModel):
    """Node in the attack graph."""
    id: str
    name: str
    type: str
    criticality: Optional[str] = None
    zone: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = []
    is_entry_point: bool = False
    is_crown_jewel: bool = False
    risk_score: float = 0.0
    metadata: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """Edge in the attack graph."""
    source: str
    target: str
    type: str  # network, access, trust
    direction: str = "unidirectional"  # unidirectional, bidirectional
    protocol: Optional[str] = None
    requires_auth: bool = True
    traversal_difficulty: float = 1.0
    metadata: Dict[str, Any] = {}


# ========== Attack Graph Schemas ==========

class AttackGraphBase(BaseModel):
    """Base schema for attack graph."""
    name: str = Field(..., description="Graph name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Graph description")
    scope_type: GraphScopeType = Field(GraphScopeType.FULL, description="Scope type")
    scope_filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for included assets")


class AttackGraphCreate(AttackGraphBase):
    """Schema for creating an attack graph."""
    pass


class AttackGraphUpdate(BaseModel):
    """Schema for updating an attack graph."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scope_type: Optional[GraphScopeType] = None
    scope_filter: Optional[Dict[str, Any]] = None


class AttackGraphResponse(AttackGraphBase):
    """Response schema for attack graph."""
    id: str
    tenant_id: str
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    total_nodes: int = 0
    total_edges: int = 0
    entry_points_count: int = 0
    crown_jewels_count: int = 0
    computed_at: Optional[datetime] = None
    computation_duration_ms: Optional[int] = None
    data_sources: Optional[Dict[str, Any]] = None
    status: GraphStatus = GraphStatus.COMPUTING
    error_message: Optional[str] = None
    last_cmdb_sync: Optional[datetime] = None
    last_vuln_sync: Optional[datetime] = None
    is_stale: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class AttackGraphListResponse(BaseModel):
    """Paginated list of attack graphs."""
    graphs: List[AttackGraphResponse]
    total: int
    page: int = 1
    page_size: int = 20


class AttackGraphStatistics(BaseModel):
    """Statistics for an attack graph."""
    graph_id: str
    total_nodes: int
    total_edges: int
    entry_points_count: int
    crown_jewels_count: int
    critical_paths_count: int
    high_risk_paths_count: int
    average_path_length: float
    max_risk_score: float
    zones: List[str]
    asset_types: Dict[str, int]


# ========== Attack Path Schemas ==========

class AttackPathBase(BaseModel):
    """Base schema for attack path."""
    name: str = Field(..., description="Path name")


class AttackPathResponse(BaseModel):
    """Response schema for attack path."""
    id: str
    tenant_id: str
    graph_id: str
    path_id: str
    name: str
    entry_point_id: str
    entry_point_name: str
    entry_point_type: str
    target_id: str
    target_name: str
    target_type: str
    target_criticality: TargetCriticality
    path_nodes: List[str]
    path_edges: List[Dict[str, Any]]
    hop_count: int
    risk_score: float
    exploitability_score: float
    impact_score: float
    vulns_in_path: Optional[List[Dict[str, Any]]] = None
    exploitable_vulns: int = 0
    chokepoints: Optional[List[Dict[str, Any]]] = None
    alternative_paths: int = 0
    status: PathStatus = PathStatus.ACTIVE
    mitigated_at: Optional[datetime] = None
    mitigated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttackPathListResponse(BaseModel):
    """Paginated list of attack paths."""
    paths: List[AttackPathResponse]
    total: int
    page: int = 1
    page_size: int = 20


class AttackPathStatusUpdate(BaseModel):
    """Schema for updating attack path status."""
    status: PathStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class AttackPathRemediation(BaseModel):
    """Remediation recommendations for an attack path."""
    path_id: str
    recommendations: List[Dict[str, Any]]
    priority_actions: List[Dict[str, Any]]
    estimated_risk_reduction: float
    chokepoints_to_secure: List[Dict[str, Any]]


# ========== Simulation Schemas ==========

class SimulationParametersPatchVuln(BaseModel):
    """Parameters for patching vulnerability simulation."""
    cve_ids: List[str] = Field(..., description="CVE IDs to simulate patching")


class SimulationParametersSegment(BaseModel):
    """Parameters for network segmentation simulation."""
    asset_id: str = Field(..., description="Asset to isolate")
    new_zone: str = Field(..., description="New network zone")


class SimulationParametersAddControl(BaseModel):
    """Parameters for adding control simulation."""
    asset_id: str = Field(..., description="Asset to add control to")
    control_type: str = Field(..., description="Type of control (mfa, firewall, edr, etc.)")


class SimulationParametersCompromise(BaseModel):
    """Parameters for asset compromise simulation."""
    asset_id: str = Field(..., description="Asset assumed compromised")


class AttackPathSimulationCreate(BaseModel):
    """Schema for creating a simulation."""
    name: str = Field(..., description="Simulation name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Simulation description")
    graph_id: str = Field(..., description="Graph to simulate on")
    simulation_type: SimulationType = Field(..., description="Type of simulation")
    parameters: Dict[str, Any] = Field(..., description="Simulation parameters")


class AttackPathSimulationResponse(BaseModel):
    """Response schema for simulation."""
    id: str
    tenant_id: str
    graph_id: str
    name: str
    description: Optional[str] = None
    simulation_type: SimulationType
    parameters: Dict[str, Any]
    original_paths_count: Optional[int] = None
    resulting_paths_count: Optional[int] = None
    paths_eliminated: Optional[int] = None
    risk_reduction_percent: Optional[float] = None
    affected_paths: Optional[List[str]] = None
    new_risk_scores: Optional[Dict[str, float]] = None
    recommendation: Optional[str] = None
    cost_estimate: Optional[str] = None
    status: SimulationStatus = SimulationStatus.PENDING
    computed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class AttackPathSimulationListResponse(BaseModel):
    """Paginated list of simulations."""
    simulations: List[AttackPathSimulationResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== Crown Jewel Schemas ==========

class CrownJewelBase(BaseModel):
    """Base schema for crown jewel."""
    asset_id: str = Field(..., description="CMDB asset ID")
    jewel_type: JewelType = Field(..., description="Type of crown jewel")
    business_impact: BusinessImpact = Field(BusinessImpact.HIGH, description="Business impact level")
    data_classification: Optional[DataClassification] = Field(None, description="Data classification")
    description: str = Field(..., description="Description of why this is a crown jewel")
    business_owner: str = Field(..., description="Business owner")
    data_types: Optional[List[str]] = Field(None, description="Types of data (PII, PHI, etc.)")
    compliance_scope: Optional[List[str]] = Field(None, description="Compliance frameworks (GDPR, etc.)")
    estimated_value: Optional[Decimal] = Field(None, description="Estimated value if compromised")


class CrownJewelCreate(CrownJewelBase):
    """Schema for creating a crown jewel."""
    pass


class CrownJewelUpdate(BaseModel):
    """Schema for updating a crown jewel."""
    jewel_type: Optional[JewelType] = None
    business_impact: Optional[BusinessImpact] = None
    data_classification: Optional[DataClassification] = None
    description: Optional[str] = None
    business_owner: Optional[str] = None
    data_types: Optional[List[str]] = None
    compliance_scope: Optional[List[str]] = None
    estimated_value: Optional[Decimal] = None
    is_active: Optional[bool] = None


class CrownJewelResponse(CrownJewelBase):
    """Response schema for crown jewel."""
    id: str
    tenant_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    # Enriched data from CMDB
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None

    class Config:
        from_attributes = True


class CrownJewelListResponse(BaseModel):
    """Paginated list of crown jewels."""
    crown_jewels: List[CrownJewelResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== Entry Point Schemas ==========

class EntryPointBase(BaseModel):
    """Base schema for entry point."""
    asset_id: str = Field(..., description="CMDB asset ID")
    entry_type: EntryType = Field(..., description="Type of entry point")
    exposure_level: ExposureLevel = Field(ExposureLevel.PUBLIC, description="Exposure level")
    protocols_exposed: Optional[List[str]] = Field(None, description="Exposed protocols (HTTPS, SSH, etc.)")
    ports_exposed: Optional[List[int]] = Field(None, description="Exposed ports")
    authentication_required: bool = Field(True, description="Is authentication required")
    mfa_enabled: bool = Field(False, description="Is MFA enabled")
    description: str = Field(..., description="Description of this entry point")
    last_pentest_date: Optional[date] = Field(None, description="Last penetration test date")


class EntryPointCreate(EntryPointBase):
    """Schema for creating an entry point."""
    pass


class EntryPointUpdate(BaseModel):
    """Schema for updating an entry point."""
    entry_type: Optional[EntryType] = None
    exposure_level: Optional[ExposureLevel] = None
    protocols_exposed: Optional[List[str]] = None
    ports_exposed: Optional[List[int]] = None
    authentication_required: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    description: Optional[str] = None
    last_pentest_date: Optional[date] = None
    is_active: Optional[bool] = None


class EntryPointResponse(EntryPointBase):
    """Response schema for entry point."""
    id: str
    tenant_id: str
    known_vulnerabilities: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    # Enriched data from CMDB
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None

    class Config:
        from_attributes = True


class EntryPointListResponse(BaseModel):
    """Paginated list of entry points."""
    entry_points: List[EntryPointResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ========== Dashboard Schemas ==========

class AttackPathDashboard(BaseModel):
    """Dashboard overview for attack path analysis."""
    total_graphs: int
    total_paths: int
    critical_paths: int
    high_risk_paths: int
    entry_points_count: int
    crown_jewels_count: int
    top_chokepoints: List[Dict[str, Any]]
    recent_simulations: List[AttackPathSimulationResponse]
    risk_distribution: Dict[str, int]
    paths_by_status: Dict[str, int]


class ChokepointInfo(BaseModel):
    """Information about a chokepoint asset."""
    asset_id: str
    asset_name: str
    asset_type: str
    paths_affected: int
    total_risk_mitigated: float
    priority_score: float
    vulnerabilities_count: int
    recommendations: List[str]


class ChokepointListResponse(BaseModel):
    """List of chokepoints."""
    chokepoints: List[ChokepointInfo]
    total: int
