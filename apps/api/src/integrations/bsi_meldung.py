"""
BSI Meldepflicht Generator - Incident Notification Form Generator.

Generates notification forms for:
- BSI KRITIS Meldung (Critical Infrastructure)
- BSI IT-Sicherheitsvorfall Meldung
- NIS2 Incident Notification

Based on:
- BSI-Gesetz (BSIG) § 8b
- BSI-Kritisverordnung (BSI-KritisV)
- NIS2 Directive (EU) 2022/2555

Reference: https://www.bsi.bund.de/DE/IT-Sicherheitsvorfall/Unternehmen/Meldepflicht/meldepflicht_node.html
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class IncidentCategory(str, Enum):
    """BSI incident categories."""
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    DOS_DDOS = "dos_ddos"
    PHISHING = "phishing"
    APT = "apt"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    INSIDER_THREAT = "insider_threat"
    SUPPLY_CHAIN = "supply_chain"
    VULNERABILITY_EXPLOITATION = "vulnerability_exploitation"
    OTHER = "other"


class ImpactLevel(str, Enum):
    """Impact level for BSI reporting."""
    CRITICAL = "kritisch"
    HIGH = "hoch"
    MEDIUM = "mittel"
    LOW = "gering"
    UNKNOWN = "unbekannt"


class KRITISSector(str, Enum):
    """KRITIS sectors as defined by BSI-KritisV."""
    ENERGY = "energie"
    WATER = "wasser"
    FOOD = "ernaehrung"
    IT_TELECOM = "it_telekommunikation"
    HEALTH = "gesundheit"
    FINANCE = "finanz_versicherung"
    TRANSPORT = "transport_verkehr"
    GOVERNMENT = "staat_verwaltung"
    MEDIA = "medien_kultur"
    NOT_KRITIS = "nicht_kritis"


class NotificationType(str, Enum):
    """Type of BSI notification."""
    INITIAL = "erstmeldung"
    UPDATE = "folgemeldung"
    FINAL = "abschlussmeldung"


@dataclass
class AffectedSystem:
    """Information about an affected system."""
    hostname: str = ""
    ip_address: str = ""
    operating_system: str = ""
    function: str = ""
    criticality: str = ""


@dataclass
class ContactPerson:
    """Contact person for BSI communication."""
    name: str = ""
    role: str = ""
    email: str = ""
    phone: str = ""
    available_24_7: bool = False


@dataclass
class BSIMeldung:
    """
    BSI Incident Notification Form.

    Contains all fields required for BSI incident reporting
    according to BSIG § 8b and BSI-KritisV.
    """
    # Metadata
    meldung_id: str = ""
    notification_type: NotificationType = NotificationType.INITIAL
    reference_id: Optional[str] = None  # For follow-up notifications
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Organization Information
    organization_name: str = ""
    organization_address: str = ""
    organization_sector: KRITISSector = KRITISSector.NOT_KRITIS
    is_kritis_operator: bool = False
    kritis_registration_number: str = ""

    # Contact Information
    primary_contact: ContactPerson = field(default_factory=ContactPerson)
    technical_contact: ContactPerson = field(default_factory=ContactPerson)

    # Incident Information
    incident_id: str = ""
    incident_title: str = ""
    incident_category: IncidentCategory = IncidentCategory.OTHER
    incident_description: str = ""

    # Timeline
    detection_time: Optional[datetime] = None
    incident_start_time: Optional[datetime] = None
    containment_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None

    # Impact Assessment
    impact_level: ImpactLevel = ImpactLevel.UNKNOWN
    impact_description: str = ""
    affected_services: List[str] = field(default_factory=list)
    affected_systems_count: int = 0
    affected_users_count: int = 0
    data_affected: bool = False
    data_types_affected: List[str] = field(default_factory=list)
    financial_impact_estimated: str = ""

    # Technical Details
    affected_systems: List[AffectedSystem] = field(default_factory=list)
    attack_vectors: List[str] = field(default_factory=list)
    iocs: List[Dict[str, str]] = field(default_factory=list)
    malware_family: str = ""
    cves_exploited: List[str] = field(default_factory=list)

    # Response Actions
    containment_measures: List[str] = field(default_factory=list)
    eradication_measures: List[str] = field(default_factory=list)
    recovery_measures: List[str] = field(default_factory=list)

    # External Support
    external_support_requested: bool = False
    external_support_details: str = ""
    law_enforcement_notified: bool = False
    law_enforcement_reference: str = ""

    # Additional Information
    lessons_learned: str = ""
    preventive_measures_planned: str = ""
    additional_notes: str = ""


class BSIMeldungGenerator:
    """
    Generator for BSI incident notification forms.

    Creates properly formatted notifications for:
    - KRITIS operators (mandatory reporting)
    - Non-KRITIS organizations (voluntary reporting)
    - NIS2 compliance
    """

    def __init__(self):
        self._templates = self._load_templates()
        self._deadlines = self._load_deadlines()

    def _load_templates(self) -> Dict[str, str]:
        """Load notification templates."""
        return {
            "subject_initial": "IT-Sicherheitsvorfall Erstmeldung - {organization} - {date}",
            "subject_update": "IT-Sicherheitsvorfall Folgemeldung - {organization} - Ref: {ref_id}",
            "subject_final": "IT-Sicherheitsvorfall Abschlussmeldung - {organization} - Ref: {ref_id}",
        }

    def _load_deadlines(self) -> Dict[str, timedelta]:
        """Load regulatory deadlines."""
        return {
            "kritis_initial": timedelta(hours=24),  # 24h for KRITIS
            "kritis_detailed": timedelta(hours=72),  # 72h for detailed report
            "nis2_early_warning": timedelta(hours=24),  # 24h early warning
            "nis2_notification": timedelta(hours=72),  # 72h full notification
            "nis2_final": timedelta(days=30),  # 30 days final report
            "gdpr_notification": timedelta(hours=72),  # 72h for GDPR
        }

    def create_from_incident(
        self,
        incident_id: str,
        incident_data: Dict[str, Any],
        organization_data: Dict[str, Any],
        contact_data: Dict[str, Any],
    ) -> BSIMeldung:
        """
        Create a BSI notification from incident data.

        Args:
            incident_id: Incident identifier
            incident_data: Incident details from IR Companion
            organization_data: Organization information
            contact_data: Contact person information

        Returns:
            Populated BSIMeldung object
        """
        meldung = BSIMeldung(
            meldung_id=f"BSI-{incident_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
            incident_id=incident_id,
        )

        # Organization info
        meldung.organization_name = organization_data.get("name", "")
        meldung.organization_address = organization_data.get("address", "")
        meldung.organization_sector = KRITISSector(
            organization_data.get("sector", "nicht_kritis")
        )
        meldung.is_kritis_operator = organization_data.get("is_kritis", False)
        meldung.kritis_registration_number = organization_data.get("kritis_number", "")

        # Primary contact
        meldung.primary_contact = ContactPerson(
            name=contact_data.get("name", ""),
            role=contact_data.get("role", ""),
            email=contact_data.get("email", ""),
            phone=contact_data.get("phone", ""),
            available_24_7=contact_data.get("available_24_7", False),
        )

        # Incident info
        meldung.incident_title = incident_data.get("title", "")
        meldung.incident_description = incident_data.get("description", "")
        meldung.incident_category = self._detect_category(incident_data)

        # Timeline
        if incident_data.get("detection_time"):
            meldung.detection_time = incident_data["detection_time"]
        if incident_data.get("start_time"):
            meldung.incident_start_time = incident_data["start_time"]

        # Impact
        meldung.impact_level = self._assess_impact(incident_data)
        meldung.impact_description = incident_data.get("impact_description", "")
        meldung.affected_services = incident_data.get("affected_services", [])
        meldung.affected_systems_count = incident_data.get("affected_systems_count", 0)
        meldung.affected_users_count = incident_data.get("affected_users_count", 0)

        # Technical details
        meldung.attack_vectors = incident_data.get("attack_vectors", [])
        meldung.iocs = incident_data.get("iocs", [])
        meldung.malware_family = incident_data.get("malware_family", "")
        meldung.cves_exploited = incident_data.get("cves", [])

        # Response actions
        meldung.containment_measures = incident_data.get("containment_measures", [])
        meldung.eradication_measures = incident_data.get("eradication_measures", [])

        return meldung

    def _detect_category(self, incident_data: Dict[str, Any]) -> IncidentCategory:
        """Detect incident category from data."""
        title = incident_data.get("title", "").lower()
        description = incident_data.get("description", "").lower()
        text = f"{title} {description}"

        if any(w in text for w in ["ransomware", "verschlüssel", "encrypt", "ransom"]):
            return IncidentCategory.RANSOMWARE
        elif any(w in text for w in ["malware", "virus", "trojan", "trojaner"]):
            return IncidentCategory.MALWARE
        elif any(w in text for w in ["ddos", "dos", "denial of service"]):
            return IncidentCategory.DOS_DDOS
        elif any(w in text for w in ["phishing", "spear-phishing", "social engineering"]):
            return IncidentCategory.PHISHING
        elif any(w in text for w in ["apt", "advanced persistent", "nation state"]):
            return IncidentCategory.APT
        elif any(w in text for w in ["data breach", "datenleck", "data leak"]):
            return IncidentCategory.DATA_BREACH
        elif any(w in text for w in ["unauthorized access", "unbefugter zugriff"]):
            return IncidentCategory.UNAUTHORIZED_ACCESS
        elif any(w in text for w in ["insider", "mitarbeiter", "employee"]):
            return IncidentCategory.INSIDER_THREAT
        elif any(w in text for w in ["supply chain", "lieferkette", "third party"]):
            return IncidentCategory.SUPPLY_CHAIN
        elif any(w in text for w in ["cve", "vulnerability", "schwachstelle", "exploit"]):
            return IncidentCategory.VULNERABILITY_EXPLOITATION

        return IncidentCategory.OTHER

    def _assess_impact(self, incident_data: Dict[str, Any]) -> ImpactLevel:
        """Assess impact level from incident data."""
        # Simple heuristic based on affected counts and keywords
        systems = incident_data.get("affected_systems_count", 0)
        users = incident_data.get("affected_users_count", 0)
        description = incident_data.get("description", "").lower()

        critical_keywords = ["kritisch", "critical", "total", "complete", "all systems"]
        high_keywords = ["significant", "major", "wichtig", "erheblich"]

        if any(kw in description for kw in critical_keywords) or systems > 100 or users > 1000:
            return ImpactLevel.CRITICAL
        elif any(kw in description for kw in high_keywords) or systems > 50 or users > 500:
            return ImpactLevel.HIGH
        elif systems > 10 or users > 100:
            return ImpactLevel.MEDIUM
        elif systems > 0 or users > 0:
            return ImpactLevel.LOW

        return ImpactLevel.UNKNOWN

    def calculate_deadlines(
        self,
        detection_time: datetime,
        is_kritis: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate regulatory deadlines based on detection time.

        Args:
            detection_time: When the incident was detected
            is_kritis: Whether organization is KRITIS operator

        Returns:
            Dictionary of deadlines with status
        """
        now = datetime.now(timezone.utc)
        if detection_time.tzinfo is None:
            detection_time = detection_time.replace(tzinfo=timezone.utc)

        deadlines = {}

        if is_kritis:
            # KRITIS deadlines
            initial_deadline = detection_time + self._deadlines["kritis_initial"]
            detailed_deadline = detection_time + self._deadlines["kritis_detailed"]

            deadlines["kritis_initial"] = {
                "name": "KRITIS Erstmeldung",
                "deadline": initial_deadline.isoformat(),
                "remaining_hours": max(0, (initial_deadline - now).total_seconds() / 3600),
                "overdue": now > initial_deadline,
                "description": "Erste Meldung an BSI innerhalb 24 Stunden",
            }
            deadlines["kritis_detailed"] = {
                "name": "KRITIS Detailmeldung",
                "deadline": detailed_deadline.isoformat(),
                "remaining_hours": max(0, (detailed_deadline - now).total_seconds() / 3600),
                "overdue": now > detailed_deadline,
                "description": "Detaillierte Meldung innerhalb 72 Stunden",
            }

        # NIS2 deadlines (applicable to many organizations)
        nis2_early = detection_time + self._deadlines["nis2_early_warning"]
        nis2_full = detection_time + self._deadlines["nis2_notification"]
        nis2_final = detection_time + self._deadlines["nis2_final"]

        deadlines["nis2_early_warning"] = {
            "name": "NIS2 Frühwarnung",
            "deadline": nis2_early.isoformat(),
            "remaining_hours": max(0, (nis2_early - now).total_seconds() / 3600),
            "overdue": now > nis2_early,
            "description": "Frühwarnung an zuständige Behörde (24h)",
        }
        deadlines["nis2_notification"] = {
            "name": "NIS2 Meldung",
            "deadline": nis2_full.isoformat(),
            "remaining_hours": max(0, (nis2_full - now).total_seconds() / 3600),
            "overdue": now > nis2_full,
            "description": "Vollständige Meldung (72h)",
        }
        deadlines["nis2_final"] = {
            "name": "NIS2 Abschlussbericht",
            "deadline": nis2_final.isoformat(),
            "remaining_days": max(0, (nis2_final - now).total_seconds() / 86400),
            "overdue": now > nis2_final,
            "description": "Abschlussbericht (30 Tage)",
        }

        # GDPR deadline (if personal data affected)
        gdpr_deadline = detection_time + self._deadlines["gdpr_notification"]
        deadlines["gdpr"] = {
            "name": "DSGVO Meldung",
            "deadline": gdpr_deadline.isoformat(),
            "remaining_hours": max(0, (gdpr_deadline - now).total_seconds() / 3600),
            "overdue": now > gdpr_deadline,
            "description": "Meldung an Datenschutzbehörde (72h)",
        }

        return deadlines

    def get_kritis_sectors(self) -> List[Dict[str, str]]:
        """Get all KRITIS sectors with German labels."""
        return [
            {"id": KRITISSector.ENERGY.value, "name": "Energie"},
            {"id": KRITISSector.WATER.value, "name": "Wasser"},
            {"id": KRITISSector.FOOD.value, "name": "Ernährung"},
            {"id": KRITISSector.IT_TELECOM.value, "name": "IT und Telekommunikation"},
            {"id": KRITISSector.HEALTH.value, "name": "Gesundheit"},
            {"id": KRITISSector.FINANCE.value, "name": "Finanz- und Versicherungswesen"},
            {"id": KRITISSector.TRANSPORT.value, "name": "Transport und Verkehr"},
            {"id": KRITISSector.GOVERNMENT.value, "name": "Staat und Verwaltung"},
            {"id": KRITISSector.MEDIA.value, "name": "Medien und Kultur"},
            {"id": KRITISSector.NOT_KRITIS.value, "name": "Kein KRITIS-Sektor"},
        ]

    def get_incident_categories(self) -> List[Dict[str, str]]:
        """Get all incident categories with German labels."""
        return [
            {"id": IncidentCategory.MALWARE.value, "name": "Schadsoftware (Malware)"},
            {"id": IncidentCategory.RANSOMWARE.value, "name": "Ransomware / Verschlüsselungstrojaner"},
            {"id": IncidentCategory.DOS_DDOS.value, "name": "DoS/DDoS-Angriff"},
            {"id": IncidentCategory.PHISHING.value, "name": "Phishing / Social Engineering"},
            {"id": IncidentCategory.APT.value, "name": "APT / Staatliche Akteure"},
            {"id": IncidentCategory.DATA_BREACH.value, "name": "Datenpanne / Datenabfluss"},
            {"id": IncidentCategory.UNAUTHORIZED_ACCESS.value, "name": "Unbefugter Zugriff"},
            {"id": IncidentCategory.INSIDER_THREAT.value, "name": "Insider-Bedrohung"},
            {"id": IncidentCategory.SUPPLY_CHAIN.value, "name": "Supply-Chain-Angriff"},
            {"id": IncidentCategory.VULNERABILITY_EXPLOITATION.value, "name": "Ausnutzung von Schwachstellen"},
            {"id": IncidentCategory.OTHER.value, "name": "Sonstiges"},
        ]

    def export_markdown(self, meldung: BSIMeldung) -> str:
        """Export notification as Markdown document."""
        lines = [
            "# BSI IT-Sicherheitsvorfall Meldung",
            "",
            f"**Meldungs-ID:** {meldung.meldung_id}",
            f"**Typ:** {self._get_notification_type_label(meldung.notification_type)}",
            f"**Erstellt:** {meldung.created_at.strftime('%d.%m.%Y %H:%M')} Uhr",
            "",
            "---",
            "",
            "## 1. Meldende Organisation",
            "",
            f"**Name:** {meldung.organization_name}",
            f"**Anschrift:** {meldung.organization_address}",
            f"**Sektor:** {self._get_sector_label(meldung.organization_sector)}",
            f"**KRITIS-Betreiber:** {'Ja' if meldung.is_kritis_operator else 'Nein'}",
        ]

        if meldung.is_kritis_operator and meldung.kritis_registration_number:
            lines.append(f"**KRITIS-Registrierungsnummer:** {meldung.kritis_registration_number}")

        lines.extend([
            "",
            "## 2. Ansprechpartner",
            "",
            "### Primärer Ansprechpartner",
            f"- **Name:** {meldung.primary_contact.name}",
            f"- **Funktion:** {meldung.primary_contact.role}",
            f"- **E-Mail:** {meldung.primary_contact.email}",
            f"- **Telefon:** {meldung.primary_contact.phone}",
            f"- **24/7 erreichbar:** {'Ja' if meldung.primary_contact.available_24_7 else 'Nein'}",
            "",
        ])

        if meldung.technical_contact.name:
            lines.extend([
                "### Technischer Ansprechpartner",
                f"- **Name:** {meldung.technical_contact.name}",
                f"- **Funktion:** {meldung.technical_contact.role}",
                f"- **E-Mail:** {meldung.technical_contact.email}",
                f"- **Telefon:** {meldung.technical_contact.phone}",
                "",
            ])

        lines.extend([
            "## 3. Vorfallsbeschreibung",
            "",
            f"**Vorfall-ID:** {meldung.incident_id}",
            f"**Titel:** {meldung.incident_title}",
            f"**Kategorie:** {self._get_category_label(meldung.incident_category)}",
            "",
            "**Beschreibung:**",
            meldung.incident_description or "_Keine Beschreibung angegeben_",
            "",
            "## 4. Zeitlicher Verlauf",
            "",
        ])

        if meldung.detection_time:
            lines.append(f"- **Erkennung:** {meldung.detection_time.strftime('%d.%m.%Y %H:%M')} Uhr")
        if meldung.incident_start_time:
            lines.append(f"- **Beginn des Vorfalls:** {meldung.incident_start_time.strftime('%d.%m.%Y %H:%M')} Uhr")
        if meldung.containment_time:
            lines.append(f"- **Eindämmung:** {meldung.containment_time.strftime('%d.%m.%Y %H:%M')} Uhr")
        if meldung.resolution_time:
            lines.append(f"- **Behebung:** {meldung.resolution_time.strftime('%d.%m.%Y %H:%M')} Uhr")

        lines.extend([
            "",
            "## 5. Auswirkungen",
            "",
            f"**Schweregrad:** {self._get_impact_label(meldung.impact_level)}",
            "",
        ])

        if meldung.impact_description:
            lines.extend([
                "**Beschreibung der Auswirkungen:**",
                meldung.impact_description,
                "",
            ])

        lines.extend([
            f"- **Betroffene Systeme:** {meldung.affected_systems_count}",
            f"- **Betroffene Nutzer:** {meldung.affected_users_count}",
            f"- **Datenverlust/-abfluss:** {'Ja' if meldung.data_affected else 'Nein'}",
        ])

        if meldung.affected_services:
            lines.extend([
                "",
                "**Betroffene Dienste:**",
            ])
            for service in meldung.affected_services:
                lines.append(f"- {service}")

        if meldung.data_types_affected:
            lines.extend([
                "",
                "**Betroffene Datenarten:**",
            ])
            for data_type in meldung.data_types_affected:
                lines.append(f"- {data_type}")

        if meldung.financial_impact_estimated:
            lines.append(f"\n**Geschätzter finanzieller Schaden:** {meldung.financial_impact_estimated}")

        lines.extend([
            "",
            "## 6. Technische Details",
            "",
        ])

        if meldung.attack_vectors:
            lines.append("**Angriffsvektoren:**")
            for vector in meldung.attack_vectors:
                lines.append(f"- {vector}")
            lines.append("")

        if meldung.malware_family:
            lines.append(f"**Malware-Familie:** {meldung.malware_family}")
            lines.append("")

        if meldung.cves_exploited:
            lines.append("**Ausgenutzte Schwachstellen (CVEs):**")
            for cve in meldung.cves_exploited:
                lines.append(f"- {cve}")
            lines.append("")

        if meldung.iocs:
            lines.append("**Indicators of Compromise (IoCs):**")
            lines.append("")
            lines.append("| Typ | Wert |")
            lines.append("|-----|------|")
            for ioc in meldung.iocs[:20]:  # Limit to 20
                lines.append(f"| {ioc.get('type', '')} | `{ioc.get('value', '')}` |")
            lines.append("")

        lines.extend([
            "## 7. Ergriffene Maßnahmen",
            "",
        ])

        if meldung.containment_measures:
            lines.append("**Eindämmungsmaßnahmen:**")
            for measure in meldung.containment_measures:
                lines.append(f"- {measure}")
            lines.append("")

        if meldung.eradication_measures:
            lines.append("**Bereinigungsmaßnahmen:**")
            for measure in meldung.eradication_measures:
                lines.append(f"- {measure}")
            lines.append("")

        if meldung.recovery_measures:
            lines.append("**Wiederherstellungsmaßnahmen:**")
            for measure in meldung.recovery_measures:
                lines.append(f"- {measure}")
            lines.append("")

        lines.extend([
            "## 8. Externe Unterstützung",
            "",
            f"**Externe Unterstützung angefordert:** {'Ja' if meldung.external_support_requested else 'Nein'}",
        ])

        if meldung.external_support_details:
            lines.append(f"**Details:** {meldung.external_support_details}")

        lines.extend([
            "",
            f"**Strafverfolgungsbehörden informiert:** {'Ja' if meldung.law_enforcement_notified else 'Nein'}",
        ])

        if meldung.law_enforcement_reference:
            lines.append(f"**Aktenzeichen:** {meldung.law_enforcement_reference}")

        if meldung.lessons_learned or meldung.preventive_measures_planned:
            lines.extend([
                "",
                "## 9. Lessons Learned & Präventivmaßnahmen",
                "",
            ])
            if meldung.lessons_learned:
                lines.append(f"**Erkenntnisse:** {meldung.lessons_learned}")
            if meldung.preventive_measures_planned:
                lines.append(f"**Geplante Präventivmaßnahmen:** {meldung.preventive_measures_planned}")

        if meldung.additional_notes:
            lines.extend([
                "",
                "## 10. Weitere Anmerkungen",
                "",
                meldung.additional_notes,
            ])

        lines.extend([
            "",
            "---",
            "",
            "*Diese Meldung wurde mit IR Companion generiert.*",
            "",
            f"*Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr*",
        ])

        return "\n".join(lines)

    def export_json(self, meldung: BSIMeldung) -> str:
        """Export notification as JSON for API submission."""
        data = {
            "meldung_id": meldung.meldung_id,
            "notification_type": meldung.notification_type.value,
            "reference_id": meldung.reference_id,
            "created_at": meldung.created_at.isoformat(),
            "organization": {
                "name": meldung.organization_name,
                "address": meldung.organization_address,
                "sector": meldung.organization_sector.value,
                "is_kritis": meldung.is_kritis_operator,
                "kritis_number": meldung.kritis_registration_number,
            },
            "contacts": {
                "primary": {
                    "name": meldung.primary_contact.name,
                    "role": meldung.primary_contact.role,
                    "email": meldung.primary_contact.email,
                    "phone": meldung.primary_contact.phone,
                    "available_24_7": meldung.primary_contact.available_24_7,
                },
            },
            "incident": {
                "id": meldung.incident_id,
                "title": meldung.incident_title,
                "category": meldung.incident_category.value,
                "description": meldung.incident_description,
            },
            "timeline": {
                "detection": meldung.detection_time.isoformat() if meldung.detection_time else None,
                "start": meldung.incident_start_time.isoformat() if meldung.incident_start_time else None,
                "containment": meldung.containment_time.isoformat() if meldung.containment_time else None,
                "resolution": meldung.resolution_time.isoformat() if meldung.resolution_time else None,
            },
            "impact": {
                "level": meldung.impact_level.value,
                "description": meldung.impact_description,
                "affected_systems": meldung.affected_systems_count,
                "affected_users": meldung.affected_users_count,
                "data_affected": meldung.data_affected,
                "services": meldung.affected_services,
            },
            "technical": {
                "attack_vectors": meldung.attack_vectors,
                "malware_family": meldung.malware_family,
                "cves": meldung.cves_exploited,
                "iocs": meldung.iocs,
            },
            "response": {
                "containment": meldung.containment_measures,
                "eradication": meldung.eradication_measures,
                "recovery": meldung.recovery_measures,
            },
            "external": {
                "support_requested": meldung.external_support_requested,
                "support_details": meldung.external_support_details,
                "law_enforcement": meldung.law_enforcement_notified,
                "law_enforcement_ref": meldung.law_enforcement_reference,
            },
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _get_notification_type_label(self, ntype: NotificationType) -> str:
        """Get German label for notification type."""
        labels = {
            NotificationType.INITIAL: "Erstmeldung",
            NotificationType.UPDATE: "Folgemeldung",
            NotificationType.FINAL: "Abschlussmeldung",
        }
        return labels.get(ntype, ntype.value)

    def _get_sector_label(self, sector: KRITISSector) -> str:
        """Get German label for KRITIS sector."""
        labels = {
            KRITISSector.ENERGY: "Energie",
            KRITISSector.WATER: "Wasser",
            KRITISSector.FOOD: "Ernährung",
            KRITISSector.IT_TELECOM: "IT und Telekommunikation",
            KRITISSector.HEALTH: "Gesundheit",
            KRITISSector.FINANCE: "Finanz- und Versicherungswesen",
            KRITISSector.TRANSPORT: "Transport und Verkehr",
            KRITISSector.GOVERNMENT: "Staat und Verwaltung",
            KRITISSector.MEDIA: "Medien und Kultur",
            KRITISSector.NOT_KRITIS: "Kein KRITIS-Sektor",
        }
        return labels.get(sector, sector.value)

    def _get_category_label(self, category: IncidentCategory) -> str:
        """Get German label for incident category."""
        labels = {
            IncidentCategory.MALWARE: "Schadsoftware (Malware)",
            IncidentCategory.RANSOMWARE: "Ransomware / Verschlüsselungstrojaner",
            IncidentCategory.DOS_DDOS: "DoS/DDoS-Angriff",
            IncidentCategory.PHISHING: "Phishing / Social Engineering",
            IncidentCategory.APT: "APT / Staatliche Akteure",
            IncidentCategory.DATA_BREACH: "Datenpanne / Datenabfluss",
            IncidentCategory.UNAUTHORIZED_ACCESS: "Unbefugter Zugriff",
            IncidentCategory.INSIDER_THREAT: "Insider-Bedrohung",
            IncidentCategory.SUPPLY_CHAIN: "Supply-Chain-Angriff",
            IncidentCategory.VULNERABILITY_EXPLOITATION: "Ausnutzung von Schwachstellen",
            IncidentCategory.OTHER: "Sonstiges",
        }
        return labels.get(category, category.value)

    def _get_impact_label(self, impact: ImpactLevel) -> str:
        """Get German label for impact level."""
        labels = {
            ImpactLevel.CRITICAL: "Kritisch",
            ImpactLevel.HIGH: "Hoch",
            ImpactLevel.MEDIUM: "Mittel",
            ImpactLevel.LOW: "Gering",
            ImpactLevel.UNKNOWN: "Unbekannt",
        }
        return labels.get(impact, impact.value)


# Singleton instance
_bsi_meldung_generator: Optional[BSIMeldungGenerator] = None


def get_bsi_meldung_generator() -> BSIMeldungGenerator:
    """Get the singleton BSI Meldung generator instance."""
    global _bsi_meldung_generator
    if _bsi_meldung_generator is None:
        _bsi_meldung_generator = BSIMeldungGenerator()
    return _bsi_meldung_generator
