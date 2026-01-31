# Changelog

All notable changes to CyberOps Companion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned (Phase 2 Remaining)
- Mobile responsive improvements

### Planned (Phase 3 - Enterprise)
- Multi-tenancy support
- SSO/SAML integration (Azure AD, Okta, etc.)
- Audit logging system
- API rate limiting

### Planned (Future)
- ML/Predictive Analytics (Phase 2C - when more data is available)
- Real scanner integration (Nessus, OpenVAS, Qualys)
- Anomaly detection
- Incident prediction

See [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) for detailed specifications.

---

## [0.8.0] - 2026-01-31

### Added

#### Advanced Analytics System (Phase 2A + 2B)

**Backend Services:**
- `AnalyticsService` - Trend analysis, distributions, heatmaps
- `SecurityScoreService` - Weighted security posture scoring (0-100)
- `SLAService` - Response and remediation SLA tracking
- `AnalystMetricsService` - SOC analyst performance metrics

**New API Endpoints:**
- `GET /api/v1/analytics/trends/{entity}/{metric}` - Time-series trend data
- `GET /api/v1/analytics/distribution/{entity}/{group_by}` - Distribution analysis
- `GET /api/v1/analytics/heatmap/{type}` - Risk matrix and time-based heatmaps
- `GET /api/v1/analytics/security-score` - Overall security score with component breakdown
- `GET /api/v1/analytics/security-score/history` - Score history for trends
- `GET /api/v1/analytics/sla/compliance/{type}` - SLA compliance metrics
- `GET /api/v1/analytics/sla/breaches` - List of SLA breaches
- `GET /api/v1/analytics/analysts/metrics` - Analyst workload and performance
- `GET /api/v1/analytics/analysts/leaderboard` - Top performers
- `GET /api/v1/analytics/vulnerabilities/aging` - Vulnerability aging buckets
- `GET /api/v1/analytics/risks/trends` - Risk velocity and mitigation trends

**Frontend Chart Components:**
- `TrendLineChart` - Line/area charts with gradients
- `DistributionChart` - Bar charts (horizontal/vertical)
- `PieChart` / `DonutChart` - Pie and donut charts
- `RiskHeatMap` - 5x5 risk matrix with click handlers
- `SparkLine` - Inline trend indicators
- `TrendIndicator` - Value with trend arrow

**Frontend Widget Components:**
- `TrendCard` - Metric card with sparkline
- `ChartCard` - Container with header, actions, loading state
- `ScoreGaugeCard` - Circular gauge for security score
- `SLAStatusCard` - SLA compliance summary

**React Hooks:**
- `useTrend` - Trend data fetching
- `useDistribution` - Distribution data fetching
- `useHeatmap` - Heatmap data fetching
- `useSecurityScore` - Security score with auto-refresh
- `useSLACompliance` - SLA compliance metrics
- `useAnalystMetrics` - Analyst performance data
- `useVulnerabilityAging` - Vulnerability aging buckets
- `useRiskTrends` - Risk trend analysis

**Security Score Components (weighted):**
| Component | Weight |
|-----------|--------|
| Vulnerabilities | 25% |
| Incidents | 20% |
| Compliance | 20% |
| Risks | 15% |
| SOC Operations | 10% |
| Patch Compliance | 10% |

**SLA Targets (default):**
| Severity | Response | Remediation |
|----------|----------|-------------|
| Critical | 15 min | 1 day |
| High | 1 hour | 7 days |
| Medium | 4 hours | 30 days |
| Low | 8 hours | 90 days |

**Dashboard Integrations:**
- `/reporting` - Security score gauge, SLA compliance, trend charts, distributions
- `/soc` - Alert trends, response SLA, analyst workload visualization
- `/risks` - 5x5 risk heatmap, risk trends over time

**Utilities:**
- `chart-colors.ts` - Consistent color palettes (severity, status, trends, gradients)

### Documentation
- Added `docs/ANALYTICS.md` with full API reference and component usage
- Added `docs/FUTURE_ROADMAP.md` with planned features and technical debt
- Updated `docs/README.md` with complete documentation structure
- Updated `docs/PROJECT_STATUS.md` with implementation details

---

## [0.7.0] - 2026-01-31

### Added

#### File Upload/Attachment System
- Full file attachment support for incidents, cases, vulnerabilities, and other entities
- Backend:
  - `Attachment` model with SHA-256 hash verification
  - `StorageService` with pluggable storage backends
  - `LocalStorageBackend` for filesystem storage
  - `S3StorageBackend` for AWS S3 and S3-compatible services (MinIO)
  - File validation (size limits, allowed extensions)
  - Duplicate detection by file hash
  - Soft delete with optional permanent deletion
  - Download tracking (count, last downloaded)
- Frontend:
  - `FileUpload` component with drag-and-drop (react-dropzone)
  - `useAttachments` hook for file management
  - Category selection (evidence, screenshot, log_file, pcap, etc.)
  - Upload progress indicators
  - File list with download/delete/verify actions
  - Integrity verification UI
- API endpoints:
  - `POST /api/v1/attachments/upload/{entity_type}/{entity_id}` - Upload file
  - `GET /api/v1/attachments/{entity_type}/{entity_id}` - List attachments
  - `GET /api/v1/attachments/download/{id}` - Download file
  - `DELETE /api/v1/attachments/{id}` - Delete attachment
  - `POST /api/v1/attachments/verify/{id}` - Verify file integrity
- Configuration options:
  - `STORAGE_BACKEND` - "local" or "s3"
  - `STORAGE_LOCAL_PATH` - Local storage directory
  - `STORAGE_MAX_FILE_SIZE_MB` - Maximum file size (default 50MB)
  - `STORAGE_ALLOWED_EXTENSIONS` - Whitelist of allowed file types
  - S3 configuration: bucket, region, credentials, endpoint URL
- Integration with Evidence page (new Attachments tab)

### Documentation
- Added `docs/features/FILE_UPLOADS.md` with full architecture and usage guide

---

## [0.6.0] - 2026-01-31

### Added

#### WebSocket Notifications
- Real-time notification delivery via WebSocket
- Backend:
  - `NotificationConnectionManager` - Manages user WebSocket connections
  - Supports multiple connections per user (tabs/devices)
  - JWT authentication via query parameter
  - Automatic dead connection cleanup
  - Integration with NotificationService for broadcast on creation
- Frontend:
  - `useNotificationWebSocket` hook with auto-reconnect
  - `NotificationBell` component in header
  - Unread count badge with real-time updates
  - Toast notifications for new alerts
  - Connection status indicator
- WebSocket endpoint: `/api/v1/ws/notifications?token=<jwt>`
- Events: notification:new, stats:updated, connection:established
- Ping/pong keep-alive (30 second interval)

### Documentation
- Added `docs/features/WEBSOCKET_NOTIFICATIONS.md` with full architecture

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
