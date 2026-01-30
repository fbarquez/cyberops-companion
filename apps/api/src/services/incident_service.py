"""Incident management service."""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.incident import Incident, IncidentStatus, AffectedSystem
from src.models.phase import IRPhase
from src.schemas.incident import IncidentCreate, IncidentUpdate, AffectedSystemCreate


class IncidentService:
    """Service for incident operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: IncidentCreate, user_id: str) -> Incident:
        """Create a new incident."""
        incident = Incident(
            id=str(uuid4()),
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=IncidentStatus.DRAFT,
            detection_source=data.detection_source,
            initial_indicator=data.initial_indicator,
            analyst_name=data.analyst_name,
            analyst_email=data.analyst_email,
            detected_at=data.detected_at,
            created_by=user_id,
            current_phase=IRPhase.DETECTION.value,
            phase_history={IRPhase.DETECTION.value: datetime.utcnow().isoformat()},
        )
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def get_by_id(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID."""
        result = await self.db.execute(
            select(Incident).where(
                and_(
                    Incident.id == incident_id,
                    Incident.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: Optional[str] = None,
        status: Optional[IncidentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Incident], int]:
        """List incidents with pagination."""
        query = select(Incident).where(Incident.is_deleted == False)

        if user_id:
            query = query.where(
                (Incident.created_by == user_id) | (Incident.assigned_to == user_id)
            )
        if status:
            query = query.where(Incident.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Get page
        query = query.order_by(Incident.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        incidents = result.scalars().all()

        return list(incidents), total or 0

    async def update(
        self, incident_id: str, data: IncidentUpdate
    ) -> Optional[Incident]:
        """Update an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(incident, field, value)

        # Update status timestamps
        if data.status == IncidentStatus.CONTAINED and not incident.contained_at:
            incident.contained_at = datetime.utcnow()
        elif data.status == IncidentStatus.ERADICATED and not incident.eradicated_at:
            incident.eradicated_at = datetime.utcnow()
        elif data.status == IncidentStatus.CLOSED and not incident.closed_at:
            incident.closed_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def soft_delete(self, incident_id: str) -> bool:
        """Soft delete an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return False

        incident.is_deleted = True
        incident.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def add_affected_system(
        self, incident_id: str, data: AffectedSystemCreate
    ) -> Optional[AffectedSystem]:
        """Add an affected system to an incident."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        system = AffectedSystem(
            incident_id=incident_id,
            hostname=data.hostname,
            ip_address=data.ip_address,
            os_type=data.os_type,
            department=data.department,
            criticality=data.criticality,
            notes=data.notes,
        )
        self.db.add(system)
        await self.db.flush()
        await self.db.refresh(system)
        return system

    async def advance_phase(self, incident_id: str, force: bool = False) -> Optional[Incident]:
        """Advance incident to next phase."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None

        phase_order = list(IRPhase)
        current_idx = phase_order.index(IRPhase(incident.current_phase))

        if current_idx >= len(phase_order) - 1:
            return incident  # Already at last phase

        next_phase = phase_order[current_idx + 1]
        incident.current_phase = next_phase.value
        incident.phase_history[next_phase.value] = datetime.utcnow().isoformat()

        # Update status based on phase
        if next_phase == IRPhase.CONTAINMENT:
            incident.status = IncidentStatus.ACTIVE
        elif next_phase == IRPhase.ERADICATION:
            incident.status = IncidentStatus.CONTAINED
            if not incident.contained_at:
                incident.contained_at = datetime.utcnow()
        elif next_phase == IRPhase.RECOVERY:
            incident.status = IncidentStatus.ERADICATED
            if not incident.eradicated_at:
                incident.eradicated_at = datetime.utcnow()
        elif next_phase == IRPhase.POST_INCIDENT:
            incident.status = IncidentStatus.RECOVERED

        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def get_timeline(self, incident_id: str) -> dict:
        """Get incident timeline."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return {}

        timeline = []
        for phase in IRPhase:
            phase_time = incident.phase_history.get(phase.value)
            timeline.append({
                "phase": phase.value,
                "entered_at": phase_time,
                "is_current": incident.current_phase == phase.value,
            })

        return {
            "incident_id": incident_id,
            "current_phase": incident.current_phase,
            "timeline": timeline,
            "created_at": incident.created_at.isoformat(),
            "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
            "contained_at": incident.contained_at.isoformat() if incident.contained_at else None,
            "eradicated_at": incident.eradicated_at.isoformat() if incident.eradicated_at else None,
            "closed_at": incident.closed_at.isoformat() if incident.closed_at else None,
        }
