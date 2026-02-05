<p align="center">
  <h1 align="center">CyberOps Companion</h1>
  <p align="center">
    <strong>Open-Source Cybersecurity Operations Platform</strong>
  </p>
  <p align="center">
    Unified platform for Security Operations, Incident Response, Risk Management, and Compliance
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

## What is CyberOps Companion?

CyberOps Companion is a comprehensive, open-source cybersecurity operations platform designed for security teams and organizations. It provides a unified interface for managing:

- **Incident Response** - Full lifecycle management with NIST-aligned phases
- **SOC Operations** - Alert triage, case management, and SOAR playbooks
- **Vulnerability Management** - CVE tracking with NVD integration
- **Risk Management** - Risk register with FAIR methodology
- **Compliance** - Multi-framework support (NIST, ISO 27001)
- **Threat Intelligence** - IOC management and MITRE ATT&CK mapping

---

## Community vs Enterprise

CyberOps Companion follows an **Open Core** model:

| Feature | Community (Free) | Enterprise |
|---------|:----------------:|:----------:|
| Incident Management | ✅ | ✅ |
| SOC (Alerts, Cases, Playbooks) | ✅ | ✅ |
| Vulnerability Management | ✅ | ✅ |
| Risk Management | ✅ | ✅ |
| TPRM (Third-Party Risk) | ✅ | ✅ |
| CMDB | ✅ | ✅ |
| Threat Intelligence | ✅ | ✅ |
| Compliance (NIST, ISO 27001) | ✅ | ✅ |
| Reporting & Analytics | ✅ | ✅ |
| WebSocket Notifications | ✅ | ✅ |
| File Attachments | ✅ | ✅ |
| Multi-language (EN/DE) | ✅ | ✅ |
| RBAC (Role-Based Access) | ✅ | ✅ |
| SSO/SAML | ✅ | ✅ |
| Multi-tenancy | ✅ | ✅ |
| Audit Logging | ✅ | ✅ |
| **AI Copilot** | ❌ | ✅ |
| **BSI IT-Grundschutz** | ❌ | ✅ |
| **NIS2 Assessment** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |
| **SLA Guarantee** | ❌ | ✅ |

**Interested in Enterprise?** Contact us for licensing options.

---

## Features

### Core Modules

| Module | Description |
|--------|-------------|
| **Incident Management** | 6-phase NIST workflow, evidence chain, decision trees, checklists |
| **SOC Module** | Alert management, case correlation, playbook automation, MTTD/MTTR metrics |
| **Vulnerability Management** | CVE tracking, NVD/EPSS/KEV integration, CVSS scoring |
| **Risk Management** | Risk register, FAIR methodology, Monte Carlo simulations |
| **TPRM** | Third-party risk assessments, vendor management |
| **CMDB** | Configuration items, asset inventory, relationships |
| **Compliance** | NIST CSF, ISO 27001:2022 (93 controls, 6-step wizard) |
| **Threat Intelligence** | IOC management, threat actors, campaigns, MITRE ATT&CK |

### Platform Features

| Feature | Description |
|---------|-------------|
| **Multi-tenancy** | Complete data isolation per organization |
| **SSO/SAML** | OAuth2/OIDC with Google, Microsoft, Okta |
| **Audit Logging** | Comprehensive audit trail for compliance |
| **Rate Limiting** | Redis-based API protection |
| **RBAC** | Role-based access control (Admin, Manager, Lead, Analyst) |
| **Real-time Updates** | WebSocket notifications |
| **File Attachments** | Evidence upload with SHA-256 integrity |
| **i18n** | Multi-language support (EN/DE) |

### Technical Highlights

- **Evidence Chain**: Forensic-grade logging with SHA-256 hash verification
- **Background Tasks**: Celery-powered async operations
- **Real-time**: WebSocket notifications for instant updates
- **API-first**: 185+ REST endpoints with OpenAPI documentation
- **Modern Stack**: FastAPI + Next.js 14 + PostgreSQL + Redis

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CyberOps Companion                        │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)                                          │
│  ├── App Router + TypeScript                                    │
│  ├── Tailwind CSS + shadcn/ui                                   │
│  ├── Zustand + React Query                                      │
│  └── Real-time WebSocket                                        │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                              │
│  ├── SQLAlchemy 2.0 (async)                                     │
│  ├── Pydantic 2.0 validation                                    │
│  ├── JWT + RBAC authentication                                  │
│  └── Celery background tasks                                    │
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
cyberops-companion/
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
│       ├── hooks/           # Custom hooks
│       └── lib/             # Utilities
│
├── docs/                    # Documentation
├── data/                    # Data files (MITRE, templates)
└── scripts/                 # Utility scripts
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Project Status](docs/PROJECT_STATUS.md) | Current development status |
| [Changelog](docs/CHANGELOG.md) | Version history |
| [Future Roadmap](docs/FUTURE_ROADMAP.md) | Planned features |
| [API Documentation](http://localhost:8000/api/docs) | OpenAPI/Swagger |

### Feature Documentation

- [ISO 27001:2022 Compliance](docs/features/ISO27001.md)
- [Multi-tenancy](docs/features/MULTI_TENANCY.md)
- [SSO/SAML](docs/features/SSO_SAML.md)
- [Rate Limiting](docs/features/RATE_LIMITING.md)
- [Audit Logging](docs/features/AUDIT_LOGGING.md)
- [WebSocket Notifications](docs/features/WEBSOCKET_NOTIFICATIONS.md)
- [File Uploads](docs/features/FILE_UPLOADS.md)

---

## Roadmap

### Completed

- [x] **Phase 0**: Foundation (i18n, Email, NVD API, RBAC)
- [x] **Phase 1**: Enhanced Features (Celery, Onboarding, Landing Page)
- [x] **Phase 2**: Advanced Features (WebSockets, File Uploads, Analytics, Mobile)
- [x] **Phase 3**: Enterprise Features (Multi-tenancy, SSO, Audit, Rate Limiting)

### Planned (Community)

- [ ] ML-based anomaly detection
- [ ] Predictive incident analytics
- [ ] Additional compliance frameworks

### Enterprise Only

- [ ] AI Copilot (multi-LLM support)
- [ ] BSI IT-Grundschutz compliance
- [ ] NIS2 Directive assessment

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

## Community

- [GitHub Issues](../../issues) - Bug reports and feature requests
- [GitHub Discussions](../../discussions) - Questions and ideas

---

## License

This project is licensed under the **AGPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

### What this means

- You can use, modify, and distribute this software
- If you modify and distribute, you must share your changes under AGPL-3.0
- Network use (SaaS) requires sharing source code with users

**Enterprise Edition** is available under a commercial license for organizations requiring:
- AI Copilot features
- BSI IT-Grundschutz / NIS2 compliance modules
- Priority support and SLA guarantees

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [MITRE ATT&CK](https://attack.mitre.org/) - Threat framework
- [NIST](https://www.nist.gov/) - Cybersecurity frameworks

---

<p align="center">
  Made with dedication for the cybersecurity community
</p>
