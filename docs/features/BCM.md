# Business Continuity Management (BCM) Module

The BCM Module provides comprehensive Business Continuity Management capabilities based on **BSI Standard 200-4** and **ISO 22301**.

## Overview

Business Continuity Management ensures organizations can maintain critical business functions during and after disruptions. This module implements:

- **Business Process Inventory** with criticality classification
- **Business Impact Analysis (BIA)** wizard with recovery objectives
- **Risk Scenario Assessment** with likelihood/impact scoring
- **Continuity Strategies** for process protection
- **Emergency Plans** (Notfallkonzepte) with structured procedures
- **BC Exercises** for testing and validation
- **BCM Maturity Assessment** with scoring

## Module Structure

```
BCM Module
├── Business Processes (Geschäftsprozesse)
│   └── Critical business processes with dependencies
│
├── Business Impact Analysis (BIA)
│   ├── RTO (Recovery Time Objective)
│   ├── RPO (Recovery Point Objective)
│   ├── MTPD (Maximum Tolerable Period of Disruption)
│   └── Impact categories (Financial, Operational, etc.)
│
├── Risk Scenarios
│   ├── Threat scenarios by category
│   ├── Likelihood/Impact assessment
│   └── Single Points of Failure
│
├── Continuity Strategies
│   ├── Prevention measures
│   └── Recovery strategies
│
├── Emergency Plans (Notfallkonzept)
│   ├── Response procedures
│   ├── Communication plans
│   └── Recovery runbooks
│
├── BC Exercises (Tests)
│   ├── Tabletop exercises
│   ├── Simulations
│   └── Full interruption tests
│
└── BCM Assessment
    └── Overall BCM maturity evaluation
```

## Key Concepts

### Recovery Objectives

| Objective | Definition | Example |
|-----------|------------|---------|
| **RTO** | Recovery Time Objective - Maximum time to restore the process | 4 hours |
| **RPO** | Recovery Point Objective - Maximum acceptable data loss | 1 hour |
| **MTPD** | Maximum Tolerable Period of Disruption | 24 hours |

### Impact Categories

Each business process is assessed across 5 impact categories (scale 1-5):

1. **Financial Impact** - Revenue loss, penalties, recovery costs
2. **Operational Impact** - Process disruption, productivity loss
3. **Reputational Impact** - Brand damage, customer trust
4. **Legal/Compliance Impact** - Regulatory violations, lawsuits
5. **Health & Safety Impact** - Employee and public safety

### Risk Scenario Categories

| Category | German | Examples |
|----------|--------|----------|
| Natural Disaster | Naturkatastrophen | Flood, earthquake, storm |
| Technical Failure | Technische Ausfälle | Power outage, hardware failure |
| Human Error | Menschliches Versagen | Configuration error, accidental deletion |
| Cyber Attack | Cyberangriffe | Ransomware, DDoS, data breach |
| Pandemic | Pandemie | Staff unavailability |
| Supply Chain | Lieferkettenausfall | Vendor failure, material shortage |
| Infrastructure | Infrastrukturausfall | Telecom outage, building access |

### Continuity Strategy Types

| Type | Description | Use Case |
|------|-------------|----------|
| Do Nothing | Accept the risk | Low-impact processes |
| Manual Workaround | Alternative manual procedures | Short-term disruptions |
| Alternate Site | Move to backup location | Site unavailability |
| Alternate Supplier | Use backup vendor | Vendor failure |
| Redundancy | Redundant systems/infrastructure | Critical systems |
| Outsource | Outsource during crisis | Specialized capabilities |
| Insurance | Financial mitigation | Financial protection |

### Emergency Plan Types

| Type | German | Purpose |
|------|--------|---------|
| Crisis Management | Krisenmanagement | Overall crisis coordination |
| Emergency Response | Notfallreaktion | Initial response procedures |
| Business Recovery | Geschäftswiederherstellung | Process restoration |
| IT Disaster Recovery | IT-Wiederherstellung | IT systems recovery |
| Communication | Kommunikationsplan | Stakeholder communication |
| Evacuation | Evakuierungsplan | Physical evacuation |

## BIA Wizard (6 Steps)

### Step 1: Process Details
Review the business process information:
- Process ID and name
- Owner and department
- Criticality level
- Dependencies (internal, external, IT systems)
- Key personnel

