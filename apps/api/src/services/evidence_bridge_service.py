"""
Evidence Bridge Service

This service implements the core ISMS ↔ SOC bridge functionality:
1. Automatic linking of activities to controls
2. Control effectiveness calculation from operational data
3. Evidence queries for auditors

The core promise: "ISMS-Anforderungen → Überprüfbare Aktivitäten → Evidenzen"
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.evidence_bridge import (
    ControlEvidenceLink,
    ControlEffectiveness,
    EvidenceLinkingRule,
    ActivityType,
    ControlFramework,
    LinkType,
    EvidenceStrength,
    EffectivenessLevel,
    CONTROL_ACTIVITY_MAPPING,
    get_controls_for_activity,
    calculate_effectiveness_level,
    get_effectiveness_color,
)
from src.schemas.evidence_bridge import (
    EvidenceLinkCreate,
    EvidenceLinkResponse,
    EvidenceListResponse,
    ControlEffectivenessResponse,
    ControlEffectivenessSummary,
    FrameworkEffectivenessResponse,
    EvidenceBridgeDashboard,
    ActivityEvidenceInfo,
    ControlAuditView,
)


# =============================================================================
# CONTROL METADATA
# =============================================================================

ISO27001_CONTROLS = {
    "A.5.1": {"name": "Policies for information security", "category": "Organizational"},
    "A.5.7": {"name": "Threat intelligence", "category": "Organizational"},
    "A.5.23": {"name": "Information security for cloud services", "category": "Organizational"},
    "A.5.24": {"name": "Incident management planning and preparation", "category": "Organizational"},
    "A.5.25": {"name": "Assessment and decision on security events", "category": "Organizational"},
    "A.5.26": {"name": "Response to information security incidents", "category": "Organizational"},
    "A.5.27": {"name": "Learning from information security incidents", "category": "Organizational"},
    "A.5.28": {"name": "Collection of evidence", "category": "Organizational"},
    "A.5.29": {"name": "Information security during disruption", "category": "Organizational"},
    "A.5.30": {"name": "ICT readiness for business continuity", "category": "Organizational"},
    "A.6.3": {"name": "Information security awareness and training", "category": "People"},
    "A.8.8": {"name": "Management of technical vulnerabilities", "category": "Technological"},
    "A.8.16": {"name": "Monitoring activities", "category": "Technological"},
    "A.8.32": {"name": "Change management", "category": "Technological"},
}

DORA_CONTROLS = {
    "DORA-P1-01": {"name": "ICT Risk Management Framework", "category": "Pillar 1"},
    "DORA-P2-01": {"name": "ICT Incident Management Process", "category": "Pillar 2"},
    "DORA-P2-02": {"name": "Major Incident Reporting", "category": "Pillar 2"},
    "DORA-P3-01": {"name": "Digital Resilience Testing", "category": "Pillar 3"},
    "DORA-P4-01": {"name": "Third-Party Risk Management", "category": "Pillar 4"},
}

NIS2_CONTROLS = {
    "NIS2-21-a": {"name": "Risk analysis and IS security policies", "category": "Article 21"},
    "NIS2-21-b": {"name": "Incident handling", "category": "Article 21"},
    "NIS2-21-c": {"name": "Business continuity and crisis management", "category": "Article 21"},
    "NIS2-21-d": {"name": "Supply chain security", "category": "Article 21"},
    "NIS2-21-e": {"name": "Security in acquisition and development", "category": "Article 21"},
    "NIS2-21-g": {"name": "Cyber hygiene and training", "category": "Article 21"},
    "NIS2-21-j": {"name": "Multi-factor authentication", "category": "Article 21"},
}

FRAMEWORK_CONTROLS = {
    ControlFramework.ISO27001: ISO27001_CONTROLS,
    ControlFramework.DORA: DORA_CONTROLS,
    ControlFramework.NIS2: NIS2_CONTROLS,
}


class EvidenceBridgeService:
    """Service for managing the ISMS ↔ SOC evidence bridge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # AUTO-LINKING
    # =========================================================================

    async def link_activity_to_controls(
        self,
        tenant_id: str,
        activity_type: ActivityType,
        activity_id: str,
        activity_title: Optional[str] = None,
        activity_date: Optional[datetime] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> List[ControlEvidenceLink]:
        """
        Automatically link an activity to all relevant controls.
        Called when an incident, alert, scan, etc. is created or updated.

        Args:
            tenant_id: Organization ID
            activity_type: Type of activity (incident, alert, etc.)
            activity_id: ID of the activity
            activity_title: Display title for the activity
            activity_date: When the activity occurred
            additional_data: Extra data for metrics snapshot

        Returns:
            List of created evidence links
        """
        # Get all controls this activity should link to
        control_mappings = get_controls_for_activity(activity_type)

        # Also check custom rules for this tenant
        custom_rules = await self._get_custom_rules(tenant_id, activity_type)

        # Merge default and custom mappings
        all_mappings = control_mappings + custom_rules

        created_links = []

        for mapping in all_mappings:
            # Check if link already exists
            existing = await self._get_existing_link(
                tenant_id,
                mapping["framework"],
                mapping["control_id"],
                activity_type,
                activity_id,
            )

            if existing:
                continue  # Don't duplicate

            # Get control name
            control_name = self._get_control_name(
                ControlFramework(mapping["framework"]),
                mapping["control_id"]
            )

            # Create the link
            link = ControlEvidenceLink(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                control_framework=ControlFramework(mapping["framework"]),
                control_id=mapping["control_id"],
                control_name=control_name,
                activity_type=activity_type,
                activity_id=activity_id,
                activity_title=activity_title,
                activity_date=activity_date or datetime.utcnow(),
                link_type=LinkType.AUTOMATIC,
                evidence_strength=mapping.get("strength", EvidenceStrength.MODERATE),
                metrics_snapshot=additional_data,
                linked_at=datetime.utcnow(),
            )

            self.db.add(link)
            created_links.append(link)

        if created_links:
            await self.db.commit()

            # Trigger effectiveness recalculation for affected controls
            for link in created_links:
                await self.recalculate_control_effectiveness(
                    tenant_id,
                    link.control_framework,
                    link.control_id,
                )

        return created_links

    async def create_manual_link(
        self,
        tenant_id: str,
        user_id: str,
        data: EvidenceLinkCreate,
        activity_title: Optional[str] = None,
        activity_date: Optional[datetime] = None,
    ) -> ControlEvidenceLink:
        """Create a manual evidence link."""
        control_name = self._get_control_name(data.control_framework, data.control_id)

        link = ControlEvidenceLink(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            control_framework=data.control_framework,
            control_id=data.control_id,
            control_name=control_name,
            activity_type=data.activity_type,
            activity_id=data.activity_id,
            activity_title=activity_title,
            activity_date=activity_date or datetime.utcnow(),
            link_type=LinkType.MANUAL,
            evidence_strength=data.evidence_strength,
            notes=data.notes,
            linked_at=datetime.utcnow(),
            linked_by=user_id,
        )

        self.db.add(link)
        await self.db.commit()

        # Recalculate effectiveness
        await self.recalculate_control_effectiveness(
            tenant_id,
            data.control_framework,
            data.control_id,
        )

        return link

    # =========================================================================
    # EFFECTIVENESS CALCULATION
    # =========================================================================

    async def recalculate_control_effectiveness(
        self,
        tenant_id: str,
        framework: ControlFramework,
        control_id: str,
        period_days: int = 90,
    ) -> ControlEffectiveness:
        """
        Recalculate effectiveness score for a control based on linked evidence.

        The score is calculated from:
        - Number of evidence items (weighted by strength)
        - Recency of evidence
        - Operational metrics (response time, resolution rate, etc.)
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        # Get all evidence links for this control in the period
        query = select(ControlEvidenceLink).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == framework,
                ControlEvidenceLink.control_id == control_id,
                ControlEvidenceLink.activity_date >= period_start,
            )
        ).order_by(desc(ControlEvidenceLink.activity_date))

        result = await self.db.execute(query)
        links = result.scalars().all()

        # Calculate evidence counts
        total_count = len(links)
        strong_count = sum(1 for l in links if l.evidence_strength == EvidenceStrength.STRONG)
        moderate_count = sum(1 for l in links if l.evidence_strength == EvidenceStrength.MODERATE)
        weak_count = sum(1 for l in links if l.evidence_strength == EvidenceStrength.WEAK)

        # Count by type
        by_type = {}
        for link in links:
            type_key = link.activity_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        # Calculate weighted score
        # Strong evidence = 3 points, Moderate = 2, Weak = 1
        weighted_points = (strong_count * 3) + (moderate_count * 2) + (weak_count * 1)

        # Base score from evidence quantity (0-50 points)
        # Diminishing returns after certain thresholds
        if total_count == 0:
            quantity_score = 0
        elif total_count < 5:
            quantity_score = total_count * 5  # 0-25
        elif total_count < 20:
            quantity_score = 25 + (total_count - 5) * 1.5  # 25-47.5
        else:
            quantity_score = min(50, 47.5 + (total_count - 20) * 0.1)  # Cap at 50

        # Quality score from strength distribution (0-30 points)
        if total_count > 0:
            strong_ratio = strong_count / total_count
            quality_score = strong_ratio * 30
        else:
            quality_score = 0

        # Recency score (0-20 points)
        if links:
            last_activity = links[0].activity_date
            days_since = (now - last_activity).days
            if days_since <= 7:
                recency_score = 20
            elif days_since <= 30:
                recency_score = 15
            elif days_since <= 60:
                recency_score = 10
            elif days_since <= 90:
                recency_score = 5
            else:
                recency_score = 0
        else:
            recency_score = 0
            last_activity = None

        # Total effectiveness score
        effectiveness_score = min(100, quantity_score + quality_score + recency_score)

        # Determine level
        effectiveness_level = calculate_effectiveness_level(effectiveness_score)

        # Calculate operational metrics from linked activities
        operational_metrics = await self._calculate_operational_metrics(links)

        # Determine if meets baseline (>50% for now)
        meets_baseline = effectiveness_score >= 50

        # Identify gaps
        gaps = []
        if total_count == 0:
            gaps.append("No evidence linked in the assessment period")
        if strong_count == 0 and total_count > 0:
            gaps.append("No strong evidence available")
        if last_activity and (now - last_activity).days > 30:
            gaps.append(f"No recent activity ({(now - last_activity).days} days since last)")

        # Get control metadata
        control_name = self._get_control_name(framework, control_id)

        # Check for existing effectiveness record
        existing_query = select(ControlEffectiveness).where(
            and_(
                ControlEffectiveness.tenant_id == tenant_id,
                ControlEffectiveness.control_framework == framework,
                ControlEffectiveness.control_id == control_id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        effectiveness = existing_result.scalar_one_or_none()

        if effectiveness:
            # Update existing
            effectiveness.effectiveness_score = effectiveness_score
            effectiveness.effectiveness_level = effectiveness_level
            effectiveness.total_evidence_count = total_count
            effectiveness.strong_evidence_count = strong_count
            effectiveness.moderate_evidence_count = moderate_count
            effectiveness.weak_evidence_count = weak_count
            effectiveness.evidence_by_type = by_type
            effectiveness.operational_metrics = operational_metrics
            effectiveness.calculation_period_start = period_start
            effectiveness.calculation_period_end = now
            effectiveness.last_activity_date = last_activity
            effectiveness.last_activity_type = links[0].activity_type if links else None
            effectiveness.last_activity_id = links[0].activity_id if links else None
            effectiveness.calculated_at = now
            effectiveness.meets_baseline = meets_baseline
            effectiveness.gaps_identified = gaps
            effectiveness.updated_at = now
        else:
            # Create new
            effectiveness = ControlEffectiveness(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                control_framework=framework,
                control_id=control_id,
                control_name=control_name,
                effectiveness_score=effectiveness_score,
                effectiveness_level=effectiveness_level,
                total_evidence_count=total_count,
                strong_evidence_count=strong_count,
                moderate_evidence_count=moderate_count,
                weak_evidence_count=weak_count,
                evidence_by_type=by_type,
                operational_metrics=operational_metrics,
                calculation_period_start=period_start,
                calculation_period_end=now,
                last_activity_date=last_activity,
                last_activity_type=links[0].activity_type if links else None,
                last_activity_id=links[0].activity_id if links else None,
                calculated_at=now,
                meets_baseline=meets_baseline,
                gaps_identified=gaps,
            )
            self.db.add(effectiveness)

        await self.db.commit()
        return effectiveness

    async def recalculate_framework_effectiveness(
        self,
        tenant_id: str,
        framework: ControlFramework,
    ) -> Dict[str, Any]:
        """Recalculate effectiveness for all controls in a framework."""
        controls = FRAMEWORK_CONTROLS.get(framework, {})

        results = []
        for control_id in controls.keys():
            eff = await self.recalculate_control_effectiveness(
                tenant_id, framework, control_id
            )
            results.append(eff)

        return {
            "framework": framework.value,
            "controls_recalculated": len(results),
            "avg_score": sum(e.effectiveness_score for e in results) / len(results) if results else 0,
        }

    # =========================================================================
    # QUERIES
    # =========================================================================

    async def get_control_evidence(
        self,
        tenant_id: str,
        framework: ControlFramework,
        control_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> EvidenceListResponse:
        """Get all evidence links for a control."""
        # Get control name
        control_name = self._get_control_name(framework, control_id)

        # Count total
        count_query = select(func.count(ControlEvidenceLink.id)).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == framework,
                ControlEvidenceLink.control_id == control_id,
            )
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        # Get evidence
        query = select(ControlEvidenceLink).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == framework,
                ControlEvidenceLink.control_id == control_id,
            )
        ).order_by(desc(ControlEvidenceLink.activity_date)).offset(offset).limit(limit)

        result = await self.db.execute(query)
        links = result.scalars().all()

        # Count by type
        by_type_query = select(
            ControlEvidenceLink.activity_type,
            func.count(ControlEvidenceLink.id)
        ).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == framework,
                ControlEvidenceLink.control_id == control_id,
            )
        ).group_by(ControlEvidenceLink.activity_type)

        by_type_result = await self.db.execute(by_type_query)
        by_type = {row[0].value: row[1] for row in by_type_result}

        # Count by strength
        by_strength_query = select(
            ControlEvidenceLink.evidence_strength,
            func.count(ControlEvidenceLink.id)
        ).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == framework,
                ControlEvidenceLink.control_id == control_id,
            )
        ).group_by(ControlEvidenceLink.evidence_strength)

        by_strength_result = await self.db.execute(by_strength_query)
        by_strength = {row[0].value: row[1] for row in by_strength_result}

        return EvidenceListResponse(
            control_framework=framework,
            control_id=control_id,
            control_name=control_name,
            total_count=total_count,
            evidence=[self._link_to_response(l) for l in links],
            by_type=by_type,
            by_strength=by_strength,
        )

    async def get_control_effectiveness(
        self,
        tenant_id: str,
        framework: ControlFramework,
        control_id: str,
    ) -> Optional[ControlEffectivenessResponse]:
        """Get effectiveness for a specific control."""
        query = select(ControlEffectiveness).where(
            and_(
                ControlEffectiveness.tenant_id == tenant_id,
                ControlEffectiveness.control_framework == framework,
                ControlEffectiveness.control_id == control_id,
            )
        )

        result = await self.db.execute(query)
        eff = result.scalar_one_or_none()

        if not eff:
            # Calculate on-demand
            eff = await self.recalculate_control_effectiveness(
                tenant_id, framework, control_id
            )

        return self._effectiveness_to_response(eff)

    async def get_framework_effectiveness(
        self,
        tenant_id: str,
        framework: ControlFramework,
    ) -> FrameworkEffectivenessResponse:
        """Get effectiveness summary for all controls in a framework."""
        controls_meta = FRAMEWORK_CONTROLS.get(framework, {})

        # Get all effectiveness records
        query = select(ControlEffectiveness).where(
            and_(
                ControlEffectiveness.tenant_id == tenant_id,
                ControlEffectiveness.control_framework == framework,
            )
        ).order_by(desc(ControlEffectiveness.effectiveness_score))

        result = await self.db.execute(query)
        effectiveness_records = result.scalars().all()

        # Build summaries
        controls = []
        by_level = {level.value: 0 for level in EffectivenessLevel}
        total_score = 0
        meeting_baseline = 0

        for eff in effectiveness_records:
            controls.append(ControlEffectivenessSummary(
                control_id=eff.control_id,
                control_name=eff.control_name or eff.control_id,
                effectiveness_score=eff.effectiveness_score,
                effectiveness_level=eff.effectiveness_level,
                effectiveness_color=get_effectiveness_color(eff.effectiveness_level),
                evidence_count=eff.total_evidence_count,
                last_activity_date=eff.last_activity_date,
                trend=eff.operational_metrics.get("trend") if eff.operational_metrics else None,
            ))
            by_level[eff.effectiveness_level.value] += 1
            total_score += eff.effectiveness_score
            if eff.meets_baseline:
                meeting_baseline += 1

        # Add controls without effectiveness records
        assessed_ids = {e.control_id for e in effectiveness_records}
        for control_id, meta in controls_meta.items():
            if control_id not in assessed_ids:
                controls.append(ControlEffectivenessSummary(
                    control_id=control_id,
                    control_name=meta["name"],
                    effectiveness_score=0,
                    effectiveness_level=EffectivenessLevel.NOT_ASSESSED,
                    effectiveness_color="gray",
                    evidence_count=0,
                    last_activity_date=None,
                    trend=None,
                ))
                by_level[EffectivenessLevel.NOT_ASSESSED.value] += 1

        # Calculate overall
        controls_assessed = len(effectiveness_records)
        controls_total = len(controls_meta)
        overall_score = total_score / controls_assessed if controls_assessed > 0 else 0
        overall_level = calculate_effectiveness_level(overall_score)

        # Top gaps (lowest scoring assessed controls)
        top_gaps = [
            {"control_id": c.control_id, "control_name": c.control_name, "score": c.effectiveness_score}
            for c in sorted(controls, key=lambda x: x.effectiveness_score)[:5]
            if c.effectiveness_score < 50
        ]

        framework_names = {
            ControlFramework.ISO27001: "ISO 27001:2022",
            ControlFramework.DORA: "DORA",
            ControlFramework.NIS2: "NIS2 Directive",
            ControlFramework.BSI: "BSI IT-Grundschutz",
        }

        return FrameworkEffectivenessResponse(
            framework=framework,
            framework_name=framework_names.get(framework, framework.value),
            overall_score=overall_score,
            overall_level=overall_level,
            controls_assessed=controls_assessed,
            controls_total=controls_total,
            controls_meeting_baseline=meeting_baseline,
            by_level=by_level,
            controls=controls,
            top_gaps=top_gaps,
        )

    async def get_dashboard(self, tenant_id: str) -> EvidenceBridgeDashboard:
        """Get main dashboard data."""
        now = datetime.utcnow()

        # Total evidence links
        total_query = select(func.count(ControlEvidenceLink.id)).where(
            ControlEvidenceLink.tenant_id == tenant_id
        )
        total_result = await self.db.execute(total_query)
        total_links = total_result.scalar()

        # Links in time periods
        async def count_links_since(days: int) -> int:
            since = now - timedelta(days=days)
            q = select(func.count(ControlEvidenceLink.id)).where(
                and_(
                    ControlEvidenceLink.tenant_id == tenant_id,
                    ControlEvidenceLink.linked_at >= since,
                )
            )
            r = await self.db.execute(q)
            return r.scalar()

        links_24h = await count_links_since(1)
        links_7d = await count_links_since(7)
        links_30d = await count_links_since(30)

        # By framework
        frameworks = []
        for fw in [ControlFramework.ISO27001, ControlFramework.DORA, ControlFramework.NIS2]:
            fw_eff = await self.get_framework_effectiveness(tenant_id, fw)
            frameworks.append({
                "framework": fw.value,
                "framework_name": fw_eff.framework_name,
                "score": fw_eff.overall_score,
                "controls_assessed": fw_eff.controls_assessed,
                "controls_total": fw_eff.controls_total,
            })

        # Activities linked
        activity_query = select(
            ControlEvidenceLink.activity_type,
            func.count(ControlEvidenceLink.id)
        ).where(
            ControlEvidenceLink.tenant_id == tenant_id
        ).group_by(ControlEvidenceLink.activity_type)

        activity_result = await self.db.execute(activity_query)
        activities_linked = {row[0].value: row[1] for row in activity_result}

        # Top controls
        top_query = select(ControlEffectiveness).where(
            ControlEffectiveness.tenant_id == tenant_id
        ).order_by(desc(ControlEffectiveness.total_evidence_count)).limit(5)

        top_result = await self.db.execute(top_query)
        top_controls = [
            ControlEffectivenessSummary(
                control_id=e.control_id,
                control_name=e.control_name or e.control_id,
                effectiveness_score=e.effectiveness_score,
                effectiveness_level=e.effectiveness_level,
                effectiveness_color=get_effectiveness_color(e.effectiveness_level),
                evidence_count=e.total_evidence_count,
                last_activity_date=e.last_activity_date,
            )
            for e in top_result.scalars().all()
        ]

        # Controls needing attention
        attention_query = select(ControlEffectiveness).where(
            and_(
                ControlEffectiveness.tenant_id == tenant_id,
                ControlEffectiveness.effectiveness_score < 50,
            )
        ).order_by(ControlEffectiveness.effectiveness_score).limit(5)

        attention_result = await self.db.execute(attention_query)
        controls_needing_attention = [
            ControlEffectivenessSummary(
                control_id=e.control_id,
                control_name=e.control_name or e.control_id,
                effectiveness_score=e.effectiveness_score,
                effectiveness_level=e.effectiveness_level,
                effectiveness_color=get_effectiveness_color(e.effectiveness_level),
                evidence_count=e.total_evidence_count,
                last_activity_date=e.last_activity_date,
            )
            for e in attention_result.scalars().all()
        ]

        # Recent evidence
        recent_query = select(ControlEvidenceLink).where(
            ControlEvidenceLink.tenant_id == tenant_id
        ).order_by(desc(ControlEvidenceLink.linked_at)).limit(10)

        recent_result = await self.db.execute(recent_query)
        recent_evidence = [self._link_to_response(l) for l in recent_result.scalars().all()]

        return EvidenceBridgeDashboard(
            total_evidence_links=total_links,
            links_last_24h=links_24h,
            links_last_7d=links_7d,
            links_last_30d=links_30d,
            frameworks=frameworks,
            activities_linked=activities_linked,
            top_controls=top_controls,
            controls_needing_attention=controls_needing_attention,
            recent_evidence=recent_evidence,
            effectiveness_trend=[],  # TODO: Implement trend calculation
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _get_existing_link(
        self,
        tenant_id: str,
        framework: str,
        control_id: str,
        activity_type: ActivityType,
        activity_id: str,
    ) -> Optional[ControlEvidenceLink]:
        """Check if a link already exists."""
        query = select(ControlEvidenceLink).where(
            and_(
                ControlEvidenceLink.tenant_id == tenant_id,
                ControlEvidenceLink.control_framework == ControlFramework(framework),
                ControlEvidenceLink.control_id == control_id,
                ControlEvidenceLink.activity_type == activity_type,
                ControlEvidenceLink.activity_id == activity_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_custom_rules(
        self,
        tenant_id: str,
        activity_type: ActivityType,
    ) -> List[Dict[str, Any]]:
        """Get custom linking rules for a tenant."""
        query = select(EvidenceLinkingRule).where(
            and_(
                EvidenceLinkingRule.tenant_id == tenant_id,
                EvidenceLinkingRule.activity_type == activity_type,
                EvidenceLinkingRule.is_active == True,
                EvidenceLinkingRule.auto_link == True,
            )
        )
        result = await self.db.execute(query)
        rules = result.scalars().all()

        return [
            {
                "framework": rule.control_framework.value,
                "control_id": rule.control_id,
                "strength": rule.evidence_strength,
                "metrics": rule.metrics_to_capture or [],
            }
            for rule in rules
        ]

    def _get_control_name(self, framework: ControlFramework, control_id: str) -> str:
        """Get the display name for a control."""
        controls = FRAMEWORK_CONTROLS.get(framework, {})
        meta = controls.get(control_id, {})
        return meta.get("name", control_id)

    async def _calculate_operational_metrics(
        self,
        links: List[ControlEvidenceLink],
    ) -> Dict[str, Any]:
        """Calculate operational metrics from linked activities."""
        # This would ideally query the actual activity data
        # For now, return summary based on what we have
        if not links:
            return {}

        metrics = {
            "evidence_count": len(links),
            "first_evidence_date": min(l.activity_date for l in links if l.activity_date).isoformat() if links else None,
            "last_evidence_date": max(l.activity_date for l in links if l.activity_date).isoformat() if links else None,
        }

        # Count by type
        type_counts = {}
        for link in links:
            key = link.activity_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        metrics["by_activity_type"] = type_counts

        # Calculate trend (simple: compare last 30 days to previous 30)
        now = datetime.utcnow()
        last_30 = sum(1 for l in links if l.activity_date and (now - l.activity_date).days <= 30)
        prev_30 = sum(1 for l in links if l.activity_date and 30 < (now - l.activity_date).days <= 60)

        if last_30 > prev_30:
            metrics["trend"] = "improving"
        elif last_30 < prev_30:
            metrics["trend"] = "declining"
        else:
            metrics["trend"] = "stable"

        return metrics

    def _link_to_response(self, link: ControlEvidenceLink) -> EvidenceLinkResponse:
        """Convert a link model to response schema."""
        return EvidenceLinkResponse(
            id=link.id,
            control_framework=link.control_framework,
            control_id=link.control_id,
            control_name=link.control_name,
            activity_type=link.activity_type,
            activity_id=link.activity_id,
            activity_title=link.activity_title,
            activity_date=link.activity_date,
            link_type=link.link_type,
            evidence_strength=link.evidence_strength,
            notes=link.notes,
            linked_at=link.linked_at,
            linked_by=link.linked_by,
        )

    def _effectiveness_to_response(self, eff: ControlEffectiveness) -> ControlEffectivenessResponse:
        """Convert an effectiveness model to response schema."""
        now = datetime.utcnow()
        days_since = None
        if eff.last_activity_date:
            days_since = (now - eff.last_activity_date).days

        return ControlEffectivenessResponse(
            id=eff.id,
            control_framework=eff.control_framework,
            control_id=eff.control_id,
            control_name=eff.control_name,
            control_description=eff.control_description,
            effectiveness_score=eff.effectiveness_score,
            effectiveness_level=eff.effectiveness_level,
            effectiveness_color=get_effectiveness_color(eff.effectiveness_level),
            total_evidence_count=eff.total_evidence_count,
            strong_evidence_count=eff.strong_evidence_count,
            moderate_evidence_count=eff.moderate_evidence_count,
            weak_evidence_count=eff.weak_evidence_count,
            evidence_by_type=eff.evidence_by_type,
            operational_metrics=eff.operational_metrics,
            last_activity_date=eff.last_activity_date,
            last_activity_type=eff.last_activity_type,
            days_since_last_activity=days_since,
            meets_baseline=eff.meets_baseline,
            gaps_identified=eff.gaps_identified,
            trend=eff.operational_metrics.get("trend") if eff.operational_metrics else None,
            calculated_at=eff.calculated_at,
        )
