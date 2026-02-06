"""BSI IT-Grundschutz service for compliance management."""
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from src.services.base_service import TenantAwareService
from src.models.bsi_grundschutz import (
    BSIBaustein, BSIAnforderung, BSIComplianceStatus,
    BSIKategorie, BSIAnforderungTyp, BSISchutzbedarf,
    BSIComplianceStatusEnum, BSI_KATEGORIE_INFO
)


class BSIBausteinService:
    """Service for BSI Baustein catalog operations (global data)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kategorien_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all categories with Baustein counts.

        Returns:
            List of categories with counts and metadata
        """
        query = select(
            BSIBaustein.kategorie,
            func.count(BSIBaustein.id).label('baustein_count')
        ).group_by(BSIBaustein.kategorie).order_by(BSIBaustein.kategorie)

        result = await self.db.execute(query)
        rows = result.all()

        kategorien = []
        for row in rows:
            kategorie = row.kategorie
            info = BSI_KATEGORIE_INFO.get(kategorie, {})
            kategorien.append({
                "kategorie": kategorie.value,
                "name_de": info.get("name_de", kategorie.value),
                "name_en": info.get("name_en", kategorie.value),
                "description_de": info.get("description_de", ""),
                "description_en": info.get("description_en", ""),
                "icon": info.get("icon", "folder"),
                "baustein_count": row.baustein_count,
            })

        return kategorien

    async def list_bausteine(
        self,
        kategorie: Optional[BSIKategorie] = None,
        search: Optional[str] = None,
        ir_phase: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Tuple[List[BSIBaustein], int]:
        """List Bausteine with filters and pagination.

        Args:
            kategorie: Filter by category
            search: Search in title/description
            ir_phase: Filter by IR phase relevance
            page: Page number (1-indexed)
            size: Items per page

        Returns:
            Tuple of (list of Bausteine, total count)
        """
        query = select(BSIBaustein)

        if kategorie:
            query = query.where(BSIBaustein.kategorie == kategorie)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    BSIBaustein.titel.ilike(search_pattern),
                    BSIBaustein.title_en.ilike(search_pattern),
                    BSIBaustein.baustein_id.ilike(search_pattern),
                    BSIBaustein.beschreibung.ilike(search_pattern)
                )
            )

        if ir_phase:
            query = query.where(
                BSIBaustein.ir_phases.contains([ir_phase])
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply ordering and pagination
        query = query.order_by(BSIBaustein.kategorie, BSIBaustein.sort_order)
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        bausteine = result.scalars().all()

        return list(bausteine), total or 0

    async def get_baustein(self, baustein_id: str) -> Optional[BSIBaustein]:
        """Get a Baustein by baustein_id (e.g., 'DER.2.1').

        Args:
            baustein_id: The BSI baustein identifier

        Returns:
            Baustein if found, None otherwise
        """
        query = select(BSIBaustein).where(BSIBaustein.baustein_id == baustein_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_baustein_by_uuid(self, uuid: str) -> Optional[BSIBaustein]:
        """Get a Baustein by internal UUID.

        Args:
            uuid: The internal UUID

        Returns:
            Baustein if found, None otherwise
        """
        query = select(BSIBaustein).where(BSIBaustein.id == uuid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_baustein_with_anforderungen(
        self,
        baustein_id: str,
        schutzbedarf: Optional[BSISchutzbedarf] = None
    ) -> Optional[Dict[str, Any]]:
        """Get Baustein with its Anforderungen.

        Args:
            baustein_id: The BSI baustein identifier
            schutzbedarf: Optional filter by protection level

        Returns:
            Dict with baustein and anforderungen, or None if not found
        """
        baustein = await self.get_baustein(baustein_id)
        if not baustein:
            return None

        # Get Anforderungen
        query = select(BSIAnforderung).where(
            BSIAnforderung.baustein_fk == baustein.id
        )

        if schutzbedarf:
            # Filter by protection level (cumulative)
            if schutzbedarf == BSISchutzbedarf.basis:
                query = query.where(BSIAnforderung.typ == BSIAnforderungTyp.MUSS)
            elif schutzbedarf == BSISchutzbedarf.standard:
                query = query.where(
                    BSIAnforderung.typ.in_([BSIAnforderungTyp.MUSS, BSIAnforderungTyp.SOLLTE])
                )
            # HOCH includes all

        query = query.order_by(BSIAnforderung.sort_order)
        result = await self.db.execute(query)
        anforderungen = result.scalars().all()

        return {
            "baustein": baustein,
            "anforderungen": list(anforderungen),
            "anforderungen_count": {
                "muss": sum(1 for a in anforderungen if a.typ == BSIAnforderungTyp.MUSS),
                "sollte": sum(1 for a in anforderungen if a.typ == BSIAnforderungTyp.SOLLTE),
                "kann": sum(1 for a in anforderungen if a.typ == BSIAnforderungTyp.KANN),
                "total": len(anforderungen)
            }
        }


class BSIAnforderungService:
    """Service for BSI Anforderung operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_anforderungen(
        self,
        baustein_id: Optional[str] = None,
        typ: Optional[BSIAnforderungTyp] = None,
        schutzbedarf: Optional[BSISchutzbedarf] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> Tuple[List[BSIAnforderung], int]:
        """List Anforderungen with filters.

        Args:
            baustein_id: Filter by Baustein ID
            typ: Filter by requirement type (MUSS/SOLLTE/KANN)
            schutzbedarf: Filter by protection level
            search: Search in title/description
            page: Page number
            size: Items per page

        Returns:
            Tuple of (list of Anforderungen, total count)
        """
        query = select(BSIAnforderung)

        if baustein_id:
            # Join with Baustein to filter by baustein_id string
            subq = select(BSIBaustein.id).where(
                BSIBaustein.baustein_id == baustein_id
            ).scalar_subquery()
            query = query.where(BSIAnforderung.baustein_fk == subq)

        if typ:
            query = query.where(BSIAnforderung.typ == typ)

        if schutzbedarf:
            query = query.where(BSIAnforderung.schutzbedarf == schutzbedarf)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    BSIAnforderung.titel.ilike(search_pattern),
                    BSIAnforderung.anforderung_id.ilike(search_pattern),
                    BSIAnforderung.beschreibung.ilike(search_pattern)
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Apply ordering and pagination
        query = query.order_by(BSIAnforderung.anforderung_id)
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        anforderungen = result.scalars().all()

        return list(anforderungen), total or 0

    async def get_anforderung(self, anforderung_id: str) -> Optional[BSIAnforderung]:
        """Get Anforderung by ID (e.g., 'DER.2.1.A1').

        Args:
            anforderung_id: The BSI anforderung identifier

        Returns:
            Anforderung if found, None otherwise
        """
        query = select(BSIAnforderung).where(
            BSIAnforderung.anforderung_id == anforderung_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class BSIComplianceService(TenantAwareService[BSIComplianceStatus]):
    """Service for tenant-scoped BSI compliance status management."""

    model_class = BSIComplianceStatus

    async def get_compliance_status(
        self,
        anforderung_id: str,
        incident_id: Optional[str] = None
    ) -> Optional[BSIComplianceStatus]:
        """Get compliance status for an Anforderung.

        Args:
            anforderung_id: The BSI anforderung identifier
            incident_id: Optional incident ID

        Returns:
            Compliance status if found, None otherwise
        """
        # Get Anforderung FK
        anf_query = select(BSIAnforderung.id).where(
            BSIAnforderung.anforderung_id == anforderung_id
        )
        anf_result = await self.db.execute(anf_query)
        anf_fk = anf_result.scalar_one_or_none()
        if not anf_fk:
            return None

        query = self._base_query().where(
            BSIComplianceStatus.anforderung_fk == anf_fk
        )

        if incident_id:
            query = query.where(BSIComplianceStatus.incident_id == incident_id)
        else:
            query = query.where(BSIComplianceStatus.incident_id.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_compliance_status(
        self,
        anforderung_id: str,
        status: BSIComplianceStatusEnum,
        user_id: str,
        incident_id: Optional[str] = None,
        evidence_provided: Optional[List[Dict]] = None,
        notes: Optional[str] = None,
        gap_description: Optional[str] = None,
        remediation_plan: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> BSIComplianceStatus:
        """Update or create compliance status for an Anforderung.

        Args:
            anforderung_id: The BSI anforderung identifier
            status: New compliance status
            user_id: ID of user making the assessment
            incident_id: Optional incident ID
            evidence_provided: List of evidence items
            notes: Assessment notes
            gap_description: Description of compliance gap
            remediation_plan: Plan to address gap
            due_date: Due date for remediation

        Returns:
            Updated or created compliance status
        """
        # Get Anforderung FK
        anf_query = select(BSIAnforderung.id).where(
            BSIAnforderung.anforderung_id == anforderung_id
        )
        anf_result = await self.db.execute(anf_query)
        anf_fk = anf_result.scalar_one_or_none()
        if not anf_fk:
            raise ValueError(f"Anforderung {anforderung_id} not found")

        # Check for existing status
        existing = await self.get_compliance_status(anforderung_id, incident_id)

        if existing:
            existing.status = status
            existing.evidence_provided = evidence_provided or existing.evidence_provided
            existing.notes = notes if notes is not None else existing.notes
            existing.gap_description = gap_description if gap_description is not None else existing.gap_description
            existing.remediation_plan = remediation_plan if remediation_plan is not None else existing.remediation_plan
            existing.due_date = due_date if due_date is not None else existing.due_date
            existing.assessed_by = user_id
            existing.assessed_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            new_status = BSIComplianceStatus(
                id=str(uuid4()),
                anforderung_fk=anf_fk,
                incident_id=incident_id,
                status=status,
                evidence_provided=evidence_provided or [],
                notes=notes,
                gap_description=gap_description,
                remediation_plan=remediation_plan,
                due_date=due_date,
                assessed_by=user_id,
                assessed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            self._set_tenant_on_create(new_status)
            self.db.add(new_status)
            await self.db.flush()
            await self.db.refresh(new_status)
            return new_status

    async def get_baustein_compliance_score(
        self,
        baustein_id: str,
        schutzbedarf: BSISchutzbedarf = BSISchutzbedarf.standard,
        incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate compliance score for a Baustein.

        Args:
            baustein_id: The BSI baustein identifier
            schutzbedarf: Protection level to evaluate
            incident_id: Optional incident ID

        Returns:
            Dict with compliance score and breakdown
        """
        # Get Baustein
        baustein_query = select(BSIBaustein).where(
            BSIBaustein.baustein_id == baustein_id
        )
        baustein_result = await self.db.execute(baustein_query)
        baustein = baustein_result.scalar_one_or_none()
        if not baustein:
            raise ValueError(f"Baustein {baustein_id} not found")

        # Get relevant Anforderungen based on Schutzbedarf
        anf_query = select(BSIAnforderung).where(
            BSIAnforderung.baustein_fk == baustein.id
        )

        if schutzbedarf == BSISchutzbedarf.basis:
            anf_query = anf_query.where(BSIAnforderung.typ == BSIAnforderungTyp.MUSS)
        elif schutzbedarf == BSISchutzbedarf.standard:
            anf_query = anf_query.where(
                BSIAnforderung.typ.in_([BSIAnforderungTyp.MUSS, BSIAnforderungTyp.SOLLTE])
            )

        anf_result = await self.db.execute(anf_query)
        anforderungen = anf_result.scalars().all()

        if not anforderungen:
            return {
                "baustein_id": baustein_id,
                "schutzbedarf": schutzbedarf.value,
                "total_anforderungen": 0,
                "compliant": 0,
                "partial": 0,
                "gap": 0,
                "not_evaluated": 0,
                "not_applicable": 0,
                "score_percent": 0.0,
            }

        # Get compliance statuses
        anf_ids = [a.id for a in anforderungen]
        status_query = self._base_query().where(
            BSIComplianceStatus.anforderung_fk.in_(anf_ids)
        )

        if incident_id:
            status_query = status_query.where(
                BSIComplianceStatus.incident_id == incident_id
            )
        else:
            status_query = status_query.where(
                BSIComplianceStatus.incident_id.is_(None)
            )

        status_result = await self.db.execute(status_query)
        statuses = {s.anforderung_fk: s for s in status_result.scalars().all()}

        # Calculate scores
        counts = {
            "compliant": 0,
            "partial": 0,
            "gap": 0,
            "not_evaluated": 0,
            "not_applicable": 0,
        }

        for anf in anforderungen:
            status = statuses.get(anf.id)
            if status:
                counts[status.status.value] += 1
            else:
                counts["not_evaluated"] += 1

        total = len(anforderungen)
        applicable = total - counts["not_applicable"]
        if applicable > 0:
            score = (counts["compliant"] + 0.5 * counts["partial"]) / applicable * 100
        else:
            score = 100.0

        return {
            "baustein_id": baustein_id,
            "schutzbedarf": schutzbedarf.value,
            "total_anforderungen": total,
            **counts,
            "score_percent": round(score, 1),
        }

    async def get_compliance_overview(
        self,
        schutzbedarf: BSISchutzbedarf = BSISchutzbedarf.standard,
        incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get compliance overview by category.

        Args:
            schutzbedarf: Protection level to evaluate
            incident_id: Optional incident ID

        Returns:
            Dict with overall score and per-category breakdown
        """
        # Get all Bausteine
        baustein_query = select(BSIBaustein).order_by(
            BSIBaustein.kategorie, BSIBaustein.sort_order
        )
        baustein_result = await self.db.execute(baustein_query)
        bausteine = baustein_result.scalars().all()

        categories: Dict[str, Dict] = {}
        total_compliant = 0
        total_partial = 0
        total_gap = 0
        total_not_evaluated = 0
        total_not_applicable = 0
        total_anforderungen = 0

        for baustein in bausteine:
            score = await self.get_baustein_compliance_score(
                baustein.baustein_id, schutzbedarf, incident_id
            )

            kat = baustein.kategorie.value
            if kat not in categories:
                info = BSI_KATEGORIE_INFO.get(baustein.kategorie, {})
                categories[kat] = {
                    "name_de": info.get("name_de", kat),
                    "name_en": info.get("name_en", kat),
                    "bausteine": [],
                    "total_anforderungen": 0,
                    "compliant": 0,
                    "partial": 0,
                    "gap": 0,
                    "not_evaluated": 0,
                    "not_applicable": 0,
                }

            categories[kat]["bausteine"].append({
                "baustein_id": baustein.baustein_id,
                "titel": baustein.titel,
                "score_percent": score["score_percent"],
            })
            categories[kat]["total_anforderungen"] += score["total_anforderungen"]
            categories[kat]["compliant"] += score["compliant"]
            categories[kat]["partial"] += score["partial"]
            categories[kat]["gap"] += score["gap"]
            categories[kat]["not_evaluated"] += score["not_evaluated"]
            categories[kat]["not_applicable"] += score["not_applicable"]

            total_anforderungen += score["total_anforderungen"]
            total_compliant += score["compliant"]
            total_partial += score["partial"]
            total_gap += score["gap"]
            total_not_evaluated += score["not_evaluated"]
            total_not_applicable += score["not_applicable"]

        # Calculate category scores
        for kat, data in categories.items():
            applicable = data["total_anforderungen"] - data["not_applicable"]
            if applicable > 0:
                data["score_percent"] = round(
                    (data["compliant"] + 0.5 * data["partial"]) / applicable * 100, 1
                )
            else:
                data["score_percent"] = 100.0

        # Calculate overall score
        overall_applicable = total_anforderungen - total_not_applicable
        if overall_applicable > 0:
            overall_score = (total_compliant + 0.5 * total_partial) / overall_applicable * 100
        else:
            overall_score = 100.0

        return {
            "schutzbedarf": schutzbedarf.value,
            "overall_score_percent": round(overall_score, 1),
            "total_anforderungen": total_anforderungen,
            "compliant": total_compliant,
            "partial": total_partial,
            "gap": total_gap,
            "not_evaluated": total_not_evaluated,
            "not_applicable": total_not_applicable,
            "categories": categories,
        }

    async def bulk_update_status(
        self,
        updates: List[Dict[str, Any]],
        user_id: str
    ) -> List[BSIComplianceStatus]:
        """Bulk update compliance statuses.

        Args:
            updates: List of updates with anforderung_id and status
            user_id: ID of user making the assessments

        Returns:
            List of updated compliance statuses
        """
        results = []
        for update in updates:
            status = await self.update_compliance_status(
                anforderung_id=update["anforderung_id"],
                status=BSIComplianceStatusEnum(update["status"]),
                user_id=user_id,
                incident_id=update.get("incident_id"),
                evidence_provided=update.get("evidence_provided"),
                notes=update.get("notes"),
                gap_description=update.get("gap_description"),
                remediation_plan=update.get("remediation_plan"),
                due_date=update.get("due_date"),
            )
            results.append(status)
        return results
