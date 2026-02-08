# CyberOps Companion - Project Documentation

## Overview

**CyberOps Companion** is an open-source, enterprise-grade cybersecurity operations platform designed for German and EU enterprises. It provides a unified solution for incident response, compliance management, threat intelligence, vulnerability management, and security operations.

**Version**: 2.0.0
**License**: Apache 2.0
**Target Market**: DACH region (Germany, Austria, Switzerland) enterprises

---

## Key Differentiator: ISMS + SOC Integration

### The Problem with Current Tools

The cybersecurity market is fragmented into two silos:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT MARKET                                │
├────────────────────────────┬────────────────────────────────────┤
│   COMPLIANCE TOOLS         │         SOC TOOLS                  │
│   (Vanta, Drata, OneTrust) │    (Splunk, QRadar, TheHive)      │
├────────────────────────────┼────────────────────────────────────┤
│   ✓ ISO 27001, SOC 2       │    ✓ Alerts & Cases               │
│   ✓ Policy Management      │    ✓ Threat Intelligence          │
│   ✓ Risk Assessments       │    ✓ SIEM Integration             │
│   ✗ No real SOC            │    ✗ Compliance = afterthought    │
├────────────────────────────┼────────────────────────────────────┤
│   "We're compliant"        │    "We detect threats"            │
│   but can't prove it works │    but can't prove compliance     │
└────────────────────────────┴────────────────────────────────────┘
```

### Our Solution: One Integrated Platform

CyberOps Companion is the **only platform that connects your SOC with your ISMS**. Every alert, incident, and vulnerability automatically feeds your compliance evidence.

```
┌─────────────────────────────────────────────────────────────────┐
│                   CYBEROPS COMPANION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐    │
│   │    ISMS     │ ←──→ │     SOC     │ ←──→ │  EVIDENCE   │    │
│   │             │      │             │      │             │    │
│   │ • ISO 27001 │      │ • Incidents │      │ • Audit Log │    │
│   │ • DORA      │      │ • Alerts    │      │ • Reports   │    │
│   │ • NIS2      │      │ • Threats   │      │ • Metrics   │    │
│   │ • BSI       │      │ • Vulns     │      │ • Timeline  │    │
│   │ • Policies  │      │ • Playbooks │      │ • Exports   │    │
│   └─────────────┘      └─────────────┘      └─────────────┘    │
│          │                    │                    │            │
│          └────────────────────┴────────────────────┘            │
│                    FULLY CONNECTED                               │
│                                                                  │
│   Security Operations ARE the Compliance Evidence               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works: The Compliance Loop

```
1. REGULATION REQUIREMENT
   └── DORA Art. 17: "You must detect and report ICT incidents"

2. FRAMEWORK CONTROL
   └── ISO 27001 A.5.24: "Implement incident management process"

3. SOC OPERATION
   └── Alert detected → Case created → Incident managed → Resolved

4. AUTOMATIC EVIDENCE
   └── Incident record linked to A.5.24 with full timeline

5. AUDIT READY
   └── Auditor asks for proof → Export 47 incidents with metadata
   └── Control effectiveness: 94% based on real operational data
```

### Competitive Comparison

| Capability | Vanta/Drata | Splunk/QRadar | CyberOps |
|------------|-------------|---------------|----------|
| Manage security incidents | ❌ Manual/external | ✅ Yes | ✅ Yes |
| Map incidents to ISO 27001 | ❌ No | ❌ No | ✅ Automatic |
| Generate compliance evidence | ⚠️ Screenshots | ⚠️ Raw logs | ✅ Integrated |
| Report to BaFin/BSI (DORA/NIS2) | ❌ No | ❌ No | ✅ Built-in |
| Real-time control effectiveness | ⚠️ Manual assessment | ❌ No | ✅ Live metrics |
| Threat Intel → Risk Register | ❌ No | ❌ No | ✅ Connected |
| Single audit trail | ❌ Multiple tools | ❌ Multiple tools | ✅ One system |

