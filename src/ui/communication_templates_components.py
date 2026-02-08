"""
Communication Templates Components for ISORA.

Pre-defined templates for incident communication.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class TemplateCategory(str, Enum):
    INTERNAL = "internal"
    MANAGEMENT = "management"
    TECHNICAL = "technical"
    CUSTOMER = "customer"
    REGULATORY = "regulatory"
    PRESS = "press"
    PARTNER = "partner"


class TemplateLanguage(str, Enum):
    DE = "de"
    EN = "en"


@dataclass
class TemplateVariable:
    name: str
    description: str
    example: str
    required: bool = True


@dataclass
class CommunicationTemplate:
    id: str
    name: str
    category: TemplateCategory
    language: TemplateLanguage
    subject: str
    body: str
    variables: List[TemplateVariable]
    notes: str = ""
    when_to_use: str = ""
    recipients: List[str] = field(default_factory=list)


# Template definitions
TEMPLATES: Dict[str, CommunicationTemplate] = {}


def _init_templates():
    """Initialize all communication templates."""
    global TEMPLATES

    # ==================== GERMAN TEMPLATES ====================

    # Internal - First Alert
    TEMPLATES["de_internal_first_alert"] = CommunicationTemplate(
        id="de_internal_first_alert",
        name="Erste interne Alarmierung",
        category=TemplateCategory.INTERNAL,
        language=TemplateLanguage.DE,
        subject="[SICHERHEITSVORFALL] Erste Alarmierung - {{incident_title}}",
        body="""Prioritaet: {{priority}}
Datum/Zeit: {{datetime}}

SICHERHEITSVORFALL - ERSTE ALARMIERUNG

Ein Sicherheitsvorfall wurde erkannt und wird aktuell untersucht.

ZUSAMMENFASSUNG
---------------
Vorfallstyp: {{incident_type}}
Erkannt am: {{detection_time}}
Erkannt durch: {{detection_source}}
Betroffene Systeme: {{affected_systems}}
Aktuelle Phase: {{current_phase}}

ERSTE EINSCHAETZUNG
-------------------
{{initial_assessment}}

SOFORTMASSNAHMEN
----------------
{{immediate_actions}}

NAECHSTE SCHRITTE
-----------------
{{next_steps}}

KONTAKT
-------
Incident Commander: {{incident_commander}}
Erreichbar unter: {{contact_info}}

Bitte behandeln Sie diese Information vertraulich.
Weitere Updates folgen.

---
ISORA | Automatisch generiert""",
        variables=[
            TemplateVariable("incident_title", "Titel des Vorfalls", "Ransomware-Angriff auf Produktionsserver"),
            TemplateVariable("priority", "Prioritaet (KRITISCH/HOCH/MITTEL/NIEDRIG)", "KRITISCH"),
            TemplateVariable("datetime", "Aktuelles Datum und Uhrzeit", "2024-01-15 14:30 UTC"),
            TemplateVariable("incident_type", "Art des Vorfalls", "Ransomware"),
            TemplateVariable("detection_time", "Zeitpunkt der Erkennung", "2024-01-15 13:45 UTC"),
            TemplateVariable("detection_source", "Wie wurde der Vorfall erkannt", "EDR-Alert"),
            TemplateVariable("affected_systems", "Betroffene Systeme", "PROD-SRV-01, PROD-SRV-02"),
            TemplateVariable("current_phase", "Aktuelle IR-Phase", "Eindaemmung"),
            TemplateVariable("initial_assessment", "Erste Einschaetzung der Lage", "Ransomware wurde auf zwei Produktionsservern erkannt. Verschluesselung hat begonnen."),
            TemplateVariable("immediate_actions", "Bereits ergriffene Massnahmen", "- Server vom Netzwerk isoliert\n- Backup-Systeme gesichert"),
            TemplateVariable("next_steps", "Geplante naechste Schritte", "- Forensische Analyse\n- Ausmass der Verschluesselung ermitteln"),
            TemplateVariable("incident_commander", "Name des Incident Commanders", "Max Mustermann"),
            TemplateVariable("contact_info", "Kontaktinformationen", "+49 123 456789"),
        ],
        notes="Diese Vorlage fuer die erste interne Benachrichtigung verwenden, sobald ein Vorfall bestaetigt wurde.",
        when_to_use="Sofort nach Bestaetigung eines Sicherheitsvorfalls",
        recipients=["IT-Sicherheitsteam", "IT-Leitung", "CISO"],
    )

    # Management - Executive Briefing
    TEMPLATES["de_management_briefing"] = CommunicationTemplate(
        id="de_management_briefing",
        name="Management-Briefing",
        category=TemplateCategory.MANAGEMENT,
        language=TemplateLanguage.DE,
        subject="[VERTRAULICH] Sicherheitsvorfall - Management-Briefing",
        body="""MANAGEMENT-BRIEFING: SICHERHEITSVORFALL

Datum: {{datetime}}
Berichterstatter: {{reporter_name}}
Vertraulichkeitsstufe: VERTRAULICH

1. ZUSAMMENFASSUNG
------------------
{{executive_summary}}

