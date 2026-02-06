"""BSI IT-Grundschutz 2023 models.

Implements the complete BSI IT-Grundschutz catalog with 111 Bausteine,
~1000+ Anforderungen (requirements), and tenant-scoped compliance tracking.
"""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    String, Enum, DateTime, Text, ForeignKey, JSON, Integer,
    UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base
from src.models.mixins import TenantMixin


class BSIKategorie(str, enum.Enum):
    """BSI IT-Grundschutz categories (10 total)."""
    ISMS = "ISMS"      # Sicherheitsmanagement
    ORP = "ORP"        # Organisation und Personal
    CON = "CON"        # Konzeption und Planung
    OPS = "OPS"        # Betrieb
    DER = "DER"        # Detektion und Reaktion
    APP = "APP"        # Anwendungen
    SYS = "SYS"        # IT-Systeme
    NET = "NET"        # Netze und Kommunikation
    INF = "INF"        # Infrastruktur
    IND = "IND"        # Industrielle IT


class BSIAnforderungTyp(str, enum.Enum):
    """BSI requirement types (modal verbs)."""
    MUSS = "MUSS"        # Mandatory - Basis level
    SOLLTE = "SOLLTE"    # Recommended - Standard level
    KANN = "KANN"        # Optional - Hoch (elevated) level


class BSISchutzbedarf(str, enum.Enum):
    """BSI protection level requirements."""
    basis = "basis"          # Basic protection - MUSS requirements
    standard = "standard"    # Standard protection - MUSS + SOLLTE
    hoch = "hoch"            # High/elevated protection - MUSS + SOLLTE + KANN


class BSIComplianceStatusEnum(str, enum.Enum):
    """Status of compliance with a requirement."""
    NOT_EVALUATED = "not_evaluated"
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_APPLICABLE = "not_applicable"


class BSIBaustein(Base):
    """BSI IT-Grundschutz Baustein (module/building block).

    Represents one of the 111 modules in the BSI IT-Grundschutz catalog.
    Each Baustein belongs to one of 10 categories and contains multiple
    Anforderungen (requirements).
    """
    __tablename__ = "bsi_bausteine"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    baustein_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )  # e.g., "DER.2.1", "ORP.1"
    kategorie: Mapped[BSIKategorie] = mapped_column(
        Enum(BSIKategorie), index=True, nullable=False
    )

    # Titles
    titel: Mapped[str] = mapped_column(String(500), nullable=False)  # German title
    title_en: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # English

    # Descriptions
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    zielsetzung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Objectives

    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="2023")
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "Edition 2023"

    # IR Phase relevance (JSON array of phase names)
    ir_phases: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    # Cross-references to other frameworks
    cross_references: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    # e.g., {"iso27001": ["A.5.1", "A.5.2"], "nist_csf": ["ID.GV-1"]}

    # Ordering
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    anforderungen: Mapped[List["BSIAnforderung"]] = relationship(
        "BSIAnforderung",
        back_populates="baustein",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('ix_bsi_baustein_kategorie_order', 'kategorie', 'sort_order'),
    )


