"""
NIS2 Directive Data Models

Pydantic models for NIS2 (Network and Information Security Directive 2)
compliance tracking and notification management.

NIS2 applies to essential and important entities across the EU.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class NIS2EntityType(str, Enum):
    """Entity classification under NIS2."""
    ESSENTIAL = "essential"    # Annex I entities - stricter requirements
    IMPORTANT = "important"    # Annex II entities - standard requirements


class NIS2Sector(str, Enum):
    """Sectors covered by NIS2 directive."""
    # Annex I - Essential entities
    ENERGY = "energy"
    TRANSPORT = "transport"
    BANKING = "banking"
    FINANCIAL_MARKET = "financial_market"
    HEALTH = "health"
    DRINKING_WATER = "drinking_water"
    WASTE_WATER = "waste_water"
    DIGITAL_INFRASTRUCTURE = "digital_infrastructure"
    ICT_SERVICE_MANAGEMENT = "ict_service_management"
    PUBLIC_ADMINISTRATION = "public_administration"
    SPACE = "space"

    # Annex II - Important entities
    POSTAL = "postal"
    WASTE_MANAGEMENT = "waste_management"
    CHEMICALS = "chemicals"
    FOOD = "food"
    MANUFACTURING = "manufacturing"
    DIGITAL_PROVIDERS = "digital_providers"
    RESEARCH = "research"


class NIS2IncidentSeverity(str, Enum):
    """Incident severity classification for NIS2 reporting."""
    SIGNIFICANT = "significant"  # Requires mandatory reporting
    SUBSTANTIAL = "substantial"  # May require reporting based on impact
    MINOR = "minor"             # Internal handling, no mandatory reporting


class NIS2NotificationStatus(str, Enum):
    """Status of a NIS2 notification."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class NIS2ContactPerson(BaseModel):
    """Contact person for NIS2 notifications."""
    name: str
    role: str
    email: str
    phone: Optional[str] = None
    available_24_7: bool = False


class NIS2IncidentImpact(BaseModel):
    """Impact assessment for NIS2 incident classification."""
    # Service disruption
    service_disrupted: bool = False
    service_name: Optional[str] = None
    disruption_duration_hours: Optional[float] = None

    # User impact
    users_affected: int = 0
    users_affected_percentage: Optional[float] = None

    # Geographic scope
    member_states_affected: List[str] = Field(default_factory=list)
    cross_border_impact: bool = False

    # Financial impact
    estimated_financial_loss_eur: Optional[float] = None

    # Data impact
    personal_data_affected: bool = False
    confidential_data_affected: bool = False

    # Reputational impact
    public_attention: bool = False
    media_coverage: bool = False

    def is_significant(self) -> bool:
        """Determine if incident meets NIS2 significant threshold.

        An incident is significant if it:
        - Causes severe operational disruption or financial loss
        - Affects other natural or legal persons by causing considerable damage
        """
        # Thresholds based on NIS2 guidance
        if self.cross_border_impact:
            return True
        if self.users_affected >= 100000:
            return True
        if self.users_affected_percentage and self.users_affected_percentage >= 25:
            return True
        if self.disruption_duration_hours and self.disruption_duration_hours >= 24:
            return True
        if self.estimated_financial_loss_eur and self.estimated_financial_loss_eur >= 500000:
            return True
        if self.personal_data_affected and self.users_affected >= 10000:
            return True
        return False


class NIS2EarlyWarning(BaseModel):
    """Early warning notification (within 24h)."""
    notification_id: str
    incident_id: str
    submitted_at: Optional[datetime] = None
    deadline: datetime

    # Minimal required information
    suspected_cause: Optional[str] = None  # malicious, technical_failure, unknown
    cross_border_suspected: bool = False
    initial_assessment: str = ""

    status: NIS2NotificationStatus = NIS2NotificationStatus.PENDING
    csirt_reference: Optional[str] = None

    @field_validator('deadline', mode='before')
    @classmethod
    def ensure_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class NIS2IncidentNotification(BaseModel):
    """Full incident notification (within 72h)."""
    notification_id: str
    incident_id: str
    early_warning_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    deadline: datetime

    # Incident details
    incident_description: str
    severity: NIS2IncidentSeverity
    incident_type: str  # e.g., ransomware, ddos, data_breach
    root_cause_preliminary: Optional[str] = None

    # Impact assessment
    impact: NIS2IncidentImpact

    # Response measures
    mitigation_measures: List[str] = Field(default_factory=list)
    containment_status: str = "ongoing"  # ongoing, contained, resolved

    status: NIS2NotificationStatus = NIS2NotificationStatus.PENDING
    csirt_reference: Optional[str] = None
    csirt_feedback: Optional[str] = None


