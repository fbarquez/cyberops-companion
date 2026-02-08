"""
Onboarding Models and Configuration

This module defines the organization profile, industry sectors, and regulation
applicability rules for the onboarding wizard.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, JSON, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base


# =============================================================================
# ENUMS
# =============================================================================

class IndustrySector(str, Enum):
    """Industry sectors for regulation applicability."""
    # Financial Services (DORA, MaRisk, BAIT)
    BANKING = "banking"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    PAYMENT_SERVICES = "payment_services"
    CRYPTO_ASSETS = "crypto_assets"

    # Critical Infrastructure (KRITIS, NIS2)
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    HEALTHCARE = "healthcare"
    TRANSPORT = "transport"
    DIGITAL_INFRASTRUCTURE = "digital_infrastructure"
    ICT_SERVICES = "ict_services"
    SPACE = "space"
    POSTAL = "postal"
    WASTE_MANAGEMENT = "waste_management"
    CHEMICALS = "chemicals"
    MANUFACTURING = "manufacturing"

    # Automotive (TISAX)
    AUTOMOTIVE = "automotive"
    AUTOMOTIVE_SUPPLIER = "automotive_supplier"

    # Public Sector
    PUBLIC_ADMINISTRATION = "public_administration"

    # Other
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    TECHNOLOGY = "technology"
    OTHER = "other"


class CompanySize(str, Enum):
    """Company size categories (EU definition)."""
    MICRO = "micro"          # < 10 employees, < €2M turnover
    SMALL = "small"          # < 50 employees, < €10M turnover
    MEDIUM = "medium"        # < 250 employees, < €50M turnover
    LARGE = "large"          # >= 250 employees or >= €50M turnover


class CountryCode(str, Enum):
    """EU/EEA country codes."""
    DE = "DE"  # Germany
    AT = "AT"  # Austria
    CH = "CH"  # Switzerland
    FR = "FR"  # France
    NL = "NL"  # Netherlands
    BE = "BE"  # Belgium
    LU = "LU"  # Luxembourg
    IT = "IT"  # Italy
    ES = "ES"  # Spain
    PT = "PT"  # Portugal
    PL = "PL"  # Poland
    CZ = "CZ"  # Czech Republic
    SK = "SK"  # Slovakia
    HU = "HU"  # Hungary
    RO = "RO"  # Romania
    BG = "BG"  # Bulgaria
    GR = "GR"  # Greece
    SE = "SE"  # Sweden
    FI = "FI"  # Finland
    DK = "DK"  # Denmark
    IE = "IE"  # Ireland
    OTHER_EU = "OTHER_EU"
    NON_EU = "NON_EU"


class OnboardingStatus(str, Enum):
    """Onboarding completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# =============================================================================
# REGULATION APPLICABILITY RULES
# =============================================================================