### Value Proposition

**Without CyberOps:**
```
├── Splunk detects incident
├── Analyst manages it in Splunk
├── Compliance officer asks "Are we DORA compliant?"
├── Nobody can connect the data
├── Auditor arrives → panic → manual screenshots
└── Result: Non-conformity or fine
```

**With CyberOps:**
```
├── SOC detects incident
├── System auto-links to DORA Art.17, ISO A.5.24
├── Evidence generated in real-time
├── Dashboard shows: "Control A.5.24: 94% effective, 47 incidents"
├── Auditor arrives → PDF export → done
└── Result: Certification without stress
```

---

## Architecture

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy, Alembic |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS |
| **Database** | PostgreSQL 15 |
| **Cache/Queue** | Redis |
| **Background Jobs** | Celery |
| **AI/LLM** | Anthropic Claude, OpenAI, Google Gemini, Groq, Ollama |
| **Real-time** | WebSocket |

### Three-Layer German Compliance Model

The platform follows the German enterprise mental model:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER A: REGULATORY (Die Gesetze / The Laws)               │
│  ├── NIS2 Directive                                         │
│  ├── DORA (Digital Operational Resilience Act)              │
│  ├── KRITIS (German Critical Infrastructure)                │
│  ├── GDPR/DSGVO                                             │
│  └── TISAX (Automotive)                                     │
├─────────────────────────────────────────────────────────────┤
│  LAYER B: FRAMEWORKS (Die Standards / Implementation)       │
│  ├── ISO 27001:2022 (93 controls)                          │
│  ├── BSI IT-Grundschutz (200+ modules)                     │
│  ├── NIST Cybersecurity Framework                          │
│  └── COBIT                                                  │
├─────────────────────────────────────────────────────────────┤
│  LAYER C: ASSURANCE (Der Nachweis / The Evidence)          │
│  ├── Evidence Management                                    │
│  ├── Audit Logs                                             │
│  ├── Testing & Validation                                   │
│  ├── Business Continuity (BCM)                             │
│  └── Incident Records                                       │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Tenancy

- Organization-based tenant isolation
- JWT tokens with tenant context
- Middleware-enforced data separation
- Role-Based Access Control (RBAC)

---

## Implemented Modules

### 1. Incident Management

**NIST 6-Phase Incident Response Workflow:**

1. **Preparation** - Team readiness, tool setup
2. **Detection & Analysis** - IOC correlation, alert triage
3. **Containment** - Isolation strategies
4. **Eradication** - Threat removal
5. **Recovery** - System restoration
6. **Post-Incident** - Lessons learned

**Features:**
- Phase-based checklists with progress tracking
- Evidence chain with SHA-256 integrity verification
- Decision trees for response procedures
- Affected systems tracking
- Compliance mapping to frameworks
- Complete audit trail

**Files:**
- `apps/api/src/api/v1/incidents.py`
- `apps/api/src/services/incident_service.py`
- `apps/api/src/models/incident.py`
- `apps/web/app/(dashboard)/incidents/`

### 2. Threat Intelligence

**IOC Types Supported:**
- IP addresses (IPv4, IPv6)
- Domains, URLs
- File hashes (MD5, SHA1, SHA256)
- Email addresses, CVE IDs
- Registry keys, file paths

**CTI Feed Integration:**
- MISP (Malware Information Sharing Platform)
- AlienVault OTX
- VirusTotal API
- Custom TAXII/STIX feeds

**Features:**
- Bulk IOC import/export
- Automatic enrichment with threat data
- Threat actor profiling
- Campaign tracking
- Feed synchronization with history

**Files:**
- `apps/api/src/api/v1/threats.py`
- `apps/api/src/services/threat_intel_service.py`
- `apps/api/src/integrations/cti_feeds/`
- `apps/web/app/(dashboard)/threats/`

### 3. Vulnerability Management

