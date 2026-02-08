"""
Attack Path Analysis Models

Models for analyzing potential attack paths through infrastructure.
"""

import enum
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Date,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from src.db.database import Base
from src.models.mixins import TenantMixin


# ============================================================================
# Enums
# ============================================================================


class GraphScopeType(str, enum.Enum):
    """Scope type for attack graphs"""
    FULL = "full"
    ZONE = "zone"
    CUSTOM = "custom"


class GraphStatus(str, enum.Enum):
    """Status of attack graph computation"""
    COMPUTING = "computing"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"


class PathStatus(str, enum.Enum):
    """Status of an attack path"""
    ACTIVE = "active"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class SimulationType(str, enum.Enum):
    """Type of what-if simulation"""
    PATCH_VULNERABILITY = "patch_vulnerability"
    SEGMENT_NETWORK = "segment_network"
    REMOVE_ACCESS = "remove_access"
    ADD_CONTROL = "add_control"
    COMPROMISE_ASSET = "compromise_asset"


class SimulationStatus(str, enum.Enum):
    """Status of simulation"""
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class JewelType(str, enum.Enum):
    """Type of crown jewel asset"""
    DATA = "data"
    SYSTEM = "system"
    CREDENTIAL = "credential"
    NETWORK = "network"
    IDENTITY = "identity"


class BusinessImpact(str, enum.Enum):
    """Business impact level"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class DataClassification(str, enum.Enum):
    """Data classification level"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class EntryType(str, enum.Enum):
    """Type of entry point"""
    INTERNET_FACING = "internet_facing"
    VPN_ENDPOINT = "vpn_endpoint"
    EMAIL_GATEWAY = "email_gateway"
    REMOTE_ACCESS = "remote_access"
    PARTNER_CONNECTION = "partner_connection"
    PHYSICAL_ACCESS = "physical_access"
    SUPPLY_CHAIN = "supply_chain"


class ExposureLevel(str, enum.Enum):
    """Exposure level of entry point"""
    PUBLIC = "public"
    SEMI_PUBLIC = "semi_public"
    INTERNAL = "internal"


class TrustLevel(str, enum.Enum):
    """Trust level of an asset for CMDB extension"""
    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TRUSTED = "trusted"