REGULATION_RULES = {
    "nis2": {
        "name": "NIS2 Directive",
        "name_de": "NIS2-Richtlinie",
        "description": "EU Network and Information Security Directive",
        "applies_to_sectors": [
            IndustrySector.ENERGY,
            IndustrySector.TRANSPORT,
            IndustrySector.BANKING,
            IndustrySector.HEALTHCARE,
            IndustrySector.WATER,
            IndustrySector.DIGITAL_INFRASTRUCTURE,
            IndustrySector.ICT_SERVICES,
            IndustrySector.PUBLIC_ADMINISTRATION,
            IndustrySector.SPACE,
            IndustrySector.POSTAL,
            IndustrySector.WASTE_MANAGEMENT,
            IndustrySector.CHEMICALS,
            IndustrySector.FOOD,
            IndustrySector.MANUFACTURING,
        ],
        "min_size": CompanySize.MEDIUM,  # Generally for medium+ companies
        "requires_eu": True,
        "special_conditions": ["is_essential_service", "is_important_entity"],
        "deadline": "2024-10-17",
        "authority": "BSI (Germany)",
        "penalties": "Up to €10M or 2% of global turnover",
    },
    "dora": {
        "name": "DORA",
        "name_de": "DORA",
        "description": "Digital Operational Resilience Act for financial sector",
        "applies_to_sectors": [
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.INVESTMENT,
            IndustrySector.PAYMENT_SERVICES,
            IndustrySector.CRYPTO_ASSETS,
        ],
        "min_size": None,  # Applies to all sizes in financial sector
        "requires_eu": True,
        "special_conditions": ["is_bafin_regulated", "is_financial_entity"],
        "deadline": "2025-01-17",
        "authority": "BaFin (Germany)",
        "penalties": "Up to €10M or 5% of annual turnover",
    },
    "kritis": {
        "name": "KRITIS",
        "name_de": "KRITIS / IT-SiG 2.0",
        "description": "German Critical Infrastructure Protection",
        "applies_to_sectors": [
            IndustrySector.ENERGY,
            IndustrySector.WATER,
            IndustrySector.FOOD,
            IndustrySector.HEALTHCARE,
            IndustrySector.TRANSPORT,
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.DIGITAL_INFRASTRUCTURE,
            IndustrySector.ICT_SERVICES,
            IndustrySector.WASTE_MANAGEMENT,
        ],
        "min_size": None,  # Based on threshold values, not size
        "requires_country": [CountryCode.DE],
        "special_conditions": ["is_kritis_operator", "exceeds_kritis_threshold"],
        "deadline": None,  # Already in effect
        "authority": "BSI",
        "penalties": "Up to €20M",
    },
    "tisax": {
        "name": "TISAX",
        "name_de": "TISAX",
        "description": "Trusted Information Security Assessment Exchange (Automotive)",
        "applies_to_sectors": [
            IndustrySector.AUTOMOTIVE,
            IndustrySector.AUTOMOTIVE_SUPPLIER,
        ],
        "min_size": None,  # Required by OEMs
        "requires_eu": False,
        "special_conditions": ["supplies_to_oem", "handles_prototype_data"],
        "deadline": None,  # Contractual requirement
        "authority": "ENX Association",
        "penalties": "Loss of OEM contracts",
    },
    "gdpr": {
        "name": "GDPR",
        "name_de": "DSGVO",
        "description": "General Data Protection Regulation",
        "applies_to_sectors": "all",  # All sectors
        "min_size": None,  # All sizes
        "requires_eu": True,  # Or processes EU data
        "special_conditions": ["processes_personal_data"],
        "deadline": None,  # Already in effect
        "authority": "Data Protection Authorities",
        "penalties": "Up to €20M or 4% of global turnover",
    },
    "bait": {
        "name": "BAIT",
        "name_de": "BAIT",
        "description": "Banking Supervisory Requirements for IT",
        "applies_to_sectors": [IndustrySector.BANKING],
        "min_size": None,
        "requires_country": [CountryCode.DE],
        "special_conditions": ["is_bafin_regulated"],
        "deadline": None,
        "authority": "BaFin",
        "penalties": "Regulatory measures",
    },
    "marisk": {
        "name": "MaRisk",
        "name_de": "MaRisk",
        "description": "Minimum Requirements for Risk Management",
        "applies_to_sectors": [
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.INVESTMENT,
        ],
        "min_size": None,
        "requires_country": [CountryCode.DE],
        "special_conditions": ["is_bafin_regulated"],
        "deadline": None,
        "authority": "BaFin",
        "penalties": "Regulatory measures",
    },
}


# =============================================================================
# BASELINE FRAMEWORK RECOMMENDATIONS
# =============================================================================

