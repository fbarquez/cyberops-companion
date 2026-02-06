"""
Celery tasks for BSI IT-Grundschutz automatic updates.
"""
import logging
from celery import shared_task

from src.celery_app import celery_app
from src.db.database import async_session_maker

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="src.tasks.bsi_tasks.check_bsi_updates",
    max_retries=3,
    default_retry_delay=300,
)
def check_bsi_updates(self):
    """
    Check for BSI IT-Grundschutz catalog updates.

    This task runs weekly to check if there are new versions
    available from BSI GitHub repositories.
    """
    import asyncio

    async def _check():
        from src.services.bsi_update_service import BSIUpdateService

        async with async_session_maker() as db:
            try:
                service = BSIUpdateService(db)
                result = await service.auto_update()

                logger.info(f"BSI update check completed: {result}")

                # If updates were applied, send notification
                if result.get("action") == "update" and result.get("result") == "success":
                    await _notify_update(result.get("details", {}))

                return result

            except Exception as e:
                logger.error(f"BSI update check failed: {e}")
                raise self.retry(exc=e)

    return asyncio.get_event_loop().run_until_complete(_check())


@celery_app.task(
    name="src.tasks.bsi_tasks.force_bsi_update",
)
def force_bsi_update():
    """
    Force a BSI catalog update regardless of version.

    Use this for manual/admin-triggered updates.
    """
    import asyncio

    async def _force_update():
        from src.services.bsi_update_service import BSIUpdateService

        async with async_session_maker() as db:
            service = BSIUpdateService(db)

            # First check for updates
            update_info = await service.check_for_updates()

            if update_info.get("content"):
                # Force has_updates to true
                update_info["has_updates"] = True
                result = await service.apply_update(update_info)
                return result
            else:
                return {"success": False, "message": "Could not fetch BSI catalog"}

    return asyncio.get_event_loop().run_until_complete(_force_update())


@celery_app.task(
    name="src.tasks.bsi_tasks.get_bsi_status",
)
def get_bsi_status():
    """
    Get current BSI catalog status.
    """
    import asyncio

    async def _get_status():
        from src.services.bsi_update_service import BSIUpdateService

        async with async_session_maker() as db:
            service = BSIUpdateService(db)
            return await service.get_status()

    return asyncio.get_event_loop().run_until_complete(_get_status())


async def _notify_update(details: dict):
    """Send notification about BSI catalog update."""
    from src.services.notification_service import NotificationService

    try:
        async with async_session_maker() as db:
            notification_service = NotificationService(db)

            stats = details.get("stats", {})
            message = (
                f"BSI IT-Grundschutz catalog updated to version {details.get('new_version', 'unknown')}. "
                f"Changes: {stats.get('bausteine_added', 0)} new Bausteine, "
                f"{stats.get('bausteine_updated', 0)} updated, "
                f"{stats.get('anforderungen_added', 0)} new Anforderungen, "
                f"{stats.get('anforderungen_updated', 0)} updated."
            )

            # Create system notification for admins
            await notification_service.create_system_notification(
                title="BSI Catalog Updated",
                message=message,
                notification_type="info",
                target_roles=["admin", "manager"],
            )

    except Exception as e:
        logger.warning(f"Failed to send BSI update notification: {e}")
