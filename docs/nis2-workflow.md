# NIS2 Onboarding Workflow

> Complete your NIS2 orientation in 20-30 minutes

## Overview

This workflow guides organizations through an initial NIS2 assessment using ISORA. The goal is to create a first orientation report and establish baseline documentation.

**Important:** This workflow provides orientation support. The binding NIS2 classification is made by the competent supervisory authority.

## Workflow Phases

```
┌──────────────────────────────────────────────────────────────────┐
│                    NIS2 ONBOARDING (20-30 min)                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: Classification (5 min)                                 │
│  ─────────────────────────────────────────────────               │
│  → Answer 5 questions about sector, size, revenue                │
│  → Receive orientation result                                    │
│                                                                  │
│  PHASE 2: Measure Assessment (10 min)                            │
│  ─────────────────────────────────────────────────               │
│  → Self-assess 10 NIS2 Art. 21 measures                         │
│  → Traffic light status (red/yellow/green)                       │
│                                                                  │
│  PHASE 3: First Evidence (10 min)                                │
│  ─────────────────────────────────────────────────               │
│  → Create 3 attestations for existing measures                   │
│  → Link to relevant controls                                     │
│                                                                  │
│  PHASE 4: Report (5 min)                                         │
│  ─────────────────────────────────────────────────               │
│  → Generate PDF overview                                         │
│  → Share with management                                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Phase 1: NIS2 Classification

### Classification Questions

| # | Question | Options |
|---|----------|---------|
| 1 | In welcher Branche ist Ihr Unternehmen tätig? | Energie, Verkehr, Bankwesen, Gesundheit, Trinkwasser, Digitale Infrastruktur, Verarbeitendes Gewerbe, Lebensmittel, Forschung, Öffentliche Verwaltung, Andere |
| 2 | Wie viele Mitarbeiter hat Ihr Unternehmen? | Unter 50, 50-250, Über 250 |
| 3 | Wie hoch ist Ihr Jahresumsatz? | Unter 10 Mio. EUR, 10-50 Mio. EUR, Über 50 Mio. EUR |
| 4 | Sind Sie Teil einer kritischen Lieferkette? | Ja (Zulieferer für Automotive/Energie/Gesundheit), Nein/Unsicher |
| 5 | Sind Sie als Betreiber wesentlicher Dienste benannt? | Ja (behördliche Benennung), Nein |

### Sector Classification (Annex I vs II)

**Annex I - Wesentliche Einrichtungen (Essential Entities):**
- Energie (Strom, Gas, Öl, Fernwärme, Wasserstoff)
- Verkehr (Luft, Schiene, Wasser, Straße)
- Bankwesen
- Finanzmarktinfrastruktur
- Gesundheit
- Trinkwasser
- Abwasser
- Digitale Infrastruktur
- ICT-Dienstleistungsmanagement (B2B)
- Öffentliche Verwaltung
- Weltraum

**Annex II - Wichtige Einrichtungen (Important Entities):**
- Post- und Kurierdienste
- Abfallwirtschaft
- Chemie
- Lebensmittel
- **Verarbeitendes Gewerbe / Herstellung**
- Digitale Dienste
- Forschung

### Result Interpretation

| Result | Kriterien | Konsequenzen |
|--------|-----------|--------------|
| **Wesentliche Einrichtung** | Annex I + Größenschwelle | Höhere Aufsicht, proaktive Prüfungen |
| **Wichtige Einrichtung** | Annex II + Größenschwelle | Standard NIS2-Anforderungen |
| **Möglicherweise nicht betroffen** | Unter Schwellenwerten | Kann dennoch für Lieferkette relevant sein |

**Disclaimer:** Dies ist ein Orientierungsergebnis basierend auf Ihren Eingaben. Die verbindliche Einstufung erfolgt durch die zuständige Aufsichtsbehörde.

## Phase 2: Art. 21 Measure Assessment

### The 10 NIS2 Measures (Art. 21.2)

| ID | Maßnahme (DE) | Measure (EN) | Beispiele |
|----|---------------|--------------|-----------|
| M01 | Risikoanalyse und Sicherheitskonzepte | Risk analysis and security policies | IT-Sicherheitsrichtlinie, Risikobewertung |
| M02 | Bewältigung von Sicherheitsvorfällen | Incident handling | Incident-Response-Plan, Kontaktliste |
| M03 | Business Continuity und Krisenmanagement | Business continuity | Backup, Notfallplan, Wiederherstellung |
| M04 | Sicherheit der Lieferkette | Supply chain security | Lieferantenbewertung, Sicherheitsklauseln |
| M05 | Sicherheit bei Erwerb, Entwicklung, Wartung | Secure acquisition and development | Secure Coding, Code Review |
| M06 | Bewertung der Wirksamkeit | Effectiveness assessment | Penetrationstests, Audits |
| M07 | Cyberhygiene und Schulungen | Cyber hygiene and training | Security Awareness, Phishing-Training |
| M08 | Kryptografie | Cryptography | Verschlüsselungsrichtlinie, Key Management |
| M09 | Personalsicherheit, Zugriffskontrolle | HR security, access control | Background Checks, RBAC |
| M10 | Multi-Faktor-Authentifizierung | Multi-factor authentication | MFA für kritische Systeme |

### Assessment Scale

| Status | Icon | Bedeutung | Aktion |
|--------|------|-----------|--------|
| Erfüllt | 🟢 | Maßnahme umgesetzt und dokumentiert | Pflegen, Evidenz erstellen |
| Teilweise | 🟡 | Teilweise umgesetzt oder veraltet | Verbessern, Dokumentation aktualisieren |
| Offen | 🔴 | Nicht umgesetzt | Implementation planen |
| N/A | ⚪ | Nicht anwendbar | Begründung dokumentieren |

### Quick Assessment (API)

```http
POST /api/v1/assessment/nis2/measures
Content-Type: application/json

