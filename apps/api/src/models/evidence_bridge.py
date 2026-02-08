"""
Evidence Bridge Models

This module implements the ISMS ↔ SOC bridge that automatically links
operational activities to compliance controls, enabling real-time
control effectiveness calculation from actual security operations.

The core promise: "ISMS-Anforderungen → Überprüfbare Aktivitäten → Evidenzen"
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, JSON,
    DateTime, Enum as SQLEnum, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship

from src.models.base import Base


# =============================================================================
# ENUMS
# =============================================================================

class ActivityType(str, Enum):
    """Types of operational activities that can serve as evidence."""
    INCIDENT = "incident"
    ALERT = "alert"
    CASE = "case"
    VULNERABILITY_SCAN = "vulnerability_scan"
    VULNERABILITY = "vulnerability"
    THREAT_IOC = "threat_ioc"
    PLAYBOOK_EXECUTION = "playbook_execution"
    RISK_ASSESSMENT = "risk_assessment"
    BCM_EXERCISE = "bcm_exercise"
    TRAINING_COMPLETION = "training_completion"
    DOCUMENT_APPROVAL = "document_approval"
    AUDIT_LOG = "audit_log"
    VENDOR_ASSESSMENT = "vendor_assessment"
    CHANGE_REQUEST = "change_request"


class ControlFramework(str, Enum):
    """Supported compliance frameworks."""
    ISO27001 = "iso27001"
    DORA = "dora"
    NIS2 = "nis2"
    BSI = "bsi"
    GDPR = "gdpr"
    TISAX = "tisax"
    NIST = "nist"
    KRITIS = "kritis"


class LinkType(str, Enum):
    """How the evidence was linked to the control."""
    AUTOMATIC = "automatic"  # System detected and linked
    MANUAL = "manual"        # User explicitly linked
    SUGGESTED = "suggested"  # System suggested, user confirmed


class EvidenceStrength(str, Enum):
    """How strongly this activity evidences the control."""
    STRONG = "strong"      # Direct proof of control operation
    MODERATE = "moderate"  # Supports control effectiveness
    WEAK = "weak"          # Tangential evidence


class EffectivenessLevel(str, Enum):
    """Control effectiveness levels based on evidence."""
    NOT_ASSESSED = "not_assessed"
    INEFFECTIVE = "ineffective"      # 0-25%
    PARTIALLY_EFFECTIVE = "partially_effective"  # 26-50%
    LARGELY_EFFECTIVE = "largely_effective"      # 51-75%
    FULLY_EFFECTIVE = "fully_effective"          # 76-100%


# =============================================================================
# CONTROL-ACTIVITY MAPPING RULES
# =============================================================================

# These rules define which activities automatically link to which controls
CONTROL_ACTIVITY_MAPPING = {
    # ISO 27001:2022 Controls
    "iso27001": {
        # A.5.24 - Information security incident management planning and preparation
        "A.5.24": {
            "activities": [ActivityType.INCIDENT, ActivityType.PLAYBOOK_EXECUTION],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["incident_count", "response_time", "resolution_rate"],
        },
        # A.5.25 - Assessment and decision on information security events
        "A.5.25": {
            "activities": [ActivityType.ALERT, ActivityType.CASE],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["alert_triage_time", "false_positive_rate"],
        },
        # A.5.26 - Response to information security incidents
        "A.5.26": {
            "activities": [ActivityType.INCIDENT, ActivityType.PLAYBOOK_EXECUTION],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["mttr", "containment_time"],
        },
        # A.5.27 - Learning from information security incidents
        "A.5.27": {
            "activities": [ActivityType.INCIDENT],  # Post-incident reports
            "strength": EvidenceStrength.MODERATE,
            "metrics": ["lessons_learned_count", "improvements_implemented"],
        },
        # A.5.28 - Collection of evidence
        "A.5.28": {
            "activities": [ActivityType.INCIDENT, ActivityType.AUDIT_LOG],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["evidence_integrity_verified"],
        },
        # A.8.8 - Management of technical vulnerabilities
        "A.8.8": {
            "activities": [ActivityType.VULNERABILITY_SCAN, ActivityType.VULNERABILITY],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["vuln_count", "remediation_rate", "scan_coverage"],
        },
        # A.8.16 - Monitoring activities
        "A.8.16": {
            "activities": [ActivityType.ALERT, ActivityType.THREAT_IOC],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["alert_volume", "detection_coverage"],
        },
        # A.5.7 - Threat intelligence
        "A.5.7": {
            "activities": [ActivityType.THREAT_IOC],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["ioc_count", "enrichment_rate", "feed_freshness"],
        },
        # A.5.23 - Information security for use of cloud services
        "A.5.23": {
            "activities": [ActivityType.VENDOR_ASSESSMENT],
            "strength": EvidenceStrength.MODERATE,
            "metrics": ["vendor_assessments_completed"],
        },
        # A.6.3 - Information security awareness, education and training
        "A.6.3": {
            "activities": [ActivityType.TRAINING_COMPLETION],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["training_completion_rate", "quiz_pass_rate"],
        },
        # A.5.1 - Policies for information security
        "A.5.1": {
            "activities": [ActivityType.DOCUMENT_APPROVAL],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["policies_approved", "acknowledgment_rate"],
        },
        # A.8.32 - Change management
        "A.8.32": {
            "activities": [ActivityType.CHANGE_REQUEST],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["changes_approved", "unauthorized_changes"],
        },
        # A.5.29 - Information security during disruption
        "A.5.29": {
            "activities": [ActivityType.BCM_EXERCISE],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["exercises_completed", "rto_achieved"],
        },
        # A.5.30 - ICT readiness for business continuity
        "A.5.30": {
            "activities": [ActivityType.BCM_EXERCISE, ActivityType.INCIDENT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["recovery_tests_passed"],
        },
    },

    # DORA Pillars and Requirements
    "dora": {
        # Pillar 2: ICT Incident Management
        "DORA-P2-01": {
            "activities": [ActivityType.INCIDENT, ActivityType.ALERT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["incident_count", "classification_accuracy"],
        },
        "DORA-P2-02": {
            "activities": [ActivityType.INCIDENT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["major_incidents_reported", "reporting_timeliness"],
        },
        # Pillar 3: Digital Operational Resilience Testing
        "DORA-P3-01": {
            "activities": [ActivityType.VULNERABILITY_SCAN, ActivityType.BCM_EXERCISE],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["tests_executed", "vulnerabilities_found"],
        },
        # Pillar 4: ICT Third-Party Risk
        "DORA-P4-01": {
            "activities": [ActivityType.VENDOR_ASSESSMENT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["vendors_assessed", "critical_vendors_monitored"],
        },
        # Pillar 1: ICT Risk Management
        "DORA-P1-01": {
            "activities": [ActivityType.RISK_ASSESSMENT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["risks_assessed", "controls_implemented"],
        },
    },

    # NIS2 Article 21 Measures
    "nis2": {
        # (a) policies on risk analysis and information system security
        "NIS2-21-a": {
            "activities": [ActivityType.RISK_ASSESSMENT, ActivityType.DOCUMENT_APPROVAL],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["risk_assessments", "policies_current"],
        },
        # (b) incident handling
        "NIS2-21-b": {
            "activities": [ActivityType.INCIDENT, ActivityType.ALERT, ActivityType.PLAYBOOK_EXECUTION],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["incidents_handled", "response_time"],
        },
        # (c) business continuity and crisis management
        "NIS2-21-c": {
            "activities": [ActivityType.BCM_EXERCISE],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["bcm_exercises", "recovery_capability"],
        },
        # (d) supply chain security
        "NIS2-21-d": {
            "activities": [ActivityType.VENDOR_ASSESSMENT],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["suppliers_assessed"],
        },
        # (e) security in network and information systems acquisition
        "NIS2-21-e": {
            "activities": [ActivityType.VULNERABILITY_SCAN, ActivityType.CHANGE_REQUEST],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["security_reviews"],
        },
        # (g) basic cyber hygiene practices and training
        "NIS2-21-g": {
            "activities": [ActivityType.TRAINING_COMPLETION],
            "strength": EvidenceStrength.STRONG,
            "metrics": ["training_completion", "awareness_score"],
        },
        # (j) use of multi-factor authentication
        "NIS2-21-j": {
            "activities": [ActivityType.AUDIT_LOG],
            "strength": EvidenceStrength.MODERATE,
            "metrics": ["mfa_adoption_rate"],
        },
    },
}


# =============================================================================
# DATABASE MODELS
# =============================================================================

class ControlEvidenceLink(Base):
    """
    Links operational activities to compliance controls.
    This is the core table that enables "SOC operations = compliance evidence".
    """
    __tablename__ = "control_evidence_links"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Control identification
    control_framework = Column(SQLEnum(ControlFramework), nullable=False)
    control_id = Column(String(50), nullable=False)  # e.g., "A.5.24", "DORA-P2-01"
    control_name = Column(String(255), nullable=True)

    # Activity identification
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    activity_id = Column(String(36), nullable=False)
    activity_title = Column(String(255), nullable=True)  # Cached for display
    activity_date = Column(DateTime, nullable=True)  # When the activity occurred

    # Link metadata
    link_type = Column(SQLEnum(LinkType), nullable=False, default=LinkType.AUTOMATIC)
    evidence_strength = Column(SQLEnum(EvidenceStrength), nullable=False, default=EvidenceStrength.MODERATE)

    # Additional context
    notes = Column(Text, nullable=True)
    metrics_snapshot = Column(JSON, nullable=True)  # Relevant metrics at time of linking

    # Timestamps
    linked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    linked_by = Column(String(36), nullable=True)  # User ID if manual

    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_evidence_links_tenant_framework', 'tenant_id', 'control_framework'),
        Index('ix_evidence_links_tenant_control', 'tenant_id', 'control_framework', 'control_id'),
        Index('ix_evidence_links_activity', 'activity_type', 'activity_id'),
        Index('ix_evidence_links_date', 'tenant_id', 'activity_date'),
    )

    def __repr__(self):
        return f"<ControlEvidenceLink {self.control_framework}:{self.control_id} ← {self.activity_type}:{self.activity_id}>"


class ControlEffectiveness(Base):
    """
    Stores calculated effectiveness scores for controls based on linked evidence.
    Updated periodically or on-demand when evidence changes.
    """
    __tablename__ = "control_effectiveness"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Control identification
    control_framework = Column(SQLEnum(ControlFramework), nullable=False)
    control_id = Column(String(50), nullable=False)
    control_name = Column(String(255), nullable=True)
    control_description = Column(Text, nullable=True)

    # Effectiveness metrics
    effectiveness_score = Column(Float, nullable=False, default=0.0)  # 0-100
    effectiveness_level = Column(SQLEnum(EffectivenessLevel), nullable=False, default=EffectivenessLevel.NOT_ASSESSED)

    # Evidence summary
    total_evidence_count = Column(Integer, nullable=False, default=0)
    strong_evidence_count = Column(Integer, nullable=False, default=0)
    moderate_evidence_count = Column(Integer, nullable=False, default=0)
    weak_evidence_count = Column(Integer, nullable=False, default=0)

    # Activity breakdown
    evidence_by_type = Column(JSON, nullable=True)  # {"incident": 47, "alert": 120, ...}

    # Operational metrics (calculated from linked activities)
    operational_metrics = Column(JSON, nullable=True)
    # Example: {
    #   "avg_response_time_hours": 2.3,
    #   "resolution_rate": 0.94,
    #   "incidents_last_30_days": 12,
    #   "trend": "improving"
    # }

    # Time range for calculation
    calculation_period_start = Column(DateTime, nullable=True)
    calculation_period_end = Column(DateTime, nullable=True)

    # Last activity info
    last_activity_date = Column(DateTime, nullable=True)
    last_activity_type = Column(SQLEnum(ActivityType), nullable=True)
    last_activity_id = Column(String(36), nullable=True)

    # Calculation metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    calculation_method = Column(String(50), default="weighted_average")

    # Compliance status
    meets_baseline = Column(Boolean, default=False)  # Does it meet minimum requirements?
    gaps_identified = Column(JSON, nullable=True)  # List of gaps/issues

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('ix_effectiveness_tenant_framework', 'tenant_id', 'control_framework'),
        Index('ix_effectiveness_tenant_control', 'tenant_id', 'control_framework', 'control_id', unique=True),
        Index('ix_effectiveness_score', 'tenant_id', 'effectiveness_score'),
    )

    def __repr__(self):
        return f"<ControlEffectiveness {self.control_framework}:{self.control_id} = {self.effectiveness_score}%>"


class EvidenceLinkingRule(Base):
    """
    Custom rules for evidence linking (tenant-specific overrides).
    Allows organizations to define their own activity-to-control mappings.
    """
    __tablename__ = "evidence_linking_rules"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Rule identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Matching criteria
    control_framework = Column(SQLEnum(ControlFramework), nullable=False)
    control_id = Column(String(50), nullable=False)
    activity_type = Column(SQLEnum(ActivityType), nullable=False)

    # Optional filters
    activity_filters = Column(JSON, nullable=True)
    # Example: {"severity": ["critical", "high"], "status": "resolved"}

    # Evidence configuration
    evidence_strength = Column(SQLEnum(EvidenceStrength), nullable=False, default=EvidenceStrength.MODERATE)
    auto_link = Column(Boolean, default=True)  # Automatically link or just suggest?

    # Metrics to capture
    metrics_to_capture = Column(JSON, nullable=True)
    # Example: ["response_time", "resolution_time", "affected_systems"]

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<EvidenceLinkingRule {self.name}: {self.activity_type} → {self.control_id}>"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_controls_for_activity(activity_type: ActivityType, framework: ControlFramework = None) -> List[Dict[str, Any]]:
    """
    Get all controls that should be linked when an activity of this type occurs.

    Args:
        activity_type: The type of activity (incident, alert, etc.)
        framework: Optional filter by framework

    Returns:
        List of control mappings with control_id, strength, and metrics
    """
    results = []

    frameworks_to_check = [framework] if framework else list(ControlFramework)

    for fw in frameworks_to_check:
        fw_value = fw.value if isinstance(fw, ControlFramework) else fw
        if fw_value not in CONTROL_ACTIVITY_MAPPING:
            continue

        for control_id, mapping in CONTROL_ACTIVITY_MAPPING[fw_value].items():
            if activity_type in mapping["activities"]:
                results.append({
                    "framework": fw_value,
                    "control_id": control_id,
                    "strength": mapping["strength"],
                    "metrics": mapping["metrics"],
                })

    return results


def calculate_effectiveness_level(score: float) -> EffectivenessLevel:
    """Convert numeric score to effectiveness level."""
    if score <= 0:
        return EffectivenessLevel.NOT_ASSESSED
    elif score <= 25:
        return EffectivenessLevel.INEFFECTIVE
    elif score <= 50:
        return EffectivenessLevel.PARTIALLY_EFFECTIVE
    elif score <= 75:
        return EffectivenessLevel.LARGELY_EFFECTIVE
    else:
        return EffectivenessLevel.FULLY_EFFECTIVE


def get_effectiveness_color(level: EffectivenessLevel) -> str:
    """Get display color for effectiveness level."""
    colors = {
        EffectivenessLevel.NOT_ASSESSED: "gray",
        EffectivenessLevel.INEFFECTIVE: "red",
        EffectivenessLevel.PARTIALLY_EFFECTIVE: "orange",
        EffectivenessLevel.LARGELY_EFFECTIVE: "yellow",
        EffectivenessLevel.FULLY_EFFECTIVE: "green",
    }
    return colors.get(level, "gray")
