"""
Cross-Framework Mapping Module for ISORA.

Provides mappings between compliance frameworks:
- BSI IT-Grundschutz <-> NIST CSF 2.0 <-> ISO 27001 <-> OWASP Top 10
- Unified control view across frameworks
- Gap analysis with cross-framework impact

Based on official mapping documents:
- BSI IT-Grundschutz Kreuzreferenztabelle
- NIST CSF to ISO 27001 mapping
- OWASP to CWE to NIST mappings
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum


class FrameworkType(str, Enum):
    """Supported framework types."""
    BSI = "bsi_grundschutz"
    NIST_CSF = "nist_csf_2"
    NIST_800_53 = "nist_800_53"
    ISO_27001 = "iso_27001"
    ISO_27035 = "iso_27035"
    OWASP = "owasp_top_10"
    MITRE = "mitre_attack"


@dataclass
class ControlMapping:
    """Represents a mapping between controls across frameworks."""
    primary_framework: FrameworkType
    primary_control_id: str
    primary_control_name: str
    mapped_controls: Dict[FrameworkType, List[Dict[str, str]]] = field(default_factory=dict)
    ir_phases: List[str] = field(default_factory=list)
    description: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class UnifiedControl:
    """A unified control that spans multiple frameworks."""
    unified_id: str
    name: str
    description: str
    category: str
    ir_phases: List[str]
    framework_controls: Dict[FrameworkType, List[str]]
    implementation_guidance: str = ""
    evidence_requirements: List[str] = field(default_factory=list)


class CrossFrameworkMapper:
    """
    Maps controls across BSI, NIST, ISO, and OWASP frameworks.

    Provides:
    - Bidirectional control mappings
    - Unified control view
    - Cross-framework gap analysis
    - Compliance coverage calculation
    """

    def __init__(self):
        self._mappings = self._load_mappings()
        self._unified_controls = self._create_unified_controls()
        self._phase_mappings = self._load_phase_mappings()

    def _load_mappings(self) -> Dict[str, ControlMapping]:
        """
        Load cross-framework control mappings.

        Based on:
        - BSI IT-Grundschutz Kreuzreferenztabelle
        - NIST CSF to ISO 27001 mapping
        - OWASP to NIST SP 800-53 mapping
        """
        mappings = {}

        # =================================================================
        # INCIDENT DETECTION & MONITORING CONTROLS
        # =================================================================

        mappings["DETECT-01"] = ControlMapping(
            primary_framework=FrameworkType.NIST_CSF,
            primary_control_id="DE.CM",
            primary_control_name="Continuous Monitoring",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.1.A1", "name": "Erstellung einer Sicherheitsrichtlinie für die Detektion"},
                    {"id": "DER.1.A3", "name": "Festlegung von Meldewegen"},
                    {"id": "DER.1.A4", "name": "Sensibilisierung der Mitarbeiter"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "SI-4", "name": "System Monitoring"},
                    {"id": "AU-6", "name": "Audit Record Review"},
                    {"id": "IR-4", "name": "Incident Handling"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.8.15", "name": "Logging"},
                    {"id": "A.8.16", "name": "Monitoring activities"},
                ],
                FrameworkType.OWASP: [
                    {"id": "A09:2021", "name": "Security Logging and Monitoring Failures"},
                ],
            },
            ir_phases=["detection"],
            description="Continuous monitoring of systems and networks for security events",
            keywords=["monitoring", "logging", "detection", "SIEM", "alerts"],
        )

        mappings["DETECT-02"] = ControlMapping(
            primary_framework=FrameworkType.BSI,
            primary_control_id="DER.1.A5",
            primary_control_name="Einsatz von mitgelieferten Systemfunktionen zur Detektion",
            mapped_controls={
                FrameworkType.NIST_CSF: [
                    {"id": "DE.CM-1", "name": "Network monitoring"},
                    {"id": "DE.CM-3", "name": "Personnel activity monitoring"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "AU-2", "name": "Event Logging"},
                    {"id": "AU-3", "name": "Content of Audit Records"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.8.15", "name": "Logging"},
                ],
                FrameworkType.OWASP: [
                    {"id": "A09:2021", "name": "Security Logging and Monitoring Failures"},
                ],
            },
            ir_phases=["detection"],
            description="Use of built-in system logging and detection capabilities",
            keywords=["logging", "audit", "system logs", "event logs"],
        )

        # =================================================================
        # INCIDENT ANALYSIS & INVESTIGATION
        # =================================================================

        mappings["ANALYZE-01"] = ControlMapping(
            primary_framework=FrameworkType.BSI,
            primary_control_id="DER.2.1.A1",
            primary_control_name="Definition eines Sicherheitsvorfalls",
            mapped_controls={
                FrameworkType.NIST_CSF: [
                    {"id": "RS.AN-1", "name": "Investigation notifications"},
                    {"id": "RS.AN-2", "name": "Incident impact analysis"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-4", "name": "Incident Handling"},
                    {"id": "IR-5", "name": "Incident Monitoring"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.24", "name": "Information security incident management planning"},
                    {"id": "A.5.25", "name": "Assessment and decision on events"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "5.2", "name": "Detection and reporting"},
                    {"id": "5.3", "name": "Assessment and decision"},
                ],
            },
            ir_phases=["analysis"],
            description="Classification and initial assessment of security incidents",
            keywords=["classification", "triage", "assessment", "severity"],
        )

        mappings["ANALYZE-02"] = ControlMapping(
            primary_framework=FrameworkType.NIST_CSF,
            primary_control_id="RS.AN-3",
            primary_control_name="Forensics are performed",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.2.1.A4", "name": "Behebung von Sicherheitsvorfällen"},
                    {"id": "DER.2.2.A1", "name": "Prüfung rechtlicher und regulatorischer Rahmenbedingungen"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-4(1)", "name": "Automated Incident Handling"},
                    {"id": "AU-9", "name": "Protection of Audit Information"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.28", "name": "Collection of evidence"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "6.2", "name": "Evidence collection"},
                ],
            },
            ir_phases=["analysis"],
            description="Digital forensics and evidence collection procedures",
            keywords=["forensics", "evidence", "chain of custody", "memory dump"],
        )

        # =================================================================
        # CONTAINMENT CONTROLS
        # =================================================================

        mappings["CONTAIN-01"] = ControlMapping(
            primary_framework=FrameworkType.NIST_CSF,
            primary_control_id="RS.MI-1",
            primary_control_name="Incidents are contained",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.2.1.A3", "name": "Festlegung von Verantwortlichkeiten"},
                    {"id": "DER.2.1.A4", "name": "Behebung von Sicherheitsvorfällen"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-4", "name": "Incident Handling"},
                    {"id": "SC-7", "name": "Boundary Protection"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.26", "name": "Response to information security incidents"},
                    {"id": "A.8.22", "name": "Segregation of networks"},
                ],
                FrameworkType.OWASP: [
                    {"id": "A01:2021", "name": "Broken Access Control"},
                    {"id": "A05:2021", "name": "Security Misconfiguration"},
                ],
            },
            ir_phases=["containment"],
            description="Actions to limit incident spread and impact",
            keywords=["isolation", "quarantine", "network segmentation", "block"],
        )

        mappings["CONTAIN-02"] = ControlMapping(
            primary_framework=FrameworkType.ISO_27001,
            primary_control_id="A.5.26",
            primary_control_name="Response to information security incidents",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.2.1.A4", "name": "Behebung von Sicherheitsvorfällen"},
                    {"id": "DER.2.1.A5", "name": "Externe Unterstützung"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "RS.MI-1", "name": "Incidents are contained"},
                    {"id": "RS.MI-2", "name": "Incidents are mitigated"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-4", "name": "Incident Handling"},
                    {"id": "IR-6", "name": "Incident Reporting"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "6.1", "name": "Response planning"},
                ],
            },
            ir_phases=["containment", "eradication"],
            description="Coordinated response actions to security incidents",
            keywords=["response", "coordination", "escalation", "CSIRT"],
        )

        # =================================================================
        # ACCESS CONTROL & AUTHENTICATION
        # =================================================================

        mappings["ACCESS-01"] = ControlMapping(
            primary_framework=FrameworkType.OWASP,
            primary_control_id="A01:2021",
            primary_control_name="Broken Access Control",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "ORP.4.A1", "name": "Regelung für Zutritts-, Zugangs- und Zugriffsrechte"},
                    {"id": "ORP.4.A2", "name": "Einweisung aller Mitarbeiter"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "PR.AC-1", "name": "Identities and credentials"},
                    {"id": "PR.AC-4", "name": "Access permissions"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "AC-2", "name": "Account Management"},
                    {"id": "AC-3", "name": "Access Enforcement"},
                    {"id": "AC-6", "name": "Least Privilege"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.15", "name": "Access control"},
                    {"id": "A.5.18", "name": "Access rights"},
                    {"id": "A.8.2", "name": "Privileged access rights"},
                ],
            },
            ir_phases=["containment", "eradication", "recovery"],
            description="Proper access control enforcement to prevent unauthorized access",
            keywords=["access control", "authorization", "RBAC", "privileges", "IDOR"],
        )

        mappings["ACCESS-02"] = ControlMapping(
            primary_framework=FrameworkType.OWASP,
            primary_control_id="A07:2021",
            primary_control_name="Identification and Authentication Failures",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "ORP.4.A8", "name": "Regelung des Passwortgebrauchs"},
                    {"id": "ORP.4.A9", "name": "Identifikation und Authentisierung"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "PR.AC-1", "name": "Identities and credentials"},
                    {"id": "PR.AC-7", "name": "Authentication"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IA-2", "name": "Identification and Authentication"},
                    {"id": "IA-5", "name": "Authenticator Management"},
                    {"id": "IA-11", "name": "Re-authentication"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.16", "name": "Identity management"},
                    {"id": "A.5.17", "name": "Authentication information"},
                    {"id": "A.8.5", "name": "Secure authentication"},
                ],
            },
            ir_phases=["containment", "eradication"],
            description="Strong authentication and identity management",
            keywords=["authentication", "MFA", "passwords", "session", "brute force"],
        )

        # =================================================================
        # CRYPTOGRAPHY & DATA PROTECTION
        # =================================================================

        mappings["CRYPTO-01"] = ControlMapping(
            primary_framework=FrameworkType.OWASP,
            primary_control_id="A02:2021",
            primary_control_name="Cryptographic Failures",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "CON.1.A1", "name": "Auswahl geeigneter kryptographischer Verfahren"},
                    {"id": "CON.1.A2", "name": "Datensicherung bei Einsatz kryptographischer Verfahren"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "PR.DS-1", "name": "Data-at-rest protection"},
                    {"id": "PR.DS-2", "name": "Data-in-transit protection"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "SC-8", "name": "Transmission Confidentiality"},
                    {"id": "SC-12", "name": "Cryptographic Key Management"},
                    {"id": "SC-13", "name": "Cryptographic Protection"},
                    {"id": "SC-28", "name": "Protection of Information at Rest"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.8.24", "name": "Use of cryptography"},
                ],
            },
            ir_phases=["analysis", "eradication", "recovery"],
            description="Proper use of cryptography to protect data",
            keywords=["encryption", "TLS", "hashing", "keys", "certificates"],
        )

        # =================================================================
        # INJECTION & INPUT VALIDATION
        # =================================================================

        mappings["INJECT-01"] = ControlMapping(
            primary_framework=FrameworkType.OWASP,
            primary_control_id="A03:2021",
            primary_control_name="Injection",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "APP.3.1.A1", "name": "Authentisierung bei Webanwendungen"},
                    {"id": "APP.3.1.A4", "name": "Kontrolliertes Einbinden von Dateien und Inhalten"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "PR.DS-5", "name": "Protections against data leaks"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "SI-10", "name": "Information Input Validation"},
                    {"id": "SI-11", "name": "Error Handling"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.8.26", "name": "Application security requirements"},
                    {"id": "A.8.28", "name": "Secure coding"},
                ],
            },
            ir_phases=["analysis", "eradication"],
            description="Protection against injection attacks (SQL, XSS, Command)",
            keywords=["SQL injection", "XSS", "command injection", "input validation"],
        )

        # =================================================================
        # VULNERABILITY MANAGEMENT
        # =================================================================

        mappings["VULN-01"] = ControlMapping(
            primary_framework=FrameworkType.OWASP,
            primary_control_id="A06:2021",
            primary_control_name="Vulnerable and Outdated Components",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "OPS.1.1.3.A1", "name": "Konzept für das Patch- und Änderungsmanagement"},
                    {"id": "OPS.1.1.3.A2", "name": "Festlegung der Verantwortlichkeiten"},
                ],
                FrameworkType.NIST_CSF: [
                    {"id": "ID.RA-1", "name": "Asset vulnerabilities identified"},
                    {"id": "PR.IP-12", "name": "Vulnerability management plan"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "RA-5", "name": "Vulnerability Monitoring and Scanning"},
                    {"id": "SI-2", "name": "Flaw Remediation"},
                    {"id": "CM-8", "name": "System Component Inventory"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.8.8", "name": "Management of technical vulnerabilities"},
                    {"id": "A.8.19", "name": "Installation of software"},
                ],
            },
            ir_phases=["analysis", "eradication", "recovery"],
            description="Identification and patching of vulnerable components",
            keywords=["patching", "CVE", "vulnerability", "outdated", "dependencies"],
        )

        # =================================================================
        # RECOVERY & BUSINESS CONTINUITY
        # =================================================================

        mappings["RECOVER-01"] = ControlMapping(
            primary_framework=FrameworkType.NIST_CSF,
            primary_control_id="RC.RP-1",
            primary_control_name="Recovery plan is executed",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.4.A1", "name": "Erstellung eines Notfallhandbuchs"},
                    {"id": "DER.4.A2", "name": "Integration in Sicherheitskonzept"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "CP-2", "name": "Contingency Plan"},
                    {"id": "CP-10", "name": "System Recovery and Reconstitution"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.29", "name": "ICT readiness for business continuity"},
                    {"id": "A.5.30", "name": "ICT for business continuity"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "7.1", "name": "Eradication and recovery"},
                ],
            },
            ir_phases=["recovery"],
            description="Execution of recovery procedures to restore systems",
            keywords=["recovery", "backup", "restore", "continuity", "RTO", "RPO"],
        )

        # =================================================================
        # POST-INCIDENT & LESSONS LEARNED
        # =================================================================

        mappings["POST-01"] = ControlMapping(
            primary_framework=FrameworkType.NIST_CSF,
            primary_control_id="RC.IM-1",
            primary_control_name="Recovery plans incorporate lessons learned",
            mapped_controls={
                FrameworkType.BSI: [
                    {"id": "DER.2.1.A6", "name": "Nachbereitung von Sicherheitsvorfällen"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-4(4)", "name": "Information Correlation"},
                    {"id": "IR-8", "name": "Incident Response Plan"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.27", "name": "Learning from information security incidents"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "8.1", "name": "Lessons learned"},
                    {"id": "8.2", "name": "Improvements"},
                ],
            },
            ir_phases=["post_incident"],
            description="Post-incident review and improvement of response procedures",
            keywords=["lessons learned", "post-mortem", "improvement", "review"],
        )

        # =================================================================
        # REGULATORY REPORTING
        # =================================================================

        mappings["REPORT-01"] = ControlMapping(
            primary_framework=FrameworkType.BSI,
            primary_control_id="DER.2.1.A7",
            primary_control_name="Meldung von Sicherheitsvorfällen",
            mapped_controls={
                FrameworkType.NIST_CSF: [
                    {"id": "RS.CO-2", "name": "Incidents reported"},
                    {"id": "RS.CO-3", "name": "Information shared"},
                ],
                FrameworkType.NIST_800_53: [
                    {"id": "IR-6", "name": "Incident Reporting"},
                    {"id": "IR-7", "name": "Incident Response Assistance"},
                ],
                FrameworkType.ISO_27001: [
                    {"id": "A.5.5", "name": "Contact with authorities"},
                    {"id": "A.5.24", "name": "Incident management planning"},
                ],
                FrameworkType.ISO_27035: [
                    {"id": "5.4", "name": "Reporting"},
                ],
            },
            ir_phases=["detection", "analysis", "post_incident"],
            description="Regulatory and stakeholder notification requirements",
            keywords=["reporting", "notification", "GDPR", "BSI", "authorities"],
        )

        return mappings

    def _create_unified_controls(self) -> Dict[str, UnifiedControl]:
        """Create unified controls from mappings."""
        unified = {}

        # Group mappings by category
        categories = {
            "detection": ["DETECT-01", "DETECT-02"],
            "analysis": ["ANALYZE-01", "ANALYZE-02"],
            "containment": ["CONTAIN-01", "CONTAIN-02"],
            "access_control": ["ACCESS-01", "ACCESS-02"],
            "cryptography": ["CRYPTO-01"],
            "injection": ["INJECT-01"],
            "vulnerability": ["VULN-01"],
            "recovery": ["RECOVER-01"],
            "post_incident": ["POST-01"],
            "reporting": ["REPORT-01"],
        }

        for category, mapping_ids in categories.items():
            for mapping_id in mapping_ids:
                mapping = self._mappings.get(mapping_id)
                if not mapping:
                    continue

                # Collect all framework controls
                framework_controls = {mapping.primary_framework: [mapping.primary_control_id]}
                for fw, controls in mapping.mapped_controls.items():
                    framework_controls[fw] = [c["id"] for c in controls]

                unified[mapping_id] = UnifiedControl(
                    unified_id=mapping_id,
                    name=mapping.primary_control_name,
                    description=mapping.description,
                    category=category,
                    ir_phases=mapping.ir_phases,
                    framework_controls=framework_controls,
                    evidence_requirements=self._get_evidence_requirements(category),
                )

        return unified

    def _get_evidence_requirements(self, category: str) -> List[str]:
        """Get evidence requirements for a control category."""
        requirements = {
            "detection": [
                "SIEM alerts or logs",
                "Detection timestamp",
                "Initial indicator of compromise",
            ],
            "analysis": [
                "Forensic images",
                "Memory dumps",
                "Log analysis reports",
                "Malware samples (hashed)",
            ],
            "containment": [
                "Network isolation logs",
                "Firewall rule changes",
                "Account lockout records",
            ],
            "access_control": [
                "Access control configurations",
                "User account audit",
                "Permission changes",
            ],
            "cryptography": [
                "Encryption configuration",
                "Key management procedures",
                "TLS certificate status",
            ],
            "injection": [
                "WAF logs",
                "Input validation tests",
                "Code review findings",
            ],
            "vulnerability": [
                "Vulnerability scan results",
                "Patch records",
                "Software inventory",
            ],
            "recovery": [
                "Backup verification",
                "System restore logs",
                "Service restoration timestamps",
            ],
            "post_incident": [
                "Post-mortem report",
                "Lessons learned document",
                "Improvement action items",
            ],
            "reporting": [
                "Regulatory notification records",
                "Stakeholder communications",
                "Incident report copies",
            ],
        }
        return requirements.get(category, [])

    def _load_phase_mappings(self) -> Dict[str, List[str]]:
        """Map IR phases to relevant unified controls."""
        return {
            "detection": ["DETECT-01", "DETECT-02", "REPORT-01"],
            "analysis": ["ANALYZE-01", "ANALYZE-02", "INJECT-01", "VULN-01"],
            "containment": ["CONTAIN-01", "CONTAIN-02", "ACCESS-01", "ACCESS-02"],
            "eradication": ["ACCESS-01", "ACCESS-02", "CRYPTO-01", "INJECT-01", "VULN-01"],
            "recovery": ["RECOVER-01", "CRYPTO-01", "VULN-01"],
            "post_incident": ["POST-01", "REPORT-01"],
        }

    def get_mapping(self, mapping_id: str) -> Optional[ControlMapping]:
        """Get a specific control mapping."""
        return self._mappings.get(mapping_id)

    def get_all_mappings(self) -> List[ControlMapping]:
        """Get all control mappings."""
        return list(self._mappings.values())

    def get_unified_control(self, unified_id: str) -> Optional[UnifiedControl]:
        """Get a unified control by ID."""
        return self._unified_controls.get(unified_id)

    def get_all_unified_controls(self) -> List[UnifiedControl]:
        """Get all unified controls."""
        return list(self._unified_controls.values())

    def get_controls_for_phase(self, phase: str) -> List[UnifiedControl]:
        """Get unified controls relevant to an IR phase."""
        control_ids = self._phase_mappings.get(phase, [])
        return [self._unified_controls[cid] for cid in control_ids if cid in self._unified_controls]

    def find_equivalent_controls(
        self,
        control_id: str,
        source_framework: FrameworkType,
    ) -> Dict[FrameworkType, List[Dict[str, str]]]:
        """
        Find equivalent controls in other frameworks.

        Args:
            control_id: Control ID to look up
            source_framework: Framework of the source control

        Returns:
            Dictionary mapping frameworks to equivalent controls
        """
        equivalents = {}

        for mapping in self._mappings.values():
            # Check if source control is the primary
            if (mapping.primary_framework == source_framework and
                mapping.primary_control_id == control_id):
                return mapping.mapped_controls

            # Check if source control is in mapped controls
            if source_framework in mapping.mapped_controls:
                for ctrl in mapping.mapped_controls[source_framework]:
                    if ctrl["id"] == control_id:
                        # Return all other mapped controls plus primary
                        result = {
                            mapping.primary_framework: [{
                                "id": mapping.primary_control_id,
                                "name": mapping.primary_control_name,
                            }]
                        }
                        for fw, ctrls in mapping.mapped_controls.items():
                            if fw != source_framework:
                                result[fw] = ctrls
                        return result

        return equivalents

    def calculate_cross_framework_coverage(
        self,
        completed_controls: Dict[FrameworkType, List[str]],
    ) -> Dict[str, Any]:
        """
        Calculate compliance coverage across all frameworks.

        Args:
            completed_controls: Dict mapping framework to list of completed control IDs

        Returns:
            Coverage statistics and gap analysis
        """
        total_unified = len(self._unified_controls)
        covered_unified = set()
        framework_coverage = {}

        # Track which unified controls are covered
        for unified_id, unified_ctrl in self._unified_controls.items():
            is_covered = False
            for fw, controls in unified_ctrl.framework_controls.items():
                if fw in completed_controls:
                    if any(c in completed_controls[fw] for c in controls):
                        is_covered = True
                        break
            if is_covered:
                covered_unified.add(unified_id)

        # Calculate per-framework coverage
        for fw in FrameworkType:
            total_controls = 0
            covered_controls = 0

            for mapping in self._mappings.values():
                if mapping.primary_framework == fw:
                    total_controls += 1
                    if fw in completed_controls and mapping.primary_control_id in completed_controls[fw]:
                        covered_controls += 1
                elif fw in mapping.mapped_controls:
                    total_controls += len(mapping.mapped_controls[fw])
                    if fw in completed_controls:
                        covered_controls += sum(
                            1 for c in mapping.mapped_controls[fw]
                            if c["id"] in completed_controls[fw]
                        )

            if total_controls > 0:
                framework_coverage[fw.value] = {
                    "total": total_controls,
                    "covered": covered_controls,
                    "percentage": round(covered_controls / total_controls * 100, 1),
                }

        # Identify gaps
        gaps = []
        for unified_id in self._unified_controls:
            if unified_id not in covered_unified:
                ctrl = self._unified_controls[unified_id]
                gaps.append({
                    "unified_id": unified_id,
                    "name": ctrl.name,
                    "category": ctrl.category,
                    "phases": ctrl.ir_phases,
                    "frameworks_affected": [fw.value for fw in ctrl.framework_controls.keys()],
                })

        return {
            "unified_coverage": {
                "total": total_unified,
                "covered": len(covered_unified),
                "percentage": round(len(covered_unified) / total_unified * 100, 1) if total_unified > 0 else 0,
            },
            "framework_coverage": framework_coverage,
            "gaps": gaps,
            "covered_controls": list(covered_unified),
        }

    def get_framework_comparison_matrix(self) -> Dict[str, Any]:
        """
        Generate a comparison matrix showing control equivalence across frameworks.

        Returns:
            Matrix data for UI rendering
        """
        matrix = []

        for unified_id, unified_ctrl in self._unified_controls.items():
            row = {
                "unified_id": unified_id,
                "name": unified_ctrl.name,
                "category": unified_ctrl.category,
                "phases": unified_ctrl.ir_phases,
            }

            for fw in [FrameworkType.BSI, FrameworkType.NIST_CSF, FrameworkType.NIST_800_53,
                       FrameworkType.ISO_27001, FrameworkType.OWASP]:
                controls = unified_ctrl.framework_controls.get(fw, [])
                row[fw.value] = controls if controls else ["-"]

            matrix.append(row)

        return {
            "headers": ["BSI", "NIST CSF", "NIST 800-53", "ISO 27001", "OWASP"],
            "rows": matrix,
        }

    def get_control_details(
        self,
        control_id: str,
        framework: FrameworkType,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a control including all cross-references.

        Args:
            control_id: Control ID
            framework: Framework of the control

        Returns:
            Detailed control information with all mappings
        """
        equivalents = self.find_equivalent_controls(control_id, framework)

        # Find the mapping this control belongs to
        for mapping_id, mapping in self._mappings.items():
            found = False
            if mapping.primary_framework == framework and mapping.primary_control_id == control_id:
                found = True
            elif framework in mapping.mapped_controls:
                for ctrl in mapping.mapped_controls[framework]:
                    if ctrl["id"] == control_id:
                        found = True
                        break

            if found:
                unified = self._unified_controls.get(mapping_id)
                return {
                    "control_id": control_id,
                    "framework": framework.value,
                    "unified_id": mapping_id,
                    "name": mapping.primary_control_name,
                    "description": mapping.description,
                    "ir_phases": mapping.ir_phases,
                    "keywords": mapping.keywords,
                    "equivalent_controls": {fw.value: ctrls for fw, ctrls in equivalents.items()},
                    "evidence_requirements": unified.evidence_requirements if unified else [],
                }

        return {"control_id": control_id, "framework": framework.value, "error": "Not found"}

    def export_mapping_table(self, format: str = "markdown") -> str:
        """
        Export the complete cross-framework mapping table.

        Args:
            format: Output format ("markdown" or "csv")

        Returns:
            Formatted mapping table
        """
        if format == "csv":
            lines = ["Unified ID,Category,BSI,NIST CSF,NIST 800-53,ISO 27001,OWASP"]
            for uid, ctrl in self._unified_controls.items():
                bsi = ";".join(ctrl.framework_controls.get(FrameworkType.BSI, ["-"]))
                nist_csf = ";".join(ctrl.framework_controls.get(FrameworkType.NIST_CSF, ["-"]))
                nist_53 = ";".join(ctrl.framework_controls.get(FrameworkType.NIST_800_53, ["-"]))
                iso = ";".join(ctrl.framework_controls.get(FrameworkType.ISO_27001, ["-"]))
                owasp = ";".join(ctrl.framework_controls.get(FrameworkType.OWASP, ["-"]))
                lines.append(f"{uid},{ctrl.category},{bsi},{nist_csf},{nist_53},{iso},{owasp}")
            return "\n".join(lines)

        # Markdown format
        lines = [
            "# Cross-Framework Control Mapping",
            "",
            "| ID | Category | BSI | NIST CSF | NIST 800-53 | ISO 27001 | OWASP |",
            "|---|---|---|---|---|---|---|",
        ]

        for uid, ctrl in self._unified_controls.items():
            bsi = ", ".join(ctrl.framework_controls.get(FrameworkType.BSI, ["-"]))
            nist_csf = ", ".join(ctrl.framework_controls.get(FrameworkType.NIST_CSF, ["-"]))
            nist_53 = ", ".join(ctrl.framework_controls.get(FrameworkType.NIST_800_53, ["-"]))
            iso = ", ".join(ctrl.framework_controls.get(FrameworkType.ISO_27001, ["-"]))
            owasp = ", ".join(ctrl.framework_controls.get(FrameworkType.OWASP, ["-"]))
            lines.append(f"| {uid} | {ctrl.category} | {bsi} | {nist_csf} | {nist_53} | {iso} | {owasp} |")

        return "\n".join(lines)