BASELINE_RECOMMENDATIONS = {
    # Financial sector → ISO 27001 + DORA pillars
    "financial": {
        "sectors": [
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.INVESTMENT,
            IndustrySector.PAYMENT_SERVICES,
            IndustrySector.CRYPTO_ASSETS,
        ],
        "frameworks": [
            {"id": "iso27001", "name": "ISO 27001:2022", "priority": 1, "reason": "International standard, basis for all frameworks"},
            {"id": "dora", "name": "DORA Pillars", "priority": 2, "reason": "Mandatory for EU financial entities"},
        ],
        "controls_focus": ["ICT Risk Management", "Incident Reporting", "Third-Party Risk", "Resilience Testing"],
    },
    # Critical Infrastructure → BSI + ISO 27001
    "critical_infrastructure": {
        "sectors": [
            IndustrySector.ENERGY,
            IndustrySector.WATER,
            IndustrySector.HEALTHCARE,
            IndustrySector.TRANSPORT,
            IndustrySector.DIGITAL_INFRASTRUCTURE,
        ],
        "frameworks": [
            {"id": "bsi", "name": "BSI IT-Grundschutz", "priority": 1, "reason": "Required for KRITIS operators in Germany"},
            {"id": "iso27001", "name": "ISO 27001:2022", "priority": 2, "reason": "International certification"},
        ],
        "controls_focus": ["Availability", "Incident Response", "Crisis Management", "Business Continuity"],
    },
    # Automotive → TISAX + ISO 27001
    "automotive": {
        "sectors": [
            IndustrySector.AUTOMOTIVE,
            IndustrySector.AUTOMOTIVE_SUPPLIER,
        ],
        "frameworks": [
            {"id": "tisax", "name": "TISAX (VDA ISA)", "priority": 1, "reason": "Required by OEMs"},
            {"id": "iso27001", "name": "ISO 27001:2022", "priority": 2, "reason": "Foundation for TISAX"},
        ],
        "controls_focus": ["Prototype Protection", "Information Classification", "Supplier Security"],
    },
    # General → ISO 27001
    "general": {
        "sectors": "other",
        "frameworks": [
            {"id": "iso27001", "name": "ISO 27001:2022", "priority": 1, "reason": "Best practice standard"},
        ],
        "controls_focus": ["Risk Assessment", "Access Control", "Incident Management"],
    },
}


# =============================================================================
# DATABASE MODELS
# =============================================================================

class OrganizationProfile(Base):
    """Organization profile created during onboarding."""
    __tablename__ = "organization_profiles"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Basic Info
    organization_name = Column(String(255), nullable=False)
    industry_sector = Column(SQLEnum(IndustrySector), nullable=False)
    company_size = Column(SQLEnum(CompanySize), nullable=False)
    employee_count = Column(Integer, nullable=True)
    annual_revenue_eur = Column(Integer, nullable=True)  # In thousands

    # Location
    headquarters_country = Column(SQLEnum(CountryCode), nullable=False)
    operates_in_eu = Column(Boolean, default=True)
    eu_member_states = Column(JSON, default=list)  # List of country codes

    # Special Status
    is_kritis_operator = Column(Boolean, default=False)
    kritis_sector = Column(String(100), nullable=True)
    is_bafin_regulated = Column(Boolean, default=False)
    is_essential_service = Column(Boolean, default=False)  # NIS2 essential
    is_important_entity = Column(Boolean, default=False)   # NIS2 important
    supplies_to_oem = Column(Boolean, default=False)       # TISAX relevant

    # Detected Regulations
    applicable_regulations = Column(JSON, default=list)  # List of regulation IDs

    # Selected Baseline
    selected_frameworks = Column(JSON, default=list)  # List of framework IDs

    # Onboarding Status
    onboarding_status = Column(SQLEnum(OnboardingStatus), default=OnboardingStatus.NOT_STARTED)
    onboarding_completed_at = Column(DateTime, nullable=True)
    current_step = Column(Integer, default=1)

    # Compliance Plan
    compliance_plan = Column(JSON, nullable=True)  # Generated plan with controls, owners, deadlines

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<OrganizationProfile {self.organization_name} ({self.industry_sector})>"


