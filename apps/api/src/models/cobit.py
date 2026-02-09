"""
COBIT 2019 Models - IT Governance Framework assessments.

Official Sources:
-----------------
- ISACA COBIT 2019 Framework:
  https://www.isaca.org/resources/cobit

- COBIT 2019 Design Guide:
  https://www.isaca.org/resources/cobit/cobit-2019-design-guide

- COBIT 2019 Implementation Guide:
  https://www.isaca.org/resources/cobit/cobit-2019-implementation-guide

- ISACA COBIT Assessment Programme:
  https://www.isaca.org/credentialing/cobit-certifications

Note: COBIT 2019 is a proprietary framework by ISACA.
Full documentation requires ISACA membership or purchase.
Objective names and domains are based on publicly available information.
Capability levels follow ISO/IEC 33000 (SPICE) model.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.db.database import Base


# =============================================================================
# Enums
# =============================================================================

class COBITDomain(str, Enum):
    """COBIT 2019 domains."""
    EDM = "edm"  # Evaluate, Direct and Monitor
    APO = "apo"  # Align, Plan and Organize
    BAI = "bai"  # Build, Acquire and Implement
    DSS = "dss"  # Deliver, Service and Support
    MEA = "mea"  # Monitor, Evaluate and Assess


class COBITCapabilityLevel(str, Enum):
    """COBIT capability levels (0-5)."""
    LEVEL_0 = "level_0"  # Incomplete
    LEVEL_1 = "level_1"  # Performed
    LEVEL_2 = "level_2"  # Managed
    LEVEL_3 = "level_3"  # Established
    LEVEL_4 = "level_4"  # Predictable
    LEVEL_5 = "level_5"  # Optimizing


class COBITAssessmentStatus(str, Enum):
    """Assessment status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class COBITProcessStatus(str, Enum):
    """Process assessment status."""
    NOT_EVALUATED = "not_evaluated"
    NOT_ACHIEVED = "not_achieved"
    PARTIALLY_ACHIEVED = "partially_achieved"
    LARGELY_ACHIEVED = "largely_achieved"
    FULLY_ACHIEVED = "fully_achieved"
    NOT_APPLICABLE = "not_applicable"


class COBITOrganizationType(str, Enum):
    """Organization types."""
    ENTERPRISE = "enterprise"
    SME = "sme"
    PUBLIC_SECTOR = "public_sector"
    NONPROFIT = "nonprofit"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    RETAIL = "retail"
    EDUCATION = "education"


class COBITOrganizationSize(str, Enum):
    """Organization sizes."""
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# =============================================================================
# Reference Data
# =============================================================================

COBIT_DOMAINS = [
    {
        "id": "edm",
        "code": "EDM",
        "name_en": "Evaluate, Direct and Monitor",
        "name_de": "Evaluieren, Steuern und Überwachen",
        "description_en": "Governance objectives ensuring stakeholder value delivery through enterprise IT governance.",
        "description_de": "Governance-Ziele zur Sicherstellung der Wertschöpfung durch IT-Governance.",
        "weight": 20,
        "process_count": 5,
    },
    {
        "id": "apo",
        "code": "APO",
        "name_en": "Align, Plan and Organize",
        "name_de": "Ausrichten, Planen und Organisieren",
        "description_en": "Management objectives for aligning IT strategy with business goals.",
        "description_de": "Management-Ziele zur Ausrichtung der IT-Strategie an Geschäftszielen.",
        "weight": 25,
        "process_count": 14,
    },
    {
        "id": "bai",
        "code": "BAI",
        "name_en": "Build, Acquire and Implement",
        "name_de": "Erstellen, Beschaffen und Implementieren",
        "description_en": "Management objectives for building, acquiring, and implementing IT solutions.",
        "description_de": "Management-Ziele für Erstellung, Beschaffung und Implementierung von IT-Lösungen.",
        "weight": 25,
        "process_count": 11,
    },
    {
        "id": "dss",
        "code": "DSS",
        "name_en": "Deliver, Service and Support",
        "name_de": "Liefern, Service und Support",
        "description_en": "Management objectives for delivering IT services and support.",
        "description_de": "Management-Ziele für IT-Service-Bereitstellung und Support.",
        "weight": 20,
        "process_count": 6,
    },
    {
        "id": "mea",
        "code": "MEA",
        "name_en": "Monitor, Evaluate and Assess",
        "name_de": "Überwachen, Evaluieren und Bewerten",
        "description_en": "Management objectives for monitoring and evaluating IT performance.",
        "description_de": "Management-Ziele für Überwachung und Bewertung der IT-Performance.",
        "weight": 10,
        "process_count": 4,
    },
]

