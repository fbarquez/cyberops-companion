"""
TISAX Compliance Service

Business logic for TISAX assessment management.
"""

import uuid
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.tisax import (
    TISAXAssessment,
    TISAXControlResponse,
    TISAXAssessmentLevel,
    TISAXAssessmentObjective,
    TISAXCompanyType,
    TISAXCompanySize,
    TISAXAssessmentStatus,
    TISAXMaturityLevel,
    TISAX_CHAPTERS,
    TISAX_CONTROLS,
    TISAX_ASSESSMENT_LEVELS,
    TISAX_OBJECTIVES,
)
from src.schemas.tisax import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    ControlResponseCreate,
    ChapterInfo,
    ControlInfo,
    AssessmentLevelInfo,
    ObjectiveInfo,
    ChapterListResponse,
    ControlListResponse,
    AssessmentLevelListResponse,
    ObjectiveListResponse,
    GapItem,
    GapAnalysisResponse,
    ChapterSummary,
    DashboardStats,
    MaturityDistribution,
    WizardState,
    WizardStep,
    AssessmentReportResponse,
    ReportChapterDetail,
    AssessmentResponse,
)


class TISAXAssessmentService:
    """Service for managing TISAX assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Reference Data
    # =========================================================================

    def get_chapters_info(self) -> ChapterListResponse:
        """Get list of VDA ISA chapters."""
        chapters = [
            ChapterInfo(
                id=ch["id"],
                number=ch["number"],
                name_en=ch["name_en"],
                name_de=ch["name_de"],
                description_en=ch["description_en"],
                control_count=ch["control_count"],
            )
            for ch in TISAX_CHAPTERS
        ]
        return ChapterListResponse(chapters=chapters, total=len(chapters))

    def get_controls_info(self, chapter: Optional[str] = None) -> ControlListResponse:
        """Get list of VDA ISA controls, optionally filtered by chapter."""
        controls = TISAX_CONTROLS
        if chapter:
            controls = [c for c in controls if c["chapter"] == chapter]

        control_infos = [
            ControlInfo(
                id=c["id"],
                chapter=c["chapter"],
                number=c["number"],
                name_en=c["name_en"],
                name_de=c["name_de"],
                description_en=c["description_en"],
                description_de=c["description_de"],
                objective=c["objective"],
                weight=c["weight"],
                must_requirements=c["must_requirements"],
                should_requirements=c["should_requirements"],
            )
            for c in controls
        ]
        return ControlListResponse(controls=control_infos, total=len(control_infos))

    def get_assessment_levels_info(self) -> AssessmentLevelListResponse:
        """Get information about assessment levels."""
        levels = [
            AssessmentLevelInfo(
                level=level,
                name_en=info["name_en"],
                name_de=info["name_de"],
                description_en=info["description_en"],
                description_de=info["description_de"],
                audit_type=info["audit_type"],
                validity_years=info["validity_years"],
                min_maturity=info["min_maturity"],
            )
            for level, info in TISAX_ASSESSMENT_LEVELS.items()
        ]
        return AssessmentLevelListResponse(levels=levels)

    def get_objectives_info(self) -> ObjectiveListResponse:
        """Get information about assessment objectives."""
        objectives = [
            ObjectiveInfo(
                objective=obj,
                name_en=info["name_en"],
                name_de=info["name_de"],
                description_en=info["description_en"],
                assessment_levels=info["assessment_levels"],
            )
            for obj, info in TISAX_OBJECTIVES.items()
        ]
        return ObjectiveListResponse(objectives=objectives)

    # =========================================================================
    # Assessment CRUD
    # =========================================================================

    async def create_assessment(
        self,
        data: AssessmentCreate,
        user_id: str,
        tenant_id: str,
    ) -> TISAXAssessment:
        """Create a new TISAX assessment."""
        assessment = TISAXAssessment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=TISAXAssessmentStatus.DRAFT,
            created_by=user_id,
            objectives=[],
            oem_requirements=[],
            chapter_scores={},
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
    ) -> Optional[TISAXAssessment]:
        """Get assessment by ID with responses."""
        result = await self.db.execute(
            select(TISAXAssessment)
            .options(selectinload(TISAXAssessment.responses))
            .where(
                and_(
                    TISAXAssessment.id == assessment_id,
                    TISAXAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[TISAXAssessmentStatus] = None,
        level: Optional[TISAXAssessmentLevel] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[TISAXAssessment], int]:
        """List assessments with optional filters."""
        query = select(TISAXAssessment).where(TISAXAssessment.tenant_id == tenant_id)

        if status:
            query = query.where(TISAXAssessment.status == status)
        if level:
            query = query.where(TISAXAssessment.assessment_level == level)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(TISAXAssessment.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = list(result.scalars().all())

        return assessments, total

    async def update_assessment_scope(
        self,
        assessment_id: str,
        data: AssessmentScopeUpdate,
        tenant_id: str,
    ) -> Optional[TISAXAssessment]:
        """Update assessment scope (wizard step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.company_type = data.company_type
        assessment.company_size = data.company_size
        assessment.employee_count = data.employee_count
        assessment.location_count = data.location_count or 1
        assessment.assessment_level = data.assessment_level
        assessment.objectives = [o.value for o in data.objectives]
        assessment.oem_requirements = data.oem_requirements or []
        assessment.target_date = data.target_date

        if assessment.status == TISAXAssessmentStatus.DRAFT:
            assessment.status = TISAXAssessmentStatus.IN_PROGRESS

        # Initialize control responses for applicable controls
        await self._initialize_control_responses(assessment)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def _initialize_control_responses(self, assessment: TISAXAssessment):
        """Initialize control responses based on selected objectives."""
        existing_ids = {r.control_id for r in assessment.responses}

        # Determine applicable controls based on objectives
        applicable_objectives = {"info_high"}  # Base controls always applicable

        for obj in assessment.objectives:
            if obj == TISAXAssessmentObjective.INFO_VERY_HIGH.value:
                applicable_objectives.add("info_very_high")
            elif obj == TISAXAssessmentObjective.PROTOTYPE.value:
                applicable_objectives.add("prototype")
            elif obj == TISAXAssessmentObjective.PROTOTYPE_VEHICLE.value:
                applicable_objectives.add("prototype_vehicle")
            elif obj == TISAXAssessmentObjective.DATA_PROTECTION.value:
                applicable_objectives.add("data_protection")

        for control in TISAX_CONTROLS:
            if control["id"] not in existing_ids:
                if control["objective"] in applicable_objectives:
                    response = TISAXControlResponse(
                        id=str(uuid.uuid4()),
                        assessment_id=assessment.id,
                        control_id=control["id"],
                        chapter_id=control["chapter"],
                        maturity_level=TISAXMaturityLevel.LEVEL_0,
                        target_maturity=TISAXMaturityLevel.LEVEL_3,
                        must_fulfilled=[],
                        should_fulfilled=[],
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
    # Control Responses
    # =========================================================================

    async def submit_control_response(
        self,
        assessment_id: str,
        data: ControlResponseCreate,
        user_id: str,
        tenant_id: str,
    ) -> Optional[TISAXControlResponse]:
        """Submit or update a control response."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find existing response
        existing = None
        for resp in assessment.responses:
            if resp.control_id == data.control_id:
                existing = resp
                break

        if existing:
            # Update existing
            existing.maturity_level = data.maturity_level
            existing.target_maturity = data.target_maturity or TISAXMaturityLevel.LEVEL_3
            existing.evidence = data.evidence
            existing.notes = data.notes
            existing.gap_description = data.gap_description
            existing.remediation_plan = data.remediation_plan
            existing.must_fulfilled = data.must_fulfilled or []
            existing.should_fulfilled = data.should_fulfilled or []
            existing.priority = data.priority or 2
            existing.due_date = data.due_date
            existing.responsible = data.responsible
            existing.assessed_at = datetime.utcnow()
            existing.assessed_by = user_id
            response = existing
        else:
            # Create new
            control = next((c for c in TISAX_CONTROLS if c["id"] == data.control_id), None)
            if not control:
                return None

            response = TISAXControlResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                control_id=data.control_id,
                chapter_id=control["chapter"],
                maturity_level=data.maturity_level,
                target_maturity=data.target_maturity or TISAXMaturityLevel.LEVEL_3,
                evidence=data.evidence,
                notes=data.notes,
                gap_description=data.gap_description,
                remediation_plan=data.remediation_plan,
                must_fulfilled=data.must_fulfilled or [],
                should_fulfilled=data.should_fulfilled or [],
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

    async def bulk_update_controls(
        self,
        assessment_id: str,
        responses: List[ControlResponseCreate],
        user_id: str,
        tenant_id: str,
    ) -> List[TISAXControlResponse]:
        """Bulk update control responses."""
        updated = []
        for resp_data in responses:
            response = await self.submit_control_response(
                assessment_id, resp_data, user_id, tenant_id
            )
            if response:
                updated.append(response)
        return updated

    # =========================================================================
    # Scoring
    # =========================================================================

    async def _recalculate_scores(self, assessment: TISAXAssessment):
        """Recalculate assessment scores."""
        if not assessment.responses:
            return

        # Calculate chapter scores
        chapter_scores = {}
        chapter_maturities = {}

        for chapter in TISAX_CHAPTERS:
            chapter_id = chapter["id"]
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter_id
            ]

            if chapter_responses:
                # Average maturity for chapter
                avg_maturity = sum(
                    int(r.maturity_level.value) for r in chapter_responses
                ) / len(chapter_responses)
                chapter_maturities[chapter_id] = avg_maturity

                # Score based on target (3) vs actual
                target = 3.0
                score = min(100, (avg_maturity / target) * 100)
                chapter_scores[chapter_id] = round(score, 1)

        assessment.chapter_scores = chapter_scores

        # Overall maturity
        if chapter_maturities:
            assessment.maturity_level = round(
                sum(chapter_maturities.values()) / len(chapter_maturities), 2
            )

        # Overall score (weighted by chapter control count)
        total_weight = sum(ch["control_count"] for ch in TISAX_CHAPTERS)
        weighted_score = 0
        for chapter in TISAX_CHAPTERS:
            if chapter["id"] in chapter_scores:
                weight = chapter["control_count"] / total_weight
                weighted_score += chapter_scores[chapter["id"]] * weight

        assessment.overall_score = round(weighted_score, 1)

        # Count gaps (maturity < 3)
        gaps = [
            r for r in assessment.responses
            if int(r.maturity_level.value) < int(r.target_maturity.value)
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
        gaps_by_chapter = {}
        gaps_by_priority = {1: 0, 2: 0, 3: 0, 4: 0}

        for response in assessment.responses:
            current = int(response.maturity_level.value)
            target = int(response.target_maturity.value)

            if current < target:
                control = next(
                    (c for c in TISAX_CONTROLS if c["id"] == response.control_id),
                    None
                )
                if control:
                    chapter = next(
                        (ch for ch in TISAX_CHAPTERS if ch["id"] == response.chapter_id),
                        None
                    )
                    gap = GapItem(
                        control_id=response.control_id,
                        control_name=control["name_de"],
                        chapter_id=response.chapter_id,
                        chapter_name=chapter["name_de"] if chapter else "",
                        current_maturity=current,
                        target_maturity=target,
                        maturity_gap=target - current,
                        priority=response.priority,
                        weight=control["weight"],
                        impact_score=(target - current) * control["weight"] / 5,
                        gap_description=response.gap_description,
                        remediation_plan=response.remediation_plan,
                        due_date=response.due_date,
                    )
                    gaps.append(gap)

                    # Count by chapter
                    if response.chapter_id not in gaps_by_chapter:
                        gaps_by_chapter[response.chapter_id] = 0
                    gaps_by_chapter[response.chapter_id] += 1

                    # Count by priority
                    gaps_by_priority[response.priority] += 1

        # Sort by impact
        gaps.sort(key=lambda g: g.impact_score, reverse=True)

        # Chapter summaries
        chapter_summaries = []
        for chapter in TISAX_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            if chapter_responses:
                avg_maturity = sum(
                    int(r.maturity_level.value) for r in chapter_responses
                ) / len(chapter_responses)
                avg_target = sum(
                    int(r.target_maturity.value) for r in chapter_responses
                ) / len(chapter_responses)
                gap_count = len([
                    r for r in chapter_responses
                    if int(r.maturity_level.value) < int(r.target_maturity.value)
                ])

                summary = ChapterSummary(
                    chapter_id=chapter["id"],
                    chapter_name=chapter["name_de"],
                    control_count=len(chapter_responses),
                    assessed_count=len([r for r in chapter_responses if r.assessed_at]),
                    average_maturity=round(avg_maturity, 2),
                    target_maturity=round(avg_target, 2),
                    gap_count=gap_count,
                    score=assessment.chapter_scores.get(chapter["id"], 0),
                )
                chapter_summaries.append(summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, assessment)

        return GapAnalysisResponse(
            assessment_id=assessment_id,
            total_gaps=len(gaps),
            critical_gaps=gaps_by_priority[1],
            gaps_by_chapter=gaps_by_chapter,
            gaps_by_priority=gaps_by_priority,
            average_maturity=assessment.maturity_level,
            target_maturity=3.0,
            gaps=gaps[:50],  # Top 50 gaps
            chapter_summaries=chapter_summaries,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        gaps: List[GapItem],
        assessment: TISAXAssessment,
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        if not gaps:
            recommendations.append(
                "Alle Kontrollen erfüllen die Mindestanforderungen. "
                "Bereiten Sie die Audit-Dokumentation vor."
            )
            return recommendations

        # Priority 1 gaps
        p1_gaps = [g for g in gaps if g.priority == 1]
        if p1_gaps:
            recommendations.append(
                f"Sofortmaßnahmen: {len(p1_gaps)} kritische Lücken mit höchster "
                f"Priorität beheben. Fokus auf: {', '.join(g.control_name[:30] for g in p1_gaps[:3])}"
            )

        # Low maturity chapters
        low_chapters = [
            ch for ch in TISAX_CHAPTERS
            if assessment.chapter_scores.get(ch["id"], 0) < 60
        ]
        if low_chapters:
            recommendations.append(
                f"Kapitel mit niedrigem Score verbessern: "
                f"{', '.join(ch['name_de'] for ch in low_chapters[:3])}"
            )

        # Assessment level specific
        if assessment.assessment_level == TISAXAssessmentLevel.AL3:
            recommendations.append(
                "AL3-Bewertung erfordert Vor-Ort-Audit. "
                "Bereiten Sie physische Sicherheitsmaßnahmen und Dokumentation vor."
            )

        # Prototype protection
        if "prototype" in assessment.objectives or "prototype_vehicle" in assessment.objectives:
            prototype_gaps = [g for g in gaps if g.control_id.startswith("ISA-PP")]
            if prototype_gaps:
                recommendations.append(
                    f"Prototypenschutz: {len(prototype_gaps)} Lücken in den "
                    f"spezifischen Prototyp-Kontrollen schließen."
                )

        # General maturity improvement
        if assessment.maturity_level < 2.5:
            recommendations.append(
                "Allgemeiner Reifegrad unter Zielwert. "
                "Fokussieren Sie auf Prozessdokumentation und regelmäßige Überprüfungen."
            )

        # Quick wins
        quick_wins = [g for g in gaps if g.maturity_gap == 1 and g.weight <= 10]
        if quick_wins:
            recommendations.append(
                f"Quick Wins: {len(quick_wins)} Kontrollen benötigen nur "
                f"geringe Verbesserungen für Compliance."
            )

        return recommendations[:6]

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard_stats(self, tenant_id: str) -> DashboardStats:
        """Get dashboard statistics."""
        # Get all assessments
        assessments, total = await self.list_assessments(tenant_id, size=1000)

        completed = [a for a in assessments if a.status == TISAXAssessmentStatus.COMPLETED]
        in_progress = [a for a in assessments if a.status == TISAXAssessmentStatus.IN_PROGRESS]

        # Calculate averages
        avg_score = sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0
        avg_maturity = sum(a.maturity_level for a in assessments) / len(assessments) if assessments else 0

        # Count by level
        by_level = {}
        for level in TISAXAssessmentLevel:
            by_level[level.value] = len([a for a in assessments if a.assessment_level == level])

        # Count by objective
        by_objective = {}
        for obj in TISAXAssessmentObjective:
            by_objective[obj.value] = len([
                a for a in assessments if obj.value in (a.objectives or [])
            ])

        # Total gaps
        total_gaps = sum(a.gaps_count for a in assessments)
        critical_gaps = sum(a.critical_gaps_count for a in assessments)

        # Maturity distribution (across all assessments)
        maturity_dist = MaturityDistribution(
            level_0=0, level_1=0, level_2=0, level_3=0, level_4=0, level_5=0
        )

        for assessment in assessments:
            full_assessment = await self.get_assessment(assessment.id, tenant_id)
            if full_assessment:
                for resp in full_assessment.responses:
                    level = int(resp.maturity_level.value)
                    if level == 0:
                        maturity_dist.level_0 += 1
                    elif level == 1:
                        maturity_dist.level_1 += 1
                    elif level == 2:
                        maturity_dist.level_2 += 1
                    elif level == 3:
                        maturity_dist.level_3 += 1
                    elif level == 4:
                        maturity_dist.level_4 += 1
                    elif level == 5:
                        maturity_dist.level_5 += 1

        # Recent assessments
        recent = sorted(assessments, key=lambda a: a.updated_at, reverse=True)[:5]

        # Upcoming audits
        now = datetime.utcnow()
        upcoming = [
            a for a in assessments
            if a.audit_date and a.audit_date > now
        ]
        upcoming = sorted(upcoming, key=lambda a: a.audit_date)[:5]

        return DashboardStats(
            total_assessments=total,
            completed_assessments=len(completed),
            in_progress_assessments=len(in_progress),
            average_score=round(avg_score, 1),
            average_maturity=round(avg_maturity, 2),
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            assessments_by_level=by_level,
            assessments_by_objective=by_objective,
            maturity_distribution=maturity_dist,
            recent_assessments=[
                AssessmentResponse.model_validate(a) for a in recent
            ],
            upcoming_audits=[
                AssessmentResponse.model_validate(a) for a in upcoming
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
                name="Geltungsbereich",
                completed=assessment.assessment_level is not None,
                current=False,
            ),
        ]

        # Add chapter steps
        for chapter in TISAX_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            assessed = all(r.assessed_at for r in chapter_responses) if chapter_responses else False
            steps.append(
                WizardStep(
                    id=chapter["id"],
                    name=chapter["name_de"],
                    completed=assessed,
                    current=False,
                )
            )

        # Add gap analysis step
        steps.append(
            WizardStep(
                id="gaps",
                name="Gap-Analyse",
                completed=assessment.status == TISAXAssessmentStatus.COMPLETED,
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

        # Can complete if all chapters assessed
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
    ) -> Optional[TISAXAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = TISAXAssessmentStatus.COMPLETED
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
        if assessment.maturity_level >= 3.0 and assessment.gaps_count == 0:
            compliance_status = "ready"
        elif assessment.maturity_level >= 2.5:
            compliance_status = "partial"
        else:
            compliance_status = "not_ready"

        # Chapter details
        chapter_details = []
        for chapter in TISAX_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            if chapter_responses:
                avg_maturity = sum(
                    int(r.maturity_level.value) for r in chapter_responses
                ) / len(chapter_responses)
                avg_target = sum(
                    int(r.target_maturity.value) for r in chapter_responses
                ) / len(chapter_responses)
                gap_count = len([
                    r for r in chapter_responses
                    if int(r.maturity_level.value) < int(r.target_maturity.value)
                ])

                if avg_maturity >= avg_target:
                    status = "compliant"
                elif avg_maturity >= avg_target * 0.7:
                    status = "partial"
                else:
                    status = "non_compliant"

                chapter_details.append(
                    ReportChapterDetail(
                        chapter_id=chapter["id"],
                        chapter_name=chapter["name_de"],
                        average_maturity=round(avg_maturity, 2),
                        target_maturity=round(avg_target, 2),
                        control_count=len(chapter_responses),
                        gaps_count=gap_count,
                        status=status,
                    )
                )

        # Executive summary
        level_info = TISAX_ASSESSMENT_LEVELS.get(assessment.assessment_level, {})
        exec_summary = (
            f"Diese TISAX-Bewertung ({level_info.get('name_de', 'N/A')}) zeigt einen "
            f"durchschnittlichen Reifegrad von {assessment.maturity_level:.1f} von 5.0. "
            f"Der Gesamtscore beträgt {assessment.overall_score:.1f}%. "
            f"Es wurden {assessment.gaps_count} Lücken identifiziert, "
            f"davon {assessment.critical_gaps_count} kritisch."
        )

        # Critical findings
        critical_findings = []
        if gap_analysis:
            for gap in gap_analysis.gaps[:5]:
                if gap.priority == 1:
                    critical_findings.append(
                        f"{gap.control_name}: Reifegrad {gap.current_maturity} "
                        f"(Ziel: {gap.target_maturity})"
                    )

        # Next steps
        next_steps = []
        if compliance_status == "ready":
            next_steps.append("Audit-Termin mit TISAX-Prüfdienstleister vereinbaren")
            next_steps.append("Audit-Dokumentation finalisieren")
        else:
            next_steps.append("Kritische Lücken priorisiert beheben")
            next_steps.append("Prozessdokumentation vervollständigen")
            next_steps.append("Mitarbeiterschulungen durchführen")

        # Audit readiness
        if assessment.maturity_level >= 3.0:
            audit_readiness = 90.0
            remediation_effort = "low"
        elif assessment.maturity_level >= 2.5:
            audit_readiness = 70.0
            remediation_effort = "medium"
        else:
            audit_readiness = 50.0
            remediation_effort = "high"

        # Maturity distribution
        maturity_dist = MaturityDistribution(
            level_0=0, level_1=0, level_2=0, level_3=0, level_4=0, level_5=0
        )
        for resp in assessment.responses:
            level = int(resp.maturity_level.value)
            if level == 0:
                maturity_dist.level_0 += 1
            elif level == 1:
                maturity_dist.level_1 += 1
            elif level == 2:
                maturity_dist.level_2 += 1
            elif level == 3:
                maturity_dist.level_3 += 1
            elif level == 4:
                maturity_dist.level_4 += 1
            elif level == 5:
                maturity_dist.level_5 += 1

        return AssessmentReportResponse(
            assessment_id=assessment_id,
            organization_name=assessment.name,
            generated_at=datetime.utcnow(),
            assessment_level=assessment.assessment_level or TISAXAssessmentLevel.AL2,
            objectives=assessment.objectives or [],
            company_type=assessment.company_type or TISAXCompanyType.TIER1,
            company_size=assessment.company_size or TISAXCompanySize.MEDIUM,
            executive_summary=exec_summary,
            overall_score=assessment.overall_score,
            average_maturity=assessment.maturity_level,
            target_maturity=3.0,
            compliance_status=compliance_status,
            chapter_details=chapter_details,
            gaps=gap_analysis.gaps[:20] if gap_analysis else [],
            maturity_distribution=maturity_dist,
            critical_findings=critical_findings,
            recommendations=gap_analysis.recommendations if gap_analysis else [],
            next_steps=next_steps,
            audit_readiness_score=audit_readiness,
            estimated_remediation_effort=remediation_effort,
        )
