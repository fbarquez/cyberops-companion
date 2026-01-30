"""
Data models for compliance and threat intelligence integrations.

These models are used across all compliance framework integrations:
- BSI IT-Grundschutz
- NIST CSF 2.0, SP 800-53
- ISO 27001:2022, ISO 27035
- MITRE ATT&CK
- OWASP Top 10
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Status of a compliance check."""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUATED = "not_evaluated"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    BSI_GRUNDSCHUTZ = "bsi_grundschutz"
    BSI_GRUNDSCHUTZ_PLUS = "bsi_grundschutz_plus"
    NIST_CSF_2 = "nist_csf_2"
    NIST_800_53 = "nist_800_53"
    NIST_800_61 = "nist_800_61"
    ISO_27001 = "iso_27001"
    ISO_27035 = "iso_27035"
    MITRE_ATTACK = "mitre_attack"
    OWASP_TOP_10 = "owasp_top_10"
    NIS2 = "nis2"


class ComplianceControl(BaseModel):
    """A single compliance control from any framework."""

    framework: ComplianceFramework
    control_id: str
    control_name: str
    control_family: Optional[str] = None
    description: Optional[str] = None
    guidance: Optional[str] = None

    # For OSCAL-based controls
    oscal_id: Optional[str] = None
    oscal_class: Optional[str] = None


class ComplianceCheck(BaseModel):
    """Result of evaluating a compliance control."""

    framework: ComplianceFramework
    control_id: str
    control_name: str
    status: ComplianceStatus = ComplianceStatus.NOT_EVALUATED

    # Evidence and documentation
    evidence_required: List[str] = Field(default_factory=list)
    evidence_provided: List[str] = Field(default_factory=list)
    evidence_found: bool = False

    # Gaps and recommendations
    gap_description: Optional[str] = None
    recommendation: Optional[str] = None
    remediation_priority: Optional[str] = None  # high, medium, low

    # Metadata
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checked_by: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_by: Optional[str] = None
    notes: Optional[str] = None

    def is_compliant(self) -> bool:
        """Check if this control is compliant."""
        return self.status == ComplianceStatus.COMPLIANT


class PhaseComplianceMapping(BaseModel):
    """Mapping of IR phase to compliance controls."""

    phase: str
    framework: ComplianceFramework
    controls: List[str]  # Control IDs
    mandatory_controls: List[str] = Field(default_factory=list)
    documentation_required: List[str] = Field(default_factory=list)


class ComplianceReport(BaseModel):
    """Full compliance report for an incident."""

    incident_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: Optional[str] = None

    # Frameworks evaluated
    frameworks_evaluated: List[ComplianceFramework] = Field(default_factory=list)

    # Results by framework
    results: Dict[str, List[ComplianceCheck]] = Field(default_factory=dict)

    # Summary statistics
    total_controls: int = 0
    compliant_count: int = 0
    partial_count: int = 0
    gap_count: int = 0

    # Overall compliance score (percentage)
    compliance_score: float = 0.0

    # Critical gaps requiring immediate attention
    critical_gaps: List[ComplianceCheck] = Field(default_factory=list)

    def calculate_statistics(self) -> None:
        """Calculate summary statistics from results."""
        self.total_controls = 0
        self.compliant_count = 0
        self.partial_count = 0
        self.gap_count = 0
        self.critical_gaps = []

        for framework_checks in self.results.values():
            for check in framework_checks:
                self.total_controls += 1
                if check.status == ComplianceStatus.COMPLIANT:
                    self.compliant_count += 1
                elif check.status == ComplianceStatus.PARTIAL:
                    self.partial_count += 1
                elif check.status == ComplianceStatus.GAP:
                    self.gap_count += 1
                    if check.remediation_priority == "high":
                        self.critical_gaps.append(check)

        if self.total_controls > 0:
            self.compliance_score = (
                (self.compliant_count + (self.partial_count * 0.5))
                / self.total_controls * 100
            )


# Threat Intelligence Models

class CVSSScore(BaseModel):
    """CVSS score information."""

    version: str  # "3.1", "3.0", "2.0"
    vector_string: Optional[str] = None
    base_score: float
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, NONE
    exploitability_score: Optional[float] = None
    impact_score: Optional[float] = None


