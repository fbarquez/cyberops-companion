# Changelog

All notable changes to CyberOps Companion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned (Future)
- ML/Predictive Analytics (Phase 2C - when more data is available)
- Real scanner integration (Nessus, OpenVAS, Qualys)
- Anomaly detection
- Incident prediction

See [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) for detailed specifications.

---

## [0.15.0] - 2026-02-05

### Added

#### Document & Policy Management Module

Complete document management system for ISMS compliance, supporting policies, procedures, standards, and other compliance documentation with versioning, approval workflows, and acknowledgment tracking.

**Backend:**

| Component | File | Description |
|-----------|------|-------------|
| Models | `models/documents.py` | Document, DocumentVersion, DocumentApproval, DocumentAcknowledgment, DocumentReview |
| Schemas | `schemas/documents.py` | 25+ Pydantic schemas for all operations |
| Service | `services/document_service.py` | ~700 lines of business logic |
| API | `api/v1/documents.py` | 28 REST endpoints |
| Migration | `alembic/versions/h8i9j0k1l2m3_add_document_tables.py` | 5 tables with indexes |

**Document Categories:**
- Policy (POL-001)
- Procedure (PRO-001)
- Standard (STD-001)
- Guideline (GDL-001)
- Form (FRM-001)
- Record (REC-001)
- Manual (MAN-001)
- Work Instruction (INS-001)

**Document Lifecycle:**
```
DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ARCHIVED
                ↓
        (rejected: back to DRAFT)
```

**API Endpoints (28 total):**

| Category | Endpoints |
|----------|-----------|
| Documents CRUD | GET/POST/PUT/DELETE `/documents`, `/documents/{id}` |
| Workflow | POST `/documents/{id}/submit-review`, `/approve`, `/reject`, `/publish`, `/archive` |
| Versions | GET/POST `/documents/{id}/versions`, compare endpoint |
| Approvals | GET/POST `/documents/{id}/approvals`, `/approvals/pending` |
| Acknowledgments | GET/POST `/documents/{id}/acknowledgments`, `/acknowledge`, `/remind` |
| Reviews | GET/POST `/documents/{id}/reviews`, `/documents/due-for-review` |
| Reports | GET `/documents/stats`, `/documents/compliance-report` |

**Frontend:**

| Component | File | Description |
|-----------|------|-------------|
| List Page | `app/(dashboard)/documents/page.tsx` | Dashboard, tabs, filters, create dialog |
| Detail Page | `app/(dashboard)/documents/[id]/page.tsx` | Multi-tab view with editor |
| API Client | `lib/api-client.ts` | `documentsAPI` with all methods |
| Sidebar | `components/shared/sidebar.tsx` | Documents navigation entry |
| Translations | `i18n/translations.ts` | EN/DE translations (~150 keys) |

**Features:**
- Version control with major/minor/patch numbering (1.0, 1.1, 2.0)
- Sequential and parallel approval workflows
- User acknowledgment tracking with due dates
- Compliance mapping to ISO 27001, NIS2, BSI frameworks
- Review cycles: Quarterly, Semi-Annual, Annual, Biennial
- Markdown content editor with live preview
- Auto-generated document IDs by category

**Notification Types Added:**
- `DOCUMENT_SUBMITTED`, `DOCUMENT_APPROVED`, `DOCUMENT_REJECTED`
- `DOCUMENT_PUBLISHED`, `DOCUMENT_UPDATED`
- `DOCUMENT_REVIEW_DUE`, `DOCUMENT_REVIEW_OVERDUE`
- `ACKNOWLEDGMENT_REQUIRED`, `ACKNOWLEDGMENT_REMINDER`, `ACKNOWLEDGMENT_OVERDUE`
- `APPROVAL_REQUIRED`, `APPROVAL_REMINDER`

**Documentation:**
- Feature docs: `docs/features/DOCUMENT_MANAGEMENT.md`
- Updated architecture overview

---