{
  "organization_id": "org-123",
  "measures": [
    {"id": "M01", "status": "partial", "note": "IT-Richtlinie von 2019", "action": "Aktualisieren bis Q2"},
    {"id": "M02", "status": "open", "note": "Kein formaler Prozess", "priority": "high"},
    {"id": "M03", "status": "partial", "note": "Backup ja, Notfallplan nein"},
    {"id": "M04", "status": "open", "note": "Keine Lieferantenbewertung"},
    {"id": "M05", "status": "na", "note": "Keine eigene Entwicklung"},
    {"id": "M06", "status": "open", "note": "Nie getestet"},
    {"id": "M07", "status": "partial", "note": "Letzte Schulung 2022"},
    {"id": "M08", "status": "partial", "note": "TLS ja, Festplattenverschlüsselung nein"},
    {"id": "M09", "status": "fulfilled", "note": "Active Directory mit RBAC"},
    {"id": "M10", "status": "partial", "note": "MFA nur für VPN"}
  ]
}
```

## Phase 3: First Evidence

### Recommended First Attestations

These three attestations can typically be created immediately:

#### 1. Training Attestation (M07)

```yaml
evidence:
  type: attestation
  control: M07
  title: "Security Awareness Training 2024"
  statement: "Sicherheitsschulung zum Thema Phishing-Erkennung durchgeführt"
  details:
    date: "2024-01-15"
    participants: 45
    topic: "Phishing-Erkennung"
    provider: "Externer Trainer (SecAware GmbH)"
  basis: document  # Teilnehmerliste vorhanden
```

#### 2. Backup Attestation (M03)

```yaml
evidence:
  type: attestation
  control: M03
  title: "Backup-Nachweis Februar 2024"
  statement: "Vollbackup erfolgreich durchgeführt, Restore-Test bestanden"
  details:
    date: "2024-02-01"
    type: "Vollbackup"
    systems: ["ERP", "Fileserver", "Mail"]
    restore_test: true
  basis: system_log  # Backup-Log vorhanden
```

#### 3. MFA Status Attestation (M10)

```yaml
evidence:
  type: attestation
  control: M10
  title: "MFA-Status Q1 2024"
  statement: "Multi-Faktor-Authentifizierung für VPN und M365 aktiv"
  details:
    systems: ["VPN", "Microsoft 365"]
    coverage: "80%"
    method: "Authenticator App"
    exceptions_documented: true
  basis: sample  # Konfiguration stichprobenartig geprüft
```

### Creating Evidence (API)

```http
POST /api/v1/evidence
Content-Type: application/json

{
  "title": "Security Awareness Training Q1 2024",
  "description": "Jährliche Schulung zur Phishing-Erkennung für alle Mitarbeiter",
  "evidence_type": "attestation",
  "attestation_data": {
    "statement": "Sicherheitsschulung zum Thema Phishing-Erkennung durchgeführt",
    "basis": "document",
    "training_date": "2024-01-15",
    "participants": 45,
    "topic": "Phishing-Erkennung",
    "provider": "SecAware GmbH"
  },
  "valid_until": "2025-01-15T00:00:00Z",
  "control_ids": ["nis2:M07", "iso27001:A.6.3", "bsi:ORP.3"]
}
```

### Confirming Evidence

```http
POST /api/v1/evidence/{id}/confirm
Content-Type: application/json

