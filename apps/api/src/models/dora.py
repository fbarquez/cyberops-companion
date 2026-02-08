"""DORA (Digital Operational Resilience Act) compliance models."""
import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class DORAPillar(str, enum.Enum):
    """DORA's 5 main pillars."""
    ICT_RISK_MANAGEMENT = "ict_risk_management"      # Art. 5-16, 25%
    INCIDENT_REPORTING = "incident_reporting"         # Art. 17-23, 20%
    RESILIENCE_TESTING = "resilience_testing"         # Art. 24-27, 20%
    THIRD_PARTY_RISK = "third_party_risk"             # Art. 28-44, 25%
    INFORMATION_SHARING = "information_sharing"       # Art. 45, 10%


class DORAEntityType(str, enum.Enum):
    """DORA entity types (20+ financial entities under scope)."""
    # Core banking and finance
    CREDIT_INSTITUTION = "credit_institution"
    INVESTMENT_FIRM = "investment_firm"
    PAYMENT_INSTITUTION = "payment_institution"
    E_MONEY_INSTITUTION = "e_money_institution"
    # Insurance
    INSURANCE_UNDERTAKING = "insurance_undertaking"
    REINSURANCE_UNDERTAKING = "reinsurance_undertaking"
    INSURANCE_INTERMEDIARY = "insurance_intermediary"
    # Asset management
    UCITS_MANAGER = "ucits_manager"
    AIFM = "aifm"
    # Market infrastructure
    CENTRAL_COUNTERPARTY = "ccp"
    CENTRAL_SECURITIES_DEPOSITORY = "csd"
    TRADING_VENUE = "trading_venue"
    TRADE_REPOSITORY = "trade_repository"
    # New digital finance
    CRYPTO_ASSET_SERVICE_PROVIDER = "casp"
    CROWDFUNDING_PROVIDER = "crowdfunding"
    # Other regulated entities
    CREDIT_RATING_AGENCY = "cra"
    PENSION_FUND = "pension_fund"
    DATA_REPORTING_SERVICE_PROVIDER = "drsp"
    SECURITISATION_REPOSITORY = "securitisation_repository"
    # ICT providers
    ICT_SERVICE_PROVIDER = "ict_provider"  # CTPP - Critical Third-Party Provider


class DORACompanySize(str, enum.Enum):
    """Company size thresholds."""
    MICRO = "micro"          # <10 employees, <€2M
    SMALL = "small"          # <50 employees, <€10M
    MEDIUM = "medium"        # 50-249 employees, €10-50M
    LARGE = "large"          # 250+ employees, €50M+