2. GESCHAEFTSAUSWIRKUNGEN
-------------------------
Betroffene Geschaeftsprozesse: {{affected_processes}}
Geschaetzter Schaden: {{estimated_damage}}
Kundenauswirkung: {{customer_impact}}
Reputationsrisiko: {{reputation_risk}}

3. AKTUELLER STATUS
-------------------
Phase: {{current_phase}}
Fortschritt: {{progress_percent}}%
Naechster Meilenstein: {{next_milestone}}

4. RESSOURCENBEDARF
-------------------
{{resource_requirements}}

5. ENTSCHEIDUNGSBEDARF
----------------------
{{decisions_needed}}

6. KOMMUNIKATIONSSTATUS
-----------------------
Interne Kommunikation: {{internal_comm_status}}
Externe Kommunikation: {{external_comm_status}}
Behoerdenmeldung: {{regulatory_status}}

7. NAECHSTES UPDATE
-------------------
Geplant fuer: {{next_update_time}}

Bei Fragen wenden Sie sich an:
{{contact_info}}

---
Dieses Dokument ist vertraulich und nur fuer den internen Gebrauch bestimmt.""",
        variables=[
            TemplateVariable("datetime", "Datum und Uhrzeit", "15.01.2024, 16:00 Uhr"),
            TemplateVariable("reporter_name", "Name des Berichterstatters", "Dr. Anna Schmidt, CISO"),
            TemplateVariable("executive_summary", "Zusammenfassung fuer Management", "Am 15.01. wurde ein Ransomware-Angriff auf unsere Produktionsumgebung erkannt. Das IR-Team arbeitet an der Eindaemmung."),
            TemplateVariable("affected_processes", "Betroffene Geschaeftsprozesse", "Auftragsbearbeitung, Lagerverwaltung"),
            TemplateVariable("estimated_damage", "Geschaetzter Schaden", "50.000-100.000 EUR (vorlaeufig)"),
            TemplateVariable("customer_impact", "Auswirkungen auf Kunden", "Verzoegerungen bei Auftragsbestaetigung moeglich"),
            TemplateVariable("reputation_risk", "Reputationsrisiko", "Mittel - keine Kundendaten betroffen"),
            TemplateVariable("current_phase", "Aktuelle Phase", "Eindaemmung"),
            TemplateVariable("progress_percent", "Fortschritt in Prozent", "35"),
            TemplateVariable("next_milestone", "Naechster Meilenstein", "Vollstaendige Isolierung bis 18:00 Uhr"),
            TemplateVariable("resource_requirements", "Ressourcenbedarf", "- Externe Forensik-Unterstuetzung\n- Zusaetzliche Server-Kapazitaet"),
            TemplateVariable("decisions_needed", "Offene Entscheidungen", "- Genehmigung fuer externes Forensik-Team\n- Kommunikation an Kunden ja/nein"),
            TemplateVariable("internal_comm_status", "Status interne Kommunikation", "IT-Team informiert"),
            TemplateVariable("external_comm_status", "Status externe Kommunikation", "Noch nicht erfolgt"),
            TemplateVariable("regulatory_status", "Status Behoerdenmeldung", "In Vorbereitung (72h Frist)"),
            TemplateVariable("next_update_time", "Naechstes Update", "15.01.2024, 20:00 Uhr"),
            TemplateVariable("contact_info", "Kontaktinformationen", "CISO: +49 123 456789"),
        ],
        notes="Fuer regelmaessige Management-Updates waehrend eines Vorfalls verwenden.",
        when_to_use="Alle 4-6 Stunden bei kritischen Vorfaellen, taeglich bei anderen",
        recipients=["Geschaeftsfuehrung", "Vorstand", "Bereichsleiter"],
    )

    # Technical - Status Update
    TEMPLATES["de_technical_status"] = CommunicationTemplate(
        id="de_technical_status",
        name="Technisches Status-Update",
        category=TemplateCategory.TECHNICAL,
        language=TemplateLanguage.DE,
        subject="[IR-{{incident_id}}] Technisches Status-Update #{{update_number}}",
        body="""INCIDENT RESPONSE - TECHNISCHES STATUS-UPDATE

Incident-ID: {{incident_id}}
Update: #{{update_number}}
Zeitstempel: {{datetime}}
Autor: {{author}}

AKTUELLER STATUS
----------------
Phase: {{current_phase}}
Schweregrad: {{severity}}

SEIT LETZTEM UPDATE
-------------------
{{changes_since_last}}

TECHNISCHE DETAILS
------------------
Betroffene Systeme:
{{affected_systems_detail}}

IOCs (Indicators of Compromise):
{{iocs}}

Angriffsvektor:
{{attack_vector}}

DURCHGEFUEHRTE MASSNAHMEN
-------------------------
{{actions_taken}}

OFFENE AUFGABEN
---------------
{{open_tasks}}

BENOETIGTE UNTERSTUETZUNG
-------------------------
{{support_needed}}

NAECHSTE SCHRITTE
-----------------
{{next_steps}}

