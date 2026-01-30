"""
BSI IT-Grundschutz Integration.

Integrates with BSI's Stand-der-Technik-Bibliothek for German compliance requirements.
Repository: https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek

Supports:
- IT-Grundschutz controls
- Grundschutz++ (2026) OSCAL format
- Phase-to-control mapping for IR
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from src.integrations.models import (
    ComplianceFramework,
    ComplianceControl,
    ComplianceCheck,
    ComplianceStatus,
    PhaseComplianceMapping,
)

logger = logging.getLogger(__name__)


class BSIIntegration:
    """
    Integration with BSI IT-Grundschutz via Stand-der-Technik-Bibliothek.

    The BSI provides security controls in OSCAL/JSON format through their
    GitHub repository. This class fetches and parses those controls for
    compliance validation during incident response.

    Features:
    - Fetch controls from BSI GitHub repository
    - Cache controls locally for offline use
    - Map IR phases to relevant BSI controls
    - Validate incident actions against BSI requirements
    """

    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/main"
    GITHUB_API_BASE = "https://api.github.com/repos/BSI-Bund/Stand-der-Technik-Bibliothek"

    # IT-Grundschutz control families relevant to Incident Response
    IR_RELEVANT_FAMILIES = {
        "DER": "Detektion und Reaktion",  # Detection and Response
        "OPS": "Betrieb",  # Operations
        "ORP": "Organisation und Personal",  # Organization and Personnel
        "CON": "Konzeption und Planung",  # Concept and Planning
        "INF": "Infrastruktur",  # Infrastructure
        "SYS": "Systeme",  # Systems
    }

    # Mapping of IR phases to BSI control modules
    PHASE_TO_CONTROLS = {
        "detection": {
            "controls": [
                "DER.1",      # Detektion von sicherheitsrelevanten Ereignissen
                "OPS.1.1.A1", # Dokumentation von IT-Systemen
                "OPS.1.1.A3", # Planung des IT-Betriebs
            ],
            "mandatory": ["DER.1"],
            "description": "Detection of security-relevant events",
        },
        "analysis": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen
                "DER.2.2",    # Vorsorge für die IT-Forensik
                "DER.1.A5",   # Auswertung von Protokolldaten
            ],
            "mandatory": ["DER.2.1", "DER.2.2"],
            "description": "Incident handling and forensic preparation",
        },
        "containment": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen
                "DER.2.3",    # Bereinigung von Sicherheitsvorfällen
                "OPS.1.1.A12", # Regelungen zur Wartung
                "NET.1.1",    # Netzarchitektur
            ],
            "mandatory": ["DER.2.1"],
            "description": "Incident containment and network isolation",
        },
        "eradication": {
            "controls": [
                "DER.2.3",    # Bereinigung weitreichender Sicherheitsvorfälle
                "OPS.1.1.A6", # Schutz vor Schadprogrammen
                "SYS.1.1",    # Allgemeiner Server
            ],
            "mandatory": ["DER.2.3"],
            "description": "Cleanup of security incidents",
        },
        "recovery": {
            "controls": [
                "DER.4",      # Notfallmanagement
                "CON.3",      # Datensicherungskonzept
                "OPS.1.1.A7", # Datensicherung
            ],
            "mandatory": ["DER.4", "CON.3"],
            "description": "Emergency management and data backup",
        },
        "post_incident": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen (Lessons Learned)
                "ORP.1",      # Organisation
                "ORP.3",      # Sensibilisierung und Schulung
            ],
            "mandatory": ["DER.2.1"],
            "description": "Lessons learned and organizational improvement",
        },
    }

    def __init__(self, cache_dir: Optional[Path] = None, offline_mode: bool = False):
        """
        Initialize BSI integration.

        Args:
            cache_dir: Directory for caching downloaded controls
            offline_mode: If True, only use cached data (no network requests)
        """
        self.cache_dir = cache_dir or Path.home() / ".cyberops_companion" / "bsi_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode
        self.controls_cache: Dict[str, ComplianceControl] = {}
        self._catalog_data: Optional[Dict] = None

    def _get_cache_path(self, identifier: str) -> Path:
        """Get cache file path for an identifier."""
        safe_name = hashlib.md5(identifier.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def _load_from_cache(self, identifier: str) -> Optional[Dict]:
        """Load data from cache if available."""
        cache_path = self._get_cache_path(identifier)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.debug(f"Loaded from cache: {identifier}")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Cache read error for {identifier}: {e}")
        return None

    def _save_to_cache(self, identifier: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(identifier)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved to cache: {identifier}")
        except IOError as e:
            logger.warning(f"Cache write error for {identifier}: {e}")

    def fetch_catalog(self, catalog_path: str = "Quellkataloge") -> Optional[Dict]:
        """
        Fetch BSI catalog from GitHub or cache.

        Args:
            catalog_path: Path within the repository

        Returns:
            Catalog data as dictionary, or None if unavailable
        """
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available, using cache only")
            return self._load_from_cache(catalog_path)

        if self.offline_mode:
            return self._load_from_cache(catalog_path)

        # Try to fetch from GitHub
        try:
            # First, list available files
            api_url = f"{self.GITHUB_API_BASE}/contents/{catalog_path}"
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()

            files = response.json()
            catalog_data = {"files": [], "controls": []}

            for file_info in files:
                if file_info.get("name", "").endswith(".json"):
                    file_url = file_info.get("download_url")
                    if file_url:
                        file_response = requests.get(file_url, timeout=30)
                        if file_response.ok:
                            catalog_data["files"].append({
                                "name": file_info["name"],
                                "data": file_response.json()
                            })

            self._save_to_cache(catalog_path, catalog_data)
            self._catalog_data = catalog_data
            return catalog_data

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch BSI catalog: {e}")
            return self._load_from_cache(catalog_path)

    def get_controls_for_phase(self, phase: str) -> List[ComplianceControl]:
        """
        Get BSI controls relevant to an IR phase.

        Args:
            phase: IR phase name (detection, analysis, containment, etc.)

        Returns:
            List of ComplianceControl objects for the phase
        """
        phase_mapping = self.PHASE_TO_CONTROLS.get(phase, {})
        control_ids = phase_mapping.get("controls", [])

        controls = []
        for control_id in control_ids:
            control = ComplianceControl(
                framework=ComplianceFramework.BSI_GRUNDSCHUTZ,
                control_id=control_id,
                control_name=self._get_control_name(control_id),
                control_family=control_id.split(".")[0] if "." in control_id else control_id,
                description=self._get_control_description(control_id),
            )
            controls.append(control)

        return controls

    def get_phase_mapping(self, phase: str) -> PhaseComplianceMapping:
        """
        Get complete phase-to-compliance mapping.

        Args:
            phase: IR phase name

        Returns:
            PhaseComplianceMapping with all relevant information
        """
        phase_data = self.PHASE_TO_CONTROLS.get(phase, {})

        return PhaseComplianceMapping(
            phase=phase,
            framework=ComplianceFramework.BSI_GRUNDSCHUTZ,
            controls=phase_data.get("controls", []),
            mandatory_controls=phase_data.get("mandatory", []),
            documentation_required=self._get_documentation_requirements(phase),
        )

    def validate_phase_compliance(
        self,
        phase: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        operator: str = "",
    ) -> List[ComplianceCheck]:
        """
        Validate compliance for a phase based on completed actions.

        Args:
            phase: IR phase name
            completed_actions: List of completed checklist item IDs
            evidence_collected: List of evidence entry descriptions
            operator: Name of the operator

        Returns:
            List of ComplianceCheck results
        """
        controls = self.get_controls_for_phase(phase)
        phase_mapping = self.PHASE_TO_CONTROLS.get(phase, {})
        mandatory_controls = phase_mapping.get("mandatory", [])

        checks = []
        for control in controls:
            # Determine status based on completed actions
            status = self._evaluate_control_compliance(
                control.control_id,
                completed_actions,
                evidence_collected,
            )

            check = ComplianceCheck(
                framework=ComplianceFramework.BSI_GRUNDSCHUTZ,
                control_id=control.control_id,
                control_name=control.control_name,
                status=status,
                evidence_required=self._get_evidence_requirements(control.control_id),
                evidence_provided=self._match_evidence(
                    control.control_id, evidence_collected
                ),
                recommendation=self._get_recommendation(control.control_id, status),
                remediation_priority="high" if control.control_id in mandatory_controls else "medium",
                evaluated_by=operator,
            )

            if status == ComplianceStatus.GAP:
                check.gap_description = self._get_gap_description(
                    control.control_id, completed_actions
                )

            checks.append(check)

        return checks

    def _get_control_name(self, control_id: str) -> str:
        """Get human-readable name for a control."""
        control_names = {
            "DER.1": "Detektion von sicherheitsrelevanten Ereignissen",
            "DER.2.1": "Behandlung von Sicherheitsvorfällen",
            "DER.2.2": "Vorsorge für die IT-Forensik",
            "DER.2.3": "Bereinigung weitreichender Sicherheitsvorfälle",
            "DER.4": "Notfallmanagement",
            "OPS.1.1.A1": "Dokumentation von IT-Systemen",
            "OPS.1.1.A3": "Planung des IT-Betriebs",
            "OPS.1.1.A6": "Schutz vor Schadprogrammen",
            "OPS.1.1.A7": "Datensicherung",
            "OPS.1.1.A12": "Regelungen zur Wartung",
            "ORP.1": "Organisation",
            "ORP.3": "Sensibilisierung und Schulung",
            "CON.3": "Datensicherungskonzept",
            "NET.1.1": "Netzarchitektur und -design",
            "SYS.1.1": "Allgemeiner Server",
            "DER.1.A5": "Auswertung von Protokolldaten",
        }
        return control_names.get(control_id, f"BSI Control {control_id}")

    def _get_control_description(self, control_id: str) -> str:
        """Get description for a control."""
        descriptions = {
            "DER.1": "Establishes requirements for detecting security-relevant events through logging, monitoring, and alerting.",
            "DER.2.1": "Defines the process for handling security incidents including reporting, classification, and response.",
            "DER.2.2": "Ensures forensic readiness through evidence preservation and chain of custody procedures.",
            "DER.2.3": "Covers cleanup procedures for widespread security incidents including malware removal.",
            "DER.4": "Emergency management procedures for maintaining business continuity during incidents.",
            "CON.3": "Data backup concept ensuring recovery capability after incidents.",
        }
        return descriptions.get(control_id, "")

    def _get_evidence_requirements(self, control_id: str) -> List[str]:
        """Get evidence requirements for a control."""
        requirements = {
            "DER.1": [
                "Log entries showing detection timestamp",
                "Alert notification records",
                "Initial triage documentation",
            ],
            "DER.2.1": [
                "Incident report form",
                "Timeline of response actions",
                "Communication logs",
            ],
            "DER.2.2": [
                "Memory capture records",
                "Disk image hashes",
                "Chain of custody forms",
            ],
            "DER.2.3": [
                "Malware removal verification",
                "System scan results",
                "Persistence mechanism removal logs",
            ],
            "DER.4": [
                "Recovery plan execution records",
                "System restoration verification",
                "Business continuity status reports",
            ],
            "CON.3": [
                "Backup verification records",
                "Restoration test results",
                "Backup integrity checks",
            ],
        }
        return requirements.get(control_id, ["Documentation of actions taken"])

    def _get_documentation_requirements(self, phase: str) -> List[str]:
        """Get documentation requirements for a phase."""
        docs = {
            "detection": [
                "Initial alert/report documentation",
                "Affected systems identification",
                "Timestamp of detection (UTC)",
                "Initial classification",
            ],
            "analysis": [
                "Scope assessment document",
                "IOC collection records",
                "Memory/disk capture verification",
                "Ransomware variant identification",
            ],
            "containment": [
                "Network isolation records",
                "Blocked indicators list",
                "Disabled accounts log",
                "Evidence preservation verification",
            ],
            "eradication": [
                "Persistence mechanism removal log",
                "Malware removal verification",
                "Credential reset records",
                "Patch application records",
            ],
            "recovery": [
                "Backup verification records",
                "System restoration log",
                "Security patch verification",
                "Enhanced monitoring confirmation",
            ],
            "post_incident": [
                "Incident timeline (complete)",
                "Root cause analysis",
                "Lessons learned document",
                "Improvement recommendations",
            ],
        }
        return docs.get(phase, [])

    def _evaluate_control_compliance(
        self,
        control_id: str,
        completed_actions: List[str],
        evidence_collected: List[str],
    ) -> ComplianceStatus:
        """Evaluate compliance status for a control."""
        # Map checklist items to controls
        control_to_checklist = {
            "DER.1": ["DET-001", "DET-002", "DET-003"],
            "DER.2.1": ["DET-004", "DET-005", "DET-006"],
            "DER.2.2": ["ANA-001", "ANA-002"],
            "DER.2.3": ["ERA-001", "ERA-002", "ERA-003"],
            "DER.4": ["REC-001", "REC-002", "REC-003"],
            "CON.3": ["REC-001", "REC-004"],
        }

        required_items = control_to_checklist.get(control_id, [])
        if not required_items:
            return ComplianceStatus.NOT_EVALUATED

        completed_required = [
            item for item in required_items if item in completed_actions
        ]

        if len(completed_required) == len(required_items):
            return ComplianceStatus.COMPLIANT
        elif len(completed_required) > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.GAP

    def _match_evidence(
        self, control_id: str, evidence_collected: List[str]
    ) -> List[str]:
        """Match collected evidence to a control's requirements."""
        # Simple keyword matching for demonstration
        keywords = {
            "DER.1": ["alert", "detection", "log", "monitor"],
            "DER.2.1": ["incident", "report", "response", "timeline"],
            "DER.2.2": ["memory", "forensic", "evidence", "capture", "image"],
            "DER.2.3": ["cleanup", "removal", "malware", "persistence"],
            "DER.4": ["recovery", "backup", "restore", "continuity"],
        }

        control_keywords = keywords.get(control_id, [])
        matched = []

        for evidence in evidence_collected:
            evidence_lower = evidence.lower()
            if any(kw in evidence_lower for kw in control_keywords):
                matched.append(evidence)

        return matched

    def _get_recommendation(
        self, control_id: str, status: ComplianceStatus
    ) -> Optional[str]:
        """Get recommendation based on control and status."""
        if status == ComplianceStatus.COMPLIANT:
            return None

        recommendations = {
            "DER.1": "Ensure all detection activities are documented with timestamps and alert sources.",
            "DER.2.1": "Complete incident handling procedures including proper classification and escalation.",
            "DER.2.2": "Capture volatile evidence (memory) before any containment actions that may alter system state.",
            "DER.2.3": "Identify and document all persistence mechanisms before removal.",
            "DER.4": "Verify backup integrity and test restoration procedures before recovery.",
            "CON.3": "Ensure backup verification is documented and recovery capability is tested.",
        }

        return recommendations.get(control_id)

    def _get_gap_description(
        self, control_id: str, completed_actions: List[str]
    ) -> str:
        """Get description of compliance gap."""
        return f"Control {control_id} requirements not fully satisfied. Review mandatory checklist items."

    def get_grundschutz_plus_info(self) -> Dict[str, Any]:
        """
        Get information about Grundschutz++ (2026) format.

        Returns:
            Information about the upcoming OSCAL-based format
        """
        return {
            "name": "IT-Grundschutz++",
            "effective_date": "2026-01-01",
            "format": "OSCAL/JSON",
            "repository": "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek",
            "features": [
                "Machine-readable OSCAL format",
                "JSON and XML representations",
                "Automated compliance checking support",
                "Integration with security tools",
            ],
            "migration_notes": [
                "Current IT-Grundschutz mappings remain valid",
                "OSCAL format enables automated validation",
                "New control IDs may be introduced",
            ],
        }

    def export_compliance_summary(
        self, checks: List[ComplianceCheck], format: str = "markdown"
    ) -> str:
        """
        Export compliance check results.

        Args:
            checks: List of compliance checks
            format: Output format ("markdown" or "json")

        Returns:
            Formatted compliance summary
        """
        if format == "json":
            return json.dumps(
                [check.model_dump() for check in checks],
                indent=2,
                default=str,
            )

        # Markdown format
        lines = [
            "# BSI IT-Grundschutz Compliance Summary",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Control Status",
            "",
            "| Control ID | Name | Status | Priority |",
            "|------------|------|--------|----------|",
        ]

        for check in checks:
            status_icon = {
                ComplianceStatus.COMPLIANT: "✅",
                ComplianceStatus.PARTIAL: "⚠️",
                ComplianceStatus.GAP: "❌",
                ComplianceStatus.NOT_EVALUATED: "⏸️",
            }.get(check.status, "❓")

            lines.append(
                f"| {check.control_id} | {check.control_name} | "
                f"{status_icon} {check.status.value} | {check.remediation_priority or 'N/A'} |"
            )

        # Add gaps section
        gaps = [c for c in checks if c.status == ComplianceStatus.GAP]
        if gaps:
            lines.extend([
                "",
                "## Identified Gaps",
                "",
            ])
            for gap in gaps:
                lines.append(f"### {gap.control_id}: {gap.control_name}")
                if gap.gap_description:
                    lines.append(f"**Gap:** {gap.gap_description}")
                if gap.recommendation:
                    lines.append(f"**Recommendation:** {gap.recommendation}")
                lines.append("")

        return "\n".join(lines)
