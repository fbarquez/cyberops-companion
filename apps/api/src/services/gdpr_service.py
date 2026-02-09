"""
GDPR Compliance Service

Business logic for GDPR assessment management.
"""

import uuid
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.gdpr import (
    GDPRAssessment,
    GDPRRequirementResponse,
    GDPRChapter,
    GDPROrganizationType,
    GDPROrganizationSize,
    GDPRAssessmentStatus,
    GDPRComplianceLevel,
    GDPRDataCategory,
    GDPRLegalBasis,
    GDPR_CHAPTERS,
    GDPR_REQUIREMENTS,
)
from src.schemas.gdpr import (
    AssessmentCreate,
    AssessmentScopeUpdate,
    RequirementResponseCreate,
    ChapterInfo,
    RequirementInfo,
    ChapterListResponse,
    RequirementListResponse,
    GapItem,
    GapAnalysisResponse,
    ChapterSummary,
    DashboardStats,
    ComplianceDistribution,
    WizardState,
    WizardStep,
    AssessmentReportResponse,
    ReportChapterDetail,
    AssessmentResponse,
)


class GDPRAssessmentService:
    """Service for managing GDPR assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Reference Data
    # =========================================================================

    def get_chapters_info(self) -> ChapterListResponse:
        """Get list of GDPR chapters."""
        chapters = [
            ChapterInfo(
                id=ch["id"],
                number=ch["number"],
                name_en=ch["name_en"],
                name_de=ch["name_de"],
                articles=ch["articles"],
                description_en=ch["description_en"],
                requirement_count=ch["requirement_count"],
            )
            for ch in GDPR_CHAPTERS
        ]
        return ChapterListResponse(chapters=chapters, total=len(chapters))

    def get_requirements_info(self, chapter: Optional[str] = None) -> RequirementListResponse:
        """Get list of GDPR requirements, optionally filtered by chapter."""
        requirements = GDPR_REQUIREMENTS
        if chapter:
            requirements = [r for r in requirements if r["chapter"] == chapter]

        requirement_infos = [
            RequirementInfo(
                id=r["id"],
                chapter=r["chapter"],
                article=r["article"],
                name_en=r["name_en"],
                name_de=r["name_de"],
                description_en=r["description_en"],
                description_de=r["description_de"],
                weight=r["weight"],
                priority=r["priority"],
                requirements=r["requirements"],
            )
            for r in requirements
        ]
        return RequirementListResponse(requirements=requirement_infos, total=len(requirement_infos))

    # =========================================================================
    # Assessment CRUD
    # =========================================================================

    async def create_assessment(
        self,
        data: AssessmentCreate,
        user_id: str,
        tenant_id: str,
    ) -> GDPRAssessment:
        """Create a new GDPR assessment."""
        assessment = GDPRAssessment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=GDPRAssessmentStatus.DRAFT,
            created_by=user_id,
            data_categories=[],
            legal_bases=[],
            eu_countries=[],
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
    ) -> Optional[GDPRAssessment]:
        """Get assessment by ID with responses."""
        result = await self.db.execute(
            select(GDPRAssessment)
            .options(selectinload(GDPRAssessment.responses))
            .where(
                and_(
                    GDPRAssessment.id == assessment_id,
                    GDPRAssessment.tenant_id == tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[GDPRAssessmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[GDPRAssessment], int]:
        """List assessments with optional filters."""
        query = select(GDPRAssessment).where(GDPRAssessment.tenant_id == tenant_id)

        if status:
            query = query.where(GDPRAssessment.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(GDPRAssessment.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = list(result.scalars().all())

        return assessments, total

    async def update_assessment_scope(
        self,
        assessment_id: str,
        data: AssessmentScopeUpdate,
        tenant_id: str,
    ) -> Optional[GDPRAssessment]:
        """Update assessment scope (wizard step 1)."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.organization_type = data.organization_type
        assessment.organization_size = data.organization_size
        assessment.employee_count = data.employee_count
        assessment.processes_special_categories = data.processes_special_categories
        assessment.processes_criminal_data = data.processes_criminal_data
        assessment.large_scale_processing = data.large_scale_processing
        assessment.systematic_monitoring = data.systematic_monitoring
        assessment.cross_border_processing = data.cross_border_processing
        assessment.data_categories = [c.value for c in data.data_categories]
        assessment.legal_bases = [b.value for b in data.legal_bases]
        assessment.eu_countries = data.eu_countries or []
        assessment.dpo_appointed = data.dpo_appointed
        assessment.dpo_name = data.dpo_name
        assessment.dpo_email = data.dpo_email
        assessment.lead_authority = data.lead_authority

        # Determine if DPO is required
        assessment.requires_dpo = self._check_dpo_requirement(assessment)

        if assessment.status == GDPRAssessmentStatus.DRAFT:
            assessment.status = GDPRAssessmentStatus.IN_PROGRESS

        # Initialize requirement responses
        await self._initialize_requirement_responses(assessment)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    def _check_dpo_requirement(self, assessment: GDPRAssessment) -> bool:
        """Check if DPO is required based on Art. 37."""
        # Public authority
        if assessment.organization_type in [
            GDPROrganizationType.CONTROLLER,
            GDPROrganizationType.PROCESSOR,
        ]:
            # Large scale processing of special categories
            if assessment.processes_special_categories and assessment.large_scale_processing:
                return True

            # Large scale systematic monitoring
            if assessment.systematic_monitoring and assessment.large_scale_processing:
                return True

            # Processing criminal data at large scale
            if assessment.processes_criminal_data and assessment.large_scale_processing:
                return True

        # Large organizations (250+ employees) often need DPO
        if assessment.employee_count and assessment.employee_count >= 250:
            return True

        return False

    async def _initialize_requirement_responses(self, assessment: GDPRAssessment):
        """Initialize requirement responses for all requirements."""
        existing_ids = {r.requirement_id for r in assessment.responses}

        for req in GDPR_REQUIREMENTS:
            if req["id"] not in existing_ids:
                response = GDPRRequirementResponse(
                    id=str(uuid.uuid4()),
                    assessment_id=assessment.id,
                    requirement_id=req["id"],
                    chapter_id=req["chapter"],
                    compliance_level=GDPRComplianceLevel.NOT_EVALUATED,
                    requirements_met=[],
                    priority=req["priority"],
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
    # Requirement Responses
    # =========================================================================

    async def submit_requirement_response(
        self,
        assessment_id: str,
        data: RequirementResponseCreate,
        user_id: str,
        tenant_id: str,
    ) -> Optional[GDPRRequirementResponse]:
        """Submit or update a requirement response."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find existing response
        existing = None
        for resp in assessment.responses:
            if resp.requirement_id == data.requirement_id:
                existing = resp
                break

        if existing:
            # Update existing
            existing.compliance_level = data.compliance_level
            existing.evidence = data.evidence
            existing.notes = data.notes
            existing.gap_description = data.gap_description
            existing.remediation_plan = data.remediation_plan
            existing.requirements_met = data.requirements_met or []
            existing.priority = data.priority or 2
            existing.due_date = data.due_date
            existing.responsible = data.responsible
            existing.assessed_at = datetime.utcnow()
            existing.assessed_by = user_id
            response = existing
        else:
            # Create new
            req = next((r for r in GDPR_REQUIREMENTS if r["id"] == data.requirement_id), None)
            if not req:
                return None

            response = GDPRRequirementResponse(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                requirement_id=data.requirement_id,
                chapter_id=req["chapter"],
                compliance_level=data.compliance_level,
                evidence=data.evidence,
                notes=data.notes,
                gap_description=data.gap_description,
                remediation_plan=data.remediation_plan,
                requirements_met=data.requirements_met or [],
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

    async def bulk_update_requirements(
        self,
        assessment_id: str,
        responses: List[RequirementResponseCreate],
        user_id: str,
        tenant_id: str,
    ) -> List[GDPRRequirementResponse]:
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
    # Scoring
    # =========================================================================

    async def _recalculate_scores(self, assessment: GDPRAssessment):
        """Recalculate assessment scores."""
        if not assessment.responses:
            return

        # Calculate chapter scores
        chapter_scores = {}
        chapter_weights = {}

        for chapter in GDPR_CHAPTERS:
            chapter_id = chapter["id"]
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter_id
            ]

            if chapter_responses:
                # Score calculation: Fully=100, Partial=50, Non=0, N/A=excluded
                scored_responses = [
                    r for r in chapter_responses
                    if r.compliance_level != GDPRComplianceLevel.NOT_EVALUATED
                ]

                if scored_responses:
                    total_score = 0
                    total_weight = 0

                    for resp in scored_responses:
                        req = next(
                            (r for r in GDPR_REQUIREMENTS if r["id"] == resp.requirement_id),
                            None
                        )
                        weight = req["weight"] if req else 10

                        if resp.compliance_level == GDPRComplianceLevel.FULLY_COMPLIANT:
                            total_score += 100 * weight
                            total_weight += weight
                        elif resp.compliance_level == GDPRComplianceLevel.PARTIALLY_COMPLIANT:
                            total_score += 50 * weight
                            total_weight += weight
                        elif resp.compliance_level == GDPRComplianceLevel.NON_COMPLIANT:
                            total_score += 0
                            total_weight += weight
                        # NOT_APPLICABLE is excluded

                    if total_weight > 0:
                        chapter_scores[chapter_id] = round(total_score / total_weight, 1)
                        chapter_weights[chapter_id] = total_weight

        assessment.chapter_scores = chapter_scores

        # Overall score (weighted average)
        if chapter_scores:
            total_weighted = sum(
                chapter_scores[ch] * chapter_weights.get(ch, 1)
                for ch in chapter_scores
            )
            total_weights = sum(chapter_weights.get(ch, 1) for ch in chapter_scores)
            assessment.overall_score = round(total_weighted / total_weights, 1) if total_weights else 0

        # Count gaps (non-compliant or partially compliant)
        gaps = [
            r for r in assessment.responses
            if r.compliance_level in [
                GDPRComplianceLevel.NON_COMPLIANT,
                GDPRComplianceLevel.PARTIALLY_COMPLIANT,
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
        gaps_by_chapter = {}
        gaps_by_priority = {1: 0, 2: 0, 3: 0, 4: 0}

        for response in assessment.responses:
            if response.compliance_level in [
                GDPRComplianceLevel.NON_COMPLIANT,
                GDPRComplianceLevel.PARTIALLY_COMPLIANT,
            ]:
                req = next(
                    (r for r in GDPR_REQUIREMENTS if r["id"] == response.requirement_id),
                    None
                )
                if req:
                    chapter = next(
                        (ch for ch in GDPR_CHAPTERS if ch["id"] == response.chapter_id),
                        None
                    )

                    # Calculate impact score
                    compliance_factor = 0 if response.compliance_level == GDPRComplianceLevel.NON_COMPLIANT else 0.5
                    impact_score = req["weight"] * (1 - compliance_factor) * (5 - response.priority) / 4

                    gap = GapItem(
                        requirement_id=response.requirement_id,
                        requirement_name=req["name_de"],
                        chapter_id=response.chapter_id,
                        chapter_name=chapter["name_de"] if chapter else "",
                        article=req["article"],
                        compliance_level=response.compliance_level,
                        priority=response.priority,
                        weight=req["weight"],
                        impact_score=round(impact_score, 2),
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
        for chapter in GDPR_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            if chapter_responses:
                assessed = [r for r in chapter_responses if r.assessed_at]
                compliant = [
                    r for r in chapter_responses
                    if r.compliance_level == GDPRComplianceLevel.FULLY_COMPLIANT
                ]
                gap_count = len([
                    r for r in chapter_responses
                    if r.compliance_level in [
                        GDPRComplianceLevel.NON_COMPLIANT,
                        GDPRComplianceLevel.PARTIALLY_COMPLIANT,
                    ]
                ])

                summary = ChapterSummary(
                    chapter_id=chapter["id"],
                    chapter_name=chapter["name_de"],
                    requirement_count=len(chapter_responses),
                    assessed_count=len(assessed),
                    compliant_count=len(compliant),
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
            overall_compliance=assessment.overall_score,
            gaps=gaps[:50],  # Top 50 gaps
            chapter_summaries=chapter_summaries,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        gaps: List[GapItem],
        assessment: GDPRAssessment,
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        if not gaps:
            recommendations.append(
                "Alle Anforderungen erfüllt. Dokumentation aktualisieren und "
                "regelmäßige Überprüfungen planen."
            )
            return recommendations

        # Priority 1 gaps
        p1_gaps = [g for g in gaps if g.priority == 1]
        if p1_gaps:
            recommendations.append(
                f"Sofortmaßnahmen: {len(p1_gaps)} kritische Lücken mit höchster "
                f"Priorität beheben. Fokus auf: {', '.join(g.requirement_name[:25] for g in p1_gaps[:3])}"
            )

        # DPO requirement
        if assessment.requires_dpo and not assessment.dpo_appointed:
            recommendations.append(
                "Datenschutzbeauftragten (DSB) gemäß Art. 37 DSGVO ernennen. "
                "Kontaktdaten veröffentlichen."
            )

        # Data subject rights
        rights_gaps = [g for g in gaps if g.chapter_id == "chapter_3"]
        if rights_gaps:
            recommendations.append(
                f"Betroffenenrechte: {len(rights_gaps)} Lücken in Kapitel 3. "
                f"Prozesse für Auskunft, Löschung und Berichtigung implementieren."
            )

        # Security and breach notification
        security_gaps = [
            g for g in gaps
            if g.requirement_id in ["GDPR-4.6", "GDPR-4.7"]
        ]
        if security_gaps:
            recommendations.append(
                "Sicherheitsmaßnahmen und Meldeprozesse für Datenschutzverletzungen "
                "verbessern (Art. 32-34)."
            )

        # DPIA
        if assessment.large_scale_processing or assessment.systematic_monitoring:
            dpia_gap = next((g for g in gaps if g.requirement_id == "GDPR-4.8"), None)
            if dpia_gap:
                recommendations.append(
                    "Datenschutz-Folgenabschätzung (DSFA) für risikoreiche "
                    "Verarbeitungstätigkeiten durchführen (Art. 35)."
                )

        # International transfers
        if assessment.cross_border_processing:
            transfer_gaps = [g for g in gaps if g.chapter_id == "chapter_5"]
            if transfer_gaps:
                recommendations.append(
                    "Internationale Datenübermittlungen absichern: SCCs, BCRs "
                    "oder andere geeignete Garantien implementieren."
                )

        # Processing records
        records_gap = next((g for g in gaps if g.requirement_id == "GDPR-4.5"), None)
        if records_gap:
            recommendations.append(
                "Verzeichnis von Verarbeitungstätigkeiten (Art. 30) erstellen "
                "und regelmäßig aktualisieren."
            )

        # Low score chapters
        low_chapters = [
            ch for ch in GDPR_CHAPTERS
            if assessment.chapter_scores.get(ch["id"], 0) < 50
        ]
        if low_chapters:
            recommendations.append(
                f"Kapitel mit niedrigem Score priorisieren: "
                f"{', '.join(ch['name_de'] for ch in low_chapters[:3])}"
            )

        return recommendations[:6]

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard_stats(self, tenant_id: str) -> DashboardStats:
        """Get dashboard statistics."""
        # Get all assessments
        assessments, total = await self.list_assessments(tenant_id, size=1000)

        completed = [a for a in assessments if a.status == GDPRAssessmentStatus.COMPLETED]
        in_progress = [a for a in assessments if a.status == GDPRAssessmentStatus.IN_PROGRESS]

        # Calculate averages
        avg_score = sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0

        # Total gaps
        total_gaps = sum(a.gaps_count for a in assessments)
        critical_gaps = sum(a.critical_gaps_count for a in assessments)

        # Count special processing
        with_dpo = len([a for a in assessments if a.dpo_appointed])
        with_special = len([a for a in assessments if a.processes_special_categories])

        # Compliance distribution (across all assessments)
        compliance_dist = ComplianceDistribution(
            not_evaluated=0,
            non_compliant=0,
            partially_compliant=0,
            fully_compliant=0,
            not_applicable=0,
        )

        for assessment in assessments:
            full_assessment = await self.get_assessment(assessment.id, tenant_id)
            if full_assessment:
                for resp in full_assessment.responses:
                    if resp.compliance_level == GDPRComplianceLevel.NOT_EVALUATED:
                        compliance_dist.not_evaluated += 1
                    elif resp.compliance_level == GDPRComplianceLevel.NON_COMPLIANT:
                        compliance_dist.non_compliant += 1
                    elif resp.compliance_level == GDPRComplianceLevel.PARTIALLY_COMPLIANT:
                        compliance_dist.partially_compliant += 1
                    elif resp.compliance_level == GDPRComplianceLevel.FULLY_COMPLIANT:
                        compliance_dist.fully_compliant += 1
                    elif resp.compliance_level == GDPRComplianceLevel.NOT_APPLICABLE:
                        compliance_dist.not_applicable += 1

        # Recent assessments
        recent = sorted(assessments, key=lambda a: a.updated_at, reverse=True)[:5]

        return DashboardStats(
            total_assessments=total,
            completed_assessments=len(completed),
            in_progress_assessments=len(in_progress),
            average_score=round(avg_score, 1),
            total_gaps=total_gaps,
            critical_gaps=critical_gaps,
            assessments_with_dpo=with_dpo,
            assessments_with_special_data=with_special,
            compliance_distribution=compliance_dist,
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
                name="Geltungsbereich",
                completed=assessment.organization_type is not None,
                current=False,
            ),
        ]

        # Add chapter steps
        for chapter in GDPR_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            assessed = all(
                r.compliance_level != GDPRComplianceLevel.NOT_EVALUATED
                for r in chapter_responses
            ) if chapter_responses else False
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
                completed=assessment.status == GDPRAssessmentStatus.COMPLETED,
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
    ) -> Optional[GDPRAssessment]:
        """Mark assessment as completed."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        assessment.status = GDPRAssessmentStatus.COMPLETED
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
        if assessment.overall_score >= 90 and assessment.gaps_count == 0:
            compliance_status = "compliant"
        elif assessment.overall_score >= 70:
            compliance_status = "partial"
        else:
            compliance_status = "non_compliant"

        # Chapter details
        chapter_details = []
        for chapter in GDPR_CHAPTERS:
            chapter_responses = [
                r for r in assessment.responses if r.chapter_id == chapter["id"]
            ]
            if chapter_responses:
                compliant = [
                    r for r in chapter_responses
                    if r.compliance_level == GDPRComplianceLevel.FULLY_COMPLIANT
                ]
                gap_count = len([
                    r for r in chapter_responses
                    if r.compliance_level in [
                        GDPRComplianceLevel.NON_COMPLIANT,
                        GDPRComplianceLevel.PARTIALLY_COMPLIANT,
                    ]
                ])

                score = assessment.chapter_scores.get(chapter["id"], 0)
                if score >= 90:
                    status = "compliant"
                elif score >= 50:
                    status = "partial"
                else:
                    status = "non_compliant"

                chapter_details.append(
                    ReportChapterDetail(
                        chapter_id=chapter["id"],
                        chapter_name=chapter["name_de"],
                        requirement_count=len(chapter_responses),
                        compliant_count=len(compliant),
                        gaps_count=gap_count,
                        score=score,
                        status=status,
                    )
                )

        # Executive summary
        exec_summary = (
            f"Diese DSGVO-Bewertung zeigt einen Gesamterfüllungsgrad von "
            f"{assessment.overall_score:.1f}%. Es wurden {assessment.gaps_count} Lücken "
            f"identifiziert, davon {assessment.critical_gaps_count} kritisch. "
        )

        if assessment.requires_dpo:
            if assessment.dpo_appointed:
                exec_summary += "Ein Datenschutzbeauftragter ist ernannt. "
            else:
                exec_summary += "ACHTUNG: Ein Datenschutzbeauftragter ist erforderlich aber nicht ernannt. "

        # Key strengths
        key_strengths = []
        for chapter in GDPR_CHAPTERS:
            score = assessment.chapter_scores.get(chapter["id"], 0)
            if score >= 80:
                key_strengths.append(f"{chapter['name_de']}: {score}% Erfüllung")

        # Critical findings
        critical_findings = []
        if gap_analysis:
            for gap in gap_analysis.gaps[:5]:
                if gap.priority == 1:
                    critical_findings.append(
                        f"{gap.requirement_name} (Art. {gap.article}): "
                        f"{'Nicht konform' if gap.compliance_level == GDPRComplianceLevel.NON_COMPLIANT else 'Teilweise konform'}"
                    )

        # Next steps
        next_steps = []
        if compliance_status == "compliant":
            next_steps.append("Dokumentation für Aufsichtsbehörde vorbereiten")
            next_steps.append("Regelmäßige Überprüfungen planen")
        else:
            next_steps.append("Kritische Lücken priorisiert beheben")
            next_steps.append("Datenschutzprozesse dokumentieren")
            if not assessment.dpo_appointed and assessment.requires_dpo:
                next_steps.append("Datenschutzbeauftragten ernennen")

        # Risk areas
        high_risk_areas = []
        if assessment.processes_special_categories:
            high_risk_areas.append("Verarbeitung besonderer Datenkategorien (Art. 9)")
        if assessment.large_scale_processing:
            high_risk_areas.append("Umfangreiche Datenverarbeitung")
        if assessment.cross_border_processing:
            high_risk_areas.append("Grenzüberschreitende Datenübermittlung")

        # Data subject rights status
        rights_chapter = assessment.chapter_scores.get("chapter_3", 0)
        if rights_chapter >= 80:
            rights_status = "implementiert"
        elif rights_chapter >= 50:
            rights_status = "teilweise implementiert"
        else:
            rights_status = "nicht ausreichend implementiert"

        # Security status
        security_score = assessment.chapter_scores.get("chapter_4", 0)
        if security_score >= 80:
            security_status = "angemessen"
        elif security_score >= 50:
            security_status = "verbesserungswürdig"
        else:
            security_status = "unzureichend"

        # Breach readiness
        breach_gap = next(
            (g for g in (gap_analysis.gaps if gap_analysis else [])
             if g.requirement_id == "GDPR-4.7"),
            None
        )
        if not breach_gap:
            breach_status = "vorbereitet"
        elif breach_gap.compliance_level == GDPRComplianceLevel.PARTIALLY_COMPLIANT:
            breach_status = "teilweise vorbereitet"
        else:
            breach_status = "nicht vorbereitet"

        # Compliance distribution
        compliance_dist = ComplianceDistribution(
            not_evaluated=0,
            non_compliant=0,
            partially_compliant=0,
            fully_compliant=0,
            not_applicable=0,
        )
        for resp in assessment.responses:
            if resp.compliance_level == GDPRComplianceLevel.NOT_EVALUATED:
                compliance_dist.not_evaluated += 1
            elif resp.compliance_level == GDPRComplianceLevel.NON_COMPLIANT:
                compliance_dist.non_compliant += 1
            elif resp.compliance_level == GDPRComplianceLevel.PARTIALLY_COMPLIANT:
                compliance_dist.partially_compliant += 1
            elif resp.compliance_level == GDPRComplianceLevel.FULLY_COMPLIANT:
                compliance_dist.fully_compliant += 1
            elif resp.compliance_level == GDPRComplianceLevel.NOT_APPLICABLE:
                compliance_dist.not_applicable += 1

        return AssessmentReportResponse(
            assessment_id=assessment_id,
            organization_name=assessment.name,
            generated_at=datetime.utcnow(),
            organization_type=assessment.organization_type or GDPROrganizationType.CONTROLLER,
            organization_size=assessment.organization_size or GDPROrganizationSize.MEDIUM,
            dpo_appointed=assessment.dpo_appointed,
            lead_authority=assessment.lead_authority,
            executive_summary=exec_summary,
            overall_score=assessment.overall_score,
            compliance_status=compliance_status,
            chapter_details=chapter_details,
            gaps=gap_analysis.gaps[:20] if gap_analysis else [],
            compliance_distribution=compliance_dist,
            key_strengths=key_strengths[:5],
            critical_findings=critical_findings,
            recommendations=gap_analysis.recommendations if gap_analysis else [],
            next_steps=next_steps,
            high_risk_areas=high_risk_areas,
            data_subject_rights_status=rights_status,
            security_measures_status=security_status,
            breach_readiness_status=breach_status,
        )