**Asset Types:**
- Servers, network devices, endpoints
- Web applications, cloud resources
- IoT devices

**Scanner Integration:**
- Nessus
- OpenVAS
- Qualys

**Features:**
- Asset inventory with criticality levels
- CVE tracking with CVSS, EPSS, KEV data
- Scan scheduling and execution
- Real-time scan progress via WebSocket
- Vulnerability lifecycle management

**Files:**
- `apps/api/src/api/v1/vulnerabilities.py`
- `apps/api/src/services/vulnerability_service.py`
- `apps/api/src/integrations/scanners/`
- `apps/web/app/(dashboard)/vulnerabilities/`

### 4. Risk Management

**Methodology:**
- FAIR (Factor Analysis of Information Risk)
- Monte Carlo simulations
- Risk heat maps (likelihood × impact)

**Features:**
- Risk register with categories
- Control mapping and effectiveness
- Treatment actions (mitigate, accept, transfer, avoid)
- Risk appetite configuration
- Association with vulnerabilities and threats

**Files:**
- `apps/api/src/api/v1/risks.py`
- `apps/api/src/services/risk_service.py`
- `apps/api/src/models/risk.py`
- `apps/web/app/(dashboard)/risks/`

### 5. Compliance Hub

#### 5.1 ISO 27001:2022

- 93 controls across 4 themes
- Statement of Applicability (SoA) generation
- 6-step assessment wizard
- Evidence linking

**Files:**
- `apps/api/src/api/v1/iso27001.py`
- `apps/api/src/services/iso27001_service.py`

#### 5.2 BSI IT-Grundschutz

- 200+ Bausteine (modules)
- German-language controls
- Mapping to ISO 27001

**Files:**
- `apps/api/src/api/v1/bsi_grundschutz.py`
- `apps/api/src/services/bsi_service.py`

#### 5.3 NIS2 Directive

- 18 sectors covered
- Essential vs Important entity classification
- Article 21 measures assessment
- Incident reporting workflows

**Files:**
- `apps/api/src/api/v1/nis2.py`
- `apps/api/src/services/nis2_service.py`

#### 5.4 DORA (Digital Operational Resilience Act)

- 5 pillars, 28 requirements
- Financial entity type classification
- Pillar-based assessment wizard
- Gap analysis and recommendations

**Files:**
- `apps/api/src/api/v1/dora.py`
- `apps/api/src/services/dora_service.py`
- `apps/api/src/models/dora.py`

#### 5.5 Cross-Framework Mapping

- Control harmonization across frameworks
- Single implementation, multiple compliance
- Gap identification

**Files:**
- `apps/api/src/integrations/cross_framework_mapper.py`

### 6. SOC Operations

**Features:**
- Alert ingestion and triage
- Case management with tasks
- Playbook execution
- Shift handover notes
- Metrics: MTTD, MTTR

**Files:**
- `apps/api/src/api/v1/soc.py`
- `apps/api/src/services/soc_service.py`
- `apps/web/app/(dashboard)/soc/`

### 7. Business Continuity Management (BCM)

**Components:**
- Business Impact Analysis (BIA)
- RTO/RPO definitions
- Risk scenario planning
- Continuity plans
- Exercise management

**Files:**
- `apps/api/src/api/v1/bcm.py`
- `apps/api/src/services/bcm_service.py`
- `apps/web/app/(dashboard)/bcm/`

### 8. Attack Path Analysis

**Features:**
- Attack graph generation
- Crown jewel identification
- Entry point mapping
- Chokepoint analysis
- Attack simulations

**Files:**
- `apps/api/src/api/v1/attack_paths.py`
- `apps/api/src/services/attack_path_service.py`
- `apps/web/app/(dashboard)/attack-paths/`

### 9. Training & Awareness

**Features:**
- Course catalog with categories
- Module-based learning
- Quizzes with scoring
- Phishing campaign management
- Gamification (badges, leaderboards)

