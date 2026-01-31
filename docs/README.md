# CyberOps Companion Documentation

Welcome to the CyberOps Companion documentation.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Project Status](./PROJECT_STATUS.md) | Current state and progress |
| [Changelog](./CHANGELOG.md) | Version history and changes |
| [UX Patterns](./UX_PATTERNS.md) | UI/UX component guidelines |

---

## Documentation Structure

```
docs/
├── README.md                    # This file
├── PROJECT_STATUS.md            # Current project state
├── CHANGELOG.md                 # Version history
├── UX_PATTERNS.md               # UI/UX guidelines
│
├── architecture/
│   └── OVERVIEW.md              # System architecture
│
├── features/
│   ├── CELERY_TASKS.md          # Background task execution
│   ├── EMAIL_SERVICE.md         # Email/SMTP service
│   ├── I18N_TRANSLATIONS.md     # Internationalization
│   ├── LANDING_PAGE.md          # Public landing page
│   ├── NVD_API.md               # NVD/CVE integration
│   ├── ONBOARDING.md            # User onboarding flow
│   └── ROLE_BASED_ACCESS.md     # RBAC system
│
├── api/                         # API documentation
│   └── (auto-generated)
│
└── changelog/                   # Detailed changelogs
```

---

## Getting Started

### For Developers

1. Read [Architecture Overview](./architecture/OVERVIEW.md)
2. Check [Project Status](./PROJECT_STATUS.md) for current state
3. Review [UX Patterns](./UX_PATTERNS.md) for UI guidelines
4. Review feature docs in `features/`

### For Deployment

1. Review `.env.example` for all configuration options
2. Check [Project Status](./PROJECT_STATUS.md) for deployment notes
3. See `docker-compose.yml` for container setup

---

## Feature Documentation

### Phase 0 - Foundation

| Feature | Status | Documentation |
|---------|--------|---------------|
| Email Service | ✅ Complete | [EMAIL_SERVICE.md](./features/EMAIL_SERVICE.md) |
| NVD API | ✅ Complete | [NVD_API.md](./features/NVD_API.md) |
| Role-Based Access | ✅ Complete | [ROLE_BASED_ACCESS.md](./features/ROLE_BASED_ACCESS.md) |
| i18n Translations | ✅ Complete | [I18N_TRANSLATIONS.md](./features/I18N_TRANSLATIONS.md) |

### Phase 1 - Enhanced Features

| Feature | Status | Documentation |
|---------|--------|---------------|
| Celery Tasks | ✅ Complete | [CELERY_TASKS.md](./features/CELERY_TASKS.md) |
| Landing Page | ✅ Complete | [LANDING_PAGE.md](./features/LANDING_PAGE.md) |
| Onboarding Flow | ✅ Complete | [ONBOARDING.md](./features/ONBOARDING.md) |
| UX Patterns | ✅ Complete | [UX_PATTERNS.md](./UX_PATTERNS.md) |

---

## API Documentation

When running in development, access interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Contributing

When adding new features:

1. Create feature documentation in `docs/features/`
2. Update `PROJECT_STATUS.md` with current state
3. Add entry to `CHANGELOG.md`
4. Update this README if needed
5. Follow [UX Patterns](./UX_PATTERNS.md) for UI components

---

## Last Updated

**2026-01-31** - Phase 1 Complete
