"""
Base classes and dataclasses for CTI Feed integrations.

Provides the abstract interface for all threat intelligence feed adapters.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.integrations import Integration


class FeedType(str, Enum):
    """Supported CTI feed types."""

    MISP = "misp"
    OTX = "otx"
    VIRUSTOTAL = "virustotal"
    OPENCTI = "opencti"
    TAXII = "taxii"


class IOCType(str, Enum):
    """Types of Indicators of Compromise."""

    IP_ADDRESS = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH_MD5 = "md5"
    FILE_HASH_SHA1 = "sha1"
    FILE_HASH_SHA256 = "sha256"
    EMAIL = "email"
    CVE = "cve"
    REGISTRY_KEY = "registry"
    FILE_PATH = "file_path"
    PROCESS_NAME = "process"
    HOSTNAME = "hostname"
    MUTEX = "mutex"
    USER_AGENT = "user_agent"
    UNKNOWN = "unknown"


class ThreatLevel(str, Enum):
    """Threat level classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class FeedConfig:
    """Configuration for connecting to a CTI feed."""

    feed_type: FeedType
    base_url: str = ""
    api_key: str = ""
    verify_ssl: bool = True
    timeout: int = 60
    filters: Dict[str, Any] = field(default_factory=dict)
    extra_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_integration(cls, integration: "Integration") -> "FeedConfig":
        """Create FeedConfig from an Integration model instance."""
        from src.models.integrations import IntegrationType

        # Map IntegrationType to FeedType
        type_map = {
            IntegrationType.MISP: FeedType.MISP,
            IntegrationType.OTX: FeedType.OTX,
            IntegrationType.VIRUSTOTAL: FeedType.VIRUSTOTAL,
            IntegrationType.OPENCTI: FeedType.OPENCTI,
        }

        feed_type = type_map.get(integration.integration_type)
        if not feed_type:
            raise ValueError(
                f"Unsupported integration type for CTI feed: {integration.integration_type}"
            )

        config = integration.config or {}
        filters = integration.sync_filters or {}

        return cls(
            feed_type=feed_type,
            base_url=integration.base_url or "",
            api_key=integration.api_key or "",
            verify_ssl=config.get("verify_ssl", True),
            timeout=config.get("timeout_seconds", 60),
            filters=filters,
            extra_config=config,
        )

    @classmethod
    def from_threat_feed(cls, feed) -> "FeedConfig":
        """Create FeedConfig from a ThreatFeed model instance."""
        feed_type_map = {
            "misp": FeedType.MISP,
            "otx": FeedType.OTX,
            "virustotal": FeedType.VIRUSTOTAL,
            "opencti": FeedType.OPENCTI,
            "taxii": FeedType.TAXII,
        }

        feed_type = feed_type_map.get(feed.feed_type.lower())
        if not feed_type:
            raise ValueError(f"Unsupported feed type: {feed.feed_type}")

        auth_config = feed.auth_config or {}

        return cls(
            feed_type=feed_type,
            base_url=feed.url or "",
            api_key=feed.api_key or "",
            verify_ssl=auth_config.get("verify_ssl", True),
            timeout=auth_config.get("timeout_seconds", 60),
            filters={
                "ioc_types": feed.ioc_types or [],
                "min_confidence": feed.min_confidence,
            },
            extra_config=auth_config,
        )


@dataclass
class NormalizedIOC:
    """Normalized IOC from any CTI feed source."""

    value: str
    type: IOCType
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    confidence: float = 0.0
    source: str = ""
    source_ref: str = ""
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    description: str = ""
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    related_actors: List[str] = field(default_factory=list)
    related_campaigns: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    country: Optional[str] = None
    asn: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "value": self.value,
            "type": self.type.value,
            "threat_level": self.threat_level.value,
            "confidence": self.confidence,
            "source": self.source,
            "source_ref": self.source_ref,
            "tags": self.tags,
            "categories": self.categories,
            "description": self.description,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "related_actors": self.related_actors,
            "related_campaigns": self.related_campaigns,
            "mitre_techniques": self.mitre_techniques,
            "country": self.country,
            "asn": self.asn,
        }


