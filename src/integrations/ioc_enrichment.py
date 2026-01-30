"""
IOC Auto-Enrichment Module for CyberOps Companion.

Provides automated enrichment of Indicators of Compromise (IOCs) using
multiple threat intelligence sources:
- VirusTotal (hashes, URLs, domains, IPs)
- AbuseIPDB (IP reputation)
- Shodan (host information)
- OTX AlienVault (threat intelligence)
- GreyNoise (IP context)

Supports offline mode with cached/simulated data for training.
"""

import hashlib
import re
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


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
    UNKNOWN = "unknown"


class ThreatLevel(str, Enum):
    """Threat level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CLEAN = "clean"
    UNKNOWN = "unknown"


class EnrichmentSource(str, Enum):
    """Available enrichment sources."""
    VIRUSTOTAL = "virustotal"
    ABUSEIPDB = "abuseipdb"
    SHODAN = "shodan"
    OTX_ALIENVAULT = "otx"
    GREYNOISE = "greynoise"
    MISP = "misp"
    INTERNAL = "internal"


@dataclass
class SourceResult:
    """Result from a single enrichment source."""
    source: EnrichmentSource
    available: bool
    threat_level: ThreatLevel
    confidence: float  # 0.0 to 1.0
    raw_score: Optional[float] = None
    detections: int = 0
    total_engines: int = 0
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    country: Optional[str] = None
    asn: Optional[str] = None
    isp: Optional[str] = None
    related_iocs: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    cached: bool = False


@dataclass
class EnrichmentResult:
    """Aggregated enrichment result for an IOC."""
    ioc_value: str
    ioc_type: IOCType
    enrichment_time: datetime

    # Aggregated assessment
    overall_threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    risk_score: float = 0.0  # 0-100
    confidence: float = 0.0  # 0.0-1.0

    # Source results
    source_results: Dict[EnrichmentSource, SourceResult] = field(default_factory=dict)

    # Aggregated intelligence
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_iocs: List[str] = field(default_factory=list)

    # Context
    first_seen_global: Optional[datetime] = None
    last_seen_global: Optional[datetime] = None
    geographic_info: Dict[str, str] = field(default_factory=dict)

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Metadata
    sources_queried: int = 0
    sources_with_data: int = 0
    is_cached: bool = False


class IOCEnricher:
    """
    IOC Enrichment Engine.

    Queries multiple threat intelligence sources and aggregates results
    into a unified risk assessment.
    """

    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        offline_mode: bool = True,
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize the IOC Enricher.

        Args:
            api_keys: Dictionary of API keys for each source
            offline_mode: If True, use simulated/cached data (for training)
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.api_keys = api_keys or {}
        self.offline_mode = offline_mode
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, Tuple[EnrichmentResult, datetime]] = {}

        # Known malicious indicators for offline mode
        self._known_malicious = self._load_known_malicious()

        # IOC type detection patterns
        self._patterns = {
            IOCType.IP_ADDRESS: re.compile(
                r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            ),
            IOCType.DOMAIN: re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
            ),
            IOCType.URL: re.compile(
                r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE
            ),
            IOCType.FILE_HASH_MD5: re.compile(r'^[a-fA-F0-9]{32}$'),
            IOCType.FILE_HASH_SHA1: re.compile(r'^[a-fA-F0-9]{40}$'),
            IOCType.FILE_HASH_SHA256: re.compile(r'^[a-fA-F0-9]{64}$'),
            IOCType.EMAIL: re.compile(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            ),
            IOCType.CVE: re.compile(r'^CVE-\d{4}-\d{4,}$', re.IGNORECASE),
        }

    def _load_known_malicious(self) -> Dict[str, Dict[str, Any]]:
        """Load known malicious indicators for offline enrichment."""
        return {
            # Known ransomware-related IPs
            "185.220.101.1": {
                "threat_level": ThreatLevel.CRITICAL,
                "categories": ["ransomware", "c2", "tor_exit"],
                "tags": ["lockbit", "tor", "malicious"],
                "country": "DE",
                "asn": "AS24940",
                "detections": 45,
                "total": 70,
            },
            "91.219.236.222": {
                "threat_level": ThreatLevel.HIGH,
                "categories": ["malware", "c2"],
                "tags": ["emotet", "banking_trojan"],
                "country": "RU",
                "asn": "AS202425",
                "detections": 38,
                "total": 70,
            },
            "194.26.192.64": {
                "threat_level": ThreatLevel.HIGH,
                "categories": ["ransomware", "c2"],
                "tags": ["conti", "ryuk"],
                "country": "RU",
                "asn": "AS44477",
                "detections": 42,
                "total": 70,
            },

            # Known malicious domains
            "evil-domain.ru": {
                "threat_level": ThreatLevel.CRITICAL,
                "categories": ["phishing", "malware_distribution"],
                "tags": ["credential_theft", "drive_by"],
                "detections": 55,
                "total": 70,
            },
            "lockbit-blog.onion": {
                "threat_level": ThreatLevel.CRITICAL,
                "categories": ["ransomware", "data_leak"],
                "tags": ["lockbit", "extortion"],
                "detections": 60,
                "total": 70,
            },
            "update-service.xyz": {
                "threat_level": ThreatLevel.HIGH,
                "categories": ["c2", "malware"],
                "tags": ["cobalt_strike", "beacon"],
                "detections": 35,
                "total": 70,
            },

            # Known malicious hashes (SHA256)
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
                "threat_level": ThreatLevel.CLEAN,
                "categories": ["empty_file"],
                "tags": ["benign", "empty"],
                "detections": 0,
                "total": 70,
            },
            "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd": {
                "threat_level": ThreatLevel.CRITICAL,
                "categories": ["ransomware"],
                "tags": ["lockbit3", "encryption"],
                "detections": 62,
                "total": 70,
                "file_name": "lockbit3.exe",
                "file_type": "Win32 EXE",
            },
            "deadbeef12345678901234567890123456789012345678901234567890123456": {
                "threat_level": ThreatLevel.HIGH,
                "categories": ["trojan", "rat"],
                "tags": ["remcos", "keylogger"],
                "detections": 48,
                "total": 70,
                "file_name": "invoice.exe",
                "file_type": "Win32 EXE",
            },

            # Known malicious URLs
            "http://malware-download.com/payload.exe": {
                "threat_level": ThreatLevel.CRITICAL,
                "categories": ["malware_distribution"],
                "tags": ["dropper", "payload"],
                "detections": 58,
                "total": 70,
            },
        }

    def detect_ioc_type(self, value: str) -> IOCType:
        """
        Automatically detect the type of an IOC.

        Args:
            value: The IOC value to classify

        Returns:
            The detected IOCType
        """
        value = value.strip()

        for ioc_type, pattern in self._patterns.items():
            if pattern.match(value):
                return ioc_type

        # Additional heuristics
        if value.startswith("HKEY_") or value.startswith("HKLM\\"):
            return IOCType.REGISTRY_KEY
        if "/" in value and any(value.endswith(ext) for ext in [".exe", ".dll", ".ps1", ".bat"]):
            return IOCType.FILE_PATH
        if value.endswith(".exe") or value.endswith(".dll"):
            return IOCType.PROCESS_NAME

        return IOCType.UNKNOWN

    def enrich(
        self,
        ioc_value: str,
        ioc_type: Optional[IOCType] = None,
        sources: Optional[List[EnrichmentSource]] = None,
    ) -> EnrichmentResult:
        """
        Enrich an IOC with threat intelligence.

        Args:
            ioc_value: The IOC value to enrich
            ioc_type: The type of IOC (auto-detected if not provided)
            sources: Specific sources to query (all applicable if not provided)

        Returns:
            EnrichmentResult with aggregated intelligence
        """
        ioc_value = ioc_value.strip().lower()

        # Check cache first
        cache_key = f"{ioc_value}:{ioc_type}"
        if cache_key in self._cache:
            cached_result, cache_time = self._cache[cache_key]
            if datetime.now() - cache_time < self.cache_ttl:
                cached_result.is_cached = True
                return cached_result

        # Auto-detect type if not provided
        if ioc_type is None:
            ioc_type = self.detect_ioc_type(ioc_value)

        # Determine applicable sources
        if sources is None:
            sources = self._get_applicable_sources(ioc_type)

        # Query each source
        source_results: Dict[EnrichmentSource, SourceResult] = {}

        for source in sources:
            if self.offline_mode:
                result = self._query_offline(ioc_value, ioc_type, source)
            else:
                result = self._query_source(ioc_value, ioc_type, source)
            source_results[source] = result

        # Aggregate results
        enrichment_result = self._aggregate_results(
            ioc_value, ioc_type, source_results
        )

        # Cache result
        self._cache[cache_key] = (enrichment_result, datetime.now())

        return enrichment_result

    def enrich_batch(
        self,
        iocs: List[str],
        sources: Optional[List[EnrichmentSource]] = None,
    ) -> List[EnrichmentResult]:
        """
        Enrich multiple IOCs.

        Args:
            iocs: List of IOC values
            sources: Specific sources to query

        Returns:
            List of EnrichmentResults
        """
        results = []
        for ioc in iocs:
            result = self.enrich(ioc, sources=sources)
            results.append(result)
        return results

    def _get_applicable_sources(self, ioc_type: IOCType) -> List[EnrichmentSource]:
        """Get applicable enrichment sources for an IOC type."""
        source_map = {
            IOCType.IP_ADDRESS: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.ABUSEIPDB,
                EnrichmentSource.SHODAN,
                EnrichmentSource.GREYNOISE,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.DOMAIN: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.URL: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.FILE_HASH_MD5: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.FILE_HASH_SHA1: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.FILE_HASH_SHA256: [
                EnrichmentSource.VIRUSTOTAL,
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.EMAIL: [
                EnrichmentSource.OTX_ALIENVAULT,
            ],
            IOCType.CVE: [
                EnrichmentSource.OTX_ALIENVAULT,
            ],
        }
        return source_map.get(ioc_type, [EnrichmentSource.INTERNAL])

    def _query_offline(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        source: EnrichmentSource,
    ) -> SourceResult:
        """Query using offline/simulated data."""
        # Check known malicious database
        known = self._known_malicious.get(ioc_value)

        if known:
            return SourceResult(
                source=source,
                available=True,
                threat_level=known.get("threat_level", ThreatLevel.UNKNOWN),
                confidence=0.85,
                raw_score=known.get("detections", 0) / known.get("total", 1) * 100,
                detections=known.get("detections", 0),
                total_engines=known.get("total", 70),
                categories=known.get("categories", []),
                tags=known.get("tags", []),
                country=known.get("country"),
                asn=known.get("asn"),
                cached=True,
                raw_data=known,
            )

        # Generate simulated response based on IOC characteristics
        return self._generate_simulated_result(ioc_value, ioc_type, source)

    def _generate_simulated_result(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        source: EnrichmentSource,
    ) -> SourceResult:
        """Generate a simulated result for unknown IOCs."""
        # Use hash of IOC to generate consistent "random" results
        hash_val = int(hashlib.md5(ioc_value.encode()).hexdigest()[:8], 16)

        # Determine if this should appear malicious (for demo purposes)
        # IOCs with certain patterns are more likely to be flagged
        suspicious_indicators = [
            "malware", "evil", "hack", "ransomware", "c2", "bot",
            ".ru", ".cn", ".onion", "temp", "update", "payload"
        ]

        is_suspicious = any(ind in ioc_value.lower() for ind in suspicious_indicators)
        base_score = 60 if is_suspicious else (hash_val % 30)

        if base_score > 70:
            threat_level = ThreatLevel.CRITICAL
        elif base_score > 50:
            threat_level = ThreatLevel.HIGH
        elif base_score > 30:
            threat_level = ThreatLevel.MEDIUM
        elif base_score > 10:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.CLEAN

        detections = int(base_score * 0.7)

        # Generate contextual tags
        tags = []
        if ioc_type == IOCType.IP_ADDRESS:
            if hash_val % 5 == 0:
                tags.append("tor_exit")
            if hash_val % 3 == 0:
                tags.append("vpn")
            if is_suspicious:
                tags.extend(["scanner", "bruteforce"])
        elif ioc_type in [IOCType.FILE_HASH_MD5, IOCType.FILE_HASH_SHA1, IOCType.FILE_HASH_SHA256]:
            if is_suspicious:
                tags.extend(["trojan", "packed"])
        elif ioc_type == IOCType.DOMAIN:
            if is_suspicious:
                tags.extend(["dga", "fast_flux"])

        return SourceResult(
            source=source,
            available=True,
            threat_level=threat_level,
            confidence=0.7 if is_suspicious else 0.5,
            raw_score=float(base_score),
            detections=detections,
            total_engines=70,
            categories=["simulated"],
            tags=tags,
            country=["US", "RU", "CN", "DE", "NL"][hash_val % 5],
            asn=f"AS{hash_val % 100000}",
            cached=True,
        )

    def _query_source(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        source: EnrichmentSource,
    ) -> SourceResult:
        """Query a real threat intelligence source (requires API keys)."""
        api_key = self.api_keys.get(source.value)

        if not api_key:
            return SourceResult(
                source=source,
                available=False,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.0,
                error=f"No API key configured for {source.value}",
            )

        try:
            if source == EnrichmentSource.VIRUSTOTAL:
                return self._query_virustotal(ioc_value, ioc_type, api_key)
            elif source == EnrichmentSource.ABUSEIPDB:
                return self._query_abuseipdb(ioc_value, api_key)
            elif source == EnrichmentSource.SHODAN:
                return self._query_shodan(ioc_value, api_key)
            elif source == EnrichmentSource.GREYNOISE:
                return self._query_greynoise(ioc_value, api_key)
            elif source == EnrichmentSource.OTX_ALIENVAULT:
                return self._query_otx(ioc_value, ioc_type, api_key)
            else:
                return SourceResult(
                    source=source,
                    available=False,
                    threat_level=ThreatLevel.UNKNOWN,
                    confidence=0.0,
                    error=f"Source {source.value} not implemented",
                )
        except Exception as e:
            return SourceResult(
                source=source,
                available=False,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.0,
                error=str(e),
            )

    def _query_virustotal(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        api_key: str,
    ) -> SourceResult:
        """Query VirusTotal API."""
        import requests

        headers = {"x-apikey": api_key}

        # Determine endpoint based on IOC type
        if ioc_type == IOCType.IP_ADDRESS:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc_value}"
        elif ioc_type == IOCType.DOMAIN:
            url = f"https://www.virustotal.com/api/v3/domains/{ioc_value}"
        elif ioc_type in [IOCType.FILE_HASH_MD5, IOCType.FILE_HASH_SHA1, IOCType.FILE_HASH_SHA256]:
            url = f"https://www.virustotal.com/api/v3/files/{ioc_value}"
        elif ioc_type == IOCType.URL:
            import base64
            url_id = base64.urlsafe_b64encode(ioc_value.encode()).decode().strip("=")
            url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        else:
            return SourceResult(
                source=EnrichmentSource.VIRUSTOTAL,
                available=False,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.0,
                error=f"IOC type {ioc_type} not supported by VirusTotal",
            )

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 404:
            return SourceResult(
                source=EnrichmentSource.VIRUSTOTAL,
                available=True,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.3,
                error="Not found in VirusTotal",
            )

        response.raise_for_status()
        data = response.json()

        # Parse response
        attributes = data.get("data", {}).get("attributes", {})
        stats = attributes.get("last_analysis_stats", {})

        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total = sum(stats.values()) if stats else 0

        # Calculate threat level
        if total > 0:
            detection_rate = (malicious + suspicious) / total
            if detection_rate > 0.5:
                threat_level = ThreatLevel.CRITICAL
            elif detection_rate > 0.3:
                threat_level = ThreatLevel.HIGH
            elif detection_rate > 0.1:
                threat_level = ThreatLevel.MEDIUM
            elif detection_rate > 0:
                threat_level = ThreatLevel.LOW
            else:
                threat_level = ThreatLevel.CLEAN
        else:
            threat_level = ThreatLevel.UNKNOWN

        return SourceResult(
            source=EnrichmentSource.VIRUSTOTAL,
            available=True,
            threat_level=threat_level,
            confidence=0.9,
            raw_score=detection_rate * 100 if total > 0 else 0,
            detections=malicious + suspicious,
            total_engines=total,
            categories=list(attributes.get("categories", {}).values()),
            tags=attributes.get("tags", []),
            country=attributes.get("country"),
            asn=str(attributes.get("asn")) if attributes.get("asn") else None,
            raw_data=data,
        )

    def _query_abuseipdb(self, ip: str, api_key: str) -> SourceResult:
        """Query AbuseIPDB API."""
        import requests

        headers = {
            "Key": api_key,
            "Accept": "application/json",
        }
        params = {
            "ipAddress": ip,
            "maxAgeInDays": 90,
            "verbose": True,
        }

        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        abuse_score = data.get("abuseConfidenceScore", 0)

        if abuse_score > 80:
            threat_level = ThreatLevel.CRITICAL
        elif abuse_score > 50:
            threat_level = ThreatLevel.HIGH
        elif abuse_score > 25:
            threat_level = ThreatLevel.MEDIUM
        elif abuse_score > 0:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.CLEAN

        return SourceResult(
            source=EnrichmentSource.ABUSEIPDB,
            available=True,
            threat_level=threat_level,
            confidence=0.85,
            raw_score=float(abuse_score),
            detections=data.get("totalReports", 0),
            total_engines=1,
            categories=data.get("usageType", "").split(",") if data.get("usageType") else [],
            country=data.get("countryCode"),
            isp=data.get("isp"),
            raw_data=data,
        )

    def _query_shodan(self, ip: str, api_key: str) -> SourceResult:
        """Query Shodan API."""
        import requests

        response = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key},
            timeout=30,
        )

        if response.status_code == 404:
            return SourceResult(
                source=EnrichmentSource.SHODAN,
                available=True,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.3,
                error="Not found in Shodan",
            )

        response.raise_for_status()
        data = response.json()

        # Check for vulnerabilities
        vulns = data.get("vulns", [])
        tags = data.get("tags", [])

        if len(vulns) > 10:
            threat_level = ThreatLevel.HIGH
        elif len(vulns) > 0:
            threat_level = ThreatLevel.MEDIUM
        elif "honeypot" in tags:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.CLEAN

        return SourceResult(
            source=EnrichmentSource.SHODAN,
            available=True,
            threat_level=threat_level,
            confidence=0.7,
            tags=tags + vulns[:10],
            country=data.get("country_code"),
            asn=data.get("asn"),
            isp=data.get("isp"),
            raw_data=data,
        )

    def _query_greynoise(self, ip: str, api_key: str) -> SourceResult:
        """Query GreyNoise API."""
        import requests

        headers = {"key": api_key}
        response = requests.get(
            f"https://api.greynoise.io/v3/community/{ip}",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 404:
            return SourceResult(
                source=EnrichmentSource.GREYNOISE,
                available=True,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.3,
            )

        response.raise_for_status()
        data = response.json()

        classification = data.get("classification", "unknown")

        if classification == "malicious":
            threat_level = ThreatLevel.HIGH
        elif classification == "benign":
            threat_level = ThreatLevel.CLEAN
        else:
            threat_level = ThreatLevel.UNKNOWN

        return SourceResult(
            source=EnrichmentSource.GREYNOISE,
            available=True,
            threat_level=threat_level,
            confidence=0.75,
            tags=[data.get("name", "")] if data.get("name") else [],
            raw_data=data,
        )

    def _query_otx(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        api_key: str,
    ) -> SourceResult:
        """Query OTX AlienVault API."""
        import requests

        headers = {"X-OTX-API-KEY": api_key}

        # Determine endpoint
        type_map = {
            IOCType.IP_ADDRESS: f"indicators/IPv4/{ioc_value}/general",
            IOCType.DOMAIN: f"indicators/domain/{ioc_value}/general",
            IOCType.URL: f"indicators/url/{ioc_value}/general",
            IOCType.FILE_HASH_MD5: f"indicators/file/{ioc_value}/general",
            IOCType.FILE_HASH_SHA1: f"indicators/file/{ioc_value}/general",
            IOCType.FILE_HASH_SHA256: f"indicators/file/{ioc_value}/general",
        }

        endpoint = type_map.get(ioc_type)
        if not endpoint:
            return SourceResult(
                source=EnrichmentSource.OTX_ALIENVAULT,
                available=False,
                threat_level=ThreatLevel.UNKNOWN,
                confidence=0.0,
                error=f"IOC type {ioc_type} not supported",
            )

        response = requests.get(
            f"https://otx.alienvault.com/api/v1/{endpoint}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        pulse_count = data.get("pulse_info", {}).get("count", 0)

        if pulse_count > 10:
            threat_level = ThreatLevel.CRITICAL
        elif pulse_count > 5:
            threat_level = ThreatLevel.HIGH
        elif pulse_count > 0:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.CLEAN

        return SourceResult(
            source=EnrichmentSource.OTX_ALIENVAULT,
            available=True,
            threat_level=threat_level,
            confidence=0.8,
            detections=pulse_count,
            country=data.get("country_code"),
            asn=data.get("asn"),
            raw_data=data,
        )

    def _aggregate_results(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        source_results: Dict[EnrichmentSource, SourceResult],
    ) -> EnrichmentResult:
        """Aggregate results from multiple sources into unified assessment."""
        result = EnrichmentResult(
            ioc_value=ioc_value,
            ioc_type=ioc_type,
            enrichment_time=datetime.now(),
            source_results=source_results,
        )

        # Count sources
        result.sources_queried = len(source_results)
        result.sources_with_data = sum(
            1 for r in source_results.values() if r.available
        )

        # Aggregate threat levels with weighted voting
        threat_weights = {
            ThreatLevel.CRITICAL: 100,
            ThreatLevel.HIGH: 75,
            ThreatLevel.MEDIUM: 50,
            ThreatLevel.LOW: 25,
            ThreatLevel.CLEAN: 0,
            ThreatLevel.UNKNOWN: -1,
        }

        weighted_scores = []
        total_confidence = 0.0

        for source_result in source_results.values():
            if source_result.available and source_result.threat_level != ThreatLevel.UNKNOWN:
                weight = threat_weights[source_result.threat_level]
                weighted_scores.append(weight * source_result.confidence)
                total_confidence += source_result.confidence

        if weighted_scores and total_confidence > 0:
            avg_score = sum(weighted_scores) / total_confidence
            result.risk_score = avg_score
            result.confidence = min(total_confidence / len(weighted_scores), 1.0)

            # Determine overall threat level
            if avg_score >= 80:
                result.overall_threat_level = ThreatLevel.CRITICAL
            elif avg_score >= 60:
                result.overall_threat_level = ThreatLevel.HIGH
            elif avg_score >= 40:
                result.overall_threat_level = ThreatLevel.MEDIUM
            elif avg_score >= 10:
                result.overall_threat_level = ThreatLevel.LOW
            else:
                result.overall_threat_level = ThreatLevel.CLEAN

        # Aggregate categories and tags
        all_categories = set()
        all_tags = set()
        all_related = set()

        for source_result in source_results.values():
            all_categories.update(source_result.categories)
            all_tags.update(source_result.tags)
            all_related.update(source_result.related_iocs)

        result.categories = list(all_categories)
        result.tags = list(all_tags)
        result.related_iocs = list(all_related)

        # Aggregate geographic info
        for source_result in source_results.values():
            if source_result.country and "country" not in result.geographic_info:
                result.geographic_info["country"] = source_result.country
            if source_result.asn and "asn" not in result.geographic_info:
                result.geographic_info["asn"] = source_result.asn
            if source_result.isp and "isp" not in result.geographic_info:
                result.geographic_info["isp"] = source_result.isp

        # Generate recommendations
        result.recommended_actions = self._generate_recommendations(result)
        result.mitre_techniques = self._map_to_mitre(result)

        return result

    def _generate_recommendations(self, result: EnrichmentResult) -> List[str]:
        """Generate recommended actions based on enrichment results."""
        actions = []

        if result.overall_threat_level == ThreatLevel.CRITICAL:
            actions.extend([
                "IMMEDIATE: Block this IOC at all network boundaries",
                "Isolate any systems that communicated with this IOC",
                "Initiate full forensic investigation",
                "Notify incident response team immediately",
                "Check for lateral movement from affected systems",
            ])
        elif result.overall_threat_level == ThreatLevel.HIGH:
            actions.extend([
                "Block this IOC at perimeter firewall",
                "Review logs for any historical communication",
                "Scan endpoints for related indicators",
                "Consider adding to threat hunting queries",
            ])
        elif result.overall_threat_level == ThreatLevel.MEDIUM:
            actions.extend([
                "Add to watchlist for monitoring",
                "Review recent connections to this IOC",
                "Consider blocking if no legitimate business need",
            ])
        elif result.overall_threat_level == ThreatLevel.LOW:
            actions.extend([
                "Monitor for suspicious activity",
                "Document in threat intelligence database",
            ])
        else:
            actions.append("No immediate action required - continue monitoring")

        # Type-specific recommendations
        if result.ioc_type == IOCType.IP_ADDRESS:
            if "tor_exit" in result.tags:
                actions.append("Review Tor usage policy - block if not business-required")
            if "vpn" in result.tags:
                actions.append("Verify if VPN traffic is authorized")
        elif result.ioc_type in [IOCType.FILE_HASH_MD5, IOCType.FILE_HASH_SHA1, IOCType.FILE_HASH_SHA256]:
            actions.append("Search for this hash across all endpoints")
            if result.overall_threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                actions.append("Add hash to EDR block list immediately")
        elif result.ioc_type == IOCType.DOMAIN:
            actions.append("Check DNS logs for resolution attempts")
            if result.overall_threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                actions.append("Sinkhole domain in DNS if possible")

        return actions

    def _map_to_mitre(self, result: EnrichmentResult) -> List[str]:
        """Map enrichment results to MITRE ATT&CK techniques."""
        techniques = []

        tag_to_technique = {
            "c2": ["T1071 - Application Layer Protocol", "T1095 - Non-Application Layer Protocol"],
            "ransomware": ["T1486 - Data Encrypted for Impact", "T1490 - Inhibit System Recovery"],
            "phishing": ["T1566 - Phishing", "T1598 - Phishing for Information"],
            "credential_theft": ["T1003 - OS Credential Dumping", "T1555 - Credentials from Password Stores"],
            "trojan": ["T1204 - User Execution", "T1036 - Masquerading"],
            "rat": ["T1219 - Remote Access Software", "T1105 - Ingress Tool Transfer"],
            "keylogger": ["T1056 - Input Capture"],
            "dropper": ["T1105 - Ingress Tool Transfer", "T1059 - Command and Scripting Interpreter"],
            "tor": ["T1090 - Proxy", "T1573 - Encrypted Channel"],
            "cobalt_strike": ["T1071.001 - Web Protocols", "T1059.001 - PowerShell"],
            "emotet": ["T1566.001 - Spearphishing Attachment", "T1055 - Process Injection"],
            "bruteforce": ["T1110 - Brute Force"],
            "scanner": ["T1595 - Active Scanning"],
            "dga": ["T1568.002 - Domain Generation Algorithms"],
        }

        for tag in result.tags:
            tag_lower = tag.lower()
            for key, techs in tag_to_technique.items():
                if key in tag_lower:
                    techniques.extend(techs)

        # Deduplicate
        return list(set(techniques))

    def get_enrichment_summary(self, result: EnrichmentResult) -> Dict[str, Any]:
        """Get a summary of enrichment results for display."""
        return {
            "ioc": result.ioc_value,
            "type": result.ioc_type.value,
            "threat_level": result.overall_threat_level.value,
            "risk_score": round(result.risk_score, 1),
            "confidence": f"{result.confidence * 100:.0f}%",
            "sources_checked": result.sources_queried,
            "sources_with_data": result.sources_with_data,
            "categories": result.categories,
            "tags": result.tags[:10],  # Limit for display
            "location": result.geographic_info,
            "recommendations": result.recommended_actions[:5],
            "mitre_techniques": result.mitre_techniques[:5],
            "related_iocs": result.related_iocs[:5],
        }

    def export_results(
        self,
        results: List[EnrichmentResult],
        format: str = "json",
    ) -> str:
        """Export enrichment results."""
        if format == "json":
            return self._export_json(results)
        elif format == "csv":
            return self._export_csv(results)
        elif format == "markdown":
            return self._export_markdown(results)
        elif format == "stix":
            return self._export_stix(results)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, results: List[EnrichmentResult]) -> str:
        """Export as JSON."""
        export_data = []
        for result in results:
            export_data.append({
                "ioc": result.ioc_value,
                "type": result.ioc_type.value,
                "enrichment_time": result.enrichment_time.isoformat(),
                "threat_level": result.overall_threat_level.value,
                "risk_score": result.risk_score,
                "confidence": result.confidence,
                "categories": result.categories,
                "tags": result.tags,
                "geographic_info": result.geographic_info,
                "recommended_actions": result.recommended_actions,
                "mitre_techniques": result.mitre_techniques,
                "sources": {
                    src.value: {
                        "available": sr.available,
                        "threat_level": sr.threat_level.value,
                        "detections": sr.detections,
                        "total_engines": sr.total_engines,
                    }
                    for src, sr in result.source_results.items()
                },
            })
        return json.dumps(export_data, indent=2)

    def _export_csv(self, results: List[EnrichmentResult]) -> str:
        """Export as CSV."""
        lines = ["IOC,Type,Threat Level,Risk Score,Confidence,Categories,Tags,Country"]
        for result in results:
            lines.append(
                f'"{result.ioc_value}",'
                f'{result.ioc_type.value},'
                f'{result.overall_threat_level.value},'
                f'{result.risk_score:.1f},'
                f'{result.confidence:.2f},'
                f'"{";".join(result.categories)}",'
                f'"{";".join(result.tags)}",'
                f'{result.geographic_info.get("country", "")}'
            )
        return "\n".join(lines)

    def _export_markdown(self, results: List[EnrichmentResult]) -> str:
        """Export as Markdown report."""
        lines = [
            "# IOC Enrichment Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nTotal IOCs analyzed: {len(results)}",
            "\n---\n",
        ]

        # Summary table
        lines.append("## Summary\n")
        lines.append("| IOC | Type | Threat Level | Risk Score |")
        lines.append("|-----|------|--------------|------------|")

        for result in results:
            threat_emoji = {
                ThreatLevel.CRITICAL: "🔴",
                ThreatLevel.HIGH: "🟠",
                ThreatLevel.MEDIUM: "🟡",
                ThreatLevel.LOW: "🟢",
                ThreatLevel.CLEAN: "⚪",
                ThreatLevel.UNKNOWN: "❓",
            }
            lines.append(
                f"| `{result.ioc_value}` | {result.ioc_type.value} | "
                f"{threat_emoji.get(result.overall_threat_level, '')} {result.overall_threat_level.value} | "
                f"{result.risk_score:.1f} |"
            )

        lines.append("\n---\n")

        # Detailed results
        lines.append("## Detailed Results\n")

        for result in results:
            lines.append(f"### {result.ioc_value}\n")
            lines.append(f"- **Type:** {result.ioc_type.value}")
            lines.append(f"- **Threat Level:** {result.overall_threat_level.value}")
            lines.append(f"- **Risk Score:** {result.risk_score:.1f}/100")
            lines.append(f"- **Confidence:** {result.confidence * 100:.0f}%")

            if result.categories:
                lines.append(f"- **Categories:** {', '.join(result.categories)}")
            if result.tags:
                lines.append(f"- **Tags:** {', '.join(result.tags[:10])}")
            if result.geographic_info:
                geo = ", ".join(f"{k}: {v}" for k, v in result.geographic_info.items())
                lines.append(f"- **Location:** {geo}")

            if result.recommended_actions:
                lines.append("\n**Recommended Actions:**")
                for action in result.recommended_actions[:5]:
                    lines.append(f"- {action}")

            if result.mitre_techniques:
                lines.append("\n**MITRE ATT&CK Techniques:**")
                for tech in result.mitre_techniques[:5]:
                    lines.append(f"- {tech}")

            lines.append("\n")

        return "\n".join(lines)

    def _export_stix(self, results: List[EnrichmentResult]) -> str:
        """Export as STIX 2.1 bundle (simplified)."""
        stix_objects = []

        for result in results:
            # Map IOC type to STIX pattern
            pattern_map = {
                IOCType.IP_ADDRESS: f"[ipv4-addr:value = '{result.ioc_value}']",
                IOCType.DOMAIN: f"[domain-name:value = '{result.ioc_value}']",
                IOCType.URL: f"[url:value = '{result.ioc_value}']",
                IOCType.FILE_HASH_MD5: f"[file:hashes.MD5 = '{result.ioc_value}']",
                IOCType.FILE_HASH_SHA1: f"[file:hashes.'SHA-1' = '{result.ioc_value}']",
                IOCType.FILE_HASH_SHA256: f"[file:hashes.'SHA-256' = '{result.ioc_value}']",
                IOCType.EMAIL: f"[email-addr:value = '{result.ioc_value}']",
            }

            pattern = pattern_map.get(result.ioc_type, f"[x-custom:value = '{result.ioc_value}']")

            indicator = {
                "type": "indicator",
                "spec_version": "2.1",
                "id": f"indicator--{hashlib.sha256(result.ioc_value.encode()).hexdigest()[:36]}",
                "created": result.enrichment_time.isoformat() + "Z",
                "modified": result.enrichment_time.isoformat() + "Z",
                "name": f"IOC: {result.ioc_value}",
                "description": f"Threat Level: {result.overall_threat_level.value}, Risk Score: {result.risk_score:.1f}",
                "pattern": pattern,
                "pattern_type": "stix",
                "valid_from": result.enrichment_time.isoformat() + "Z",
                "labels": result.tags[:5] if result.tags else ["unknown"],
                "confidence": int(result.confidence * 100),
            }
            stix_objects.append(indicator)

        bundle = {
            "type": "bundle",
            "id": f"bundle--{hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:36]}",
            "objects": stix_objects,
        }

        return json.dumps(bundle, indent=2)
