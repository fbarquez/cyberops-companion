"""ISO 27001:2022 Compliance API endpoints."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from src.db.database import get_db
from src.api.deps import (
    CurrentUser, DBSession, UserWithTenant, OrgAdmin,
    get_current_user_with_tenant
)
from src.models.user import User
from src.core.tenant_context import TenantContext
from src.services.iso27001_service import ISO27001Service
from src.schemas.iso27001 import (
    # Enums
    ISO27001Theme, ISO27001AssessmentStatus, ISO27001Applicability, ISO27001ComplianceStatus,
    # Responses
    ThemeInfo, ThemeListResponse,
    ISO27001ControlResponse, ControlListResponse,
    AssessmentCreate, AssessmentScopeUpdate, AssessmentResponse, AssessmentListResponse,
    SoAEntryUpdate, SoAEntryBulkUpdate, SoAEntryResponse, SoAListResponse,
    WizardState, ISO27001DashboardStats, AssessmentOverview,
    GapAnalysisResponse, CrossFrameworkMappingResponse,
    CompleteAssessmentRequest, ReportRequest, ReportResponse,
)

router = APIRouter(prefix="/iso27001")


def get_service(db: AsyncSession) -> ISO27001Service:
    """Get ISO 27001 service instance."""
    return ISO27001Service(db)


# ========== Reference Data Endpoints ==========

@router.get("/themes", response_model=ThemeListResponse)
async def get_themes(
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Get all ISO 27001:2022 themes with control counts.

    Returns the 4 themes from Annex A:
    - A.5 Organizational (37 controls)
    - A.6 People (8 controls)
    - A.7 Physical (14 controls)
    - A.8 Technological (34 controls)
    """
    service = get_service(db)
    themes = await service.get_themes()
    total_controls = sum(t.control_count for t in themes)

    return ThemeListResponse(themes=themes, total_controls=total_controls)


