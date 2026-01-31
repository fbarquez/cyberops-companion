# Changelog

All notable changes to CyberOps Companion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned (Phase 3 - Enterprise)
- Multi-tenancy support
- SSO/SAML integration (Azure AD, Okta, etc.)
- API rate limiting

### Planned (Future)
- ML/Predictive Analytics (Phase 2C - when more data is available)
- Real scanner integration (Nessus, OpenVAS, Qualys)
- Anomaly detection
- Incident prediction

See [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) for detailed specifications.

---

## [0.10.0] - 2026-01-31

### Added

#### Audit Logging System (Phase 3)

Complete audit trail system for compliance and forensics.

**Backend:**
- Enhanced `ActivityLog` model with new fields:
  - `action_category` - Categorization (auth, crud, data, system)
  - `resource_name` - Human-readable resource name
  - `changes_summary` - Auto-generated change description
  - `request_id` - Request correlation ID
  - `severity` - Log severity (info, warning, critical)
  - Database indices for performance
- `AuditService` (`services/audit_service.py`):
  - `log_action()` - Create audit log entries
  - `list_logs()` - Query with filters and pagination
  - `get_stats()` - Aggregate statistics
  - `export_logs()` - Export to CSV/JSON
  - Automatic sensitive data filtering (passwords, tokens, etc.)
  - Auto-generated severity based on action type
  - Auto-generated changes summary for updates
- `audit_decorator.py` - Decorator for automatic endpoint logging
- Pydantic schemas (`schemas/audit.py`):
  - `ActivityLogResponse`, `ActivityLogDetailResponse`
  - `ActivityLogListResponse`, `AuditStatsResponse`
  - `AuditExportRequest`, `AuditLogFilter`

**API Endpoints:**
- `GET /api/v1/audit/logs` - List logs with filters and pagination
- `GET /api/v1/audit/logs/{id}` - Get log detail with old/new values
- `GET /api/v1/audit/stats` - Statistics (admin only)
- `POST /api/v1/audit/export` - Export CSV/JSON (admin only)
- `GET /api/v1/audit/actions` - Available filter options

**Frontend:**
- `/audit` page with:
  - Stats cards (total logs, logs today, critical, failures)
  - Filter bar (search, action, resource, severity)
  - Logs table with pagination
  - Log detail dialog with old/new values
  - Export dropdown (CSV/JSON)
- `auditAPI` client (`lib/api-client.ts`)
- Sidebar navigation link
- EN/DE translations

**Integrations:**
- Auth endpoints log login/logout/failed attempts
- Incident endpoints log create/update/delete

**Access Control:**
- All authenticated users can view their own logs
- Admin/Manager can view all logs
- Admin only can export and view stats

### Documentation
- Added `docs/features/AUDIT_LOGGING.md` with full API reference
- Added `docs/features/MOBILE_RESPONSIVE.md` with responsive patterns
- Updated `docs/README.md` with current feature status
- Updated `docs/PROJECT_STATUS.md` with Phase 3 progress

---

## [0.9.0] - 2026-01-31

### Added

#### Mobile Responsive Improvements (Phase 2 Complete)

**New Components:**
- `Sheet` (`components/ui/sheet.tsx`) - Drawer component from shadcn/ui for mobile sidebar
- `MobileSidebar` (`components/shared/mobile-sidebar.tsx`) - Mobile drawer sidebar with navigation
- `ResponsiveTable` (`components/shared/responsive-table.tsx`) - Adaptive table/cards component with helpers:
  - `MobileCardRow` - Helper for mobile card data rows
  - `MobileCardHeader` - Helper for mobile card headers
  - `ScrollableTable` - Wrapper for horizontal scrolling tables

**Layout Changes:**
- Sidebar now hidden on mobile (`hidden md:flex`), visible on tablet/desktop
- Mobile sidebar drawer opens via hamburger menu in header
- Dashboard layout integrates both desktop sidebar and mobile drawer

**Header Improvements:**
- Added hamburger menu button (visible only on mobile, `md:hidden`)
- Responsive height (`h-14 md:h-16`)
- Responsive padding (`px-4 md:px-6`)
- Language switcher shows icon-only on mobile, full text on desktop
- Title truncates on mobile to prevent overflow

**Dialog Improvements:**
- Responsive width (`w-[95vw] max-w-lg`)
- Responsive padding (`p-4 md:p-6`)
- Max height with overflow scroll (`max-h-[90vh] overflow-y-auto`)
- Always rounded corners (`rounded-lg`)

**ChartCard Improvements:**
- Responsive loading height (`h-48 md:h-64`)
- Responsive icon sizes
- Responsive title/description text sizes
- Flexible header layout for mobile

**Page Updates:**
- `/risks` - Form grids now `grid-cols-1 md:grid-cols-2`, responsive padding
- `/soc` - Responsive tabs, filters stack on mobile, table columns hide on mobile/tablet
- `/incidents` - Responsive filters, card layouts adapt to mobile

**Table Improvements:**
- Tables wrapped with horizontal scroll container
- Less important columns hidden on mobile (`hidden md:table-cell`, `hidden lg:table-cell`)
- Whitespace handling for cell content

**Breakpoints:**
| Breakpoint | Pixels | Usage |
|------------|--------|-------|
| Default | < 768px | Mobile (drawer sidebar, stacked layouts, single column forms) |
| `md:` | >= 768px | Tablet/Desktop (fixed sidebar visible, two-column forms, tables) |
| `lg:` | >= 1024px | Large desktop (more table columns, wider layouts) |

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
