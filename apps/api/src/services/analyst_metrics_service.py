"""Analyst Metrics Service for SOC analyst performance tracking."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.soc import SOCAlert as Alert, AlertSeverity, AlertStatus, SOCCase as Case, CaseStatus
from src.models.user import User, UserRole
from src.schemas.analytics import (
    AnalystMetrics, AnalystMetricsResponse, DistributionDataPoint
)


class AnalystMetricsService:
    """Service for analyst performance metrics."""

    # Optimal workload thresholds
    OPTIMAL_ALERTS_PER_ANALYST = 20
    OPTIMAL_CASES_PER_ANALYST = 5

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_analyst_metrics(
        self,
        period_days: int = 30,
    ) -> AnalystMetricsResponse:
        """Get metrics for all analysts."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        # Get all analysts (users with analyst role)
        analyst_query = (
            select(User)
            .where(User.role.in_([UserRole.ANALYST, UserRole.LEAD, UserRole.MANAGER]))
            .where(User.is_active == True)
        )
        analyst_result = await self.db.execute(analyst_query)
        analysts = analyst_result.scalars().all()

        metrics_list = []
        total_alerts_assigned = 0
        total_alerts_resolved = 0
        total_cases_assigned = 0
        total_cases_closed = 0
        total_response_time = 0
        response_time_count = 0

        for analyst in analysts:
            analyst_metrics = await self._calculate_analyst_metrics(
                analyst.id, analyst.full_name or analyst.email, cutoff
            )
            metrics_list.append(analyst_metrics)

            total_alerts_assigned += analyst_metrics.alerts_assigned
            total_alerts_resolved += analyst_metrics.alerts_resolved
            total_cases_assigned += analyst_metrics.cases_assigned
            total_cases_closed += analyst_metrics.cases_closed

            if analyst_metrics.avg_response_time_minutes > 0:
                total_response_time += analyst_metrics.avg_response_time_minutes
                response_time_count += 1

        # Calculate team averages
        num_analysts = len(analysts) or 1
        team_averages = {
            "alerts_per_analyst": round(total_alerts_assigned / num_analysts, 1),
            "cases_per_analyst": round(total_cases_assigned / num_analysts, 1),
            "avg_response_time_minutes": round(total_response_time / response_time_count, 1) if response_time_count > 0 else 0,
            "alert_resolution_rate": round(total_alerts_resolved / total_alerts_assigned * 100, 1) if total_alerts_assigned > 0 else 0,
            "case_closure_rate": round(total_cases_closed / total_cases_assigned * 100, 1) if total_cases_assigned > 0 else 0,
        }

        # Calculate workload distribution
        workload_distribution = self._calculate_workload_distribution(metrics_list)

        return AnalystMetricsResponse(
            period_days=period_days,
            total_analysts=len(analysts),
            analysts=metrics_list,
            team_averages=team_averages,
            workload_distribution=workload_distribution,
        )

    async def _calculate_analyst_metrics(
        self,
        analyst_id: str,
        analyst_name: str,
        cutoff: datetime,
    ) -> AnalystMetrics:
        """Calculate metrics for a single analyst."""

        # Alerts assigned
        alerts_assigned_query = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.assigned_to == analyst_id)
            .where(Alert.created_at >= cutoff)
        )
        alerts_assigned_result = await self.db.execute(alerts_assigned_query)
        alerts_assigned = alerts_assigned_result.scalar() or 0

        # Alerts resolved
        alerts_resolved_query = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.assigned_to == analyst_id)
            .where(Alert.status.in_([AlertStatus.CLOSED, AlertStatus.RESOLVED]))
            .where(Alert.created_at >= cutoff)
        )
        alerts_resolved_result = await self.db.execute(alerts_resolved_query)
        alerts_resolved = alerts_resolved_result.scalar() or 0

        # Cases assigned
        cases_assigned_query = (
            select(func.count())
            .select_from(Case)
            .where(Case.assigned_to == analyst_id)
            .where(Case.created_at >= cutoff)
        )
        cases_assigned_result = await self.db.execute(cases_assigned_query)
        cases_assigned = cases_assigned_result.scalar() or 0

        # Cases closed
        cases_closed_query = (
            select(func.count())
            .select_from(Case)
            .where(Case.assigned_to == analyst_id)
            .where(Case.status == CaseStatus.CLOSED)
            .where(Case.created_at >= cutoff)
        )
        cases_closed_result = await self.db.execute(cases_closed_query)
        cases_closed = cases_closed_result.scalar() or 0

        # Average response time (from alert creation to acknowledgement)
        response_time_query = (
            select(Alert)
            .where(Alert.assigned_to == analyst_id)
            .where(Alert.acknowledged_at.isnot(None))
            .where(Alert.created_at >= cutoff)
        )
        response_time_result = await self.db.execute(response_time_query)
        alerts_with_response = response_time_result.scalars().all()

        response_times = []
        for alert in alerts_with_response:
            if alert.acknowledged_at:
                response_minutes = (alert.acknowledged_at - alert.created_at).total_seconds() / 60
                response_times.append(response_minutes)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Average resolution time (from case creation to close)
        resolution_time_query = (
            select(Case)
            .where(Case.assigned_to == analyst_id)
            .where(Case.status == CaseStatus.CLOSED)
            .where(Case.closed_at.isnot(None))
            .where(Case.created_at >= cutoff)
        )
        resolution_time_result = await self.db.execute(resolution_time_query)
        closed_cases = resolution_time_result.scalars().all()

        resolution_times = []
        for case in closed_cases:
            if case.closed_at:
                resolution_hours = (case.closed_at - case.created_at).total_seconds() / 3600
                resolution_times.append(resolution_hours)

        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # False positive rate (alerts marked as false positive / total handled)
        false_positive_query = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.assigned_to == analyst_id)
            .where(Alert.is_false_positive == True)
            .where(Alert.created_at >= cutoff)
        )
        false_positive_result = await self.db.execute(false_positive_query)
        false_positives = false_positive_result.scalar() or 0

        handled_alerts = alerts_resolved + false_positives
        false_positive_rate = (false_positives / handled_alerts * 100) if handled_alerts > 0 else 0

        # Calculate workload score (0-100, where 100 = overloaded)
        alert_load = alerts_assigned / self.OPTIMAL_ALERTS_PER_ANALYST
        case_load = cases_assigned / self.OPTIMAL_CASES_PER_ANALYST
        workload_score = min(100, (alert_load + case_load) / 2 * 100)

        # Calculate efficiency score (0-100)
        resolution_rate = alerts_resolved / alerts_assigned if alerts_assigned > 0 else 0
        case_closure_rate = cases_closed / cases_assigned if cases_assigned > 0 else 0

        # Factor in response time (target: 30 min avg)
        response_efficiency = max(0, 1 - (avg_response_time / 60)) if avg_response_time > 0 else 1

        efficiency_score = min(100, (
            resolution_rate * 40 +
            case_closure_rate * 40 +
            response_efficiency * 20
        ) * 100)

        return AnalystMetrics(
            analyst_id=analyst_id,
            analyst_name=analyst_name,
            alerts_assigned=alerts_assigned,
            alerts_resolved=alerts_resolved,
            cases_assigned=cases_assigned,
            cases_closed=cases_closed,
            avg_response_time_minutes=round(avg_response_time, 1),
            avg_resolution_time_hours=round(avg_resolution_time, 1),
            false_positive_rate=round(false_positive_rate, 1),
            workload_score=round(workload_score, 1),
            efficiency_score=round(efficiency_score, 1),
        )

    def _calculate_workload_distribution(
        self,
        metrics: List[AnalystMetrics],
    ) -> List[DistributionDataPoint]:
        """Calculate workload distribution across analysts."""
        categories = {
            "Underloaded": 0,  # < 50%
            "Optimal": 0,      # 50-80%
            "Heavy": 0,        # 80-100%
            "Overloaded": 0,   # > 100%
        }

        for m in metrics:
            score = m.workload_score
            if score < 50:
                categories["Underloaded"] += 1
            elif score < 80:
                categories["Optimal"] += 1
            elif score <= 100:
                categories["Heavy"] += 1
            else:
                categories["Overloaded"] += 1

        total = len(metrics) or 1
        return [
            DistributionDataPoint(
                name=name,
                value=count,
                percentage=round(count / total * 100, 1),
            )
            for name, count in categories.items()
        ]

    async def get_analyst_leaderboard(
        self,
        period_days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top performing analysts."""
        metrics = await self.get_analyst_metrics(period_days)

        # Sort by efficiency score
        sorted_analysts = sorted(
            metrics.analysts,
            key=lambda a: a.efficiency_score,
            reverse=True
        )[:limit]

        return [
            {
                "rank": i + 1,
                "analyst_id": a.analyst_id,
                "analyst_name": a.analyst_name,
                "efficiency_score": a.efficiency_score,
                "alerts_resolved": a.alerts_resolved,
                "cases_closed": a.cases_closed,
                "avg_response_time_minutes": a.avg_response_time_minutes,
            }
            for i, a in enumerate(sorted_analysts)
        ]
