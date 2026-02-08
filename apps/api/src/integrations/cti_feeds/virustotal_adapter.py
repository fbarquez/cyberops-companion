"""
VirusTotal Feed Adapter.

Integrates with VirusTotal API for IOC enrichment:
- File hash analysis
- URL/Domain reputation
- IP address information
- Detection statistics from multiple engines
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.integrations.cti_feeds.base import (
    BaseCTIFeedAdapter,
    FeedConfig,
    FeedType,
    IOCType,
    NormalizedIOC,
    ThreatLevel,
)
from src.integrations.cti_feeds.exceptions import (
    FeedAPIError,
    FeedAuthError,
    FeedConnectionError,
    FeedParseError,
    FeedRateLimitError,
)

logger = logging.getLogger(__name__)


class VirusTotalAdapter(BaseCTIFeedAdapter):
    """
    Adapter for VirusTotal threat intelligence.

    Uses vt-py library for async API access.
    Note: VirusTotal is primarily for enrichment, not bulk IOC feeds.
    The fetch_iocs method is limited; use get_ioc_details for enrichment.
    """

    feed_type = FeedType.VIRUSTOTAL

    # Rate limiting: Free tier = 4 requests/minute
    RATE_LIMIT_DELAY = 15  # seconds between requests for free tier

    def __init__(self, config: FeedConfig):
        super().__init__(config)
        self._client = None
        self._connected = False
        self._last_request_time = 0

    async def _get_client(self):
        """Get or create the VirusTotal client."""
        if self._client is None:
            try:
                import vt
            except ImportError:
                raise FeedConnectionError(
                    "vt-py library not installed. Run: pip install vt-py",
                    feed_type="virustotal",
                )

            try:
                self._client = vt.Client(self.config.api_key)
                self._connected = True
            except Exception as e:
                raise FeedConnectionError(
                    f"Failed to create VirusTotal client: {str(e)}",
                    feed_type="virustotal",
                )

        return self._client

    async def _rate_limit(self):
        """Implement rate limiting for free tier."""
        import time

        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self.RATE_LIMIT_DELAY:
            wait_time = self.RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    async def test_connection(self) -> bool:
        """Test connection to VirusTotal API."""
        try:
            client = await self._get_client()
            await self._rate_limit()

            # Get API usage to verify key
            url = "/api/v3/users/current"

            async with client:
                user = await client.get_object_async("/users/current")
                logger.info(f"Connected to VirusTotal as: {user.id}")
                return True

        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                raise FeedAuthError(
                    "VirusTotal authentication failed: Invalid API key",
                    feed_type="virustotal",
                )
            if "429" in error_str or "quota" in error_str.lower():
                raise FeedRateLimitError(
                    "VirusTotal rate limit exceeded",
                    feed_type="virustotal",
                    retry_after=60,
                )
            raise FeedConnectionError(
                f"VirusTotal connection test failed: {str(e)}",
                feed_type="virustotal",
            )

    async def fetch_iocs(
        self,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[NormalizedIOC]:
        """
        Fetch IOCs from VirusTotal.

        Note: VirusTotal is not designed for bulk IOC feeds.
        This method has limited functionality. For hunting, use the
        VT Intelligence search (premium feature).

        Args:
            since: Not used for VirusTotal.
            limit: Maximum number of IOCs to fetch.

        Returns:
            Empty list (use get_ioc_details for individual lookups).
        """
        logger.warning(
            "VirusTotal adapter does not support bulk IOC feeds. "
            "Use get_ioc_details() for individual IOC enrichment, "
            "or VT Intelligence (premium) for IOC hunting."
        )
        return []

    async def get_ioc_details(
        self,
        ioc_value: str,
        ioc_type: Optional[IOCType] = None,
    ) -> Optional[NormalizedIOC]:
        """
        Get detailed information about a specific IOC from VirusTotal.

        Args:
            ioc_value: The IOC value to look up.
            ioc_type: The type of IOC (auto-detected if not provided).

        Returns:
            NormalizedIOC with details, or None if not found.
        """
        try:
            client = await self._get_client()
            await self._rate_limit()

            # Detect IOC type if not provided
            if not ioc_type:
                ioc_type = self._detect_ioc_type(ioc_value)

            async with client:
                if ioc_type == IOCType.IP_ADDRESS:
                    return await self._lookup_ip(client, ioc_value)
                elif ioc_type == IOCType.DOMAIN:
                    return await self._lookup_domain(client, ioc_value)
                elif ioc_type == IOCType.URL:
                    return await self._lookup_url(client, ioc_value)
                elif ioc_type in [
                    IOCType.FILE_HASH_MD5,
                    IOCType.FILE_HASH_SHA1,
                    IOCType.FILE_HASH_SHA256,
                ]:
                    return await self._lookup_file(client, ioc_value, ioc_type)
                else:
                    logger.warning(f"Unsupported IOC type for VirusTotal: {ioc_type}")
                    return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                raise FeedRateLimitError(
                    "VirusTotal rate limit exceeded",
                    feed_type="virustotal",
                    retry_after=60,
                )
            if "NotFoundError" in error_str or "404" in error_str:
                logger.debug(f"IOC not found in VirusTotal: {ioc_value}")
                return None
            logger.warning(f"Error looking up IOC {ioc_value} in VirusTotal: {e}")
            return None

    async def _lookup_ip(
        self,
        client,
        ip_address: str,
    ) -> Optional[NormalizedIOC]:
        """Look up an IP address in VirusTotal."""
        try:
            ip_obj = await client.get_object_async(f"/ip_addresses/{ip_address}")

            # Get detection stats
            last_analysis = getattr(ip_obj, "last_analysis_stats", {})
            malicious = last_analysis.get("malicious", 0)
            suspicious = last_analysis.get("suspicious", 0)
            total = sum(last_analysis.values()) if last_analysis else 0

            # Calculate threat level
            detection_ratio = (malicious + suspicious) / total if total > 0 else 0
            threat_level = self._map_threat_level(
                detection_ratio * 100, "virustotal"
            )

            # Extract tags and categories
            tags = list(getattr(ip_obj, "tags", []))
            categories = list(getattr(ip_obj, "categories", {}).values()) if hasattr(ip_obj, "categories") else []

            # Get AS information
            asn = getattr(ip_obj, "asn", None)
            as_owner = getattr(ip_obj, "as_owner", "")
            country = getattr(ip_obj, "country", None)

            # Crowdsourced context
            crowd_context = getattr(ip_obj, "crowdsourced_context", [])
            description_parts = []
            for ctx in crowd_context[:3]:
                if isinstance(ctx, dict):
                    description_parts.append(ctx.get("details", ""))

            return NormalizedIOC(
                value=ip_address,
                type=IOCType.IP_ADDRESS,
                threat_level=threat_level,
                confidence=min(0.95, 0.5 + (detection_ratio * 0.5)),
                source="virustotal",
                source_ref=f"ip:{ip_address}",
                tags=tags[:10],
                categories=categories[:5],
                description=" | ".join(description_parts) if description_parts else f"VT: {malicious}/{total} malicious",
                first_seen=None,
                last_seen=None,
                related_actors=[],
                related_campaigns=[],
                mitre_techniques=[],
                country=country,
                asn=f"AS{asn} {as_owner}" if asn else None,
                raw_data={
                    "last_analysis_stats": last_analysis,
                    "reputation": getattr(ip_obj, "reputation", 0),
                    "total_votes": getattr(ip_obj, "total_votes", {}),
                },
            )

        except Exception as e:
            if "NotFoundError" in str(e):
                return None
            raise

    async def _lookup_domain(
        self,
        client,
        domain: str,
    ) -> Optional[NormalizedIOC]:
        """Look up a domain in VirusTotal."""
        try:
            domain_obj = await client.get_object_async(f"/domains/{domain}")

            # Get detection stats
            last_analysis = getattr(domain_obj, "last_analysis_stats", {})
            malicious = last_analysis.get("malicious", 0)
            suspicious = last_analysis.get("suspicious", 0)
            total = sum(last_analysis.values()) if last_analysis else 0

            # Calculate threat level
            detection_ratio = (malicious + suspicious) / total if total > 0 else 0
            threat_level = self._map_threat_level(
                detection_ratio * 100, "virustotal"
            )

            # Extract categories
            categories = list(getattr(domain_obj, "categories", {}).values()) if hasattr(domain_obj, "categories") else []
            tags = list(getattr(domain_obj, "tags", []))

            # Popularity ranks
            popularity = getattr(domain_obj, "popularity_ranks", {})

            # Crowdsourced context
            crowd_context = getattr(domain_obj, "crowdsourced_context", [])
            description_parts = []
            for ctx in crowd_context[:3]:
                if isinstance(ctx, dict):
                    description_parts.append(ctx.get("details", ""))

            return NormalizedIOC(
                value=domain,
                type=IOCType.DOMAIN,
                threat_level=threat_level,
                confidence=min(0.95, 0.5 + (detection_ratio * 0.5)),
                source="virustotal",
                source_ref=f"domain:{domain}",
                tags=tags[:10],
                categories=categories[:5],
                description=" | ".join(description_parts) if description_parts else f"VT: {malicious}/{total} malicious",
                first_seen=None,
                last_seen=None,
                related_actors=[],
                related_campaigns=[],
                mitre_techniques=[],
                raw_data={
                    "last_analysis_stats": last_analysis,
                    "reputation": getattr(domain_obj, "reputation", 0),
                    "popularity_ranks": popularity,
                    "registrar": getattr(domain_obj, "registrar", None),
                },
            )

        except Exception as e:
            if "NotFoundError" in str(e):
                return None
            raise

    async def _lookup_url(
        self,
        client,
        url: str,
    ) -> Optional[NormalizedIOC]:
        """Look up a URL in VirusTotal."""
        import base64
        import hashlib

        try:
            # URL needs to be base64 encoded for VT API
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
            url_obj = await client.get_object_async(f"/urls/{url_id}")

            # Get detection stats
            last_analysis = getattr(url_obj, "last_analysis_stats", {})
            malicious = last_analysis.get("malicious", 0)
            suspicious = last_analysis.get("suspicious", 0)
            total = sum(last_analysis.values()) if last_analysis else 0

            # Calculate threat level
            detection_ratio = (malicious + suspicious) / total if total > 0 else 0
            threat_level = self._map_threat_level(
                detection_ratio * 100, "virustotal"
            )

            # Extract categories
            categories = list(getattr(url_obj, "categories", {}).values()) if hasattr(url_obj, "categories") else []
            tags = list(getattr(url_obj, "tags", []))

            return NormalizedIOC(
                value=url,
                type=IOCType.URL,
                threat_level=threat_level,
                confidence=min(0.95, 0.5 + (detection_ratio * 0.5)),
                source="virustotal",
                source_ref=f"url:{url_id}",
                tags=tags[:10],
                categories=categories[:5],
                description=f"VT: {malicious}/{total} malicious",
                first_seen=None,
                last_seen=None,
                related_actors=[],
                related_campaigns=[],
                mitre_techniques=[],
                raw_data={
                    "last_analysis_stats": last_analysis,
                    "final_url": getattr(url_obj, "final_url", url),
                    "title": getattr(url_obj, "title", None),
                },
            )

        except Exception as e:
            if "NotFoundError" in str(e):
                return None
            raise

    async def _lookup_file(
        self,
        client,
        file_hash: str,
        ioc_type: IOCType,
    ) -> Optional[NormalizedIOC]:
        """Look up a file hash in VirusTotal."""
        try:
            file_obj = await client.get_object_async(f"/files/{file_hash}")

            # Get detection stats
            last_analysis = getattr(file_obj, "last_analysis_stats", {})
            malicious = last_analysis.get("malicious", 0)
            suspicious = last_analysis.get("suspicious", 0)
            total = sum(last_analysis.values()) if last_analysis else 0

            # Calculate threat level
            detection_ratio = (malicious + suspicious) / total if total > 0 else 0
            threat_level = self._map_threat_level(
                detection_ratio * 100, "virustotal"
            )

            # Extract file info
            tags = list(getattr(file_obj, "tags", []))
            type_description = getattr(file_obj, "type_description", "")
            meaningful_name = getattr(file_obj, "meaningful_name", "")

            # Popular threat labels
            popular_threat = getattr(file_obj, "popular_threat_classification", {})
            suggested_label = popular_threat.get("suggested_threat_label", "")

            categories = []
            if type_description:
                categories.append(type_description)
            if suggested_label:
                categories.append(suggested_label)

            # Crowdsourced context / YARA rules
            crowd_yara = getattr(file_obj, "crowdsourced_yara_results", [])
            mitre_techniques = []
            for yara in crowd_yara[:5]:
                if isinstance(yara, dict):
                    rule = yara.get("rule_name", "")
                    if rule:
                        tags.append(f"yara:{rule}")

            # Sandbox verdicts
            sandbox = getattr(file_obj, "sandbox_verdicts", {})
            for vendor, verdict in list(sandbox.items())[:3]:
                if isinstance(verdict, dict):
                    cat = verdict.get("category", "")
                    if cat:
                        categories.append(f"{vendor}:{cat}")

            # Signature info
            signature = getattr(file_obj, "signature_info", {})
            if signature and signature.get("verified") == "Signed":
                tags.append("signed")

            return NormalizedIOC(
                value=file_hash,
                type=ioc_type,
                threat_level=threat_level,
                confidence=min(0.95, 0.5 + (detection_ratio * 0.5)),
                source="virustotal",
                source_ref=f"file:{file_hash}",
                tags=list(set(tags))[:15],
                categories=categories[:5],
                description=f"{meaningful_name or 'Unknown'} - {suggested_label or f'{malicious}/{total} detections'}",
                first_seen=None,
                last_seen=None,
                related_actors=[],
                related_campaigns=[],
                mitre_techniques=mitre_techniques,
                raw_data={
                    "last_analysis_stats": last_analysis,
                    "md5": getattr(file_obj, "md5", None),
                    "sha1": getattr(file_obj, "sha1", None),
                    "sha256": getattr(file_obj, "sha256", None),
                    "size": getattr(file_obj, "size", None),
                    "type_description": type_description,
                    "meaningful_name": meaningful_name,
                },
            )

        except Exception as e:
            if "NotFoundError" in str(e):
                return None
            raise

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.close_async()
            self._client = None
        self._connected = False
