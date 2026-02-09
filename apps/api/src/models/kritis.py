"""
KRITIS (Kritische Infrastrukturen) Compliance Models

Models for German Critical Infrastructure Protection compliance.
Based on BSI-Gesetz (BSI Act) and BSI-KritisV regulation.
"""

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from src.db.database import Base


# =============================================================================
# Enums
# =============================================================================

class KRITISSector(str, enum.Enum):
    """KRITIS sectors according to BSI-KritisV."""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    IT_TELECOM = "it_telecom"
    HEALTH = "health"
    FINANCE = "finance"
    TRANSPORT = "transport"
    WASTE = "waste"


class KRITISCompanySize(str, enum.Enum):
    """Company size classification."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class KRITISAssessmentStatus(str, enum.Enum):
    """Assessment workflow status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class KRITISRequirementStatus(str, enum.Enum):
    """Requirement implementation status."""
    NOT_EVALUATED = "not_evaluated"
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NOT_APPLICABLE = "not_applicable"


# =============================================================================
# Reference Data
# =============================================================================

KRITIS_SECTORS = {
    KRITISSector.ENERGY: {
        "name_en": "Energy",
        "name_de": "Energie",
        "icon": "Zap",
        "description_en": "Electricity, gas, fuel supply",
        "description_de": "Strom-, Gas- und Kraftstoffversorgung",
        "threshold_info": "500,000+ supplied customers or 104 MW installed capacity",
        "subsectors": ["electricity", "gas", "fuel", "district_heating"],
    },
    KRITISSector.WATER: {
        "name_en": "Water",
        "name_de": "Wasser",
        "icon": "Droplets",
        "description_en": "Drinking water supply, wastewater disposal",
        "description_de": "Trinkwasserversorgung, Abwasserentsorgung",
        "threshold_info": "500,000+ supplied population",
        "subsectors": ["drinking_water", "wastewater"],
    },
    KRITISSector.FOOD: {
        "name_en": "Food",
        "name_de": "Ernährung",
        "icon": "Utensils",
        "description_en": "Food production and supply",
        "description_de": "Lebensmittelproduktion und -versorgung",
        "threshold_info": "434,500+ tons/year production",
        "subsectors": ["food_production", "food_retail"],
    },
    KRITISSector.IT_TELECOM: {
        "name_en": "IT and Telecommunications",
        "name_de": "Informationstechnik und Telekommunikation",
        "icon": "Server",
        "description_en": "IT infrastructure, telecommunications networks",
        "description_de": "IT-Infrastruktur, Telekommunikationsnetze",
        "threshold_info": "100,000+ subscribers or critical infrastructure service",
        "subsectors": ["telecommunications", "data_centers", "dns", "ix"],
    },
    KRITISSector.HEALTH: {
        "name_en": "Health",
        "name_de": "Gesundheit",
        "icon": "Heart",
        "description_en": "Hospitals, laboratories, pharmaceuticals",
        "description_de": "Krankenhäuser, Labore, Pharmaindustrie",
        "threshold_info": "30,000+ inpatient cases/year",
        "subsectors": ["hospitals", "laboratories", "pharmaceuticals"],
    },
    KRITISSector.FINANCE: {
        "name_en": "Finance and Insurance",
        "name_de": "Finanz- und Versicherungswesen",
        "icon": "Landmark",
        "description_en": "Banks, insurance, financial infrastructure",
        "description_de": "Banken, Versicherungen, Finanzinfrastruktur",
        "threshold_info": "Various thresholds by subsector",
        "subsectors": ["banking", "insurance", "stock_exchange", "payment_services"],
    },
    KRITISSector.TRANSPORT: {
        "name_en": "Transport and Traffic",
        "name_de": "Transport und Verkehr",
        "icon": "Truck",
        "description_en": "Air, rail, water, road transport",
        "description_de": "Luft-, Schienen-, Wasser- und Straßenverkehr",
        "threshold_info": "Various thresholds by transport mode",
        "subsectors": ["aviation", "rail", "maritime", "road", "logistics"],
    },
    KRITISSector.WASTE: {
        "name_en": "Municipal Waste Management",
        "name_de": "Siedlungsabfallentsorgung",
        "icon": "Trash2",
        "description_en": "Waste collection and disposal",
        "description_de": "Abfallsammlung und -entsorgung",
        "threshold_info": "500,000+ served population",
        "subsectors": ["waste_collection", "waste_disposal", "recycling"],
    },
}

