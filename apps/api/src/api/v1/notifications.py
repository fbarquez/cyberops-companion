"""Notification API endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import DBSession, CurrentUser, AdminUser
from src.models.notifications import NotificationType, NotificationPriority
from src.schemas.notifications import (
    NotificationCreate, NotificationResponse, NotificationUpdate,
    NotificationMarkRead, NotificationStats,
    NotificationPreferenceCreate, NotificationPreferenceUpdate, NotificationPreferenceResponse,
    WebhookSubscriptionCreate, WebhookSubscriptionUpdate, WebhookSubscriptionResponse,
    WebhookTest, WebhookTestResult
)
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


# ============== Notifications ==============

@router.get("", response_model=dict)
async def list_notifications(
    db: DBSession,
    current_user: CurrentUser,
    unread_only: bool = Query(False, description="Only return unread notifications"),
    include_archived: bool = Query(False, description="Include archived notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List notifications for the current user."""
    service = NotificationService(db)

    types = None
    if notification_type:
        try:
            types = [NotificationType(notification_type)]
        except ValueError:
            pass

    priority_filter = None
    if priority:
        try:
            priority_filter = NotificationPriority(priority)
        except ValueError:
            pass

    notifications, total = await service.list_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        include_archived=include_archived,
        notification_types=types,
        priority=priority_filter,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [NotificationResponse.model_validate(n) for n in notifications],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: DBSession,
    current_user: CurrentUser
):
    """Get notification statistics for the current user."""
    service = NotificationService(db)
    return await service.get_notification_stats(current_user.id)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get a specific notification."""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/mark-read")
async def mark_notifications_read(
    data: NotificationMarkRead,
    db: DBSession,
    current_user: CurrentUser
):
    """Mark notifications as read."""
    service = NotificationService(db)
    count = await service.mark_as_read(
        user_id=current_user.id,
        notification_ids=data.notification_ids,
        mark_all=data.mark_all
    )
    return {"marked_count": count}


@router.post("/{notification_id}/archive", response_model=NotificationResponse)
async def archive_notification(
    notification_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Archive a notification."""
    service = NotificationService(db)
    notification = await service.archive_notification(notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Delete a notification."""
    service = NotificationService(db)
    deleted = await service.delete_notification(notification_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}


# ============== Preferences ==============

@router.get("/preferences/me", response_model=NotificationPreferenceResponse)
async def get_my_preferences(
    db: DBSession,
    current_user: CurrentUser
):
    """Get notification preferences for the current user."""
    service = NotificationService(db)
    preferences = await service.get_or_create_preferences(current_user.id)
    return NotificationPreferenceResponse.model_validate(preferences)


@router.put("/preferences/me", response_model=NotificationPreferenceResponse)
async def update_my_preferences(
    data: NotificationPreferenceUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update notification preferences for the current user."""
    service = NotificationService(db)
    preferences = await service.update_preferences(current_user.id, data)
    return NotificationPreferenceResponse.model_validate(preferences)


# ============== Webhooks ==============

@router.get("/webhooks", response_model=dict)
async def list_webhooks(
    db: DBSession,
    current_user: CurrentUser,
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """List webhook subscriptions."""
    service = NotificationService(db)
    webhooks, total = await service.list_webhooks(
        active_only=active_only,
        limit=size,
        offset=(page - 1) * size
    )

    return {
        "items": [WebhookSubscriptionResponse.model_validate(w) for w in webhooks],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0
    }


@router.post("/webhooks", response_model=WebhookSubscriptionResponse)
async def create_webhook(
    data: WebhookSubscriptionCreate,
    db: DBSession,
    current_user: CurrentUser
):
    """Create a new webhook subscription."""
    service = NotificationService(db)
    webhook = await service.create_webhook(data, current_user.id)
    return WebhookSubscriptionResponse.model_validate(webhook)


@router.get("/webhooks/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook(
    webhook_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Get a specific webhook subscription."""
    service = NotificationService(db)
    webhook = await service.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookSubscriptionResponse.model_validate(webhook)


@router.put("/webhooks/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookSubscriptionUpdate,
    db: DBSession,
    current_user: CurrentUser
):
    """Update a webhook subscription."""
    service = NotificationService(db)
    webhook = await service.update_webhook(webhook_id, data)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookSubscriptionResponse.model_validate(webhook)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    db: DBSession,
    current_user: CurrentUser
):
    """Delete a webhook subscription."""
    service = NotificationService(db)
    deleted = await service.delete_webhook(webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}


@router.post("/webhooks/test", response_model=WebhookTestResult)
async def test_webhook(
    data: WebhookTest,
    db: DBSession,
    current_user: CurrentUser
):
    """Test a webhook endpoint."""
    service = NotificationService(db)
    result = await service.test_webhook(
        url=data.url,
        method=data.method,
        headers=data.headers,
        auth_type=data.auth_type,
        auth_config=data.auth_config,
        test_payload=data.test_payload
    )
    return result


# ============== Admin Endpoints ==============

@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    data: NotificationCreate,
    db: DBSession,
    current_user: AdminUser
):
    """Send a notification to a user (admin only)."""
    service = NotificationService(db)
    notification = await service.create_notification(data)
    return NotificationResponse.model_validate(notification)


@router.post("/cleanup")
async def cleanup_notifications(
    db: DBSession,
    current_user: AdminUser,
    days_old: int = Query(30, ge=1, le=365)
):
    """Clean up old notifications (admin only)."""
    service = NotificationService(db)
    count = await service.cleanup_expired_notifications(days_old)
    return {"deleted_count": count}


@router.post("/email/test")
async def test_email(
    current_user: AdminUser,
    email: Optional[str] = Query(None, description="Email to send test to (defaults to current user's email)")
):
    """
    Send a test email to verify email configuration.

    This endpoint is useful for verifying that SMTP settings are correctly configured.
    """
    from src.services.email_service import get_email_service

    email_service = get_email_service()

    if not email_service.is_configured():
        return {
            "success": False,
            "message": "Email service is not configured. Set EMAIL_ENABLED=true and configure SMTP settings in .env"
        }

    target_email = email or current_user.email
    if not target_email:
        return {
            "success": False,
            "message": "No email address provided and current user has no email"
        }

    success = await email_service.send_test_email(target_email)

    return {
        "success": success,
        "message": f"Test email {'sent successfully' if success else 'failed to send'} to {target_email}",
        "email": target_email
    }


@router.get("/email/status")
async def email_status(current_user: AdminUser):
    """
    Check email service configuration status.
    """
    from src.services.email_service import get_email_service
    from src.config import settings

    email_service = get_email_service()

    return {
        "enabled": settings.EMAIL_ENABLED,
        "configured": email_service.is_configured(),
        "smtp_host": settings.SMTP_HOST if settings.SMTP_HOST else None,
        "smtp_port": settings.SMTP_PORT,
        "smtp_from": settings.SMTP_FROM if settings.SMTP_FROM else None,
        "smtp_tls": settings.SMTP_TLS,
    }
