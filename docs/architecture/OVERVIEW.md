# Architecture Overview

**Last Updated:** 2026-02-05

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                             │
│                      (nginx/traefik)                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Frontend    │  │    Backend    │  │   Static      │
│   (Next.js)   │  │   (FastAPI)   │  │   Files       │
│   Port 3000   │  │   Port 8000   │  │               │
└───────┬───────┘  └───────┬───────┘  └───────────────┘
        │                  │
        │                  ├──────────────────┐
        │                  │                  │
        │                  ▼                  ▼
        │          ┌───────────────┐  ┌───────────────┐
        │          │  PostgreSQL   │  │    Redis      │
        │          │   Port 5432   │  │   Port 6379   │
        │          └───────────────┘  └───────────────┘
        │
        └──────────► Browser
```

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 15+ |
| Cache | Redis | 7+ |
| Auth | JWT (PyJWT) | - |
| Email | aiosmtplib | 2.0+ |
| Validation | Pydantic | 2.0+ |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 14+ |
| UI Library | shadcn/ui | - |
| Styling | Tailwind CSS | 3+ |
| State | React Query | 5+ |
| i18n | next-intl | - |
| Charts | Recharts | - |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Containerization | Docker |
| Orchestration | Docker Compose |
| Reverse Proxy | Nginx (optional) |

---

## Directory Structure

```
cyberops-companion/
├── apps/
│   ├── api/                    # FastAPI Backend
│   │   ├── src/
│   │   │   ├── api/           # API routes
│   │   │   │   ├── deps.py    # Dependencies (auth, db)
│   │   │   │   └── v1/        # API version 1
│   │   │   ├── db/            # Database setup
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   ├── services/      # Business logic
│   │   │   ├── templates/     # Email templates
│   │   │   ├── config.py      # Settings
│   │   │   └── main.py        # App entry point
│   │   ├── alembic/           # Database migrations
│   │   ├── tests/             # API tests
│   │   └── requirements.txt
│   │
│   └── web/                    # Next.js Frontend
│       ├── src/
│       │   ├── app/           # App router pages
│       │   ├── components/    # React components
│       │   ├── hooks/         # Custom hooks
│       │   ├── lib/           # Utilities
│       │   ├── providers/     # Context providers
│       │   └── i18n/          # Translations
│       ├── public/            # Static assets
│       └── package.json
│
├── docs/                       # Documentation
│   ├── architecture/
│   ├── features/
│   ├── changelog/
│   └── api/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Data Flow

### Authentication Flow
```
1. User submits credentials
2. Backend validates against database
3. JWT token generated with user info + role
4. Token returned to frontend
5. Frontend stores token in cookies
6. Subsequent requests include token in header
7. Backend validates token on each request
```

### API Request Flow
```
Request → Router → Dependencies → Service → Database
                        │
                   Auth Check
                   DB Session
                   Role Check
```

---

## Database Schema (Key Tables)

```
users
├── id (UUID)
├── email
├── username
├── password_hash
├── role (enum)
└── is_active

incidents
├── id (UUID)
├── title
├── description
├── severity
├── status
├── created_by → users.id
└── assigned_to → users.id

vulnerabilities
├── id (UUID)
├── cve_id
├── title
├── cvss_score
├── severity
└── status

assets (CMDB)
├── id (UUID)
├── name
├── asset_type
├── criticality
└── owner

notifications
├── id (UUID)
├── user_id → users.id
├── type
├── priority
├── title
├── message
└── read_at

documents
├── id (UUID)
├── document_id (auto: POL-001)
├── title
├── category (policy, procedure, etc.)
├── status (draft → published)
├── content (markdown)
├── owner_id → users.id
├── frameworks (JSON)
└── requires_acknowledgment
```

---

## API Structure

### Base URL
```
/api/v1/
```

### Endpoints by Module
| Module | Prefix | Description |
|--------|--------|-------------|
| Auth | `/auth` | Login, register, refresh |
| Users | `/users` | User management |
| Incidents | `/incidents` | Incident response |
| SOC | `/soc` | Alerts, cases |
| Vulnerabilities | `/vulnerabilities` | CVE tracking |
| Risks | `/risks` | Risk register |
| Attack Paths | `/attack-paths` | Attack path analysis |
| TPRM | `/tprm` | Vendor management |
| Compliance | `/compliance` | Frameworks |
| Documents | `/documents` | Policies & document management |
| CMDB | `/cmdb` | Asset inventory |
| Threats | `/threats` | Threat catalog |
| Integrations | `/integrations` | External platforms |
| Notifications | `/notifications` | User notifications |
| Reporting | `/reporting` | Reports, dashboards |

---

## Security Measures

| Layer | Measure |
|-------|---------|
| Transport | HTTPS (TLS 1.3) |
| Auth | JWT with short expiry |
| Password | bcrypt hashing |
| API | Rate limiting |
| Input | Pydantic validation |
| SQL | SQLAlchemy ORM (no raw SQL) |
| CORS | Configured origins only |
| Secrets | Environment variables |

---

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Redis for session/cache sharing
- Database connection pooling

### Vertical Scaling
- Async I/O throughout
- Connection pooling
- Query optimization

### Future Improvements
- Celery for background tasks
- WebSocket for real-time updates
- Read replicas for database
- CDN for static assets
