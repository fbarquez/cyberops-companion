# BSI IT-Grundschutz / ISO 27001 / NIS2 Mapping

> Cross-reference between major compliance frameworks in the DACH region

## Overview

This document maps controls between:
- **NIS2** Article 21 (10 measures)
- **ISO 27001:2022** (93 controls in 4 themes)
- **BSI IT-Grundschutz** (selected building blocks from Kompendium 2023)

## Quick Reference Matrix

| NIS2 | ISO 27001:2022 Controls | BSI IT-Grundschutz |
|------|-------------------------|---------------------|
| M01 | A.5.1-A.5.3 | ISMS.1, ORP.1 |
| M02 | A.5.24-A.5.27 | DER.2.1, DER.2.2 |
| M03 | A.5.29-A.5.30, A.8.13-A.8.14 | DER.4, CON.3, CON.6 |
| M04 | A.5.19-A.5.23 | OPS.2.1, OPS.2.3 |
| M05 | A.8.25-A.8.31 | CON.8, APP.* |
| M06 | A.5.35-A.5.36, A.8.34 | DER.3.1, DER.3.2 |
| M07 | A.6.3, A.6.7 | ORP.3, CON.7 |
| M08 | A.8.24 | CON.1, CON.2 |
| M09 | A.5.9-A.5.18, A.6.*, A.7.* | ORP.2, ORP.4, INF.* |
| M10 | A.5.14, A.5.17, A.8.5 | ORP.4, NET.* |

---

## Detailed Mapping

### M01: Risikoanalyse und Sicherheitskonzepte

**NIS2 Art. 21.2(a):** Konzepte für die Risikoanalyse und für die Sicherheit von Informationssystemen

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.1 | Informationssicherheitsrichtlinien | Policies for information security |
| **ISO 27001** | A.5.2 | Rollen und Verantwortlichkeiten | Information security roles and responsibilities |
| **ISO 27001** | A.5.3 | Aufgabentrennung | Segregation of duties |
| **BSI** | ISMS.1 | Sicherheitsmanagement | Security management |
| **BSI** | ORP.1 | Organisation | Organization |

**Typische Nachweise:**
- IT-Sicherheitsrichtlinie (aktuell, freigegeben)
- Risikobewertungsbericht
- Rollen- und Verantwortlichkeitsmatrix
- Organigramm mit Sicherheitsverantwortlichen

---

### M02: Bewältigung von Sicherheitsvorfällen

**NIS2 Art. 21.2(b):** Bewältigung von Sicherheitsvorfällen

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.24 | Planung der Vorfallbehandlung | Incident management planning |
| **ISO 27001** | A.5.25 | Bewertung von Sicherheitsereignissen | Assessment of information security events |
| **ISO 27001** | A.5.26 | Reaktion auf Vorfälle | Response to incidents |
| **ISO 27001** | A.5.27 | Erkenntnisse aus Vorfällen | Learning from incidents |
| **BSI** | DER.2.1 | Behandlung von Sicherheitsvorfällen | Incident handling |
| **BSI** | DER.2.2 | Vorsorge für IT-Forensik | IT forensics preparation |

**Typische Nachweise:**
- Incident-Response-Plan
- Eskalationsmatrix mit Kontaktdaten
- Incident-Log (anonymisiert)
- Post-Incident-Reports
- Meldeformulare (NIS2: 24h/72h)

---

### M03: Business Continuity und Krisenmanagement

**NIS2 Art. 21.2(c):** Aufrechterhaltung des Betriebs, Backup-Management, Wiederherstellung, Krisenmanagement

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.29 | Informationssicherheit bei Störungen | Security during disruption |
| **ISO 27001** | A.5.30 | IKT-Bereitschaft für BC | ICT readiness for business continuity |
| **ISO 27001** | A.8.13 | Informationssicherung | Information backup |
| **ISO 27001** | A.8.14 | Redundanz | Redundancy of processing facilities |
| **BSI** | DER.4 | Notfallmanagement | Emergency management |
| **BSI** | CON.3 | Datensicherungskonzept | Backup concept |
| **BSI** | CON.6 | Löschen und Vernichten | Deletion and destruction |

**Typische Nachweise:**
- Business-Continuity-Plan
- Backup-Richtlinie
- Backup-Logs (Erfolg/Fehler)
- Restore-Test-Protokolle
- RTO/RPO-Dokumentation
- Notfall-Kontaktlisten

---

### M04: Sicherheit der Lieferkette

