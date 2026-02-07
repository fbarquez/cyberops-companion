"""NIS2 Assessment Wizard API endpoints."""
from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import io

from src.api.deps import DBSession, UserWithTenant
from src.models.nis2 import NIS2AssessmentStatus
from src.schemas.nis2 import (
    AssessmentCreate, AssessmentScopeUpdate, MeasureResponseCreate,
    BulkMeasureUpdate, AssessmentResponse, AssessmentDetailResponse,
    AssessmentListResponse, SectorListResponse, MeasuresListResponse,
    GapAnalysisResponse, AssessmentReportResponse, WizardState,
)
from src.services.nis2_service import NIS2AssessmentService

router = APIRouter(prefix="/nis2")


# ============== Dashboard ==============

@router.get("/dashboard")
async def get_dashboard_stats(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get dashboard statistics for all NIS2 assessments."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    stats = await service.get_dashboard_stats(context.tenant_id)
    return stats


# ============== Reference Data ==============

@router.get("/sectors", response_model=SectorListResponse)
async def get_sectors(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get all NIS2 sectors with metadata for the wizard."""
    service = NIS2AssessmentService(db)
    data = service.get_sectors_info()
    return SectorListResponse(**data)


@router.get("/measures", response_model=MeasuresListResponse)
async def get_security_measures(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get all NIS2 security measures (Article 21)."""
    service = NIS2AssessmentService(db)
    data = service.get_security_measures()
    return MeasuresListResponse(**data)


# ============== Assessment CRUD ==============

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a new NIS2 assessment."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected. Please select an organization first.",
        )

    service = NIS2AssessmentService(db)

    try:
        assessment = await service.create_assessment(
            data=data,
            user_id=current_user.id,
            tenant_id=context.tenant_id,
        )
        await db.commit()
        return AssessmentResponse.model_validate(assessment)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    db: DBSession,
    user_context: UserWithTenant,
    status_filter: Optional[NIS2AssessmentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List NIS2 assessments for the current organization."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    assessments, total = await service.list_assessments(
        tenant_id=context.tenant_id,
        status=status_filter,
        page=page,
        size=size,
    )

    return AssessmentListResponse(
        assessments=[AssessmentResponse.model_validate(a) for a in assessments],
        total=total,
        page=page,
        size=size,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get assessment details with measure responses."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    data = await service.get_assessment_with_responses(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return AssessmentDetailResponse(
        assessment=AssessmentResponse.model_validate(data["assessment"]),
        measure_responses=[r for r in data["measure_responses"]],
        classification=data["classification"],
    )


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Delete an assessment."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    deleted = await service.delete_assessment(assessment_id, context.tenant_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()


# ============== Wizard Steps ==============

@router.put("/assessments/{assessment_id}/scope", response_model=AssessmentResponse)
async def update_assessment_scope(
    assessment_id: str,
    data: AssessmentScopeUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update assessment scope (Wizard Step 1) and get classification."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    assessment = await service.update_scope(assessment_id, context.tenant_id, data)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get current wizard state for an assessment."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    data = await service.get_assessment_with_responses(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    assessment = data["assessment"]
    responses = data["measure_responses"]

    # Determine completed steps
    steps_completed = []

    # Step 1: Scope
    if assessment.sector and assessment.company_size:
        steps_completed.append(1)

    # Step 2: Classification (auto-completed with step 1)
    if assessment.entity_type:
        steps_completed.append(2)

    # Step 3-4: Measures (at least one evaluated)
    evaluated_count = sum(1 for r in responses if r.status.value != "not_evaluated")
    if evaluated_count > 0:
        steps_completed.append(3)
    if evaluated_count == len(responses):
        steps_completed.append(4)

    # Step 5: Gap Analysis (always available after measures)
    if 4 in steps_completed:
        steps_completed.append(5)

    # Determine current step
    if not steps_completed:
        current_step = 1
    elif 5 in steps_completed:
        current_step = 6  # Report
    elif 4 in steps_completed:
        current_step = 5
    elif 3 in steps_completed:
        current_step = 4
    elif 2 in steps_completed:
        current_step = 3
    else:
        current_step = 2

    return WizardState(
        current_step=current_step,
        total_steps=6,
        assessment_id=assessment_id,
        can_go_back=current_step > 1,
        can_go_forward=current_step < 6 and (current_step - 1) in steps_completed or current_step == 1,
        is_complete=assessment.status == NIS2AssessmentStatus.COMPLETED,
        steps_completed=steps_completed,
    )


# ============== Measure Responses ==============

@router.put("/assessments/{assessment_id}/measures/{measure_id}")
async def update_measure_response(
    assessment_id: str,
    measure_id: str,
    data: MeasureResponseCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a single measure response."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    # Ensure measure_id in path matches body
    data.measure_id = measure_id

    service = NIS2AssessmentService(db)
    response = await service.update_measure_response(
        assessment_id, context.tenant_id, data, current_user.id
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()
    return response


@router.put("/assessments/{assessment_id}/measures")
async def bulk_update_measures(
    assessment_id: str,
    data: BulkMeasureUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Bulk update measure responses."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    responses = await service.bulk_update_measures(
        assessment_id, context.tenant_id, data.responses, current_user.id
    )

    if not responses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()
    return responses


# ============== Gap Analysis ==============

@router.get("/assessments/{assessment_id}/gaps", response_model=GapAnalysisResponse)
async def get_gap_analysis(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get gap analysis for an assessment."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    data = await service.get_gap_analysis(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return GapAnalysisResponse(**data)


# ============== Report ==============

@router.get("/assessments/{assessment_id}/report", response_model=None)
async def get_assessment_report(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    format: str = Query("json", regex="^(pdf|json)$"),
):
    """
    Generate assessment report.

    - **format**: Output format (pdf, json)

    For PDF format, streams the PDF file directly.
    For JSON format, returns the report data directly.
    """
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    data = await service.generate_report(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    if format == "pdf":
        try:
            from src.services.pdf_reports import NIS2ReportGenerator

            # Prepare data for PDF generator
            assessment_data = {
                "name": data.get("assessment_id", "NIS2 Assessment"),
                "organization_name": data.get("organization_name", "Unknown Organization"),
                "status": "completed",
                "overall_score": data.get("overall_score", 0),
                "compliance_level": data.get("compliance_level", "Unknown"),
                "executive_summary": data.get("executive_summary", ""),
                "gaps_count": len(data.get("gaps", [])),
                "measures_compliant": sum(1 for s in data.get("sections", []) if s.get("status") == "compliant"),
                "measures_total": len(data.get("sections", [])),
            }

            classification_data = data.get("entity_classification", {})
            if isinstance(classification_data, dict):
                classification = {
                    "entity_type": classification_data.get("entity_type", "unknown"),
                    "sector": classification_data.get("sector", "unknown"),
                    "subsector": classification_data.get("subsector", ""),
                    "employee_count": classification_data.get("employee_count", 0),
                    "annual_revenue": classification_data.get("annual_revenue", 0),
                }
            else:
                classification = {
                    "entity_type": "unknown",
                    "sector": "unknown",
                    "subsector": "",
                    "employee_count": 0,
                    "annual_revenue": 0,
                }

            # Convert sections to measures format
            measures = []
            for section in data.get("sections", []):
                measures.append({
                    "name": section.get("title", "Unknown"),
                    "status": section.get("status", "not_evaluated"),
                    "implementation_level": section.get("score", 0),
                })

            gaps = data.get("gaps", [])
            recommendations = data.get("recommendations", [])

            # Generate PDF
            generator = NIS2ReportGenerator()
            pdf_bytes = generator.generate_report(
                assessment=assessment_data,
                classification=classification,
                measures=measures,
                gaps=gaps,
                recommendations=recommendations,
            )

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=NIS2_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
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

    return AssessmentReportResponse(**data)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Mark assessment as completed."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = NIS2AssessmentService(db)
    assessment = await service.complete_assessment(assessment_id, context.tenant_id)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()
    return AssessmentResponse.model_validate(assessment)
