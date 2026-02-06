"""NIS2 Directive compliance models."""
import enum
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from src.db.database import Base


class NIS2Sector(str, enum.Enum):
    """NIS2 sectors from Annexes I and II."""
    # Annex I - Essential Entities
    ENERGY = "energy"
    TRANSPORT = "transport"
    BANKING = "banking"
    FINANCIAL_INFRASTRUCTURE = "financial_infrastructure"
    HEALTH = "health"
    DRINKING_WATER = "drinking_water"
    WASTE_WATER = "waste_water"
    DIGITAL_INFRASTRUCTURE = "digital_infrastructure"
    ICT_SERVICE_MANAGEMENT = "ict_service_management"
    PUBLIC_ADMINISTRATION = "public_administration"
    SPACE = "space"
    # Annex II - Important Entities
    POSTAL_COURIER = "postal_courier"
    WASTE_MANAGEMENT = "waste_management"
    CHEMICALS = "chemicals"
    FOOD = "food"
    MANUFACTURING = "manufacturing"
    DIGITAL_PROVIDERS = "digital_providers"
    RESEARCH = "research"


class NIS2EntityType(str, enum.Enum):
    """NIS2 entity classification."""
    ESSENTIAL = "essential"      # Anexo I - stricter requirements
    IMPORTANT = "important"      # Anexo II - lighter supervision
    OUT_OF_SCOPE = "out_of_scope"


class NIS2CompanySize(str, enum.Enum):
    """Company size thresholds for NIS2."""
    MICRO = "micro"          # <10 employees, <€2M
    SMALL = "small"          # <50 employees, <€10M
    MEDIUM = "medium"        # 50-249 employees, €10-50M
    LARGE = "large"          # 250+ employees, €50M+


