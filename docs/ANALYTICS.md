# Advanced Analytics System

**Version:** 0.8.0
**Last Updated:** 2026-01-31
**Status:** Phase 2A + 2B Complete

---

## Overview

The CyberOps Companion includes a comprehensive analytics system that provides visual insights, security scoring, SLA tracking, and analyst performance metrics. This document describes the architecture, components, and usage of the analytics features.

### What's Included (Phase 2A + 2B)

| Feature | Status |
|---------|--------|
| Trend Analysis | ✅ Complete |
| Distribution Charts | ✅ Complete |
| Risk Heatmap | ✅ Complete |
| Security Score | ✅ Complete |
| SLA Tracking | ✅ Complete |
| Analyst Metrics | ✅ Complete |
| Vulnerability Aging | ✅ Complete |

### What's Planned (Phase 2C - Future)

| Feature | Status | Notes |
|---------|--------|-------|
| Anomaly Detection | 🔲 Future | Requires historical data |
| Incident Prediction | 🔲 Future | ML model training needed |
| ML Risk Scoring | 🔲 Future | Enhanced risk predictions |
| Alert Prioritization | 🔲 Future | Learn from analyst behavior |

See [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) for Phase 2C specifications.

---

## Architecture

### Backend Services

```
apps/api/src/services/
├── analytics_service.py       # Trends, distributions, heatmaps
├── security_score_service.py  # Security posture scoring
├── sla_service.py             # SLA compliance tracking
└── analyst_metrics_service.py # SOC analyst performance
```

### Frontend Components

```
apps/web/components/dashboard/
├── charts/
│   ├── TrendLineChart.tsx     # Line/area charts for trends
│   ├── DistributionChart.tsx  # Bar charts for distributions
│   ├── PieChart.tsx           # Pie/donut charts
│   ├── RiskHeatMap.tsx        # 5x5 risk matrix heatmap
│   └── SparkLine.tsx          # Inline trend indicators
├── widgets/
│   ├── TrendCard.tsx          # Metric cards with trends
│   └── ChartCard.tsx          # Chart containers, score gauges
└── index.ts
```

## API Endpoints

### Trend Analysis

```
GET /api/v1/analytics/trends/{entity}/{metric}
```

**Parameters:**
- `entity`: incidents, alerts, vulnerabilities, risks, cases
- `metric`: count, created, resolved, mttr, mttd, severity
- `period_days`: Number of days (1-365, default: 30)
- `aggregation`: hourly, daily, weekly, monthly

**Response:**
```json
{
  "entity": "incidents",
  "metric": "count",
  "period_days": 30,
  "aggregation": "daily",
  "data": [
    {"date": "2024-01-01", "value": 5},
    {"date": "2024-01-02", "value": 8}
  ],
  "total": 150,
  "average": 5.0,
  "change_percentage": 12.5
}
```

### Distribution Analysis

```
GET /api/v1/analytics/distribution/{entity}/{group_by}
```

**Parameters:**
- `entity`: incidents, alerts, vulnerabilities, risks, cases
- `group_by`: severity, status, category, assignee, source, priority

**Response:**
```json
{
  "entity": "incidents",
  "group_by": "severity",
  "total": 100,
  "data": [
    {"name": "critical", "value": 5, "percentage": 5.0},
    {"name": "high", "value": 20, "percentage": 20.0}
  ]
}
```

### Heatmaps

```
GET /api/v1/analytics/heatmap/{type}
```

**Types:**
- `risk_matrix`: 5x5 impact vs likelihood matrix
- `alert_time`: Hour of day vs day of week alert volume

### Security Score

```
GET /api/v1/analytics/security-score
```

**Response:**
```json
{
  "overall_score": 78,
  "grade": "B",
  "trend": "up",
  "components": [
    {
      "name": "Vulnerabilities",
      "weight": 0.25,
      "score": 70,
      "weighted_score": 17.5,
      "status": "warning",
      "details": {"critical_open": 2, "high_open": 5}
    }
  ],
  "recommendations": [
    "Address 2 critical vulnerabilities immediately"
  ]
}
```

**Score Components:**
| Component | Weight | Description |
|-----------|--------|-------------|
| Vulnerabilities | 25% | Open critical/high vulnerabilities |
| Incidents | 20% | Active critical/high incidents |
| Compliance | 20% | Compliance framework status |
| Risks | 15% | Unmitigated high-risk items |
| SOC Operations | 10% | Unhandled alerts and escalations |
| Patch Compliance | 10% | Overdue patches |

### SLA Compliance

```
GET /api/v1/analytics/sla/compliance/{type}
```

