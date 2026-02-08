"""
Compliance Hub - Central integration point for regulatory compliance and threat intelligence.

Orchestrates integrations with:
- BSI IT-Grundschutz (Germany)
- NIST CSF 2.0, SP 800-53, SP 800-61r3, NVD
- ISO 27001:2022, ISO 27035
- MITRE ATT&CK
- OWASP Top 10, Cheat Sheet Series

Features:
- Unified compliance validation across multiple frameworks
- Threat intelligence enrichment
- Compliance reporting and export
- Phase-based compliance checking
- Web application security guidance (OWASP)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.integrations.models import (
    ComplianceFramework,
    ComplianceCheck,
    ComplianceStatus,
    ComplianceReport,
    ThreatIntelligence,
    CVEInfo,
    ATTACKTechnique,
)
from src.integrations.bsi_integration import BSIIntegration
from src.integrations.nist_integration import NISTOSCALIntegration, NVDIntegration
from src.integrations.mitre_integration import MITREATTACKIntegration
from src.integrations.iso_mapper import ISOComplianceMapper
from src.integrations.owasp_integration import OWASPIntegration
from src.integrations.cross_framework_mapper import CrossFrameworkMapper, FrameworkType

logger = logging.getLogger(__name__)


class ComplianceHub:
    """
    Central hub for compliance and threat intelligence integrations.

    Provides a unified interface to validate incident response activities
    against multiple regulatory frameworks and enrich incidents with
    threat intelligence.

    Usage:
        hub = ComplianceHub()

        # Validate compliance for a phase
        results = hub.validate_phase_compliance(
            phase="analysis",
            incident_data={...},
            frameworks=[ComplianceFramework.BSI_GRUNDSCHUTZ, ComplianceFramework.ISO_27001]
        )

        # Enrich incident with threat intelligence
        intel = hub.enrich_with_threat_intelligence(
            incident_id="INC-2024-001",
            iocs=[{"type": "ip", "value": "192.168.1.1"}],
            affected_software=["Windows Server 2019"]
        )

        # Generate compliance report
        report = hub.generate_compliance_report(
            incident_id="INC-2024-001",
            all_checks=[...]
        )
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_dir: Optional[Path] = None,
        offline_mode: bool = False,
    ):
        """
        Initialize the Compliance Hub.

        Args:
            config: Configuration dictionary with optional API keys:
                - nvd_api_key: NVD API key for higher rate limits
            cache_dir: Base directory for caching data
            offline_mode: If True, only use cached data (no network requests)
        """
        self.config = config or {}
        self.cache_dir = cache_dir or Path.home() / ".cyberops_companion" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode

        # Initialize integrations
        self._init_integrations()

    def _init_integrations(self) -> None:
        """Initialize all integration modules."""
        # BSI Integration
        self.bsi = BSIIntegration(
            cache_dir=self.cache_dir / "bsi",
            offline_mode=self.offline_mode,
        )

        # NIST Integrations
        self.nist_oscal = NISTOSCALIntegration(
            cache_dir=self.cache_dir / "nist",
            offline_mode=self.offline_mode,
        )
        self.nist_nvd = NVDIntegration(
            api_key=self.config.get("nvd_api_key"),
            cache_dir=self.cache_dir / "nvd",
        )

        # MITRE ATT&CK Integration
        self.mitre = MITREATTACKIntegration(
            cache_dir=self.cache_dir / "mitre",
            offline_mode=self.offline_mode,
        )

        # ISO Mapper (static mappings, no network needed)
        self.iso = ISOComplianceMapper()

        # OWASP Integration (static data, no network needed)
        self.owasp = OWASPIntegration()

        # Cross-Framework Mapper (static mappings)
        self.cross_mapper = CrossFrameworkMapper()

        logger.info("Compliance Hub initialized with all integrations")

    def validate_phase_compliance(
        self,
        phase: str,
        incident_data: Dict[str, Any],
        frameworks: Optional[List[ComplianceFramework]] = None,
        operator: str = "",
    ) -> Dict[str, List[ComplianceCheck]]:
        """
        Validate compliance for an IR phase against multiple frameworks.

        Args:
            phase: IR phase name (detection, analysis, containment, etc.)
            incident_data: Dictionary containing:
                - completed_actions: List of completed checklist item IDs
                - evidence_collected: List of evidence entry descriptions
                - documentation_provided: List of documentation items
            frameworks: List of frameworks to validate (None = all)
            operator: Name of the operator performing validation

        Returns:
            Dictionary mapping framework name to list of ComplianceCheck results
        """
        if frameworks is None:
            frameworks = [
                ComplianceFramework.BSI_GRUNDSCHUTZ,
                ComplianceFramework.NIST_CSF_2,
                ComplianceFramework.ISO_27001,
            ]

        completed_actions = incident_data.get("completed_actions", [])
        evidence_collected = incident_data.get("evidence_collected", [])
        documentation_provided = incident_data.get("documentation_provided", [])

        results: Dict[str, List[ComplianceCheck]] = {}

        for framework in frameworks:
            try:
                checks = self._validate_framework(
                    framework=framework,
                    phase=phase,
                    completed_actions=completed_actions,
                    evidence_collected=evidence_collected,
                    documentation_provided=documentation_provided,
                    operator=operator,
                )
                results[framework.value] = checks
            except Exception as e:
                logger.error(f"Error validating {framework.value}: {e}")
                results[framework.value] = []

        return results

    def _validate_framework(
        self,
        framework: ComplianceFramework,
        phase: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        documentation_provided: List[str],
        operator: str,
    ) -> List[ComplianceCheck]:
        """Validate a single framework."""
        if framework == ComplianceFramework.BSI_GRUNDSCHUTZ:
            return self.bsi.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                operator=operator,
            )

        elif framework == ComplianceFramework.NIST_CSF_2:
            return self.nist_oscal.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                framework="csf",
                operator=operator,
            )

        elif framework == ComplianceFramework.NIST_800_53:
            return self.nist_oscal.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                framework="sp800_53",
                operator=operator,
            )

        elif framework == ComplianceFramework.ISO_27001:
            return self.iso.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                documentation_provided=documentation_provided,
                standard="iso27001",
                operator=operator,
            )

        elif framework == ComplianceFramework.ISO_27035:
            return self.iso.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                documentation_provided=documentation_provided,
                standard="iso27035",
                operator=operator,
            )

        elif framework == ComplianceFramework.OWASP_TOP_10:
            return self._validate_owasp(
                phase=phase,
                evidence_collected=evidence_collected,
                operator=operator,
            )

        else:
            logger.warning(f"Framework {framework} validation not implemented")
            return []

    def _validate_owasp(
        self,
        phase: str,
        evidence_collected: List[str],
        operator: str,
    ) -> List[ComplianceCheck]:
        """Validate against OWASP Top 10."""
        checks = []
        phase_recs = self.owasp.get_phase_recommendations(phase)

        # Identify risks from evidence/indicators
        identified_risks = self.owasp.identify_risks_from_indicators(evidence_collected)

        for risk in self.owasp.get_all_risks():
            is_identified = risk in identified_risks
            phase_relevance = risk.ir_phase_relevance.get(phase, "")

            # Determine status based on whether risk is addressed
            if is_identified:
                # Risk was identified - check if mitigation steps mentioned
                mitigated = any(
                    step.lower() in " ".join(evidence_collected).lower()
                    for step in risk.prevention[:3]
                )
                status = ComplianceStatus.PARTIAL if mitigated else ComplianceStatus.GAP
                priority = "high"
            else:
                status = ComplianceStatus.COMPLIANT
                priority = "low"

            checks.append(ComplianceCheck(
                framework=ComplianceFramework.OWASP_TOP_10,
                control_id=risk.id,
                control_name=risk.name,
                status=status,
                checked_at=datetime.now(timezone.utc),
                checked_by=operator,
                evidence_found=is_identified,
                recommendation=phase_relevance if is_identified else None,
                remediation_priority=priority if is_identified else None,
            ))

        return checks

    def validate_all_phases(
        self,
        incident_data: Dict[str, Any],
        frameworks: Optional[List[ComplianceFramework]] = None,
        operator: str = "",
    ) -> Dict[str, Dict[str, List[ComplianceCheck]]]:
        """
        Validate compliance for all IR phases.

        Args:
            incident_data: Dictionary mapping phase names to phase data
            frameworks: List of frameworks to validate
            operator: Name of the operator

        Returns:
            Nested dictionary: phase -> framework -> checks
        """
        phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
        all_results: Dict[str, Dict[str, List[ComplianceCheck]]] = {}

        for phase in phases:
            phase_data = incident_data.get(phase, {})
            if phase_data:
                all_results[phase] = self.validate_phase_compliance(
                    phase=phase,
                    incident_data=phase_data,
                    frameworks=frameworks,
                    operator=operator,
                )

        return all_results

    def enrich_with_threat_intelligence(
        self,
        incident_id: str,
        iocs: Optional[List[Dict[str, str]]] = None,
        affected_software: Optional[List[str]] = None,
        ransomware_family: Optional[str] = None,
    ) -> ThreatIntelligence:
        """
        Enrich incident with threat intelligence from multiple sources.

        Args:
            incident_id: Incident identifier
            iocs: List of IOCs with "type" and "value" keys
            affected_software: List of affected software names
            ransomware_family: Known ransomware family name

        Returns:
            ThreatIntelligence object with enrichment data
        """
        iocs = iocs or []
        affected_software = affected_software or []

        # Get MITRE ATT&CK threat intelligence
        mitre_intel = self.mitre.generate_threat_intelligence(
            incident_id=incident_id,
            iocs=iocs,
            ransomware_family=ransomware_family,
        )

        # Enrich with NVD CVE data (if not offline)
        if not self.offline_mode and affected_software:
            try:
                cve_enrichment = self.nist_nvd.enrich_incident_with_cves(
                    affected_software=affected_software,
                    ransomware_family=ransomware_family,
                )

                # Add CVE info to threat intelligence
                for software, cve_data in cve_enrichment.get("software_cves", {}).items():
                    for cve_id in cve_data.get("cves", [])[:5]:
                        cve_info = self.nist_nvd.get_cve(cve_id)
                        if cve_info:
                            mitre_intel.related_cves.append(cve_info)
                            if cve_info.is_critical():
                                mitre_intel.critical_cves.append(cve_id)
                            if cve_info.cisa_kev:
                                mitre_intel.actively_exploited_cves.append(cve_id)

            except Exception as e:
                logger.warning(f"Failed to enrich with CVE data: {e}")

        return mitre_intel

    def get_attack_techniques_for_phase(
        self, phase: str
    ) -> List[ATTACKTechnique]:
        """
        Get relevant ATT&CK techniques for an IR phase.

        Args:
            phase: IR phase name

        Returns:
            List of relevant ATTACKTechnique objects
        """
        return self.mitre.get_techniques_for_phase(phase)

    def get_ransomware_techniques(self) -> List[ATTACKTechnique]:
        """
        Get ATT&CK techniques commonly used by ransomware.

        Returns:
            List of ransomware-related techniques
        """
        return self.mitre.get_ransomware_techniques()

    def search_cves(
        self,
        keyword: Optional[str] = None,
        cve_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[CVEInfo]:
        """
        Search for CVEs in NVD.

        Args:
            keyword: Search keyword
            cve_id: Specific CVE ID
            severity: CVSS severity (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            List of CVEInfo objects
        """
        if self.offline_mode:
            logger.warning("CVE search not available in offline mode")
            return []

        cves, _ = self.nist_nvd.search_cves(
            keyword=keyword,
            cve_id=cve_id,
            cvss_v3_severity=severity,
        )
        return cves

    def generate_compliance_report(
        self,
        incident_id: str,
        phase_results: Dict[str, Dict[str, List[ComplianceCheck]]],
        operator: str = "",
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report.

        Args:
            incident_id: Incident identifier
            phase_results: Results from validate_all_phases()
            operator: Name of the operator

        Returns:
            ComplianceReport object
        """
        # Flatten results by framework
        all_checks_by_framework: Dict[str, List[ComplianceCheck]] = {}

        for phase, framework_results in phase_results.items():
            for framework, checks in framework_results.items():
                if framework not in all_checks_by_framework:
                    all_checks_by_framework[framework] = []
                all_checks_by_framework[framework].extend(checks)

        # Determine frameworks evaluated
        frameworks_evaluated = [
            ComplianceFramework(fw) for fw in all_checks_by_framework.keys()
        ]

        report = ComplianceReport(
            incident_id=incident_id,
            generated_by=operator,
            frameworks_evaluated=frameworks_evaluated,
            results=all_checks_by_framework,
        )

        # Calculate statistics
        report.calculate_statistics()

        return report

    def export_compliance_report(
        self,
        report: ComplianceReport,
        format: str = "markdown",
        include_details: bool = True,
    ) -> str:
        """
        Export compliance report to various formats.

        Args:
            report: ComplianceReport to export
            format: "markdown", "json", or "html"
            include_details: Include detailed control information

        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps(report.model_dump(), indent=2, default=str)

        # Markdown format
        lines = [
            "# Compliance Report",
            "",
            f"**Incident ID:** {report.incident_id}",
            f"**Generated:** {report.generated_at.isoformat()}",
            f"**Generated By:** {report.generated_by or 'System'}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Controls Evaluated | {report.total_controls} |",
            f"| Compliant | {report.compliant_count} |",
            f"| Partial | {report.partial_count} |",
            f"| Gaps | {report.gap_count} |",
            f"| **Compliance Score** | **{report.compliance_score:.1f}%** |",
            "",
        ]

        # Critical gaps
        if report.critical_gaps:
            lines.extend([
                "## Critical Gaps Requiring Immediate Attention",
                "",
            ])
            for gap in report.critical_gaps:
                lines.append(f"- **{gap.control_id}** ({gap.framework.value}): {gap.control_name}")
                if gap.recommendation:
                    lines.append(f"  - Recommendation: {gap.recommendation}")
            lines.append("")

        # Results by framework
        if include_details:
            lines.extend([
                "## Results by Framework",
                "",
            ])

            for framework, checks in report.results.items():
                compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT)
                total = len(checks)
                score = (compliant / total * 100) if total > 0 else 0

                lines.extend([
                    f"### {framework.upper()}",
                    "",
                    f"Score: {score:.1f}% ({compliant}/{total} controls compliant)",
                    "",
                    "| Control | Status | Priority |",
                    "|---------|--------|----------|",
                ])

                for check in checks:
                    status_icon = {
                        ComplianceStatus.COMPLIANT: "✅",
                        ComplianceStatus.PARTIAL: "⚠️",
                        ComplianceStatus.GAP: "❌",
                        ComplianceStatus.NOT_EVALUATED: "⏸️",
                    }.get(check.status, "❓")

                    lines.append(
                        f"| {check.control_id} | {status_icon} {check.status.value} | "
                        f"{check.remediation_priority or 'N/A'} |"
                    )

                lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*This report was generated by ISORA Compliance Hub.*",
            "",
            "**Frameworks Referenced:**",
        ])

        for fw in report.frameworks_evaluated:
            lines.append(f"- {fw.value}")

        return "\n".join(lines)

    def export_threat_intelligence(
        self,
        intel: ThreatIntelligence,
        format: str = "markdown",
    ) -> str:
        """
        Export threat intelligence to various formats.

        Args:
            intel: ThreatIntelligence object
            format: "markdown" or "json"

        Returns:
            Formatted threat intelligence string
        """
        if format == "json":
            return json.dumps(intel.model_dump(), indent=2, default=str)

        # Markdown format
        lines = [
            "# Threat Intelligence Report",
            "",
            f"**Incident ID:** {intel.incident_id}",
            f"**Collected:** {intel.collected_at.isoformat()}",
            "",
        ]

        if intel.ransomware_family:
            lines.append(f"**Ransomware Family:** {intel.ransomware_family}")
            lines.append("")

        # MITRE ATT&CK
        if intel.mapped_techniques:
            lines.extend([
                "## MITRE ATT&CK Mapping",
                "",
                "### Identified Techniques",
                "",
                "| ID | Name | Tactics | Relevance |",
                "|----|------|---------|-----------|",
            ])

            for tech in intel.mapped_techniques[:15]:
                tactics = ", ".join(tech.tactics[:2])
                relevance = f"{tech.relevance_score:.0%}" if tech.relevance_score else "-"
                lines.append(
                    f"| [{tech.technique_id}]({tech.url}) | {tech.name} | {tactics} | {relevance} |"
                )

            lines.append("")

        # Primary tactics
        if intel.primary_tactics:
            lines.extend([
                "### Primary Tactics (Kill Chain)",
                "",
            ])
            for i, tactic in enumerate(intel.primary_tactics, 1):
                lines.append(f"{i}. {tactic}")
            lines.append("")

        # CVEs
        if intel.related_cves:
            lines.extend([
                "## Related Vulnerabilities (CVEs)",
                "",
                "| CVE ID | Severity | CISA KEV | Description |",
                "|--------|----------|----------|-------------|",
            ])

            for cve in intel.related_cves[:10]:
                severity = cve.cvss_v3.severity if cve.cvss_v3 else "N/A"
                kev = "⚠️ Yes" if cve.cisa_kev else "No"
                desc = cve.description[:50] + "..." if len(cve.description) > 50 else cve.description
                lines.append(f"| {cve.cve_id} | {severity} | {kev} | {desc} |")

            lines.append("")

        if intel.critical_cves:
            lines.append(f"**Critical CVEs:** {', '.join(intel.critical_cves)}")
            lines.append("")

        if intel.actively_exploited_cves:
            lines.append(f"**⚠️ CISA KEV (Actively Exploited):** {', '.join(intel.actively_exploited_cves)}")
            lines.append("")

        # Recommendations
        if intel.detection_recommendations:
            lines.extend([
                "## Detection Recommendations",
                "",
            ])
            for rec in intel.detection_recommendations[:5]:
                lines.append(f"- {rec}")
            lines.append("")

        if intel.mitigation_recommendations:
            lines.extend([
                "## Mitigation Recommendations",
                "",
            ])
            for rec in intel.mitigation_recommendations[:5]:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    def get_framework_info(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """
        Get information about a compliance framework.

        Args:
            framework: Framework to get info for

        Returns:
            Dictionary with framework information
        """
        info = {
            ComplianceFramework.BSI_GRUNDSCHUTZ: {
                "name": "BSI IT-Grundschutz",
                "organization": "Bundesamt für Sicherheit in der Informationstechnik (Germany)",
                "version": "2023 (Grundschutz++ coming 2026)",
                "format": "OSCAL/JSON",
                "url": "https://www.bsi.bund.de/",
                "repository": "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek",
            },
            ComplianceFramework.NIST_CSF_2: {
                "name": "NIST Cybersecurity Framework 2.0",
                "organization": "National Institute of Standards and Technology (USA)",
                "version": "2.0 (2024)",
                "format": "OSCAL/JSON/XML/YAML",
                "url": "https://www.nist.gov/cyberframework",
                "repository": "https://github.com/usnistgov/oscal-content",
            },
            ComplianceFramework.NIST_800_53: {
                "name": "NIST SP 800-53 Security Controls",
                "organization": "National Institute of Standards and Technology (USA)",
                "version": "Revision 5.1.1",
                "format": "OSCAL/JSON/XML/YAML",
                "url": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                "repository": "https://github.com/usnistgov/oscal-content",
            },
            ComplianceFramework.NIST_800_61: {
                "name": "NIST SP 800-61 Incident Response Guide",
                "organization": "National Institute of Standards and Technology (USA)",
                "version": "Revision 3 (April 2025)",
                "format": "PDF/OSCAL",
                "url": "https://csrc.nist.gov/publications/detail/sp/800-61/rev-3/final",
                "notes": "Aligned with CSF 2.0",
            },
            ComplianceFramework.ISO_27001: {
                "name": "ISO/IEC 27001 Information Security Management",
                "organization": "International Organization for Standardization",
                "version": "2022",
                "format": "Document (not machine-readable)",
                "url": "https://www.iso.org/standard/27001",
                "notes": "Paid standard, mappings provided",
            },
            ComplianceFramework.ISO_27035: {
                "name": "ISO/IEC 27035 Incident Management",
                "organization": "International Organization for Standardization",
                "version": "2023 (Part 1)",
                "format": "Document (not machine-readable)",
                "url": "https://www.iso.org/standard/78973.html",
                "notes": "Paid standard, mappings provided",
            },
            ComplianceFramework.MITRE_ATTACK: {
                "name": "MITRE ATT&CK",
                "organization": "MITRE Corporation",
                "version": "Enterprise ATT&CK (latest)",
                "format": "STIX 2.1 JSON",
                "url": "https://attack.mitre.org/",
                "repository": "https://github.com/mitre-attack/attack-stix-data",
            },
            ComplianceFramework.OWASP_TOP_10: {
                "name": "OWASP Top 10",
                "organization": "Open Web Application Security Project",
                "version": "2021",
                "format": "Web/JSON",
                "url": "https://owasp.org/Top10/",
                "cheat_sheets": "https://cheatsheetseries.owasp.org/",
                "notes": "Web application security risks with Cheat Sheet Series",
            },
        }

        return info.get(framework, {"name": framework.value, "status": "Unknown"})

    def get_owasp_recommendations(self, phase: str) -> Dict[str, Any]:
        """
        Get OWASP recommendations for an IR phase.

        Args:
            phase: Current IR phase

        Returns:
            Dictionary with OWASP guidance for the phase
        """
        return self.owasp.get_phase_recommendations(phase)

    def get_owasp_cheat_sheets(self, risk_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relevant OWASP Cheat Sheets.

        Args:
            risk_id: Optional OWASP Top 10 risk ID to filter sheets

        Returns:
            List of cheat sheet references
        """
        if risk_id:
            guidance = self.owasp.get_remediation_guidance(risk_id)
            return guidance.get("cheat_sheets", [])

        return [
            {
                "name": sheet.name,
                "url": sheet.url,
                "category": sheet.category,
                "summary": sheet.summary,
            }
            for sheet in self.owasp.get_all_cheat_sheets()
        ]

    def identify_owasp_risks(self, indicators: List[str]) -> List[Dict[str, Any]]:
        """
        Identify OWASP Top 10 risks from incident indicators.

        Args:
            indicators: List of incident indicators (logs, errors, etc.)

        Returns:
            List of identified risks with remediation guidance
        """
        risks = self.owasp.identify_risks_from_indicators(indicators)

        return [
            {
                "id": risk.id,
                "name": risk.name,
                "description": risk.description,
                "attack_vectors": risk.attack_vectors,
                "prevention": risk.prevention,
                "cheat_sheets": risk.cheat_sheets,
            }
            for risk in risks
        ]

    # =========================================================================
    # Cross-Framework Mapping Methods
    # =========================================================================

    def get_cross_framework_mapping(self, phase: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cross-framework control mapping.

        Args:
            phase: Optional IR phase to filter controls

        Returns:
            Mapping data including matrix and control details
        """
        if phase:
            controls = self.cross_mapper.get_controls_for_phase(phase)
            return {
                "phase": phase,
                "controls": [
                    {
                        "unified_id": c.unified_id,
                        "name": c.name,
                        "description": c.description,
                        "category": c.category,
                        "framework_controls": {
                            fw.value: ctrls for fw, ctrls in c.framework_controls.items()
                        },
                        "evidence_requirements": c.evidence_requirements,
                    }
                    for c in controls
                ],
            }

        return self.cross_mapper.get_framework_comparison_matrix()

    def find_equivalent_controls(
        self,
        control_id: str,
        framework: str,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Find equivalent controls in other frameworks.

        Args:
            control_id: Source control ID
            framework: Source framework name

        Returns:
            Dictionary mapping framework names to equivalent controls
        """
        try:
            fw_type = FrameworkType(framework)
        except ValueError:
            return {}

        equivalents = self.cross_mapper.find_equivalent_controls(control_id, fw_type)

        return {
            fw.value: controls
            for fw, controls in equivalents.items()
        }

    def calculate_unified_coverage(
        self,
        completed_controls: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Calculate compliance coverage across all frameworks.

        Args:
            completed_controls: Dict mapping framework name to completed control IDs

        Returns:
            Unified coverage statistics
        """
        # Convert string keys to FrameworkType
        typed_controls = {}
        for fw_name, controls in completed_controls.items():
            try:
                fw_type = FrameworkType(fw_name)
                typed_controls[fw_type] = controls
            except ValueError:
                continue

        return self.cross_mapper.calculate_cross_framework_coverage(typed_controls)

    def get_control_details(
        self,
        control_id: str,
        framework: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a control with all cross-references.

        Args:
            control_id: Control ID
            framework: Framework name

        Returns:
            Control details with all mappings
        """
        try:
            fw_type = FrameworkType(framework)
        except ValueError:
            return {"error": f"Unknown framework: {framework}"}

        return self.cross_mapper.get_control_details(control_id, fw_type)

    def export_cross_framework_matrix(self, format: str = "markdown") -> str:
        """
        Export the complete cross-framework mapping table.

        Args:
            format: "markdown" or "csv"

        Returns:
            Formatted mapping table
        """
        return self.cross_mapper.export_mapping_table(format)

    def preload_data(self) -> Dict[str, bool]:
        """
        Preload data from all integrations for faster access.

        Useful to call during application startup.

        Returns:
            Dictionary mapping integration name to load success status
        """
        results = {}

        # Load MITRE ATT&CK data
        try:
            results["mitre_attack"] = self.mitre.load_attack_data()
        except Exception as e:
            logger.error(f"Failed to preload MITRE ATT&CK: {e}")
            results["mitre_attack"] = False

        # Load NIST OSCAL catalogs
        try:
            catalog = self.nist_oscal.fetch_sp800_53_catalog()
            results["nist_sp800_53"] = catalog is not None
        except Exception as e:
            logger.error(f"Failed to preload NIST SP 800-53: {e}")
            results["nist_sp800_53"] = False

        # BSI data (if available)
        try:
            catalog = self.bsi.fetch_catalog()
            results["bsi_grundschutz"] = catalog is not None
        except Exception as e:
            logger.error(f"Failed to preload BSI: {e}")
            results["bsi_grundschutz"] = False

        # ISO mapper is always available (static mappings)
        results["iso_27001_27035"] = True

        return results


# Convenience function for quick compliance check
def quick_compliance_check(
    phase: str,
    completed_actions: List[str],
    evidence_collected: List[str],
    frameworks: Optional[List[str]] = None,
) -> Dict[str, List[Dict]]:
    """
    Quick compliance check without full hub initialization.

    Args:
        phase: IR phase name
        completed_actions: Completed checklist items
        evidence_collected: Evidence descriptions
        frameworks: Framework names to check

    Returns:
        Simplified compliance results
    """
    hub = ComplianceHub(offline_mode=True)

    fw_enums = None
    if frameworks:
        fw_enums = [ComplianceFramework(fw) for fw in frameworks]

    results = hub.validate_phase_compliance(
        phase=phase,
        incident_data={
            "completed_actions": completed_actions,
            "evidence_collected": evidence_collected,
        },
        frameworks=fw_enums,
    )

    # Simplify results for quick use
    simplified = {}
    for fw, checks in results.items():
        simplified[fw] = [
            {
                "control": c.control_id,
                "status": c.status.value,
                "recommendation": c.recommendation,
            }
            for c in checks
        ]

    return simplified
