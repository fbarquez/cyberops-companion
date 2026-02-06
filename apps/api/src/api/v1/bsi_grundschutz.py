"""BSI IT-Grundschutz API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Query

from src.api.deps import DBSession, CurrentUser
from src.models.bsi_grundschutz import (
    BSIKategorie, BSIAnforderungTyp, BSISchutzbedarf, BSIComplianceStatusEnum
)
from src.schemas.bsi_grundschutz import (
    KategorienListResponse, KategorieResponse,
    BausteinListResponse, BausteinListItem, BausteinResponse, BausteinDetailResponse,
    AnforderungListResponse, AnforderungResponse, AnforderungCountResponse,
    ComplianceStatusResponse, ComplianceStatusCreate, BulkComplianceStatusUpdate,
    ComplianceScoreResponse, ComplianceOverviewResponse,
)
from src.services.bsi_grundschutz_service import (
    BSIBausteinService, BSIAnforderungService, BSIComplianceService
)


router = APIRouter(prefix="/bsi/grundschutz")


# ============== Catalog Endpoints (Global Data) ==============

@router.get("/kategorien", response_model=KategorienListResponse)
async def list_kategorien(
    db: DBSession,
    current_user: CurrentUser,
):
    """Get all BSI IT-Grundschutz categories with Baustein counts."""
    service = BSIBausteinService(db)
    kategorien = await service.get_kategorien_summary()
    return KategorienListResponse(
        kategorien=[KategorieResponse(**k) for k in kategorien],
        total=len(kategorien)
    )


@router.get("/bausteine", response_model=BausteinListResponse)
async def list_bausteine(
    db: DBSession,
    current_user: CurrentUser,
    kategorie: Optional[BSIKategorie] = None,
    search: Optional[str] = Query(None, description="Search in title/description"),
    ir_phase: Optional[str] = Query(None, description="Filter by IR phase"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """List BSI IT-Grundschutz Bausteine with filters."""
    service = BSIBausteinService(db)
    bausteine, total = await service.list_bausteine(
        kategorie=kategorie,
        search=search,
        ir_phase=ir_phase,
        page=page,
        size=size,
    )

    return BausteinListResponse(
        bausteine=[
            BausteinListItem(
                id=b.id,
                baustein_id=b.baustein_id,
                kategorie=b.kategorie,
                titel=b.titel,
                title_en=b.title_en,
                version=b.version,
                ir_phases=b.ir_phases or [],
                anforderungen_count=len(b.anforderungen) if b.anforderungen else None,
            )
            for b in bausteine
        ],
        total=total,
        page=page,
        size=size,
    )


@router.get("/bausteine/{baustein_id}", response_model=BausteinDetailResponse)
async def get_baustein(
    baustein_id: str,
    db: DBSession,
    current_user: CurrentUser,
    schutzbedarf: Optional[BSISchutzbedarf] = Query(
        None,
        description="Filter Anforderungen by protection level"
    ),
):
    """Get Baustein detail with its Anforderungen."""
    service = BSIBausteinService(db)
    result = await service.get_baustein_with_anforderungen(
        baustein_id=baustein_id,
        schutzbedarf=schutzbedarf,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baustein {baustein_id} not found",
        )

    return BausteinDetailResponse(
        baustein=BausteinResponse.model_validate(result["baustein"]),
        anforderungen=[
            AnforderungResponse.model_validate(a)
            for a in result["anforderungen"]
        ],
        anforderungen_count=AnforderungCountResponse(**result["anforderungen_count"]),
    )


@router.get("/anforderungen", response_model=AnforderungListResponse)
async def list_anforderungen(
    db: DBSession,
    current_user: CurrentUser,
    baustein_id: Optional[str] = Query(None, description="Filter by Baustein ID"),
    typ: Optional[BSIAnforderungTyp] = None,
    schutzbedarf: Optional[BSISchutzbedarf] = None,
    search: Optional[str] = Query(None, description="Search in title/description"),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
):
    """List BSI IT-Grundschutz Anforderungen with filters."""
    service = BSIAnforderungService(db)
    anforderungen, total = await service.list_anforderungen(
        baustein_id=baustein_id,
        typ=typ,
        schutzbedarf=schutzbedarf,
        search=search,
        page=page,
        size=size,
    )

    return AnforderungListResponse(
        anforderungen=[
            AnforderungResponse.model_validate(a)
            for a in anforderungen
        ],
        total=total,
        page=page,
        size=size,
    )


@router.get("/anforderungen/{anforderung_id}", response_model=AnforderungResponse)
async def get_anforderung(
    anforderung_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get Anforderung by ID."""
    service = BSIAnforderungService(db)
    anforderung = await service.get_anforderung(anforderung_id)

    if not anforderung:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anforderung {anforderung_id} not found",
        )

    return AnforderungResponse.model_validate(anforderung)


# ============== Compliance Endpoints (Tenant-Scoped) ==============

