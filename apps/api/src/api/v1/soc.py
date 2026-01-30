"""
SOC API Endpoints.

REST API for Security Operations Center functionality.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.services.soc_service import SOCService
from src.schemas.soc import (
    AlertCreate, AlertUpdate, AlertAssign, AlertResolve,
    AlertCommentCreate, AlertCommentResponse,
    AlertResponse, AlertListResponse, AlertBulkCreate,
    CaseCreate, CaseUpdate, CaseEscalate, CaseResolve,
    CaseTaskCreate, CaseTaskUpdate, CaseTaskResponse,
    CaseTimelineCreate, CaseTimelineResponse,
    CaseResponse, CaseListResponse,
    PlaybookCreate, PlaybookUpdate, PlaybookResponse, PlaybookListResponse,
    PlaybookExecutionCreate, PlaybookExecutionResponse,
    ShiftHandoverCreate, ShiftHandoverResponse,
    SOCDashboardStats,
    AlertSeverity, AlertStatus, AlertSource,
    CaseStatus, CasePriority, PlaybookStatus, PlaybookTriggerType
)

router = APIRouter(prefix="/soc", tags=["SOC"])


# ==================== Alerts ====================

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new security alert."""
    service = SOCService(db)
    return await service.create_alert(data)


@router.post("/alerts/bulk", status_code=status.HTTP_201_CREATED)
async def create_alerts_bulk(
    data: AlertBulkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create multiple alerts at once."""
    service = SOCService(db)
    alerts = await service.create_alerts_bulk(data.alerts)
    return {"created": len(alerts), "alerts": [a.alert_id for a in alerts]}


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[AlertSeverity] = None,
    alert_status: Optional[AlertStatus] = Query(None, alias="status"),
    source: Optional[AlertSource] = None,
    assigned_to: Optional[str] = None,
    unassigned: bool = False,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List alerts with filtering and pagination."""
    service = SOCService(db)
    filters = {}
    if severity:
        filters["severity"] = severity
    if alert_status:
        filters["status"] = alert_status
    if source:
        filters["source"] = source
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if unassigned:
        filters["unassigned"] = True
    if search:
        filters["search"] = search

    return await service.list_alerts(page=page, page_size=page_size, filters=filters)


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get an alert by ID."""
    service = SOCService(db)
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alert."""
    service = SOCService(db)
    alert = await service.update_alert(alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/assign", response_model=AlertResponse)
async def assign_alert(
    alert_id: str,
    data: AlertAssign,
    db: AsyncSession = Depends(get_db)
):
    """Assign an alert to an analyst."""
    service = SOCService(db)
    alert = await service.assign_alert(alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    analyst: str = Query(..., description="Analyst acknowledging the alert"),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert."""
    service = SOCService(db)
    alert = await service.acknowledge_alert(alert_id, analyst)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    data: AlertResolve,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert."""
    service = SOCService(db)
    alert = await service.resolve_alert(alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/comments", response_model=AlertCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_alert_comment(
    alert_id: str,
    data: AlertCommentCreate,
    author: str = Query(..., description="Comment author"),
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to an alert."""
    service = SOCService(db)
    try:
        return await service.add_alert_comment(alert_id, data, author)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Cases ====================

@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    created_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new investigation case."""
    service = SOCService(db)
    return await service.create_case(data, created_by)


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_status: Optional[CaseStatus] = Query(None, alias="status"),
    priority: Optional[CasePriority] = None,
    assigned_to: Optional[str] = None,
    assigned_team: Optional[str] = None,
    overdue: bool = False,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List cases with filtering and pagination."""
    service = SOCService(db)
    filters = {}
    if case_status:
        filters["status"] = case_status
    if priority:
        filters["priority"] = priority
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if assigned_team:
        filters["assigned_team"] = assigned_team
    if overdue:
        filters["overdue"] = True
    if search:
        filters["search"] = search

    return await service.list_cases(page=page, page_size=page_size, filters=filters)


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a case by ID."""
    service = SOCService(db)
    case = await service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.alert_count = len(case.alerts) if case.alerts else 0
    case.task_count = len(case.tasks) if case.tasks else 0
    return case


@router.put("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a case."""
    service = SOCService(db)
    case = await service.update_case(case_id, data)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/cases/{case_id}/escalate", response_model=CaseResponse)
async def escalate_case(
    case_id: str,
    data: CaseEscalate,
    escalated_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Escalate a case."""
    service = SOCService(db)
    case = await service.escalate_case(case_id, data, escalated_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/cases/{case_id}/resolve", response_model=CaseResponse)
async def resolve_case(
    case_id: str,
    data: CaseResolve,
    resolved_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a case."""
    service = SOCService(db)
    case = await service.resolve_case(case_id, data, resolved_by)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/cases/{case_id}/alerts/{alert_id}", response_model=CaseResponse)
async def link_alert_to_case(
    case_id: str,
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Link an alert to a case."""
    service = SOCService(db)
    case = await service.link_alert_to_case(case_id, alert_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case or alert not found")
    return case


# ==================== Case Tasks ====================

@router.post("/cases/{case_id}/tasks", response_model=CaseTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_case_task(
    case_id: str,
    data: CaseTaskCreate,
    created_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a task within a case."""
    service = SOCService(db)
    return await service.create_case_task(case_id, data, created_by)


@router.put("/cases/tasks/{task_id}", response_model=CaseTaskResponse)
async def update_case_task(
    task_id: str,
    data: CaseTaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a case task."""
    service = SOCService(db)
    task = await service.update_case_task(task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ==================== Case Timeline ====================

@router.post("/cases/{case_id}/timeline", response_model=CaseTimelineResponse, status_code=status.HTTP_201_CREATED)
async def add_case_timeline(
    case_id: str,
    data: CaseTimelineCreate,
    author: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Add a timeline entry to a case."""
    service = SOCService(db)
    return await service.add_case_timeline(case_id, data, author)


# ==================== Playbooks ====================

@router.post("/playbooks", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    data: PlaybookCreate,
    created_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new playbook."""
    service = SOCService(db)
    return await service.create_playbook(data, created_by)


@router.get("/playbooks", response_model=PlaybookListResponse)
async def list_playbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    playbook_status: Optional[PlaybookStatus] = Query(None, alias="status"),
    trigger_type: Optional[PlaybookTriggerType] = None,
    is_enabled: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List playbooks with filtering."""
    service = SOCService(db)
    filters = {}
    if playbook_status:
        filters["status"] = playbook_status
    if trigger_type:
        filters["trigger_type"] = trigger_type
    if is_enabled is not None:
        filters["is_enabled"] = is_enabled
    if category:
        filters["category"] = category
    if search:
        filters["search"] = search

    return await service.list_playbooks(page=page, page_size=page_size, filters=filters)


@router.get("/playbooks/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a playbook by ID."""
    service = SOCService(db)
    playbook = await service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.put("/playbooks/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str,
    data: PlaybookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a playbook."""
    service = SOCService(db)
    playbook = await service.update_playbook(playbook_id, data)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("/playbooks/{playbook_id}/execute", response_model=PlaybookExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_playbook(
    playbook_id: str,
    data: PlaybookExecutionCreate,
    executed_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Execute a playbook."""
    service = SOCService(db)
    try:
        return await service.execute_playbook(playbook_id, data, executed_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/playbooks/executions/{execution_id}/approve", response_model=PlaybookExecutionResponse)
async def approve_execution(
    execution_id: str,
    approved_by: str = Query(..., description="Approver"),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending playbook execution."""
    service = SOCService(db)
    execution = await service.approve_execution(execution_id, approved_by)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found or not pending")
    return execution


# ==================== Dashboard & Metrics ====================

@router.get("/dashboard", response_model=SOCDashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """Get SOC dashboard statistics."""
    service = SOCService(db)
    return await service.get_dashboard_stats()


# ==================== Shift Handover ====================

@router.post("/handover", response_model=ShiftHandoverResponse, status_code=status.HTTP_201_CREATED)
async def create_handover(
    data: ShiftHandoverCreate,
    analyst: str = Query(..., description="Outgoing analyst"),
    db: AsyncSession = Depends(get_db)
):
    """Create a shift handover."""
    service = SOCService(db)
    return await service.create_shift_handover(data, analyst)


@router.post("/handover/{handover_id}/acknowledge", response_model=ShiftHandoverResponse)
async def acknowledge_handover(
    handover_id: str,
    analyst: str = Query(..., description="Incoming analyst"),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge a shift handover."""
    service = SOCService(db)
    handover = await service.acknowledge_handover(handover_id, analyst)
    if not handover:
        raise HTTPException(status_code=404, detail="Handover not found")
    return handover


@router.get("/handover/latest", response_model=ShiftHandoverResponse)
async def get_latest_handover(
    db: AsyncSession = Depends(get_db)
):
    """Get the latest shift handover."""
    service = SOCService(db)
    handover = await service.get_latest_handover()
    if not handover:
        raise HTTPException(status_code=404, detail="No handover found")
    return handover
