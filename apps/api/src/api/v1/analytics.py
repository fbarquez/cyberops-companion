"""Analytics API endpoints for advanced metrics and visualizations."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user, DBSession, CurrentUser
from src.models.user import User
from src.services.analytics_service import AnalyticsService
from src.services.security_score_service import SecurityScoreService
from src.services.sla_service import SLAService
from src.services.analyst_metrics_service import AnalystMetricsService
from src.schemas.analytics import (
    TrendEntity, TrendMetric, DistributionGroupBy, HeatmapType, TimeAggregation,
    TrendResponse, DistributionResponse,
    RiskHeatmapResponse, TimeHeatmapResponse,
    SecurityScoreResponse, SecurityScoreHistoryResponse,
    SLAComplianceResponse, SLABreachesResponse,
    AnalystMetricsResponse,
    VulnerabilityAgingResponse, AgingBucket,
    RiskTrendsResponse, RiskTrendPoint,
)

router = APIRouter(prefix="/analytics")


# ============== Trend Analysis ==============

@router.get("/trends/{entity}/{metric}", response_model=TrendResponse)
async def get_trend(
    entity: TrendEntity,
    metric: TrendMetric,
    period_days: int = Query(30, ge=1, le=365),
    aggregation: TimeAggregation = Query(TimeAggregation.DAILY),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get trend data for an entity/metric combination.

    - **entity**: incidents, alerts, vulnerabilities, risks, cases
    - **metric**: count, created, resolved, mttr, mttd, severity
    - **period_days**: Number of days to analyze (1-365)
    - **aggregation**: hourly, daily, weekly, monthly
    """
    service = AnalyticsService(db)
    return await service.get_trend(entity, metric, period_days, aggregation)


