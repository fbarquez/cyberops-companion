"""
Scenario Runner

Manages safe ransomware simulation scenarios for training purposes.
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
from dataclasses import dataclass, field
import json
import uuid

from config import SCENARIOS_DIR, get_config
from src.simulation.artifact_generator import ArtifactGenerator


@dataclass
class SimulationScenario:
    """Represents a simulation scenario configuration."""

    id: str
    name: str
    description: str
    difficulty: str  # beginner, intermediate, advanced

    # Scenario narrative
    background: str
    initial_situation: str
    objectives: List[str]

    # Artifacts to generate
    artifacts_config: Dict[str, Any] = field(default_factory=dict)

    # Expected findings for validation
    expected_findings: List[str] = field(default_factory=list)

    # Hints (optional, for training)
    hints: List[str] = field(default_factory=list)


class ScenarioRunner:
    """
    Runs safe ransomware simulation scenarios.

    IMPORTANT: This simulation creates SAFE artifacts that mimic
    ransomware indicators WITHOUT any actual malicious capability.

    Features:
    - Load scenario definitions
    - Generate safe simulation artifacts
    - Track simulation state
    - Cleanup artifacts after training
    """

    SIMULATION_MARKER = "[IR_COMPANION_SIMULATION]"

    def __init__(self):
        """Initialize the scenario runner."""
        self.config = get_config()
        self.scenarios: Dict[str, SimulationScenario] = {}
        self.artifact_generator = ArtifactGenerator()
        self.active_simulation: Optional[Dict[str, Any]] = None
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load scenario definitions from JSON files."""
        scenarios_file = SCENARIOS_DIR / "scenarios.json"

        if scenarios_file.exists():
            with open(scenarios_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for scenario_data in data.get("scenarios", []):
                    scenario = SimulationScenario(**scenario_data)
                    self.scenarios[scenario.id] = scenario
        else:
            # Create default scenarios
            self._create_default_scenarios()

    def _create_default_scenarios(self) -> None:
        """Create default scenario definitions."""
        corporate_workstation = SimulationScenario(
            id="corporate_workstation",
            name="Corporate Workstation Ransomware",
            description="A typical ransomware incident on a corporate workstation",
            difficulty="beginner",
            background="""
            You are the on-call security analyst at a mid-sized company.
            At 14:30, you receive a call from an employee in the Finance department
            reporting strange behavior on their workstation.
            """,
            initial_situation="""
            The employee reports:
            - A strange text file appeared on their desktop
            - Some of their files have unusual extensions
            - The computer seems slower than usual

            The workstation is still powered on and connected to the network.
            """,
            objectives=[
                "Preserve volatile evidence (memory) before taking containment actions",
                "Identify the ransomware variant based on available indicators",
                "Safely contain the affected system",
                "Document all findings and actions taken",
                "Determine if lateral movement occurred",
            ],
            artifacts_config={
                "ransom_note": {
                    "filename": "README_RANSOMWARE.txt",
                    "variant_name": "SimulatedLocker",
                },
                "encrypted_files": {
                    "count": 5,
                    "extension": ".encrypted_sim",
                },
                "registry_key": {
                    "path": "HKCU\\Software\\SimulatedMalware",
                },
                "process_artifacts": {
                    "suspicious_process": "simloader.exe",
                },
            },
            expected_findings=[
                "Ransom note with bitcoin address",
                "Files with .encrypted_sim extension",
                "Registry persistence key",
                "Suspicious process in execution history",
            ],
            hints=[
                "Check the desktop for any new text files",
                "Look for files with unusual extensions",
                "Memory capture should be done BEFORE network isolation",
                "Document the contents of the ransom note",
            ],
        )

        lateral_movement = SimulationScenario(
            id="lateral_movement",
            name="Ransomware with Lateral Movement",
            description="Ransomware incident with evidence of lateral movement",
            difficulty="intermediate",
            background="""
            Multiple departments have reported similar issues with their workstations.
            This suggests the ransomware may have spread beyond the initial infection point.
            """,
            initial_situation="""
            Reports from:
            - Finance department (2 workstations)
            - HR department (1 workstation)
            - IT admin workstation showing suspicious authentication events

            The incidents appear to have occurred within a 30-minute window.
            """,
            objectives=[
                "Identify all affected systems",
                "Determine the lateral movement method",
                "Identify potentially compromised credentials",
                "Coordinate containment across multiple systems",
                "Preserve evidence from multiple sources",
            ],
            artifacts_config={
                "ransom_note": {
                    "filename": "YOUR_FILES_ARE_ENCRYPTED.txt",
                    "variant_name": "LateralLocker",
                },
                "encrypted_files": {
                    "count": 10,
                    "extension": ".llocked",
                },
                "auth_logs": {
                    "suspicious_logins": 3,
                    "service_account_abuse": True,
                },
                "network_indicators": {
                    "internal_scanning": True,
                    "smb_activity": True,
                },
            },
            expected_findings=[
                "Multiple systems with ransomware indicators",
                "Suspicious authentication events",
                "Evidence of SMB lateral movement",
                "Potentially compromised service account",
            ],
            hints=[
                "Check authentication logs for unusual patterns",
                "Look for evidence of network scanning",
                "Service accounts are often targeted for lateral movement",
            ],
        )

        self.scenarios = {
            corporate_workstation.id: corporate_workstation,
            lateral_movement.id: lateral_movement,
        }

    def get_scenario(self, scenario_id: str) -> Optional[SimulationScenario]:
        """Get a scenario by ID."""
        return self.scenarios.get(scenario_id)

    def list_scenarios(self) -> List[Dict[str, str]]:
        """List all available scenarios."""
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "difficulty": s.difficulty,
            }
            for s in self.scenarios.values()
        ]

    def start_simulation(
        self,
        scenario_id: str,
        target_directory: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Start a simulation scenario.

        Args:
            scenario_id: ID of the scenario to run
            target_directory: Directory to place artifacts (optional)

        Returns:
            Simulation state dictionary
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        simulation_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        # Generate artifacts
        artifacts = self.artifact_generator.generate_artifacts(
            scenario=scenario,
            target_directory=target_directory,
            simulation_id=simulation_id,
        )

        self.active_simulation = {
            "simulation_id": simulation_id,
            "scenario_id": scenario_id,
            "scenario_name": scenario.name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "target_directory": str(target_directory) if target_directory else None,
            "artifacts": artifacts,
            "status": "active",
            "findings_recorded": [],
        }

        return self.active_simulation

    def get_simulation_status(self) -> Optional[Dict[str, Any]]:
        """Get the status of the active simulation."""
        return self.active_simulation

    def record_finding(self, finding: str) -> None:
        """Record a finding during the simulation."""
        if self.active_simulation:
            self.active_simulation["findings_recorded"].append({
                "finding": finding,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def get_scenario_briefing(self, scenario_id: str) -> Dict[str, Any]:
        """Get the briefing information for a scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        return {
            "name": scenario.name,
            "difficulty": scenario.difficulty,
            "background": scenario.background.strip(),
            "initial_situation": scenario.initial_situation.strip(),
            "objectives": scenario.objectives,
        }

    def get_hints(self, scenario_id: str) -> List[str]:
        """Get hints for a scenario (for training purposes)."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return []
        return scenario.hints

    def end_simulation(self) -> Dict[str, Any]:
        """
        End the active simulation and cleanup.

        Returns:
            Final simulation state with summary
        """
        if not self.active_simulation:
            raise ValueError("No active simulation to end")

        simulation = self.active_simulation

        # Cleanup artifacts
        cleanup_result = self.artifact_generator.cleanup(
            simulation_id=simulation["simulation_id"]
        )

        simulation["ended_at"] = datetime.now(timezone.utc).isoformat()
        simulation["status"] = "completed"
        simulation["cleanup_result"] = cleanup_result

        # Calculate basic metrics
        scenario = self.get_scenario(simulation["scenario_id"])
        if scenario:
            expected = set(scenario.expected_findings)
            found = set(f["finding"] for f in simulation["findings_recorded"])
            simulation["metrics"] = {
                "expected_findings": len(expected),
                "findings_recorded": len(simulation["findings_recorded"]),
            }

        result = simulation.copy()
        self.active_simulation = None

        return result

    def generate_training_report(
        self, simulation_result: Dict[str, Any]
    ) -> str:
        """
        Generate a training report from simulation results.

        Args:
            simulation_result: Result from end_simulation()

        Returns:
            Markdown formatted training report
        """
        scenario = self.get_scenario(simulation_result["scenario_id"])

        report = f"""# Simulation Training Report

## Scenario: {simulation_result['scenario_name']}

**Simulation ID:** {simulation_result['simulation_id']}
**Started:** {simulation_result['started_at']}
**Ended:** {simulation_result.get('ended_at', 'N/A')}

---

## Objectives

"""
        if scenario:
            for i, obj in enumerate(scenario.objectives, 1):
                report += f"{i}. {obj}\n"

        report += """
## Findings Recorded

"""
        for finding in simulation_result.get("findings_recorded", []):
            report += f"- [{finding['timestamp'][:19]}] {finding['finding']}\n"

        if scenario:
            report += """
## Expected Findings (Reference)

"""
            for finding in scenario.expected_findings:
                report += f"- {finding}\n"

        report += """
---

## Review Notes

*Add your lessons learned and observations here.*

"""
        return report