class CVEInfo(BaseModel):
    """CVE information from NVD."""

    cve_id: str  # CVE-2024-XXXXX
    source_identifier: Optional[str] = None

    # Description
    description: str

    # Dates
    published: datetime
    last_modified: datetime

    # CVSS Scores
    cvss_v3: Optional[CVSSScore] = None
    cvss_v2: Optional[CVSSScore] = None

    # Status
    vuln_status: str  # Analyzed, Modified, Awaiting Analysis, etc.

    # CISA KEV (Known Exploited Vulnerabilities)
    cisa_kev: bool = False
    cisa_action_due: Optional[datetime] = None
    cisa_required_action: Optional[str] = None

    # References
    references: List[str] = Field(default_factory=list)

    # CPE (affected products)
    affected_products: List[str] = Field(default_factory=list)

    # Weaknesses (CWE)
    weaknesses: List[str] = Field(default_factory=list)

    def is_critical(self) -> bool:
        """Check if CVE is critical severity."""
        if self.cvss_v3:
            return self.cvss_v3.severity == "CRITICAL"
        return False

    def is_actively_exploited(self) -> bool:
        """Check if CVE is in CISA KEV."""
        return self.cisa_kev


class ATTACKTechnique(BaseModel):
    """MITRE ATT&CK technique information."""

    technique_id: str  # T1486
    name: str
    description: Optional[str] = None

    # Tactic (kill chain phase)
    tactics: List[str] = Field(default_factory=list)  # e.g., ["impact"]

    # Sub-techniques
    is_subtechnique: bool = False
    parent_technique: Optional[str] = None
    subtechniques: List[str] = Field(default_factory=list)

    # Platform
    platforms: List[str] = Field(default_factory=list)  # Windows, Linux, macOS

    # Data sources for detection
    data_sources: List[str] = Field(default_factory=list)

    # Mitigations
    mitigations: List[Dict[str, str]] = Field(default_factory=list)

    # Detection guidance
    detection: Optional[str] = None

    # ATT&CK URL
    url: Optional[str] = None

    # Relevance to current incident (computed)
    relevance_score: float = 0.0
    relevance_indicators: List[str] = Field(default_factory=list)


class ThreatIntelligence(BaseModel):
    """Aggregated threat intelligence for an incident."""

    incident_id: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # CVE Information
    related_cves: List[CVEInfo] = Field(default_factory=list)
    critical_cves: List[str] = Field(default_factory=list)  # CVE IDs
    actively_exploited_cves: List[str] = Field(default_factory=list)

    # MITRE ATT&CK
    mapped_techniques: List[ATTACKTechnique] = Field(default_factory=list)
    primary_tactics: List[str] = Field(default_factory=list)
    recommended_mitigations: List[Dict[str, str]] = Field(default_factory=list)

    # Ransomware specific
    ransomware_family: Optional[str] = None
    known_iocs: List[Dict[str, str]] = Field(default_factory=list)  # type, value

    # Recommendations
    detection_recommendations: List[str] = Field(default_factory=list)
    mitigation_recommendations: List[str] = Field(default_factory=list)


# OSCAL-specific models

class OSCALCatalog(BaseModel):
    """OSCAL Catalog representation (simplified)."""

    uuid: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    groups: List[Dict[str, Any]] = Field(default_factory=list)
    controls: List[Dict[str, Any]] = Field(default_factory=list)


class OSCALProfile(BaseModel):
    """OSCAL Profile representation (simplified)."""

    uuid: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    imports: List[Dict[str, Any]] = Field(default_factory=list)
    modify: Optional[Dict[str, Any]] = None


# API Response Models

class FrameworkInfo(BaseModel):
    """Framework information for API responses."""
    id: str
    name: str
    description: str
    version: str
    controls_count: int
    organization: Optional[str] = None
    url: Optional[str] = None


class ComplianceValidationResult(BaseModel):
    """Result of compliance validation."""
    framework: str
    compliant: bool
    score: float
    total_controls: int
    compliant_count: int
    partial_count: int
    gap_count: int
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CrossFrameworkMapping(BaseModel):
    """Cross-framework control mapping."""
    unified_id: str
    name: str
    category: str
    ir_phases: List[str]
    framework_controls: Dict[str, List[str]]
    evidence_requirements: List[str] = Field(default_factory=list)
