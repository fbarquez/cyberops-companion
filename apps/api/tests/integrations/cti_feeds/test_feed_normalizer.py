"""Tests for feed normalizer utilities."""
import pytest
from datetime import datetime

from src.integrations.cti_feeds.base import (
    IOCType,
    NormalizedIOC,
    ThreatLevel,
)
from src.integrations.cti_feeds.feed_normalizer import (
    normalize_ioc_value,
    deduplicate_iocs,
    merge_iocs,
    calculate_risk_score,
    filter_iocs,
    validate_ioc,
    sanitize_tags,
    generate_ioc_fingerprint,
    extract_related_iocs,
)


class TestNormalizeIOCValue:
    """Tests for IOC value normalization."""

    def test_normalize_ip(self):
        """Test IP address normalization."""
        assert normalize_ioc_value("192.168.001.001", IOCType.IP_ADDRESS) == "192.168.1.1"
        assert normalize_ioc_value("  192.168.1.1  ", IOCType.IP_ADDRESS) == "192.168.1.1"

    def test_normalize_domain(self):
        """Test domain normalization."""
        assert normalize_ioc_value("Example.COM", IOCType.DOMAIN) == "example.com"
        assert normalize_ioc_value("example.com.", IOCType.DOMAIN) == "example.com"

    def test_normalize_url(self):
        """Test URL normalization."""
        assert normalize_ioc_value("HTTP://Example.COM/path", IOCType.URL) == "http://example.com/path"

    def test_normalize_hash(self):
        """Test hash normalization."""
        assert normalize_ioc_value("D41D8CD98F00B204E9800998ECF8427E", IOCType.FILE_HASH_MD5) == "d41d8cd98f00b204e9800998ecf8427e"

    def test_normalize_email(self):
        """Test email normalization."""
        assert normalize_ioc_value("User@Example.COM", IOCType.EMAIL) == "user@example.com"

    def test_normalize_cve(self):
        """Test CVE normalization."""
        assert normalize_ioc_value("cve-2021-44228", IOCType.CVE) == "CVE-2021-44228"


class TestDeduplicateIOCs:
    """Tests for IOC deduplication."""

    def test_deduplicate_identical(self):
        """Test deduplication of identical IOCs."""
        iocs = [
            NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS, source="source1"),
            NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS, source="source2"),
        ]

        result = deduplicate_iocs(iocs)

        assert len(result) == 1
        assert "source1" in result[0].source
        assert "source2" in result[0].source

    def test_deduplicate_different(self):
        """Test deduplication keeps different IOCs."""
        iocs = [
            NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS),
            NormalizedIOC(value="192.168.1.2", type=IOCType.IP_ADDRESS),
        ]

        result = deduplicate_iocs(iocs)

        assert len(result) == 2

    def test_deduplicate_case_insensitive(self):
        """Test case-insensitive deduplication."""
        iocs = [
            NormalizedIOC(value="example.com", type=IOCType.DOMAIN),
            NormalizedIOC(value="EXAMPLE.COM", type=IOCType.DOMAIN),
        ]

        result = deduplicate_iocs(iocs)

        assert len(result) == 1


class TestMergeIOCs:
    """Tests for IOC merging."""

    def test_merge_keeps_higher_threat_level(self):
        """Test that merge keeps higher threat level."""
        existing = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            threat_level=ThreatLevel.MEDIUM,
        )
        new = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            threat_level=ThreatLevel.CRITICAL,
        )

        result = merge_iocs(existing, new)

        assert result.threat_level == ThreatLevel.CRITICAL

    def test_merge_keeps_higher_confidence(self):
        """Test that merge keeps higher confidence."""
        existing = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            confidence=0.5,
        )
        new = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            confidence=0.9,
        )

        result = merge_iocs(existing, new)

        assert result.confidence == 0.9

    def test_merge_combines_tags(self):
        """Test that merge combines tags."""
        existing = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            tags=["tag1", "tag2"],
        )
        new = NormalizedIOC(
            value="test", type=IOCType.DOMAIN,
            tags=["tag2", "tag3"],
        )

        result = merge_iocs(existing, new)

        assert "tag1" in result.tags
        assert "tag2" in result.tags
        assert "tag3" in result.tags


class TestCalculateRiskScore:
    """Tests for risk score calculation."""

    def test_critical_threat_level(self):
        """Test risk score for critical threat."""
        ioc = NormalizedIOC(
            value="test", type=IOCType.IP_ADDRESS,
            threat_level=ThreatLevel.CRITICAL,
            confidence=0.9,
        )

        score = calculate_risk_score(ioc)

        assert score >= 80

    def test_low_threat_level(self):
        """Test risk score for low threat."""
        ioc = NormalizedIOC(
            value="test", type=IOCType.IP_ADDRESS,
            threat_level=ThreatLevel.LOW,
            confidence=0.5,
        )

        score = calculate_risk_score(ioc)

        assert score < 50

    def test_high_risk_tags_increase_score(self):
        """Test that high-risk tags increase score."""
        ioc = NormalizedIOC(
            value="test", type=IOCType.IP_ADDRESS,
            threat_level=ThreatLevel.MEDIUM,
            confidence=0.5,
            tags=["ransomware"],
        )

        score = calculate_risk_score(ioc)

        ioc_no_tags = NormalizedIOC(
            value="test", type=IOCType.IP_ADDRESS,
            threat_level=ThreatLevel.MEDIUM,
            confidence=0.5,
        )
        score_no_tags = calculate_risk_score(ioc_no_tags)

        assert score > score_no_tags


