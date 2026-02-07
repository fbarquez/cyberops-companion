"""Scan progress pub/sub for real-time updates between Celery and WebSocket."""
import json
import logging
from typing import Optional
from datetime import datetime

import redis

from src.config import settings

logger = logging.getLogger(__name__)

# Redis channel prefix for scan progress
SCAN_PROGRESS_CHANNEL = "scan:progress:"


def get_sync_redis_client():
    """Get synchronous Redis client for Celery tasks."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def publish_scan_progress(
    scan_id: str,
    event: str,
    progress_percent: int = 0,
    state: str = "running",
    hosts_total: int = 0,
    hosts_completed: int = 0,
    current_host: Optional[str] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    total_findings: int = 0,
    severity_counts: Optional[dict] = None,
):
    """
    Publish scan progress update to Redis.

    Called from Celery tasks to broadcast progress to WebSocket clients.

    Args:
        scan_id: The scan ID
        event: Event type (progress, started, completed, failed, cancelled)
        progress_percent: Progress percentage (0-100)
        state: Scan state
        hosts_total: Total hosts to scan
        hosts_completed: Hosts completed
        current_host: Currently scanning host
        message: Status message
        error: Error message (for failed events)
        total_findings: Total findings (for completed events)
        severity_counts: Severity breakdown (for completed events)
    """
    try:
        client = get_sync_redis_client()

        data = {
            "event": f"scan:{event}",
            "data": {
                "scan_id": scan_id,
                "progress_percent": progress_percent,
                "state": state,
                "hosts_total": hosts_total,
                "hosts_completed": hosts_completed,
                "current_host": current_host,
                "message": message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add error for failed events
        if error:
            data["data"]["error"] = error

        # Add findings for completed events
        if event == "completed":
            data["data"]["total_findings"] = total_findings
            data["data"]["severity_counts"] = severity_counts or {}

        channel = f"{SCAN_PROGRESS_CHANNEL}{scan_id}"
        client.publish(channel, json.dumps(data))

        # Also store latest progress in Redis for clients that connect mid-scan
        client.setex(
            f"scan:latest:{scan_id}",
            3600,  # Expire after 1 hour
            json.dumps(data)
        )

        logger.debug(f"Published scan progress: {scan_id} - {event} - {progress_percent}%")

    except Exception as e:
        logger.error(f"Failed to publish scan progress: {e}")


def get_latest_scan_progress(scan_id: str) -> Optional[dict]:
    """Get the latest progress for a scan (for clients connecting mid-scan)."""
    try:
        client = get_sync_redis_client()
        data = client.get(f"scan:latest:{scan_id}")
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get scan progress: {e}")
        return None