@router.get("/controls", response_model=ControlListResponse)
async def get_controls(
    db: DBSession,
    current_user: CurrentUser,
    theme: Optional[str] = Query(None, description="Filter by theme (A.5, A.6, A.7, A.8)"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
):
    """
    Get ISO 27001:2022 controls with optional filtering.

    - **theme**: Filter by theme (A.5, A.6, A.7, A.8)
    - **search**: Search in control titles and descriptions
    """
    service = get_service(db)
    controls, total = await service.get_controls(
        theme=theme,
        search=search,
        page=page,
        page_size=page_size
    )

    return ControlListResponse(
        controls=[ISO27001ControlResponse.model_validate(c) for c in controls],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/controls/{control_id}", response_model=ISO27001ControlResponse)
async def get_control(
    control_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Get a specific ISO 27001 control by ID or control code.

    - **control_id**: UUID or control code (e.g., A.5.1)
    """
    service = get_service(db)
    control = await service.get_control(control_id)

    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )

    return ISO27001ControlResponse.model_validate(control)


# ========== Dashboard Endpoint ==========

@router.get("/dashboard", response_model=ISO27001DashboardStats)
async def get_dashboard(
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get ISO 27001 dashboard statistics for the current tenant.

    Returns:
    - Total/active/completed assessment counts
    - Average compliance score
    - Theme-wise scores
    - Recent assessments
    """
    user, context = user_context
    service = get_service(db)
    stats = await service.get_dashboard_stats(context.tenant_id)

    # Convert assessments to response models
    recent = [
        AssessmentResponse.model_validate(a)
        for a in stats.get("recent_assessments", [])
    ]

    return ISO27001DashboardStats(
        total_assessments=stats["total_assessments"],
        active_assessments=stats["active_assessments"],
        completed_assessments=stats["completed_assessments"],
        total_controls=stats["total_controls"],
        average_compliance_score=stats["average_compliance_score"],
        theme_scores=stats["theme_scores"],
        recent_assessments=recent,
    )


# ========== Assessment CRUD Endpoints ==========

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Create a new ISO 27001 assessment.

    This will:
    1. Create the assessment record
    2. Initialize Statement of Applicability entries for all 93 controls
    """
    user, context = user_context
    service = get_service(db)

    assessment = await service.create_assessment(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    db: DBSession,
    user_context: UserWithTenant,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List ISO 27001 assessments for the current tenant."""
    user, context = user_context
    service = get_service(db)

    assessments, total = await service.list_assessments(
        tenant_id=context.tenant_id,
        status=status_filter,
        page=page,
        page_size=page_size
    )

    return AssessmentListResponse(
        assessments=[AssessmentResponse.model_validate(a) for a in assessments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific assessment by ID."""
    user, context = user_context
    service = get_service(db)

    assessment = await service.get_assessment(assessment_id, context.tenant_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return AssessmentResponse.model_validate(assessment)


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """
    Delete an assessment.

    Requires organization admin role.
    """
    user, context = user_context
    service = get_service(db)

    success = await service.delete_assessment(assessment_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )


# ========== Wizard Steps Endpoints ==========

@router.put("/assessments/{assessment_id}/scope", response_model=AssessmentResponse)
async def update_assessment_scope(
    assessment_id: str,
    data: AssessmentScopeUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Update assessment scope (Wizard Step 1).

    Define:
    - Scope description
    - Systems in scope
    - Locations in scope
    - Processes in scope
    - Risk appetite
    """
    user, context = user_context
    service = get_service(db)

    assessment = await service.update_assessment_scope(
        assessment_id=assessment_id,
        tenant_id=context.tenant_id,
        data=data
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get current wizard state for an assessment.

    Returns:
    - Current step number (1-6)
    - Step name
    - All steps with status
    - Validation errors if any
    - Can proceed flag
    """
    user, context = user_context
    service = get_service(db)

    state = await service.get_wizard_state(assessment_id, context.tenant_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return WizardState(**state)


# ========== Statement of Applicability Endpoints ==========

@router.get("/assessments/{assessment_id}/soa", response_model=SoAListResponse)
async def get_soa_entries(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    theme: Optional[str] = Query(None, description="Filter by theme (A.5, A.6, A.7, A.8)"),
):
    """
    Get Statement of Applicability entries for an assessment.

    - **theme**: Optional filter by theme
    """
    user, context = user_context
    service = get_service(db)

    entries = await service.get_soa_entries(
        assessment_id=assessment_id,
        tenant_id=context.tenant_id,
        theme=theme
    )

    if not entries and theme is None:
        # Check if assessment exists
        assessment = await service.get_assessment(assessment_id, context.tenant_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )

    # Calculate stats
    by_theme: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for entry in entries:
        theme_key = entry.get("control_theme", "unknown")
        by_theme[theme_key] = by_theme.get(theme_key, 0) + 1

        status_key = entry.get("status", "unknown")
        by_status[status_key] = by_status.get(status_key, 0) + 1

    return SoAListResponse(
        entries=[SoAEntryResponse(**e) for e in entries],
        total=len(entries),
        by_theme=by_theme,
        by_status=by_status
    )


@router.put("/assessments/{assessment_id}/soa/{control_code}", response_model=SoAEntryResponse)
async def update_soa_entry(
    assessment_id: str,
    control_code: str,
    data: SoAEntryUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Update a single SoA entry.

    - **control_code**: Control identifier (e.g., A.5.1)
    """
    user, context = user_context
    service = get_service(db)

    entry = await service.update_soa_entry(
        assessment_id=assessment_id,
        control_code=control_code,
        tenant_id=context.tenant_id,
        data=data,
        assessed_by=user.id
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment or control not found"
        )

    # Get the full entry with control details
    entries = await service.get_soa_entries(assessment_id, context.tenant_id)
    for e in entries:
        if e.get("control_code") == control_code:
            return SoAEntryResponse(**e)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error retrieving updated entry"
    )


@router.put("/assessments/{assessment_id}/soa")
async def bulk_update_soa_entries(
    assessment_id: str,
    data: SoAEntryBulkUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Bulk update SoA entries.

    Body should contain a map of control_code to update data:
    ```json
    {
      "entries": {
        "A.5.1": {"status": "compliant", "implementation_level": 100},
        "A.5.2": {"status": "partial", "implementation_level": 50}
      }
    }
    ```
    """
    user, context = user_context
    service = get_service(db)

    count = await service.bulk_update_soa_entries(
        assessment_id=assessment_id,
        tenant_id=context.tenant_id,
        entries=data.entries,
        assessed_by=user.id
    )

    return {"updated": count, "total_submitted": len(data.entries)}


# ========== Analysis & Reports Endpoints ==========

@router.get("/assessments/{assessment_id}/overview", response_model=AssessmentOverview)
async def get_assessment_overview(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get detailed overview of an assessment.

    Includes:
    - Assessment details
    - Theme-wise breakdown
    - Overall compliance statistics
    - Completion percentage
    """
    user, context = user_context
    service = get_service(db)

    overview = await service.get_assessment_overview(assessment_id, context.tenant_id)
    if not overview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return AssessmentOverview(
        assessment=AssessmentResponse.model_validate(overview["assessment"]),
        themes=overview["themes"],
        total_applicable=overview["total_applicable"],
        total_compliant=overview["total_compliant"],
        total_partial=overview["total_partial"],
        total_gap=overview["total_gap"],
        overall_score=overview["overall_score"],
        completion_percentage=overview["completion_percentage"],
    )


@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get gap analysis for an assessment.

    Returns all controls with GAP or PARTIAL status, including:
    - Gap descriptions
    - Remediation plans
    - Cross-framework references for context
    - Priority breakdown
    """
    user, context = user_context
    service = get_service(db)

    gap_analysis = await service.get_gap_analysis(assessment_id, context.tenant_id)
    if not gap_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return GapAnalysisResponse(**gap_analysis)


@router.get("/assessments/{assessment_id}/mapping", response_model=CrossFrameworkMappingResponse)
async def get_cross_framework_mapping(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get cross-framework mapping for an assessment.

    Shows how ISO 27001 controls map to:
    - BSI IT-Grundschutz
    - NIS2 Directive
    - NIST CSF
    """
    user, context = user_context
    service = get_service(db)

    mapping = await service.get_cross_framework_mapping(assessment_id, context.tenant_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return CrossFrameworkMappingResponse(**mapping)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    data: CompleteAssessmentRequest,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Mark an assessment as complete.

    This will:
    1. Recalculate all scores
    2. Set status to COMPLETED
    3. Record completion timestamp
    """
    if not data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm completion by setting confirm=true"
        )

    user, context = user_context
    service = get_service(db)

    assessment = await service.complete_assessment(
        assessment_id=assessment_id,
        tenant_id=context.tenant_id,
        notes=data.notes
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments/{assessment_id}/report")
async def get_assessment_report(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    format: str = Query("json", regex="^(pdf|html|json)$"),
    include_gaps: bool = Query(True),
    include_evidence: bool = Query(False),
    language: str = Query("en", regex="^(en|de|es)$"),
):
    """
    Get or generate assessment report.

    - **format**: Output format (pdf, html, json)
    - **include_gaps**: Include gap analysis section
    - **include_evidence**: Include evidence details
    - **language**: Report language (en, de, es)

    For PDF format, streams the PDF file directly.
    For JSON format, returns the report data directly.
    """
    user, context = user_context
    service = get_service(db)

    # Get assessment
    assessment = await service.get_assessment(assessment_id, context.tenant_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    # Get assessment overview
    overview = await service.get_assessment_overview(assessment_id, context.tenant_id)
    if not overview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    # Get SoA entries
    soa_entries = await service.get_soa_entries(assessment_id, context.tenant_id)

    # Get gap analysis if requested
    gaps = []
    gaps_data = None
    if include_gaps:
        gaps_data = await service.get_gap_analysis(assessment_id, context.tenant_id)
        if gaps_data:
            gaps = gaps_data.get("gaps", [])

    # Get cross-framework mapping
    cross_framework = await service.get_cross_framework_mapping(assessment_id, context.tenant_id)

    if format == "json":
        return {
            "assessment_id": assessment_id,
            "format": format,
            "generated_at": datetime.utcnow().isoformat(),
            "overview": {
                "name": overview["assessment"].name,
                "status": overview["assessment"].status.value if hasattr(overview["assessment"].status, 'value') else overview["assessment"].status,
                "overall_score": overview["overall_score"],
                "completion_percentage": overview["completion_percentage"],
                "themes": overview["themes"],
            },
            "gaps": gaps_data if include_gaps else None,
            "cross_framework": cross_framework,
        }

    if format == "pdf":
        try:
            from src.services.pdf_reports import ISO27001ReportGenerator

            # Prepare assessment data as dict
            assessment_dict = {
                "id": str(assessment.id),
                "name": assessment.name,
                "description": assessment.description,
                "status": assessment.status.value if hasattr(assessment.status, 'value') else assessment.status,
                "scope_description": assessment.scope_description,
                "scope_systems": assessment.scope_systems or [],
                "scope_locations": assessment.scope_locations or [],
                "scope_processes": assessment.scope_processes or [],
                "overall_score": assessment.overall_score,
                "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
                "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            }

            # Prepare overview data
            overview_dict = {
                "overall_score": overview["overall_score"],
                "total_applicable": overview["total_applicable"],
                "total_compliant": overview["total_compliant"],
                "total_partial": overview["total_partial"],
                "total_gap": overview["total_gap"],
                "completion_percentage": overview["completion_percentage"],
                "themes": overview["themes"],
            }

            # Generate PDF
            generator = ISO27001ReportGenerator()
            pdf_bytes = generator.generate_report(
                assessment=assessment_dict,
                overview=overview_dict,
                soa_entries=soa_entries,
                gaps=gaps,
                cross_framework=cross_framework,
                language=language,
                include_soa=include_evidence,
                include_gaps=include_gaps,
                include_mapping=True,
            )

            # Stream PDF response
            filename = f"ISO27001_Report_{assessment.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(pdf_bytes)),
                }
            )

        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF generation not available. Please install reportlab: pip install reportlab"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating PDF: {str(e)}"
            )

    # HTML format - return JSON for now
    return ReportResponse(
        report_id=f"rpt_{assessment_id[:8]}",
        assessment_id=assessment_id,
        format=format,
        status="completed",
        download_url=None,
        generated_at=datetime.utcnow(),
    )
