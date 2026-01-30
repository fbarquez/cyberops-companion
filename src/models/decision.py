"""
Decision tree data model.

Supports guided decision-making with confidence indicators.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for a decision option."""
    HIGH = "high"      # Well-established procedure, tested
    MEDIUM = "medium"  # Standard practice, context-dependent
    LOW = "low"        # Situational judgment required


class DecisionOption(BaseModel):
    """
    Single option within a decision node.

    Each option represents a possible path forward with associated
    confidence level and consequences.
    """

    id: str
    label: str
    description: str

    # Guidance
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    recommended: bool = Field(default=False)
    warning: Optional[str] = None  # Warning if this option has risks

    # Navigation
    next_node_id: Optional[str] = None  # Next decision node (if any)
    next_phase: Optional[str] = None  # Phase transition (if any)
    checklist_items_to_complete: List[str] = Field(default_factory=list)

    # Forensic implications
    modifies_evidence: bool = Field(default=False)
    requires_confirmation: bool = Field(default=False)

    class Config:
        use_enum_values = True


class DecisionNode(BaseModel):
    """
    Single decision point in the IR process.

    Presents a question with multiple options and tracks the decision made.
    """

    # Identification
    id: str
    phase: str

    # Content
    title: str
    question: str
    context: Optional[str] = None  # Additional context/explanation
    help_text: Optional[str] = None

    # Options
    options: List[DecisionOption] = Field(default_factory=list)

    # Prerequisites
    requires_checklist_items: List[str] = Field(default_factory=list)
    requires_decisions: List[str] = Field(default_factory=list)

    # Display order
    order: int = Field(default=0)

    def get_recommended_option(self) -> Optional[DecisionOption]:
        """Get the recommended option, if any."""
        for option in self.options:
            if option.recommended:
                return option
        return None

    def get_option(self, option_id: str) -> Optional[DecisionOption]:
        """Get a specific option by ID."""
        for option in self.options:
            if option.id == option_id:
                return option
        return None


class DecisionPath(BaseModel):
    """
    Record of a decision made during incident response.

    Captures the full context of why a decision was made.
    """

    # Identification
    id: str = Field(
        default_factory=lambda: f"DEC-{datetime.now().strftime('%H%M%S')}"
    )
    incident_id: str
    node_id: str

    # The decision
    selected_option_id: str
    selected_option_label: str
    confidence: ConfidenceLevel

    # Context
    rationale: Optional[str] = None  # Why this option was chosen
    operator: str = Field(default="")

    # Timestamp
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Navigation result
    next_node_id: Optional[str] = None
    next_phase: Optional[str] = None

    class Config:
        use_enum_values = True

    def to_log_entry(self) -> dict:
        """Convert to evidence log entry format."""
        return {
            "entry_type": "decision",
            "description": f"Decision: {self.selected_option_label}",
            "decision_node_id": self.node_id,
            "decision_option_selected": self.selected_option_id,
            "decision_rationale": self.rationale,
        }


class DecisionTree(BaseModel):
    """
    Complete decision tree for a phase or scenario.

    Contains all decision nodes and tracks the path taken.
    """

    id: str
    name: str
    description: str
    phase: str

    # Nodes
    nodes: List[DecisionNode] = Field(default_factory=list)
    entry_node_id: str  # First node in the tree

    # State tracking
    current_node_id: Optional[str] = None
    completed: bool = Field(default=False)
    path_taken: List[DecisionPath] = Field(default_factory=list)

    def get_node(self, node_id: str) -> Optional[DecisionNode]:
        """Get a specific node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_entry_node(self) -> Optional[DecisionNode]:
        """Get the entry node of the tree."""
        return self.get_node(self.entry_node_id)

    def get_current_node(self) -> Optional[DecisionNode]:
        """Get the current active node."""
        if self.current_node_id:
            return self.get_node(self.current_node_id)
        return self.get_entry_node()

    def record_decision(
        self,
        incident_id: str,
        option_id: str,
        operator: str,
        rationale: Optional[str] = None,
    ) -> DecisionPath:
        """
        Record a decision and advance to next node.

        Returns the DecisionPath record.
        """
        current = self.get_current_node()
        if not current:
            raise ValueError("No current node to make decision on")

        option = current.get_option(option_id)
        if not option:
            raise ValueError(f"Invalid option ID: {option_id}")

        # Create decision record
        path = DecisionPath(
            incident_id=incident_id,
            node_id=current.id,
            selected_option_id=option.id,
            selected_option_label=option.label,
            confidence=option.confidence,
            rationale=rationale,
            operator=operator,
            next_node_id=option.next_node_id,
            next_phase=option.next_phase,
        )

        self.path_taken.append(path)

        # Advance to next node
        if option.next_node_id:
            self.current_node_id = option.next_node_id
        else:
            self.completed = True
            self.current_node_id = None

        return path

    def get_summary(self) -> dict:
        """Get summary of decisions made."""
        return {
            "tree_id": self.id,
            "tree_name": self.name,
            "total_nodes": len(self.nodes),
            "decisions_made": len(self.path_taken),
            "completed": self.completed,
            "current_node": self.current_node_id,
        }
