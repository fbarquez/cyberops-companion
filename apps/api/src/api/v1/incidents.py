"""Incident management endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query

from src.api.deps import DBSession, CurrentUser, LeadUser, UserWithTenant
from src.models.incident import IncidentStatus
from src.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentList,
    AffectedSystemCreate, AffectedSystemResponse,
)
from src.services.incident_service import IncidentService
from src.services.phase_service import PhaseService
from src.services.audit_service import AuditService


router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a new incident."""
    current_user, context = user_context
    service = IncidentService(db)
    incident = await service.create(data, current_user.id, context.tenant_id)

    # Log audit action
    audit_service = AuditService(db)
    await audit_service.log_action(
        user_id=current_user.id,
        action="create",
        resource_type="incident",
        resource_id=incident.id,
        resource_name=incident.title,
        description=f"{current_user.full_name} created incident: {incident.title}",
        new_values={"title": incident.title, "severity": incident.severity.value, "status": incident.status.value},
    )

    return incident


@router.get("", response_model=IncidentList)
async def list_incidents(
    db: DBSession,
    current_user: CurrentUser,
    status: Optional[IncidentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List incidents with pagination."""
    service = IncidentService(db)
    incidents, total = await service.list(
        user_id=current_user.id if current_user.role.value == "analyst" else None,
        status=status,
        page=page,
        size=size,
    )

    return IncidentList(
        items=incidents,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get incident by ID."""
    service = IncidentService(db)
    incident = await service.get_by_id(incident_id)

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update an incident."""
    service = IncidentService(db)

    # Get old values for audit
    old_incident = await service.get_by_id(incident_id)
    if not old_incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    old_values = {
        "title": old_incident.title,
        "severity": old_incident.severity.value if old_incident.severity else None,
        "status": old_incident.status.value if old_incident.status else None,
    }

    incident = await service.update(incident_id, data)

    # Log audit action
    audit_service = AuditService(db)
    new_values = data.model_dump(exclude_unset=True)
    # Convert enums to strings
    for key in ["severity", "status"]:
        if key in new_values and hasattr(new_values[key], "value"):
            new_values[key] = new_values[key].value

    await audit_service.log_action(
        user_id=current_user.id,
        action="update",
        resource_type="incident",
        resource_id=incident_id,
        resource_name=incident.title,
        description=f"{current_user.full_name} updated incident: {incident.title}",
        old_values=old_values,
        new_values=new_values,
    )

    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: str,
    db: DBSession,
    current_user: LeadUser,
):
    """Soft delete an incident (requires lead role)."""
    service = IncidentService(db)

    # Get incident info for audit before deletion
    incident = await service.get_by_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    incident_title = incident.title
    success = await service.soft_delete(incident_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    # Log audit action
    audit_service = AuditService(db)
    await audit_service.log_action(
        user_id=current_user.id,
        action="delete",
        resource_type="incident",
        resource_id=incident_id,
        resource_name=incident_title,
        description=f"{current_user.full_name} deleted incident: {incident_title}",
        severity="warning",
    )


@router.post("/{incident_id}/systems", response_model=AffectedSystemResponse)
async def add_affected_system(
    incident_id: str,
    data: AffectedSystemCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Add an affected system to an incident."""
    current_user, context = user_context
    service = IncidentService(db)
    system = await service.add_affected_system(incident_id, data, context.tenant_id)

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return system


@router.post("/{incident_id}/advance-phase", response_model=IncidentResponse)
async def advance_phase(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
    force: bool = False,
):
    """Advance incident to next phase."""
    service = IncidentService(db)
    incident = await service.advance_phase(incident_id, force=force)

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@router.get("/{incident_id}/summary")
async def get_incident_summary(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get incident executive summary."""
    incident_service = IncidentService(db)
    phase_service = PhaseService(db)

    incident = await incident_service.get_by_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    progress = await phase_service.get_overall_progress(incident_id)
    timeline = await incident_service.get_timeline(incident_id)

    return {
        "incident": incident,
        "progress": progress,
        "timeline": timeline,
    }


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get incident timeline."""
    service = IncidentService(db)
    timeline = await service.get_timeline(incident_id)

    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return timeline
