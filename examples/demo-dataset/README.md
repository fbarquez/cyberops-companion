# ISOVA Demo Dataset

> Fictional dataset for testing and demonstration purposes

## Overview

This directory contains a complete demo dataset for ISOVA featuring a fictional manufacturing company. Use this data for:

- Testing new installations
- Demonstrating features to prospects
- Training new users
- Development and testing

**Disclaimer:** This is entirely fictional data. Any resemblance to real companies, persons, or situations is coincidental.

## Fictional Company Profile

**Müller Maschinenbau GmbH** (fictional)

| Attribute | Value |
|-----------|-------|
| Industry | Manufacturing / Mechanical Engineering |
| Location | Schwäbisch Hall, Germany |
| Employees | 220 |
| Revenue | 35 Mio. EUR |
| IT Team | 4 persons |
| Current Status | ISO 9001 certified, no IT certification |
| NIS2 Indication | Important Entity (Annex II) |

### Organizational Structure

```
Müller Maschinenbau GmbH
├── IT Department (4 people)
│   ├── Thomas Weber (IT-Leiter)
│   ├── Sandra Müller (System Admin)
│   ├── Michael Schmidt (Network Admin)
│   └── Lisa Fischer (Helpdesk)
│
├── Production (180 people)
│   └── 12 CNC machines, 3 assembly lines
│
├── Administration (30 people)
│   ├── Finance
│   ├── HR
│   └── Sales
│
└── Engineering (10 people)
    └── CAD/CAM systems
```

## Dataset Files

### organizations.json

