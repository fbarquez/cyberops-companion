"""Tests for CTI Feed base classes and dataclasses."""
import pytest
from datetime import datetime

from src.integrations.cti_feeds.base import (
    FeedConfig,
    FeedType,
    IOCType,
    NormalizedIOC,
    FeedSyncResult,
    ThreatLevel,
    BaseCTIFeedAdapter,
)


class TestFeedConfig:
    """Tests for FeedConfig dataclass."""

    def test_basic_config(self):
        """Test basic config creation."""
        config = FeedConfig(
            feed_type=FeedType.MISP,
            base_url="https://misp.example.com",
            api_key="test-api-key",
        )

        assert config.feed_type == FeedType.MISP
        assert config.base_url == "https://misp.example.com"
        assert config.api_key == "test-api-key"
        assert config.verify_ssl is True
        assert config.timeout == 60

    def test_config_with_all_options(self):
        """Test config with all options specified."""
        config = FeedConfig(
            feed_type=FeedType.OTX,
            base_url="https://otx.alienvault.com",
            api_key="otx-key",
            verify_ssl=False,
            timeout=120,
            filters={"min_confidence": 0.5},
            extra_config={"region": "us"},
        )

        assert config.verify_ssl is False
        assert config.timeout == 120
        assert config.filters["min_confidence"] == 0.5
        assert config.extra_config["region"] == "us"


class TestNormalizedIOC:
    """Tests for NormalizedIOC dataclass."""

    def test_basic_ioc(self):
        """Test basic IOC creation."""
        ioc = NormalizedIOC(
            value="192.168.1.1",
            type=IOCType.IP_ADDRESS,
            threat_level=ThreatLevel.HIGH,
            confidence=0.85,
            source="misp",
        )

        assert ioc.value == "192.168.1.1"
        assert ioc.type == IOCType.IP_ADDRESS
        assert ioc.threat_level == ThreatLevel.HIGH
        assert ioc.confidence == 0.85
        assert ioc.source == "misp"

    def test_ioc_with_metadata(self):
        """Test IOC with full metadata."""
        now = datetime.utcnow()
        ioc = NormalizedIOC(
            value="evil.domain.com",
            type=IOCType.DOMAIN,
            threat_level=ThreatLevel.CRITICAL,
            confidence=0.95,
            source="virustotal",
            tags=["malware", "c2"],
            categories=["ransomware"],
            related_actors=["APT28"],
            mitre_techniques=["T1071"],
            first_seen=now,
            country="RU",
        )

        assert "malware" in ioc.tags
        assert "c2" in ioc.tags
        assert "ransomware" in ioc.categories
        assert "APT28" in ioc.related_actors
        assert "T1071" in ioc.mitre_techniques
        assert ioc.country == "RU"

    def test_ioc_to_dict(self):
        """Test IOC serialization to dict."""
        ioc = NormalizedIOC(
            value="test.hash",
            type=IOCType.FILE_HASH_SHA256,
            threat_level=ThreatLevel.MEDIUM,
            confidence=0.7,
            source="otx",
            tags=["trojan"],
        )

        result = ioc.to_dict()

        assert result["value"] == "test.hash"
        assert result["type"] == "sha256"
        assert result["threat_level"] == "medium"
        assert result["confidence"] == 0.7
        assert result["source"] == "otx"
        assert "trojan" in result["tags"]


class TestFeedSyncResult:
    """Tests for FeedSyncResult dataclass."""

    def test_successful_sync_result(self):
        """Test successful sync result."""
        result = FeedSyncResult(
            feed_id="feed-123",
            feed_type=FeedType.MISP,
            success=True,
            iocs_fetched=100,
            iocs_new=50,
            iocs_updated=30,
            iocs_skipped=20,
            duration_seconds=45.5,
        )

        assert result.success is True
        assert result.iocs_fetched == 100
        assert result.iocs_new == 50
        assert result.iocs_updated == 30
        assert result.iocs_skipped == 20
        assert result.duration_seconds == 45.5

    def test_failed_sync_result(self):
        """Test failed sync result with errors."""
        result = FeedSyncResult(
            feed_id="feed-456",
            feed_type=FeedType.OTX,
            success=False,
            errors=["Connection timeout", "Rate limit exceeded"],
        )

        assert result.success is False
        assert len(result.errors) == 2
        assert "Connection timeout" in result.errors

    def test_sync_result_to_dict(self):
        """Test sync result serialization."""
        now = datetime.utcnow()
        result = FeedSyncResult(
            feed_id="feed-789",
            feed_type=FeedType.VIRUSTOTAL,
            success=True,
            iocs_fetched=10,
            sync_started_at=now,
            sync_completed_at=now,
        )

        data = result.to_dict()

        assert data["feed_id"] == "feed-789"
        assert data["feed_type"] == "virustotal"
        assert data["success"] is True
        assert data["iocs_fetched"] == 10


