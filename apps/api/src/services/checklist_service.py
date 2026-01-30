"""Checklist management service."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.checklist import ChecklistItem, ChecklistStatus, ChecklistTemplate
from src.schemas.checklist import ChecklistItemComplete, ChecklistItemSkip, ChecklistPhaseResponse


class ChecklistService:
    """Service for checklist operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_checklist(self, incident_id: str, phase: str) -> List[ChecklistItem]:
        """Initialize checklist items for a phase from templates."""
        # Get templates for this phase
        result = await self.db.execute(
            select(ChecklistTemplate)
            .where(ChecklistTemplate.phase == phase)
            .order_by(ChecklistTemplate.order)
        )
        templates = result.scalars().all()

        # Create items from templates
        items = []
        for template in templates:
            item = ChecklistItem(
                id=str(uuid4()),
                incident_id=incident_id,
                item_id=template.item_id,
                phase=template.phase,
                text=template.text,
                help_text=template.help_text,
                warning=template.warning,
                mandatory=template.mandatory,
                forensic_critical=template.forensic_critical,
                order=template.order,
                depends_on=template.depends_on or [],
                blocks=template.blocks or [],
            )
            self.db.add(item)
            items.append(item)

        await self.db.flush()
        return items

    async def get_phase_checklist(
        self, incident_id: str, phase: str
    ) -> ChecklistPhaseResponse:
        """Get checklist for a phase."""
        result = await self.db.execute(
            select(ChecklistItem)
            .where(
                and_(
                    ChecklistItem.incident_id == incident_id,
                    ChecklistItem.phase == phase,
                )
            )
            .order_by(ChecklistItem.order)
        )
        items = list(result.scalars().all())

        # If no items exist, initialize from templates
        if not items:
            items = await self.initialize_checklist(incident_id, phase)

        # Calculate blocked status
        completed_ids = {
            item.item_id for item in items
            if item.status in [ChecklistStatus.COMPLETED, ChecklistStatus.SKIPPED]
        }

        items_with_blocked = []
        blocked_items = []
        for item in items:
            blockers = [
                dep for dep in (item.depends_on or [])
                if dep not in completed_ids
            ]
            is_blocked = len(blockers) > 0

            if is_blocked:
                blocked_items.append(item.item_id)

            # Convert to response format with computed fields
            item_dict = {
                "id": item.id,
                "item_id": item.item_id,
                "phase": item.phase,
                "text": item.text,
                "help_text": item.help_text,
                "warning": item.warning,
                "mandatory": item.mandatory,
                "forensic_critical": item.forensic_critical,
                "order": item.order,
                "depends_on": item.depends_on or [],
                "blocks": item.blocks or [],
                "status": item.status,
                "completed_at": item.completed_at,
                "completed_by": item.completed_by,
                "notes": item.notes,
                "skip_reason": item.skip_reason,
                "is_blocked": is_blocked,
                "blockers": blockers,
            }
            items_with_blocked.append(item_dict)

        total = len(items)
        completed = len([i for i in items if i.status == ChecklistStatus.COMPLETED])
        mandatory_total = len([i for i in items if i.mandatory])
        mandatory_completed = len([
            i for i in items
            if i.mandatory and i.status == ChecklistStatus.COMPLETED
        ])

        can_advance = mandatory_completed >= mandatory_total

        return ChecklistPhaseResponse(
            incident_id=incident_id,
            phase=phase,
            items=items_with_blocked,
            total_items=total,
            completed_items=completed,
            mandatory_total=mandatory_total,
            mandatory_completed=mandatory_completed,
            progress_percent=(completed / total * 100) if total > 0 else 0,
            can_advance=can_advance,
            blocked_items=blocked_items,
        )

    async def complete_item(
        self,
        incident_id: str,
        phase: str,
        item_id: str,
        user_id: str,
        data: ChecklistItemComplete,
    ) -> Optional[ChecklistItem]:
        """Mark a checklist item as completed."""
        result = await self.db.execute(
            select(ChecklistItem).where(
                and_(
                    ChecklistItem.incident_id == incident_id,
                    ChecklistItem.phase == phase,
                    ChecklistItem.item_id == item_id,
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        item.status = ChecklistStatus.COMPLETED
        item.completed_at = datetime.utcnow()
        item.completed_by = user_id
        item.notes = data.notes

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def skip_item(
        self,
        incident_id: str,
        phase: str,
        item_id: str,
        user_id: str,
        data: ChecklistItemSkip,
    ) -> Optional[ChecklistItem]:
        """Mark a checklist item as skipped."""
        result = await self.db.execute(
            select(ChecklistItem).where(
                and_(
                    ChecklistItem.incident_id == incident_id,
                    ChecklistItem.phase == phase,
                    ChecklistItem.item_id == item_id,
                )
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Cannot skip mandatory items without force
        if item.mandatory:
            raise ValueError("Cannot skip mandatory item")

        item.status = ChecklistStatus.SKIPPED
        item.completed_at = datetime.utcnow()
        item.completed_by = user_id
        item.skip_reason = data.skip_reason

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def can_advance_phase(self, incident_id: str, phase: str) -> dict:
        """Check if incident can advance to next phase."""
        checklist = await self.get_phase_checklist(incident_id, phase)

        blocking_items = []
        for item in checklist.items:
            if item["mandatory"] and item["status"] not in [
                ChecklistStatus.COMPLETED.value,
                ChecklistStatus.SKIPPED.value,
            ]:
                blocking_items.append({
                    "item_id": item["item_id"],
                    "text": item["text"],
                    "forensic_critical": item["forensic_critical"],
                })

        return {
            "can_advance": len(blocking_items) == 0,
            "blocking_items": blocking_items,
            "progress": checklist.progress_percent,
        }
