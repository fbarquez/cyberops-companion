# Document & Policy Management

Complete document management system for ISMS (Information Security Management System) compliance, supporting policies, procedures, standards, and other compliance documentation with versioning, approval workflows, and acknowledgment tracking.

## Overview

The Document & Policy Management module provides:
- Document lifecycle management (Draft → Published → Archived)
- Version control with major/minor/patch numbering
- Sequential and parallel approval workflows
- User acknowledgment tracking with due dates
- Periodic review cycles (quarterly to biennial)
- Compliance mapping to frameworks (ISO 27001, NIS2, BSI)
- Full-text search and filtering
- Multi-language support (EN/DE)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Management Module                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │    Documents     │  │    Versions      │  │   Approvals  │  │
│  │  - CRUD          │  │  - History       │  │  - Chain     │  │
│  │  - Categories    │  │  - Comparison    │  │  - Workflow  │  │
│  │  - Status        │  │  - Rollback      │  │  - Comments  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                                 ▼                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    DocumentService                        │  │
│  │  - Workflow management (submit, approve, reject, publish) │  │
│  │  - Version management (create, compare)                   │  │
│  │  - ID generation (POL-001, PRO-002, etc.)                │  │
│  │  - Compliance tracking                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                 │                               │
│           ┌─────────────────────┼─────────────────────┐        │
│           │                     │                     │        │
│           ▼                     ▼                     ▼        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Acknowledgments  │  │    Reviews       │  │ Notifications│  │
│  │  - Assignments   │  │  - Scheduled     │  │  - Email     │  │
│  │  - Tracking      │  │  - Outcomes      │  │  - In-app    │  │
│  │  - Reminders     │  │  - Action items  │  │  - Reminders │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Document Lifecycle

```
                    ┌─────────────────┐
                    │      DRAFT      │
                    │  (Initial state)│
                    └────────┬────────┘
                             │ Submit for Review
                             ▼
                    ┌─────────────────┐
              ┌─────│ PENDING_REVIEW  │─────┐
              │     │ (Awaiting approval)   │
              │     └─────────────────┘     │
              │                             │
     Reject   │                             │ Approve (all)
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │      DRAFT      │           │    APPROVED     │
    │ (With feedback) │           │ (Ready to publish)
    └─────────────────┘           └────────┬────────┘
                                           │ Publish
                                           ▼
                                  ┌─────────────────┐
                            ┌─────│   PUBLISHED     │─────┐
                            │     │  (Active)       │     │
                            │     └─────────────────┘     │
                            │                             │
              Create new    │                             │ Archive
              version       ▼                             ▼
                    ┌─────────────────┐         ┌─────────────────┐
                    │ UNDER_REVISION  │         │    ARCHIVED     │
                    │ (New version)   │         │ (Retired)       │
                    └─────────────────┘         └─────────────────┘
```

## Database Models

### 1. Document

Main document entity with metadata, status, and compliance mapping.

```python
class DocumentCategory(str, enum.Enum):
    POLICY = "policy"              # High-level policies
    PROCEDURE = "procedure"        # Operational procedures
    STANDARD = "standard"          # Technical standards
    GUIDELINE = "guideline"        # Guidelines and recommendations
    FORM = "form"                  # Forms and templates
    RECORD = "record"              # Records
    MANUAL = "manual"              # Manuals
    INSTRUCTION = "instruction"    # Work instructions

class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    UNDER_REVISION = "under_revision"
    ARCHIVED = "archived"

class Document(TenantMixin, Base):
    __tablename__ = "documents"

    id: UUID (PK)
    tenant_id: FK → organizations.id

    # Identification
    document_id: str           # Auto-generated: "POL-001", "PRO-002"
    title: str
    description: Optional[str]
    category: DocumentCategory

    # Status & Version
    status: DocumentStatus = DRAFT
    current_version: str = "0.1"

    # Content
    content: Optional[Text]    # Markdown content
    attachment_id: Optional[FK → attachments.id]

    # Ownership
    owner_id: FK → users.id
    department: Optional[str]

    # Review Cycle
    review_frequency_days: Optional[int]  # 90, 180, 365, 730
    last_review_date: Optional[date]
    next_review_date: Optional[date]

    # Compliance Mapping
    frameworks: JSON           # ["iso27001", "nis2", "bsi"]
    control_references: JSON   # ["A.5.1", "A.5.2"]

    # Acknowledgment Settings
    requires_acknowledgment: bool = False
    acknowledgment_due_days: int = 14

    # Publishing
    published_at: Optional[datetime]
    published_by: Optional[FK → users.id]

    # Audit
    created_at, updated_at, created_by
```

