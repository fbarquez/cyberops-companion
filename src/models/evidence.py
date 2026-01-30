"""
Evidence logging data model.

Provides append-only evidence logging with hash chain integrity.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import hashlib
import uuid


class EvidenceType(str, Enum):
    """Type of evidence entry."""
    OBSERVATION = "observation"  # Something observed/discovered
    ACTION = "action"            # Action taken by analyst
    DECISION = "decision"        # Decision made at a decision point
    ARTIFACT = "artifact"        # Evidence artifact reference
    NOTE = "note"                # General note or comment
    SYSTEM = "system"            # System-generated entry


class ArtifactReference(BaseModel):
    """
    Reference to an evidence artifact.

    Note: IR Companion does NOT store actual files, only references
    and hashes to maintain forensic integrity.
    """
    filename: str
    original_path: Optional[str] = None
    file_hash_sha256: str
    file_size_bytes: Optional[int] = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collection_method: str = Field(default="manual")
    notes: Optional[str] = None


class EvidenceEntry(BaseModel):
    """
    Single evidence log entry.

    Designed for append-only logging with hash chain integrity.
    Once created, entries should never be modified.
    """

    # Identification
    entry_id: str = Field(
        default_factory=lambda: f"EVD-{uuid.uuid4().hex[:12].upper()}"
    )
    incident_id: str

    # Sequence for hash chain
    sequence_number: int = Field(default=0)
    previous_hash: Optional[str] = None

    # Classification
    entry_type: EvidenceType = Field(default=EvidenceType.NOTE)
    phase: str = Field(default="")

    # Content
    description: str = Field(..., min_length=1)
    system_affected: Optional[str] = None

    # Forensic integrity tracking
    evidence_preserved: bool = Field(default=True)
    integrity_notes: Optional[str] = None

    # Artifact references (if type is ARTIFACT)
    artifacts: List[ArtifactReference] = Field(default_factory=list)

    # Decision tracking (if type is DECISION)
    decision_node_id: Optional[str] = None
    decision_option_selected: Optional[str] = None
    decision_rationale: Optional[str] = None

    # Metadata
    operator: str = Field(default="")
    tags: List[str] = Field(default_factory=list)

    # Timestamp (UTC, immutable after creation)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Computed hash of this entry
    entry_hash: Optional[str] = None

    class Config:
        use_enum_values = True

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of this entry for chain integrity.

        The hash includes all meaningful fields to detect tampering.
        """
        hash_content = (
            f"{self.entry_id}|"
            f"{self.incident_id}|"
            f"{self.sequence_number}|"
            f"{self.previous_hash or 'GENESIS'}|"
            f"{self.entry_type}|"
            f"{self.phase}|"
            f"{self.description}|"
            f"{self.system_affected or ''}|"
            f"{self.evidence_preserved}|"
            f"{self.operator}|"
            f"{self.timestamp.isoformat()}"
        )

        return hashlib.sha256(hash_content.encode("utf-8")).hexdigest()

    def finalize(self, sequence: int, previous_hash: Optional[str] = None) -> None:
        """
        Finalize the entry with sequence number and hash chain.

        Should be called once when adding to the evidence log.
        """
        self.sequence_number = sequence
        self.previous_hash = previous_hash
        self.entry_hash = self.compute_hash()

    def verify_integrity(self) -> bool:
        """Verify that the entry hash matches computed hash."""
        if not self.entry_hash:
            return False
        return self.entry_hash == self.compute_hash()

    def to_log_line(self) -> str:
        """Format entry as a single log line for display."""
        timestamp_str = self.timestamp.strftime("%H:%M:%S")
        type_str = self.entry_type.upper()[:8].ljust(8)
        return f"{timestamp_str} | {type_str} | {self.description[:60]}"


class EvidenceChain(BaseModel):
    """
    Complete evidence chain for an incident.

    Manages the append-only log with hash chain integrity.
    """

    incident_id: str
    entries: List[EvidenceEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def append(self, entry: EvidenceEntry) -> EvidenceEntry:
        """
        Append a new entry to the chain.

        Automatically assigns sequence number and computes hash chain.
        """
        if entry.incident_id != self.incident_id:
            raise ValueError("Entry incident_id does not match chain incident_id")

        sequence = len(self.entries)
        previous_hash = self.entries[-1].entry_hash if self.entries else None

        entry.finalize(sequence=sequence, previous_hash=previous_hash)
        self.entries.append(entry)

        return entry

    def verify_chain(self) -> tuple[bool, Optional[int]]:
        """
        Verify the integrity of the entire chain.

        Returns (is_valid, first_invalid_index).
        """
        for i, entry in enumerate(self.entries):
            # Verify entry's own hash
            if not entry.verify_integrity():
                return False, i

            # Verify chain linkage
            if i == 0:
                if entry.previous_hash is not None:
                    return False, i
            else:
                if entry.previous_hash != self.entries[i - 1].entry_hash:
                    return False, i

        return True, None

    def get_entries_by_phase(self, phase: str) -> List[EvidenceEntry]:
        """Get all entries for a specific phase."""
        return [e for e in self.entries if e.phase == phase]

    def get_entries_by_type(self, entry_type: EvidenceType) -> List[EvidenceEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.entry_type == entry_type]

    def get_decisions(self) -> List[EvidenceEntry]:
        """Get all decision entries."""
        return self.get_entries_by_type(EvidenceType.DECISION)

    def export_hashes(self) -> List[dict]:
        """Export hash chain for verification."""
        return [
            {
                "sequence": e.sequence_number,
                "entry_id": e.entry_id,
                "timestamp": e.timestamp.isoformat(),
                "previous_hash": e.previous_hash,
                "entry_hash": e.entry_hash,
            }
            for e in self.entries
        ]
