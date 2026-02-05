"""
ISO 27001:2022 Compliance Service.

Business logic for ISO 27001 controls, assessments, scoring, and gap analysis.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.iso27001 import (
    ISO27001Control, ISO27001Assessment, ISO27001SoAEntry,
    ISO27001Theme, ISO27001AssessmentStatus,
    ISO27001Applicability, ISO27001ComplianceStatus
)
from src.schemas.iso27001 import (
    AssessmentCreate, AssessmentScopeUpdate, SoAEntryUpdate,
    ThemeInfo, ThemeOverview, GapItem
)


class ISO27001Service:
    """Service for ISO 27001:2022 compliance management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Theme Methods ==========

    async def get_themes(self) -> List[ThemeInfo]:
        """Get all ISO 27001 themes with control counts."""
        themes = []
        theme_info = {
            ISO27001Theme.ORGANIZATIONAL: ("Organizational", "Organizational controls for policies, roles, and governance"),
            ISO27001Theme.PEOPLE: ("People", "People controls for HR security and awareness"),
            ISO27001Theme.PHYSICAL: ("Physical", "Physical and environmental security controls"),
            ISO27001Theme.TECHNOLOGICAL: ("Technological", "Technological controls for systems and networks"),
        }

        for theme in ISO27001Theme:
            result = await self.db.execute(
                select(func.count(ISO27001Control.id))
                .where(ISO27001Control.theme == theme)
            )
            count = result.scalar() or 0

            name, desc = theme_info.get(theme, (theme.name, None))
            themes.append(ThemeInfo(
                theme_id=theme.value,
                name=name,
                control_count=count,
                description=desc
            ))

        return themes

    # ========== Control Methods ==========

    async def get_controls(
        self,
        theme: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[ISO27001Control], int]:
        """Get controls with optional filtering."""
        query = select(ISO27001Control)

        # Filter by theme
        if theme:
            try:
                theme_enum = ISO27001Theme(theme)
                query = query.where(ISO27001Control.theme == theme_enum)
            except ValueError:
                pass

        # Search in title and description
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    ISO27001Control.title_en.ilike(search_term),
                    ISO27001Control.title_de.ilike(search_term),
                    ISO27001Control.control_id.ilike(search_term),
                    ISO27001Control.description_en.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate and order
        query = query.order_by(ISO27001Control.sort_order)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        controls = result.scalars().all()

        return list(controls), total

    async def get_control(self, control_id: str) -> Optional[ISO27001Control]:
        """Get a single control by ID or control_id."""
        # Try by UUID first
        result = await self.db.execute(
            select(ISO27001Control).where(ISO27001Control.id == control_id)
        )
        control = result.scalar_one_or_none()

        if not control:
            # Try by control_id (e.g., A.5.1)
            result = await self.db.execute(
                select(ISO27001Control).where(ISO27001Control.control_id == control_id)
            )
            control = result.scalar_one_or_none()

        return control

    # ========== Assessment Methods ==========

    async def get_dashboard_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for the tenant."""
        # Count assessments by status
        result = await self.db.execute(
            select(ISO27001Assessment)
            .where(ISO27001Assessment.tenant_id == tenant_id)
        )
        assessments = result.scalars().all()

        total = len(assessments)
        active = sum(1 for a in assessments if a.status not in [
            ISO27001AssessmentStatus.COMPLETED,
            ISO27001AssessmentStatus.ARCHIVED
        ])
        completed = sum(1 for a in assessments if a.status == ISO27001AssessmentStatus.COMPLETED)

        # Calculate average score from completed assessments
        scores = [a.overall_score for a in assessments if a.overall_score is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        # Get theme scores from latest completed assessment
        theme_scores = {}
        completed_assessments = [a for a in assessments if a.status == ISO27001AssessmentStatus.COMPLETED]
        if completed_assessments:
            latest = max(completed_assessments, key=lambda a: a.completed_at or a.created_at)
            theme_scores = {
                "A.5": latest.organizational_score,
                "A.6": latest.people_score,
                "A.7": latest.physical_score,
                "A.8": latest.technological_score,
            }

        # Get recent assessments
        recent = sorted(assessments, key=lambda a: a.created_at, reverse=True)[:5]

        return {
            "total_assessments": total,
            "active_assessments": active,
            "completed_assessments": completed,
            "total_controls": 93,
            "average_compliance_score": avg_score,
            "theme_scores": theme_scores,
            "recent_assessments": recent,
        }

    async def create_assessment(
        self,
        tenant_id: str,
        data: AssessmentCreate,
        created_by: str
    ) -> ISO27001Assessment:
        """Create a new assessment and initialize SoA entries."""
        # Create assessment
        assessment = ISO27001Assessment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=ISO27001AssessmentStatus.DRAFT,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        self.db.add(assessment)
        await self.db.flush()

        # Initialize SoA entries for all controls
        controls_result = await self.db.execute(select(ISO27001Control))
        controls = controls_result.scalars().all()

        for control in controls:
            soa_entry = ISO27001SoAEntry(
                id=str(uuid4()),
                assessment_id=assessment.id,
                control_id=control.id,
                applicability=ISO27001Applicability.APPLICABLE,
                status=ISO27001ComplianceStatus.NOT_EVALUATED,
                created_at=datetime.utcnow(),
            )
            self.db.add(soa_entry)

        await self.db.flush()
        return assessment

    async def get_assessment(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[ISO27001Assessment]:
        """Get an assessment by ID."""
        result = await self.db.execute(
            select(ISO27001Assessment)
            .where(
                and_(
                    ISO27001Assessment.id == assessment_id,
                    ISO27001Assessment.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ISO27001Assessment], int]:
        """List assessments for a tenant."""
        query = select(ISO27001Assessment).where(
            ISO27001Assessment.tenant_id == tenant_id
        )

        if status:
            try:
                status_enum = ISO27001AssessmentStatus(status)
                query = query.where(ISO27001Assessment.status == status_enum)
            except ValueError:
                pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(ISO27001Assessment.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        return list(assessments), total

    async def delete_assessment(self, assessment_id: str, tenant_id: str) -> bool:
        """Delete an assessment and its SoA entries."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return False

        await self.db.delete(assessment)
        return True

    async def update_assessment_scope(
        self,
        assessment_id: str,
        tenant_id: str,
        data: AssessmentScopeUpdate
    ) -> Optional[ISO27001Assessment]:
        """Update assessment scope."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Update scope fields
        if data.scope_description is not None:
            assessment.scope_description = data.scope_description
        if data.scope_systems:
            assessment.scope_systems = data.scope_systems
        if data.scope_locations:
            assessment.scope_locations = data.scope_locations
        if data.scope_processes:
            assessment.scope_processes = data.scope_processes
        if data.risk_appetite is not None:
            assessment.risk_appetite = data.risk_appetite

        # Update status if still in draft
        if assessment.status == ISO27001AssessmentStatus.DRAFT:
            assessment.status = ISO27001AssessmentStatus.SCOPING
            assessment.started_at = datetime.utcnow()

        assessment.updated_at = datetime.utcnow()
        return assessment

    # ========== SoA Methods ==========

    async def get_soa_entries(
        self,
        assessment_id: str,
        tenant_id: str,
        theme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get SoA entries for an assessment with control details."""
        # Verify assessment belongs to tenant
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return []

        # Query entries with control join
        query = (
            select(ISO27001SoAEntry, ISO27001Control)
            .join(ISO27001Control, ISO27001SoAEntry.control_id == ISO27001Control.id)
            .where(ISO27001SoAEntry.assessment_id == assessment_id)
        )

        if theme:
            try:
                theme_enum = ISO27001Theme(theme)
                query = query.where(ISO27001Control.theme == theme_enum)
            except ValueError:
                pass

        query = query.order_by(ISO27001Control.sort_order)
        result = await self.db.execute(query)
        rows = result.all()

        entries = []
        for soa_entry, control in rows:
            entry_dict = {
                "id": soa_entry.id,
                "assessment_id": soa_entry.assessment_id,
                "control_id": soa_entry.control_id,
                "control_code": control.control_id,
                "control_title": control.title_en,
                "control_theme": control.theme.value,
                "applicability": soa_entry.applicability.value,
                "justification": soa_entry.justification,
                "status": soa_entry.status.value,
                "implementation_level": soa_entry.implementation_level,
                "evidence": soa_entry.evidence,
                "implementation_notes": soa_entry.implementation_notes,
                "gap_description": soa_entry.gap_description,
                "remediation_plan": soa_entry.remediation_plan,
                "remediation_owner": soa_entry.remediation_owner,
                "remediation_due_date": soa_entry.remediation_due_date,
                "priority": soa_entry.priority,
                "assessed_by": soa_entry.assessed_by,
                "assessed_at": soa_entry.assessed_at,
                "created_at": soa_entry.created_at,
                "updated_at": soa_entry.updated_at,
            }
            entries.append(entry_dict)

        return entries

    async def update_soa_entry(
        self,
        assessment_id: str,
        control_code: str,
        tenant_id: str,
        data: SoAEntryUpdate,
        assessed_by: str
    ) -> Optional[ISO27001SoAEntry]:
        """Update a single SoA entry."""
        # Verify assessment belongs to tenant
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Find the control by control_id (code)
        control_result = await self.db.execute(
            select(ISO27001Control).where(ISO27001Control.control_id == control_code)
        )
        control = control_result.scalar_one_or_none()
        if not control:
            return None

        # Find the SoA entry
        result = await self.db.execute(
            select(ISO27001SoAEntry).where(
                and_(
                    ISO27001SoAEntry.assessment_id == assessment_id,
                    ISO27001SoAEntry.control_id == control.id
                )
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None

        # Update fields
        if data.applicability is not None:
            entry.applicability = data.applicability
        if data.justification is not None:
            entry.justification = data.justification
        if data.status is not None:
            entry.status = data.status
        if data.implementation_level is not None:
            entry.implementation_level = data.implementation_level
        if data.evidence is not None:
            entry.evidence = data.evidence
        if data.implementation_notes is not None:
            entry.implementation_notes = data.implementation_notes
        if data.gap_description is not None:
            entry.gap_description = data.gap_description
        if data.remediation_plan is not None:
            entry.remediation_plan = data.remediation_plan
        if data.remediation_owner is not None:
            entry.remediation_owner = data.remediation_owner
        if data.remediation_due_date is not None:
            entry.remediation_due_date = data.remediation_due_date
        if data.priority is not None:
            entry.priority = data.priority

        entry.assessed_by = assessed_by
        entry.assessed_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()

        # Update assessment status if needed
        if assessment.status in [ISO27001AssessmentStatus.SCOPING, ISO27001AssessmentStatus.DRAFT]:
            assessment.status = ISO27001AssessmentStatus.SOA

        return entry

    async def bulk_update_soa_entries(
        self,
        assessment_id: str,
        tenant_id: str,
        entries: Dict[str, SoAEntryUpdate],
        assessed_by: str
    ) -> int:
        """Bulk update SoA entries."""
        count = 0
        for control_code, data in entries.items():
            result = await self.update_soa_entry(
                assessment_id, control_code, tenant_id, data, assessed_by
            )
            if result:
                count += 1
        return count

    # ========== Scoring Methods ==========

    def calculate_score(
        self,
        compliant: int,
        partial: int,
        applicable: int
    ) -> Optional[float]:
        """
        Calculate compliance score.
        Formula: (compliant + 0.5 * partial) / applicable * 100
        """
        if applicable == 0:
            return None
        return ((compliant + 0.5 * partial) / applicable) * 100

    async def recalculate_assessment_scores(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[ISO27001Assessment]:
        """Recalculate all scores for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get all entries with controls
        entries = await self.get_soa_entries(assessment_id, tenant_id)

        # Initialize counters
        total_applicable = 0
        total_compliant = 0
        total_partial = 0
        total_gap = 0

        theme_counts: Dict[str, Dict[str, int]] = {
            "A.5": {"applicable": 0, "compliant": 0, "partial": 0},
            "A.6": {"applicable": 0, "compliant": 0, "partial": 0},
            "A.7": {"applicable": 0, "compliant": 0, "partial": 0},
            "A.8": {"applicable": 0, "compliant": 0, "partial": 0},
        }

        for entry in entries:
            if entry["applicability"] == "applicable":
                total_applicable += 1
                theme = entry["control_theme"]
                if theme in theme_counts:
                    theme_counts[theme]["applicable"] += 1

                status = entry["status"]
                if status == "compliant":
                    total_compliant += 1
                    theme_counts[theme]["compliant"] += 1
                elif status == "partial":
                    total_partial += 1
                    theme_counts[theme]["partial"] += 1
                elif status == "gap":
                    total_gap += 1

        # Update assessment
        assessment.applicable_controls = total_applicable
        assessment.compliant_controls = total_compliant
        assessment.partial_controls = total_partial
        assessment.gap_controls = total_gap

        # Calculate overall score
        assessment.overall_score = self.calculate_score(
            total_compliant, total_partial, total_applicable
        )

        # Calculate theme scores
        assessment.organizational_score = self.calculate_score(
            theme_counts["A.5"]["compliant"],
            theme_counts["A.5"]["partial"],
            theme_counts["A.5"]["applicable"]
        )
        assessment.people_score = self.calculate_score(
            theme_counts["A.6"]["compliant"],
            theme_counts["A.6"]["partial"],
            theme_counts["A.6"]["applicable"]
        )
        assessment.physical_score = self.calculate_score(
            theme_counts["A.7"]["compliant"],
            theme_counts["A.7"]["partial"],
            theme_counts["A.7"]["applicable"]
        )
        assessment.technological_score = self.calculate_score(
            theme_counts["A.8"]["compliant"],
            theme_counts["A.8"]["partial"],
            theme_counts["A.8"]["applicable"]
        )

        assessment.updated_at = datetime.utcnow()
        return assessment

    # ========== Overview Methods ==========

    async def get_assessment_overview(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed overview of an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Recalculate scores
        await self.recalculate_assessment_scores(assessment_id, tenant_id)

        entries = await self.get_soa_entries(assessment_id, tenant_id)

        # Build theme overviews
        themes_data: Dict[str, Dict[str, int]] = {}
        theme_names = {
            "A.5": "Organizational",
            "A.6": "People",
            "A.7": "Physical",
            "A.8": "Technological"
        }

        for entry in entries:
            theme = entry["control_theme"]
            if theme not in themes_data:
                themes_data[theme] = {
                    "total": 0, "applicable": 0, "compliant": 0,
                    "partial": 0, "gap": 0, "not_evaluated": 0
                }

            themes_data[theme]["total"] += 1
            if entry["applicability"] == "applicable":
                themes_data[theme]["applicable"] += 1
                status = entry["status"]
                if status == "compliant":
                    themes_data[theme]["compliant"] += 1
                elif status == "partial":
                    themes_data[theme]["partial"] += 1
                elif status == "gap":
                    themes_data[theme]["gap"] += 1
                elif status == "not_evaluated":
                    themes_data[theme]["not_evaluated"] += 1

        theme_overviews = []
        for theme_id, data in sorted(themes_data.items()):
            score = self.calculate_score(
                data["compliant"], data["partial"], data["applicable"]
            )
            theme_overviews.append(ThemeOverview(
                theme_id=theme_id,
                theme_name=theme_names.get(theme_id, theme_id),
                total_controls=data["total"],
                applicable_controls=data["applicable"],
                compliant_controls=data["compliant"],
                partial_controls=data["partial"],
                gap_controls=data["gap"],
                not_evaluated=data["not_evaluated"],
                score=score
            ))

        # Calculate completion percentage
        total_entries = len(entries)
        evaluated = sum(
            1 for e in entries
            if e["applicability"] != "applicable" or e["status"] != "not_evaluated"
        )
        completion = (evaluated / total_entries * 100) if total_entries > 0 else 0

        return {
            "assessment": assessment,
            "themes": theme_overviews,
            "total_applicable": assessment.applicable_controls,
            "total_compliant": assessment.compliant_controls,
            "total_partial": assessment.partial_controls,
            "total_gap": assessment.gap_controls,
            "overall_score": assessment.overall_score,
            "completion_percentage": completion,
        }

    # ========== Gap Analysis Methods ==========

    async def get_gap_analysis(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get gap analysis for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get entries with gaps
        query = (
            select(ISO27001SoAEntry, ISO27001Control)
            .join(ISO27001Control, ISO27001SoAEntry.control_id == ISO27001Control.id)
            .where(
                and_(
                    ISO27001SoAEntry.assessment_id == assessment_id,
                    ISO27001SoAEntry.applicability == ISO27001Applicability.APPLICABLE,
                    ISO27001SoAEntry.status.in_([
                        ISO27001ComplianceStatus.GAP,
                        ISO27001ComplianceStatus.PARTIAL
                    ])
                )
            )
            .order_by(ISO27001SoAEntry.priority, ISO27001Control.sort_order)
        )

        result = await self.db.execute(query)
        rows = result.all()

        gaps = []
        gaps_by_priority: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        gaps_by_theme: Dict[str, int] = {}

        for soa_entry, control in rows:
            gap_item = GapItem(
                control_id=soa_entry.control_id,
                control_code=control.control_id,
                control_title=control.title_en,
                theme=control.theme.value,
                status=soa_entry.status,
                implementation_level=soa_entry.implementation_level,
                gap_description=soa_entry.gap_description,
                remediation_plan=soa_entry.remediation_plan,
                remediation_owner=soa_entry.remediation_owner,
                remediation_due_date=soa_entry.remediation_due_date,
                priority=soa_entry.priority,
                cross_references=control.cross_references or {}
            )
            gaps.append(gap_item)

            # Count by priority
            gaps_by_priority[soa_entry.priority] = gaps_by_priority.get(soa_entry.priority, 0) + 1

            # Count by theme
            theme = control.theme.value
            gaps_by_theme[theme] = gaps_by_theme.get(theme, 0) + 1

        return {
            "assessment_id": assessment_id,
            "assessment_name": assessment.name,
            "total_gaps": len(gaps),
            "gaps_by_priority": gaps_by_priority,
            "gaps_by_theme": gaps_by_theme,
            "gaps": gaps,
        }

    # ========== Cross-Framework Mapping Methods ==========

    async def get_cross_framework_mapping(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cross-framework mapping for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get all entries with controls
        query = (
            select(ISO27001SoAEntry, ISO27001Control)
            .join(ISO27001Control, ISO27001SoAEntry.control_id == ISO27001Control.id)
            .where(ISO27001SoAEntry.assessment_id == assessment_id)
            .order_by(ISO27001Control.sort_order)
        )

        result = await self.db.execute(query)
        rows = result.all()

        mappings = []
        total_bsi = 0
        total_nis2 = 0
        total_nist = 0
        frameworks_referenced = set()

        for soa_entry, control in rows:
            cross_refs = control.cross_references or {}
            related_controls = []

            # BSI Grundschutz
            for ref in cross_refs.get("bsi_grundschutz", []):
                related_controls.append({
                    "framework": "BSI IT-Grundschutz",
                    "control_id": ref,
                    "control_name": None
                })
                total_bsi += 1
                frameworks_referenced.add("BSI IT-Grundschutz")

            # NIS2
            for ref in cross_refs.get("nis2", []):
                related_controls.append({
                    "framework": "NIS2 Directive",
                    "control_id": ref,
                    "control_name": None
                })
                total_nis2 += 1
                frameworks_referenced.add("NIS2 Directive")

            # NIST CSF
            for ref in cross_refs.get("nist_csf", []):
                related_controls.append({
                    "framework": "NIST CSF",
                    "control_id": ref,
                    "control_name": None
                })
                total_nist += 1
                frameworks_referenced.add("NIST CSF")

            mappings.append({
                "control_id": soa_entry.control_id,
                "control_code": control.control_id,
                "control_title": control.title_en,
                "theme": control.theme.value,
                "status": soa_entry.status.value if soa_entry.applicability == ISO27001Applicability.APPLICABLE else None,
                "related_controls": related_controls
            })

        return {
            "assessment_id": assessment_id,
            "mappings": mappings,
            "frameworks_referenced": list(frameworks_referenced),
            "total_bsi_references": total_bsi,
            "total_nis2_references": total_nis2,
            "total_nist_references": total_nist,
        }

    # ========== Wizard State Methods ==========

    async def get_wizard_state(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current wizard state for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Define steps
        steps = [
            {"step": 1, "name": "Scope", "status": "pending"},
            {"step": 2, "name": "Statement of Applicability", "status": "pending"},
            {"step": 3, "name": "Assessment", "status": "pending"},
            {"step": 4, "name": "Gap Analysis", "status": "pending"},
            {"step": 5, "name": "Cross-Framework Mapping", "status": "pending"},
            {"step": 6, "name": "Report", "status": "pending"},
        ]

        # Determine current step based on status
        status_to_step = {
            ISO27001AssessmentStatus.DRAFT: 1,
            ISO27001AssessmentStatus.SCOPING: 1,
            ISO27001AssessmentStatus.SOA: 2,
            ISO27001AssessmentStatus.ASSESSMENT: 3,
            ISO27001AssessmentStatus.GAP_ANALYSIS: 4,
            ISO27001AssessmentStatus.COMPLETED: 6,
            ISO27001AssessmentStatus.ARCHIVED: 6,
        }

        current_step = status_to_step.get(assessment.status, 1)

        # Update step statuses
        for step in steps:
            if step["step"] < current_step:
                step["status"] = "completed"
            elif step["step"] == current_step:
                step["status"] = "current"

        # Validation
        validation_errors = []
        can_proceed = True

        if current_step == 1 and not assessment.scope_description:
            validation_errors.append("Please define the assessment scope")
            can_proceed = False

        return {
            "assessment_id": assessment_id,
            "current_step": current_step,
            "step_name": steps[current_step - 1]["name"],
            "steps": steps,
            "is_complete": assessment.status == ISO27001AssessmentStatus.COMPLETED,
            "can_proceed": can_proceed,
            "validation_errors": validation_errors,
        }

    # ========== Complete Assessment Methods ==========

    async def complete_assessment(
        self,
        assessment_id: str,
        tenant_id: str,
        notes: Optional[str] = None
    ) -> Optional[ISO27001Assessment]:
        """Mark an assessment as complete."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Recalculate scores before completing
        await self.recalculate_assessment_scores(assessment_id, tenant_id)

        assessment.status = ISO27001AssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()

        return assessment
