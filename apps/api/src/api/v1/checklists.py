"""Checklist management endpoints."""
from fastapi import APIRouter, HTTPException, status

from src.api.deps import DBSession, CurrentUser
from src.schemas.checklist import (
    ChecklistPhaseResponse, ChecklistItemComplete, ChecklistItemSkip,
)
from src.services.checklist_service import ChecklistService


router = APIRouter()


@router.get(
    "/incidents/{incident_id}/checklists/{phase}",
    response_model=ChecklistPhaseResponse,
)
async def get_phase_checklist(
    incident_id: str,
    phase: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get checklist for a specific phase."""
    service = ChecklistService(db)
    checklist = await service.get_phase_checklist(incident_id, phase)
    return checklist


@router.post(
    "/incidents/{incident_id}/checklists/{phase}/items/{item_id}/complete",
)
async def complete_checklist_item(
    incident_id: str,
    phase: str,
    item_id: str,
    data: ChecklistItemComplete,
    db: DBSession,
    current_user: CurrentUser,
):
    """Mark a checklist item as completed."""
    service = ChecklistService(db)
    item = await service.complete_item(
        incident_id=incident_id,
        phase=phase,
        item_id=item_id,
        user_id=current_user.id,
        data=data,
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist item not found",
        )

    return {"status": "completed", "item_id": item_id}


@router.post(
    "/incidents/{incident_id}/checklists/{phase}/items/{item_id}/skip",
)
async def skip_checklist_item(
    incident_id: str,
    phase: str,
    item_id: str,
    data: ChecklistItemSkip,
    db: DBSession,
    current_user: CurrentUser,
):
    """Mark a checklist item as skipped."""
    service = ChecklistService(db)
    try:
        item = await service.skip_item(
            incident_id=incident_id,
            phase=phase,
            item_id=item_id,
            user_id=current_user.id,
            data=data,
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checklist item not found",
            )

        return {"status": "skipped", "item_id": item_id}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/incidents/{incident_id}/checklists/{phase}/progress")
async def get_checklist_progress(
    incident_id: str,
    phase: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get progress for a phase checklist."""
    service = ChecklistService(db)
    checklist = await service.get_phase_checklist(incident_id, phase)

    return {
        "phase": phase,
        "total_items": checklist.total_items,
        "completed_items": checklist.completed_items,
        "mandatory_total": checklist.mandatory_total,
        "mandatory_completed": checklist.mandatory_completed,
        "progress_percent": checklist.progress_percent,
        "can_advance": checklist.can_advance,
    }


@router.post("/incidents/{incident_id}/checklists/{phase}/can-advance")
async def check_can_advance(
    incident_id: str,
    phase: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Check if incident can advance to next phase."""
    service = ChecklistService(db)
    result = await service.can_advance_phase(incident_id, phase)
    return result
