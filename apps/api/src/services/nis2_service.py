"""NIS2 Assessment Wizard service."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.nis2 import (
    NIS2Assessment, NIS2MeasureResponse,
    NIS2Sector, NIS2EntityType, NIS2CompanySize,
    NIS2AssessmentStatus, NIS2MeasureStatus,
    NIS2_SECURITY_MEASURES, ESSENTIAL_SECTORS, IMPORTANT_SECTORS, SECTOR_METADATA
)
from src.schemas.nis2 import (
    AssessmentCreate, AssessmentScopeUpdate, MeasureResponseCreate,
    ClassificationResult, GapItem, SectorInfo
)

logger = logging.getLogger(__name__)


class NIS2AssessmentService:
    """Service for NIS2 assessment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Sector Information ==============

    def get_sectors_info(self) -> Dict[str, List[SectorInfo]]:
        """Get all NIS2 sectors with metadata."""
        essential = []
        important = []

        for sector in NIS2Sector:
            meta = SECTOR_METADATA.get(sector, {})
            info = SectorInfo(
                sector=sector,
                name_en=meta.get("name_en", sector.value),
                name_de=meta.get("name_de", sector.value),
                name_es=meta.get("name_es", sector.value),
                icon=meta.get("icon", "shield"),
                subsectors=meta.get("subsectors", []),
                is_essential=sector in ESSENTIAL_SECTORS,
            )
            if sector in ESSENTIAL_SECTORS:
                essential.append(info)
            else:
                important.append(info)

        return {"essential_sectors": essential, "important_sectors": important}

    def get_security_measures(self) -> Dict[str, Any]:
        """Get all NIS2 security measures."""
        measures = []
        total_weight = 0

        for m in NIS2_SECURITY_MEASURES:
            measures.append({
                "id": m["id"],
                "article": m["article"],
                "name_en": m["name_en"],
                "name_de": m["name_de"],
                "name_es": m["name_es"],
                "description_en": m["description_en"],
                "weight": m["weight"],
                "sub_requirements": m["sub_requirements"],
            })
            total_weight += m["weight"]

        return {"measures": measures, "total_weight": total_weight}

    # ============== Assessment CRUD ==============

    async def create_assessment(
        self, data: AssessmentCreate, user_id: str, tenant_id: str
    ) -> NIS2Assessment:
        """Create a new NIS2 assessment."""
        assessment = NIS2Assessment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=NIS2AssessmentStatus.DRAFT,
            created_by=user_id,
            started_at=datetime.utcnow(),
        )
        self.db.add(assessment)
        await self.db.flush()
        await self.db.refresh(assessment)

        # Initialize measure responses
        for measure in NIS2_SECURITY_MEASURES:
            response = NIS2MeasureResponse(
                id=str(uuid4()),
                assessment_id=assessment.id,
                measure_id=measure["id"],
                status=NIS2MeasureStatus.NOT_EVALUATED,
                sub_requirements_status=[
                    {"name": req, "implemented": False, "notes": None}
                    for req in measure["sub_requirements"]
                ],
            )
            self.db.add(response)

        await self.db.flush()
        return assessment

    async def get_assessment(self, assessment_id: str, tenant_id: str) -> Optional[NIS2Assessment]:
        """Get assessment by ID."""
        result = await self.db.execute(
            select(NIS2Assessment).where(
                and_(
                    NIS2Assessment.id == assessment_id,
                    NIS2Assessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_assessment_with_responses(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get assessment with all measure responses."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get measure responses
        result = await self.db.execute(
            select(NIS2MeasureResponse).where(
                NIS2MeasureResponse.assessment_id == assessment_id
            ).order_by(NIS2MeasureResponse.measure_id)
        )
        responses = result.scalars().all()

        # Build classification if available
        classification = None
        if assessment.entity_type:
            classification = self._build_classification_result(assessment)

        return {
            "assessment": assessment,
            "measure_responses": list(responses),
            "classification": classification,
        }

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[NIS2AssessmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[NIS2Assessment], int]:
        """List assessments for a tenant."""
        query = select(NIS2Assessment).where(NIS2Assessment.tenant_id == tenant_id)

        if status:
            query = query.where(NIS2Assessment.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Get page
        query = query.order_by(NIS2Assessment.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    async def delete_assessment(self, assessment_id: str, tenant_id: str) -> bool:
        """Delete an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return False

        await self.db.delete(assessment)
        await self.db.flush()
        return True

    # ============== Wizard Steps ==============

    async def update_scope(
        self, assessment_id: str, tenant_id: str, data: AssessmentScopeUpdate
    ) -> Optional[NIS2Assessment]:
        """Update assessment scope (Wizard Step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.sector = data.sector
        assessment.subsector = data.subsector
        assessment.company_size = data.company_size
        assessment.employee_count = data.employee_count
        assessment.annual_turnover_eur = data.annual_turnover_eur
        assessment.operates_in_eu = data.operates_in_eu
        assessment.eu_countries = data.eu_countries

        # Auto-classify based on scope
        entity_type, reason = self._classify_entity(data)
        assessment.entity_type = entity_type
        assessment.classification_reason = reason

        assessment.status = NIS2AssessmentStatus.IN_PROGRESS

        await self.db.flush()
        await self.db.refresh(assessment)
        return assessment

    def _classify_entity(
        self, data: AssessmentScopeUpdate
    ) -> Tuple[NIS2EntityType, str]:
        """Classify entity as Essential, Important, or Out of Scope."""
        sector = data.sector
        size = data.company_size

        # Check if operates in EU
        if not data.operates_in_eu:
            return (
                NIS2EntityType.OUT_OF_SCOPE,
                "Organization does not operate in the EU"
            )

        # Micro and small companies are generally out of scope
        # (with some exceptions for critical infrastructure)
        if size in [NIS2CompanySize.MICRO, NIS2CompanySize.SMALL]:
            if sector in [NIS2Sector.DIGITAL_INFRASTRUCTURE, NIS2Sector.PUBLIC_ADMINISTRATION]:
                # These sectors have no size exemption
                pass
            else:
                return (
                    NIS2EntityType.OUT_OF_SCOPE,
                    f"Organization is below the size threshold ({size.value}) for NIS2 applicability"
                )

        # Essential entities (Annex I)
        if sector in ESSENTIAL_SECTORS:
            if size == NIS2CompanySize.LARGE:
                return (
                    NIS2EntityType.ESSENTIAL,
                    f"Large entity in essential sector ({sector.value}) - classified as Essential Entity per NIS2 Annex I"
                )
            else:  # Medium
                return (
                    NIS2EntityType.ESSENTIAL,
                    f"Medium entity in essential sector ({sector.value}) - classified as Essential Entity per NIS2 Annex I"
                )

        # Important entities (Annex II)
        if sector in IMPORTANT_SECTORS:
            return (
                NIS2EntityType.IMPORTANT,
                f"Entity in important sector ({sector.value}) - classified as Important Entity per NIS2 Annex II"
            )

        return (
            NIS2EntityType.OUT_OF_SCOPE,
            f"Sector {sector.value} is not covered by NIS2"
        )

    def _build_classification_result(self, assessment: NIS2Assessment) -> ClassificationResult:
        """Build classification result from assessment."""
        is_essential = assessment.entity_type == NIS2EntityType.ESSENTIAL

        # Determine supervision level
        if assessment.entity_type == NIS2EntityType.OUT_OF_SCOPE:
            supervision = "Not applicable"
            reporting = {"required": False}
        elif is_essential:
            supervision = "Ex-ante supervision by competent authorities"
            reporting = {
                "required": True,
                "initial_notification": "24 hours",
                "incident_notification": "72 hours",
                "final_report": "1 month",
                "authority": "National competent authority (NCA)"
            }
        else:
            supervision = "Ex-post supervision (reactive)"
            reporting = {
                "required": True,
                "initial_notification": "24 hours",
                "incident_notification": "72 hours",
                "final_report": "1 month",
                "authority": "National competent authority (NCA)"
            }

        # All 10 measures apply to both Essential and Important entities
        applicable = [m["id"] for m in NIS2_SECURITY_MEASURES]

        return ClassificationResult(
            entity_type=assessment.entity_type,
            classification_reason=assessment.classification_reason or "",
            applicable_requirements=applicable,
            supervision_level=supervision,
            reporting_obligations=reporting,
        )

    # ============== Measure Responses ==============

    async def update_measure_response(
        self,
        assessment_id: str,
        tenant_id: str,
        data: MeasureResponseCreate,
        user_id: str,
    ) -> Optional[NIS2MeasureResponse]:
        """Update a measure response."""
        # Verify assessment ownership
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get or create response
        result = await self.db.execute(
            select(NIS2MeasureResponse).where(
                and_(
                    NIS2MeasureResponse.assessment_id == assessment_id,
                    NIS2MeasureResponse.measure_id == data.measure_id,
                )
            )
        )
        response = result.scalar_one_or_none()

        if not response:
            response = NIS2MeasureResponse(
                id=str(uuid4()),
                assessment_id=assessment_id,
                measure_id=data.measure_id,
            )
            self.db.add(response)

        # Update fields
        response.status = data.status
        response.implementation_level = data.implementation_level
        if data.sub_requirements_status:
            response.sub_requirements_status = [
                s.model_dump() for s in data.sub_requirements_status
            ]
        response.evidence = data.evidence
        response.notes = data.notes
        response.gap_description = data.gap_description
        response.remediation_plan = data.remediation_plan
        response.priority = data.priority
        response.due_date = data.due_date
        response.assessed_at = datetime.utcnow()
        response.assessed_by = user_id

        await self.db.flush()
        await self.db.refresh(response)

        # Update assessment scores
        await self._recalculate_scores(assessment_id)

        return response

    async def bulk_update_measures(
        self,
        assessment_id: str,
        tenant_id: str,
        responses: List[MeasureResponseCreate],
        user_id: str,
    ) -> List[NIS2MeasureResponse]:
        """Bulk update measure responses."""
        results = []
        for data in responses:
            response = await self.update_measure_response(
                assessment_id, tenant_id, data, user_id
            )
            if response:
                results.append(response)
        return results

    async def _recalculate_scores(self, assessment_id: str):
        """Recalculate assessment scores based on measure responses."""
        # Get all responses
        result = await self.db.execute(
            select(NIS2MeasureResponse).where(
                NIS2MeasureResponse.assessment_id == assessment_id
            )
        )
        responses = result.scalars().all()

        # Calculate weighted score
        total_weight = 0
        weighted_score = 0
        gaps_count = 0
        critical_gaps_count = 0

        measure_weights = {m["id"]: m["weight"] for m in NIS2_SECURITY_MEASURES}

        for response in responses:
            weight = measure_weights.get(response.measure_id, 10)
            total_weight += weight

            if response.status == NIS2MeasureStatus.FULLY_IMPLEMENTED:
                weighted_score += weight
            elif response.status == NIS2MeasureStatus.PARTIALLY_IMPLEMENTED:
                weighted_score += weight * (response.implementation_level / 100)
                gaps_count += 1
            elif response.status == NIS2MeasureStatus.NOT_APPLICABLE:
                total_weight -= weight  # Don't count N/A in total
            elif response.status in [NIS2MeasureStatus.NOT_IMPLEMENTED, NIS2MeasureStatus.NOT_EVALUATED]:
                gaps_count += 1
                if weight >= 12:  # High-weight measures are critical
                    critical_gaps_count += 1

        # Calculate percentage
        overall_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0

        # Update assessment
        result = await self.db.execute(
            select(NIS2Assessment).where(NIS2Assessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment:
            assessment.overall_score = round(overall_score, 1)
            assessment.gaps_count = gaps_count
            assessment.critical_gaps_count = critical_gaps_count

    # ============== Gap Analysis ==============

    async def get_gap_analysis(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get gap analysis for an assessment."""
        data = await self.get_assessment_with_responses(assessment_id, tenant_id)
        if not data:
            return None

        assessment = data["assessment"]
        responses = data["measure_responses"]

        gaps = []
        measure_info = {m["id"]: m for m in NIS2_SECURITY_MEASURES}

        for response in responses:
            if response.status in [
                NIS2MeasureStatus.NOT_IMPLEMENTED,
                NIS2MeasureStatus.PARTIALLY_IMPLEMENTED,
                NIS2MeasureStatus.NOT_EVALUATED,
            ]:
                measure = measure_info.get(response.measure_id, {})
                weight = measure.get("weight", 10)

                # Calculate impact score
                if response.status == NIS2MeasureStatus.NOT_IMPLEMENTED:
                    impact = weight
                elif response.status == NIS2MeasureStatus.PARTIALLY_IMPLEMENTED:
                    impact = weight * (1 - response.implementation_level / 100)
                else:
                    impact = weight * 0.8  # Not evaluated treated as high impact

                priority = response.priority or (1 if weight >= 12 else 2 if weight >= 8 else 3)

                gaps.append(GapItem(
                    measure_id=response.measure_id,
                    measure_name=measure.get("name_en", response.measure_id),
                    status=response.status,
                    implementation_level=response.implementation_level,
                    gap_description=response.gap_description,
                    remediation_plan=response.remediation_plan,
                    priority=priority,
                    weight=weight,
                    impact_score=round(impact, 1),
                ))

        # Sort by priority and impact
        gaps.sort(key=lambda x: (x.priority, -x.impact_score))

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        return {
            "assessment_id": assessment_id,
            "total_gaps": len(gaps),
            "critical_gaps": len([g for g in gaps if g.priority == 1]),
            "high_priority_gaps": len([g for g in gaps if g.priority <= 2]),
            "gaps": gaps,
            "recommendations": recommendations,
        }

    def _generate_recommendations(
        self, gaps: List[GapItem], assessment: NIS2Assessment
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        if not gaps:
            recommendations.append("Congratulations! No significant gaps identified. Maintain current security posture and conduct regular reviews.")
            return recommendations

        # Priority-based recommendations
        critical_gaps = [g for g in gaps if g.priority == 1]
        if critical_gaps:
            recommendations.append(
                f"URGENT: Address {len(critical_gaps)} critical gap(s) immediately: "
                + ", ".join([g.measure_name for g in critical_gaps[:3]])
            )

        # Measure-specific recommendations
        gap_ids = {g.measure_id for g in gaps}

        if "NIS2-M02" in gap_ids:
            recommendations.append(
                "Implement incident handling procedures to meet NIS2 24-hour initial notification requirement."
            )

        if "NIS2-M01" in gap_ids:
            recommendations.append(
                "Develop comprehensive risk analysis and security policies as foundation for NIS2 compliance."
            )

        if "NIS2-M04" in gap_ids:
            recommendations.append(
                "Establish supply chain security program to assess and monitor third-party risks."
            )

        if "NIS2-M10" in gap_ids:
            recommendations.append(
                "Deploy multi-factor authentication for all critical systems and privileged access."
            )

        # General recommendations
        if assessment.entity_type == NIS2EntityType.ESSENTIAL:
            recommendations.append(
                "As an Essential Entity, prepare for proactive supervision by competent authorities."
            )

        if len(gaps) > 5:
            recommendations.append(
                "Consider engaging external consultants to accelerate remediation of multiple gaps."
            )

        return recommendations[:8]  # Limit to 8 recommendations

    # ============== Complete Assessment ==============

    async def complete_assessment(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[NIS2Assessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = NIS2AssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(assessment)
        return assessment

    # ============== Report Generation ==============

    async def generate_report(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate assessment report."""
        data = await self.get_assessment_with_responses(assessment_id, tenant_id)
        if not data:
            return None

        assessment = data["assessment"]
        responses = data["measure_responses"]
        classification = data["classification"]

        # Determine compliance level
        score = assessment.overall_score
        if score >= 80:
            compliance_level = "Compliant"
        elif score >= 50:
            compliance_level = "Partially Compliant"
        else:
            compliance_level = "Non-Compliant"

        # Build sections
        sections = []
        measure_info = {m["id"]: m for m in NIS2_SECURITY_MEASURES}

        for response in responses:
            measure = measure_info.get(response.measure_id, {})
            status_text = response.status.value.replace("_", " ").title()

            sections.append({
                "title": f"{response.measure_id}: {measure.get('name_en', '')}",
                "content": f"Status: {status_text}\nImplementation: {response.implementation_level}%\n"
                          + (f"Notes: {response.notes}" if response.notes else ""),
                "score": response.implementation_level,
                "status": status_text,
            })

        # Get gap analysis
        gap_data = await self.get_gap_analysis(assessment_id, tenant_id)
        gaps = gap_data["gaps"] if gap_data else []
        recommendations = gap_data["recommendations"] if gap_data else []

        # Next steps
        next_steps = [
            "Review and prioritize identified gaps",
            "Develop remediation plan with timelines",
            "Assign responsibilities for each remediation action",
            "Implement monitoring for NIS2 compliance",
            "Schedule follow-up assessment in 3-6 months",
        ]

        if assessment.entity_type == NIS2EntityType.ESSENTIAL:
            next_steps.insert(0, "Register with national competent authority if not already done")

        return {
            "assessment_id": assessment_id,
            "organization_name": assessment.name,
            "generated_at": datetime.utcnow(),
            "executive_summary": self._generate_executive_summary(assessment, compliance_level, len(gaps)),
            "entity_classification": classification,
            "overall_score": assessment.overall_score,
            "compliance_level": compliance_level,
            "sections": sections,
            "gaps": gaps,
            "recommendations": recommendations,
            "next_steps": next_steps,
        }

    def _generate_executive_summary(
        self, assessment: NIS2Assessment, compliance_level: str, gap_count: int
    ) -> str:
        """Generate executive summary for report."""
        entity_type = assessment.entity_type.value if assessment.entity_type else "unknown"
        sector = assessment.sector.value if assessment.sector else "unknown"

        summary = (
            f"This NIS2 compliance assessment evaluates {assessment.name} against the "
            f"requirements of the EU Network and Information Security Directive 2 (NIS2). "
            f"\n\n"
            f"The organization operates in the {sector} sector and has been classified as an "
            f"{entity_type.title()} Entity under NIS2. "
            f"\n\n"
            f"Overall compliance score: {assessment.overall_score:.1f}% ({compliance_level}). "
            f"\n\n"
        )

        if gap_count > 0:
            summary += (
                f"The assessment identified {gap_count} gap(s) requiring attention. "
                f"Of these, {assessment.critical_gaps_count} are considered critical priority. "
                f"Immediate action is recommended to address these gaps before the NIS2 "
                f"enforcement deadline."
            )
        else:
            summary += (
                "The assessment found no significant compliance gaps. The organization "
                "demonstrates strong alignment with NIS2 requirements. Continued monitoring "
                "and regular reassessment is recommended to maintain compliance."
            )

        return summary

    # ============== Dashboard Statistics ==============

    async def get_dashboard_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for all assessments."""
        # Get all assessments for tenant
        result = await self.db.execute(
            select(NIS2Assessment).where(NIS2Assessment.tenant_id == tenant_id)
        )
        assessments = result.scalars().all()

        if not assessments:
            return {
                "total_assessments": 0,
                "completed_assessments": 0,
                "average_score": 0,
                "total_gaps": 0,
                "critical_gaps": 0,
                "by_status": {
                    "draft": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "archived": 0,
                },
                "by_entity_type": {
                    "essential": 0,
                    "important": 0,
                    "out_of_scope": 0,
                },
                "by_sector": [],
                "recent_assessments": [],
                "compliance_trend": [],
            }

        # Calculate statistics
        total = len(assessments)
        completed = sum(1 for a in assessments if a.status == NIS2AssessmentStatus.COMPLETED)

        # Score calculation (only for assessments with scores)
        scored_assessments = [a for a in assessments if a.overall_score is not None and a.overall_score > 0]
        avg_score = sum(a.overall_score for a in scored_assessments) / len(scored_assessments) if scored_assessments else 0

        total_gaps = sum(a.gaps_count or 0 for a in assessments)
        critical_gaps = sum(a.critical_gaps_count or 0 for a in assessments)

        # By status
        by_status = {
            "draft": sum(1 for a in assessments if a.status == NIS2AssessmentStatus.DRAFT),
            "in_progress": sum(1 for a in assessments if a.status == NIS2AssessmentStatus.IN_PROGRESS),
            "completed": completed,
            "archived": sum(1 for a in assessments if a.status == NIS2AssessmentStatus.ARCHIVED),
        }

        # By entity type
        by_entity_type = {
            "essential": sum(1 for a in assessments if a.entity_type == NIS2EntityType.ESSENTIAL),
            "important": sum(1 for a in assessments if a.entity_type == NIS2EntityType.IMPORTANT),
            "out_of_scope": sum(1 for a in assessments if a.entity_type == NIS2EntityType.OUT_OF_SCOPE),
        }

        # By sector
        sector_counts = {}
        for a in assessments:
            if a.sector:
                sector_name = a.sector.value
                if sector_name not in sector_counts:
                    sector_counts[sector_name] = {"sector": sector_name, "count": 0, "avg_score": 0, "scores": []}
                sector_counts[sector_name]["count"] += 1
                if a.overall_score:
                    sector_counts[sector_name]["scores"].append(a.overall_score)

        by_sector = []
        for sector_data in sector_counts.values():
            scores = sector_data["scores"]
            by_sector.append({
                "sector": sector_data["sector"],
                "count": sector_data["count"],
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            })
        by_sector.sort(key=lambda x: x["count"], reverse=True)

        # Recent assessments (last 5)
        recent = sorted(assessments, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        recent_assessments = [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status.value,
                "entity_type": a.entity_type.value if a.entity_type else None,
                "overall_score": a.overall_score,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent
        ]

        # Compliance trend (completed assessments over time)
        completed_assessments = [a for a in assessments if a.completed_at]
        completed_assessments.sort(key=lambda x: x.completed_at)
        compliance_trend = [
            {
                "date": a.completed_at.strftime("%Y-%m-%d") if a.completed_at else None,
                "score": a.overall_score,
                "name": a.name,
            }
            for a in completed_assessments[-10:]  # Last 10 completed
        ]

        return {
            "total_assessments": total,
            "completed_assessments": completed,
            "average_score": round(avg_score, 1),
            "total_gaps": total_gaps,
            "critical_gaps": critical_gaps,
            "by_status": by_status,
            "by_entity_type": by_entity_type,
            "by_sector": by_sector,
            "recent_assessments": recent_assessments,
            "compliance_trend": compliance_trend,
        }
