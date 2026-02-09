"""
NIST Cybersecurity Framework 2.0 Models

Official Sources:
-----------------
- NIST Cybersecurity Framework 2.0 (February 2024):
  https://www.nist.gov/cyberframework

- CSF 2.0 Core (Excel/JSON):
  https://www.nist.gov/document/csf-20-core-spreadsheet

- NIST CSF 2.0 Reference Tool:
  https://csf.tools/

- NIST SP 800-53 Rev. 5 (Security Controls):
  https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final

- NIST Informative References:
  https://www.nist.gov/cyberframework/informative-references

CSF 2.0 Released: February 26, 2024

Functions: GOVERN (new), IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER
Categories: 22 total across 6 functions
Subcategories: 106 total

Note: This is the public US government framework. Control mappings and
implementation tiers are based on official NIST publications.
"""

import uuid
from typing import Optional, List
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from src.db.database import Base


# =============================================================================
# Enums
# =============================================================================

class NISTFunction(str, Enum):
    """NIST CSF 2.0 Core Functions."""
    GOVERN = "govern"
    IDENTIFY = "identify"
    PROTECT = "protect"
    DETECT = "detect"
    RESPOND = "respond"
    RECOVER = "recover"


class NISTImplementationTier(str, Enum):
    """NIST Implementation Tiers (1-4)."""
    TIER_1 = "tier_1"  # Partial
    TIER_2 = "tier_2"  # Risk Informed
    TIER_3 = "tier_3"  # Repeatable
    TIER_4 = "tier_4"  # Adaptive


