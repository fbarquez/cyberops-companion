"""
COBIT 2019 Assessment Service

Business logic for COBIT 2019 IT governance framework assessments.
"""

import uuid
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.cobit import (
    COBITAssessment,
    COBITProcessResponse,
    COBITDomain,
    COBITCapabilityLevel,
    COBITAssessmentStatus,
    COBITProcessStatus,
    COBIT_DOMAINS,
    COBIT_PROCESSES,
    COBIT_CAPABILITY_LEVELS,
)
from src.schemas.cobit import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    ProcessResponseCreate,
    DomainInfo,
    ProcessInfo,
    CapabilityLevelInfo,
    DomainListResponse,
    ProcessListResponse,
    CapabilityLevelListResponse,
    GapItem,
    DomainSummary,
    GapAnalysisResponse,
    AchievementDistribution,
    DashboardStats,
    WizardStep,
    WizardState,
    AssessmentReportResponse,
    ReportDomainDetail,
    CapabilityComparison,
)


class COBITAssessmentService:
    """Service for COBIT 2019 assessment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Reference Data
    # =========================================================================

    def get_domains_info(self) -> DomainListResponse:
        """Get all COBIT domains."""
        domains = [DomainInfo(**d) for d in COBIT_DOMAINS]
        return DomainListResponse(domains=domains, total=len(domains))

    def get_processes_info(self, domain: Optional[str] = None) -> ProcessListResponse:
        """Get all COBIT processes, optionally filtered by domain."""
        processes = COBIT_PROCESSES
        if domain:
            processes = [p for p in processes if p["domain"] == domain]
        process_infos = [ProcessInfo(**p) for p in processes]
        return ProcessListResponse(processes=process_infos, total=len(process_infos))

    def get_capability_levels_info(self) -> CapabilityLevelListResponse:
        """Get all capability levels."""
        levels = [CapabilityLevelInfo(**l) for l in COBIT_CAPABILITY_LEVELS]
        return CapabilityLevelListResponse(levels=levels)

    # =========================================================================
    # Assessment CRUD
    # =========================================================================

    async def create_assessment(
        self,
        data: AssessmentCreate,
        user_id: str,
        tenant_id: str,
    ) -> COBITAssessment:
        """Create a new COBIT assessment."""
        assessment = COBITAssessment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            created_by=user_id,
            name=data.name,
            description=data.description,
            status=COBITAssessmentStatus.DRAFT,
            domain_scores={},
            focus_areas=[],
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[COBITAssessment]:
        """Get assessment by ID with all responses."""
        result = await self.db.execute(
            select(COBITAssessment)
            .options(selectinload(COBITAssessment.responses))
            .where(
                and_(
                    COBITAssessment.id == assessment_id,
                    COBITAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[COBITAssessmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[COBITAssessment], int]:
        """List assessments with pagination."""
        query = select(COBITAssessment).where(COBITAssessment.tenant_id == tenant_id)

        if status:
            query = query.where(COBITAssessment.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page
        query = query.order_by(COBITAssessment.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        assessments = list(result.scalars().all())

        return assessments, total

    async def update_assessment_scope(
        self,
        assessment_id: str,
        data: AssessmentScopeUpdate,
        tenant_id: str,
    ) -> Optional[COBITAssessment]:
        """Update assessment scope."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.organization_type = data.organization_type
        assessment.organization_size = data.organization_size
        assessment.employee_count = data.employee_count
        assessment.industry_sector = data.industry_sector
        assessment.current_capability_level = data.current_capability_level
        assessment.target_capability_level = data.target_capability_level
        assessment.focus_areas = data.focus_areas or []

        if assessment.status == COBITAssessmentStatus.DRAFT:
            assessment.status = COBITAssessmentStatus.IN_PROGRESS

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
    # Process Responses
    # =========================================================================

    async def submit_process_response(
        self,
        assessment_id: str,
        data: ProcessResponseCreate,
        user_id: str,
        tenant_id: str,
    ) -> Optional[COBITProcessResponse]:
        """Submit or update a process response."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find process info
        process_info = next(
            (p for p in COBIT_PROCESSES if p["id"] == data.process_id),
            None
        )
        if not process_info:
            return None

        # Find existing response or create new
        existing = next(
            (r for r in assessment.responses if r.process_id == data.process_id),
            None
        )

        if existing:
            response = existing
        else:
            response = COBITProcessResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                process_id=data.process_id,
                domain_id=process_info["domain"],
            )
            self.db.add(response)

        # Update fields
        response.status = data.status
        response.capability_level = data.capability_level
        response.achievement_percentage = data.achievement_percentage
        response.current_state = data.current_state
        response.target_state = data.target_state
        response.evidence = data.evidence
        response.notes = data.notes
        response.gap_description = data.gap_description
        response.remediation_plan = data.remediation_plan
        response.priority = data.priority or 2
        response.due_date = data.due_date
        response.responsible = data.responsible
        response.assessed_at = datetime.utcnow()
        response.assessed_by = user_id

        await self.db.commit()
        await self._recalculate_scores(assessment_id)
        await self.db.refresh(response)
        return response

    async def bulk_update_processes(
        self,
        assessment_id: str,
        responses: List[ProcessResponseCreate],
        user_id: str,
        tenant_id: str,
    ) -> List[COBITProcessResponse]:
        """Bulk update process responses."""
        results = []
        for response_data in responses:
            result = await self.submit_process_response(
                assessment_id, response_data, user_id, tenant_id
            )
            if result:
                results.append(result)
        return results

    # =========================================================================
    # Scoring
    # =========================================================================

    async def _recalculate_scores(self, assessment_id: str) -> None:
        """Recalculate assessment scores based on responses."""
        result = await self.db.execute(
            select(COBITAssessment)
            .options(selectinload(COBITAssessment.responses))
            .where(COBITAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if not assessment:
            return

        domain_scores: Dict[str, float] = {}
        total_weight = 0
        weighted_score = 0
        gaps_count = 0
        critical_gaps = 0

        for domain in COBIT_DOMAINS:
            domain_id = domain["id"]
            domain_weight = domain["weight"]
            domain_processes = [p for p in COBIT_PROCESSES if p["domain"] == domain_id]

            if not domain_processes:
                continue

            domain_score_sum = 0
            domain_weight_sum = 0

            for process in domain_processes:
                response = next(
                    (r for r in assessment.responses if r.process_id == process["id"]),
                    None
                )

                if response and response.status not in [
                    COBITProcessStatus.NOT_EVALUATED,
                    COBITProcessStatus.NOT_APPLICABLE
                ]:
                    process_score = response.achievement_percentage
                    domain_score_sum += process_score * process["weight"]
                    domain_weight_sum += process["weight"]

                    # Count gaps
                    if response.status in [
                        COBITProcessStatus.NOT_ACHIEVED,
                        COBITProcessStatus.PARTIALLY_ACHIEVED
                    ]:
                        gaps_count += 1
                        if response.priority == 1:
                            critical_gaps += 1

            if domain_weight_sum > 0:
                domain_scores[domain_id] = domain_score_sum / domain_weight_sum
                weighted_score += domain_scores[domain_id] * domain_weight
                total_weight += domain_weight
            else:
                domain_scores[domain_id] = 0

        overall_score = weighted_score / total_weight if total_weight > 0 else 0

        assessment.overall_score = overall_score
        assessment.domain_scores = domain_scores
        assessment.gaps_count = gaps_count
        assessment.critical_gaps_count = critical_gaps

        await self.db.commit()

    # =========================================================================
    # Gap Analysis
    # =========================================================================

    async def get_gap_analysis(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[GapAnalysisResponse]:
        """Generate gap analysis for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        gaps: List[GapItem] = []
        gaps_by_domain: Dict[str, int] = {}
        gaps_by_priority: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        domain_summaries: List[DomainSummary] = []

        for domain in COBIT_DOMAINS:
            domain_id = domain["id"]
            domain_processes = [p for p in COBIT_PROCESSES if p["domain"] == domain_id]
            domain_gaps = 0
            assessed_count = 0
            achieved_count = 0
            domain_capability_levels = []

            for process in domain_processes:
                response = next(
                    (r for r in assessment.responses if r.process_id == process["id"]),
                    None
                )

                if response and response.status not in [
                    COBITProcessStatus.NOT_EVALUATED,
                    COBITProcessStatus.NOT_APPLICABLE
                ]:
                    assessed_count += 1
                    if response.capability_level:
                        domain_capability_levels.append(response.capability_level.value)

                    if response.status in [
                        COBITProcessStatus.FULLY_ACHIEVED,
                        COBITProcessStatus.LARGELY_ACHIEVED
                    ]:
                        achieved_count += 1
                    else:
                        domain_gaps += 1
                        gaps_by_priority[response.priority] = gaps_by_priority.get(response.priority, 0) + 1

                        gaps.append(GapItem(
                            process_id=process["id"],
                            process_name=process["name_en"],
                            domain_id=domain_id,
                            domain_name=domain["name_en"],
                            status=response.status,
                            capability_level=response.capability_level,
                            achievement_percentage=response.achievement_percentage,
                            current_state=response.current_state,
                            target_state=response.target_state,
                            priority=response.priority,
                            weight=process["weight"],
                            impact_score=process["weight"] * (100 - response.achievement_percentage) / 100,
                            gap_description=response.gap_description,
                            remediation_plan=response.remediation_plan,
                            due_date=response.due_date,
                        ))

            gaps_by_domain[domain_id] = domain_gaps

            # Determine average capability level
            avg_capability = None
            if domain_capability_levels:
                level_values = {"level_0": 0, "level_1": 1, "level_2": 2, "level_3": 3, "level_4": 4, "level_5": 5}
                avg_val = sum(level_values.get(l, 0) for l in domain_capability_levels) / len(domain_capability_levels)
                avg_capability = f"level_{int(round(avg_val))}"

            domain_summaries.append(DomainSummary(
                domain_id=domain_id,
                domain_name=domain["name_en"],
                domain_code=domain["code"],
                process_count=len(domain_processes),
                assessed_count=assessed_count,
                achieved_count=achieved_count,
                gap_count=domain_gaps,
                score=assessment.domain_scores.get(domain_id, 0),
                average_capability=avg_capability,
            ))

        # Sort gaps by priority and impact
        gaps.sort(key=lambda g: (g.priority, -g.impact_score))

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        # Calculate level gap
        level_gap = None
        if assessment.current_capability_level and assessment.target_capability_level:
            level_values = {"level_0": 0, "level_1": 1, "level_2": 2, "level_3": 3, "level_4": 4, "level_5": 5}
            current_val = level_values.get(assessment.current_capability_level.value, 0)
            target_val = level_values.get(assessment.target_capability_level.value, 0)
            if target_val > current_val:
                level_gap = f"{target_val - current_val} Level(s)"

        return GapAnalysisResponse(
            assessment_id=assessment_id,
            total_gaps=len(gaps),
            critical_gaps=gaps_by_priority.get(1, 0),
            gaps_by_domain=gaps_by_domain,
            gaps_by_priority=gaps_by_priority,
            overall_compliance=assessment.overall_score,
            current_level=assessment.current_capability_level.value if assessment.current_capability_level else None,
            target_level=assessment.target_capability_level.value if assessment.target_capability_level else None,
            level_gap=level_gap,
            gaps=gaps,
            domain_summaries=domain_summaries,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        gaps: List[GapItem],
        assessment: COBITAssessment,
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        # Critical gaps
        critical_gaps = [g for g in gaps if g.priority == 1]
        if critical_gaps:
            recommendations.append(
                f"Prioritize {len(critical_gaps)} critical process gap(s): {', '.join(g.process_id for g in critical_gaps[:3])}"
            )

        # Domain-specific recommendations
        domain_gap_counts = {}
        for gap in gaps:
            domain_gap_counts[gap.domain_id] = domain_gap_counts.get(gap.domain_id, 0) + 1

        worst_domain = max(domain_gap_counts.items(), key=lambda x: x[1], default=(None, 0))
        if worst_domain[0]:
            domain_info = next((d for d in COBIT_DOMAINS if d["id"] == worst_domain[0]), None)
            if domain_info:
                recommendations.append(
                    f"Focus on {domain_info['code']} domain with {worst_domain[1]} gaps"
                )

        # Capability level recommendations
        if assessment.target_capability_level:
            level_info = next(
                (l for l in COBIT_CAPABILITY_LEVELS if l["level"] == assessment.target_capability_level.value),
                None
            )
            if level_info:
                recommendations.append(
                    f"Target achieving {level_info['name_en']} capability level across all domains"
                )

        # Security and risk focus
        security_processes = ["APO12", "APO13", "DSS05"]
        security_gaps = [g for g in gaps if g.process_id in security_processes]
        if security_gaps:
            recommendations.append(
                "Address security and risk management gaps (APO12, APO13, DSS05) as priority"
            )

        # Quick wins
        quick_wins = [g for g in gaps if g.priority >= 3 and g.achievement_percentage >= 50]
        if quick_wins:
            recommendations.append(
                f"Consider {len(quick_wins)} quick wins with >50% achievement for rapid improvement"
            )

        return recommendations[:8]

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard_stats(self, tenant_id: str) -> DashboardStats:
        """Get dashboard statistics."""
        result = await self.db.execute(
            select(COBITAssessment)
            .options(selectinload(COBITAssessment.responses))
            .where(COBITAssessment.tenant_id == tenant_id)
        )
        assessments = list(result.scalars().all())

        total = len(assessments)
        completed = sum(1 for a in assessments if a.status == COBITAssessmentStatus.COMPLETED)
        in_progress = sum(1 for a in assessments if a.status == COBITAssessmentStatus.IN_PROGRESS)

        # Average score
        scores = [a.overall_score for a in assessments if a.overall_score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Total gaps
        total_gaps = sum(a.gaps_count for a in assessments)
        critical_gaps = sum(a.critical_gaps_count for a in assessments)

        # Assessments by level
        assessments_by_level: Dict[str, int] = {}
        for a in assessments:
            if a.target_capability_level:
                level = a.target_capability_level.value
                assessments_by_level[level] = assessments_by_level.get(level, 0) + 1

        # Average domain scores
        domain_score_sums: Dict[str, float] = {}
        domain_score_counts: Dict[str, int] = {}
        for a in assessments:
            for domain_id, score in (a.domain_scores or {}).items():
                if score > 0:
                    domain_score_sums[domain_id] = domain_score_sums.get(domain_id, 0) + score
                    domain_score_counts[domain_id] = domain_score_counts.get(domain_id, 0) + 1

        avg_domain_scores = {
            d: domain_score_sums[d] / domain_score_counts[d]
            for d in domain_score_sums
            if domain_score_counts.get(d, 0) > 0
        }

        # Achievement distribution
        distribution = AchievementDistribution(
            not_evaluated=0,
            not_achieved=0,
            partially_achieved=0,
            largely_achieved=0,
            fully_achieved=0,
            not_applicable=0,
        )
        for a in assessments:
            for r in a.responses:
                if r.status == COBITProcessStatus.NOT_EVALUATED:
                    distribution.not_evaluated += 1
                elif r.status == COBITProcessStatus.NOT_ACHIEVED:
                    distribution.not_achieved += 1
                elif r.status == COBITProcessStatus.PARTIALLY_ACHIEVED:
                    distribution.partially_achieved += 1
                elif r.status == COBITProcessStatus.LARGELY_ACHIEVED:
                    distribution.largely_achieved += 1
                elif r.status == COBITProcessStatus.FULLY_ACHIEVED:
                    distribution.fully_achieved += 1
                elif r.status == COBITProcessStatus.NOT_APPLICABLE:
                    distribution.not_applicable += 1

        # Recent assessments
        recent = sorted(assessments, key=lambda a: a.updated_at, reverse=True)[:5]

        from src.schemas.cobit import AssessmentResponse
        recent_responses = [
            AssessmentResponse.model_validate(a) for a in recent
        ]

        return DashboardStats(
            total_assessments=total,
            completed_assessments=completed,
            in_progress_assessments=in_progress,
            average_score=avg_score,
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            assessments_by_level=assessments_by_level,
            average_domain_scores=avg_domain_scores,
            achievement_distribution=distribution,
            recent_assessments=recent_responses,
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

        # Steps: Scope + 5 Domains + Gap Analysis
        steps = [
            WizardStep(
                id="scope",
                name="Scope",
                completed=assessment.organization_type is not None,
                current=assessment.organization_type is None,
            )
        ]

        for domain in COBIT_DOMAINS:
            domain_processes = [p for p in COBIT_PROCESSES if p["domain"] == domain["id"]]
            assessed = sum(
                1 for p in domain_processes
                if any(
                    r.process_id == p["id"] and r.status != COBITProcessStatus.NOT_EVALUATED
                    for r in assessment.responses
                )
            )
            completed = assessed == len(domain_processes) and len(domain_processes) > 0

            steps.append(WizardStep(
                id=domain["id"],
                name=domain["code"],
                completed=completed,
                current=False,
            ))

        steps.append(WizardStep(
            id="gaps",
            name="Gap Analysis",
            completed=assessment.status == COBITAssessmentStatus.COMPLETED,
            current=False,
        ))

        # Determine current step
        current_step = 0
        for i, step in enumerate(steps):
            if not step.completed:
                current_step = i
                steps[i].current = True
                break
        else:
            current_step = len(steps) - 1
            steps[-1].current = True

        # Calculate completion percentage
        total_processes = len(COBIT_PROCESSES)
        assessed_processes = sum(
            1 for r in assessment.responses
            if r.status != COBITProcessStatus.NOT_EVALUATED
        )
        completion = (assessed_processes / total_processes * 100) if total_processes > 0 else 0

        can_complete = assessed_processes > 0 and assessment.organization_type is not None

        return WizardState(
            assessment_id=assessment_id,
            current_step=current_step,
            total_steps=len(steps),
            steps=steps,
            can_complete=can_complete,
            completion_percentage=completion,
        )

    # =========================================================================
    # Completion and Reporting
    # =========================================================================

    async def complete_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[COBITAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = COBITAssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def generate_report(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[AssessmentReportResponse]:
        """Generate comprehensive assessment report."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        gap_analysis = await self.get_gap_analysis(assessment_id, tenant_id)
        if not gap_analysis:
            return None

        # Domain details
        domain_details = []
        for summary in gap_analysis.domain_summaries:
            status = "compliant"
            if summary.score < 50:
                status = "non_compliant"
            elif summary.score < 80:
                status = "partial"

            domain_details.append(ReportDomainDetail(
                domain_id=summary.domain_id,
                domain_name=summary.domain_name,
                domain_code=summary.domain_code,
                process_count=summary.process_count,
                achieved_count=summary.achieved_count,
                gaps_count=summary.gap_count,
                score=summary.score,
                capability_level=summary.average_capability,
                status=status,
            ))

        # Capability comparison
        capability_comparison = []
        level_values = {"level_0": 0, "level_1": 1, "level_2": 2, "level_3": 3, "level_4": 4, "level_5": 5}
        target_val = level_values.get(
            assessment.target_capability_level.value if assessment.target_capability_level else "level_0",
            0
        )
        for summary in gap_analysis.domain_summaries:
            current_val = level_values.get(summary.average_capability or "level_0", 0)
            capability_comparison.append(CapabilityComparison(
                domain_id=summary.domain_id,
                domain_name=summary.domain_name,
                current_level=summary.average_capability,
                target_level=assessment.target_capability_level.value if assessment.target_capability_level else None,
                gap_levels=max(0, target_val - current_val),
            ))

        # Compliance status
        compliance_status = "compliant"
        if assessment.overall_score < 50:
            compliance_status = "non_compliant"
        elif assessment.overall_score < 80:
            compliance_status = "partial"

        # Executive summary
        exec_summary = self._generate_executive_summary(assessment, gap_analysis)

        # Capability analysis
        capability_analysis = self._generate_capability_analysis(assessment, capability_comparison)

        # Key findings
        key_strengths = self._identify_strengths(assessment, gap_analysis)
        critical_findings = self._identify_critical_findings(gap_analysis)
        high_priority = self._identify_high_priority(gap_analysis)
        quick_wins = self._identify_quick_wins(gap_analysis)

        return AssessmentReportResponse(
            assessment_id=assessment_id,
            organization_name=assessment.name,
            generated_at=datetime.utcnow(),
            organization_type=assessment.organization_type,
            organization_size=assessment.organization_size,
            industry_sector=assessment.industry_sector,
            current_capability_level=assessment.current_capability_level,
            target_capability_level=assessment.target_capability_level,
            executive_summary=exec_summary,
            overall_score=assessment.overall_score,
            compliance_status=compliance_status,
            capability_analysis=capability_analysis,
            capability_recommendations=gap_analysis.recommendations[:4],
            domain_details=domain_details,
            capability_comparison=capability_comparison,
            gaps=gap_analysis.gaps[:20],
            achievement_distribution=AchievementDistribution(
                not_evaluated=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.NOT_EVALUATED),
                not_achieved=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.NOT_ACHIEVED),
                partially_achieved=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.PARTIALLY_ACHIEVED),
                largely_achieved=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.LARGELY_ACHIEVED),
                fully_achieved=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.FULLY_ACHIEVED),
                not_applicable=sum(1 for r in assessment.responses if r.status == COBITProcessStatus.NOT_APPLICABLE),
            ),
            key_strengths=key_strengths,
            critical_findings=critical_findings,
            recommendations=gap_analysis.recommendations,
            next_steps=self._generate_next_steps(assessment, gap_analysis),
            high_priority_areas=high_priority,
            quick_wins=quick_wins,
        )

    def _generate_executive_summary(
        self,
        assessment: COBITAssessment,
        gap_analysis: GapAnalysisResponse,
    ) -> str:
        """Generate executive summary text."""
        level_name = "Not defined"
        if assessment.target_capability_level:
            level_info = next(
                (l for l in COBIT_CAPABILITY_LEVELS if l["level"] == assessment.target_capability_level.value),
                None
            )
            if level_info:
                level_name = level_info["name_en"]

        return (
            f"This COBIT 2019 assessment evaluates IT governance maturity across 40 processes "
            f"in 5 domains. The overall maturity score is {assessment.overall_score:.1f}% "
            f"with a target capability level of {level_name}. "
            f"A total of {gap_analysis.total_gaps} gaps were identified, "
            f"including {gap_analysis.critical_gaps} critical gaps requiring immediate attention."
        )

    def _generate_capability_analysis(
        self,
        assessment: COBITAssessment,
        comparison: List[CapabilityComparison],
    ) -> str:
        """Generate capability level analysis text."""
        gaps_to_close = sum(c.gap_levels for c in comparison)
        domains_at_target = sum(1 for c in comparison if c.gap_levels == 0 and c.current_level)

        return (
            f"Capability analysis reveals {domains_at_target} domain(s) at or above target level. "
            f"A total capability gap of {gaps_to_close} level(s) needs to be closed across all domains "
            f"to achieve the target maturity state."
        )

    def _identify_strengths(
        self,
        assessment: COBITAssessment,
        gap_analysis: GapAnalysisResponse,
    ) -> List[str]:
        """Identify key strengths."""
        strengths = []
        for summary in gap_analysis.domain_summaries:
            if summary.score >= 80:
                strengths.append(f"{summary.domain_code}: {summary.domain_name} ({summary.score:.0f}%)")
        return strengths[:5]

    def _identify_critical_findings(self, gap_analysis: GapAnalysisResponse) -> List[str]:
        """Identify critical findings."""
        findings = []
        critical_gaps = [g for g in gap_analysis.gaps if g.priority == 1]
        for gap in critical_gaps[:5]:
            findings.append(f"{gap.process_id}: {gap.process_name}")
        return findings

    def _identify_high_priority(self, gap_analysis: GapAnalysisResponse) -> List[str]:
        """Identify high priority areas."""
        areas = []
        for summary in gap_analysis.domain_summaries:
            if summary.score < 50:
                areas.append(f"{summary.domain_code} - {summary.gap_count} gaps")
        return areas[:5]

    def _identify_quick_wins(self, gap_analysis: GapAnalysisResponse) -> List[str]:
        """Identify quick wins."""
        quick_wins = []
        for gap in gap_analysis.gaps:
            if gap.priority >= 3 and gap.achievement_percentage >= 60:
                quick_wins.append(f"{gap.process_id}: {gap.achievement_percentage}% achieved")
        return quick_wins[:5]

    def _generate_next_steps(
        self,
        assessment: COBITAssessment,
        gap_analysis: GapAnalysisResponse,
    ) -> List[str]:
        """Generate recommended next steps."""
        steps = []
        if gap_analysis.critical_gaps > 0:
            steps.append(f"Address {gap_analysis.critical_gaps} critical gaps immediately")
        steps.append("Create remediation roadmap with timeline and ownership")
        steps.append("Establish governance oversight for improvement initiatives")
        steps.append("Schedule follow-up assessment in 6 months")
        return steps
