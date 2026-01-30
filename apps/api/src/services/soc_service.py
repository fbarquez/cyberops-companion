"""
SOC Service.

Business logic for Security Operations Center functionality.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.soc import (
    SOCAlert, AlertComment, SOCCase, CaseTask, CaseTimeline,
    SOCPlaybook, PlaybookExecution, SOCMetrics, ShiftHandover,
    AlertSeverity, AlertStatus, AlertSource,
    CaseStatus, CasePriority, PlaybookStatus, ExecutionStatus
)
from src.schemas.soc import (
    AlertCreate, AlertUpdate, AlertAssign, AlertResolve, AlertCommentCreate,
    CaseCreate, CaseUpdate, CaseEscalate, CaseResolve,
    CaseTaskCreate, CaseTaskUpdate, CaseTimelineCreate,
    PlaybookCreate, PlaybookUpdate, PlaybookExecutionCreate,
    ShiftHandoverCreate, SOCDashboardStats
)


class SOCService:
    """Service for SOC operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Alert Operations ====================

    async def generate_alert_id(self) -> str:
        """Generate a unique alert ID."""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"ALT-{today}-"

        result = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(SOCAlert.alert_id.like(f"{prefix}%"))
        )
        count = result.scalar() or 0

        return f"{prefix}{str(count + 1).zfill(4)}"

    async def create_alert(self, data: AlertCreate, created_by: Optional[str] = None) -> SOCAlert:
        """Create a new security alert."""
        alert_id = await self.generate_alert_id()

        alert = SOCAlert(
            alert_id=alert_id,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=AlertStatus.NEW,
            source=data.source,
            source_ref=data.source_ref,
            detection_rule=data.detection_rule,
            mitre_tactics=data.mitre_tactics,
            mitre_techniques=data.mitre_techniques,
            affected_assets=data.affected_assets,
            affected_users=data.affected_users,
            source_ip=data.source_ip,
            destination_ip=data.destination_ip,
            risk_score=data.risk_score,
            confidence=data.confidence,
            detected_at=data.detected_at or datetime.utcnow(),
            first_seen=data.detected_at or datetime.utcnow(),
            last_seen=data.detected_at or datetime.utcnow(),
            tags=data.tags,
            raw_event=data.raw_event,
            custom_fields=data.custom_fields
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def create_alerts_bulk(self, alerts: List[AlertCreate], created_by: Optional[str] = None) -> List[SOCAlert]:
        """Create multiple alerts."""
        created = []
        for alert_data in alerts:
            alert = await self.create_alert(alert_data, created_by)
            created.append(alert)
        return created

    async def get_alert(self, alert_id: str) -> Optional[SOCAlert]:
        """Get alert by ID."""
        result = await self.db.execute(
            select(SOCAlert)
            .options(selectinload(SOCAlert.comments))
            .where(or_(SOCAlert.id == alert_id, SOCAlert.alert_id == alert_id))
        )
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List alerts with filtering and pagination."""
        query = select(SOCAlert).order_by(SOCAlert.detected_at.desc())

        if filters:
            if filters.get("severity"):
                query = query.where(SOCAlert.severity == filters["severity"])
            if filters.get("status"):
                query = query.where(SOCAlert.status == filters["status"])
            if filters.get("source"):
                query = query.where(SOCAlert.source == filters["source"])
            if filters.get("assigned_to"):
                query = query.where(SOCAlert.assigned_to == filters["assigned_to"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        SOCAlert.title.ilike(search),
                        SOCAlert.alert_id.ilike(search),
                        SOCAlert.description.ilike(search)
                    )
                )
            if filters.get("unassigned"):
                query = query.where(SOCAlert.assigned_to.is_(None))
            if filters.get("date_from"):
                query = query.where(SOCAlert.detected_at >= filters["date_from"])
            if filters.get("date_to"):
                query = query.where(SOCAlert.detected_at <= filters["date_to"])

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    async def update_alert(self, alert_id: str, data: AlertUpdate) -> Optional[SOCAlert]:
        """Update an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(alert, key, value)

        alert.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def assign_alert(self, alert_id: str, data: AlertAssign, assigned_by: Optional[str] = None) -> Optional[SOCAlert]:
        """Assign an alert to an analyst."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.assigned_to = data.assigned_to
        alert.assigned_at = datetime.utcnow()
        alert.status = AlertStatus.ASSIGNED

        if data.notes:
            await self.add_alert_comment(
                alert_id,
                AlertCommentCreate(content=f"Assigned to {data.assigned_to}. {data.notes}"),
                author=assigned_by or "system"
            )

        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def acknowledge_alert(self, alert_id: str, analyst: str) -> Optional[SOCAlert]:
        """Acknowledge an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.acknowledged_at = datetime.utcnow()
        if alert.status == AlertStatus.NEW:
            alert.status = AlertStatus.IN_PROGRESS

        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def resolve_alert(self, alert_id: str, data: AlertResolve, resolved_by: Optional[str] = None) -> Optional[SOCAlert]:
        """Resolve an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = data.resolution_notes

        if data.is_false_positive:
            alert.status = AlertStatus.FALSE_POSITIVE
            alert.false_positive_reason = data.false_positive_reason
        else:
            alert.status = AlertStatus.RESOLVED

        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def add_alert_comment(self, alert_id: str, data: AlertCommentCreate, author: str) -> AlertComment:
        """Add a comment to an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            raise ValueError("Alert not found")

        comment = AlertComment(
            alert_id=alert.id,
            author=author,
            content=data.content,
            is_internal=data.is_internal
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    # ==================== Case Operations ====================

    async def generate_case_number(self) -> str:
        """Generate a unique case number."""
        year = datetime.utcnow().year
        prefix = f"CASE-{year}-"

        result = await self.db.execute(
            select(func.count(SOCCase.id))
            .where(SOCCase.case_number.like(f"{prefix}%"))
        )
        count = result.scalar() or 0

        return f"{prefix}{str(count + 1).zfill(4)}"

    async def create_case(self, data: CaseCreate, created_by: Optional[str] = None) -> SOCCase:
        """Create a new investigation case."""
        case_number = await self.generate_case_number()

        case = SOCCase(
            case_number=case_number,
            title=data.title,
            description=data.description,
            priority=data.priority,
            case_type=data.case_type,
            assigned_to=data.assigned_to,
            assigned_team=data.assigned_team,
            due_date=data.due_date,
            tags=data.tags,
            custom_fields=data.custom_fields,
            created_by=created_by
        )

        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)

        # Link alerts if provided
        if data.alert_ids:
            for alert_id in data.alert_ids:
                alert = await self.get_alert(alert_id)
                if alert:
                    case.alerts.append(alert)
            await self.db.commit()

        return case

    async def get_case(self, case_id: str) -> Optional[SOCCase]:
        """Get case by ID."""
        result = await self.db.execute(
            select(SOCCase)
            .options(
                selectinload(SOCCase.alerts),
                selectinload(SOCCase.tasks),
                selectinload(SOCCase.timeline_entries)
            )
            .where(or_(SOCCase.id == case_id, SOCCase.case_number == case_id))
        )
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List cases with filtering and pagination."""
        query = select(SOCCase).order_by(SOCCase.opened_at.desc())

        if filters:
            if filters.get("status"):
                query = query.where(SOCCase.status == filters["status"])
            if filters.get("priority"):
                query = query.where(SOCCase.priority == filters["priority"])
            if filters.get("assigned_to"):
                query = query.where(SOCCase.assigned_to == filters["assigned_to"])
            if filters.get("assigned_team"):
                query = query.where(SOCCase.assigned_team == filters["assigned_team"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        SOCCase.title.ilike(search),
                        SOCCase.case_number.ilike(search),
                        SOCCase.description.ilike(search)
                    )
                )
            if filters.get("overdue"):
                query = query.where(
                    and_(
                        SOCCase.due_date < datetime.utcnow(),
                        SOCCase.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS])
                    )
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        # Add counts
        for item in items:
            item.alert_count = len(item.alerts) if item.alerts else 0
            item.task_count = len(item.tasks) if item.tasks else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    async def update_case(self, case_id: str, data: CaseUpdate) -> Optional[SOCCase]:
        """Update a case."""
        case = await self.get_case(case_id)
        if not case:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(case, key, value)

        case.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def escalate_case(self, case_id: str, data: CaseEscalate, escalated_by: Optional[str] = None) -> Optional[SOCCase]:
        """Escalate a case."""
        case = await self.get_case(case_id)
        if not case:
            return None

        case.status = CaseStatus.ESCALATED
        case.escalated_to = data.escalated_to
        case.escalation_reason = data.reason
        case.escalated_at = datetime.utcnow()

        # Add timeline entry
        await self.add_case_timeline(
            case_id,
            CaseTimelineCreate(
                event_time=datetime.utcnow(),
                event_type="escalation",
                description=f"Escalated to {data.escalated_to}: {data.reason}"
            ),
            author=escalated_by
        )

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def resolve_case(self, case_id: str, data: CaseResolve, resolved_by: Optional[str] = None) -> Optional[SOCCase]:
        """Resolve a case."""
        case = await self.get_case(case_id)
        if not case:
            return None

        case.status = CaseStatus.RESOLVED
        case.resolved_at = datetime.utcnow()
        case.resolution_summary = data.resolution_summary
        case.root_cause = data.root_cause
        case.lessons_learned = data.lessons_learned

        # Calculate time to resolve
        if case.opened_at:
            case.time_to_resolve = int((case.resolved_at - case.opened_at).total_seconds())

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def link_alert_to_case(self, case_id: str, alert_id: str) -> Optional[SOCCase]:
        """Link an alert to a case."""
        case = await self.get_case(case_id)
        alert = await self.get_alert(alert_id)

        if not case or not alert:
            return None

        if alert not in case.alerts:
            case.alerts.append(alert)
            await self.db.commit()

        return case

    async def create_case_task(self, case_id: str, data: CaseTaskCreate, created_by: Optional[str] = None) -> CaseTask:
        """Create a task within a case."""
        task = CaseTask(
            case_id=case_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            assigned_to=data.assigned_to,
            due_date=data.due_date,
            created_by=created_by
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_case_task(self, task_id: str, data: CaseTaskUpdate) -> Optional[CaseTask]:
        """Update a case task."""
        result = await self.db.execute(
            select(CaseTask).where(CaseTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        if data.status == "completed":
            task.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def add_case_timeline(self, case_id: str, data: CaseTimelineCreate, author: Optional[str] = None) -> CaseTimeline:
        """Add a timeline entry to a case."""
        entry = CaseTimeline(
            case_id=case_id,
            event_time=data.event_time,
            event_type=data.event_type,
            description=data.description,
            author=author,
            evidence_ids=data.evidence_ids
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    # ==================== Playbook Operations ====================

    async def create_playbook(self, data: PlaybookCreate, created_by: Optional[str] = None) -> SOCPlaybook:
        """Create a new playbook."""
        # Convert actions to dict format
        actions = [action.model_dump() for action in data.actions]

        playbook = SOCPlaybook(
            name=data.name,
            description=data.description,
            trigger_type=data.trigger_type,
            trigger_conditions=data.trigger_conditions,
            actions=actions,
            is_enabled=data.is_enabled,
            run_automatically=data.run_automatically,
            require_approval=data.require_approval,
            timeout_seconds=data.timeout_seconds,
            category=data.category,
            tags=data.tags,
            created_by=created_by
        )

        self.db.add(playbook)
        await self.db.commit()
        await self.db.refresh(playbook)
        return playbook

    async def get_playbook(self, playbook_id: str) -> Optional[SOCPlaybook]:
        """Get playbook by ID."""
        result = await self.db.execute(
            select(SOCPlaybook).where(SOCPlaybook.id == playbook_id)
        )
        return result.scalar_one_or_none()

    async def list_playbooks(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List playbooks with filtering."""
        query = select(SOCPlaybook).order_by(SOCPlaybook.name)

        if filters:
            if filters.get("status"):
                query = query.where(SOCPlaybook.status == filters["status"])
            if filters.get("trigger_type"):
                query = query.where(SOCPlaybook.trigger_type == filters["trigger_type"])
            if filters.get("is_enabled") is not None:
                query = query.where(SOCPlaybook.is_enabled == filters["is_enabled"])
            if filters.get("category"):
                query = query.where(SOCPlaybook.category == filters["category"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        SOCPlaybook.name.ilike(search),
                        SOCPlaybook.description.ilike(search)
                    )
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    async def update_playbook(self, playbook_id: str, data: PlaybookUpdate) -> Optional[SOCPlaybook]:
        """Update a playbook."""
        playbook = await self.get_playbook(playbook_id)
        if not playbook:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle actions separately
        if "actions" in update_data and update_data["actions"]:
            update_data["actions"] = [action.model_dump() if hasattr(action, 'model_dump') else action for action in update_data["actions"]]

        for key, value in update_data.items():
            setattr(playbook, key, value)

        playbook.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(playbook)
        return playbook

    async def execute_playbook(
        self,
        playbook_id: str,
        data: PlaybookExecutionCreate,
        executed_by: Optional[str] = None
    ) -> PlaybookExecution:
        """Execute a playbook."""
        playbook = await self.get_playbook(playbook_id)
        if not playbook:
            raise ValueError("Playbook not found")

        execution = PlaybookExecution(
            playbook_id=playbook_id,
            alert_id=data.alert_id,
            case_id=data.case_id,
            trigger_reason=data.trigger_reason,
            status=ExecutionStatus.PENDING if playbook.require_approval else ExecutionStatus.RUNNING,
            executed_by=executed_by
        )

        if not playbook.require_approval:
            execution.started_at = datetime.utcnow()

        self.db.add(execution)
        playbook.total_runs += 1
        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def approve_execution(self, execution_id: str, approved_by: str) -> Optional[PlaybookExecution]:
        """Approve a pending playbook execution."""
        result = await self.db.execute(
            select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution or execution.status != ExecutionStatus.PENDING:
            return None

        execution.approved_by = approved_by
        execution.approved_at = datetime.utcnow()
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def complete_execution(
        self,
        execution_id: str,
        success: bool,
        action_results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[PlaybookExecution]:
        """Mark a playbook execution as complete."""
        result = await self.db.execute(
            select(PlaybookExecution)
            .options(selectinload(PlaybookExecution.playbook))
            .where(PlaybookExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            return None

        execution.completed_at = datetime.utcnow()
        execution.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
        execution.action_results = action_results
        execution.error_message = error_message

        # Update playbook stats
        if execution.playbook:
            if success:
                execution.playbook.successful_runs += 1
            else:
                execution.playbook.failed_runs += 1

            # Update avg execution time
            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                if execution.playbook.avg_execution_time:
                    execution.playbook.avg_execution_time = (
                        (execution.playbook.avg_execution_time + duration) / 2
                    )
                else:
                    execution.playbook.avg_execution_time = duration

        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    # ==================== Dashboard & Metrics ====================

    async def get_dashboard_stats(self) -> SOCDashboardStats:
        """Get SOC dashboard statistics."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Total alerts today
        alerts_today = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(SOCAlert.detected_at >= today)
        )
        total_alerts_today = alerts_today.scalar() or 0

        # Alerts by status
        new_alerts = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(SOCAlert.status == AlertStatus.NEW)
        )

        in_progress_alerts = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(SOCAlert.status == AlertStatus.IN_PROGRESS)
        )

        # Critical/high alerts
        critical_alerts = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(
                and_(
                    SOCAlert.severity == AlertSeverity.CRITICAL,
                    SOCAlert.status.in_([AlertStatus.NEW, AlertStatus.IN_PROGRESS, AlertStatus.ASSIGNED])
                )
            )
        )

        high_alerts = await self.db.execute(
            select(func.count(SOCAlert.id))
            .where(
                and_(
                    SOCAlert.severity == AlertSeverity.HIGH,
                    SOCAlert.status.in_([AlertStatus.NEW, AlertStatus.IN_PROGRESS, AlertStatus.ASSIGNED])
                )
            )
        )

        # Open cases
        open_cases = await self.db.execute(
            select(func.count(SOCCase.id))
            .where(SOCCase.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS]))
        )

        # Escalated cases
        escalated_cases = await self.db.execute(
            select(func.count(SOCCase.id))
            .where(SOCCase.status == CaseStatus.ESCALATED)
        )

        # Overdue cases
        overdue_cases = await self.db.execute(
            select(func.count(SOCCase.id))
            .where(
                and_(
                    SOCCase.due_date < datetime.utcnow(),
                    SOCCase.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS])
                )
            )
        )

        # Alerts by severity
        severity_counts = await self.db.execute(
            select(SOCAlert.severity, func.count(SOCAlert.id))
            .where(SOCAlert.status.in_([AlertStatus.NEW, AlertStatus.IN_PROGRESS, AlertStatus.ASSIGNED]))
            .group_by(SOCAlert.severity)
        )
        alerts_by_severity = {str(row[0].value): row[1] for row in severity_counts.fetchall()}

        # Alerts by source
        source_counts = await self.db.execute(
            select(SOCAlert.source, func.count(SOCAlert.id))
            .where(SOCAlert.detected_at >= today)
            .group_by(SOCAlert.source)
        )
        alerts_by_source = {str(row[0].value): row[1] for row in source_counts.fetchall()}

        # Alerts by status
        status_counts = await self.db.execute(
            select(SOCAlert.status, func.count(SOCAlert.id))
            .group_by(SOCAlert.status)
        )
        alerts_by_status = {str(row[0].value): row[1] for row in status_counts.fetchall()}

        # Cases by priority
        priority_counts = await self.db.execute(
            select(SOCCase.priority, func.count(SOCCase.id))
            .where(SOCCase.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS]))
            .group_by(SOCCase.priority)
        )
        cases_by_priority = {str(row[0].value): row[1] for row in priority_counts.fetchall()}

        # Cases by status
        case_status_counts = await self.db.execute(
            select(SOCCase.status, func.count(SOCCase.id))
            .group_by(SOCCase.status)
        )
        cases_by_status = {str(row[0].value): row[1] for row in case_status_counts.fetchall()}

        # Playbook runs today
        playbook_runs = await self.db.execute(
            select(func.count(PlaybookExecution.id))
            .where(PlaybookExecution.created_at >= today)
        )
        playbook_runs_today = playbook_runs.scalar() or 0

        # Alerts per analyst
        analyst_counts = await self.db.execute(
            select(SOCAlert.assigned_to, func.count(SOCAlert.id))
            .where(
                and_(
                    SOCAlert.assigned_to.isnot(None),
                    SOCAlert.status.in_([AlertStatus.ASSIGNED, AlertStatus.IN_PROGRESS])
                )
            )
            .group_by(SOCAlert.assigned_to)
        )
        alerts_per_analyst = {row[0]: row[1] for row in analyst_counts.fetchall() if row[0]}

        return SOCDashboardStats(
            total_alerts_today=total_alerts_today,
            new_alerts=new_alerts.scalar() or 0,
            in_progress_alerts=in_progress_alerts.scalar() or 0,
            critical_alerts=critical_alerts.scalar() or 0,
            high_alerts=high_alerts.scalar() or 0,
            open_cases=open_cases.scalar() or 0,
            escalated_cases=escalated_cases.scalar() or 0,
            overdue_cases=overdue_cases.scalar() or 0,
            alerts_by_severity=alerts_by_severity,
            alerts_by_source=alerts_by_source,
            alerts_by_status=alerts_by_status,
            cases_by_priority=cases_by_priority,
            cases_by_status=cases_by_status,
            playbook_runs_today=playbook_runs_today,
            alerts_per_analyst=alerts_per_analyst
        )

    # ==================== Shift Handover ====================

    async def create_shift_handover(self, data: ShiftHandoverCreate, analyst: str) -> ShiftHandover:
        """Create a shift handover."""
        handover = ShiftHandover(
            shift_date=datetime.utcnow(),
            shift_type=data.shift_type,
            outgoing_analyst=analyst,
            summary=data.summary,
            open_alerts=data.open_alerts,
            open_cases=data.open_cases,
            pending_actions=data.pending_actions,
            important_notes=data.important_notes,
            escalations=data.escalations
        )

        self.db.add(handover)
        await self.db.commit()
        await self.db.refresh(handover)
        return handover

    async def acknowledge_handover(self, handover_id: str, analyst: str) -> Optional[ShiftHandover]:
        """Acknowledge a shift handover."""
        result = await self.db.execute(
            select(ShiftHandover).where(ShiftHandover.id == handover_id)
        )
        handover = result.scalar_one_or_none()

        if not handover:
            return None

        handover.incoming_analyst = analyst
        handover.acknowledged_at = datetime.utcnow()
        handover.acknowledged_by = analyst

        await self.db.commit()
        await self.db.refresh(handover)
        return handover

    async def get_latest_handover(self) -> Optional[ShiftHandover]:
        """Get the latest shift handover."""
        result = await self.db.execute(
            select(ShiftHandover)
            .order_by(ShiftHandover.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