class NISTAssessmentStatus(str, Enum):
    """Assessment status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NISTOutcomeStatus(str, Enum):
    """Status for subcategory outcomes."""
    NOT_EVALUATED = "not_evaluated"
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    LARGELY_IMPLEMENTED = "largely_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"
    NOT_APPLICABLE = "not_applicable"


class NISTOrganizationType(str, Enum):
    """Organization types."""
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    ENERGY = "energy"
    TECHNOLOGY = "technology"
    GOVERNMENT = "government"
    EDUCATION = "education"
    RETAIL = "retail"
    OTHER = "other"


class NISTOrganizationSize(str, Enum):
    """Organization sizes."""
    SMALL = "small"       # <100 employees
    MEDIUM = "medium"     # 100-999 employees
    LARGE = "large"       # 1000-9999 employees
    ENTERPRISE = "enterprise"  # 10000+ employees


# =============================================================================
# Reference Data - NIST CSF 2.0 Functions and Categories
# =============================================================================

NIST_FUNCTIONS = [
    {
        "id": "govern",
        "code": "GV",
        "name_en": "Govern",
        "name_de": "Steuern",
        "description_en": "Establish and monitor the organization's cybersecurity risk management strategy, expectations, and policy.",
        "description_de": "Festlegung und Überwachung der Cybersecurity-Risikomanagementstrategie, Erwartungen und Richtlinien.",
        "weight": 20,
        "category_count": 6,
    },
    {
        "id": "identify",
        "code": "ID",
        "name_en": "Identify",
        "name_de": "Identifizieren",
        "description_en": "Understand the organization's current cybersecurity risk posture and assets.",
        "description_de": "Verständnis der aktuellen Cybersecurity-Risikolage und Assets der Organisation.",
        "weight": 15,
        "category_count": 4,
    },
    {
        "id": "protect",
        "code": "PR",
        "name_en": "Protect",
        "name_de": "Schützen",
        "description_en": "Use safeguards to prevent or reduce cybersecurity risk.",
        "description_de": "Einsatz von Schutzmaßnahmen zur Verhinderung oder Reduzierung von Cybersecurity-Risiken.",
        "weight": 20,
        "category_count": 5,
    },
    {
        "id": "detect",
        "code": "DE",
        "name_en": "Detect",
        "name_de": "Erkennen",
        "description_en": "Find and analyze possible cybersecurity attacks and compromises.",
        "description_de": "Erkennung und Analyse möglicher Cybersecurity-Angriffe und Kompromittierungen.",
        "weight": 15,
        "category_count": 2,
    },
    {
        "id": "respond",
        "code": "RS",
        "name_en": "Respond",
        "name_de": "Reagieren",
        "description_en": "Take action regarding a detected cybersecurity incident.",
        "description_de": "Maßnahmen bei erkannten Cybersecurity-Vorfällen ergreifen.",
        "weight": 15,
        "category_count": 4,
    },
    {
        "id": "recover",
        "code": "RC",
        "name_en": "Recover",
        "name_de": "Wiederherstellen",
        "description_en": "Restore assets and operations affected by a cybersecurity incident.",
        "description_de": "Wiederherstellung betroffener Assets und Betriebsabläufe nach einem Cybersecurity-Vorfall.",
        "weight": 15,
        "category_count": 2,
    },
]


NIST_CATEGORIES = [
    # GOVERN
    {"id": "GV.OC", "function": "govern", "code": "OC", "name_en": "Organizational Context", "name_de": "Organisationskontext", "subcategory_count": 5},
    {"id": "GV.RM", "function": "govern", "code": "RM", "name_en": "Risk Management Strategy", "name_de": "Risikomanagementstrategie", "subcategory_count": 7},
    {"id": "GV.RR", "function": "govern", "code": "RR", "name_en": "Roles, Responsibilities, and Authorities", "name_de": "Rollen, Verantwortlichkeiten und Befugnisse", "subcategory_count": 4},
    {"id": "GV.PO", "function": "govern", "code": "PO", "name_en": "Policy", "name_de": "Richtlinien", "subcategory_count": 2},
    {"id": "GV.OV", "function": "govern", "code": "OV", "name_en": "Oversight", "name_de": "Aufsicht", "subcategory_count": 3},
    {"id": "GV.SC", "function": "govern", "code": "SC", "name_en": "Cybersecurity Supply Chain Risk Management", "name_de": "Cybersecurity-Lieferkettenrisikomanagement", "subcategory_count": 10},
    # IDENTIFY
    {"id": "ID.AM", "function": "identify", "code": "AM", "name_en": "Asset Management", "name_de": "Asset-Management", "subcategory_count": 8},
    {"id": "ID.RA", "function": "identify", "code": "RA", "name_en": "Risk Assessment", "name_de": "Risikobewertung", "subcategory_count": 10},
    {"id": "ID.IM", "function": "identify", "code": "IM", "name_en": "Improvement", "name_de": "Verbesserung", "subcategory_count": 4},
    # PROTECT
    {"id": "PR.AA", "function": "protect", "code": "AA", "name_en": "Identity Management, Authentication, and Access Control", "name_de": "Identitätsmanagement, Authentifizierung und Zugriffskontrolle", "subcategory_count": 6},
    {"id": "PR.AT", "function": "protect", "code": "AT", "name_en": "Awareness and Training", "name_de": "Bewusstsein und Schulung", "subcategory_count": 2},
    {"id": "PR.DS", "function": "protect", "code": "DS", "name_en": "Data Security", "name_de": "Datensicherheit", "subcategory_count": 10},
    {"id": "PR.PS", "function": "protect", "code": "PS", "name_en": "Platform Security", "name_de": "Plattformsicherheit", "subcategory_count": 6},
    {"id": "PR.IR", "function": "protect", "code": "IR", "name_en": "Technology Infrastructure Resilience", "name_de": "Technologie-Infrastruktur-Resilienz", "subcategory_count": 4},
    # DETECT
    {"id": "DE.CM", "function": "detect", "code": "CM", "name_en": "Continuous Monitoring", "name_de": "Kontinuierliche Überwachung", "subcategory_count": 9},
    {"id": "DE.AE", "function": "detect", "code": "AE", "name_en": "Adverse Event Analysis", "name_de": "Analyse unerwünschter Ereignisse", "subcategory_count": 8},
    # RESPOND
    {"id": "RS.MA", "function": "respond", "code": "MA", "name_en": "Incident Management", "name_de": "Vorfallmanagement", "subcategory_count": 5},
    {"id": "RS.AN", "function": "respond", "code": "AN", "name_en": "Incident Analysis", "name_de": "Vorfallanalyse", "subcategory_count": 8},
    {"id": "RS.CO", "function": "respond", "code": "CO", "name_en": "Incident Response Reporting and Communication", "name_de": "Vorfallreaktions-Berichterstattung und Kommunikation", "subcategory_count": 3},
    {"id": "RS.MI", "function": "respond", "code": "MI", "name_en": "Incident Mitigation", "name_de": "Vorfallminderung", "subcategory_count": 2},
    # RECOVER
    {"id": "RC.RP", "function": "recover", "code": "RP", "name_en": "Incident Recovery Plan Execution", "name_de": "Ausführung des Wiederherstellungsplans", "subcategory_count": 6},
    {"id": "RC.CO", "function": "recover", "code": "CO", "name_en": "Incident Recovery Communication", "name_de": "Wiederherstellungskommunikation", "subcategory_count": 4},
]


# Subcategories (outcomes) - Selected key subcategories for each category
NIST_SUBCATEGORIES = [
    # GOVERN - Organizational Context (GV.OC)
    {"id": "GV.OC-01", "category": "GV.OC", "function": "govern", "name_en": "Organizational mission understood", "name_de": "Organisationsmission verstanden", "description_en": "The organizational mission is understood and informs cybersecurity risk management", "weight": 10, "priority": 1},
    {"id": "GV.OC-02", "category": "GV.OC", "function": "govern", "name_en": "Internal and external stakeholders understood", "name_de": "Interne und externe Stakeholder verstanden", "description_en": "Internal and external stakeholders are understood, and their needs and expectations are identified", "weight": 10, "priority": 2},
    {"id": "GV.OC-03", "category": "GV.OC", "function": "govern", "name_en": "Legal and regulatory requirements understood", "name_de": "Rechtliche und regulatorische Anforderungen verstanden", "description_en": "Legal, regulatory, and contractual requirements are understood and managed", "weight": 10, "priority": 1},
    {"id": "GV.OC-04", "category": "GV.OC", "function": "govern", "name_en": "Critical objectives and dependencies identified", "name_de": "Kritische Ziele und Abhängigkeiten identifiziert", "description_en": "Critical objectives, capabilities, and services are understood and communicated", "weight": 10, "priority": 1},
    {"id": "GV.OC-05", "category": "GV.OC", "function": "govern", "name_en": "Outcomes and priorities established", "name_de": "Ergebnisse und Prioritäten festgelegt", "description_en": "Outcomes, capabilities, and services that the organization depends on are understood", "weight": 8, "priority": 2},

    # GOVERN - Risk Management Strategy (GV.RM)
    {"id": "GV.RM-01", "category": "GV.RM", "function": "govern", "name_en": "Risk management objectives established", "name_de": "Risikomanagementziele festgelegt", "description_en": "Risk management objectives are established and agreed upon by organizational stakeholders", "weight": 12, "priority": 1},
    {"id": "GV.RM-02", "category": "GV.RM", "function": "govern", "name_en": "Risk appetite and tolerance established", "name_de": "Risikoappetit und -toleranz festgelegt", "description_en": "Risk appetite and risk tolerance statements are established and communicated", "weight": 12, "priority": 1},
    {"id": "GV.RM-03", "category": "GV.RM", "function": "govern", "name_en": "Risk management activities integrated", "name_de": "Risikomanagementaktivitäten integriert", "description_en": "Cybersecurity risk management activities are integrated into enterprise risk management", "weight": 10, "priority": 1},
    {"id": "GV.RM-04", "category": "GV.RM", "function": "govern", "name_en": "Strategic direction established", "name_de": "Strategische Ausrichtung festgelegt", "description_en": "Strategic direction that describes appropriate risk response options is established", "weight": 10, "priority": 2},
    {"id": "GV.RM-05", "category": "GV.RM", "function": "govern", "name_en": "Lines of communication established", "name_de": "Kommunikationswege etabliert", "description_en": "Lines of communication across the organization are established for cybersecurity risks", "weight": 8, "priority": 2},
    {"id": "GV.RM-06", "category": "GV.RM", "function": "govern", "name_en": "Standard method for calculating risk", "name_de": "Standardmethode zur Risikoberechnung", "description_en": "A standardized method for calculating, documenting, and prioritizing cybersecurity risks", "weight": 10, "priority": 1},
    {"id": "GV.RM-07", "category": "GV.RM", "function": "govern", "name_en": "Opportunities identified", "name_de": "Chancen identifiziert", "description_en": "Strategic opportunities are characterized and communicated", "weight": 6, "priority": 3},

    # GOVERN - Roles and Responsibilities (GV.RR)
    {"id": "GV.RR-01", "category": "GV.RR", "function": "govern", "name_en": "Leadership accountable", "name_de": "Führung rechenschaftspflichtig", "description_en": "Organizational leadership is responsible and accountable for cybersecurity risk", "weight": 12, "priority": 1},
    {"id": "GV.RR-02", "category": "GV.RR", "function": "govern", "name_en": "Roles and responsibilities established", "name_de": "Rollen und Verantwortlichkeiten festgelegt", "description_en": "Roles, responsibilities, and authorities are established and communicated", "weight": 12, "priority": 1},
    {"id": "GV.RR-03", "category": "GV.RR", "function": "govern", "name_en": "Adequate resources allocated", "name_de": "Ausreichende Ressourcen zugewiesen", "description_en": "Adequate resources are allocated commensurate with cybersecurity risk strategy", "weight": 10, "priority": 1},
    {"id": "GV.RR-04", "category": "GV.RR", "function": "govern", "name_en": "Cybersecurity included in HR practices", "name_de": "Cybersecurity in HR-Praktiken einbezogen", "description_en": "Cybersecurity is included in human resources practices", "weight": 8, "priority": 2},

    # GOVERN - Policy (GV.PO)
    {"id": "GV.PO-01", "category": "GV.PO", "function": "govern", "name_en": "Policy established", "name_de": "Richtlinie etabliert", "description_en": "Policy for managing cybersecurity risks is established based on organizational context", "weight": 12, "priority": 1},
    {"id": "GV.PO-02", "category": "GV.PO", "function": "govern", "name_en": "Policy communicated and enforced", "name_de": "Richtlinie kommuniziert und durchgesetzt", "description_en": "Policy for managing cybersecurity risks is reviewed, updated, communicated, and enforced", "weight": 10, "priority": 1},

    # GOVERN - Oversight (GV.OV)
    {"id": "GV.OV-01", "category": "GV.OV", "function": "govern", "name_en": "Cybersecurity risk management reviewed", "name_de": "Cybersecurity-Risikomanagement überprüft", "description_en": "Cybersecurity risk management strategy outcomes are reviewed to inform adjustments", "weight": 10, "priority": 1},
    {"id": "GV.OV-02", "category": "GV.OV", "function": "govern", "name_en": "Performance evaluated", "name_de": "Leistung bewertet", "description_en": "The cybersecurity risk management strategy is reviewed and adjusted as needed", "weight": 10, "priority": 2},
    {"id": "GV.OV-03", "category": "GV.OV", "function": "govern", "name_en": "Legal compliance evaluated", "name_de": "Rechtliche Compliance bewertet", "description_en": "Organizational cybersecurity risk management performance is evaluated and reviewed", "weight": 10, "priority": 1},

    # GOVERN - Supply Chain (GV.SC)
    {"id": "GV.SC-01", "category": "GV.SC", "function": "govern", "name_en": "Supply chain risk management program", "name_de": "Lieferkettenrisikomanagement-Programm", "description_en": "A cybersecurity supply chain risk management program is established and agreed upon", "weight": 12, "priority": 1},
    {"id": "GV.SC-02", "category": "GV.SC", "function": "govern", "name_en": "Suppliers and partners identified", "name_de": "Lieferanten und Partner identifiziert", "description_en": "Cybersecurity roles and responsibilities for suppliers, customers, and partners are established", "weight": 10, "priority": 1},
    {"id": "GV.SC-03", "category": "GV.SC", "function": "govern", "name_en": "Supply chain requirements integrated", "name_de": "Lieferkettenanforderungen integriert", "description_en": "Cybersecurity supply chain risk management is integrated into overall risk management", "weight": 10, "priority": 1},
    {"id": "GV.SC-04", "category": "GV.SC", "function": "govern", "name_en": "Suppliers assessed", "name_de": "Lieferanten bewertet", "description_en": "Suppliers are known and prioritized by criticality", "weight": 10, "priority": 1},
    {"id": "GV.SC-05", "category": "GV.SC", "function": "govern", "name_en": "Requirements in contracts", "name_de": "Anforderungen in Verträgen", "description_en": "Requirements to address cybersecurity risks are established in contracts", "weight": 10, "priority": 1},

    # IDENTIFY - Asset Management (ID.AM)
    {"id": "ID.AM-01", "category": "ID.AM", "function": "identify", "name_en": "Hardware inventoried", "name_de": "Hardware inventarisiert", "description_en": "Inventories of hardware managed by the organization are maintained", "weight": 12, "priority": 1},
    {"id": "ID.AM-02", "category": "ID.AM", "function": "identify", "name_en": "Software inventoried", "name_de": "Software inventarisiert", "description_en": "Inventories of software, services, and systems managed by the organization are maintained", "weight": 12, "priority": 1},
    {"id": "ID.AM-03", "category": "ID.AM", "function": "identify", "name_en": "Network architecture represented", "name_de": "Netzwerkarchitektur dargestellt", "description_en": "Representations of the organization's authorized network architecture are maintained", "weight": 10, "priority": 1},
    {"id": "ID.AM-04", "category": "ID.AM", "function": "identify", "name_en": "Data flows inventoried", "name_de": "Datenflüsse inventarisiert", "description_en": "Inventories of services provided by suppliers are maintained", "weight": 10, "priority": 2},
    {"id": "ID.AM-05", "category": "ID.AM", "function": "identify", "name_en": "Assets prioritized", "name_de": "Assets priorisiert", "description_en": "Assets are prioritized based on classification, criticality, resources, and mission impact", "weight": 12, "priority": 1},
    {"id": "ID.AM-07", "category": "ID.AM", "function": "identify", "name_en": "Data and assets inventoried", "name_de": "Daten und Assets inventarisiert", "description_en": "Inventories of data and corresponding metadata are maintained", "weight": 10, "priority": 1},
    {"id": "ID.AM-08", "category": "ID.AM", "function": "identify", "name_en": "Systems managed", "name_de": "Systeme verwaltet", "description_en": "Systems, hardware, software, and services are managed throughout their life cycles", "weight": 10, "priority": 2},

    # IDENTIFY - Risk Assessment (ID.RA)
    {"id": "ID.RA-01", "category": "ID.RA", "function": "identify", "name_en": "Vulnerabilities identified", "name_de": "Schwachstellen identifiziert", "description_en": "Vulnerabilities in assets are identified, validated, and recorded", "weight": 12, "priority": 1},
    {"id": "ID.RA-02", "category": "ID.RA", "function": "identify", "name_en": "Threat intelligence received", "name_de": "Bedrohungsinformationen empfangen", "description_en": "Cyber threat intelligence is received from information sharing forums and sources", "weight": 10, "priority": 1},
    {"id": "ID.RA-03", "category": "ID.RA", "function": "identify", "name_en": "Threats identified", "name_de": "Bedrohungen identifiziert", "description_en": "Internal and external threats to the organization are identified and recorded", "weight": 12, "priority": 1},
    {"id": "ID.RA-04", "category": "ID.RA", "function": "identify", "name_en": "Impacts identified", "name_de": "Auswirkungen identifiziert", "description_en": "Potential impacts and likelihoods of threats exploiting vulnerabilities are identified", "weight": 12, "priority": 1},
    {"id": "ID.RA-05", "category": "ID.RA", "function": "identify", "name_en": "Risk determined", "name_de": "Risiko bestimmt", "description_en": "Threats, vulnerabilities, likelihoods, and impacts are used to understand inherent risk", "weight": 12, "priority": 1},
    {"id": "ID.RA-06", "category": "ID.RA", "function": "identify", "name_en": "Risk responses chosen", "name_de": "Risikobehandlung gewählt", "description_en": "Risk responses are chosen, prioritized, planned, tracked, and communicated", "weight": 10, "priority": 1},
    {"id": "ID.RA-07", "category": "ID.RA", "function": "identify", "name_en": "Changes and exceptions managed", "name_de": "Änderungen und Ausnahmen verwaltet", "description_en": "Changes and exceptions are managed, assessed for risk impact, and recorded", "weight": 8, "priority": 2},

    # IDENTIFY - Improvement (ID.IM)
    {"id": "ID.IM-01", "category": "ID.IM", "function": "identify", "name_en": "Improvements identified", "name_de": "Verbesserungen identifiziert", "description_en": "Improvements are identified from evaluations", "weight": 10, "priority": 2},
    {"id": "ID.IM-02", "category": "ID.IM", "function": "identify", "name_en": "Improvements identified from tests", "name_de": "Verbesserungen aus Tests identifiziert", "description_en": "Improvements are identified from security tests and exercises", "weight": 10, "priority": 2},
    {"id": "ID.IM-03", "category": "ID.IM", "function": "identify", "name_en": "Improvements identified from incidents", "name_de": "Verbesserungen aus Vorfällen identifiziert", "description_en": "Improvements are identified from execution of operational processes and procedures", "weight": 10, "priority": 2},
    {"id": "ID.IM-04", "category": "ID.IM", "function": "identify", "name_en": "Incident lessons learned", "name_de": "Lessons Learned aus Vorfällen", "description_en": "Incident response plans incorporate lessons learned", "weight": 10, "priority": 1},

    # PROTECT - Identity Management (PR.AA)
    {"id": "PR.AA-01", "category": "PR.AA", "function": "protect", "name_en": "Identities and credentials managed", "name_de": "Identitäten und Anmeldeinformationen verwaltet", "description_en": "Identities and credentials for authorized users, services, and hardware are managed", "weight": 12, "priority": 1},
    {"id": "PR.AA-02", "category": "PR.AA", "function": "protect", "name_en": "Identities proofed and bound", "name_de": "Identitäten geprüft und gebunden", "description_en": "Identities are proofed and bound to credentials based on context of interactions", "weight": 10, "priority": 1},
    {"id": "PR.AA-03", "category": "PR.AA", "function": "protect", "name_en": "Users authenticated", "name_de": "Benutzer authentifiziert", "description_en": "Users, services, and hardware are authenticated", "weight": 12, "priority": 1},
    {"id": "PR.AA-04", "category": "PR.AA", "function": "protect", "name_en": "Identity assertions protected", "name_de": "Identitätsaussagen geschützt", "description_en": "Identity assertions are protected, conveyed, and verified", "weight": 8, "priority": 2},
    {"id": "PR.AA-05", "category": "PR.AA", "function": "protect", "name_en": "Access permissions managed", "name_de": "Zugriffsrechte verwaltet", "description_en": "Access permissions, entitlements, and authorizations are defined and managed", "weight": 12, "priority": 1},
    {"id": "PR.AA-06", "category": "PR.AA", "function": "protect", "name_en": "Physical access managed", "name_de": "Physischer Zugang verwaltet", "description_en": "Physical access to assets is managed, monitored, and enforced", "weight": 10, "priority": 1},

    # PROTECT - Awareness and Training (PR.AT)
    {"id": "PR.AT-01", "category": "PR.AT", "function": "protect", "name_en": "Awareness provided", "name_de": "Bewusstsein geschaffen", "description_en": "Personnel are provided awareness and training so they have the knowledge and skills", "weight": 12, "priority": 1},
    {"id": "PR.AT-02", "category": "PR.AT", "function": "protect", "name_en": "Privileged users trained", "name_de": "Privilegierte Benutzer geschult", "description_en": "Individuals in specialized roles are provided with awareness and training", "weight": 10, "priority": 1},

    # PROTECT - Data Security (PR.DS)
    {"id": "PR.DS-01", "category": "PR.DS", "function": "protect", "name_en": "Data-at-rest protected", "name_de": "Gespeicherte Daten geschützt", "description_en": "The confidentiality, integrity, and availability of data-at-rest are protected", "weight": 12, "priority": 1},
    {"id": "PR.DS-02", "category": "PR.DS", "function": "protect", "name_en": "Data-in-transit protected", "name_de": "Übertragene Daten geschützt", "description_en": "The confidentiality, integrity, and availability of data-in-transit are protected", "weight": 12, "priority": 1},
    {"id": "PR.DS-10", "category": "PR.DS", "function": "protect", "name_en": "Data-in-use protected", "name_de": "Genutzte Daten geschützt", "description_en": "The confidentiality, integrity, and availability of data-in-use are protected", "weight": 10, "priority": 1},
    {"id": "PR.DS-11", "category": "PR.DS", "function": "protect", "name_en": "Backups created and protected", "name_de": "Backups erstellt und geschützt", "description_en": "Backups of data are created, protected, maintained, and tested", "weight": 12, "priority": 1},

    # PROTECT - Platform Security (PR.PS)
    {"id": "PR.PS-01", "category": "PR.PS", "function": "protect", "name_en": "Configuration management practices", "name_de": "Konfigurationsmanagement-Praktiken", "description_en": "Configuration management practices are established and applied", "weight": 12, "priority": 1},
    {"id": "PR.PS-02", "category": "PR.PS", "function": "protect", "name_en": "Software maintained", "name_de": "Software gewartet", "description_en": "Software is maintained, replaced, and removed commensurate with risk", "weight": 10, "priority": 1},
    {"id": "PR.PS-03", "category": "PR.PS", "function": "protect", "name_en": "Hardware maintained", "name_de": "Hardware gewartet", "description_en": "Hardware is maintained, replaced, and removed commensurate with risk", "weight": 10, "priority": 1},
    {"id": "PR.PS-04", "category": "PR.PS", "function": "protect", "name_en": "Log records generated", "name_de": "Protokolle generiert", "description_en": "Log records are generated and made available for continuous monitoring", "weight": 12, "priority": 1},
    {"id": "PR.PS-05", "category": "PR.PS", "function": "protect", "name_en": "Unauthorized installation prevented", "name_de": "Unautorisierte Installation verhindert", "description_en": "Installation and execution of unauthorized software are prevented", "weight": 10, "priority": 1},
    {"id": "PR.PS-06", "category": "PR.PS", "function": "protect", "name_en": "Secure software development", "name_de": "Sichere Softwareentwicklung", "description_en": "Secure software development practices are integrated and their performance monitored", "weight": 10, "priority": 1},

    # PROTECT - Infrastructure Resilience (PR.IR)
    {"id": "PR.IR-01", "category": "PR.IR", "function": "protect", "name_en": "Networks and environments protected", "name_de": "Netzwerke und Umgebungen geschützt", "description_en": "Networks and environments are protected from unauthorized logical access", "weight": 12, "priority": 1},
    {"id": "PR.IR-02", "category": "PR.IR", "function": "protect", "name_en": "Network architecture managed", "name_de": "Netzwerkarchitektur verwaltet", "description_en": "The organization's technology assets are protected from environmental threats", "weight": 10, "priority": 2},
    {"id": "PR.IR-03", "category": "PR.IR", "function": "protect", "name_en": "Resilience mechanisms implemented", "name_de": "Resilienzmechanismen implementiert", "description_en": "Mechanisms are implemented to achieve resilience requirements in normal and adverse situations", "weight": 10, "priority": 1},
    {"id": "PR.IR-04", "category": "PR.IR", "function": "protect", "name_en": "Adequate capacity maintained", "name_de": "Ausreichende Kapazität aufrechterhalten", "description_en": "Adequate resource capacity to ensure availability is maintained", "weight": 8, "priority": 2},

    # DETECT - Continuous Monitoring (DE.CM)
    {"id": "DE.CM-01", "category": "DE.CM", "function": "detect", "name_en": "Networks monitored", "name_de": "Netzwerke überwacht", "description_en": "Networks and network services are monitored to find potentially adverse events", "weight": 12, "priority": 1},
    {"id": "DE.CM-02", "category": "DE.CM", "function": "detect", "name_en": "Physical environment monitored", "name_de": "Physische Umgebung überwacht", "description_en": "The physical environment is monitored to find potentially adverse events", "weight": 8, "priority": 2},
    {"id": "DE.CM-03", "category": "DE.CM", "function": "detect", "name_en": "Personnel activity monitored", "name_de": "Personalaktivitäten überwacht", "description_en": "Personnel activity and technology usage are monitored", "weight": 10, "priority": 1},
    {"id": "DE.CM-06", "category": "DE.CM", "function": "detect", "name_en": "External service provider activity monitored", "name_de": "Externe Dienstleister überwacht", "description_en": "External service provider activity and services are monitored", "weight": 10, "priority": 1},
    {"id": "DE.CM-09", "category": "DE.CM", "function": "detect", "name_en": "Computing hardware monitored", "name_de": "Computing-Hardware überwacht", "description_en": "Computing hardware and software, runtime environments, and their data are monitored", "weight": 12, "priority": 1},

    # DETECT - Adverse Event Analysis (DE.AE)
    {"id": "DE.AE-02", "category": "DE.AE", "function": "detect", "name_en": "Events analyzed", "name_de": "Ereignisse analysiert", "description_en": "Potentially adverse events are analyzed to better understand associated activities", "weight": 12, "priority": 1},
    {"id": "DE.AE-03", "category": "DE.AE", "function": "detect", "name_en": "Events correlated", "name_de": "Ereignisse korreliert", "description_en": "Information is correlated from multiple sources", "weight": 10, "priority": 1},
    {"id": "DE.AE-04", "category": "DE.AE", "function": "detect", "name_en": "Impact estimated", "name_de": "Auswirkung geschätzt", "description_en": "The estimated impact and scope of adverse events are understood", "weight": 10, "priority": 1},
    {"id": "DE.AE-06", "category": "DE.AE", "function": "detect", "name_en": "Incidents declared", "name_de": "Vorfälle deklariert", "description_en": "Information on adverse events is provided to authorized staff and tools", "weight": 10, "priority": 1},
    {"id": "DE.AE-07", "category": "DE.AE", "function": "detect", "name_en": "Threat intelligence integrated", "name_de": "Bedrohungsintelligenz integriert", "description_en": "Cyber threat intelligence and other contextual information are integrated into analysis", "weight": 10, "priority": 1},

    # RESPOND - Incident Management (RS.MA)
    {"id": "RS.MA-01", "category": "RS.MA", "function": "respond", "name_en": "Incident response plan executed", "name_de": "Incident-Response-Plan ausgeführt", "description_en": "The incident response plan is executed in coordination with relevant third parties", "weight": 12, "priority": 1},
    {"id": "RS.MA-02", "category": "RS.MA", "function": "respond", "name_en": "Incidents triaged", "name_de": "Vorfälle triagiert", "description_en": "Incident reports are triaged and validated", "weight": 12, "priority": 1},
    {"id": "RS.MA-03", "category": "RS.MA", "function": "respond", "name_en": "Incidents categorized", "name_de": "Vorfälle kategorisiert", "description_en": "Incidents are categorized and prioritized", "weight": 10, "priority": 1},
    {"id": "RS.MA-04", "category": "RS.MA", "function": "respond", "name_en": "Incidents escalated", "name_de": "Vorfälle eskaliert", "description_en": "Incidents are escalated or elevated as needed", "weight": 10, "priority": 1},
    {"id": "RS.MA-05", "category": "RS.MA", "function": "respond", "name_en": "Criteria for incident response", "name_de": "Kriterien für Incident Response", "description_en": "The criteria for initiating incident response are applied", "weight": 8, "priority": 2},

    # RESPOND - Incident Analysis (RS.AN)
    {"id": "RS.AN-03", "category": "RS.AN", "function": "respond", "name_en": "Root cause analysis performed", "name_de": "Ursachenanalyse durchgeführt", "description_en": "Analysis is performed to establish what has taken place during an incident", "weight": 12, "priority": 1},
    {"id": "RS.AN-06", "category": "RS.AN", "function": "respond", "name_en": "Incident scope determined", "name_de": "Vorfallumfang bestimmt", "description_en": "Actions performed during an investigation are recorded", "weight": 10, "priority": 1},
    {"id": "RS.AN-07", "category": "RS.AN", "function": "respond", "name_en": "Artifact collection", "name_de": "Artefaktsammlung", "description_en": "Incident data and metadata are collected and their integrity and provenance preserved", "weight": 10, "priority": 1},
    {"id": "RS.AN-08", "category": "RS.AN", "function": "respond", "name_en": "Incident forensics performed", "name_de": "Forensik durchgeführt", "description_en": "An incident's magnitude is estimated and validated", "weight": 10, "priority": 1},

    # RESPOND - Communication (RS.CO)
    {"id": "RS.CO-02", "category": "RS.CO", "function": "respond", "name_en": "Internal stakeholders notified", "name_de": "Interne Stakeholder benachrichtigt", "description_en": "Internal and external stakeholders are notified of incidents", "weight": 10, "priority": 1},
    {"id": "RS.CO-03", "category": "RS.CO", "function": "respond", "name_en": "Information shared", "name_de": "Informationen geteilt", "description_en": "Information is shared with designated internal and external stakeholders", "weight": 8, "priority": 2},

    # RESPOND - Mitigation (RS.MI)
    {"id": "RS.MI-01", "category": "RS.MI", "function": "respond", "name_en": "Incidents contained", "name_de": "Vorfälle eingedämmt", "description_en": "Incidents are contained", "weight": 12, "priority": 1},
    {"id": "RS.MI-02", "category": "RS.MI", "function": "respond", "name_en": "Incidents eradicated", "name_de": "Vorfälle beseitigt", "description_en": "Incidents are eradicated", "weight": 12, "priority": 1},

    # RECOVER - Recovery Plan (RC.RP)
    {"id": "RC.RP-01", "category": "RC.RP", "function": "recover", "name_en": "Recovery plan executed", "name_de": "Wiederherstellungsplan ausgeführt", "description_en": "The recovery portion of the incident response plan is executed", "weight": 12, "priority": 1},
    {"id": "RC.RP-02", "category": "RC.RP", "function": "recover", "name_en": "Recovery actions selected", "name_de": "Wiederherstellungsmaßnahmen ausgewählt", "description_en": "Recovery actions are selected, scoped, prioritized, and performed", "weight": 12, "priority": 1},
    {"id": "RC.RP-03", "category": "RC.RP", "function": "recover", "name_en": "Backup integrity verified", "name_de": "Backup-Integrität verifiziert", "description_en": "The integrity of backups and other restoration assets is verified", "weight": 12, "priority": 1},
    {"id": "RC.RP-04", "category": "RC.RP", "function": "recover", "name_en": "Critical functions considered", "name_de": "Kritische Funktionen berücksichtigt", "description_en": "Critical mission functions and cybersecurity risk management are considered", "weight": 10, "priority": 1},
    {"id": "RC.RP-05", "category": "RC.RP", "function": "recover", "name_en": "Integrity of restored assets verified", "name_de": "Integrität wiederhergestellter Assets verifiziert", "description_en": "The integrity of restored assets is verified, systems tested, and normal operations confirmed", "weight": 10, "priority": 1},
    {"id": "RC.RP-06", "category": "RC.RP", "function": "recover", "name_en": "Recovery declared", "name_de": "Wiederherstellung erklärt", "description_en": "The end of incident recovery is declared based on criteria", "weight": 8, "priority": 2},

    # RECOVER - Communication (RC.CO)
    {"id": "RC.CO-03", "category": "RC.CO", "function": "recover", "name_en": "Recovery activities communicated", "name_de": "Wiederherstellungsaktivitäten kommuniziert", "description_en": "Recovery activities and progress are communicated to stakeholders", "weight": 10, "priority": 1},
    {"id": "RC.CO-04", "category": "RC.CO", "function": "recover", "name_en": "Public updates shared", "name_de": "Öffentliche Updates geteilt", "description_en": "Public updates on incident recovery are shared using approved methods and messaging", "weight": 8, "priority": 2},
]


# =============================================================================
# Implementation Tiers Reference
# =============================================================================

NIST_TIERS = [
    {
        "tier": "tier_1",
        "name_en": "Partial",
        "name_de": "Teilweise",
        "description_en": "Risk management practices are not formalized. Risk is managed in an ad hoc and reactive manner.",
        "risk_management": "Ad hoc, reactive",
        "integrated_program": "Limited awareness",
        "external_participation": "Limited",
    },
    {
        "tier": "tier_2",
        "name_en": "Risk Informed",
        "name_de": "Risikoinformiert",
        "description_en": "Risk management practices are approved by management but may not be established organization-wide.",
        "risk_management": "Management approved",
        "integrated_program": "Awareness but informal sharing",
        "external_participation": "Organization aware of role",
    },
    {
        "tier": "tier_3",
        "name_en": "Repeatable",
        "name_de": "Wiederholbar",
        "description_en": "Risk management practices are formally approved and expressed as policy.",
        "risk_management": "Formal policy-based",
        "integrated_program": "Organization-wide awareness",
        "external_participation": "Active collaboration",
    },
    {
        "tier": "tier_4",
        "name_en": "Adaptive",
        "name_de": "Adaptiv",
        "description_en": "The organization adapts its practices based on lessons learned and predictive indicators.",
        "risk_management": "Continuous improvement",
        "integrated_program": "Continuous improvement culture",
        "external_participation": "Active, proactive sharing",
    },
]


# =============================================================================
# Database Models
# =============================================================================

class NISTAssessment(Base):
    """NIST CSF 2.0 Assessment."""

    __tablename__ = "nist_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=NISTAssessmentStatus.DRAFT.value)

    # Organization Profile
    organization_type = Column(String(50), nullable=True)
    organization_size = Column(String(50), nullable=True)
    employee_count = Column(Integer, nullable=True)
    industry_sector = Column(String(100), nullable=True)

    # Profile Configuration
    current_tier = Column(String(20), nullable=True)  # Current implementation tier
    target_tier = Column(String(20), nullable=True)   # Target implementation tier
    profile_type = Column(String(50), default="organizational")  # organizational, community, etc.

    # Scoring
    overall_score = Column(Float, default=0.0)
    function_scores = Column(JSON, default=dict)  # {"govern": 75.0, "identify": 80.0, ...}
    gaps_count = Column(Integer, default=0)
    critical_gaps_count = Column(Integer, default=0)

    # Metadata
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    responses = relationship("NISTSubcategoryResponse", back_populates="assessment", cascade="all, delete-orphan")


class NISTSubcategoryResponse(Base):
    """Response for a NIST CSF subcategory outcome."""

    __tablename__ = "nist_subcategory_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("nist_assessments.id", ondelete="CASCADE"), nullable=False)
    subcategory_id = Column(String(20), nullable=False)  # e.g., "GV.OC-01"
    function_id = Column(String(20), nullable=False)     # e.g., "govern"
    category_id = Column(String(20), nullable=False)     # e.g., "GV.OC"

    # Assessment
    status = Column(String(50), default=NISTOutcomeStatus.NOT_EVALUATED.value)
    implementation_level = Column(Integer, default=0)  # 0-100%

    # Current vs Target
    current_state = Column(String(50), nullable=True)
    target_state = Column(String(50), nullable=True)

    # Evidence and Notes
    evidence = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    gap_description = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)

    # Priority and Timeline
    priority = Column(Integer, default=2)  # 1=Critical, 2=High, 3=Medium, 4=Low
    due_date = Column(DateTime, nullable=True)
    responsible = Column(String(255), nullable=True)

    # Audit
    assessed_at = Column(DateTime, nullable=True)
    assessed_by = Column(String(36), nullable=True)

    # Relationships
    assessment = relationship("NISTAssessment", back_populates="responses")
