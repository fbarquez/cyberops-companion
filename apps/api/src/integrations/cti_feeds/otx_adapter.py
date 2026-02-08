"""
AlienVault OTX (Open Threat Exchange) Feed Adapter.

Integrates with OTX to fetch threat intelligence:
- Subscribed pulses with indicators
- IOC enrichment with pulse context
- Tags and targeted countries/industries
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


class OTXAdapter(BaseCTIFeedAdapter):
    """
    Adapter for AlienVault OTX threat intelligence platform.

    Uses the OTXv2 library to interact with OTX API.
    """

    feed_type = FeedType.OTX

    # OTX indicator type to IOCType mapping
    OTX_TYPE_MAP = {
        "IPv4": IOCType.IP_ADDRESS,
        "IPv6": IOCType.IP_ADDRESS,
        "domain": IOCType.DOMAIN,
        "hostname": IOCType.HOSTNAME,
        "URL": IOCType.URL,
        "URI": IOCType.URL,
        "FileHash-MD5": IOCType.FILE_HASH_MD5,
        "FileHash-SHA1": IOCType.FILE_HASH_SHA1,
        "FileHash-SHA256": IOCType.FILE_HASH_SHA256,
        "email": IOCType.EMAIL,
        "CVE": IOCType.CVE,
        "Mutex": IOCType.MUTEX,
        "FilePath": IOCType.FILE_PATH,
    }

    def __init__(self, config: FeedConfig):
        super().__init__(config)
        self._otx = None
        self._connected = False

    async def _get_client(self):
        """Get or create the OTX client."""
        if self._otx is None:
            try:
                from OTXv2 import OTXv2
            except ImportError:
                raise FeedConnectionError(
                    "OTXv2 library not installed. Run: pip install OTXv2",
                    feed_type="otx",
                )

            try:
                # OTX uses default server, API key for auth
                self._otx = OTXv2(
                    self.config.api_key,
                    server=self.config.base_url or "https://otx.alienvault.com",
                )
                self._connected = True
            except Exception as e:
                raise FeedConnectionError(
                    f"Failed to connect to OTX: {str(e)}",
                    feed_type="otx",
                )

        return self._otx

    async def test_connection(self) -> bool:
        """Test connection to OTX."""
        try:
            otx = await self._get_client()
            # Get user info to verify API key
            user = otx.get_my_user()
            if not user or "username" not in user:
                raise FeedAuthError(
                    "OTX authentication failed: Invalid API key",
                    feed_type="otx",
                )
            logger.info(f"Connected to OTX as: {user.get('username', 'unknown')}")
            return True
        except FeedAuthError:
            raise
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise FeedAuthError(
                    "OTX authentication failed: Invalid API key",
                    feed_type="otx",
                )
            raise FeedConnectionError(
                f"OTX connection test failed: {str(e)}",
                feed_type="otx",
            )

    async def fetch_iocs(
        self,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[NormalizedIOC]:
        """
        Fetch IOCs from subscribed OTX pulses.

        Args:
            since: Only fetch pulses modified after this datetime.
            limit: Maximum number of IOCs to fetch.

        Returns:
            List of normalized IOCs.
        """
        otx = await self._get_client()
        normalized_iocs: List[NormalizedIOC] = []

        try:
            # Get subscribed pulses
            if since:
                mtime = since.strftime("%Y-%m-%dT%H:%M:%S")
                pulses = otx.getsince(mtime, limit=100)
            else:
                pulses = otx.getall(limit=100)

            if not pulses:
                return []

            # Process each pulse
            for pulse in pulses:
                if len(normalized_iocs) >= limit:
                    break

                pulse_iocs = self._process_pulse(pulse)

                # Apply type filter if configured
                type_filter = self.config.filters.get("ioc_types", [])
                if type_filter:
                    pulse_iocs = [
                        ioc for ioc in pulse_iocs
                        if ioc.type.value in type_filter
                    ]

                normalized_iocs.extend(pulse_iocs)

            logger.info(f"Fetched {len(normalized_iocs)} IOCs from OTX")
            return normalized_iocs[:limit]

        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                raise FeedRateLimitError(
                    "OTX rate limit exceeded",
                    feed_type="otx",
                    retry_after=60,
                )
            raise FeedParseError(
                f"Error fetching IOCs from OTX: {str(e)}",
                feed_type="otx",
            )

    def _process_pulse(self, pulse: Dict[str, Any]) -> List[NormalizedIOC]:
        """Process an OTX pulse and extract IOCs."""
        iocs = []

        pulse_id = pulse.get("id", "")
        pulse_name = pulse.get("name", "")
        pulse_description = pulse.get("description", "")
        created = pulse.get("created")
        modified = pulse.get("modified")

        # Extract pulse metadata
        tags = pulse.get("tags", [])
        targeted_countries = pulse.get("targeted_countries", [])
        industries = pulse.get("industries", [])
        adversary = pulse.get("adversary")
        attack_ids = pulse.get("attack_ids", [])

        # Parse MITRE ATT&CK IDs
        mitre_techniques = []
        for attack_id in attack_ids:
            if isinstance(attack_id, dict):
                tech_id = attack_id.get("id", "")
                tech_name = attack_id.get("name", "")
                if tech_id:
                    mitre_techniques.append(f"{tech_id} - {tech_name}")
            elif isinstance(attack_id, str):
                mitre_techniques.append(attack_id)

        # Determine threat level from adversary
        threat_level = ThreatLevel.MEDIUM  # Default for OTX
        if adversary:
            # Known APT groups are high threat
            if any(
                apt in adversary.lower()
                for apt in ["apt", "lazarus", "cozy bear", "fancy bear"]
            ):
                threat_level = ThreatLevel.HIGH

        # Parse timestamps
        first_seen = None
        if created:
            try:
                first_seen = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        last_seen = None
        if modified:
            try:
                last_seen = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Process indicators
        indicators = pulse.get("indicators", [])
        for indicator in indicators:
            indicator_type = indicator.get("type", "")
            indicator_value = indicator.get("indicator", "").strip()

            if not indicator_value:
                continue

            ioc_type = self.OTX_TYPE_MAP.get(indicator_type)
            if not ioc_type:
                ioc_type = self._detect_ioc_type(indicator_value, indicator_type)

            if ioc_type == IOCType.UNKNOWN:
                continue

            # Build categories
            categories = []
            if industries:
                categories.extend(industries[:3])
            if targeted_countries:
                categories.append(f"targets:{','.join(targeted_countries[:3])}")

            # Related actors from adversary field
            related_actors = [adversary] if adversary else []

            ioc = NormalizedIOC(
                value=indicator_value,
                type=ioc_type,
                threat_level=threat_level,
                confidence=0.7,
                source="otx",
                source_ref=f"pulse:{pulse_id}",
                tags=tags[:10],
                categories=categories,
                description=f"{pulse_name}: {indicator.get('description', pulse_description[:200])}",
                first_seen=first_seen,
                last_seen=last_seen,
                related_actors=related_actors,
                related_campaigns=[],
                mitre_techniques=mitre_techniques,
                raw_data={
                    "pulse_id": pulse_id,
                    "pulse_name": pulse_name,
                    "indicator_type": indicator_type,
                    "adversary": adversary,
                    "targeted_countries": targeted_countries,
                },
            )
            iocs.append(ioc)

        return iocs

    async def get_ioc_details(
        self,
        ioc_value: str,
        ioc_type: Optional[IOCType] = None,
    ) -> Optional[NormalizedIOC]:
        """
        Get detailed information about a specific IOC from OTX.

        Args:
            ioc_value: The IOC value to look up.
            ioc_type: The type of IOC.

        Returns:
            NormalizedIOC with details, or None if not found.
        """
        otx = await self._get_client()

        try:
            # Determine OTX indicator type for lookup
            if ioc_type:
                otx_type = self._ioc_type_to_otx_type(ioc_type)
            else:
                detected_type = self._detect_ioc_type(ioc_value)
                otx_type = self._ioc_type_to_otx_type(detected_type)
                ioc_type = detected_type

            if not otx_type:
                return None

            # Get indicator details
            details = otx.get_indicator_details_full(otx_type, ioc_value)

            if not details:
                return None

            # Extract general section
            general = details.get("general", {})
            if not general:
                return None

            # Aggregate data from all sections
            pulse_info = general.get("pulse_info", {})
            pulses = pulse_info.get("pulses", [])

            # Collect tags, countries, and techniques from all pulses
            all_tags = set()
            all_actors = set()
            all_techniques = set()
            all_countries = set()

            for pulse in pulses[:10]:  # Limit to first 10 pulses
                all_tags.update(pulse.get("tags", []))
                if pulse.get("adversary"):
                    all_actors.add(pulse["adversary"])
                for attack_id in pulse.get("attack_ids", []):
                    if isinstance(attack_id, dict):
                        tech_id = attack_id.get("id", "")
                        if tech_id:
                            all_techniques.add(tech_id)
                all_countries.update(pulse.get("targeted_countries", []))

            # Determine threat level from pulse count and context
            pulse_count = pulse_info.get("count", 0)
            if pulse_count > 10:
                threat_level = ThreatLevel.HIGH
            elif pulse_count > 5:
                threat_level = ThreatLevel.MEDIUM
            elif pulse_count > 0:
                threat_level = ThreatLevel.LOW
            else:
                threat_level = ThreatLevel.UNKNOWN

            # Get geographic info for IPs
            geo_data = details.get("geo", {})
            country = geo_data.get("country_code")
            asn = geo_data.get("asn")

            return NormalizedIOC(
                value=ioc_value,
                type=ioc_type,
                threat_level=threat_level,
                confidence=min(0.9, 0.5 + (pulse_count * 0.05)),
                source="otx",
                source_ref=f"indicator:{ioc_value}",
                tags=list(all_tags)[:15],
                categories=[f"pulses:{pulse_count}"],
                description=f"Found in {pulse_count} OTX pulses",
                first_seen=None,
                last_seen=None,
                related_actors=list(all_actors),
                related_campaigns=[],
                mitre_techniques=list(all_techniques),
                country=country,
                asn=asn,
                raw_data={
                    "pulse_count": pulse_count,
                    "targeted_countries": list(all_countries),
                    "geo": geo_data,
                },
            )

        except Exception as e:
            if "429" in str(e):
                raise FeedRateLimitError(
                    "OTX rate limit exceeded",
                    feed_type="otx",
                    retry_after=60,
                )
            logger.warning(f"Error looking up IOC {ioc_value} in OTX: {e}")
            return None

    def _ioc_type_to_otx_type(self, ioc_type: IOCType) -> Optional[str]:
        """Convert IOCType to OTX indicator type for API calls."""
        type_map = {
            IOCType.IP_ADDRESS: "IPv4",
            IOCType.DOMAIN: "domain",
            IOCType.HOSTNAME: "hostname",
            IOCType.URL: "url",
            IOCType.FILE_HASH_MD5: "file",
            IOCType.FILE_HASH_SHA1: "file",
            IOCType.FILE_HASH_SHA256: "file",
            IOCType.CVE: "cve",
        }
        return type_map.get(ioc_type)

    async def close(self):
        """Clean up resources."""
        self._otx = None
        self._connected = False