@router.get("/compliance/status", response_model=List[ComplianceStatusResponse])
async def list_compliance_status(
    db: DBSession,
    current_user: CurrentUser,
    baustein_id: Optional[str] = Query(None, description="Filter by Baustein ID"),
    incident_id: Optional[str] = Query(None, description="Filter by Incident ID"),
    status_filter: Optional[BSIComplianceStatusEnum] = Query(
        None, alias="status", description="Filter by compliance status"
    ),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
):
    """List compliance statuses for current tenant."""
    service = BSIComplianceService(db)
    statuses, total = await service.list_paginated(
        page=page,
        size=size,
        filters={
            "incident_id": incident_id,
            "status": status_filter,
        } if incident_id or status_filter else None,
    )

    return [ComplianceStatusResponse.model_validate(s) for s in statuses]


@router.post("/compliance/status", response_model=ComplianceStatusResponse)
async def update_compliance_status(
    data: ComplianceStatusCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create or update compliance status for an Anforderung."""
    service = BSIComplianceService(db)

    try:
        result = await service.update_compliance_status(
            anforderung_id=data.anforderung_id,
            status=data.status,
            user_id=current_user.id,
            incident_id=data.incident_id,
            evidence_provided=data.evidence_provided,
            notes=data.notes,
            gap_description=data.gap_description,
            remediation_plan=data.remediation_plan,
            due_date=data.due_date,
        )
        await db.commit()
        return ComplianceStatusResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/compliance/status/bulk", response_model=List[ComplianceStatusResponse])
async def bulk_update_compliance_status(
    data: BulkComplianceStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Bulk update compliance statuses."""
    service = BSIComplianceService(db)

    try:
        results = await service.bulk_update_status(
            updates=[u.model_dump() for u in data.updates],
            user_id=current_user.id,
        )
        await db.commit()
        return [ComplianceStatusResponse.model_validate(r) for r in results]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/compliance/score/{baustein_id}", response_model=ComplianceScoreResponse)
async def get_baustein_compliance_score(
    baustein_id: str,
    db: DBSession,
    current_user: CurrentUser,
    schutzbedarf: BSISchutzbedarf = Query(
        BSISchutzbedarf.standard,
        description="Protection level to evaluate"
    ),
    incident_id: Optional[str] = Query(None, description="Scope to specific incident"),
):
    """Get compliance score for a specific Baustein."""
    service = BSIComplianceService(db)

    try:
        score = await service.get_baustein_compliance_score(
            baustein_id=baustein_id,
            schutzbedarf=schutzbedarf,
            incident_id=incident_id,
        )
        return ComplianceScoreResponse(**score)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/compliance/overview", response_model=ComplianceOverviewResponse)
async def get_compliance_overview(
    db: DBSession,
    current_user: CurrentUser,
    schutzbedarf: BSISchutzbedarf = Query(
        BSISchutzbedarf.standard,
        description="Protection level to evaluate"
    ),
    incident_id: Optional[str] = Query(None, description="Scope to specific incident"),
):
    """Get overall compliance overview by category."""
    service = BSIComplianceService(db)
    overview = await service.get_compliance_overview(
        schutzbedarf=schutzbedarf,
        incident_id=incident_id,
    )
    return ComplianceOverviewResponse(**overview)


# ============== IR Phase Mapping Endpoints ==============

@router.get("/ir-phases/{phase}/bausteine", response_model=BausteinListResponse)
async def get_bausteine_for_ir_phase(
    phase: str,
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """Get Bausteine relevant to a specific IR phase."""
    valid_phases = [
        "preparation", "detection", "analysis", "containment",
        "eradication", "recovery", "lessons_learned"
    ]

    if phase not in valid_phases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid IR phase. Valid phases: {', '.join(valid_phases)}",
        )

    service = BSIBausteinService(db)
    bausteine, total = await service.list_bausteine(
        ir_phase=phase,
        page=page,
        size=size,
    )

    return BausteinListResponse(
        bausteine=[
            BausteinListItem(
                id=b.id,
                baustein_id=b.baustein_id,
                kategorie=b.kategorie,
                titel=b.titel,
                title_en=b.title_en,
                version=b.version,
                ir_phases=b.ir_phases or [],
            )
            for b in bausteine
        ],
        total=total,
        page=page,
        size=size,
    )


# ============== Admin Endpoints (Catalog Updates) ==============

@router.get("/admin/status")
async def get_catalog_status(
    db: DBSession,
    current_user: CurrentUser,
):
    """Get BSI catalog status including version and last update time."""
    from src.services.bsi_update_service import BSIUpdateService

    service = BSIUpdateService(db)
    return await service.get_status()


@router.post("/admin/check-updates")
async def check_for_updates(
    db: DBSession,
    current_user: CurrentUser,
):
    """Check if BSI catalog updates are available."""
    from src.services.bsi_update_service import BSIUpdateService

    service = BSIUpdateService(db)
    result = await service.check_for_updates()

    # Don't return the full content in the response
    if "content" in result:
        del result["content"]

    return result


@router.post("/admin/update")
async def trigger_update(
    db: DBSession,
    current_user: CurrentUser,
):
    """Trigger a manual BSI catalog update.

    This will check for updates and apply them if available.
    """
    from src.services.bsi_update_service import BSIUpdateService

    service = BSIUpdateService(db)
    return await service.auto_update()
