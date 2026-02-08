"""DORA (Digital Operational Resilience Act) Assessment API endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import io

from src.api.deps import DBSession, UserWithTenant
from src.models.dora import DORAAssessmentStatus, DORAPillar
from src.schemas.dora import (
    AssessmentCreate, AssessmentScopeUpdate, RequirementResponseCreate,
    BulkRequirementUpdate, AssessmentResponse, AssessmentDetailResponse,
    AssessmentListResponse, PillarListResponse, EntityTypeListResponse,
    RequirementsListResponse, GapAnalysisResponse, AssessmentReportResponse,
    WizardState, DashboardStats,
)
from src.services.dora_service import DORAAssessmentService

router = APIRouter(prefix="/dora", tags=["DORA Compliance"])


# ============== Dashboard ==============

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get dashboard statistics for all DORA assessments."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
    stats = await service.get_dashboard_stats(context.tenant_id)
    return DashboardStats(**stats)


# ============== Reference Data ==============

@router.get("/pillars", response_model=PillarListResponse)
async def get_pillars(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get all DORA pillars with metadata."""
    service = DORAAssessmentService(db)
    data = service.get_pillars_info()
    return PillarListResponse(**data)


@router.get("/entity-types", response_model=EntityTypeListResponse)
async def get_entity_types(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get all DORA entity types with metadata."""
    service = DORAAssessmentService(db)
    data = service.get_entity_types_info()
    return EntityTypeListResponse(**data)


@router.get("/requirements", response_model=RequirementsListResponse)
async def get_requirements(
    db: DBSession,
    user_context: UserWithTenant,
    pillar: Optional[DORAPillar] = Query(None, description="Filter by pillar"),
):
    """Get all DORA requirements (28 requirements across 5 pillars)."""
    service = DORAAssessmentService(db)
    data = service.get_requirements_info()

    if pillar:
        # Filter requirements by pillar
        pillar_key = pillar.value
        filtered_requirements = [r for r in data["requirements"] if r.pillar == pillar]
        return RequirementsListResponse(
            requirements=filtered_requirements,
            by_pillar={pillar_key: filtered_requirements},
            total_count=len(filtered_requirements),
        )

    return RequirementsListResponse(**data)


# ============== Assessment CRUD ==============

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a new DORA assessment."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected. Please select an organization first.",
        )

    service = DORAAssessmentService(db)

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
    status_filter: Optional[DORAAssessmentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List DORA assessments for the current organization."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
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
    """Get assessment details with requirement responses."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
    data = await service.get_assessment_with_responses(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return AssessmentDetailResponse(
        assessment=AssessmentResponse.model_validate(data["assessment"]),
        requirement_responses=[r for r in data["requirement_responses"]],
        scope_result=data["scope_result"],
        responses_by_pillar={
            k: list(v) for k, v in data["responses_by_pillar"].items()
        },
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

    service = DORAAssessmentService(db)
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
    """Update assessment scope (Wizard Step 1) - entity type, size, CTPP status."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
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
    """Get current wizard state for an assessment (8 steps)."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
    state = await service.get_wizard_state(assessment_id, context.tenant_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return WizardState(**state)


# ============== Requirement Responses ==============

@router.put("/assessments/{assessment_id}/requirements/{requirement_id}")
async def update_requirement_response(
    assessment_id: str,
    requirement_id: str,
    data: RequirementResponseCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a single requirement response."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    # Ensure requirement_id in path matches body
    data.requirement_id = requirement_id

    service = DORAAssessmentService(db)
    response = await service.update_requirement_response(
        assessment_id, context.tenant_id, data, current_user.id
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment or requirement not found",
        )

    await db.commit()
    return response


@router.put("/assessments/{assessment_id}/requirements")
async def bulk_update_requirements(
    assessment_id: str,
    data: BulkRequirementUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Bulk update requirement responses, optionally filtered by pillar."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
    responses = await service.bulk_update_requirements(
        assessment_id, context.tenant_id, data.responses, current_user.id, data.pillar
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
    """Get gap analysis for an assessment with pillar-by-pillar breakdown."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
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
    format: str = Query("json", pattern="^(pdf|json)$"),
):
    """
    Generate DORA assessment report.

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

    service = DORAAssessmentService(db)
    data = await service.generate_report(assessment_id, context.tenant_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    if format == "pdf":
        try:
            from src.services.pdf_reports import DORAReportGenerator

            # Generate PDF
            generator = DORAReportGenerator()
            pdf_bytes = generator.generate_report(data)

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=DORA_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                }
            )

        except ImportError:
            # Fallback: generate a simple PDF if DORA generator not available
            try:
                from src.services.pdf_reports import NIS2ReportGenerator

                # Adapt DORA data to NIS2 format for PDF generation
                assessment_data = {
                    "name": data.get("assessment_id", "DORA Assessment"),
                    "organization_name": data.get("organization_name", "Unknown Organization"),
                    "status": "completed",
                    "overall_score": data.get("overall_score", 0),
                    "compliance_level": data.get("compliance_level", "Unknown"),
                    "executive_summary": data.get("executive_summary", ""),
                    "gaps_count": len(data.get("gaps", [])),
                    "measures_compliant": sum(
                        s.get("implemented_count", 0) for s in data.get("pillar_summaries", [])
                    ),
                    "measures_total": sum(
                        s.get("requirements_count", 0) for s in data.get("pillar_summaries", [])
                    ),
                }

                classification = {
                    "entity_type": str(data.get("entity_type", "unknown")),
                    "sector": "Financial Services (DORA)",
                    "subsector": data.get("entity_type_name", ""),
                    "employee_count": 0,
                    "annual_revenue": 0,
                }

                # Convert pillar summaries to measures format
                measures = []
                for pillar in data.get("pillar_summaries", []):
                    measures.append({
                        "name": f"{pillar.get('pillar_name', '')} ({pillar.get('article_range', '')})",
                        "status": pillar.get("compliance_level", "not_evaluated").lower().replace(" ", "_"),
                        "implementation_level": pillar.get("score", 0),
                    })

                gaps = [
                    {
                        "measure_id": g.requirement_id if hasattr(g, 'requirement_id') else g.get("requirement_id", ""),
                        "measure_name": g.requirement_name if hasattr(g, 'requirement_name') else g.get("requirement_name", ""),
                        "status": str(g.status if hasattr(g, 'status') else g.get("status", "")),
                        "implementation_level": g.implementation_level if hasattr(g, 'implementation_level') else g.get("implementation_level", 0),
                        "priority": g.priority if hasattr(g, 'priority') else g.get("priority", 3),
                        "weight": g.weight if hasattr(g, 'weight') else g.get("weight", 10),
                        "impact_score": g.impact_score if hasattr(g, 'impact_score') else g.get("impact_score", 0),
                    }
                    for g in data.get("gaps", [])
                ]

                recommendations = data.get("recommendations", [])

                # Generate PDF using NIS2 generator
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
                        "Content-Disposition": f"attachment; filename=DORA_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                    }
                )

            except ImportError:
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
    """Mark DORA assessment as completed."""
    current_user, context = user_context

    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected.",
        )

    service = DORAAssessmentService(db)
    assessment = await service.complete_assessment(assessment_id, context.tenant_id)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    await db.commit()
    return AssessmentResponse.model_validate(assessment)