**NIS2 Art. 21.2(d):** Sicherheit der Lieferkette einschließlich Beziehungen zu Anbietern

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.19 | Lieferantenbeziehungen | Supplier relationships |
| **ISO 27001** | A.5.20 | Sicherheit in Lieferantenvereinbarungen | Security in supplier agreements |
| **ISO 27001** | A.5.21 | ICT-Lieferkette | ICT supply chain |
| **ISO 27001** | A.5.22 | Überwachung von Lieferanten | Monitoring of supplier services |
| **ISO 27001** | A.5.23 | Cloud-Dienste | Cloud services |
| **BSI** | OPS.2.1 | Outsourcing | Outsourcing |
| **BSI** | OPS.2.3 | Nutzung von Outsourcing | Use of outsourcing |

**Typische Nachweise:**
- Lieferantenverzeichnis mit Risikobewertung
- Verträge mit Sicherheitsklauseln
- AVV (Auftragsverarbeitung)
- Lieferanten-Audits / Zertifikate (SOC 2, ISO 27001)
- Cloud-Sicherheitsbewertungen

---

### M05: Sichere Entwicklung und Wartung

**NIS2 Art. 21.2(e):** Sicherheit bei Erwerb, Entwicklung und Wartung von Netz- und Informationssystemen

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.8.25 | Sicherer Entwicklungslebenszyklus | Secure development life cycle |
| **ISO 27001** | A.8.26 | Anwendungssicherheitsanforderungen | Application security requirements |
| **ISO 27001** | A.8.27 | Sichere Systemarchitektur | Secure system architecture |
| **ISO 27001** | A.8.28 | Sichere Codierung | Secure coding |
| **ISO 27001** | A.8.29 | Sicherheitstests | Security testing in development |
| **ISO 27001** | A.8.30 | Ausgelagerte Entwicklung | Outsourced development |
| **ISO 27001** | A.8.31 | Trennung von Umgebungen | Separation of environments |
| **BSI** | CON.8 | Software-Entwicklung | Software development |
| **BSI** | APP.* | Anwendungsspezifische Bausteine | Application building blocks |

**Typische Nachweise:**
- Secure Coding Guidelines
- Code-Review-Protokolle
- SAST/DAST-Berichte
- Penetrationstest-Reports
- Change-Management-Prozess

**Hinweis:** Für Unternehmen ohne eigene Entwicklung kann M05 als "N/A" mit Begründung dokumentiert werden.

---

### M06: Bewertung der Wirksamkeit

**NIS2 Art. 21.2(f):** Konzepte und Verfahren zur Bewertung der Wirksamkeit von Risikomanagementmaßnahmen

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.35 | Unabhängige Überprüfung | Independent review |
| **ISO 27001** | A.5.36 | Konformität mit Richtlinien | Compliance with policies |
| **ISO 27001** | A.8.34 | Schutz bei Audits | Protection during audit testing |
| **BSI** | DER.3.1 | Audits und Revisionen | Audits and reviews |
| **BSI** | DER.3.2 | Revision auf Basis IS-Revision | IS revision based review |

**Typische Nachweise:**
- Penetrationstest-Berichte
- Interne Audit-Ergebnisse
- Vulnerability-Scan-Reports
- Compliance-Prüfberichte
- Management-Reviews

---

### M07: Cyberhygiene und Schulungen

**NIS2 Art. 21.2(g):** Grundlegende Verfahren der Cyberhygiene und Schulungen

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.6.3 | Sensibilisierung und Schulung | Awareness, education and training |
| **ISO 27001** | A.6.7 | Mobiles Arbeiten | Remote working |
| **BSI** | ORP.3 | Sensibilisierung und Schulung | Awareness and training |
| **BSI** | CON.7 | Informationssicherheit auf Reisen | Security during travel |

**Typische Nachweise:**
- Schulungsnachweise (Teilnehmerlisten)
- Awareness-Kampagnen-Dokumentation
- Phishing-Simulationsberichte
- E-Learning-Abschlussraten
- Richtlinie für mobiles Arbeiten

---

### M08: Kryptografie

**NIS2 Art. 21.2(h):** Konzepte und Verfahren für den Einsatz von Kryptografie und Verschlüsselung

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.8.24 | Verwendung von Kryptografie | Use of cryptography |
| **BSI** | CON.1 | Kryptokonzept | Cryptography concept |
| **BSI** | CON.2 | Datenschutz | Data protection |