### 2. DocumentVersion

Tracks all versions with content snapshots and change history.

```python
class VersionType(str, enum.Enum):
    MAJOR = "major"    # 1.0 → 2.0 (significant changes)
    MINOR = "minor"    # 1.0 → 1.1 (minor updates)
    PATCH = "patch"    # 1.0 → 1.0.1 (typos, formatting)

class DocumentVersion(TenantMixin, Base):
    __tablename__ = "document_versions"

    id: UUID (PK)
    tenant_id: FK → organizations.id
    document_id: FK → documents.id

    version_number: str        # "1.0", "1.1", "2.0"
    version_type: VersionType

    content: Optional[Text]    # Content snapshot
    attachment_id: Optional[FK]
    content_hash: str          # SHA-256 for integrity

    change_summary: str        # Brief description
    change_details: Optional[Text]

    is_current: bool = False
    is_published: bool = False

    created_at: datetime
    created_by: FK → users.id
    published_at: Optional[datetime]
```

### 3. DocumentApproval

Manages approval chain with sequential or parallel workflows.

```python
class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

class ApprovalType(str, enum.Enum):
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"      # All at once

class DocumentApproval(TenantMixin, Base):
    __tablename__ = "document_approvals"

    id: UUID (PK)
    tenant_id: FK → organizations.id
    document_id: FK → documents.id
    version_id: FK → document_versions.id

    approver_id: FK → users.id
    approval_order: int        # For sequential approvals
    approval_type: ApprovalType

    status: ApprovalStatus = PENDING
    decision_at: Optional[datetime]
    comments: Optional[Text]

    reminder_sent_at: Optional[datetime]
    reminder_count: int = 0
```

### 4. DocumentAcknowledgment

Tracks user confirmations with due dates and compliance reporting.

```python
class AcknowledgmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    DECLINED = "declined"
    EXPIRED = "expired"

class DocumentAcknowledgment(TenantMixin, Base):
    __tablename__ = "document_acknowledgments"

    id: UUID (PK)
    tenant_id: FK → organizations.id
    document_id: FK → documents.id
    version_id: FK → document_versions.id

    user_id: FK → users.id
    status: AcknowledgmentStatus = PENDING
    due_date: date

    acknowledged_at: Optional[datetime]
    ip_address: Optional[str]   # For audit
    user_agent: Optional[str]
    decline_reason: Optional[str]

    reminder_sent_at: Optional[datetime]
    reminder_count: int = 0
```

### 5. DocumentReview

Tracks periodic document reviews and outcomes.

```python
class ReviewOutcome(str, enum.Enum):
    NO_CHANGES = "no_changes"          # Still valid
    MINOR_UPDATE = "minor_update"      # Small changes needed
    MAJOR_REVISION = "major_revision"  # Significant rewrite
    RETIRE = "retire"                  # Should be archived

class DocumentReview(TenantMixin, Base):
    __tablename__ = "document_reviews"

    id: UUID (PK)
    tenant_id: FK → organizations.id
    document_id: FK → documents.id

    review_date: date
    reviewer_id: FK → users.id
    outcome: ReviewOutcome

    review_notes: Optional[Text]
    action_items: Optional[JSON]
    next_review_date: date
```

## API Endpoints (28 Total)

### Documents CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List documents with filters |
| POST | `/documents` | Create new document |
| GET | `/documents/{id}` | Get document details |
| PUT | `/documents/{id}` | Update document |
| DELETE | `/documents/{id}` | Soft delete document |

### Workflow Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/{id}/submit-review` | Submit for approval |
| POST | `/documents/{id}/approve` | Approve document |
| POST | `/documents/{id}/reject` | Reject with reason |
| POST | `/documents/{id}/request-changes` | Request changes |
| POST | `/documents/{id}/publish` | Publish document |
| POST | `/documents/{id}/archive` | Archive document |

