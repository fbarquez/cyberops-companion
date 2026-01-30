"""
Checklist data model.

Interactive checklists for each IR phase with forensic awareness.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ChecklistStatus(str, Enum):
    """Status of a checklist item."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


class ChecklistItem(BaseModel):
    """
    Single checklist item with forensic awareness.

    Items can be mandatory, forensic-critical, or have dependencies.
    """

    # Identification
    id: str
    phase: str

    # Content
    text: str
    help_text: Optional[str] = None
    warning: Optional[str] = None  # Forensic or safety warning

    # Classification
    mandatory: bool = Field(default=False)
    forensic_critical: bool = Field(default=False)  # Could affect evidence integrity
    order: int = Field(default=0)

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # Item IDs that must be completed first
    blocks: List[str] = Field(default_factory=list)  # Items that depend on this one

    # State (mutable)
    status: ChecklistStatus = Field(default=ChecklistStatus.NOT_STARTED)
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None
    skip_reason: Optional[str] = None  # Required if skipped

    class Config:
        use_enum_values = True

    def complete(self, operator: str, notes: Optional[str] = None) -> None:
        """Mark item as completed."""
        self.status = ChecklistStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.completed_by = operator
        if notes:
            self.notes = notes

    def skip(self, operator: str, reason: str) -> None:
        """Skip item with mandatory reason."""
        if not reason:
            raise ValueError("Skip reason is required")
        self.status = ChecklistStatus.SKIPPED
        self.completed_at = datetime.now(timezone.utc)
        self.completed_by = operator
        self.skip_reason = reason

    def mark_not_applicable(self, operator: str, reason: str) -> None:
        """Mark item as not applicable."""
        self.status = ChecklistStatus.NOT_APPLICABLE
        self.completed_at = datetime.now(timezone.utc)
        self.completed_by = operator
        self.skip_reason = reason

    def start(self) -> None:
        """Mark item as in progress."""
        self.status = ChecklistStatus.IN_PROGRESS

    def reset(self) -> None:
        """Reset item to not started."""
        self.status = ChecklistStatus.NOT_STARTED
        self.completed_at = None
        self.completed_by = None
        self.notes = None
        self.skip_reason = None

    def is_blocking(self) -> bool:
        """Check if this item is blocking other items."""
        return bool(self.blocks) and self.status not in [
            ChecklistStatus.COMPLETED,
            ChecklistStatus.SKIPPED,
            ChecklistStatus.NOT_APPLICABLE,
        ]

    def is_blocked(self, completed_items: set) -> bool:
        """Check if this item is blocked by uncompleted dependencies."""
        return bool(self.depends_on) and not all(
            dep in completed_items for dep in self.depends_on
        )


class ChecklistPhase(BaseModel):
    """
    Collection of checklist items for a single IR phase.

    Tracks overall phase completion and enforces dependencies.
    """

    phase_id: str
    phase_name: str
    description: str
    items: List[ChecklistItem] = Field(default_factory=list)

    def get_item(self, item_id: str) -> Optional[ChecklistItem]:
        """Get a specific item by ID."""
        for item in self.items:
            return item if item.id == item_id else None
        return None

    def get_completed_ids(self) -> set:
        """Get IDs of all completed/skipped/N/A items."""
        return {
            item.id
            for item in self.items
            if item.status
            in [
                ChecklistStatus.COMPLETED,
                ChecklistStatus.SKIPPED,
                ChecklistStatus.NOT_APPLICABLE,
            ]
        }

    def get_available_items(self) -> List[ChecklistItem]:
        """Get items that are not blocked and not yet completed."""
        completed = self.get_completed_ids()
        return [
            item
            for item in self.items
            if item.status == ChecklistStatus.NOT_STARTED
            and not item.is_blocked(completed)
        ]

    def get_blocked_items(self) -> List[ChecklistItem]:
        """Get items that are currently blocked."""
        completed = self.get_completed_ids()
        return [
            item
            for item in self.items
            if item.status == ChecklistStatus.NOT_STARTED
            and item.is_blocked(completed)
        ]

    def get_progress(self) -> dict:
        """Calculate phase progress."""
        total = len(self.items)
        if total == 0:
            return {"total": 0, "completed": 0, "percentage": 100}

        completed = len(self.get_completed_ids())
        return {
            "total": total,
            "completed": completed,
            "percentage": round((completed / total) * 100),
            "mandatory_remaining": len(
                [
                    i
                    for i in self.items
                    if i.mandatory and i.status == ChecklistStatus.NOT_STARTED
                ]
            ),
        }

    def can_advance(self) -> tuple[bool, List[str]]:
        """
        Check if phase can be advanced to next.

        Returns (can_advance, list of blocking reasons).
        """
        blocking_reasons = []

        for item in self.items:
            if item.mandatory and item.status == ChecklistStatus.NOT_STARTED:
                blocking_reasons.append(f"Mandatory item incomplete: {item.text}")

            if item.forensic_critical and item.status == ChecklistStatus.SKIPPED:
                if not item.skip_reason:
                    blocking_reasons.append(
                        f"Forensic-critical item skipped without reason: {item.text}"
                    )

        return len(blocking_reasons) == 0, blocking_reasons

    def to_summary(self) -> dict:
        """Generate phase summary for display."""
        progress = self.get_progress()
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "total_items": progress["total"],
            "completed_items": progress["completed"],
            "percentage": progress["percentage"],
            "can_advance": self.can_advance()[0],
        }
