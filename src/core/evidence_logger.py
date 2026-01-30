"""
Evidence Logger

Provides append-only evidence logging with forensic integrity features.
"""

import sys
from pathlib import Path as PathLib

# Add project root to path for imports
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path
import json
import sqlite3
from contextlib import contextmanager

from src.models.evidence import (
    EvidenceEntry,
    EvidenceType,
    EvidenceChain,
    ArtifactReference,
)
from config import DATA_DIR, get_config


class EvidenceLogger:
    """
    Manages forensic-grade evidence logging.

    Features:
    - Append-only log (no deletions, no modifications)
    - Hash chain integrity
    - SQLite storage for persistence
    - Export capabilities
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the evidence logger.

        Args:
            db_path: Path to SQLite database (uses config default if not specified)
        """
        self.db_path = db_path or get_config().database.db_path
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT UNIQUE NOT NULL,
                    incident_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    previous_hash TEXT,
                    entry_type TEXT NOT NULL,
                    phase TEXT,
                    description TEXT NOT NULL,
                    system_affected TEXT,
                    evidence_preserved INTEGER DEFAULT 1,
                    integrity_notes TEXT,
                    artifacts_json TEXT,
                    decision_node_id TEXT,
                    decision_option_selected TEXT,
                    decision_rationale TEXT,
                    operator TEXT,
                    tags_json TEXT,
                    timestamp TEXT NOT NULL,
                    entry_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_incident
                ON evidence_entries(incident_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_phase
                ON evidence_entries(incident_id, phase)
            """)

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_entry(
        self,
        incident_id: str,
        description: str,
        entry_type: EvidenceType = EvidenceType.NOTE,
        phase: str = "",
        system_affected: Optional[str] = None,
        operator: str = "",
        tags: Optional[List[str]] = None,
        evidence_preserved: bool = True,
        integrity_notes: Optional[str] = None,
    ) -> EvidenceEntry:
        """
        Log a new evidence entry.

        This is the primary method for adding entries to the log.
        The entry is automatically assigned a sequence number and hash.

        Args:
            incident_id: ID of the incident
            description: Description of what was observed/done
            entry_type: Type of entry (observation, action, decision, etc.)
            phase: Current IR phase
            system_affected: System this entry relates to
            operator: Name/ID of the operator
            tags: List of tags for categorization
            evidence_preserved: Whether evidence integrity was maintained
            integrity_notes: Notes about evidence handling

        Returns:
            The created EvidenceEntry with hash chain applied
        """
        entry = EvidenceEntry(
            incident_id=incident_id,
            entry_type=entry_type,
            phase=phase,
            description=description,
            system_affected=system_affected,
            operator=operator,
            tags=tags or [],
            evidence_preserved=evidence_preserved,
            integrity_notes=integrity_notes,
        )

        return self._persist_entry(entry)

    def log_decision(
        self,
        incident_id: str,
        description: str,
        decision_node_id: str,
        decision_option_selected: str,
        phase: str = "",
        operator: str = "",
        rationale: Optional[str] = None,
    ) -> EvidenceEntry:
        """
        Log a decision entry.

        Specialized method for logging decisions made at decision points.
        """
        entry = EvidenceEntry(
            incident_id=incident_id,
            entry_type=EvidenceType.DECISION,
            phase=phase,
            description=description,
            operator=operator,
            decision_node_id=decision_node_id,
            decision_option_selected=decision_option_selected,
            decision_rationale=rationale,
        )

        return self._persist_entry(entry)

    def log_artifact(
        self,
        incident_id: str,
        description: str,
        artifact: ArtifactReference,
        phase: str = "",
        operator: str = "",
    ) -> EvidenceEntry:
        """
        Log an artifact reference.

        Note: This logs a reference to the artifact (including its hash),
        NOT the artifact itself. The actual artifact should be stored
        separately using proper chain of custody procedures.
        """
        entry = EvidenceEntry(
            incident_id=incident_id,
            entry_type=EvidenceType.ARTIFACT,
            phase=phase,
            description=description,
            operator=operator,
            artifacts=[artifact],
        )

        return self._persist_entry(entry)

    def _persist_entry(self, entry: EvidenceEntry) -> EvidenceEntry:
        """Persist an entry to the database with hash chain."""
        with self._get_connection() as conn:
            # Get the last entry for this incident to build hash chain
            cursor = conn.execute(
                """
                SELECT sequence_number, entry_hash
                FROM evidence_entries
                WHERE incident_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
                """,
                (entry.incident_id,),
            )
            row = cursor.fetchone()

            if row:
                sequence = row["sequence_number"] + 1
                previous_hash = row["entry_hash"]
            else:
                sequence = 0
                previous_hash = None

            # Finalize the entry with hash chain
            entry.finalize(sequence=sequence, previous_hash=previous_hash)

            # Insert into database
            conn.execute(
                """
                INSERT INTO evidence_entries (
                    entry_id, incident_id, sequence_number, previous_hash,
                    entry_type, phase, description, system_affected,
                    evidence_preserved, integrity_notes, artifacts_json,
                    decision_node_id, decision_option_selected, decision_rationale,
                    operator, tags_json, timestamp, entry_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.incident_id,
                    entry.sequence_number,
                    entry.previous_hash,
                    entry.entry_type,
                    entry.phase,
                    entry.description,
                    entry.system_affected,
                    1 if entry.evidence_preserved else 0,
                    entry.integrity_notes,
                    json.dumps([a.model_dump() for a in entry.artifacts]),
                    entry.decision_node_id,
                    entry.decision_option_selected,
                    entry.decision_rationale,
                    entry.operator,
                    json.dumps(entry.tags),
                    entry.timestamp.isoformat(),
                    entry.entry_hash,
                ),
            )

        return entry

    def get_entries(
        self,
        incident_id: str,
        phase: Optional[str] = None,
        entry_type: Optional[EvidenceType] = None,
        limit: Optional[int] = None,
    ) -> List[EvidenceEntry]:
        """
        Retrieve evidence entries.

        Args:
            incident_id: ID of the incident
            phase: Filter by phase (optional)
            entry_type: Filter by entry type (optional)
            limit: Maximum number of entries to return

        Returns:
            List of EvidenceEntry objects
        """
        query = "SELECT * FROM evidence_entries WHERE incident_id = ?"
        params: list = [incident_id]

        if phase:
            query += " AND phase = ?"
            params.append(phase)

        if entry_type:
            query += " AND entry_type = ?"
            params.append(entry_type.value if isinstance(entry_type, EvidenceType) else entry_type)

        query += " ORDER BY sequence_number ASC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_chain(self, incident_id: str) -> EvidenceChain:
        """Get the complete evidence chain for an incident."""
        entries = self.get_entries(incident_id)
        chain = EvidenceChain(incident_id=incident_id, entries=entries)
        return chain

    def verify_chain(self, incident_id: str) -> tuple[bool, Optional[int], str]:
        """
        Verify the integrity of an incident's evidence chain.

        Returns:
            Tuple of (is_valid, first_invalid_index, message)
        """
        chain = self.get_chain(incident_id)

        if not chain.entries:
            return True, None, "No entries to verify"

        is_valid, invalid_idx = chain.verify_chain()

        if is_valid:
            return True, None, f"Chain verified: {len(chain.entries)} entries intact"
        else:
            return (
                False,
                invalid_idx,
                f"Chain integrity failure at entry {invalid_idx}",
            )

    def export_chain(
        self, incident_id: str, include_hashes: bool = True
    ) -> dict:
        """
        Export the evidence chain for reporting.

        Returns a dictionary suitable for JSON export.
        """
        chain = self.get_chain(incident_id)
        is_valid, invalid_idx, message = self.verify_chain(incident_id)

        export = {
            "incident_id": incident_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(chain.entries),
            "chain_integrity": {
                "verified": is_valid,
                "message": message,
                "invalid_entry_index": invalid_idx,
            },
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "sequence": e.sequence_number,
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.entry_type,
                    "phase": e.phase,
                    "description": e.description,
                    "operator": e.operator,
                    "system_affected": e.system_affected,
                    "evidence_preserved": e.evidence_preserved,
                    "tags": e.tags,
                    **(
                        {
                            "entry_hash": e.entry_hash,
                            "previous_hash": e.previous_hash,
                        }
                        if include_hashes
                        else {}
                    ),
                }
                for e in chain.entries
            ],
        }

        if include_hashes:
            export["hash_chain"] = chain.export_hashes()

        return export

    def _row_to_entry(self, row: sqlite3.Row) -> EvidenceEntry:
        """Convert a database row to an EvidenceEntry."""
        artifacts_data = json.loads(row["artifacts_json"] or "[]")
        artifacts = [ArtifactReference(**a) for a in artifacts_data]

        return EvidenceEntry(
            entry_id=row["entry_id"],
            incident_id=row["incident_id"],
            sequence_number=row["sequence_number"],
            previous_hash=row["previous_hash"],
            entry_type=EvidenceType(row["entry_type"]),
            phase=row["phase"] or "",
            description=row["description"],
            system_affected=row["system_affected"],
            evidence_preserved=bool(row["evidence_preserved"]),
            integrity_notes=row["integrity_notes"],
            artifacts=artifacts,
            decision_node_id=row["decision_node_id"],
            decision_option_selected=row["decision_option_selected"],
            decision_rationale=row["decision_rationale"],
            operator=row["operator"] or "",
            tags=json.loads(row["tags_json"] or "[]"),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            entry_hash=row["entry_hash"],
        )

    def get_entry_count(self, incident_id: str) -> int:
        """Get the total number of entries for an incident."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM evidence_entries WHERE incident_id = ?",
                (incident_id,),
            )
            return cursor.fetchone()[0]

    def get_recent_entries(
        self, incident_id: str, count: int = 10
    ) -> List[EvidenceEntry]:
        """Get the most recent entries for an incident."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM evidence_entries
                WHERE incident_id = ?
                ORDER BY sequence_number DESC
                LIMIT ?
                """,
                (incident_id, count),
            )
            rows = cursor.fetchall()

        # Return in chronological order
        return [self._row_to_entry(row) for row in reversed(rows)]
