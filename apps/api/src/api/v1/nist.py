"""
NIST CSF 2.0 Compliance API

REST endpoints for NIST Cybersecurity Framework assessment management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.services.nist_service import NISTAssessmentService
from src.models.nist import NISTAssessmentStatus, NISTFunction
from src.schemas.nist import (
    # Reference Data
    FunctionListResponse,
    CategoryListResponse,
    SubcategoryListResponse,
    TierListResponse,
    # Request Schemas
    AssessmentCreate,
    AssessmentScopeUpdate,
    SubcategoryResponseCreate,
    BulkSubcategoryUpdate,
    # Response Schemas
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    SubcategoryResponseOut,
    # Analysis
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)

router = APIRouter(prefix="/nist", tags=["NIST CSF 2.0 Compliance"])


def get_service(db: AsyncSession = Depends(get_db)) -> NISTAssessmentService:
    """Get NIST service instance."""
    return NISTAssessmentService(db)


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get("/functions", response_model=FunctionListResponse)
async def list_functions(
    service: NISTAssessmentService = Depends(get_service),
):
    """Get list of NIST CSF 2.0 functions (Govern, Identify, Protect, Detect, Respond, Recover)."""
    return service.get_functions_info()


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    function: Optional[NISTFunction] = Query(None, description="Filter by function"),
    service: NISTAssessmentService = Depends(get_service),
):
    """Get list of NIST CSF categories."""
    return service.get_categories_info(function.value if function else None)


@router.get("/subcategories", response_model=SubcategoryListResponse)
async def list_subcategories(
    function: Optional[NISTFunction] = Query(None, description="Filter by function"),
    category: Optional[str] = Query(None, description="Filter by category ID"),
    service: NISTAssessmentService = Depends(get_service),
):
    """Get list of NIST CSF subcategories (outcomes)."""
    return service.get_subcategories_info(
        function.value if function else None,
        category
    )


@router.get("/tiers", response_model=TierListResponse)
async def list_tiers(
    service: NISTAssessmentService = Depends(get_service),
):
    """Get list of NIST CSF implementation tiers (1-4)."""
    return service.get_tiers_info()


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """Get NIST CSF dashboard statistics."""
    return await service.get_dashboard_stats(current_user.tenant_id)


# =============================================================================
# Assessment CRUD
# =============================================================================

@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """Create a new NIST CSF assessment."""
    assessment = await service.create_assessment(
        data, current_user.id, current_user.tenant_id
    )
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    status: Optional[NISTAssessmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """List all NIST CSF assessments."""
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
    service: NISTAssessmentService = Depends(get_service),
):
    """Get assessment by ID with all subcategory responses."""
    assessment = await service.get_assessment(assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
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
    service: NISTAssessmentService = Depends(get_service),
):
    """Update assessment scope - organization profile and target tier (wizard step 1)."""
    assessment = await service.update_assessment_scope(
        assessment_id, data, current_user.tenant_id
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.put(
    "/assessments/{assessment_id}/subcategories/{subcategory_id}",
    response_model=SubcategoryResponseOut,
)
async def update_subcategory(
    assessment_id: str,
    subcategory_id: str,
    data: SubcategoryResponseCreate,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """Update a single subcategory response."""
    data.subcategory_id = subcategory_id
    response = await service.submit_subcategory_response(
        assessment_id, data, current_user.id, current_user.tenant_id
    )
    if not response:
        raise HTTPException(status_code=404, detail="Assessment or subcategory not found")
    return SubcategoryResponseOut.model_validate(response)


@router.put(
    "/assessments/{assessment_id}/subcategories",
    response_model=List[SubcategoryResponseOut],
)
async def bulk_update_subcategories(
    assessment_id: str,
    data: BulkSubcategoryUpdate,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """Bulk update subcategory responses (useful for wizard steps by function)."""
    responses = await service.bulk_update_subcategories(
        assessment_id, data.responses, current_user.id, current_user.tenant_id
    )
    return [SubcategoryResponseOut.model_validate(r) for r in responses]


# =============================================================================
# Analysis
# =============================================================================

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
):
    """Get gap analysis for an assessment comparing current vs target profile."""
    analysis = await service.get_gap_analysis(assessment_id, current_user.tenant_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return analysis


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    service: NISTAssessmentService = Depends(get_service),
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
    service: NISTAssessmentService = Depends(get_service),
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
    service: NISTAssessmentService = Depends(get_service),
):
    """Generate comprehensive assessment report."""
    report = await service.generate_report(assessment_id, current_user.tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report
