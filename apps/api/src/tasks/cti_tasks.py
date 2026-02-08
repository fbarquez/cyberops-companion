"""
CTI (Cyber Threat Intelligence) Feed Sync Tasks.

Background tasks for synchronizing threat intelligence feeds.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import shared_task

from src.celery_app import celery_app, TaskState

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _sync_feed_async(feed_id: str) -> Dict[str, Any]:
    """
    Synchronize a single threat feed asynchronously.

    Args:
        feed_id: The ID of the ThreatFeed to sync.

    Returns:
        Dict with sync results.
    """
    from src.db.database import async_session_maker
    from src.models.threat_intel import ThreatFeed, IOC, ThreatLevel, IOCType, IOCStatus
    from src.integrations.cti_feeds import (
        get_feed_adapter,
        FeedConfig,
        FeedSyncResult,
        FeedType,
    )
    from src.integrations.cti_feeds.base import NormalizedIOC
    from src.integrations.cti_feeds.feed_normalizer import (
        deduplicate_iocs,
        calculate_risk_score,
        filter_iocs,
        normalize_ioc_value,
    )
    from src.integrations.cti_feeds.exceptions import (
        CTIFeedError,
        FeedRateLimitError,
    )
    from sqlalchemy import select

    start_time = datetime.utcnow()

    async with async_session_maker() as db:
        # Get feed configuration
        result = await db.execute(
            select(ThreatFeed).where(ThreatFeed.id == feed_id)
        )
        feed = result.scalar_one_or_none()

        if not feed:
            logger.error(f"Feed {feed_id} not found")
            return {
                "feed_id": feed_id,
                "success": False,
                "error": "Feed not found",
            }

        if not feed.is_enabled:
            logger.info(f"Feed {feed.name} is disabled, skipping sync")
            return {
                "feed_id": feed_id,
                "success": True,
                "skipped": True,
                "reason": "Feed is disabled",
            }

        logger.info(f"Starting sync for feed: {feed.name} (type: {feed.feed_type})")

        sync_result = FeedSyncResult(
            feed_id=feed_id,
            feed_type=FeedType(feed.feed_type.lower()),
            success=False,
            sync_started_at=start_time,
        )

        adapter = None
        try:
            # Create adapter from feed config
            config = FeedConfig.from_threat_feed(feed)
            adapter = get_feed_adapter(config)

            # Test connection
            await adapter.test_connection()

            # Fetch IOCs since last sync
            since = feed.last_sync if feed.last_sync else None
            iocs = await adapter.fetch_iocs(since=since, limit=5000)

            sync_result.iocs_fetched = len(iocs)
            logger.info(f"Fetched {len(iocs)} IOCs from {feed.name}")

            # Apply feed filters
            min_confidence = feed.min_confidence or 0.0
            allowed_types = None
            if feed.ioc_types:
                try:
                    allowed_types = [IOCType(t) for t in feed.ioc_types]
                except ValueError:
                    pass

            iocs = filter_iocs(
                iocs,
                min_confidence=min_confidence,
                allowed_types=allowed_types,
            )

            # Deduplicate
            iocs = deduplicate_iocs(iocs)

            # Process and store IOCs
            for normalized_ioc in iocs:
                try:
                    # Check if IOC exists
                    existing_result = await db.execute(
                        select(IOC).where(
                            IOC.value == normalize_ioc_value(normalized_ioc.value, normalized_ioc.type),
                            IOC.type == IOCType(normalized_ioc.type.value),
                        )
                    )
                    existing = existing_result.scalar_one_or_none()

                    if existing:
                        # Update existing IOC
                        _update_ioc_from_normalized(existing, normalized_ioc)
                        sync_result.iocs_updated += 1
                    else:
                        # Create new IOC
                        new_ioc = _create_ioc_from_normalized(normalized_ioc)
                        db.add(new_ioc)
                        sync_result.iocs_new += 1

                except Exception as e:
                    logger.warning(f"Error processing IOC {normalized_ioc.value}: {e}")
                    sync_result.iocs_skipped += 1

            # Update feed status
            feed.last_sync = datetime.utcnow()
            feed.last_sync_status = "success"
            feed.last_sync_count = sync_result.iocs_new + sync_result.iocs_updated

            await db.commit()

            sync_result.success = True
            sync_result.sync_completed_at = datetime.utcnow()
            sync_result.duration_seconds = (
                sync_result.sync_completed_at - start_time
            ).total_seconds()

            logger.info(
                f"Feed {feed.name} sync completed: "
                f"{sync_result.iocs_new} new, {sync_result.iocs_updated} updated, "
                f"{sync_result.iocs_skipped} skipped"
            )

        except FeedRateLimitError as e:
            sync_result.errors.append(f"Rate limit exceeded: {str(e)}")
            feed.last_sync_status = "rate_limited"
            await db.commit()
            logger.warning(f"Feed {feed.name} hit rate limit: {e}")

        except CTIFeedError as e:
            sync_result.errors.append(str(e))
            feed.last_sync_status = "error"
            await db.commit()
            logger.error(f"Feed {feed.name} sync error: {e}")

        except Exception as e:
            sync_result.errors.append(str(e))
            feed.last_sync_status = "error"
            await db.commit()
            logger.exception(f"Feed {feed.name} sync failed: {e}")

        finally:
            if adapter:
                await adapter.close()

        return sync_result.to_dict()


def _create_ioc_from_normalized(normalized: "NormalizedIOC") -> "IOC":
    """Create an IOC model from a NormalizedIOC."""
    from src.models.threat_intel import IOC, IOCType, IOCStatus, ThreatLevel
    from src.integrations.cti_feeds.feed_normalizer import calculate_risk_score

    ioc = IOC(
        value=normalized.value.lower().strip(),
        type=IOCType(normalized.type.value),
        status=IOCStatus.ACTIVE,
        threat_level=ThreatLevel(normalized.threat_level.value),
        risk_score=calculate_risk_score(normalized),
        confidence=normalized.confidence,
        description=normalized.description,
        tags=normalized.tags[:20],
        categories=normalized.categories[:10],
        source=normalized.source,
        source_ref=normalized.source_ref,
        first_seen=normalized.first_seen,
        last_seen=normalized.last_seen or datetime.utcnow(),
        country=normalized.country,
        asn=normalized.asn,
        mitre_techniques=normalized.mitre_techniques[:15],
        enrichment_data=normalized.raw_data,
        last_enriched=datetime.utcnow(),
    )
    return ioc


def _update_ioc_from_normalized(ioc: "IOC", normalized: "NormalizedIOC") -> None:
    """Update an existing IOC with data from a NormalizedIOC."""
    from src.models.threat_intel import ThreatLevel
    from src.integrations.cti_feeds.feed_normalizer import calculate_risk_score

    # Update threat level if higher
    threat_priority = {
        ThreatLevel.CRITICAL: 4,
        ThreatLevel.HIGH: 3,
        ThreatLevel.MEDIUM: 2,
        ThreatLevel.LOW: 1,
        ThreatLevel.UNKNOWN: 0,
    }
    new_level = ThreatLevel(normalized.threat_level.value)
    if threat_priority.get(new_level, 0) > threat_priority.get(ioc.threat_level, 0):
        ioc.threat_level = new_level

    # Update confidence if higher
    if normalized.confidence > ioc.confidence:
        ioc.confidence = normalized.confidence

    # Merge tags
    existing_tags = set(ioc.tags or [])
    existing_tags.update(normalized.tags)
    ioc.tags = list(existing_tags)[:20]

    # Merge categories
    existing_cats = set(ioc.categories or [])
    existing_cats.update(normalized.categories)
    ioc.categories = list(existing_cats)[:10]

    # Update sources
    if normalized.source and normalized.source not in (ioc.source or ""):
        ioc.source = f"{ioc.source},{normalized.source}" if ioc.source else normalized.source

    # Update last_seen
    ioc.last_seen = datetime.utcnow()

    # Update risk score
    ioc.risk_score = max(ioc.risk_score, calculate_risk_score(normalized))

    # Update MITRE techniques
    existing_mitre = set(ioc.mitre_techniques or [])
    existing_mitre.update(normalized.mitre_techniques)
    ioc.mitre_techniques = list(existing_mitre)[:15]

    # Update enrichment data
    enrichment = ioc.enrichment_data or {}
    enrichment.update(normalized.raw_data)
    ioc.enrichment_data = enrichment

    ioc.last_enriched = datetime.utcnow()
    ioc.updated_at = datetime.utcnow()


@celery_app.task(
    bind=True,
    name="src.tasks.cti_tasks.sync_threat_feed",
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def sync_threat_feed(self, feed_id: str) -> Dict[str, Any]:
    """
    Sync a single threat feed.

    Args:
        feed_id: The ID of the ThreatFeed to sync.

    Returns:
        Dict with sync results.
    """
    logger.info(f"Starting threat feed sync task for feed_id: {feed_id}")

    try:
        self.update_state(
            state=TaskState.PROGRESS,
            meta={"feed_id": feed_id, "status": "syncing"}
        )

        result = run_async(_sync_feed_async(feed_id))

        return result

    except Exception as e:
        logger.error(f"Feed sync task failed for {feed_id}: {str(e)}")
        return {
            "feed_id": feed_id,
            "success": False,
            "error": str(e),
        }


async def _sync_all_feeds_async() -> Dict[str, Any]:
    """Sync all enabled threat feeds."""
    from src.db.database import async_session_maker
    from src.models.threat_intel import ThreatFeed
    from sqlalchemy import select

    results = {
        "total_feeds": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "feed_results": [],
    }

    async with async_session_maker() as db:
        # Get all enabled feeds
        query = select(ThreatFeed).where(ThreatFeed.is_enabled == True)
        feed_result = await db.execute(query)
        feeds = feed_result.scalars().all()

        results["total_feeds"] = len(feeds)

        for feed in feeds:
            try:
                feed_result = await _sync_feed_async(str(feed.id))
                results["feed_results"].append(feed_result)

                if feed_result.get("success"):
                    results["successful"] += 1
                elif feed_result.get("skipped"):
                    results["skipped"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"Error syncing feed {feed.name}: {e}")
                results["failed"] += 1
                results["feed_results"].append({
                    "feed_id": str(feed.id),
                    "feed_name": feed.name,
                    "success": False,
                    "error": str(e),
                })

    return results


@celery_app.task(
    bind=True,
    name="src.tasks.cti_tasks.sync_all_threat_feeds",
    max_retries=2,
    default_retry_delay=600,
)
def sync_all_threat_feeds(self) -> Dict[str, Any]:
    """
    Sync all enabled threat feeds.

    This task is designed to run periodically (e.g., hourly via Celery Beat).

    Returns:
        Dict with overall sync results.
    """
    logger.info("Starting sync of all threat feeds")

    try:
        self.update_state(
            state=TaskState.PROGRESS,
            meta={"status": "syncing_all_feeds"}
        )

        result = run_async(_sync_all_feeds_async())

        logger.info(
            f"All feeds sync completed: "
            f"{result['successful']}/{result['total_feeds']} successful, "
            f"{result['failed']} failed, {result['skipped']} skipped"
        )

        return result

    except Exception as e:
        logger.error(f"Sync all feeds task failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


async def _enrich_ioc_async(
    ioc_value: str,
    ioc_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enrich a single IOC using configured integrations.

    Args:
        ioc_value: The IOC value to enrich.
        ioc_type: The type of IOC (optional).

    Returns:
        Dict with enrichment results.
    """
    from src.db.database import async_session_maker
    from src.models.integrations import Integration, IntegrationType, IntegrationStatus
    from src.integrations.cti_feeds import get_feed_adapter, FeedConfig, FeedType
    from src.integrations.cti_feeds.base import IOCType
    from sqlalchemy import select

    results = {
        "ioc_value": ioc_value,
        "sources": {},
        "aggregated": None,
    }

    # Map of integration types to feed types
    feed_integrations = {
        IntegrationType.VIRUSTOTAL: FeedType.VIRUSTOTAL,
        IntegrationType.OTX: FeedType.OTX,
        IntegrationType.MISP: FeedType.MISP,
    }

    async with async_session_maker() as db:
        for integration_type, feed_type in feed_integrations.items():
            try:
                # Check for active integration
                query = select(Integration).where(
                    Integration.integration_type == integration_type,
                    Integration.status == IntegrationStatus.ACTIVE,
                    Integration.is_enabled == True,
                )
                result = await db.execute(query)
                integration = result.scalar_one_or_none()

                if not integration:
                    continue

                # Create adapter and fetch details
                config = FeedConfig.from_integration(integration)
                adapter = get_feed_adapter(config)

                try:
                    detected_type = None
                    if ioc_type:
                        detected_type = IOCType(ioc_type)

                    ioc_details = await adapter.get_ioc_details(ioc_value, detected_type)

                    if ioc_details:
                        results["sources"][feed_type.value] = ioc_details.to_dict()

                finally:
                    await adapter.close()

            except Exception as e:
                logger.warning(f"Error enriching IOC with {integration_type}: {e}")
                results["sources"][feed_type.value] = {"error": str(e)}

    return results


@celery_app.task(
    bind=True,
    name="src.tasks.cti_tasks.enrich_ioc",
    max_retries=2,
    default_retry_delay=60,
)
def enrich_ioc(
    self,
    ioc_value: str,
    ioc_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enrich a single IOC with data from configured threat intel sources.

    Args:
        ioc_value: The IOC value to enrich.
        ioc_type: The type of IOC (optional).

    Returns:
        Dict with enrichment results from all sources.
    """
    logger.info(f"Enriching IOC: {ioc_value}")

    try:
        result = run_async(_enrich_ioc_async(ioc_value, ioc_type))
        return result

    except Exception as e:
        logger.error(f"IOC enrichment failed for {ioc_value}: {str(e)}")
        return {
            "ioc_value": ioc_value,
            "error": str(e),
        }