**Files:**
- `apps/api/src/api/v1/training.py`
- `apps/api/src/services/training_service.py`
- `apps/web/app/(dashboard)/training/`

### 10. Document & Policy Management

**Features:**
- Version control
- Approval workflows
- Acknowledgment tracking
- Review reminders
- Access control

**Files:**
- `apps/api/src/api/v1/documents.py`
- `apps/api/src/services/document_service.py`
- `apps/web/app/(dashboard)/documents/`

### 11. Third-Party Risk Management (TPRM)

**Features:**
- Vendor registry
- Assessment questionnaires
- Risk tier classification
- Finding tracking
- Contract management

**Files:**
- `apps/api/src/api/v1/tprm.py`
- `apps/api/src/services/tprm_service.py`
- `apps/web/app/(dashboard)/tprm/`

### 12. CMDB (Configuration Management Database)

**Features:**
- Hardware/software inventory
- Asset relationships
- Change management
- Lifecycle tracking

**Files:**
- `apps/api/src/api/v1/cmdb.py`
- `apps/api/src/services/cmdb_service.py`
- `apps/web/app/(dashboard)/cmdb/`

### 13. AI Copilot

**Providers:**
- Anthropic Claude
- OpenAI GPT
- Google Gemini
- Groq
- Local Ollama

**Capabilities:**
- Incident analysis
- Compliance guidance
- Vulnerability prioritization
- Report generation
- Gap remediation suggestions

**Files:**
- `apps/api/src/api/v1/copilot.py`
- `apps/api/src/services/copilot/`
- `apps/web/components/copilot/`

### 14. Onboarding Wizard

**5-Step Wizard:**
1. **Organization Profile** - Industry, size, country
2. **Regulatory Status** - KRITIS, BaFin, NIS2 status
3. **Framework Selection** - Recommended baselines
4. **Compliance Plan** - Generated action items
5. **Completion** - Next steps

**Features:**
- Automatic regulation detection
- Industry-based framework recommendations
- Compliance plan generation with priorities
- EN/DE translations

**Files:**
- `apps/api/src/api/v1/onboarding.py`
- `apps/api/src/services/onboarding_service.py`
- `apps/api/src/models/onboarding.py`
- `apps/web/app/(dashboard)/onboarding/`

### 15. Integrations Hub

**Categories:**
| Type | Integrations |
|------|-------------|
| Threat Intel | MISP, OTX, VirusTotal |
| Scanners | Nessus, OpenVAS, Qualys |
| SIEM | Splunk, ELK, QRadar |
| Ticketing | Jira, ServiceNow |
| Communication | Slack, MS Teams |
| SOAR | Shuffle |

**Files:**
- `apps/api/src/api/v1/integrations.py`
- `apps/api/src/services/integrations_service.py`
- `apps/web/app/(dashboard)/integrations/`

### 16. Reporting & Analytics

**Features:**
- Report templates (PDF, Excel)
- Customizable dashboards
- KPI metrics
- Trend analysis
- Scheduled reports

**Files:**
- `apps/api/src/api/v1/reporting.py`
- `apps/api/src/services/reporting_service.py`
- `apps/web/app/(dashboard)/reporting/`

### 17. Audit Logging

**Features:**
- Comprehensive activity tracking
- User action logging
- Change history
- Export capabilities

**Files:**
- `apps/api/src/api/v1/audit.py`
- `apps/api/src/services/audit_service.py`
- `apps/web/app/(dashboard)/audit/`

---

## API Structure

### Endpoint Categories