### Versions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/versions` | List all versions |
| POST | `/documents/{id}/versions` | Create new version |
| GET | `/documents/{id}/versions/{v}` | Get specific version |
| GET | `/documents/{id}/versions/{v1}/compare/{v2}` | Compare versions |

### Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/approvals` | Get approval chain |
| POST | `/documents/{id}/approvals` | Set approvers |
| GET | `/approvals/pending` | My pending approvals |

### Acknowledgments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/acknowledgments` | List acknowledgments |
| POST | `/documents/{id}/acknowledgments` | Assign users |
| POST | `/documents/{id}/acknowledge` | User acknowledges |
| GET | `/acknowledgments/pending` | My pending acknowledgments |
| POST | `/acknowledgments/{id}/remind` | Send reminder |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/reviews` | Review history |
| POST | `/documents/{id}/reviews` | Record review |
| GET | `/documents/due-for-review` | Documents needing review |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/stats` | Dashboard statistics |
| GET | `/documents/compliance-report` | Acknowledgment compliance |

## API Request/Response Examples

### Create Document

```http
POST /api/v1/documents
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Information Security Policy",
  "description": "Main information security policy for the organization",
  "category": "policy",
  "department": "IT Security",
  "review_frequency_days": 365,
  "requires_acknowledgment": true,
  "acknowledgment_due_days": 14,
  "frameworks": ["iso27001", "nis2"],
  "control_references": ["A.5.1", "A.5.2"]
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "POL-001",
  "title": "Information Security Policy",
  "category": "policy",
  "status": "draft",
  "current_version": "0.1",
  "created_at": "2026-02-05T10:00:00Z"
}
```

### Submit for Review

```http
POST /api/v1/documents/{id}/submit-review
Content-Type: application/json

{
  "approver_ids": [
    "user-uuid-1",
    "user-uuid-2"
  ],
  "approval_type": "sequential"
}
```

### Approve Document

```http
POST /api/v1/documents/{id}/approve
Content-Type: application/json

{
  "comments": "Reviewed and approved. Good coverage of security controls."
}
```

### Acknowledge Document

```http
POST /api/v1/documents/{id}/acknowledge
```

**Response:**
```json
{
  "id": "ack-uuid",
  "document_id": "doc-uuid",
  "status": "acknowledged",
  "acknowledged_at": "2026-02-05T14:30:00Z"
}
```

### Get Dashboard Stats

```http
GET /api/v1/documents/stats
```

**Response:**
```json
{
  "total_documents": 45,
  "by_status": {
    "draft": 5,
    "pending_review": 3,
    "approved": 2,
    "published": 32,
    "archived": 3
  },
  "by_category": {
    "policy": 12,
    "procedure": 18,
    "standard": 8,
    "guideline": 5,
    "form": 2
  },
  "reviews_due": 4,
  "reviews_overdue": 1,
  "pending_acknowledgments": 156,
  "acknowledgment_compliance_rate": 85.5
}
```

## Backend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/api/src/models/documents.py` | SQLAlchemy models and enums |
| `apps/api/src/schemas/documents.py` | Pydantic schemas |
| `apps/api/src/services/document_service.py` | Business logic (~700 lines) |
| `apps/api/src/api/v1/documents.py` | API endpoints (28) |
| `apps/api/alembic/versions/h8i9j0k1l2m3_add_document_tables.py` | Migration |

### DocumentService

```python
from src.services.document_service import DocumentService

async def example_workflow(db: AsyncSession, user_id: str):
    service = DocumentService(db, tenant_id)

    # Create document
    doc = await service.create_document(
        DocumentCreate(
            title="Security Policy",
            category=DocumentCategory.POLICY,
            requires_acknowledgment=True
        ),
        user_id=user_id
    )

    # Add content
    await service.update(
        doc.id,
        DocumentUpdate(content="# Security Policy\n\n## Purpose...")
    )

    # Submit for review
    await service.submit_for_review(
        doc.id,
        approver_ids=["approver-1", "approver-2"],
        approval_type=ApprovalType.SEQUENTIAL
    )

    # Approve (as approver)
    await service.approve_document(
        doc.id,
        approver_id="approver-1",
        comments="Approved"
    )

    # Publish
    await service.publish_document(doc.id, user_id)

    # Assign acknowledgments
    await service.assign_acknowledgments(
        doc.id,
        user_ids=["user-1", "user-2", "user-3"],
        due_days=14
    )
```