# KRITIS Requirements based on BSI-Gesetz §8a
KRITIS_REQUIREMENTS = [
    # 1. Governance & Organization
    {
        "id": "KRITIS-01",
        "category": "governance",
        "article": "§8a Abs. 1",
        "name_en": "Information Security Management System (ISMS)",
        "name_de": "Informationssicherheits-Managementsystem (ISMS)",
        "description_en": "Implement and maintain an ISMS appropriate to the criticality of the infrastructure",
        "description_de": "Implementierung und Pflege eines ISMS entsprechend der Kritikalität der Infrastruktur",
        "weight": 15,
        "sub_requirements": [
            "Documented ISMS policies and procedures",
            "Risk management process",
            "Management commitment and resources",
            "Continuous improvement process",
        ],
    },
    {
        "id": "KRITIS-02",
        "category": "governance",
        "article": "§8a Abs. 1",
        "name_en": "Roles and Responsibilities",
        "name_de": "Rollen und Verantwortlichkeiten",
        "description_en": "Define clear roles and responsibilities for IT security",
        "description_de": "Definition klarer Rollen und Verantwortlichkeiten für IT-Sicherheit",
        "weight": 10,
        "sub_requirements": [
            "IT Security Officer (CISO) appointed",
            "Security team structure defined",
            "Escalation paths established",
            "Deputy roles assigned",
        ],
    },
    # 2. Risk Management
    {
        "id": "KRITIS-03",
        "category": "risk_management",
        "article": "§8a Abs. 1",
        "name_en": "Risk Assessment",
        "name_de": "Risikobewertung",
        "description_en": "Regular risk assessments for critical IT systems and processes",
        "description_de": "Regelmäßige Risikobewertungen für kritische IT-Systeme und -Prozesse",
        "weight": 15,
        "sub_requirements": [
            "Annual risk assessment conducted",
            "Critical assets identified",
            "Threat landscape analyzed",
            "Risk treatment plans documented",
        ],
    },
    {
        "id": "KRITIS-04",
        "category": "risk_management",
        "article": "§8a Abs. 1",
        "name_en": "Asset Management",
        "name_de": "Asset-Management",
        "description_en": "Complete inventory and classification of critical assets",
        "description_de": "Vollständige Inventarisierung und Klassifizierung kritischer Assets",
        "weight": 10,
        "sub_requirements": [
            "Asset inventory maintained",
            "Assets classified by criticality",
            "Ownership assigned",
            "Regular asset reviews conducted",
        ],
    },
    # 3. Technical Security Measures
    {
        "id": "KRITIS-05",
        "category": "technical",
        "article": "§8a Abs. 1",
        "name_en": "Network Security",
        "name_de": "Netzwerksicherheit",
        "description_en": "Implement network segmentation and security controls",
        "description_de": "Implementierung von Netzwerksegmentierung und Sicherheitskontrollen",
        "weight": 12,
        "sub_requirements": [
            "Network segmentation implemented",
            "Firewalls and IDS/IPS deployed",
            "Secure remote access (VPN)",
            "Network monitoring active",
        ],
    },
    {
        "id": "KRITIS-06",
        "category": "technical",
        "article": "§8a Abs. 1",
        "name_en": "Access Control",
        "name_de": "Zugriffskontrolle",
        "description_en": "Implement identity and access management",
        "description_de": "Implementierung von Identitäts- und Zugriffsmanagement",
        "weight": 12,
        "sub_requirements": [
            "Identity management system in place",
            "Role-based access control (RBAC)",
            "Multi-factor authentication for critical systems",
            "Regular access reviews",
            "Privileged access management",
        ],
    },
    {
        "id": "KRITIS-07",
        "category": "technical",
        "article": "§8a Abs. 1",
        "name_en": "Cryptography",
        "name_de": "Kryptographie",
        "description_en": "Use encryption for data protection",
        "description_de": "Einsatz von Verschlüsselung zum Datenschutz",
        "weight": 8,
        "sub_requirements": [
            "Encryption for data at rest",
            "Encryption for data in transit",
            "Key management procedures",
            "Use of approved algorithms",
        ],
    },
    {
        "id": "KRITIS-08",
        "category": "technical",
        "article": "§8a Abs. 1",
        "name_en": "Vulnerability Management",
        "name_de": "Schwachstellenmanagement",
        "description_en": "Systematic identification and remediation of vulnerabilities",
        "description_de": "Systematische Identifikation und Behebung von Schwachstellen",
        "weight": 10,
        "sub_requirements": [
            "Regular vulnerability scans",
            "Patch management process",
            "Penetration testing (annual)",
            "Vulnerability tracking and remediation",
        ],
    },
    {
        "id": "KRITIS-09",
        "category": "technical",
        "article": "§8a Abs. 1",
        "name_en": "Security Monitoring",
        "name_de": "Sicherheitsüberwachung",
        "description_en": "Continuous monitoring and logging of security events",
        "description_de": "Kontinuierliche Überwachung und Protokollierung von Sicherheitsereignissen",
        "weight": 10,
        "sub_requirements": [
            "SIEM system implemented",
            "24/7 monitoring capability",
            "Log retention policy (min. 6 months)",
            "Alerting and escalation procedures",
        ],
    },
    # 4. Incident Management
    {
        "id": "KRITIS-10",
        "category": "incident_management",
        "article": "§8b",
        "name_en": "Incident Detection",
        "name_de": "Vorfallserkennung",
        "description_en": "Capability to detect security incidents",
        "description_de": "Fähigkeit zur Erkennung von Sicherheitsvorfällen",
        "weight": 10,
        "sub_requirements": [
            "Incident detection mechanisms in place",
            "Security Operations Center (SOC) or equivalent",
            "Automated alerting configured",
            "Threat intelligence integration",
        ],
    },
    {
        "id": "KRITIS-11",
        "category": "incident_management",
        "article": "§8b",
        "name_en": "Incident Response",
        "name_de": "Vorfallsbehandlung",
        "description_en": "Documented incident response procedures",
        "description_de": "Dokumentierte Verfahren zur Vorfallsbehandlung",
        "weight": 12,
        "sub_requirements": [
            "Incident response plan documented",
            "Incident response team established",
            "Response procedures tested annually",
            "Forensic capability available",
        ],
    },
    {
        "id": "KRITIS-12",
        "category": "incident_management",
        "article": "§8b Abs. 4",
        "name_en": "BSI Incident Reporting",
        "name_de": "Meldung an das BSI",
        "description_en": "Process for reporting significant incidents to BSI",
        "description_de": "Prozess zur Meldung erheblicher Vorfälle an das BSI",
        "weight": 15,
        "sub_requirements": [
            "BSI reporting process documented",
            "Reporting criteria defined",
            "24h initial notification capability",
            "Follow-up reporting procedures",
            "Contact with BSI established",
        ],
    },
    # 5. Business Continuity
    {
        "id": "KRITIS-13",
        "category": "business_continuity",
        "article": "§8a Abs. 1",
        "name_en": "Business Continuity Planning",
        "name_de": "Notfallplanung",
        "description_en": "Business continuity and disaster recovery plans",
        "description_de": "Business-Continuity- und Disaster-Recovery-Pläne",
        "weight": 12,
        "sub_requirements": [
            "Business impact analysis conducted",
            "Recovery time objectives defined",
            "Backup systems and procedures",
            "Disaster recovery site (if applicable)",
        ],
    },
    {
        "id": "KRITIS-14",
        "category": "business_continuity",
        "article": "§8a Abs. 1",
        "name_en": "BCM Testing",
        "name_de": "BCM-Tests",
        "description_en": "Regular testing of continuity and recovery plans",
        "description_de": "Regelmäßige Tests der Kontinuitäts- und Wiederherstellungspläne",
        "weight": 8,
        "sub_requirements": [
            "Annual BCM exercises conducted",
            "Recovery procedures tested",
            "Lessons learned documented",
            "Plans updated after tests",
        ],
    },
    # 6. Supply Chain Security
    {
        "id": "KRITIS-15",
        "category": "supply_chain",
        "article": "§8a Abs. 1",
        "name_en": "Supplier Security",
        "name_de": "Lieferantensicherheit",
        "description_en": "Security requirements for suppliers and service providers",
        "description_de": "Sicherheitsanforderungen an Lieferanten und Dienstleister",
        "weight": 8,
        "sub_requirements": [
            "Supplier security assessment process",
            "Security clauses in contracts",
            "Regular supplier reviews",
            "Critical supplier monitoring",
        ],
    },
    # 7. Personnel Security
    {
        "id": "KRITIS-16",
        "category": "personnel",
        "article": "§8a Abs. 1",
        "name_en": "Security Awareness",
        "name_de": "Sicherheitsbewusstsein",
        "description_en": "Security awareness training for all employees",
        "description_de": "Sicherheitsbewusstseinsschulung für alle Mitarbeiter",
        "weight": 8,
        "sub_requirements": [
            "Annual security awareness training",
            "Role-specific training programs",
            "Phishing awareness exercises",
            "Training records maintained",
        ],
    },
    {
        "id": "KRITIS-17",
        "category": "personnel",
        "article": "§8a Abs. 1",
        "name_en": "Personnel Vetting",
        "name_de": "Personalüberprüfung",
        "description_en": "Background checks for personnel in critical roles",
        "description_de": "Hintergrundprüfungen für Personal in kritischen Rollen",
        "weight": 6,
        "sub_requirements": [
            "Background check policy defined",
            "Checks conducted for critical roles",
            "NDA requirements",
            "Termination procedures",
        ],
    },
    # 8. Physical Security
    {
        "id": "KRITIS-18",
        "category": "physical",
        "article": "§8a Abs. 1",
        "name_en": "Physical Access Control",
        "name_de": "Physische Zugangskontrolle",
        "description_en": "Physical security for critical infrastructure locations",
        "description_de": "Physische Sicherheit für kritische Infrastrukturstandorte",
        "weight": 8,
        "sub_requirements": [
            "Perimeter security measures",
            "Access control systems",
            "Visitor management",
            "CCTV monitoring",
        ],
    },
    # 9. Compliance & Audit
    {
        "id": "KRITIS-19",
        "category": "compliance",
        "article": "§8a Abs. 3",
        "name_en": "Compliance Audit (§8a Nachweis)",
        "name_de": "Nachweiserbringung (§8a Nachweis)",
        "description_en": "Biennial compliance proof to BSI",
        "description_de": "Zweijährlicher Nachweis gegenüber dem BSI",
        "weight": 15,
        "sub_requirements": [
            "Audit conducted by qualified auditor",
            "Audit scope covers all KRITIS requirements",
            "Findings documented and addressed",
            "Proof submitted to BSI on time",
        ],
    },
    {
        "id": "KRITIS-20",
        "category": "compliance",
        "article": "§8a Abs. 1",
        "name_en": "Documentation",
        "name_de": "Dokumentation",
        "description_en": "Complete security documentation maintained",
        "description_de": "Vollständige Sicherheitsdokumentation geführt",
        "weight": 6,
        "sub_requirements": [
            "Security policies documented",
            "Procedures and guidelines available",
            "Evidence collection process",
            "Documentation regularly reviewed",
        ],
    },
]

