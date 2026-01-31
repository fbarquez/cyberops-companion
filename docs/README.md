# CyberOps Companion Documentation

Welcome to the CyberOps Companion documentation.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Project Status](./PROJECT_STATUS.md) | Current state and progress |
| [Changelog](./CHANGELOG.md) | Version history and changes |

---

## Documentation Structure

```
docs/
├── README.md                    # This file
├── PROJECT_STATUS.md            # Current project state
├── CHANGELOG.md                 # Version history
│
├── architecture/
│   └── OVERVIEW.md              # System architecture
│
├── features/
│   ├── EMAIL_SERVICE.md         # Email/SMTP service
│   ├── NVD_API.md               # NVD/CVE integration
│   ├── ROLE_BASED_ACCESS.md     # RBAC system
│   └── I18N_TRANSLATIONS.md     # Internationalization
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
3. Review feature docs in `features/`

### For Deployment

1. Review `.env.example` for all configuration options
2. Check [Project Status](./PROJECT_STATUS.md) for deployment notes
3. See `docker-compose.yml` for container setup

---

## Feature Documentation

| Feature | Status | Documentation |
|---------|--------|---------------|
| Email Service | ✅ Complete | [EMAIL_SERVICE.md](./features/EMAIL_SERVICE.md) |
| NVD API | ✅ Complete | [NVD_API.md](./features/NVD_API.md) |
| Role-Based Access | ✅ Complete | [ROLE_BASED_ACCESS.md](./features/ROLE_BASED_ACCESS.md) |
| i18n Translations | ✅ Complete | [I18N_TRANSLATIONS.md](./features/I18N_TRANSLATIONS.md) |

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

---

## Last Updated

**2026-01-31** - Phase 0 Complete