class NIS2FinalReport(BaseModel):
    """Final incident report (within 30 days)."""
    report_id: str
    incident_id: str
    notification_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    deadline: datetime

    # Detailed analysis
    incident_description: str
    root_cause_analysis: str
    threat_type: str
    attack_techniques: List[str] = Field(default_factory=list)

    # Impact summary
    total_impact_assessment: str
    services_affected: List[str] = Field(default_factory=list)
    recovery_time_hours: Optional[float] = None

    # Lessons learned
    lessons_learned: str = ""
    preventive_measures: List[str] = Field(default_factory=list)
    security_improvements: List[str] = Field(default_factory=list)

    # Cross-border coordination
    other_csirts_notified: List[str] = Field(default_factory=list)
    enisa_notified: bool = False

    status: NIS2NotificationStatus = NIS2NotificationStatus.PENDING


class NIS2Notification(BaseModel):
    """Complete NIS2 notification tracking for an incident."""
    incident_id: str
    entity_type: NIS2EntityType
    sector: NIS2Sector
    organization_name: str
    member_state: str  # ISO 3166-1 alpha-2 country code

    # Detection and deadlines
    detection_time: datetime
    early_warning_deadline: datetime   # +24h
    notification_deadline: datetime     # +72h
    final_report_deadline: datetime     # +30d

    # Contact information
    primary_contact: NIS2ContactPerson
    technical_contact: Optional[NIS2ContactPerson] = None

    # Notification components
    early_warning: Optional[NIS2EarlyWarning] = None
    incident_notification: Optional[NIS2IncidentNotification] = None
    final_report: Optional[NIS2FinalReport] = None

    # External references
    csirt_reference: Optional[str] = None
    national_authority_reference: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        incident_id: str,
        entity_type: NIS2EntityType,
        sector: NIS2Sector,
        organization_name: str,
        member_state: str,
        detection_time: datetime,
        primary_contact: NIS2ContactPerson,
        technical_contact: Optional[NIS2ContactPerson] = None,
    ) -> "NIS2Notification":
        """Create a new NIS2 notification with calculated deadlines.

        Args:
            incident_id: Unique incident identifier
            entity_type: Essential or Important entity
            sector: NIS2 sector classification
            organization_name: Name of the organization
            member_state: EU member state (ISO code)
            detection_time: When incident was detected
            primary_contact: Primary contact person
            technical_contact: Optional technical contact

        Returns:
            New NIS2Notification instance
        """
        if detection_time.tzinfo is None:
            detection_time = detection_time.replace(tzinfo=timezone.utc)

        return cls(
            incident_id=incident_id,
            entity_type=entity_type,
            sector=sector,
            organization_name=organization_name,
            member_state=member_state,
            detection_time=detection_time,
            early_warning_deadline=detection_time + timedelta(hours=24),
            notification_deadline=detection_time + timedelta(hours=72),
            final_report_deadline=detection_time + timedelta(days=30),
            primary_contact=primary_contact,
            technical_contact=technical_contact,
        )

    def is_early_warning_overdue(self, now: Optional[datetime] = None) -> bool:
        """Check if early warning deadline has passed."""
        if now is None:
            now = datetime.now(timezone.utc)
        if self.early_warning and self.early_warning.status == NIS2NotificationStatus.SUBMITTED:
            return False
        return now > self.early_warning_deadline

    def is_notification_overdue(self, now: Optional[datetime] = None) -> bool:
        """Check if incident notification deadline has passed."""
        if now is None:
            now = datetime.now(timezone.utc)
        if self.incident_notification and self.incident_notification.status == NIS2NotificationStatus.SUBMITTED:
            return False
        return now > self.notification_deadline

    def is_final_report_overdue(self, now: Optional[datetime] = None) -> bool:
        """Check if final report deadline has passed."""
        if now is None:
            now = datetime.now(timezone.utc)
        if self.final_report and self.final_report.status == NIS2NotificationStatus.SUBMITTED:
            return False
        return now > self.final_report_deadline

    def get_compliance_status(self, now: Optional[datetime] = None) -> dict:
        """Get overall compliance status for all deadlines.

        Returns:
            Dict with status for each deadline
        """
        if now is None:
            now = datetime.now(timezone.utc)

        return {
            "early_warning": {
                "submitted": self.early_warning is not None and self.early_warning.status != NIS2NotificationStatus.PENDING,
                "overdue": self.is_early_warning_overdue(now),
                "deadline": self.early_warning_deadline,
            },
            "notification": {
                "submitted": self.incident_notification is not None and self.incident_notification.status != NIS2NotificationStatus.PENDING,
                "overdue": self.is_notification_overdue(now),
                "deadline": self.notification_deadline,
            },
            "final_report": {
                "submitted": self.final_report is not None and self.final_report.status != NIS2NotificationStatus.PENDING,
                "overdue": self.is_final_report_overdue(now),
                "deadline": self.final_report_deadline,
            },
        }


