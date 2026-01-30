"""Reporting & Analytics API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.reporting import ReportType, ReportStatus, WidgetType
from src.schemas.reporting import (
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    GenerateReportRequest, GeneratedReportResponse, GeneratedReportListResponse,
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse, ReportScheduleListResponse,
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse,
    DashboardWidgetCreate, DashboardWidgetResponse,
    ExecutiveDashboardStats, TrendData, TrendDataPoint
)
from src.services.reporting_service import ReportingService

router = APIRouter(prefix="/reporting")


# ============== Executive Dashboard ==============

@router.get("/executive-dashboard", response_model=ExecutiveDashboardStats)
async def get_executive_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get executive dashboard with aggregated KPIs."""
    service = ReportingService(db)
    return await service.get_executive_dashboard()


# ============== Report Templates ==============

@router.get("/templates")
async def list_templates(
    report_type: Optional[ReportType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List report templates."""
    service = ReportingService(db)
    templates = await service.list_templates(report_type=report_type)
    return [ReportTemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=ReportTemplateResponse)
async def create_template(
    data: ReportTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a report template."""
    service = ReportingService(db)
    template = await service.create_template(data, created_by=current_user.id)
    return ReportTemplateResponse.model_validate(template)


@router.post("/templates/seed")
async def seed_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed default report templates."""
    service = ReportingService(db)
    await service.seed_default_templates()
    return {"message": "Templates seeded successfully"}


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a report template by ID."""
    service = ReportingService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ReportTemplateResponse.model_validate(template)


@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
async def update_template(
    template_id: str,
    data: ReportTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a report template."""
    service = ReportingService(db)
    template = await service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ReportTemplateResponse.model_validate(template)


# ============== Report Generation ==============

@router.post("/reports/generate", response_model=GeneratedReportResponse)
async def generate_report(
    data: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new report."""
    if not data.template_id and not data.report_type:
        raise HTTPException(
            status_code=400,
            detail="Either template_id or report_type must be provided"
        )
    service = ReportingService(db)
    report = await service.generate_report(data, generated_by=current_user.id)
    return GeneratedReportResponse.model_validate(report)


@router.get("/reports", response_model=GeneratedReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List generated reports."""
    service = ReportingService(db)
    return await service.list_reports(
        page=page,
        size=size,
        report_type=report_type,
        status=status,
    )


@router.get("/reports/{report_id}", response_model=GeneratedReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a generated report by ID."""
    service = ReportingService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return GeneratedReportResponse.model_validate(report)


@router.get("/reports/{report_id}/data")
async def get_report_data(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get report data for rendering."""
    service = ReportingService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "report_id": report.report_id,
        "report_type": report.report_type,
        "generated_at": report.generated_at,
        "period_start": report.period_start,
        "period_end": report.period_end,
        "data": report.report_data,
    }


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a generated report file."""
    service = ReportingService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not available")

    # In production, this would return a file response or signed URL
    return {
        "download_url": f"/files/reports/{report.report_id}.{report.format.value}",
        "filename": f"{report.name}.{report.format.value}",
    }


# ============== Report Schedules ==============

@router.post("/schedules", response_model=ReportScheduleResponse)
async def create_schedule(
    data: ReportScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a report schedule."""
    service = ReportingService(db)
    schedule = await service.create_schedule(data, created_by=current_user.id)
    return ReportScheduleResponse.model_validate(schedule)


@router.get("/schedules", response_model=ReportScheduleListResponse)
async def list_schedules(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List report schedules."""
    service = ReportingService(db)
    return await service.list_schedules(page=page, size=size)


# ============== Dashboards ==============

@router.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a custom dashboard."""
    service = ReportingService(db)
    dashboard = await service.create_dashboard(data, created_by=current_user.id)
    return DashboardResponse.model_validate(dashboard)


@router.get("/dashboards", response_model=DashboardListResponse)
async def list_dashboards(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List dashboards."""
    service = ReportingService(db)
    return await service.list_dashboards(
        user_id=current_user.id,
        include_public=True,
        page=page,
        size=size,
    )


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a dashboard by ID."""
    service = ReportingService(db)
    dashboard = await service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return DashboardResponse.model_validate(dashboard)


@router.post("/dashboards/{dashboard_id}/widgets", response_model=DashboardWidgetResponse)
async def add_widget(
    dashboard_id: str,
    data: DashboardWidgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a widget to a dashboard."""
    service = ReportingService(db)
    widget = await service.add_widget(dashboard_id, data)
    if not widget:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return DashboardWidgetResponse.model_validate(widget)


# ============== Metrics & Trends ==============

@router.get("/metrics/{metric_name}/trend")
async def get_metric_trend(
    metric_name: str,
    period_days: int = Query(30, ge=1, le=365),
    aggregation: str = Query("daily"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get trend data for a specific metric."""
    service = ReportingService(db)
    trend = await service.get_metric_trend(
        metric_name=metric_name,
        period_days=period_days,
        aggregation=aggregation,
    )
    return {
        "metric_name": metric_name,
        "period_days": period_days,
        "data_points": [{"date": p.date, "value": p.value} for p in trend],
    }


@router.post("/metrics/snapshot")
async def record_metric(
    metric_name: str,
    value: float,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a metric snapshot (for automated collection)."""
    service = ReportingService(db)
    await service.record_metric_snapshot(
        metric_name=metric_name,
        value=value,
        category=category,
    )
    return {"message": "Metric recorded successfully"}
