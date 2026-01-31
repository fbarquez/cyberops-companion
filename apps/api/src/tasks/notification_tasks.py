"""
Notification background tasks.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from src.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="src.tasks.notification_tasks.send_notification_async",
    max_retries=3,
    default_retry_delay=30,
)
def send_notification_async(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "medium",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a notification asynchronously.

    Args:
        user_id: Target user ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        priority: Priority level
        entity_type: Related entity type
        entity_id: Related entity ID

    Returns:
        Dict with notification result
    """
    logger.info(f"Sending async notification to user {user_id}: {title}")

    async def _send():
        from src.db.database import async_session_maker
        from src.services.notification_service import NotificationService
        from src.schemas.notifications import NotificationCreate
        from src.models.notifications import NotificationType, NotificationPriority

        async with async_session_maker() as db:
            service = NotificationService(db)

            notification_data = NotificationCreate(
                user_id=user_id,
                type=NotificationType(notification_type),
                priority=NotificationPriority(priority),
                title=title,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id,
            )

            notification = await service.create_notification(notification_data)

            return {
                "notification_id": notification.id,
                "status": "sent",
                "user_id": user_id,
            }

    try:
        result = run_async(_send())
        logger.info(f"Notification sent: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise


@celery_app.task(
    name="src.tasks.notification_tasks.send_scan_completion_notification",
)
def send_scan_completion_notification(
    scan_id: str,
    user_id: str,
    scan_name: str,
    total_findings: int,
    critical_count: int,
    high_count: int,
) -> Dict[str, Any]:
    """
    Send notification when a scan completes.

    Args:
        scan_id: Completed scan ID
        user_id: User to notify
        scan_name: Name of the scan
        total_findings: Total vulnerabilities found
        critical_count: Critical severity count
        high_count: High severity count

    Returns:
        Dict with notification result
    """
    priority = "critical" if critical_count > 0 else "high" if high_count > 0 else "medium"

    title = f"Scan Completed: {scan_name}"
    message = f"Found {total_findings} vulnerabilities"
    if critical_count > 0:
        message += f" ({critical_count} critical, {high_count} high)"
    elif high_count > 0:
        message += f" ({high_count} high severity)"

    return send_notification_async(
        user_id=user_id,
        notification_type="vulnerability",
        title=title,
        message=message,
        priority=priority,
        entity_type="scan",
        entity_id=scan_id,
    )


@celery_app.task(
    name="src.tasks.notification_tasks.cleanup_old_notifications",
)
def cleanup_old_notifications(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old notifications.

    Args:
        days_old: Delete notifications older than this many days

    Returns:
        Dict with cleanup result
    """
    logger.info(f"Cleaning up notifications older than {days_old} days")

    async def _cleanup():
        from src.db.database import async_session_maker
        from src.services.notification_service import NotificationService

        async with async_session_maker() as db:
            service = NotificationService(db)
            deleted_count = await service.cleanup_expired_notifications(days_old)

            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "days_old": days_old,
            }

    try:
        result = run_async(_cleanup())
        logger.info(f"Notification cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Notification cleanup failed: {str(e)}")
        raise
