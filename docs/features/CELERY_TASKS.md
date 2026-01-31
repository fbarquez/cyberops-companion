# Celery Background Tasks

**Status:** ✅ Implemented
**Date:** 2026-01-31
**Location:** `apps/api/src/celery_app.py`, `apps/api/src/tasks/`

---

## Overview

Celery integration for executing background tasks such as vulnerability scans, NVD synchronization, and async notifications. Uses Redis as the message broker and result backend.

---

## Features

- Async vulnerability scan execution
- NVD CVE synchronization
- Async notification delivery
- Task progress tracking
- Automatic retries with backoff
- Task queues for prioritization
- Scheduled tasks (Celery Beat)

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│     API     │     │   Broker    │     │   Worker    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Celery    │
                    │    Beat     │
                    └─────────────┘
```

---

## Configuration

```env
# .env file
REDIS_URL=redis://redis:6379/0
```

---

## Task Queues

| Queue | Purpose |
|-------|---------|
| `default` | General tasks |
| `scans` | Vulnerability scan execution |
| `notifications` | Notification delivery |

---

## Available Tasks

### Scan Tasks (`src.tasks.scan_tasks`)

#### `execute_vulnerability_scan`
Execute a vulnerability scan in the background.

```python
from src.tasks.scan_tasks import execute_vulnerability_scan

# Trigger scan execution
task = execute_vulnerability_scan.delay(scan_id)

# Check task status
result = task.get(timeout=300)  # Wait up to 5 minutes
```

#### `sync_nvd_updates`
Synchronize recent CVE updates from NVD.

```python
from src.tasks.scan_tasks import sync_nvd_updates

# Sync last 7 days of CVE updates
task = sync_nvd_updates.delay(days_back=7)
```

#### `cancel_scan`
Cancel a running or pending scan.

```python
from src.tasks.scan_tasks import cancel_scan

result = cancel_scan(scan_id)
```

### Notification Tasks (`src.tasks.notification_tasks`)

#### `send_notification_async`
Send a notification asynchronously.

```python
from src.tasks.notification_tasks import send_notification_async

task = send_notification_async.delay(
    user_id="user-uuid",
    notification_type="vulnerability",
    title="New Critical Vulnerability",
    message="A critical vulnerability was detected",
    priority="critical",
    entity_type="scan",
    entity_id="scan-uuid"
)
```

#### `send_scan_completion_notification`
Send notification when scan completes.

```python
from src.tasks.notification_tasks import send_scan_completion_notification

task = send_scan_completion_notification.delay(
    scan_id="scan-uuid",
    user_id="user-uuid",
    scan_name="Weekly Network Scan",
    total_findings=15,
    critical_count=2,
    high_count=5
)
```

#### `cleanup_old_notifications`
Clean up old notifications (for scheduled execution).

```python
from src.tasks.notification_tasks import cleanup_old_notifications

task = cleanup_old_notifications.delay(days_old=30)
```

---

## API Endpoints

### Start Scan
```
POST /api/v1/vulnerabilities/scans/{scan_id}/start
Authorization: Bearer <token>

Response:
{
  "id": "scan-uuid",
  "name": "Weekly Scan",
  "status": "running",
  "celery_task_id": "abc123..."
}
```

### Get Scan Task Status
```
GET /api/v1/vulnerabilities/scans/{scan_id}/status
Authorization: Bearer <token>

Response:
{
  "scan_id": "scan-uuid",
  "scan_status": "running",
  "task_id": "abc123...",
  "task_state": "PROGRESS",
  "task_info": {"status": "executing"}
}
```

### Cancel Scan
```
POST /api/v1/vulnerabilities/scans/{scan_id}/cancel
Authorization: Bearer <token>

Response:
{
  "scan_id": "scan-uuid",
  "status": "cancelled"
}
```

---

## Docker Compose Services

```yaml
# Celery Worker
celery-worker:
  command: celery -A src.celery_app worker --loglevel=info --concurrency=2 -Q default,scans,notifications

# Celery Beat (scheduler)
celery-beat:
  command: celery -A src.celery_app beat --loglevel=info
```

---

## Running Locally

### Start Worker
```bash
cd apps/api
celery -A src.celery_app worker --loglevel=info
```

### Start Beat Scheduler
```bash
cd apps/api
celery -A src.celery_app beat --loglevel=info
```

### Monitor Tasks (Flower)
```bash
pip install flower
celery -A src.celery_app flower --port=5555
```

---

## Task States

| State | Description |
|-------|-------------|
| PENDING | Task waiting in queue |
| STARTED | Task started executing |
| PROGRESS | Task in progress (custom) |
| SUCCESS | Task completed successfully |
| FAILURE | Task failed |
| RETRY | Task retrying after failure |
| REVOKED | Task was cancelled |

---

## Scheduled Tasks

Configured in `celery_app.py` via `beat_schedule`:

```python
beat_schedule={
    "sync-nvd-updates": {
        "task": "src.tasks.scan_tasks.sync_nvd_updates",
        "schedule": 21600.0,  # Every 6 hours
    },
    "cleanup-notifications": {
        "task": "src.tasks.notification_tasks.cleanup_old_notifications",
        "schedule": 86400.0,  # Daily
    },
}
```

---

## Files

| File | Purpose |
|------|---------|
| `celery_app.py` | Celery configuration |
| `tasks/__init__.py` | Task exports |
| `tasks/scan_tasks.py` | Vulnerability scan tasks |
| `tasks/notification_tasks.py` | Notification tasks |
| `docker-compose.yml` | Worker/beat services |

---

## Dependencies

```
celery[redis]>=5.3.0
```

---

## Extending

### Adding New Tasks

1. Create task file in `tasks/`:
```python
from src.celery_app import celery_app

@celery_app.task(name="src.tasks.my_tasks.my_task")
def my_task(arg1, arg2):
    # Task logic
    return {"status": "done"}
```

2. Add to `celery_app.py` include list:
```python
include=[
    "src.tasks.scan_tasks",
    "src.tasks.notification_tasks",
    "src.tasks.my_tasks",  # Add new module
]
```

3. Add routing if needed:
```python
task_routes={
    "src.tasks.my_tasks.*": {"queue": "my_queue"},
}
```

---

## Notes

- Worker runs with `acks_late=True` for reliability
- Failed tasks retry up to 3 times with exponential backoff
- Results expire after 24 hours
- Use `delay()` for async execution, `apply_async()` for options
- Scan tasks currently simulate execution (replace with real scanner integration)