```
/api/v1/
├── auth/                    # Authentication
├── sso/                     # SSO providers
├── organizations/           # Tenant management
├── users/                   # User management
├── incidents/               # Incident response
├── threats/                 # Threat intelligence
│   ├── iocs/               # Indicators of Compromise
│   ├── actors/             # Threat actors
│   ├── campaigns/          # Campaigns
│   └── feeds/              # CTI feeds
├── vulnerabilities/         # Vulnerability management
│   ├── assets/             # Asset inventory
│   ├── scans/              # Scan management
│   └── cves/               # CVE tracking
├── risks/                   # Risk register
├── compliance/              # Compliance validation
├── iso27001/               # ISO 27001 assessments
├── bsi_grundschutz/        # BSI framework
├── nis2/                   # NIS2 assessments
├── dora/                   # DORA assessments
├── soc/                    # SOC operations
│   ├── alerts/             # Alert management
│   ├── cases/              # Case management
│   └── playbooks/          # Playbook execution
├── bcm/                    # Business continuity
├── attack-paths/           # Attack path analysis
├── training/               # Training & awareness
├── documents/              # Document management
├── tprm/                   # Third-party risk
├── cmdb/                   # Configuration management
├── integrations/           # External integrations
├── reporting/              # Reports & dashboards
├── notifications/          # Notification preferences
├── analytics/              # Metrics & analytics
├── audit/                  # Audit logs
├── copilot/                # AI assistant
└── onboarding/             # Setup wizard
```

---

## Database Models

### Core Entities

| Model | Table | Purpose |
|-------|-------|---------|
| User | users | Authentication, profiles |
| Organization | organizations | Multi-tenancy |
| Incident | incidents | Incident tracking |
| IOC | iocs | Threat indicators |
| ThreatActor | threat_actors | Actor profiles |
| Asset | assets | IT inventory |
| Vulnerability | vulnerabilities | CVE tracking |
| Risk | risks | Risk register |
| SOCAlert | soc_alerts | Security alerts |
| SOCCase | soc_cases | Investigation cases |
| TrainingCourse | training_courses | Learning content |
| Document | documents | Policies |
| Vendor | vendors | Third parties |
| ConfigurationItem | cmdb_items | CMDB entries |

### Compliance Models

| Model | Table | Framework |
|-------|-------|-----------|
| ISO27001Assessment | iso27001_assessments | ISO 27001:2022 |
| DORAAssessment | dora_assessments | DORA |
| NIS2Assessment | nis2_assessments | NIS2 |
| BSIAssessment | bsi_assessments | BSI IT-Grundschutz |
| OrganizationProfile | organization_profiles | Onboarding |

---

## Frontend Structure

### Page Layout

```
apps/web/app/(dashboard)/
├── home/                   # Dashboard
├── incidents/              # Incident management
│   └── [id]/              # Incident detail
├── threats/                # Threat intel
│   ├── iocs/              # IOC list
│   ├── actors/            # Actors
│   ├── campaigns/         # Campaigns
│   └── feeds/             # Feed management
├── vulnerabilities/        # Vuln management
├── risks/                  # Risk register
├── compliance/             # Compliance hub
│   ├── frameworks/        # ISO, BSI, NIST
│   ├── regulatory/        # NIS2, DORA, GDPR
│   └── assurance/         # Evidence, audits
├── soc/                    # SOC dashboard
├── bcm/                    # BCM
├── attack-paths/           # Attack graphs
├── training/               # Learning
├── documents/              # Policies
├── tprm/                   # Vendors
├── cmdb/                   # Assets
├── integrations/           # Connections
├── reporting/              # Reports
├── audit/                  # Logs
├── notifications/          # Preferences
├── users/                  # User mgmt
└── onboarding/             # Setup wizard
```

### Key Components

| Directory | Components |
|-----------|------------|
| `components/copilot/` | CopilotChat, CopilotButton, ModelSelector |
| `components/compliance/` | DORADashboard, NIS2Dashboard |
| `components/dashboard/` | KPI cards, charts, visualizations |
| `components/navigation/` | Sidebar, CommandPalette |
| `components/shared/` | Loading, EmptyState, FormField |
| `components/ui/` | Shadcn UI base components |

---

## Internationalization

- **Languages**: English (en), German (de)
- **Translation File**: `apps/web/i18n/translations.ts`
- **Coverage**: All UI strings, error messages, labels

