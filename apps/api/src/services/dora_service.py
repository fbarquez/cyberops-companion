"""DORA Assessment Wizard service."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.dora import (
    DORAAssessment, DORARequirementResponse,
    DORAPillar, DORAEntityType, DORACompanySize,
    DORAAssessmentStatus, DORARequirementStatus,
    DORA_REQUIREMENTS, DORA_PILLARS_METADATA, ENTITY_TYPE_METADATA
)
from src.schemas.dora import (
    AssessmentCreate, AssessmentScopeUpdate, RequirementResponseCreate,
    ScopeResult, GapItem, PillarInfo, EntityTypeInfo, RequirementInfo,
    PillarGapSummary
)

logger = logging.getLogger(__name__)


class DORAAssessmentService:
    """Service for DORA assessment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Reference Data ==============

    def get_pillars_info(self) -> Dict[str, Any]:
        """Get all DORA pillars with metadata."""
        pillars = []
        total_weight = 0

        for pillar in DORAPillar:
            meta = DORA_PILLARS_METADATA.get(pillar, {})
            req_count = len([r for r in DORA_REQUIREMENTS if r["pillar"] == pillar])

            pillars.append(PillarInfo(
                pillar=pillar,
                name_en=meta.get("name_en", pillar.value),
                name_de=meta.get("name_de", pillar.value),
                article_range=meta.get("article_range", ""),
                weight=meta.get("weight", 20),
                icon=meta.get("icon", "shield"),
                description_en=meta.get("description_en", ""),
                requirement_count=req_count,
            ))
            total_weight += meta.get("weight", 20)

        return {"pillars": pillars, "total_weight": total_weight}

    def get_entity_types_info(self) -> Dict[str, Any]:
        """Get all DORA entity types with metadata."""
        entity_types = []

        for entity_type in DORAEntityType:
            meta = ENTITY_TYPE_METADATA.get(entity_type, {})
            entity_types.append(EntityTypeInfo(
                entity_type=entity_type,
                name_en=meta.get("name_en", entity_type.value),
                name_de=meta.get("name_de", entity_type.value),
                icon=meta.get("icon", "building"),
                requires_tlpt=meta.get("requires_tlpt", False),
                description_en=meta.get("description_en", ""),
            ))

        return {"entity_types": entity_types}

    def get_requirements_info(self) -> Dict[str, Any]:
        """Get all DORA requirements."""
        requirements = []
        by_pillar: Dict[str, List[RequirementInfo]] = {}

        for r in DORA_REQUIREMENTS:
            req_info = RequirementInfo(
                id=r["id"],
                pillar=r["pillar"],
                article=r["article"],
                name_en=r["name_en"],
                name_de=r["name_de"],
                description_en=r["description_en"],
                weight=r["weight"],
                sub_requirements=r["sub_requirements"],
            )
            requirements.append(req_info)

            pillar_key = r["pillar"].value
            if pillar_key not in by_pillar:
                by_pillar[pillar_key] = []
            by_pillar[pillar_key].append(req_info)

        return {
            "requirements": requirements,
            "by_pillar": by_pillar,
            "total_count": len(requirements),
        }

    # ============== Assessment CRUD ==============

    async def create_assessment(
        self, data: AssessmentCreate, user_id: str, tenant_id: str
    ) -> DORAAssessment:
        """Create a new DORA assessment."""
        assessment = DORAAssessment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=DORAAssessmentStatus.DRAFT,
            created_by=user_id,
            started_at=datetime.utcnow(),
            pillar_scores={},
        )
        self.db.add(assessment)
        await self.db.flush()
        await self.db.refresh(assessment)

        # Initialize requirement responses
        for req in DORA_REQUIREMENTS:
            response = DORARequirementResponse(
                id=str(uuid4()),
                assessment_id=assessment.id,
                requirement_id=req["id"],
                pillar=req["pillar"],
                status=DORARequirementStatus.NOT_EVALUATED,
                sub_requirements_status=[
                    {"name": sub_req, "implemented": False, "notes": None}
                    for sub_req in req["sub_requirements"]
                ],
            )
            self.db.add(response)

        await self.db.flush()
        return assessment

    async def get_assessment(self, assessment_id: str, tenant_id: str) -> Optional[DORAAssessment]:
        """Get assessment by ID."""
        result = await self.db.execute(
            select(DORAAssessment).where(
                and_(
                    DORAAssessment.id == assessment_id,
                    DORAAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_assessment_with_responses(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get assessment with all requirement responses."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get requirement responses
        result = await self.db.execute(
            select(DORARequirementResponse).where(
                DORARequirementResponse.assessment_id == assessment_id
            ).order_by(DORARequirementResponse.requirement_id)
        )
        responses = result.scalars().all()

        # Group responses by pillar
        responses_by_pillar: Dict[str, List] = {}
        for response in responses:
            pillar_key = response.pillar.value
            if pillar_key not in responses_by_pillar:
                responses_by_pillar[pillar_key] = []
            responses_by_pillar[pillar_key].append(response)

        # Build scope result if entity type is set
        scope_result = None
        if assessment.entity_type:
            scope_result = self._build_scope_result(assessment)

        return {
            "assessment": assessment,
            "requirement_responses": list(responses),
            "responses_by_pillar": responses_by_pillar,
            "scope_result": scope_result,
        }

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[DORAAssessmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[DORAAssessment], int]:
        """List assessments for a tenant."""
        query = select(DORAAssessment).where(DORAAssessment.tenant_id == tenant_id)

        if status:
            query = query.where(DORAAssessment.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Get page
        query = query.order_by(DORAAssessment.created_at.desc())
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
    ) -> Optional[DORAAssessment]:
        """Update assessment scope (Wizard Step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.entity_type = data.entity_type
        assessment.company_size = data.company_size
        assessment.employee_count = data.employee_count
        assessment.annual_balance_eur = data.annual_balance_eur
        assessment.is_ctpp = data.is_ctpp
        assessment.operates_in_eu = data.operates_in_eu
        assessment.eu_member_states = data.eu_member_states
        assessment.supervised_by = data.supervised_by
        assessment.group_level_assessment = data.group_level_assessment

        # Determine if simplified framework applies (Art. 16)
        assessment.simplified_framework = (
            data.company_size == DORACompanySize.MICRO and
            data.entity_type not in [
                DORAEntityType.CREDIT_INSTITUTION,
                DORAEntityType.CENTRAL_COUNTERPARTY,
                DORAEntityType.CENTRAL_SECURITIES_DEPOSITORY,
            ]
        )

        assessment.status = DORAAssessmentStatus.IN_PROGRESS

        await self.db.flush()
        await self.db.refresh(assessment)
        return assessment

    def _build_scope_result(self, assessment: DORAAssessment) -> ScopeResult:
        """Build scope result from assessment."""
        entity_meta = ENTITY_TYPE_METADATA.get(assessment.entity_type, {})
        requires_tlpt = entity_meta.get("requires_tlpt", False)

        # All pillars apply to all entities (with some variations)
        applicable_pillars = [p.value for p in DORAPillar]

        # Key obligations based on entity type
        key_obligations = [
            "Establish ICT risk management framework (Art. 5-16)",
            "Implement incident reporting procedures (Art. 17-23)",
            "Conduct regular resilience testing (Art. 24-27)",
            "Manage ICT third-party risks (Art. 28-44)",
            "Consider information sharing arrangements (Art. 45)",
        ]

        if requires_tlpt:
            key_obligations.append("Perform Threat-Led Penetration Testing (TLPT) every 3 years (Art. 26)")

        if assessment.is_ctpp:
            key_obligations.append("Subject to EU oversight framework for critical third-party providers")

        if assessment.simplified_framework:
            key_obligations = [
                "Simplified ICT risk management framework (Art. 16)",
                "Basic incident reporting requirements",
                "Proportionate testing requirements",
            ]

        # Reporting timelines for incidents
        reporting_timelines = {
            "initial_notification": "4 hours (for major incidents)",
            "intermediate_report": "72 hours",
            "final_report": "1 month",
            "voluntary_notification": "As appropriate for significant cyber threats",
        }

        return ScopeResult(
            entity_type=assessment.entity_type,
            entity_type_name=entity_meta.get("name_en", assessment.entity_type.value),
            requires_tlpt=requires_tlpt,
            simplified_framework=assessment.simplified_framework,
            is_ctpp=assessment.is_ctpp,
            applicable_pillars=applicable_pillars,
            key_obligations=key_obligations,
            reporting_timelines=reporting_timelines,
        )

    # ============== Requirement Responses ==============

    async def update_requirement_response(
        self,
        assessment_id: str,
        tenant_id: str,
        data: RequirementResponseCreate,
        user_id: str,
    ) -> Optional[DORARequirementResponse]:
        """Update a requirement response."""
        # Verify assessment ownership
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get or create response
        result = await self.db.execute(
            select(DORARequirementResponse).where(
                and_(
                    DORARequirementResponse.assessment_id == assessment_id,
                    DORARequirementResponse.requirement_id == data.requirement_id,
                )
            )
        )
        response = result.scalar_one_or_none()

        if not response:
            # Find pillar for this requirement
            req_info = next((r for r in DORA_REQUIREMENTS if r["id"] == data.requirement_id), None)
            if not req_info:
                return None

            response = DORARequirementResponse(
                id=str(uuid4()),
                assessment_id=assessment_id,
                requirement_id=data.requirement_id,
                pillar=req_info["pillar"],
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

    async def bulk_update_requirements(
        self,
        assessment_id: str,
        tenant_id: str,
        responses: List[RequirementResponseCreate],
        user_id: str,
        pillar: Optional[DORAPillar] = None,
    ) -> List[DORARequirementResponse]:
        """Bulk update requirement responses, optionally filtered by pillar."""
        results = []
        for data in responses:
            # If pillar filter is specified, only update matching requirements
            if pillar:
                req_info = next((r for r in DORA_REQUIREMENTS if r["id"] == data.requirement_id), None)
                if not req_info or req_info["pillar"] != pillar:
                    continue

            response = await self.update_requirement_response(
                assessment_id, tenant_id, data, user_id
            )
            if response:
                results.append(response)
        return results

    async def _recalculate_scores(self, assessment_id: str):
        """Recalculate assessment scores based on requirement responses."""
        # Get all responses
        result = await self.db.execute(
            select(DORARequirementResponse).where(
                DORARequirementResponse.assessment_id == assessment_id
            )
        )
        responses = result.scalars().all()

        # Build requirement weight map
        req_weights = {r["id"]: r["weight"] for r in DORA_REQUIREMENTS}
        req_pillars = {r["id"]: r["pillar"] for r in DORA_REQUIREMENTS}

        # Calculate overall and per-pillar scores
        total_weight = 0
        weighted_score = 0
        gaps_count = 0
        critical_gaps_count = 0

        pillar_totals: Dict[str, Dict[str, float]] = {}
        for pillar in DORAPillar:
            pillar_totals[pillar.value] = {"weight": 0, "score": 0}

        for response in responses:
            weight = req_weights.get(response.requirement_id, 10)
            pillar = req_pillars.get(response.requirement_id)
            pillar_key = pillar.value if pillar else "unknown"

            if response.status == DORARequirementStatus.FULLY_IMPLEMENTED:
                weighted_score += weight
                pillar_totals[pillar_key]["score"] += weight
            elif response.status == DORARequirementStatus.PARTIALLY_IMPLEMENTED:
                partial = weight * (response.implementation_level / 100)
                weighted_score += partial
                pillar_totals[pillar_key]["score"] += partial
                gaps_count += 1
            elif response.status == DORARequirementStatus.NOT_APPLICABLE:
                # Don't count N/A in totals
                continue
            elif response.status in [DORARequirementStatus.NOT_IMPLEMENTED, DORARequirementStatus.NOT_EVALUATED]:
                gaps_count += 1
                if weight >= 12:  # High-weight requirements are critical
                    critical_gaps_count += 1

            total_weight += weight
            pillar_totals[pillar_key]["weight"] += weight

        # Calculate overall percentage
        overall_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0

        # Calculate pillar scores
        pillar_scores = {}
        for pillar_key, data in pillar_totals.items():
            if data["weight"] > 0:
                pillar_scores[pillar_key] = round(data["score"] / data["weight"] * 100, 1)
            else:
                pillar_scores[pillar_key] = 0

        # Update assessment
        result = await self.db.execute(
            select(DORAAssessment).where(DORAAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment:
            assessment.overall_score = round(overall_score, 1)
            assessment.pillar_scores = pillar_scores
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
        responses = data["requirement_responses"]

        gaps = []
        req_info_map = {r["id"]: r for r in DORA_REQUIREMENTS}

        # Group gaps by pillar
        gaps_by_pillar: Dict[str, List[GapItem]] = {p.value: [] for p in DORAPillar}

        for response in responses:
            if response.status in [
                DORARequirementStatus.NOT_IMPLEMENTED,
                DORARequirementStatus.PARTIALLY_IMPLEMENTED,
                DORARequirementStatus.NOT_EVALUATED,
            ]:
                req = req_info_map.get(response.requirement_id, {})
                weight = req.get("weight", 10)

                # Calculate impact score
                if response.status == DORARequirementStatus.NOT_IMPLEMENTED:
                    impact = weight
                elif response.status == DORARequirementStatus.PARTIALLY_IMPLEMENTED:
                    impact = weight * (1 - response.implementation_level / 100)
                else:
                    impact = weight * 0.8  # Not evaluated treated as high impact

                priority = response.priority or (1 if weight >= 12 else 2 if weight >= 8 else 3)

                gap_item = GapItem(
                    requirement_id=response.requirement_id,
                    requirement_name=req.get("name_en", response.requirement_id),
                    pillar=response.pillar,
                    article=req.get("article", ""),
                    status=response.status,
                    implementation_level=response.implementation_level,
                    gap_description=response.gap_description,
                    remediation_plan=response.remediation_plan,
                    priority=priority,
                    weight=weight,
                    impact_score=round(impact, 1),
                )
                gaps.append(gap_item)
                gaps_by_pillar[response.pillar.value].append(gap_item)

        # Sort by priority and impact
        gaps.sort(key=lambda x: (x.priority, -x.impact_score))

        # Build pillar summaries
        pillar_summaries = []
        for pillar in DORAPillar:
            pillar_meta = DORA_PILLARS_METADATA.get(pillar, {})
            pillar_reqs = [r for r in DORA_REQUIREMENTS if r["pillar"] == pillar]
            pillar_gaps = gaps_by_pillar.get(pillar.value, [])
            pillar_score = assessment.pillar_scores.get(pillar.value, 0) if assessment.pillar_scores else 0

            pillar_summaries.append(PillarGapSummary(
                pillar=pillar,
                pillar_name=pillar_meta.get("name_en", pillar.value),
                total_requirements=len(pillar_reqs),
                gaps_count=len(pillar_gaps),
                critical_gaps=len([g for g in pillar_gaps if g.priority == 1]),
                score=pillar_score,
                gap_items=pillar_gaps,
            ))

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        return {
            "assessment_id": assessment_id,
            "total_gaps": len(gaps),
            "critical_gaps": len([g for g in gaps if g.priority == 1]),
            "high_priority_gaps": len([g for g in gaps if g.priority <= 2]),
            "gaps_by_pillar": {p.value: len(gaps_by_pillar[p.value]) for p in DORAPillar},
            "pillar_summaries": pillar_summaries,
            "all_gaps": gaps,
            "recommendations": recommendations,
        }

    def _generate_recommendations(
        self, gaps: List[GapItem], assessment: DORAAssessment
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        if not gaps:
            recommendations.append(
                "Excellent! No significant gaps identified. Maintain current operational resilience posture "
                "and conduct regular reviews in accordance with DORA requirements."
            )
            return recommendations

        # Priority-based recommendations
        critical_gaps = [g for g in gaps if g.priority == 1]
        if critical_gaps:
            recommendations.append(
                f"URGENT: Address {len(critical_gaps)} critical gap(s) immediately: "
                + ", ".join([g.requirement_name for g in critical_gaps[:3]])
            )

        # Pillar-specific recommendations
        pillar_gaps = {}
        for gap in gaps:
            pillar_key = gap.pillar.value
            if pillar_key not in pillar_gaps:
                pillar_gaps[pillar_key] = []
            pillar_gaps[pillar_key].append(gap)

        # ICT Risk Management gaps
        if "ict_risk_management" in pillar_gaps:
            p1_gaps = pillar_gaps["ict_risk_management"]
            if len(p1_gaps) >= 3:
                recommendations.append(
                    "Strengthen ICT risk management framework - multiple gaps identified in Pillar 1 (Art. 5-16). "
                    "Consider engaging specialized consultants."
                )

        # Incident Reporting gaps
        if "incident_reporting" in pillar_gaps:
            recommendations.append(
                "Implement robust incident classification and reporting procedures to meet DORA's "
                "4-hour initial notification requirement for major incidents."
            )

        # Resilience Testing gaps
        if "resilience_testing" in pillar_gaps:
            entity_meta = ENTITY_TYPE_METADATA.get(assessment.entity_type, {})
            if entity_meta.get("requires_tlpt", False):
                recommendations.append(
                    "As a significant entity, establish TLPT programme using TIBER-EU framework. "
                    "Plan for first TLPT execution before January 2025 deadline."
                )
            else:
                recommendations.append(
                    "Develop comprehensive digital resilience testing programme including "
                    "vulnerability assessments and scenario-based testing."
                )

        # Third-Party Risk gaps
        if "third_party_risk" in pillar_gaps:
            recommendations.append(
                "Establish ICT third-party risk register and review contractual arrangements "
                "for compliance with DORA Art. 30 key provisions."
            )
            if len(pillar_gaps.get("third_party_risk", [])) >= 4:
                recommendations.append(
                    "High number of gaps in third-party risk management. Prioritize developing "
                    "exit strategies and concentration risk assessments."
                )

        # Information Sharing gaps
        if "information_sharing" in pillar_gaps:
            recommendations.append(
                "Consider joining financial sector information sharing arrangements (ISACs) "
                "to enhance cyber threat intelligence capabilities."
            )

        # CTPP-specific recommendation
        if assessment.is_ctpp:
            recommendations.append(
                "As a Critical Third-Party Provider (CTPP), prepare for EU oversight framework "
                "and lead overseer designation. Ensure compliance across all pillars."
            )

        # Simplified framework note
        if assessment.simplified_framework:
            recommendations.append(
                "As an eligible microenterprise, you may apply the simplified ICT risk management "
                "framework under Art. 16. Focus on proportionate measures."
            )

        return recommendations[:10]  # Limit to 10 recommendations

    # ============== Complete Assessment ==============

    async def complete_assessment(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[DORAAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = DORAAssessmentStatus.COMPLETED
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
        responses = data["requirement_responses"]
        scope_result = data["scope_result"]

        # Determine compliance level
        score = assessment.overall_score
        if score >= 85:
            compliance_level = "Fully Compliant"
        elif score >= 70:
            compliance_level = "Largely Compliant"
        elif score >= 50:
            compliance_level = "Partially Compliant"
        else:
            compliance_level = "Non-Compliant"

        # Build pillar summaries
        req_info_map = {r["id"]: r for r in DORA_REQUIREMENTS}
        pillar_summaries = []

        for pillar in DORAPillar:
            pillar_meta = DORA_PILLARS_METADATA.get(pillar, {})
            pillar_responses = [r for r in responses if r.pillar == pillar]
            pillar_score = assessment.pillar_scores.get(pillar.value, 0) if assessment.pillar_scores else 0

            implemented = sum(1 for r in pillar_responses if r.status == DORARequirementStatus.FULLY_IMPLEMENTED)
            partial = sum(1 for r in pillar_responses if r.status == DORARequirementStatus.PARTIALLY_IMPLEMENTED)
            gaps = sum(1 for r in pillar_responses if r.status in [
                DORARequirementStatus.NOT_IMPLEMENTED,
                DORARequirementStatus.NOT_EVALUATED,
            ])

            # Determine pillar compliance level
            if pillar_score >= 85:
                pillar_compliance = "Fully Compliant"
            elif pillar_score >= 70:
                pillar_compliance = "Largely Compliant"
            elif pillar_score >= 50:
                pillar_compliance = "Partially Compliant"
            else:
                pillar_compliance = "Non-Compliant"

            # Key findings for this pillar
            key_findings = []
            if implemented == len(pillar_responses):
                key_findings.append(f"All {pillar_meta.get('name_en', '')} requirements fully implemented")
            else:
                if gaps > 0:
                    key_findings.append(f"{gaps} requirement(s) not implemented or not evaluated")
                if partial > 0:
                    key_findings.append(f"{partial} requirement(s) partially implemented")

            pillar_summaries.append({
                "pillar": pillar,
                "pillar_name": pillar_meta.get("name_en", pillar.value),
                "article_range": pillar_meta.get("article_range", ""),
                "weight": pillar_meta.get("weight", 20),
                "score": pillar_score,
                "compliance_level": pillar_compliance,
                "requirements_count": len(pillar_responses),
                "implemented_count": implemented,
                "partial_count": partial,
                "gaps_count": gaps,
                "key_findings": key_findings,
            })

        # Get gap analysis
        gap_data = await self.get_gap_analysis(assessment_id, tenant_id)
        gaps = gap_data["all_gaps"] if gap_data else []
        recommendations = gap_data["recommendations"] if gap_data else []

        # Next steps
        next_steps = [
            "Review and prioritize identified gaps by pillar",
            "Develop remediation plan with specific timelines",
            "Assign ownership for each remediation action",
            "Establish ongoing monitoring for DORA compliance",
            "Schedule follow-up assessment in 6 months",
        ]

        entity_meta = ENTITY_TYPE_METADATA.get(assessment.entity_type, {})
        if entity_meta.get("requires_tlpt", False):
            next_steps.insert(0, "Plan and schedule TLPT within required timeframe")

        if assessment.is_ctpp:
            next_steps.insert(0, "Prepare for EU oversight framework requirements")

        # Regulatory deadlines
        regulatory_deadlines = {
            "dora_application": "January 17, 2025",
            "initial_tlpt": "Within 3 years of DORA application for significant entities",
            "register_of_information": "Annual update and submission to competent authority",
            "incident_reporting": "4h initial / 72h intermediate / 1 month final",
        }

        return {
            "assessment_id": assessment_id,
            "organization_name": assessment.name,
            "generated_at": datetime.utcnow(),
            "executive_summary": self._generate_executive_summary(assessment, compliance_level, len(gaps)),
            "entity_type": assessment.entity_type,
            "entity_type_name": entity_meta.get("name_en", ""),
            "is_ctpp": assessment.is_ctpp,
            "requires_tlpt": entity_meta.get("requires_tlpt", False),
            "simplified_framework": assessment.simplified_framework,
            "overall_score": assessment.overall_score,
            "compliance_level": compliance_level,
            "pillar_summaries": pillar_summaries,
            "gaps": gaps,
            "recommendations": recommendations,
            "next_steps": next_steps,
            "regulatory_deadlines": regulatory_deadlines,
        }

    def _generate_executive_summary(
        self, assessment: DORAAssessment, compliance_level: str, gap_count: int
    ) -> str:
        """Generate executive summary for report."""
        entity_meta = ENTITY_TYPE_METADATA.get(assessment.entity_type, {})
        entity_type_name = entity_meta.get("name_en", str(assessment.entity_type.value) if assessment.entity_type else "unknown")

        summary = (
            f"This DORA (Digital Operational Resilience Act) compliance assessment evaluates {assessment.name} "
            f"against the requirements of EU Regulation 2022/2554. "
            f"\n\n"
            f"The organization is classified as a {entity_type_name} under DORA. "
        )

        if assessment.is_ctpp:
            summary += "Additionally, the organization is designated as a Critical Third-Party Provider (CTPP), subject to the EU oversight framework. "

        if assessment.simplified_framework:
            summary += "As an eligible microenterprise, the simplified ICT risk management framework under Article 16 applies. "

        summary += (
            f"\n\n"
            f"Overall compliance score: {assessment.overall_score:.1f}% ({compliance_level}). "
            f"\n\n"
        )

        if gap_count > 0:
            summary += (
                f"The assessment identified {gap_count} gap(s) requiring attention across the five DORA pillars. "
                f"Of these, {assessment.critical_gaps_count} are considered critical priority and should be "
                f"addressed before the January 2025 application deadline. "
                f"Immediate action is recommended to ensure operational resilience."
            )
        else:
            summary += (
                "The assessment found no significant compliance gaps. The organization demonstrates strong "
                "digital operational resilience aligned with DORA requirements. Continued monitoring and "
                "regular reassessment is recommended to maintain compliance."
            )

        return summary

    # ============== Dashboard Statistics ==============

    async def get_dashboard_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for all assessments."""
        # Get all assessments for tenant
        result = await self.db.execute(
            select(DORAAssessment).where(DORAAssessment.tenant_id == tenant_id)
        )
        assessments = result.scalars().all()

        if not assessments:
            return {
                "total_assessments": 0,
                "completed_assessments": 0,
                "in_progress_assessments": 0,
                "draft_assessments": 0,
                "average_score": 0,
                "total_gaps": 0,
                "critical_gaps": 0,
                "by_entity_type": {},
                "pillar_scores": {p.value: 0 for p in DORAPillar},
                "recent_assessments": [],
                "compliance_trend": [],
            }

        # Calculate statistics
        total = len(assessments)
        completed = sum(1 for a in assessments if a.status == DORAAssessmentStatus.COMPLETED)
        in_progress = sum(1 for a in assessments if a.status == DORAAssessmentStatus.IN_PROGRESS)
        draft = sum(1 for a in assessments if a.status == DORAAssessmentStatus.DRAFT)

        # Score calculation (only for assessments with scores)
        scored_assessments = [a for a in assessments if a.overall_score is not None and a.overall_score > 0]
        avg_score = sum(a.overall_score for a in scored_assessments) / len(scored_assessments) if scored_assessments else 0

        total_gaps = sum(a.gaps_count or 0 for a in assessments)
        critical_gaps = sum(a.critical_gaps_count or 0 for a in assessments)

        # By entity type
        by_entity_type = {}
        for a in assessments:
            if a.entity_type:
                key = a.entity_type.value
                by_entity_type[key] = by_entity_type.get(key, 0) + 1

        # Average pillar scores across all assessments
        pillar_scores: Dict[str, List[float]] = {p.value: [] for p in DORAPillar}
        for a in assessments:
            if a.pillar_scores:
                for pillar, score in a.pillar_scores.items():
                    if pillar in pillar_scores:
                        pillar_scores[pillar].append(score)

        avg_pillar_scores = {}
        for pillar, scores in pillar_scores.items():
            avg_pillar_scores[pillar] = round(sum(scores) / len(scores), 1) if scores else 0

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
            "in_progress_assessments": in_progress,
            "draft_assessments": draft,
            "average_score": round(avg_score, 1),
            "total_gaps": total_gaps,
            "critical_gaps": critical_gaps,
            "by_entity_type": by_entity_type,
            "pillar_scores": avg_pillar_scores,
            "recent_assessments": recent_assessments,
            "compliance_trend": compliance_trend,
        }

    # ============== Wizard State ==============

    async def get_wizard_state(
        self, assessment_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get wizard state for frontend."""
        data = await self.get_assessment_with_responses(assessment_id, tenant_id)
        if not data:
            return None

        assessment = data["assessment"]
        responses_by_pillar = data["responses_by_pillar"]

        # Determine completed steps
        steps_completed = []

        # Step 1: Scope - complete if entity_type is set
        if assessment.entity_type:
            steps_completed.append(1)

        # Steps 2-6: Pillars - complete if all requirements in pillar are evaluated
        pillar_order = [
            DORAPillar.ICT_RISK_MANAGEMENT,
            DORAPillar.INCIDENT_REPORTING,
            DORAPillar.RESILIENCE_TESTING,
            DORAPillar.THIRD_PARTY_RISK,
            DORAPillar.INFORMATION_SHARING,
        ]

        for i, pillar in enumerate(pillar_order):
            pillar_responses = responses_by_pillar.get(pillar.value, [])
            if pillar_responses:
                all_evaluated = all(
                    r.status != DORARequirementStatus.NOT_EVALUATED
                    for r in pillar_responses
                )
                if all_evaluated:
                    steps_completed.append(i + 2)  # Steps 2-6

        # Determine current step
        current_step = 1
        if 1 in steps_completed:
            current_step = 2
            for step in range(2, 7):
                if step in steps_completed:
                    current_step = step + 1
                else:
                    break
        current_step = min(current_step, 8)  # Max step is 8 (Report)

        step_names = [
            "Scope",
            "ICT Risk Management",
            "Incident Reporting",
            "Resilience Testing",
            "Third-Party Risk",
            "Information Sharing",
            "Gap Analysis",
            "Report",
        ]

        return {
            "current_step": current_step,
            "total_steps": 8,
            "assessment_id": assessment_id,
            "can_go_back": current_step > 1,
            "can_go_forward": 1 in steps_completed,
            "is_complete": assessment.status == DORAAssessmentStatus.COMPLETED,
            "steps_completed": steps_completed,
            "step_names": step_names,
        }