---
Technisches IR-Team
Naechstes Update: {{next_update}}""",
        variables=[
            TemplateVariable("incident_id", "Incident-ID", "INC-2024-0042"),
            TemplateVariable("update_number", "Update-Nummer", "3"),
            TemplateVariable("datetime", "Zeitstempel", "2024-01-15 18:30 UTC"),
            TemplateVariable("author", "Autor des Updates", "Thomas Mueller, Security Analyst"),
            TemplateVariable("current_phase", "Aktuelle Phase", "Analyse"),
            TemplateVariable("severity", "Schweregrad", "KRITISCH"),
            TemplateVariable("changes_since_last", "Aenderungen seit letztem Update", "- 3 weitere betroffene Server identifiziert\n- C2-Kommunikation blockiert\n- Memory Dumps erstellt"),
            TemplateVariable("affected_systems_detail", "Details zu betroffenen Systemen", "- PROD-SRV-01 (Windows Server 2019) - verschluesselt\n- PROD-SRV-02 (Windows Server 2019) - verschluesselt\n- PROD-SRV-03 (Windows Server 2019) - isoliert, nicht verschluesselt"),
            TemplateVariable("iocs", "Indicators of Compromise", "- SHA256: abc123...\n- C2-Domain: evil.example.com\n- IP: 192.168.1.100"),
            TemplateVariable("attack_vector", "Angriffsvektor", "Initiale Kompromittierung ueber Phishing-E-Mail mit Makro-Dokument"),
            TemplateVariable("actions_taken", "Durchgefuehrte Massnahmen", "- Netzwerk-Segmente isoliert\n- EDR-Vollscan gestartet\n- Firewall-Regeln aktualisiert"),
            TemplateVariable("open_tasks", "Offene Aufgaben", "- [ ] Forensische Analyse der Memory Dumps\n- [ ] Lateral Movement Timeline erstellen\n- [ ] Backup-Integritaet pruefen"),
            TemplateVariable("support_needed", "Benoetigte Unterstuetzung", "- Windows-Admin fuer Backup-Restore\n- Netzwerk-Team fuer Firewall-Analyse"),
            TemplateVariable("next_steps", "Naechste Schritte", "1. Memory-Analyse abschliessen\n2. Decryption-Moeglichkeiten pruefen\n3. Restore-Plan erstellen"),
            TemplateVariable("next_update", "Naechstes Update", "In 2 Stunden oder bei wesentlichen Aenderungen"),
        ],
        notes="Fuer regelmaessige technische Updates an das IR-Team und IT-Kollegen.",
        when_to_use="Alle 2-4 Stunden oder bei wesentlichen Erkenntnissen",
        recipients=["IR-Team", "IT-Administratoren", "SOC"],
    )

    # Customer Notification
    TEMPLATES["de_customer_notification"] = CommunicationTemplate(
        id="de_customer_notification",
        name="Kundenbenachrichtigung",
        category=TemplateCategory.CUSTOMER,
        language=TemplateLanguage.DE,
        subject="Wichtige Sicherheitsinformation",
        body="""Sehr geehrte Damen und Herren,

wir moechten Sie ueber einen Sicherheitsvorfall informieren, der moeglicherweise Auswirkungen auf Sie haben koennte.

WAS IST PASSIERT?
-----------------
{{incident_description}}

WELCHE DATEN SIND BETROFFEN?
----------------------------
{{affected_data}}

WAS TUN WIR?
------------
{{our_actions}}

WAS SOLLTEN SIE TUN?
--------------------
{{recommended_actions}}

WEITERE INFORMATIONEN
---------------------
Wir haben eine spezielle Informationsseite eingerichtet:
{{info_url}}

Bei Fragen erreichen Sie uns unter:
Telefon: {{hotline_phone}}
E-Mail: {{contact_email}}
Erreichbarkeit: {{availability}}

Wir bedauern die entstandenen Unannehmlichkeiten und arbeiten mit Hochdruck an der Loesung.

Mit freundlichen Gruessen

