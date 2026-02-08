"""
KRITIS Compliance API Endpoints

REST API for KRITIS (German Critical Infrastructure) compliance management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.api.deps import get_current_user, get_tenant_id
from src.models.user import User
from src.models.kritis import KRITISSector, KRITISAssessmentStatus
from src.services.kritis_service import KRITISAssessmentService
from src.schemas.kritis import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    RequirementResponseCreate,
    BulkRequirementUpdate,
    SectorListResponse,
    RequirementsListResponse,
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)

router = APIRouter(prefix="/kritis", tags=["KRITIS Compliance"])


# =============================================================================
# Reference Data
# =============================================================================

@router.get("/sectors", response_model=SectorListResponse)
async def get_sectors(
    db: AsyncSession = Depends(get_db),
):
    """Get list of KRITIS sectors."""
    service = KRITISAssessmentService(db)
    return service.get_sectors_info()


@router.get("/requirements", response_model=RequirementsListResponse)
async def get_requirements(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of KRITIS requirements."""
    service = KRITISAssessmentService(db)
    return service.get_requirements_info(category)


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get KRITIS dashboard statistics."""
    service = KRITISAssessmentService(db)
    return await service.get_dashboard_stats(tenant_id)


# =============================================================================
# Assessment CRUD
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new KRITIS assessment."""
    service = KRITISAssessmentService(db)
    assessment = await service.create_assessment(data, current_user.id, tenant_id)
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    status: Optional[KRITISAssessmentStatus] = Query(None),
    sector: Optional[KRITISSector] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """List KRITIS assessments."""
    service = KRITISAssessmentService(db)
    assessments, total = await service.list_assessments(
        tenant_id, status, sector, page, size
    )
    return AssessmentListResponse(
        items=[AssessmentResponse.model_validate(a) for a in assessments],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get assessment details."""
    service = KRITISAssessmentService(db)
    assessment = await service.get_assessment(assessment_id, tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse.model_validate(assessment)


@router.patch("/assessments/{assessment_id}/scope", response_model=AssessmentResponse)
async def update_assessment_scope(
    assessment_id: str,
    data: AssessmentScopeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update assessment scope (wizard step 1)."""
    service = KRITISAssessmentService(db)
    assessment = await service.update_assessment_scope(assessment_id, data, tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Delete an assessment."""
    service = KRITISAssessmentService(db)
    deleted = await service.delete_assessment(assessment_id, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assessment not found")


# =============================================================================
# Requirement Responses
# =============================================================================

@router.post("/assessments/{assessment_id}/responses")
async def submit_requirement_response(
    assessment_id: str,
    data: RequirementResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Submit or update a requirement response."""
    service = KRITISAssessmentService(db)
    response = await service.submit_requirement_response(
        assessment_id, data, current_user.id, tenant_id
    )
    if not response:
        raise HTTPException(status_code=404, detail="Assessment or requirement not found")
    return {"status": "success", "requirement_id": data.requirement_id}


@router.post("/assessments/{assessment_id}/responses/bulk")
async def bulk_update_requirements(
    assessment_id: str,
    data: BulkRequirementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Bulk update requirement responses."""
    service = KRITISAssessmentService(db)
    updated = await service.bulk_update_requirements(
        assessment_id, data.responses, current_user.id, tenant_id
    )
    return {"status": "success", "updated_count": len(updated)}


# =============================================================================
# Analysis & Reporting
# =============================================================================

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get gap analysis for an assessment."""
    service = KRITISAssessmentService(db)
    analysis = await service.get_gap_analysis(assessment_id, tenant_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return analysis


@router.get("/assessments/{assessment_id}/report", response_model=AssessmentReportResponse)
async def get_assessment_report(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get assessment report."""
    service = KRITISAssessmentService(db)
    report = await service.generate_report(assessment_id, tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Mark assessment as completed."""
    service = KRITISAssessmentService(db)
    assessment = await service.complete_assessment(assessment_id, tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


# =============================================================================
# Wizard State
# =============================================================================

@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get wizard navigation state."""
    service = KRITISAssessmentService(db)
    state = await service.get_wizard_state(assessment_id, tenant_id)
    if not state:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return state
