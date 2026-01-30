"""
Playbook Generator Components for IR Companion.

Generates automated incident response playbooks based on incident type.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from src.utils.translations import t

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class IncidentType(str, Enum):
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    DDOS = "ddos"
    INSIDER_THREAT = "insider_threat"
    MALWARE = "malware"
    ACCOUNT_COMPROMISE = "account_compromise"
    WEB_APPLICATION = "web_application"
    SUPPLY_CHAIN = "supply_chain"
    APT = "apt"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PlaybookStep:
    id: str
    title: str
    description: str
    actions: List[str]
    tools: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    notes: str = ""
    time_estimate: str = ""
    responsible: str = ""
    completed: bool = False


@dataclass
class PlaybookPhase:
    name: str
    description: str
    steps: List[PlaybookStep]
    order: int


@dataclass
class Playbook:
    incident_type: IncidentType
    title: str
    description: str
    severity: Severity
    phases: List[PlaybookPhase]
    compliance_refs: List[str] = field(default_factory=list)
    communication_required: List[str] = field(default_factory=list)
    escalation_criteria: List[str] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)


# Playbook definitions
PLAYBOOKS: Dict[IncidentType, Playbook] = {}


def _init_playbooks():
    """Initialize all playbook templates."""
    global PLAYBOOKS

    # Ransomware Playbook
    PLAYBOOKS[IncidentType.RANSOMWARE] = Playbook(
        incident_type=IncidentType.RANSOMWARE,
        title="Ransomware Incident Response",
        description="Playbook fuer die Reaktion auf Ransomware-Angriffe. Umfasst Isolierung, Analyse, Wiederherstellung und Praevention.",
        severity=Severity.CRITICAL,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Erste Erkennung und Bewertung des Ransomware-Vorfalls",
                order=1,
                steps=[
                    PlaybookStep(
                        id="R-D1",
                        title="Ransomware-Indikatoren identifizieren",
                        description="Typische Anzeichen einer Ransomware-Infektion erkennen",
                        actions=[
                            "Verschluesselte Dateien mit ungewoehnlichen Endungen pruefen",
                            "Ransom Notes (Erpresserbriefe) sichern",
                            "Ungewoehnliche Prozesse im Task Manager identifizieren",
                            "Netzwerkverbindungen zu C2-Servern pruefen",
                        ],
                        tools=["Process Explorer", "Autoruns", "TCPView", "Wireshark"],
                        artifacts=["Ransom Note", "Verschluesselte Dateien-Samples", "Prozessliste"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="R-D2",
                        title="Ausmass bestimmen",
                        description="Umfang der Infektion ermitteln",
                        actions=[
                            "Betroffene Systeme identifizieren",
                            "Betroffene Netzwerksegmente dokumentieren",
                            "Kritische Systeme priorisieren",
                            "Backup-Status pruefen",
                        ],
                        tools=["Netzwerk-Scanner", "EDR-Konsole", "SIEM"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="R-D3",
                        title="Ransomware-Variante identifizieren",
                        description="Spezifische Ransomware-Familie bestimmen",
                        actions=[
                            "Hash der Ransomware-Executable ermitteln",
                            "Ransom Note analysieren",
                            "ID Ransomware / No More Ransom pruefen",
                            "Bekannte Decryption-Tools recherchieren",
                        ],
                        tools=["ID Ransomware", "VirusTotal", "Any.Run", "Hybrid Analysis"],
                        time_estimate="15-30 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Sofortige Massnahmen zur Begrenzung der Ausbreitung",
                order=2,
                steps=[
                    PlaybookStep(
                        id="R-C1",
                        title="Netzwerk-Isolierung",
                        description="Betroffene Systeme vom Netzwerk trennen",
                        actions=[
                            "Infizierte Systeme vom Netzwerk trennen (Kabel/WLAN)",
                            "Netzwerksegmente isolieren",
                            "VPN-Zugaenge temporaer sperren",
                            "Firewall-Regeln verschaerfen",
                        ],
                        tools=["Firewall", "Switch-Konsole", "NAC"],
                        notes="WICHTIG: Systeme NICHT herunterfahren - forensische Daten koennten verloren gehen",
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="R-C2",
                        title="Backup-Sicherung",
                        description="Backups vor Verschluesselung schuetzen",
                        actions=[
                            "Backup-Systeme isolieren",
                            "Offline-Backups verifizieren",
                            "Cloud-Backup-Sync pausieren",
                            "Backup-Integritaet pruefen",
                        ],
                        tools=["Backup-Software", "Offline-Storage"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="R-C3",
                        title="Credentials sperren",
                        description="Kompromittierte Zugangsdaten deaktivieren",
                        actions=[
                            "Admin-Passwoerter aendern",
                            "Service-Accounts pruefen und zuruecksetzen",
                            "Kerberos-Tickets invalidieren",
                            "MFA erzwingen",
                        ],
                        tools=["Active Directory", "IAM-System", "Password Manager"],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse & Investigation",
                description="Detaillierte forensische Untersuchung",
                order=3,
                steps=[
                    PlaybookStep(
                        id="R-A1",
                        title="Forensische Sicherung",
                        description="Beweismaterial forensisch sichern",
                        actions=[
                            "Memory Dump erstellen",
                            "Disk Images anfertigen",
                            "Log-Dateien sichern (Event Logs, Security Logs)",
                            "Netzwerk-Captures sichern",
                        ],
                        tools=["FTK Imager", "Volatility", "KAPE", "Velociraptor"],
                        artifacts=["Memory Dumps", "Disk Images", "Log Files"],
                        time_estimate="2-4 h",
                    ),
                    PlaybookStep(
                        id="R-A2",
                        title="Angriffsvektor ermitteln",
                        description="Initialen Zugangsweg identifizieren",
                        actions=[
                            "E-Mail-Logs auf Phishing pruefen",
                            "RDP/VPN-Logs analysieren",
                            "Exploit-Spuren suchen",
                            "Zeitlinie der Ereignisse erstellen",
                        ],
                        tools=["SIEM", "E-Mail Gateway Logs", "EDR"],
                        time_estimate="2-4 h",
                    ),
                    PlaybookStep(
                        id="R-A3",
                        title="Lateral Movement analysieren",
                        description="Ausbreitung im Netzwerk nachvollziehen",
                        actions=[
                            "RDP-Verbindungen analysieren",
                            "SMB-Zugriffe pruefen",
                            "PsExec/WMI-Nutzung identifizieren",
                            "Kompromittierte Accounts ermitteln",
                        ],
                        tools=["BloodHound", "Event Log Analyzer", "Chainsaw"],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Beseitigung",
                description="Ransomware und Backdoors entfernen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="R-E1",
                        title="Malware entfernen",
                        description="Ransomware und zugehoerige Komponenten beseitigen",
                        actions=[
                            "Ransomware-Prozesse beenden",
                            "Persistenz-Mechanismen entfernen",
                            "Scheduled Tasks pruefen",
                            "Registry-Eintraege bereinigen",
                        ],
                        tools=["EDR", "Autoruns", "Process Explorer"],
                        time_estimate="1-2 h pro System",
                    ),
                    PlaybookStep(
                        id="R-E2",
                        title="Backdoors entfernen",
                        description="Zusaetzliche Hintertüren beseitigen",
                        actions=[
                            "Web Shells suchen und entfernen",
                            "Neue Admin-Accounts pruefen",
                            "Firewall-Regeln pruefen",
                            "Remote Access Tools entfernen",
                        ],
                        tools=["YARA", "Loki Scanner", "Thor"],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Systeme wiederherstellen und Betrieb aufnehmen",
                order=5,
                steps=[
                    PlaybookStep(
                        id="R-R1",
                        title="Systeme wiederherstellen",
                        description="Betroffene Systeme aus Backup wiederherstellen",
                        actions=[
                            "Priorisierte Systeme zuerst wiederherstellen",
                            "Backup-Integritaet vor Restore verifizieren",
                            "Clean OS Images verwenden",
                            "Patches vor Netzwerk-Reconnect installieren",
                        ],
                        tools=["Backup-Software", "Deployment-Tools"],
                        time_estimate="Variable",
                    ),
                    PlaybookStep(
                        id="R-R2",
                        title="Monitoring intensivieren",
                        description="Erhoehte Ueberwachung nach Wiederherstellung",
                        actions=[
                            "EDR auf allen Systemen aktivieren",
                            "SIEM-Alerts verschaerfen",
                            "Netzwerk-Monitoring intensivieren",
                            "24/7-Ueberwachung einrichten",
                        ],
                        tools=["EDR", "SIEM", "NDR"],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung und Verbesserungen",
                order=6,
                steps=[
                    PlaybookStep(
                        id="R-P1",
                        title="Lessons Learned",
                        description="Erkenntnisse dokumentieren und teilen",
                        actions=[
                            "Timeline des Vorfalls dokumentieren",
                            "Root Cause Analysis durchfuehren",
                            "Verbesserungsmassnahmen identifizieren",
                            "Lessons Learned Meeting durchfuehren",
                        ],
                        time_estimate="2-4 h",
                    ),
                    PlaybookStep(
                        id="R-P2",
                        title="Sicherheitsverbesserungen",
                        description="Praeventive Massnahmen implementieren",
                        actions=[
                            "Backup-Strategie ueberpruefen (3-2-1 Regel)",
                            "Segmentierung verbessern",
                            "Mitarbeiter-Awareness schulen",
                            "Incident Response Plan aktualisieren",
                        ],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
        ],
        compliance_refs=["BSIG 8b", "DSGVO Art. 33/34", "NIS2 Art. 23", "ISO 27001 A.16"],
        communication_required=[
            "Management (sofort)",
            "IT-Sicherheitsbeauftragter",
            "Datenschutzbeauftragter (bei personenbezogenen Daten)",
            "BSI (bei KRITIS innerhalb 24h)",
            "Betroffene Kunden (bei Datenleck)",
            "Strafverfolgungsbehoerden",
            "Cyber-Versicherung",
        ],
        escalation_criteria=[
            "Mehr als 10 Systeme betroffen",
            "Kritische Geschaeftsprozesse unterbrochen",
            "Personenbezogene Daten betroffen",
            "Loesegeld-Forderung erhalten",
            "Backup-Systeme kompromittiert",
        ],
        resources_needed=[
            "Forensik-Experte",
            "Malware-Analyst",
            "Netzwerk-Administrator",
            "System-Administratoren",
            "Kommunikations-Team",
            "Rechtsbeistand",
        ],
    )

    # Phishing Playbook
    PLAYBOOKS[IncidentType.PHISHING] = Playbook(
        incident_type=IncidentType.PHISHING,
        title="Phishing Incident Response",
        description="Playbook fuer die Reaktion auf Phishing-Angriffe und kompromittierte Credentials.",
        severity=Severity.HIGH,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Phishing-Vorfall erkennen und bewerten",
                order=1,
                steps=[
                    PlaybookStep(
                        id="P-D1",
                        title="Phishing-E-Mail analysieren",
                        description="Verdaechtige E-Mail untersuchen",
                        actions=[
                            "E-Mail-Header analysieren (SPF, DKIM, DMARC)",
                            "Absender-Domain pruefen",
                            "Links extrahieren (NICHT klicken)",
                            "Anhaenge in Sandbox analysieren",
                        ],
                        tools=["MXToolbox", "URLScan.io", "Any.Run", "VirusTotal"],
                        artifacts=["Original E-Mail (.eml)", "Screenshots", "URL-Liste"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="P-D2",
                        title="Betroffene Benutzer ermitteln",
                        description="Wer hat die E-Mail erhalten/geoeffnet",
                        actions=[
                            "E-Mail-Logs nach Empfaengern durchsuchen",
                            "Klick-Tracking pruefen (falls vorhanden)",
                            "Benutzer befragen",
                            "Credential-Eingaben ermitteln",
                        ],
                        tools=["E-Mail Gateway", "SIEM", "Proxy Logs"],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Weitere Kompromittierung verhindern",
                order=2,
                steps=[
                    PlaybookStep(
                        id="P-C1",
                        title="Phishing-URLs blockieren",
                        description="Zugang zu schaedlichen URLs unterbinden",
                        actions=[
                            "URLs in Proxy/Firewall blockieren",
                            "DNS-Blacklist aktualisieren",
                            "E-Mail-Filter-Regel erstellen",
                            "Weitere E-Mails aus der Kampagne loeschen",
                        ],
                        tools=["Proxy", "Firewall", "E-Mail Gateway", "DNS Filter"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="P-C2",
                        title="Kompromittierte Accounts sichern",
                        description="Betroffene Benutzerkonten schuetzen",
                        actions=[
                            "Passwoerter zuruecksetzen",
                            "MFA aktivieren/zuruecksetzen",
                            "Active Sessions beenden",
                            "OAuth-Tokens widerrufen",
                        ],
                        tools=["Active Directory", "Azure AD", "IAM"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="P-C3",
                        title="Benutzer benachrichtigen",
                        description="Betroffene Mitarbeiter informieren",
                        actions=[
                            "Warnung an alle Empfaenger senden",
                            "Awareness-Hinweis verbreiten",
                            "Reporting-Kanal kommunizieren",
                        ],
                        time_estimate="15-30 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse",
                description="Tiefergehende Untersuchung",
                order=3,
                steps=[
                    PlaybookStep(
                        id="P-A1",
                        title="Account-Aktivitaeten pruefen",
                        description="Verdaechtige Aktivitaeten nach Kompromittierung",
                        actions=[
                            "Login-Logs analysieren (ungewoehnliche IPs/Zeiten)",
                            "E-Mail-Weiterleitungsregeln pruefen",
                            "Postfach-Zugriffe analysieren",
                            "Datei-Zugriffe pruefen",
                        ],
                        tools=["Azure AD Logs", "Exchange Logs", "SIEM"],
                        time_estimate="1-2 h",
                    ),
                    PlaybookStep(
                        id="P-A2",
                        title="Lateral Movement pruefen",
                        description="Hat der Angreifer weitere Systeme erreicht",
                        actions=[
                            "Zugriffe auf andere Systeme pruefen",
                            "VPN-Verbindungen analysieren",
                            "Interne Phishing-Weiterleitungen suchen",
                        ],
                        tools=["SIEM", "EDR", "Network Logs"],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Normalbetrieb wiederherstellen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="P-R1",
                        title="Account-Wiederherstellung",
                        description="Benutzer-Accounts wiederherstellen",
                        actions=[
                            "Neue sichere Passwoerter setzen",
                            "MFA verifizieren",
                            "Berechtigungen pruefen",
                            "Benutzer informieren",
                        ],
                        time_estimate="30 min pro Account",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="P-P1",
                        title="Awareness verbessern",
                        description="Schulungsmassnahmen ableiten",
                        actions=[
                            "Phishing-Simulation planen",
                            "Awareness-Training durchfuehren",
                            "Reporting-Prozess verbessern",
                            "E-Mail-Filter optimieren",
                        ],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
        ],
        compliance_refs=["DSGVO Art. 33/34", "ISO 27001 A.16"],
        communication_required=[
            "IT-Sicherheitsbeauftragter",
            "Betroffene Benutzer",
            "Management (bei groesserer Kampagne)",
            "Datenschutzbeauftragter (bei Datenleck)",
        ],
        escalation_criteria=[
            "Mehr als 5 Benutzer haben Credentials eingegeben",
            "Admin-Account kompromittiert",
            "Verdacht auf Datenzugriff",
            "Interne Weiterverbreitung",
        ],
        resources_needed=[
            "Security Analyst",
            "E-Mail Administrator",
            "Identity Administrator",
        ],
    )

    # Data Breach Playbook
    PLAYBOOKS[IncidentType.DATA_BREACH] = Playbook(
        incident_type=IncidentType.DATA_BREACH,
        title="Data Breach Response",
        description="Playbook fuer die Reaktion auf Datenschutzverletzungen und Datenlecks.",
        severity=Severity.CRITICAL,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Datenleck erkennen und bewerten",
                order=1,
                steps=[
                    PlaybookStep(
                        id="DB-D1",
                        title="Art der Daten identifizieren",
                        description="Welche Daten sind betroffen",
                        actions=[
                            "Kategorie der Daten bestimmen (PII, PHI, Finanzdaten)",
                            "Anzahl betroffener Datensaetze schaetzen",
                            "Sensitivitaet bewerten",
                            "Betroffene Personen/Gruppen identifizieren",
                        ],
                        time_estimate="1-2 h",
                    ),
                    PlaybookStep(
                        id="DB-D2",
                        title="Quelle des Lecks identifizieren",
                        description="Wie sind die Daten abgeflossen",
                        actions=[
                            "Technischen Angriffsvektor ermitteln",
                            "Insider-Bedrohung pruefen",
                            "Fehlkonfiguration pruefen",
                            "Zeitraum des Abflusses bestimmen",
                        ],
                        tools=["DLP-Logs", "SIEM", "Cloud Access Logs"],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Weiteren Datenabfluss stoppen",
                order=2,
                steps=[
                    PlaybookStep(
                        id="DB-C1",
                        title="Datenabfluss stoppen",
                        description="Sofortige Massnahmen",
                        actions=[
                            "Betroffene Systeme/Zugaenge sperren",
                            "API-Keys/Tokens widerrufen",
                            "Netzwerk-Exfiltration blockieren",
                            "Kompromittierte Accounts deaktivieren",
                        ],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="DB-C2",
                        title="Beweise sichern",
                        description="Forensische Sicherung",
                        actions=[
                            "Logs sichern",
                            "Systemzustaende dokumentieren",
                            "Chain of Custody etablieren",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Rechtliche Bewertung",
                description="Meldepflichten und rechtliche Anforderungen",
                order=3,
                steps=[
                    PlaybookStep(
                        id="DB-L1",
                        title="Meldepflicht pruefen",
                        description="Regulatorische Anforderungen bewerten",
                        actions=[
                            "DSGVO Art. 33 Meldepflicht pruefen (72h)",
                            "Branchenspezifische Anforderungen pruefen",
                            "Risiko fuer Betroffene bewerten",
                            "Dokumentation fuer Aufsichtsbehoerde vorbereiten",
                        ],
                        time_estimate="2-4 h",
                    ),
                    PlaybookStep(
                        id="DB-L2",
                        title="Betroffene informieren",
                        description="DSGVO Art. 34 Benachrichtigung",
                        actions=[
                            "Benachrichtigungspflicht pruefen",
                            "Kommunikation vorbereiten",
                            "Hotline einrichten",
                            "FAQ erstellen",
                        ],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Systeme und Prozesse wiederherstellen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="DB-R1",
                        title="Sicherheitsluecken schliessen",
                        description="Ursachen beheben",
                        actions=[
                            "Schwachstelle patchen",
                            "Fehlkonfigurationen korrigieren",
                            "Zugriffskontrollen verschaerfen",
                            "DLP-Massnahmen implementieren",
                        ],
                        time_estimate="Variable",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung und Verbesserung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="DB-P1",
                        title="Dokumentation abschliessen",
                        description="Vollstaendige Dokumentation fuer Compliance",
                        actions=[
                            "Vorfallbericht erstellen",
                            "Massnahmen dokumentieren",
                            "Lessons Learned durchfuehren",
                            "Prozesse verbessern",
                        ],
                        time_estimate="4-8 h",
                    ),
                ],
            ),
        ],
        compliance_refs=["DSGVO Art. 33/34", "BDSG", "NIS2", "Branchenspezifisch"],
        communication_required=[
            "Datenschutzbeauftragter (sofort)",
            "Rechtsabteilung",
            "Management/Vorstand",
            "Aufsichtsbehoerde (innerhalb 72h)",
            "Betroffene Personen (bei hohem Risiko)",
            "PR/Kommunikation",
        ],
        escalation_criteria=[
            "Personenbezogene Daten betroffen",
            "Mehr als 1000 Datensaetze",
            "Sensible Datenkategorien (Art. 9 DSGVO)",
            "Finanzdaten betroffen",
            "Oeffentliche Exposition der Daten",
        ],
        resources_needed=[
            "Datenschutzbeauftragter",
            "Security Analyst",
            "Rechtsanwalt",
            "Kommunikationsspezialist",
        ],
    )

    # DDoS Playbook
    PLAYBOOKS[IncidentType.DDOS] = Playbook(
        incident_type=IncidentType.DDOS,
        title="DDoS Attack Response",
        description="Playbook fuer die Reaktion auf Distributed Denial of Service Angriffe.",
        severity=Severity.HIGH,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="DDoS-Angriff erkennen und klassifizieren",
                order=1,
                steps=[
                    PlaybookStep(
                        id="DD-D1",
                        title="Angriffstyp identifizieren",
                        description="Art des DDoS-Angriffs bestimmen",
                        actions=[
                            "Volumetrischer Angriff (Bandbreite)?",
                            "Protokoll-Angriff (SYN Flood)?",
                            "Application Layer Angriff (HTTP Flood)?",
                            "Traffic-Muster analysieren",
                        ],
                        tools=["Netflow", "Firewall Logs", "WAF", "Load Balancer"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="DD-D2",
                        title="Auswirkungen bewerten",
                        description="Geschaeftsauswirkungen ermitteln",
                        actions=[
                            "Betroffene Dienste identifizieren",
                            "Verfuegbarkeit messen",
                            "Kundenauswirkungen bewerten",
                            "SLA-Verletzungen pruefen",
                        ],
                        time_estimate="15-30 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Angriff abwehren",
                order=2,
                steps=[
                    PlaybookStep(
                        id="DD-C1",
                        title="DDoS-Mitigation aktivieren",
                        description="Abwehrmassnahmen einleiten",
                        actions=[
                            "DDoS-Protection-Service aktivieren",
                            "Traffic-Scrubbing einschalten",
                            "GeoIP-Blocking (falls sinnvoll)",
                            "Rate Limiting verschaerfen",
                        ],
                        tools=["DDoS Protection Service", "WAF", "CDN"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="DD-C2",
                        title="ISP/Provider kontaktieren",
                        description="Upstream-Hilfe anfordern",
                        actions=[
                            "ISP ueber Angriff informieren",
                            "Blackhole-Routing anfragen",
                            "Zusaetzliche Bandbreite anfragen",
                        ],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="DD-C3",
                        title="Infrastruktur skalieren",
                        description="Kapazitaeten erhoehen",
                        actions=[
                            "Auto-Scaling aktivieren",
                            "Zusaetzliche Server hochfahren",
                            "CDN-Caching optimieren",
                            "Non-kritische Dienste reduzieren",
                        ],
                        tools=["Cloud Console", "Load Balancer"],
                        time_estimate="15-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse",
                description="Angriff analysieren",
                order=3,
                steps=[
                    PlaybookStep(
                        id="DD-A1",
                        title="Angriffsquelle analysieren",
                        description="Herkunft und Muster verstehen",
                        actions=[
                            "Quell-IPs analysieren",
                            "Botnet-Charakteristiken identifizieren",
                            "Attack Signatures dokumentieren",
                            "IOCs extrahieren",
                        ],
                        tools=["SIEM", "Threat Intelligence"],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Normalbetrieb wiederherstellen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="DD-R1",
                        title="Dienste wiederherstellen",
                        description="Volle Verfuegbarkeit wiederherstellen",
                        actions=[
                            "Dienstverfuegbarkeit verifizieren",
                            "Performance-Baseline pruefen",
                            "Mitigation schrittweise reduzieren",
                            "Monitoring beibehalten",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="DD-P1",
                        title="DDoS-Resilienz verbessern",
                        description="Zukuenftige Abwehr staerken",
                        actions=[
                            "DDoS-Schutz evaluieren",
                            "Kapazitaetsplanung ueberpruefen",
                            "Runbook aktualisieren",
                            "Ueberfall-Test planen",
                        ],
                        time_estimate="4-8 h",
                    ),
                ],
            ),
        ],
        compliance_refs=["NIS2", "ISO 27001 A.17"],
        communication_required=[
            "NOC/SOC",
            "Management",
            "Kunden (bei laengerer Ausfallzeit)",
            "ISP/Hosting Provider",
            "DDoS Protection Provider",
        ],
        escalation_criteria=[
            "Kritische Dienste nicht erreichbar",
            "Angriff dauert >1 Stunde",
            "Mitigation nicht wirksam",
            "Erpresserschreiben erhalten",
        ],
        resources_needed=[
            "Netzwerk-Administrator",
            "Security Analyst",
            "Cloud/Hosting Support",
        ],
    )

    # Malware Playbook
    PLAYBOOKS[IncidentType.MALWARE] = Playbook(
        incident_type=IncidentType.MALWARE,
        title="Malware Incident Response",
        description="Playbook fuer die Reaktion auf allgemeine Malware-Infektionen (Trojaner, Spyware, etc.).",
        severity=Severity.HIGH,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Malware erkennen und klassifizieren",
                order=1,
                steps=[
                    PlaybookStep(
                        id="M-D1",
                        title="Malware identifizieren",
                        description="Art und Familie der Malware bestimmen",
                        actions=[
                            "Hash der verdaechtigen Datei ermitteln",
                            "VirusTotal-Analyse durchfuehren",
                            "Malware-Verhalten analysieren",
                            "IOCs extrahieren",
                        ],
                        tools=["VirusTotal", "Any.Run", "Hybrid Analysis", "YARA"],
                        artifacts=["Malware-Sample", "Hash-Werte", "IOCs"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="M-D2",
                        title="Ausmass ermitteln",
                        description="Verbreitung im Netzwerk pruefen",
                        actions=[
                            "EDR auf weitere Infektionen pruefen",
                            "IOC-Suche im gesamten Netzwerk",
                            "Betroffene Systeme auflisten",
                        ],
                        tools=["EDR", "SIEM"],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Ausbreitung verhindern",
                order=2,
                steps=[
                    PlaybookStep(
                        id="M-C1",
                        title="Infizierte Systeme isolieren",
                        description="Netzwerkzugriff einschraenken",
                        actions=[
                            "System vom Netzwerk trennen",
                            "C2-Kommunikation blockieren",
                            "EDR-Isolation aktivieren",
                        ],
                        tools=["EDR", "Firewall"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="M-C2",
                        title="IOCs blockieren",
                        description="Bekannte IOCs sperren",
                        actions=[
                            "Hashes in EDR blockieren",
                            "C2-Domains/IPs in Firewall sperren",
                            "E-Mail-Anhaenge blockieren",
                        ],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse",
                description="Detaillierte Malware-Analyse",
                order=3,
                steps=[
                    PlaybookStep(
                        id="M-A1",
                        title="Forensische Analyse",
                        description="System forensisch untersuchen",
                        actions=[
                            "Memory Dump analysieren",
                            "Persistenz-Mechanismen identifizieren",
                            "Infektionsvektor ermitteln",
                            "Datenexfiltration pruefen",
                        ],
                        tools=["Volatility", "FTK", "Autopsy"],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Beseitigung",
                description="Malware entfernen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="M-E1",
                        title="Malware entfernen",
                        description="Schadsoftware vollstaendig beseitigen",
                        actions=[
                            "Malware-Dateien loeschen",
                            "Registry bereinigen",
                            "Scheduled Tasks pruefen",
                            "Neuinstallation bei Bedarf",
                        ],
                        tools=["EDR", "Malwarebytes", "Autoruns"],
                        time_estimate="1-2 h pro System",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Systeme wiederherstellen",
                order=5,
                steps=[
                    PlaybookStep(
                        id="M-R1",
                        title="System wiederherstellen",
                        description="Normalbetrieb wiederherstellen",
                        actions=[
                            "System patchen",
                            "Passwoerter aendern",
                            "Monitoring intensivieren",
                            "Benutzer informieren",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=6,
                steps=[
                    PlaybookStep(
                        id="M-P1",
                        title="Lessons Learned",
                        description="Erkenntnisse dokumentieren",
                        actions=[
                            "Infektionsweg dokumentieren",
                            "Praevention verbessern",
                            "IOCs mit Community teilen",
                        ],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
        ],
        compliance_refs=["ISO 27001 A.16", "BSI IT-Grundschutz"],
        communication_required=[
            "IT-Sicherheitsbeauftragter",
            "Betroffene Benutzer",
            "Management (bei kritischen Systemen)",
        ],
        escalation_criteria=[
            "Mehr als 5 Systeme betroffen",
            "Server/kritische Systeme infiziert",
            "Verdacht auf Datenabfluss",
            "APT-Verdacht",
        ],
        resources_needed=[
            "Security Analyst",
            "Malware Analyst",
            "System Administrator",
        ],
    )

    # Account Compromise Playbook
    PLAYBOOKS[IncidentType.ACCOUNT_COMPROMISE] = Playbook(
        incident_type=IncidentType.ACCOUNT_COMPROMISE,
        title="Account Compromise Response",
        description="Playbook fuer die Reaktion auf kompromittierte Benutzerkonten.",
        severity=Severity.HIGH,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Kompromittierung erkennen und bewerten",
                order=1,
                steps=[
                    PlaybookStep(
                        id="AC-D1",
                        title="Kompromittierung verifizieren",
                        description="Verdacht bestaetigen",
                        actions=[
                            "Ungewoehnliche Logins pruefen (Zeit, Ort, Geraet)",
                            "Impossible Travel Detection",
                            "Benutzer befragen",
                            "MFA-Umgehung pruefen",
                        ],
                        tools=["Azure AD Logs", "SIEM", "UEBA"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="AC-D2",
                        title="Account-Typ bewerten",
                        description="Kritikalitaet des Accounts",
                        actions=[
                            "Berechtigungen des Accounts pruefen",
                            "Admin-Rechte vorhanden?",
                            "Zugriff auf sensitive Daten?",
                            "Service Account?",
                        ],
                        time_estimate="15-30 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Account sichern",
                order=2,
                steps=[
                    PlaybookStep(
                        id="AC-C1",
                        title="Account sperren",
                        description="Sofortige Sperrung",
                        actions=[
                            "Passwort zuruecksetzen",
                            "Alle Sessions beenden",
                            "MFA zuruecksetzen",
                            "OAuth-Tokens widerrufen",
                        ],
                        tools=["Active Directory", "Azure AD", "IAM"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="AC-C2",
                        title="Verbundene Accounts pruefen",
                        description="Weitere Kompromittierungen",
                        actions=[
                            "SSO-verbundene Apps pruefen",
                            "Delegierte Zugriffe pruefen",
                            "Passwort-Wiederverwendung pruefen",
                        ],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse",
                description="Aktivitaeten analysieren",
                order=3,
                steps=[
                    PlaybookStep(
                        id="AC-A1",
                        title="Account-Aktivitaeten pruefen",
                        description="Was hat der Angreifer getan",
                        actions=[
                            "E-Mail-Zugriffe pruefen",
                            "Datei-Downloads analysieren",
                            "Weiterleitungsregeln pruefen",
                            "Berechtigungsaenderungen pruefen",
                        ],
                        tools=["Audit Logs", "SIEM", "DLP"],
                        time_estimate="1-2 h",
                    ),
                    PlaybookStep(
                        id="AC-A2",
                        title="Kompromittierungsweg ermitteln",
                        description="Wie wurde der Account kompromittiert",
                        actions=[
                            "Phishing pruefen",
                            "Password Spray Angriffe pruefen",
                            "Credential Stuffing pruefen",
                            "Malware auf Endgeraet pruefen",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Wiederherstellung",
                description="Account wiederherstellen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="AC-R1",
                        title="Sicherer Account-Reset",
                        description="Account sicher wiederherstellen",
                        actions=[
                            "Neues starkes Passwort setzen",
                            "MFA neu einrichten",
                            "Berechtigungen verifizieren",
                            "Benutzer schulen",
                        ],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="AC-P1",
                        title="Sicherheit verbessern",
                        description="Praevention staerken",
                        actions=[
                            "MFA fuer alle Accounts erzwingen",
                            "Password Policy verschaerfen",
                            "Conditional Access implementieren",
                            "UEBA aktivieren",
                        ],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
        ],
        compliance_refs=["DSGVO Art. 33/34", "ISO 27001 A.9"],
        communication_required=[
            "Betroffener Benutzer",
            "IT-Sicherheitsbeauftragter",
            "Datenschutzbeauftragter (bei Datenzugriff)",
            "Management (bei Admin-Account)",
        ],
        escalation_criteria=[
            "Admin-Account betroffen",
            "Datenzugriff nachgewiesen",
            "Mehrere Accounts kompromittiert",
            "Persistence etabliert",
        ],
        resources_needed=[
            "Identity Administrator",
            "Security Analyst",
        ],
    )

    # Insider Threat Playbook
    PLAYBOOKS[IncidentType.INSIDER_THREAT] = Playbook(
        incident_type=IncidentType.INSIDER_THREAT,
        title="Insider Threat Response",
        description="Playbook fuer die Reaktion auf Insider-Bedrohungen (boesartig oder fahrlässig).",
        severity=Severity.CRITICAL,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Insider-Bedrohung erkennen und bewerten",
                order=1,
                steps=[
                    PlaybookStep(
                        id="IT-D1",
                        title="Verdacht verifizieren",
                        description="Insider-Aktivitaet bestaetigen",
                        actions=[
                            "Anomales Verhalten analysieren",
                            "Datenexfiltration pruefen",
                            "Zugriffsmuster analysieren",
                            "HR/Manager konsultieren",
                        ],
                        tools=["UEBA", "DLP", "SIEM"],
                        time_estimate="1-2 h",
                        notes="WICHTIG: Diskretion wahren - Verdaechtigen nicht warnen",
                    ),
                    PlaybookStep(
                        id="IT-D2",
                        title="Risiko bewerten",
                        description="Bedrohungspotential einschaetzen",
                        actions=[
                            "Zugriff auf sensitive Daten pruefen",
                            "Kuendigungsstatus pruefen",
                            "Vorherige Vorfaelle pruefen",
                            "Motivation einschaetzen",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Risiko begrenzen",
                order=2,
                steps=[
                    PlaybookStep(
                        id="IT-C1",
                        title="Zugriff einschraenken",
                        description="Berechtigungen reduzieren",
                        actions=[
                            "Nicht-essentielle Zugriffe entfernen",
                            "Monitoring intensivieren",
                            "DLP-Alerts verschaerfen",
                            "USB-Zugriff einschraenken",
                        ],
                        tools=["IAM", "DLP", "EDR"],
                        time_estimate="1-2 h",
                        notes="Aenderungen diskret durchfuehren",
                    ),
                    PlaybookStep(
                        id="IT-C2",
                        title="Beweise sichern",
                        description="Forensische Sicherung",
                        actions=[
                            "E-Mail-Logs sichern",
                            "Dateizugriffs-Logs sichern",
                            "Netzwerk-Logs sichern",
                            "Physical Security einbinden",
                        ],
                        time_estimate="2-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Investigation",
                description="Detaillierte Untersuchung",
                order=3,
                steps=[
                    PlaybookStep(
                        id="IT-I1",
                        title="Forensische Untersuchung",
                        description="Umfassende Analyse",
                        actions=[
                            "Timeline der Aktivitaeten erstellen",
                            "Exfiltrierte Daten identifizieren",
                            "Kommunikation analysieren",
                            "Komplizen pruefen",
                        ],
                        tools=["Forensik-Tools", "E-Discovery"],
                        time_estimate="Variable",
                        notes="Mit Rechtsabteilung koordinieren",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Reaktion",
                description="Massnahmen ergreifen",
                order=4,
                steps=[
                    PlaybookStep(
                        id="IT-R1",
                        title="HR/Rechtliche Massnahmen",
                        description="Personalmassnahmen koordinieren",
                        actions=[
                            "HR einbinden",
                            "Rechtsabteilung einbinden",
                            "Disziplinarmassnahmen besprechen",
                            "Exit-Prozess vorbereiten (falls erforderlich)",
                        ],
                        time_estimate="Variable",
                    ),
                    PlaybookStep(
                        id="IT-R2",
                        title="Account-Deaktivierung",
                        description="Bei Beendigung",
                        actions=[
                            "Alle Zugaenge sperren",
                            "Firmengeraete einsammeln",
                            "Remote-Wipe durchfuehren",
                            "Badge deaktivieren",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="IT-P1",
                        title="Praevention verbessern",
                        description="Kontrollen staerken",
                        actions=[
                            "Insider-Threat-Programm etablieren",
                            "UEBA implementieren/verbessern",
                            "DLP verschaerfen",
                            "Offboarding-Prozess pruefen",
                        ],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
        ],
        compliance_refs=["DSGVO", "Arbeitsrecht", "Betriebsrat"],
        communication_required=[
            "Management",
            "Rechtsabteilung",
            "HR",
            "Betriebsrat (falls vorhanden)",
            "Strafverfolgung (bei Straftat)",
        ],
        escalation_criteria=[
            "Datendiebstahl nachgewiesen",
            "Kundendaten betroffen",
            "IP/Geschaeftsgeheimnisse betroffen",
            "Sabotage-Verdacht",
        ],
        resources_needed=[
            "Security Analyst",
            "HR",
            "Rechtsabteilung",
            "Forensik-Experte",
        ],
    )

    # Web Application Attack Playbook
    PLAYBOOKS[IncidentType.WEB_APPLICATION] = Playbook(
        incident_type=IncidentType.WEB_APPLICATION,
        title="Web Application Attack Response",
        description="Playbook fuer die Reaktion auf Web-Application-Angriffe (SQLi, XSS, etc.).",
        severity=Severity.HIGH,
        phases=[
            PlaybookPhase(
                name="Erkennung & Triage",
                description="Angriff erkennen und klassifizieren",
                order=1,
                steps=[
                    PlaybookStep(
                        id="WA-D1",
                        title="Angriffstyp identifizieren",
                        description="Art des Web-Angriffs bestimmen",
                        actions=[
                            "WAF-Logs analysieren",
                            "SQL Injection pruefen",
                            "XSS-Angriffe pruefen",
                            "Path Traversal pruefen",
                            "Authentication Bypass pruefen",
                        ],
                        tools=["WAF", "Web Server Logs", "SIEM"],
                        time_estimate="30-60 min",
                    ),
                    PlaybookStep(
                        id="WA-D2",
                        title="Erfolg des Angriffs pruefen",
                        description="War der Angriff erfolgreich",
                        actions=[
                            "Datenbankzugriffe pruefen",
                            "Session-Hijacking pruefen",
                            "Defacement pruefen",
                            "Backend-Kompromittierung pruefen",
                        ],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Eindaemmung",
                description="Angriff stoppen",
                order=2,
                steps=[
                    PlaybookStep(
                        id="WA-C1",
                        title="WAF-Regeln verschaerfen",
                        description="Sofortige Abwehrmassnahmen",
                        actions=[
                            "Angreifer-IP blockieren",
                            "WAF in Block-Mode schalten",
                            "Rate Limiting aktivieren",
                            "Virtual Patching anwenden",
                        ],
                        tools=["WAF", "Firewall", "CDN"],
                        time_estimate="15-30 min",
                    ),
                    PlaybookStep(
                        id="WA-C2",
                        title="Anwendung sichern",
                        description="Weitere Kompromittierung verhindern",
                        actions=[
                            "Kompromittierte Sessions invalidieren",
                            "API-Keys rotieren",
                            "Database-Credentials aendern",
                            "Temporaer Funktionen deaktivieren",
                        ],
                        time_estimate="30-60 min",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Analyse",
                description="Angriff analysieren",
                order=3,
                steps=[
                    PlaybookStep(
                        id="WA-A1",
                        title="Schwachstelle identifizieren",
                        description="Ausgenutzte Luecke finden",
                        actions=[
                            "Verwundbare Endpoints identifizieren",
                            "Payload analysieren",
                            "Code-Review durchfuehren",
                            "Penetration Test (gezielt)",
                        ],
                        tools=["Burp Suite", "OWASP ZAP", "Code Scanner"],
                        time_estimate="2-4 h",
                    ),
                    PlaybookStep(
                        id="WA-A2",
                        title="Datenexfiltration pruefen",
                        description="Wurden Daten gestohlen",
                        actions=[
                            "Datenbankabfragen analysieren",
                            "Ausgehenden Traffic pruefen",
                            "Betroffene Daten identifizieren",
                        ],
                        time_estimate="1-2 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Beseitigung",
                description="Schwachstelle beheben",
                order=4,
                steps=[
                    PlaybookStep(
                        id="WA-E1",
                        title="Vulnerability Fix",
                        description="Code-Korrektur",
                        actions=[
                            "Schwachstelle im Code beheben",
                            "Input Validation implementieren",
                            "Prepared Statements verwenden",
                            "Output Encoding implementieren",
                        ],
                        time_estimate="Variable",
                    ),
                    PlaybookStep(
                        id="WA-E2",
                        title="Deployment",
                        description="Fix ausrollen",
                        actions=[
                            "Code-Review des Fixes",
                            "Staging-Test",
                            "Production-Deployment",
                            "Verify Fix",
                        ],
                        time_estimate="1-4 h",
                    ),
                ],
            ),
            PlaybookPhase(
                name="Post-Incident",
                description="Nachbereitung",
                order=5,
                steps=[
                    PlaybookStep(
                        id="WA-P1",
                        title="Security verbessern",
                        description="Praevention staerken",
                        actions=[
                            "SAST/DAST in Pipeline integrieren",
                            "Security-Training fuer Entwickler",
                            "WAF-Regeln optimieren",
                            "Bug Bounty Programm erwaegen",
                        ],
                        time_estimate="Ongoing",
                    ),
                ],
            ),
        ],
        compliance_refs=["OWASP Top 10", "PCI-DSS", "ISO 27001"],
        communication_required=[
            "Development Team",
            "IT-Sicherheitsbeauftragter",
            "Datenschutzbeauftragter (bei Datenleck)",
            "Kunden (bei Kompromittierung)",
        ],
        escalation_criteria=[
            "Datenbank kompromittiert",
            "Kundendaten betroffen",
            "Persistenter Zugriff etabliert",
            "Mehrere Anwendungen betroffen",
        ],
        resources_needed=[
            "Security Analyst",
            "Web Developer",
            "DevOps Engineer",
        ],
    )


# Initialize playbooks on module load
_init_playbooks()


def get_incident_type_labels() -> Dict[IncidentType, str]:
    """Get display labels for incident types."""
    return {
        IncidentType.RANSOMWARE: "Ransomware",
        IncidentType.PHISHING: "Phishing",
        IncidentType.DATA_BREACH: "Datenleck / Data Breach",
        IncidentType.DDOS: "DDoS-Angriff",
        IncidentType.INSIDER_THREAT: "Insider-Bedrohung",
        IncidentType.MALWARE: "Malware (allgemein)",
        IncidentType.ACCOUNT_COMPROMISE: "Account-Kompromittierung",
        IncidentType.WEB_APPLICATION: "Web-Application-Angriff",
        IncidentType.SUPPLY_CHAIN: "Supply Chain Attack",
        IncidentType.APT: "APT / Advanced Persistent Threat",
    }


def render_playbook_generator(lang: str = "de") -> None:
    """Render the playbook generator interface."""
    st.header("Playbook Generator")
    st.caption("Automatische Erstellung von Incident Response Playbooks")

    # Incident type selection
    st.subheader("1. Vorfallstyp waehlen")

    incident_labels = get_incident_type_labels()
    available_types = [t for t in IncidentType if t in PLAYBOOKS]

    selected_type_label = st.selectbox(
        "Incident-Typ",
        options=[incident_labels[t] for t in available_types],
        index=0,
    )

    # Find selected type
    selected_type = None
    for t in available_types:
        if incident_labels[t] == selected_type_label:
            selected_type = t
            break

    if not selected_type or selected_type not in PLAYBOOKS:
        st.warning("Playbook fuer diesen Typ noch nicht verfuegbar")
        return

    playbook = PLAYBOOKS[selected_type]

    st.divider()

    # Playbook overview
    st.subheader("2. Playbook-Uebersicht")

    col1, col2, col3 = st.columns(3)
    with col1:
        severity_colors = {
            Severity.CRITICAL: "KRITISCH",
            Severity.HIGH: "HOCH",
            Severity.MEDIUM: "MITTEL",
            Severity.LOW: "NIEDRIG",
        }
        st.metric("Severity", severity_colors.get(playbook.severity, "---"))
    with col2:
        total_steps = sum(len(phase.steps) for phase in playbook.phases)
        st.metric("Schritte", total_steps)
    with col3:
        st.metric("Phasen", len(playbook.phases))

    st.markdown(f"**Beschreibung:** {playbook.description}")

    # Compliance references
    if playbook.compliance_refs:
        st.markdown(f"**Compliance:** {', '.join(playbook.compliance_refs)}")

    st.divider()

    # Phases and steps
    st.subheader("3. Playbook-Phasen")

    # Track progress in session state
    if 'playbook_progress' not in st.session_state:
        st.session_state.playbook_progress = {}

    playbook_key = f"playbook_{selected_type.value}"
    if playbook_key not in st.session_state.playbook_progress:
        st.session_state.playbook_progress[playbook_key] = {}

    for phase in sorted(playbook.phases, key=lambda p: p.order):
        with st.expander(f"Phase {phase.order}: {phase.name}", expanded=(phase.order == 1)):
            st.caption(phase.description)

            for step in phase.steps:
                step_key = f"{playbook_key}_{step.id}"
                is_completed = st.session_state.playbook_progress.get(playbook_key, {}).get(step.id, False)

                col1, col2 = st.columns([0.05, 0.95])
                with col1:
                    completed = st.checkbox(
                        "",
                        value=is_completed,
                        key=f"check_{step_key}",
                        label_visibility="collapsed",
                    )
                    if completed != is_completed:
                        if playbook_key not in st.session_state.playbook_progress:
                            st.session_state.playbook_progress[playbook_key] = {}
                        st.session_state.playbook_progress[playbook_key][step.id] = completed

                with col2:
                    status_marker = "[x]" if completed else "[ ]"
                    st.markdown(f"**{step.id}: {step.title}**")

                    st.markdown(step.description)

                    if step.actions:
                        st.markdown("**Aktionen:**")
                        for action in step.actions:
                            st.markdown(f"- {action}")

                    meta_cols = st.columns(3)
                    if step.tools:
                        with meta_cols[0]:
                            st.caption(f"Tools: {', '.join(step.tools)}")
                    if step.time_estimate:
                        with meta_cols[1]:
                            st.caption(f"Zeit: {step.time_estimate}")
                    if step.artifacts:
                        with meta_cols[2]:
                            st.caption(f"Artifacts: {', '.join(step.artifacts)}")

                    if step.notes:
                        st.info(step.notes)

                st.markdown("---")

    st.divider()

    # Communication and escalation
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("4. Kommunikation")
        if playbook.communication_required:
            for item in playbook.communication_required:
                st.markdown(f"- {item}")

    with col2:
        st.subheader("5. Eskalationskriterien")
        if playbook.escalation_criteria:
            for item in playbook.escalation_criteria:
                st.markdown(f"- {item}")

    st.divider()

    # Resources
    st.subheader("6. Benoetigte Ressourcen")
    if playbook.resources_needed:
        resource_cols = st.columns(len(playbook.resources_needed))
        for i, resource in enumerate(playbook.resources_needed):
            with resource_cols[i]:
                st.markdown(f"**{resource}**")

    st.divider()

    # Export options
    st.subheader("7. Export")
    _render_playbook_export(playbook)


def _render_playbook_export(playbook: Playbook) -> None:
    """Render export options for playbook."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if FPDF_AVAILABLE:
            pdf_content = _generate_playbook_pdf(playbook)
            st.download_button(
                label="PDF Export",
                data=pdf_content,
                file_name=f"playbook_{playbook.incident_type.value}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("PDF (nicht verfuegbar)", disabled=True, use_container_width=True)

    with col2:
        latex_content = _generate_playbook_latex(playbook)
        st.download_button(
            label="LaTeX Export",
            data=latex_content,
            file_name=f"playbook_{playbook.incident_type.value}_{datetime.now().strftime('%Y%m%d')}.tex",
            mime="application/x-latex",
            use_container_width=True,
        )

    with col3:
        md_content = _generate_playbook_markdown(playbook)
        st.download_button(
            label="Markdown Export",
            data=md_content,
            file_name=f"playbook_{playbook.incident_type.value}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col4:
        json_content = _generate_playbook_json(playbook)
        st.download_button(
            label="JSON Export",
            data=json_content,
            file_name=f"playbook_{playbook.incident_type.value}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )


def _generate_playbook_pdf(playbook: Playbook) -> bytes:
    """Generate PDF version of playbook."""
    if not FPDF_AVAILABLE:
        return b""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, playbook.title, new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, playbook.description)
    pdf.ln(5)

    # Metadata
    pdf.set_font("Helvetica", "B", 10)
    severity_labels = {"critical": "KRITISCH", "high": "HOCH", "medium": "MITTEL", "low": "NIEDRIG"}
    pdf.cell(0, 8, f"Severity: {severity_labels.get(playbook.severity.value, playbook.severity.value)}", new_x="LMARGIN", new_y="NEXT")

    if playbook.compliance_refs:
        pdf.cell(0, 8, f"Compliance: {', '.join(playbook.compliance_refs)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Phases
    for phase in sorted(playbook.phases, key=lambda p: p.order):
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Phase {phase.order}: {phase.name}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 5, phase.description)
        pdf.ln(3)

        for step in phase.steps:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, f"[ ] {step.id}: {step.title}", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, step.description)

            if step.actions:
                pdf.set_font("Helvetica", "", 9)
                for action in step.actions:
                    pdf.cell(0, 5, f"- {action[:80]}{'...' if len(action) > 80 else ''}", new_x="LMARGIN", new_y="NEXT")

            if step.tools:
                pdf.set_font("Helvetica", "I", 9)
                tools_text = ', '.join(step.tools)
                pdf.cell(0, 5, f"Tools: {tools_text[:70]}{'...' if len(tools_text) > 70 else ''}", new_x="LMARGIN", new_y="NEXT")

            if step.time_estimate:
                pdf.cell(0, 5, f"Zeit: {step.time_estimate}", new_x="LMARGIN", new_y="NEXT")

            if step.notes:
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 5, f"HINWEIS: {step.notes[:70]}{'...' if len(step.notes) > 70 else ''}", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(3)

    # Communication
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Kommunikation", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for item in playbook.communication_required:
        pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Escalation
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Eskalationskriterien", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for item in playbook.escalation_criteria:
        pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Resources
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Benoetigte Ressourcen", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for item in playbook.resources_needed:
        pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, f"Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    return bytes(pdf.output())


def _generate_playbook_latex(playbook: Playbook) -> str:
    """Generate LaTeX version of playbook."""
    def escape_latex(text: str) -> str:
        replacements = [
            ("\\", "\\textbackslash{}"),
            ("&", "\\&"),
            ("%", "\\%"),
            ("$", "\\$"),
            ("#", "\\#"),
            ("_", "\\_"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("~", "\\textasciitilde{}"),
            ("^", "\\textasciicircum{}"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    severity_labels = {"critical": "KRITISCH", "high": "HOCH", "medium": "MITTEL", "low": "NIEDRIG"}

    latex = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage[german]{{babel}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{enumitem}}
\\usepackage{{fancyhdr}}
\\usepackage{{lastpage}}
\\usepackage{{xcolor}}
\\usepackage{{tcolorbox}}

\\geometry{{margin=2.5cm}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{IR Playbook: {escape_latex(playbook.title)}}}
\\fancyhead[R]{{\\today}}
\\fancyfoot[C]{{Seite \\thepage\\ von \\pageref{{LastPage}}}}

\\begin{{document}}

\\begin{{center}}
\\LARGE\\textbf{{{escape_latex(playbook.title)}}}\\\\[0.5cm]
\\normalsize
\\end{{center}}

\\textbf{{Severity:}} {severity_labels.get(playbook.severity.value, playbook.severity.value)}\\\\
\\textbf{{Compliance:}} {escape_latex(', '.join(playbook.compliance_refs))}

\\vspace{{0.5cm}}

{escape_latex(playbook.description)}

\\tableofcontents
\\newpage

"""

    # Phases
    for phase in sorted(playbook.phases, key=lambda p: p.order):
        latex += f"\\section{{Phase {phase.order}: {escape_latex(phase.name)}}}\n"
        latex += f"\\textit{{{escape_latex(phase.description)}}}\n\n"

        for step in phase.steps:
            latex += f"\\subsection{{{escape_latex(step.id)}: {escape_latex(step.title)}}}\n"
            latex += f"{escape_latex(step.description)}\n\n"

            if step.actions:
                latex += "\\textbf{Aktionen:}\n\\begin{itemize}\n"
                for action in step.actions:
                    latex += f"  \\item {escape_latex(action)}\n"
                latex += "\\end{itemize}\n\n"

            if step.tools:
                latex += f"\\textbf{{Tools:}} {escape_latex(', '.join(step.tools))}\n\n"

            if step.time_estimate:
                latex += f"\\textbf{{Zeitschaetzung:}} {escape_latex(step.time_estimate)}\n\n"

            if step.notes:
                latex += f"\\begin{{tcolorbox}}[colback=yellow!10]\n\\textbf{{HINWEIS:}} {escape_latex(step.notes)}\n\\end{{tcolorbox}}\n\n"

    # Communication
    latex += "\\section{Kommunikation}\n\\begin{itemize}\n"
    for item in playbook.communication_required:
        latex += f"  \\item {escape_latex(item)}\n"
    latex += "\\end{itemize}\n\n"

    # Escalation
    latex += "\\section{Eskalationskriterien}\n\\begin{itemize}\n"
    for item in playbook.escalation_criteria:
        latex += f"  \\item {escape_latex(item)}\n"
    latex += "\\end{itemize}\n\n"

    # Resources
    latex += "\\section{Benoetigte Ressourcen}\n\\begin{itemize}\n"
    for item in playbook.resources_needed:
        latex += f"  \\item {escape_latex(item)}\n"
    latex += "\\end{itemize}\n\n"

    latex += f"""
\\vfill
\\begin{{center}}
\\small Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M')}
\\end{{center}}

\\end{{document}}
"""

    return latex


def _generate_playbook_markdown(playbook: Playbook) -> str:
    """Generate Markdown version of playbook."""
    severity_labels = {"critical": "KRITISCH", "high": "HOCH", "medium": "MITTEL", "low": "NIEDRIG"}

    md = f"""# {playbook.title}

**Severity:** {severity_labels.get(playbook.severity.value, playbook.severity.value)}
**Compliance:** {', '.join(playbook.compliance_refs)}

{playbook.description}

---

"""

    # Phases
    for phase in sorted(playbook.phases, key=lambda p: p.order):
        md += f"## Phase {phase.order}: {phase.name}\n\n"
        md += f"*{phase.description}*\n\n"

        for step in phase.steps:
            md += f"### [ ] {step.id}: {step.title}\n\n"
            md += f"{step.description}\n\n"

            if step.actions:
                md += "**Aktionen:**\n"
                for action in step.actions:
                    md += f"- {action}\n"
                md += "\n"

            if step.tools:
                md += f"**Tools:** {', '.join(step.tools)}\n\n"

            if step.time_estimate:
                md += f"**Zeit:** {step.time_estimate}\n\n"

            if step.artifacts:
                md += f"**Artifacts:** {', '.join(step.artifacts)}\n\n"

            if step.notes:
                md += f"> **HINWEIS:** {step.notes}\n\n"

            md += "---\n\n"

    # Communication
    md += "## Kommunikation\n\n"
    for item in playbook.communication_required:
        md += f"- {item}\n"
    md += "\n"

    # Escalation
    md += "## Eskalationskriterien\n\n"
    for item in playbook.escalation_criteria:
        md += f"- {item}\n"
    md += "\n"

    # Resources
    md += "## Benoetigte Ressourcen\n\n"
    for item in playbook.resources_needed:
        md += f"- {item}\n"
    md += "\n"

    md += f"\n---\n*Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"

    return md


def _generate_playbook_json(playbook: Playbook) -> str:
    """Generate JSON version of playbook."""
    data = {
        "generated": datetime.now().isoformat(),
        "incident_type": playbook.incident_type.value,
        "title": playbook.title,
        "description": playbook.description,
        "severity": playbook.severity.value,
        "compliance_refs": playbook.compliance_refs,
        "communication_required": playbook.communication_required,
        "escalation_criteria": playbook.escalation_criteria,
        "resources_needed": playbook.resources_needed,
        "phases": [
            {
                "order": phase.order,
                "name": phase.name,
                "description": phase.description,
                "steps": [
                    {
                        "id": step.id,
                        "title": step.title,
                        "description": step.description,
                        "actions": step.actions,
                        "tools": step.tools,
                        "artifacts": step.artifacts,
                        "time_estimate": step.time_estimate,
                        "notes": step.notes,
                    }
                    for step in phase.steps
                ],
            }
            for phase in sorted(playbook.phases, key=lambda p: p.order)
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