COBIT_PROCESSES = [
    # EDM Domain - 5 processes
    {"id": "EDM01", "domain": "edm", "name_en": "Ensured Governance Framework Setting and Maintenance", "name_de": "Governance-Framework sicherstellen", "description_en": "Analyze and articulate requirements for enterprise IT governance.", "weight": 4, "priority": 1},
    {"id": "EDM02", "domain": "edm", "name_en": "Ensured Benefits Delivery", "name_de": "Nutzenrealisierung sicherstellen", "description_en": "Optimize value contribution from business processes and IT services.", "weight": 4, "priority": 1},
    {"id": "EDM03", "domain": "edm", "name_en": "Ensured Risk Optimization", "name_de": "Risikooptimierung sicherstellen", "description_en": "Ensure enterprise risk appetite and tolerance are understood and managed.", "weight": 4, "priority": 1},
    {"id": "EDM04", "domain": "edm", "name_en": "Ensured Resource Optimization", "name_de": "Ressourcenoptimierung sicherstellen", "description_en": "Ensure adequate and sufficient IT-related capabilities are available.", "weight": 4, "priority": 2},
    {"id": "EDM05", "domain": "edm", "name_en": "Ensured Stakeholder Engagement", "name_de": "Stakeholder-Engagement sicherstellen", "description_en": "Ensure stakeholders are supportive of IT strategy and roadmap.", "weight": 4, "priority": 2},

    # APO Domain - 14 processes
    {"id": "APO01", "domain": "apo", "name_en": "Managed I&T Management Framework", "name_de": "I&T-Management-Framework verwalten", "description_en": "Clarify and maintain governance of enterprise IT.", "weight": 2, "priority": 1},
    {"id": "APO02", "domain": "apo", "name_en": "Managed Strategy", "name_de": "Strategie verwalten", "description_en": "Provide holistic view of current IT environment and future direction.", "weight": 2, "priority": 1},
    {"id": "APO03", "domain": "apo", "name_en": "Managed Enterprise Architecture", "name_de": "Unternehmensarchitektur verwalten", "description_en": "Establish common architecture to deliver the strategy.", "weight": 2, "priority": 2},
    {"id": "APO04", "domain": "apo", "name_en": "Managed Innovation", "name_de": "Innovation verwalten", "description_en": "Maintain awareness of IT and related service trends.", "weight": 1, "priority": 3},
    {"id": "APO05", "domain": "apo", "name_en": "Managed Portfolio", "name_de": "Portfolio verwalten", "description_en": "Execute strategic direction for investments aligned with business goals.", "weight": 2, "priority": 2},
    {"id": "APO06", "domain": "apo", "name_en": "Managed Budget and Costs", "name_de": "Budget und Kosten verwalten", "description_en": "Manage IT-related financial activities.", "weight": 2, "priority": 2},
    {"id": "APO07", "domain": "apo", "name_en": "Managed Human Resources", "name_de": "Personal verwalten", "description_en": "Provide structured approach to ensure optimal structuring of HR.", "weight": 2, "priority": 2},
    {"id": "APO08", "domain": "apo", "name_en": "Managed Relationships", "name_de": "Beziehungen verwalten", "description_en": "Manage relationships between IT and business stakeholders.", "weight": 1, "priority": 3},
    {"id": "APO09", "domain": "apo", "name_en": "Managed Service Agreements", "name_de": "Service-Vereinbarungen verwalten", "description_en": "Align IT services with business requirements.", "weight": 2, "priority": 2},
    {"id": "APO10", "domain": "apo", "name_en": "Managed Vendors", "name_de": "Lieferanten verwalten", "description_en": "Manage IT-related services provided by all types of vendors.", "weight": 2, "priority": 2},
    {"id": "APO11", "domain": "apo", "name_en": "Managed Quality", "name_de": "Qualität verwalten", "description_en": "Define and communicate quality requirements.", "weight": 1, "priority": 3},
    {"id": "APO12", "domain": "apo", "name_en": "Managed Risk", "name_de": "Risiko verwalten", "description_en": "Continually identify, assess and reduce IT-related risk.", "weight": 2, "priority": 1},
    {"id": "APO13", "domain": "apo", "name_en": "Managed Security", "name_de": "Sicherheit verwalten", "description_en": "Keep impact and occurrence of security incidents within risk appetite.", "weight": 2, "priority": 1},
    {"id": "APO14", "domain": "apo", "name_en": "Managed Data", "name_de": "Daten verwalten", "description_en": "Achieve and sustain effective management of data assets.", "weight": 2, "priority": 1},

    # BAI Domain - 11 processes
    {"id": "BAI01", "domain": "bai", "name_en": "Managed Programs", "name_de": "Programme verwalten", "description_en": "Manage all programs from the investment portfolio.", "weight": 3, "priority": 2},
    {"id": "BAI02", "domain": "bai", "name_en": "Managed Requirements Definition", "name_de": "Anforderungsdefinition verwalten", "description_en": "Identify solutions and analyze requirements before acquisition.", "weight": 2, "priority": 2},
    {"id": "BAI03", "domain": "bai", "name_en": "Managed Solutions Identification and Build", "name_de": "Lösungsidentifikation und -erstellung verwalten", "description_en": "Ensure timely and cost-effective availability of solutions.", "weight": 3, "priority": 2},
    {"id": "BAI04", "domain": "bai", "name_en": "Managed Availability and Capacity", "name_de": "Verfügbarkeit und Kapazität verwalten", "description_en": "Maintain service availability and efficient resource management.", "weight": 2, "priority": 2},
    {"id": "BAI05", "domain": "bai", "name_en": "Managed Organizational Change", "name_de": "Organisatorische Änderungen verwalten", "description_en": "Prepare and commit stakeholders for business change.", "weight": 2, "priority": 3},
    {"id": "BAI06", "domain": "bai", "name_en": "Managed IT Changes", "name_de": "IT-Änderungen verwalten", "description_en": "Manage all changes in a controlled manner.", "weight": 3, "priority": 1},
    {"id": "BAI07", "domain": "bai", "name_en": "Managed IT Change Acceptance and Transitioning", "name_de": "IT-Änderungsakzeptanz und -übergang verwalten", "description_en": "Formally accept and make operational new solutions.", "weight": 2, "priority": 2},
    {"id": "BAI08", "domain": "bai", "name_en": "Managed Knowledge", "name_de": "Wissen verwalten", "description_en": "Provide required knowledge to support all staff.", "weight": 1, "priority": 3},
    {"id": "BAI09", "domain": "bai", "name_en": "Managed Assets", "name_de": "Assets verwalten", "description_en": "Manage IT assets through their lifecycle.", "weight": 2, "priority": 2},
    {"id": "BAI10", "domain": "bai", "name_en": "Managed Configuration", "name_de": "Konfiguration verwalten", "description_en": "Define and maintain descriptions of assets and relationships.", "weight": 2, "priority": 2},
    {"id": "BAI11", "domain": "bai", "name_en": "Managed Projects", "name_de": "Projekte verwalten", "description_en": "Manage all projects initiated from investment portfolio.", "weight": 3, "priority": 2},

    # DSS Domain - 6 processes
    {"id": "DSS01", "domain": "dss", "name_en": "Managed Operations", "name_de": "Betrieb verwalten", "description_en": "Coordinate and execute operational procedures.", "weight": 4, "priority": 1},
    {"id": "DSS02", "domain": "dss", "name_en": "Managed Service Requests and Incidents", "name_de": "Service-Anfragen und Incidents verwalten", "description_en": "Provide timely and effective response to user requests and incidents.", "weight": 4, "priority": 1},
    {"id": "DSS03", "domain": "dss", "name_en": "Managed Problems", "name_de": "Probleme verwalten", "description_en": "Identify and classify problems and root causes.", "weight": 3, "priority": 2},
    {"id": "DSS04", "domain": "dss", "name_en": "Managed Continuity", "name_de": "Kontinuität verwalten", "description_en": "Establish and maintain plan to enable business continuity.", "weight": 3, "priority": 1},
    {"id": "DSS05", "domain": "dss", "name_en": "Managed Security Services", "name_de": "Sicherheitsservices verwalten", "description_en": "Protect enterprise information to maintain risk at acceptable level.", "weight": 4, "priority": 1},
    {"id": "DSS06", "domain": "dss", "name_en": "Managed Business Process Controls", "name_de": "Geschäftsprozesskontrollen verwalten", "description_en": "Define and maintain appropriate business process controls.", "weight": 2, "priority": 2},

    # MEA Domain - 4 processes
    {"id": "MEA01", "domain": "mea", "name_en": "Managed Performance and Conformance Monitoring", "name_de": "Performance- und Konformitätsüberwachung verwalten", "description_en": "Provide transparency of IT performance and conformance.", "weight": 3, "priority": 2},
    {"id": "MEA02", "domain": "mea", "name_en": "Managed System of Internal Control", "name_de": "Internes Kontrollsystem verwalten", "description_en": "Monitor and evaluate effectiveness of internal IT controls.", "weight": 3, "priority": 1},
    {"id": "MEA03", "domain": "mea", "name_en": "Managed Compliance with External Requirements", "name_de": "Compliance mit externen Anforderungen verwalten", "description_en": "Ensure IT complies with external requirements.", "weight": 2, "priority": 1},
    {"id": "MEA04", "domain": "mea", "name_en": "Managed Assurance", "name_de": "Assurance verwalten", "description_en": "Enable organization to design and develop efficient assurance initiatives.", "weight": 2, "priority": 2},
]

