# Email Service

**Status:** ✅ Implemented
**Date:** 2026-01-31
**Location:** `apps/api/src/services/email_service.py`

---

## Overview

Async email service using `aiosmtplib` for non-blocking SMTP operations. Supports HTML templates with Jinja2 rendering.

---

## Features

- Async SMTP sending (non-blocking)
- HTML email templates with Jinja2
- TLS/SSL support
- Priority-based email styling
- Test email functionality
- Configuration validation

---

## Configuration

```env
# .env file
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
SMTP_FROM_NAME=CyberOps Companion
SMTP_TLS=true
SMTP_SSL=false
```

---

## API Endpoints

### Test Email
```
POST /api/v1/notifications/email/test
Authorization: Bearer <admin_token>
Query: email=test@example.com (optional)
```

### Email Status
```
GET /api/v1/notifications/email/status
Authorization: Bearer <admin_token>
```

---

## Usage in Code

```python
from src.services.email_service import get_email_service

email_service = get_email_service()

# Check if configured
if email_service.is_configured():
    # Send notification email
    await email_service.send_notification_email(
        to="user@example.com",
        title="New Alert",
        message="A critical alert has been triggered.",
        priority="critical",
        action_url="https://app.example.com/alerts/123",
        action_text="View Alert"
    )

    # Send custom email
    await email_service.send_email(
        to="user@example.com",
        subject="Custom Subject",
        body_html="<h1>Hello</h1>",
        body_text="Hello"
    )
```

---

## Email Template

Located at: `apps/api/src/templates/email/notification.html`

Features:
- Responsive design
- Priority-based header colors:
  - Critical/High: Red (#dc2626)
  - Medium: Yellow (#f59e0b)
  - Low/Info: Blue (#3b82f6)
- Action button
- Footer with app name

---

## Files

| File | Purpose |
|------|---------|
| `services/email_service.py` | Main email service class |
| `templates/email/notification.html` | HTML email template |
| `config.py` | SMTP configuration settings |

---

## Dependencies

```
aiosmtplib>=2.0.0
jinja2>=3.0.0
```

---

## Notes

- For Gmail: Use App Passwords, not regular password
- For testing: Use Mailtrap.io to catch emails without sending
- Email is sent asynchronously in notification service
