# Evidence Model

> Documentation for ISOVA's evidence management system

## Overview

ISOVA uses a structured evidence model to capture, version, and verify compliance documentation. Each evidence record includes cryptographic integrity verification and full audit trail.

## Data Model

### Evidence Entity

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `organization_id` | UUID | Owning organization |
| `title` | String | Human-readable title |
| `description` | Text | Detailed description |
| `evidence_type` | Enum | `attestation`, `document`, `auto` |
| `status` | Enum | `draft`, `confirmed`, `expired`, `superseded` |
| `content_hash` | String | SHA-256 of content |
| `valid_from` | DateTime | Start of validity |
| `valid_until` | DateTime | End of validity (nullable) |
| `confirmed_by` | UUID | User who confirmed |
| `confirmed_at` | DateTime | Confirmation timestamp |
| `version` | Integer | Version number |
| `previous_version_id` | UUID | Link to prior version |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification |

### Evidence Types

#### 1. Attestation

Internal confirmation by a responsible person.

```json
{
  "evidence_type": "attestation",
  "attestation_data": {
    "statement": "Security awareness training completed",
    "basis": "observation",
    "basis_options": ["observation", "document", "sample", "system_log"],
    "confirmed_by_name": "Thomas Weber",
    "confirmed_by_role": "IT-Leiter"
  }
}
```

**Basis Options:**

| Basis | German | When to Use |
|-------|--------|-------------|
| `observation` | Beobachtung | You personally witnessed/verified |
| `document` | Dokument | Written proof exists (certificate, list) |
| `sample` | Stichprobe | Spot-check performed |
| `system_log` | Systemmeldung | Automated log/report available |

#### 2. Document

Uploaded file with metadata.

```json
{
  "evidence_type": "document",
  "document_data": {
    "filename": "training_attendance.pdf",
    "mime_type": "application/pdf",
    "file_size": 245789,
    "storage_path": "evidence/2024/02/abc123.pdf",
    "file_hash": "sha256:8d969eef..."
  }
}
```

#### 3. Auto-Evidence

System-generated evidence from integrations.

```json
{
  "evidence_type": "auto",
  "auto_data": {
    "source": "azure_ad",
    "collection_method": "api",
    "raw_data": { "mfa_enabled_users": 156, "total_users": 180 },
    "collected_at": "2024-02-07T10:30:00Z"
  }
}
```

## Lifecycle

```
┌─────────┐      confirm()      ┌───────────┐
│  DRAFT  │ ─────────────────▶  │ CONFIRMED │
└─────────┘                     └───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              ┌─────────┐      ┌───────────┐     ┌────────────┐
              │ EXPIRED │      │ SUPERSEDED│     │  ARCHIVED  │
              └─────────┘      └───────────┘     └────────────┘
              (auto/manual)    (new version)     (manual)
```

### State Transitions

| From | To | Trigger | Reversible |
|------|----|---------|------------|
| `draft` | `confirmed` | User confirmation with name/role | No |
| `confirmed` | `expired` | `valid_until` date passed | No |
| `confirmed` | `superseded` | New version created | No |
| `confirmed` | `archived` | Manual archive action | Yes |

### Versioning Rules

1. Confirmed evidence is immutable
2. Modifications create new version with `previous_version_id` link
3. Original remains with status `superseded`
4. Version chain is fully traversable

## Integrity Verification

### Hash Calculation

Evidence integrity is verified using SHA-256 hashing of the canonical content representation:

```python
import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

def calculate_evidence_hash(evidence: dict) -> str:
    """Calculate SHA-256 hash of evidence content.

    Args:
        evidence: Dictionary of evidence fields to hash

    Returns:
        Hexadecimal hash string (64 characters)
    """
    # Canonical fields for hashing (order matters)
    hashable_content = {
        "title": evidence["title"],
        "description": evidence["description"],
        "evidence_type": evidence["evidence_type"],
        "attestation_data": evidence.get("attestation_data"),
        "document_hash": evidence.get("document_data", {}).get("file_hash"),
        "auto_data": evidence.get("auto_data"),
        "confirmed_by": str(evidence.get("confirmed_by")) if evidence.get("confirmed_by") else None,
        "confirmed_at": evidence.get("confirmed_at").isoformat() if isinstance(evidence.get("confirmed_at"), datetime) else evidence.get("confirmed_at"),
    }

    # Sort keys for deterministic output
    canonical = json.dumps(hashable_content, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_evidence_integrity(evidence: dict) -> tuple[bool, str]:
    """Verify that evidence has not been tampered with.

    Args:
        evidence: Evidence record with stored content_hash

    Returns:
        Tuple of (is_valid, calculated_hash)
    """
    stored_hash = evidence.get("content_hash")
    calculated_hash = calculate_evidence_hash(evidence)

    return (stored_hash == calculated_hash, calculated_hash)
```

### Verification Endpoint

