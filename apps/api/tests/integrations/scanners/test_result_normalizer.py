"""Tests for result normalizer utilities."""

import pytest

from src.integrations.scanners import (
    NormalizedFinding,
    ScanResult,
    ScanState,
)
from src.integrations.scanners.result_normalizer import (
    normalize_severity,
    cvss_to_severity,
    extract_cve_ids,
    deduplicate_findings,
    merge_findings,
    findings_to_dicts,
    filter_findings_by_severity,
    summarize_results,
)


class TestNormalizeSeverity:
    """Tests for normalize_severity function."""

    def test_standard_severities(self):
        """Test standard severity strings."""
        assert normalize_severity("critical") == "critical"
        assert normalize_severity("high") == "high"
        assert normalize_severity("medium") == "medium"
        assert normalize_severity("low") == "low"
        assert normalize_severity("info") == "info"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert normalize_severity("CRITICAL") == "critical"
        assert normalize_severity("High") == "high"
        assert normalize_severity("MEDIUM") == "medium"

    def test_alternate_names(self):
        """Test alternate severity names."""
        assert normalize_severity("crit") == "critical"
        assert normalize_severity("urgent") == "critical"
        assert normalize_severity("severe") == "critical"
        assert normalize_severity("important") == "high"
        assert normalize_severity("moderate") == "medium"
        assert normalize_severity("warning") == "medium"
        assert normalize_severity("minor") == "low"
        assert normalize_severity("informational") == "info"
        assert normalize_severity("none") == "info"

    def test_numeric_severities(self):
        """Test numeric severity values."""
        assert normalize_severity("4") == "critical"
        assert normalize_severity("3") == "high"
        assert normalize_severity("2") == "medium"
        assert normalize_severity("1") == "low"
        assert normalize_severity("0") == "info"

    def test_empty_and_unknown(self):
        """Test empty and unknown values."""
        assert normalize_severity("") == "info"
        assert normalize_severity(None) == "info"
        assert normalize_severity("unknown") == "info"


class TestCVSSToSeverity:
    """Tests for cvss_to_severity function."""

    def test_critical_range(self):
        """Test critical CVSS range (9.0-10.0)."""
        assert cvss_to_severity(9.0) == "critical"
        assert cvss_to_severity(9.5) == "critical"
        assert cvss_to_severity(10.0) == "critical"

    def test_high_range(self):
        """Test high CVSS range (7.0-8.9)."""
        assert cvss_to_severity(7.0) == "high"
        assert cvss_to_severity(8.0) == "high"
        assert cvss_to_severity(8.9) == "high"

    def test_medium_range(self):
        """Test medium CVSS range (4.0-6.9)."""
        assert cvss_to_severity(4.0) == "medium"
        assert cvss_to_severity(5.5) == "medium"
        assert cvss_to_severity(6.9) == "medium"

    def test_low_range(self):
        """Test low CVSS range (0.1-3.9)."""
        assert cvss_to_severity(0.1) == "low"
        assert cvss_to_severity(2.0) == "low"
        assert cvss_to_severity(3.9) == "low"

    def test_info_range(self):
        """Test info CVSS range (0.0)."""
        assert cvss_to_severity(0.0) == "info"

    def test_none_value(self):
        """Test None value."""
        assert cvss_to_severity(None) == "info"


class TestExtractCVEIds:
    """Tests for extract_cve_ids function."""

    def test_single_cve(self):
        """Test extracting single CVE."""
        text = "This vulnerability is CVE-2024-1234"
        result = extract_cve_ids(text)
        assert result == ["CVE-2024-1234"]

    def test_multiple_cves(self):
        """Test extracting multiple CVEs."""
        text = "Found CVE-2024-1234 and CVE-2023-5678 in the scan"
        result = extract_cve_ids(text)
        assert "CVE-2024-1234" in result
        assert "CVE-2023-5678" in result

    def test_no_cves(self):
        """Test text without CVEs."""
        text = "No vulnerabilities found"
        result = extract_cve_ids(text)
        assert result == []

    def test_case_insensitive(self):
        """Test case insensitive extraction."""
        text = "found cve-2024-9999"
        result = extract_cve_ids(text)
        assert result == ["CVE-2024-9999"]

    def test_deduplicated(self):
        """Test CVEs are deduplicated."""
        text = "CVE-2024-1234 is related to CVE-2024-1234"
        result = extract_cve_ids(text)
        assert result == ["CVE-2024-1234"]

    def test_empty_input(self):
        """Test empty input."""
        assert extract_cve_ids("") == []
        assert extract_cve_ids(None) == []