## [0.14.0] - 2026-02-05

### Added

#### ISO 27001:2022 Compliance Module

Complete implementation of ISO 27001:2022 Information Security Management System (ISMS) compliance support.

**Control Catalog:**
- 93 Annex A controls organized in 4 themes:
  - A.5 Organizational (37 controls)
  - A.6 People (8 controls)
  - A.7 Physical (14 controls)
  - A.8 Technological (34 controls)
- Multi-language support (EN/DE/ES)
- Cross-framework references to BSI IT-Grundschutz, NIS2, NIST CSF

**Backend:**

| Component | File | Description |
|-----------|------|-------------|
| Models | `models/iso27001.py` | ISO27001Control, ISO27001Assessment, ISO27001SoAEntry |
| Schemas | `schemas/iso27001.py` | 25+ Pydantic schemas for API validation |
| Service | `services/iso27001_service.py` | Full business logic with scoring, gap analysis, mapping |
| API | `api/v1/iso27001.py` | 15 REST endpoints |
| Migration | `alembic/versions/e5f6g7h8i9j0_add_iso27001_tables.py` | Database tables and enums |
| Seed Data | `db/data/iso27001_2022.json` | 93 controls with full metadata |
| Seed Script | `db/seed_iso27001.py` | Control seeding and verification |
| PDF Generator | `services/pdf_reports/iso27001_report_generator.py` | ReportLab-based PDF reports |

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/iso27001/themes` | GET | List 4 themes with control counts |
| `/iso27001/controls` | GET | List controls with filtering |
| `/iso27001/controls/{id}` | GET | Get control details |
| `/iso27001/dashboard` | GET | Dashboard statistics |
| `/iso27001/assessments` | POST | Create assessment |
| `/iso27001/assessments` | GET | List assessments |
| `/iso27001/assessments/{id}` | GET | Get assessment |
| `/iso27001/assessments/{id}` | DELETE | Delete assessment |
| `/iso27001/assessments/{id}/scope` | PUT | Update scope (Step 1) |
| `/iso27001/assessments/{id}/wizard-state` | GET | Get wizard state |
| `/iso27001/assessments/{id}/soa` | GET | Get SoA entries |
| `/iso27001/assessments/{id}/soa/{control}` | PUT | Update SoA entry |
| `/iso27001/assessments/{id}/soa` | PUT | Bulk update SoA |
| `/iso27001/assessments/{id}/overview` | GET | Assessment overview |
| `/iso27001/assessments/{id}/gaps` | GET | Gap analysis |
| `/iso27001/assessments/{id}/mapping` | GET | Cross-framework mapping |
| `/iso27001/assessments/{id}/report` | GET | Generate report (JSON/PDF) |
| `/iso27001/assessments/{id}/complete` | POST | Mark complete |

**Frontend:**

| Component | File | Description |
|-----------|------|-------------|
| Main Page | `app/(dashboard)/compliance/iso27001/page.tsx` | Dashboard + assessment list |
| Wizard Page | `app/(dashboard)/compliance/iso27001/[id]/page.tsx` | 6-step assessment wizard |
| API Client | `lib/api-client.ts` | `iso27001API` methods |
| Sidebar | `components/shared/sidebar.tsx` | Compliance navigation section |
| Translations | `i18n/translations.ts` | EN/DE nav labels |

**6-Step Assessment Wizard:**

| Step | Name | Description |
|------|------|-------------|
| 1 | Scope | Define certification scope (systems, locations, processes) |
| 2 | SoA | Statement of Applicability - mark controls applicable/excluded |
| 3 | Assessment | Evaluate control compliance status and implementation level |
| 4 | Gap Analysis | Review gaps with remediation plans and priorities |
| 5 | Cross-Framework | View related BSI/NIS2/NIST CSF controls |
| 6 | Report | Executive summary with PDF export |

**Scoring Formula:**
```
score = (compliant + 0.5 * partial) / applicable * 100
```

**PDF Report Features:**
- Executive summary with overall score
- Theme-by-theme compliance breakdown
- Statement of Applicability table
- Gap analysis with priorities
- Cross-framework mapping summary
- Generated using ReportLab library

**Dependencies Added:**
- `reportlab>=4.0.0` - PDF generation

**Documentation:**
- Added `docs/features/ISO27001.md` with full implementation guide
- Added `docs/ENTERPRISE.md` with enterprise edition overview
- Updated `docs/README.md` with ISO 27001, Rate Limiting, and Enterprise docs
- Updated `README.md` with ISO 27001 documentation link

---

## [0.13.0] - 2026-02-01

### Added

#### API Rate Limiting (Phase 3 Complete)

Comprehensive rate limiting system to protect the API against abuse with plan-based limits.

**Rate Limits by Plan:**
| Plan | Requests/Hour | Requests/Minute |
|------|---------------|-----------------|
| FREE | 1,000 | 60 |
| STARTER | 5,000 | 200 |
| PROFESSIONAL | 20,000 | 500 |
| ENTERPRISE | 100,000 | 2,000 |

**Endpoint-Specific Limits (per IP):**
- `/api/v1/auth/login` - 5/minute
- `/api/v1/auth/register` - 3/minute
- `/api/v1/auth/forgot-password` - 3/minute
- `/api/v1/auth/reset-password` - 5/minute
- Unauthenticated requests - 30/minute

**Backend:**
- `RedisManager` (`core/redis.py`) - Async Redis connection pool
- `RateLimitService` (`services/rate_limit_service.py`) - Sliding window algorithm with Redis sorted sets
- `RateLimitMiddleware` (`middleware/rate_limit_middleware.py`) - FastAPI middleware
- Rate limit configuration (`core/rate_limit_config.py`) - Plan and endpoint limits
- Redis DB 1 for rate limiting (separate from Celery on DB 0)
- Super admin bypass option (`RATE_LIMIT_BYPASS_SUPER_ADMIN`)
- Plan caching to reduce database queries

**Response Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706745720
Retry-After: 35  (only on 429)
```

