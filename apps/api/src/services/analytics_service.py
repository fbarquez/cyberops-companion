"""Analytics service for advanced metrics and visualizations."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.incident import Incident, IncidentStatus, IncidentSeverity
from src.models.soc import SOCAlert, AlertSeverity, AlertStatus, SOCCase, CaseStatus
from src.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from src.models.risk import Risk, RiskStatus
from src.schemas.analytics import (
    TrendDataPoint, TrendResponse, MultiTrendResponse,
    DistributionDataPoint, DistributionResponse,
    HeatmapCell, RiskHeatmapResponse, TimeHeatmapCell, TimeHeatmapResponse,
    TrendEntity, TrendMetric, DistributionGroupBy, HeatmapType,
    TimeAggregation
)


class AnalyticsService:
    """Service for analytics and visualizations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Trend Analysis ====================

    async def get_trend(
        self,
        entity: TrendEntity,
        metric: TrendMetric,
        period_days: int = 30,
        aggregation: TimeAggregation = TimeAggregation.DAILY,
    ) -> TrendResponse:
        """Get trend data for an entity/metric combination."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Get the model and date field based on entity
        model, date_field, count_field = self._get_entity_model(entity)
        if not model:
            return TrendResponse(
                entity=entity.value,
                metric=metric.value,
                period_days=period_days,
                aggregation=aggregation.value,
                data=[],
            )

        # Build date truncation based on aggregation
        if aggregation == TimeAggregation.HOURLY:
            date_trunc = func.date_trunc('hour', date_field)
        elif aggregation == TimeAggregation.WEEKLY:
            date_trunc = func.date_trunc('week', date_field)
        elif aggregation == TimeAggregation.MONTHLY:
            date_trunc = func.date_trunc('month', date_field)
        else:  # DAILY
            date_trunc = func.date_trunc('day', date_field)

        # Build query based on metric
        if metric == TrendMetric.COUNT or metric == TrendMetric.CREATED:
            query = (
                select(date_trunc.label('date'), func.count().label('value'))
                .where(date_field >= start_date)
                .where(date_field <= end_date)
                .group_by(date_trunc)
                .order_by(date_trunc)
            )
        elif metric == TrendMetric.RESOLVED:
            # Need a resolved_at or closed_at field
            resolved_field = self._get_resolved_field(model)
            if resolved_field:
                query = (
                    select(func.date_trunc('day', resolved_field).label('date'), func.count().label('value'))
                    .where(resolved_field >= start_date)
                    .where(resolved_field <= end_date)
                    .group_by(func.date_trunc('day', resolved_field))
                    .order_by(func.date_trunc('day', resolved_field))
                )
            else:
                query = None
        else:
            query = None

        if query is None:
            return TrendResponse(
                entity=entity.value,
                metric=metric.value,
                period_days=period_days,
                aggregation=aggregation.value,
                data=[],
            )

        result = await self.db.execute(query)
        rows = result.all()

        data = [
            TrendDataPoint(
                date=row.date.isoformat() if row.date else "",
                value=float(row.value)
            )
            for row in rows
        ]

        # Calculate totals
        total = sum(point.value for point in data)
        average = total / len(data) if data else 0

        # Calculate change percentage (compare first half to second half)
        mid = len(data) // 2
        if mid > 0:
            first_half = sum(p.value for p in data[:mid])
            second_half = sum(p.value for p in data[mid:])
            change_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        else:
            change_pct = 0

        return TrendResponse(
            entity=entity.value,
            metric=metric.value,
            period_days=period_days,
            aggregation=aggregation.value,
            data=data,
            total=total,
            average=average,
            change_percentage=round(change_pct, 1),
        )

    def _get_entity_model(self, entity: TrendEntity):
        """Get model and date field for an entity."""
        mapping = {
            TrendEntity.INCIDENTS: (Incident, Incident.created_at, Incident.id),
            TrendEntity.ALERTS: (SOCAlert, SOCAlert.created_at, SOCAlert.id),
            TrendEntity.VULNERABILITIES: (Vulnerability, Vulnerability.created_at, Vulnerability.id),
            TrendEntity.RISKS: (Risk, Risk.created_at, Risk.id),
            TrendEntity.CASES: (SOCCase, SOCCase.created_at, SOCCase.id),
        }
        return mapping.get(entity, (None, None, None))

    def _get_resolved_field(self, model):
        """Get the resolved/closed date field for a model."""
        if hasattr(model, 'resolved_at'):
            return model.resolved_at
        if hasattr(model, 'closed_at'):
            return model.closed_at
        return None

    # ==================== Distribution Analysis ====================

    async def get_distribution(
        self,
        entity: TrendEntity,
        group_by: DistributionGroupBy,
    ) -> DistributionResponse:
        """Get distribution data for an entity grouped by a field."""
        model, date_field, _ = self._get_entity_model(entity)
        if not model:
            return DistributionResponse(
                entity=entity.value,
                group_by=group_by.value,
                total=0,
                data=[],
            )

        # Get the grouping field
        group_field = self._get_group_field(model, group_by)
        if not group_field:
            return DistributionResponse(
                entity=entity.value,
                group_by=group_by.value,
                total=0,
                data=[],
            )

        query = (
            select(group_field.label('name'), func.count().label('value'))
            .group_by(group_field)
            .order_by(func.count().desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        total = sum(row.value for row in rows)
        data = [
            DistributionDataPoint(
                name=str(row.name) if row.name else "Unknown",
                value=row.value,
                percentage=round((row.value / total * 100), 1) if total > 0 else 0,
            )
            for row in rows
        ]

        return DistributionResponse(
            entity=entity.value,
            group_by=group_by.value,
            total=total,
            data=data,
        )

    def _get_group_field(self, model, group_by: DistributionGroupBy):
        """Get the field to group by."""
        if group_by == DistributionGroupBy.SEVERITY:
            if hasattr(model, 'severity'):
                return model.severity
        elif group_by == DistributionGroupBy.STATUS:
            if hasattr(model, 'status'):
                return model.status
        elif group_by == DistributionGroupBy.CATEGORY:
            if hasattr(model, 'category'):
                return model.category
            if hasattr(model, 'incident_type'):
                return model.incident_type
        elif group_by == DistributionGroupBy.ASSIGNEE:
            if hasattr(model, 'assigned_to'):
                return model.assigned_to
        elif group_by == DistributionGroupBy.SOURCE:
            if hasattr(model, 'source'):
                return model.source
        elif group_by == DistributionGroupBy.PRIORITY:
            if hasattr(model, 'priority'):
                return model.priority
        return None

    # ==================== Heatmap Analysis ====================

    async def get_heatmap(
        self,
        heatmap_type: HeatmapType,
    ) -> RiskHeatmapResponse | TimeHeatmapResponse:
        """Get heatmap data."""
        if heatmap_type == HeatmapType.RISK_MATRIX:
            return await self._get_risk_matrix_heatmap()
        elif heatmap_type == HeatmapType.ALERT_TIME:
            return await self._get_alert_time_heatmap()
        else:
            return RiskHeatmapResponse(total_risks=0, cells=[])

    async def _get_risk_matrix_heatmap(self) -> RiskHeatmapResponse:
        """Get risk matrix heatmap (impact vs likelihood)."""
        query = (
            select(
                Risk.impact,
                Risk.likelihood,
                func.count().label('count')
            )
            .where(Risk.status != RiskStatus.CLOSED)
            .group_by(Risk.impact, Risk.likelihood)
        )

        result = await self.db.execute(query)
        rows = result.all()

        total = sum(row.count for row in rows)
        cells = [
            HeatmapCell(
                x=row.likelihood if row.likelihood else 1,
                y=row.impact if row.impact else 1,
                value=row.count,
            )
            for row in rows
        ]

        return RiskHeatmapResponse(
            total_risks=total,
            cells=cells,
        )

    async def _get_alert_time_heatmap(self) -> TimeHeatmapResponse:
        """Get alert volume by hour and day of week."""
        # Last 30 days of alerts
        start_date = datetime.utcnow() - timedelta(days=30)

        query = (
            select(
                extract('hour', SOCAlert.created_at).label('hour'),
                extract('dow', SOCAlert.created_at).label('day'),
                func.count().label('count')
            )
            .where(SOCAlert.created_at >= start_date)
            .group_by(
                extract('hour', SOCAlert.created_at),
                extract('dow', SOCAlert.created_at)
            )
        )

        result = await self.db.execute(query)
        rows = result.all()

        total = sum(row.count for row in rows)
        cells = [
            TimeHeatmapCell(
                hour=int(row.hour),
                day=int(row.day),
                value=row.count,
            )
            for row in rows
        ]

        return TimeHeatmapResponse(
            total=total,
            cells=cells,
        )

    # ==================== Comparison Analysis ====================

    async def get_period_comparison(
        self,
        entity: TrendEntity,
        current_period_days: int = 30,
    ) -> Dict[str, Any]:
        """Compare current period with previous period."""
        now = datetime.utcnow()
        current_start = now - timedelta(days=current_period_days)
        previous_start = current_start - timedelta(days=current_period_days)

        model, date_field, _ = self._get_entity_model(entity)
        if not model:
            return {"error": "Unknown entity"}

        # Current period count
        current_query = (
            select(func.count())
            .where(date_field >= current_start)
            .where(date_field <= now)
        )
        current_result = await self.db.execute(current_query)
        current_count = current_result.scalar() or 0

        # Previous period count
        previous_query = (
            select(func.count())
            .where(date_field >= previous_start)
            .where(date_field < current_start)
        )
        previous_result = await self.db.execute(previous_query)
        previous_count = previous_result.scalar() or 0

        change = current_count - previous_count
        change_pct = (change / previous_count * 100) if previous_count > 0 else 0

        return {
            "entity": entity.value,
            "period_days": current_period_days,
            "current_period": {
                "start": current_start.isoformat(),
                "end": now.isoformat(),
                "count": current_count,
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": current_start.isoformat(),
                "count": previous_count,
            },
            "change": change,
            "change_percentage": round(change_pct, 1),
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
        }
