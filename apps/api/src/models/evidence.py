"""
Evidence model with forensic hash chain integrity.
CRITICAL: This preserves the hash chain logic from src/models/evidence.py:92-128
"""
import enum
import hashlib
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Enum, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base
from src.models.mixins import ImmutableTenantMixin


class EvidenceType(str, enum.Enum):
    """Types of evidence entries."""
    OBSERVATION = "observation"  # Something observed
    ACTION = "action"  # Action taken
    DECISION = "decision"  # Decision made
    ARTIFACT = "artifact"  # File/artifact reference
    NOTE = "note"  # General note
    SYSTEM = "system"  # System-generated entry


class EvidenceEntry(ImmutableTenantMixin, Base):
    """
    Single evidence entry in the forensic chain.
    Implements append-only logging with hash chain verification.
    Note: Uses ImmutableTenantMixin because tenant_id must never change
    after creation to preserve forensic integrity.
    """
    __tablename__ = "evidence_entries"

    # Primary identification
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    entry_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )  # Format: EVD-{uuid}
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )

    # Hash chain fields - CRITICAL for forensic integrity
    sequence_number: Mapped[int] = mapped_column(Integer)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), index=True)

    # Entry content
    entry_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType))
    phase: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)

    # Artifact references (JSON array of artifact metadata)
    artifacts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Decision tracking (if entry_type is DECISION)
    decision_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decision_option: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    operator: Mapped[str] = mapped_column(String(255))  # Who made this entry
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Foreign key to user who created
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id")
    )

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of all meaningful fields.
        CRITICAL: This must match the original implementation for chain integrity.
        """
        hash_input = (
            f"{self.entry_id}"
            f"{self.incident_id}"
            f"{self.sequence_number}"
            f"{self.previous_hash or ''}"
            f"{self.entry_type.value}"
            f"{self.phase}"
            f"{self.description}"
            f"{self.operator}"
            f"{self.timestamp.isoformat()}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def finalize(self, previous_entry: Optional["EvidenceEntry"] = None) -> None:
        """
        Finalize entry by computing hash and linking to chain.
        Must be called before persisting.
        """
        if previous_entry:
            self.sequence_number = previous_entry.sequence_number + 1
            self.previous_hash = previous_entry.entry_hash
        else:
            self.sequence_number = 1
            self.previous_hash = None

        self.entry_hash = self.compute_hash()

    def verify_integrity(self) -> bool:
        """Verify this entry's hash matches its content."""
        return self.entry_hash == self.compute_hash()

    @staticmethod
    def generate_entry_id() -> str:
        """Generate unique entry ID."""
        return f"EVD-{uuid4().hex[:12].upper()}"


class EvidenceChainVerification:
    """
    Utility class for verifying evidence chain integrity.
    """

    @staticmethod
    def verify_chain(entries: List[EvidenceEntry]) -> tuple[bool, List[str]]:
        """
        Verify the integrity of an entire evidence chain.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not entries:
            return True, []

        # Sort by sequence number
        sorted_entries = sorted(entries, key=lambda e: e.sequence_number)

        # Check first entry
        first = sorted_entries[0]
        if first.sequence_number != 1:
            errors.append(f"Chain doesn't start at sequence 1 (starts at {first.sequence_number})")
        if first.previous_hash is not None:
            errors.append("First entry should have no previous hash")

        # Verify each entry
        for i, entry in enumerate(sorted_entries):
            # Verify entry hash
            if not entry.verify_integrity():
                errors.append(f"Entry {entry.entry_id} (seq {entry.sequence_number}) hash mismatch")

            # Verify chain linkage (except first entry)
            if i > 0:
                prev = sorted_entries[i - 1]
                if entry.previous_hash != prev.entry_hash:
                    errors.append(
                        f"Entry {entry.entry_id} (seq {entry.sequence_number}) "
                        f"chain broken: expected prev_hash {prev.entry_hash[:8]}..., "
                        f"got {entry.previous_hash[:8] if entry.previous_hash else 'None'}..."
                    )
                if entry.sequence_number != prev.sequence_number + 1:
                    errors.append(
                        f"Entry {entry.entry_id} sequence gap: "
                        f"expected {prev.sequence_number + 1}, got {entry.sequence_number}"
                    )

        return len(errors) == 0, errors
