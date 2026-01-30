"""
Workflow Engine

Manages the overall incident response workflow, including phase transitions
and state management.
"""

import sys
from pathlib import Path as PathLib

# Add project root to path for imports
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path
import json

from src.models.incident import Incident, IncidentStatus
from src.models.phase import (
    IRPhase,
    PhaseStatus,
    PhaseDefinition,
    IncidentPhaseTracker,
    PHASE_ORDER,
)
from src.models.evidence import EvidenceEntry, EvidenceType
from config import PLAYBOOKS_DIR


class WorkflowEngine:
    """
    Manages the incident response workflow.

    Responsible for:
    - Loading playbook definitions
    - Managing phase transitions
    - Enforcing workflow rules
    - Tracking incident state
    """

    def __init__(self, playbook_name: str = "ransomware"):
        """
        Initialize the workflow engine.

        Args:
            playbook_name: Name of the playbook to load (default: ransomware)
        """
        self.playbook_name = playbook_name
        self.phase_definitions: dict[str, PhaseDefinition] = {}
        self._load_playbook()

    def _load_playbook(self) -> None:
        """Load playbook phase definitions from JSON."""
        playbook_path = PLAYBOOKS_DIR / f"{self.playbook_name}.json"

        if playbook_path.exists():
            with open(playbook_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for phase_data in data.get("phases", []):
                    definition = PhaseDefinition(**phase_data)
                    self.phase_definitions[definition.phase] = definition
        else:
            # Load default phase definitions
            self._load_default_phases()

    def _load_default_phases(self) -> None:
        """Load default phase definitions if no playbook file exists."""
        defaults = [
            PhaseDefinition(
                id="phase_detection",
                phase=IRPhase.DETECTION,
                name="Detection & Triage",
                short_name="Detection",
                description="Initial detection and triage of the potential ransomware incident.",
                objective="Confirm the incident, gather initial indicators, and initiate response.",
                key_questions=[
                    "What triggered this alert/report?",
                    "What systems are potentially affected?",
                    "Is this a confirmed ransomware incident?",
                ],
                critical_reminders=[
                    "Do NOT power off affected systems",
                    "Do NOT attempt to decrypt files",
                    "Document everything from the start",
                ],
                icon="🔍",
                order=0,
            ),
            PhaseDefinition(
                id="phase_analysis",
                phase=IRPhase.ANALYSIS,
                name="Analysis & Scoping",
                short_name="Analysis",
                description="Analyze the scope and impact of the ransomware incident.",
                objective="Determine the full scope of compromise before containment.",
                key_questions=[
                    "What ransomware variant is this?",
                    "How did the attacker gain access?",
                    "What is the lateral movement scope?",
                ],
                forensic_considerations=[
                    "Preserve volatile memory before shutdown",
                    "Document all IOCs found",
                    "Check for data exfiltration indicators",
                ],
                icon="🔬",
                order=1,
            ),
            PhaseDefinition(
                id="phase_containment",
                phase=IRPhase.CONTAINMENT,
                name="Containment",
                short_name="Contain",
                description="Contain the incident to prevent further damage.",
                objective="Stop the spread while preserving evidence.",
                key_questions=[
                    "Are all affected systems identified?",
                    "Is network isolation complete?",
                    "Is the attacker still active?",
                ],
                critical_reminders=[
                    "Network isolation before system shutdown",
                    "Capture memory before powering off",
                    "Document all containment actions",
                ],
                icon="🛡️",
                order=2,
            ),
            PhaseDefinition(
                id="phase_eradication",
                phase=IRPhase.ERADICATION,
                name="Eradication",
                short_name="Eradicate",
                description="Remove the threat from the environment.",
                objective="Eliminate all traces of the ransomware and attacker access.",
                key_questions=[
                    "Are all persistence mechanisms identified?",
                    "Are compromised credentials reset?",
                    "Is the attack vector closed?",
                ],
                icon="🧹",
                order=3,
            ),
            PhaseDefinition(
                id="phase_recovery",
                phase=IRPhase.RECOVERY,
                name="Recovery",
                short_name="Recover",
                description="Restore systems and return to normal operations.",
                objective="Safely restore systems with monitoring for reinfection.",
                key_questions=[
                    "Are clean backups available?",
                    "Is the restoration process validated?",
                    "Is enhanced monitoring in place?",
                ],
                icon="🔄",
                order=4,
            ),
            PhaseDefinition(
                id="phase_post_incident",
                phase=IRPhase.POST_INCIDENT,
                name="Post-Incident Review",
                short_name="Review",
                description="Review the incident and capture lessons learned.",
                objective="Document findings, improve processes, and close the incident.",
                key_questions=[
                    "What was the root cause?",
                    "What can be improved?",
                    "Are all documentation requirements met?",
                ],
                icon="📝",
                order=5,
            ),
        ]

        for definition in defaults:
            self.phase_definitions[definition.phase] = definition

    def create_incident(
        self,
        title: str,
        analyst_name: str,
        detection_source: str = "other",
        initial_indicator: str = "",
        is_simulation: bool = False,
    ) -> tuple[Incident, IncidentPhaseTracker]:
        """
        Create a new incident and initialize phase tracking.

        Returns:
            Tuple of (Incident, IncidentPhaseTracker)
        """
        incident = Incident(
            title=title,
            analyst_name=analyst_name,
            detection_source=detection_source,
            initial_indicator=initial_indicator,
            is_simulation=is_simulation,
        )

        tracker = IncidentPhaseTracker(incident_id=incident.id)
        tracker.get_current_progress().start()

        return incident, tracker

    def get_phase_definition(self, phase: IRPhase) -> Optional[PhaseDefinition]:
        """Get the definition for a specific phase."""
        return self.phase_definitions.get(phase)

    def get_current_phase_info(
        self, tracker: IncidentPhaseTracker
    ) -> dict:
        """Get comprehensive information about the current phase."""
        current_phase = tracker.current_phase
        definition = self.get_phase_definition(current_phase)
        progress = tracker.get_current_progress()

        phase_index = PHASE_ORDER.index(current_phase)

        return {
            "phase": current_phase.value,
            "phase_number": phase_index + 1,
            "total_phases": len(PHASE_ORDER),
            "definition": definition.model_dump() if definition else None,
            "status": progress.status,
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "is_first_phase": phase_index == 0,
            "is_last_phase": phase_index == len(PHASE_ORDER) - 1,
        }

    def can_advance_phase(
        self,
        tracker: IncidentPhaseTracker,
        checklist_complete: bool = False,
        decisions_made: bool = False,
    ) -> tuple[bool, List[str]]:
        """
        Check if the current phase can be advanced.

        Args:
            tracker: The incident's phase tracker
            checklist_complete: Whether the phase checklist is complete
            decisions_made: Whether required decisions have been made

        Returns:
            Tuple of (can_advance, list of blocking reasons)
        """
        blocking_reasons = []

        # Check basic advancement capability
        can_advance, reason = tracker.can_advance()
        if not can_advance:
            blocking_reasons.append(reason)

        # Check checklist
        if not checklist_complete:
            blocking_reasons.append("Phase checklist has incomplete mandatory items")

        # Check decisions
        if not decisions_made:
            blocking_reasons.append("Required decisions have not been made")

        return len(blocking_reasons) == 0, blocking_reasons

    def advance_phase(
        self,
        incident: Incident,
        tracker: IncidentPhaseTracker,
        completion_notes: Optional[str] = None,
    ) -> tuple[IRPhase, EvidenceEntry]:
        """
        Advance to the next phase.

        Args:
            incident: The incident being worked
            tracker: The phase tracker
            completion_notes: Optional notes about phase completion

        Returns:
            Tuple of (new_phase, evidence_entry for the transition)
        """
        old_phase = tracker.current_phase
        new_phase = tracker.advance_phase(completion_notes)

        # Record phase transition in incident
        incident.transition_phase(
            new_phase.value, reason=completion_notes or "Phase completed"
        )

        # Create evidence entry for the transition
        entry = EvidenceEntry(
            incident_id=incident.id,
            entry_type=EvidenceType.SYSTEM,
            phase=old_phase.value,
            description=f"Phase transition: {old_phase.value} → {new_phase.value}",
            operator="SYSTEM",
            tags=["phase_transition"],
        )

        return new_phase, entry

    def get_workflow_summary(self, tracker: IncidentPhaseTracker) -> dict:
        """Get a summary of the workflow state."""
        overall = tracker.get_overall_progress()
        timeline = tracker.get_timeline()

        return {
            "overall_progress": overall,
            "timeline": timeline,
            "phases": [
                {
                    "phase": phase.value,
                    "name": (
                        self.phase_definitions[phase].name
                        if phase in self.phase_definitions
                        else phase.value
                    ),
                    "status": tracker.phases[phase.value].status,
                    "is_current": phase == tracker.current_phase,
                }
                for phase in PHASE_ORDER
            ],
        }
