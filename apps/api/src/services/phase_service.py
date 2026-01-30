"""Phase tracking service."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.phase import PhaseProgress, PhaseStatus, IRPhase, PhaseDefinition
from src.schemas.phase import PhaseProgressResponse, PhaseTimelineResponse, PhaseTimelineEntry


class PhaseService:
    """Service for phase tracking operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_phase_progress(
        self, incident_id: str, phase: IRPhase
    ) -> PhaseProgress:
        """Get or create phase progress record."""
        result = await self.db.execute(
            select(PhaseProgress).where(
                and_(
                    PhaseProgress.incident_id == incident_id,
                    PhaseProgress.phase == phase,
                )
            )
        )
        progress = result.scalar_one_or_none()

        if not progress:
            progress = PhaseProgress(
                id=str(uuid4()),
                incident_id=incident_id,
                phase=phase,
                status=PhaseStatus.NOT_STARTED,
            )
            self.db.add(progress)
            await self.db.flush()
            await self.db.refresh(progress)

        return progress

    async def start_phase(self, incident_id: str, phase: IRPhase) -> PhaseProgress:
        """Mark a phase as started."""
        progress = await self.get_phase_progress(incident_id, phase)

        if progress.status == PhaseStatus.NOT_STARTED:
            progress.status = PhaseStatus.IN_PROGRESS
            progress.started_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(progress)

        return progress

    async def complete_phase(
        self, incident_id: str, phase: IRPhase, notes: Optional[str] = None
    ) -> PhaseProgress:
        """Mark a phase as completed."""
        progress = await self.get_phase_progress(incident_id, phase)

        progress.status = PhaseStatus.COMPLETED
        progress.completed_at = datetime.utcnow()
        progress.notes = notes

        if progress.started_at:
            delta = progress.completed_at - progress.started_at
            progress.duration_seconds = int(delta.total_seconds())

        await self.db.flush()
        await self.db.refresh(progress)
        return progress

    async def update_progress(
        self,
        incident_id: str,
        phase: IRPhase,
        checklist_total: int = 0,
        checklist_completed: int = 0,
        mandatory_total: int = 0,
        mandatory_completed: int = 0,
        decisions_required: int = 0,
        decisions_made: int = 0,
        evidence_count: int = 0,
    ) -> PhaseProgress:
        """Update phase progress metrics."""
        progress = await self.get_phase_progress(incident_id, phase)

        progress.checklist_total = checklist_total
        progress.checklist_completed = checklist_completed
        progress.mandatory_total = mandatory_total
        progress.mandatory_completed = mandatory_completed
        progress.decisions_required = decisions_required
        progress.decisions_made = decisions_made
        progress.evidence_count = evidence_count

        await self.db.flush()
        await self.db.refresh(progress)
        return progress

    async def get_timeline(self, incident_id: str) -> PhaseTimelineResponse:
        """Get complete phase timeline for an incident."""
        result = await self.db.execute(
            select(PhaseProgress)
            .where(PhaseProgress.incident_id == incident_id)
            .order_by(PhaseProgress.phase)
        )
        progress_records = {p.phase: p for p in result.scalars().all()}

        timeline = []
        total_duration = 0
        started_at = None

        for phase in IRPhase:
            progress = progress_records.get(phase)
            if progress:
                entry = PhaseTimelineEntry(
                    phase=phase,
                    status=progress.status,
                    started_at=progress.started_at,
                    completed_at=progress.completed_at,
                    duration_seconds=progress.duration_seconds,
                    evidence_count=progress.evidence_count,
                    decisions_count=progress.decisions_made,
                )
                if progress.duration_seconds:
                    total_duration += progress.duration_seconds
                if progress.started_at and (not started_at or progress.started_at < started_at):
                    started_at = progress.started_at
            else:
                entry = PhaseTimelineEntry(
                    phase=phase,
                    status=PhaseStatus.NOT_STARTED,
                    evidence_count=0,
                    decisions_count=0,
                )
            timeline.append(entry)

        # Determine current phase
        current_phase = IRPhase.DETECTION
        for entry in timeline:
            if entry.status == PhaseStatus.IN_PROGRESS:
                current_phase = entry.phase
                break
            elif entry.status == PhaseStatus.COMPLETED:
                idx = list(IRPhase).index(entry.phase)
                if idx < len(IRPhase) - 1:
                    current_phase = list(IRPhase)[idx + 1]

        return PhaseTimelineResponse(
            incident_id=incident_id,
            current_phase=current_phase,
            timeline=timeline,
            total_duration_seconds=total_duration if total_duration > 0 else None,
            started_at=started_at,
        )

    async def get_definition(self, phase: IRPhase, lang: str = "en") -> Optional[dict]:
        """Get phase definition with guidance."""
        result = await self.db.execute(
            select(PhaseDefinition).where(PhaseDefinition.phase == phase)
        )
        definition = result.scalar_one_or_none()

        if not definition:
            return None

        is_german = lang == "de"
        return {
            "phase": phase.value,
            "name": definition.name_de if is_german else definition.name,
            "description": definition.description_de if is_german else definition.description,
            "objectives": definition.objectives_de if is_german else definition.objectives,
            "key_questions": definition.key_questions_de if is_german else definition.key_questions,
            "critical_reminders": definition.critical_reminders_de if is_german else definition.critical_reminders,
            "common_mistakes": definition.common_mistakes_de if is_german else definition.common_mistakes,
            "forensic_considerations": definition.forensic_considerations_de if is_german else definition.forensic_considerations,
            "icon": definition.icon,
            "color": definition.color,
            "order": definition.order,
        }

    async def can_advance(self, incident_id: str, phase: IRPhase) -> dict:
        """Check if incident can advance from current phase."""
        progress = await self.get_phase_progress(incident_id, phase)

        # Check mandatory checklist items
        mandatory_complete = progress.mandatory_completed >= progress.mandatory_total

        # Check required decisions
        decisions_complete = progress.decisions_made >= progress.decisions_required

        can_advance = mandatory_complete and decisions_complete

        return {
            "can_advance": can_advance,
            "mandatory_complete": mandatory_complete,
            "decisions_complete": decisions_complete,
            "checklist_progress": (
                progress.checklist_completed / progress.checklist_total * 100
                if progress.checklist_total > 0 else 0
            ),
            "blocking_reasons": [
                reason for reason, passed in [
                    ("Mandatory checklist items incomplete", mandatory_complete),
                    ("Required decisions not made", decisions_complete),
                ] if not passed
            ],
        }

    async def get_overall_progress(self, incident_id: str) -> dict:
        """Get overall incident progress."""
        timeline = await self.get_timeline(incident_id)

        phases_completed = sum(
            1 for entry in timeline.timeline
            if entry.status == PhaseStatus.COMPLETED
        )
        total_phases = len(IRPhase)

        return {
            "incident_id": incident_id,
            "current_phase": timeline.current_phase,
            "phases_completed": phases_completed,
            "total_phases": total_phases,
            "overall_progress": (phases_completed / total_phases * 100),
            "total_duration_seconds": timeline.total_duration_seconds,
            "started_at": timeline.started_at,
        }
