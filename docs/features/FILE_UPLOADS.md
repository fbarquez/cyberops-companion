# File Uploads

File attachment system supporting upload, download, and management of files for security incidents, vulnerabilities, and other entities.

## Overview

The file upload system provides:
- Drag-and-drop file uploads
- Support for local filesystem and S3 storage backends
- SHA-256 file hash verification for integrity
- Category-based file organization
- Soft delete with optional permanent deletion
- File size and type validation
- Download tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
├─────────────────────────────────────────────────────────────────┤
│  FileUpload Component                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - Drag-and-drop zone (react-dropzone)                    │  │
│  │ - File category selection                                │  │
│  │ - Upload progress tracking                               │  │
│  │ - Attachment list display                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ useAttachments Hook                                      │  │
│  │ - Upload/download/delete operations                      │  │
│  │ - Progress state management                              │  │
│  │ - Error handling with toasts                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (multipart/form-data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend                                  │
├─────────────────────────────────────────────────────────────────┤
│  Attachments API Router                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ POST /upload/{entity_type}/{entity_id}                   │  │
│  │ GET /{entity_type}/{entity_id}                           │  │
│  │ GET /download/{attachment_id}                            │  │
│  │ DELETE /{attachment_id}                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ StorageService                                           │  │
│  │ - File validation (size, type)                           │  │
│  │ - SHA-256 hash calculation                               │  │
│  │ - Storage backend abstraction                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                   │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │ LocalStorage     │           │ S3Storage        │           │
│  │ (filesystem)     │           │ (AWS S3/MinIO)   │           │
│  └──────────────────┘           └──────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Upload File

```
POST /api/v1/attachments/upload/{entity_type}/{entity_id}
Content-Type: multipart/form-data
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| entity_type | string | incident, vulnerability, case, alert, risk, vendor, asset, evidence, report, general |
| entity_id | string | UUID of the entity |

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | The file to upload |
| category | string | No | evidence, screenshot, log_file, document, report, pcap, memory_dump, malware_sample, other |
| description | string | No | Optional file description |

**Response:** `201 Created`
```json
{
  "attachment": {
    "id": "uuid",
    "filename": "evidence.pcap",
    "content_type": "application/vnd.tcpdump.pcap",
    "file_size": 1048576,
    "file_size_human": "1.0 MB",
    "file_hash": "sha256...",
    "category": "pcap",
    "description": "Network capture from server",
    "entity_type": "incident",
    "entity_id": "uuid",
    "uploaded_by": "user_uuid",
    "uploaded_at": "2024-01-31T12:00:00Z",
    "download_count": 0
  },
  "message": "File uploaded successfully"
}
```

### List Attachments

```
GET /api/v1/attachments/{entity_type}/{entity_id}?category=evidence
```

**Response:** `200 OK`
```json
{
  "items": [...],
  "total": 5
}
```

### Download File

```
GET /api/v1/attachments/download/{attachment_id}
```

**Response:** File stream with headers:
- `Content-Disposition: attachment; filename="original_name.ext"`
- `Content-Type: application/octet-stream`
- `X-File-Hash: sha256...`

### Delete Attachment

```
DELETE /api/v1/attachments/{attachment_id}?permanent=false
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| permanent | boolean | false | If true, permanently deletes file and record |

### Verify Integrity

```
POST /api/v1/attachments/verify/{attachment_id}
```

**Response:** `200 OK`
```json
{
  "attachment_id": "uuid",
  "is_valid": true,
  "message": "File integrity verified",
  "verified_at": "2024-01-31T12:00:00Z"
}
```

## Backend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/api/src/models/attachment.py` | SQLAlchemy model and enums |
| `apps/api/src/schemas/attachment.py` | Pydantic schemas |
| `apps/api/src/services/storage_service.py` | Storage abstraction layer |
| `apps/api/src/api/v1/attachments.py` | API endpoints |
| `apps/api/src/config.py` | Storage configuration |

### Attachment Model

```python
class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String, primary_key=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    category = Column(Enum(AttachmentCategory))
    description = Column(Text)
    entity_type = Column(Enum(AttachmentEntityType))
    entity_id = Column(String)
    uploaded_by = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime)
    is_deleted = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
```

### StorageService

```python
from src.services.storage_service import StorageService

async def upload_file(db, file, entity_type, entity_id, user_id):
    service = StorageService(db)
    attachment = await service.upload(
        file=file,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        category=AttachmentCategory.EVIDENCE,
        description="Optional description"
    )
    return attachment
```

### Storage Backends

#### Local Storage
- Files stored in `STORAGE_LOCAL_PATH` directory
- Organized by: `{entity_type}/{entity_id}/{year}/{month}/{uuid}_{filename}`
- Directory traversal protection

#### S3 Storage
- Supports AWS S3 and S3-compatible services (MinIO, DigitalOcean Spaces)
- Requires `boto3` package

## Frontend Implementation

### Files

| File | Description |
|------|-------------|
| `apps/web/hooks/use-attachments.ts` | Attachment management hook |
| `apps/web/components/shared/file-upload.tsx` | File upload component |
| `apps/web/lib/api-client.ts` | API client (attachmentsAPI) |

### useAttachments Hook

```typescript
import { useAttachments } from "@/hooks/use-attachments";

function EvidencePage({ incidentId }) {
  const {
    attachments,
    isLoading,
    isUploading,
    uploadQueue,
    fetchAttachments,
    uploadFile,
    downloadFile,
    deleteAttachment,
    verifyIntegrity,
  } = useAttachments({
    entityType: "incident",
    entityId: incidentId,
    onUploadComplete: (attachment) => {
      console.log("Uploaded:", attachment.filename);
    },
  });

  // Upload a file
  await uploadFile(file, "evidence", "Network capture");

  // Download
  await downloadFile(attachmentId);

  // Verify integrity
  const result = await verifyIntegrity(attachmentId);
}
```

### FileUpload Component

```typescript
import { FileUpload } from "@/components/shared";

<FileUpload
  entityType="incident"
  entityId={incidentId}
  showList={true}           // Show attachment list
  compact={false}           // Full or compact mode
  maxFiles={10}             // Max files per upload
  maxSizeMB={50}            // Max file size
  onUploadComplete={(attachment) => {
    // Handle upload complete
  }}
/>
```

### Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| entityType | string | required | Entity type for attachments |
| entityId | string | required | Entity ID |
| onUploadComplete | function | - | Callback after upload |
| onDeleteComplete | function | - | Callback after delete |
| maxFiles | number | 10 | Max files per upload |
| maxSizeMB | number | 50 | Max file size in MB |
| acceptedTypes | string[] | - | MIME types to accept |
| showList | boolean | true | Show attachment list |
| compact | boolean | false | Compact display mode |

## Configuration

### Environment Variables

```env
# Storage Backend
STORAGE_BACKEND=local              # "local" or "s3"
STORAGE_LOCAL_PATH=uploads         # Local storage directory
STORAGE_MAX_FILE_SIZE_MB=50        # Maximum file size

# Allowed Extensions
STORAGE_ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,ppt,pptx,txt,csv,json,xml,jpg,jpeg,png,gif,bmp,svg,webp,zip,tar,gz,7z,rar,pcap,pcapng,log,evtx,dmp,mem

# S3 Storage (when STORAGE_BACKEND=s3)
S3_BUCKET_NAME=cyberops-attachments
S3_REGION=us-east-1
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=secret
S3_ENDPOINT_URL=                   # For S3-compatible services
```

### File Categories

| Category | Use Case |
|----------|----------|
| evidence | General evidence files |
| screenshot | Screen captures |
| log_file | System/application logs |
| document | Reports, policies |
| report | Generated reports |
| pcap | Network captures |
| memory_dump | Memory forensics |
| malware_sample | Suspicious files |
| other | Uncategorized |

### Allowed Extensions

Default allowed extensions grouped by type:

- **Documents:** pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv, json, xml
- **Images:** jpg, jpeg, png, gif, bmp, svg, webp
- **Archives:** zip, tar, gz, 7z, rar
- **Security/Forensics:** pcap, pcapng, log, evtx, dmp, mem

## Security

### File Validation

1. **Size limit:** Configurable max size (default 50MB)
2. **Extension whitelist:** Only allowed extensions accepted
3. **MIME type detection:** Content-Type verified
4. **Filename sanitization:** Path traversal prevention
5. **Duplicate detection:** Same hash for same entity rejected

### Integrity Verification

- SHA-256 hash calculated on upload
- Hash stored in database
- Verify endpoint compares stored vs actual hash
- Detects file corruption or tampering

### Access Control

- All endpoints require authentication
- User ID tracked for uploads/deletes
- Download count tracking
- Soft delete with audit trail

## Database Migration

```sql
CREATE TABLE attachments (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    category VARCHAR(20) NOT NULL,
    description TEXT,
    entity_type VARCHAR(20) NOT NULL,
    entity_id VARCHAR NOT NULL,
    uploaded_by VARCHAR NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR REFERENCES users(id),
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP
);

CREATE INDEX ix_attachments_entity ON attachments(entity_type, entity_id);
CREATE INDEX ix_attachments_uploaded_by ON attachments(uploaded_by);
CREATE INDEX ix_attachments_category ON attachments(category);
CREATE INDEX ix_attachments_file_hash ON attachments(file_hash);
```

## Troubleshooting

### Upload Fails

1. **413 Entity Too Large:** File exceeds size limit
2. **400 Bad Request:** Invalid file extension
3. **409 Conflict:** Duplicate file (same hash for entity)

### Download Fails

1. **404 Not Found:** Attachment record deleted or file missing from storage
2. **Check storage backend:** Verify file exists at storage_path

### Integrity Check Fails

1. **Hash mismatch:** File was modified after upload
2. **Storage corruption:** Check storage backend health

## Future Enhancements

- [ ] Virus/malware scanning integration
- [ ] Image thumbnails generation
- [ ] File preview for common types
- [ ] Batch upload with ZIP extraction
- [ ] Expiring download links
- [ ] Encryption at rest
