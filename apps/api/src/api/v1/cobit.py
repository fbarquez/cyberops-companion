"""
COBIT 2019 Compliance API

REST endpoints for COBIT 2019 IT Governance assessment management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.api.v1.auth import get_current_user, User
from src.services.cobit_service import COBITAssessmentService
from src.models.cobit import COBITAssessmentStatus, COBITDomain
from src.schemas.cobit import (
    # Reference Data
    DomainListResponse,
    ProcessListResponse,
    CapabilityLevelListResponse,
    # Request Schemas
    AssessmentCreate,
    AssessmentScopeUpdate,
    ProcessResponseCreate,
    BulkProcessUpdate,
    # Response Schemas
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    ProcessResponseOut,
    # Analysis
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)

router = APIRouter(prefix="/cobit", tags=["COBIT 2019 Compliance"])


def get_service(db: AsyncSession = Depends(get_db)) -> COBITAssessmentService:
    """Get COBIT service instance."""
    return COBITAssessmentService(db)


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get("/domains", response_model=DomainListResponse)
async def list_domains(
    service: COBITAssessmentService = Depends(get_service),
):
    """Get list of COBIT 2019 domains (EDM, APO, BAI, DSS, MEA)."""
    return service.get_domains_info()


@router.get("/processes", response_model=ProcessListResponse)
async def list_processes(
    domain: Optional[COBITDomain] = Query(None, description="Filter by domain"),
    service: COBITAssessmentService = Depends(get_service),
):
    """Get list of COBIT 2019 processes (40 total)."""
    return service.get_processes_info(domain.value if domain else None)


@router.get("/capability-levels", response_model=CapabilityLevelListResponse)
async def list_capability_levels(
    service: COBITAssessmentService = Depends(get_service),
):
    """Get list of COBIT capability levels (0-5)."""
    return service.get_capability_levels_info()


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Get COBIT dashboard statistics."""
    return await service.get_dashboard_stats(current_user.tenant_id)


# =============================================================================
# Assessment CRUD
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Create a new COBIT assessment."""
    assessment = await service.create_assessment(
        data, current_user.id, current_user.tenant_id
    )
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    status: Optional[COBITAssessmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """List all COBIT assessments."""
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
    service: COBITAssessmentService = Depends(get_service),
):
    """Get assessment by ID with all process responses."""
    assessment = await service.get_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
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
    service: COBITAssessmentService = Depends(get_service),
):
    """Update assessment scope - organization profile and target capability level (wizard step 1)."""
    assessment = await service.update_assessment_scope(
        assessment_id, data, current_user.tenant_id
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.put(
    "/assessments/{assessment_id}/processes/{process_id}",
    response_model=ProcessResponseOut,
)
async def update_process(
    assessment_id: str,
    process_id: str,
    data: ProcessResponseCreate,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Update a single process response."""
    data.process_id = process_id
    response = await service.submit_process_response(
        assessment_id, data, current_user.id, current_user.tenant_id
    )
    if not response:
        raise HTTPException(status_code=404, detail="Assessment or process not found")
    return ProcessResponseOut.model_validate(response)


@router.put(
    "/assessments/{assessment_id}/processes",
    response_model=List[ProcessResponseOut],
)
async def bulk_update_processes(
    assessment_id: str,
    data: BulkProcessUpdate,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Bulk update process responses (useful for wizard steps by domain)."""
    responses = await service.bulk_update_processes(
        assessment_id, data.responses, current_user.id, current_user.tenant_id
    )
    return [ProcessResponseOut.model_validate(r) for r in responses]


# =============================================================================
# Analysis
# =============================================================================

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Get gap analysis for an assessment comparing current vs target capability."""
    analysis = await service.get_gap_analysis(assessment_id, current_user.tenant_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return analysis


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: COBITAssessmentService = Depends(get_service),
):
    """Get wizard navigation state showing progress through assessment steps."""
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
    service: COBITAssessmentService = Depends(get_service),
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
    service: COBITAssessmentService = Depends(get_service),
):
    """Generate comprehensive assessment report."""
    report = await service.generate_report(assessment_id, current_user.tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report