### ID Generation

Documents receive auto-generated IDs based on category:

| Category | Prefix | Example |
|----------|--------|---------|
| Policy | POL | POL-001, POL-002 |
| Procedure | PRO | PRO-001, PRO-002 |
| Standard | STD | STD-001, STD-002 |
| Guideline | GDL | GDL-001, GDL-002 |
| Form | FRM | FRM-001, FRM-002 |
| Record | REC | REC-001, REC-002 |
| Manual | MAN | MAN-001, MAN-002 |
| Instruction | INS | INS-001, INS-002 |

## Frontend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/web/app/(dashboard)/documents/page.tsx` | Documents list page |
| `apps/web/app/(dashboard)/documents/[id]/page.tsx` | Document detail page |
| `apps/web/lib/api-client.ts` | API client (documentsAPI) |
| `apps/web/i18n/translations.ts` | Translations (EN/DE) |

### Documents List Page

Features:
- **Dashboard Stats**: Total documents, pending actions, reviews due, compliance rate
- **Tabs**: All Documents, Pending Review, My Approvals, My Acknowledgments
- **Filters**: Category, Status, Search
- **Create Dialog**: New document form with all fields
- **Document Cards**: Status badges, progress bars, quick actions

```
┌─────────────────────────────────────────────────────────────────┐
│  Documents & Policies                          [+ New Document] │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ Total: 45  │ │ Pending: 5 │ │ Review: 4  │ │ Ack: 85%   │   │
│  │ 32 published│ │ 2 approvals│ │ 1 overdue │ │ compliance  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  [All] [Pending Review] [My Approvals] [My Acknowledgments]     │
├─────────────────────────────────────────────────────────────────┤
│  Category ▾  Status ▾                       🔍 Search docs...   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📋 POL-001 │ Information Security Policy     │ v2.1    │   │
│  │ Policy     │ Published • ISO 27001           │ ✓ 85%   │   │
│  │ Owner: John Smith • Next review: Jan 2027    │ [View]  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Document Detail Page

Multi-tab interface with:

1. **Content Tab**: Markdown editor with live preview
2. **Versions Tab**: Version history with change summaries
3. **Approvals Tab**: Approval chain status
4. **Acknowledgments Tab**: User acknowledgment progress
5. **Reviews Tab**: Review history and outcomes

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back   POL-001: Information Security Policy   [Actions ▾]    │
│           v2.1 • Published • Last updated: Feb 5, 2026          │
├─────────────────────────────────────────────────────────────────┤
│  [Content] [Versions] [Approvals] [Acknowledgments] [Reviews]   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────┐ ┌──────────────────────┐  │
│  │                                 │ │ Metadata             │  │
│  │  # Information Security Policy  │ │ Category: Policy     │  │
│  │                                 │ │ Status: Published    │  │
│  │  ## 1. Purpose                  │ │ Owner: John Smith    │  │
│  │  This policy establishes...     │ │ Department: IT Sec   │  │
│  │                                 │ ├──────────────────────┤  │
│  │  ## 2. Scope                    │ │ Review Cycle         │  │
│  │  All employees and...           │ │ Frequency: Annual    │  │
│  │                                 │ │ Next: Jan 2027       │  │
│  │  ## 3. Responsibilities         │ ├──────────────────────┤  │
│  │  ...                            │ │ Compliance           │  │
│  │                                 │ │ ISO 27001: A.5.1     │  │
│  └─────────────────────────────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### API Client Usage

```typescript
import { documentsAPI } from "@/lib/api-client";

// List documents
const { items, total } = await documentsAPI.list({
  category: "policy",
  status: "published",
  search: "security"
});

// Create document
const doc = await documentsAPI.create({
  title: "New Policy",
  category: "policy",
  requires_acknowledgment: true
});

