"""
GDPR Compliance API

REST endpoints for GDPR assessment management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.services.gdpr_service import GDPRAssessmentService
from src.models.gdpr import GDPRAssessmentStatus
from src.schemas.gdpr import (
    # Reference Data
    ChapterListResponse,
    RequirementListResponse,
    # Request Schemas
    AssessmentCreate,
    AssessmentScopeUpdate,
    RequirementResponseCreate,
    BulkRequirementUpdate,
    # Response Schemas
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    RequirementResponseOut,
    # Analysis
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


def get_service(db: AsyncSession = Depends(get_db)) -> GDPRAssessmentService:
    """Get GDPR service instance."""
    return GDPRAssessmentService(db)


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get("/chapters", response_model=ChapterListResponse)
async def list_chapters(
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get list of GDPR chapters."""
    return service.get_chapters_info()


@router.get("/requirements", response_model=RequirementListResponse)
async def list_requirements(
    chapter: Optional[str] = Query(None, description="Filter by chapter ID"),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get list of GDPR requirements."""
    return service.get_requirements_info(chapter)


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get GDPR dashboard statistics."""
    return await service.get_dashboard_stats(current_user.tenant_id)


# =============================================================================
# Assessment CRUD
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Create a new GDPR assessment."""
    assessment = await service.create_assessment(
        data, current_user.id, current_user.tenant_id
    )
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    status: Optional[GDPRAssessmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """List all GDPR assessments."""
    assessments, total = await service.list_assessments(
        current_user.tenant_id, status, page, size
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
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get assessment by ID with all responses."""
    assessment = await service.get_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Delete an assessment."""
    deleted = await service.delete_assessment(assessment_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assessment not found")


# =============================================================================
# Wizard Steps
# =============================================================================

@router.put("/assessments/{assessment_id}/scope", response_model=AssessmentResponse)
async def update_scope(
    assessment_id: str,
    data: AssessmentScopeUpdate,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Update assessment scope (wizard step 1)."""
    assessment = await service.update_assessment_scope(
        assessment_id, data, current_user.tenant_id
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.put(
    "/assessments/{assessment_id}/requirements/{requirement_id}",
    response_model=RequirementResponseOut,
)
async def update_requirement(
    assessment_id: str,
    requirement_id: str,
    data: RequirementResponseCreate,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Update a single requirement response."""
    data.requirement_id = requirement_id
    response = await service.submit_requirement_response(
        assessment_id, data, current_user.id, current_user.tenant_id
    )
    if not response:
        raise HTTPException(status_code=404, detail="Assessment or requirement not found")
    return RequirementResponseOut.model_validate(response)


@router.put(
    "/assessments/{assessment_id}/requirements",
    response_model=List[RequirementResponseOut],
)
async def bulk_update_requirements(
    assessment_id: str,
    data: BulkRequirementUpdate,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Bulk update requirement responses."""
    responses = await service.bulk_update_requirements(
        assessment_id, data.responses, current_user.id, current_user.tenant_id
    )
    return [RequirementResponseOut.model_validate(r) for r in responses]


# =============================================================================
# Analysis
# =============================================================================

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get gap analysis for an assessment."""
    analysis = await service.get_gap_analysis(assessment_id, current_user.tenant_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return analysis


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Get wizard navigation state."""
    state = await service.get_wizard_state(assessment_id, current_user.tenant_id)
    if not state:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return state


# =============================================================================
# Completion and Reporting
# =============================================================================

@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Mark assessment as completed."""
    assessment = await service.complete_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments/{assessment_id}/report", response_model=AssessmentReportResponse)
async def get_report(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: GDPRAssessmentService = Depends(get_service),
):
    """Generate assessment report."""
    report = await service.generate_report(assessment_id, current_user.tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report