COBIT_CAPABILITY_LEVELS = [
    {
        "level": "level_0",
        "name_en": "Incomplete",
        "name_de": "Unvollständig",
        "description_en": "Process is not implemented or fails to achieve its purpose.",
        "score_range": "0%",
    },
    {
        "level": "level_1",
        "name_en": "Performed",
        "name_de": "Ausgeführt",
        "description_en": "Process achieves its purpose through applying an incomplete set of activities.",
        "score_range": "15-50%",
    },
    {
        "level": "level_2",
        "name_en": "Managed",
        "name_de": "Gemanagt",
        "description_en": "Process is planned, monitored, and adjusted. Work products are established, controlled, and maintained.",
        "score_range": "50-85%",
    },
    {
        "level": "level_3",
        "name_en": "Established",
        "name_de": "Etabliert",
        "description_en": "Process is implemented using a defined process capable of achieving outcomes.",
        "score_range": "85-100%",
    },
    {
        "level": "level_4",
        "name_en": "Predictable",
        "name_de": "Vorhersagbar",
        "description_en": "Process operates within defined limits to achieve outcomes. Quantitative management needs are identified.",
        "score_range": "100%+",
    },
    {
        "level": "level_5",
        "name_en": "Optimizing",
        "name_de": "Optimierend",
        "description_en": "Process is continuously improved to meet current and projected business goals.",
        "score_range": "100%++",
    },
]


