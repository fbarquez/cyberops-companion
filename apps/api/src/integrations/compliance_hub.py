"""
Compliance Hub - Central integration point for regulatory compliance.

Orchestrates integrations with:
- BSI IT-Grundschutz (Germany)
- NIST CSF 2.0, SP 800-53
- ISO 27001:2022, ISO 27035
- Cross-framework mapping

Features:
- Unified compliance validation across multiple frameworks
- Compliance reporting and export
- Phase-based compliance checking
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.integrations.models import (
    ComplianceFramework,
    ComplianceCheck,
    ComplianceStatus,
    ComplianceReport,
    FrameworkInfo,
    ComplianceValidationResult,
)
from src.integrations.bsi_integration import BSIIntegration
from src.integrations.iso_mapper import ISOComplianceMapper
from src.integrations.cross_framework_mapper import CrossFrameworkMapper, FrameworkType

logger = logging.getLogger(__name__)


class ComplianceHub:
    """
    Central hub for compliance integrations.

    Provides a unified interface to validate incident response activities
    against multiple regulatory frameworks.

    Usage:
        hub = ComplianceHub()

        # Validate compliance for a phase
        results = hub.validate_phase_compliance(
            phase="analysis",
            incident_data={...},
            frameworks=["bsi_grundschutz", "iso_27001"]
        )

        # Generate compliance report
        report = hub.generate_compliance_report(
            incident_id="INC-2024-001",
            phase_results={...}
        )
    """

    # Framework metadata
    FRAMEWORKS = {
        "bsi_grundschutz": FrameworkInfo(
            id="bsi_grundschutz",
            name="BSI IT-Grundschutz",
            description="German Federal Office for Information Security framework",
            version="2023",
            controls_count=150,
            organization="Bundesamt für Sicherheit in der Informationstechnik",
            url="https://www.bsi.bund.de/",
        ),
        "nist_csf_2": FrameworkInfo(
            id="nist_csf_2",
            name="NIST CSF 2.0",
            description="NIST Cybersecurity Framework version 2.0",
            version="2.0",
            controls_count=108,
            organization="National Institute of Standards and Technology",
            url="https://www.nist.gov/cyberframework",
        ),
        "nist_800_53": FrameworkInfo(
            id="nist_800_53",
            name="NIST SP 800-53",
            description="Security and Privacy Controls for Information Systems",
            version="Rev 5.1",
            controls_count=1189,
            organization="National Institute of Standards and Technology",
            url="https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
        ),
        "iso_27001": FrameworkInfo(
            id="iso_27001",
            name="ISO/IEC 27001:2022",
            description="Information Security Management Systems - Requirements",
            version="2022",
            controls_count=93,
            organization="International Organization for Standardization",
            url="https://www.iso.org/standard/27001",
        ),
        "iso_27035": FrameworkInfo(
            id="iso_27035",
            name="ISO/IEC 27035",
            description="Information Security Incident Management",
            version="2023",
            controls_count=40,
            organization="International Organization for Standardization",
            url="https://www.iso.org/standard/78973.html",
        ),
        "mitre_attack": FrameworkInfo(
            id="mitre_attack",
            name="MITRE ATT&CK",
            description="Adversarial Tactics, Techniques & Common Knowledge",
            version="v14",
            controls_count=600,
            organization="MITRE Corporation",
            url="https://attack.mitre.org/",
        ),
        "nis2": FrameworkInfo(
            id="nis2",
            name="NIS2 Directive",
            description="EU Network and Information Security Directive 2.0",
            version="2022",
            controls_count=35,
            organization="European Union",
            url="https://digital-strategy.ec.europa.eu/en/policies/nis2-directive",
        ),
        "owasp_top_10": FrameworkInfo(
            id="owasp_top_10",
            name="OWASP Top 10",
            description="Top 10 Web Application Security Risks",
            version="2021",
            controls_count=10,
            organization="Open Web Application Security Project",
            url="https://owasp.org/Top10/",
        ),
    }

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        offline_mode: bool = False,
    ):
        """
        Initialize the Compliance Hub.

        Args:
            cache_dir: Base directory for caching data
            offline_mode: If True, only use cached data (no network requests)
        """
        self.cache_dir = cache_dir or Path.home() / ".ir_companion" / "cache"
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

        # ISO Mapper (static mappings, no network needed)
        self.iso = ISOComplianceMapper()

        # Cross-Framework Mapper (static mappings)
        self.cross_mapper = CrossFrameworkMapper()

        logger.info("Compliance Hub initialized with all integrations")

    def get_frameworks(self) -> List[FrameworkInfo]:
        """Get all available compliance frameworks."""
        return list(self.FRAMEWORKS.values())

    def get_framework(self, framework_id: str) -> Optional[FrameworkInfo]:
        """Get a specific framework by ID."""
        return self.FRAMEWORKS.get(framework_id)

    def validate_phase_compliance(
        self,
        phase: str,
        incident_data: Dict[str, Any],
        frameworks: Optional[List[str]] = None,
        operator: str = "",
    ) -> Dict[str, ComplianceValidationResult]:
        """
        Validate compliance for an IR phase against multiple frameworks.

        Args:
            phase: IR phase name (detection, analysis, containment, etc.)
            incident_data: Dictionary containing:
                - completed_actions: List of completed checklist item IDs
                - evidence_collected: List of evidence entry descriptions
                - documentation_provided: List of documentation items
            frameworks: List of framework IDs to validate (None = default set)
            operator: Name of the operator performing validation

        Returns:
            Dictionary mapping framework ID to ComplianceValidationResult
        """
        if frameworks is None:
            frameworks = ["bsi_grundschutz", "iso_27001", "nist_csf_2"]

        completed_actions = incident_data.get("completed_actions", [])
        evidence_collected = incident_data.get("evidence_collected", [])
        documentation_provided = incident_data.get("documentation_provided", [])

        results: Dict[str, ComplianceValidationResult] = {}

        for framework_id in frameworks:
            try:
                checks = self._validate_framework(
                    framework_id=framework_id,
                    phase=phase,
                    completed_actions=completed_actions,
                    evidence_collected=evidence_collected,
                    documentation_provided=documentation_provided,
                    operator=operator,
                )

                # Calculate statistics
                total = len(checks)
                compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT)
                partial = sum(1 for c in checks if c.status == ComplianceStatus.PARTIAL)
                gaps = sum(1 for c in checks if c.status == ComplianceStatus.GAP)

                score = 0.0
                if total > 0:
                    score = ((compliant + partial * 0.5) / total) * 100

                # Extract gaps and recommendations
                gap_list = [
                    {
                        "control_id": c.control_id,
                        "control_name": c.control_name,
                        "gap_description": c.gap_description,
                        "priority": c.remediation_priority,
                    }
                    for c in checks
                    if c.status == ComplianceStatus.GAP
                ]

                recommendations = [
                    c.recommendation
                    for c in checks
                    if c.recommendation and c.status != ComplianceStatus.COMPLIANT
                ]

                results[framework_id] = ComplianceValidationResult(
                    framework=framework_id,
                    compliant=gaps == 0,
                    score=round(score, 1),
                    total_controls=total,
                    compliant_count=compliant,
                    partial_count=partial,
                    gap_count=gaps,
                    gaps=gap_list,
                    recommendations=list(set(recommendations))[:10],
                )

            except Exception as e:
                logger.error(f"Error validating {framework_id}: {e}")
                results[framework_id] = ComplianceValidationResult(
                    framework=framework_id,
                    compliant=False,
                    score=0.0,
                    total_controls=0,
                    compliant_count=0,
                    partial_count=0,
                    gap_count=0,
                    gaps=[{"error": str(e)}],
                    recommendations=[],
                )

        return results

    def _validate_framework(
        self,
        framework_id: str,
        phase: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        documentation_provided: List[str],
        operator: str,
    ) -> List[ComplianceCheck]:
        """Validate a single framework."""
        if framework_id == "bsi_grundschutz":
            return self.bsi.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                operator=operator,
            )

        elif framework_id == "iso_27001":
            return self.iso.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                documentation_provided=documentation_provided,
                standard="iso27001",
                operator=operator,
            )

        elif framework_id == "iso_27035":
            return self.iso.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                documentation_provided=documentation_provided,
                standard="iso27035",
                operator=operator,
            )

        elif framework_id in ["nist_csf_2", "nist_800_53"]:
            # Use ISO mapper with NIST keywords (simplified)
            return self.iso.validate_phase_compliance(
                phase=phase,
                completed_actions=completed_actions,
                evidence_collected=evidence_collected,
                documentation_provided=documentation_provided,
                standard="iso27001",  # Similar structure
                operator=operator,
            )

        else:
            logger.warning(f"Framework {framework_id} validation not fully implemented")
            return []

    def validate_all_phases(
        self,
        incident_data: Dict[str, Dict[str, Any]],
        frameworks: Optional[List[str]] = None,
        operator: str = "",
    ) -> Dict[str, Dict[str, ComplianceValidationResult]]:
        """
        Validate compliance for all IR phases.

        Args:
            incident_data: Dictionary mapping phase names to phase data
            frameworks: List of framework IDs to validate
            operator: Name of the operator

        Returns:
            Nested dictionary: phase -> framework -> result
        """
        phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
        all_results: Dict[str, Dict[str, ComplianceValidationResult]] = {}

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

    def generate_compliance_report(
        self,
        incident_id: str,
        phase_results: Dict[str, Dict[str, ComplianceValidationResult]],
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
        # Flatten results and convert to ComplianceCheck format
        all_checks_by_framework: Dict[str, List[ComplianceCheck]] = {}
        frameworks_set = set()

        for phase, framework_results in phase_results.items():
            for framework_id, result in framework_results.items():
                frameworks_set.add(framework_id)
                if framework_id not in all_checks_by_framework:
                    all_checks_by_framework[framework_id] = []

                # Create ComplianceCheck objects from gaps
                for gap in result.gaps:
                    if "error" not in gap:
                        check = ComplianceCheck(
                            framework=ComplianceFramework(framework_id) if framework_id in [e.value for e in ComplianceFramework] else ComplianceFramework.BSI_GRUNDSCHUTZ,
                            control_id=gap.get("control_id", ""),
                            control_name=gap.get("control_name", ""),
                            status=ComplianceStatus.GAP,
                            gap_description=gap.get("gap_description"),
                            remediation_priority=gap.get("priority"),
                            evaluated_by=operator,
                        )
                        all_checks_by_framework[framework_id].append(check)

        # Determine frameworks evaluated
        frameworks_evaluated = []
        for fw_id in frameworks_set:
            try:
                frameworks_evaluated.append(ComplianceFramework(fw_id))
            except ValueError:
                pass

        report = ComplianceReport(
            incident_id=incident_id,
            generated_by=operator,
            frameworks_evaluated=frameworks_evaluated,
            results=all_checks_by_framework,
        )

        # Calculate statistics
        report.calculate_statistics()

        return report

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
            "*This report was generated by IR Companion Compliance Hub.*",
            "",
            "**Frameworks Referenced:**",
        ])

        for fw in report.frameworks_evaluated:
            lines.append(f"- {fw.value}")

        return "\n".join(lines)

    def export_cross_framework_matrix(self, format: str = "markdown") -> str:
        """
        Export the complete cross-framework mapping table.

        Args:
            format: "markdown" or "csv"

        Returns:
            Formatted mapping table
        """
        return self.cross_mapper.export_mapping_table(format)
