# ISORA - Enterprise Edition

**Status:** Available
**License:** Commercial License

---

## Overview

ISORA Enterprise extends the open-source Community edition with advanced compliance modules, AI-powered assistance, and priority support. Designed for organizations requiring comprehensive regulatory compliance and enterprise-grade features.

---

## Enterprise Features

| Feature | Description | Status |
|---------|-------------|--------|
| [ISO 27001:2022 Compliance](#iso-270012022-compliance) | Full ISMS assessment with 93 controls | ✅ Available |
| [Business Continuity Management](#business-continuity-management) | BCM based on BSI 200-4 and ISO 22301 | ✅ Available |
| [BSI IT-Grundschutz](#bsi-it-grundschutz) | German federal security standards (61 Bausteine, 276 Anforderungen) | ✅ Available |
| [NIS2 Directive Assessment](#nis2-directive-assessment) | EU cybersecurity directive compliance (5-step wizard, 18 sectors) | ✅ Available |
| [AI Copilot](#ai-copilot) | Multi-LLM security assistant (5 providers, streaming) | ✅ Available |
| [PDF Reports](#pdf-reports) | Professional LaTeX reports (DIN 5008 standard) | ✅ Available |
| [Priority Support](#priority-support) | SLA-backed technical support | ✅ Available |

---

## ISO 27001:2022 Compliance

Full implementation of ISO/IEC 27001:2022 Information Security Management System (ISMS) assessment.

### Features

- **93 Annex A Controls** organized in 4 themes:
  - A.5 Organizational (37 controls)
  - A.6 People (8 controls)
  - A.7 Physical (14 controls)
  - A.8 Technological (34 controls)

- **6-Step Assessment Wizard**:
  1. Scope Definition
  2. Statement of Applicability (SoA)
  3. Control Assessment
  4. Gap Analysis
  5. Cross-Framework Mapping
  6. Report Generation

- **Statement of Applicability (SoA)**:
  - Mark controls as Applicable/Not Applicable/Excluded
  - Document justifications
  - Track implementation status

- **Gap Analysis**:
  - Identify non-compliant controls
  - Prioritize remediation (Critical/High/Medium/Low)
  - Assign owners and due dates
  - Track remediation progress

- **Cross-Framework Mapping**:
  - Map to BSI IT-Grundschutz bausteins
  - Map to NIS2 Directive measures
  - Map to NIST Cybersecurity Framework
  - Reduce duplicate compliance efforts

- **PDF Report Generation**:
  - Executive summary with scores
  - Theme-by-theme breakdown
  - Gap analysis with roadmap
  - Cross-framework coverage

### Documentation

See [ISO 27001:2022 Documentation](./features/ISO27001.md) for detailed API reference and usage.

---

## Business Continuity Management

Comprehensive BCM implementation based on BSI Standard 200-4 and ISO 22301.

### Features

- **Business Process Inventory**:
  - Critical process documentation
  - Dependency mapping (internal, external, IT)
  - Key personnel identification
  - Criticality classification (Critical/High/Medium/Low)

- **Business Impact Analysis (BIA)**:
  - 6-step wizard for structured analysis
  - Impact timeline (1h, 4h, 8h, 24h, 72h, 1w)
  - Impact categories (Financial, Operational, Reputational, Legal, Safety)
  - Recovery objectives (RTO, RPO, MTPD)
  - Resource requirements

- **Risk Scenarios**:
  - Scenario categories (Natural disaster, Cyber attack, Pandemic, etc.)
  - Likelihood and impact assessment (5x5 matrix)
  - Risk score calculation
  - Single Points of Failure identification

- **Continuity Strategies**:
  - Strategy types (Manual workaround, Alternate site, Redundancy, etc.)
  - Achievable RTO/RPO per strategy
  - Activation triggers and procedures

- **Emergency Plans (Notfallkonzepte)**:
  - Plan types (Crisis management, DR, Communication, etc.)
  - Structured sections (Phases, Procedures, Roles, Contacts)
  - Activation and recovery checklists
  - Approval workflow
  - PDF export

- **BC Exercises**:
  - Exercise types (Tabletop, Simulation, Full test)
  - Objectives tracking
  - Results documentation
  - Issues and lessons learned
  - Action item management

- **BCM Maturity Assessment**:
  - Overall program scoring
  - Coverage metrics (BIA, strategies, plans, testing)
  - Progress tracking

### Documentation

See [BCM Documentation](./features/BCM.md) for detailed API reference and usage.

---

## BSI IT-Grundschutz

Complete implementation of the German Federal Office for Information Security (BSI) IT-Grundschutz methodology.

### Features

- **Full IT-Grundschutz Kompendium**:
  - 61 Bausteine (building blocks/modules)
  - 276 Anforderungen (requirements)
  - Complete catalog with descriptions

- **Compliance Dashboard**:
  - Visual overview with category breakdown
  - Progress tracking per Baustein
  - Aggregate compliance statistics

- **Three Protection Levels**:
  - Basis (Basic protection)
  - Standard (Standard protection)
  - Hoch (High protection)

- **Compliance Tracking**:
  - Status per requirement: Compliant, Partial, Gap, N/A
  - Evidence documentation
  - Remediation planning

- **Export Functionality**:
  - CSV export for spreadsheets
  - JSON export for integration
  - PDF reports (DIN 5008 standard)

- **18 API Endpoints**:
  - Full CRUD for Bausteine and Anforderungen
  - Compliance status management
  - Dashboard aggregations

### Use Cases

- German federal agency compliance
- KRITIS (critical infrastructure) operators
- Organizations seeking BSI certification
- Defense sector contractors

### Documentation

See the Enterprise repository for detailed BSI IT-Grundschutz documentation.

---

## NIS2 Directive Assessment

Complete compliance assessment for the EU Network and Information Security Directive 2 (NIS2).

### Features

- **5-Step Assessment Wizard**:
  1. Organization Scope - Define organization details
  2. Sector Classification - Determine Essential/Important/Out of Scope
  3. Security Measures - Assess Article 21 requirements
  4. Gap Analysis - Identify and prioritize gaps
  5. Report Generation - Create compliance documentation

- **18 NIS2 Sectors**:
  - 11 Essential sectors (Annex I): Energy, Transport, Banking, Financial markets, Health, Water supply, Digital infrastructure, ICT service management, Public administration, Space
  - 7 Important sectors (Annex II): Postal services, Waste management, Manufacturing, Food, Chemicals, Research, Digital providers

- **10 Security Measures** (Article 21):
  - Risk management policies
  - Incident handling procedures
  - Business continuity measures
  - Supply chain security
  - Cybersecurity hygiene practices
  - Cryptography and encryption
  - Human resources security
  - Access control policies
  - Asset management
  - Multi-factor authentication

- **Automatic Classification**:
  - Determines Essential, Important, or Out of Scope status
  - Based on sector, size, and criticality criteria
  - Calculates applicable requirements

- **Gap Analysis**:
  - Prioritized gaps with severity levels
  - Remediation recommendations
  - Action item tracking
  - Owner assignment

- **Dashboard**:
  - Aggregate statistics across assessments
  - Compliance trends over time
  - Sector breakdown visualization

- **Export Functionality**:
  - CSV export for spreadsheets
  - JSON export for integration
  - PDF reports (professional format)

- **14 API Endpoints**:
  - Full assessment lifecycle management
  - Dashboard aggregations
  - Export functionality

### Documentation

See the Enterprise repository for detailed NIS2 documentation.

---

## AI Copilot

Full-featured AI-powered security assistant with multiple LLM providers.

### Features

- **5 LLM Providers**:
  - **Ollama** (Local) - Privacy-focused, no data leaves your infrastructure
  - **OpenAI** (GPT-4/GPT-4o) - Industry-leading language model
  - **Anthropic** (Claude) - Advanced reasoning and analysis
  - **Google Gemini** - Multi-modal capabilities
  - **Groq** - Ultra-fast inference

- **Auto-Detection**:
  - Automatically detects local Ollama installation
  - Falls back to configured cloud providers
  - Seamless provider switching

- **Security Capabilities**:
  - **Incident Analysis**: Automated triage and classification
  - **Threat Intelligence**: IOC analysis and threat correlation
  - **Compliance Guidance**: Context-aware control recommendations
  - **Vulnerability Prioritization**: Risk-based vulnerability ranking
  - **Report Generation**: Automated executive summaries
  - **Query Interface**: Natural language security queries

- **Streaming Support**:
  - Real-time SSE (Server-Sent Events) streaming
  - Progressive response display
  - Reduced perceived latency

- **Settings Page**:
  - UI for provider configuration
  - API key management
  - Model selection per provider
  - Test connection functionality

- **9 API Endpoints**:
  - Chat completion (streaming and non-streaming)
  - Incident analysis
  - Compliance guidance
  - Vulnerability prioritization
  - Threat intelligence queries

### Documentation

See the Enterprise repository for detailed AI Copilot documentation.

---

## PDF Reports

Professional compliance report generation using LaTeX.

### Features

- **DIN 5008 Standard**:
  - German business document formatting
  - Professional typography and layout
  - Consistent branding

- **BSI Standard 200-2**:
  - IT-Grundschutz reporting methodology
  - Structured findings and recommendations
  - Action plan formatting

- **Report Types**:
  - BSI IT-Grundschutz Compliance Report (German)
  - NIS2 Assessment Report (English)
  - ISO 27001 Compliance Report
  - BCM Assessment Report

- **Document Classification**:
  - Public
  - Internal
  - Confidential
  - Strictly Confidential

- **Professional Structure**:
  - Cover page with organization branding
  - Table of contents
  - Executive summary
  - Detailed findings by category
  - Gap analysis with severity levels
  - Remediation roadmap
  - Action plans with owners and deadlines

- **Frontend Integration**:
  - One-click PDF export from dashboards
  - Progress indicator during generation
  - Automatic download

- **3 API Endpoints**:
  - BSI compliance report generation
  - NIS2 assessment report generation
  - LaTeX health check

### Technical Requirements

- LaTeX distribution (TeX Live or MiKTeX)
- Included in Enterprise Docker image

---

## Priority Support

Enterprise customers receive priority technical support with SLA guarantees.

### Support Tiers

| Tier | Response Time | Availability | Channels |
|------|---------------|--------------|----------|
| Standard | 24 hours | Business hours | Email |
| Professional | 8 hours | Extended hours | Email, Chat |
| Enterprise | 4 hours | 24/7 | Email, Chat, Phone |

### Included Services

- Dedicated support engineer
- Implementation assistance
- Configuration review
- Security assessment guidance
- Custom integration support
- Training sessions

---

## Enterprise vs Community

| Feature | Community | Enterprise |
|---------|:---------:|:----------:|
| Incident Management | ✅ | ✅ |
| SOC (Alerts, Cases, Playbooks) | ✅ | ✅ |
| Vulnerability Management | ✅ | ✅ |
| Risk Management | ✅ | ✅ |
| TPRM (Third-Party Risk) | ✅ | ✅ |
| CMDB | ✅ | ✅ |
| Threat Intelligence | ✅ | ✅ |
| NIST CSF Compliance | ✅ | ✅ |
| Reporting & Analytics | ✅ | ✅ |
| Multi-tenancy | ✅ | ✅ |
| SSO/SAML | ✅ | ✅ |
| Audit Logging | ✅ | ✅ |
| API Rate Limiting | ✅ | ✅ |
| **ISO 27001:2022** | ❌ | ✅ |
| **Business Continuity (BCM)** | ❌ | ✅ |
| **BSI IT-Grundschutz** | ❌ | ✅ |
| **NIS2 Assessment** | ❌ | ✅ |
| **AI Copilot** | ❌ | ✅ |
| **PDF Reports (LaTeX)** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |
| **SLA Guarantee** | ❌ | ✅ |

---

## API Access

Enterprise features are available through the standard API with enterprise license authentication.

### Base URL

```
/api/v1/iso27001/...     # ISO 27001 endpoints (18 endpoints)
/api/v1/bcm/...          # Business Continuity Management endpoints (43 endpoints)
/api/v1/bsi/...          # BSI IT-Grundschutz endpoints (18 endpoints)
/api/v1/nis2/...         # NIS2 Directive endpoints (14 endpoints)
/api/v1/copilot/...      # AI Copilot endpoints (9 endpoints)
/api/v1/reports/...      # PDF Report generation endpoints (3 endpoints)
```

### Authentication

Enterprise endpoints require:
1. Valid user authentication (JWT)
2. Organization with Enterprise plan
3. Feature enabled for organization

---

## Licensing

### License Types

| License | Users | Organizations | Features |
|---------|-------|---------------|----------|
| Community | Unlimited | Unlimited | Core features |
| Enterprise Starter | Up to 25 | 1 | All enterprise features |
| Enterprise Professional | Up to 100 | Up to 5 | All + priority support |
| Enterprise Unlimited | Unlimited | Unlimited | All + dedicated support |

### Contact

For enterprise licensing inquiries:
- Email: enterprise@cyberops-companion.io
- Website: https://cyberops-companion.io/enterprise

---

## Installation

Enterprise features are included in the standard installation. Enable them by:

1. Obtain enterprise license key
2. Configure in `.env`:
   ```env
   ENTERPRISE_LICENSE_KEY=your-license-key
   ```
3. Features automatically unlock based on license

---

## Related Documentation

- [ISO 27001:2022](./features/ISO27001.md) - Detailed ISO 27001 documentation
- [Business Continuity Management](./features/BCM.md) - BCM module documentation
- [Multi-Tenancy](./features/MULTI_TENANCY.md) - Organization management
- [SSO/SAML](./features/SSO_SAML.md) - Single sign-on configuration
- [Audit Logging](./features/AUDIT_LOGGING.md) - Compliance audit trails
- [Rate Limiting](./features/RATE_LIMITING.md) - API protection

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.2.0 | 2026-02-05 | AI Copilot with 5 LLM providers (Ollama, OpenAI, Anthropic, Gemini, Groq), streaming support |
| 2.1.0 | 2026-02-05 | BCM module with BIA wizard, emergency plans, and exercises |
| 2.0.0 | 2026-02-05 | ISO 27001:2022 module with full wizard and PDF reports |
| 1.9.0 | 2026-02-01 | BSI IT-Grundschutz: 61 Bausteine, 276 Anforderungen, dashboard, PDF reports |
| 1.8.0 | 2026-02-01 | NIS2 Directive: 5-step wizard, 18 sectors, automatic classification |
| 1.7.0 | 2026-02-01 | PDF Reports with LaTeX (DIN 5008 standard) |

---

*ISORA Enterprise - Comprehensive Compliance for Security Teams*