class BSIAnforderung(Base):
    """BSI IT-Grundschutz Anforderung (requirement).

    Individual security requirements within a Baustein. Each has a type
    (MUSS/SOLLTE/KANN) that determines which protection level it applies to.
    """
    __tablename__ = "bsi_anforderungen"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    baustein_fk: Mapped[str] = mapped_column(
        String(36), ForeignKey("bsi_bausteine.id", ondelete="CASCADE"), index=True
    )
    anforderung_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )  # e.g., "DER.2.1.A1", "ORP.1.A5"

    # Requirement type and protection level
    typ: Mapped[BSIAnforderungTyp] = mapped_column(
        Enum(BSIAnforderungTyp), nullable=False
    )
    schutzbedarf: Mapped[BSISchutzbedarf] = mapped_column(
        Enum(BSISchutzbedarf), nullable=False
    )

    # Content
    titel: Mapped[str] = mapped_column(String(500), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Implementation guidance
    umsetzungshinweise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cross-references to other frameworks
    cross_references: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    # e.g., {"iso27001": ["A.5.1.1"], "nist_csf": ["PR.AT-1"]}

    # Implementation effort (0-4 scale)
    aufwandsstufe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # OSCAL identifier for traceability
    oscal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Ordering within Baustein
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    baustein: Mapped["BSIBaustein"] = relationship(
        "BSIBaustein",
        back_populates="anforderungen"
    )
    compliance_statuses: Mapped[List["BSIComplianceStatus"]] = relationship(
        "BSIComplianceStatus",
        back_populates="anforderung",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('ix_bsi_anforderung_baustein_typ', 'baustein_fk', 'typ'),
        Index('ix_bsi_anforderung_schutzbedarf', 'schutzbedarf'),
    )


class BSIComplianceStatus(TenantMixin, Base):
    """Tenant-scoped compliance status for BSI requirements.

    Tracks the compliance state of each Anforderung for a specific tenant,
    including evidence provided, notes, and assessment metadata.
    """
    __tablename__ = "bsi_compliance_status"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    anforderung_fk: Mapped[str] = mapped_column(
        String(36), ForeignKey("bsi_anforderungen.id", ondelete="CASCADE"), index=True
    )

    # Optional link to specific incident
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Compliance status
    status: Mapped[BSIComplianceStatusEnum] = mapped_column(
        Enum(BSIComplianceStatusEnum),
        default=BSIComplianceStatusEnum.NOT_EVALUATED
    )

    # Evidence and documentation
    evidence_provided: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    # e.g., [{"type": "document", "name": "Policy.pdf", "uploaded_at": "..."}]

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gap_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assessment tracking
    assessed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    anforderung: Mapped["BSIAnforderung"] = relationship(
        "BSIAnforderung",
        back_populates="compliance_statuses"
    )

    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 'anforderung_fk', 'incident_id',
            name='uq_bsi_compliance_tenant_anforderung_incident'
        ),
        Index('ix_bsi_compliance_tenant_status', 'tenant_id', 'status'),
    )


# Category metadata for UI display
BSI_KATEGORIE_INFO = {
    BSIKategorie.ISMS: {
        "name_de": "Sicherheitsmanagement",
        "name_en": "Security Management",
        "description_de": "Prozesse und Verfahren zur Steuerung der Informationssicherheit",
        "description_en": "Processes and procedures for managing information security",
        "icon": "shield-check",
    },
    BSIKategorie.ORP: {
        "name_de": "Organisation und Personal",
        "name_en": "Organization and Personnel",
        "description_de": "Organisatorische und personelle Sicherheitsmaßnahmen",
        "description_en": "Organizational and personnel security measures",
        "icon": "users",
    },
    BSIKategorie.CON: {
        "name_de": "Konzeption und Planung",
        "name_en": "Concept and Planning",
        "description_de": "Konzepte und Planungsaspekte der Informationssicherheit",
        "description_en": "Concepts and planning aspects of information security",
        "icon": "clipboard-list",
    },
    BSIKategorie.OPS: {
        "name_de": "Betrieb",
        "name_en": "Operations",
        "description_de": "Operative Aspekte des IT-Betriebs",
        "description_en": "Operational aspects of IT operations",
        "icon": "cog",
    },
    BSIKategorie.DER: {
        "name_de": "Detektion und Reaktion",
        "name_en": "Detection and Response",
        "description_de": "Erkennung und Behandlung von Sicherheitsvorfällen",
        "description_en": "Detection and handling of security incidents",
        "icon": "alert-triangle",
    },
    BSIKategorie.APP: {
        "name_de": "Anwendungen",
        "name_en": "Applications",
        "description_de": "Sicherheit von Anwendungen und Diensten",
        "description_en": "Security of applications and services",
        "icon": "layout-grid",
    },
    BSIKategorie.SYS: {
        "name_de": "IT-Systeme",
        "name_en": "IT Systems",
        "description_de": "Sicherheit von IT-Systemen und Komponenten",
        "description_en": "Security of IT systems and components",
        "icon": "server",
    },
    BSIKategorie.NET: {
        "name_de": "Netze und Kommunikation",
        "name_en": "Networks and Communication",
        "description_de": "Netzwerk- und Kommunikationssicherheit",
        "description_en": "Network and communication security",
        "icon": "network",
    },
    BSIKategorie.INF: {
        "name_de": "Infrastruktur",
        "name_en": "Infrastructure",
        "description_de": "Physische und infrastrukturelle Sicherheit",
        "description_en": "Physical and infrastructure security",
        "icon": "building",
    },
    BSIKategorie.IND: {
        "name_de": "Industrielle IT",
        "name_en": "Industrial IT",
        "description_de": "Sicherheit industrieller Steuerungssysteme (ICS/OT)",
        "description_en": "Security of industrial control systems (ICS/OT)",
        "icon": "factory",
    },
}