{{sender_name}}
{{sender_title}}
{{company_name}}""",
        variables=[
            TemplateVariable("incident_description", "Beschreibung des Vorfalls (kundenfreundlich)", "Am [Datum] haben wir ungewoehnliche Aktivitaeten in unseren Systemen festgestellt. Nach eingehender Untersuchung haben wir festgestellt, dass unbefugte Dritte Zugriff auf einen Teil unserer Systeme erlangt haben."),
            TemplateVariable("affected_data", "Welche Daten sind betroffen", "Nach aktuellem Kenntnisstand koennten folgende Daten betroffen sein:\n- Name und Kontaktdaten\n- [weitere Daten]"),
            TemplateVariable("our_actions", "Unsere Massnahmen", "- Sofortige Sicherung aller Systeme\n- Einschaltung externer Sicherheitsexperten\n- Benachrichtigung der zustaendigen Behoerden\n- Verstaerkung unserer Sicherheitsmassnahmen"),
            TemplateVariable("recommended_actions", "Empfohlene Massnahmen fuer Kunden", "- Aendern Sie Ihr Passwort bei unserem Service\n- Aktivieren Sie die Zwei-Faktor-Authentifizierung\n- Achten Sie auf verdaechtige E-Mails oder Anrufe"),
            TemplateVariable("info_url", "URL zur Informationsseite", "https://www.example.com/sicherheitsinfo"),
            TemplateVariable("hotline_phone", "Hotline-Nummer", "+49 800 123 4567 (kostenfrei)"),
            TemplateVariable("contact_email", "Kontakt-E-Mail", "sicherheit@example.com"),
            TemplateVariable("availability", "Erreichbarkeit der Hotline", "Mo-Fr 8-20 Uhr, Sa-So 10-16 Uhr"),
            TemplateVariable("sender_name", "Name des Absenders", "Dr. Max Mustermann"),
            TemplateVariable("sender_title", "Titel des Absenders", "Geschaeftsfuehrer"),
            TemplateVariable("company_name", "Firmenname", "Beispiel GmbH"),
        ],
        notes="WICHTIG: Vor dem Versand mit Rechtsabteilung und PR abstimmen!",
        when_to_use="Bei Datenschutzverletzungen mit Kundenbetroffenheit (DSGVO Art. 34)",
        recipients=["Betroffene Kunden"],
    )

    # BSI/Regulatory Notification
    TEMPLATES["de_bsi_notification"] = CommunicationTemplate(
        id="de_bsi_notification",
        name="BSI-Meldung (KRITIS)",
        category=TemplateCategory.REGULATORY,
        language=TemplateLanguage.DE,
        subject="Meldung gemaess 8b BSIG - {{company_name}}",
        body="""MELDUNG GEMAESS 8B BSIG

1. MELDENDE STELLE
------------------
Unternehmen: {{company_name}}
KRITIS-Sektor: {{kritis_sector}}
Ansprechpartner: {{contact_person}}
Telefon: {{contact_phone}}
E-Mail: {{contact_email}}

2. ART DER MELDUNG
------------------
[ ] Erstmeldung
[ ] Folgemeldung zu Meldung vom: {{previous_report_date}}
[ ] Abschlussmeldung

3. ZEITANGABEN
--------------
Erkennungszeitpunkt: {{detection_time}}
Meldezeitpunkt: {{report_time}}
Vorfall andauernd: {{ongoing}} (Ja/Nein)

4. BETROFFENE KRITISCHE DIENSTLEISTUNG
--------------------------------------
{{affected_service}}

5. VORFALLSBESCHREIBUNG
-----------------------
Art des Vorfalls: {{incident_type}}
Beschreibung: {{incident_description}}

6. AUSWIRKUNGEN
---------------
Auf kritische Dienstleistung: {{service_impact}}
Auf Versorgungssicherheit: {{supply_impact}}
Geschaetzte Betroffene: {{affected_count}}

7. URSACHE (falls bekannt)
--------------------------
{{root_cause}}

8. ERGRIFFENE MASSNAHMEN
------------------------
{{measures_taken}}

9. GEPLANTE MASSNAHMEN
----------------------
{{planned_measures}}

10. UNTERSTUETZUNGSBEDARF
-------------------------
{{support_needed}}

11. ANLAGEN
-----------
{{attachments}}

---
Diese Meldung erfolgt gemaess 8b Absatz 4 BSIG.
Erstellt: {{datetime}}""",
        variables=[
            TemplateVariable("company_name", "Unternehmensname", "Beispiel Energie GmbH"),
            TemplateVariable("kritis_sector", "KRITIS-Sektor", "Energie"),
            TemplateVariable("contact_person", "Ansprechpartner", "Dr. Max Mustermann, CISO"),
            TemplateVariable("contact_phone", "Telefon", "+49 123 456789"),
            TemplateVariable("contact_email", "E-Mail", "ciso@example.com"),
            TemplateVariable("previous_report_date", "Datum vorherige Meldung (bei Folgemeldung)", ""),
            TemplateVariable("detection_time", "Erkennungszeitpunkt", "15.01.2024, 13:45 Uhr"),
            TemplateVariable("report_time", "Meldezeitpunkt", "15.01.2024, 18:00 Uhr"),
            TemplateVariable("ongoing", "Vorfall andauernd", "Ja"),
            TemplateVariable("affected_service", "Betroffene kritische Dienstleistung", "Stromversorgung - Netzleittechnik"),
            TemplateVariable("incident_type", "Art des Vorfalls", "Ransomware-Angriff"),
            TemplateVariable("incident_description", "Beschreibung", "Ransomware-Infektion auf Systemen der Netzleittechnik. Verschluesselung von Dateien festgestellt."),
            TemplateVariable("service_impact", "Auswirkung auf Dienstleistung", "Aktuell keine Beeintraechtigung der Stromversorgung. Monitoring eingeschraenkt."),
            TemplateVariable("supply_impact", "Auswirkung auf Versorgung", "Keine unmittelbare Gefaehrdung"),
            TemplateVariable("affected_count", "Geschaetzte Betroffene", "Potentiell 50.000 Haushalte bei Eskalation"),
            TemplateVariable("root_cause", "Ursache", "Noch in Untersuchung. Vermutlich Phishing-Angriff."),
            TemplateVariable("measures_taken", "Ergriffene Massnahmen", "- Betroffene Systeme isoliert\n- Backup-Systeme aktiviert\n- Externes IR-Team beauftragt"),
            TemplateVariable("planned_measures", "Geplante Massnahmen", "- Forensische Analyse\n- Systemwiederherstellung aus Backup\n- Haertung der Systeme"),
            TemplateVariable("support_needed", "Unterstuetzungsbedarf", "Aktuell kein Unterstuetzungsbedarf durch BSI"),
            TemplateVariable("attachments", "Anlagen", "- IOC-Liste (separat verschluesselt)"),
            TemplateVariable("datetime", "Erstellungszeitpunkt", "15.01.2024, 18:00 Uhr"),
        ],
        notes="KRITIS-Meldung innerhalb von 24 Stunden nach Erkennung erforderlich!",
        when_to_use="Bei IT-Stoerungen mit Auswirkung auf kritische Dienstleistungen",
        recipients=["BSI", "Aufsichtsbehoerde"],
    )

    # Press Statement
    TEMPLATES["de_press_statement"] = CommunicationTemplate(
        id="de_press_statement",
        name="Pressemitteilung",
        category=TemplateCategory.PRESS,
        language=TemplateLanguage.DE,
        subject="Pressemitteilung: {{headline}}",
        body="""PRESSEMITTEILUNG

