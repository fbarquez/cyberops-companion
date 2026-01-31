# Changelog

All notable changes to CyberOps Companion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- Real scanner integration (Nessus, OpenVAS, Qualys)
- Real-time WebSocket notifications
- File upload/attachment system

---

## [0.5.0] - 2026-01-31

### Added

#### UX Pattern Unification
- Created standardized shared components for consistent UI patterns
- New components:
  - `LoadingButton` - Button with built-in loading spinner
  - `FormField` - Unified form field (input, textarea, select) with label and error
  - `FormDialog` - Standardized dialog for forms with size presets
  - `ConfirmDialog` - Confirmation dialog for dangerous actions
  - `TableSkeleton` - Skeleton loading state for tables
  - `CardSkeleton` - Skeleton loading for cards
  - `StatCardSkeleton` - Skeleton for dashboard stat cards
  - `Skeleton` - Base skeleton component
- Enhanced empty state components:
  - `TableEmptyState` - Now supports icon, description, and action
  - `NoItemsEmptyState` - Preset for "no items created yet"
  - `NoResultsEmptyState` - Preset for "search returned nothing"
  - `ErrorEmptyState` - Preset for error states
- Created barrel export `components/shared/index.ts` for cleaner imports
- Created `docs/UX_PATTERNS.md` comprehensive documentation

### Documentation
- Added UX Patterns Guide with:
  - Button variants and loading states
  - Form field patterns and validation
  - Dialog sizes and structure
  - Table patterns with loading/empty states
  - Icon sizing guidelines
  - Migration guide for updating existing code

---

## [0.4.0] - 2026-01-31

### Added

#### Onboarding Flow
- Implemented 5-step onboarding wizard for new users
- Created `onboarding-store.ts` with Zustand for state management
- Persistent state with localStorage (resume if user leaves)
- Step components:
  - `WelcomeStep` - Introduction with overview of what's coming
  - `OrganizationStep` - Organization profile (name, size, industry, job title)
  - `ModulesStep` - Security module selection with recommendations
  - `TourStep` - Interactive feature tour carousel
  - `CompleteStep` - Success page with quick start actions
- Progress indicator in header showing current step
- Redirects:
  - New users (register) → Onboarding
  - Dashboard access without onboarding → Onboarding
  - Completed onboarding → Dashboard

---

## [0.3.0] - 2026-01-31

### Added

#### Landing Page
- Created professional landing page for unauthenticated users
- Components:
  - `LandingNavbar` - Responsive navigation with mobile menu
  - `HeroSection` - Value proposition with dashboard preview
  - `FeaturesSection` - Key platform capabilities (6 features)
  - `ModulesSection` - All 10 security modules showcase
  - `CTASection` - Call-to-action for trial signup
  - `Footer` - Links and social media
- Responsive design for mobile and desktop
- Dark mode support

---

## [0.2.0] - 2026-01-31

### Added

#### Celery Background Tasks
- Added Celery integration with Redis broker for background task execution
- Created `celery_app.py` with task configuration and queues
- Implemented scan execution tasks:
  - `execute_vulnerability_scan` - Run vulnerability scans in background
  - `sync_nvd_updates` - Sync CVE updates from NVD (schedulable)
  - `cancel_scan` - Cancel running or pending scans
- Implemented notification tasks:
  - `send_notification_async` - Async notification delivery
  - `send_scan_completion_notification` - Notify on scan completion
  - `cleanup_old_notifications` - Periodic cleanup task
- Added task queues: `default`, `scans`, `notifications`
- Added progress tracking with custom task states

#### New API Endpoints
- `POST /vulnerabilities/scans/{id}/cancel` - Cancel a running scan
- `GET /vulnerabilities/scans/{id}/status` - Get Celery task status

#### Docker Services
- Added `celery-worker` service for task execution
- Added `celery-beat` service for scheduled tasks

#### Database Changes
- Added `celery_task_id` field to `VulnerabilityScan` model

### Changed
- Updated `vulnerability_service.py` to trigger Celery tasks on scan start
- Updated `docker-compose.yml` with worker services

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
