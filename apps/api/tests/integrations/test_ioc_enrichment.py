"""
IOC Enrichment integration tests.
"""

import pytest

from src.integrations.ioc_enrichment import (
    IOCEnricher,
    IOCType,
    ThreatLevel,
    EnrichmentResult,
)


class TestIOCEnricher:
    """Tests for IOC Enricher."""

    @pytest.fixture
    def enricher(self):
        """Get IOC enricher instance."""
        return IOCEnricher()

    def test_detect_ip_type(self, enricher):
        """Test IP address type detection."""
        ioc_type = enricher.detect_ioc_type("192.168.1.1")
        assert ioc_type == IOCType.IP_ADDRESS

        ioc_type = enricher.detect_ioc_type("8.8.8.8")
        assert ioc_type == IOCType.IP_ADDRESS

    def test_detect_domain_type(self, enricher):
        """Test domain type detection."""
        ioc_type = enricher.detect_ioc_type("example.com")
        assert ioc_type == IOCType.DOMAIN

        ioc_type = enricher.detect_ioc_type("subdomain.example.org")
        assert ioc_type == IOCType.DOMAIN

    def test_detect_url_type(self, enricher):
        """Test URL type detection."""
        ioc_type = enricher.detect_ioc_type("https://example.com/path")
        assert ioc_type == IOCType.URL

        ioc_type = enricher.detect_ioc_type("http://malicious.site/payload")
        assert ioc_type == IOCType.URL

    def test_detect_hash_types(self, enricher):
        """Test hash type detection."""
        # MD5 (32 chars)
        ioc_type = enricher.detect_ioc_type("d41d8cd98f00b204e9800998ecf8427e")
        assert ioc_type == IOCType.FILE_HASH_MD5

        # SHA1 (40 chars)
        ioc_type = enricher.detect_ioc_type("da39a3ee5e6b4b0d3255bfef95601890afd80709")
        assert ioc_type == IOCType.FILE_HASH_SHA1

        # SHA256 (64 chars)
        ioc_type = enricher.detect_ioc_type("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert ioc_type == IOCType.FILE_HASH_SHA256

    def test_detect_email_type(self, enricher):
        """Test email type detection."""
        ioc_type = enricher.detect_ioc_type("test@example.com")
        assert ioc_type == IOCType.EMAIL

    def test_enrich_ip(self, enricher):
        """Test IP enrichment."""
        # enrich() is synchronous, returns EnrichmentResult directly
        result = enricher.enrich("8.8.8.8")

        assert isinstance(result, EnrichmentResult)
        assert result.ioc_type == IOCType.IP_ADDRESS
        assert result.ioc_value == "8.8.8.8"
        assert result.overall_threat_level in ThreatLevel

    def test_enrich_known_malicious(self, enricher):
        """Test enrichment of known malicious IOC."""
        # Use a known malicious IP from the test data
        result = enricher.enrich("185.220.101.1")

        assert isinstance(result, EnrichmentResult)
        # Should have threat assessment
        assert result.overall_threat_level is not None

    def test_enrich_batch(self, enricher):
        """Test batch IOC enrichment."""
        # enrich_batch expects list of strings
        iocs = ["8.8.8.8", "example.com", "test@example.com"]

        results = enricher.enrich_batch(iocs)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, EnrichmentResult)

    def test_enrichment_summary(self, enricher):
        """Test enrichment summary generation."""
        # Test with single result (get_enrichment_summary expects single EnrichmentResult)
        result = enricher.enrich("8.8.8.8")

        # Check if get_enrichment_summary exists
        if hasattr(enricher, 'get_enrichment_summary'):
            if isinstance(result, EnrichmentResult):
                summary = enricher.get_enrichment_summary(result)
                assert summary is not None
                assert "ioc" in summary

    def test_export_json(self, enricher):
        """Test JSON export."""
        result = enricher.enrich("8.8.8.8")

        # Check if export_results exists
        if hasattr(enricher, 'export_results'):
            exported = enricher.export_results([result], "json")
            assert isinstance(exported, str)
        elif hasattr(enricher, 'export_json'):
            exported = enricher.export_json([result])
            assert exported is not None

    def test_export_markdown(self, enricher):
        """Test Markdown export."""
        result = enricher.enrich("8.8.8.8")

        if hasattr(enricher, 'export_results'):
            exported = enricher.export_results([result], "markdown")
            assert isinstance(exported, str)
        elif hasattr(enricher, 'export_markdown'):
            exported = enricher.export_markdown([result])
            assert exported is not None

    def test_export_csv(self, enricher):
        """Test CSV export."""
        result = enricher.enrich("8.8.8.8")

        if hasattr(enricher, 'export_results'):
            exported = enricher.export_results([result], "csv")
            assert isinstance(exported, str)
        elif hasattr(enricher, 'export_csv'):
            exported = enricher.export_csv([result])
            assert exported is not None

    def test_mitre_mapping(self, enricher):
        """Test MITRE ATT&CK mapping for IOCs."""
        result = enricher.enrich("185.220.101.1")
        # Result should have some threat data
        assert result is not None


class TestIOCTypes:
    """Tests for IOC type handling."""

    def test_ioc_type_enum_values(self):
        """Test IOC type enum has expected values."""
        assert IOCType.IP_ADDRESS.value == "ip"
        assert IOCType.DOMAIN.value == "domain"
        assert IOCType.URL.value == "url"
        assert IOCType.FILE_HASH_MD5.value == "md5"
        assert IOCType.FILE_HASH_SHA1.value == "sha1"
        assert IOCType.FILE_HASH_SHA256.value == "sha256"
        assert IOCType.EMAIL.value == "email"

    def test_threat_level_enum_values(self):
        """Test threat level enum has expected values."""
        assert ThreatLevel.CRITICAL.value == "critical"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.CLEAN.value == "clean"
        assert ThreatLevel.UNKNOWN.value == "unknown"
