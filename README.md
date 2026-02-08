<p align="center">
  <h1 align="center">ISORA</h1>
  <p align="center">
    <strong>ISMS Operations & Risk Assurance Platform</strong>
  </p>
  <p align="center">
    Dokumentation, Nachweisführung und Risikomanagement für regulierte Unternehmen
  </p>
</p>

<p align="center">
  <a href="#nis2-start-in-2030-minuten">NIS2 Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#quick-start">Installation</a> •
  <a href="#community-vs-enterprise">Editionen</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node">
</p>

---

## NIS2-Start in 20–30 Minuten

- **Selbsteinstufung durchführen** — Geführter Wizard zur Bestimmung Ihrer NIS2-Kategorie (wesentlich/wichtig) mit dokumentierter Begründung
- **GAP-Analyse starten** — Strukturierte Erfassung des IST-Zustands gegen die 10 Mindestmaßnahmen nach Art. 21
- **Nachweise verknüpfen** — Vorhandene Dokumente, Richtlinien und operative Aktivitäten den Anforderungen zuordnen

📖 **Dokumentation**: [NIS2 Workflow](docs/nis2-workflow.md) | [Evidence Model](docs/evidence-model.md)

---

## Compliance Disclaimer

> **ISORA ist ein Dokumentationstool. Es ersetzt keine Zertifizierung.**
>
> Verbindliche NIS2-Einstufung erfolgt durch die zuständige Aufsichtsbehörde.
>
> Bestätigungen in ISORA sind interne Dokumentation, kein Audit-Ersatz.

---

## Was ist ISORA?

ISORA (**I**SMS **O**perations & **R**isk **A**ssurance) ist eine Plattform zur strukturierten Dokumentation von Compliance-Anforderungen und deren Verknüpfung mit operativen Sicherheitsaktivitäten.

Im Unterschied zu reinen GRC-Tools, die sich auf Dokumentenverwaltung konzentrieren, verbindet ISORA ISMS-Kontrollen mit dem operativen Sicherheitsbetrieb und erzeugt nachvollziehbare Nachweise aus tatsächlichen Aktivitäten.

### Differenzierungsmerkmal: ISMS ↔ SOC Bridge

ISORA verknüpft operative Aktivitäten automatisch mit Compliance-Kontrollen:

| Aktivität | Verknüpfte Kontrolle | Generierter Nachweis |
|-----------|---------------------|---------------------|
| Incident abgeschlossen | A.5.24 (Incident Management) | Reaktionszeit, Lösungsdokumentation |
| Alert bearbeitet | A.8.16 (Monitoring) | Erkennungsmetriken |
| Schwachstellenscan durchgeführt | A.8.8 (Technische Schwachstellen) | Scan-Bericht, Behebungsstatus |
| Playbook ausgeführt | A.5.26 (Reaktion auf Vorfälle) | Automatisierungsnachweis |
| Schulung abgeschlossen | A.6.3 (Awareness) | Teilnahmebestätigung |

Diese Verknüpfung ermöglicht eine nachvollziehbare Dokumentation der Kontrollwirksamkeit auf Basis operativer Daten.

---

## Community vs Enterprise

ISORA folgt dem **Open-Core-Modell**: Die Community Edition enthält die vollständige Kernfunktionalität für ISMS-Dokumentation und operatives Sicherheitsmanagement. Die Enterprise Edition erweitert dies um geführte Compliance-Wizards und Audit-Unterstützung.

| Funktionsbereich | Community (AGPL-3.0) | Enterprise |
|------------------|:--------------------:|:----------:|
| **Kernfunktionen** | | |
| Incident Management | ✅ | ✅ |
| SOC (Alerts, Cases, Playbooks) | ✅ | ✅ |
| Vulnerability Management | ✅ | ✅ |
| Risk Management | ✅ | ✅ |
| TPRM (Third-Party Risk) | ✅ | ✅ |
| CMDB | ✅ | ✅ |
| Threat Intelligence | ✅ | ✅ |
| ISMS ↔ SOC Evidence Bridge | ✅ | ✅ |
| Multi-Tenancy | ✅ | ✅ |
| SSO (OAuth2/OIDC) | ✅ | ✅ |
| Audit-Logging | ✅ | ✅ |
| Multi-Sprache (DE/EN) | ✅ | ✅ |
| **Compliance Frameworks** | | |
| ISO 27001:2022 (Kontrollen-Tracking) | ✅ | ✅ |
| NIS2 Self-Assessment Wizard | — | ✅ |
| DORA Assessment (5 Pillars) | — | ✅ |
| BSI IT-Grundschutz Mapping | — | ✅ |
| Cross-Framework Mapping | — | ✅ |
| **Audit & Reporting** | | |
| Standard-Reports (PDF/CSV) | ✅ | ✅ |
| Auditor View (Read-Only) | — | ✅ |
| Compliance-Dashboard | — | ✅ |
| Audit-Package Export | — | ✅ |
| **Erweitert** | | |
| AI Copilot | — | ✅ |
| Scanner-Integrationen (Nessus, Qualys) | — | ✅ |
| SIEM-Anbindung | — | ✅ |
| Priority Support & SLA | — | ✅ |

**Enterprise-Lizenzierung**: Kontaktieren Sie uns für Preise und Teststellung.

---

## Features

### Compliance-Dokumentation