---

## Real-time Features

### WebSocket Endpoints

```
/api/v1/ws/notifications    # User notifications
/api/v1/ws/alerts          # SOC alerts
/api/v1/ws/scans           # Scan progress
```

### Event Types

- Incident status changes
- New security alerts
- Scan progress updates
- Report generation status
- System notifications

---

## Security Features

### Authentication
- Email/password (bcrypt)
- JWT tokens (15min access, 7d refresh)
- SSO (Google, Microsoft, Okta)
- MFA (TOTP)
- API keys

### Authorization
- RBAC (Admin, Manager, Lead, Analyst)
- Permission-based endpoints
- Tenant isolation middleware

### Protection
- Rate limiting (Redis)
- CORS configuration
- Audit logging
- Encrypted credentials

---

## Deployment

### Docker Compose Services

```yaml
services:
  api:        # FastAPI backend
  web:        # Next.js frontend
  postgres:   # Database
  redis:      # Cache/queue
  celery:     # Background worker
  caddy:      # Reverse proxy
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Authentication
SECRET_KEY=...
JWT_SECRET=...

# Integrations
MISP_URL=...
MISP_API_KEY=...
VIRUSTOTAL_API_KEY=...

# AI Providers
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
```

---

## Project Statistics

| Metric | Count |
|--------|-------|
| API Routes | 30+ modules |
| Endpoints | 200+ |
| Database Models | 30+ entities |
| Services | 40+ classes |
| Frontend Pages | 22+ sections |
| Components | 40+ reusable |
| Integrations | 10+ platforms |
| Frameworks | 8 supported |

---

## Recent Commits

```
b708a72 feat: implement onboarding wizard with regulation detection
2e2d934 feat: implement DORA compliance and restructure to German 3-layer model
cee5ff0 feat(web): add threat feed management UI
8d9d030 feat: implement CTI feed integration (MISP, OTX, VirusTotal)
839b633 feat(web): integrate scan progress UI into vulnerabilities page
```

---

## ISMS ↔ SOC Integration Points

This section details the specific connections between compliance (ISMS) and security operations (SOC).

### Integration Matrix

| SOC Activity | ISMS Connection | Evidence Generated |
|--------------|-----------------|-------------------|
| **Incident Response** | ISO 27001 A.5.24, A.5.26 | Incident records, timeline, resolution |
| **Alert Triage** | DORA Art. 17, NIS2 Art. 23 | Alert classification, response time |
| **Threat Detection** | ISO 27001 A.8.16 | Detection logs, IOC matches |
| **Vulnerability Scan** | ISO 27001 A.8.8, DORA Art. 25 | Scan reports, remediation tracking |
| **Playbook Execution** | ISO 27001 A.5.24 | Automated response evidence |
| **Case Investigation** | DORA Art. 17 | Investigation timeline, findings |
| **Shift Handover** | ISO 27001 A.6.1 | Operational continuity records |

### Control ↔ Operation Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│ ISO 27001 A.5.24 (Incident Management)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTROL REQUIREMENT          SOC EVIDENCE                      │
│  ──────────────────          ────────────                       │
│  "Plan incident response" → Playbooks defined in system         │
│  "Detect incidents"       → Alerts from SIEM integration        │
│  "Respond to incidents"   → Case management with timeline       │
│  "Learn from incidents"   → Post-incident reports               │
│  "Preserve evidence"      → SHA-256 verified evidence chain     │
│                                                                  │
│  EFFECTIVENESS METRIC: Response time, resolution rate           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DORA Article 17 (ICT Incident Management)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DORA REQUIREMENT             SOC EVIDENCE                      │
│  ────────────────             ────────────                      │
│  "Detect anomalies"       → Alert correlation engine            │
│  "Classify incidents"     → Severity classification system      │
│  "Report major incidents" → BaFin notification workflow         │
│  "Root cause analysis"    → Post-incident investigation         │
│  "Track trends"           → Incident analytics dashboard        │
│                                                                  │
│  REPORTING: Initial (4h), Intermediate (72h), Final (1mo)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ NIS2 Article 21 (Cybersecurity Risk Management)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  NIS2 REQUIREMENT             SOC EVIDENCE                      │
│  ────────────────             ────────────                      │
│  "Incident handling"      → Full incident lifecycle tracking    │
│  "Crisis management"      → BCM integration with exercises      │
│  "Supply chain security"  → TPRM vendor assessments            │
│  "Vulnerability handling" → Scan results and remediation       │
│  "Security testing"       → Penetration test tracking          │
│                                                                  │
│  REPORTING: 24h initial, 72h full notification                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Automatic Evidence Flow

