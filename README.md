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
  <a href="#community-vs-enterprise-open-core">Editionen</a> •
  <a href="#für-berater-und-mssps">Partner</a> •
  <a href="#quick-start">Installation</a>
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

## Community vs. Enterprise (Open-Core)

ISORA ist **partner- und OSS-freundlich**: Die Community Edition ist mandantenfähig, damit Berater und MSSPs ISORA direkt bei Kunden einsetzen können.
Enterprise differenziert sich nicht durch „Grundfunktionen", sondern durch **Audit-Grade Capabilities**.

| Aspekt | Community (AGPL-3.0) | Enterprise (Kommerziell) |
|--------|----------------------|--------------------------|
| **Multi-Tenancy (Mandanten)** | ✅ Basic (Mandanten, Rollen, Permissions) | ✅ Advanced (SLA-Hardening, Enterprise-Policies) |
| **Core ISMS** (Assets, Risks, Controls, SoA) | ✅ Enthalten | ✅ Enthalten |
| **Evidenz (Evidence)** | ✅ Basic (Attestation + File, SHA-256, Validität) | ✅ Advanced (Approvals, Expirations, Reminders, Reviews, Audit-Pack) |
| **NIS2** | ✅ Quick Start / Basis-Flow | ✅ Full Wizard + Dashboards + Gap-Priorisierung |
| **BSI IT-Grundschutz** | ✅ Basis-Tracking | ✅ Full Wizard + Reports + Workflows |
| **PDF Reports** | — | ✅ DIN 5008 / BSI-Methodik + Branding |
| **Auditor View** | — | ✅ Read-Only Auditor Portal + Export (ZIP Audit Pack) |
| **Integrationen** | ✅ Basis (API, Webhooks) | ✅ Production Integrations (Scanner, Tickets, SIEM) |
| **AI Copilot** | — | ✅ Multi-LLM (inkl. Ollama lokal) + Governance |
| **Support** | Community (GitHub Issues) | ✅ SLA + Support (DE/EN) |
| **Code-Pflichten** | AGPL: Bei SaaS-Angebot Quellcode der Änderungen bereitstellen* | Keine AGPL-Pflichten |

*\* **Zur AGPL-Lizenz:** Wenn Sie ISORA modifizieren und als Netzwerkdienst (SaaS) anbieten, müssen Sie den Quellcode Ihrer Änderungen den Nutzern des Dienstes zugänglich machen. Rein interne Nutzung ohne Bereitstellung an Dritte löst keine Veröffentlichungspflicht aus.*

**Warum Enterprise? (5 Killer Features)**

1. **Auditor View + ZIP Audit Pack** — Revisionssichere Übergabe an externe Prüfer
2. **PDF Reports nach DIN 5008 / BSI-Methodik** — Inkl. Logo und Custom Branding
3. **Evidence Lifecycle Advanced** — Freigaben, Ablauferinnerungen, Reviews
4. **Full NIS2 + Full BSI Wizards** — Inkl. Dashboards und Priorisierung
5. **Integrationen + AI Copilot + SLA** — Enterprise-Betrieb mit garantierten Reaktionszeiten

**Hinweis:** Enterprise-Code ist separat lizenziert und nicht Teil des Open-Source-Repositories.

**Lizenzierung**: Pro Mandant/Jahr. Kontakt für Teststellung: [enterprise@isora.dev](mailto:enterprise@isora.dev)

---

## Für Berater und MSSPs

ISORA ist für den Einsatz durch Beratungsunternehmen und Managed Security Service Provider konzipiert:

- **Multi-Tenancy ab Community** — Eigene Instanz für jeden Kunden, saubere Datentrennung, kein Vendor Lock-in
- **White-Label-fähig (Enterprise)** — Eigenes Branding in Reports und Oberfläche, Ihre Marke im Vordergrund
- **Partnermodell** — Vergünstigte Enterprise-Lizenzen für Beratungspartner mit mehreren Kunden

Interesse an einer Partnerschaft? Kontakt: [partner@isora.dev](mailto:partner@isora.dev)

---

## Features

### Operativer Sicherheitsbetrieb

| Modul | Beschreibung |
|-------|--------------|
| **Incident Management** | 6-Phasen-Workflow nach NIST, Nachweiskette |
| **SOC-Modul** | Alert-Triage, Case Management, Playbooks |
| **Vulnerability Management** | CVE-Tracking, NVD/EPSS/KEV-Integration |
| **Threat Intelligence** | IOC-Verwaltung, MITRE ATT&CK Mapping |
| **Risk Management** | Risikoregister, Behandlungspläne, Heatmaps |
| **TPRM** | Lieferantenbewertung, Fragebögen |
| **CMDB** | Asset-Inventar, Abhängigkeiten |

### Compliance-Dokumentation

| Modul | Community | Enterprise |
|-------|:---------:|:----------:|
| ISO 27001:2022 (93 Kontrollen) | ✅ | ✅ |
| NIS2 Basis-Assessment | ✅ | ✅ |
| NIS2 Vollständiger Wizard | — | ✅ |
| DORA (5 Säulen, 28 Anforderungen) | — | ✅ |
| BSI IT-Grundschutz Mapping | ✅ | ✅ |
| BSI Full Wizard + Reports | — | ✅ |
| Cross-Framework Mapping | — | ✅ |

### Nachweisführung

| Funktion | Community | Enterprise |
|----------|:---------:|:----------:|
| Evidence Upload + Bestätigungen | ✅ | ✅ |
| Kontrollen-Zuordnung | ✅ | ✅ |
| ISMS ↔ SOC Bridge | ✅ | ✅ |
| SHA-256 Integritätsprüfung | ✅ | ✅ |
| Freigabe-Workflows | — | ✅ |
| Ablauferinnerungen | — | ✅ |
| Versionierung + Historie | — | ✅ |

### Plattform

| Feature | Beschreibung |
|---------|--------------|
| **Multi-Tenancy** | Mandantentrennung (Basis in Community, erweitert in Enterprise) |
| **SSO** | OAuth2/OIDC (Google, Microsoft, Okta) |
| **Audit-Logging** | Lückenlose Protokollierung aller Aktionen |
| **Dateianhänge** | Upload mit Integritätsprüfung |
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

## Zielmarkt: DACH-Region

ISORA ist für den deutschsprachigen Markt optimiert:

- **Regulatorischer Fokus** — NIS2, DORA, BSI IT-Grundschutz, ISO 27001
- **Sprache** — Vollständige deutsche Lokalisierung
- **Hosting** — Self-Hosted, DSGVO-konform
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

Die **Enterprise Edition** ist unter einer kommerziellen Lizenz verfügbar und nicht Teil dieses Repositories.

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
