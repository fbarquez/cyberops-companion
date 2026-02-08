"""
KRITIS Compliance Service

Business logic for KRITIS compliance assessments.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.kritis import (
    KRITISAssessment,
    KRITISRequirementResponse,
    KRITISSector,
    KRITISCompanySize,
    KRITISAssessmentStatus,
    KRITISRequirementStatus,
    KRITIS_SECTORS,
    KRITIS_REQUIREMENTS,
    KRITIS_CATEGORIES,
)
from src.schemas.kritis import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    RequirementResponseCreate,
    SectorInfo,
    SectorListResponse,
    RequirementInfo,
    CategoryInfo,
    RequirementsListResponse,
    AssessmentResponse,
    AssessmentDetailResponse,
    AssessmentListResponse,
    RequirementResponseResponse,
    GapItem,
    CategoryGapSummary,
    GapAnalysisResponse,
    DashboardStats,
    WizardState,
    AssessmentReportResponse,
)


class KRITISAssessmentService:
    """Service for KRITIS compliance assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Reference Data
    # =========================================================================

    def get_sectors_info(self) -> SectorListResponse:
        """Get list of KRITIS sectors."""
        sectors = []
        for sector, data in KRITIS_SECTORS.items():
            sectors.append(SectorInfo(
                sector=sector,
                name_en=data["name_en"],
                name_de=data["name_de"],
                icon=data["icon"],
                description_en=data["description_en"],
                description_de=data["description_de"],
                threshold_info=data["threshold_info"],
                subsectors=data["subsectors"],
            ))
        return SectorListResponse(sectors=sectors, total=len(sectors))

    def get_requirements_info(self, category: Optional[str] = None) -> RequirementsListResponse:
        """Get list of KRITIS requirements."""
        requirements = []
        for req in KRITIS_REQUIREMENTS:
            if category and req["category"] != category:
                continue
            requirements.append(RequirementInfo(
                id=req["id"],
                category=req["category"],
                article=req["article"],
                name_en=req["name_en"],
                name_de=req["name_de"],
                description_en=req["description_en"],
                description_de=req["description_de"],
                weight=req["weight"],
                sub_requirements=req["sub_requirements"],
            ))

        categories = []
        for cat_id, cat_data in KRITIS_CATEGORIES.items():
            req_count = len([r for r in KRITIS_REQUIREMENTS if r["category"] == cat_id])
            categories.append(CategoryInfo(
                id=cat_id,
                name_en=cat_data["name_en"],
                name_de=cat_data["name_de"],
                weight=cat_data["weight"],
                requirements_count=req_count,
            ))

        return RequirementsListResponse(
            requirements=requirements,
            categories=categories,
            total=len(requirements),
        )

    # =========================================================================
    # Assessment CRUD
    # =========================================================================

    async def create_assessment(
        self,
        data: AssessmentCreate,
        user_id: str,
        tenant_id: str,
    ) -> KRITISAssessment:
        """Create a new KRITIS assessment."""
        assessment = KRITISAssessment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=KRITISAssessmentStatus.DRAFT,
            created_by=user_id,
        )
        self.db.add(assessment)

        # Create empty requirement responses
        for req in KRITIS_REQUIREMENTS:
            response = KRITISRequirementResponse(
                id=str(uuid4()),
                assessment_id=assessment.id,
                requirement_id=req["id"],
                category=req["category"],
                status=KRITISRequirementStatus.NOT_EVALUATED,
                implementation_level=0,
                sub_requirements_status=[False] * len(req["sub_requirements"]),
            )
            self.db.add(response)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[KRITISAssessment]:
        """Get assessment by ID."""
        result = await self.db.execute(
            select(KRITISAssessment)
            .options(selectinload(KRITISAssessment.requirement_responses))
            .where(
                and_(
                    KRITISAssessment.id == assessment_id,
                    KRITISAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[KRITISAssessmentStatus] = None,
        sector: Optional[KRITISSector] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[KRITISAssessment], int]:
        """List assessments with pagination."""
        query = select(KRITISAssessment).where(
            KRITISAssessment.tenant_id == tenant_id
        )

        if status:
            query = query.where(KRITISAssessment.status == status)
        if sector:
            query = query.where(KRITISAssessment.sector == sector)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(KRITISAssessment.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    async def update_assessment_scope(
        self,
        assessment_id: str,
        data: AssessmentScopeUpdate,
        tenant_id: str,
    ) -> Optional[KRITISAssessment]:
        """Update assessment scope (wizard step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Update fields
        assessment.sector = data.sector
        assessment.subsector = data.subsector
        assessment.company_size = data.company_size
        assessment.employee_count = data.employee_count
        assessment.annual_revenue_eur = data.annual_revenue_eur
        assessment.operates_in_germany = data.operates_in_germany
        assessment.german_states = data.german_states
        assessment.bsi_registered = data.bsi_registered
        assessment.bsi_registration_date = data.bsi_registration_date
        assessment.bsi_contact_established = data.bsi_contact_established
        assessment.last_audit_date = data.last_audit_date
        assessment.next_audit_due = data.next_audit_due

        # Update status if still draft
        if assessment.status == KRITISAssessmentStatus.DRAFT:
            assessment.status = KRITISAssessmentStatus.IN_PROGRESS
            assessment.started_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def delete_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return False

        await self.db.delete(assessment)
        await self.db.commit()
        return True

    # =========================================================================
    # Requirement Responses
    # =========================================================================

    async def submit_requirement_response(
        self,
        assessment_id: str,
        data: RequirementResponseCreate,
        user_id: str,
        tenant_id: str,
    ) -> Optional[KRITISRequirementResponse]:
        """Submit or update a requirement response."""
        # Verify assessment exists and belongs to tenant
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find existing response
        result = await self.db.execute(
            select(KRITISRequirementResponse).where(
                and_(
                    KRITISRequirementResponse.assessment_id == assessment_id,
                    KRITISRequirementResponse.requirement_id == data.requirement_id,
                )
            )
        )
        response = result.scalar_one_or_none()

        if not response:
            return None

        # Update response
        response.status = data.status
        response.implementation_level = data.implementation_level
        response.sub_requirements_status = data.sub_requirements_status
        response.evidence = data.evidence
        response.notes = data.notes
        response.gap_description = data.gap_description
        response.remediation_plan = data.remediation_plan
        response.priority = data.priority
        response.due_date = data.due_date
        response.assessed_at = datetime.utcnow()
        response.assessed_by = user_id

        await self.db.commit()
        await self.db.refresh(response)

        # Recalculate scores
        await self._recalculate_scores(assessment_id)

        return response

    async def bulk_update_requirements(
        self,
        assessment_id: str,
        responses: List[RequirementResponseCreate],
        user_id: str,
        tenant_id: str,
    ) -> List[KRITISRequirementResponse]:
        """Bulk update requirement responses."""
        updated = []
        for resp_data in responses:
            response = await self.submit_requirement_response(
                assessment_id, resp_data, user_id, tenant_id
            )
            if response:
                updated.append(response)
        return updated

    # =========================================================================
    # Scoring & Analysis
    # =========================================================================

    async def _recalculate_scores(self, assessment_id: str) -> None:
        """Recalculate assessment scores."""
        result = await self.db.execute(
            select(KRITISRequirementResponse).where(
                KRITISRequirementResponse.assessment_id == assessment_id
            )
        )
        responses = result.scalars().all()

        # Calculate category scores
        category_scores = {}
        category_weights = {}
        gaps_count = 0
        critical_gaps_count = 0

        for resp in responses:
            cat = resp.category
            req = next((r for r in KRITIS_REQUIREMENTS if r["id"] == resp.requirement_id), None)
            if not req:
                continue

            weight = req["weight"]
            if cat not in category_scores:
                category_scores[cat] = 0
                category_weights[cat] = 0

            category_weights[cat] += weight

            if resp.status == KRITISRequirementStatus.FULLY_IMPLEMENTED:
                category_scores[cat] += weight * 100
            elif resp.status == KRITISRequirementStatus.PARTIALLY_IMPLEMENTED:
                category_scores[cat] += weight * resp.implementation_level
            elif resp.status == KRITISRequirementStatus.NOT_APPLICABLE:
                category_weights[cat] -= weight  # Don't count N/A

            # Count gaps
            if resp.status in [
                KRITISRequirementStatus.NOT_IMPLEMENTED,
                KRITISRequirementStatus.PARTIALLY_IMPLEMENTED,
            ]:
                gaps_count += 1
                if resp.priority == 1 or weight >= 12:
                    critical_gaps_count += 1

        # Calculate normalized category scores
        normalized_scores = {}
        for cat, score in category_scores.items():
            if category_weights.get(cat, 0) > 0:
                normalized_scores[cat] = round(score / category_weights[cat], 1)
            else:
                normalized_scores[cat] = 100.0  # All N/A

        # Calculate overall score
        total_weight = sum(category_weights.values())
        if total_weight > 0:
            overall_score = sum(category_scores.values()) / total_weight
        else:
            overall_score = 0

        # Update assessment
        result = await self.db.execute(
            select(KRITISAssessment).where(KRITISAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment:
            assessment.overall_score = round(overall_score, 1)
            assessment.category_scores = normalized_scores
            assessment.gaps_count = gaps_count
            assessment.critical_gaps_count = critical_gaps_count
            await self.db.commit()

    async def get_gap_analysis(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[GapAnalysisResponse]:
        """Get gap analysis for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        gaps = []
        category_summaries = {cat: {
            "total": 0,
            "fully": 0,
            "partial": 0,
            "not_impl": 0,
            "not_eval": 0,
            "score": 0,
        } for cat in KRITIS_CATEGORIES}

        for resp in assessment.requirement_responses:
            req = next((r for r in KRITIS_REQUIREMENTS if r["id"] == resp.requirement_id), None)
            if not req:
                continue

            cat = resp.category
            category_summaries[cat]["total"] += 1

            if resp.status == KRITISRequirementStatus.FULLY_IMPLEMENTED:
                category_summaries[cat]["fully"] += 1
            elif resp.status == KRITISRequirementStatus.PARTIALLY_IMPLEMENTED:
                category_summaries[cat]["partial"] += 1
            elif resp.status == KRITISRequirementStatus.NOT_IMPLEMENTED:
                category_summaries[cat]["not_impl"] += 1
            else:
                category_summaries[cat]["not_eval"] += 1

            # Add to gaps list if not fully implemented
            if resp.status in [
                KRITISRequirementStatus.NOT_IMPLEMENTED,
                KRITISRequirementStatus.PARTIALLY_IMPLEMENTED,
                KRITISRequirementStatus.NOT_EVALUATED,
            ]:
                priority = resp.priority or (1 if req["weight"] >= 12 else 2 if req["weight"] >= 8 else 3)
                gaps.append(GapItem(
                    requirement_id=resp.requirement_id,
                    requirement_name=req["name_en"],
                    category=resp.category,
                    article=req["article"],
                    status=resp.status,
                    implementation_level=resp.implementation_level,
                    gap_description=resp.gap_description,
                    priority=priority,
                    weight=req["weight"],
                    impact_score=req["weight"] * (100 - resp.implementation_level) / 100,
                    remediation_plan=resp.remediation_plan,
                    due_date=resp.due_date,
                ))

        # Sort gaps by priority and weight
        gaps.sort(key=lambda g: (g.priority, -g.weight))

        # Build category summaries
        cat_summary_list = []
        for cat_id, cat_data in KRITIS_CATEGORIES.items():
            summary = category_summaries[cat_id]
            if summary["total"] > 0:
                score = (summary["fully"] * 100 + summary["partial"] * 50) / summary["total"]
            else:
                score = 0
            cat_summary_list.append(CategoryGapSummary(
                category=cat_id,
                name_en=cat_data["name_en"],
                name_de=cat_data["name_de"],
                total_requirements=summary["total"],
                fully_implemented=summary["fully"],
                partially_implemented=summary["partial"],
                not_implemented=summary["not_impl"],
                not_evaluated=summary["not_eval"],
                score=round(score, 1),
            ))

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        return GapAnalysisResponse(
            assessment_id=assessment.id,
            assessment_name=assessment.name,
            sector=assessment.sector,
            overall_score=assessment.overall_score,
            total_gaps=len([g for g in gaps if g.status != KRITISRequirementStatus.NOT_EVALUATED]),
            critical_gaps=len([g for g in gaps if g.priority == 1]),
            gaps_by_category=cat_summary_list,
            gaps=gaps,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
        )

    def _generate_recommendations(
        self,
        gaps: List[GapItem],
        assessment: KRITISAssessment,
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        # Check critical gaps
        critical_gaps = [g for g in gaps if g.priority == 1]
        if critical_gaps:
            recommendations.append(
                f"Prioritize {len(critical_gaps)} critical gaps that pose significant compliance risk."
            )

        # Check BSI registration
        if not assessment.bsi_registered:
            recommendations.append(
                "Complete BSI registration as required for KRITIS operators."
            )

        # Check BSI contact
        if not assessment.bsi_contact_established:
            recommendations.append(
                "Establish contact with BSI for incident reporting and coordination."
            )

        # Check audit status
        if assessment.next_audit_due:
            days_until_audit = (assessment.next_audit_due - datetime.utcnow()).days
            if days_until_audit < 180:
                recommendations.append(
                    f"Prepare for upcoming §8a audit in {days_until_audit} days."
                )

        # Category-specific recommendations
        category_gaps = {}
        for gap in gaps:
            if gap.category not in category_gaps:
                category_gaps[gap.category] = 0
            category_gaps[gap.category] += 1

        for cat, count in sorted(category_gaps.items(), key=lambda x: -x[1])[:3]:
            cat_name = KRITIS_CATEGORIES.get(cat, {}).get("name_en", cat)
            recommendations.append(
                f"Focus on {cat_name} area with {count} open requirements."
            )

        # Overall score recommendations
        if assessment.overall_score < 50:
            recommendations.append(
                "Overall compliance is below 50%. Consider engaging external consultants for rapid improvement."
            )
        elif assessment.overall_score < 75:
            recommendations.append(
                "Continue systematic implementation to reach target compliance level of 80%+."
            )

        return recommendations[:6]  # Limit to 6 recommendations

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard_stats(self, tenant_id: str) -> DashboardStats:
        """Get dashboard statistics."""
        # Get all assessments
        assessments, total = await self.list_assessments(tenant_id, page=1, size=1000)

        # Count by status
        by_status = {}
        by_sector = {}
        total_score = 0
        completed_count = 0
        in_progress_count = 0
        upcoming_audits = 0
        overdue_audits = 0
        now = datetime.utcnow()

        for a in assessments:
            status = a.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if a.sector:
                sector = a.sector.value
                by_sector[sector] = by_sector.get(sector, 0) + 1

            if a.status == KRITISAssessmentStatus.COMPLETED:
                completed_count += 1
                total_score += a.overall_score

            if a.status == KRITISAssessmentStatus.IN_PROGRESS:
                in_progress_count += 1

            if a.next_audit_due:
                if a.next_audit_due > now:
                    upcoming_audits += 1
                else:
                    overdue_audits += 1

        avg_score = total_score / completed_count if completed_count > 0 else 0

        # Get recent assessments
        recent = assessments[:5]

        return DashboardStats(
            total_assessments=total,
            completed_assessments=completed_count,
            in_progress_assessments=in_progress_count,
            average_score=round(avg_score, 1),
            assessments_by_sector=by_sector,
            assessments_by_status=by_status,
            upcoming_audits=upcoming_audits,
            overdue_audits=overdue_audits,
            recent_assessments=[AssessmentResponse.model_validate(a) for a in recent],
        )

    # =========================================================================
    # Wizard State
    # =========================================================================

    async def get_wizard_state(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[WizardState]:
        """Get wizard navigation state."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Check scope completion
        scope_completed = assessment.sector is not None

        # Check requirements by category
        requirements_completed = {}
        for cat in KRITIS_CATEGORIES:
            cat_responses = [
                r for r in assessment.requirement_responses
                if r.category == cat and r.status != KRITISRequirementStatus.NOT_EVALUATED
            ]
            cat_total = len([r for r in KRITIS_REQUIREMENTS if r["category"] == cat])
            requirements_completed[cat] = len(cat_responses) >= cat_total

        # Determine current step
        current_step = 1
        if scope_completed:
            current_step = 2
            for i, cat in enumerate(KRITIS_CATEGORIES.keys()):
                if not requirements_completed.get(cat, False):
                    current_step = i + 2
                    break
            else:
                current_step = len(KRITIS_CATEGORIES) + 2  # Gap analysis

        # Can complete if all requirements evaluated
        can_complete = scope_completed and all(requirements_completed.values())

        steps = [
            {"id": 1, "name": "Scope", "completed": scope_completed},
        ]
        for i, (cat_id, cat_data) in enumerate(KRITIS_CATEGORIES.items()):
            steps.append({
                "id": i + 2,
                "name": cat_data["name_en"],
                "category": cat_id,
                "completed": requirements_completed.get(cat_id, False),
            })
        steps.append({
            "id": len(KRITIS_CATEGORIES) + 2,
            "name": "Gap Analysis",
            "completed": assessment.status == KRITISAssessmentStatus.COMPLETED,
        })

        return WizardState(
            assessment_id=assessment.id,
            current_step=current_step,
            total_steps=len(steps),
            steps=steps,
            scope_completed=scope_completed,
            requirements_completed=requirements_completed,
            can_complete=can_complete,
        )

    # =========================================================================
    # Complete Assessment
    # =========================================================================

    async def complete_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[KRITISAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = KRITISAssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    # =========================================================================
    # Report Generation
    # =========================================================================

    async def generate_report(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[AssessmentReportResponse]:
        """Generate assessment report."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        gap_analysis = await self.get_gap_analysis(assessment_id, tenant_id)
        if not gap_analysis:
            return None

        # Determine compliance level
        score = assessment.overall_score
        if score >= 90:
            compliance_level = "Excellent"
        elif score >= 75:
            compliance_level = "Good"
        elif score >= 50:
            compliance_level = "Needs Improvement"
        else:
            compliance_level = "Critical"

        # Determine audit readiness
        if score >= 80 and assessment.bsi_registered:
            audit_readiness = "Ready for §8a audit"
        elif score >= 60:
            audit_readiness = "Partial readiness - address critical gaps first"
        else:
            audit_readiness = "Not ready - significant remediation needed"

        # Generate executive summary
        sector_name = KRITIS_SECTORS.get(assessment.sector, {}).get("name_en", "Unknown") if assessment.sector else "Not specified"
        exec_summary = (
            f"This KRITIS compliance assessment for the {sector_name} sector "
            f"achieved an overall score of {score}%. "
            f"There are {gap_analysis.total_gaps} gaps identified, "
            f"including {gap_analysis.critical_gaps} critical gaps requiring immediate attention."
        )

        # Key findings
        key_findings = []
        if not assessment.bsi_registered:
            key_findings.append("Organization is not registered with BSI as a KRITIS operator")
        if gap_analysis.critical_gaps > 0:
            key_findings.append(f"{gap_analysis.critical_gaps} critical compliance gaps identified")

        for cat_summary in gap_analysis.gaps_by_category:
            if cat_summary.not_implemented > 0:
                key_findings.append(
                    f"{cat_summary.name_en}: {cat_summary.not_implemented} requirements not implemented"
                )

        # Next steps
        next_steps = [
            "Address critical gaps within 30 days",
            "Complete BSI registration if not done",
            "Establish incident reporting process",
            "Schedule §8a compliance audit",
            "Implement continuous monitoring",
        ]

        return AssessmentReportResponse(
            assessment_id=assessment.id,
            organization_name=assessment.name,
            sector=assessment.sector,
            sector_name=sector_name,
            generated_at=datetime.utcnow(),
            executive_summary=exec_summary,
            overall_score=score,
            compliance_level=compliance_level,
            category_summaries=gap_analysis.gaps_by_category,
            key_findings=key_findings[:5],
            critical_gaps=[g for g in gap_analysis.gaps if g.priority == 1][:5],
            recommendations=gap_analysis.recommendations,
            next_steps=next_steps,
            audit_readiness=audit_readiness,
        )
