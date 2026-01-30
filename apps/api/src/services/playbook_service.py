"""
Playbook Service - Manages IR playbooks.

Provides:
- Loading playbook templates from data files
- Generating customized playbooks for incidents
- Exporting playbooks in various formats
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PlaybookPhase(BaseModel):
    """A phase in an incident response playbook."""
    id: str
    phase: str
    name: str
    short_name: str
    description: str
    objective: str
    key_questions: List[str] = Field(default_factory=list)
    critical_reminders: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    forensic_considerations: List[str] = Field(default_factory=list)
    icon: str = ""
    order: int = 0


class Playbook(BaseModel):
    """An incident response playbook."""
    playbook_id: str
    name: str
    version: str
    description: str
    created_at: str
    phases: List[PlaybookPhase] = Field(default_factory=list)


class PlaybookType(BaseModel):
    """A playbook type/template."""
    id: str
    name: str
    description: str
    available: bool = True


# Default playbook types
DEFAULT_PLAYBOOK_TYPES = [
    PlaybookType(
        id="ransomware",
        name="Ransomware",
        description="Response playbook for ransomware attacks including data encryption and extortion",
    ),
    PlaybookType(
        id="phishing",
        name="Phishing",
        description="Response playbook for phishing campaigns and credential theft",
    ),
    PlaybookType(
        id="data_breach",
        name="Data Breach",
        description="Response playbook for data breach incidents with potential data exfiltration",
    ),
    PlaybookType(
        id="malware",
        name="Malware",
        description="General malware incident response playbook",
    ),
    PlaybookType(
        id="insider_threat",
        name="Insider Threat",
        description="Response playbook for insider threat incidents",
    ),
    PlaybookType(
        id="ddos",
        name="DDoS",
        description="Response playbook for distributed denial of service attacks",
    ),
    PlaybookType(
        id="apt",
        name="APT",
        description="Response playbook for advanced persistent threat incidents",
    ),
]


class PlaybookService:
    """Service for managing IR playbooks."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the playbook service.

        Args:
            data_dir: Directory containing playbook data files
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent.parent.parent / "data" / "playbooks"
        self._playbooks: Dict[str, Playbook] = {}
        self._load_playbooks()

    def _load_playbooks(self) -> None:
        """Load playbooks from data directory."""
        if not self.data_dir.exists():
            logger.warning(f"Playbook data directory not found: {self.data_dir}")
            return

        for playbook_file in self.data_dir.glob("*.json"):
            try:
                with open(playbook_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    playbook = Playbook(
                        playbook_id=data.get("playbook_id", playbook_file.stem),
                        name=data.get("name", playbook_file.stem),
                        version=data.get("version", "1.0.0"),
                        description=data.get("description", ""),
                        created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                        phases=[PlaybookPhase(**phase) for phase in data.get("phases", [])],
                    )
                    self._playbooks[playbook.playbook_id] = playbook
                    logger.info(f"Loaded playbook: {playbook.playbook_id}")
            except Exception as e:
                logger.error(f"Failed to load playbook {playbook_file}: {e}")

    def get_playbook_types(self) -> List[PlaybookType]:
        """Get available playbook types."""
        types = []
        for ptype in DEFAULT_PLAYBOOK_TYPES:
            # Mark as available if we have a loaded playbook
            ptype_copy = ptype.model_copy()
            ptype_copy.available = ptype.id in self._playbooks
            types.append(ptype_copy)
        return types

    def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a specific playbook by ID."""
        return self._playbooks.get(playbook_id)

    def generate_playbook(
        self,
        incident_type: str,
        severity: str,
        affected_systems: List[str],
        compliance_frameworks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a customized playbook for an incident.

        Args:
            incident_type: Type of incident (ransomware, phishing, etc.)
            severity: Severity level (critical, high, medium, low)
            affected_systems: List of affected system names/IPs
            compliance_frameworks: List of compliance frameworks to consider

        Returns:
            Generated playbook structure
        """
        # Get base playbook if available
        base_playbook = self._playbooks.get(incident_type)

        # Generate phases
        phases = []
        if base_playbook:
            for phase in base_playbook.phases:
                phase_data = phase.model_dump()
                # Add severity-specific tasks
                phase_data["severity_considerations"] = self._get_severity_considerations(
                    phase.phase, severity
                )
                # Add system-specific notes
                if affected_systems:
                    phase_data["affected_systems"] = affected_systems
                phases.append(phase_data)
        else:
            # Generate default phases
            default_phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
            for i, phase in enumerate(default_phases):
                phases.append({
                    "phase": phase,
                    "name": phase.replace("_", " ").title(),
                    "order": i,
                    "tasks": [],
                    "critical_reminders": [],
                    "forensic_considerations": [],
                })

        return {
            "incident_type": incident_type,
            "severity": severity,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phases": phases,
            "compliance_mappings": compliance_frameworks or [],
            "affected_systems": affected_systems,
            "metadata": {
                "base_playbook": base_playbook.playbook_id if base_playbook else None,
                "version": base_playbook.version if base_playbook else "1.0.0",
            },
        }

    def _get_severity_considerations(self, phase: str, severity: str) -> List[str]:
        """Get severity-specific considerations for a phase."""
        considerations = {
            "critical": {
                "detection": ["Immediate escalation to management", "Consider external IR support"],
                "analysis": ["Fast-track analysis to enable rapid containment"],
                "containment": ["Aggressive containment may be needed", "Consider full network isolation"],
                "eradication": ["Complete rebuild may be faster than cleaning"],
                "recovery": ["Prioritize business-critical systems"],
                "post_incident": ["Executive-level briefing required"],
            },
            "high": {
                "detection": ["Escalate to incident commander"],
                "analysis": ["Thorough scoping required before containment"],
                "containment": ["Balance between speed and evidence preservation"],
                "eradication": ["Verify all persistence mechanisms removed"],
                "recovery": ["Staged recovery with monitoring"],
                "post_incident": ["Management briefing recommended"],
            },
            "medium": {
                "detection": ["Standard triage procedures"],
                "analysis": ["Complete analysis before containment"],
                "containment": ["Standard containment procedures"],
                "eradication": ["Follow standard eradication checklist"],
                "recovery": ["Normal recovery procedures"],
                "post_incident": ["Standard post-incident review"],
            },
            "low": {
                "detection": ["Normal monitoring procedures"],
                "analysis": ["Standard analysis timeframe"],
                "containment": ["Monitor before containment if needed"],
                "eradication": ["Standard remediation"],
                "recovery": ["Normal service restoration"],
                "post_incident": ["Document for lessons learned"],
            },
        }
        return considerations.get(severity, {}).get(phase, [])

    def export_playbook(
        self,
        playbook_id: str,
        format: str = "markdown",
    ) -> str:
        """
        Export a playbook in the specified format.

        Args:
            playbook_id: ID of the playbook to export
            format: Export format (markdown, json)

        Returns:
            Formatted playbook content
        """
        playbook = self._playbooks.get(playbook_id)
        if not playbook:
            return ""

        if format == "json":
            return json.dumps(playbook.model_dump(), indent=2)

        # Markdown format
        lines = [
            f"# {playbook.name}",
            "",
            f"**Version:** {playbook.version}",
            f"**Description:** {playbook.description}",
            "",
            "---",
            "",
        ]

        for phase in playbook.phases:
            lines.extend([
                f"## {phase.icon} {phase.name}",
                "",
                f"**Objective:** {phase.objective}",
                "",
                "### Key Questions",
                "",
            ])
            for q in phase.key_questions:
                lines.append(f"- {q}")

            lines.extend([
                "",
                "### Critical Reminders",
                "",
            ])
            for r in phase.critical_reminders:
                lines.append(f"- {r}")

            lines.extend([
                "",
                "### Common Mistakes to Avoid",
                "",
            ])
            for m in phase.common_mistakes:
                lines.append(f"- {m}")

            lines.extend([
                "",
                "### Forensic Considerations",
                "",
            ])
            for f in phase.forensic_considerations:
                lines.append(f"- {f}")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_playbook_service: Optional[PlaybookService] = None


def get_playbook_service() -> PlaybookService:
    """Get the playbook service singleton."""
    global _playbook_service
    if _playbook_service is None:
        _playbook_service = PlaybookService()
    return _playbook_service