### Step 2: Impact Timeline
Assess how impact changes over time:
- 1 hour: Initial impact
- 4 hours: Short-term impact
- 8 hours: Half-day impact
- 24 hours: Full-day impact
- 72 hours: 3-day impact
- 1 week: Extended impact

Impact levels: None, Low, Medium, High, Critical

### Step 3: Impact Categories
Rate impact severity for each category (1-5 scale):
- Financial Impact with justification
- Operational Impact with justification
- Reputational Impact
- Legal/Compliance Impact
- Health & Safety Impact

### Step 4: Recovery Objectives
Define recovery targets based on impact analysis:
- **RTO**: When must the process be restored?
- **RPO**: How much data loss is acceptable?
- **MTPD**: What's the absolute maximum downtime?

Visual timeline shows the relationship between RPO, RTO, and MTPD.

### Step 5: Resource Requirements
Identify minimum resources needed for recovery:
- Minimum staff required
- Minimum workspace
- Critical equipment list
- Critical data/systems list

### Step 6: Review & Complete
Review the complete BIA:
- Recovery objectives summary
- Impact categories overview
- Resource requirements
- Set analyst name and next review date
- Complete the BIA

## Scoring Formula

### Risk Score (Scenarios)

```
risk_score = likelihood_value × impact_value
```

Where likelihood and impact are rated 1-5:
- **Likelihood**: Rare(1), Unlikely(2), Possible(3), Likely(4), Almost Certain(5)
- **Impact**: Negligible(1), Minor(2), Moderate(3), Major(4), Catastrophic(5)

Risk score range: 1-25

### BCM Maturity Score

```
overall_score = (
    process_coverage × 0.15 +    # 15%
    bia_completion × 0.25 +      # 25%
    strategy_coverage × 0.20 +   # 20%
    plan_coverage × 0.25 +       # 25%
    test_coverage × 0.15         # 15%
)
```

Individual scores:
- `process_coverage` = documented / total critical processes × 100
- `bia_completion` = processes with complete BIA / total processes × 100
- `strategy_coverage` = processes with strategy / processes needing strategy × 100
- `plan_coverage` = processes with plan / critical processes × 100
- `test_coverage` = plans tested this year / total active plans × 100

## API Endpoints

### Dashboard

```
GET  /api/v1/bcm/dashboard                    # BCM program overview
```

### Business Processes

```
GET    /api/v1/bcm/processes                  # List processes
POST   /api/v1/bcm/processes                  # Create process
GET    /api/v1/bcm/processes/{id}             # Get process
PUT    /api/v1/bcm/processes/{id}             # Update process
DELETE /api/v1/bcm/processes/{id}             # Delete process
```

### Business Impact Analysis

```
GET  /api/v1/bcm/processes/{id}/bia           # Get BIA for process
POST /api/v1/bcm/processes/{id}/bia           # Create/Update BIA
GET  /api/v1/bcm/bia/summary                  # BIA summary across all
```

### Risk Scenarios

```
GET    /api/v1/bcm/scenarios                  # List scenarios
POST   /api/v1/bcm/scenarios                  # Create scenario
GET    /api/v1/bcm/scenarios/{id}             # Get scenario
PUT    /api/v1/bcm/scenarios/{id}             # Update scenario
DELETE /api/v1/bcm/scenarios/{id}             # Delete scenario
GET    /api/v1/bcm/scenarios/risk-matrix      # Risk matrix data
```

### Continuity Strategies

```
GET    /api/v1/bcm/processes/{id}/strategies  # List strategies for process
POST   /api/v1/bcm/processes/{id}/strategies  # Create strategy
PUT    /api/v1/bcm/strategies/{id}            # Update strategy
DELETE /api/v1/bcm/strategies/{id}            # Delete strategy
```

### Emergency Plans

```
GET    /api/v1/bcm/plans                      # List plans
POST   /api/v1/bcm/plans                      # Create plan
GET    /api/v1/bcm/plans/{id}                 # Get plan details
PUT    /api/v1/bcm/plans/{id}                 # Update plan
DELETE /api/v1/bcm/plans/{id}                 # Delete plan
POST   /api/v1/bcm/plans/{id}/approve         # Approve plan
GET    /api/v1/bcm/plans/{id}/export          # Export as PDF
```

### Emergency Contacts

```
GET    /api/v1/bcm/contacts                   # List contacts
POST   /api/v1/bcm/contacts                   # Create contact
PUT    /api/v1/bcm/contacts/{id}              # Update contact
DELETE /api/v1/bcm/contacts/{id}              # Delete contact
```