class NIS2AssessmentStatus(str, enum.Enum):
    """Assessment progress status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NIS2MeasureStatus(str, enum.Enum):
    """Compliance status for each measure."""
    NOT_EVALUATED = "not_evaluated"
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NOT_APPLICABLE = "not_applicable"


# NIS2 Article 21 - 10 Security Measures
NIS2_SECURITY_MEASURES = [
    {
        "id": "NIS2-M01",
        "article": "21.2.a",
        "name_en": "Risk analysis and information system security policies",
        "name_de": "Risikoanalyse und Sicherheitskonzepte für Informationssysteme",
        "name_es": "Análisis de riesgos y políticas de seguridad de sistemas de información",
        "description_en": "Policies on risk analysis and information system security",
        "weight": 15,
        "sub_requirements": [
            "Risk assessment methodology",
            "Asset inventory and classification",
            "Security policy documentation",
            "Regular policy review process"
        ]
    },
    {
        "id": "NIS2-M02",
        "article": "21.2.b",
        "name_en": "Incident handling",
        "name_de": "Bewältigung von Sicherheitsvorfällen",
        "name_es": "Gestión de incidentes",
        "description_en": "Incident handling procedures and capabilities",
        "weight": 15,
        "sub_requirements": [
            "Incident detection capabilities",
            "Incident response procedures",
            "Incident reporting to authorities (24h/72h)",
            "Post-incident analysis"
        ]
    },
    {
        "id": "NIS2-M03",
        "article": "21.2.c",
        "name_en": "Business continuity and crisis management",
        "name_de": "Aufrechterhaltung des Betriebs und Krisenmanagement",
        "name_es": "Continuidad del negocio y gestión de crisis",
        "description_en": "Business continuity, backup management, disaster recovery, crisis management",
        "weight": 12,
        "sub_requirements": [
            "Business continuity plan",
            "Backup and recovery procedures",
            "Disaster recovery plan",
            "Crisis management procedures"
        ]
    },
    {
        "id": "NIS2-M04",
        "article": "21.2.d",
        "name_en": "Supply chain security",
        "name_de": "Sicherheit der Lieferkette",
        "name_es": "Seguridad de la cadena de suministro",
        "description_en": "Supply chain security including security-related aspects of relationships with suppliers",
        "weight": 10,
        "sub_requirements": [
            "Supplier security assessment",
            "Contractual security requirements",
            "Supplier monitoring",
            "Third-party risk management"
        ]
    },
    {
        "id": "NIS2-M05",
        "article": "21.2.e",
        "name_en": "Security in acquisition, development and maintenance",
        "name_de": "Sicherheit bei Erwerb, Entwicklung und Wartung",
        "name_es": "Seguridad en adquisición, desarrollo y mantenimiento",
        "description_en": "Security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure",
        "weight": 10,
        "sub_requirements": [
            "Secure development lifecycle",
            "Vulnerability management",
            "Patch management",
            "Security testing procedures"
        ]
    },
    {
        "id": "NIS2-M06",
        "article": "21.2.f",
        "name_en": "Effectiveness assessment",
        "name_de": "Bewertung der Wirksamkeit",
        "name_es": "Evaluación de la efectividad",
        "description_en": "Policies and procedures to assess the effectiveness of cybersecurity risk-management measures",
        "weight": 8,
        "sub_requirements": [
            "Security metrics and KPIs",
            "Regular security assessments",
            "Penetration testing",
            "Audit procedures"
        ]
    },
    {
        "id": "NIS2-M07",
        "article": "21.2.g",
        "name_en": "Cyber hygiene and training",
        "name_de": "Cyberhygiene und Schulungen",
        "name_es": "Ciberhigiene y formación",
        "description_en": "Basic cyber hygiene practices and cybersecurity training",
        "weight": 8,
        "sub_requirements": [
            "Security awareness program",
            "Regular training for all staff",
            "Specialized training for IT/security staff",
            "Phishing simulations"
        ]
    },
    {
        "id": "NIS2-M08",
        "article": "21.2.h",
        "name_en": "Cryptography and encryption",
        "name_de": "Kryptografie und Verschlüsselung",
        "name_es": "Criptografía y cifrado",
        "description_en": "Policies and procedures regarding the use of cryptography and, where appropriate, encryption",
        "weight": 8,
        "sub_requirements": [
            "Encryption policy",
            "Key management procedures",
            "Data-at-rest encryption",
            "Data-in-transit encryption"
        ]
    },
    {
        "id": "NIS2-M09",
        "article": "21.2.i",
        "name_en": "HR security and access control",
        "name_de": "Personalsicherheit und Zugriffskontrolle",
        "name_es": "Seguridad de RRHH y control de acceso",
        "description_en": "Human resources security, access control policies and asset management",
        "weight": 7,
        "sub_requirements": [
            "Background checks",
            "Access control policy",
            "Privileged access management",
            "Asset management procedures"
        ]
    },
    {
        "id": "NIS2-M10",
        "article": "21.2.j",
        "name_en": "Multi-factor authentication and secure communications",
        "name_de": "Multi-Faktor-Authentifizierung und sichere Kommunikation",
        "name_es": "Autenticación multifactor y comunicaciones seguras",
        "description_en": "Use of multi-factor authentication, secured voice, video and text communications, and secured emergency communication systems",
        "weight": 7,
        "sub_requirements": [
            "MFA implementation",
            "Secure communication channels",
            "Emergency communication systems",
            "Authentication policies"
        ]
    },
]

# Sectors classification
ESSENTIAL_SECTORS = [
    NIS2Sector.ENERGY,
    NIS2Sector.TRANSPORT,
    NIS2Sector.BANKING,
    NIS2Sector.FINANCIAL_INFRASTRUCTURE,
    NIS2Sector.HEALTH,
    NIS2Sector.DRINKING_WATER,
    NIS2Sector.WASTE_WATER,
    NIS2Sector.DIGITAL_INFRASTRUCTURE,
    NIS2Sector.ICT_SERVICE_MANAGEMENT,
    NIS2Sector.PUBLIC_ADMINISTRATION,
    NIS2Sector.SPACE,
]

IMPORTANT_SECTORS = [
    NIS2Sector.POSTAL_COURIER,
    NIS2Sector.WASTE_MANAGEMENT,
    NIS2Sector.CHEMICALS,
    NIS2Sector.FOOD,
    NIS2Sector.MANUFACTURING,
    NIS2Sector.DIGITAL_PROVIDERS,
    NIS2Sector.RESEARCH,
]

# Sector metadata for UI
SECTOR_METADATA = {
    NIS2Sector.ENERGY: {
        "name_en": "Energy",
        "name_de": "Energie",
        "name_es": "Energía",
        "icon": "zap",
        "subsectors": ["Electricity", "Oil", "Gas", "Hydrogen", "District heating/cooling"]
    },
    NIS2Sector.TRANSPORT: {
        "name_en": "Transport",
        "name_de": "Verkehr",
        "name_es": "Transporte",
        "icon": "truck",
        "subsectors": ["Air", "Rail", "Water", "Road"]
    },
    NIS2Sector.BANKING: {
        "name_en": "Banking",
        "name_de": "Bankwesen",
        "name_es": "Banca",
        "icon": "landmark",
        "subsectors": ["Credit institutions"]
    },
    NIS2Sector.FINANCIAL_INFRASTRUCTURE: {
        "name_en": "Financial Market Infrastructure",
        "name_de": "Finanzmarktinfrastruktur",
        "name_es": "Infraestructura de mercados financieros",
        "icon": "trending-up",
        "subsectors": ["Trading venues", "Central counterparties"]
    },
    NIS2Sector.HEALTH: {
        "name_en": "Health",
        "name_de": "Gesundheitswesen",
        "name_es": "Salud",
        "icon": "heart-pulse",
        "subsectors": ["Healthcare providers", "EU reference laboratories", "Pharma R&D", "Medical devices"]
    },
    NIS2Sector.DRINKING_WATER: {
        "name_en": "Drinking Water",
        "name_de": "Trinkwasser",
        "name_es": "Agua potable",
        "icon": "droplet",
        "subsectors": ["Water supply", "Water distribution"]
    },
    NIS2Sector.WASTE_WATER: {
        "name_en": "Waste Water",
        "name_de": "Abwasser",
        "name_es": "Aguas residuales",
        "icon": "droplets",
        "subsectors": ["Waste water collection", "Treatment", "Disposal"]
    },
    NIS2Sector.DIGITAL_INFRASTRUCTURE: {
        "name_en": "Digital Infrastructure",
        "name_de": "Digitale Infrastruktur",
        "name_es": "Infraestructura digital",
        "icon": "server",
        "subsectors": ["IXPs", "DNS providers", "TLD registries", "Cloud computing", "Data centers", "CDNs", "Trust services", "Electronic communications"]
    },
    NIS2Sector.ICT_SERVICE_MANAGEMENT: {
        "name_en": "ICT Service Management (B2B)",
        "name_de": "IKT-Dienstleistungsmanagement (B2B)",
        "name_es": "Gestión de servicios TIC (B2B)",
        "icon": "settings",
        "subsectors": ["Managed service providers", "Managed security service providers"]
    },
    NIS2Sector.PUBLIC_ADMINISTRATION: {
        "name_en": "Public Administration",
        "name_de": "Öffentliche Verwaltung",
        "name_es": "Administración pública",
        "icon": "building-2",
        "subsectors": ["Central government", "Regional government"]
    },
    NIS2Sector.SPACE: {
        "name_en": "Space",
        "name_de": "Weltraum",
        "name_es": "Espacio",
        "icon": "rocket",
        "subsectors": ["Ground-based infrastructure operators"]
    },
    NIS2Sector.POSTAL_COURIER: {
        "name_en": "Postal and Courier Services",
        "name_de": "Post- und Kurierdienste",
        "name_es": "Servicios postales y de mensajería",
        "icon": "mail",
        "subsectors": ["Postal services", "Courier services"]
    },
    NIS2Sector.WASTE_MANAGEMENT: {
        "name_en": "Waste Management",
        "name_de": "Abfallbewirtschaftung",
        "name_es": "Gestión de residuos",
        "icon": "trash-2",
        "subsectors": ["Waste collection", "Treatment", "Recovery", "Disposal"]
    },
    NIS2Sector.CHEMICALS: {
        "name_en": "Chemicals",
        "name_de": "Chemikalien",
        "name_es": "Químicos",
        "icon": "flask-conical",
        "subsectors": ["Production", "Distribution", "Storage"]
    },
    NIS2Sector.FOOD: {
        "name_en": "Food",
        "name_de": "Lebensmittel",
        "name_es": "Alimentación",
        "icon": "utensils",
        "subsectors": ["Production", "Processing", "Distribution", "Wholesale"]
    },
    NIS2Sector.MANUFACTURING: {
        "name_en": "Manufacturing",
        "name_de": "Verarbeitendes Gewerbe",
        "name_es": "Manufactura",
        "icon": "factory",
        "subsectors": ["Medical devices", "Computers/electronics", "Electrical equipment", "Machinery", "Motor vehicles", "Transport equipment"]
    },
    NIS2Sector.DIGITAL_PROVIDERS: {
        "name_en": "Digital Providers",
        "name_de": "Digitale Anbieter",
        "name_es": "Proveedores digitales",
        "icon": "globe",
        "subsectors": ["Online marketplaces", "Search engines", "Social networks"]
    },
    NIS2Sector.RESEARCH: {
        "name_en": "Research",
        "name_de": "Forschung",
        "name_es": "Investigación",
        "icon": "microscope",
        "subsectors": ["Research organizations"]
    },
}


class NIS2Assessment(Base):
    """NIS2 compliance assessment for an organization."""
    __tablename__ = "nis2_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    # Assessment metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(NIS2AssessmentStatus), default=NIS2AssessmentStatus.DRAFT)

    # Wizard Step 1: Organization Profile
    sector = Column(Enum(NIS2Sector), nullable=True)
    subsector = Column(String(100))
    company_size = Column(Enum(NIS2CompanySize), nullable=True)
    employee_count = Column(Integer)
    annual_turnover_eur = Column(Float)  # in millions
    operates_in_eu = Column(Boolean, default=True)
    eu_countries = Column(JSON)  # List of country codes

    # Wizard Step 2: Classification Result
    entity_type = Column(Enum(NIS2EntityType), nullable=True)
    classification_reason = Column(Text)

    # Wizard Step 3-5: Assessment Results
    overall_score = Column(Float, default=0.0)  # 0-100
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(String(36))

    # Relationships
    measure_responses = relationship("NIS2MeasureResponse", back_populates="assessment", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_nis2_assessment_tenant_name'),
    )


class NIS2MeasureResponse(Base):
    """Response to a NIS2 security measure in an assessment."""
    __tablename__ = "nis2_measure_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id = Column(String(36), ForeignKey("nis2_assessments.id", ondelete="CASCADE"), nullable=False)

    # Measure identification
    measure_id = Column(String(20), nullable=False)  # NIS2-M01 to NIS2-M10

    # Response
    status = Column(Enum(NIS2MeasureStatus), default=NIS2MeasureStatus.NOT_EVALUATED)
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
    assessment = relationship("NIS2Assessment", back_populates="measure_responses")

    __table_args__ = (
        UniqueConstraint('assessment_id', 'measure_id', name='uq_nis2_measure_assessment'),
    )