| Modul | Beschreibung |
|-------|--------------|
| **ISO 27001:2022** | 93 Kontrollen, strukturierte Bewertung |
| **DORA** | 5 Säulen, 28 Anforderungen, entitätsspezifisch (Enterprise) |
| **NIS2** | Einstufung wesentlich/wichtig, GAP-Analyse (Enterprise) |
| **BSI IT-Grundschutz** | Baustein-Mapping (Enterprise) |

### Operativer Sicherheitsbetrieb

| Modul | Beschreibung |
|-------|--------------|
| **Incident Management** | 6-Phasen-Workflow nach NIST, Nachweiskette |
| **SOC-Modul** | Alert-Triage, Case Management, Playbooks |
| **Vulnerability Management** | CVE-Tracking, NVD/EPSS/KEV-Integration |
| **Threat Intelligence** | IOC-Verwaltung, MITRE ATT&CK Mapping |

### Nachweisführung

| Modul | Beschreibung |
|-------|--------------|
| **Evidence Bridge** | Automatische Verknüpfung Betrieb → Kontrollen |
| **Kontrollwirksamkeit** | Berechnung aus operativen Daten |
| **BCM & Resilience** | BIA, Wiederherstellungspläne, Übungen |
| **Audit Management** | Interne/externe Audit-Dokumentation |

### Plattform

| Feature | Beschreibung |
|---------|--------------|
| **Multi-Tenancy** | Mandantentrennung |
| **SSO/SAML** | OAuth2/OIDC (Google, Microsoft, Okta) |
| **Audit-Logging** | Lückenlose Protokollierung |
| **Dateianhänge** | Upload mit SHA-256 Integritätsprüfung |
| **Mehrsprachigkeit** | Deutsch, Englisch |

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                            ISORA                                │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)                                          │
│  ├── App Router + TypeScript                                    │
│  ├── Tailwind CSS + shadcn/ui                                   │
│  └── Zustand + React Query                                      │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                              │
│  ├── SQLAlchemy 2.0 (async)                                     │
│  ├── Pydantic 2.0                                               │
│  └── 190+ REST-Endpunkte                                        │
├─────────────────────────────────────────────────────────────────┤
│  Datenbank                                                      │
│  ├── PostgreSQL 16                                              │
│  └── Redis 7 (Cache, Sessions, Rate Limiting)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Voraussetzungen

- Docker und Docker Compose
- Git

### Installation mit Docker

```bash
# Repository klonen
git clone https://github.com/fbarquez/cyberops-companion.git
cd cyberops-companion

# Umgebungsvariablen konfigurieren
cp .env.example .env

# Services starten
docker-compose up -d

# Zugriff
# Frontend: http://localhost:3000
# API-Dokumentation: http://localhost:8000/api/docs
```

### Lokale Entwicklung

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für detaillierte Anweisungen zur Entwicklungsumgebung.

---

## Projektstruktur

```
isora/
├── apps/
│   ├── api/                 # FastAPI Backend
│   │   └── src/
│   │       ├── api/         # REST-Endpunkte
│   │       ├── models/      # SQLAlchemy Models
│   │       ├── schemas/     # Pydantic Schemas
│   │       ├── services/    # Business Logic
│   │       └── tasks/       # Celery Tasks
│   │
│   └── web/                 # Next.js Frontend
│       ├── app/             # App Router
│       ├── components/      # React-Komponenten
│       └── hooks/           # Custom Hooks
│
├── docs/                    # Dokumentation
└── scripts/                 # Hilfsskripte
```

---

## Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [Projektdokumentation](docs/PROJECT_DOCUMENTATION.md) | Vollständige Übersicht |
| [NIS2 Workflow](docs/nis2-workflow.md) | NIS2-Einstufung und GAP-Analyse |
| [Evidence Model](docs/evidence-model.md) | Nachweismodell und Verknüpfungen |
| [Changelog](docs/CHANGELOG.md) | Versionshistorie |
| [API-Dokumentation](http://localhost:8000/api/docs) | OpenAPI/Swagger |

---

## Zielmarkt

ISORA ist für den deutschsprachigen Markt optimiert:

- **DACH-Region** — Deutsche Sprachunterstützung, DSGVO-konformes Hosting möglich
- **Regulatorischer Fokus** — NIS2, DORA, BSI IT-Grundschutz
- **Branchen** — Finanzdienstleistungen, Gesundheitswesen, Fertigung, kritische Infrastrukturen

---

## Contributing

Beiträge sind willkommen. Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Richtlinien.

1. Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/neue-funktion`)
3. Änderungen committen (`git commit -m 'feat: neue Funktion hinzugefügt'`)
4. Branch pushen (`git push origin feature/neue-funktion`)
5. Pull Request öffnen

---

## Lizenz

Dieses Projekt steht unter der **AGPL-3.0-Lizenz** — siehe [LICENSE](LICENSE).

Die **Enterprise Edition** ist unter einer kommerziellen Lizenz verfügbar für Organisationen, die benötigen:
- Geführte Compliance-Wizards (NIS2, DORA, BSI)
- Auditor View und Audit-Package Export
- AI Copilot
- Scanner- und SIEM-Integrationen
- Priority Support mit SLA

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Python Web Framework
- [Next.js](https://nextjs.org/) — React Framework
- [shadcn/ui](https://ui.shadcn.com/) — UI-Komponenten
- [MITRE ATT&CK](https://attack.mitre.org/) — Threat Framework

---

<p align="center">
  Entwickelt für die Anforderungen regulierter Unternehmen im DACH-Raum
</p>
