# CyberOps Companion

A comprehensive CyberOps platform for managing security operations, incident response, risk management, and compliance. Built for security teams and organizations requiring a unified security operations center.

## Architecture

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui
- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL with UUID support
- **Cache**: Redis
- **Auth**: JWT with role-based access control

## Project Structure

```
cyberops-companion/
├── apps/
│   ├── web/                # Next.js Frontend
│   │   ├── app/            # App Router pages
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── lib/            # Utilities & API client
│   │   ├── stores/         # Zustand stores
│   │   └── i18n/           # Translations (DE/EN)
│   │
│   └── api/                # FastAPI Backend
│       └── src/
│           ├── api/        # API endpoints (routers)
│           ├── models/     # SQLAlchemy models
│           ├── schemas/    # Pydantic schemas
│           ├── services/   # Business logic
│           └── db/         # Database config
│
├── scripts/                # Utility scripts
│   └── init-db.sql         # Database initialization
├── data/                   # Data files (MITRE ATT&CK, etc.)
├── docker-compose.yml      # Development setup
└── docker-compose.prod.yml # Production setup
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)
- pnpm (recommended) or npm

### Development with Docker

```bash
# Clone the repository
git clone <repo-url>
cd cyberops-companion

# Copy environment file
cp .env.example .env
# Edit .env and set your SECRET_KEY and other values

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Local Development

**Backend:**

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/cyberops_companion"
export SECRET_KEY="your-secret-key"
export REDIS_URL="redis://localhost:6379/0"

uvicorn src.main:app --reload --port 8000
```

**Frontend:**

```bash
cd apps/web
pnpm install  # or npm install

# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

pnpm dev      # or npm run dev
```

## Modules

### Core Security Operations
- **Incident Management**: Full incident lifecycle with NIST-aligned phases (Preparation, Detection, Containment, Eradication, Recovery, Lessons Learned)
- **SOC Module**: Alert management, case management, and SOAR playbooks
- **Threat Intelligence Platform (TIP)**: IOC management, threat actors, campaigns, MITRE ATT&CK mapping

### Risk & Compliance
- **Vulnerability Management**: Asset-based vulnerability tracking with CVSS scoring
- **Risk Management**: Risk register, assessments, and treatment plans
- **TPRM (Third-Party Risk Management)**: Vendor risk assessments and monitoring

### Asset Management
- **CMDB**: Configuration items, software catalog, and asset relationships
- **Integrations**: API integrations with external security tools

### Reporting & Notifications
- **Reporting**: Dashboard metrics and scheduled reports
- **Notifications**: Multi-channel alerts (email, Slack, MS Teams)

### Administration
- **User Management**: Users, roles, and access control (Admin, Manager, Lead, Analyst)
- **Settings**: System configuration and preferences

## Key Features

- **Evidence Chain**: Forensic-grade logging with SHA-256 hash chain verification
- **Decision Trees**: Guided decision-making for incident response
- **Phase Checklists**: Task tracking with dependency awareness
- **Multi-framework Compliance**: BSI, NIST, ISO 27001, MITRE ATT&CK, NIS2, DORA
- **Training Simulations**: Practice IR procedures safely
- **Multi-language**: German (DE) and English (EN)
- **Dark/Light Mode**: System-aware theme switching

## User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full system access, user management |
| Manager | View all data, manage team, reports |
| Lead | Manage incidents, approve decisions |
| Analyst | Create and work on incidents/alerts |

## API Documentation

Full API documentation available at `/api/docs` (Swagger UI) or `/api/redoc` (ReDoc).

### Main API Endpoints

```
/api/v1/auth/*           - Authentication (login, register, refresh)
/api/v1/incidents/*      - Incident management
/api/v1/soc/*            - SOC (alerts, cases, playbooks)
/api/v1/threats/*        - Threat intelligence (IOCs, actors, campaigns)
/api/v1/vulnerabilities/* - Vulnerability management
/api/v1/risks/*          - Risk management
/api/v1/cmdb/*           - Configuration management
/api/v1/tprm/*           - Third-party risk management
/api/v1/integrations/*   - External integrations
/api/v1/reporting/*      - Reports and metrics
/api/v1/notifications/*  - Notification management
/api/v1/users/*          - User administration
```

## Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| SECRET_KEY | JWT signing key (generate with `openssl rand -hex 32`) | Yes |
| REDIS_URL | Redis connection string | Yes |
| CORS_ORIGINS | Allowed CORS origins | Yes |

## Known Limitations

Current MVP limitations to be aware of:

1. **No email service**: Email notifications are logged but not sent (requires SMTP configuration)
2. **No file uploads**: Evidence attachments are metadata-only (file storage not implemented)
3. **Basic search**: Full-text search is pattern-based, not indexed
4. **Single tenant**: Multi-tenancy not implemented
5. **Manual backups**: No automated backup system

## Development Status

This project is under active development. See `PLAN_ESTRATEGICO.md` for the full roadmap and strategic plan.

## Testing

```bash
# Backend tests
cd apps/api
pytest tests/ -v --cov=src

# Frontend tests (if configured)
cd apps/web
pnpm test
```

## License

AGPL-3.0 (Open Core model - see LICENSE file)