class TestIOCTypeDetection:
    """Tests for IOC type detection in BaseCTIFeedAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a minimal adapter for testing."""
        config = FeedConfig(
            feed_type=FeedType.MISP,
            base_url="https://test.com",
            api_key="test",
        )
        # Create a concrete implementation for testing
        class TestAdapter(BaseCTIFeedAdapter):
            feed_type = FeedType.MISP

            async def test_connection(self):
                return True

            async def fetch_iocs(self, since=None, limit=1000):
                return []

            async def get_ioc_details(self, ioc_value, ioc_type=None):
                return None

        return TestAdapter(config)

    def test_detect_ip_address(self, adapter):
        """Test IP address detection."""
        assert adapter._detect_ioc_type("192.168.1.1") == IOCType.IP_ADDRESS
        assert adapter._detect_ioc_type("10.0.0.1") == IOCType.IP_ADDRESS
        assert adapter._detect_ioc_type("255.255.255.255") == IOCType.IP_ADDRESS

    def test_detect_domain(self, adapter):
        """Test domain detection."""
        assert adapter._detect_ioc_type("example.com") == IOCType.DOMAIN
        assert adapter._detect_ioc_type("sub.example.com") == IOCType.DOMAIN
        assert adapter._detect_ioc_type("test.co.uk") == IOCType.DOMAIN

    def test_detect_url(self, adapter):
        """Test URL detection."""
        assert adapter._detect_ioc_type("http://example.com") == IOCType.URL
        assert adapter._detect_ioc_type("https://example.com/path") == IOCType.URL

    def test_detect_md5_hash(self, adapter):
        """Test MD5 hash detection."""
        assert adapter._detect_ioc_type("d41d8cd98f00b204e9800998ecf8427e") == IOCType.FILE_HASH_MD5

    def test_detect_sha1_hash(self, adapter):
        """Test SHA1 hash detection."""
        assert adapter._detect_ioc_type("da39a3ee5e6b4b0d3255bfef95601890afd80709") == IOCType.FILE_HASH_SHA1

    def test_detect_sha256_hash(self, adapter):
        """Test SHA256 hash detection."""
        assert adapter._detect_ioc_type(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ) == IOCType.FILE_HASH_SHA256

    def test_detect_email(self, adapter):
        """Test email detection."""
        assert adapter._detect_ioc_type("user@example.com") == IOCType.EMAIL
        assert adapter._detect_ioc_type("test.user@domain.co.uk") == IOCType.EMAIL

    def test_detect_cve(self, adapter):
        """Test CVE detection."""
        assert adapter._detect_ioc_type("CVE-2021-44228") == IOCType.CVE
        assert adapter._detect_ioc_type("CVE-2024-12345") == IOCType.CVE

    def test_detect_with_type_hint(self, adapter):
        """Test detection with type hint."""
        assert adapter._detect_ioc_type("192.168.1.1", "ip-src") == IOCType.IP_ADDRESS
        assert adapter._detect_ioc_type("test", "domain") == IOCType.DOMAIN
        assert adapter._detect_ioc_type("hash", "md5") == IOCType.FILE_HASH_MD5


class TestThreatLevelMapping:
    """Tests for threat level mapping."""

    @pytest.fixture
    def adapter(self):
        """Create a minimal adapter for testing."""
        config = FeedConfig(
            feed_type=FeedType.MISP,
            base_url="https://test.com",
            api_key="test",
        )

        class TestAdapter(BaseCTIFeedAdapter):
            feed_type = FeedType.MISP

            async def test_connection(self):
                return True

            async def fetch_iocs(self, since=None, limit=1000):
                return []

            async def get_ioc_details(self, ioc_value, ioc_type=None):
                return None

        return TestAdapter(config)

    def test_misp_threat_level(self, adapter):
        """Test MISP threat level mapping."""
        assert adapter._map_threat_level(1, "misp") == ThreatLevel.HIGH
        assert adapter._map_threat_level(2, "misp") == ThreatLevel.MEDIUM
        assert adapter._map_threat_level(3, "misp") == ThreatLevel.LOW
        assert adapter._map_threat_level(4, "misp") == ThreatLevel.UNKNOWN

    def test_virustotal_threat_level(self, adapter):
        """Test VirusTotal threat level mapping."""
        assert adapter._map_threat_level(60, "virustotal") == ThreatLevel.CRITICAL
        assert adapter._map_threat_level(35, "virustotal") == ThreatLevel.HIGH
        assert adapter._map_threat_level(15, "virustotal") == ThreatLevel.MEDIUM
        assert adapter._map_threat_level(5, "virustotal") == ThreatLevel.LOW
        assert adapter._map_threat_level(0, "virustotal") == ThreatLevel.UNKNOWN

    def test_generic_threat_level(self, adapter):
        """Test generic string threat level mapping."""
        assert adapter._map_threat_level("critical", "generic") == ThreatLevel.CRITICAL
        assert adapter._map_threat_level("high", "generic") == ThreatLevel.HIGH
        assert adapter._map_threat_level("medium", "generic") == ThreatLevel.MEDIUM
        assert adapter._map_threat_level("low", "generic") == ThreatLevel.LOW