```http
GET /api/v1/evidence/{id}/verify

Response 200:
{
  "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
  "stored_hash": "7a3f8c9d2e1b4a5f6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
  "calculated_hash": "7a3f8c9d2e1b4a5f6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
  "integrity_valid": true,
  "verified_at": "2024-02-07T14:30:00Z"
}

Response 200 (integrity failed):
{
  "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
  "stored_hash": "7a3f8c9d...",
  "calculated_hash": "different...",
  "integrity_valid": false,
  "verified_at": "2024-02-07T14:30:00Z",
  "warning": "Evidence content may have been modified outside normal procedures"
}
```

## Traceability

### Control Linkage

Each evidence can be linked to multiple controls across frameworks:

```json
{
  "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
  "linked_controls": [
    {
      "framework": "iso27001",
      "control_id": "A.6.3",
      "control_name": "Information security awareness, education and training"
    },
    {
      "framework": "nis2",
      "control_id": "M07",
      "control_name": "Cyberhygiene und Schulungen"
    },
    {
      "framework": "bsi",
      "control_id": "ORP.3",
      "control_name": "Sensibilisierung und Schulung"
    }
  ]
}
```

### Audit Log

All evidence operations are logged immutably:

```json
{
  "log_id": "log-2024-001",
  "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "confirm",
  "actor_id": "user-123",
  "actor_name": "Thomas Weber",
  "actor_role": "IT-Leiter",
  "timestamp": "2024-02-07T14:00:00Z",
  "changes": {
    "status": { "old": "draft", "new": "confirmed" },
    "confirmed_by": { "old": null, "new": "user-123" },
    "confirmed_at": { "old": null, "new": "2024-02-07T14:00:00Z" }
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

**Logged Actions:**

| Action | Description |
|--------|-------------|
| `create` | New evidence created |
| `update` | Draft evidence modified |
| `confirm` | Evidence confirmed |
| `supersede` | New version created |
| `archive` | Evidence archived |
| `restore` | Evidence restored from archive |
| `link_control` | Control association added |
| `unlink_control` | Control association removed |
| `verify` | Integrity verification performed |

## API Reference

### Create Evidence

```http
POST /api/v1/evidence
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Backup-Nachweis Februar 2024",
  "description": "Monatliche Backup-Bestätigung für Kernsysteme",
  "evidence_type": "attestation",
  "attestation_data": {
    "statement": "Backup erfolgreich durchgeführt und Restore-Test bestanden",
    "basis": "system_log"
  },
  "valid_until": "2024-03-07T00:00:00Z",
  "control_ids": ["nis2:M03", "iso27001:A.8.13"]
}

Response 201:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "content_hash": null,
  "created_at": "2024-02-07T10:00:00Z"
}
```

### List Evidence

```http
GET /api/v1/evidence?status=confirmed&framework=nis2&control=M03&page=1&limit=20

Response 200:
{
  "items": [...],
  "total": 45,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

### Confirm Evidence

```http
POST /api/v1/evidence/{id}/confirm
Content-Type: application/json

{
  "confirmed_by_name": "Thomas Weber",
  "confirmed_by_role": "IT-Leiter"
}

Response 200:
{
  "id": "550e8400-...",
  "status": "confirmed",
  "confirmed_at": "2024-02-07T14:00:00Z",
  "content_hash": "7a3f8c9d..."
}
```

### Create New Version

```http
POST /api/v1/evidence/{id}/new-version
Content-Type: application/json

{
  "title": "Backup-Nachweis März 2024",
  "description": "Updated monthly backup verification",
  "attestation_data": {
    "statement": "Backup and restore test completed successfully",
    "basis": "system_log"
  }
}

Response 201:
{
  "id": "new-version-id",
  "version": 2,
  "previous_version_id": "550e8400-...",
  "status": "draft"
}
```

## Database Schema

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    evidence_type VARCHAR(20) NOT NULL CHECK (evidence_type IN ('attestation', 'document', 'auto')),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'expired', 'superseded', 'archived')),
    attestation_data JSONB,
    document_data JSONB,
    auto_data JSONB,
    content_hash VARCHAR(64),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    confirmed_by UUID REFERENCES users(id),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    version INTEGER NOT NULL DEFAULT 1,
    previous_version_id UUID REFERENCES evidence(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_attestation CHECK (
        evidence_type != 'attestation' OR attestation_data IS NOT NULL
    ),
    CONSTRAINT valid_document CHECK (
        evidence_type != 'document' OR document_data IS NOT NULL
    ),
    CONSTRAINT confirmed_has_hash CHECK (
        status != 'confirmed' OR content_hash IS NOT NULL
    )
);

CREATE INDEX idx_evidence_org ON evidence(organization_id);
CREATE INDEX idx_evidence_status ON evidence(status);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_valid_until ON evidence(valid_until) WHERE valid_until IS NOT NULL;
```

## Best Practices

1. **Use attestations for quick documentation** - No file upload required, captures the essentials
2. **Always specify basis** - Makes evidence more credible for auditors
3. **Set validity periods** - System reminds you when review is due
4. **Link to controls** - Creates traceability for audits and SoA generation
5. **Version, don't delete** - Preserve complete audit history
6. **Verify before audits** - Use integrity check endpoint to confirm no tampering

## Disclaimer

Evidence created in ISOVA is internal documentation. Attestations are confirmations made in good faith and do not constitute formal audit evidence in the sense of certification. For formal certification audits, additional documentation may be required.