```json
{
  "organizations": [
    {
      "id": "org-demo-mueller",
      "name": "Müller Maschinenbau GmbH",
      "industry": "manufacturing",
      "employees": 220,
      "revenue_eur": 35000000,
      "location": {
        "city": "Schwäbisch Hall",
        "country": "DE",
        "timezone": "Europe/Berlin"
      },
      "nis2_classification": "important_entity",
      "frameworks": ["nis2", "iso27001"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### users.json

```json
{
  "users": [
    {
      "id": "user-demo-weber",
      "email": "t.weber@mueller-maschinenbau.example",
      "name": "Thomas Weber",
      "role": "IT-Leiter",
      "organization_id": "org-demo-mueller",
      "permissions": ["admin", "evidence.create", "evidence.confirm", "reports.generate"],
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "user-demo-smueller",
      "email": "s.mueller@mueller-maschinenbau.example",
      "name": "Sandra Müller",
      "role": "System Administrator",
      "organization_id": "org-demo-mueller",
      "permissions": ["evidence.create", "evidence.view"],
      "created_at": "2024-01-02T00:00:00Z"
    },
    {
      "id": "user-demo-schmidt",
      "email": "m.schmidt@mueller-maschinenbau.example",
      "name": "Michael Schmidt",
      "role": "Network Administrator",
      "organization_id": "org-demo-mueller",
      "permissions": ["evidence.create", "evidence.view"],
      "created_at": "2024-01-02T00:00:00Z"
    }
  ]
}
```

### evidences.json

```json
{
  "evidences": [
    {
      "id": "ev-demo-001",
      "organization_id": "org-demo-mueller",
      "title": "Security Awareness Training Q1 2024",
      "description": "Annual phishing awareness training for all employees",
      "evidence_type": "attestation",
      "status": "confirmed",
      "attestation_data": {
        "statement": "Security awareness training on phishing recognition was conducted for 45 participants.",
        "basis": "document",
        "training_date": "2024-01-15",
        "participants": 45,
        "topic": "Phishing recognition",
        "provider": "SecAware GmbH (external)"
      },
      "control_ids": ["nis2:M07", "iso27001:A.6.3"],
      "confirmed_by": "user-demo-weber",
      "confirmed_by_name": "Thomas Weber",
      "confirmed_by_role": "IT-Leiter",
      "confirmed_at": "2024-01-20T14:30:00Z",
      "valid_from": "2024-01-15T00:00:00Z",
      "valid_until": "2025-01-15T00:00:00Z",
      "content_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "version": 1,
      "created_at": "2024-01-16T10:00:00Z"
    },
    {
      "id": "ev-demo-002",
      "organization_id": "org-demo-mueller",
      "title": "Backup Verification February 2024",
      "description": "Monthly backup completion verification with restore test",
      "evidence_type": "attestation",
      "status": "confirmed",
      "attestation_data": {
        "statement": "Full backup completed successfully. Restore test performed and verified.",
        "basis": "system_log",
        "backup_date": "2024-02-01",
        "backup_type": "full",
        "systems": ["ERP (SAP Business One)", "Fileserver", "Exchange Online"],
        "restore_test": true,
        "restore_test_date": "2024-02-02",
        "restore_success": true
      },
      "control_ids": ["nis2:M03", "iso27001:A.8.13"],
      "confirmed_by": "user-demo-smueller",
      "confirmed_by_name": "Sandra Müller",
      "confirmed_by_role": "System Administrator",
      "confirmed_at": "2024-02-02T09:00:00Z",
      "valid_from": "2024-02-01T00:00:00Z",
      "valid_until": "2024-03-01T00:00:00Z",
      "content_hash": "b2c3d4e5f67890123456789012345678901234abcdef567890abcdef12345678",
      "version": 1,
      "created_at": "2024-02-01T15:00:00Z"
    },
    {
      "id": "ev-demo-003",
      "organization_id": "org-demo-mueller",
      "title": "MFA Status Q1 2024",
      "description": "Multi-factor authentication coverage documentation",
      "evidence_type": "attestation",
      "status": "confirmed",
      "attestation_data": {
        "statement": "MFA is active for VPN and Microsoft 365. Coverage: 80% of users.",
        "basis": "sample",
        "systems_with_mfa": ["VPN (FortiClient)", "Microsoft 365"],
        "coverage_percent": 80,
        "method": "Microsoft Authenticator",
        "exceptions": "Production terminals (documented exception)",
        "exceptions_count": 12,
        "exceptions_justified": true
      },
      "control_ids": ["nis2:M10", "iso27001:A.8.5"],
      "confirmed_by": "user-demo-weber",
      "confirmed_by_name": "Thomas Weber",
      "confirmed_by_role": "IT-Leiter",
      "confirmed_at": "2024-02-05T11:00:00Z",
      "valid_from": "2024-02-05T00:00:00Z",
      "valid_until": "2024-05-05T00:00:00Z",
      "content_hash": "c3d4e5f678901234567890123456789012345abcdef67890abcdef1234567890",
      "version": 1,
      "created_at": "2024-02-05T10:00:00Z"
    },
    {
      "id": "ev-demo-004",
      "organization_id": "org-demo-mueller",
      "title": "IT Security Policy 2024",
      "description": "Updated IT security policy document",
      "evidence_type": "document",
      "status": "confirmed",
      "document_data": {
        "filename": "IT_Sicherheitsrichtlinie_2024_v2.pdf",
        "mime_type": "application/pdf",
        "file_size": 524288,
        "file_hash": "sha256:d4e5f6789012345678901234567890123456abcdef7890abcdef12345678901",
        "pages": 24,
        "language": "de"
      },
      "control_ids": ["nis2:M01", "iso27001:A.5.1"],
      "confirmed_by": "user-demo-weber",
      "confirmed_by_name": "Thomas Weber",
      "confirmed_by_role": "IT-Leiter",
      "confirmed_at": "2024-01-10T16:00:00Z",
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_until": "2025-01-01T00:00:00Z",
      "content_hash": "e5f678901234567890123456789012345678abcdef890abcdef123456789012",
      "version": 2,
      "previous_version_id": "ev-demo-004-v1",
      "created_at": "2024-01-10T14:00:00Z"
    },
    {
      "id": "ev-demo-005",
      "organization_id": "org-demo-mueller",
      "title": "Access Rights Review Q4 2023",
      "description": "Quarterly review of Active Directory access rights",
      "evidence_type": "attestation",
      "status": "confirmed",
      "attestation_data": {
        "statement": "Quarterly access rights review completed. 3 outdated accounts deactivated.",
        "basis": "observation",
        "review_date": "2023-12-15",
        "accounts_reviewed": 245,
        "accounts_deactivated": 3,
        "accounts_modified": 12,
        "reviewer": "Sandra Müller"
      },
      "control_ids": ["nis2:M09", "iso27001:A.5.18"],
      "confirmed_by": "user-demo-weber",
      "confirmed_by_name": "Thomas Weber",
      "confirmed_by_role": "IT-Leiter",
      "confirmed_at": "2023-12-18T10:00:00Z",
      "valid_from": "2023-12-15T00:00:00Z",
      "valid_until": "2024-03-15T00:00:00Z",
      "content_hash": "f67890123456789012345678901234567890abcdef90abcdef12345678901234",
      "version": 1,
      "created_at": "2023-12-15T16:00:00Z"
    }
  ]
}
```

### assessment.json

```json
{
  "assessment": {
    "id": "assess-demo-001",
    "organization_id": "org-demo-mueller",
    "framework": "nis2",
    "assessed_at": "2024-02-01T10:00:00Z",
    "assessed_by": "user-demo-weber",
    "measures": [
      {
        "id": "M01",
        "name_de": "Risikoanalyse und Sicherheitskonzepte",
        "name_en": "Risk analysis and security policies",
        "status": "partial",
        "note": "IT-Richtlinie existiert (2024 aktualisiert), formale Risikoanalyse fehlt",
        "action": "Formale Risikobewertung durchführen bis Q2 2024",
        "evidence_ids": ["ev-demo-004"]
      },
      {
        "id": "M02",
        "name_de": "Bewältigung von Sicherheitsvorfällen",
        "name_en": "Incident handling",
        "status": "open",
        "note": "Kein formaler Incident-Response-Prozess. Ad-hoc Behandlung.",
        "action": "Incident-Response-Plan erstellen",
        "priority": "high",
        "evidence_ids": []
      },
      {
        "id": "M03",
        "name_de": "Business Continuity",
        "name_en": "Business continuity",
        "status": "partial",
        "note": "Backup vorhanden und getestet. Notfallplan fehlt.",
        "action": "Disaster-Recovery-Plan erstellen",
        "evidence_ids": ["ev-demo-002"]
      },
      {
        "id": "M04",
        "name_de": "Sicherheit der Lieferkette",
        "name_en": "Supply chain security",
        "status": "open",
        "note": "Keine systematische Lieferantenbewertung. Kritische Lieferanten: SAP, Microsoft, Fortinet.",
        "action": "Top-10 Lieferanten bewerten",
        "priority": "high",
        "evidence_ids": []
      },
      {
        "id": "M05",
        "name_de": "Sichere Entwicklung",
        "name_en": "Secure development",
        "status": "na",
        "note": "Keine eigene Softwareentwicklung. CAD/CAM wird nicht als Entwicklung betrachtet.",
        "evidence_ids": []
      },
      {
        "id": "M06",
        "name_de": "Wirksamkeitsprüfung",
        "name_en": "Effectiveness assessment",
        "status": "open",
        "note": "Keine Penetrationstests oder formalen Audits durchgeführt.",
        "action": "Jährlichen Pentest planen",
        "evidence_ids": []
      },
      {
        "id": "M07",
        "name_de": "Cyberhygiene und Schulungen",
        "name_en": "Cyber hygiene and training",
        "status": "partial",
        "note": "Einmalige Schulung in 2024. Kein kontinuierliches Programm.",
        "action": "Jährliches Awareness-Programm etablieren",
        "evidence_ids": ["ev-demo-001"]
      },
      {
        "id": "M08",
        "name_de": "Kryptografie",
        "name_en": "Cryptography",
        "status": "partial",
        "note": "TLS für Web-Dienste. Festplattenverschlüsselung nur für Laptops.",
        "action": "Verschlüsselung für alle mobilen Geräte",
        "evidence_ids": []
      },
      {
        "id": "M09",
        "name_de": "Personalsicherheit, Zugriffskontrolle",
        "name_en": "HR security, access control",
        "status": "fulfilled",
        "note": "Active Directory mit RBAC. Regelmäßige Reviews.",
        "evidence_ids": ["ev-demo-005"]
      },
      {
        "id": "M10",
        "name_de": "Multi-Faktor-Authentifizierung",
        "name_en": "Multi-factor authentication",
        "status": "partial",
        "note": "MFA für VPN und M365 (80%). ERP noch ohne MFA.",
        "action": "MFA auf ERP-System ausweiten",
        "evidence_ids": ["ev-demo-003"]
      }
    ],
    "summary": {
      "fulfilled": 1,
      "partial": 5,
      "open": 3,
      "na": 1,
      "total": 10,
      "completion_percent": 45
    }
  }
}
```

## How to Load

### Option 1: API Import

```bash
# Set your API base URL
API_URL="http://localhost:8000/api/v1"