class TargetCriticality(str, enum.Enum):
    """Criticality of attack path target"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Models
# ============================================================================


class AttackGraph(TenantMixin, Base):
    """
    Computed attack graph for an organization.

    Stores the graph structure as JSON for flexibility and query performance.
    The graph is computed from CMDB assets, relationships, and vulnerabilities.
    """
    __tablename__ = "attack_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Graph metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Scope
    scope_type = Column(
        Enum(GraphScopeType, name="graph_scope_type_enum"),
        nullable=False,
        default=GraphScopeType.FULL
    )
    scope_filter = Column(JSON, nullable=True)  # Filter criteria for included assets

    # Graph data (stored as JSON for flexibility)
    nodes = Column(JSON, nullable=False, default=list)  # List of node objects
    edges = Column(JSON, nullable=False, default=list)  # List of edge objects

    # Statistics
    total_nodes = Column(Integer, nullable=False, default=0)
    total_edges = Column(Integer, nullable=False, default=0)
    entry_points_count = Column(Integer, nullable=False, default=0)
    crown_jewels_count = Column(Integer, nullable=False, default=0)

    # Computation metadata
    computed_at = Column(DateTime, nullable=True)
    computation_duration_ms = Column(Integer, nullable=True)
    data_sources = Column(JSON, nullable=True)  # Which modules contributed data

    # Status
    status = Column(
        Enum(GraphStatus, name="graph_status_enum"),
        nullable=False,
        default=GraphStatus.COMPUTING
    )
    error_message = Column(Text, nullable=True)

    # Staleness tracking
    last_cmdb_sync = Column(DateTime, nullable=True)
    last_vuln_sync = Column(DateTime, nullable=True)
    is_stale = Column(Boolean, nullable=False, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    paths = relationship("AttackPath", back_populates="graph", cascade="all, delete-orphan")
    simulations = relationship("AttackPathSimulation", back_populates="graph", cascade="all, delete-orphan")


class AttackPath(TenantMixin, Base):
    """
    Individual attack path from entry point to crown jewel.

    Represents a specific route an attacker could take through the infrastructure.
    """
    __tablename__ = "attack_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("attack_graphs.id", ondelete="CASCADE"), nullable=False)

    # Path identification
    path_id = Column(String(50), nullable=False)  # e.g., "PATH-001"
    name = Column(String(255), nullable=False)  # Auto-generated or custom

    # Entry point details
    entry_point_id = Column(UUID(as_uuid=True), nullable=False)  # CMDB asset ID
    entry_point_name = Column(String(255), nullable=False)
    entry_point_type = Column(String(100), nullable=False)

    # Target (crown jewel) details
    target_id = Column(UUID(as_uuid=True), nullable=False)  # CMDB asset ID
    target_name = Column(String(255), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_criticality = Column(
        Enum(TargetCriticality, name="target_criticality_enum"),
        nullable=False,
        default=TargetCriticality.HIGH
    )

    # Path details
    path_nodes = Column(JSON, nullable=False)  # Ordered list of asset IDs in path
    path_edges = Column(JSON, nullable=False)  # List of edge details
    hop_count = Column(Integer, nullable=False)  # Number of hops

    # Risk scoring
    risk_score = Column(Float, nullable=False, default=0.0)  # 0-10
    exploitability_score = Column(Float, nullable=False, default=0.0)  # Based on vulns in path
    impact_score = Column(Float, nullable=False, default=0.0)  # Based on target criticality

    # Vulnerability context
    vulns_in_path = Column(JSON, nullable=True)  # CVEs present in path nodes
    exploitable_vulns = Column(Integer, nullable=False, default=0)  # Count with EPSS > 0.1 or in KEV

    # Analysis
    chokepoints = Column(JSON, nullable=True)  # Assets that if secured would break path
    alternative_paths = Column(Integer, nullable=False, default=0)  # Count of other paths to same target

    # Status
    status = Column(
        Enum(PathStatus, name="path_status_enum"),
        nullable=False,
        default=PathStatus.ACTIVE
    )
    mitigated_at = Column(DateTime, nullable=True)
    mitigated_by = Column(String(255), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    graph = relationship("AttackGraph", back_populates="paths")


class AttackPathSimulation(TenantMixin, Base):
    """
    What-if simulation for attack paths.

    Allows users to simulate the effect of remediation actions on attack paths.
    """
    __tablename__ = "attack_path_simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("attack_graphs.id", ondelete="CASCADE"), nullable=False)

    # Simulation metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Simulation type
    simulation_type = Column(
        Enum(SimulationType, name="simulation_type_enum"),
        nullable=False
    )

    # Simulation parameters (depends on simulation_type)
    # Examples:
    # patch_vulnerability: {"cve_id": "CVE-2024-1234"}
    # segment_network: {"asset_id": "...", "new_zone": "dmz"}
    # add_control: {"asset_id": "...", "control_type": "mfa"}
    parameters = Column(JSON, nullable=False)

    # Results
    original_paths_count = Column(Integer, nullable=True)
    resulting_paths_count = Column(Integer, nullable=True)
    paths_eliminated = Column(Integer, nullable=True)
    risk_reduction_percent = Column(Float, nullable=True)

    affected_paths = Column(JSON, nullable=True)  # List of path IDs affected
    new_risk_scores = Column(JSON, nullable=True)  # Updated scores per path

    # Recommendations
    recommendation = Column(Text, nullable=True)  # AI-generated or rule-based
    cost_estimate = Column(String(255), nullable=True)  # Estimated effort

    # Status
    status = Column(
        Enum(SimulationStatus, name="simulation_status_enum"),
        nullable=False,
        default=SimulationStatus.PENDING
    )
    computed_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    graph = relationship("AttackGraph", back_populates="simulations")


class CrownJewel(TenantMixin, Base):
    """
    Critical assets that attackers target.

    Crown jewels are the high-value assets that represent the ultimate
    targets in an attack scenario (e.g., databases with PII, AD controllers).
    """
    __tablename__ = "crown_jewels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to CMDB asset

    # Classification
    jewel_type = Column(
        Enum(JewelType, name="jewel_type_enum"),
        nullable=False
    )

    # Importance
    business_impact = Column(
        Enum(BusinessImpact, name="business_impact_enum"),
        nullable=False,
        default=BusinessImpact.HIGH
    )
    data_classification = Column(
        Enum(DataClassification, name="data_classification_enum"),
        nullable=True
    )

    # Context
    description = Column(Text, nullable=False)
    business_owner = Column(String(255), nullable=False)
    data_types = Column(JSON, nullable=True)  # e.g., ["PII", "PHI", "Financial"]
    compliance_scope = Column(JSON, nullable=True)  # e.g., ["GDPR", "HIPAA", "PCI-DSS"]

    # Valuation (for FAIR analysis)
    estimated_value = Column(Numeric(15, 2), nullable=True)  # Estimated loss if compromised

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class EntryPoint(TenantMixin, Base):
    """
    Potential attacker entry points.

    Entry points are assets that could be the initial foothold for an attacker
    (e.g., internet-facing servers, VPN gateways, email servers).
    """
    __tablename__ = "entry_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to CMDB asset

    # Classification
    entry_type = Column(
        Enum(EntryType, name="entry_type_enum"),
        nullable=False
    )

    # Exposure details
    exposure_level = Column(
        Enum(ExposureLevel, name="exposure_level_enum"),
        nullable=False,
        default=ExposureLevel.PUBLIC
    )
    protocols_exposed = Column(JSON, nullable=True)  # e.g., ["HTTPS", "SSH", "RDP"]
    ports_exposed = Column(JSON, nullable=True)  # e.g., [443, 22, 3389]

    # Risk context
    authentication_required = Column(Boolean, nullable=False, default=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    known_vulnerabilities = Column(Integer, nullable=False, default=0)  # Count of CVEs on this asset

    # Context
    description = Column(Text, nullable=False)
    last_pentest_date = Column(Date, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