@dataclass
class FeedSyncResult:
    """Result of a feed synchronization operation."""

    feed_id: str
    feed_type: FeedType
    success: bool
    iocs_fetched: int = 0
    iocs_new: int = 0
    iocs_updated: int = 0
    iocs_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    sync_started_at: Optional[datetime] = None
    sync_completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/response."""
        return {
            "feed_id": self.feed_id,
            "feed_type": self.feed_type.value,
            "success": self.success,
            "iocs_fetched": self.iocs_fetched,
            "iocs_new": self.iocs_new,
            "iocs_updated": self.iocs_updated,
            "iocs_skipped": self.iocs_skipped,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
            "sync_started_at": self.sync_started_at.isoformat() if self.sync_started_at else None,
            "sync_completed_at": self.sync_completed_at.isoformat() if self.sync_completed_at else None,
        }


class BaseCTIFeedAdapter(ABC):
    """Abstract base class for CTI feed adapters."""

    feed_type: FeedType

    def __init__(self, config: FeedConfig):
        """Initialize the adapter with configuration."""
        self.config = config
        self._session = None

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the CTI feed.

        Returns:
            True if connection is successful, raises exception otherwise.
        """
        pass

    @abstractmethod
    async def fetch_iocs(
        self,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[NormalizedIOC]:
        """
        Fetch IOCs from the feed.

        Args:
            since: Only fetch IOCs modified after this datetime.
            limit: Maximum number of IOCs to fetch.

        Returns:
            List of normalized IOCs.
        """
        pass

    @abstractmethod
    async def get_ioc_details(
        self,
        ioc_value: str,
        ioc_type: Optional[IOCType] = None,
    ) -> Optional[NormalizedIOC]:
        """
        Get detailed information about a specific IOC.

        Args:
            ioc_value: The IOC value to look up.
            ioc_type: The type of IOC (for disambiguation).

        Returns:
            NormalizedIOC with details, or None if not found.
        """
        pass

    async def close(self):
        """Clean up resources. Override if needed."""
        if self._session:
            await self._session.close()
            self._session = None

    def _map_threat_level(self, value: Any, source_type: str = "generic") -> ThreatLevel:
        """
        Map a source-specific threat level to normalized ThreatLevel.

        Args:
            value: The source threat level value.
            source_type: Type of source (misp, otx, virustotal).

        Returns:
            Normalized ThreatLevel.
        """
        if source_type == "misp":
            # MISP threat levels: 1 (High), 2 (Medium), 3 (Low), 4 (Undefined)
            level_map = {
                1: ThreatLevel.HIGH,
                "1": ThreatLevel.HIGH,
                2: ThreatLevel.MEDIUM,
                "2": ThreatLevel.MEDIUM,
                3: ThreatLevel.LOW,
                "3": ThreatLevel.LOW,
            }
            return level_map.get(value, ThreatLevel.UNKNOWN)

        elif source_type == "virustotal":
            # VirusTotal: use detection ratio
            if isinstance(value, (int, float)):
                if value >= 50:
                    return ThreatLevel.CRITICAL
                elif value >= 30:
                    return ThreatLevel.HIGH
                elif value >= 10:
                    return ThreatLevel.MEDIUM
                elif value >= 1:
                    return ThreatLevel.LOW
                return ThreatLevel.UNKNOWN

        elif source_type == "otx":
            # OTX pulse indicators have adversary field
            if value in ["high", "critical"]:
                return ThreatLevel.HIGH
            elif value == "medium":
                return ThreatLevel.MEDIUM
            elif value == "low":
                return ThreatLevel.LOW

        # Generic string mapping
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ["critical", "severe"]:
                return ThreatLevel.CRITICAL
            elif value_lower in ["high", "danger"]:
                return ThreatLevel.HIGH
            elif value_lower in ["medium", "moderate"]:
                return ThreatLevel.MEDIUM
            elif value_lower in ["low", "minor"]:
                return ThreatLevel.LOW

        return ThreatLevel.UNKNOWN

    def _detect_ioc_type(self, value: str, type_hint: str = None) -> IOCType:
        """
        Detect the IOC type from its value or type hint.

        Args:
            value: The IOC value.
            type_hint: Optional hint about the type.

        Returns:
            Detected IOCType.
        """
        import re

        value = value.strip()

        # Type hint mapping
        if type_hint:
            hint_lower = type_hint.lower()
            hint_map = {
                "ip-src": IOCType.IP_ADDRESS,
                "ip-dst": IOCType.IP_ADDRESS,
                "ip": IOCType.IP_ADDRESS,
                "ipv4": IOCType.IP_ADDRESS,
                "ipv4-addr": IOCType.IP_ADDRESS,
                "domain": IOCType.DOMAIN,
                "hostname": IOCType.HOSTNAME,
                "url": IOCType.URL,
                "uri": IOCType.URL,
                "md5": IOCType.FILE_HASH_MD5,
                "sha1": IOCType.FILE_HASH_SHA1,
                "sha256": IOCType.FILE_HASH_SHA256,
                "sha-256": IOCType.FILE_HASH_SHA256,
                "email": IOCType.EMAIL,
                "email-src": IOCType.EMAIL,
                "email-dst": IOCType.EMAIL,
                "cve": IOCType.CVE,
                "vulnerability": IOCType.CVE,
                "regkey": IOCType.REGISTRY_KEY,
                "filename": IOCType.FILE_PATH,
                "filepath": IOCType.FILE_PATH,
                "mutex": IOCType.MUTEX,
                "user-agent": IOCType.USER_AGENT,
            }
            if hint_lower in hint_map:
                return hint_map[hint_lower]

        # Pattern-based detection
        patterns = {
            IOCType.IP_ADDRESS: re.compile(
                r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            ),
            IOCType.FILE_HASH_MD5: re.compile(r'^[a-fA-F0-9]{32}$'),
            IOCType.FILE_HASH_SHA1: re.compile(r'^[a-fA-F0-9]{40}$'),
            IOCType.FILE_HASH_SHA256: re.compile(r'^[a-fA-F0-9]{64}$'),
            IOCType.EMAIL: re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            IOCType.CVE: re.compile(r'^CVE-\d{4}-\d{4,}$', re.IGNORECASE),
            IOCType.URL: re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE),
            IOCType.DOMAIN: re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
            ),
        }

        for ioc_type, pattern in patterns.items():
            if pattern.match(value):
                return ioc_type

        # Additional heuristics
        if value.startswith("HKEY_") or value.startswith("HKLM\\"):
            return IOCType.REGISTRY_KEY
        if "\\" in value and any(
            value.lower().endswith(ext) for ext in [".exe", ".dll", ".ps1", ".bat"]
        ):
            return IOCType.FILE_PATH

        return IOCType.UNKNOWN