class TestFilterIOCs:
    """Tests for IOC filtering."""

    def test_filter_by_confidence(self):
        """Test filtering by minimum confidence."""
        iocs = [
            NormalizedIOC(value="1", type=IOCType.IP_ADDRESS, confidence=0.3),
            NormalizedIOC(value="2", type=IOCType.IP_ADDRESS, confidence=0.7),
            NormalizedIOC(value="3", type=IOCType.IP_ADDRESS, confidence=0.9),
        ]

        result = filter_iocs(iocs, min_confidence=0.5)

        assert len(result) == 2
        values = [ioc.value for ioc in result]
        assert "1" not in values

    def test_filter_by_threat_level(self):
        """Test filtering by minimum threat level."""
        iocs = [
            NormalizedIOC(value="1", type=IOCType.IP_ADDRESS, threat_level=ThreatLevel.LOW),
            NormalizedIOC(value="2", type=IOCType.IP_ADDRESS, threat_level=ThreatLevel.HIGH),
            NormalizedIOC(value="3", type=IOCType.IP_ADDRESS, threat_level=ThreatLevel.CRITICAL),
        ]

        result = filter_iocs(iocs, min_threat_level=ThreatLevel.HIGH)

        assert len(result) == 2
        values = [ioc.value for ioc in result]
        assert "1" not in values

    def test_filter_by_type(self):
        """Test filtering by allowed types."""
        iocs = [
            NormalizedIOC(value="1", type=IOCType.IP_ADDRESS),
            NormalizedIOC(value="2", type=IOCType.DOMAIN),
            NormalizedIOC(value="3", type=IOCType.URL),
        ]

        result = filter_iocs(iocs, allowed_types=[IOCType.IP_ADDRESS, IOCType.DOMAIN])

        assert len(result) == 2
        values = [ioc.value for ioc in result]
        assert "3" not in values


class TestValidateIOC:
    """Tests for IOC validation."""

    def test_valid_ip(self):
        """Test valid IP address."""
        is_valid, error = validate_ioc("192.168.1.1", IOCType.IP_ADDRESS)
        assert is_valid is True
        assert error is None

    def test_invalid_ip(self):
        """Test invalid IP address."""
        is_valid, error = validate_ioc("999.999.999.999", IOCType.IP_ADDRESS)
        assert is_valid is False
        assert "Invalid IPv4" in error

    def test_valid_domain(self):
        """Test valid domain."""
        is_valid, error = validate_ioc("example.com", IOCType.DOMAIN)
        assert is_valid is True

    def test_valid_md5(self):
        """Test valid MD5 hash."""
        is_valid, error = validate_ioc("d41d8cd98f00b204e9800998ecf8427e", IOCType.FILE_HASH_MD5)
        assert is_valid is True

    def test_invalid_md5(self):
        """Test invalid MD5 hash."""
        is_valid, error = validate_ioc("not-a-hash", IOCType.FILE_HASH_MD5)
        assert is_valid is False

    def test_valid_cve(self):
        """Test valid CVE."""
        is_valid, error = validate_ioc("CVE-2021-44228", IOCType.CVE)
        assert is_valid is True

    def test_empty_value(self):
        """Test empty value."""
        is_valid, error = validate_ioc("", IOCType.IP_ADDRESS)
        assert is_valid is False
        assert "Empty" in error


class TestSanitizeTags:
    """Tests for tag sanitization."""

    def test_remove_duplicates(self):
        """Test duplicate removal."""
        tags = ["tag1", "TAG1", "tag2"]
        result = sanitize_tags(tags)
        assert len(result) == 2

    def test_remove_special_chars(self):
        """Test special character removal."""
        tags = ["tag<script>", "normal_tag"]
        result = sanitize_tags(tags)
        assert "tagscript" in result

    def test_max_length(self):
        """Test max length truncation."""
        long_tag = "a" * 100
        result = sanitize_tags([long_tag], max_length=20)
        assert len(result[0]) == 20


class TestGenerateFingerprint:
    """Tests for IOC fingerprint generation."""

    def test_same_ioc_same_fingerprint(self):
        """Test same IOC generates same fingerprint."""
        ioc1 = NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS)
        ioc2 = NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS)

        fp1 = generate_ioc_fingerprint(ioc1)
        fp2 = generate_ioc_fingerprint(ioc2)

        assert fp1 == fp2

    def test_different_ioc_different_fingerprint(self):
        """Test different IOC generates different fingerprint."""
        ioc1 = NormalizedIOC(value="192.168.1.1", type=IOCType.IP_ADDRESS)
        ioc2 = NormalizedIOC(value="192.168.1.2", type=IOCType.IP_ADDRESS)

        fp1 = generate_ioc_fingerprint(ioc1)
        fp2 = generate_ioc_fingerprint(ioc2)

        assert fp1 != fp2


class TestExtractRelatedIOCs:
    """Tests for extracting related IOCs."""

    def test_extract_domain_from_url(self):
        """Test extracting domain from URL."""
        ioc = NormalizedIOC(
            value="https://evil.com/malware.exe",
            type=IOCType.URL,
        )

        related = extract_related_iocs(ioc)

        assert "evil.com" in related

    def test_extract_hashes_from_description(self):
        """Test extracting hashes from description."""
        ioc = NormalizedIOC(
            value="malware.exe",
            type=IOCType.FILE_PATH,
            description="Associated hash: d41d8cd98f00b204e9800998ecf8427e",
        )

        related = extract_related_iocs(ioc)

        assert "d41d8cd98f00b204e9800998ecf8427e" in related

    def test_extract_ips_from_description(self):
        """Test extracting IPs from description."""
        ioc = NormalizedIOC(
            value="evil.com",
            type=IOCType.DOMAIN,
            description="Resolves to 192.168.1.100",
        )

        related = extract_related_iocs(ioc)

        assert "192.168.1.100" in related
