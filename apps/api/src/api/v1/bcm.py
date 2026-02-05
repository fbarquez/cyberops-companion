"""Business Continuity Management (BCM) API endpoints."""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from src.db.database import get_db
from src.api.deps import (
    CurrentUser, DBSession, UserWithTenant, OrgAdmin
)
from src.services.bcm_service import BCMService
from src.schemas.bcm import (
    # Enums
    BCMProcessCriticality, BCMProcessStatus, BCMBIAStatus,
    BCMScenarioCategory, BCMScenarioStatus,
    BCMPlanType, BCMPlanStatus,
    BCMExerciseType, BCMExerciseStatus,
    BCMAssessmentStatus,
    # Process schemas
    ProcessCreate, ProcessUpdate, ProcessResponse, ProcessListResponse,
    # BIA schemas
    BIACreate, BIAResponse, BIASummaryResponse,
    # Scenario schemas
    ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioListResponse, RiskMatrixData,
    # Strategy schemas
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse,
    # Plan schemas
    PlanCreate, PlanUpdate, PlanResponse, PlanListResponse, PlanApproveRequest,
    # Contact schemas
    ContactCreate, ContactUpdate, ContactResponse, ContactListResponse,
    # Exercise schemas
    ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseListResponse, ExerciseCompleteRequest,
    # Assessment schemas
    AssessmentCreate, AssessmentResponse, AssessmentListResponse, CompleteAssessmentRequest,
    # Other schemas
    BCMDashboardStats, WizardState, BCMReportData,
)

router = APIRouter(prefix="/bcm")


def get_service(db: AsyncSession) -> BCMService:
    """Get BCM service instance."""
    return BCMService(db)


# ========== Dashboard Endpoint ==========

