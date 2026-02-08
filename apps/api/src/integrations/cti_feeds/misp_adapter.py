"""
MISP (Malware Information Sharing Platform) Feed Adapter.

Integrates with MISP instances to fetch threat intelligence:
- Events with IOC attributes
- Galaxy clusters for threat actors and campaigns
- Tags for categorization
"""
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


class MISPAdapter(BaseCTIFeedAdapter):
    """
    Adapter for MISP threat intelligence platform.

    Uses the PyMISP library to interact with MISP REST API.
    """

    feed_type = FeedType.MISP

    def __init__(self, config: FeedConfig):
        super().__init__(config)
        self._misp = None
        self._connected = False

    async def _get_client(self):
        """Get or create the MISP client."""
        if self._misp is None:
            try:
                from pymisp import PyMISP
            except ImportError:
                raise FeedConnectionError(
                    "PyMISP library not installed. Run: pip install pymisp",
                    feed_type="misp",
                )

            try:
                self._misp = PyMISP(
                    url=self.config.base_url,
                    key=self.config.api_key,
                    ssl=self.config.verify_ssl,
                    timeout=self.config.timeout,
                )
                self._connected = True
            except Exception as e:
                raise FeedConnectionError(
                    f"Failed to connect to MISP: {str(e)}",
                    feed_type="misp",
                )

        return self._misp

    async def test_connection(self) -> bool:
        """Test connection to MISP instance."""
        try:
            misp = await self._get_client()
            # Get server version to verify connection
            version = misp.get_version()
            if "errors" in version:
                raise FeedAuthError(
                    f"MISP authentication failed: {version['errors']}",
                    feed_type="misp",
                )
            logger.info(f"Connected to MISP version: {version.get('version', 'unknown')}")
            return True
        except FeedAuthError:
            raise
        except Exception as e:
            raise FeedConnectionError(
                f"MISP connection test failed: {str(e)}",
                feed_type="misp",
            )

    async def fetch_iocs(
        self,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[NormalizedIOC]:
        """
        Fetch IOCs from MISP events.

        Args:
            since: Only fetch events modified after this datetime.
            limit: Maximum number of IOCs to fetch.

        Returns:
            List of normalized IOCs.
        """
        misp = await self._get_client()
        normalized_iocs: List[NormalizedIOC] = []

        try:
            # Build search parameters
            search_params = {
                "limit": min(limit, 1000),
                "to_ids": 1,  # Only get IOCs marked for IDS
                "published": True,
            }

            if since:
                search_params["timestamp"] = since.strftime("%Y-%m-%d")

            # Apply filters from config
            filters = self.config.filters
            if filters.get("tags"):
                search_params["tags"] = filters["tags"]
            if filters.get("threat_level"):
                search_params["threat_level"] = filters["threat_level"]

            # Search for events
            events = misp.search("events", **search_params)

            if isinstance(events, dict) and "errors" in events:
                raise FeedAPIError(
                    f"MISP search error: {events['errors']}",
                    feed_type="misp",
                )

            # Process each event
            for event_data in events:
                if len(normalized_iocs) >= limit:
                    break

                event = event_data.get("Event", event_data)
                event_iocs = self._process_event(event)
                normalized_iocs.extend(event_iocs)

            logger.info(f"Fetched {len(normalized_iocs)} IOCs from MISP")
            return normalized_iocs[:limit]

        except (FeedAPIError, FeedAuthError):
            raise
        except Exception as e:
            raise FeedParseError(
                f"Error fetching IOCs from MISP: {str(e)}",
                feed_type="misp",
            )

    def _process_event(self, event: Dict[str, Any]) -> List[NormalizedIOC]:
        """Process a MISP event and extract IOCs."""
        iocs = []
        event_id = event.get("id", "")
        event_info = event.get("info", "")
        threat_level = self._map_threat_level(
            event.get("threat_level_id"), "misp"
        )

        # Extract event-level tags
        event_tags = self._extract_tags(event.get("Tag", []))
        event_galaxies = self._extract_galaxies(event.get("Galaxy", []))

        # Process attributes (IOCs)
        for attr in event.get("Attribute", []):
            if not attr.get("to_ids"):
                continue

            ioc = self._attribute_to_ioc(
                attr,
                event_id=event_id,
                event_info=event_info,
                threat_level=threat_level,
                event_tags=event_tags,
                galaxies=event_galaxies,
            )
            if ioc:
                iocs.append(ioc)

        # Process object attributes
        for obj in event.get("Object", []):
            for attr in obj.get("Attribute", []):
                if not attr.get("to_ids"):
                    continue

                ioc = self._attribute_to_ioc(
                    attr,
                    event_id=event_id,
                    event_info=event_info,
                    threat_level=threat_level,
                    event_tags=event_tags,
                    galaxies=event_galaxies,
                )
                if ioc:
                    iocs.append(ioc)

        return iocs

    def _attribute_to_ioc(
        self,
        attr: Dict[str, Any],
        event_id: str,
        event_info: str,
        threat_level: ThreatLevel,
        event_tags: List[str],
        galaxies: Dict[str, List[str]],
    ) -> Optional[NormalizedIOC]:
        """Convert a MISP attribute to a NormalizedIOC."""
        value = attr.get("value", "").strip()
        if not value:
            return None

        attr_type = attr.get("type", "")
        ioc_type = self._detect_ioc_type(value, attr_type)

        # Skip unsupported types
        if ioc_type == IOCType.UNKNOWN:
            return None

        # Extract attribute-specific tags
        attr_tags = self._extract_tags(attr.get("Tag", []))
        all_tags = list(set(event_tags + attr_tags))

        # Parse timestamps
        first_seen = None
        if attr.get("first_seen"):
            try:
                first_seen = datetime.fromisoformat(
                    attr["first_seen"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        last_seen = None
        if attr.get("last_seen"):
            try:
                last_seen = datetime.fromisoformat(
                    attr["last_seen"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        if not first_seen and attr.get("timestamp"):
            try:
                first_seen = datetime.fromtimestamp(int(attr["timestamp"]))
            except (ValueError, TypeError):
                pass

        return NormalizedIOC(
            value=value,
            type=ioc_type,
            threat_level=threat_level,
            confidence=0.8 if attr.get("to_ids") else 0.5,
            source="misp",
            source_ref=f"event:{event_id}:attr:{attr.get('id', '')}",
            tags=all_tags,
            categories=[attr.get("category", "")],
            description=f"{event_info} - {attr.get('comment', '')}".strip(" -"),
            first_seen=first_seen,
            last_seen=last_seen,
            related_actors=galaxies.get("threat_actors", []),
            related_campaigns=galaxies.get("campaigns", []),
            mitre_techniques=galaxies.get("mitre_attack", []),
            raw_data={
                "event_id": event_id,
                "attribute_id": attr.get("id"),
                "attribute_type": attr_type,
                "category": attr.get("category"),
            },
        )

    def _extract_tags(self, tags: List[Dict[str, Any]]) -> List[str]:
        """Extract tag names from MISP tag objects."""
        return [
            tag.get("name", "")
            for tag in tags
            if tag.get("name") and not tag.get("name", "").startswith("misp-galaxy:")
        ]

    def _extract_galaxies(self, galaxies: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract galaxy information for threat actors, campaigns, and MITRE ATT&CK.
        """
        result = {
            "threat_actors": [],
            "campaigns": [],
            "mitre_attack": [],
        }

        for galaxy in galaxies:
            galaxy_type = galaxy.get("type", "").lower()
            clusters = galaxy.get("GalaxyCluster", [])

            for cluster in clusters:
                name = cluster.get("value", "")
                if not name:
                    continue

                if "threat-actor" in galaxy_type:
                    result["threat_actors"].append(name)
                elif "campaign" in galaxy_type:
                    result["campaigns"].append(name)
                elif "mitre-attack" in galaxy_type or "attack-pattern" in galaxy_type:
                    # Extract MITRE technique ID
                    meta = cluster.get("meta", {})
                    external_id = None
                    for ref in meta.get("external_id", []):
                        if ref.startswith("T"):
                            external_id = ref
                            break
                    if external_id:
                        result["mitre_attack"].append(f"{external_id} - {name}")
                    else:
                        result["mitre_attack"].append(name)

        return result

    async def get_ioc_details(
        self,
        ioc_value: str,
        ioc_type: Optional[IOCType] = None,
    ) -> Optional[NormalizedIOC]:
        """
        Get detailed information about a specific IOC from MISP.

        Args:
            ioc_value: The IOC value to look up.
            ioc_type: The type of IOC.

        Returns:
            NormalizedIOC with details, or None if not found.
        """
        misp = await self._get_client()

        try:
            # Search for attribute by value
            results = misp.search("attributes", value=ioc_value, limit=1)

            if isinstance(results, dict) and "errors" in results:
                return None

            if not results or len(results) == 0:
                return None

            # Get the first matching attribute
            attr_data = results[0]
            attr = attr_data.get("Attribute", attr_data)

            # Get the parent event for context
            event_id = attr.get("event_id")
            event = None
            if event_id:
                event_result = misp.get_event(event_id)
                if event_result and "Event" in event_result:
                    event = event_result["Event"]

            # Build IOC with full context
            threat_level = ThreatLevel.UNKNOWN
            event_tags = []
            galaxies = {"threat_actors": [], "campaigns": [], "mitre_attack": []}
            event_info = ""

            if event:
                threat_level = self._map_threat_level(
                    event.get("threat_level_id"), "misp"
                )
                event_tags = self._extract_tags(event.get("Tag", []))
                galaxies = self._extract_galaxies(event.get("Galaxy", []))
                event_info = event.get("info", "")

            return self._attribute_to_ioc(
                attr,
                event_id=event_id or "",
                event_info=event_info,
                threat_level=threat_level,
                event_tags=event_tags,
                galaxies=galaxies,
            )

        except Exception as e:
            logger.warning(f"Error looking up IOC {ioc_value} in MISP: {e}")
            return None

    async def close(self):
        """Clean up resources."""
        self._misp = None
        self._connected = False
