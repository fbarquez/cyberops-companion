"""Decision schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.decision import ConfidenceLevel


class DecisionOptionResponse(BaseModel):
    """Schema for decision option."""
    id: str
    label: str
    description: Optional[str] = None
    confidence: Optional[ConfidenceLevel] = None
    recommended: bool = False
    warning: Optional[str] = None
    next_node_id: Optional[str] = None
    next_phase: Optional[str] = None
    checklist_items_to_complete: List[str] = []
    modifies_evidence: bool = False
    requires_confirmation: bool = False


class DecisionNodeResponse(BaseModel):
    """Schema for decision node response."""
    id: str
    node_id: str
    tree_id: str
    phase: str
    title: str
    question: str
    context: Optional[str] = None
    help_text: Optional[str] = None
    options: List[DecisionOptionResponse]
    requires_checklist_items: List[str] = []
    requires_decisions: List[str] = []
    is_entry_node: bool
    is_available: bool = True  # Computed based on prerequisites
    blocked_by: List[str] = []  # Computed - what blocks this node

    class Config:
        from_attributes = True


class DecisionTreeResponse(BaseModel):
    """Schema for decision tree response."""
    id: str
    tree_id: str
    phase: str
    name: str
    description: Optional[str] = None
    entry_node_id: str
    current_node_id: Optional[str] = None
    completed: bool
    path_taken: List[str] = []
    total_nodes: int
    completed_nodes: int


class DecisionMake(BaseModel):
    """Schema for making a decision."""
    option_id: str
    rationale: Optional[str] = None
    confirm: bool = False  # For decisions requiring confirmation


class DecisionPathResponse(BaseModel):
    """Schema for decision path response."""
    id: str
    incident_id: str
    tree_id: str
    node_id: str
    selected_option_id: str
    selected_option_label: str
    confidence: Optional[ConfidenceLevel] = None
    rationale: Optional[str] = None
    decided_by: str
    decided_at: datetime
    next_node_id: Optional[str] = None
    next_phase: Optional[str] = None
    modifies_evidence: bool
    requires_confirmation: bool
    was_confirmed: bool

    class Config:
        from_attributes = True


class DecisionHistoryResponse(BaseModel):
    """Schema for decision history."""
    incident_id: str
    total_decisions: int
    decisions: List[DecisionPathResponse]
    trees_completed: List[str]
    trees_in_progress: List[str]