# Category metadata
KRITIS_CATEGORIES = {
    "governance": {
        "name_en": "Governance & Organization",
        "name_de": "Governance & Organisation",
        "weight": 25,
    },
    "risk_management": {
        "name_en": "Risk Management",
        "name_de": "Risikomanagement",
        "weight": 15,
    },
    "technical": {
        "name_en": "Technical Security Measures",
        "name_de": "Technische Sicherheitsmaßnahmen",
        "weight": 25,
    },
    "incident_management": {
        "name_en": "Incident Management",
        "name_de": "Vorfallsmanagement",
        "weight": 15,
    },
    "business_continuity": {
        "name_en": "Business Continuity",
        "name_de": "Business Continuity",
        "weight": 10,
    },
    "supply_chain": {
        "name_en": "Supply Chain Security",
        "name_de": "Lieferkettensicherheit",
        "weight": 5,
    },
    "personnel": {
        "name_en": "Personnel Security",
        "name_de": "Personalsicherheit",
        "weight": 5,
    },
    "physical": {
        "name_en": "Physical Security",
        "name_de": "Physische Sicherheit",
        "weight": 5,
    },
    "compliance": {
        "name_en": "Compliance & Audit",
        "name_de": "Compliance & Audit",
        "weight": 10,
    },
}