@router.get("/dashboard", response_model=BCMDashboardStats)
async def get_dashboard(
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get BCM dashboard statistics for the current tenant.

    Returns:
    - Process counts and criticality breakdown
    - BIA completion percentage
    - Scenario counts and risk distribution
    - Plan counts and types
    - Exercise statistics
    - Latest assessment score
    - Recent activity
    """
    user, context = user_context
    service = get_service(db)
    stats = await service.get_dashboard_stats(context.tenant_id)
    return BCMDashboardStats(**stats)


# ========== Process CRUD Endpoints ==========

@router.get("/processes", response_model=ProcessListResponse)
async def list_processes(
    db: DBSession,
    user_context: UserWithTenant,
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List business processes."""
    user, context = user_context
    service = get_service(db)

    processes = await service.list_processes(
        tenant_id=context.tenant_id,
        criticality=criticality,
        status=status,
        page=page,
        page_size=page_size
    )

    # Add BIA info to each process
    process_responses = []
    for p in processes:
        bia = await service.get_bia(p.id, context.tenant_id)
        response = ProcessResponse.model_validate(p)
        response.has_bia = bia is not None
        response.bia_status = bia.status if bia else None
        process_responses.append(response)

    return ProcessListResponse(
        processes=process_responses,
        total=len(processes),
        page=page,
        page_size=page_size
    )


@router.post("/processes", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED)
async def create_process(
    data: ProcessCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a new business process."""
    user, context = user_context
    service = get_service(db)

    process = await service.create_process(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return ProcessResponse.model_validate(process)


@router.get("/processes/{process_id}", response_model=ProcessResponse)
async def get_process(
    process_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific process by ID."""
    user, context = user_context
    service = get_service(db)

    process = await service.get_process(process_id, context.tenant_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    bia = await service.get_bia(process_id, context.tenant_id)
    response = ProcessResponse.model_validate(process)
    response.has_bia = bia is not None
    response.bia_status = bia.status if bia else None

    return response


@router.put("/processes/{process_id}", response_model=ProcessResponse)
async def update_process(
    process_id: str,
    data: ProcessUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a process."""
    user, context = user_context
    service = get_service(db)

    process = await service.update_process(process_id, context.tenant_id, data)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    return ProcessResponse.model_validate(process)


@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_process(
    process_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Delete a process. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_process(process_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )


# ========== BIA Endpoints ==========

@router.get("/processes/{process_id}/bia", response_model=BIAResponse)
async def get_process_bia(
    process_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get BIA for a process."""
    user, context = user_context
    service = get_service(db)

    # Verify process exists
    process = await service.get_process(process_id, context.tenant_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    bia = await service.get_bia(process_id, context.tenant_id)
    if not bia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BIA not found for this process"
        )

    response = BIAResponse.model_validate(bia)
    response.process_name = process.name
    response.process_criticality = process.criticality

    return response


@router.post("/processes/{process_id}/bia", response_model=BIAResponse)
async def create_or_update_bia(
    process_id: str,
    data: BIACreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create or update BIA for a process."""
    user, context = user_context
    service = get_service(db)

    bia = await service.create_or_update_bia(process_id, context.tenant_id, data)
    if not bia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    process = await service.get_process(process_id, context.tenant_id)
    response = BIAResponse.model_validate(bia)
    if process:
        response.process_name = process.name
        response.process_criticality = process.criticality

    return response


@router.get("/bia/summary", response_model=BIASummaryResponse)
async def get_bia_summary(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get BIA summary across all processes."""
    user, context = user_context
    service = get_service(db)

    summary = await service.get_bia_summary(context.tenant_id)
    return BIASummaryResponse(**summary)


# ========== Risk Scenario Endpoints ==========

@router.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios(
    db: DBSession,
    user_context: UserWithTenant,
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """List risk scenarios."""
    user, context = user_context
    service = get_service(db)

    scenarios, total = await service.list_scenarios(
        tenant_id=context.tenant_id,
        category=category,
        page=page,
        page_size=page_size
    )

    return ScenarioListResponse(
        scenarios=[ScenarioResponse.model_validate(s) for s in scenarios],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/scenarios", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a risk scenario."""
    user, context = user_context
    service = get_service(db)

    scenario = await service.create_scenario(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return ScenarioResponse.model_validate(scenario)


@router.get("/scenarios/risk-matrix", response_model=RiskMatrixData)
async def get_risk_matrix(
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get risk matrix data for visualization."""
    user, context = user_context
    service = get_service(db)

    matrix_data = await service.get_risk_matrix(context.tenant_id)
    return RiskMatrixData(**matrix_data)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific scenario by ID."""
    user, context = user_context
    service = get_service(db)

    scenario = await service.get_scenario(scenario_id, context.tenant_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    return ScenarioResponse.model_validate(scenario)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    data: ScenarioUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a scenario."""
    user, context = user_context
    service = get_service(db)

    scenario = await service.update_scenario(
        scenario_id, context.tenant_id, data, user.id
    )
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )

    return ScenarioResponse.model_validate(scenario)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Delete a scenario. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_scenario(scenario_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )


# ========== Strategy Endpoints ==========

@router.get("/processes/{process_id}/strategies", response_model=StrategyListResponse)
async def list_process_strategies(
    process_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """List strategies for a process."""
    user, context = user_context
    service = get_service(db)

    # Verify process exists
    process = await service.get_process(process_id, context.tenant_id)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    strategies = await service.list_strategies_for_process(process_id, context.tenant_id)

    strategy_responses = []
    for s in strategies:
        response = StrategyResponse.model_validate(s)
        response.process_name = process.name
        strategy_responses.append(response)

    return StrategyListResponse(
        strategies=strategy_responses,
        total=len(strategies)
    )


@router.post("/processes/{process_id}/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    process_id: str,
    data: StrategyCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a strategy for a process."""
    user, context = user_context
    service = get_service(db)

    strategy = await service.create_strategy(process_id, context.tenant_id, data)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found"
        )

    return StrategyResponse.model_validate(strategy)


@router.put("/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    data: StrategyUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a strategy."""
    user, context = user_context
    service = get_service(db)

    strategy = await service.update_strategy(strategy_id, context.tenant_id, data)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    return StrategyResponse.model_validate(strategy)


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Delete a strategy. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_strategy(strategy_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )


# ========== Emergency Plan Endpoints ==========

@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    db: DBSession,
    user_context: UserWithTenant,
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    plan_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List emergency plans."""
    user, context = user_context
    service = get_service(db)

    plans, total = await service.list_plans(
        tenant_id=context.tenant_id,
        plan_type=plan_type,
        status=plan_status,
        page=page,
        page_size=page_size
    )

    return PlanListResponse(
        plans=[PlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create an emergency plan."""
    user, context = user_context
    service = get_service(db)

    plan = await service.create_plan(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return PlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific plan by ID."""
    user, context = user_context
    service = get_service(db)

    plan = await service.get_plan(plan_id, context.tenant_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    return PlanResponse.model_validate(plan)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: str,
    data: PlanUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a plan."""
    user, context = user_context
    service = get_service(db)

    plan = await service.update_plan(plan_id, context.tenant_id, data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    return PlanResponse.model_validate(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Delete a plan. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_plan(plan_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )


@router.post("/plans/{plan_id}/approve", response_model=PlanResponse)
async def approve_plan(
    plan_id: str,
    data: PlanApproveRequest,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Approve a plan. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    plan = await service.approve_plan(plan_id, context.tenant_id, data.approved_by)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    return PlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}/export")
async def export_plan(
    plan_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    format: str = Query("pdf", regex="^(pdf|json)$"),
):
    """Export a plan as PDF or JSON."""
    user, context = user_context
    service = get_service(db)

    plan = await service.get_plan(plan_id, context.tenant_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    if format == "json":
        return PlanResponse.model_validate(plan)

    # PDF export
    try:
        from src.services.pdf_reports.bcm_report_generator import BCMReportGenerator

        generator = BCMReportGenerator()
        pdf_bytes = generator.generate_plan_pdf(plan)

        filename = f"BCM_Plan_{plan.plan_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF generation not available"
        )


# ========== Contact Endpoints ==========

@router.get("/contacts", response_model=ContactListResponse)
async def list_contacts(
    db: DBSession,
    user_context: UserWithTenant,
):
    """List emergency contacts ordered by priority."""
    user, context = user_context
    service = get_service(db)

    contacts = await service.list_contacts(context.tenant_id)

    return ContactListResponse(
        contacts=[ContactResponse.model_validate(c) for c in contacts],
        total=len(contacts)
    )


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create an emergency contact."""
    user, context = user_context
    service = get_service(db)

    contact = await service.create_contact(context.tenant_id, data)
    return ContactResponse.model_validate(contact)


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a contact."""
    user, context = user_context
    service = get_service(db)

    contact = await service.update_contact(contact_id, context.tenant_id, data)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return ContactResponse.model_validate(contact)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Delete a contact."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_contact(contact_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )


# ========== Exercise Endpoints ==========

@router.get("/exercises", response_model=ExerciseListResponse)
async def list_exercises(
    db: DBSession,
    user_context: UserWithTenant,
    exercise_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List BC exercises."""
    user, context = user_context
    service = get_service(db)

    exercises, total = await service.list_exercises(
        tenant_id=context.tenant_id,
        status=exercise_status,
        page=page,
        page_size=page_size
    )

    exercise_responses = []
    for e in exercises:
        response = ExerciseResponse.model_validate(e)
        # Add scenario name if linked
        if e.scenario_id:
            scenario = await service.get_scenario(e.scenario_id, context.tenant_id)
            if scenario:
                response.scenario_name = scenario.name
        # Add plan name if linked
        if e.plan_id:
            plan = await service.get_plan(e.plan_id, context.tenant_id)
            if plan:
                response.plan_name = plan.name
        exercise_responses.append(response)

    return ExerciseListResponse(
        exercises=exercise_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    data: ExerciseCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a BC exercise."""
    user, context = user_context
    service = get_service(db)

    exercise = await service.create_exercise(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return ExerciseResponse.model_validate(exercise)


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific exercise by ID."""
    user, context = user_context
    service = get_service(db)

    exercise = await service.get_exercise(exercise_id, context.tenant_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    response = ExerciseResponse.model_validate(exercise)
    # Add scenario name if linked
    if exercise.scenario_id:
        scenario = await service.get_scenario(exercise.scenario_id, context.tenant_id)
        if scenario:
            response.scenario_name = scenario.name
    # Add plan name if linked
    if exercise.plan_id:
        plan = await service.get_plan(exercise.plan_id, context.tenant_id)
        if plan:
            response.plan_name = plan.name

    return response


@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: str,
    data: ExerciseUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update an exercise."""
    user, context = user_context
    service = get_service(db)

    exercise = await service.update_exercise(exercise_id, context.tenant_id, data)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    return ExerciseResponse.model_validate(exercise)


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: str,
    db: DBSession,
    user_context: OrgAdmin,
):
    """Delete an exercise. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_exercise(exercise_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )


@router.post("/exercises/{exercise_id}/complete", response_model=ExerciseResponse)
async def complete_exercise(
    exercise_id: str,
    data: ExerciseCompleteRequest,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Complete an exercise with results."""
    user, context = user_context
    service = get_service(db)

    exercise = await service.complete_exercise(
        exercise_id, context.tenant_id, data, user.id
    )
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    return ExerciseResponse.model_validate(exercise)


# ========== Assessment Endpoints ==========

@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    db: DBSession,
    user_context: UserWithTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List BCM assessments."""
    user, context = user_context
    service = get_service(db)

    assessments, total = await service.list_assessments(
        tenant_id=context.tenant_id,
        page=page,
        page_size=page_size
    )

    return AssessmentListResponse(
        assessments=[AssessmentResponse.model_validate(a) for a in assessments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    data: AssessmentCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Create a BCM assessment."""
    user, context = user_context
    service = get_service(db)

    assessment = await service.create_assessment(
        tenant_id=context.tenant_id,
        data=data,
        created_by=user.id
    )

    return AssessmentResponse.model_validate(assessment)


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
    """Delete an assessment. Requires organization admin role."""
    user, context = user_context
    service = get_service(db)

    success = await service.delete_assessment(assessment_id, context.tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )


@router.get("/assessments/{assessment_id}/wizard-state", response_model=WizardState)
async def get_wizard_state(
    assessment_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get current wizard state for an assessment."""
    user, context = user_context
    service = get_service(db)

    state = await service.get_wizard_state(assessment_id, context.tenant_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return WizardState(**state)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    data: CompleteAssessmentRequest,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Mark an assessment as complete."""
    if not data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm completion by setting confirm=true"
        )

    user, context = user_context
    service = get_service(db)

    assessment = await service.complete_assessment(assessment_id, context.tenant_id)
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
    format: str = Query("json", regex="^(pdf|json)$"),
):
    """Get or generate assessment report."""
    user, context = user_context
    service = get_service(db)

    assessment = await service.get_assessment(assessment_id, context.tenant_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    # Recalculate scores
    await service.recalculate_assessment_scores(assessment_id, context.tenant_id)

    # Get all data for the report
    processes = await service.list_processes(context.tenant_id)
    bia_summary = await service.get_bia_summary(context.tenant_id)
    scenarios, _ = await service.list_scenarios(context.tenant_id)
    plans, _ = await service.list_plans(context.tenant_id)
    exercises, _ = await service.list_exercises(context.tenant_id)

    if format == "json":
        return {
            "assessment": AssessmentResponse.model_validate(assessment),
            "processes": [ProcessResponse.model_validate(p) for p in processes],
            "bia_summary": BIASummaryResponse(**bia_summary),
            "scenarios": [ScenarioResponse.model_validate(s) for s in scenarios],
            "plans": [PlanResponse.model_validate(p) for p in plans],
            "exercises": [ExerciseResponse.model_validate(e) for e in exercises],
            "generated_at": datetime.utcnow().isoformat(),
        }

    # PDF export
    try:
        from src.services.pdf_reports.bcm_report_generator import BCMReportGenerator

        generator = BCMReportGenerator()
        pdf_bytes = generator.generate_assessment_report(
            assessment=assessment,
            processes=processes,
            bia_summary=bia_summary,
            scenarios=scenarios,
            plans=plans,
            exercises=exercises,
        )

        filename = f"BCM_Assessment_Report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF generation not available"
        )