class TestDeduplicateFindings:
    """Tests for deduplicate_findings function."""

    def test_no_duplicates(self):
        """Test list without duplicates."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host1"),
            NormalizedFinding(title="V2", description="", severity="medium", affected_host="host2"),
        ]

        result = deduplicate_findings(findings)

        assert len(result) == 2

    def test_removes_duplicates(self):
        """Test removing duplicates."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host1"),
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host1"),
            NormalizedFinding(title="V1", description="Different", severity="high", affected_host="host1"),
        ]

        result = deduplicate_findings(findings)

        assert len(result) == 1

    def test_same_vuln_different_hosts(self):
        """Test same vulnerability on different hosts."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host1"),
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host2"),
        ]

        result = deduplicate_findings(findings)

        assert len(result) == 2


class TestMergeFindings:
    """Tests for merge_findings function."""

    def test_no_merge(self):
        """Test without merging by CVE."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", cve_id="CVE-2024-1", affected_host="host1"),
            NormalizedFinding(title="V1", description="", severity="high", cve_id="CVE-2024-1", affected_host="host2"),
        ]

        result = merge_findings(findings, merge_by_cve=False)

        assert len(result) == 2

    def test_merge_by_cve(self):
        """Test merging by CVE."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", cve_id="CVE-2024-1", affected_host="host1"),
            NormalizedFinding(title="V1", description="", severity="critical", cve_id="CVE-2024-1", affected_host="host2"),
        ]

        result = merge_findings(findings, merge_by_cve=True)

        assert len(result) == 1
        # Should use highest severity
        assert result[0].severity == "critical"
        # Should include both hosts
        assert "host1" in result[0].affected_host
        assert "host2" in result[0].affected_host

    def test_merge_preserves_no_cve(self):
        """Test findings without CVE are preserved."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="high", affected_host="host1"),
            NormalizedFinding(title="V2", description="", severity="medium", affected_host="host2"),
        ]

        result = merge_findings(findings, merge_by_cve=True)

        assert len(result) == 2


class TestFindingsToDicts:
    """Tests for findings_to_dicts function."""

    def test_convert_findings(self):
        """Test converting findings to dicts."""
        findings = [
            NormalizedFinding(title="V1", description="Desc1", severity="high"),
            NormalizedFinding(title="V2", description="Desc2", severity="low", cvss_score=3.5),
        ]

        result = findings_to_dicts(findings)

        assert len(result) == 2
        assert all(isinstance(r, dict) for r in result)
        assert result[0]["title"] == "V1"
        assert result[1]["cvss_score"] == 3.5

    def test_empty_list(self):
        """Test empty list."""
        result = findings_to_dicts([])
        assert result == []


class TestFilterFindingsBySeverity:
    """Tests for filter_findings_by_severity function."""

    @pytest.fixture
    def sample_findings(self):
        """Create sample findings."""
        return [
            NormalizedFinding(title="Critical", description="", severity="critical"),
            NormalizedFinding(title="High", description="", severity="high"),
            NormalizedFinding(title="Medium", description="", severity="medium"),
            NormalizedFinding(title="Low", description="", severity="low"),
            NormalizedFinding(title="Info", description="", severity="info"),
        ]

    def test_filter_high_and_above(self, sample_findings):
        """Test filtering high and above."""
        result = filter_findings_by_severity(sample_findings, min_severity="high")

        assert len(result) == 2
        assert all(f.severity in ["critical", "high"] for f in result)

    def test_filter_medium_and_above(self, sample_findings):
        """Test filtering medium and above."""
        result = filter_findings_by_severity(sample_findings, min_severity="medium")

        assert len(result) == 3
        assert all(f.severity in ["critical", "high", "medium"] for f in result)

    def test_filter_all(self, sample_findings):
        """Test filtering all (info)."""
        result = filter_findings_by_severity(sample_findings, min_severity="info")

        assert len(result) == 5


class TestSummarizeResults:
    """Tests for summarize_results function."""

    def test_summarize_empty(self):
        """Test summarizing empty results."""
        result = ScanResult(
            scan_id="scan-123",
            state=ScanState.COMPLETED,
        )

        summary = summarize_results(result)

        assert summary["scan_id"] == "scan-123"
        assert summary["state"] == "completed"
        assert summary["total_findings"] == 0
        assert summary["unique_cves"] == 0

    def test_summarize_with_findings(self):
        """Test summarizing results with findings."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="critical", cve_id="CVE-2024-1", affected_host="host1"),
            NormalizedFinding(title="V2", description="", severity="high", cve_id="CVE-2024-2", affected_host="host1"),
            NormalizedFinding(title="V3", description="", severity="high", cve_id="CVE-2024-2", affected_host="host2"),
            NormalizedFinding(title="V4", description="", severity="info", affected_host="host3"),
        ]

        result = ScanResult(
            scan_id="scan-456",
            state=ScanState.COMPLETED,
            findings=findings,
            hosts_scanned=3,
            duration_seconds=120,
        )
        result.count_severities()

        summary = summarize_results(result)

        assert summary["total_findings"] == 4
        assert summary["hosts_scanned"] == 3
        assert summary["duration_seconds"] == 120
        assert summary["severity_counts"]["critical"] == 1
        assert summary["severity_counts"]["high"] == 2
        assert summary["severity_counts"]["info"] == 1
        assert summary["unique_cves"] == 2
        assert summary["affected_hosts"] == 3
