"""Reporting & Analytics service."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.reporting import (
    ReportTemplate, GeneratedReport, ReportSchedule, ReportDistribution,
    Dashboard, DashboardWidget, MetricSnapshot, SavedQuery,
    ReportType, ReportFormat, ReportStatus, ScheduleFrequency, WidgetType
)
from src.schemas.reporting import (
    ReportTemplateCreate, ReportTemplateUpdate,
    GenerateReportRequest,
    ReportScheduleCreate, ReportScheduleUpdate,
    DashboardCreate, DashboardUpdate, DashboardWidgetCreate, DashboardWidgetUpdate,
    SavedQueryCreate,
    ExecutiveDashboardStats, TrendDataPoint
)


def generate_report_id():
    """Generate a report ID."""
    from uuid import uuid4
    now = datetime.utcnow()
    return f"RPT-{now.strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"


class ReportingService:
    """Service for reporting and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Report Templates ====================

    async def create_template(self, data: ReportTemplateCreate, created_by: str) -> ReportTemplate:
        """Create a report template."""
        template = ReportTemplate(
            name=data.name,
            description=data.description,
            report_type=data.report_type,
            config=data.config,
            logo_url=data.logo_url,
            header_template=data.header_template,
            footer_template=data.footer_template,
            supported_formats=data.supported_formats,
            is_public=data.is_public,
            allowed_roles=data.allowed_roles,
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get a template by ID."""
        result = await self.db.execute(
            select(ReportTemplate).where(ReportTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        report_type: Optional[ReportType] = None,
        is_active: bool = True,
    ) -> List[ReportTemplate]:
        """List report templates."""
        query = select(ReportTemplate)

        if report_type:
            query = query.where(ReportTemplate.report_type == report_type)
        if is_active is not None:
            query = query.where(ReportTemplate.is_active == is_active)

        query = query.order_by(ReportTemplate.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_template(self, template_id: str, data: ReportTemplateUpdate) -> Optional[ReportTemplate]:
        """Update a template."""
        template = await self.get_template(template_id)
        if not template:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def seed_default_templates(self):
        """Seed default report templates."""
        templates = [
            {
                "name": "Executive Summary Report",
                "description": "High-level security posture overview for executives",
                "report_type": ReportType.EXECUTIVE_SUMMARY,
                "config": {
                    "sections": [
                        {"title": "Security Score", "type": "metric"},
                        {"title": "Key Incidents", "type": "summary"},
                        {"title": "Risk Overview", "type": "chart"},
                        {"title": "Compliance Status", "type": "gauge"},
                        {"title": "Recommendations", "type": "list"},
                    ],
                    "default_period_days": 30,
                },
                "supported_formats": ["pdf", "html"],
            },
            {
                "name": "Incident Report",
                "description": "Detailed incident analysis and metrics",
                "report_type": ReportType.INCIDENT_REPORT,
                "config": {
                    "sections": [
                        {"title": "Incident Summary", "type": "summary"},
                        {"title": "Timeline", "type": "timeline"},
                        {"title": "Severity Distribution", "type": "chart"},
                        {"title": "MTTR Analysis", "type": "metric"},
                        {"title": "Incident Details", "type": "table"},
                    ],
                    "default_period_days": 30,
                },
                "supported_formats": ["pdf", "excel", "csv"],
            },
            {
                "name": "SOC Metrics Report",
                "description": "Security Operations Center performance metrics",
                "report_type": ReportType.SOC_METRICS,
                "config": {
                    "sections": [
                        {"title": "Alert Volume", "type": "chart"},
                        {"title": "MTTD & MTTR", "type": "metric"},
                        {"title": "Case Resolution", "type": "chart"},
                        {"title": "Analyst Performance", "type": "table"},
                        {"title": "Escalation Trends", "type": "chart"},
                    ],
                    "default_period_days": 7,
                },
                "supported_formats": ["pdf", "excel"],
            },
            {
                "name": "Vulnerability Report",
                "description": "Vulnerability assessment and remediation status",
                "report_type": ReportType.VULNERABILITY,
                "config": {
                    "sections": [
                        {"title": "Vulnerability Summary", "type": "summary"},
                        {"title": "Severity Breakdown", "type": "chart"},
                        {"title": "Aging Analysis", "type": "chart"},
                        {"title": "Top Affected Assets", "type": "table"},
                        {"title": "Remediation Progress", "type": "gauge"},
                    ],
                    "default_period_days": 30,
                },
                "supported_formats": ["pdf", "excel", "csv"],
            },
            {
                "name": "Risk Assessment Report",
                "description": "Enterprise risk analysis and treatment status",
                "report_type": ReportType.RISK_ASSESSMENT,
                "config": {
                    "sections": [
                        {"title": "Risk Overview", "type": "summary"},
                        {"title": "Risk Matrix", "type": "heatmap"},
                        {"title": "Top Risks", "type": "table"},
                        {"title": "Control Effectiveness", "type": "chart"},
                        {"title": "Treatment Progress", "type": "gauge"},
                    ],
                    "default_period_days": 90,
                },
                "supported_formats": ["pdf", "excel"],
            },
            {
                "name": "Third-Party Risk Report",
                "description": "Vendor risk assessment and compliance status",
                "report_type": ReportType.TPRM,
                "config": {
                    "sections": [
                        {"title": "Vendor Overview", "type": "summary"},
                        {"title": "Risk Distribution", "type": "chart"},
                        {"title": "High-Risk Vendors", "type": "table"},
                        {"title": "Assessment Status", "type": "gauge"},
                        {"title": "Findings Summary", "type": "chart"},
                    ],
                    "default_period_days": 90,
                },
                "supported_formats": ["pdf", "excel"],
            },
            {
                "name": "Threat Intelligence Report",
                "description": "Threat landscape and IOC analysis",
                "report_type": ReportType.THREAT_INTEL,
                "config": {
                    "sections": [
                        {"title": "Threat Overview", "type": "summary"},
                        {"title": "IOC Statistics", "type": "chart"},
                        {"title": "Threat Actors", "type": "table"},
                        {"title": "Campaign Analysis", "type": "timeline"},
                        {"title": "Top IOCs", "type": "table"},
                    ],
                    "default_period_days": 30,
                },
                "supported_formats": ["pdf", "json"],
            },
            {
                "name": "Compliance Report",
                "description": "Regulatory compliance status and gaps",
                "report_type": ReportType.COMPLIANCE,
                "config": {
                    "sections": [
                        {"title": "Compliance Score", "type": "gauge"},
                        {"title": "Framework Coverage", "type": "chart"},
                        {"title": "Control Status", "type": "table"},
                        {"title": "Gap Analysis", "type": "list"},
                        {"title": "Remediation Plan", "type": "table"},
                    ],
                    "default_period_days": 90,
                },
                "supported_formats": ["pdf", "excel"],
            },
        ]

        for template_data in templates:
            # Check if template already exists
            existing = await self.db.execute(
                select(ReportTemplate).where(
                    ReportTemplate.report_type == template_data["report_type"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            template = ReportTemplate(
                **template_data,
                is_public=True,
                is_active=True,
            )
            self.db.add(template)

        await self.db.commit()

    # ==================== Report Generation ====================

    async def generate_report(
        self,
        data: GenerateReportRequest,
        generated_by: str
    ) -> GeneratedReport:
        """Generate a report."""
        # Determine period
        period_end = data.period_end or datetime.utcnow()
        if data.period_start:
            period_start = data.period_start
        else:
            period_days = data.period_days or 30
            period_start = period_end - timedelta(days=period_days)

        # Get template if specified
        template = None
        report_type = data.report_type
        if data.template_id:
            template = await self.get_template(data.template_id)
            if template:
                report_type = template.report_type

        # Create report record
        report = GeneratedReport(
            report_id=generate_report_id(),
            name=data.name or f"{report_type.value.replace('_', ' ').title()} Report",
            description=data.description,
            report_type=report_type,
            template_id=data.template_id,
            status=ReportStatus.GENERATING,
            period_start=period_start,
            period_end=period_end,
            filters=data.filters,
            format=data.format,
            generated_by=generated_by,
        )
        self.db.add(report)
        await self.db.commit()

        # Generate report data
        try:
            start_time = datetime.utcnow()
            report_data = await self._generate_report_data(
                report_type, period_start, period_end, data.filters
            )
            generation_time = (datetime.utcnow() - start_time).total_seconds()

            report.report_data = report_data
            report.status = ReportStatus.COMPLETED
            report.generated_at = datetime.utcnow()
            report.generation_time_seconds = generation_time
            report.expires_at = datetime.utcnow() + timedelta(days=30)

        except Exception as e:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)

        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def _generate_report_data(
        self,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate report data based on type."""
        # This would normally query the respective modules
        # For now, we return structured placeholder data

        if report_type == ReportType.EXECUTIVE_SUMMARY:
            return await self._generate_executive_summary(period_start, period_end)
        elif report_type == ReportType.INCIDENT_REPORT:
            return await self._generate_incident_report(period_start, period_end, filters)
        elif report_type == ReportType.SOC_METRICS:
            return await self._generate_soc_report(period_start, period_end, filters)
        elif report_type == ReportType.VULNERABILITY:
            return await self._generate_vulnerability_report(period_start, period_end, filters)
        elif report_type == ReportType.RISK_ASSESSMENT:
            return await self._generate_risk_report(period_start, period_end, filters)
        elif report_type == ReportType.TPRM:
            return await self._generate_tprm_report(period_start, period_end, filters)
        else:
            return {"message": "Report type not yet implemented"}

    async def _generate_executive_summary(
        self, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Generate executive summary data."""
        # This would aggregate data from all modules
        return {
            "summary": {
                "security_score": 78,
                "security_score_change": 3,
                "period": f"{period_start.date()} to {period_end.date()}",
            },
            "highlights": [
                {"metric": "Incidents Resolved", "value": 45, "trend": "up"},
                {"metric": "Mean Time to Respond", "value": "4.2 hours", "trend": "down"},
                {"metric": "Vulnerabilities Patched", "value": 128, "trend": "up"},
                {"metric": "Compliance Score", "value": "92%", "trend": "stable"},
            ],
            "sections": [
                {
                    "title": "Security Incidents",
                    "metrics": {"total": 52, "critical": 3, "high": 12, "resolved": 45},
                },
                {
                    "title": "Vulnerabilities",
                    "metrics": {"total": 234, "critical": 8, "remediated": 128, "overdue": 12},
                },
                {
                    "title": "Risk Posture",
                    "metrics": {"total_risks": 45, "critical": 2, "treated": 38},
                },
            ],
            "recommendations": [
                "Address 3 critical vulnerabilities in production systems",
                "Complete risk treatment plans for 2 high-priority risks",
                "Review and update incident response procedures",
            ],
        }

    async def _generate_incident_report(
        self, period_start: datetime, period_end: datetime, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate incident report data."""
        return {
            "summary": {
                "total_incidents": 52,
                "by_severity": {"critical": 3, "high": 12, "medium": 25, "low": 12},
                "by_status": {"active": 7, "contained": 5, "closed": 40},
                "mttr_hours": 4.2,
            },
            "charts": [
                {"type": "line", "title": "Incidents Over Time", "data": []},
                {"type": "pie", "title": "By Severity", "data": []},
            ],
            "tables": [
                {
                    "title": "Recent Incidents",
                    "columns": ["ID", "Title", "Severity", "Status", "Created"],
                    "rows": [],
                }
            ],
        }

    async def _generate_soc_report(
        self, period_start: datetime, period_end: datetime, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate SOC metrics report data."""
        return {
            "summary": {
                "total_alerts": 1250,
                "alerts_by_severity": {"critical": 45, "high": 180, "medium": 520, "low": 505},
                "total_cases": 85,
                "cases_resolved": 72,
                "mttd_minutes": 12,
                "mttr_minutes": 45,
            },
            "charts": [
                {"type": "line", "title": "Alert Volume", "data": []},
                {"type": "bar", "title": "Response Times", "data": []},
            ],
        }

    async def _generate_vulnerability_report(
        self, period_start: datetime, period_end: datetime, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate vulnerability report data."""
        return {
            "summary": {
                "total_vulnerabilities": 234,
                "by_severity": {"critical": 8, "high": 45, "medium": 98, "low": 83},
                "by_status": {"open": 78, "in_progress": 34, "remediated": 122},
                "overdue": 12,
                "patch_compliance": 85.5,
            },
            "charts": [
                {"type": "bar", "title": "By Severity", "data": []},
                {"type": "line", "title": "Remediation Trend", "data": []},
            ],
        }

    async def _generate_risk_report(
        self, period_start: datetime, period_end: datetime, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate risk assessment report data."""
        return {
            "summary": {
                "total_risks": 45,
                "by_level": {"critical": 2, "high": 8, "medium": 20, "low": 15},
                "by_status": {"identified": 5, "assessed": 12, "treated": 28},
                "average_risk_score": 6.2,
            },
            "risk_matrix": {
                "data": [[0, 1, 2, 1, 0], [0, 2, 5, 3, 1], [1, 3, 8, 4, 2], [0, 2, 4, 3, 1], [0, 0, 1, 1, 0]]
            },
        }

    async def _generate_tprm_report(
        self, period_start: datetime, period_end: datetime, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate TPRM report data."""
        return {
            "summary": {
                "total_vendors": 78,
                "by_risk": {"critical": 3, "high": 12, "medium": 35, "low": 28},
                "assessments_completed": 45,
                "assessments_pending": 12,
                "findings_open": 34,
            },
        }

    async def get_report(self, report_id: str) -> Optional[GeneratedReport]:
        """Get a report by ID."""
        result = await self.db.execute(
            select(GeneratedReport).where(
                or_(
                    GeneratedReport.id == report_id,
                    GeneratedReport.report_id == report_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        page: int = 1,
        size: int = 20,
        report_type: Optional[ReportType] = None,
        status: Optional[ReportStatus] = None,
    ) -> Dict[str, Any]:
        """List generated reports."""
        query = select(GeneratedReport)

        if report_type:
            query = query.where(GeneratedReport.report_type == report_type)
        if status:
            query = query.where(GeneratedReport.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        # Get paginated results
        query = query.order_by(GeneratedReport.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "size": size,
            "pages": (total_count + size - 1) // size if total_count else 0,
        }

    # ==================== Schedules ====================

    async def create_schedule(self, data: ReportScheduleCreate, created_by: str) -> ReportSchedule:
        """Create a report schedule."""
        schedule = ReportSchedule(
            name=data.name,
            description=data.description,
            template_id=data.template_id,
            frequency=data.frequency,
            schedule_config=data.schedule_config,
            report_config=data.report_config,
            recipients=data.recipients,
            distribution_config=data.distribution_config,
            is_enabled=data.is_enabled,
            created_by=created_by,
        )

        # Calculate next run
        schedule.next_run_at = self._calculate_next_run(data.frequency, data.schedule_config)

        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    def _calculate_next_run(
        self,
        frequency: ScheduleFrequency,
        config: Optional[Dict[str, Any]] = None
    ) -> datetime:
        """Calculate next run time based on frequency."""
        now = datetime.utcnow()
        config = config or {}
        hour = config.get("hour", 8)
        minute = config.get("minute", 0)

        if frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            day_of_week = config.get("day_of_week", 1)  # Monday
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        elif frequency == ScheduleFrequency.MONTHLY:
            day_of_month = config.get("day_of_month", 1)
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(days=7)

        return next_run

    async def list_schedules(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """List report schedules."""
        query = select(ReportSchedule).order_by(ReportSchedule.name)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "size": size,
            "pages": (total_count + size - 1) // size if total_count else 0,
        }

    # ==================== Dashboards ====================

    async def create_dashboard(self, data: DashboardCreate, created_by: str) -> Dashboard:
        """Create a dashboard."""
        dashboard = Dashboard(
            name=data.name,
            description=data.description,
            layout=data.layout or {"columns": 4, "rows": "auto"},
            is_public=data.is_public,
            is_default=data.is_default,
            shared_with=data.shared_with,
            owner=created_by,
            created_by=created_by,
        )
        self.db.add(dashboard)
        await self.db.flush()

        # Add widgets if provided
        if data.widgets:
            for widget_data in data.widgets:
                widget = DashboardWidget(
                    dashboard_id=dashboard.id,
                    title=widget_data.title,
                    widget_type=widget_data.widget_type,
                    data_source=widget_data.data_source,
                    query_config=widget_data.query_config,
                    display_config=widget_data.display_config,
                    refresh_interval_seconds=widget_data.refresh_interval_seconds,
                    position_x=widget_data.position_x,
                    position_y=widget_data.position_y,
                    width=widget_data.width,
                    height=widget_data.height,
                )
                self.db.add(widget)

        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        result = await self.db.execute(
            select(Dashboard).where(Dashboard.id == dashboard_id)
        )
        return result.scalar_one_or_none()

    async def list_dashboards(
        self,
        user_id: Optional[str] = None,
        include_public: bool = True,
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """List dashboards."""
        query = select(Dashboard)

        conditions = []
        if include_public:
            conditions.append(Dashboard.is_public == True)
        if user_id:
            conditions.append(Dashboard.owner == user_id)

        if conditions:
            query = query.where(or_(*conditions))

        query = query.order_by(Dashboard.is_default.desc(), Dashboard.name)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total_count = total.scalar()

        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "size": size,
            "pages": (total_count + size - 1) // size if total_count else 0,
        }

    async def add_widget(
        self, dashboard_id: str, data: DashboardWidgetCreate
    ) -> Optional[DashboardWidget]:
        """Add a widget to a dashboard."""
        dashboard = await self.get_dashboard(dashboard_id)
        if not dashboard:
            return None

        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            title=data.title,
            widget_type=data.widget_type,
            data_source=data.data_source,
            query_config=data.query_config,
            display_config=data.display_config,
            refresh_interval_seconds=data.refresh_interval_seconds,
            position_x=data.position_x,
            position_y=data.position_y,
            width=data.width,
            height=data.height,
        )
        self.db.add(widget)
        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    # ==================== Executive Dashboard ====================

    async def get_executive_dashboard(self) -> ExecutiveDashboardStats:
        """Get executive dashboard statistics."""
        # This would aggregate data from all modules
        # For now, returning sample data

        return ExecutiveDashboardStats(
            security_score=78,
            security_score_trend="up",
            incidents_total=52,
            incidents_open=7,
            incidents_critical=3,
            incidents_mttr_hours=4.2,
            alerts_today=145,
            alerts_critical=8,
            cases_open=12,
            cases_escalated=2,
            mttd_minutes=12,
            mttr_minutes=45,
            vulnerabilities_total=234,
            vulnerabilities_critical=8,
            vulnerabilities_high=45,
            vulnerabilities_overdue=12,
            patch_compliance_rate=85.5,
            risks_total=45,
            risks_critical=2,
            risks_high=8,
            risk_score_average=6.2,
            risks_requiring_treatment=7,
            vendors_total=78,
            vendors_high_risk=15,
            assessments_pending=12,
            findings_open=34,
            integrations_active=8,
            integrations_with_errors=1,
            syncs_today=45,
            compliance_score=92.0,
            controls_implemented=156,
            controls_total=170,
        )

    async def get_metric_trend(
        self,
        metric_name: str,
        period_days: int = 30,
        aggregation: str = "daily"
    ) -> List[TrendDataPoint]:
        """Get trend data for a metric."""
        # Query metric snapshots
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        result = await self.db.execute(
            select(MetricSnapshot)
            .where(
                and_(
                    MetricSnapshot.metric_name == metric_name,
                    MetricSnapshot.snapshot_date >= start_date,
                    MetricSnapshot.snapshot_date <= end_date,
                )
            )
            .order_by(MetricSnapshot.snapshot_date)
        )
        snapshots = list(result.scalars().all())

        return [
            TrendDataPoint(
                date=s.snapshot_date,
                value=s.value,
                label=s.metric_category,
            )
            for s in snapshots
        ]

    async def record_metric_snapshot(
        self,
        metric_name: str,
        value: float,
        category: Optional[str] = None,
        breakdown: Optional[Dict[str, Any]] = None,
    ):
        """Record a metric snapshot."""
        # Get previous value
        previous = await self.db.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.metric_name == metric_name)
            .order_by(MetricSnapshot.snapshot_date.desc())
            .limit(1)
        )
        previous_snapshot = previous.scalar_one_or_none()
        previous_value = previous_snapshot.value if previous_snapshot else None

        # Calculate change
        change_percentage = None
        if previous_value and previous_value != 0:
            change_percentage = ((value - previous_value) / previous_value) * 100

        snapshot = MetricSnapshot(
            metric_name=metric_name,
            metric_category=category,
            snapshot_date=datetime.utcnow(),
            period_type="daily",
            value=value,
            previous_value=previous_value,
            change_percentage=change_percentage,
            breakdown=breakdown,
        )
        self.db.add(snapshot)
        await self.db.commit()
