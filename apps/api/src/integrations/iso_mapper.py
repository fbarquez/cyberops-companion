"""
ISO Compliance Mapper.

Provides mapping of ISO 27001:2022 and ISO 27035:2023 controls
to incident response phases.

Standards covered:
- ISO/IEC 27001:2022 - Information Security Management Systems
- ISO/IEC 27035-1:2023 - Information Security Incident Management (Principles)
- ISO/IEC 27035-2:2023 - Information Security Incident Management (Planning)
- ISO/IEC 27035-3:2020 - Information Security Incident Management (Operations)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from src.integrations.models import (
    ComplianceFramework,
    ComplianceControl,
    ComplianceCheck,
    ComplianceStatus,
    PhaseComplianceMapping,
)

logger = logging.getLogger(__name__)


class ISO27035Phase(str, Enum):
    """ISO 27035 Incident Management Phases."""
    PLAN_PREPARE = "plan_prepare"
    DETECTION_REPORTING = "detection_reporting"
    ASSESSMENT_DECISION = "assessment_decision"
    RESPONSES = "responses"
    LESSONS_LEARNED = "lessons_learned"


class ISOComplianceMapper:
    """
    Maps ISO 27001:2022 and ISO 27035 controls to IR phases.

    This class provides static mappings since ISO standards
    are not available as public APIs or machine-readable formats.

    Features:
    - Map IR phases to ISO 27001 Annex A controls
    - Map IR phases to ISO 27035 requirements
    - Generate compliance checklists
    - Validate documentation requirements
    """

    # ISO 27001:2022 Annex A controls relevant to Incident Response
    ISO27001_PHASE_MAPPING = {
        "detection": {
            "controls": [
                {
                    "id": "A.5.24",
                    "name": "Information security incident management planning and preparation",
                    "description": "Plans and procedures for managing information security incidents shall be established and communicated.",
                },
                {
                    "id": "A.5.25",
                    "name": "Assessment and decision on information security events",
                    "description": "Information security events shall be assessed and classified as information security incidents.",
                },
                {
                    "id": "A.8.15",
                    "name": "Logging",
                    "description": "Logs that record activities, exceptions, faults and other relevant events shall be produced, stored, protected and analyzed.",
                },
                {
                    "id": "A.8.16",
                    "name": "Monitoring activities",
                    "description": "Networks, systems and applications shall be monitored for anomalous behavior.",
                },
            ],
            "mandatory": ["A.5.24", "A.5.25"],
            "iso27035_phase": ISO27035Phase.DETECTION_REPORTING,
            "description": "Incident detection and initial classification",
        },
        "analysis": {
            "controls": [
                {
                    "id": "A.5.26",
                    "name": "Response to information security incidents",
                    "description": "Information security incidents shall be responded to in accordance with documented procedures.",
                },
                {
                    "id": "A.5.28",
                    "name": "Collection of evidence",
                    "description": "Procedures for identification, collection, acquisition and preservation of evidence shall be defined and implemented.",
                },
                {
                    "id": "A.8.12",
                    "name": "Data leakage prevention",
                    "description": "Data leakage prevention measures shall be applied to systems, networks and any other devices that process, store or transmit sensitive information.",
                },
            ],
            "mandatory": ["A.5.26", "A.5.28"],
            "iso27035_phase": ISO27035Phase.ASSESSMENT_DECISION,
            "description": "Incident analysis and evidence collection",
        },
        "containment": {
            "controls": [
                {
                    "id": "A.5.26",
                    "name": "Response to information security incidents",
                    "description": "Information security incidents shall be responded to in accordance with documented procedures.",
                },
                {
                    "id": "A.8.20",
                    "name": "Networks security",
                    "description": "Networks and network devices shall be secured, managed and controlled.",
                },
                {
                    "id": "A.8.21",
                    "name": "Security of network services",
                    "description": "Security mechanisms, service levels and service requirements shall be identified, implemented and monitored.",
                },
                {
                    "id": "A.8.22",
                    "name": "Segregation of networks",
                    "description": "Groups of information services, users and information systems shall be segregated in networks.",
                },
            ],
            "mandatory": ["A.5.26"],
            "iso27035_phase": ISO27035Phase.RESPONSES,
            "description": "Incident containment activities",
        },
        "eradication": {
            "controls": [
                {
                    "id": "A.5.26",
                    "name": "Response to information security incidents",
                    "description": "Information security incidents shall be responded to in accordance with documented procedures.",
                },
                {
                    "id": "A.8.7",
                    "name": "Protection against malware",
                    "description": "Protection against malware shall be implemented and supported by appropriate user awareness.",
                },
                {
                    "id": "A.8.8",
                    "name": "Management of technical vulnerabilities",
                    "description": "Information about technical vulnerabilities shall be obtained, evaluated and appropriate measures taken.",
                },
                {
                    "id": "A.8.9",
                    "name": "Configuration management",
                    "description": "Configurations of hardware, software, services and networks shall be established, documented, implemented, monitored and reviewed.",
                },
            ],
            "mandatory": ["A.5.26", "A.8.7", "A.8.8"],
            "iso27035_phase": ISO27035Phase.RESPONSES,
            "description": "Threat eradication activities",
        },
        "recovery": {
            "controls": [
                {
                    "id": "A.5.29",
                    "name": "Information security during disruption",
                    "description": "Plans shall be maintained for ensuring information security during disruptions.",
                },
                {
                    "id": "A.5.30",
                    "name": "ICT readiness for business continuity",
                    "description": "ICT readiness shall be planned, implemented, maintained and tested based on business continuity objectives.",
                },
                {
                    "id": "A.8.13",
                    "name": "Information backup",
                    "description": "Backup copies of information, software and system images shall be maintained and regularly tested.",
                },
                {
                    "id": "A.8.14",
                    "name": "Redundancy of information processing facilities",
                    "description": "Information processing facilities shall be implemented with sufficient redundancy.",
                },
            ],
            "mandatory": ["A.5.29", "A.5.30", "A.8.13"],
            "iso27035_phase": ISO27035Phase.RESPONSES,
            "description": "Recovery and restoration activities",
        },
        "post_incident": {
            "controls": [
                {
                    "id": "A.5.27",
                    "name": "Learning from information security incidents",
                    "description": "Knowledge gained from information security incidents shall be used to strengthen and improve the information security controls.",
                },
                {
                    "id": "A.5.35",
                    "name": "Independent review of information security",
                    "description": "The organization's approach to managing information security shall be reviewed independently at planned intervals.",
                },
                {
                    "id": "A.5.36",
                    "name": "Compliance with policies, rules and standards for information security",
                    "description": "Compliance with policies, rules and standards shall be regularly reviewed.",
                },
            ],
            "mandatory": ["A.5.27"],
            "iso27035_phase": ISO27035Phase.LESSONS_LEARNED,
            "description": "Post-incident review and improvement",
        },
    }

    # ISO 27035 specific requirements
    ISO27035_REQUIREMENTS = {
        ISO27035Phase.PLAN_PREPARE: {
            "requirements": [
                "Incident management policy established",
                "Incident response team defined",
                "Communication procedures documented",
                "Escalation procedures defined",
                "Testing and exercises conducted",
            ],
            "documentation": [
                "Incident management policy",
                "Incident response plan",
                "Communication plan",
                "Contact lists",
            ],
        },
        ISO27035Phase.DETECTION_REPORTING: {
            "requirements": [
                "Detection mechanisms operational",
                "Reporting channels available",
                "Initial classification performed",
                "Incident logged and tracked",
            ],
            "documentation": [
                "Incident report form",
                "Initial classification record",
                "Detection timestamp",
                "Reporter information",
            ],
        },
        ISO27035Phase.ASSESSMENT_DECISION: {
            "requirements": [
                "Incident assessed and classified",
                "Impact analysis performed",
                "Response decision made",
                "Resources allocated",
            ],
            "documentation": [
                "Assessment report",
                "Impact analysis",
                "Classification decision",
                "Resource allocation record",
            ],
        },
        ISO27035Phase.RESPONSES: {
            "requirements": [
                "Containment actions executed",
                "Evidence collected and preserved",
                "Eradication activities completed",
                "Recovery procedures followed",
                "Communication maintained",
            ],
            "documentation": [
                "Response action log",
                "Evidence collection records",
                "Chain of custody forms",
                "Recovery verification records",
                "Communication log",
            ],
        },
        ISO27035Phase.LESSONS_LEARNED: {
            "requirements": [
                "Post-incident review conducted",
                "Root cause identified",
                "Improvements identified",
                "Documentation completed",
                "Incident formally closed",
            ],
            "documentation": [
                "Post-incident report",
                "Root cause analysis",
                "Lessons learned document",
                "Improvement recommendations",
                "Incident closure record",
            ],
        },
    }

    # Documentation requirements by IR phase
    DOCUMENTATION_REQUIREMENTS = {
        "detection": [
            "Initial incident report (who, what, when, where)",
            "Alert/notification records",
            "Affected systems inventory",
            "Initial classification justification",
            "Timestamp of detection (UTC)",
        ],
        "analysis": [
            "Scope assessment document",
            "Evidence collection log",
            "Chain of custody forms",
            "IOC documentation",
            "Impact analysis",
            "Memory/disk acquisition records",
        ],
        "containment": [
            "Network isolation records",
            "System isolation documentation",
            "Blocked indicators list",
            "Credential changes log",
            "Communication to stakeholders",
        ],
        "eradication": [
            "Malware removal verification",
            "Persistence mechanism removal log",
            "Patch application records",
            "Configuration changes log",
            "Scan/verification results",
        ],
        "recovery": [
            "Backup verification records",
            "System restoration log",
            "Integrity verification records",
            "Monitoring enablement confirmation",
            "Business validation sign-off",
        ],
        "post_incident": [
            "Complete incident timeline",
            "Root cause analysis",
            "Lessons learned document",
            "Improvement recommendations",
            "Final incident report",
            "Stakeholder sign-off",
        ],
    }

    def __init__(self):
        """Initialize ISO compliance mapper."""
        self.controls_cache: Dict[str, ComplianceControl] = {}

    def get_iso27001_mapping_for_phase(self, phase: str) -> PhaseComplianceMapping:
        """
        Get ISO 27001:2022 control mapping for an IR phase.

        Args:
            phase: IR phase name

        Returns:
            PhaseComplianceMapping with ISO 27001 controls
        """
        phase_data = self.ISO27001_PHASE_MAPPING.get(phase, {})
        controls = phase_data.get("controls", [])

        return PhaseComplianceMapping(
            phase=phase,
            framework=ComplianceFramework.ISO_27001,
            controls=[c["id"] for c in controls],
            mandatory_controls=phase_data.get("mandatory", []),
            documentation_required=self.DOCUMENTATION_REQUIREMENTS.get(phase, []),
        )

    def get_iso27035_mapping_for_phase(self, phase: str) -> PhaseComplianceMapping:
        """
        Get ISO 27035 requirements mapping for an IR phase.

        Args:
            phase: IR phase name

        Returns:
            PhaseComplianceMapping with ISO 27035 requirements
        """
        phase_data = self.ISO27001_PHASE_MAPPING.get(phase, {})
        iso27035_phase = phase_data.get("iso27035_phase")

        if not iso27035_phase:
            return PhaseComplianceMapping(
                phase=phase,
                framework=ComplianceFramework.ISO_27035,
                controls=[],
                documentation_required=[],
            )

        requirements = self.ISO27035_REQUIREMENTS.get(iso27035_phase, {})

        return PhaseComplianceMapping(
            phase=phase,
            framework=ComplianceFramework.ISO_27035,
            controls=requirements.get("requirements", []),
            documentation_required=requirements.get("documentation", []),
        )

    def get_controls_for_phase(
        self, phase: str, standard: str = "iso27001"
    ) -> List[ComplianceControl]:
        """
        Get ISO controls relevant to an IR phase.

        Args:
            phase: IR phase name
            standard: "iso27001" or "iso27035"

        Returns:
            List of ComplianceControl objects
        """
        if standard == "iso27001":
            phase_data = self.ISO27001_PHASE_MAPPING.get(phase, {})
            controls_data = phase_data.get("controls", [])
            framework = ComplianceFramework.ISO_27001

            controls = []
            for ctrl in controls_data:
                control = ComplianceControl(
                    framework=framework,
                    control_id=ctrl["id"],
                    control_name=ctrl["name"],
                    description=ctrl.get("description", ""),
                )
                controls.append(control)
            return controls

        else:  # iso27035
            phase_data = self.ISO27001_PHASE_MAPPING.get(phase, {})
            iso27035_phase = phase_data.get("iso27035_phase")

            if not iso27035_phase:
                return []

            requirements = self.ISO27035_REQUIREMENTS.get(iso27035_phase, {})
            req_list = requirements.get("requirements", [])

            controls = []
            for i, req in enumerate(req_list):
                control = ComplianceControl(
                    framework=ComplianceFramework.ISO_27035,
                    control_id=f"27035-{iso27035_phase.value}-{i+1}",
                    control_name=req,
                    description=f"ISO 27035 requirement: {req}",
                )
                controls.append(control)
            return controls

    def get_all_controls(self, standard: str = "iso27001") -> List[ComplianceControl]:
        """Get all defined ISO controls."""
        all_controls = []
        seen_ids = set()
        
        for phase_data in self.ISO27001_PHASE_MAPPING.values():
            if standard == "iso27001":
                for ctrl in phase_data.get("controls", []):
                    if ctrl["id"] not in seen_ids:
                        seen_ids.add(ctrl["id"])
                        all_controls.append(ComplianceControl(
                            framework=ComplianceFramework.ISO_27001,
                            control_id=ctrl["id"],
                            control_name=ctrl["name"],
                            description=ctrl.get("description", ""),
                        ))
        
        return all_controls

    def validate_phase_compliance(
        self,
        phase: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        documentation_provided: List[str],
        standard: str = "iso27001",
        operator: str = "",
    ) -> List[ComplianceCheck]:
        """
        Validate compliance for a phase against ISO requirements.

        Args:
            phase: IR phase name
            completed_actions: Completed checklist items
            evidence_collected: Evidence entry descriptions
            documentation_provided: Documentation items provided
            standard: "iso27001" or "iso27035"
            operator: Operator name

        Returns:
            List of ComplianceCheck results
        """
        controls = self.get_controls_for_phase(phase, standard)
        phase_data = self.ISO27001_PHASE_MAPPING.get(phase, {})
        mandatory_controls = phase_data.get("mandatory", [])

        checks = []
        for control in controls:
            status = self._evaluate_control_compliance(
                control.control_id,
                completed_actions,
                evidence_collected,
                documentation_provided,
                standard,
            )

            check = ComplianceCheck(
                framework=control.framework,
                control_id=control.control_id,
                control_name=control.control_name,
                status=status,
                evidence_required=self._get_evidence_requirements(
                    control.control_id, phase, standard
                ),
                recommendation=self._get_recommendation(control.control_id, status),
                remediation_priority="high" if control.control_id in mandatory_controls else "medium",
                evaluated_by=operator,
                checked_by=operator,
            )

            if status == ComplianceStatus.GAP:
                check.gap_description = self._get_gap_description(
                    control.control_id, standard
                )

            checks.append(check)

        return checks

    def get_compliance_requirements(self, phase: str) -> Dict[str, Any]:
        """
        Get all compliance requirements for a phase.

        Args:
            phase: IR phase name

        Returns:
            Dictionary with ISO 27001 and 27035 requirements
        """
        iso27001_mapping = self.get_iso27001_mapping_for_phase(phase)
        iso27035_mapping = self.get_iso27035_mapping_for_phase(phase)

        return {
            "phase": phase,
            "iso_27001_controls": iso27001_mapping.controls,
            "iso_27001_mandatory": iso27001_mapping.mandatory_controls,
            "iso_27035_requirements": iso27035_mapping.controls,
            "documentation_required": self.DOCUMENTATION_REQUIREMENTS.get(phase, []),
        }

    def _evaluate_control_compliance(
        self,
        control_id: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        documentation_provided: List[str],
        standard: str,
    ) -> ComplianceStatus:
        """Evaluate compliance status for a control."""
        # Combine all provided evidence
        all_evidence = (
            " ".join(completed_actions) + " " +
            " ".join(evidence_collected) + " " +
            " ".join(documentation_provided)
        ).lower()

        # Keywords for each control
        keywords = {
            # ISO 27001
            "A.5.24": ["plan", "procedure", "incident management"],
            "A.5.25": ["assess", "classif", "event"],
            "A.5.26": ["response", "respond", "procedure"],
            "A.5.27": ["lesson", "learn", "improve"],
            "A.5.28": ["evidence", "collect", "preserv"],
            "A.5.29": ["continuity", "disruption"],
            "A.5.30": ["readiness", "business continuity"],
            "A.5.35": ["review", "independent"],
            "A.5.36": ["compliance", "policy"],
            "A.8.7": ["malware", "protect", "antivirus"],
            "A.8.8": ["vulnerabilit", "patch"],
            "A.8.9": ["configuration", "config"],
            "A.8.12": ["leakage", "dlp", "exfiltration"],
            "A.8.13": ["backup", "restore"],
            "A.8.14": ["redundancy", "failover"],
            "A.8.15": ["log", "audit"],
            "A.8.16": ["monitor", "anomal"],
            "A.8.20": ["network", "secur"],
            "A.8.21": ["network service", "security service"],
            "A.8.22": ["segregat", "isolat"],
        }

        control_keywords = keywords.get(control_id, [])
        if not control_keywords:
            # For ISO 27035 requirements, use the requirement text
            return ComplianceStatus.NOT_EVALUATED

        matches = sum(1 for kw in control_keywords if kw in all_evidence)

        if matches >= len(control_keywords):
            return ComplianceStatus.COMPLIANT
        elif matches > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.GAP

    def _get_evidence_requirements(
        self, control_id: str, phase: str, standard: str
    ) -> List[str]:
        """Get evidence requirements for a control."""
        return self.DOCUMENTATION_REQUIREMENTS.get(phase, [])[:5]

    def _get_recommendation(
        self, control_id: str, status: ComplianceStatus
    ) -> Optional[str]:
        """Get recommendation based on status."""
        if status == ComplianceStatus.COMPLIANT:
            return None

        recommendations = {
            "A.5.24": "Ensure incident management procedures are documented and communicated.",
            "A.5.25": "Document the incident classification and assessment process.",
            "A.5.26": "Follow documented incident response procedures.",
            "A.5.27": "Conduct and document post-incident review and lessons learned.",
            "A.5.28": "Implement proper evidence collection and chain of custody procedures.",
            "A.5.29": "Maintain information security during incident response.",
            "A.5.30": "Ensure ICT recovery capabilities are available and tested.",
            "A.5.35": "Schedule independent security review.",
            "A.5.36": "Verify compliance with security policies.",
            "A.8.7": "Implement and document malware protection measures.",
            "A.8.8": "Apply security patches and document vulnerability management.",
            "A.8.9": "Review and document configuration management.",
            "A.8.13": "Verify backup availability and document restoration capability.",
            "A.8.15": "Ensure logging is enabled and log data is preserved.",
            "A.8.16": "Document monitoring activities and anomaly detection.",
            "A.8.22": "Document network isolation and segregation measures.",
        }

        return recommendations.get(control_id, f"Review and address requirements for {control_id}")

    def _get_gap_description(self, control_id: str, standard: str) -> str:
        """Get description of compliance gap."""
        return f"Control {control_id} requirements not fully documented or implemented."

    def get_framework_info(self, standard: str = "iso27001") -> Dict[str, Any]:
        """Get information about ISO framework."""
        if standard == "iso27001":
            return {
                "id": "iso27001",
                "name": "ISO/IEC 27001:2022",
                "organization": "International Organization for Standardization",
                "version": "2022",
                "description": "Information Security Management Systems - Requirements",
                "url": "https://www.iso.org/standard/27001",
                "controls_count": len(self.get_all_controls("iso27001")),
                "annex_a_controls": 93,
            }
        else:
            return {
                "id": "iso27035",
                "name": "ISO/IEC 27035",
                "organization": "International Organization for Standardization",
                "version": "2023",
                "description": "Information Security Incident Management",
                "url": "https://www.iso.org/standard/78973.html",
                "parts": [
                    "27035-1: Principles and process",
                    "27035-2: Guidelines to plan and prepare",
                    "27035-3: Guidelines for operations",
                ],
            }

    def export_compliance_matrix(
        self, phases: Optional[List[str]] = None, format: str = "markdown"
    ) -> str:
        """
        Export complete ISO compliance matrix.

        Args:
            phases: Specific phases to include (None = all)
            format: "markdown" or "json"

        Returns:
            Formatted compliance matrix
        """
        if phases is None:
            phases = list(self.ISO27001_PHASE_MAPPING.keys())

        if format == "json":
            matrix = {}
            for phase in phases:
                matrix[phase] = self.get_compliance_requirements(phase)
            return json.dumps(matrix, indent=2)

        # Markdown format
        lines = [
            "# ISO Compliance Matrix for Incident Response",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
        ]

        for phase in phases:
            reqs = self.get_compliance_requirements(phase)
            lines.extend([
                f"## Phase: {phase.title().replace('_', ' ')}",
                "",
                "### ISO 27001:2022 Controls",
                "",
            ])

            for control_id in reqs["iso_27001_controls"]:
                mandatory = "**[MANDATORY]**" if control_id in reqs["iso_27001_mandatory"] else ""
                lines.append(f"- {control_id} {mandatory}")

            lines.extend([
                "",
                "### Documentation Required",
                "",
            ])

            for doc in reqs["documentation_required"]:
                lines.append(f"- {doc}")

            lines.append("")

        return "\n".join(lines)