# =============================================================================
# Database Models
# =============================================================================

class COBITAssessment(Base):
    """COBIT 2019 assessment."""
    __tablename__ = "cobit_assessments"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(COBITAssessmentStatus), default=COBITAssessmentStatus.DRAFT)

    # Scope
    organization_type = Column(SQLEnum(COBITOrganizationType), nullable=True)
    organization_size = Column(SQLEnum(COBITOrganizationSize), nullable=True)
    employee_count = Column(Integer, nullable=True)
    industry_sector = Column(String(100), nullable=True)

    # Maturity targets
    current_capability_level = Column(SQLEnum(COBITCapabilityLevel), nullable=True)
    target_capability_level = Column(SQLEnum(COBITCapabilityLevel), nullable=True)

    # Focus areas (JSON array of domain IDs)
    focus_areas = Column(JSON, default=list)

    # Scores (0-100)
    overall_score = Column(Float, default=0)
    domain_scores = Column(JSON, default=dict)  # {"edm": 75.0, "apo": 60.0, ...}
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship("COBITProcessResponse", back_populates="assessment", cascade="all, delete-orphan")


class COBITProcessResponse(Base):
    """Response for a COBIT process assessment."""
    __tablename__ = "cobit_process_responses"

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(36), ForeignKey("cobit_assessments.id", ondelete="CASCADE"), nullable=False)
    process_id = Column(String(10), nullable=False)  # e.g., "EDM01"
    domain_id = Column(String(10), nullable=False)  # e.g., "edm"

    status = Column(SQLEnum(COBITProcessStatus), default=COBITProcessStatus.NOT_EVALUATED)
    capability_level = Column(SQLEnum(COBITCapabilityLevel), nullable=True)
    achievement_percentage = Column(Integer, default=0)  # 0-100

    current_state = Column(Text, nullable=True)
    target_state = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    gap_description = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)
    priority = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime, nullable=True)
    responsible = Column(String(255), nullable=True)

    assessed_at = Column(DateTime, nullable=True)
    assessed_by = Column(String(36), nullable=True)

    # Relationships
    assessment = relationship("COBITAssessment", back_populates="responses")
