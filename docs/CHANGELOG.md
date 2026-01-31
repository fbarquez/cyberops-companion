# Changelog

All notable changes to CyberOps Companion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- Celery integration for background scan execution
- Landing page for unauthenticated users
- In-app onboarding flow
- UX pattern unification

---

## [0.1.0] - 2026-01-31

### Added

#### Role-Based Access Control (RBAC)
- Implemented typed role dependencies (`AdminUser`, `ManagerUser`, `LeadUser`)
- Added role checks to notification endpoints:
  - `POST /notifications/send` - Admin only
  - `POST /notifications/cleanup` - Admin only
  - `POST /notifications/email/test` - Admin only
  - `GET /notifications/email/status` - Admin only
- Added role checks to integration endpoints:
  - `POST /integrations` - Admin only
  - `PUT /integrations/{id}` - Admin only
  - `DELETE /integrations/{id}` - Admin only
  - `POST /integrations/{id}/enable` - Admin only
  - `POST /integrations/{id}/disable` - Admin only
  - `POST /integrations/test-connection` - Admin only
  - `POST /integrations/templates/seed` - Admin only
  - `POST /integrations/{id}/sync` - Manager+
- Added role checks to reporting endpoints:
  - `POST /reporting/templates` - Manager+
  - `PUT /reporting/templates/{id}` - Manager+
  - `POST /reporting/templates/seed` - Admin only
  - `POST /reporting/schedules` - Manager+

#### NVD API Integration
- Created `nvd_service.py` with comprehensive CVE lookup
- NVD API 2.0 integration for CVE details
- EPSS (Exploit Prediction Scoring System) integration
- CISA KEV (Known Exploited Vulnerabilities) catalog integration
- CVE enrichment with automatic database updates
- New API endpoints:
  - `GET /vulnerabilities/cve/{cve_id}` - Lookup CVE details
  - `POST /vulnerabilities/cve/{cve_id}/enrich` - Enrich CVE data
  - `GET /vulnerabilities/cve/search/` - Search CVEs
  - `GET /vulnerabilities/kev/catalog` - Get KEV catalog
  - `GET /vulnerabilities/nvd/status` - Check NVD service status

#### Email Service
- Created `email_service.py` with async SMTP support
- Uses `aiosmtplib` for non-blocking email sending
- HTML email templates with Jinja2
- Created `templates/email/notification.html` responsive template
- Priority-based styling (critical/high = red, medium = yellow, low = blue)
- Test email endpoint for configuration verification
- New API endpoints:
  - `POST /notifications/email/test` - Send test email
  - `GET /notifications/email/status` - Check email configuration

#### Configuration
- Added `NVD_API_KEY` setting for NVD API authentication
- Added `FRONTEND_URL` setting for email links
- Added SMTP configuration settings:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
  - `SMTP_FROM`, `SMTP_FROM_NAME`
  - `SMTP_TLS`, `SMTP_SSL`
  - `EMAIL_ENABLED`

#### Internationalization (i18n)
- Migrated all page translations to new namespace structure
- Added translations for all modules (EN/DE):
  - SOC (alerts, cases, investigations)
  - CMDB (assets, relationships)
  - Threats
  - Risks
  - Vulnerabilities
  - TPRM (vendors, assessments)
  - Integrations
  - Reporting
  - Users
  - Notifications
  - Incidents
  - Simulation
  - Lessons Learned
  - Templates
  - Navigator
  - Playbook

### Changed
- Updated `notification_service.py` to use new email service
- Updated `vulnerability_service.py` with NVD integration methods
- Updated `.env.example` with all new configuration options

### Fixed
- Removed outdated TODO comments in notification service
- Fixed hardcoded frontend URL to use `FRONTEND_URL` config

---

## [0.0.1] - 2026-01-30

### Added
- Initial project setup (migrated from IR Companion)
- Complete backend API with FastAPI
- Complete frontend with Next.js
- Database models for all modules
- Basic authentication with JWT
- Docker Compose configuration
- GitHub repository initialization

### Renamed
- Project renamed from "IR Companion" to "CyberOps Companion"
- Updated all references in code, configs, and documentation
