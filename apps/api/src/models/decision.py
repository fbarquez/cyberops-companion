"""Decision tree and path tracking models."""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Text, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class ConfidenceLevel(str, enum.Enum):
    """Confidence level for decision options."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionNode(Base):
    """A decision point in the IR process."""
    __tablename__ = "decision_nodes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    node_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    tree_id: Mapped[str] = mapped_column(String(100), index=True)
    phase: Mapped[str] = mapped_column(String(50), index=True)

    # Node content
    title: Mapped[str] = mapped_column(String(500))
    title_de: Mapped[str] = mapped_column(String(500))  # German
    question: Mapped[str] = mapped_column(Text)
    question_de: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    help_text_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Options (JSON array of DecisionOption)
    options: Mapped[List[dict]] = mapped_column(JSON, default=list)

    # Prerequisites
    requires_checklist_items: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    requires_decisions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # Navigation
    is_entry_node: Mapped[bool] = mapped_column(Boolean, default=False)


class DecisionTree(Base):
    """Collection of decision nodes forming a tree."""
    __tablename__ = "decision_trees"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    tree_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phase: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255))
    name_de: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entry_node_id: Mapped[str] = mapped_column(String(100))


class DecisionPath(Base):
    """Record of a decision made during incident handling."""
    __tablename__ = "decision_paths"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    tree_id: Mapped[str] = mapped_column(String(100), index=True)
    node_id: Mapped[str] = mapped_column(String(100))
    selected_option_id: Mapped[str] = mapped_column(String(100))
    selected_option_label: Mapped[str] = mapped_column(String(500))

    # Decision context
    confidence: Mapped[Optional[ConfidenceLevel]] = mapped_column(
        Enum(ConfidenceLevel), nullable=True
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Operator info
    decided_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id")
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Navigation result
    next_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    next_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Flags
    modifies_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    was_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class IncidentDecisionState(Base):
    """Tracks current decision state for an incident."""
    __tablename__ = "incident_decision_states"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"),
        unique=True, index=True
    )
    tree_id: Mapped[str] = mapped_column(String(100))
    current_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    path_taken: Mapped[List[str]] = mapped_column(JSON, default=list)  # List of node_ids
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
