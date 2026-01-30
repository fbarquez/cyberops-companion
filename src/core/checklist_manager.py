"""
Checklist Manager

Manages interactive checklists with forensic awareness and dependency tracking.
"""

import sys
from pathlib import Path as PathLib

# Add project root to path for imports
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Optional, List, Dict
from pathlib import Path
import json

from src.models.checklist import ChecklistItem, ChecklistPhase, ChecklistStatus
from src.models.phase import IRPhase
from config import PLAYBOOKS_DIR


class ChecklistManager:
    """
    Manages phase checklists with forensic awareness.

    Features:
    - Load checklists from playbook definitions
    - Track completion status
    - Enforce dependencies
    - Highlight forensic-critical items
    """

    def __init__(self, playbook_name: str = "ransomware"):
        """
        Initialize the checklist manager.

        Args:
            playbook_name: Name of the playbook to load checklists from
        """
        self.playbook_name = playbook_name
        self.phase_checklists: Dict[str, ChecklistPhase] = {}
        self._load_checklists()

    def _load_checklists(self) -> None:
        """Load checklist definitions from playbook."""
        checklist_path = PLAYBOOKS_DIR / f"{self.playbook_name}_checklists.json"

        if checklist_path.exists():
            with open(checklist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for phase_data in data.get("phases", []):
                    phase = ChecklistPhase(**phase_data)
                    self.phase_checklists[phase.phase_id] = phase
        else:
            # Load default checklists
            self._load_default_checklists()

    def _load_default_checklists(self) -> None:
        """Create default checklist definitions."""
        default_checklists = {
            IRPhase.DETECTION.value: ChecklistPhase(
                phase_id=IRPhase.DETECTION.value,
                phase_name="Detection & Triage",
                description="Initial detection and triage checklist",
                items=[
                    ChecklistItem(
                        id="DET-001",
                        phase=IRPhase.DETECTION.value,
                        text="Document the initial alert/report details",
                        help_text="Record who reported, when, and what was observed",
                        mandatory=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="DET-002",
                        phase=IRPhase.DETECTION.value,
                        text="Identify affected system(s)",
                        help_text="Record hostname, IP, location, user",
                        mandatory=True,
                        order=2,
                    ),
                    ChecklistItem(
                        id="DET-003",
                        phase=IRPhase.DETECTION.value,
                        text="Confirm ransomware indicators present",
                        help_text="Look for ransom notes, encrypted files, suspicious processes",
                        mandatory=True,
                        order=3,
                    ),
                    ChecklistItem(
                        id="DET-004",
                        phase=IRPhase.DETECTION.value,
                        text="Verify system is still running (DO NOT power off)",
                        help_text="Check if volatile evidence can be captured",
                        warning="Powering off will destroy volatile memory evidence",
                        mandatory=True,
                        forensic_critical=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="DET-005",
                        phase=IRPhase.DETECTION.value,
                        text="Notify incident response team/manager",
                        mandatory=False,
                        order=5,
                    ),
                    ChecklistItem(
                        id="DET-006",
                        phase=IRPhase.DETECTION.value,
                        text="Assign incident ID and open tracking",
                        mandatory=True,
                        order=6,
                    ),
                ],
            ),
            IRPhase.ANALYSIS.value: ChecklistPhase(
                phase_id=IRPhase.ANALYSIS.value,
                phase_name="Analysis & Scoping",
                description="Analysis and scope determination checklist",
                items=[
                    ChecklistItem(
                        id="ANA-001",
                        phase=IRPhase.ANALYSIS.value,
                        text="Capture volatile memory (if system running)",
                        help_text="Use approved memory capture tool before any other action",
                        warning="Must be done BEFORE network isolation or shutdown",
                        mandatory=True,
                        forensic_critical=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="ANA-002",
                        phase=IRPhase.ANALYSIS.value,
                        text="Identify ransomware variant (if possible)",
                        help_text="Check ransom note, file extensions, known IOCs",
                        mandatory=True,
                        depends_on=["ANA-001"],
                        order=2,
                    ),
                    ChecklistItem(
                        id="ANA-003",
                        phase=IRPhase.ANALYSIS.value,
                        text="Document ransom note contents",
                        help_text="Screenshot and transcribe the ransom note",
                        mandatory=True,
                        order=3,
                    ),
                    ChecklistItem(
                        id="ANA-004",
                        phase=IRPhase.ANALYSIS.value,
                        text="Identify encrypted file extensions",
                        help_text="Document the file extension pattern used",
                        mandatory=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="ANA-005",
                        phase=IRPhase.ANALYSIS.value,
                        text="Check for lateral movement indicators",
                        help_text="Review authentication logs, network connections",
                        mandatory=True,
                        order=5,
                    ),
                    ChecklistItem(
                        id="ANA-006",
                        phase=IRPhase.ANALYSIS.value,
                        text="Review recent authentication events",
                        help_text="Check for suspicious logins, credential use",
                        mandatory=True,
                        order=6,
                    ),
                    ChecklistItem(
                        id="ANA-007",
                        phase=IRPhase.ANALYSIS.value,
                        text="Check for data exfiltration indicators",
                        help_text="Review outbound traffic, cloud storage access",
                        mandatory=False,
                        order=7,
                    ),
                    ChecklistItem(
                        id="ANA-008",
                        phase=IRPhase.ANALYSIS.value,
                        text="Document initial scope assessment",
                        mandatory=True,
                        order=8,
                    ),
                ],
            ),
            IRPhase.CONTAINMENT.value: ChecklistPhase(
                phase_id=IRPhase.CONTAINMENT.value,
                phase_name="Containment",
                description="Containment actions checklist",
                items=[
                    ChecklistItem(
                        id="CON-001",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Network isolation of affected system(s)",
                        help_text="Disconnect network cable or disable NIC - do NOT power off",
                        warning="Keep system powered on if possible for evidence",
                        mandatory=True,
                        forensic_critical=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="CON-002",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Block malicious IPs/domains at firewall",
                        help_text="Based on IOCs identified during analysis",
                        mandatory=False,
                        depends_on=["CON-001"],
                        order=2,
                    ),
                    ChecklistItem(
                        id="CON-003",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Disable compromised user accounts",
                        help_text="Reset passwords for any accounts used by attacker",
                        mandatory=True,
                        order=3,
                    ),
                    ChecklistItem(
                        id="CON-004",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Preserve system state (disk image if needed)",
                        help_text="Create forensic image before any remediation",
                        warning="Once remediation begins, evidence may be altered",
                        mandatory=True,
                        forensic_critical=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="CON-005",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Document all containment actions taken",
                        mandatory=True,
                        order=5,
                    ),
                    ChecklistItem(
                        id="CON-006",
                        phase=IRPhase.CONTAINMENT.value,
                        text="Verify containment is effective",
                        help_text="Confirm no further spread or activity",
                        mandatory=True,
                        depends_on=["CON-001", "CON-003"],
                        order=6,
                    ),
                ],
            ),
            IRPhase.ERADICATION.value: ChecklistPhase(
                phase_id=IRPhase.ERADICATION.value,
                phase_name="Eradication",
                description="Threat removal checklist",
                items=[
                    ChecklistItem(
                        id="ERA-001",
                        phase=IRPhase.ERADICATION.value,
                        text="Identify all persistence mechanisms",
                        help_text="Check scheduled tasks, services, registry, startup items",
                        mandatory=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="ERA-002",
                        phase=IRPhase.ERADICATION.value,
                        text="Remove ransomware binaries and artifacts",
                        mandatory=True,
                        depends_on=["ERA-001"],
                        order=2,
                    ),
                    ChecklistItem(
                        id="ERA-003",
                        phase=IRPhase.ERADICATION.value,
                        text="Remove persistence mechanisms",
                        mandatory=True,
                        depends_on=["ERA-001"],
                        order=3,
                    ),
                    ChecklistItem(
                        id="ERA-004",
                        phase=IRPhase.ERADICATION.value,
                        text="Reset all potentially compromised credentials",
                        mandatory=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="ERA-005",
                        phase=IRPhase.ERADICATION.value,
                        text="Patch the initial attack vector",
                        help_text="Address vulnerability or misconfiguration exploited",
                        mandatory=True,
                        order=5,
                    ),
                    ChecklistItem(
                        id="ERA-006",
                        phase=IRPhase.ERADICATION.value,
                        text="Scan for remaining indicators",
                        help_text="Use EDR/AV to verify clean state",
                        mandatory=True,
                        order=6,
                    ),
                ],
            ),
            IRPhase.RECOVERY.value: ChecklistPhase(
                phase_id=IRPhase.RECOVERY.value,
                phase_name="Recovery",
                description="System restoration checklist",
                items=[
                    ChecklistItem(
                        id="REC-001",
                        phase=IRPhase.RECOVERY.value,
                        text="Verify clean backup availability",
                        help_text="Confirm backups pre-date infection",
                        mandatory=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="REC-002",
                        phase=IRPhase.RECOVERY.value,
                        text="Restore systems from clean state",
                        help_text="Rebuild or restore from verified backups",
                        mandatory=True,
                        depends_on=["REC-001"],
                        order=2,
                    ),
                    ChecklistItem(
                        id="REC-003",
                        phase=IRPhase.RECOVERY.value,
                        text="Apply security patches before reconnection",
                        mandatory=True,
                        depends_on=["REC-002"],
                        order=3,
                    ),
                    ChecklistItem(
                        id="REC-004",
                        phase=IRPhase.RECOVERY.value,
                        text="Enable enhanced monitoring",
                        help_text="Increase logging, enable additional alerts",
                        mandatory=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="REC-005",
                        phase=IRPhase.RECOVERY.value,
                        text="Gradually restore network connectivity",
                        help_text="Monitor for signs of reinfection",
                        mandatory=True,
                        depends_on=["REC-003", "REC-004"],
                        order=5,
                    ),
                    ChecklistItem(
                        id="REC-006",
                        phase=IRPhase.RECOVERY.value,
                        text="Verify business operations restored",
                        mandatory=True,
                        order=6,
                    ),
                ],
            ),
            IRPhase.POST_INCIDENT.value: ChecklistPhase(
                phase_id=IRPhase.POST_INCIDENT.value,
                phase_name="Post-Incident Review",
                description="Lessons learned and closure checklist",
                items=[
                    ChecklistItem(
                        id="POST-001",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Complete incident timeline documentation",
                        mandatory=True,
                        order=1,
                    ),
                    ChecklistItem(
                        id="POST-002",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Document root cause analysis",
                        mandatory=True,
                        order=2,
                    ),
                    ChecklistItem(
                        id="POST-003",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Identify lessons learned",
                        mandatory=True,
                        order=3,
                    ),
                    ChecklistItem(
                        id="POST-004",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Document improvement recommendations",
                        mandatory=True,
                        order=4,
                    ),
                    ChecklistItem(
                        id="POST-005",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Update playbooks based on findings",
                        mandatory=False,
                        order=5,
                    ),
                    ChecklistItem(
                        id="POST-006",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Generate final incident report",
                        mandatory=True,
                        order=6,
                    ),
                    ChecklistItem(
                        id="POST-007",
                        phase=IRPhase.POST_INCIDENT.value,
                        text="Close incident with stakeholder sign-off",
                        mandatory=True,
                        depends_on=["POST-006"],
                        order=7,
                    ),
                ],
            ),
        }

        self.phase_checklists = default_checklists

    def get_phase_checklist(self, phase: str) -> Optional[ChecklistPhase]:
        """Get the checklist for a specific phase."""
        return self.phase_checklists.get(phase)

    def create_incident_checklist(self, incident_id: str) -> Dict[str, ChecklistPhase]:
        """
        Create a fresh copy of checklists for a new incident.

        Returns a dictionary of phase checklists that can be modified
        without affecting the template.
        """
        incident_checklists = {}

        for phase_id, phase_checklist in self.phase_checklists.items():
            # Deep copy the checklist
            items = [
                ChecklistItem(**item.model_dump())
                for item in phase_checklist.items
            ]
            incident_checklists[phase_id] = ChecklistPhase(
                phase_id=phase_checklist.phase_id,
                phase_name=phase_checklist.phase_name,
                description=phase_checklist.description,
                items=items,
            )

        return incident_checklists

    def complete_item(
        self,
        checklist: ChecklistPhase,
        item_id: str,
        operator: str,
        notes: Optional[str] = None,
    ) -> ChecklistItem:
        """
        Mark a checklist item as completed.

        Args:
            checklist: The phase checklist
            item_id: ID of the item to complete
            operator: Name of the operator completing the item
            notes: Optional notes about completion

        Returns:
            The updated ChecklistItem
        """
        item = checklist.get_item(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        # Check dependencies
        completed_ids = checklist.get_completed_ids()
        if item.is_blocked(completed_ids):
            blocking = [d for d in item.depends_on if d not in completed_ids]
            raise ValueError(f"Item is blocked by: {blocking}")

        item.complete(operator=operator, notes=notes)
        return item

    def skip_item(
        self,
        checklist: ChecklistPhase,
        item_id: str,
        operator: str,
        reason: str,
    ) -> ChecklistItem:
        """
        Skip a checklist item with a reason.

        Args:
            checklist: The phase checklist
            item_id: ID of the item to skip
            operator: Name of the operator
            reason: Reason for skipping (required)

        Returns:
            The updated ChecklistItem
        """
        item = checklist.get_item(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        if item.mandatory:
            raise ValueError("Cannot skip mandatory items without special override")

        item.skip(operator=operator, reason=reason)
        return item

    def get_phase_progress(self, checklist: ChecklistPhase) -> dict:
        """Get progress information for a phase checklist."""
        return checklist.get_progress()

    def get_available_items(self, checklist: ChecklistPhase) -> List[ChecklistItem]:
        """Get items that can currently be worked on."""
        return checklist.get_available_items()

    def get_forensic_critical_items(
        self, checklist: ChecklistPhase
    ) -> List[ChecklistItem]:
        """Get all forensic-critical items in a checklist."""
        return [item for item in checklist.items if item.forensic_critical]

    def can_advance_phase(self, checklist: ChecklistPhase) -> tuple[bool, List[str]]:
        """Check if the phase can be advanced based on checklist completion."""
        return checklist.can_advance()

    def export_checklist_state(self, checklist: ChecklistPhase) -> dict:
        """Export the checklist state for reporting."""
        progress = checklist.get_progress()

        return {
            "phase_id": checklist.phase_id,
            "phase_name": checklist.phase_name,
            "progress": progress,
            "items": [
                {
                    "id": item.id,
                    "text": item.text,
                    "status": item.status,
                    "mandatory": item.mandatory,
                    "forensic_critical": item.forensic_critical,
                    "completed_at": (
                        item.completed_at.isoformat() if item.completed_at else None
                    ),
                    "completed_by": item.completed_by,
                    "notes": item.notes,
                    "skip_reason": item.skip_reason,
                }
                for item in checklist.items
            ],
        }
