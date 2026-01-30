"""Evidence schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.evidence import EvidenceType


class ArtifactReference(BaseModel):
    """Reference to an artifact file (not stored, just metadata)."""
    filename: str
    original_path: Optional[str] = None
    file_hash_sha256: str
    file_size_bytes: int
    collected_at: datetime
    collection_method: Optional[str] = None
    notes: Optional[str] = None


class EvidenceCreate(BaseModel):
    """Schema for creating evidence entry."""
    entry_type: EvidenceType
    phase: str
    description: str = Field(..., min_length=1)
    artifacts: Optional[List[ArtifactReference]] = None
    decision_id: Optional[str] = None
    decision_option: Optional[str] = None
    decision_rationale: Optional[str] = None
    tags: Optional[List[str]] = []


class EvidenceResponse(BaseModel):
    """Schema for evidence entry response."""
    id: str
    entry_id: str
    incident_id: str
    sequence_number: int
    previous_hash: Optional[str] = None
    entry_hash: str
    entry_type: EvidenceType
    phase: str
    description: str
    artifacts: Optional[List[dict]] = None
    decision_id: Optional[str] = None
    decision_option: Optional[str] = None
    decision_rationale: Optional[str] = None
    operator: str
    tags: List[str] = []
    timestamp: datetime
    created_by: str

    class Config:
        from_attributes = True


class EvidenceChainResponse(BaseModel):
    """Schema for complete evidence chain."""
    incident_id: str
    total_entries: int
    chain_valid: bool
    entries: List[EvidenceResponse]
    first_entry: Optional[datetime] = None
    last_entry: Optional[datetime] = None


class ChainVerificationResult(BaseModel):
    """Schema for chain verification result."""
    incident_id: str
    is_valid: bool
    total_entries: int
    verified_entries: int
    errors: List[str] = []
    verified_at: datetime


class EvidenceExport(BaseModel):
    """Schema for evidence export."""
    incident_id: str
    format: str = "markdown"  # markdown, json, csv
    include_hashes: bool = True
    include_artifacts: bool = True
    phases: Optional[List[str]] = None  # None = all phases