{{company_name}}
{{location}}, {{date}}

{{headline}}

{{lead_paragraph}}

{{main_body}}

UNSERE MASSNAHMEN
-----------------
{{our_measures}}

FUER KUNDEN
-----------
{{customer_info}}

KONTAKT FUER MEDIENANFRAGEN
---------------------------
{{press_contact_name}}
{{press_contact_title}}
Telefon: {{press_contact_phone}}
E-Mail: {{press_contact_email}}

---
Ueber {{company_name}}:
{{company_boilerplate}}""",
        variables=[
            TemplateVariable("company_name", "Firmenname", "Beispiel AG"),
            TemplateVariable("location", "Ort", "Muenchen"),
            TemplateVariable("date", "Datum", "15. Januar 2024"),
            TemplateVariable("headline", "Ueberschrift", "Beispiel AG informiert ueber Cyber-Sicherheitsvorfall"),
            TemplateVariable("lead_paragraph", "Einleitungsabsatz", "Die Beispiel AG wurde Ziel eines Cyber-Angriffs. Das Unternehmen hat umgehend Massnahmen ergriffen und arbeitet eng mit Sicherheitsbehoerden zusammen."),
            TemplateVariable("main_body", "Haupttext", "[Detaillierte, aber kontrollierte Informationen zum Vorfall]"),
            TemplateVariable("our_measures", "Unsere Massnahmen", "- Sofortige Einschaltung von IT-Sicherheitsexperten\n- Enge Zusammenarbeit mit Behoerden\n- Umfassende Untersuchung eingeleitet"),
            TemplateVariable("customer_info", "Information fuer Kunden", "Kunden koennen sich bei Fragen an unsere Hotline wenden: [Nummer]"),
            TemplateVariable("press_contact_name", "Pressekontakt Name", "Maria Beispiel"),
            TemplateVariable("press_contact_title", "Pressekontakt Titel", "Leiterin Unternehmenskommunikation"),
            TemplateVariable("press_contact_phone", "Pressekontakt Telefon", "+49 89 123456"),
            TemplateVariable("press_contact_email", "Pressekontakt E-Mail", "presse@example.com"),
            TemplateVariable("company_boilerplate", "Unternehmenstext", "[Standardtext ueber das Unternehmen]"),
        ],
        notes="WICHTIG: Vor Veroeffentlichung Freigabe durch GF und Rechtsabteilung erforderlich!",
        when_to_use="Bei oeffentlich bekannt gewordenen Vorfaellen",
        recipients=["Medien", "Oeffentlichkeit"],
    )

    # Partner Notification
    TEMPLATES["de_partner_notification"] = CommunicationTemplate(
        id="de_partner_notification",
        name="Partner-/Lieferantenbenachrichtigung",
        category=TemplateCategory.PARTNER,
        language=TemplateLanguage.DE,
        subject="[Vertraulich] Sicherheitsinformation - {{company_name}}",
        body="""VERTRAULICHE SICHERHEITSINFORMATION

An: {{partner_name}}
Von: {{company_name}}
Datum: {{date}}

Sehr geehrte Geschaeftspartner,

im Rahmen unserer vertrauensvollen Zusammenarbeit moechten wir Sie ueber einen Sicherheitsvorfall in unserem Unternehmen informieren.

HINTERGRUND
-----------
{{incident_background}}

MOEGLICHE AUSWIRKUNGEN AUF SIE
------------------------------
{{potential_impact}}

EMPFOHLENE MASSNAHMEN
---------------------
{{recommended_actions}}

UNSERE MASSNAHMEN
-----------------
{{our_actions}}

WEITERE KOMMUNIKATION
---------------------
{{communication_plan}}

Bei Fragen steht Ihnen {{contact_name}} unter {{contact_info}} zur Verfuegung.

Wir bitten Sie, diese Information vertraulich zu behandeln.

Mit freundlichen Gruessen