### BC Exercises

```
GET    /api/v1/bcm/exercises                  # List exercises
POST   /api/v1/bcm/exercises                  # Create exercise
GET    /api/v1/bcm/exercises/{id}             # Get exercise
PUT    /api/v1/bcm/exercises/{id}             # Update exercise
DELETE /api/v1/bcm/exercises/{id}             # Delete exercise
POST   /api/v1/bcm/exercises/{id}/complete    # Complete with results
```

### BCM Assessments

```
GET    /api/v1/bcm/assessments                # List assessments
POST   /api/v1/bcm/assessments                # Create assessment
GET    /api/v1/bcm/assessments/{id}           # Get assessment
DELETE /api/v1/bcm/assessments/{id}           # Delete assessment
GET    /api/v1/bcm/assessments/{id}/wizard-state  # Wizard progress
POST   /api/v1/bcm/assessments/{id}/complete  # Mark complete
GET    /api/v1/bcm/assessments/{id}/report    # Generate report
```

## Database Schema

### Tables (All Tenant-Scoped)

| Table | Description |
|-------|-------------|
| `bcm_processes` | Business processes with criticality and dependencies |
| `bcm_bia` | Business Impact Analysis records |
| `bcm_risk_scenarios` | Risk scenarios with likelihood/impact |
| `bcm_strategies` | Continuity strategies for processes |
| `bcm_emergency_plans` | Emergency plans with procedures |
| `bcm_contacts` | Emergency contact list |
| `bcm_exercises` | BC exercises and test results |
| `bcm_assessments` | BCM maturity assessments |

## Setup

### 1. Run Database Migration

```bash
cd apps/api
alembic upgrade head
```

### 2. Seed Template Data

```bash
python -m src.db.seed_bcm
```

This seeds:
- 4 emergency plan templates
- 8 risk scenario templates
- 4 exercise templates
- Demo processes and contacts

### 3. Verify Installation

```bash
# Check dashboard
curl http://localhost:8000/api/v1/bcm/dashboard \
  -H "Authorization: Bearer $TOKEN"

# List processes
curl http://localhost:8000/api/v1/bcm/processes \
  -H "Authorization: Bearer $TOKEN"
```

## PDF Reports

PDF reports require the `reportlab` library:

```bash
pip install reportlab
```

Generate reports:

```bash
# Emergency plan PDF
GET /api/v1/bcm/plans/{id}/export?format=pdf

# BCM assessment report
GET /api/v1/bcm/assessments/{id}/report?format=pdf
```

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/bcm` | Main dashboard with tabs |
| `/bcm/processes/{id}` | Process detail and strategies |
| `/bcm/bia/{id}` | BIA wizard (6 steps) |
| `/bcm/plans/{id}` | Emergency plan editor |
| `/bcm/plans/new` | Create new plan |
| `/bcm/exercises/{id}` | Exercise detail |
| `/bcm/exercises/new` | Schedule new exercise |

## Cross-References

BCM integrates with other modules:

| Module | Integration |
|--------|-------------|
| **CMDB** | IT systems linked to processes |
| **Risk Management** | BCM scenarios feed into risk register |
| **Incident Management** | Crisis activations create incidents |
| **ISO 27001** | A.5.29, A.5.30 control mapping |
| **NIS2** | Business continuity measures |

## Best Practices

1. **Start with Critical Processes**: Identify and document critical processes first
2. **Complete BIA Early**: Conduct BIA before developing strategies
3. **Define Clear Objectives**: Set realistic RTO/RPO based on business needs
4. **Document Dependencies**: Map all internal and external dependencies
5. **Test Regularly**: Conduct exercises at least annually
6. **Update After Changes**: Review plans after organizational changes
7. **Involve Stakeholders**: Include process owners in BIA and planning
8. **Keep Contacts Current**: Regularly verify emergency contact information

## Compliance Mapping

| Standard | Relevant Controls |
|----------|-------------------|
| ISO 27001:2022 | A.5.29, A.5.30 |
| ISO 22301 | Clauses 4-10 |
| BSI 200-4 | BCM process model |
| NIS2 | Article 21 (Business Continuity) |
| NIST CSF | PR.IP-9, PR.IP-10 |

## OSCAL Catalog

This module includes a machine-readable representation of **BSI Standard 200-4** in [OSCAL](https://pages.nist.gov/OSCAL/) (Open Security Controls Assessment Language) format.

### What is OSCAL?

OSCAL is a standardized format developed by NIST for representing security and compliance information in machine-readable formats (JSON, XML, YAML). It enables:

- **Automation** - Tools can read and process controls automatically
- **Interoperability** - Different systems can share compliance data
- **Consistency** - Standardized format for any framework
- **Mappings** - Facilitates relating controls between different standards

### OSCAL Models

| Model | Purpose |
|-------|---------|
| **Catalog** | Defines controls (used for BSI 200-4) |
| **Profile** | Selection/customization of controls |
| **Component Definition** | Security capabilities of a system |
| **System Security Plan** | Organization's security plan |
| **Assessment Plan/Results** | Audit plans and results |
| **Plan of Action & Milestones** | Finding tracking |

### BSI 200-4 OSCAL Catalog

Location: `apps/api/src/db/data/bsi_200_4_catalog.json`

The catalog follows OSCAL Catalog Model v1.1.2 and contains:

| Group ID | Title (DE) | Title (EN) | Controls |
|----------|------------|------------|----------|
| BCM-1 | BCMS-Rahmenwerk | BCMS Framework | 5 |
| BCM-2 | Business Impact Analysis | Business Impact Analysis | 6 |
| BCM-3 | Risikoanalyse | Risk Assessment | 4 |
| BCM-4 | Kontinuitätsstrategien | BC Strategies | 4 |
| BCM-5 | Notfallpläne | Emergency Plans | 7 |
| BCM-6 | Übungen und Tests | Exercises and Testing | 5 |
| BCM-7 | Pflege und Verbesserung | Maintenance and Improvement | 5 |
| BCM-8 | Krisenmanagement | Crisis Management | 4 |

**Total: 8 groups, 40 controls**

Each control includes:
- German and English titles
- Priority level: `must`, `should`, `informative`
- ISO 22301:2019 clause mapping
- Statement, guidance, and assessment objectives

### Using the OSCAL Catalog

```python
import json

