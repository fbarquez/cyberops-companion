"""
GDPR Compliance Models

GDPR (General Data Protection Regulation) is the EU regulation on data protection
and privacy, applicable to all organizations processing personal data of EU residents.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.db.database import Base


# =============================================================================
# Enums
# =============================================================================

class GDPRChapter(str, Enum):
    """GDPR Chapters (11 total)."""
    GENERAL_PROVISIONS = "chapter_1"  # Art. 1-4
    PRINCIPLES = "chapter_2"  # Art. 5-11
    DATA_SUBJECT_RIGHTS = "chapter_3"  # Art. 12-23
    CONTROLLER_PROCESSOR = "chapter_4"  # Art. 24-43
    TRANSFERS = "chapter_5"  # Art. 44-50
    SUPERVISORY_AUTHORITIES = "chapter_6"  # Art. 51-59
    COOPERATION = "chapter_7"  # Art. 60-76
    REMEDIES = "chapter_8"  # Art. 77-84
    SPECIFIC_SITUATIONS = "chapter_9"  # Art. 85-91
    DELEGATED_ACTS = "chapter_10"  # Art. 92-93
    FINAL_PROVISIONS = "chapter_11"  # Art. 94-99


class GDPROrganizationType(str, Enum):
    """Types of organizations under GDPR."""
    CONTROLLER = "controller"  # Data Controller
    PROCESSOR = "processor"  # Data Processor
    JOINT_CONTROLLER = "joint_controller"  # Joint Controller
    CONTROLLER_PROCESSOR = "controller_processor"  # Both roles


class GDPROrganizationSize(str, Enum):
    """Organization size classifications."""
    MICRO = "micro"  # <10 employees
    SMALL = "small"  # 10-49 employees
    MEDIUM = "medium"  # 50-249 employees
    LARGE = "large"  # 250+ employees


class GDPRAssessmentStatus(str, Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GDPRComplianceLevel(str, Enum):
    """Compliance level for requirements."""
    NOT_EVALUATED = "not_evaluated"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    FULLY_COMPLIANT = "fully_compliant"
    NOT_APPLICABLE = "not_applicable"


class GDPRDataCategory(str, Enum):
    """Categories of personal data processed."""
    BASIC_IDENTITY = "basic_identity"  # Name, address, email
    FINANCIAL = "financial"  # Bank accounts, payment data
    CONTACT = "contact"  # Phone, email, address
    BEHAVIORAL = "behavioral"  # Browsing, purchase history
    TECHNICAL = "technical"  # IP, device IDs, cookies
    LOCATION = "location"  # GPS, travel history
    SPECIAL_CATEGORY = "special_category"  # Art. 9 data
    CRIMINAL = "criminal"  # Art. 10 data


class GDPRLegalBasis(str, Enum):
    """Legal basis for processing (Art. 6)."""
    CONSENT = "consent"  # Art. 6(1)(a)
    CONTRACT = "contract"  # Art. 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Art. 6(1)(c)
    VITAL_INTERESTS = "vital_interests"  # Art. 6(1)(d)
    PUBLIC_TASK = "public_task"  # Art. 6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Art. 6(1)(f)


# =============================================================================
# Reference Data - GDPR Requirements
# =============================================================================

GDPR_CHAPTERS = [
    {
        "id": "chapter_1",
        "number": "1",
        "name_en": "General Provisions",
        "name_de": "Allgemeine Bestimmungen",
        "articles": "1-4",
        "description_en": "Subject matter, scope, definitions",
        "requirement_count": 3,
    },
    {
        "id": "chapter_2",
        "number": "2",
        "name_en": "Principles",
        "name_de": "Grundsätze",
        "articles": "5-11",
        "description_en": "Data protection principles and lawfulness",
        "requirement_count": 6,
    },
    {
        "id": "chapter_3",
        "number": "3",
        "name_en": "Rights of the Data Subject",
        "name_de": "Rechte der betroffenen Person",
        "articles": "12-23",
        "description_en": "Transparency, access, rectification, erasure",
        "requirement_count": 8,
    },
    {
        "id": "chapter_4",
        "number": "4",
        "name_en": "Controller and Processor",
        "name_de": "Verantwortlicher und Auftragsverarbeiter",
        "articles": "24-43",
        "description_en": "Obligations, security, DPO, DPIA",
        "requirement_count": 12,
    },
    {
        "id": "chapter_5",
        "number": "5",
        "name_en": "International Transfers",
        "name_de": "Übermittlung in Drittländer",
        "articles": "44-50",
        "description_en": "Transfer mechanisms and safeguards",
        "requirement_count": 4,
    },
]

# Key GDPR Requirements
GDPR_REQUIREMENTS = [
    # Chapter 1: General Provisions
    {
        "id": "GDPR-1.1",
        "chapter": "chapter_1",
        "article": "2-3",
        "name_en": "Scope Determination",
        "name_de": "Anwendungsbereichsbestimmung",
        "description_en": "Determine if GDPR applies to processing activities",
        "description_de": "Bestimmen Sie, ob die DSGVO auf Verarbeitungstätigkeiten anwendbar ist",
        "weight": 10,
        "priority": 1,
        "requirements": [
            "Document processing activities scope",
            "Identify EU data subjects processed",
            "Assess territorial applicability",
        ],
    },
    {
        "id": "GDPR-1.2",
        "chapter": "chapter_1",
        "article": "4",
        "name_en": "Key Definitions",
        "name_de": "Schlüsselbegriffe",
        "description_en": "Understand and apply GDPR definitions correctly",
        "description_de": "Verstehen und korrekte Anwendung der DSGVO-Definitionen",
        "weight": 8,
        "priority": 2,
        "requirements": [
            "Define personal data in context",
            "Identify controller vs processor roles",
            "Document consent requirements",
        ],
    },
    {
        "id": "GDPR-1.3",
        "chapter": "chapter_1",
        "article": "4",
        "name_en": "Data Inventory",
        "name_de": "Dateninventar",
        "description_en": "Maintain inventory of personal data processed",
        "description_de": "Führen eines Verzeichnisses der verarbeiteten personenbezogenen Daten",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Complete data inventory",
            "Data flow documentation",
            "Regular inventory updates",
        ],
    },

    # Chapter 2: Principles
    {
        "id": "GDPR-2.1",
        "chapter": "chapter_2",
        "article": "5(1)(a)",
        "name_en": "Lawfulness, Fairness, Transparency",
        "name_de": "Rechtmäßigkeit, Verarbeitung nach Treu und Glauben, Transparenz",
        "description_en": "Process data lawfully, fairly and transparently",
        "description_de": "Rechtmäßige, faire und transparente Datenverarbeitung",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Valid legal basis documented",
            "Fair processing practices",
            "Clear privacy notices",
        ],
    },
    {
        "id": "GDPR-2.2",
        "chapter": "chapter_2",
        "article": "5(1)(b)",
        "name_en": "Purpose Limitation",
        "name_de": "Zweckbindung",
        "description_en": "Collect for specified, explicit and legitimate purposes",
        "description_de": "Erhebung für festgelegte, eindeutige und legitime Zwecke",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Documented processing purposes",
            "No incompatible further processing",
            "Purpose compatibility assessment",
        ],
    },
    {
        "id": "GDPR-2.3",
        "chapter": "chapter_2",
        "article": "5(1)(c)",
        "name_en": "Data Minimization",
        "name_de": "Datenminimierung",
        "description_en": "Process only adequate, relevant and necessary data",
        "description_de": "Verarbeitung nur angemessener, relevanter und notwendiger Daten",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Necessity assessment",
            "No excessive data collection",
            "Regular data review",
        ],
    },
    {
        "id": "GDPR-2.4",
        "chapter": "chapter_2",
        "article": "5(1)(d)",
        "name_en": "Accuracy",
        "name_de": "Richtigkeit",
        "description_en": "Keep personal data accurate and up to date",
        "description_de": "Personenbezogene Daten sachlich richtig und auf dem neuesten Stand halten",
        "weight": 10,
        "priority": 2,
        "requirements": [
            "Data accuracy procedures",
            "Update mechanisms",
            "Correction processes",
        ],
    },
    {
        "id": "GDPR-2.5",
        "chapter": "chapter_2",
        "article": "5(1)(e)",
        "name_en": "Storage Limitation",
        "name_de": "Speicherbegrenzung",
        "description_en": "Keep data only as long as necessary",
        "description_de": "Daten nur so lange aufbewahren wie nötig",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Retention policy defined",
            "Deletion procedures",
            "Regular retention review",
        ],
    },
    {
        "id": "GDPR-2.6",
        "chapter": "chapter_2",
        "article": "5(1)(f)",
        "name_en": "Integrity and Confidentiality",
        "name_de": "Integrität und Vertraulichkeit",
        "description_en": "Ensure appropriate security of personal data",
        "description_de": "Angemessene Sicherheit personenbezogener Daten gewährleisten",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Technical security measures",
            "Organizational measures",
            "Access controls",
        ],
    },

    # Chapter 3: Data Subject Rights
    {
        "id": "GDPR-3.1",
        "chapter": "chapter_3",
        "article": "12",
        "name_en": "Transparent Communication",
        "name_de": "Transparente Kommunikation",
        "description_en": "Provide clear information and facilitate rights exercise",
        "description_de": "Klare Informationen bereitstellen und Rechtsausübung erleichtern",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Clear privacy notices",
            "Easy-to-understand language",
            "Response within 1 month",
        ],
    },
    {
        "id": "GDPR-3.2",
        "chapter": "chapter_3",
        "article": "13-14",
        "name_en": "Information Provision",
        "name_de": "Informationspflichten",
        "description_en": "Provide required information at collection",
        "description_de": "Erforderliche Informationen bei der Erhebung bereitstellen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Identity of controller",
            "Processing purposes and legal basis",
            "Recipients and transfers",
            "Retention periods",
            "Data subject rights",
        ],
    },
    {
        "id": "GDPR-3.3",
        "chapter": "chapter_3",
        "article": "15",
        "name_en": "Right of Access",
        "name_de": "Auskunftsrecht",
        "description_en": "Enable data subjects to access their data",
        "description_de": "Betroffenen Personen Zugang zu ihren Daten ermöglichen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Access request process",
            "Copy provision capability",
            "Processing information",
        ],
    },
    {
        "id": "GDPR-3.4",
        "chapter": "chapter_3",
        "article": "16-17",
        "name_en": "Rectification and Erasure",
        "name_de": "Berichtigung und Löschung",
        "description_en": "Allow correction and deletion of personal data",
        "description_de": "Berichtigung und Löschung personenbezogener Daten ermöglichen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Rectification process",
            "Erasure/deletion capability",
            "Right to be forgotten implementation",
        ],
    },
    {
        "id": "GDPR-3.5",
        "chapter": "chapter_3",
        "article": "18",
        "name_en": "Restriction of Processing",
        "name_de": "Einschränkung der Verarbeitung",
        "description_en": "Allow restriction of processing in certain cases",
        "description_de": "Einschränkung der Verarbeitung in bestimmten Fällen ermöglichen",
        "weight": 8,
        "priority": 2,
        "requirements": [
            "Restriction mechanism",
            "Marking restricted data",
            "Restriction notification",
        ],
    },
    {
        "id": "GDPR-3.6",
        "chapter": "chapter_3",
        "article": "20",
        "name_en": "Data Portability",
        "name_de": "Datenübertragbarkeit",
        "description_en": "Provide data in portable format on request",
        "description_de": "Daten auf Anfrage in portablem Format bereitstellen",
        "weight": 10,
        "priority": 2,
        "requirements": [
            "Machine-readable format",
            "Direct transfer capability",
            "Export functionality",
        ],
    },
    {
        "id": "GDPR-3.7",
        "chapter": "chapter_3",
        "article": "21",
        "name_en": "Right to Object",
        "name_de": "Widerspruchsrecht",
        "description_en": "Allow objection to processing in certain cases",
        "description_de": "Widerspruch gegen Verarbeitung in bestimmten Fällen ermöglichen",
        "weight": 10,
        "priority": 2,
        "requirements": [
            "Objection mechanism",
            "Direct marketing opt-out",
            "Compelling grounds assessment",
        ],
    },
    {
        "id": "GDPR-3.8",
        "chapter": "chapter_3",
        "article": "22",
        "name_en": "Automated Decision-Making",
        "name_de": "Automatisierte Entscheidungsfindung",
        "description_en": "Provide safeguards for automated decisions",
        "description_de": "Schutzmaßnahmen für automatisierte Entscheidungen bereitstellen",
        "weight": 10,
        "priority": 2,
        "requirements": [
            "Human intervention option",
            "Right to explanation",
            "Contest mechanism",
        ],
    },

    # Chapter 4: Controller and Processor
    {
        "id": "GDPR-4.1",
        "chapter": "chapter_4",
        "article": "24",
        "name_en": "Controller Responsibility",
        "name_de": "Verantwortlichkeit des Verantwortlichen",
        "description_en": "Implement appropriate measures to ensure compliance",
        "description_de": "Geeignete Maßnahmen zur Gewährleistung der Compliance umsetzen",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Compliance program",
            "Policies and procedures",
            "Regular reviews",
        ],
    },
    {
        "id": "GDPR-4.2",
        "chapter": "chapter_4",
        "article": "25",
        "name_en": "Data Protection by Design and Default",
        "name_de": "Datenschutz durch Technikgestaltung und Voreinstellungen",
        "description_en": "Build privacy into systems from the start",
        "description_de": "Datenschutz von Anfang an in Systeme einbauen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Privacy by design methodology",
            "Default privacy settings",
            "Minimization in system design",
        ],
    },
    {
        "id": "GDPR-4.3",
        "chapter": "chapter_4",
        "article": "26",
        "name_en": "Joint Controllers",
        "name_de": "Gemeinsam Verantwortliche",
        "description_en": "Define responsibilities between joint controllers",
        "description_de": "Verantwortlichkeiten zwischen gemeinsam Verantwortlichen festlegen",
        "weight": 8,
        "priority": 3,
        "requirements": [
            "Joint controller agreement",
            "Responsibility allocation",
            "Contact point designation",
        ],
    },
    {
        "id": "GDPR-4.4",
        "chapter": "chapter_4",
        "article": "28",
        "name_en": "Processor Obligations",
        "name_de": "Auftragsverarbeiter-Pflichten",
        "description_en": "Ensure processor compliance through contracts",
        "description_de": "Compliance des Auftragsverarbeiters durch Verträge sicherstellen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Data processing agreements",
            "Processor due diligence",
            "Sub-processor controls",
        ],
    },
    {
        "id": "GDPR-4.5",
        "chapter": "chapter_4",
        "article": "30",
        "name_en": "Records of Processing",
        "name_de": "Verzeichnis von Verarbeitungstätigkeiten",
        "description_en": "Maintain records of processing activities",
        "description_de": "Verzeichnis von Verarbeitungstätigkeiten führen",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Processing activity register",
            "Required information documented",
            "Regular updates",
        ],
    },
    {
        "id": "GDPR-4.6",
        "chapter": "chapter_4",
        "article": "32",
        "name_en": "Security of Processing",
        "name_de": "Sicherheit der Verarbeitung",
        "description_en": "Implement appropriate technical and organizational measures",
        "description_de": "Geeignete technische und organisatorische Maßnahmen umsetzen",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Pseudonymization and encryption",
            "Confidentiality measures",
            "Resilience capabilities",
            "Regular testing",
        ],
    },
    {
        "id": "GDPR-4.7",
        "chapter": "chapter_4",
        "article": "33-34",
        "name_en": "Breach Notification",
        "name_de": "Meldung von Datenschutzverletzungen",
        "description_en": "Notify authorities and data subjects of breaches",
        "description_de": "Behörden und betroffene Personen über Verletzungen informieren",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "72-hour authority notification",
            "Data subject notification",
            "Breach documentation",
            "Incident response plan",
        ],
    },
    {
        "id": "GDPR-4.8",
        "chapter": "chapter_4",
        "article": "35",
        "name_en": "Data Protection Impact Assessment",
        "name_de": "Datenschutz-Folgenabschätzung",
        "description_en": "Conduct DPIA for high-risk processing",
        "description_de": "DSFA für risikoreiche Verarbeitung durchführen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "DPIA process defined",
            "High-risk assessment",
            "Risk mitigation measures",
            "Prior consultation when needed",
        ],
    },
    {
        "id": "GDPR-4.9",
        "chapter": "chapter_4",
        "article": "37-39",
        "name_en": "Data Protection Officer",
        "name_de": "Datenschutzbeauftragter",
        "description_en": "Appoint and support DPO where required",
        "description_de": "DSB ernennen und unterstützen, wo erforderlich",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "DPO appointment (if required)",
            "DPO independence",
            "DPO tasks defined",
            "Contact details published",
        ],
    },
    {
        "id": "GDPR-4.10",
        "chapter": "chapter_4",
        "article": "40-41",
        "name_en": "Codes of Conduct",
        "name_de": "Verhaltensregeln",
        "description_en": "Adhere to approved codes of conduct",
        "description_de": "Genehmigte Verhaltensregeln einhalten",
        "weight": 5,
        "priority": 3,
        "requirements": [
            "Code adherence assessment",
            "Monitoring body engagement",
        ],
    },
    {
        "id": "GDPR-4.11",
        "chapter": "chapter_4",
        "article": "42-43",
        "name_en": "Certification",
        "name_de": "Zertifizierung",
        "description_en": "Consider certification mechanisms",
        "description_de": "Zertifizierungsmechanismen in Betracht ziehen",
        "weight": 5,
        "priority": 3,
        "requirements": [
            "Certification assessment",
            "Seals and marks evaluation",
        ],
    },
    {
        "id": "GDPR-4.12",
        "chapter": "chapter_4",
        "article": "5(2)",
        "name_en": "Accountability",
        "name_de": "Rechenschaftspflicht",
        "description_en": "Demonstrate compliance with GDPR principles",
        "description_de": "Einhaltung der DSGVO-Grundsätze nachweisen",
        "weight": 15,
        "priority": 1,
        "requirements": [
            "Documentation of compliance",
            "Audit trail",
            "Evidence retention",
        ],
    },

    # Chapter 5: International Transfers
    {
        "id": "GDPR-5.1",
        "chapter": "chapter_5",
        "article": "44-45",
        "name_en": "Transfer Principles",
        "name_de": "Übermittlungsgrundsätze",
        "description_en": "Ensure adequate protection for international transfers",
        "description_de": "Angemessenen Schutz für internationale Übermittlungen sicherstellen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Transfer assessment",
            "Adequacy decisions review",
            "Transfer mapping",
        ],
    },
    {
        "id": "GDPR-5.2",
        "chapter": "chapter_5",
        "article": "46",
        "name_en": "Appropriate Safeguards",
        "name_de": "Geeignete Garantien",
        "description_en": "Implement appropriate safeguards for transfers",
        "description_de": "Geeignete Garantien für Übermittlungen umsetzen",
        "weight": 12,
        "priority": 1,
        "requirements": [
            "Standard contractual clauses",
            "Binding corporate rules",
            "Supplementary measures",
        ],
    },
    {
        "id": "GDPR-5.3",
        "chapter": "chapter_5",
        "article": "47",
        "name_en": "Binding Corporate Rules",
        "name_de": "Verbindliche interne Datenschutzvorschriften",
        "description_en": "Implement BCRs for intra-group transfers",
        "description_de": "BCRs für konzerninterne Übermittlungen umsetzen",
        "weight": 8,
        "priority": 2,
        "requirements": [
            "BCR development",
            "Authority approval",
            "BCR compliance monitoring",
        ],
    },
    {
        "id": "GDPR-5.4",
        "chapter": "chapter_5",
        "article": "49",
        "name_en": "Derogations",
        "name_de": "Ausnahmen",
        "description_en": "Apply derogations only in specific situations",
        "description_de": "Ausnahmen nur in bestimmten Situationen anwenden",
        "weight": 8,
        "priority": 2,
        "requirements": [
            "Derogation assessment",
            "Explicit consent documentation",
            "Contractual necessity evaluation",
        ],
    },
]


# =============================================================================
# Database Models
# =============================================================================

class GDPRAssessment(Base):
    """GDPR Assessment for an organization."""
    __tablename__ = "gdpr_assessments"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(GDPRAssessmentStatus), default=GDPRAssessmentStatus.DRAFT)

    # Organization Info
    organization_type = Column(SQLEnum(GDPROrganizationType), nullable=True)
    organization_size = Column(SQLEnum(GDPROrganizationSize), nullable=True)
    employee_count = Column(Integer, nullable=True)

    # Scope
    processes_special_categories = Column(Boolean, default=False)  # Art. 9 data
    processes_criminal_data = Column(Boolean, default=False)  # Art. 10 data
    large_scale_processing = Column(Boolean, default=False)
    systematic_monitoring = Column(Boolean, default=False)
    cross_border_processing = Column(Boolean, default=False)
    requires_dpo = Column(Boolean, default=False)

    # Data Categories Processed
    data_categories = Column(JSON, default=list)  # List of GDPRDataCategory values
    legal_bases = Column(JSON, default=list)  # List of GDPRLegalBasis values
    eu_countries = Column(JSON, default=list)  # EU countries with data subjects

    # Scores
    overall_score = Column(Float, default=0.0)
    chapter_scores = Column(JSON, default=dict)
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # DPO Info
    dpo_appointed = Column(Boolean, default=False)
    dpo_name = Column(String(255), nullable=True)
    dpo_email = Column(String(255), nullable=True)

    # Supervisory Authority
    lead_authority = Column(String(100), nullable=True)  # e.g., "BfDI" (Germany)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Owner
    created_by = Column(String(36), nullable=True)

    # Relationships
    responses = relationship("GDPRRequirementResponse", back_populates="assessment", cascade="all, delete-orphan")


class GDPRRequirementResponse(Base):
    """Response to a GDPR requirement within an assessment."""
    __tablename__ = "gdpr_requirement_responses"

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(36), ForeignKey("gdpr_assessments.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(String(50), nullable=False)  # e.g., "GDPR-2.1"
    chapter_id = Column(String(50), nullable=False)  # e.g., "chapter_2"

    # Compliance Assessment
    compliance_level = Column(SQLEnum(GDPRComplianceLevel), default=GDPRComplianceLevel.NOT_EVALUATED)

    # Evidence and Notes
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    gap_description = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)

    # Sub-requirements Status
    requirements_met = Column(JSON, default=list)  # List of met sub-requirements

    # Priority and Planning
    priority = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime, nullable=True)
    responsible = Column(String(255), nullable=True)

    # Timestamps
    assessed_at = Column(DateTime, nullable=True)
    assessed_by = Column(String(36), nullable=True)

    # Relationships
    assessment = relationship("GDPRAssessment", back_populates="responses")