# =============================================================================
# Database Models
# =============================================================================

class KRITISAssessment(Base):
    """KRITIS compliance assessment."""
    __tablename__ = "kritis_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(KRITISAssessmentStatus),
        default=KRITISAssessmentStatus.DRAFT,
        nullable=False,
    )

    # Scope
    sector = Column(Enum(KRITISSector), nullable=True)
    subsector = Column(String(100), nullable=True)
    company_size = Column(Enum(KRITISCompanySize), nullable=True)
    employee_count = Column(Integer, nullable=True)
    annual_revenue_eur = Column(Float, nullable=True)

    # Location
    operates_in_germany = Column(Boolean, default=True)
    german_states = Column(JSON, nullable=True)  # List of state codes

    # Registration
    bsi_registered = Column(Boolean, default=False)
    bsi_registration_date = Column(DateTime, nullable=True)
    bsi_contact_established = Column(Boolean, default=False)
    last_audit_date = Column(DateTime, nullable=True)
    next_audit_due = Column(DateTime, nullable=True)

    # Scores
    overall_score = Column(Float, default=0)
    category_scores = Column(JSON, nullable=True)  # Dict[category, score]
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), nullable=True)

    # Relationships
    requirement_responses = relationship(
        "KRITISRequirementResponse",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class KRITISRequirementResponse(Base):
    """Response to a KRITIS requirement within an assessment."""
    __tablename__ = "kritis_requirement_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id = Column(
        String(36),
        ForeignKey("kritis_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)

    # Status
    status = Column(
        Enum(KRITISRequirementStatus),
        default=KRITISRequirementStatus.NOT_EVALUATED,
        nullable=False,
    )
    implementation_level = Column(Integer, default=0)  # 0-100%

    # Sub-requirements tracking
    sub_requirements_status = Column(JSON, nullable=True)  # List of booleans

    # Evidence and notes
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    gap_description = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)

    # Priority and planning
    priority = Column(Integer, nullable=True)  # 1-4 (1=Critical, 4=Low)
    due_date = Column(DateTime, nullable=True)

    # Audit trail
    assessed_at = Column(DateTime, nullable=True)
    assessed_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("KRITISAssessment", back_populates="requirement_responses")