with open('bsi_200_4_catalog.json', 'r') as f:
    catalog = json.load(f)

# Access groups
for group in catalog['catalog']['groups']:
    print(f"{group['id']}: {group['title']}")
    for control in group.get('controls', []):
        print(f"  {control['id']}: {control['title']}")
```

### Validating the Catalog

```bash
# Using oscal-cli (https://github.com/usnistgov/oscal-cli)
oscal-cli catalog validate bsi_200_4_catalog.json
```

## References

### Official Standards

| Standard | Source | Description |
|----------|--------|-------------|
| **BSI Standard 200-4** | [BSI Official](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/BSI-Standards/BSI-Standard-200-4-Business-Continuity-Management/bsi-standard-200-4_Business_Continuity_Management_node.html) | German BCM standard |
| **ISO 22301:2019** | [ISO Official](https://www.iso.org/standard/75106.html) | International BCM standard |
| **OSCAL** | [NIST OSCAL](https://pages.nist.gov/OSCAL/) | Security controls format |

### BSI Resources

- [BSI Standard 200-4 PDF (German)](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_4.html)
- [BSI IT-Grundschutz Compendium](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/IT-Grundschutz-Kompendium/it-grundschutz-kompendium_node.html)
- [BSI GitHub - Stand-der-Technik-Bibliothek](https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek)

### ISO 22301 Resources

- [ISO 22301:2019 - Security and resilience](https://www.iso.org/standard/75106.html)
- [ISO 22313:2020 - BCM Guidance](https://www.iso.org/standard/75107.html)
- [ISO 22317:2021 - BIA Guidelines](https://www.iso.org/standard/79000.html)

### OSCAL Resources

- [NIST OSCAL Documentation](https://pages.nist.gov/OSCAL/)
- [OSCAL GitHub Repository](https://github.com/usnistgov/OSCAL)
- [OSCAL CLI Tool](https://github.com/usnistgov/oscal-cli)
- [OSCAL Catalog Model](https://pages.nist.gov/OSCAL/concepts/layer/control/catalog/)

### Related Standards

- [NIST SP 800-34 Rev. 1](https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final) - Contingency Planning Guide
- [NIST CSF 2.0](https://www.nist.gov/cyberframework) - Cybersecurity Framework
- [NIS2 Directive](https://digital-strategy.ec.europa.eu/en/policies/nis2-directive) - EU Network and Information Security

---

*Business Continuity Management - Ensuring organizational resilience*