```
SOC OPERATION                      ISMS EVIDENCE
─────────────                      ─────────────

Analyst creates incident     ───→  Evidence: Incident created
    │                               - Timestamp
    │                               - Creator
    │                               - Initial classification
    ▼
Analyst adds IOCs            ───→  Evidence: Threat indicators
    │                               - IOC type and value
    │                               - Source attribution
    │                               - Enrichment data
    ▼
Playbook executes            ───→  Evidence: Response actions
    │                               - Automated steps
    │                               - Execution time
    │                               - Results
    ▼
Incident resolved            ───→  Evidence: Resolution
    │                               - Resolution time (MTTR)
    │                               - Root cause
    │                               - Lessons learned
    ▼
Post-incident report         ───→  Evidence: Continuous improvement
                                    - Recommendations
                                    - Control updates
                                    - Training needs

ALL EVIDENCE LINKED TO:
├── ISO 27001 controls (A.5.24, A.5.26, A.8.16)
├── DORA pillars (P2: Incident Reporting)
├── NIS2 articles (Art. 21, Art. 23)
└── BSI modules (DER.2.1, DER.2.2)
```

### Dashboard Integration

```
┌─────────────────────────────────────────────────────────────────┐
│ COMPLIANCE DASHBOARD                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ISO 27001 Control Status                SOC Metrics            │
│  ────────────────────────                ───────────            │
│  A.5.24 Incident Mgmt: 94%   ←────────   47 incidents handled   │
│  A.8.8 Vuln Mgmt: 87%        ←────────   312 vulns remediated  │
│  A.8.16 Monitoring: 91%      ←────────   99.2% alert coverage   │
│                                                                  │
│  DORA Compliance                         Real-time Ops          │
│  ───────────────                         ────────────           │
│  P2 Incident Report: 96%     ←────────   Avg response: 2.3h    │
│  P3 Resilience Test: 88%     ←────────   Last test: 5 days ago │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Control effectiveness calculated from ACTUAL OPERATIONS │   │
│  │ Not self-assessments. Not checkboxes. Real data.        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Roadmap

### Completed
- [x] Incident Management (NIST 6-phase)
- [x] Threat Intelligence (IOC, actors, campaigns)
- [x] Vulnerability Management (scanners, assets)
- [x] Risk Management (FAIR methodology)
- [x] ISO 27001:2022 Assessment
- [x] BSI IT-Grundschutz
- [x] NIS2 Compliance Wizard
- [x] DORA Assessment (5 pillars)
- [x] SOC Operations
- [x] BCM (Business Continuity)
- [x] Attack Path Analysis
- [x] Training & Awareness
- [x] Document Management
- [x] TPRM (Third-Party Risk)
- [x] CMDB
- [x] AI Copilot
- [x] Onboarding Wizard
- [x] CTI Feed Integration
- [x] Real-time WebSocket

### Planned
- [ ] TISAX Assessment Wizard
- [ ] Mobile App
- [ ] Advanced ML-based threat detection
- [ ] Automated compliance evidence collection
- [ ] Extended SOAR capabilities

---

## License

Apache License 2.0

---

*Documentation generated: 2026-02-08*