{{sender_name}}
{{sender_title}}
{{company_name}}""",
        variables=[
            TemplateVariable("partner_name", "Name des Partners", "Partner GmbH"),
            TemplateVariable("company_name", "Eigener Firmenname", "Beispiel AG"),
            TemplateVariable("date", "Datum", "15. Januar 2024"),
            TemplateVariable("incident_background", "Hintergrund zum Vorfall", "Am [Datum] haben wir einen Sicherheitsvorfall in unseren IT-Systemen festgestellt. [Weitere Details]"),
            TemplateVariable("potential_impact", "Moegliche Auswirkungen auf Partner", "- Gemeinsam genutzte Systeme/Schnittstellen\n- Ausgetauschte Zugangsdaten\n- [Weitere Punkte]"),
            TemplateVariable("recommended_actions", "Empfohlene Massnahmen", "- Ueberpruefen Sie Zugangsdaten fuer unsere Systeme\n- Achten Sie auf verdaechtige Aktivitaeten\n- Kontaktieren Sie uns bei Auffaelligkeiten"),
            TemplateVariable("our_actions", "Unsere Massnahmen", "- Externe Sicherheitsexperten eingeschaltet\n- Betroffene Systeme isoliert\n- Umfassende Untersuchung eingeleitet"),
            TemplateVariable("communication_plan", "Weitere Kommunikation", "Wir werden Sie ueber wesentliche Entwicklungen informieren."),
            TemplateVariable("contact_name", "Kontaktperson", "Max Mustermann"),
            TemplateVariable("contact_info", "Kontaktinformation", "+49 123 456789 / max@example.com"),
            TemplateVariable("sender_name", "Absendername", "Dr. Anna Schmidt"),
            TemplateVariable("sender_title", "Absendertitel", "CISO"),
        ],
        notes="Bei Supply-Chain-Vorfaellen besonders wichtig. NDA beachten!",
        when_to_use="Wenn Partner von Vorfall betroffen sein koennten",
        recipients=["Geschaeftspartner", "Lieferanten", "Dienstleister"],
    )

    # ==================== ENGLISH TEMPLATES ====================

    # Internal - First Alert (EN)
    TEMPLATES["en_internal_first_alert"] = CommunicationTemplate(
        id="en_internal_first_alert",
        name="Initial Internal Alert",
        category=TemplateCategory.INTERNAL,
        language=TemplateLanguage.EN,
        subject="[SECURITY INCIDENT] Initial Alert - {{incident_title}}",
        body="""Priority: {{priority}}
Date/Time: {{datetime}}

SECURITY INCIDENT - INITIAL ALERT

A security incident has been detected and is currently under investigation.

SUMMARY
-------
Incident Type: {{incident_type}}
Detected: {{detection_time}}
Detection Source: {{detection_source}}
Affected Systems: {{affected_systems}}
Current Phase: {{current_phase}}

INITIAL ASSESSMENT
------------------
{{initial_assessment}}

IMMEDIATE ACTIONS
-----------------
{{immediate_actions}}

NEXT STEPS
----------
{{next_steps}}

CONTACT
-------
Incident Commander: {{incident_commander}}
Reachable at: {{contact_info}}

Please treat this information as confidential.
Further updates will follow.

---
ISORA | Auto-generated""",
        variables=[
            TemplateVariable("incident_title", "Incident title", "Ransomware Attack on Production Server"),
            TemplateVariable("priority", "Priority (CRITICAL/HIGH/MEDIUM/LOW)", "CRITICAL"),
            TemplateVariable("datetime", "Current date and time", "2024-01-15 14:30 UTC"),
            TemplateVariable("incident_type", "Type of incident", "Ransomware"),
            TemplateVariable("detection_time", "Time of detection", "2024-01-15 13:45 UTC"),
            TemplateVariable("detection_source", "How was the incident detected", "EDR Alert"),
            TemplateVariable("affected_systems", "Affected systems", "PROD-SRV-01, PROD-SRV-02"),
            TemplateVariable("current_phase", "Current IR phase", "Containment"),
            TemplateVariable("initial_assessment", "Initial situation assessment", "Ransomware detected on two production servers. Encryption has begun."),
            TemplateVariable("immediate_actions", "Actions already taken", "- Servers isolated from network\n- Backup systems secured"),
            TemplateVariable("next_steps", "Planned next steps", "- Forensic analysis\n- Determine encryption scope"),
            TemplateVariable("incident_commander", "Incident Commander name", "John Smith"),
            TemplateVariable("contact_info", "Contact information", "+1 555 123 4567"),
        ],
        notes="Use this template for initial internal notification once an incident is confirmed.",
        when_to_use="Immediately after confirming a security incident",
        recipients=["IT Security Team", "IT Leadership", "CISO"],
    )

    # Customer Notification (EN)
    TEMPLATES["en_customer_notification"] = CommunicationTemplate(
        id="en_customer_notification",
        name="Customer Notification",
        category=TemplateCategory.CUSTOMER,
        language=TemplateLanguage.EN,
        subject="Important Security Notice",
        body="""Dear Customer,

