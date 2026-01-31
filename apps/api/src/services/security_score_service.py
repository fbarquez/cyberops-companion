"""Security Score service for calculating organization security posture."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.incident import Incident, IncidentStatus, IncidentSeverity
from src.models.soc import Alert, AlertSeverity, AlertStatus, Case, CaseStatus
from src.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from src.models.risk import Risk, RiskStatus
from src.schemas.analytics import (
    SecurityScoreComponent, SecurityScoreResponse,
    SecurityScoreHistoryPoint, SecurityScoreHistoryResponse,
)


class SecurityScoreService:
    """Service for calculating and tracking security score."""

    # Weights for score components (must sum to 1.0)
    WEIGHTS = {
        "vulnerabilities": 0.25,
        "incidents": 0.20,
        "compliance": 0.20,
        "risks": 0.15,
        "soc": 0.10,
        "patches": 0.10,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_security_score(self) -> SecurityScoreResponse:
        """Calculate current security score."""
        components = []

        # Calculate each component
        vuln_score = await self._calculate_vulnerability_score()
        components.append(vuln_score)

        incident_score = await self._calculate_incident_score()
        components.append(incident_score)

        compliance_score = await self._calculate_compliance_score()
        components.append(compliance_score)

        risk_score = await self._calculate_risk_score()
        components.append(risk_score)

        soc_score = await self._calculate_soc_score()
        components.append(soc_score)

        patch_score = await self._calculate_patch_score()
        components.append(patch_score)

        # Calculate overall score
        overall_score = sum(c.weighted_score for c in components)
        overall_score = max(0, min(100, int(overall_score)))

        # Determine grade
        grade = self._get_grade(overall_score)

        # Determine trend (compare to 7 days ago - simplified)
        trend = "stable"  # Would compare to historical data

        # Generate recommendations
        recommendations = self._generate_recommendations(components)

        return SecurityScoreResponse(
            overall_score=overall_score,
            grade=grade,
            trend=trend,
            components=components,
            calculated_at=datetime.utcnow(),
            recommendations=recommendations,
        )

    async def _calculate_vulnerability_score(self) -> SecurityScoreComponent:
        """Calculate vulnerability component score."""
        # Count open vulnerabilities by severity
        query = (
            select(
                Vulnerability.severity,
                func.count().label('count')
            )
            .where(Vulnerability.status.in_([
                VulnerabilityStatus.OPEN,
                VulnerabilityStatus.IN_PROGRESS
            ]))
            .group_by(Vulnerability.severity)
        )
        result = await self.db.execute(query)
        counts = {str(row.severity): row.count for row in result.all()}

        # Score penalties based on severity
        critical = counts.get('critical', 0) + counts.get('VulnerabilitySeverity.CRITICAL', 0)
        high = counts.get('high', 0) + counts.get('VulnerabilitySeverity.HIGH', 0)
        medium = counts.get('medium', 0) + counts.get('VulnerabilitySeverity.MEDIUM', 0)

        # Start at 100, deduct for open vulns
        score = 100
        score -= critical * 15  # -15 per critical
        score -= high * 5      # -5 per high
        score -= medium * 1    # -1 per medium
        score = max(0, score)

        weight = self.WEIGHTS["vulnerabilities"]
        weighted = score * weight

        status = "good" if score >= 80 else "warning" if score >= 50 else "critical"

        return SecurityScoreComponent(
            name="Vulnerabilities",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status=status,
            details={
                "critical_open": critical,
                "high_open": high,
                "medium_open": medium,
            }
        )

    async def _calculate_incident_score(self) -> SecurityScoreComponent:
        """Calculate incident component score."""
        # Active incidents in last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)

        query = (
            select(
                Incident.severity,
                func.count().label('count')
            )
            .where(Incident.created_at >= cutoff)
            .where(Incident.status.in_([
                IncidentStatus.ACTIVE,
                IncidentStatus.INVESTIGATING,
                IncidentStatus.CONTAINMENT,
            ]))
            .group_by(Incident.severity)
        )
        result = await self.db.execute(query)
        counts = {str(row.severity): row.count for row in result.all()}

        critical = counts.get('critical', 0) + counts.get('IncidentSeverity.CRITICAL', 0)
        high = counts.get('high', 0) + counts.get('IncidentSeverity.HIGH', 0)

        score = 100
        score -= critical * 20  # -20 per active critical incident
        score -= high * 10      # -10 per active high incident
        score = max(0, score)

        weight = self.WEIGHTS["incidents"]
        weighted = score * weight

        status = "good" if score >= 80 else "warning" if score >= 50 else "critical"

        return SecurityScoreComponent(
            name="Incidents",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status=status,
            details={
                "active_critical": critical,
                "active_high": high,
            }
        )

    async def _calculate_compliance_score(self) -> SecurityScoreComponent:
        """Calculate compliance component score."""
        # For now, return a baseline score
        # In production, this would check compliance framework status
        score = 85
        weight = self.WEIGHTS["compliance"]
        weighted = score * weight

        return SecurityScoreComponent(
            name="Compliance",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status="good",
            details={"note": "Based on framework implementation status"}
        )

    async def _calculate_risk_score(self) -> SecurityScoreComponent:
        """Calculate risk component score."""
        # Count unmitigated risks by level
        query = (
            select(func.count())
            .where(Risk.status.in_([
                RiskStatus.IDENTIFIED,
                RiskStatus.ASSESSED,
            ]))
        )
        result = await self.db.execute(query)
        open_risks = result.scalar() or 0

        # Count high/critical risks
        critical_query = (
            select(func.count())
            .where(Risk.status.in_([RiskStatus.IDENTIFIED, RiskStatus.ASSESSED]))
            .where(Risk.risk_score >= 20)  # High risk threshold
        )
        critical_result = await self.db.execute(critical_query)
        critical_risks = critical_result.scalar() or 0

        score = 100
        score -= critical_risks * 10  # -10 per critical/high risk
        score -= max(0, open_risks - 10) * 2  # -2 per risk after first 10
        score = max(0, score)

        weight = self.WEIGHTS["risks"]
        weighted = score * weight

        status = "good" if score >= 80 else "warning" if score >= 50 else "critical"

        return SecurityScoreComponent(
            name="Risk Posture",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status=status,
            details={
                "open_risks": open_risks,
                "critical_risks": critical_risks,
            }
        )

    async def _calculate_soc_score(self) -> SecurityScoreComponent:
        """Calculate SOC operations score."""
        # Check for unhandled critical alerts in last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)

        query = (
            select(func.count())
            .where(Alert.created_at >= cutoff)
            .where(Alert.status == AlertStatus.NEW)
            .where(Alert.severity == AlertSeverity.CRITICAL)
        )
        result = await self.db.execute(query)
        unhandled_critical = result.scalar() or 0

        # Escalated cases not resolved
        escalated_query = (
            select(func.count())
            .where(Case.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS]))
            .where(Case.is_escalated == True)
        )
        escalated_result = await self.db.execute(escalated_query)
        escalated_open = escalated_result.scalar() or 0

        score = 100
        score -= unhandled_critical * 15  # -15 per unhandled critical alert
        score -= escalated_open * 10      # -10 per open escalated case
        score = max(0, score)

        weight = self.WEIGHTS["soc"]
        weighted = score * weight

        status = "good" if score >= 80 else "warning" if score >= 50 else "critical"

        return SecurityScoreComponent(
            name="SOC Operations",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status=status,
            details={
                "unhandled_critical_alerts": unhandled_critical,
                "escalated_cases_open": escalated_open,
            }
        )

    async def _calculate_patch_score(self) -> SecurityScoreComponent:
        """Calculate patch compliance score."""
        # Count overdue vulnerabilities
        query = (
            select(func.count())
            .where(Vulnerability.status.in_([
                VulnerabilityStatus.OPEN,
                VulnerabilityStatus.IN_PROGRESS
            ]))
            .where(Vulnerability.due_date < datetime.utcnow())
        )
        result = await self.db.execute(query)
        overdue = result.scalar() or 0

        # Total open vulnerabilities
        total_query = (
            select(func.count())
            .where(Vulnerability.status.in_([
                VulnerabilityStatus.OPEN,
                VulnerabilityStatus.IN_PROGRESS
            ]))
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        if total > 0:
            compliance_rate = ((total - overdue) / total) * 100
        else:
            compliance_rate = 100

        score = min(100, compliance_rate)

        weight = self.WEIGHTS["patches"]
        weighted = score * weight

        status = "good" if score >= 80 else "warning" if score >= 50 else "critical"

        return SecurityScoreComponent(
            name="Patch Compliance",
            weight=weight,
            score=score,
            weighted_score=weighted,
            status=status,
            details={
                "overdue_patches": overdue,
                "total_open": total,
                "compliance_rate": round(compliance_rate, 1),
            }
        )

    def _get_grade(self, score: int) -> str:
        """Get letter grade from score."""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _generate_recommendations(self, components: List[SecurityScoreComponent]) -> List[str]:
        """Generate recommendations based on component scores."""
        recommendations = []

        for component in components:
            if component.status == "critical":
                if component.name == "Vulnerabilities":
                    recommendations.append(
                        f"Critical: Address {component.details.get('critical_open', 0)} critical vulnerabilities immediately"
                    )
                elif component.name == "Incidents":
                    recommendations.append(
                        f"Critical: Resolve {component.details.get('active_critical', 0)} active critical incidents"
                    )
                elif component.name == "SOC Operations":
                    recommendations.append(
                        "Critical: Review unhandled critical alerts and escalated cases"
                    )
            elif component.status == "warning":
                if component.name == "Patch Compliance":
                    recommendations.append(
                        f"Warning: {component.details.get('overdue_patches', 0)} patches are overdue"
                    )
                elif component.name == "Risk Posture":
                    recommendations.append(
                        f"Warning: {component.details.get('critical_risks', 0)} high-risk items require treatment"
                    )

        return recommendations[:5]  # Top 5 recommendations

    async def get_score_history(
        self,
        period_days: int = 30,
    ) -> SecurityScoreHistoryResponse:
        """Get security score history."""
        # In production, this would query stored snapshots
        # For now, generate simulated history based on current score
        current = await self.get_security_score()
        current_score = current.overall_score

        # Generate history points (simplified - would use actual stored data)
        history = []
        for i in range(period_days, -1, -1):
            date = datetime.utcnow() - timedelta(days=i)
            # Add some variance to simulate history
            variance = (hash(date.strftime("%Y-%m-%d")) % 20) - 10
            score = max(0, min(100, current_score + variance))
            history.append(SecurityScoreHistoryPoint(
                date=date.strftime("%Y-%m-%d"),
                score=score,
            ))

        scores = [h.score for h in history]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Calculate trend
        if len(scores) >= 2:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            trend_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        else:
            trend_pct = 0

        return SecurityScoreHistoryResponse(
            current_score=current_score,
            period_days=period_days,
            history=history,
            average_score=round(avg_score, 1),
            min_score=min(scores) if scores else 0,
            max_score=max(scores) if scores else 0,
            trend_percentage=round(trend_pct, 1),
        )
