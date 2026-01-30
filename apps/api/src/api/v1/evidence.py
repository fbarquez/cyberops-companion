"""Evidence management endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import PlainTextResponse

from src.api.deps import DBSession, CurrentUser
from src.models.evidence import EvidenceType
from src.schemas.evidence import (
    EvidenceCreate, EvidenceResponse, EvidenceChainResponse, ChainVerificationResult,
)
from src.services.evidence_service import EvidenceService


router = APIRouter()


@router.post(
    "/incidents/{incident_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evidence_entry(
    incident_id: str,
    data: EvidenceCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create a new evidence entry with hash chain linkage."""
    service = EvidenceService(db)
    entry = await service.create_entry(
        incident_id=incident_id,
        data=data,
        user_id=current_user.id,
        operator_name=current_user.full_name,
    )
    return entry


@router.get("/incidents/{incident_id}/evidence", response_model=list[EvidenceResponse])
async def list_evidence(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
    phase: Optional[str] = None,
    entry_type: Optional[EvidenceType] = None,
):
    """List evidence entries with optional filters."""
    service = EvidenceService(db)
    entries = await service.get_entries(
        incident_id=incident_id,
        phase=phase,
        entry_type=entry_type,
    )
    return entries


@router.get("/incidents/{incident_id}/evidence/chain", response_model=EvidenceChainResponse)
async def get_evidence_chain(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get complete evidence chain for an incident."""
    service = EvidenceService(db)
    entries = await service.get_chain(incident_id)
    verification = await service.verify_chain(incident_id)

    return EvidenceChainResponse(
        incident_id=incident_id,
        total_entries=len(entries),
        chain_valid=verification.is_valid,
        entries=entries,
        first_entry=entries[0].timestamp if entries else None,
        last_entry=entries[-1].timestamp if entries else None,
    )


@router.post("/incidents/{incident_id}/evidence/verify", response_model=ChainVerificationResult)
async def verify_evidence_chain(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Verify integrity of evidence chain."""
    service = EvidenceService(db)
    result = await service.verify_chain(incident_id)
    return result


@router.get("/incidents/{incident_id}/evidence/export")
async def export_evidence(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    include_hashes: bool = True,
):
    """Export evidence chain in specified format."""
    service = EvidenceService(db)
    content = await service.export_chain(
        incident_id=incident_id,
        format=format,
        include_hashes=include_hashes,
    )

    media_type = "text/markdown" if format == "markdown" else "application/json"
    return PlainTextResponse(content=content, media_type=media_type)