We are writing to inform you about a security incident that may have affected your data.

WHAT HAPPENED?
--------------
{{incident_description}}

WHAT DATA WAS INVOLVED?
-----------------------
{{affected_data}}

WHAT ARE WE DOING?
------------------
{{our_actions}}

WHAT SHOULD YOU DO?
-------------------
{{recommended_actions}}

MORE INFORMATION
----------------
We have set up a dedicated information page:
{{info_url}}

For questions, please contact us:
Phone: {{hotline_phone}}
Email: {{contact_email}}
Hours: {{availability}}

We sincerely apologize for any inconvenience and are working diligently to resolve this matter.

Sincerely,

{{sender_name}}
{{sender_title}}
{{company_name}}""",
        variables=[
            TemplateVariable("incident_description", "Description of incident (customer-friendly)", "On [date], we detected unusual activity in our systems. After investigation, we determined that unauthorized parties gained access to a portion of our systems."),
            TemplateVariable("affected_data", "What data was affected", "Based on our investigation, the following data may have been affected:\n- Name and contact information\n- [other data]"),
            TemplateVariable("our_actions", "Our actions", "- Immediately secured all systems\n- Engaged external security experts\n- Notified relevant authorities\n- Enhanced our security measures"),
            TemplateVariable("recommended_actions", "Recommended actions for customers", "- Change your password for our service\n- Enable two-factor authentication\n- Watch for suspicious emails or calls"),
            TemplateVariable("info_url", "Information page URL", "https://www.example.com/securityinfo"),
            TemplateVariable("hotline_phone", "Hotline number", "+1 800 123 4567 (toll-free)"),
            TemplateVariable("contact_email", "Contact email", "security@example.com"),
            TemplateVariable("availability", "Hotline availability", "Mon-Fri 8am-8pm, Sat-Sun 10am-4pm"),
            TemplateVariable("sender_name", "Sender name", "John Smith"),
            TemplateVariable("sender_title", "Sender title", "Chief Executive Officer"),
            TemplateVariable("company_name", "Company name", "Example Corp"),
        ],
        notes="IMPORTANT: Coordinate with Legal and PR before sending!",
        when_to_use="For data breaches affecting customers (GDPR Art. 34 equivalent)",
        recipients=["Affected customers"],
    )


# Initialize templates on module load
_init_templates()


def get_category_labels() -> Dict[TemplateCategory, str]:
    """Get display labels for template categories."""
    return {
        TemplateCategory.INTERNAL: "Intern",
        TemplateCategory.MANAGEMENT: "Management",
        TemplateCategory.TECHNICAL: "Technisch",
        TemplateCategory.CUSTOMER: "Kunden",
        TemplateCategory.REGULATORY: "Behoerden",
        TemplateCategory.PRESS: "Presse",
        TemplateCategory.PARTNER: "Partner",
    }


def render_communication_templates(lang: str = "de") -> None:
    """Render the communication templates interface."""
    st.header("Communication Templates")
    st.caption("Vorlagen fuer Incident-Kommunikation")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        category_labels = get_category_labels()
        selected_category = st.selectbox(
            "Kategorie",
            options=["Alle"] + list(category_labels.values()),
        )

    with col2:
        selected_lang = st.selectbox(
            "Sprache",
            options=["Deutsch", "English"],
            index=0 if lang == "de" else 1,
        )
        template_lang = TemplateLanguage.DE if selected_lang == "Deutsch" else TemplateLanguage.EN

    st.divider()

    # Filter templates
    filtered_templates = []
    for template in TEMPLATES.values():
        # Language filter
        if template.language != template_lang:
            continue

        # Category filter
        if selected_category != "Alle":
            cat_label = category_labels.get(template.category, "")
            if cat_label != selected_category:
                continue

        filtered_templates.append(template)

    if not filtered_templates:
        st.info("Keine Vorlagen fuer diese Auswahl verfuegbar.")
        return

    # Template selection
    template_names = [t.name for t in filtered_templates]
    selected_name = st.selectbox(
        "Vorlage waehlen",
        options=template_names,
    )

    selected_template = None
    for t in filtered_templates:
        if t.name == selected_name:
            selected_template = t
            break

    if not selected_template:
        return

    st.divider()

    # Template info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Kategorie", category_labels.get(selected_template.category, ""))
    with col2:
        st.metric("Variablen", len(selected_template.variables))
    with col3:
        st.metric("Empfaenger", len(selected_template.recipients))

    if selected_template.when_to_use:
        st.info(f"**Verwendung:** {selected_template.when_to_use}")

    if selected_template.notes:
        st.warning(f"**Hinweis:** {selected_template.notes}")

    st.divider()

    # Variable inputs
    st.subheader("Variablen ausfuellen")

    # Initialize session state for variables
    var_key = f"template_vars_{selected_template.id}"
    if var_key not in st.session_state:
        st.session_state[var_key] = {}

    var_values = st.session_state[var_key]

    # Create input fields for each variable
    for var in selected_template.variables:
        help_text = f"{var.description}. Beispiel: {var.example}"
        required_marker = " *" if var.required else ""

        # Use text_area for longer content
        if any(keyword in var.name.lower() for keyword in ["description", "summary", "body", "actions", "steps", "details"]):
            var_values[var.name] = st.text_area(
                f"{var.name}{required_marker}",
                value=var_values.get(var.name, ""),
                help=help_text,
                height=100,
            )
        else:
            var_values[var.name] = st.text_input(
                f"{var.name}{required_marker}",
                value=var_values.get(var.name, ""),
                help=help_text,
            )

    st.session_state[var_key] = var_values

    st.divider()

    # Generate filled template
    st.subheader("Vorschau")

    filled_subject = _fill_template(selected_template.subject, var_values)
    filled_body = _fill_template(selected_template.body, var_values)

    # Show preview
    st.markdown(f"**Betreff:** {filled_subject}")
    st.text_area(
        "Inhalt",
        value=filled_body,
        height=400,
        disabled=True,
    )

    st.divider()

    # Export options
    st.subheader("Export")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Copy to clipboard (download as txt)
        st.download_button(
            label="Als Text",
            data=f"Betreff: {filled_subject}\n\n{filled_body}",
            file_name=f"template_{selected_template.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        # HTML format
        html_content = _generate_html_template(selected_template, filled_subject, filled_body)
        st.download_button(
            label="Als HTML",
            data=html_content,
            file_name=f"template_{selected_template.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True,
        )

    with col3:
        # PDF format
        if FPDF_AVAILABLE:
            pdf_content = _generate_pdf_template(selected_template, filled_subject, filled_body)
            st.download_button(
                label="Als PDF",
                data=pdf_content,
                file_name=f"template_{selected_template.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("PDF (n/a)", disabled=True, use_container_width=True)

    with col4:
        # JSON with all data
        json_content = _generate_json_template(selected_template, var_values, filled_subject, filled_body)
        st.download_button(
            label="Als JSON",
            data=json_content,
            file_name=f"template_{selected_template.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    # Recipients reminder
    if selected_template.recipients:
        st.divider()
        st.subheader("Empfaenger")
        st.markdown("Diese Vorlage ist vorgesehen fuer:")
        for recipient in selected_template.recipients:
            st.markdown(f"- {recipient}")


def _fill_template(template_text: str, variables: Dict[str, str]) -> str:
    """Fill template with variable values."""
    result = template_text
    for var_name, var_value in variables.items():
        placeholder = "{{" + var_name + "}}"
        result = result.replace(placeholder, var_value if var_value else f"[{var_name}]")
    return result


def _generate_html_template(template: CommunicationTemplate, subject: str, body: str) -> str:
    """Generate HTML version of filled template."""
    # Escape HTML characters in body and convert newlines
    body_html = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body_html = body_html.replace("\n", "<br>\n")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
        .subject {{ font-size: 18px; font-weight: bold; }}
        .meta {{ color: #666; font-size: 12px; margin-top: 5px; }}
        .body {{ white-space: pre-wrap; font-family: inherit; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="subject">{subject}</div>
        <div class="meta">Vorlage: {template.name} | Kategorie: {template.category.value} | Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    <div class="body">{body_html}</div>
    <div class="footer">
        Generiert mit ISORA
    </div>
</body>
</html>"""
    return html