**Types:**
- `response`: Alert response SLAs
- `remediation`: Vulnerability remediation SLAs

**Default SLA Targets:**

| Severity | Response Time | Remediation Time |
|----------|---------------|------------------|
| Critical | 15 minutes | 24 hours (1 day) |
| High | 1 hour | 168 hours (7 days) |
| Medium | 4 hours | 720 hours (30 days) |
| Low | 8 hours | 2160 hours (90 days) |

### SLA Breaches

```
GET /api/v1/analytics/sla/breaches
```

Returns list of items that have breached SLA targets.

### Analyst Metrics

```
GET /api/v1/analytics/analysts/metrics
```

**Response:**
```json
{
  "period_days": 30,
  "total_analysts": 5,
  "analysts": [
    {
      "analyst_id": "uuid",
      "analyst_name": "John Doe",
      "alerts_assigned": 50,
      "alerts_resolved": 45,
      "avg_response_time_minutes": 12.5,
      "false_positive_rate": 5.2,
      "workload_score": 65.0,
      "efficiency_score": 85.0
    }
  ],
  "team_averages": {
    "alerts_per_analyst": 42.5,
    "avg_response_time_minutes": 15.0
  }
}
```

### Vulnerability Aging

```
GET /api/v1/analytics/vulnerabilities/aging
```

**Response:**
```json
{
  "total_open": 150,
  "total_overdue": 25,
  "aging_buckets": [
    {"bucket": "0-7d", "count": 30, "by_severity": {"critical": 2}},
    {"bucket": "7-30d", "count": 50, "by_severity": {"critical": 5}},
    {"bucket": "30-90d", "count": 45, "by_severity": {"critical": 8}},
    {"bucket": "90+d", "count": 25, "by_severity": {"critical": 10}}
  ],
  "average_age_days": 42.5,
  "oldest_vulnerability_days": 180
}
```

### Risk Trends

```
GET /api/v1/analytics/risks/trends
```

Returns risk creation/mitigation trends over time.

## Frontend Hooks

### Usage

```typescript
import {
  useTrend,
  useDistribution,
  useHeatmap,
  useSecurityScore,
  useSLACompliance,
  useAnalystMetrics,
  useVulnerabilityAging,
  useRiskTrends,
} from "@/hooks/useAnalytics";

// Example usage
const { data: trend } = useTrend("incidents", "count", 30, "daily");
const { data: distribution } = useDistribution("alerts", "severity");
const { data: securityScore } = useSecurityScore();
```

## Chart Components

### TrendLineChart

```tsx
<TrendLineChart
  data={[{date: "2024-01-01", value: 10}]}
  height={300}
  showArea={true}
  color="#3b82f6"
/>
```

### DistributionChart

```tsx
<DistributionChart
  data={[{name: "Critical", value: 5}]}
  colorScheme="severity"
  orientation="vertical"
/>
```

### DonutChart

```tsx
<DonutChart
  data={[{name: "Open", value: 30}]}
  colorScheme="status"
  showLegend={true}
/>
```

### RiskHeatMap

```tsx
<RiskHeatMap
  data={[{impact: 5, likelihood: 4, count: 3}]}
  size="md"
  showLabels={true}
  onCellClick={(cell) => console.log(cell)}
/>
```

### ScoreGaugeCard

```tsx
<ScoreGaugeCard
  title="Security Score"
  score={78}
  label="B"
  trend="up"
/>
```

### SLAStatusCard

```tsx
<SLAStatusCard
  title="Response SLA"
  compliant={80}
  total={100}
  breached={10}
  atRisk={10}
/>
```

## Color Utilities

The `@/lib/chart-colors.ts` module provides consistent color palettes:

```typescript
import {
  severityColors,
  statusColors,
  trendColors,
  riskHeatmapColors,
  getScoreColor,
  getRiskColor,
} from "@/lib/chart-colors";
```

## Integration Points

### Reporting Dashboard
- Security score gauge
- SLA compliance card
- Incident/alert trend charts
- Severity distribution charts
- Vulnerability aging chart

### SOC Dashboard
- Alert volume trends
- Response SLA compliance
- Alert distribution by severity
- Analyst workload metrics

### Risks Dashboard
- 5x5 risk heat map
- Risk trends over time
- Risk distribution by status/category

## Best Practices

1. **Caching**: All analytics queries use React Query with 60-second stale time
2. **Auto-refresh**: Security score refreshes every 5 minutes
3. **Loading states**: Use `ChartCard` with `loading` prop for consistent UX
4. **Error handling**: Hooks return undefined when no token available
5. **Performance**: Trend queries support pagination via period_days parameter
