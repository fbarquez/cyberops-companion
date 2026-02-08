"""
Celery application configuration for background tasks.
"""
import os
from celery import Celery
from kombu import Queue

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "cyberops_companion",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "src.tasks.scan_tasks",
        "src.tasks.notification_tasks",
        "src.tasks.cti_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours

    # Task routing
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("scans", routing_key="scans.#"),
        Queue("notifications", routing_key="notifications.#"),
        Queue("cti", routing_key="cti.#"),
    ),
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Task routes
    task_routes={
        "src.tasks.scan_tasks.*": {"queue": "scans"},
        "src.tasks.notification_tasks.*": {"queue": "notifications"},
        "src.tasks.cti_tasks.*": {"queue": "cti"},
    },

    # Retry settings
    task_annotations={
        "*": {
            "rate_limit": "10/m",
            "max_retries": 3,
            "default_retry_delay": 60,
        }
    },

    # Beat scheduler (for periodic tasks)
    beat_schedule={
        # Sync all threat intelligence feeds every hour
        "sync-threat-feeds": {
            "task": "src.tasks.cti_tasks.sync_all_threat_feeds",
            "schedule": 3600.0,  # 1 hour in seconds
        },
        # Example: Run vulnerability sync every 6 hours
        # "sync-nvd-updates": {
        #     "task": "src.tasks.scan_tasks.sync_nvd_updates",
        #     "schedule": 21600.0,  # 6 hours in seconds
        # },
    },
)


# Task state constants
class TaskState:
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
