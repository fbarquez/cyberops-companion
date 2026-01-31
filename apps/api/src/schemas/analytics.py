"""Analytics schemas for advanced metrics and visualizations."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TimeAggregation(str, Enum):
    """Time aggregation options."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TrendEntity(str, Enum):
    """Entities that support trend analysis."""
    INCIDENTS = "incidents"
    ALERTS = "alerts"
    VULNERABILITIES = "vulnerabilities"
    RISKS = "risks"
    CASES = "cases"


class TrendMetric(str, Enum):
    """Metrics available for trend analysis."""
    COUNT = "count"
    CREATED = "created"
    RESOLVED = "resolved"
    MTTR = "mttr"
    MTTD = "mttd"
    SEVERITY = "severity"


class DistributionGroupBy(str, Enum):
    """Grouping options for distribution charts."""
    SEVERITY = "severity"
    STATUS = "status"
    CATEGORY = "category"
    ASSIGNEE = "assignee"
    SOURCE = "source"
    PRIORITY = "priority"


class HeatmapType(str, Enum):
    """Types of heatmaps available."""
    RISK_MATRIX = "risk_matrix"
    ALERT_TIME = "alert_time"  # Hour of day vs day of week
    INCIDENT_CATEGORY = "incident_category"


# ============== Trend Data Schemas ==============

class TrendDataPoint(BaseModel):
    """Single data point for trend charts."""
    date: str  # ISO date string
    value: float
    label: Optional[str] = None


class TrendResponse(BaseModel):
    """Response for trend analysis."""
    entity: str
    metric: str
    period_days: int
    aggregation: str
    data: List[TrendDataPoint]
    total: Optional[float] = None
    average: Optional[float] = None
    change_percentage: Optional[float] = None
    previous_period_total: Optional[float] = None


class MultiTrendResponse(BaseModel):
    """Response for multi-series trend analysis."""
    entity: str
    period_days: int
    series: Dict[str, List[TrendDataPoint]]


# ============== Distribution Schemas ==============

class DistributionDataPoint(BaseModel):
    """Single data point for distribution charts."""
    name: str
    value: int
    percentage: Optional[float] = None
    color: Optional[str] = None


class DistributionResponse(BaseModel):
    """Response for distribution analysis."""
    entity: str
    group_by: str
    total: int
    data: List[DistributionDataPoint]


# ============== Heatmap Schemas ==============

class HeatmapCell(BaseModel):
    """Single cell in a heatmap."""
    x: int  # X coordinate (e.g., likelihood 1-5)
    y: int  # Y coordinate (e.g., impact 1-5)
    value: int
    items: Optional[List[Dict[str, Any]]] = None


class RiskHeatmapResponse(BaseModel):
    """Response for risk matrix heatmap."""
    type: str = "risk_matrix"
    total_risks: int
    cells: List[HeatmapCell]
    x_labels: List[str] = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
    y_labels: List[str] = ["Very Low", "Low", "Medium", "High", "Very High"]


class TimeHeatmapCell(BaseModel):
    """Cell for time-based heatmap."""
    hour: int  # 0-23
    day: int  # 0-6 (Sun-Sat)
    value: int


class TimeHeatmapResponse(BaseModel):
    """Response for time-based heatmap."""
    type: str = "alert_time"
    total: int
    cells: List[TimeHeatmapCell]
    hour_labels: List[str] = [f"{i:02d}:00" for i in range(24)]
    day_labels: List[str] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


# ============== Security Score Schemas ==============

class SecurityScoreComponent(BaseModel):
    """Individual component of security score."""
    name: str
    weight: float  # 0.0 to 1.0
    score: float  # 0-100
    weighted_score: float
    status: str  # good, warning, critical
    details: Optional[Dict[str, Any]] = None


class SecurityScoreResponse(BaseModel):
    """Response for security score."""
    overall_score: int  # 0-100
    grade: str  # A, B, C, D, F
    trend: str  # up, down, stable
    components: List[SecurityScoreComponent]
    calculated_at: datetime
    recommendations: Optional[List[str]] = None


class SecurityScoreHistoryPoint(BaseModel):
    """Historical security score point."""
    date: str
    score: int
    components: Optional[Dict[str, float]] = None


class SecurityScoreHistoryResponse(BaseModel):
    """Response for security score history."""
    current_score: int
    period_days: int
    history: List[SecurityScoreHistoryPoint]
    average_score: float
    min_score: int
    max_score: int
    trend_percentage: float


# ============== SLA Schemas ==============

class SLATarget(BaseModel):
    """SLA target definition."""
    severity: str
    response_time_minutes: int
    resolution_time_hours: Optional[int] = None


class SLAMetric(BaseModel):
    """SLA metric for a specific severity."""
    severity: str
    target_minutes: int
    average_minutes: float
    compliant_count: int
    breached_count: int
    at_risk_count: int
    compliance_rate: float


class SLAComplianceResponse(BaseModel):
    """Response for SLA compliance."""
    type: str  # response, remediation
    period_days: int
    overall_compliance_rate: float
    metrics: List[SLAMetric]
    total_items: int
    compliant_items: int
    breached_items: int
    at_risk_items: int


class SLABreach(BaseModel):
    """Individual SLA breach."""
    id: str
    entity_type: str
    entity_id: str
    entity_name: str
    severity: str
    sla_type: str
    target_time: datetime
    breach_time: datetime
    delay_minutes: int
    assigned_to: Optional[str] = None


class SLABreachesResponse(BaseModel):
    """Response for SLA breaches."""
    period_days: int
    total_breaches: int
    breaches: List[SLABreach]
    by_severity: Dict[str, int]
    by_type: Dict[str, int]


# ============== Analyst Metrics Schemas ==============

class AnalystMetrics(BaseModel):
    """Metrics for a single analyst."""
    analyst_id: str
    analyst_name: str
    alerts_assigned: int
    alerts_resolved: int
    cases_assigned: int
    cases_closed: int
    avg_response_time_minutes: float
    avg_resolution_time_hours: float
    false_positive_rate: float
    workload_score: float  # 0-100 (100 = overloaded)
    efficiency_score: float  # 0-100


class AnalystMetricsResponse(BaseModel):
    """Response for analyst metrics."""
    period_days: int
    total_analysts: int
    analysts: List[AnalystMetrics]
    team_averages: Dict[str, float]
    workload_distribution: List[DistributionDataPoint]


# ============== Vulnerability Aging Schemas ==============

class AgingBucket(BaseModel):
    """Aging bucket for vulnerability aging."""
    bucket: str  # e.g., "0-7d", "7-30d", "30-90d", "90+d"
    count: int
    by_severity: Dict[str, int]


class VulnerabilityAgingResponse(BaseModel):
    """Response for vulnerability aging analysis."""
    total_open: int
    total_overdue: int
    aging_buckets: List[AgingBucket]
    overdue_by_severity: Dict[str, int]
    average_age_days: float
    oldest_vulnerability_days: int


# ============== Risk Trends Schemas ==============

class RiskTrendPoint(BaseModel):
    """Risk trend data point."""
    date: str
    total: int
    critical: int
    high: int
    medium: int
    low: int
    average_score: float


class RiskTrendsResponse(BaseModel):
    """Response for risk trends."""
    period_days: int
    current_totals: Dict[str, int]
    trend_data: List[RiskTrendPoint]
    risk_velocity: float  # New risks per day
    mitigation_rate: float  # Risks mitigated per day
