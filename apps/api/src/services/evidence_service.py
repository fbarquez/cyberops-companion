"""Evidence service with hash chain integrity."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.evidence import EvidenceEntry, EvidenceType, EvidenceChainVerification
from src.schemas.evidence import EvidenceCreate, ChainVerificationResult


class EvidenceService:
    """Service for forensic evidence management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(
        self,
        incident_id: str,
        data: EvidenceCreate,
        user_id: str,
        operator_name: str,
        tenant_id: str,
    ) -> EvidenceEntry:
        """
        Create a new evidence entry with hash chain linkage.
        CRITICAL: Maintains forensic integrity through hash chain.
        """
        # Get the last entry for this incident to link the chain
        last_entry = await self._get_last_entry(incident_id)

        # Create new entry
        entry = EvidenceEntry(
            entry_id=EvidenceEntry.generate_entry_id(),
            incident_id=incident_id,
            entry_type=data.entry_type,
            phase=data.phase,
            description=data.description,
            artifacts=[a.model_dump() for a in data.artifacts] if data.artifacts else None,
            decision_id=data.decision_id,
            decision_option=data.decision_option,
            decision_rationale=data.decision_rationale,
            operator=operator_name,
            tags=data.tags or [],
            timestamp=datetime.utcnow(),
            created_by=user_id,
            tenant_id=tenant_id,
        )

        # Finalize with hash chain linkage
        entry.finalize(last_entry)

        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def _get_last_entry(self, incident_id: str) -> Optional[EvidenceEntry]:
        """Get the last evidence entry for an incident."""
        result = await self.db.execute(
            select(EvidenceEntry)
            .where(EvidenceEntry.incident_id == incident_id)
            .order_by(EvidenceEntry.sequence_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_entries(
        self,
        incident_id: str,
        phase: Optional[str] = None,
        entry_type: Optional[EvidenceType] = None,
    ) -> List[EvidenceEntry]:
        """Get evidence entries with optional filters."""
        query = select(EvidenceEntry).where(
            EvidenceEntry.incident_id == incident_id
        )

        if phase:
            query = query.where(EvidenceEntry.phase == phase)
        if entry_type:
            query = query.where(EvidenceEntry.entry_type == entry_type)

        query = query.order_by(EvidenceEntry.sequence_number)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_chain(self, incident_id: str) -> List[EvidenceEntry]:
        """Get complete evidence chain for an incident."""
        result = await self.db.execute(
            select(EvidenceEntry)
            .where(EvidenceEntry.incident_id == incident_id)
            .order_by(EvidenceEntry.sequence_number)
        )
        return list(result.scalars().all())

    async def verify_chain(self, incident_id: str) -> ChainVerificationResult:
        """
        Verify the integrity of the evidence chain.
        CRITICAL: This ensures forensic evidence hasn't been tampered with.
        """
        entries = await self.get_chain(incident_id)

        is_valid, errors = EvidenceChainVerification.verify_chain(entries)

        return ChainVerificationResult(
            incident_id=incident_id,
            is_valid=is_valid,
            total_entries=len(entries),
            verified_entries=len(entries) - len(errors),
            errors=errors,
            verified_at=datetime.utcnow(),
        )

    async def log_decision(
        self,
        incident_id: str,
        decision_id: str,
        option_id: str,
        option_label: str,
        rationale: Optional[str],
        user_id: str,
        operator_name: str,
        phase: str,
        tenant_id: str,
    ) -> EvidenceEntry:
        """Log a decision as an evidence entry."""
        data = EvidenceCreate(
            entry_type=EvidenceType.DECISION,
            phase=phase,
            description=f"Decision made: {option_label}",
            decision_id=decision_id,
            decision_option=option_id,
            decision_rationale=rationale,
            tags=["decision", decision_id],
        )
        return await self.create_entry(incident_id, data, user_id, operator_name, tenant_id)

    async def export_chain(
        self,
        incident_id: str,
        format: str = "markdown",
        include_hashes: bool = True,
    ) -> str:
        """Export evidence chain in specified format."""
        entries = await self.get_chain(incident_id)

        if format == "markdown":
            return self._export_markdown(entries, include_hashes)
        elif format == "json":
            return self._export_json(entries, include_hashes)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(
        self, entries: List[EvidenceEntry], include_hashes: bool
    ) -> str:
        """Export chain as markdown."""
        lines = ["# Evidence Chain\n"]

        for entry in entries:
            lines.append(f"## Entry {entry.sequence_number}: {entry.entry_id}")
            lines.append(f"- **Type:** {entry.entry_type.value}")
            lines.append(f"- **Phase:** {entry.phase}")
            lines.append(f"- **Timestamp:** {entry.timestamp.isoformat()}")
            lines.append(f"- **Operator:** {entry.operator}")
            lines.append(f"\n{entry.description}\n")

            if include_hashes:
                lines.append(f"- **Hash:** `{entry.entry_hash}`")
                if entry.previous_hash:
                    lines.append(f"- **Previous Hash:** `{entry.previous_hash}`")

            lines.append("\n---\n")

        return "\n".join(lines)

    def _export_json(
        self, entries: List[EvidenceEntry], include_hashes: bool
    ) -> str:
        """Export chain as JSON."""
        import json

        data = []
        for entry in entries:
            item = {
                "entry_id": entry.entry_id,
                "sequence_number": entry.sequence_number,
                "entry_type": entry.entry_type.value,
                "phase": entry.phase,
                "description": entry.description,
                "operator": entry.operator,
                "timestamp": entry.timestamp.isoformat(),
                "tags": entry.tags,
            }
            if include_hashes:
                item["entry_hash"] = entry.entry_hash
                item["previous_hash"] = entry.previous_hash
            if entry.artifacts:
                item["artifacts"] = entry.artifacts
            if entry.decision_id:
                item["decision"] = {
                    "id": entry.decision_id,
                    "option": entry.decision_option,
                    "rationale": entry.decision_rationale,
                }
            data.append(item)

        return json.dumps(data, indent=2)