{
  "confirmed_by_name": "Thomas Weber",
  "confirmed_by_role": "IT-Leiter"
}
```

## Phase 4: Report Generation

### Report Contents

1. **Orientierungsergebnis**
   - Sektor-Einordnung
   - Größenkategorie
   - Indikation mit Disclaimer

2. **Maßnahmenübersicht**
   - Ampelübersicht (x grün, y gelb, z rot)
   - Priorisierte Empfehlungen

3. **Evidenz-Zusammenfassung**
   - Liste erstellter Bestätigungen
   - Abdeckung pro Maßnahme

4. **Nächste Schritte**
   - Priorisierte Aktionspunkte
   - Empfohlener Zeitplan

### Generate Report (API)

```http
POST /api/v1/reports/nis2-overview
Content-Type: application/json

{
  "organization_id": "org-123",
  "format": "pdf",
  "language": "de",
  "include_evidence": true,
  "include_recommendations": true
}

Response:
{
  "report_id": "rpt-456",
  "download_url": "/api/v1/reports/rpt-456/download",
  "expires_at": "2024-02-08T14:00:00Z"
}
```

### Report Disclaimer

The following disclaimer is automatically included:

> **Hinweis:** Dieser Bericht dient der internen Orientierung und ersetzt keine rechtliche Beratung oder behördliche Einstufung. Die Maßnahmen und Bewertungen stellen die Selbsteinschätzung der Organisation zum Erstellungszeitpunkt dar.

## Timeline Summary

| Phase | Dauer | Ergebnis |
|-------|-------|----------|
| Klassifizierung | 5 min | Orientierungsergebnis |
| Assessment | 10 min | Maßnahmenübersicht |
| Erste Evidenzen | 10 min | 3 verlinkte Bestätigungen |
| Report | 5 min | PDF für Management |
| **Gesamt** | **30 min** | **Vollständige Erstorientierung** |

## After Onboarding: Next Steps

### Week 1-2
- [ ] Weitere Bestätigungen für "grüne" Maßnahmen erstellen
- [ ] PDF-Report an Geschäftsführung senden
- [ ] Rückmeldung sammeln

### Week 3-4
- [ ] Höchste Priorität "rot" Maßnahmen adressieren (M02, M04, M06)
- [ ] Quick Wins umsetzen (Schulungen planen)

### Month 2
- [ ] "Gelbe" Maßnahmen verbessern und dokumentieren
- [ ] Erste Dokumente hochladen (Policies, Logs)

### Quarterly
- [ ] Alle Bestätigungen reviewen und auffrischen
- [ ] Report aktualisieren
- [ ] Fortschritt prüfen

## Typical Results by Company Type

### Mittelstand Maschinenbau (50-250 MA)

```
Typisches Assessment-Ergebnis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Erfüllt:    1-2 (meist M09 Zugriffsrechte)
🟡 Teilweise:  4-5 (M01, M03, M07, M08, M10)
🔴 Offen:      3-4 (M02, M04, M06)
⚪ N/A:        0-1 (M05 bei keiner Entwicklung)

Quick Wins:
• M07 Schulung durchführen → 1 Tag
• M03 Notfallplan erstellen → 1 Woche
• M10 MFA ausweiten → 2 Wochen
```

### IT-Dienstleister (10-50 MA)

```
Typisches Assessment-Ergebnis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Erfüllt:    3-4 (M05, M08, M09, M10)
🟡 Teilweise:  3-4 (M01, M03, M06, M07)
🔴 Offen:      2-3 (M02, M04)
⚪ N/A:        0

Fokus:
• M04 Kundensicherheit dokumentieren
• M02 Incident-Prozess formalisieren
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/assessment/nis2/classify` | POST | NIS2 classification questions |
| `/api/v1/assessment/nis2/measures` | POST | Save measure assessment |
| `/api/v1/assessment/nis2/measures` | GET | Get current assessment |
| `/api/v1/evidence` | POST | Create evidence |
| `/api/v1/evidence/{id}/confirm` | POST | Confirm evidence |
| `/api/v1/reports/nis2-overview` | POST | Generate PDF report |

## References

- [NIS2 Directive (2022/2555)](https://eur-lex.europa.eu/eli/dir/2022/2555)
- [BSI NIS2 Information](https://www.bsi.bund.de/nis2)
- [Evidence Model Documentation](./evidence-model.md)
- [BSI/ISO/NIS2 Mapping](./bsi-mapping.md)
