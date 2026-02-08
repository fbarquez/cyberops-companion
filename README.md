<p align="center">
  <h1 align="center">ISORA</h1>
  <p align="center">
    <strong>ISMS Operations & Risk Assurance Platform</strong>
  </p>
  <p align="center">
    <em>ISMS-Anforderungen in überprüfbare Aktivitäten und Evidenzen</em>
  </p>
  <p align="center">
    Unified platform for Compliance Operations, Risk Management, and Security Assurance
  </p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Docs</a> •
  <a href="#community-vs-enterprise">Editions</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

---

## What is ISORA?

ISORA (**I**SMS **O**perations & **R**isk **A**ssurance) is a comprehensive platform that bridges the gap between compliance requirements and operational security. Unlike traditional GRC tools that focus solely on documentation, ISORA connects your ISMS controls directly to security operations, generating verifiable evidence from real activities.

### Key Differentiator: ISMS ↔ SOC Bridge

ISORA automatically links operational activities to compliance controls:

| When this happens... | ISORA links to... | Evidence generated |
|---------------------|-------------------|-------------------|
| Incident resolved | A.5.24 (Incident Management) | Response time, resolution proof |
| Alert triaged | A.8.16 (Monitoring) | Detection metrics |
| Vulnerability scanned | A.8.8 (Technical Vulnerabilities) | Scan reports, remediation tracking |
| Playbook executed | A.5.26 (Response to Incidents) | Automation evidence |
| Training completed | A.6.3 (Awareness) | Completion certificates |

---

## Community vs Enterprise

ISORA follows an **Open Core** model:

| Feature | Community (Free) | Enterprise |
|---------|:----------------:|:----------:|
| Incident Management | ✅ | ✅ |
| SOC (Alerts, Cases, Playbooks) | ✅ | ✅ |
| Vulnerability Management | ✅ | ✅ |
| Risk Management | ✅ | ✅ |
| TPRM (Third-Party Risk) | ✅ | ✅ |
| CMDB | ✅ | ✅ |
| Threat Intelligence | ✅ | ✅ |
| ISO 27001:2022 Compliance | ✅ | ✅ |
| ISMS ↔ SOC Evidence Bridge | ✅ | ✅ |
| Multi-language (EN/DE) | ✅ | ✅ |
| SSO/SAML | ✅ | ✅ |
| Multi-tenancy | ✅ | ✅ |
| **AI Copilot** | ❌ | ✅ |
| **DORA Compliance** | ❌ | ✅ |
| **NIS2 Assessment** | ❌ | ✅ |
| **BSI IT-Grundschutz** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |

**Interested in Enterprise?** Contact us for licensing options.

---

## Features

### Compliance Layer (ISMS)

| Module | Description |
|--------|-------------|
| **ISO 27001:2022** | 93 controls, 6-step assessment wizard |
| **DORA** | 5 pillars, 28 requirements, entity-type aware |
| **NIS2** | Essential/Important entity classification |
| **BSI IT-Grundschutz** | German standard compliance |
| **Onboarding Wizard** | Auto-detect applicable regulations |

### Operations Layer (SOC)

| Module | Description |
|--------|-------------|
| **Incident Management** | 6-phase NIST workflow, evidence chain |
| **SOC Module** | Alert triage, case management, playbooks |
| **Vulnerability Management** | CVE tracking, NVD/EPSS/KEV integration |
| **Threat Intelligence** | IOC management, MITRE ATT&CK mapping |

### Assurance Layer (Evidence)

| Module | Description |
|--------|-------------|
| **Evidence Bridge** | Auto-link operations to controls |
| **Control Effectiveness** | Calculated from real operational data |
| **BCM & Resilience** | BIA, recovery plans, exercises |
| **Audit Management** | Internal/external audit tracking |

### Platform Features

| Feature | Description |
|---------|-------------|
| **Multi-tenancy** | Complete data isolation per organization |
| **SSO/SAML** | OAuth2/OIDC with Google, Microsoft, Okta |
| **Audit Logging** | Comprehensive audit trail |
| **Real-time Updates** | WebSocket notifications |
| **File Attachments** | Evidence upload with SHA-256 integrity |
| **i18n** | Multi-language support (EN/DE) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                            ISORA                                 │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)                                          │
│  ├── App Router + TypeScript                                    │
│  ├── Tailwind CSS + shadcn/ui                                   │
│  └── Zustand + React Query                                      │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                              │
│  ├── SQLAlchemy 2.0 (async)                                     │
│  ├── Pydantic 2.0 validation                                    │
│  └── 190+ REST endpoints                                        │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── PostgreSQL 16 (primary database)                           │
│  └── Redis 7 (cache, sessions, rate limiting)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/fbarquez/cyberops-companion.git
cd cyberops-companion

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

### Local Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup instructions.

---

## Project Structure

```
isora/
├── apps/
│   ├── api/                 # FastAPI Backend
│   │   └── src/
│   │       ├── api/         # REST endpoints
│   │       ├── models/      # SQLAlchemy models
│   │       ├── schemas/     # Pydantic schemas
│   │       ├── services/    # Business logic
│   │       └── tasks/       # Celery tasks
│   │
│   └── web/                 # Next.js Frontend
│       ├── app/             # App Router pages
│       ├── components/      # React components
│       └── hooks/           # Custom hooks
│
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Project Documentation](docs/PROJECT_DOCUMENTATION.md) | Complete project overview |
| [Changelog](docs/CHANGELOG.md) | Version history |
| [API Documentation](http://localhost:8000/api/docs) | OpenAPI/Swagger |

### Feature Documentation

- [ISO 27001:2022 Compliance](docs/features/ISO27001.md)
- [Multi-tenancy](docs/features/MULTI_TENANCY.md)
- [SSO/SAML](docs/features/SSO_SAML.md)
- [Audit Logging](docs/features/AUDIT_LOGGING.md)

---

## Target Market: DACH Region

ISORA is optimized for German-speaking markets (DACH):

- **DE/AT/CH** - Native German language support
- **Regulatory Focus** - DORA, NIS2, BSI IT-Grundschutz, KRITIS
- **Industry Verticals** - Financial services, healthcare, manufacturing

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **AGPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

**Enterprise Edition** is available under a commercial license for organizations requiring:
- AI Copilot features
- DORA / NIS2 / BSI IT-Grundschutz modules
- Priority support and SLA guarantees

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [MITRE ATT&CK](https://attack.mitre.org/) - Threat framework

---

<p align="center">
  Made with dedication for the cybersecurity community
</p>