# Import organization
curl -X POST "$API_URL/import/organizations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @organizations.json

# Import users
curl -X POST "$API_URL/import/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @users.json

# Import evidences
curl -X POST "$API_URL/import/evidences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @evidences.json

# Import assessment
curl -X POST "$API_URL/import/assessment" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @assessment.json
```

### Option 2: Docker

```bash
# Start services with demo data
docker-compose up -d

# Load demo data
docker-compose exec api python scripts/load_demo_data.py --path /app/examples/demo-dataset
```

### Option 3: Make Command

```bash
# Load demo data into running instance
make demo-data

# Start fresh with demo data
make dev-demo
```

## Included Scenarios

This dataset demonstrates:

| Scenario | Example | Status |
|----------|---------|--------|
| Confirmed attestation | Training (ev-demo-001) | ✅ Active |
| Document evidence | IT Policy (ev-demo-004) | ✅ Active |
| Expiring soon | Backup (ev-demo-002) | ⏰ Expires in <30 days |
| Multiple control links | Each evidence linked to NIS2 + ISO | ✅ |
| Different basis types | document, system_log, sample, observation | ✅ |
| Versioned evidence | IT Policy v2 | ✅ |
| Open measures | M02, M04, M06 | ⚠️ Need attention |
| N/A measure | M05 (no development) | ⚪ |
| Partial measures | M01, M03, M07, M08, M10 | 🟡 |
| Fulfilled measure | M09 (access control) | 🟢 |

## Customization

To create your own demo dataset:

1. Copy this directory
2. Replace company details in `organizations.json`
3. Update user names/emails (keep `.example` TLD)
4. Adjust evidence entries for your scenario
5. Update assessment status as needed

### Email Convention

Always use `.example` TLD for fictional emails (per RFC 2606):
- ✅ `t.weber@mueller-maschinenbau.example`
- ❌ `t.weber@mueller-maschinenbau.de`

## License

This demo dataset is provided under the same license as ISOVA (AGPL-3.0).
