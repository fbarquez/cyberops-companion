"""
CTI Feed Integration Module.

Provides adapters for integrating with various Cyber Threat Intelligence feeds:
- MISP (Malware Information Sharing Platform)
- OTX (AlienVault Open Threat Exchange)
- VirusTotal
- OpenCTI
- TAXII

Usage:
    from src.integrations.cti_feeds import get_feed_adapter, FeedConfig, FeedType

    config = FeedConfig(
        feed_type=FeedType.MISP,
        base_url="https://misp.example.com",
        api_key="your-api-key",
    )
    adapter = get_feed_adapter(config)
    iocs = await adapter.fetch_iocs(since=datetime.now() - timedelta(hours=24))
"""
from src.integrations.cti_feeds.base import (
    BaseCTIFeedAdapter,
    FeedConfig,
    FeedSyncResult,
    FeedType,
    IOCType,
    NormalizedIOC,
    ThreatLevel,
)
from src.integrations.cti_feeds.exceptions import (
    CTIFeedError,
    FeedAPIError,
    FeedAuthError,
    FeedConfigError,
    FeedConnectionError,
    FeedParseError,
    FeedRateLimitError,
    FeedTimeoutError,
)


def get_feed_adapter(config: FeedConfig) -> BaseCTIFeedAdapter:
    """
    Factory function to get the appropriate feed adapter.

    Args:
        config: FeedConfig with connection details.

    Returns:
        An instance of the appropriate adapter.

    Raises:
        FeedConfigError: If feed type is not supported.
    """
    if config.feed_type == FeedType.MISP:
        from src.integrations.cti_feeds.misp_adapter import MISPAdapter
        return MISPAdapter(config)

    elif config.feed_type == FeedType.OTX:
        from src.integrations.cti_feeds.otx_adapter import OTXAdapter
        return OTXAdapter(config)

    elif config.feed_type == FeedType.VIRUSTOTAL:
        from src.integrations.cti_feeds.virustotal_adapter import VirusTotalAdapter
        return VirusTotalAdapter(config)

    else:
        raise FeedConfigError(
            f"Unsupported feed type: {config.feed_type}",
            feed_type=str(config.feed_type),
        )


__all__ = [
    # Core classes
    "BaseCTIFeedAdapter",
    "FeedConfig",
    "FeedSyncResult",
    "FeedType",
    "IOCType",
    "NormalizedIOC",
    "ThreatLevel",
    # Factory
    "get_feed_adapter",
    # Exceptions
    "CTIFeedError",
    "FeedAPIError",
    "FeedAuthError",
    "FeedConfigError",
    "FeedConnectionError",
    "FeedParseError",
    "FeedRateLimitError",
    "FeedTimeoutError",
]
