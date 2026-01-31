"""SLA Service for tracking response and remediation SLAs."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.soc import Alert, AlertSeverity, AlertStatus, Case, CaseStatus
from src.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.schemas.analytics import (
    SLATarget, SLAMetric, SLAComplianceResponse,
    SLABreach, SLABreachesResponse,
)


class SLAService:
    """Service for SLA tracking and compliance."""

    # Default SLA targets (in minutes for response, hours for remediation)
    RESPONSE_SLA = {
        "critical": 15,    # 15 minutes
        "high": 60,        # 1 hour
        "medium": 240,     # 4 hours
        "low": 480,        # 8 hours
    }

    REMEDIATION_SLA = {
        "critical": 24,    # 24 hours (1 day)
        "high": 168,       # 168 hours (7 days)
        "medium": 720,     # 720 hours (30 days)
        "low": 2160,       # 2160 hours (90 days)
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_response_sla_compliance(
        self,
        period_days: int = 30,
    ) -> SLAComplianceResponse:
        """Get response SLA compliance for alerts."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        metrics = []
        total_compliant = 0
        total_breached = 0
        total_at_risk = 0
        total_items = 0

        for severity, target_minutes in self.RESPONSE_SLA.items():
            # Get alerts for this severity
            severity_enum = self._get_alert_severity(severity)
            if not severity_enum:
                continue

            # Query alerts with their response times
            query = (
                select(Alert)
                .where(Alert.created_at >= cutoff)
                .where(Alert.severity == severity_enum)
            )
            result = await self.db.execute(query)
            alerts = result.scalars().all()

            compliant = 0
            breached = 0
            at_risk = 0
            response_times = []

            for alert in alerts:
                if alert.acknowledged_at:
                    # Calculate response time
                    response_minutes = (alert.acknowledged_at - alert.created_at).total_seconds() / 60
                    response_times.append(response_minutes)

                    if response_minutes <= target_minutes:
                        compliant += 1
                    else:
                        breached += 1
                elif alert.status == AlertStatus.NEW:
                    # Check if at risk of breach
                    elapsed = (datetime.utcnow() - alert.created_at).total_seconds() / 60
                    if elapsed >= target_minutes:
                        breached += 1
                    elif elapsed >= target_minutes * 0.75:
                        at_risk += 1
                    else:
                        compliant += 1

            avg_response = sum(response_times) / len(response_times) if response_times else 0
            total = compliant + breached + at_risk
            compliance_rate = (compliant / total * 100) if total > 0 else 100

            metrics.append(SLAMetric(
                severity=severity,
                target_minutes=target_minutes,
                average_minutes=round(avg_response, 1),
                compliant_count=compliant,
                breached_count=breached,
                at_risk_count=at_risk,
                compliance_rate=round(compliance_rate, 1),
            ))

            total_compliant += compliant
            total_breached += breached
            total_at_risk += at_risk
            total_items += total

        overall_rate = (total_compliant / total_items * 100) if total_items > 0 else 100

        return SLAComplianceResponse(
            type="response",
            period_days=period_days,
            overall_compliance_rate=round(overall_rate, 1),
            metrics=metrics,
            total_items=total_items,
            compliant_items=total_compliant,
            breached_items=total_breached,
            at_risk_items=total_at_risk,
        )

    async def get_remediation_sla_compliance(
        self,
        period_days: int = 30,
    ) -> SLAComplianceResponse:
        """Get remediation SLA compliance for vulnerabilities."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        metrics = []
        total_compliant = 0
        total_breached = 0
        total_at_risk = 0
        total_items = 0

        for severity, target_hours in self.REMEDIATION_SLA.items():
            severity_enum = self._get_vuln_severity(severity)
            if not severity_enum:
                continue

            target_minutes = target_hours * 60

            # Query vulnerabilities for this severity
            query = (
                select(Vulnerability)
                .where(Vulnerability.created_at >= cutoff)
                .where(Vulnerability.severity == severity_enum)
            )
            result = await self.db.execute(query)
            vulns = result.scalars().all()

            compliant = 0
            breached = 0
            at_risk = 0
            remediation_times = []

            for vuln in vulns:
                if vuln.status in [VulnerabilityStatus.REMEDIATED, VulnerabilityStatus.ACCEPTED]:
                    # Use updated_at as proxy for remediation time
                    if vuln.remediated_at:
                        remediation_minutes = (vuln.remediated_at - vuln.created_at).total_seconds() / 60
                    else:
                        remediation_minutes = (vuln.updated_at - vuln.created_at).total_seconds() / 60
                    remediation_times.append(remediation_minutes)

                    if remediation_minutes <= target_minutes:
                        compliant += 1
                    else:
                        breached += 1
                elif vuln.status in [VulnerabilityStatus.OPEN, VulnerabilityStatus.IN_PROGRESS]:
                    # Check if at risk or breached
                    elapsed = (datetime.utcnow() - vuln.created_at).total_seconds() / 60
                    if elapsed >= target_minutes:
                        breached += 1
                    elif elapsed >= target_minutes * 0.75:
                        at_risk += 1
                    else:
                        compliant += 1

            avg_time = sum(remediation_times) / len(remediation_times) if remediation_times else 0
            total = compliant + breached + at_risk
            compliance_rate = (compliant / total * 100) if total > 0 else 100

            metrics.append(SLAMetric(
                severity=severity,
                target_minutes=target_minutes,
                average_minutes=round(avg_time, 1),
                compliant_count=compliant,
                breached_count=breached,
                at_risk_count=at_risk,
                compliance_rate=round(compliance_rate, 1),
            ))

            total_compliant += compliant
            total_breached += breached
            total_at_risk += at_risk
            total_items += total

        overall_rate = (total_compliant / total_items * 100) if total_items > 0 else 100

        return SLAComplianceResponse(
            type="remediation",
            period_days=period_days,
            overall_compliance_rate=round(overall_rate, 1),
            metrics=metrics,
            total_items=total_items,
            compliant_items=total_compliant,
            breached_items=total_breached,
            at_risk_items=total_at_risk,
        )

    async def get_sla_breaches(
        self,
        period_days: int = 30,
    ) -> SLABreachesResponse:
        """Get list of SLA breaches."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        breaches = []
        by_severity: Dict[str, int] = {}
        by_type: Dict[str, int] = {"response": 0, "remediation": 0}

        # Check alerts for response SLA breaches
        for severity, target_minutes in self.RESPONSE_SLA.items():
            severity_enum = self._get_alert_severity(severity)
            if not severity_enum:
                continue

            # Find breached alerts
            query = (
                select(Alert)
                .where(Alert.created_at >= cutoff)
                .where(Alert.severity == severity_enum)
                .where(Alert.status == AlertStatus.NEW)
            )
            result = await self.db.execute(query)
            alerts = result.scalars().all()

            for alert in alerts:
                elapsed = (datetime.utcnow() - alert.created_at).total_seconds() / 60
                if elapsed > target_minutes:
                    target_time = alert.created_at + timedelta(minutes=target_minutes)
                    breaches.append(SLABreach(
                        id=alert.id,
                        entity_type="alert",
                        entity_id=alert.id,
                        entity_name=alert.title,
                        severity=severity,
                        sla_type="response",
                        target_time=target_time,
                        breach_time=target_time,
                        delay_minutes=int(elapsed - target_minutes),
                        assigned_to=alert.assigned_to,
                    ))
                    by_severity[severity] = by_severity.get(severity, 0) + 1
                    by_type["response"] += 1

        # Check vulnerabilities for remediation SLA breaches
        for severity, target_hours in self.REMEDIATION_SLA.items():
            severity_enum = self._get_vuln_severity(severity)
            if not severity_enum:
                continue

            target_minutes = target_hours * 60

            query = (
                select(Vulnerability)
                .where(Vulnerability.created_at >= cutoff)
                .where(Vulnerability.severity == severity_enum)
                .where(Vulnerability.status.in_([
                    VulnerabilityStatus.OPEN,
                    VulnerabilityStatus.IN_PROGRESS
                ]))
            )
            result = await self.db.execute(query)
            vulns = result.scalars().all()

            for vuln in vulns:
                elapsed = (datetime.utcnow() - vuln.created_at).total_seconds() / 60
                if elapsed > target_minutes:
                    target_time = vuln.created_at + timedelta(minutes=target_minutes)
                    breaches.append(SLABreach(
                        id=vuln.id,
                        entity_type="vulnerability",
                        entity_id=vuln.id,
                        entity_name=vuln.title,
                        severity=severity,
                        sla_type="remediation",
                        target_time=target_time,
                        breach_time=target_time,
                        delay_minutes=int(elapsed - target_minutes),
                        assigned_to=vuln.assigned_to,
                    ))
                    by_severity[severity] = by_severity.get(severity, 0) + 1
                    by_type["remediation"] += 1

        # Sort by delay (most severe first)
        breaches.sort(key=lambda b: b.delay_minutes, reverse=True)

        return SLABreachesResponse(
            period_days=period_days,
            total_breaches=len(breaches),
            breaches=breaches[:100],  # Limit to 100 most severe
            by_severity=by_severity,
            by_type=by_type,
        )

    def _get_alert_severity(self, severity: str) -> Optional[AlertSeverity]:
        """Get AlertSeverity enum from string."""
        mapping = {
            "critical": AlertSeverity.CRITICAL,
            "high": AlertSeverity.HIGH,
            "medium": AlertSeverity.MEDIUM,
            "low": AlertSeverity.LOW,
        }
        return mapping.get(severity.lower())

    def _get_vuln_severity(self, severity: str) -> Optional[VulnerabilitySeverity]:
        """Get VulnerabilitySeverity enum from string."""
        mapping = {
            "critical": VulnerabilitySeverity.CRITICAL,
            "high": VulnerabilitySeverity.HIGH,
            "medium": VulnerabilitySeverity.MEDIUM,
            "low": VulnerabilitySeverity.LOW,
        }
        return mapping.get(severity.lower())