**Typische Nachweise:**
- Verschlüsselungsrichtlinie
- TLS-Konfigurationsstandards
- Key-Management-Prozess
- Liste verschlüsselter Systeme/Daten
- Zertifikatsmanagement-Prozess

---

### M09: Personalsicherheit und Zugriffskontrolle

**NIS2 Art. 21.2(i):** Sicherheit des Personals, Konzepte für die Zugriffskontrolle und Anlagenmanagement

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.9 | Inventar | Inventory of assets |
| **ISO 27001** | A.5.10 | Zulässige Nutzung | Acceptable use |
| **ISO 27001** | A.5.15 | Zugriffskontrolle | Access control |
| **ISO 27001** | A.5.16 | Identitätsmanagement | Identity management |
| **ISO 27001** | A.5.17 | Authentifizierungsinformationen | Authentication information |
| **ISO 27001** | A.5.18 | Zugriffsrechte | Access rights |
| **ISO 27001** | A.6.1 | Überprüfung | Screening |
| **ISO 27001** | A.6.2 | Beschäftigungsbedingungen | Terms of employment |
| **ISO 27001** | A.6.4 | Disziplinarverfahren | Disciplinary process |
| **ISO 27001** | A.6.5 | Verantwortlichkeiten nach Beendigung | Responsibilities after termination |
| **ISO 27001** | A.7.* | Physische Sicherheit | Physical controls |
| **BSI** | ORP.2 | Personal | Personnel |
| **BSI** | ORP.4 | Identitäts- und Berechtigungsmanagement | Identity and access management |
| **BSI** | INF.* | Infrastruktur-Bausteine | Infrastructure building blocks |

**Typische Nachweise:**
- Asset-Inventar
- Berechtigungsmatrix
- Onboarding-/Offboarding-Checklisten
- Nutzungsrichtlinien
- Zutrittskontrollen-Dokumentation

---

### M10: Multi-Faktor-Authentifizierung

**NIS2 Art. 21.2(j):** Verwendung von MFA, gesicherte Kommunikation, Notfall-Kommunikation

| Framework | Reference | Control (DE) | Control (EN) |
|-----------|-----------|--------------|--------------|
| **ISO 27001** | A.5.14 | Informationsübertragung | Information transfer |
| **ISO 27001** | A.5.17 | Authentifizierungsinformationen | Authentication information |
| **ISO 27001** | A.8.5 | Sichere Authentifizierung | Secure authentication |
| **BSI** | ORP.4 | Identitäts- und Berechtigungsmanagement | Identity and access management |
| **BSI** | NET.* | Netzwerk-Bausteine | Network building blocks |

**Typische Nachweise:**
- MFA-Konfigurationsdokumentation
- Liste MFA-geschützter Systeme
- VPN-Zugangsrichtlinie
- Abdeckungsrate (% Benutzer mit MFA)
- Ausnahmen-Dokumentation

---

## Using This Mapping in ISOVA

### Linking Evidence to Multiple Frameworks

When creating evidence, link to all relevant frameworks:

```json
{
  "title": "Security Awareness Training Q1 2024",
  "evidence_type": "attestation",
  "control_ids": [
    "nis2:M07",
    "iso27001:A.6.3",
    "bsi:ORP.3"
  ]
}
```

### Benefits of Cross-Mapping

1. **Efficiency:** One evidence record covers multiple frameworks
2. **Consistency:** Same measure evaluated uniformly
3. **Reporting:** Generate SoA for any framework from same data
4. **Audit preparation:** Show controls are addressed regardless of framework focus

### Statement of Applicability (SoA) Generation

ISOVA can generate SoA documents for each framework:

```http
POST /api/v1/reports/soa
{
  "framework": "iso27001",
  "language": "de",
  "include_evidence_summary": true
}
```

The SoA will show:
- Control applicability status
- Implementation status
- Linked evidence
- Justification for exclusions

---

## Framework Versions

| Framework | Version | Status |
|-----------|---------|--------|
| NIS2 | Directive 2022/2555 | In force since 2024 |
| ISO 27001 | 2022 (93 controls) | Current |
| BSI IT-Grundschutz | Kompendium 2023 | Current |

---

## References

- [NIS2 Directive Full Text](https://eur-lex.europa.eu/eli/dir/2022/2555)
- [ISO/IEC 27001:2022](https://www.iso.org/standard/27001)
- [BSI IT-Grundschutz Kompendium](https://www.bsi.bund.de/grundschutz)
- [BSI NIS2 FAQ](https://www.bsi.bund.de/nis2)