def _generate_pdf_template(template: CommunicationTemplate, subject: str, body: str) -> bytes:
    """Generate PDF version of filled template."""
    if not FPDF_AVAILABLE:
        return b""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    # Subject - truncate if too long
    pdf.set_font("Helvetica", "B", 14)
    subject_text = f"Betreff: {subject}"
    if len(subject_text) > 80:
        subject_text = subject_text[:77] + "..."
    pdf.cell(0, 8, subject_text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Metadata
    pdf.set_font("Helvetica", "I", 9)
    meta_text = f"Vorlage: {template.name} | Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    pdf.cell(0, 5, meta_text[:85], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Body - process line by line with safe truncation
    pdf.set_font("Helvetica", "", 10)
    max_line_len = 85

    for line in body.split("\n"):
        line = line.rstrip()

        if not line:
            pdf.ln(3)
            continue

        # Check if line is a header
        is_header = line.strip().isupper() or line.strip().endswith("---") or line.strip().startswith("---")

        if is_header:
            pdf.set_font("Helvetica", "B", 10)
            clean_line = line.rstrip("-").strip()
            if len(clean_line) > max_line_len:
                clean_line = clean_line[:max_line_len-3] + "..."
            pdf.cell(0, 5, clean_line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
        else:
            # Regular line - truncate if needed
            if len(line) > max_line_len:
                pdf.cell(0, 5, line[:max_line_len-3] + "...", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Generiert mit ISORA", align="C")

    return bytes(pdf.output())


def _generate_json_template(template: CommunicationTemplate, variables: Dict[str, str], subject: str, body: str) -> str:
    """Generate JSON export of template and filled content."""
    data = {
        "generated": datetime.now().isoformat(),
        "template": {
            "id": template.id,
            "name": template.name,
            "category": template.category.value,
            "language": template.language.value,
        },
        "variables": variables,
        "filled_content": {
            "subject": subject,
            "body": body,
        },
        "recipients": template.recipients,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