// Submit for review
await documentsAPI.submitForReview(docId, {
  approver_ids: ["user-1", "user-2"],
  approval_type: "sequential"
});

// Approve
await documentsAPI.approve(docId, {
  comments: "Looks good!"
});

// Publish
await documentsAPI.publish(docId);

// Acknowledge (as user)
await documentsAPI.acknowledge(docId);

// Get my pending items
const myApprovals = await documentsAPI.getMyPendingApprovals();
const myAcks = await documentsAPI.getMyPendingAcknowledgments();
```

## Notification Types

The module integrates with the notification system:

| Type | Trigger | Recipients |
|------|---------|------------|
| `DOCUMENT_SUBMITTED` | Document submitted for review | Approvers |
| `DOCUMENT_APPROVED` | Document approved | Owner |
| `DOCUMENT_REJECTED` | Document rejected | Owner |
| `DOCUMENT_PUBLISHED` | Document published | Users needing to acknowledge |
| `DOCUMENT_UPDATED` | New version published | Previous acknowledgers |
| `DOCUMENT_REVIEW_DUE` | Review date approaching | Owner |
| `DOCUMENT_REVIEW_OVERDUE` | Review date passed | Owner, Admins |
| `ACKNOWLEDGMENT_REQUIRED` | New acknowledgment assigned | User |
| `ACKNOWLEDGMENT_REMINDER` | Acknowledgment reminder | User |
| `ACKNOWLEDGMENT_OVERDUE` | Acknowledgment overdue | User, Admins |
| `APPROVAL_REQUIRED` | Approval needed | Approver |
| `APPROVAL_REMINDER` | Approval reminder | Approver |

## Compliance Frameworks

Documents can be mapped to multiple compliance frameworks:

| Framework | Controls |
|-----------|----------|
| ISO 27001:2022 | A.5.x - A.8.x (Annex A controls) |
| NIS2 | Article references |
| BSI IT-Grundschutz | Module references |
| SOC 2 | CC criteria |
| GDPR | Article references |

## Review Cycles

| Frequency | Days | Use Case |
|-----------|------|----------|
| Quarterly | 90 | High-change areas, operational procedures |
| Semi-Annual | 180 | Standard policies |
| Annual | 365 | Most policies and standards |
| Biennial | 730 | Stable, foundational documents |

## Database Migration

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    document_id VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    current_version VARCHAR(20) NOT NULL DEFAULT '0.1',
    content TEXT,
    attachment_id UUID REFERENCES attachments(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    department VARCHAR(100),
    review_frequency_days INTEGER,
    last_review_date DATE,
    next_review_date DATE,
    frameworks JSONB DEFAULT '[]',
    control_references JSONB DEFAULT '[]',
    requires_acknowledgment BOOLEAN DEFAULT false,
    acknowledgment_due_days INTEGER DEFAULT 14,
    published_at TIMESTAMP,
    published_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    UNIQUE(tenant_id, document_id)
);

-- Indexes
CREATE INDEX ix_documents_tenant ON documents(tenant_id);
CREATE INDEX ix_documents_status ON documents(status);
CREATE INDEX ix_documents_category ON documents(category);
CREATE INDEX ix_documents_owner ON documents(owner_id);
CREATE INDEX ix_documents_next_review ON documents(next_review_date);
```

## Security Considerations

1. **Multi-tenancy**: All documents are tenant-scoped
2. **Access Control**: Role-based permissions for CRUD and workflow actions
3. **Audit Trail**: All changes tracked with user ID and timestamp
4. **Content Integrity**: Version content hashed with SHA-256
5. **Acknowledgment Audit**: IP address and user agent captured

## Translations

The module includes full translations for:
- **English (en)**: Complete UI strings
- **German (de)**: Complete UI strings

Translation keys are in `apps/web/i18n/translations.ts` under the `documents` section.

## Future Enhancements

- [ ] PDF export/generation
- [ ] Document templates
- [ ] Bulk acknowledgment assignments by group/department
- [ ] Automated review reminders (Celery tasks)
- [ ] Document comparison/diff view
- [ ] Digital signatures for approvals
- [ ] External sharing with access codes
- [ ] Integration with document storage (SharePoint, Google Drive)
