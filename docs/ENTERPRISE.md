# CyberOps Companion - Enterprise Edition

**Status:** Available
**License:** Commercial License

---

## Overview

CyberOps Companion Enterprise extends the open-source Community edition with advanced compliance modules, AI-powered assistance, and priority support. Designed for organizations requiring comprehensive regulatory compliance and enterprise-grade features.

---

## Enterprise Features

| Feature | Description | Status |
|---------|-------------|--------|
| [ISO 27001:2022 Compliance](#iso-270012022-compliance) | Full ISMS assessment with 93 controls | ✅ Available |
| [BSI IT-Grundschutz](#bsi-it-grundschutz) | German federal security standards | ✅ Available |
| [NIS2 Directive Assessment](#nis2-directive-assessment) | EU cybersecurity directive compliance | ✅ Available |
| [AI Copilot](#ai-copilot) | Multi-LLM security assistant | 🔜 Coming Soon |
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

## BSI IT-Grundschutz

Implementation of the German Federal Office for Information Security (BSI) IT-Grundschutz methodology.

### Features

- **IT-Grundschutz Kompendium** catalog
- **Baustein** (building block) browser
- **Requirement** assessment wizard
- **Gap analysis** with remediation planning
- **Cross-mapping** to ISO 27001 and NIS2

### Use Cases

- German federal agency compliance
- KRITIS (critical infrastructure) operators
- Organizations seeking BSI certification
- Defense sector contractors

---

## NIS2 Directive Assessment

Compliance assessment for the EU Network and Information Security Directive 2 (NIS2).

### Features

- **NIS2 Measure Catalog**:
  - Risk management policies
  - Incident handling procedures
  - Business continuity measures
  - Supply chain security
  - Cybersecurity hygiene practices

- **Assessment Workflow**:
  - Sector classification (Essential/Important)
  - Measure applicability determination
  - Implementation status tracking
  - Evidence documentation

- **Reporting**:
  - Compliance status dashboard
  - Gap analysis report
  - Remediation roadmap
  - Audit-ready documentation

### Applicability

Required for organizations in these sectors:
- Energy, Transport, Banking, Financial markets
- Health, Water supply, Digital infrastructure
- ICT service management, Public administration
- Space, Postal services, Waste management
- Manufacturing, Food, Chemicals, Research

---

## AI Copilot

AI-powered security assistant using multiple LLM providers.

### Planned Features

- **Incident Analysis**: Automated incident triage and classification
- **Threat Intelligence**: IOC analysis and threat correlation
- **Compliance Guidance**: Context-aware control recommendations
- **Report Generation**: Automated executive summaries
- **Query Interface**: Natural language security queries

### Supported Providers (Planned)

- OpenAI (GPT-4)
- Anthropic (Claude)
- Azure OpenAI
- Local LLMs (Ollama)

### Status

🔜 **Coming Soon** - Currently in development

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
| **BSI IT-Grundschutz** | ❌ | ✅ |
| **NIS2 Assessment** | ❌ | ✅ |
| **AI Copilot** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |
| **SLA Guarantee** | ❌ | ✅ |

---

## API Access

Enterprise features are available through the standard API with enterprise license authentication.

### Base URL

```
/api/v1/iso27001/...     # ISO 27001 endpoints
/api/v1/bsi/...          # BSI IT-Grundschutz endpoints
/api/v1/nis2/...         # NIS2 Directive endpoints
/api/v1/copilot/...      # AI Copilot endpoints (coming soon)
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
- [Multi-Tenancy](./features/MULTI_TENANCY.md) - Organization management
- [SSO/SAML](./features/SSO_SAML.md) - Single sign-on configuration
- [Audit Logging](./features/AUDIT_LOGGING.md) - Compliance audit trails
- [Rate Limiting](./features/RATE_LIMITING.md) - API protection

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-02-05 | ISO 27001:2022 module with full wizard and PDF reports |
| 1.9.0 | 2026-02-01 | BSI IT-Grundschutz catalog and assessment |
| 1.8.0 | 2026-02-01 | NIS2 Directive assessment wizard |

---

*CyberOps Companion Enterprise - Comprehensive Compliance for Security Teams*
