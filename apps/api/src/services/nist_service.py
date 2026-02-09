"""
NIST CSF 2.0 Service

Business logic for NIST assessment management.
"""

import uuid
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.nist import (
    NISTAssessment,
    NISTSubcategoryResponse,
    NISTFunction,
    NISTImplementationTier,
    NISTAssessmentStatus,
    NISTOutcomeStatus,
    NISTOrganizationType,
    NISTOrganizationSize,
    NIST_FUNCTIONS,
    NIST_CATEGORIES,
    NIST_SUBCATEGORIES,
    NIST_TIERS,
)
from src.schemas.nist import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    SubcategoryResponseCreate,
    FunctionInfo,
    CategoryInfo,
    SubcategoryInfo,
    TierInfo,
    FunctionListResponse,
    CategoryListResponse,
    SubcategoryListResponse,
    TierListResponse,
    GapItem,
    GapAnalysisResponse,
    FunctionSummary,
    DashboardStats,
    ImplementationDistribution,
    WizardState,
    WizardStep,
    AssessmentReportResponse,
    ReportFunctionDetail,
    ProfileComparison,
    AssessmentResponse,
)


class NISTAssessmentService:
    """Service for managing NIST CSF assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Reference Data
    # =========================================================================

    def get_functions_info(self) -> FunctionListResponse:
        """Get list of NIST CSF functions."""
        functions = [
            FunctionInfo(
                id=f["id"],
                code=f["code"],
                name_en=f["name_en"],
                name_de=f["name_de"],
                description_en=f["description_en"],
                description_de=f["description_de"],
                weight=f["weight"],
                category_count=f["category_count"],
            )
            for f in NIST_FUNCTIONS
        ]
        return FunctionListResponse(functions=functions, total=len(functions))

    def get_categories_info(self, function: Optional[str] = None) -> CategoryListResponse:
        """Get list of NIST CSF categories."""
        categories = NIST_CATEGORIES
        if function:
            categories = [c for c in categories if c["function"] == function]

        category_infos = [
            CategoryInfo(
                id=c["id"],
                function=c["function"],
                code=c["code"],
                name_en=c["name_en"],
                name_de=c["name_de"],
                subcategory_count=c["subcategory_count"],
            )
            for c in categories
        ]
        return CategoryListResponse(categories=category_infos, total=len(category_infos))

    def get_subcategories_info(self, function: Optional[str] = None, category: Optional[str] = None) -> SubcategoryListResponse:
        """Get list of NIST CSF subcategories."""
        subcategories = NIST_SUBCATEGORIES
        if function:
            subcategories = [s for s in subcategories if s["function"] == function]
        if category:
            subcategories = [s for s in subcategories if s["category"] == category]

        subcategory_infos = [
            SubcategoryInfo(
                id=s["id"],
                category=s["category"],
                function=s["function"],
                name_en=s["name_en"],
                name_de=s["name_de"],
                description_en=s["description_en"],
                weight=s["weight"],
                priority=s["priority"],
            )
            for s in subcategories
        ]
        return SubcategoryListResponse(subcategories=subcategory_infos, total=len(subcategory_infos))

    def get_tiers_info(self) -> TierListResponse:
        """Get list of implementation tiers."""
        tiers = [
            TierInfo(
                tier=t["tier"],
                name_en=t["name_en"],
                name_de=t["name_de"],
                description_en=t["description_en"],
                risk_management=t["risk_management"],
                integrated_program=t["integrated_program"],
                external_participation=t["external_participation"],
            )
            for t in NIST_TIERS
        ]
        return TierListResponse(tiers=tiers)

    # =========================================================================
    # Assessment CRUD
    # =========================================================================

    async def create_assessment(
        self,
        data: AssessmentCreate,
        user_id: str,
        tenant_id: str,
    ) -> NISTAssessment:
        """Create a new NIST assessment."""
        assessment = NISTAssessment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=NISTAssessmentStatus.DRAFT,
            created_by=user_id,
            function_scores={},
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[NISTAssessment]:
        """Get assessment by ID with responses."""
        result = await self.db.execute(
            select(NISTAssessment)
            .options(selectinload(NISTAssessment.responses))
            .where(
                and_(
                    NISTAssessment.id == assessment_id,
                    NISTAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[NISTAssessmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[NISTAssessment], int]:
        """List assessments with optional filters."""
        query = select(NISTAssessment).where(NISTAssessment.tenant_id == tenant_id)

        if status:
            query = query.where(NISTAssessment.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(NISTAssessment.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = list(result.scalars().all())

        return assessments, total

    async def update_assessment_scope(
        self,
        assessment_id: str,
        data: AssessmentScopeUpdate,
        tenant_id: str,
    ) -> Optional[NISTAssessment]:
        """Update assessment scope (wizard step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.organization_type = data.organization_type.value
        assessment.organization_size = data.organization_size.value
        assessment.employee_count = data.employee_count
        assessment.industry_sector = data.industry_sector
        assessment.current_tier = data.current_tier.value
        assessment.target_tier = data.target_tier.value
        assessment.profile_type = data.profile_type

        if assessment.status == NISTAssessmentStatus.DRAFT:
            assessment.status = NISTAssessmentStatus.IN_PROGRESS

        # Initialize subcategory responses
        await self._initialize_subcategory_responses(assessment)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def _initialize_subcategory_responses(self, assessment: NISTAssessment):
        """Initialize subcategory responses for all subcategories."""
        existing_ids = {r.subcategory_id for r in assessment.responses}

        for sub in NIST_SUBCATEGORIES:
            if sub["id"] not in existing_ids:
                response = NISTSubcategoryResponse(
                    id=str(uuid.uuid4()),
                    assessment_id=assessment.id,
                    subcategory_id=sub["id"],
                    function_id=sub["function"],
                    category_id=sub["category"],
                    status=NISTOutcomeStatus.NOT_EVALUATED,
                    implementation_level=0,
                    priority=sub["priority"],
                )
                self.db.add(response)

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
    # Subcategory Responses
    # =========================================================================

    async def submit_subcategory_response(
        self,
        assessment_id: str,
        data: SubcategoryResponseCreate,
        user_id: str,
        tenant_id: str,
    ) -> Optional[NISTSubcategoryResponse]:
        """Submit or update a subcategory response."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find existing response
        existing = None
        for resp in assessment.responses:
            if resp.subcategory_id == data.subcategory_id:
                existing = resp
                break

        if existing:
            # Update existing
            existing.status = data.status
            existing.implementation_level = data.implementation_level
            existing.current_state = data.current_state
            existing.target_state = data.target_state
            existing.evidence = data.evidence
            existing.notes = data.notes
            existing.gap_description = data.gap_description
            existing.remediation_plan = data.remediation_plan
            existing.priority = data.priority or 2
            existing.due_date = data.due_date
            existing.responsible = data.responsible
            existing.assessed_at = datetime.utcnow()
            existing.assessed_by = user_id
            response = existing
        else:
            # Create new
            sub = next((s for s in NIST_SUBCATEGORIES if s["id"] == data.subcategory_id), None)
            if not sub:
                return None

            response = NISTSubcategoryResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                subcategory_id=data.subcategory_id,
                function_id=sub["function"],
                category_id=sub["category"],
                status=data.status,
                implementation_level=data.implementation_level,
                current_state=data.current_state,
                target_state=data.target_state,
                evidence=data.evidence,
                notes=data.notes,
                gap_description=data.gap_description,
                remediation_plan=data.remediation_plan,
                priority=data.priority or 2,
                due_date=data.due_date,
                responsible=data.responsible,
                assessed_at=datetime.utcnow(),
                assessed_by=user_id,
            )
            self.db.add(response)

        await self._recalculate_scores(assessment)
        await self.db.commit()
        return response

    async def bulk_update_subcategories(
        self,
        assessment_id: str,
        responses: List[SubcategoryResponseCreate],
        user_id: str,
        tenant_id: str,
    ) -> List[NISTSubcategoryResponse]:
        """Bulk update subcategory responses."""
        updated = []
        for resp_data in responses:
            response = await self.submit_subcategory_response(
                assessment_id, resp_data, user_id, tenant_id
            )
            if response:
                updated.append(response)
        return updated

    # =========================================================================
    # Scoring
    # =========================================================================

    async def _recalculate_scores(self, assessment: NISTAssessment):
        """Recalculate assessment scores."""
        if not assessment.responses:
            return

        # Calculate function scores
        function_scores = {}
        function_weights = {}

        for func in NIST_FUNCTIONS:
            function_id = func["id"]
            func_responses = [
                r for r in assessment.responses if r.function_id == function_id
            ]

            if func_responses:
                scored_responses = [
                    r for r in func_responses
                    if r.status != NISTOutcomeStatus.NOT_EVALUATED
                ]

                if scored_responses:
                    total_score = 0
                    total_weight = 0

                    for resp in scored_responses:
                        sub = next(
                            (s for s in NIST_SUBCATEGORIES if s["id"] == resp.subcategory_id),
                            None
                        )
                        weight = sub["weight"] if sub else 10

                        if resp.status == NISTOutcomeStatus.FULLY_IMPLEMENTED:
                            total_score += 100 * weight
                            total_weight += weight
                        elif resp.status == NISTOutcomeStatus.LARGELY_IMPLEMENTED:
                            total_score += 75 * weight
                            total_weight += weight
                        elif resp.status == NISTOutcomeStatus.PARTIALLY_IMPLEMENTED:
                            score = resp.implementation_level if resp.implementation_level else 50
                            total_score += score * weight
                            total_weight += weight
                        elif resp.status == NISTOutcomeStatus.NOT_IMPLEMENTED:
                            total_score += 0
                            total_weight += weight
                        # NOT_APPLICABLE is excluded

                    if total_weight > 0:
                        function_scores[function_id] = round(total_score / total_weight, 1)
                        function_weights[function_id] = total_weight

        assessment.function_scores = function_scores

        # Overall score (weighted average by function weight)
        if function_scores:
            total_weighted = 0
            total_weights = 0
            for func in NIST_FUNCTIONS:
                if func["id"] in function_scores:
                    total_weighted += function_scores[func["id"]] * func["weight"]
                    total_weights += func["weight"]
            assessment.overall_score = round(total_weighted / total_weights, 1) if total_weights else 0

        # Count gaps
        gaps = [
            r for r in assessment.responses
            if r.status in [
                NISTOutcomeStatus.NOT_IMPLEMENTED,
                NISTOutcomeStatus.PARTIALLY_IMPLEMENTED,
            ]
        ]
        assessment.gaps_count = len(gaps)
        assessment.critical_gaps_count = len([g for g in gaps if g.priority == 1])

    # =========================================================================
    # Gap Analysis
    # =========================================================================

    async def get_gap_analysis(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[GapAnalysisResponse]:
        """Get gap analysis for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find all gaps
        gaps = []
        gaps_by_function = {}
        gaps_by_priority = {1: 0, 2: 0, 3: 0, 4: 0}

        for response in assessment.responses:
            if response.status in [
                NISTOutcomeStatus.NOT_IMPLEMENTED,
                NISTOutcomeStatus.PARTIALLY_IMPLEMENTED,
            ]:
                sub = next(
                    (s for s in NIST_SUBCATEGORIES if s["id"] == response.subcategory_id),
                    None
                )
                if sub:
                    func = next(
                        (f for f in NIST_FUNCTIONS if f["id"] == response.function_id),
                        None
                    )
                    cat = next(
                        (c for c in NIST_CATEGORIES if c["id"] == response.category_id),
                        None
                    )

                    # Calculate impact score
                    impl_factor = response.implementation_level / 100 if response.implementation_level else 0
                    if response.status == NISTOutcomeStatus.NOT_IMPLEMENTED:
                        impl_factor = 0
                    impact_score = sub["weight"] * (1 - impl_factor) * (5 - response.priority) / 4

                    gap = GapItem(
                        subcategory_id=response.subcategory_id,
                        subcategory_name=sub["name_en"],
                        function_id=response.function_id,
                        function_name=func["name_en"] if func else "",
                        category_id=response.category_id,
                        category_name=cat["name_en"] if cat else "",
                        status=response.status,
                        implementation_level=response.implementation_level,
                        current_state=response.current_state,
                        target_state=response.target_state,
                        priority=response.priority,
                        weight=sub["weight"],
                        impact_score=round(impact_score, 2),
                        gap_description=response.gap_description,
                        remediation_plan=response.remediation_plan,
                        due_date=response.due_date,
                    )
                    gaps.append(gap)

                    # Count by function
                    if response.function_id not in gaps_by_function:
                        gaps_by_function[response.function_id] = 0
                    gaps_by_function[response.function_id] += 1

                    # Count by priority
                    gaps_by_priority[response.priority] += 1

        # Sort by impact
        gaps.sort(key=lambda g: g.impact_score, reverse=True)

        # Function summaries
        function_summaries = []
        for func in NIST_FUNCTIONS:
            func_responses = [
                r for r in assessment.responses if r.function_id == func["id"]
            ]
            if func_responses:
                assessed = [r for r in func_responses if r.assessed_at]
                implemented = [
                    r for r in func_responses
                    if r.status in [NISTOutcomeStatus.FULLY_IMPLEMENTED, NISTOutcomeStatus.LARGELY_IMPLEMENTED]
                ]
                gap_count = len([
                    r for r in func_responses
                    if r.status in [
                        NISTOutcomeStatus.NOT_IMPLEMENTED,
                        NISTOutcomeStatus.PARTIALLY_IMPLEMENTED,
                    ]
                ])

                summary = FunctionSummary(
                    function_id=func["id"],
                    function_name=func["name_en"],
                    function_code=func["code"],
                    subcategory_count=len(func_responses),
                    assessed_count=len(assessed),
                    implemented_count=len(implemented),
                    gap_count=gap_count,
                    score=assessment.function_scores.get(func["id"], 0),
                )
                function_summaries.append(summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        # Tier gap analysis
        tier_gap = None
        if assessment.current_tier and assessment.target_tier:
            tier_order = ["tier_1", "tier_2", "tier_3", "tier_4"]
            current_idx = tier_order.index(assessment.current_tier) if assessment.current_tier in tier_order else 0
            target_idx = tier_order.index(assessment.target_tier) if assessment.target_tier in tier_order else 0
            if target_idx > current_idx:
                tier_gap = f"{target_idx - current_idx} tier(s) to advance"

        return GapAnalysisResponse(
            assessment_id=assessment_id,
            total_gaps=len(gaps),
            critical_gaps=gaps_by_priority[1],
            gaps_by_function=gaps_by_function,
            gaps_by_priority=gaps_by_priority,
            overall_compliance=assessment.overall_score,
            current_tier=assessment.current_tier,
            target_tier=assessment.target_tier,
            tier_gap=tier_gap,
            gaps=gaps[:50],  # Top 50 gaps
            function_summaries=function_summaries,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        gaps: List[GapItem],
        assessment: NISTAssessment,
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        if not gaps:
            recommendations.append(
                "Excellent! All subcategories are implemented. Focus on maintaining and improving current practices."
            )
            return recommendations

        # Priority 1 gaps
        p1_gaps = [g for g in gaps if g.priority == 1]
        if p1_gaps:
            recommendations.append(
                f"Address {len(p1_gaps)} critical gaps immediately: "
                f"{', '.join(g.subcategory_id for g in p1_gaps[:3])}"
            )

        # Function with most gaps
        func_gap_counts = {}
        for gap in gaps:
            func_gap_counts[gap.function_id] = func_gap_counts.get(gap.function_id, 0) + 1
        worst_func = max(func_gap_counts.items(), key=lambda x: x[1]) if func_gap_counts else None
        if worst_func:
            func_name = next((f["name_en"] for f in NIST_FUNCTIONS if f["id"] == worst_func[0]), worst_func[0])
            recommendations.append(
                f"Focus on {func_name} function with {worst_func[1]} gaps"
            )

        # Tier advancement
        if assessment.current_tier and assessment.target_tier:
            current_tier_info = next((t for t in NIST_TIERS if t["tier"] == assessment.current_tier), None)
            target_tier_info = next((t for t in NIST_TIERS if t["tier"] == assessment.target_tier), None)
            if current_tier_info and target_tier_info:
                recommendations.append(
                    f"To advance from {current_tier_info['name_en']} to {target_tier_info['name_en']}, "
                    f"formalize risk management practices and establish organization-wide policies"
                )

        # Specific function recommendations
        govern_gaps = [g for g in gaps if g.function_id == "govern"]
        if govern_gaps:
            recommendations.append(
                "Establish cybersecurity governance structure with clear roles, policies, and oversight"
            )

        identify_gaps = [g for g in gaps if g.function_id == "identify"]
        if identify_gaps:
            recommendations.append(
                "Improve asset inventory and risk assessment processes"
            )

        protect_gaps = [g for g in gaps if g.function_id == "protect"]
        if protect_gaps:
            recommendations.append(
                "Strengthen identity management, access controls, and data protection measures"
            )

        detect_gaps = [g for g in gaps if g.function_id == "detect"]
        if detect_gaps:
            recommendations.append(
                "Enhance continuous monitoring and threat detection capabilities"
            )

        respond_gaps = [g for g in gaps if g.function_id == "respond"]
        if respond_gaps:
            recommendations.append(
                "Develop and test incident response procedures"
            )

        recover_gaps = [g for g in gaps if g.function_id == "recover"]
        if recover_gaps:
            recommendations.append(
                "Establish and test recovery plans and backup procedures"
            )

        # Low score warning
        low_funcs = [
            f["name_en"] for f in NIST_FUNCTIONS
            if assessment.function_scores.get(f["id"], 0) < 50
        ]
        if low_funcs:
            recommendations.append(
                f"Prioritize improvements in: {', '.join(low_funcs[:3])}"
            )

        return recommendations[:8]

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard_stats(self, tenant_id: str) -> DashboardStats:
        """Get dashboard statistics."""
        # Get all assessments
        assessments, total = await self.list_assessments(tenant_id, size=1000)

        completed = [a for a in assessments if a.status == NISTAssessmentStatus.COMPLETED]
        in_progress = [a for a in assessments if a.status == NISTAssessmentStatus.IN_PROGRESS]

        # Calculate averages
        avg_score = sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0

        # Total gaps
        total_gaps = sum(a.gaps_count for a in assessments)
        critical_gaps = sum(a.critical_gaps_count for a in assessments)

        # Assessments by tier
        assessments_by_tier = {}
        for a in assessments:
            if a.current_tier:
                assessments_by_tier[a.current_tier] = assessments_by_tier.get(a.current_tier, 0) + 1

        # Average function scores
        avg_function_scores = {}
        for func in NIST_FUNCTIONS:
            scores = [
                a.function_scores.get(func["id"], 0)
                for a in assessments
                if a.function_scores.get(func["id"])
            ]
            if scores:
                avg_function_scores[func["id"]] = round(sum(scores) / len(scores), 1)

        # Implementation distribution
        impl_dist = ImplementationDistribution(
            not_evaluated=0,
            not_implemented=0,
            partially_implemented=0,
            largely_implemented=0,
            fully_implemented=0,
            not_applicable=0,
        )

        for assessment in assessments:
            full_assessment = await self.get_assessment(assessment.id, tenant_id)
            if full_assessment:
                for resp in full_assessment.responses:
                    if resp.status == NISTOutcomeStatus.NOT_EVALUATED:
                        impl_dist.not_evaluated += 1
                    elif resp.status == NISTOutcomeStatus.NOT_IMPLEMENTED:
                        impl_dist.not_implemented += 1
                    elif resp.status == NISTOutcomeStatus.PARTIALLY_IMPLEMENTED:
                        impl_dist.partially_implemented += 1
                    elif resp.status == NISTOutcomeStatus.LARGELY_IMPLEMENTED:
                        impl_dist.largely_implemented += 1
                    elif resp.status == NISTOutcomeStatus.FULLY_IMPLEMENTED:
                        impl_dist.fully_implemented += 1
                    elif resp.status == NISTOutcomeStatus.NOT_APPLICABLE:
                        impl_dist.not_applicable += 1

        # Recent assessments
        recent = sorted(assessments, key=lambda a: a.updated_at, reverse=True)[:5]

        return DashboardStats(
            total_assessments=total,
            completed_assessments=len(completed),
            in_progress_assessments=len(in_progress),
            average_score=round(avg_score, 1),
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            assessments_by_tier=assessments_by_tier,
            average_function_scores=avg_function_scores,
            implementation_distribution=impl_dist,
            recent_assessments=[
                AssessmentResponse.model_validate(a) for a in recent
            ],
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

        # Define steps
        steps = [
            WizardStep(
                id="scope",
                name="Organization Profile",
                completed=assessment.organization_type is not None,
                current=False,
            ),
        ]

        # Add function steps
        for func in NIST_FUNCTIONS:
            func_responses = [
                r for r in assessment.responses if r.function_id == func["id"]
            ]
            assessed = all(
                r.status != NISTOutcomeStatus.NOT_EVALUATED
                for r in func_responses
            ) if func_responses else False
            steps.append(
                WizardStep(
                    id=func["id"],
                    name=f"{func['code']}: {func['name_en']}",
                    completed=assessed,
                    current=False,
                )
            )

        # Add gap analysis step
        steps.append(
            WizardStep(
                id="gaps",
                name="Gap Analysis",
                completed=assessment.status == NISTAssessmentStatus.COMPLETED,
                current=False,
            )
        )

        # Determine current step
        current_step = 0
        for i, step in enumerate(steps):
            if not step.completed:
                current_step = i
                break
        else:
            current_step = len(steps) - 1

        steps[current_step].current = True

        # Calculate completion
        completed_count = sum(1 for s in steps if s.completed)
        completion_pct = (completed_count / len(steps)) * 100

        # Can complete if all functions assessed
        can_complete = all(s.completed for s in steps[:-1])

        return WizardState(
            assessment_id=assessment_id,
            current_step=current_step,
            total_steps=len(steps),
            steps=steps,
            can_complete=can_complete,
            completion_percentage=round(completion_pct, 1),
        )

    # =========================================================================
    # Assessment Completion
    # =========================================================================

    async def complete_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[NISTAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = NISTAssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    # =========================================================================
    # Reporting
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

        # Determine compliance status
        if assessment.overall_score >= 85:
            compliance_status = "compliant"
        elif assessment.overall_score >= 60:
            compliance_status = "partial"
        else:
            compliance_status = "non_compliant"

        # Function details
        function_details = []
        for func in NIST_FUNCTIONS:
            func_responses = [
                r for r in assessment.responses if r.function_id == func["id"]
            ]
            if func_responses:
                implemented = [
                    r for r in func_responses
                    if r.status in [NISTOutcomeStatus.FULLY_IMPLEMENTED, NISTOutcomeStatus.LARGELY_IMPLEMENTED]
                ]
                gap_count = len([
                    r for r in func_responses
                    if r.status in [
                        NISTOutcomeStatus.NOT_IMPLEMENTED,
                        NISTOutcomeStatus.PARTIALLY_IMPLEMENTED,
                    ]
                ])

                score = assessment.function_scores.get(func["id"], 0)
                if score >= 85:
                    status = "compliant"
                elif score >= 60:
                    status = "partial"
                else:
                    status = "non_compliant"

                function_details.append(
                    ReportFunctionDetail(
                        function_id=func["id"],
                        function_name=func["name_en"],
                        function_code=func["code"],
                        subcategory_count=len(func_responses),
                        implemented_count=len(implemented),
                        gaps_count=gap_count,
                        score=score,
                        status=status,
                    )
                )

        # Profile comparison
        profile_comparison = []
        target_score = 85.0  # Assume target is full compliance
        for func in NIST_FUNCTIONS:
            current = assessment.function_scores.get(func["id"], 0)
            profile_comparison.append(
                ProfileComparison(
                    function_id=func["id"],
                    function_name=func["name_en"],
                    current_score=current,
                    target_score=target_score,
                    gap_percentage=round(target_score - current, 1) if current < target_score else 0,
                )
            )

        # Executive summary
        current_tier_name = next(
            (t["name_en"] for t in NIST_TIERS if t["tier"] == assessment.current_tier),
            "Unknown"
        )
        target_tier_name = next(
            (t["name_en"] for t in NIST_TIERS if t["tier"] == assessment.target_tier),
            "Unknown"
        )

        exec_summary = (
            f"This NIST CSF 2.0 assessment shows an overall compliance score of "
            f"{assessment.overall_score:.1f}%. The organization is currently at "
            f"Implementation Tier: {current_tier_name}, with a target of {target_tier_name}. "
            f"{assessment.gaps_count} gaps were identified, including {assessment.critical_gaps_count} critical gaps."
        )

        # Tier analysis
        tier_analysis = (
            f"Current implementation tier ({current_tier_name}) indicates "
            f"{'formalized' if assessment.current_tier in ['tier_3', 'tier_4'] else 'informal'} "
            f"risk management practices. To reach {target_tier_name}, focus on "
            f"{'continuous improvement and adaptive practices' if assessment.target_tier == 'tier_4' else 'formalizing and documenting processes'}."
        )

        # Tier recommendations
        tier_recommendations = []
        if assessment.current_tier == "tier_1":
            tier_recommendations.append("Establish formal risk management policies")
            tier_recommendations.append("Define cybersecurity roles and responsibilities")
        elif assessment.current_tier == "tier_2":
            tier_recommendations.append("Implement organization-wide risk management")
            tier_recommendations.append("Establish regular cybersecurity reviews")
        elif assessment.current_tier == "tier_3":
            tier_recommendations.append("Implement continuous improvement processes")
            tier_recommendations.append("Establish predictive indicators for risk")

        # Key strengths
        key_strengths = []
        for func in NIST_FUNCTIONS:
            score = assessment.function_scores.get(func["id"], 0)
            if score >= 80:
                key_strengths.append(f"{func['name_en']}: {score:.0f}% implemented")

        # Critical findings
        critical_findings = []
        if gap_analysis:
            for gap in gap_analysis.gaps[:5]:
                if gap.priority == 1:
                    critical_findings.append(
                        f"{gap.subcategory_id}: {gap.subcategory_name} - "
                        f"{'Not implemented' if gap.status == NISTOutcomeStatus.NOT_IMPLEMENTED else 'Partially implemented'}"
                    )

        # Next steps
        next_steps = []
        if compliance_status == "compliant":
            next_steps.append("Maintain current practices and monitor for changes")
            next_steps.append("Consider advancing to next implementation tier")
        else:
            next_steps.append("Address critical gaps within 30 days")
            next_steps.append("Develop remediation plan for high-priority items")
            if not key_strengths:
                next_steps.append("Establish baseline security controls")

        # High priority areas
        high_priority_areas = []
        for func in NIST_FUNCTIONS:
            if assessment.function_scores.get(func["id"], 0) < 50:
                high_priority_areas.append(func["name_en"])

        # Quick wins (high weight, partially implemented)
        quick_wins = []
        if gap_analysis:
            partial_gaps = [g for g in gap_analysis.gaps if g.status == NISTOutcomeStatus.PARTIALLY_IMPLEMENTED]
            for gap in partial_gaps[:3]:
                if gap.implementation_level and gap.implementation_level >= 50:
                    quick_wins.append(f"{gap.subcategory_id}: {gap.subcategory_name} ({gap.implementation_level}% complete)")

        # Implementation distribution
        impl_dist = ImplementationDistribution(
            not_evaluated=0,
            not_implemented=0,
            partially_implemented=0,
            largely_implemented=0,
            fully_implemented=0,
            not_applicable=0,
        )
        for resp in assessment.responses:
            if resp.status == NISTOutcomeStatus.NOT_EVALUATED:
                impl_dist.not_evaluated += 1
            elif resp.status == NISTOutcomeStatus.NOT_IMPLEMENTED:
                impl_dist.not_implemented += 1
            elif resp.status == NISTOutcomeStatus.PARTIALLY_IMPLEMENTED:
                impl_dist.partially_implemented += 1
            elif resp.status == NISTOutcomeStatus.LARGELY_IMPLEMENTED:
                impl_dist.largely_implemented += 1
            elif resp.status == NISTOutcomeStatus.FULLY_IMPLEMENTED:
                impl_dist.fully_implemented += 1
            elif resp.status == NISTOutcomeStatus.NOT_APPLICABLE:
                impl_dist.not_applicable += 1

        return AssessmentReportResponse(
            assessment_id=assessment_id,
            organization_name=assessment.name,
            generated_at=datetime.utcnow(),
            organization_type=NISTOrganizationType(assessment.organization_type) if assessment.organization_type else NISTOrganizationType.OTHER,
            organization_size=NISTOrganizationSize(assessment.organization_size) if assessment.organization_size else NISTOrganizationSize.MEDIUM,
            industry_sector=assessment.industry_sector,
            current_tier=NISTImplementationTier(assessment.current_tier) if assessment.current_tier else NISTImplementationTier.TIER_1,
            target_tier=NISTImplementationTier(assessment.target_tier) if assessment.target_tier else NISTImplementationTier.TIER_3,
            executive_summary=exec_summary,
            overall_score=assessment.overall_score,
            compliance_status=compliance_status,
            tier_analysis=tier_analysis,
            tier_recommendations=tier_recommendations,
            function_details=function_details,
            profile_comparison=profile_comparison,
            gaps=gap_analysis.gaps[:20] if gap_analysis else [],
            implementation_distribution=impl_dist,
            key_strengths=key_strengths[:5],
            critical_findings=critical_findings,
            recommendations=gap_analysis.recommendations if gap_analysis else [],
            next_steps=next_steps,
            high_priority_areas=high_priority_areas,
            quick_wins=quick_wins,
        )
