"""Notification service for managing notifications."""
import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notifications import (
    Notification, NotificationPreference, NotificationTemplate,
    WebhookSubscription, NotificationLog,
    NotificationType, NotificationPriority, NotificationChannel
)
from src.models.user import User
from src.schemas.notifications import (
    NotificationCreate, NotificationBulkCreate, NotificationUpdate, NotificationStats,
    NotificationPreferenceCreate, NotificationPreferenceUpdate,
    WebhookSubscriptionCreate, WebhookSubscriptionUpdate, WebhookTestResult
)
from src.services.email_service import get_email_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Notifications ==============

    async def create_notification(
        self,
        data: NotificationCreate,
        send_immediately: bool = True
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            priority=data.priority,
            title=data.title,
            message=data.message,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            entity_url=data.entity_url,
            data=data.data,
            expires_at=data.expires_at,
            channels_sent=[]
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        if send_immediately:
            await self._deliver_notification(notification, data.channels)

        return notification

    async def create_bulk_notifications(
        self,
        data: NotificationBulkCreate
    ) -> List[Notification]:
        """Create notifications for multiple users."""
        notifications = []
        for user_id in data.user_ids:
            notification = Notification(
                user_id=user_id,
                notification_type=data.notification_type,
                priority=data.priority,
                title=data.title,
                message=data.message,
                entity_type=data.entity_type,
                entity_id=data.entity_id,
                entity_url=data.entity_url,
                data=data.data,
                channels_sent=[]
            )
            self.db.add(notification)
            notifications.append(notification)

        await self.db.commit()

        # Deliver notifications
        for notification in notifications:
            await self._deliver_notification(notification)

        return notifications

    async def get_notification(self, notification_id: str, user_id: str) -> Optional[Notification]:
        """Get a specific notification."""
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        include_archived: bool = False,
        notification_types: Optional[List[NotificationType]] = None,
        priority: Optional[NotificationPriority] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Notification], int]:
        """List notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        if not include_archived:
            query = query.where(Notification.is_archived == False)

        if notification_types:
            query = query.where(Notification.notification_type.in_(notification_types))

        if priority:
            query = query.where(Notification.priority == priority)

        # Filter expired notifications
        query = query.where(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Get paginated results
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total or 0

    async def mark_as_read(
        self,
        user_id: str,
        notification_ids: Optional[List[str]] = None,
        mark_all: bool = False
    ) -> int:
        """Mark notifications as read."""
        query = update(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )

        if not mark_all and notification_ids:
            query = query.where(Notification.id.in_(notification_ids))

        query = query.values(is_read=True, read_at=datetime.utcnow())

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount

    async def archive_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> Optional[Notification]:
        """Archive a notification."""
        notification = await self.get_notification(notification_id, user_id)
        if notification:
            notification.is_archived = True
            notification.archived_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)
        return notification

    async def delete_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """Delete a notification."""
        notification = await self.get_notification(notification_id, user_id)
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        return False

    async def get_notification_stats(self, user_id: str) -> NotificationStats:
        """Get notification statistics for a user."""
        # Total count
        total_query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_archived == False
            )
        )
        total = await self.db.scalar(total_query) or 0

        # Unread count
        unread_query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_archived == False
            )
        )
        unread = await self.db.scalar(unread_query) or 0

        # By type
        type_query = select(
            Notification.notification_type,
            func.count().label("count")
        ).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_archived == False
            )
        ).group_by(Notification.notification_type)

        type_result = await self.db.execute(type_query)
        by_type = {str(row[0].value): row[1] for row in type_result.fetchall()}

        # By priority
        priority_query = select(
            Notification.priority,
            func.count().label("count")
        ).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_archived == False
            )
        ).group_by(Notification.priority)

        priority_result = await self.db.execute(priority_query)
        by_priority = {str(row[0].value): row[1] for row in priority_result.fetchall()}

        return NotificationStats(
            total=total,
            unread=unread,
            by_type=by_type,
            by_priority=by_priority
        )

    # ============== Notification Preferences ==============

    async def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_preferences(
        self,
        user_id: str,
        data: NotificationPreferenceCreate
    ) -> NotificationPreference:
        """Create notification preferences for a user."""
        preferences = NotificationPreference(
            user_id=user_id,
            notifications_enabled=data.notifications_enabled,
            email_enabled=data.email_enabled,
            email_frequency=data.email_frequency,
            quiet_hours_enabled=data.quiet_hours_enabled,
            quiet_hours_start=data.quiet_hours_start,
            quiet_hours_end=data.quiet_hours_end,
            quiet_hours_timezone=data.quiet_hours_timezone,
            channel_preferences=data.channel_preferences,
            min_priority_email=data.min_priority_email,
            min_priority_sms=data.min_priority_sms,
            category_settings=data.category_settings.dict() if data.category_settings else None
        )
        self.db.add(preferences)
        await self.db.commit()
        await self.db.refresh(preferences)
        return preferences

    async def update_preferences(
        self,
        user_id: str,
        data: NotificationPreferenceUpdate
    ) -> Optional[NotificationPreference]:
        """Update user notification preferences."""
        preferences = await self.get_preferences(user_id)

        if not preferences:
            # Create default preferences if none exist
            create_data = NotificationPreferenceCreate(**data.model_dump(exclude_unset=True))
            return await self.create_preferences(user_id, create_data)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        await self.db.commit()
        await self.db.refresh(preferences)
        return preferences

    async def get_or_create_preferences(self, user_id: str) -> NotificationPreference:
        """Get existing preferences or create defaults."""
        preferences = await self.get_preferences(user_id)
        if not preferences:
            preferences = await self.create_preferences(
                user_id,
                NotificationPreferenceCreate()
            )
        return preferences

    # ============== Webhook Subscriptions ==============

    async def create_webhook(
        self,
        data: WebhookSubscriptionCreate,
        created_by: str
    ) -> WebhookSubscription:
        """Create a webhook subscription."""
        webhook = WebhookSubscription(
            name=data.name,
            description=data.description,
            url=data.url,
            method=data.method,
            headers=data.headers,
            auth_type=data.auth_type,
            auth_config=data.auth_config,
            subscribed_events=[e.value for e in data.subscribed_events],
            filters=data.filters,
            is_active=data.is_active,
            created_by=created_by
        )
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def get_webhook(self, webhook_id: str) -> Optional[WebhookSubscription]:
        """Get a webhook subscription."""
        result = await self.db.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def list_webhooks(
        self,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[WebhookSubscription], int]:
        """List webhook subscriptions."""
        query = select(WebhookSubscription)

        if active_only:
            query = query.where(WebhookSubscription.is_active == True)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(WebhookSubscription.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        webhooks = list(result.scalars().all())

        return webhooks, total or 0

    async def update_webhook(
        self,
        webhook_id: str,
        data: WebhookSubscriptionUpdate
    ) -> Optional[WebhookSubscription]:
        """Update a webhook subscription."""
        webhook = await self.get_webhook(webhook_id)
        if not webhook:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if 'subscribed_events' in update_data and update_data['subscribed_events']:
            update_data['subscribed_events'] = [e.value for e in update_data['subscribed_events']]

        for field, value in update_data.items():
            setattr(webhook, field, value)

        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook subscription."""
        webhook = await self.get_webhook(webhook_id)
        if webhook:
            await self.db.delete(webhook)
            await self.db.commit()
            return True
        return False

    async def test_webhook(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        auth_type: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None,
        test_payload: Optional[Dict[str, Any]] = None
    ) -> WebhookTestResult:
        """Test a webhook endpoint."""
        if test_payload is None:
            test_payload = {
                "event_type": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "This is a test notification from CyberOps Companion"
            }

        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"
        request_headers["User-Agent"] = "IR-Companion-Webhook/1.0"

        # Add authentication
        if auth_type == "bearer" and auth_config:
            request_headers["Authorization"] = f"Bearer {auth_config.get('token', '')}"
        elif auth_type == "basic" and auth_config:
            import base64
            credentials = f"{auth_config.get('username', '')}:{auth_config.get('password', '')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            request_headers["Authorization"] = f"Basic {encoded}"

        try:
            start_time = datetime.utcnow()
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "POST":
                    response = await client.post(url, json=test_payload, headers=request_headers)
                else:
                    response = await client.put(url, json=test_payload, headers=request_headers)

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return WebhookTestResult(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_time_ms=response_time
            )
        except Exception as e:
            return WebhookTestResult(
                success=False,
                error=str(e)
            )

    # ============== Delivery ==============

    async def _deliver_notification(
        self,
        notification: Notification,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """Deliver notification through configured channels."""
        # Get user preferences
        preferences = await self.get_preferences(notification.user_id)

        if preferences and not preferences.notifications_enabled:
            return

        # Determine channels
        if channels is None:
            channels = [NotificationChannel.IN_APP]

            if preferences:
                # Check channel preferences for this notification type
                type_channels = (preferences.channel_preferences or {}).get(
                    notification.notification_type.value, []
                )
                channels.extend([NotificationChannel(c) for c in type_channels if c != "in_app"])

        # Deliver to each channel
        channels_sent = []
        delivery_status = {}

        for channel in channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    # Already stored in database
                    channels_sent.append("in_app")
                    delivery_status["in_app"] = {
                        "status": "delivered",
                        "at": datetime.utcnow().isoformat()
                    }

                elif channel == NotificationChannel.EMAIL:
                    if preferences and preferences.email_enabled:
                        # TODO: Send email using email service
                        await self._send_email_notification(notification)
                        channels_sent.append("email")
                        delivery_status["email"] = {
                            "status": "sent",
                            "at": datetime.utcnow().isoformat()
                        }

                elif channel == NotificationChannel.WEBHOOK:
                    await self._trigger_webhooks(notification)

            except Exception as e:
                delivery_status[channel.value] = {
                    "status": "failed",
                    "error": str(e),
                    "at": datetime.utcnow().isoformat()
                }

        # Update notification with delivery status
        notification.channels_sent = channels_sent
        notification.delivery_status = delivery_status
        await self.db.commit()

    async def _send_email_notification(self, notification: Notification):
        """Send email notification via SMTP."""
        email_service = get_email_service()

        if not email_service.is_configured():
            logger.debug("Email service not configured, skipping email notification")
            return

        # Get user email
        user = await self.db.get(User, notification.user_id)
        if not user or not user.email:
            logger.warning(f"User {notification.user_id} not found or has no email")
            return

        # Build action URL if entity exists
        action_url = notification.entity_url
        if not action_url and notification.entity_type and notification.entity_id:
            # Build URL based on entity type
            base_url = "http://localhost:3000"  # TODO: Get from config
            entity_routes = {
                "incident": f"/incidents/{notification.entity_id}",
                "alert": f"/soc?tab=alerts&id={notification.entity_id}",
                "case": f"/soc?tab=cases&id={notification.entity_id}",
                "vulnerability": f"/vulnerabilities?id={notification.entity_id}",
                "risk": f"/risks?id={notification.entity_id}",
                "vendor": f"/tprm?vendor={notification.entity_id}",
            }
            route = entity_routes.get(notification.entity_type, "")
            if route:
                action_url = f"{base_url}{route}"

        # Send email
        try:
            success = await email_service.send_notification_email(
                to=user.email,
                title=notification.title,
                message=notification.message or "",
                priority=notification.priority.value if notification.priority else "normal",
                notification_type=notification.notification_type.value if notification.notification_type else "general",
                entity_type=notification.entity_type,
                entity_id=notification.entity_id,
                action_url=action_url,
            )

            if success:
                logger.info(f"Email notification sent to {user.email}")
            else:
                logger.warning(f"Failed to send email notification to {user.email}")

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")

    async def _trigger_webhooks(self, notification: Notification):
        """Trigger webhooks for notification."""
        # Find matching webhooks
        result = await self.db.execute(
            select(WebhookSubscription).where(
                and_(
                    WebhookSubscription.is_active == True,
                    WebhookSubscription.consecutive_failures < 5
                )
            )
        )
        webhooks = result.scalars().all()

        for webhook in webhooks:
            if notification.notification_type.value in (webhook.subscribed_events or []):
                await self._send_webhook(webhook, notification)

    async def _send_webhook(
        self,
        webhook: WebhookSubscription,
        notification: Notification
    ):
        """Send notification to webhook."""
        payload = {
            "event_type": notification.notification_type.value,
            "notification_id": notification.id,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": notification.priority.value,
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "data": notification.data
        }

        result = await self.test_webhook(
            url=webhook.url,
            method=webhook.method,
            headers=webhook.headers,
            auth_type=webhook.auth_type,
            auth_config=webhook.auth_config,
            test_payload=payload
        )

        # Update webhook status
        webhook.last_triggered_at = datetime.utcnow()
        webhook.last_status = "success" if result.success else "failed"
        webhook.total_deliveries += 1

        if result.success:
            webhook.consecutive_failures = 0
        else:
            webhook.consecutive_failures += 1
            webhook.total_failures += 1
            webhook.last_error = result.error

        # Log delivery
        log = NotificationLog(
            notification_id=notification.id,
            channel=NotificationChannel.WEBHOOK,
            recipient=webhook.url,
            status="delivered" if result.success else "failed",
            attempted_at=datetime.utcnow(),
            delivered_at=datetime.utcnow() if result.success else None,
            response_code=result.status_code,
            error_message=result.error
        )
        self.db.add(log)

        await self.db.commit()

    # ============== Helpers ==============

    async def notify_incident_event(
        self,
        event_type: str,
        incident_id: str,
        incident_name: str,
        user_ids: List[str],
        severity: str,
        additional_data: Optional[Dict] = None
    ):
        """Create notifications for incident events."""
        type_mapping = {
            "created": NotificationType.INCIDENT_CREATED,
            "assigned": NotificationType.INCIDENT_ASSIGNED,
            "updated": NotificationType.INCIDENT_UPDATED,
            "escalated": NotificationType.INCIDENT_ESCALATED,
            "resolved": NotificationType.INCIDENT_RESOLVED,
            "closed": NotificationType.INCIDENT_CLOSED
        }

        notification_type = type_mapping.get(event_type, NotificationType.INCIDENT_UPDATED)

        priority = NotificationPriority.MEDIUM
        if severity == "critical":
            priority = NotificationPriority.CRITICAL
        elif severity == "high":
            priority = NotificationPriority.HIGH

        data = NotificationBulkCreate(
            user_ids=user_ids,
            notification_type=notification_type,
            priority=priority,
            title=f"Incident {event_type.title()}: {incident_name}",
            message=f"Incident {incident_id} has been {event_type}",
            entity_type="incident",
            entity_id=incident_id,
            entity_url=f"/incidents/{incident_id}",
            data={
                "incident_id": incident_id,
                "severity": severity,
                **(additional_data or {})
            }
        )

        await self.create_bulk_notifications(data)

    async def cleanup_expired_notifications(self, days_old: int = 30) -> int:
        """Clean up old read/archived notifications."""
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff
                )
            )
        )
        notifications = result.scalars().all()

        count = 0
        for notification in notifications:
            await self.db.delete(notification)
            count += 1

        await self.db.commit()
        return count
