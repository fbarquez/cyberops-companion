"""
Decision Engine

Manages decision trees with confidence indicators for guided decision-making.
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

from src.models.decision import (
    DecisionNode,
    DecisionOption,
    DecisionTree,
    DecisionPath,
    ConfidenceLevel,
)
from src.models.phase import IRPhase
from config import PLAYBOOKS_DIR


class DecisionEngine:
    """
    Manages decision trees for incident response.

    Features:
    - Load decision trees from playbook definitions
    - Track decision paths taken
    - Provide confidence indicators
    - Support multiple decision trees per phase
    """

    def __init__(self, playbook_name: str = "ransomware"):
        """
        Initialize the decision engine.

        Args:
            playbook_name: Name of the playbook to load trees from
        """
        self.playbook_name = playbook_name
        self.decision_trees: Dict[str, DecisionTree] = {}
        self._load_decision_trees()

    def _load_decision_trees(self) -> None:
        """Load decision tree definitions from playbook."""
        trees_path = PLAYBOOKS_DIR / f"{self.playbook_name}_decisions.json"

        if trees_path.exists():
            with open(trees_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for tree_data in data.get("trees", []):
                    tree = DecisionTree(**tree_data)
                    self.decision_trees[tree.id] = tree
        else:
            # Load default decision trees
            self._load_default_trees()

    def _load_default_trees(self) -> None:
        """Create default decision tree definitions."""
        # Containment Strategy Decision Tree
        containment_tree = DecisionTree(
            id="containment_strategy",
            name="Containment Strategy",
            description="Determine the appropriate containment approach",
            phase=IRPhase.CONTAINMENT.value,
            entry_node_id="contain_start",
            nodes=[
                DecisionNode(
                    id="contain_start",
                    phase=IRPhase.CONTAINMENT.value,
                    title="Initial Containment Assessment",
                    question="Is the affected system still running and accessible?",
                    context="The system state determines our containment options and evidence preservation capabilities.",
                    options=[
                        DecisionOption(
                            id="system_running",
                            label="Yes - System is running",
                            description="System is powered on and responsive",
                            confidence=ConfidenceLevel.HIGH,
                            recommended=True,
                            next_node_id="memory_capture_available",
                        ),
                        DecisionOption(
                            id="system_off",
                            label="No - System is off/inaccessible",
                            description="System is powered off or not responding",
                            confidence=ConfidenceLevel.MEDIUM,
                            next_node_id="disk_imaging",
                        ),
                    ],
                    order=1,
                ),
                DecisionNode(
                    id="memory_capture_available",
                    phase=IRPhase.CONTAINMENT.value,
                    title="Memory Capture Capability",
                    question="Is memory capture tooling available and tested?",
                    context="Volatile memory contains valuable forensic evidence that is lost on shutdown.",
                    help_text="Memory capture tools include: WinPMEM, FTK Imager, DumpIt",
                    options=[
                        DecisionOption(
                            id="memory_yes",
                            label="Yes - Tools available",
                            description="Memory capture tools are ready to use",
                            confidence=ConfidenceLevel.HIGH,
                            recommended=True,
                            next_node_id="isolation_method",
                            checklist_items_to_complete=["ANA-001"],
                        ),
                        DecisionOption(
                            id="memory_no",
                            label="No - Tools not available",
                            description="Cannot capture memory, proceed with caution",
                            confidence=ConfidenceLevel.MEDIUM,
                            warning="Volatile evidence will be lost",
                            next_node_id="isolation_method",
                        ),
                    ],
                    order=2,
                ),
                DecisionNode(
                    id="isolation_method",
                    phase=IRPhase.CONTAINMENT.value,
                    title="Isolation Method",
                    question="How should the affected system be isolated?",
                    context="Network isolation prevents further spread while preserving evidence.",
                    options=[
                        DecisionOption(
                            id="network_isolate",
                            label="Network Isolation",
                            description="Disconnect network cable or disable NIC. System remains powered on.",
                            confidence=ConfidenceLevel.HIGH,
                            recommended=True,
                            checklist_items_to_complete=["CON-001"],
                        ),
                        DecisionOption(
                            id="vlan_isolate",
                            label="VLAN Isolation",
                            description="Move to isolated VLAN via switch configuration",
                            confidence=ConfidenceLevel.HIGH,
                        ),
                        DecisionOption(
                            id="full_shutdown",
                            label="Full Shutdown",
                            description="Power off the system immediately",
                            confidence=ConfidenceLevel.LOW,
                            warning="This will DESTROY volatile memory evidence. Only use if active encryption is ongoing and cannot be stopped otherwise.",
                            modifies_evidence=True,
                            requires_confirmation=True,
                        ),
                    ],
                    order=3,
                ),
                DecisionNode(
                    id="disk_imaging",
                    phase=IRPhase.CONTAINMENT.value,
                    title="Disk Imaging Decision",
                    question="Should a forensic disk image be created?",
                    context="Disk imaging preserves evidence for later analysis.",
                    options=[
                        DecisionOption(
                            id="image_yes",
                            label="Yes - Create forensic image",
                            description="Create bit-for-bit copy before any remediation",
                            confidence=ConfidenceLevel.HIGH,
                            recommended=True,
                            checklist_items_to_complete=["CON-004"],
                        ),
                        DecisionOption(
                            id="image_no",
                            label="No - Proceed without imaging",
                            description="Skip imaging due to time/resource constraints",
                            confidence=ConfidenceLevel.LOW,
                            warning="Evidence may be lost during remediation",
                        ),
                    ],
                    order=4,
                ),
            ],
        )

        # Analysis Scope Decision Tree
        analysis_tree = DecisionTree(
            id="analysis_scope",
            name="Analysis Scope Determination",
            description="Determine the scope of the compromise",
            phase=IRPhase.ANALYSIS.value,
            entry_node_id="scope_start",
            nodes=[
                DecisionNode(
                    id="scope_start",
                    phase=IRPhase.ANALYSIS.value,
                    title="Lateral Movement Assessment",
                    question="Have you identified potential lateral movement indicators?",
                    context="Lateral movement suggests the compromise extends beyond the initially affected system.",
                    options=[
                        DecisionOption(
                            id="lateral_yes",
                            label="Yes - Lateral movement detected",
                            description="Evidence of attacker moving to other systems",
                            confidence=ConfidenceLevel.HIGH,
                            next_node_id="scope_expansion",
                        ),
                        DecisionOption(
                            id="lateral_no",
                            label="No - No lateral movement found",
                            description="Compromise appears limited to initial system",
                            confidence=ConfidenceLevel.MEDIUM,
                            next_node_id="single_system",
                        ),
                        DecisionOption(
                            id="lateral_uncertain",
                            label="Uncertain - Need more analysis",
                            description="Insufficient data to determine",
                            confidence=ConfidenceLevel.LOW,
                            next_node_id="additional_analysis",
                        ),
                    ],
                    order=1,
                ),
                DecisionNode(
                    id="scope_expansion",
                    phase=IRPhase.ANALYSIS.value,
                    title="Scope Expansion",
                    question="How many additional systems may be affected?",
                    context="This helps determine containment priority and resource needs.",
                    options=[
                        DecisionOption(
                            id="few_systems",
                            label="Few systems (< 5)",
                            description="Limited spread, manageable scope",
                            confidence=ConfidenceLevel.MEDIUM,
                        ),
                        DecisionOption(
                            id="many_systems",
                            label="Many systems (5-50)",
                            description="Significant spread, may need additional resources",
                            confidence=ConfidenceLevel.MEDIUM,
                        ),
                        DecisionOption(
                            id="widespread",
                            label="Widespread (50+)",
                            description="Major incident, escalate immediately",
                            confidence=ConfidenceLevel.HIGH,
                            warning="Consider activating full incident response team",
                        ),
                    ],
                    order=2,
                ),
                DecisionNode(
                    id="single_system",
                    phase=IRPhase.ANALYSIS.value,
                    title="Single System Confirmation",
                    question="Have you confirmed the compromise is limited to one system?",
                    options=[
                        DecisionOption(
                            id="confirmed_single",
                            label="Yes - Confirmed single system",
                            description="Analysis confirms isolated incident",
                            confidence=ConfidenceLevel.HIGH,
                            recommended=True,
                        ),
                        DecisionOption(
                            id="not_confirmed",
                            label="No - Still investigating",
                            description="Continue analysis before concluding",
                            confidence=ConfidenceLevel.MEDIUM,
                            next_node_id="additional_analysis",
                        ),
                    ],
                    order=3,
                ),
                DecisionNode(
                    id="additional_analysis",
                    phase=IRPhase.ANALYSIS.value,
                    title="Additional Analysis Required",
                    question="What additional analysis is needed?",
                    options=[
                        DecisionOption(
                            id="auth_logs",
                            label="Review authentication logs",
                            description="Check for suspicious login activity",
                            confidence=ConfidenceLevel.HIGH,
                            checklist_items_to_complete=["ANA-006"],
                        ),
                        DecisionOption(
                            id="network_logs",
                            label="Review network traffic",
                            description="Analyze firewall and proxy logs",
                            confidence=ConfidenceLevel.HIGH,
                        ),
                        DecisionOption(
                            id="endpoint_scan",
                            label="Run endpoint scans",
                            description="Scan other systems for IOCs",
                            confidence=ConfidenceLevel.MEDIUM,
                        ),
                    ],
                    order=4,
                ),
            ],
        )

        self.decision_trees = {
            containment_tree.id: containment_tree,
            analysis_tree.id: analysis_tree,
        }

    def get_tree(self, tree_id: str) -> Optional[DecisionTree]:
        """Get a decision tree by ID."""
        return self.decision_trees.get(tree_id)

    def get_trees_for_phase(self, phase: str) -> List[DecisionTree]:
        """Get all decision trees for a specific phase."""
        return [tree for tree in self.decision_trees.values() if tree.phase == phase]

    def create_incident_tree(self, tree_id: str) -> Optional[DecisionTree]:
        """
        Create a fresh copy of a decision tree for an incident.

        Returns a copy that can be modified without affecting the template.
        """
        template = self.get_tree(tree_id)
        if not template:
            return None

        # Deep copy the tree
        nodes = [DecisionNode(**node.model_dump()) for node in template.nodes]

        return DecisionTree(
            id=template.id,
            name=template.name,
            description=template.description,
            phase=template.phase,
            nodes=nodes,
            entry_node_id=template.entry_node_id,
        )

    def get_current_node(self, tree: DecisionTree) -> Optional[DecisionNode]:
        """Get the current active node in a decision tree."""
        return tree.get_current_node()

    def make_decision(
        self,
        tree: DecisionTree,
        incident_id: str,
        option_id: str,
        operator: str,
        rationale: Optional[str] = None,
    ) -> DecisionPath:
        """
        Record a decision and advance the tree.

        Args:
            tree: The decision tree being navigated
            incident_id: ID of the incident
            option_id: ID of the selected option
            operator: Name of the operator making the decision
            rationale: Optional explanation for the decision

        Returns:
            DecisionPath record of the decision
        """
        return tree.record_decision(
            incident_id=incident_id,
            option_id=option_id,
            operator=operator,
            rationale=rationale,
        )

    def get_decision_history(self, tree: DecisionTree) -> List[DecisionPath]:
        """Get the history of decisions made in a tree."""
        return tree.path_taken

    def export_decision_path(self, tree: DecisionTree) -> dict:
        """Export the decision path for reporting."""
        return {
            "tree_id": tree.id,
            "tree_name": tree.name,
            "phase": tree.phase,
            "completed": tree.completed,
            "decisions": [
                {
                    "node_id": path.node_id,
                    "selected_option": path.selected_option_label,
                    "confidence": path.confidence,
                    "rationale": path.rationale,
                    "decided_at": path.decided_at.isoformat(),
                    "operator": path.operator,
                }
                for path in tree.path_taken
            ],
        }

    def get_all_decisions_for_incident(
        self, trees: List[DecisionTree]
    ) -> List[dict]:
        """Get all decisions made across multiple trees."""
        all_decisions = []

        for tree in trees:
            for path in tree.path_taken:
                all_decisions.append(
                    {
                        "tree_id": tree.id,
                        "tree_name": tree.name,
                        "phase": tree.phase,
                        "node_id": path.node_id,
                        "selected_option": path.selected_option_label,
                        "confidence": path.confidence,
                        "rationale": path.rationale,
                        "decided_at": path.decided_at,
                        "operator": path.operator,
                    }
                )

        # Sort by timestamp
        all_decisions.sort(key=lambda x: x["decided_at"])
        return all_decisions
