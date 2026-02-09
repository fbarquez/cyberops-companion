"""
TISAX Compliance API Endpoints

REST API for TISAX (Trusted Information Security Assessment Exchange) compliance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.tisax import TISAXAssessmentLevel, TISAXAssessmentStatus
from src.services.tisax_service import TISAXAssessmentService
from src.schemas.tisax import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    ControlResponseCreate,
    BulkControlUpdate,
    ChapterListResponse,
    ControlListResponse,
    AssessmentLevelListResponse,
    ObjectiveListResponse,
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)

router = APIRouter(prefix="/tisax", tags=["TISAX Compliance"])


def get_service(db: AsyncSession = Depends(get_db)) -> TISAXAssessmentService:
    """Get TISAX service instance."""
    return TISAXAssessmentService(db)


# =============================================================================
# Reference Data
# =============================================================================

@router.get("/chapters", response_model=ChapterListResponse)
async def get_chapters(
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get list of VDA ISA chapters."""
    return service.get_chapters_info()


@router.get("/controls", response_model=ControlListResponse)
async def get_controls(
    chapter: Optional[str] = Query(None, description="Filter by chapter ID"),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get list of VDA ISA controls."""
    return service.get_controls_info(chapter)


@router.get("/assessment-levels", response_model=AssessmentLevelListResponse)
async def get_assessment_levels(
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get TISAX assessment levels (AL1-AL3)."""
    return service.get_assessment_levels_info()


@router.get("/objectives", response_model=ObjectiveListResponse)
async def get_objectives(
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get TISAX assessment objectives."""
    return service.get_objectives_info()


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get TISAX dashboard statistics."""
    return await service.get_dashboard_stats(current_user.tenant_id)


# =============================================================================
# Assessment CRUD
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Create a new TISAX assessment."""
    assessment = await service.create_assessment(data, current_user.id, current_user.tenant_id)
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    status: Optional[TISAXAssessmentStatus] = Query(None),
    level: Optional[TISAXAssessmentLevel] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """List TISAX assessments."""
    assessments, total = await service.list_assessments(
        current_user.tenant_id, status, level, page, size
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
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get assessment details."""
    assessment = await service.get_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse.model_validate(assessment)


@router.patch("/assessments/{assessment_id}/scope", response_model=AssessmentResponse)
async def update_assessment_scope(
    assessment_id: str,
    data: AssessmentScopeUpdate,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Update assessment scope (wizard step 1)."""
    assessment = await service.update_assessment_scope(assessment_id, data, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Delete an assessment."""
    deleted = await service.delete_assessment(assessment_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assessment not found")


# =============================================================================
# Control Responses
# =============================================================================

@router.post("/assessments/{assessment_id}/controls")
async def submit_control_response(
    assessment_id: str,
    data: ControlResponseCreate,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Submit or update a control response."""
    response = await service.submit_control_response(
        assessment_id, data, current_user.id, current_user.tenant_id
    )
    if not response:
        raise HTTPException(status_code=404, detail="Assessment or control not found")
    return {"status": "success", "control_id": data.control_id}


@router.post("/assessments/{assessment_id}/controls/bulk")
async def bulk_update_controls(
    assessment_id: str,
    data: BulkControlUpdate,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Bulk update control responses."""
    updated = await service.bulk_update_controls(
        assessment_id, data.responses, current_user.id, current_user.tenant_id
    )
    return {"status": "success", "updated_count": len(updated)}


# =============================================================================
# Analysis & Reporting
# =============================================================================

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get gap analysis for an assessment."""
    analysis = await service.get_gap_analysis(assessment_id, current_user.tenant_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return analysis


@router.get("/assessments/{assessment_id}/report", response_model=AssessmentReportResponse)
async def get_assessment_report(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get assessment report."""
    report = await service.generate_report(assessment_id, current_user.tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Mark assessment as completed."""
    assessment = await service.complete_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


# =============================================================================
# Wizard State
# =============================================================================

@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: TISAXAssessmentService = Depends(get_service),
):
    """Get wizard navigation state."""
    state = await service.get_wizard_state(assessment_id, current_user.tenant_id)
    if not state:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return state