# EU Member States with their national CSIRTs
EU_MEMBER_STATES = {
    "AT": {"name": "Austria", "csirt": "CERT.at"},
    "BE": {"name": "Belgium", "csirt": "CERT.be"},
    "BG": {"name": "Bulgaria", "csirt": "CERT Bulgaria"},
    "HR": {"name": "Croatia", "csirt": "CERT.hr"},
    "CY": {"name": "Cyprus", "csirt": "CSIRT-CY"},
    "CZ": {"name": "Czechia", "csirt": "CSIRT.CZ"},
    "DK": {"name": "Denmark", "csirt": "CFCS"},
    "EE": {"name": "Estonia", "csirt": "CERT-EE"},
    "FI": {"name": "Finland", "csirt": "NCSC-FI"},
    "FR": {"name": "France", "csirt": "CERT-FR"},
    "DE": {"name": "Germany", "csirt": "BSI CERT-Bund"},
    "GR": {"name": "Greece", "csirt": "GR-CSIRT"},
    "HU": {"name": "Hungary", "csirt": "CERT-Hungary"},
    "IE": {"name": "Ireland", "csirt": "CSIRT-IE"},
    "IT": {"name": "Italy", "csirt": "CSIRT Italia"},
    "LV": {"name": "Latvia", "csirt": "CERT.LV"},
    "LT": {"name": "Lithuania", "csirt": "CERT-LT"},
    "LU": {"name": "Luxembourg", "csirt": "CIRCL"},
    "MT": {"name": "Malta", "csirt": "CSIRTMalta"},
    "NL": {"name": "Netherlands", "csirt": "NCSC-NL"},
    "PL": {"name": "Poland", "csirt": "CERT Polska"},
    "PT": {"name": "Portugal", "csirt": "CERT.PT"},
    "RO": {"name": "Romania", "csirt": "CERT-RO"},
    "SK": {"name": "Slovakia", "csirt": "SK-CERT"},
    "SI": {"name": "Slovenia", "csirt": "SI-CERT"},
    "ES": {"name": "Spain", "csirt": "INCIBE-CERT"},
    "SE": {"name": "Sweden", "csirt": "CERT-SE"},
}

# Sector to entity type mapping
SECTOR_ENTITY_TYPE = {
    # Essential (Annex I)
    NIS2Sector.ENERGY: NIS2EntityType.ESSENTIAL,
    NIS2Sector.TRANSPORT: NIS2EntityType.ESSENTIAL,
    NIS2Sector.BANKING: NIS2EntityType.ESSENTIAL,
    NIS2Sector.FINANCIAL_MARKET: NIS2EntityType.ESSENTIAL,
    NIS2Sector.HEALTH: NIS2EntityType.ESSENTIAL,
    NIS2Sector.DRINKING_WATER: NIS2EntityType.ESSENTIAL,
    NIS2Sector.WASTE_WATER: NIS2EntityType.ESSENTIAL,
    NIS2Sector.DIGITAL_INFRASTRUCTURE: NIS2EntityType.ESSENTIAL,
    NIS2Sector.ICT_SERVICE_MANAGEMENT: NIS2EntityType.ESSENTIAL,
    NIS2Sector.PUBLIC_ADMINISTRATION: NIS2EntityType.ESSENTIAL,
    NIS2Sector.SPACE: NIS2EntityType.ESSENTIAL,
    # Important (Annex II)
    NIS2Sector.POSTAL: NIS2EntityType.IMPORTANT,
    NIS2Sector.WASTE_MANAGEMENT: NIS2EntityType.IMPORTANT,
    NIS2Sector.CHEMICALS: NIS2EntityType.IMPORTANT,
    NIS2Sector.FOOD: NIS2EntityType.IMPORTANT,
    NIS2Sector.MANUFACTURING: NIS2EntityType.IMPORTANT,
    NIS2Sector.DIGITAL_PROVIDERS: NIS2EntityType.IMPORTANT,
    NIS2Sector.RESEARCH: NIS2EntityType.IMPORTANT,
}