**429 Response Format:**
```json
{
  "detail": "Rate limit exceeded",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "limit": 60,
    "retry_after": 35,
    "reset_at": 1706745720
  }
}
```

**Frontend:**
- `RateLimitError` class with rate limit info
- `RateLimitInfo` interface for typed rate limit data
- `onRateLimitExceeded()` event system for global notifications
- `RateLimitBanner` component with countdown timer
- `useRateLimitState()` hook for components needing rate limit state
- Auto-dismiss banner when retry period expires

**Excluded Paths (no rate limiting):**
- `/health`, `/`, `/api/docs`, `/api/redoc`, `/api/openapi.json`
- `/api/v1/ws/*` (WebSocket connections)

**Configuration:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=1
RATE_LIMIT_BYPASS_SUPER_ADMIN=true
RATE_LIMIT_FREE_HOUR=1000
RATE_LIMIT_FREE_MINUTE=60
# ... etc for other plans
```

**Documentation:** [RATE_LIMITING.md](./features/RATE_LIMITING.md)

---

## [0.12.0] - 2026-02-01

### Added

#### Multi-Tenancy / Organizations (Phase 3)

Complete multi-tenant architecture allowing multiple organizations to use the platform with full data isolation.

**Database:**
- `Organization` model with status (active, suspended, trial, cancelled) and plans (free, starter, professional, enterprise)
- `OrganizationMember` model with roles (owner, admin, member, viewer)
- `tenant_id` column added to 27 domain tables
- `is_super_admin` field added to User model
- `TenantMixin` and `ImmutableTenantMixin` for consistent tenant_id handling

**Backend:**
- `TenantContext` using Python's ContextVar for thread-safe tenant storage
- `TenantMiddleware` extracts tenant from JWT on every request
- `TenantAwareService` base class with automatic query filtering
- `OrganizationService` for CRUD operations and member management
- JWT tokens now include `tenant_id`, `org_role`, and `available_tenants`
- New endpoints: `/api/v1/organizations/*` for organization management
- Super admin can access any tenant via `X-Tenant-ID` header

**Frontend:**
- `tenant-store.ts` - Zustand store for tenant state management
- `TenantSelector` component in header for switching organizations
- Auth store integration - loads tenants on login, clears on logout
- EN/DE translations for all organization-related UI

**Migrations:**
- `a1b2c3d4e5f6` - Creates organization tables, adds tenant_id (nullable)
- `b2c3d4e5f6g7` - Migrates existing data to default organization, makes tenant_id NOT NULL

**Documentation:** [MULTI_TENANCY.md](./features/MULTI_TENANCY.md)

---

## [0.11.0] - 2026-02-01

### Added

#### SSO/SAML Integration (Phase 3)

Enterprise Single Sign-On with OAuth2/OIDC protocol support.

**Supported Providers:**
- Google Workspace
- Microsoft Entra ID (Azure AD)
- Okta

**Backend:**
- `SSOProvider` model for provider configuration
- `SSOState` model for CSRF protection (state tokens)
- Extended `User` model with SSO fields:
  - `sso_provider` - Provider slug (google, azure, okta)
  - `sso_id` - Provider's unique user identifier
  - `sso_email` - Email from SSO provider
  - `sso_linked_at` - Timestamp when SSO was linked
- `SSOService` (`services/sso_service.py`):
  - OAuth2 flow management
  - State token generation and validation
  - Code-to-token exchange
  - User info retrieval
  - JIT (Just-in-Time) user provisioning
  - Account linking
- Pydantic schemas (`schemas/sso.py`):
  - `SSOProviderPublic`, `SSOProvidersResponse`
  - `SSOAuthorizeResponse`, `SSOCallbackRequest`
  - `SSOCallbackResponse`, `SSOUserInfo`

**API Endpoints:**
- `GET /api/v1/auth/sso/providers` - List enabled SSO providers
- `GET /api/v1/auth/sso/{provider}/authorize` - Get OAuth2 authorization URL
- `POST /api/v1/auth/sso/{provider}/callback` - Exchange code for tokens
- `POST /api/v1/auth/sso/{provider}/unlink` - Remove SSO from account

**Frontend:**
- `SSOButtons` component with provider icons
- `/auth/callback` page for OAuth2 callback handling
- Updated login page with SSO options
- Updated auth store with `loginWithSSO`
- EN/DE translations for SSO messages

**Security Features:**
- CSRF protection via state tokens (32 bytes, URL-safe)
- State tokens expire after 10 minutes
- One-time use tokens (deleted after validation)
- Email domain validation (`allowed_domains`)
- SSO provider tokens NOT stored (only internal JWTs)

**Configuration:**
```bash
SSO_GOOGLE_ENABLED=true
SSO_GOOGLE_CLIENT_ID=...
SSO_GOOGLE_CLIENT_SECRET=...

SSO_AZURE_ENABLED=true
SSO_AZURE_CLIENT_ID=...
SSO_AZURE_CLIENT_SECRET=...
SSO_AZURE_TENANT_ID=common

SSO_OKTA_ENABLED=true
SSO_OKTA_CLIENT_ID=...
SSO_OKTA_CLIENT_SECRET=...
SSO_OKTA_DOMAIN=dev-123456.okta.com

SSO_AUTO_CREATE_USERS=true
SSO_DEFAULT_ROLE=analyst
SSO_ALLOWED_DOMAINS=company.com
```

**Database Migrations:**
- Added SSO columns to users table
- Created sso_providers table
- Created sso_states table

### Documentation
- Added `docs/features/SSO_SAML.md` with full implementation guide
- Updated `docs/PROJECT_STATUS.md` with Phase 3 progress
- Added `docs/DOCUMENTACION_COMPLETA.md` (Spanish comprehensive docs)

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
