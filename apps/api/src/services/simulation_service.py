"""
Simulation Service - Manages training simulations.

Provides:
- Loading simulation scenarios from data files
- Managing simulation sessions
- Tracking simulation progress
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SimulationArtifacts(BaseModel):
    """Artifacts configuration for a scenario."""
    ransom_note: Optional[Dict[str, str]] = None
    encrypted_files: Optional[Dict[str, Any]] = None
    registry_key: Optional[Dict[str, str]] = None
    process_artifacts: Optional[Dict[str, str]] = None
    auth_logs: Optional[Dict[str, Any]] = None
    network_indicators: Optional[Dict[str, Any]] = None
    exfiltration_indicators: Optional[Dict[str, Any]] = None


class Scenario(BaseModel):
    """A training simulation scenario."""
    id: str
    name: str
    description: str
    difficulty: str  # beginner, intermediate, advanced
    background: str
    initial_situation: str
    objectives: List[str] = Field(default_factory=list)
    artifacts_config: Optional[SimulationArtifacts] = None
    expected_findings: List[str] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)
    estimated_duration: str = "30 minutes"


class SimulationSession(BaseModel):
    """An active simulation session."""
    session_id: str
    scenario_id: str
    user_id: str
    started_at: str
    status: str = "active"  # active, paused, completed, abandoned
    current_phase: str = "detection"
    completed_objectives: List[str] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    hints_used: int = 0
    score: Optional[int] = None


class SimulationService:
    """Service for managing training simulations."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the simulation service.

        Args:
            data_dir: Directory containing scenario data files
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent.parent.parent / "data" / "scenarios"
        self._scenarios: Dict[str, Scenario] = {}
        self._sessions: Dict[str, SimulationSession] = {}
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load scenarios from data directory."""
        if not self.data_dir.exists():
            logger.warning(f"Scenarios data directory not found: {self.data_dir}")
            self._load_default_scenarios()
            return

        for scenario_file in self.data_dir.glob("*.json"):
            try:
                with open(scenario_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Handle both single scenario and array of scenarios
                    scenarios_data = data.get("scenarios", [data])
                    
                    for scenario_data in scenarios_data:
                        artifacts = None
                        if "artifacts_config" in scenario_data:
                            artifacts = SimulationArtifacts(**scenario_data["artifacts_config"])
                        
                        scenario = Scenario(
                            id=scenario_data.get("id", str(uuid.uuid4())),
                            name=scenario_data.get("name", "Unknown"),
                            description=scenario_data.get("description", ""),
                            difficulty=scenario_data.get("difficulty", "beginner"),
                            background=scenario_data.get("background", ""),
                            initial_situation=scenario_data.get("initial_situation", ""),
                            objectives=scenario_data.get("objectives", []),
                            artifacts_config=artifacts,
                            expected_findings=scenario_data.get("expected_findings", []),
                            hints=scenario_data.get("hints", []),
                            estimated_duration=scenario_data.get("estimated_duration", "30 minutes"),
                        )
                        self._scenarios[scenario.id] = scenario
                        logger.info(f"Loaded scenario: {scenario.id}")
            except Exception as e:
                logger.error(f"Failed to load scenarios from {scenario_file}: {e}")

        if not self._scenarios:
            self._load_default_scenarios()

    def _load_default_scenarios(self) -> None:
        """Load default scenarios if no data files found."""
        default_scenarios = [
            Scenario(
                id="corporate_workstation",
                name="Corporate Workstation Infection",
                description="Single workstation infected via email attachment - ideal for beginners",
                difficulty="beginner",
                background="You are the on-call security analyst at a mid-sized company.",
                initial_situation="An employee reports strange behavior on their workstation.",
                objectives=[
                    "Preserve volatile evidence (memory)",
                    "Identify the ransomware variant",
                    "Safely contain the affected system",
                    "Document all findings",
                ],
                hints=["Check the desktop for new text files", "Memory capture before network isolation"],
                estimated_duration="30 minutes",
            ),
            Scenario(
                id="lateral_movement",
                name="Lateral Movement Attack",
                description="Multi-system compromise with lateral movement - intermediate difficulty",
                difficulty="intermediate",
                background="Multiple departments are reporting issues.",
                initial_situation="Finance: 2 workstations affected. HR: 1 workstation affected.",
                objectives=[
                    "Identify all affected systems",
                    "Determine lateral movement method",
                    "Identify compromised credentials",
                    "Coordinate containment",
                ],
                hints=["Check authentication logs", "Look for PsExec usage"],
                estimated_duration="60 minutes",
            ),
            Scenario(
                id="enterprise_breach",
                name="Enterprise Data Breach",
                description="Large-scale breach with data exfiltration - advanced",
                difficulty="advanced",
                background="Attackers have been in the environment before deploying ransomware.",
                initial_situation="Large outbound data transfers detected. Ransomware deployed.",
                objectives=[
                    "Assess data exfiltration scope",
                    "Identify accessed/stolen data",
                    "Coordinate with legal/compliance",
                    "Preserve evidence for law enforcement",
                ],
                hints=["Check for large archive files", "Review firewall logs"],
                estimated_duration="120 minutes",
            ),
        ]
        for scenario in default_scenarios:
            self._scenarios[scenario.id] = scenario

    def get_scenarios(self, difficulty: Optional[str] = None) -> List[Scenario]:
        """
        Get available simulation scenarios.

        Args:
            difficulty: Optional filter by difficulty level

        Returns:
            List of scenarios
        """
        scenarios = list(self._scenarios.values())
        if difficulty:
            scenarios = [s for s in scenarios if s.difficulty == difficulty]
        return scenarios

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get a specific scenario by ID."""
        return self._scenarios.get(scenario_id)

    def start_simulation(
        self,
        scenario_id: str,
        user_id: str,
    ) -> SimulationSession:
        """
        Start a new simulation session.

        Args:
            scenario_id: ID of the scenario to run
            user_id: ID of the user starting the simulation

        Returns:
            New simulation session
        """
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        session = SimulationSession(
            session_id=str(uuid.uuid4()),
            scenario_id=scenario_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="active",
            current_phase="detection",
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SimulationSession]:
        """Get a simulation session by ID."""
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        current_phase: Optional[str] = None,
        completed_objectives: Optional[List[str]] = None,
        finding: Optional[Dict[str, Any]] = None,
        action: Optional[Dict[str, Any]] = None,
        use_hint: bool = False,
    ) -> Optional[SimulationSession]:
        """
        Update a simulation session.

        Args:
            session_id: Session to update
            current_phase: New phase (if advancing)
            completed_objectives: List of completed objective IDs
            finding: New finding to add
            action: New action to record
            use_hint: Whether a hint was used

        Returns:
            Updated session
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        if current_phase:
            session.current_phase = current_phase

        if completed_objectives:
            for obj in completed_objectives:
                if obj not in session.completed_objectives:
                    session.completed_objectives.append(obj)

        if finding:
            finding["timestamp"] = datetime.now(timezone.utc).isoformat()
            session.findings.append(finding)

        if action:
            action["timestamp"] = datetime.now(timezone.utc).isoformat()
            session.actions_taken.append(action)

        if use_hint:
            session.hints_used += 1

        return session

    def complete_simulation(self, session_id: str) -> Optional[SimulationSession]:
        """
        Complete a simulation session and calculate score.

        Args:
            session_id: Session to complete

        Returns:
            Completed session with score
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        scenario = self._scenarios.get(session.scenario_id)
        if not scenario:
            return None

        # Calculate score
        total_objectives = len(scenario.objectives)
        completed = len(session.completed_objectives)
        hint_penalty = session.hints_used * 5

        if total_objectives > 0:
            base_score = int((completed / total_objectives) * 100)
            session.score = max(0, base_score - hint_penalty)
        else:
            session.score = 100 - hint_penalty

        session.status = "completed"
        return session

    def get_scenario_artifacts(self, scenario_id: str) -> Dict[str, Any]:
        """
        Get simulated artifacts for a scenario.

        Args:
            scenario_id: Scenario to get artifacts for

        Returns:
            Dictionary of simulated artifacts
        """
        scenario = self._scenarios.get(scenario_id)
        if not scenario or not scenario.artifacts_config:
            return {}

        artifacts = {}
        config = scenario.artifacts_config

        if config.ransom_note:
            artifacts["ransom_note"] = {
                "filename": config.ransom_note.get("filename", "README.txt"),
                "content": self._generate_ransom_note(config.ransom_note.get("variant_name", "Unknown")),
            }

        if config.encrypted_files:
            artifacts["encrypted_files"] = [
                {
                    "original_name": f"document_{i}.docx",
                    "encrypted_name": f"document_{i}.docx{config.encrypted_files.get('extension', '.encrypted')}",
                    "size": 1024 * (i + 1),
                }
                for i in range(config.encrypted_files.get("count", 3))
            ]

        if config.process_artifacts:
            artifacts["suspicious_processes"] = [
                {
                    "name": config.process_artifacts.get("suspicious_process", "unknown.exe"),
                    "pid": 1234,
                    "parent_pid": 4,
                    "command_line": f"C:\\Temp\\{config.process_artifacts.get('suspicious_process', 'unknown.exe')}",
                }
            ]

        return artifacts

    def _generate_ransom_note(self, variant_name: str) -> str:
        """Generate a simulated ransom note."""
        return f"""
=== YOUR FILES HAVE BEEN ENCRYPTED ===

This is a SIMULATION for training purposes.

Variant: {variant_name}

Your important files have been encrypted. To decrypt them, you must:
1. Do NOT attempt to decrypt files yourself
2. Contact your security team immediately
3. Follow proper incident response procedures

This is a training simulation. No actual encryption has occurred.

SIMULATION BITCOIN ADDRESS: 1SimulatedAddress12345
SIMULATION DECRYPTION ID: SIM-{uuid.uuid4().hex[:8].upper()}

=== END OF SIMULATED RANSOM NOTE ===
"""


# Singleton instance
_simulation_service: Optional[SimulationService] = None


def get_simulation_service() -> SimulationService:
    """Get the simulation service singleton."""
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service
