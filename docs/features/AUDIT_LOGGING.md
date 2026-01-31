# Audit Logging

Complete audit trail system for compliance, forensics, and security monitoring.

---

## Overview

The Audit Logging system tracks all user actions across the platform, providing:
- Complete audit trail for compliance requirements
- Forensic investigation support
- Security monitoring and anomaly detection
- User activity analytics

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  /audit page                                            │ │
│  │  - Stats cards (total, today, critical, failures)       │ │
│  │  - Filters (action, resource, severity, search)         │ │
│  │  - Logs table with pagination                           │ │
│  │  - Detail dialog with old/new values                    │ │
│  │  - Export (CSV/JSON)                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  /api/v1/audit/*                                        │ │
│  │  - GET /logs - List with filters & pagination           │ │
│  │  - GET /logs/{id} - Detail with old/new values          │ │
│  │  - GET /stats - Statistics (admin only)                 │ │
│  │  - POST /export - Export CSV/JSON (admin only)          │ │
│  │  - GET /actions - Available filter options              │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  AuditService                                           │ │
│  │  - log_action() - Create log entry                      │ │
│  │  - list_logs() - Query with filters                     │ │
│  │  - get_stats() - Aggregate statistics                   │ │
│  │  - export_logs() - Generate CSV/JSON                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  activity_logs table                                    │ │
│  │  - Indexed: user_id, action, resource_type, created_at  │ │
│  │  - JSON fields: old_values, new_values                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Model

### ActivityLog Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | String (UUID) | Primary key |
| `user_id` | String (FK) | User who performed action (indexed) |
| `action` | String(50) | Action type (indexed) |
| `action_category` | String(50) | Category (auth, crud, data, system) |
| `resource_type` | String(50) | Resource type (indexed) |
| `resource_id` | String | Resource identifier |
| `resource_name` | String | Human-readable resource name |
| `description` | Text | Action description |
| `old_values` | JSON | Previous values (for updates) |
| `new_values` | JSON | New values (for creates/updates) |
| `changes_summary` | Text | Human-readable changes |
| `ip_address` | String(45) | Client IP (IPv6 compatible) |
| `user_agent` | String(500) | Client user agent |
| `request_id` | String | Request correlation ID |
| `success` | Boolean | Whether action succeeded |
| `error_message` | Text | Error message if failed |
| `severity` | String(20) | info, warning, critical |
| `created_at` | DateTime | Timestamp (indexed) |

---

## Actions Tracked

### Authentication (Category: `auth`)

| Action | Severity | Description |
|--------|----------|-------------|
| `login` | info | Successful login |
| `logout` | info | User logout |
| `login_failed` | warning | Failed login attempt |
| `password_change` | warning | Password changed |

### CRUD Operations (Category: `crud`)

| Action | Severity | Description |
|--------|----------|-------------|
| `create` | info | Resource created |
| `read` | info | Resource accessed |
| `update` | info | Resource modified |
| `delete` | warning | Resource deleted |
| `assign` | info | Resource assigned |
| `escalate` | info | Resource escalated |
| `status_change` | info | Status changed |

### Data Operations (Category: `data`)

| Action | Severity | Description |
|--------|----------|-------------|
| `export` | info | Data exported |
| `import` | warning | Data imported |
| `bulk_delete` | critical | Bulk deletion |

### System Operations (Category: `system`)

| Action | Severity | Description |
|--------|----------|-------------|
| `config_change` | critical | Configuration modified |
| `role_change` | warning | User role changed |

---

## Resource Types

| Resource Type | Description |
|---------------|-------------|
| `incident` | Security incidents |
| `alert` | SOC alerts |
| `case` | Investigation cases |
| `user` | User accounts |
| `team` | Teams |
| `role` | Roles and permissions |
| `vulnerability` | Vulnerabilities |
| `risk` | Risk entries |
| `asset` | CMDB assets |
| `report` | Generated reports |
| `playbook` | Playbooks |
| `ioc` | Indicators of Compromise |
| `setting` | System settings |
| `api_key` | API keys |
| `session` | User sessions |

---

## API Reference

### List Audit Logs

```http
GET /api/v1/audit/logs
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Filter by user ID |
| `action` | string | Filter by action type |
| `action_category` | string | Filter by category |
| `resource_type` | string | Filter by resource type |
| `resource_id` | string | Filter by resource ID |
| `start_date` | datetime | Filter after date |
| `end_date` | datetime | Filter before date |
| `success` | boolean | Filter by success status |
| `severity` | string | Filter by severity |
| `search` | string | Search in description/name |
| `page` | integer | Page number (default: 1) |
| `size` | integer | Page size (default: 50, max: 100) |

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "action": "create",
      "action_category": "crud",
      "resource_type": "incident",
      "resource_id": "uuid",
      "resource_name": "Ransomware Attack",
      "description": "John Doe created incident: Ransomware Attack",
      "changes_summary": null,
      "ip_address": "192.168.1.100",
      "success": true,
      "severity": "info",
      "created_at": "2026-01-31T10:30:00Z"
    }
  ],
  "total": 1234,
  "page": 1,
  "size": 50,
  "pages": 25
}
```

### Get Log Detail

```http
GET /api/v1/audit/logs/{log_id}
```

**Response:** Same as list item but includes `old_values` and `new_values` JSON fields.

### Get Statistics (Admin Only)

```http
GET /api/v1/audit/stats
```

**Response:**

```json
{
  "total_logs": 12456,
  "logs_today": 89,
  "logs_this_week": 523,
  "critical_actions": 23,
  "failed_actions": 5,
  "active_users_today": 12,
  "actions_by_type": {
    "create": 234,
    "update": 456,
    "delete": 12,
    "login": 89
  },
  "actions_by_resource": {
    "incident": 345,
    "alert": 234,
    "user": 56
  },
  "actions_by_severity": {
    "info": 1100,
    "warning": 45,
    "critical": 5
  },
  "top_users": [
    {"user_id": "uuid", "name": "John", "email": "john@example.com", "action_count": 45}
  ],
  "recent_critical": [...]
}
```

### Export Logs (Admin Only)

```http
POST /api/v1/audit/export
```

**Request Body:**

```json
{
  "format": "csv",
  "user_id": null,
  "action": null,
  "resource_type": "incident",
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-01-31T23:59:59Z",
  "severity": null
}
```

**Response:** File download (CSV or JSON)

### Get Filter Options

```http
GET /api/v1/audit/actions
```

**Response:**

```json
{
  "actions": [
    {"value": "login", "label": "Login", "category": "auth"},
    {"value": "create", "label": "Create", "category": "crud"}
  ],
  "categories": [
    {"value": "auth", "label": "Authentication"},
    {"value": "crud", "label": "CRUD Operations"}
  ],
  "resource_types": [
    {"value": "incident", "label": "Incident"},
    {"value": "alert", "label": "Alert"}
  ],
  "severities": [
    {"value": "info", "label": "Info"},
    {"value": "warning", "label": "Warning"},
    {"value": "critical", "label": "Critical"}
  ]
}
```

---

## Frontend Usage

### Accessing the Audit Page

Navigate to `/audit` in the sidebar. The page shows:

1. **Stats Cards** (Admin/Manager only)
   - Total Logs
   - Logs Today
   - Critical Actions
   - Failed Actions

2. **Filters**
   - Search box
   - Action type dropdown
   - Resource type dropdown
   - Severity dropdown

3. **Logs Table**
   - Timestamp
   - User
   - Action
   - Resource
   - Description
   - Status (success/failure)
   - Severity badge

4. **Log Detail Dialog**
   - Click any row to view full details
   - Shows old/new values for updates
   - IP address and user agent

5. **Export** (Admin only)
   - Export as CSV
   - Export as JSON

### API Client Usage

```typescript
import { auditAPI } from "@/lib/api-client";

// List logs with filters
const logs = await auditAPI.list(token, {
  action: "create",
  resource_type: "incident",
  page: 1,
  size: 25,
});

// Get log detail
const detail = await auditAPI.get(token, logId);

// Get statistics (admin only)
const stats = await auditAPI.getStats(token);

// Export logs (admin only)
const { blob, filename } = await auditAPI.export(token, {
  format: "csv",
  start_date: "2026-01-01",
});

// Get filter options
const actions = await auditAPI.getActions(token);
```

---

## Backend Usage

### Logging Actions in Endpoints

```python
from src.services.audit_service import AuditService

@router.post("")
async def create_incident(
    data: IncidentCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    service = IncidentService(db)
    incident = await service.create(data, current_user.id)

    # Log the action
    audit_service = AuditService(db)
    await audit_service.log_action(
        user_id=current_user.id,
        action="create",
        resource_type="incident",
        resource_id=incident.id,
        resource_name=incident.title,
        description=f"{current_user.full_name} created incident: {incident.title}",
        new_values={
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status.value,
        },
    )

    return incident
```

### Logging Updates with Old/New Values

```python
@router.patch("/{incident_id}")
async def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    service = IncidentService(db)

    # Get old values first
    old_incident = await service.get_by_id(incident_id)
    old_values = {
        "title": old_incident.title,
        "severity": old_incident.severity.value,
        "status": old_incident.status.value,
    }

    # Perform update
    incident = await service.update(incident_id, data)

    # Log with old and new values
    audit_service = AuditService(db)
    new_values = data.model_dump(exclude_unset=True)

    await audit_service.log_action(
        user_id=current_user.id,
        action="update",
        resource_type="incident",
        resource_id=incident_id,
        resource_name=incident.title,
        old_values=old_values,
        new_values=new_values,
    )

    return incident
```

---

## Security Features

### Sensitive Data Filtering

The AuditService automatically filters sensitive fields from logged values:

```python
SENSITIVE_FIELDS = {
    "password", "password_hash", "hashed_password",
    "token", "access_token", "refresh_token", "api_key",
    "secret", "key_hash", "token_hash",
    "credit_card", "ssn", "social_security",
}
```

These fields are replaced with `[REDACTED]` in the logs.

### Auto-Generated Severity

If severity is not specified, it's automatically determined:

| Action | Default Severity |
|--------|------------------|
| `login_failed` | warning |
| `password_change` | warning |
| `delete` | warning |
| `role_change` | warning |
| `config_change` | critical |
| `bulk_delete` | critical |
| All failures | warning (minimum) |
| Everything else | info |

### Auto-Generated Changes Summary

For updates with old/new values, a human-readable summary is generated:

```
Changed status from 'open' to 'closed'; Changed severity from 'low' to 'high'
```

---

## Access Control

| Endpoint | Required Role |
|----------|---------------|
| `GET /logs` | Any authenticated (users see only own logs) |
| `GET /logs/{id}` | Any authenticated (users see only own logs) |
| `GET /stats` | Admin or Manager |
| `POST /export` | Admin |
| `GET /actions` | Any authenticated |

---

## Translations

Translations are available in English and German under the `audit` namespace:

```typescript
t("audit.title")           // "Audit Logs" / "Audit-Protokolle"
t("audit.subtitle")        // "System activity and security audit trail"
t("audit.totalLogs")       // "Total Logs"
t("audit.logsToday")       // "Logs Today"
t("audit.criticalActions") // "Critical Actions"
t("audit.export")          // "Export"
t("audit.noLogs")          // "No audit logs found"
```

---

## Files Created/Modified

### Backend

| File | Description |
|------|-------------|
| `src/models/user_management.py` | Enhanced ActivityLog model |
| `src/schemas/audit.py` | Pydantic schemas |
| `src/services/audit_service.py` | AuditService class |
| `src/api/v1/audit.py` | API endpoints |
| `src/api/v1/router.py` | Added audit router |
| `src/utils/audit_decorator.py` | Logging decorator |
| `src/api/v1/auth.py` | Login/logout logging |
| `src/api/v1/incidents.py` | CRUD logging |

### Frontend

| File | Description |
|------|-------------|
| `app/(dashboard)/audit/page.tsx` | Audit page |
| `lib/api-client.ts` | Added auditAPI |
| `components/shared/sidebar.tsx` | Added audit link |
| `i18n/translations.ts` | EN/DE translations |

---

## Best Practices

1. **Log all CRUD operations** on sensitive resources
2. **Include resource_name** for human-readable logs without joins
3. **Capture old_values** before updates for change tracking
4. **Use appropriate severity** for compliance alerting
5. **Don't log read operations** on non-sensitive resources (too noisy)
6. **Never log sensitive data** - the service filters it, but be careful with custom new_values

---

## Compliance Notes

This audit system supports:

- **SOC 2** - User activity monitoring
- **GDPR** - Data access tracking
- **HIPAA** - Access audit trails
- **PCI-DSS** - Security event logging
- **ISO 27001** - Information security monitoring

Logs are append-only and should not be modified or deleted in production.
