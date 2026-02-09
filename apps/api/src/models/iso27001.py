"""
ISO 27001:2022 Compliance Models.

Official Sources:
-----------------
- ISO/IEC 27001:2022 (Purchase required):
  https://www.iso.org/standard/27001

- ISO/IEC 27002:2022 (Control guidance):
  https://www.iso.org/standard/75652.html

- ISO 27001 Certification Bodies:
  https://www.iso.org/certification.html

- Free Resources:
  - ISO 27001 Overview: https://www.iso.org/isoiec-27001-information-security.html
  - ISO 27000 Family: https://www.iso.org/iso-27001-information-security.html

2022 Edition Changes:
- Controls reorganized into 4 themes (Organizational, People, Physical, Technological)
- Annex A: 93 controls (reduced from 114 in 2013 edition)
- 11 new controls added, several merged

Note: ISO standards are copyrighted and must be purchased from ISO or national bodies.
Control names and structure used here are based on publicly available information.
Full implementation guidance requires the official ISO/IEC 27002:2022 document.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base
from src.models.mixins import TenantMixin


class ISO27001Theme(str, enum.Enum):
    """ISO 27001:2022 Annex A themes."""
    ORGANIZATIONAL = "A.5"
    PEOPLE = "A.6"
    PHYSICAL = "A.7"
    TECHNOLOGICAL = "A.8"


class ISO27001ControlType(str, enum.Enum):
    """Control types per ISO 27001:2022."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class ISO27001SecurityProperty(str, enum.Enum):
    """CIA triad security properties."""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"


class ISO27001AssessmentStatus(str, enum.Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    SCOPING = "scoping"
    SOA = "soa"
    ASSESSMENT = "assessment"
    GAP_ANALYSIS = "gap_analysis"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ISO27001Applicability(str, enum.Enum):
    """Control applicability status."""
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    EXCLUDED = "excluded"


class ISO27001ComplianceStatus(str, enum.Enum):
    """Control compliance status."""
    NOT_EVALUATED = "not_evaluated"
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_APPLICABLE = "not_applicable"


class ISO27001Control(Base):
    """ISO 27001:2022 Annex A control definition (global reference data - 93 controls)."""
    __tablename__ = "iso27001_controls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Control identification
    control_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # A.5.1, A.5.2, ..., A.8.34
    theme = mapped_column(SQLEnum(ISO27001Theme), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Titles in multiple languages
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    title_de: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title_es: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Descriptions
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_de: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Implementation guidance
    guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Control classification
    control_type = mapped_column(JSON, default=[])  # List of: preventive, detective, corrective
    security_properties = mapped_column(JSON, default=[])  # List of: confidentiality, integrity, availability

    # Cross-framework references
    cross_references = mapped_column(JSON, default={})  # {bsi_grundschutz: [], nis2: [], nist_csf: []}

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    soa_entries = relationship("ISO27001SoAEntry", back_populates="control", cascade="all, delete-orphan")


class ISO27001Assessment(TenantMixin, Base):
    """ISO 27001:2022 assessment (tenant-scoped)."""
    __tablename__ = "iso27001_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status = mapped_column(SQLEnum(ISO27001AssessmentStatus), default=ISO27001AssessmentStatus.DRAFT, index=True)

    # Scope definition (Step 1)
    scope_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scope_systems: Mapped[Optional[str]] = mapped_column(JSON, default=[])  # List of system names
    scope_locations: Mapped[Optional[str]] = mapped_column(JSON, default=[])  # List of location names
    scope_processes: Mapped[Optional[str]] = mapped_column(JSON, default=[])  # List of process names

    # Risk appetite
    risk_appetite: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # low, medium, high

    # Calculated scores
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    organizational_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # A.5
    people_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # A.6
    physical_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # A.7
    technological_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # A.8

    # Control counts
    applicable_controls: Mapped[int] = mapped_column(Integer, default=0)
    compliant_controls: Mapped[int] = mapped_column(Integer, default=0)
    partial_controls: Mapped[int] = mapped_column(Integer, default=0)
    gap_controls: Mapped[int] = mapped_column(Integer, default=0)

    # Audit trail
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    soa_entries = relationship("ISO27001SoAEntry", back_populates="assessment", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class ISO27001SoAEntry(Base):
    """Statement of Applicability entry linking assessment to control."""
    __tablename__ = "iso27001_soa_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # References
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("iso27001_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    control_id: Mapped[str] = mapped_column(String(36), ForeignKey("iso27001_controls.id", ondelete="CASCADE"), nullable=False, index=True)

    # Applicability (Step 2 - SoA)
    applicability = mapped_column(SQLEnum(ISO27001Applicability), default=ISO27001Applicability.APPLICABLE)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Required if not applicable or excluded

    # Assessment (Step 3)
    status = mapped_column(SQLEnum(ISO27001ComplianceStatus), default=ISO27001ComplianceStatus.NOT_EVALUATED)
    implementation_level: Mapped[int] = mapped_column(Integer, default=0)  # 0-100%

    # Evidence and notes
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    implementation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Gap analysis (Step 4)
    gap_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remediation_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1=Critical, 2=High, 3=Medium, 4=Low

    # Audit trail
    assessed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("ISO27001Assessment", back_populates="soa_entries")
    control = relationship("ISO27001Control", back_populates="soa_entries")
    assessor = relationship("User", foreign_keys=[assessed_by])