class DORAAssessmentStatus(str, enum.Enum):
    """Assessment progress status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DORARequirementStatus(str, enum.Enum):
    """Compliance status for each requirement."""
    NOT_EVALUATED = "not_evaluated"
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NOT_APPLICABLE = "not_applicable"


# Pillar metadata for UI and scoring
DORA_PILLARS_METADATA = {
    DORAPillar.ICT_RISK_MANAGEMENT: {
        "name_en": "ICT Risk Management",
        "name_de": "IKT-Risikomanagement",
        "article_range": "5-16",
        "weight": 25,
        "icon": "shield-check",
        "description_en": "Governance, risk management framework, and operational resilience requirements"
    },
    DORAPillar.INCIDENT_REPORTING: {
        "name_en": "ICT Incident Reporting",
        "name_de": "IKT-Vorfallmeldung",
        "article_range": "17-23",
        "weight": 20,
        "icon": "alert-triangle",
        "description_en": "Incident management, classification, and reporting to competent authorities"
    },
    DORAPillar.RESILIENCE_TESTING: {
        "name_en": "Digital Resilience Testing",
        "name_de": "Digitale Resilienzprüfung",
        "article_range": "24-27",
        "weight": 20,
        "icon": "test-tube",
        "description_en": "Testing programme, TLPT, and validation of ICT systems"
    },
    DORAPillar.THIRD_PARTY_RISK: {
        "name_en": "ICT Third-Party Risk Management",
        "name_de": "IKT-Drittparteienrisikomanagement",
        "article_range": "28-44",
        "weight": 25,
        "icon": "users",
        "description_en": "Management of ICT service provider risks, contracts, and oversight"
    },
    DORAPillar.INFORMATION_SHARING: {
        "name_en": "Information Sharing",
        "name_de": "Informationsaustausch",
        "article_range": "45",
        "weight": 10,
        "icon": "share-2",
        "description_en": "Cyber threat intelligence and information sharing arrangements"
    },
}

# Entity type metadata for UI
ENTITY_TYPE_METADATA = {
    DORAEntityType.CREDIT_INSTITUTION: {
        "name_en": "Credit Institution",
        "name_de": "Kreditinstitut",
        "icon": "landmark",
        "requires_tlpt": True,
        "description_en": "Banks and credit institutions under CRD"
    },
    DORAEntityType.INVESTMENT_FIRM: {
        "name_en": "Investment Firm",
        "name_de": "Wertpapierfirma",
        "icon": "trending-up",
        "requires_tlpt": True,
        "description_en": "Investment firms under MiFID II"
    },
    DORAEntityType.PAYMENT_INSTITUTION: {
        "name_en": "Payment Institution",
        "name_de": "Zahlungsinstitut",
        "icon": "credit-card",
        "requires_tlpt": False,
        "description_en": "Payment service providers under PSD2"
    },
    DORAEntityType.E_MONEY_INSTITUTION: {
        "name_en": "E-Money Institution",
        "name_de": "E-Geld-Institut",
        "icon": "wallet",
        "requires_tlpt": False,
        "description_en": "Electronic money institutions under EMD2"
    },
    DORAEntityType.INSURANCE_UNDERTAKING: {
        "name_en": "Insurance Undertaking",
        "name_de": "Versicherungsunternehmen",
        "icon": "shield",
        "requires_tlpt": True,
        "description_en": "Insurance and reinsurance undertakings under Solvency II"
    },
    DORAEntityType.REINSURANCE_UNDERTAKING: {
        "name_en": "Reinsurance Undertaking",
        "name_de": "Rückversicherungsunternehmen",
        "icon": "shield-check",
        "requires_tlpt": True,
        "description_en": "Reinsurance undertakings under Solvency II"
    },
    DORAEntityType.INSURANCE_INTERMEDIARY: {
        "name_en": "Insurance Intermediary",
        "name_de": "Versicherungsvermittler",
        "icon": "briefcase",
        "requires_tlpt": False,
        "description_en": "Insurance intermediaries under IDD"
    },
    DORAEntityType.UCITS_MANAGER: {
        "name_en": "UCITS Management Company",
        "name_de": "OGAW-Verwaltungsgesellschaft",
        "icon": "pie-chart",
        "requires_tlpt": False,
        "description_en": "UCITS management companies under UCITS Directive"
    },
    DORAEntityType.AIFM: {
        "name_en": "Alternative Investment Fund Manager",
        "name_de": "Verwalter alternativer Investmentfonds",
        "icon": "bar-chart-3",
        "requires_tlpt": False,
        "description_en": "AIFMs under AIFMD"
    },
    DORAEntityType.CENTRAL_COUNTERPARTY: {
        "name_en": "Central Counterparty (CCP)",
        "name_de": "Zentrale Gegenpartei (CCP)",
        "icon": "git-merge",
        "requires_tlpt": True,
        "description_en": "Central counterparties under EMIR"
    },
    DORAEntityType.CENTRAL_SECURITIES_DEPOSITORY: {
        "name_en": "Central Securities Depository (CSD)",
        "name_de": "Zentralverwahrer (CSD)",
        "icon": "database",
        "requires_tlpt": True,
        "description_en": "Central securities depositories under CSDR"
    },
    DORAEntityType.TRADING_VENUE: {
        "name_en": "Trading Venue",
        "name_de": "Handelsplatz",
        "icon": "activity",
        "requires_tlpt": True,
        "description_en": "Operators of trading venues under MiFID II"
    },
    DORAEntityType.TRADE_REPOSITORY: {
        "name_en": "Trade Repository",
        "name_de": "Transaktionsregister",
        "icon": "file-text",
        "requires_tlpt": True,
        "description_en": "Trade repositories under EMIR/SFTR"
    },
    DORAEntityType.CRYPTO_ASSET_SERVICE_PROVIDER: {
        "name_en": "Crypto-Asset Service Provider (CASP)",
        "name_de": "Kryptowerte-Dienstleister (CASP)",
        "icon": "bitcoin",
        "requires_tlpt": False,
        "description_en": "Crypto-asset service providers under MiCA"
    },
    DORAEntityType.CROWDFUNDING_PROVIDER: {
        "name_en": "Crowdfunding Service Provider",
        "name_de": "Crowdfunding-Dienstleister",
        "icon": "users",
        "requires_tlpt": False,
        "description_en": "Crowdfunding service providers under ECSP Regulation"
    },
    DORAEntityType.CREDIT_RATING_AGENCY: {
        "name_en": "Credit Rating Agency",
        "name_de": "Ratingagentur",
        "icon": "star",
        "requires_tlpt": True,
        "description_en": "Credit rating agencies under CRA Regulation"
    },
    DORAEntityType.PENSION_FUND: {
        "name_en": "Occupational Pension Fund (IORP)",
        "name_de": "Einrichtung der betrieblichen Altersversorgung",
        "icon": "piggy-bank",
        "requires_tlpt": False,
        "description_en": "IORPs under IORP II Directive"
    },
    DORAEntityType.DATA_REPORTING_SERVICE_PROVIDER: {
        "name_en": "Data Reporting Service Provider",
        "name_de": "Datenbereitstellungsdienst",
        "icon": "file-bar-chart",
        "requires_tlpt": True,
        "description_en": "DRSPs under MiFID II (APAs, ARMs, CTPs)"
    },
    DORAEntityType.SECURITISATION_REPOSITORY: {
        "name_en": "Securitisation Repository",
        "name_de": "Verbriefungsregister",
        "icon": "folder-archive",
        "requires_tlpt": False,
        "description_en": "Securitisation repositories under STS Regulation"
    },
    DORAEntityType.ICT_SERVICE_PROVIDER: {
        "name_en": "Critical ICT Third-Party Service Provider",
        "name_de": "Kritischer IKT-Drittdienstleister",
        "icon": "cloud",
        "requires_tlpt": True,
        "description_en": "Critical third-party providers (CTPPs) under DORA oversight"
    },
}

# DORA Requirements - 28 requirements across 5 pillars
DORA_REQUIREMENTS = [
    # Pillar 1: ICT Risk Management (Art. 5-16) - 8 requirements
    {
        "id": "DORA-P1-01",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "5",
        "name_en": "Governance & Organization",
        "name_de": "Governance & Organisation",
        "description_en": "Management body defines, approves, and oversees ICT risk management framework with ultimate responsibility",
        "weight": 15,
        "sub_requirements": [
            "Clear ICT policies approved by management body",
            "Defined roles and responsibilities for ICT risk",
            "Regular management training on ICT risk",
            "Adequate resources allocated to ICT risk management"
        ]
    },
    {
        "id": "DORA-P1-02",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "6",
        "name_en": "ICT Risk Management Framework",
        "name_de": "IKT-Risikomanagement-Rahmenwerk",
        "description_en": "Comprehensive framework including strategies, policies, procedures, ICT protocols and tools",
        "weight": 15,
        "sub_requirements": [
            "Documented ICT risk management strategy",
            "Digital operational resilience strategy",
            "Methods for identifying and assessing ICT risks",
            "Risk tolerance thresholds defined"
        ]
    },
    {
        "id": "DORA-P1-03",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "7",
        "name_en": "ICT Systems, Protocols & Tools",
        "name_de": "IKT-Systeme, Protokolle & Tools",
        "description_en": "Use and maintain resilient ICT systems, protocols, and tools appropriate to the complexity of operations",
        "weight": 12,
        "sub_requirements": [
            "ICT systems designed for resilience",
            "Capacity and performance monitoring",
            "Regularly updated ICT protocols",
            "Appropriate ICT tools for operations"
        ]
    },
    {
        "id": "DORA-P1-04",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "8",
        "name_en": "Identification",
        "name_de": "Identifizierung",
        "description_en": "Identify, classify, and document all ICT assets, business functions, and their dependencies",
        "weight": 10,
        "sub_requirements": [
            "Complete inventory of ICT assets",
            "Business function and ICT asset mapping",
            "Identification of critical functions",
            "Documentation of interconnections and dependencies"
        ]
    },
    {
        "id": "DORA-P1-05",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "9",
        "name_en": "Protection & Prevention",
        "name_de": "Schutz & Prävention",
        "description_en": "Implement appropriate ICT security policies, procedures, and tools for protection and prevention",
        "weight": 12,
        "sub_requirements": [
            "Access control and identity management",
            "Network and infrastructure security",
            "Data protection and encryption",
            "Physical and environmental security"
        ]
    },
    {
        "id": "DORA-P1-06",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "10",
        "name_en": "Detection",
        "name_de": "Erkennung",
        "description_en": "Implement mechanisms to promptly detect anomalous activities and ICT-related incidents",
        "weight": 10,
        "sub_requirements": [
            "Continuous monitoring capabilities",
            "Anomaly detection mechanisms",
            "Logging and audit trails",
            "Threat intelligence integration"
        ]
    },
    {
        "id": "DORA-P1-07",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "11",
        "name_en": "Response & Recovery",
        "name_de": "Reaktion & Wiederherstellung",
        "description_en": "Implement ICT business continuity policy with response and recovery procedures",
        "weight": 13,
        "sub_requirements": [
            "ICT business continuity policy",
            "Response procedures for incidents",
            "Recovery time and point objectives",
            "Crisis management and communication plans"
        ]
    },
    {
        "id": "DORA-P1-08",
        "pillar": DORAPillar.ICT_RISK_MANAGEMENT,
        "article": "12-16",
        "name_en": "Backup, Learning & Communication",
        "name_de": "Sicherung, Lernen & Kommunikation",
        "description_en": "Backup policies, lessons learned processes, communication protocols, and simplified ICT risk management for eligible entities",
        "weight": 13,
        "sub_requirements": [
            "Backup and restoration policies",
            "Lessons learned from incidents and tests",
            "Internal and external communication plans",
            "Simplified framework for microenterprises (Art. 16)"
        ]
    },
    # Pillar 2: ICT Incident Reporting (Art. 17-23) - 5 requirements
    {
        "id": "DORA-P2-01",
        "pillar": DORAPillar.INCIDENT_REPORTING,
        "article": "17",
        "name_en": "Incident Management Process",
        "name_de": "Vorfallmanagement-Prozess",
        "description_en": "Establish incident management process to detect, manage, and notify ICT-related incidents",
        "weight": 15,
        "sub_requirements": [
            "Incident detection and recording procedures",
            "Early warning indicators defined",
            "Root cause analysis process",
            "Roles and responsibilities for incident handling"
        ]
    },
    {
        "id": "DORA-P2-02",
        "pillar": DORAPillar.INCIDENT_REPORTING,
        "article": "18",
        "name_en": "Classification of Incidents",
        "name_de": "Klassifizierung von Vorfällen",
        "description_en": "Classify ICT-related incidents based on criteria: clients affected, duration, geographic spread, data losses, criticality, economic impact",
        "weight": 12,
        "sub_requirements": [
            "Classification criteria defined",
            "Thresholds for major incidents",
            "Impact assessment methodology",
            "Severity levels and escalation rules"
        ]
    },
    {
        "id": "DORA-P2-03",
        "pillar": DORAPillar.INCIDENT_REPORTING,
        "article": "19",
        "name_en": "Reporting Major Incidents",
        "name_de": "Meldung schwerwiegender Vorfälle",
        "description_en": "Report major ICT-related incidents to competent authority: initial (same day), intermediate (72h), final (1 month)",
        "weight": 18,
        "sub_requirements": [
            "Initial notification within 4 hours (major) or same day",
            "Intermediate report within 72 hours",
            "Final report within 1 month",
            "Single EU reporting hub integration (when available)"
        ]
    },
    {
        "id": "DORA-P2-04",
        "pillar": DORAPillar.INCIDENT_REPORTING,
        "article": "20",
        "name_en": "Voluntary Notification",
        "name_de": "Freiwillige Meldung",
        "description_en": "Voluntary notification of significant cyber threats even if not classified as major incidents",
        "weight": 8,
        "sub_requirements": [
            "Process for voluntary threat notification",
            "Criteria for significant cyber threats",
            "Information sharing with authorities",
            "Feedback loop from competent authorities"
        ]
    },
    {
        "id": "DORA-P2-05",
        "pillar": DORAPillar.INCIDENT_REPORTING,
        "article": "21-23",
        "name_en": "Harmonised Reporting & Feedback",
        "name_de": "Harmonisierte Meldung & Rückmeldung",
        "description_en": "Implement harmonised reporting using RTS templates, receive feedback from authorities, and aggregate analysis",
        "weight": 7,
        "sub_requirements": [
            "Use of standardised reporting templates",
            "Process for receiving authority feedback",
            "Aggregated incident analysis",
            "Anonymised information sharing"
        ]
    },
    # Pillar 3: Digital Resilience Testing (Art. 24-27) - 4 requirements
    {
        "id": "DORA-P3-01",
        "pillar": DORAPillar.RESILIENCE_TESTING,
        "article": "24",
        "name_en": "Testing Programme",
        "name_de": "Testprogramm",
        "description_en": "Establish comprehensive digital operational resilience testing programme",
        "weight": 15,
        "sub_requirements": [
            "Risk-based testing programme established",
            "Annual testing of critical ICT systems",
            "Testing methodology documented",
            "Testing scope covers all critical functions"
        ]
    },
    {
        "id": "DORA-P3-02",
        "pillar": DORAPillar.RESILIENCE_TESTING,
        "article": "25",
        "name_en": "Testing of ICT Tools & Systems",
        "name_de": "Prüfung von IKT-Tools & Systemen",
        "description_en": "Perform vulnerability assessments, network security assessments, gap analyses, and scenario-based tests",
        "weight": 12,
        "sub_requirements": [
            "Vulnerability assessments performed",
            "Network security assessments",
            "Gap analyses conducted",
            "Scenario-based testing (business continuity)"
        ]
    },
    {
        "id": "DORA-P3-03",
        "pillar": DORAPillar.RESILIENCE_TESTING,
        "article": "26",
        "name_en": "Threat-Led Penetration Testing (TLPT)",
        "name_de": "Bedrohungsbasierte Penetrationstests (TLPT)",
        "description_en": "Perform TLPT at least every 3 years for significant financial entities using TIBER-EU framework",
        "weight": 18,
        "sub_requirements": [
            "TLPT performed every 3 years (significant entities)",
            "TIBER-EU or equivalent framework used",
            "Critical functions and live production tested",
            "ICT third-party providers included in scope"
        ]
    },
    {
        "id": "DORA-P3-04",
        "pillar": DORAPillar.RESILIENCE_TESTING,
        "article": "27",
        "name_en": "Tester Requirements",
        "name_de": "Anforderungen an Tester",
        "description_en": "Ensure testers meet requirements: accreditation, technical expertise, independence, and insurance",
        "weight": 10,
        "sub_requirements": [
            "Tester accreditation and certification",
            "Demonstrated technical expertise",
            "Independence of testers",
            "Professional liability insurance coverage"
        ]
    },
    # Pillar 4: ICT Third-Party Risk (Art. 28-44) - 9 requirements
    {
        "id": "DORA-P4-01",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "28",
        "name_en": "General Principles",
        "name_de": "Allgemeine Grundsätze",
        "description_en": "Manage ICT third-party risk as integral part of ICT risk management framework",
        "weight": 12,
        "sub_requirements": [
            "ICT third-party risk strategy defined",
            "Third-party risk integrated in framework",
            "Responsibility retained for compliance",
            "Proportionate to nature and scale of services"
        ]
    },
    {
        "id": "DORA-P4-02",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "29",
        "name_en": "Register of Information",
        "name_de": "Informationsregister",
        "description_en": "Maintain and update register of all ICT third-party service providers and contractual arrangements",
        "weight": 15,
        "sub_requirements": [
            "Complete register of ICT third-party providers",
            "All contractual arrangements documented",
            "Register regularly updated",
            "Register available for competent authorities"
        ]
    },
    {
        "id": "DORA-P4-03",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "30",
        "name_en": "Key Contractual Provisions",
        "name_de": "Wesentliche Vertragsbestimmungen",
        "description_en": "Include mandatory contractual provisions covering SLAs, audit rights, exit strategies, and more",
        "weight": 15,
        "sub_requirements": [
            "Service level agreements (SLAs) defined",
            "Audit and access rights included",
            "Exit strategies and termination clauses",
            "Data protection and security requirements"
        ]
    },
    {
        "id": "DORA-P4-04",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "31-32",
        "name_en": "Oversight Framework",
        "name_de": "Aufsichtsrahmen",
        "description_en": "Critical third-party providers (CTPPs) subject to EU oversight framework and lead overseer designation",
        "weight": 8,
        "sub_requirements": [
            "CTPP designation criteria understood",
            "Lead overseer requirements known",
            "Oversight recommendations implemented",
            "Cooperation with oversight activities"
        ]
    },
    {
        "id": "DORA-P4-05",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "33-35",
        "name_en": "Critical Functions Assessment",
        "name_de": "Bewertung kritischer Funktionen",
        "description_en": "Assess and regularly review which ICT services support critical or important functions",
        "weight": 10,
        "sub_requirements": [
            "Critical ICT services identified",
            "Criticality assessment methodology",
            "Regular review of criticality",
            "Impact analysis for critical services"
        ]
    },
    {
        "id": "DORA-P4-06",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "36-38",
        "name_en": "Concentration Risk",
        "name_de": "Konzentrationsrisiko",
        "description_en": "Identify, assess, and manage ICT concentration risk including for critical third-party providers",
        "weight": 10,
        "sub_requirements": [
            "Concentration risk identification",
            "Multi-vendor strategy where appropriate",
            "Dependency mapping for critical providers",
            "Contingency plans for provider failure"
        ]
    },
    {
        "id": "DORA-P4-07",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "39-41",
        "name_en": "Subcontracting",
        "name_de": "Unterauftragsvergabe",
        "description_en": "Manage risks from subcontracting chains and ensure visibility into sub-contractors",
        "weight": 8,
        "sub_requirements": [
            "Subcontracting approval process",
            "Visibility into subcontracting chains",
            "Subcontractor requirements in contracts",
            "Right to object to subcontracting"
        ]
    },
    {
        "id": "DORA-P4-08",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "42-43",
        "name_en": "Exit Strategies",
        "name_de": "Ausstiegsstrategien",
        "description_en": "Develop and maintain exit strategies for ICT third-party service providers",
        "weight": 10,
        "sub_requirements": [
            "Exit strategies documented",
            "Transition plans for critical services",
            "Data portability provisions",
            "Termination assistance clauses"
        ]
    },
    {
        "id": "DORA-P4-09",
        "pillar": DORAPillar.THIRD_PARTY_RISK,
        "article": "44",
        "name_en": "Supervisory Cooperation",
        "name_de": "Zusammenarbeit der Aufsichtsbehörden",
        "description_en": "Support supervisory cooperation and information exchange regarding ICT third-party providers",
        "weight": 7,
        "sub_requirements": [
            "Information sharing with supervisors",
            "Cooperation with supervisory requests",
            "Cross-border coordination supported",
            "Timely provision of required information"
        ]
    },
    # Pillar 5: Information Sharing (Art. 45) - 2 requirements
    {
        "id": "DORA-P5-01",
        "pillar": DORAPillar.INFORMATION_SHARING,
        "article": "45.1-2",
        "name_en": "Sharing Arrangements",
        "name_de": "Austauschvereinbarungen",
        "description_en": "Participate in cyber threat intelligence sharing arrangements within trusted communities",
        "weight": 30,
        "sub_requirements": [
            "Participation in threat intelligence sharing",
            "Trusted community memberships",
            "Information sharing agreements in place",
            "Contribute to sector-level intelligence"
        ]
    },
    {
        "id": "DORA-P5-02",
        "pillar": DORAPillar.INFORMATION_SHARING,
        "article": "45.3-4",
        "name_en": "Authority Notification",
        "name_de": "Behördenmeldung",
        "description_en": "Notify competent authorities of participation in information-sharing arrangements",
        "weight": 20,
        "sub_requirements": [
            "Authorities notified of sharing arrangements",
            "Changes to arrangements communicated",
            "Validation of shared information",
            "Protection of shared information"
        ]
    },
]


class DORAAssessment(Base):
    """DORA compliance assessment for a financial entity."""
    __tablename__ = "dora_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    # Assessment metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(DORAAssessmentStatus), default=DORAAssessmentStatus.DRAFT)

    # Wizard Step 1: Entity Scope
    entity_type = Column(Enum(DORAEntityType), nullable=True)
    company_size = Column(Enum(DORACompanySize), nullable=True)
    employee_count = Column(Integer)
    annual_balance_eur = Column(Float)  # Total balance sheet in millions
    is_ctpp = Column(Boolean, default=False)  # Critical Third-Party Provider
    operates_in_eu = Column(Boolean, default=True)
    eu_member_states = Column(JSON)  # List of country codes

    # Regulatory context
    supervised_by = Column(String(255))  # Primary competent authority
    group_level_assessment = Column(Boolean, default=False)  # Part of group assessment
    simplified_framework = Column(Boolean, default=False)  # Art. 16 microenterprise

    # Assessment Results
    overall_score = Column(Float, default=0.0)  # 0-100
    pillar_scores = Column(JSON)  # Dict[pillar, score]
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(String(36))

    # Relationships
    requirement_responses = relationship(
        "DORARequirementResponse",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_dora_assessment_tenant_name'),
    )


class DORARequirementResponse(Base):
    """Response to a DORA requirement in an assessment."""
    __tablename__ = "dora_requirement_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id = Column(
        String(36),
        ForeignKey("dora_assessments.id", ondelete="CASCADE"),
        nullable=False
    )

    # Requirement identification
    requirement_id = Column(String(20), nullable=False)  # DORA-P1-01 to DORA-P5-02
    pillar = Column(Enum(DORAPillar), nullable=False)

    # Response
    status = Column(Enum(DORARequirementStatus), default=DORARequirementStatus.NOT_EVALUATED)
    implementation_level = Column(Integer, default=0)  # 0-100 percentage

    # Sub-requirements responses (JSON array of {name, implemented: bool, notes})
    sub_requirements_status = Column(JSON)

    # Evidence and notes
    evidence = Column(Text)
    notes = Column(Text)
    gap_description = Column(Text)
    remediation_plan = Column(Text)
    priority = Column(Integer)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime)

    # Timestamps
    assessed_at = Column(DateTime)
    assessed_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("DORAAssessment", back_populates="requirement_responses")

    __table_args__ = (
        UniqueConstraint('assessment_id', 'requirement_id', name='uq_dora_requirement_assessment'),
    )
