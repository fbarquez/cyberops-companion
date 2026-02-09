"""
TISAX Compliance Models

TISAX (Trusted Information Security Assessment Exchange) is the automotive
industry standard for information security assessment, based on VDA ISA.
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

class TISAXAssessmentLevel(str, Enum):
    """TISAX Assessment Levels (AL1-AL3)."""
    AL1 = "al1"  # Normal - Self-assessment
    AL2 = "al2"  # High - Remote assessment by auditor
    AL3 = "al3"  # Very High - On-site assessment by auditor


class TISAXAssessmentObjective(str, Enum):
    """TISAX Assessment Objectives."""
    INFO_HIGH = "info_high"  # Information with high protection need
    INFO_VERY_HIGH = "info_very_high"  # Information with very high protection need
    PROTOTYPE = "prototype"  # Prototype protection
    PROTOTYPE_VEHICLE = "prototype_vehicle"  # Prototype vehicles
    DATA_PROTECTION = "data_protection"  # Data protection (GDPR)


class TISAXCompanyType(str, Enum):
    """Types of companies in automotive supply chain."""
    OEM = "oem"  # Original Equipment Manufacturer
    TIER1 = "tier1"  # Tier 1 Supplier
    TIER2 = "tier2"  # Tier 2 Supplier
    TIER3 = "tier3"  # Tier 3 Supplier
    SERVICE_PROVIDER = "service_provider"  # IT/Engineering Service Provider
    LOGISTICS = "logistics"  # Logistics Provider
    DEVELOPMENT = "development"  # Development Partner


class TISAXCompanySize(str, Enum):
    """Company size classifications."""
    MICRO = "micro"  # <10 employees
    SMALL = "small"  # 10-49 employees
    MEDIUM = "medium"  # 50-249 employees
    LARGE = "large"  # 250+ employees


class TISAXAssessmentStatus(str, Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TISAXMaturityLevel(str, Enum):
    """VDA ISA Maturity Levels (0-5)."""
    LEVEL_0 = "0"  # Incomplete
    LEVEL_1 = "1"  # Performed
    LEVEL_2 = "2"  # Managed
    LEVEL_3 = "3"  # Established
    LEVEL_4 = "4"  # Predictable
    LEVEL_5 = "5"  # Optimizing


# =============================================================================
# Reference Data - VDA ISA Catalog Structure
# =============================================================================

TISAX_CHAPTERS = [
    {
        "id": "chapter_1",
        "number": "1",
        "name_en": "Information Security Policies",
        "name_de": "Informationssicherheitsrichtlinien",
        "description_en": "Policies, organization, and responsibilities for information security",
        "control_count": 4,
    },
    {
        "id": "chapter_2",
        "number": "2",
        "name_en": "Organization of Information Security",
        "name_de": "Organisation der Informationssicherheit",
        "description_en": "Internal organization and mobile/teleworking security",
        "control_count": 5,
    },
    {
        "id": "chapter_3",
        "number": "3",
        "name_en": "Human Resource Security",
        "name_de": "Personalsicherheit",
        "description_en": "Security awareness and training for personnel",
        "control_count": 4,
    },
    {
        "id": "chapter_4",
        "number": "4",
        "name_en": "Asset Management",
        "name_de": "Verwaltung der Werte",
        "description_en": "Asset inventory, classification, and handling",
        "control_count": 5,
    },
    {
        "id": "chapter_5",
        "number": "5",
        "name_en": "Access Control",
        "name_de": "Zugangssteuerung",
        "description_en": "User access management and responsibilities",
        "control_count": 6,
    },
    {
        "id": "chapter_6",
        "number": "6",
        "name_en": "Cryptography",
        "name_de": "Kryptographie",
        "description_en": "Cryptographic controls and key management",
        "control_count": 3,
    },
    {
        "id": "chapter_7",
        "number": "7",
        "name_en": "Physical Security",
        "name_de": "Physische Sicherheit",
        "description_en": "Secure areas and equipment protection",
        "control_count": 6,
    },
    {
        "id": "chapter_8",
        "number": "8",
        "name_en": "Operations Security",
        "name_de": "Betriebssicherheit",
        "description_en": "Operational procedures and malware protection",
        "control_count": 7,
    },
    {
        "id": "chapter_9",
        "number": "9",
        "name_en": "Communications Security",
        "name_de": "Kommunikationssicherheit",
        "description_en": "Network security and information transfer",
        "control_count": 4,
    },
    {
        "id": "chapter_10",
        "number": "10",
        "name_en": "System Acquisition & Development",
        "name_de": "Anschaffung, Entwicklung und Wartung",
        "description_en": "Security in development and procurement",
        "control_count": 5,
    },
    {
        "id": "chapter_11",
        "number": "11",
        "name_en": "Supplier Relationships",
        "name_de": "Lieferantenbeziehungen",
        "description_en": "Information security in supplier agreements",
        "control_count": 4,
    },
    {
        "id": "chapter_12",
        "number": "12",
        "name_en": "Incident Management",
        "name_de": "Handhabung von Sicherheitsvorfällen",
        "description_en": "Security incident management and improvement",
        "control_count": 4,
    },
    {
        "id": "chapter_13",
        "number": "13",
        "name_en": "Business Continuity",
        "name_de": "Betriebskontinuitätsmanagement",
        "description_en": "Business continuity and redundancy",
        "control_count": 3,
    },
    {
        "id": "chapter_14",
        "number": "14",
        "name_en": "Compliance",
        "name_de": "Compliance",
        "description_en": "Legal, regulatory, and contractual compliance",
        "control_count": 4,
    },
]

# VDA ISA Controls (simplified - key controls per chapter)
TISAX_CONTROLS = [
    # Chapter 1: Information Security Policies
    {
        "id": "ISA-1.1",
        "chapter": "chapter_1",
        "number": "1.1",
        "name_en": "Information Security Policy",
        "name_de": "Informationssicherheitsrichtlinie",
        "description_en": "A set of policies for information security shall be defined, approved by management, published and communicated",
        "description_de": "Ein Satz von Richtlinien für Informationssicherheit muss definiert, vom Management genehmigt, veröffentlicht und kommuniziert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Policy document exists", "Management approval documented", "Communication to employees"],
        "should_requirements": ["Regular policy review", "Version control"],
    },
    {
        "id": "ISA-1.2",
        "chapter": "chapter_1",
        "number": "1.2",
        "name_en": "Review of Policies",
        "name_de": "Überprüfung der Richtlinien",
        "description_en": "Information security policies shall be reviewed at planned intervals or when significant changes occur",
        "description_de": "Informationssicherheitsrichtlinien müssen in geplanten Intervallen oder bei wesentlichen Änderungen überprüft werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Review process defined", "Review documentation"],
        "should_requirements": ["Annual review minimum"],
    },
    {
        "id": "ISA-1.3",
        "chapter": "chapter_1",
        "number": "1.3",
        "name_en": "Roles and Responsibilities",
        "name_de": "Rollen und Verantwortlichkeiten",
        "description_en": "All information security responsibilities shall be defined and allocated",
        "description_de": "Alle Informationssicherheitsverantwortlichkeiten müssen definiert und zugewiesen werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["CISO/ISB appointed", "Responsibilities documented"],
        "should_requirements": ["RACI matrix", "Regular review of roles"],
    },
    {
        "id": "ISA-1.4",
        "chapter": "chapter_1",
        "number": "1.4",
        "name_en": "Management Commitment",
        "name_de": "Management-Engagement",
        "description_en": "Management shall actively support security through direction, commitment and resources",
        "description_de": "Das Management muss Sicherheit durch Führung, Engagement und Ressourcen aktiv unterstützen",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Budget allocation", "Management participation"],
        "should_requirements": ["Security in management meetings"],
    },

    # Chapter 2: Organization of Information Security
    {
        "id": "ISA-2.1",
        "chapter": "chapter_2",
        "number": "2.1",
        "name_en": "Internal Organization",
        "name_de": "Interne Organisation",
        "description_en": "A management framework shall be established to initiate and control implementation of information security",
        "description_de": "Ein Management-Rahmenwerk muss etabliert werden zur Initiierung und Steuerung der Informationssicherheit",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Security organization defined", "Reporting lines clear"],
        "should_requirements": ["Security committee established"],
    },
    {
        "id": "ISA-2.2",
        "chapter": "chapter_2",
        "number": "2.2",
        "name_en": "Segregation of Duties",
        "name_de": "Aufgabentrennung",
        "description_en": "Conflicting duties and areas of responsibility shall be segregated",
        "description_de": "Konfligierende Aufgaben und Verantwortungsbereiche müssen getrennt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Duty segregation documented", "Access rights aligned"],
        "should_requirements": ["Regular review of segregation"],
    },
    {
        "id": "ISA-2.3",
        "chapter": "chapter_2",
        "number": "2.3",
        "name_en": "Contact with Authorities",
        "name_de": "Kontakt mit Behörden",
        "description_en": "Appropriate contacts with relevant authorities shall be maintained",
        "description_de": "Angemessene Kontakte mit relevanten Behörden müssen gepflegt werden",
        "objective": "info_high",
        "weight": 8,
        "must_requirements": ["Contact list maintained", "Incident reporting procedures"],
        "should_requirements": ["Regular contact testing"],
    },
    {
        "id": "ISA-2.4",
        "chapter": "chapter_2",
        "number": "2.4",
        "name_en": "Mobile Device Policy",
        "name_de": "Richtlinie für mobile Geräte",
        "description_en": "A policy and supporting security measures shall be adopted to manage risks from mobile devices",
        "description_de": "Eine Richtlinie und unterstützende Sicherheitsmaßnahmen müssen für mobile Geräte umgesetzt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Mobile device policy", "MDM solution"],
        "should_requirements": ["Container solution for BYOD"],
    },
    {
        "id": "ISA-2.5",
        "chapter": "chapter_2",
        "number": "2.5",
        "name_en": "Teleworking",
        "name_de": "Telearbeit",
        "description_en": "A policy and supporting security measures shall be implemented to protect information accessed, processed or stored at teleworking sites",
        "description_de": "Eine Richtlinie und Sicherheitsmaßnahmen müssen für Telearbeit umgesetzt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Teleworking policy", "VPN access", "Secure home office guidelines"],
        "should_requirements": ["Regular compliance checks"],
    },

    # Chapter 3: Human Resource Security
    {
        "id": "ISA-3.1",
        "chapter": "chapter_3",
        "number": "3.1",
        "name_en": "Screening",
        "name_de": "Überprüfung",
        "description_en": "Background verification checks shall be carried out on all candidates for employment",
        "description_de": "Hintergrundüberprüfungen müssen für alle Bewerber durchgeführt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Background check process", "Documentation"],
        "should_requirements": ["Risk-based screening levels"],
    },
    {
        "id": "ISA-3.2",
        "chapter": "chapter_3",
        "number": "3.2",
        "name_en": "Terms and Conditions",
        "name_de": "Beschäftigungsbedingungen",
        "description_en": "Employment contracts shall state employee and organization responsibilities for information security",
        "description_de": "Arbeitsverträge müssen die Verantwortlichkeiten für Informationssicherheit enthalten",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Security clauses in contracts", "NDA signed"],
        "should_requirements": ["Regular contract review"],
    },
    {
        "id": "ISA-3.3",
        "chapter": "chapter_3",
        "number": "3.3",
        "name_en": "Security Awareness",
        "name_de": "Sicherheitsbewusstsein",
        "description_en": "All employees shall receive appropriate awareness education and training",
        "description_de": "Alle Mitarbeiter müssen angemessene Sensibilisierung und Schulung erhalten",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Initial training", "Annual refresher", "Training records"],
        "should_requirements": ["Role-specific training", "Phishing tests"],
    },
    {
        "id": "ISA-3.4",
        "chapter": "chapter_3",
        "number": "3.4",
        "name_en": "Termination Process",
        "name_de": "Beendigungsprozess",
        "description_en": "Information security responsibilities that remain valid after termination shall be defined, communicated and enforced",
        "description_de": "Fortbestehende Sicherheitspflichten nach Beendigung müssen definiert und kommuniziert werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Offboarding checklist", "Access revocation process"],
        "should_requirements": ["Exit interview"],
    },

    # Chapter 4: Asset Management
    {
        "id": "ISA-4.1",
        "chapter": "chapter_4",
        "number": "4.1",
        "name_en": "Asset Inventory",
        "name_de": "Inventar der Werte",
        "description_en": "Assets associated with information and information processing facilities shall be identified and inventoried",
        "description_de": "Werte im Zusammenhang mit Informationen und Verarbeitungseinrichtungen müssen identifiziert und inventarisiert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Asset register", "Owner assignment"],
        "should_requirements": ["Automated discovery", "Regular reconciliation"],
    },
    {
        "id": "ISA-4.2",
        "chapter": "chapter_4",
        "number": "4.2",
        "name_en": "Information Classification",
        "name_de": "Klassifizierung von Informationen",
        "description_en": "Information shall be classified in terms of legal requirements, value, criticality and sensitivity",
        "description_de": "Informationen müssen nach rechtlichen Anforderungen, Wert, Kritikalität und Sensibilität klassifiziert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Classification scheme", "Labeling procedures"],
        "should_requirements": ["Automated classification tools"],
    },
    {
        "id": "ISA-4.3",
        "chapter": "chapter_4",
        "number": "4.3",
        "name_en": "Media Handling",
        "name_de": "Handhabung von Datenträgern",
        "description_en": "Procedures for handling assets shall be developed and implemented in accordance with classification",
        "description_de": "Verfahren für den Umgang mit Werten müssen entsprechend der Klassifizierung entwickelt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Media handling procedures", "Secure disposal"],
        "should_requirements": ["Encryption for mobile media"],
    },
    {
        "id": "ISA-4.4",
        "chapter": "chapter_4",
        "number": "4.4",
        "name_en": "Return of Assets",
        "name_de": "Rückgabe von Werten",
        "description_en": "All employees shall return all organizational assets upon termination",
        "description_de": "Alle Mitarbeiter müssen bei Beendigung alle Organisationswerte zurückgeben",
        "objective": "info_high",
        "weight": 8,
        "must_requirements": ["Return process", "Checklist"],
        "should_requirements": ["Asset tracking system"],
    },
    {
        "id": "ISA-4.5",
        "chapter": "chapter_4",
        "number": "4.5",
        "name_en": "Acceptable Use",
        "name_de": "Zulässige Nutzung",
        "description_en": "Rules for acceptable use of information and assets shall be identified, documented and implemented",
        "description_de": "Regeln für die zulässige Nutzung von Informationen und Werten müssen dokumentiert werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Acceptable use policy", "User acknowledgment"],
        "should_requirements": ["Regular policy review"],
    },

    # Chapter 5: Access Control
    {
        "id": "ISA-5.1",
        "chapter": "chapter_5",
        "number": "5.1",
        "name_en": "Access Control Policy",
        "name_de": "Zugangssteuerungsrichtlinie",
        "description_en": "An access control policy shall be established, documented and reviewed based on business requirements",
        "description_de": "Eine Zugangssteuerungsrichtlinie muss basierend auf Geschäftsanforderungen etabliert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Access control policy", "Need-to-know principle"],
        "should_requirements": ["Role-based access control"],
    },
    {
        "id": "ISA-5.2",
        "chapter": "chapter_5",
        "number": "5.2",
        "name_en": "User Registration",
        "name_de": "Benutzerregistrierung",
        "description_en": "A formal user registration and de-registration process shall be implemented",
        "description_de": "Ein formeller Benutzerregistrierungs- und Deregistrierungsprozess muss implementiert werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["User provisioning process", "Approval workflow"],
        "should_requirements": ["Identity management system"],
    },
    {
        "id": "ISA-5.3",
        "chapter": "chapter_5",
        "number": "5.3",
        "name_en": "Privileged Access",
        "name_de": "Privilegierter Zugang",
        "description_en": "The allocation and use of privileged access rights shall be restricted and controlled",
        "description_de": "Die Zuweisung und Nutzung privilegierter Zugriffsrechte muss eingeschränkt und kontrolliert werden",
        "objective": "info_very_high",
        "weight": 15,
        "must_requirements": ["Admin account management", "Privileged access logging"],
        "should_requirements": ["PAM solution", "Just-in-time access"],
    },
    {
        "id": "ISA-5.4",
        "chapter": "chapter_5",
        "number": "5.4",
        "name_en": "Authentication",
        "name_de": "Authentifizierung",
        "description_en": "A secure authentication procedure shall control access to systems and applications",
        "description_de": "Ein sicheres Authentifizierungsverfahren muss den Zugang zu Systemen kontrollieren",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Strong passwords", "Account lockout"],
        "should_requirements": ["Multi-factor authentication", "SSO"],
    },
    {
        "id": "ISA-5.5",
        "chapter": "chapter_5",
        "number": "5.5",
        "name_en": "Access Rights Review",
        "name_de": "Überprüfung von Zugriffsrechten",
        "description_en": "Asset owners shall review user access rights at regular intervals",
        "description_de": "Eigentümer von Werten müssen Benutzerzugriffsrechte regelmäßig überprüfen",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Periodic access review", "Documentation"],
        "should_requirements": ["Automated review tools"],
    },
    {
        "id": "ISA-5.6",
        "chapter": "chapter_5",
        "number": "5.6",
        "name_en": "Remote Access",
        "name_de": "Fernzugriff",
        "description_en": "Access to networks and network services shall be secured",
        "description_de": "Der Zugang zu Netzwerken und Netzwerkdiensten muss gesichert werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["VPN required", "Remote access policy"],
        "should_requirements": ["Network access control"],
    },

    # Chapter 6: Cryptography
    {
        "id": "ISA-6.1",
        "chapter": "chapter_6",
        "number": "6.1",
        "name_en": "Cryptographic Policy",
        "name_de": "Kryptographierichtlinie",
        "description_en": "A policy on the use of cryptographic controls for protection of information shall be developed",
        "description_de": "Eine Richtlinie für kryptographische Kontrollen zum Schutz von Informationen muss entwickelt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Crypto policy", "Approved algorithms"],
        "should_requirements": ["Crypto standards documentation"],
    },
    {
        "id": "ISA-6.2",
        "chapter": "chapter_6",
        "number": "6.2",
        "name_en": "Key Management",
        "name_de": "Schlüsselmanagement",
        "description_en": "A policy on the use, protection and lifetime of cryptographic keys shall be developed",
        "description_de": "Eine Richtlinie für Nutzung, Schutz und Lebensdauer kryptographischer Schlüssel muss entwickelt werden",
        "objective": "info_very_high",
        "weight": 15,
        "must_requirements": ["Key management procedures", "Secure key storage"],
        "should_requirements": ["HSM usage", "Key rotation"],
    },
    {
        "id": "ISA-6.3",
        "chapter": "chapter_6",
        "number": "6.3",
        "name_en": "Data Encryption",
        "name_de": "Datenverschlüsselung",
        "description_en": "Information shall be encrypted at rest and in transit according to classification",
        "description_de": "Informationen müssen entsprechend der Klassifizierung verschlüsselt werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Encryption at rest", "Encryption in transit"],
        "should_requirements": ["End-to-end encryption"],
    },

    # Chapter 7: Physical Security
    {
        "id": "ISA-7.1",
        "chapter": "chapter_7",
        "number": "7.1",
        "name_en": "Physical Security Perimeter",
        "name_de": "Physische Sicherheitszonen",
        "description_en": "Security perimeters shall be defined and used to protect areas containing sensitive information",
        "description_de": "Sicherheitszonen müssen definiert werden zum Schutz sensibler Bereiche",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Zone concept", "Access controls"],
        "should_requirements": ["Intrusion detection"],
    },
    {
        "id": "ISA-7.2",
        "chapter": "chapter_7",
        "number": "7.2",
        "name_en": "Entry Controls",
        "name_de": "Zutrittskontrolle",
        "description_en": "Secure areas shall be protected by appropriate entry controls",
        "description_de": "Sichere Bereiche müssen durch angemessene Zutrittskontrollen geschützt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Access control system", "Visitor management"],
        "should_requirements": ["Biometric controls"],
    },
    {
        "id": "ISA-7.3",
        "chapter": "chapter_7",
        "number": "7.3",
        "name_en": "Securing Offices",
        "name_de": "Sicherung von Büros",
        "description_en": "Physical security for offices, rooms and facilities shall be designed and applied",
        "description_de": "Physische Sicherheit für Büros und Räume muss gestaltet und angewandt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Clean desk policy", "Screen lock"],
        "should_requirements": ["Privacy screens"],
    },
    {
        "id": "ISA-7.4",
        "chapter": "chapter_7",
        "number": "7.4",
        "name_en": "Equipment Protection",
        "name_de": "Schutz von Betriebsmitteln",
        "description_en": "Equipment shall be protected from physical and environmental threats",
        "description_de": "Betriebsmittel müssen vor physischen und umgebungsbedingten Bedrohungen geschützt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Equipment siting", "Environmental controls"],
        "should_requirements": ["UPS", "Fire suppression"],
    },
    {
        "id": "ISA-7.5",
        "chapter": "chapter_7",
        "number": "7.5",
        "name_en": "Supporting Utilities",
        "name_de": "Versorgungseinrichtungen",
        "description_en": "Equipment shall be protected from power failures and other disruptions",
        "description_de": "Betriebsmittel müssen vor Stromausfällen und anderen Störungen geschützt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Power protection", "Redundancy"],
        "should_requirements": ["Generator backup"],
    },
    {
        "id": "ISA-7.6",
        "chapter": "chapter_7",
        "number": "7.6",
        "name_en": "Equipment Disposal",
        "name_de": "Entsorgung von Betriebsmitteln",
        "description_en": "All items containing storage media shall be verified to ensure sensitive data is removed",
        "description_de": "Alle Gegenstände mit Speichermedien müssen vor Entsorgung bereinigt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Secure disposal process", "Data destruction"],
        "should_requirements": ["Destruction certificates"],
    },

    # Chapter 8: Operations Security
    {
        "id": "ISA-8.1",
        "chapter": "chapter_8",
        "number": "8.1",
        "name_en": "Operational Procedures",
        "name_de": "Betriebsverfahren",
        "description_en": "Operating procedures shall be documented and made available to all users",
        "description_de": "Betriebsverfahren müssen dokumentiert und allen Benutzern zugänglich sein",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Documented procedures", "Change management"],
        "should_requirements": ["Runbooks", "Automation"],
    },
    {
        "id": "ISA-8.2",
        "chapter": "chapter_8",
        "number": "8.2",
        "name_en": "Change Management",
        "name_de": "Änderungsmanagement",
        "description_en": "Changes to the organization, business processes, systems shall be controlled",
        "description_de": "Änderungen an Organisation, Prozessen und Systemen müssen kontrolliert werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Change process", "Approval workflow"],
        "should_requirements": ["CAB meetings", "Impact assessment"],
    },
    {
        "id": "ISA-8.3",
        "chapter": "chapter_8",
        "number": "8.3",
        "name_en": "Capacity Management",
        "name_de": "Kapazitätsmanagement",
        "description_en": "The use of resources shall be monitored and adjusted to ensure required system performance",
        "description_de": "Die Ressourcennutzung muss überwacht und angepasst werden",
        "objective": "info_high",
        "weight": 8,
        "must_requirements": ["Capacity monitoring", "Planning"],
        "should_requirements": ["Auto-scaling"],
    },
    {
        "id": "ISA-8.4",
        "chapter": "chapter_8",
        "number": "8.4",
        "name_en": "Malware Protection",
        "name_de": "Schutz vor Schadsoftware",
        "description_en": "Detection, prevention and recovery controls against malware shall be implemented",
        "description_de": "Erkennungs-, Präventions- und Wiederherstellungskontrollen gegen Schadsoftware müssen implementiert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Anti-malware solution", "Regular updates"],
        "should_requirements": ["EDR solution", "Behavioral analysis"],
    },
    {
        "id": "ISA-8.5",
        "chapter": "chapter_8",
        "number": "8.5",
        "name_en": "Backup",
        "name_de": "Datensicherung",
        "description_en": "Backup copies of information, software and system images shall be taken and tested regularly",
        "description_de": "Sicherungskopien von Informationen, Software und Systemabbildern müssen regelmäßig erstellt und getestet werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Backup strategy", "Regular backups", "Recovery testing"],
        "should_requirements": ["Offsite backup", "Encryption"],
    },
    {
        "id": "ISA-8.6",
        "chapter": "chapter_8",
        "number": "8.6",
        "name_en": "Logging and Monitoring",
        "name_de": "Protokollierung und Überwachung",
        "description_en": "Event logs recording user activities, exceptions and security events shall be produced and reviewed",
        "description_de": "Ereignisprotokolle müssen erstellt, aufbewahrt und regelmäßig überprüft werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Logging enabled", "Log retention", "Regular review"],
        "should_requirements": ["SIEM solution", "Alerting"],
    },
    {
        "id": "ISA-8.7",
        "chapter": "chapter_8",
        "number": "8.7",
        "name_en": "Vulnerability Management",
        "name_de": "Schwachstellenmanagement",
        "description_en": "Information about technical vulnerabilities shall be obtained and appropriate measures taken",
        "description_de": "Informationen über technische Schwachstellen müssen beschafft und Maßnahmen ergriffen werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Vulnerability scanning", "Patch management"],
        "should_requirements": ["Continuous scanning", "Risk prioritization"],
    },

    # Chapter 9: Communications Security
    {
        "id": "ISA-9.1",
        "chapter": "chapter_9",
        "number": "9.1",
        "name_en": "Network Security",
        "name_de": "Netzwerksicherheit",
        "description_en": "Networks shall be managed and controlled to protect information in systems and applications",
        "description_de": "Netzwerke müssen verwaltet und kontrolliert werden zum Schutz von Informationen",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Network segmentation", "Firewall"],
        "should_requirements": ["IDS/IPS", "Network monitoring"],
    },
    {
        "id": "ISA-9.2",
        "chapter": "chapter_9",
        "number": "9.2",
        "name_en": "Network Services",
        "name_de": "Netzwerkdienste",
        "description_en": "Security mechanisms, service levels and requirements shall be identified and included in agreements",
        "description_de": "Sicherheitsmechanismen und Dienstgüteanforderungen müssen in Vereinbarungen aufgenommen werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["SLA documentation", "Security requirements"],
        "should_requirements": ["Regular review"],
    },
    {
        "id": "ISA-9.3",
        "chapter": "chapter_9",
        "number": "9.3",
        "name_en": "Information Transfer",
        "name_de": "Informationsübertragung",
        "description_en": "Formal transfer policies and procedures shall protect information transfer through all types of communication",
        "description_de": "Formelle Übertragungsrichtlinien müssen die Informationsübertragung schützen",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Transfer policy", "Secure channels"],
        "should_requirements": ["DLP solution"],
    },
    {
        "id": "ISA-9.4",
        "chapter": "chapter_9",
        "number": "9.4",
        "name_en": "Electronic Messaging",
        "name_de": "Elektronische Nachrichtenübermittlung",
        "description_en": "Information involved in electronic messaging shall be appropriately protected",
        "description_de": "Informationen in elektronischen Nachrichten müssen angemessen geschützt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Email security", "Encryption capability"],
        "should_requirements": ["S/MIME or PGP", "Email filtering"],
    },

    # Chapter 10: System Acquisition & Development
    {
        "id": "ISA-10.1",
        "chapter": "chapter_10",
        "number": "10.1",
        "name_en": "Security Requirements",
        "name_de": "Sicherheitsanforderungen",
        "description_en": "Information security requirements shall be included in requirements for new systems or enhancements",
        "description_de": "Informationssicherheitsanforderungen müssen in Anforderungen für neue Systeme aufgenommen werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Security requirements process", "Documentation"],
        "should_requirements": ["Security architecture review"],
    },
    {
        "id": "ISA-10.2",
        "chapter": "chapter_10",
        "number": "10.2",
        "name_en": "Secure Development",
        "name_de": "Sichere Entwicklung",
        "description_en": "Rules for development of software and systems shall be established and applied",
        "description_de": "Regeln für die Entwicklung von Software und Systemen müssen etabliert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Secure coding guidelines", "Code review"],
        "should_requirements": ["SAST/DAST tools", "Security training"],
    },
    {
        "id": "ISA-10.3",
        "chapter": "chapter_10",
        "number": "10.3",
        "name_en": "Test Data Protection",
        "name_de": "Schutz von Testdaten",
        "description_en": "Test data shall be selected carefully, protected and controlled",
        "description_de": "Testdaten müssen sorgfältig ausgewählt, geschützt und kontrolliert werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Test data policy", "Data masking"],
        "should_requirements": ["Synthetic test data"],
    },
    {
        "id": "ISA-10.4",
        "chapter": "chapter_10",
        "number": "10.4",
        "name_en": "System Acceptance Testing",
        "name_de": "Systemabnahmetests",
        "description_en": "Acceptance testing programs and related criteria shall be established",
        "description_de": "Abnahmetestprogramme und zugehörige Kriterien müssen etabliert werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Acceptance criteria", "Testing process"],
        "should_requirements": ["Security testing included"],
    },
    {
        "id": "ISA-10.5",
        "chapter": "chapter_10",
        "number": "10.5",
        "name_en": "Development Environment",
        "name_de": "Entwicklungsumgebung",
        "description_en": "Development, testing and operational environments shall be separated",
        "description_de": "Entwicklungs-, Test- und Produktionsumgebungen müssen getrennt werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Environment separation", "Access controls"],
        "should_requirements": ["Infrastructure as Code"],
    },

    # Chapter 11: Supplier Relationships
    {
        "id": "ISA-11.1",
        "chapter": "chapter_11",
        "number": "11.1",
        "name_en": "Supplier Security Policy",
        "name_de": "Lieferantensicherheitsrichtlinie",
        "description_en": "Information security requirements for mitigating risks from supplier access shall be agreed",
        "description_de": "Informationssicherheitsanforderungen zur Risikominderung bei Lieferantenzugang müssen vereinbart werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Supplier security policy", "Risk assessment"],
        "should_requirements": ["Supplier classification"],
    },
    {
        "id": "ISA-11.2",
        "chapter": "chapter_11",
        "number": "11.2",
        "name_en": "Supplier Agreements",
        "name_de": "Lieferantenvereinbarungen",
        "description_en": "All relevant information security requirements shall be established in agreements with suppliers",
        "description_de": "Alle relevanten Sicherheitsanforderungen müssen in Lieferantenvereinbarungen festgelegt werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Security clauses", "Audit rights"],
        "should_requirements": ["Security SLA"],
    },
    {
        "id": "ISA-11.3",
        "chapter": "chapter_11",
        "number": "11.3",
        "name_en": "Supplier Monitoring",
        "name_de": "Lieferantenüberwachung",
        "description_en": "Organizations shall monitor, review and audit supplier service delivery regularly",
        "description_de": "Organisationen müssen Lieferantenleistungen regelmäßig überwachen und auditieren",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Regular reviews", "Performance monitoring"],
        "should_requirements": ["Security assessments"],
    },
    {
        "id": "ISA-11.4",
        "chapter": "chapter_11",
        "number": "11.4",
        "name_en": "Supply Chain Security",
        "name_de": "Lieferkettensicherheit",
        "description_en": "Agreements with suppliers shall include requirements for addressing supply chain risks",
        "description_de": "Vereinbarungen mit Lieferanten müssen Anforderungen zur Bewältigung von Lieferkettenrisiken enthalten",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Supply chain assessment", "Subcontractor controls"],
        "should_requirements": ["Tiered supplier management"],
    },

    # Chapter 12: Incident Management
    {
        "id": "ISA-12.1",
        "chapter": "chapter_12",
        "number": "12.1",
        "name_en": "Incident Management Process",
        "name_de": "Vorfallmanagementprozess",
        "description_en": "Responsibilities and procedures shall be established to ensure effective incident response",
        "description_de": "Verantwortlichkeiten und Verfahren müssen für effektive Vorfallreaktion etabliert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Incident process", "Response team"],
        "should_requirements": ["24/7 response capability"],
    },
    {
        "id": "ISA-12.2",
        "chapter": "chapter_12",
        "number": "12.2",
        "name_en": "Incident Reporting",
        "name_de": "Vorfallmeldung",
        "description_en": "Information security events shall be reported through appropriate channels as quickly as possible",
        "description_de": "Informationssicherheitsereignisse müssen so schnell wie möglich über geeignete Kanäle gemeldet werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Reporting channels", "Escalation procedures"],
        "should_requirements": ["Automated alerting"],
    },
    {
        "id": "ISA-12.3",
        "chapter": "chapter_12",
        "number": "12.3",
        "name_en": "Incident Response",
        "name_de": "Vorfallreaktion",
        "description_en": "Information security incidents shall be responded to in accordance with documented procedures",
        "description_de": "Auf Informationssicherheitsvorfälle muss gemäß dokumentierten Verfahren reagiert werden",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["Response procedures", "Containment measures"],
        "should_requirements": ["Forensic capability", "Playbooks"],
    },
    {
        "id": "ISA-12.4",
        "chapter": "chapter_12",
        "number": "12.4",
        "name_en": "Lessons Learned",
        "name_de": "Lessons Learned",
        "description_en": "Knowledge gained from analyzing incidents shall be used to reduce likelihood or impact of future incidents",
        "description_de": "Erkenntnisse aus der Analyse von Vorfällen müssen genutzt werden",
        "objective": "info_high",
        "weight": 10,
        "must_requirements": ["Post-incident review", "Documentation"],
        "should_requirements": ["Trend analysis", "Process improvement"],
    },

    # Chapter 13: Business Continuity
    {
        "id": "ISA-13.1",
        "chapter": "chapter_13",
        "number": "13.1",
        "name_en": "BCM Planning",
        "name_de": "BCM-Planung",
        "description_en": "The organization shall determine requirements for information security continuity in adverse situations",
        "description_de": "Die Organisation muss Anforderungen für Informationssicherheitskontinuität bestimmen",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["BCM policy", "BIA conducted"],
        "should_requirements": ["BCM program"],
    },
    {
        "id": "ISA-13.2",
        "chapter": "chapter_13",
        "number": "13.2",
        "name_en": "BCM Implementation",
        "name_de": "BCM-Umsetzung",
        "description_en": "The organization shall establish, document, implement and maintain processes to ensure continuity",
        "description_de": "Die Organisation muss Prozesse zur Sicherstellung der Kontinuität etablieren und pflegen",
        "objective": "info_high",
        "weight": 15,
        "must_requirements": ["BC plans documented", "Recovery procedures"],
        "should_requirements": ["Alternate site"],
    },
    {
        "id": "ISA-13.3",
        "chapter": "chapter_13",
        "number": "13.3",
        "name_en": "BCM Testing",
        "name_de": "BCM-Tests",
        "description_en": "The organization shall verify established continuity controls at regular intervals",
        "description_de": "Die Organisation muss etablierte Kontinuitätskontrollen regelmäßig verifizieren",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Regular testing", "Test documentation"],
        "should_requirements": ["Annual exercises", "Tabletop exercises"],
    },

    # Chapter 14: Compliance
    {
        "id": "ISA-14.1",
        "chapter": "chapter_14",
        "number": "14.1",
        "name_en": "Legal Requirements",
        "name_de": "Rechtliche Anforderungen",
        "description_en": "All relevant legislative, regulatory and contractual requirements shall be identified and documented",
        "description_de": "Alle relevanten gesetzlichen, regulatorischen und vertraglichen Anforderungen müssen identifiziert werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Requirements register", "Regular updates"],
        "should_requirements": ["Legal monitoring service"],
    },
    {
        "id": "ISA-14.2",
        "chapter": "chapter_14",
        "number": "14.2",
        "name_en": "Privacy and Data Protection",
        "name_de": "Datenschutz",
        "description_en": "Privacy and protection of personal data shall be ensured as required",
        "description_de": "Datenschutz und Schutz personenbezogener Daten müssen sichergestellt werden",
        "objective": "data_protection",
        "weight": 15,
        "must_requirements": ["GDPR compliance", "DPO appointed"],
        "should_requirements": ["Privacy by design", "DPIA process"],
    },
    {
        "id": "ISA-14.3",
        "chapter": "chapter_14",
        "number": "14.3",
        "name_en": "Independent Review",
        "name_de": "Unabhängige Überprüfung",
        "description_en": "The organization's approach to managing information security shall be reviewed independently",
        "description_de": "Der Ansatz der Organisation zur Informationssicherheit muss unabhängig überprüft werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Internal audits", "Audit program"],
        "should_requirements": ["External audits", "Certification"],
    },
    {
        "id": "ISA-14.4",
        "chapter": "chapter_14",
        "number": "14.4",
        "name_en": "Technical Compliance",
        "name_de": "Technische Compliance",
        "description_en": "Information systems shall be regularly reviewed for compliance with security policies",
        "description_de": "Informationssysteme müssen regelmäßig auf Einhaltung der Sicherheitsrichtlinien überprüft werden",
        "objective": "info_high",
        "weight": 12,
        "must_requirements": ["Technical assessments", "Compliance checks"],
        "should_requirements": ["Automated compliance tools"],
    },

    # Prototype Protection (Additional controls for AL3)
    {
        "id": "ISA-PP-1",
        "chapter": "chapter_7",
        "number": "PP.1",
        "name_en": "Prototype Physical Security",
        "name_de": "Physische Prototypensicherheit",
        "description_en": "Physical prototypes shall be stored in secured areas with enhanced access controls",
        "description_de": "Physische Prototypen müssen in gesicherten Bereichen mit verstärkter Zugangskontrolle gelagert werden",
        "objective": "prototype",
        "weight": 20,
        "must_requirements": ["Dedicated prototype area", "Enhanced access control", "CCTV"],
        "should_requirements": ["Motion sensors", "24/7 monitoring"],
    },
    {
        "id": "ISA-PP-2",
        "chapter": "chapter_4",
        "number": "PP.2",
        "name_en": "Prototype Handling",
        "name_de": "Handhabung von Prototypen",
        "description_en": "Procedures for handling prototypes including transport and disposal shall be defined",
        "description_de": "Verfahren für den Umgang mit Prototypen einschließlich Transport und Entsorgung müssen definiert werden",
        "objective": "prototype",
        "weight": 18,
        "must_requirements": ["Handling procedures", "Chain of custody", "Secure transport"],
        "should_requirements": ["GPS tracking"],
    },
    {
        "id": "ISA-PP-3",
        "chapter": "chapter_7",
        "number": "PP.3",
        "name_en": "Test Vehicle Security",
        "name_de": "Testfahrzeugsicherheit",
        "description_en": "Test vehicles shall be protected with camouflage and restricted test areas",
        "description_de": "Testfahrzeuge müssen mit Tarnung und eingeschränkten Testgebieten geschützt werden",
        "objective": "prototype_vehicle",
        "weight": 20,
        "must_requirements": ["Camouflage procedures", "Restricted test areas", "Photography ban"],
        "should_requirements": ["GPS geofencing", "Driver training"],
    },
]


# Assessment Level Requirements
TISAX_ASSESSMENT_LEVELS = {
    TISAXAssessmentLevel.AL1: {
        "name_en": "Normal Protection Need",
        "name_de": "Normaler Schutzbedarf",
        "description_en": "Self-assessment without external verification",
        "description_de": "Selbstbewertung ohne externe Verifizierung",
        "audit_type": "self_assessment",
        "validity_years": 3,
        "min_maturity": 3,
    },
    TISAXAssessmentLevel.AL2: {
        "name_en": "High Protection Need",
        "name_de": "Hoher Schutzbedarf",
        "description_en": "Plausibility check by external auditor (remote possible)",
        "description_de": "Plausibilitätsprüfung durch externen Auditor (remote möglich)",
        "audit_type": "remote_audit",
        "validity_years": 3,
        "min_maturity": 3,
    },
    TISAXAssessmentLevel.AL3: {
        "name_en": "Very High Protection Need",
        "name_de": "Sehr hoher Schutzbedarf",
        "description_en": "Comprehensive on-site audit by external auditor",
        "description_de": "Umfassende Vor-Ort-Prüfung durch externen Auditor",
        "audit_type": "onsite_audit",
        "validity_years": 3,
        "min_maturity": 3,
    },
}


# Assessment Objectives
TISAX_OBJECTIVES = {
    TISAXAssessmentObjective.INFO_HIGH: {
        "name_en": "Information with High Protection Need",
        "name_de": "Informationen mit hohem Schutzbedarf",
        "description_en": "Handling of confidential information",
        "assessment_levels": [TISAXAssessmentLevel.AL2],
        "applicable_controls": "info_high",
    },
    TISAXAssessmentObjective.INFO_VERY_HIGH: {
        "name_en": "Information with Very High Protection Need",
        "name_de": "Informationen mit sehr hohem Schutzbedarf",
        "description_en": "Handling of strictly confidential information",
        "assessment_levels": [TISAXAssessmentLevel.AL3],
        "applicable_controls": "info_very_high",
    },
    TISAXAssessmentObjective.PROTOTYPE: {
        "name_en": "Prototype Protection",
        "name_de": "Prototypenschutz",
        "description_en": "Protection of physical and digital prototypes",
        "assessment_levels": [TISAXAssessmentLevel.AL3],
        "applicable_controls": "prototype",
    },
    TISAXAssessmentObjective.PROTOTYPE_VEHICLE: {
        "name_en": "Prototype Vehicle Protection",
        "name_de": "Prototypen-Fahrzeugschutz",
        "description_en": "Additional protection for test vehicles",
        "assessment_levels": [TISAXAssessmentLevel.AL3],
        "applicable_controls": "prototype_vehicle",
    },
    TISAXAssessmentObjective.DATA_PROTECTION: {
        "name_en": "Data Protection",
        "name_de": "Datenschutz",
        "description_en": "GDPR compliance for personal data processing",
        "assessment_levels": [TISAXAssessmentLevel.AL2, TISAXAssessmentLevel.AL3],
        "applicable_controls": "data_protection",
    },
}


# =============================================================================
# Database Models
# =============================================================================

class TISAXAssessment(Base):
    """TISAX Assessment for an organization."""
    __tablename__ = "tisax_assessments"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TISAXAssessmentStatus), default=TISAXAssessmentStatus.DRAFT)

    # Scope
    company_type = Column(SQLEnum(TISAXCompanyType), nullable=True)
    company_size = Column(SQLEnum(TISAXCompanySize), nullable=True)
    employee_count = Column(Integer, nullable=True)
    location_count = Column(Integer, default=1)

    # Assessment Configuration
    assessment_level = Column(SQLEnum(TISAXAssessmentLevel), nullable=True)
    objectives = Column(JSON, default=list)  # List of TISAXAssessmentObjective values

    # OEM Requirements (which OEMs require this assessment)
    oem_requirements = Column(JSON, default=list)  # e.g., ["VW", "BMW", "Mercedes"]

    # Scores
    overall_score = Column(Float, default=0.0)
    chapter_scores = Column(JSON, default=dict)  # Chapter ID -> score
    maturity_level = Column(Float, default=0.0)  # Average maturity (0-5)
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Target & Deadlines
    target_date = Column(DateTime, nullable=True)  # Target certification date
    audit_date = Column(DateTime, nullable=True)  # Scheduled audit date

    # Audit Info
    auditor_name = Column(String(255), nullable=True)
    audit_provider = Column(String(255), nullable=True)  # e.g., "TÜV", "DEKRA"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Owner
    created_by = Column(String(36), nullable=True)

    # Relationships
    responses = relationship("TISAXControlResponse", back_populates="assessment", cascade="all, delete-orphan")


class TISAXControlResponse(Base):
    """Response to a TISAX control within an assessment."""
    __tablename__ = "tisax_control_responses"

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(36), ForeignKey("tisax_assessments.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(String(50), nullable=False)  # e.g., "ISA-1.1"
    chapter_id = Column(String(50), nullable=False)  # e.g., "chapter_1"

    # VDA ISA Maturity Assessment
    maturity_level = Column(SQLEnum(TISAXMaturityLevel), default=TISAXMaturityLevel.LEVEL_0)
    target_maturity = Column(SQLEnum(TISAXMaturityLevel), default=TISAXMaturityLevel.LEVEL_3)

    # Evidence and Notes
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    gap_description = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)

    # Must/Should Requirements Status
    must_fulfilled = Column(JSON, default=list)  # List of fulfilled must requirements
    should_fulfilled = Column(JSON, default=list)  # List of fulfilled should requirements

    # Priority and Planning
    priority = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime, nullable=True)
    responsible = Column(String(255), nullable=True)

    # Timestamps
    assessed_at = Column(DateTime, nullable=True)
    assessed_by = Column(String(36), nullable=True)

    # Relationships
    assessment = relationship("TISAXAssessment", back_populates="responses")
