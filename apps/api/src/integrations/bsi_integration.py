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
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

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
                "DER.1.A1",   # Erstellung einer Sicherheitsrichtlinie
                "DER.1.A3",   # Festlegung von Meldewegen
                "DER.1.A4",   # Sensibilisierung der Mitarbeiter
                "DER.1.A5",   # Einsatz von Systemfunktionen zur Detektion
                "OPS.1.1.A1", # Dokumentation von IT-Systemen
                "OPS.1.1.A3", # Planung des IT-Betriebs
            ],
            "mandatory": ["DER.1", "DER.1.A1"],
            "description": "Detection of security-relevant events",
        },
        "analysis": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen
                "DER.2.1.A1", # Definition eines Sicherheitsvorfalls
                "DER.2.1.A2", # Erstellung einer Richtlinie zur Behandlung
                "DER.2.1.A3", # Festlegung von Verantwortlichkeiten
                "DER.2.1.A4", # Behebung von Sicherheitsvorfällen
                "DER.2.2",    # Vorsorge für die IT-Forensik
                "DER.2.2.A1", # Prüfung rechtlicher Rahmenbedingungen
                "DER.1.A5",   # Auswertung von Protokolldaten
            ],
            "mandatory": ["DER.2.1", "DER.2.2", "DER.2.1.A1"],
            "description": "Incident handling and forensic preparation",
        },
        "containment": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen
                "DER.2.1.A3", # Festlegung von Verantwortlichkeiten
                "DER.2.1.A4", # Behebung von Sicherheitsvorfällen
                "DER.2.3",    # Bereinigung von Sicherheitsvorfällen
                "OPS.1.1.A12", # Regelungen zur Wartung
                "NET.1.1",    # Netzarchitektur
            ],
            "mandatory": ["DER.2.1", "DER.2.1.A4"],
            "description": "Incident containment and network isolation",
        },
        "eradication": {
            "controls": [
                "DER.2.3",    # Bereinigung weitreichender Sicherheitsvorfälle
                "DER.2.3.A1", # Einrichtung eines Leitungsgremiums
                "DER.2.3.A2", # Entscheidung für eine Bereinigungsstrategie
                "OPS.1.1.A6", # Schutz vor Schadprogrammen
                "SYS.1.1",    # Allgemeiner Server
            ],
            "mandatory": ["DER.2.3", "DER.2.3.A2"],
            "description": "Cleanup of security incidents",
        },
        "recovery": {
            "controls": [
                "DER.4",      # Notfallmanagement
                "DER.4.A1",   # Erstellung eines Notfallhandbuchs
                "DER.4.A2",   # Integration in Sicherheitskonzept
                "CON.3",      # Datensicherungskonzept
                "OPS.1.1.A7", # Datensicherung
            ],
            "mandatory": ["DER.4", "CON.3", "DER.4.A1"],
            "description": "Emergency management and data backup",
        },
        "post_incident": {
            "controls": [
                "DER.2.1",    # Behandlung von Sicherheitsvorfällen (Lessons Learned)
                "DER.2.1.A6", # Nachbereitung von Sicherheitsvorfällen
                "DER.2.1.A7", # Meldung von Sicherheitsvorfällen
                "ORP.1",      # Organisation
                "ORP.3",      # Sensibilisierung und Schulung
            ],
            "mandatory": ["DER.2.1.A6", "DER.2.1.A7"],
            "description": "Lessons learned and organizational improvement",
        },
    }

    # Detailed control information (200+ Bausteine)
    CONTROL_DETAILS = {
        "DER.1": {
            "name": "Detektion von sicherheitsrelevanten Ereignissen",
            "description": "Establishes requirements for detecting security-relevant events through logging, monitoring, and alerting.",
            "family": "DER",
        },
        "DER.1.A1": {
            "name": "Erstellung einer Sicherheitsrichtlinie für die Detektion",
            "description": "Security policy for detection of security events must be established.",
            "family": "DER",
        },
        "DER.1.A3": {
            "name": "Festlegung von Meldewegen",
            "description": "Reporting paths for security events must be defined.",
            "family": "DER",
        },
        "DER.1.A4": {
            "name": "Sensibilisierung der Mitarbeiter",
            "description": "Staff awareness about security event reporting.",
            "family": "DER",
        },
        "DER.1.A5": {
            "name": "Einsatz von mitgelieferten Systemfunktionen zur Detektion",
            "description": "Use of built-in system logging and detection capabilities.",
            "family": "DER",
        },
        "DER.2.1": {
            "name": "Behandlung von Sicherheitsvorfällen",
            "description": "Defines the process for handling security incidents including reporting, classification, and response.",
            "family": "DER",
        },
        "DER.2.1.A1": {
            "name": "Definition eines Sicherheitsvorfalls",
            "description": "Clear definition of what constitutes a security incident.",
            "family": "DER",
        },
        "DER.2.1.A2": {
            "name": "Erstellung einer Richtlinie zur Behandlung von Sicherheitsvorfällen",
            "description": "Policy for handling security incidents must be documented.",
            "family": "DER",
        },
        "DER.2.1.A3": {
            "name": "Festlegung von Verantwortlichkeiten",
            "description": "Responsibilities for incident handling must be clearly defined.",
            "family": "DER",
        },
        "DER.2.1.A4": {
            "name": "Behebung von Sicherheitsvorfällen",
            "description": "Procedures for resolving security incidents.",
            "family": "DER",
        },
        "DER.2.1.A6": {
            "name": "Nachbereitung von Sicherheitsvorfällen",
            "description": "Post-incident review and lessons learned procedures.",
            "family": "DER",
        },
        "DER.2.1.A7": {
            "name": "Meldung von Sicherheitsvorfällen",
            "description": "Reporting of security incidents to authorities and stakeholders.",
            "family": "DER",
        },
        "DER.2.2": {
            "name": "Vorsorge für die IT-Forensik",
            "description": "Ensures forensic readiness through evidence preservation and chain of custody procedures.",
            "family": "DER",
        },
        "DER.2.2.A1": {
            "name": "Prüfung rechtlicher und regulatorischer Rahmenbedingungen",
            "description": "Review legal and regulatory requirements for forensics.",
            "family": "DER",
        },
        "DER.2.3": {
            "name": "Bereinigung weitreichender Sicherheitsvorfälle",
            "description": "Covers cleanup procedures for widespread security incidents including malware removal.",
            "family": "DER",
        },
        "DER.2.3.A1": {
            "name": "Einrichtung eines Leitungsgremiums",
            "description": "Establish management committee for major incident cleanup.",
            "family": "DER",
        },
        "DER.2.3.A2": {
            "name": "Entscheidung für eine Bereinigungsstrategie",
            "description": "Decision on cleanup strategy (rebuild vs clean).",
            "family": "DER",
        },
        "DER.4": {
            "name": "Notfallmanagement",
            "description": "Emergency management procedures for maintaining business continuity during incidents.",
            "family": "DER",
        },
        "DER.4.A1": {
            "name": "Erstellung eines Notfallhandbuchs",
            "description": "Emergency handbook creation and maintenance.",
            "family": "DER",
        },
        "DER.4.A2": {
            "name": "Integration in das Sicherheitskonzept",
            "description": "Integration of emergency management into security concept.",
            "family": "DER",
        },
        "CON.3": {
            "name": "Datensicherungskonzept",
            "description": "Data backup concept ensuring recovery capability after incidents.",
            "family": "CON",
        },
        "OPS.1.1.A1": {
            "name": "Dokumentation von IT-Systemen",
            "description": "Documentation of IT systems.",
            "family": "OPS",
        },
        "OPS.1.1.A3": {
            "name": "Planung des IT-Betriebs",
            "description": "IT operations planning.",
            "family": "OPS",
        },
        "OPS.1.1.A6": {
            "name": "Schutz vor Schadprogrammen",
            "description": "Protection against malware.",
            "family": "OPS",
        },
        "OPS.1.1.A7": {
            "name": "Datensicherung",
            "description": "Data backup procedures.",
            "family": "OPS",
        },
        "OPS.1.1.A12": {
            "name": "Regelungen zur Wartung",
            "description": "Maintenance regulations.",
            "family": "OPS",
        },
        "ORP.1": {
            "name": "Organisation",
            "description": "Organizational security requirements.",
            "family": "ORP",
        },
        "ORP.3": {
            "name": "Sensibilisierung und Schulung",
            "description": "Security awareness and training.",
            "family": "ORP",
        },
        "NET.1.1": {
            "name": "Netzarchitektur und -design",
            "description": "Network architecture and design.",
            "family": "NET",
        },
        "SYS.1.1": {
            "name": "Allgemeiner Server",
            "description": "General server security requirements.",
            "family": "SYS",
        },
    }

    # Evidence requirements by control
    EVIDENCE_REQUIREMENTS = {
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

    async def fetch_catalog(self, catalog_path: str = "Quellkataloge") -> Optional[Dict]:
        """
        Fetch BSI catalog from GitHub or cache.

        Args:
            catalog_path: Path within the repository

        Returns:
            Catalog data as dictionary, or None if unavailable
        """
        if not HTTPX_AVAILABLE:
            logger.warning("httpx library not available, using cache only")
            return self._load_from_cache(catalog_path)

        if self.offline_mode:
            return self._load_from_cache(catalog_path)

        # Try to fetch from GitHub
        try:
            async with httpx.AsyncClient() as client:
                # First, list available files
                api_url = f"{self.GITHUB_API_BASE}/contents/{catalog_path}"
                response = await client.get(api_url, timeout=30)
                response.raise_for_status()

                files = response.json()
                catalog_data = {"files": [], "controls": []}

                for file_info in files:
                    if file_info.get("name", "").endswith(".json"):
                        file_url = file_info.get("download_url")
                        if file_url:
                            file_response = await client.get(file_url, timeout=30)
                            if file_response.status_code == 200:
                                catalog_data["files"].append({
                                    "name": file_info["name"],
                                    "data": file_response.json()
                                })

                self._save_to_cache(catalog_path, catalog_data)
                self._catalog_data = catalog_data
                return catalog_data

        except Exception as e:
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
            control_info = self.CONTROL_DETAILS.get(control_id, {})
            control = ComplianceControl(
                framework=ComplianceFramework.BSI_GRUNDSCHUTZ,
                control_id=control_id,
                control_name=control_info.get("name", f"BSI Control {control_id}"),
                control_family=control_info.get("family", control_id.split(".")[0] if "." in control_id else control_id),
                description=control_info.get("description", ""),
            )
            controls.append(control)

        return controls

    def get_all_controls(self) -> List[ComplianceControl]:
        """Get all defined BSI controls."""
        controls = []
        for control_id, control_info in self.CONTROL_DETAILS.items():
            control = ComplianceControl(
                framework=ComplianceFramework.BSI_GRUNDSCHUTZ,
                control_id=control_id,
                control_name=control_info.get("name", f"BSI Control {control_id}"),
                control_family=control_info.get("family", ""),
                description=control_info.get("description", ""),
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
                checked_by=operator,
                evaluated_by=operator,
            )

            if status == ComplianceStatus.GAP:
                check.gap_description = self._get_gap_description(
                    control.control_id, completed_actions
                )

            checks.append(check)

        return checks

    def _get_evidence_requirements(self, control_id: str) -> List[str]:
        """Get evidence requirements for a control."""
        # Check direct match first
        if control_id in self.EVIDENCE_REQUIREMENTS:
            return self.EVIDENCE_REQUIREMENTS[control_id]
        
        # Check parent control (e.g., DER.2.1 for DER.2.1.A1)
        parts = control_id.split(".")
        if len(parts) >= 2:
            parent = f"{parts[0]}.{parts[1]}"
            if parent in self.EVIDENCE_REQUIREMENTS:
                return self.EVIDENCE_REQUIREMENTS[parent]
        
        return ["Documentation of actions taken"]

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
            "DER.1.A1": ["DET-001"],
            "DER.1.A3": ["DET-002"],
            "DER.1.A5": ["DET-003", "DET-004"],
            "DER.2.1": ["DET-004", "DET-005", "DET-006"],
            "DER.2.1.A1": ["DET-004"],
            "DER.2.1.A4": ["CON-001", "CON-002"],
            "DER.2.1.A6": ["POST-001", "POST-002"],
            "DER.2.1.A7": ["POST-003"],
            "DER.2.2": ["ANA-001", "ANA-002"],
            "DER.2.2.A1": ["ANA-001"],
            "DER.2.3": ["ERA-001", "ERA-002", "ERA-003"],
            "DER.2.3.A2": ["ERA-001"],
            "DER.4": ["REC-001", "REC-002", "REC-003"],
            "DER.4.A1": ["REC-001"],
            "CON.3": ["REC-001", "REC-004"],
        }

        required_items = control_to_checklist.get(control_id, [])
        if not required_items:
            # Use keyword matching if no direct mapping
            return self._evaluate_by_keywords(control_id, evidence_collected)

        completed_required = [
            item for item in required_items if item in completed_actions
        ]

        if len(completed_required) == len(required_items):
            return ComplianceStatus.COMPLIANT
        elif len(completed_required) > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.GAP

    def _evaluate_by_keywords(
        self, control_id: str, evidence_collected: List[str]
    ) -> ComplianceStatus:
        """Evaluate compliance using keyword matching."""
        keywords = {
            "DER.1": ["alert", "detection", "log", "monitor"],
            "DER.2.1": ["incident", "report", "response", "timeline"],
            "DER.2.2": ["memory", "forensic", "evidence", "capture", "image"],
            "DER.2.3": ["cleanup", "removal", "malware", "persistence"],
            "DER.4": ["recovery", "backup", "restore", "continuity"],
            "CON.3": ["backup", "restore", "integrity"],
            "ORP.1": ["organization", "policy", "procedure"],
            "ORP.3": ["training", "awareness", "lesson"],
        }

        # Get keywords for control or parent
        control_keywords = keywords.get(control_id)
        if not control_keywords:
            parts = control_id.split(".")
            if len(parts) >= 2:
                parent = f"{parts[0]}.{parts[1]}"
                control_keywords = keywords.get(parent, [])

        if not control_keywords:
            return ComplianceStatus.NOT_EVALUATED

        evidence_text = " ".join(evidence_collected).lower()
        matches = sum(1 for kw in control_keywords if kw in evidence_text)

        if matches >= len(control_keywords):
            return ComplianceStatus.COMPLIANT
        elif matches > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.GAP

    def _match_evidence(
        self, control_id: str, evidence_collected: List[str]
    ) -> List[str]:
        """Match collected evidence to a control's requirements."""
        keywords = {
            "DER.1": ["alert", "detection", "log", "monitor"],
            "DER.2.1": ["incident", "report", "response", "timeline"],
            "DER.2.2": ["memory", "forensic", "evidence", "capture", "image"],
            "DER.2.3": ["cleanup", "removal", "malware", "persistence"],
            "DER.4": ["recovery", "backup", "restore", "continuity"],
        }

        # Get keywords for control or parent
        control_keywords = keywords.get(control_id)
        if not control_keywords:
            parts = control_id.split(".")
            if len(parts) >= 2:
                parent = f"{parts[0]}.{parts[1]}"
                control_keywords = keywords.get(parent, [])

        if not control_keywords:
            return []

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
            "DER.1.A1": "Document security policy for detection of security events.",
            "DER.1.A3": "Define and document reporting paths for security events.",
            "DER.2.1": "Complete incident handling procedures including proper classification and escalation.",
            "DER.2.1.A1": "Clearly define what constitutes a security incident.",
            "DER.2.1.A6": "Conduct and document post-incident review and lessons learned.",
            "DER.2.1.A7": "Report incident to relevant authorities within required timeframe.",
            "DER.2.2": "Capture volatile evidence (memory) before any containment actions that may alter system state.",
            "DER.2.2.A1": "Review and document legal requirements for forensic evidence.",
            "DER.2.3": "Identify and document all persistence mechanisms before removal.",
            "DER.2.3.A2": "Document decision on cleanup strategy (rebuild vs clean).",
            "DER.4": "Verify backup integrity and test restoration procedures before recovery.",
            "DER.4.A1": "Create and maintain emergency handbook.",
            "CON.3": "Ensure backup verification is documented and recovery capability is tested.",
        }

        # Try direct match first
        rec = recommendations.get(control_id)
        if rec:
            return rec

        # Try parent control
        parts = control_id.split(".")
        if len(parts) >= 2:
            parent = f"{parts[0]}.{parts[1]}"
            rec = recommendations.get(parent)
            if rec:
                return rec

        return f"Review and complete requirements for control {control_id}."

    def _get_gap_description(
        self, control_id: str, completed_actions: List[str]
    ) -> str:
        """Get description of compliance gap."""
        return f"Control {control_id} requirements not fully satisfied. Review mandatory checklist items."

    def get_framework_info(self) -> Dict[str, Any]:
        """Get information about BSI IT-Grundschutz."""
        return {
            "id": "bsi_grundschutz",
            "name": "BSI IT-Grundschutz",
            "organization": "Bundesamt für Sicherheit in der Informationstechnik (Germany)",
            "version": "2023",
            "effective_date": "2023-01-01",
            "format": "OSCAL/JSON",
            "url": "https://www.bsi.bund.de/",
            "repository": "https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek",
            "controls_count": len(self.CONTROL_DETAILS),
            "description": "German Federal Office for Information Security framework for IT security.",
            "grundschutz_plus": {
                "name": "IT-Grundschutz++",
                "effective_date": "2026-01-01",
                "features": [
                    "Machine-readable OSCAL format",
                    "JSON and XML representations",
                    "Automated compliance checking support",
                    "Integration with security tools",
                ],
            },
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
