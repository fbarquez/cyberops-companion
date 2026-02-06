"""BSI IT-Grundschutz schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.bsi_grundschutz import (
    BSIKategorie, BSIAnforderungTyp, BSISchutzbedarf, BSIComplianceStatusEnum
)


# Kategorie schemas
class KategorieResponse(BaseModel):
    """Schema for category response."""
    kategorie: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    icon: str
    baustein_count: int


class KategorienListResponse(BaseModel):
    """Schema for categories list response."""
    kategorien: List[KategorieResponse]
    total: int


# Baustein schemas
class BausteinListItem(BaseModel):
    """Schema for Baustein list item."""
    id: str
    baustein_id: str
    kategorie: BSIKategorie
    titel: str
    title_en: Optional[str] = None
    version: str
    ir_phases: List[str] = []
    anforderungen_count: Optional[int] = None

    class Config:
        from_attributes = True


class BausteinResponse(BaseModel):
    """Schema for Baustein response."""
    id: str
    baustein_id: str
    kategorie: BSIKategorie
    titel: str
    title_en: Optional[str] = None
    beschreibung: Optional[str] = None
    zielsetzung: Optional[str] = None
    version: str
    edition: Optional[str] = None
    ir_phases: List[str] = []
    cross_references: Dict[str, Any] = {}
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BausteinListResponse(BaseModel):
    """Schema for Baustein list response."""
    bausteine: List[BausteinListItem]
    total: int
    page: int
    size: int


# Anforderung schemas
class AnforderungResponse(BaseModel):
    """Schema for Anforderung response."""
    id: str
    anforderung_id: str
    baustein_fk: str
    typ: BSIAnforderungTyp
    schutzbedarf: BSISchutzbedarf
    titel: str
    title_en: Optional[str] = None
    beschreibung: Optional[str] = None
    description_en: Optional[str] = None
    umsetzungshinweise: Optional[str] = None
    cross_references: Dict[str, Any] = {}
    aufwandsstufe: Optional[int] = None
    oscal_id: Optional[str] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnforderungListResponse(BaseModel):
    """Schema for Anforderung list response."""
    anforderungen: List[AnforderungResponse]
    total: int
    page: int
    size: int


class AnforderungCountResponse(BaseModel):
    """Schema for Anforderung counts."""
    muss: int
    sollte: int
    kann: int
    total: int


class BausteinDetailResponse(BaseModel):
    """Schema for Baustein detail with Anforderungen."""
    baustein: BausteinResponse
    anforderungen: List[AnforderungResponse]
    anforderungen_count: AnforderungCountResponse


# Compliance schemas
class ComplianceStatusResponse(BaseModel):
    """Schema for compliance status response."""
    id: str
    anforderung_fk: str
    anforderung_id: Optional[str] = None
    incident_id: Optional[str] = None
    status: BSIComplianceStatusEnum
    evidence_provided: List[Dict[str, Any]] = []
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceStatusCreate(BaseModel):
    """Schema for creating/updating compliance status."""
    anforderung_id: str = Field(..., description="BSI Anforderung ID (e.g., 'DER.2.1.A1')")
    status: BSIComplianceStatusEnum
    incident_id: Optional[str] = None
    evidence_provided: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    gap_description: Optional[str] = None
    remediation_plan: Optional[str] = None
    due_date: Optional[datetime] = None


class BulkComplianceStatusUpdate(BaseModel):
    """Schema for bulk compliance status update."""
    updates: List[ComplianceStatusCreate]


class ComplianceScoreResponse(BaseModel):
    """Schema for Baustein compliance score."""
    baustein_id: str
    schutzbedarf: str
    total_anforderungen: int
    compliant: int
    partial: int
    gap: int
    not_evaluated: int
    not_applicable: int
    score_percent: float


class BausteinScoreSummary(BaseModel):
    """Schema for Baustein score summary in category."""
    baustein_id: str
    titel: str
    score_percent: float


class CategoryComplianceResponse(BaseModel):
    """Schema for category compliance response."""
    name_de: str
    name_en: str
    bausteine: List[BausteinScoreSummary]
    total_anforderungen: int
    compliant: int
    partial: int
    gap: int
    not_evaluated: int
    not_applicable: int
    score_percent: float


class ComplianceOverviewResponse(BaseModel):
    """Schema for overall compliance overview."""
    schutzbedarf: str
    overall_score_percent: float
    total_anforderungen: int
    compliant: int
    partial: int
    gap: int
    not_evaluated: int
    not_applicable: int
    categories: Dict[str, CategoryComplianceResponse]


# Query parameters
class BausteinQueryParams(BaseModel):
    """Query parameters for Baustein list."""
    kategorie: Optional[BSIKategorie] = None
    search: Optional[str] = None
    ir_phase: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=200)


class AnforderungQueryParams(BaseModel):
    """Query parameters for Anforderung list."""
    baustein_id: Optional[str] = None
    typ: Optional[BSIAnforderungTyp] = None
    schutzbedarf: Optional[BSISchutzbedarf] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(100, ge=1, le=500)
