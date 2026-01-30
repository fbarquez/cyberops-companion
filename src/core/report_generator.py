"""
Report Generator

Generates incident reports and evidence packages for export.
"""

import sys
from pathlib import Path as PathLib

# Add project root to path for imports
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import zipfile
import hashlib

from jinja2 import Environment, PackageLoader, select_autoescape

from src.models.incident import Incident
from src.models.phase import IncidentPhaseTracker, PHASE_ORDER
from src.models.checklist import ChecklistPhase
from src.models.decision import DecisionTree
from config import EXPORTS_DIR, TEMPLATES_DIR, get_config


class ReportGenerator:
    """
    Generates incident reports and evidence packages.

    Features:
    - Markdown report generation
    - JSON evidence export
    - ZIP package creation
    - Hash verification files
    """

    def __init__(self):
        """Initialize the report generator."""
        self.config = get_config()

        # Try to load Jinja2 templates, fall back to string templates
        try:
            self.env = Environment(
                loader=PackageLoader("src", "../data/templates"),
                autoescape=select_autoescape(["html", "xml"]),
            )
        except Exception:
            self.env = None

    def generate_incident_report(
        self,
        incident: Incident,
        phase_tracker: IncidentPhaseTracker,
        checklists: Dict[str, ChecklistPhase],
        decision_trees: List[DecisionTree],
        evidence_export: dict,
        lessons_learned: Optional[str] = None,
    ) -> str:
        """
        Generate a complete incident report in Markdown format.

        Args:
            incident: The incident being reported
            phase_tracker: Phase progress tracker
            checklists: Phase checklists with completion state
            decision_trees: Decision trees with paths taken
            evidence_export: Exported evidence chain
            lessons_learned: Optional lessons learned notes

        Returns:
            Markdown report content
        """
        # Build report sections
        sections = []

        # Header
        sections.append(self._generate_header(incident))

        # Executive Summary
        sections.append(self._generate_executive_summary(incident, phase_tracker))

        # Timeline
        sections.append(self._generate_timeline(phase_tracker))

        # Phase Details
        sections.append(self._generate_phase_details(phase_tracker, checklists))

        # Decisions Made
        sections.append(self._generate_decisions_section(decision_trees))

        # Evidence Summary
        sections.append(self._generate_evidence_summary(evidence_export))

        # Lessons Learned (if provided)
        if lessons_learned:
            sections.append(self._generate_lessons_learned(lessons_learned))

        # Footer
        sections.append(self._generate_footer(incident))

        return "\n\n".join(sections)

    def _generate_header(self, incident: Incident) -> str:
        """Generate report header."""
        simulation_badge = " [SIMULATION]" if incident.is_simulation else ""

        return f"""# Incident Report{simulation_badge}

**Incident ID:** {incident.id}
**Title:** {incident.title}
**Severity:** {incident.severity.upper()}
**Status:** {incident.status.upper()}

**Report Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**Analyst:** {incident.analyst_name}

---"""

    def _generate_executive_summary(
        self, incident: Incident, tracker: IncidentPhaseTracker
    ) -> str:
        """Generate executive summary section."""
        progress = tracker.get_overall_progress()
        duration = incident.get_duration()
        duration_str = (
            f"{duration / 3600:.1f} hours" if duration else "In Progress"
        )

        affected_systems = ", ".join(
            [s.hostname for s in incident.affected_systems]
        ) or "None documented"

        return f"""## Executive Summary

**Detection Source:** {incident.detection_source.replace('_', ' ').title()}
**Initial Indicator:** {incident.initial_indicator or 'Not specified'}

**Affected Systems:** {affected_systems}

**Response Progress:** {progress['percentage']}% complete ({progress['completed_phases']}/{progress['total_phases']} phases)
**Duration:** {duration_str}

**Description:**
{incident.description or 'No description provided.'}"""

    def _generate_timeline(self, tracker: IncidentPhaseTracker) -> str:
        """Generate incident timeline."""
        timeline = tracker.get_timeline()

        if not timeline:
            return """## Timeline

No timeline data available."""

        lines = ["## Timeline", "", "| Phase | Started | Completed | Duration |",
                 "|-------|---------|-----------|----------|"]

        for entry in timeline:
            started = entry["started_at"][:19].replace("T", " ") if entry["started_at"] else "-"
            completed = entry["completed_at"][:19].replace("T", " ") if entry["completed_at"] else "-"

            if entry["duration_seconds"]:
                mins = entry["duration_seconds"] / 60
                duration = f"{mins:.1f} min"
            else:
                duration = "-"

            lines.append(
                f"| {entry['phase'].replace('_', ' ').title()} | {started} | {completed} | {duration} |"
            )

        return "\n".join(lines)

    def _generate_phase_details(
        self,
        tracker: IncidentPhaseTracker,
        checklists: Dict[str, ChecklistPhase],
    ) -> str:
        """Generate detailed phase information."""
        sections = ["## Phase Details"]

        for phase in PHASE_ORDER:
            phase_key = phase.value
            progress = tracker.phases.get(phase_key)
            checklist = checklists.get(phase_key)

            phase_name = phase_key.replace("_", " ").title()
            status = progress.status if progress else "not_started"

            sections.append(f"\n### {phase_name}")
            sections.append(f"**Status:** {status.replace('_', ' ').title()}")

            if checklist:
                checklist_progress = checklist.get_progress()
                sections.append(
                    f"**Checklist:** {checklist_progress['completed']}/{checklist_progress['total']} items completed"
                )

                # List completed items
                completed_items = [
                    item for item in checklist.items
                    if item.status in ["completed", "skipped", "not_applicable"]
                ]

                if completed_items:
                    sections.append("\n**Completed Items:**")
                    for item in completed_items:
                        status_icon = "✓" if item.status == "completed" else "⊘"
                        sections.append(f"- {status_icon} {item.text}")
                        if item.notes:
                            sections.append(f"  - *Note: {item.notes}*")
                        if item.skip_reason:
                            sections.append(f"  - *Skipped: {item.skip_reason}*")

        return "\n".join(sections)

    def _generate_decisions_section(self, trees: List[DecisionTree]) -> str:
        """Generate decisions section."""
        sections = ["## Key Decisions"]

        total_decisions = sum(len(tree.path_taken) for tree in trees)

        if total_decisions == 0:
            sections.append("\nNo decisions have been recorded.")
            return "\n".join(sections)

        for tree in trees:
            if not tree.path_taken:
                continue

            sections.append(f"\n### {tree.name}")

            for path in tree.path_taken:
                timestamp = path.decided_at.strftime("%Y-%m-%d %H:%M")
                sections.append(f"\n**{timestamp}** - {path.selected_option_label}")
                sections.append(f"- Confidence: {path.confidence.upper()}")
                sections.append(f"- Operator: {path.operator}")
                if path.rationale:
                    sections.append(f"- Rationale: {path.rationale}")

        return "\n".join(sections)

    def _generate_evidence_summary(self, evidence_export: dict) -> str:
        """Generate evidence summary section."""
        sections = ["## Evidence Log Summary"]

        total = evidence_export.get("total_entries", 0)
        integrity = evidence_export.get("chain_integrity", {})

        sections.append(f"\n**Total Evidence Entries:** {total}")
        sections.append(
            f"**Chain Integrity:** {'Verified ✓' if integrity.get('verified') else 'FAILED ✗'}"
        )

        if not integrity.get("verified"):
            sections.append(f"*Integrity Issue: {integrity.get('message')}*")

        # Entry type breakdown
        entries = evidence_export.get("entries", [])
        type_counts: Dict[str, int] = {}
        for entry in entries:
            entry_type = entry.get("type", "unknown")
            type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

        if type_counts:
            sections.append("\n**Entry Breakdown:**")
            for entry_type, count in sorted(type_counts.items()):
                sections.append(f"- {entry_type.replace('_', ' ').title()}: {count}")

        return "\n".join(sections)

    def _generate_lessons_learned(self, lessons_learned: str) -> str:
        """Generate lessons learned section."""
        return f"""## Lessons Learned

{lessons_learned}"""

    def _generate_footer(self, incident: Incident) -> str:
        """Generate report footer."""
        return f"""---

## Report Metadata

- **Generated By:** CyberOps Companion v{self.config.version}
- **Report Time:** {datetime.now(timezone.utc).isoformat()}
- **Incident ID:** {incident.id}
- **Classification:** {'SIMULATION/TRAINING' if incident.is_simulation else 'PRODUCTION INCIDENT'}

*This report was generated by CyberOps Companion, an incident response decision support tool.*"""

    def create_evidence_package(
        self,
        incident: Incident,
        phase_tracker: IncidentPhaseTracker,
        checklists: Dict[str, ChecklistPhase],
        decision_trees: List[DecisionTree],
        evidence_export: dict,
        lessons_learned: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Create a complete evidence package as a ZIP file.

        Args:
            incident: The incident
            phase_tracker: Phase tracker
            checklists: Phase checklists
            decision_trees: Decision trees
            evidence_export: Exported evidence
            lessons_learned: Optional lessons learned
            output_dir: Output directory (uses EXPORTS_DIR if not specified)

        Returns:
            Path to the created ZIP file
        """
        output_dir = output_dir or EXPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"incident_package_{incident.id}_{timestamp}"
        zip_path = output_dir / f"{package_name}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Generate and add main report
            report_content = self.generate_incident_report(
                incident=incident,
                phase_tracker=phase_tracker,
                checklists=checklists,
                decision_trees=decision_trees,
                evidence_export=evidence_export,
                lessons_learned=lessons_learned,
            )
            zf.writestr(f"{package_name}/incident_report.md", report_content)

            # Add evidence log
            evidence_json = json.dumps(evidence_export, indent=2, default=str)
            zf.writestr(f"{package_name}/evidence_log.json", evidence_json)

            # Add hash verification file
            hash_chain = evidence_export.get("hash_chain", [])
            hash_content = self._generate_hash_verification_file(hash_chain)
            zf.writestr(f"{package_name}/evidence_log_hashes.txt", hash_content)

            # Add checklist states
            for phase_id, checklist in checklists.items():
                checklist_data = {
                    "phase_id": phase_id,
                    "phase_name": checklist.phase_name,
                    "progress": checklist.get_progress(),
                    "items": [
                        {
                            "id": item.id,
                            "text": item.text,
                            "status": item.status,
                            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                            "completed_by": item.completed_by,
                            "notes": item.notes,
                        }
                        for item in checklist.items
                    ],
                }
                zf.writestr(
                    f"{package_name}/checklists/{phase_id}.json",
                    json.dumps(checklist_data, indent=2),
                )

            # Add decision logs
            decision_data = {
                "trees": [
                    {
                        "id": tree.id,
                        "name": tree.name,
                        "phase": tree.phase,
                        "completed": tree.completed,
                        "decisions": [
                            {
                                "node_id": p.node_id,
                                "option": p.selected_option_label,
                                "confidence": p.confidence,
                                "rationale": p.rationale,
                                "timestamp": p.decided_at.isoformat(),
                                "operator": p.operator,
                            }
                            for p in tree.path_taken
                        ],
                    }
                    for tree in decision_trees
                ]
            }
            zf.writestr(
                f"{package_name}/decisions/decision_log.json",
                json.dumps(decision_data, indent=2),
            )

            # Add incident metadata
            metadata = {
                "incident_id": incident.id,
                "title": incident.title,
                "severity": incident.severity,
                "status": incident.status,
                "is_simulation": incident.is_simulation,
                "created_at": incident.created_at.isoformat(),
                "package_generated_at": datetime.now(timezone.utc).isoformat(),
                "analyst": incident.analyst_name,
                "cyberops_companion_version": self.config.version,
            }
            zf.writestr(
                f"{package_name}/metadata.json",
                json.dumps(metadata, indent=2),
            )

        return zip_path

    def _generate_hash_verification_file(self, hash_chain: List[dict]) -> str:
        """Generate a human-readable hash verification file."""
        lines = [
            "# Evidence Log Hash Verification",
            f"# Generated: {datetime.now(timezone.utc).isoformat()}",
            "#",
            "# Each entry's hash is computed from its content and the previous entry's hash,",
            "# forming an append-only chain that detects any tampering.",
            "#",
            "# Format: SEQUENCE | ENTRY_ID | TIMESTAMP | HASH",
            "#" + "=" * 70,
            "",
        ]

        for entry in hash_chain:
            lines.append(
                f"{entry['sequence']:04d} | {entry['entry_id']} | "
                f"{entry['timestamp'][:19]} | {entry['entry_hash'][:32]}..."
            )

        lines.append("")
        lines.append(f"# Total entries: {len(hash_chain)}")

        if hash_chain:
            # Compute verification hash of the entire chain
            chain_str = json.dumps(hash_chain, sort_keys=True)
            chain_hash = hashlib.sha256(chain_str.encode()).hexdigest()
            lines.append(f"# Chain verification hash: {chain_hash}")

        return "\n".join(lines)

    def export_report_only(
        self,
        incident: Incident,
        phase_tracker: IncidentPhaseTracker,
        checklists: Dict[str, ChecklistPhase],
        decision_trees: List[DecisionTree],
        evidence_export: dict,
        lessons_learned: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Export just the Markdown report (without ZIP packaging).

        Returns:
            Path to the created Markdown file
        """
        output_dir = output_dir or EXPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        report_content = self.generate_incident_report(
            incident=incident,
            phase_tracker=phase_tracker,
            checklists=checklists,
            decision_trees=decision_trees,
            evidence_export=evidence_export,
            lessons_learned=lessons_learned,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"incident_report_{incident.id}_{timestamp}.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_path