class CompliancePlanItem(Base):
    """Individual item in the compliance plan."""
    __tablename__ = "compliance_plan_items"

    id = Column(String(36), primary_key=True)
    profile_id = Column(String(36), ForeignKey("organization_profiles.id"), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)

    # Item Details
    category = Column(String(100), nullable=False)  # e.g., "Policies", "Technical Controls"
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Source
    regulation_id = Column(String(50), nullable=True)  # e.g., "dora", "nis2"
    framework_id = Column(String(50), nullable=True)   # e.g., "iso27001", "bsi"
    control_ref = Column(String(50), nullable=True)    # e.g., "A.5.1", "ORP.1"

    # Assignment
    owner_role = Column(String(100), nullable=True)  # e.g., "CISO", "IT Manager"
    owner_id = Column(String(36), nullable=True)

    # Timeline
    priority = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime, nullable=True)
    estimated_effort_days = Column(Integer, nullable=True)

    # Status
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    completed_at = Column(DateTime, nullable=True)

    # Evidence
    evidence_required = Column(Boolean, default=True)
    evidence_type = Column(String(100), nullable=True)  # e.g., "Policy Document", "Scan Report"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_industry_display_name(sector: IndustrySector, language: str = "en") -> str:
    """Get display name for industry sector."""
    names = {
        IndustrySector.BANKING: {"en": "Banking & Credit Institutions", "de": "Banken & Kreditinstitute"},
        IndustrySector.INSURANCE: {"en": "Insurance", "de": "Versicherungen"},
        IndustrySector.INVESTMENT: {"en": "Investment & Asset Management", "de": "Investment & Vermögensverwaltung"},
        IndustrySector.PAYMENT_SERVICES: {"en": "Payment Services", "de": "Zahlungsdienste"},
        IndustrySector.CRYPTO_ASSETS: {"en": "Crypto-Asset Services", "de": "Krypto-Dienstleistungen"},
        IndustrySector.ENERGY: {"en": "Energy", "de": "Energie"},
        IndustrySector.WATER: {"en": "Water Supply", "de": "Wasserversorgung"},
        IndustrySector.FOOD: {"en": "Food Production & Distribution", "de": "Lebensmittelproduktion"},
        IndustrySector.HEALTHCARE: {"en": "Healthcare", "de": "Gesundheitswesen"},
        IndustrySector.TRANSPORT: {"en": "Transport & Logistics", "de": "Transport & Logistik"},
        IndustrySector.DIGITAL_INFRASTRUCTURE: {"en": "Digital Infrastructure", "de": "Digitale Infrastruktur"},
        IndustrySector.ICT_SERVICES: {"en": "ICT Services (B2B)", "de": "IKT-Dienste (B2B)"},
        IndustrySector.SPACE: {"en": "Space", "de": "Raumfahrt"},
        IndustrySector.POSTAL: {"en": "Postal & Courier", "de": "Post & Kurier"},
        IndustrySector.WASTE_MANAGEMENT: {"en": "Waste Management", "de": "Abfallwirtschaft"},
        IndustrySector.CHEMICALS: {"en": "Chemicals", "de": "Chemie"},
        IndustrySector.MANUFACTURING: {"en": "Manufacturing", "de": "Produktion"},
        IndustrySector.AUTOMOTIVE: {"en": "Automotive (OEM)", "de": "Automobilhersteller (OEM)"},
        IndustrySector.AUTOMOTIVE_SUPPLIER: {"en": "Automotive Supplier", "de": "Automobilzulieferer"},
        IndustrySector.PUBLIC_ADMINISTRATION: {"en": "Public Administration", "de": "Öffentliche Verwaltung"},
        IndustrySector.RETAIL: {"en": "Retail & E-Commerce", "de": "Einzelhandel & E-Commerce"},
        IndustrySector.PROFESSIONAL_SERVICES: {"en": "Professional Services", "de": "Beratung & Dienstleistungen"},
        IndustrySector.TECHNOLOGY: {"en": "Technology & Software", "de": "Technologie & Software"},
        IndustrySector.OTHER: {"en": "Other", "de": "Sonstige"},
    }
    return names.get(sector, {}).get(language, sector.value)


def get_size_display_name(size: CompanySize, language: str = "en") -> str:
    """Get display name for company size."""
    names = {
        CompanySize.MICRO: {"en": "Micro (<10 employees)", "de": "Kleinstunternehmen (<10 Mitarbeiter)"},
        CompanySize.SMALL: {"en": "Small (10-49 employees)", "de": "Klein (10-49 Mitarbeiter)"},
        CompanySize.MEDIUM: {"en": "Medium (50-249 employees)", "de": "Mittel (50-249 Mitarbeiter)"},
        CompanySize.LARGE: {"en": "Large (250+ employees)", "de": "Groß (250+ Mitarbeiter)"},
    }
    return names.get(size, {}).get(language, size.value)