@router.get("/trends/{entity}/comparison")
async def get_period_comparison(
    entity: TrendEntity,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare current period with previous period."""
    service = AnalyticsService(db)
    return await service.get_period_comparison(entity, period_days)


# ============== Distribution Analysis ==============

@router.get("/distribution/{entity}/{group_by}", response_model=DistributionResponse)
async def get_distribution(
    entity: TrendEntity,
    group_by: DistributionGroupBy,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get distribution data for an entity grouped by a field.

    - **entity**: incidents, alerts, vulnerabilities, risks, cases
    - **group_by**: severity, status, category, assignee, source, priority
    """
    service = AnalyticsService(db)
    return await service.get_distribution(entity, group_by)


# ============== Heatmap Analysis ==============

@router.get("/heatmap/{heatmap_type}")
async def get_heatmap(
    heatmap_type: HeatmapType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get heatmap data.

    - **heatmap_type**: risk_matrix, alert_time, incident_category
    """
    service = AnalyticsService(db)
    return await service.get_heatmap(heatmap_type)


# ============== Security Score ==============

@router.get("/security-score", response_model=SecurityScoreResponse)
async def get_security_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current security score with component breakdown.

    The security score is calculated from:
    - Vulnerabilities (25%): Open critical/high vulnerabilities
    - Incidents (20%): Active critical/high incidents
    - Compliance (20%): Compliance framework status
    - Risks (15%): Unmitigated high-risk items
    - SOC Operations (10%): Unhandled alerts and escalations
    - Patch Compliance (10%): Overdue patches
    """
    service = SecurityScoreService(db)
    return await service.get_security_score()


@router.get("/security-score/history", response_model=SecurityScoreHistoryResponse)
async def get_security_score_history(
    period_days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security score history for trend analysis."""
    service = SecurityScoreService(db)
    return await service.get_score_history(period_days)


# ============== SLA Compliance ==============

@router.get("/sla/compliance/{sla_type}", response_model=SLAComplianceResponse)
async def get_sla_compliance(
    sla_type: str,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SLA compliance metrics.

    - **sla_type**: response (alert response SLAs) or remediation (vulnerability remediation SLAs)
    """
    service = SLAService(db)

    if sla_type == "response":
        return await service.get_response_sla_compliance(period_days)
    elif sla_type == "remediation":
        return await service.get_remediation_sla_compliance(period_days)
    else:
        raise HTTPException(status_code=400, detail="Invalid SLA type. Use 'response' or 'remediation'")


@router.get("/sla/breaches", response_model=SLABreachesResponse)
async def get_sla_breaches(
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of SLA breaches."""
    service = SLAService(db)
    return await service.get_sla_breaches(period_days)


# ============== Analyst Metrics ==============

@router.get("/analysts/metrics", response_model=AnalystMetricsResponse)
async def get_analyst_metrics(
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analyst performance metrics.

    Includes:
    - Alerts assigned/resolved per analyst
    - Cases assigned/closed per analyst
    - Average response and resolution times
    - False positive rates
    - Workload distribution
    """
    service = AnalystMetricsService(db)
    return await service.get_analyst_metrics(period_days)


@router.get("/analysts/leaderboard")
async def get_analyst_leaderboard(
    period_days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top performing analysts leaderboard."""
    service = AnalystMetricsService(db)
    return await service.get_analyst_leaderboard(period_days, limit)


# ============== Vulnerability Aging ==============

@router.get("/vulnerabilities/aging", response_model=VulnerabilityAgingResponse)
async def get_vulnerability_aging(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability aging analysis.

    Buckets: 0-7 days, 7-30 days, 30-90 days, 90+ days
    """
    from src.models.vulnerability import Vulnerability, VulnerabilityStatus, VulnerabilitySeverity
    from sqlalchemy import select, func, case
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    day_7 = now - timedelta(days=7)
    day_30 = now - timedelta(days=30)
    day_90 = now - timedelta(days=90)

    # Query open vulnerabilities with aging buckets
    open_statuses = [VulnerabilityStatus.OPEN, VulnerabilityStatus.IN_PROGRESS]

    query = (
        select(
            Vulnerability.severity,
            func.count().label('count'),
            case(
                (Vulnerability.created_at >= day_7, '0-7d'),
                (Vulnerability.created_at >= day_30, '7-30d'),
                (Vulnerability.created_at >= day_90, '30-90d'),
                else_='90+d'
            ).label('bucket')
        )
        .where(Vulnerability.status.in_(open_statuses))
        .group_by(Vulnerability.severity, 'bucket')
    )

    result = await db.execute(query)
    rows = result.all()

    # Process results into buckets
    buckets_data: dict = {
        '0-7d': {'count': 0, 'by_severity': {}},
        '7-30d': {'count': 0, 'by_severity': {}},
        '30-90d': {'count': 0, 'by_severity': {}},
        '90+d': {'count': 0, 'by_severity': {}},
    }

    for row in rows:
        bucket = row.bucket
        severity = str(row.severity).split('.')[-1].lower()
        count = row.count

        buckets_data[bucket]['count'] += count
        buckets_data[bucket]['by_severity'][severity] = \
            buckets_data[bucket]['by_severity'].get(severity, 0) + count

    aging_buckets = [
        AgingBucket(
            bucket=bucket,
            count=data['count'],
            by_severity=data['by_severity']
        )
        for bucket, data in buckets_data.items()
    ]

    # Count overdue
    overdue_query = (
        select(Vulnerability.severity, func.count().label('count'))
        .where(Vulnerability.status.in_(open_statuses))
        .where(Vulnerability.due_date < now)
        .group_by(Vulnerability.severity)
    )
    overdue_result = await db.execute(overdue_query)
    overdue_by_severity = {
        str(row.severity).split('.')[-1].lower(): row.count
        for row in overdue_result.all()
    }
    total_overdue = sum(overdue_by_severity.values())

    # Total open
    total_open = sum(b.count for b in aging_buckets)

    # Average age
    avg_query = (
        select(func.avg(func.extract('day', now - Vulnerability.created_at)))
        .where(Vulnerability.status.in_(open_statuses))
    )
    avg_result = await db.execute(avg_query)
    avg_age = avg_result.scalar() or 0

    # Oldest
    oldest_query = (
        select(func.min(Vulnerability.created_at))
        .where(Vulnerability.status.in_(open_statuses))
    )
    oldest_result = await db.execute(oldest_query)
    oldest_date = oldest_result.scalar()
    oldest_days = (now - oldest_date).days if oldest_date else 0

    return VulnerabilityAgingResponse(
        total_open=total_open,
        total_overdue=total_overdue,
        aging_buckets=aging_buckets,
        overdue_by_severity=overdue_by_severity,
        average_age_days=round(float(avg_age), 1),
        oldest_vulnerability_days=oldest_days,
    )


# ============== Risk Trends ==============

@router.get("/risks/trends", response_model=RiskTrendsResponse)
async def get_risk_trends(
    period_days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get risk trends over time."""
    from src.models.risk import Risk, RiskStatus
    from sqlalchemy import select, func
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    start_date = now - timedelta(days=period_days)

    # Get current totals
    current_query = (
        select(
            func.count().label('total'),
            func.sum(case((Risk.risk_score >= 20, 1), else_=0)).label('critical'),
            func.sum(case((Risk.risk_score >= 15, 1), else_=0)).label('high'),
            func.sum(case((Risk.risk_score >= 10, 1), else_=0)).label('medium'),
            func.sum(case((Risk.risk_score < 10, 1), else_=0)).label('low'),
        )
        .where(Risk.status != RiskStatus.CLOSED)
    )
    current_result = await db.execute(current_query)
    current = current_result.one()

    current_totals = {
        'total': current.total or 0,
        'critical': int(current.critical or 0),
        'high': int(current.high or 0),
        'medium': int(current.medium or 0),
        'low': int(current.low or 0),
    }

    # Get daily trend data
    trend_query = (
        select(
            func.date_trunc('day', Risk.created_at).label('date'),
            func.count().label('total'),
            func.avg(Risk.risk_score).label('avg_score')
        )
        .where(Risk.created_at >= start_date)
        .group_by(func.date_trunc('day', Risk.created_at))
        .order_by(func.date_trunc('day', Risk.created_at))
    )
    trend_result = await db.execute(trend_query)
    trend_rows = trend_result.all()

    trend_data = [
        RiskTrendPoint(
            date=row.date.strftime('%Y-%m-%d'),
            total=row.total,
            critical=0,  # Would need more complex query
            high=0,
            medium=0,
            low=0,
            average_score=round(float(row.avg_score or 0), 1)
        )
        for row in trend_rows
    ]

    # Calculate velocity (new risks per day)
    new_risks_query = (
        select(func.count())
        .where(Risk.created_at >= start_date)
    )
    new_risks_result = await db.execute(new_risks_query)
    new_risks = new_risks_result.scalar() or 0
    risk_velocity = new_risks / period_days if period_days > 0 else 0

    # Calculate mitigation rate
    mitigated_query = (
        select(func.count())
        .where(Risk.status.in_([RiskStatus.MITIGATED, RiskStatus.CLOSED]))
        .where(Risk.updated_at >= start_date)
    )
    mitigated_result = await db.execute(mitigated_query)
    mitigated = mitigated_result.scalar() or 0
    mitigation_rate = mitigated / period_days if period_days > 0 else 0

    return RiskTrendsResponse(
        period_days=period_days,
        current_totals=current_totals,
        trend_data=trend_data,
        risk_velocity=round(risk_velocity, 2),
        mitigation_rate=round(mitigation_rate, 2),
    )
