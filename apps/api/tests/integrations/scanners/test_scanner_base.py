"""Tests for scanner base classes and dataclasses."""

import pytest

from src.integrations.scanners import (
    ScannerType,
    ScanState,
    ScannerConfig,
    NormalizedFinding,
    ScanProgress,
    ScanResult,
    get_scanner_adapter,
)
from src.integrations.scanners.exceptions import (
    ScannerError,
    ScannerConnectionError,
    ScannerAPIError,
    ScannerAuthenticationError,
    ScannerTimeoutError,
    ScanNotFoundError,
)


class TestScannerType:
    """Tests for ScannerType enum."""

    def test_scanner_types_exist(self):
        """Test that all expected scanner types exist."""
        assert ScannerType.NESSUS == "nessus"
        assert ScannerType.OPENVAS == "openvas"
        assert ScannerType.QUALYS == "qualys"

    def test_scanner_type_values(self):
        """Test scanner type string values."""
        assert ScannerType.NESSUS.value == "nessus"
        assert ScannerType.OPENVAS.value == "openvas"
        assert ScannerType.QUALYS.value == "qualys"


class TestScanState:
    """Tests for ScanState enum."""

    def test_scan_states_exist(self):
        """Test that all scan states exist."""
        assert ScanState.PENDING == "pending"
        assert ScanState.RUNNING == "running"
        assert ScanState.COMPLETED == "completed"
        assert ScanState.FAILED == "failed"
        assert ScanState.CANCELLED == "cancelled"
        assert ScanState.PAUSED == "paused"


class TestScannerConfig:
    """Tests for ScannerConfig dataclass."""

    def test_create_config_minimal(self):
        """Test creating config with minimal params."""
        config = ScannerConfig(scanner_type=ScannerType.NESSUS)

        assert config.scanner_type == ScannerType.NESSUS
        assert config.base_url == ""
        assert config.api_key == ""
        assert config.verify_ssl is True
        assert config.timeout == 60

    def test_create_config_full(self):
        """Test creating config with all params."""
        config = ScannerConfig(
            scanner_type=ScannerType.QUALYS,
            base_url="https://qualys.example.com",
            api_key="my-api-key",
            api_secret="my-api-secret",
            username="user",
            password="pass",
            verify_ssl=False,
            timeout=120,
            extra_config={"region": "us"},
        )

        assert config.scanner_type == ScannerType.QUALYS
        assert config.base_url == "https://qualys.example.com"
        assert config.api_key == "my-api-key"
        assert config.api_secret == "my-api-secret"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.verify_ssl is False
        assert config.timeout == 120
        assert config.extra_config == {"region": "us"}


class TestNormalizedFinding:
    """Tests for NormalizedFinding dataclass."""

    def test_create_finding_minimal(self):
        """Test creating finding with minimal params."""
        finding = NormalizedFinding(
            title="Test Vulnerability",
            description="A test vulnerability",
            severity="high",
        )

        assert finding.title == "Test Vulnerability"
        assert finding.description == "A test vulnerability"
        assert finding.severity == "high"
        assert finding.cvss_score is None
        assert finding.cve_id is None
        assert finding.references == []

    def test_create_finding_full(self):
        """Test creating finding with all params."""
        finding = NormalizedFinding(
            title="SQL Injection",
            description="SQL injection in login form",
            severity="critical",
            cvss_score=9.8,
            cve_id="CVE-2024-1234",
            affected_host="192.168.1.10",
            affected_port=443,
            protocol="tcp",
            solution="Use parameterized queries",
            plugin_id="12345",
            plugin_name="SQL Injection Detection",
            plugin_family="Web Application",
            references=["https://cve.mitre.org/CVE-2024-1234"],
        )

        assert finding.title == "SQL Injection"
        assert finding.cvss_score == 9.8
        assert finding.cve_id == "CVE-2024-1234"
        assert finding.affected_host == "192.168.1.10"
        assert finding.affected_port == 443

    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = NormalizedFinding(
            title="XSS Vulnerability",
            description="Cross-site scripting",
            severity="medium",
            cvss_score=6.1,
            cve_id="CVE-2024-5678",
        )

        result = finding.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "XSS Vulnerability"
        assert result["severity"] == "medium"
        assert result["cvss_score"] == 6.1
        assert result["cve_id"] == "CVE-2024-5678"


class TestScanProgress:
    """Tests for ScanProgress dataclass."""

    def test_create_progress(self):
        """Test creating scan progress."""
        progress = ScanProgress(
            scan_id="scan-123",
            state=ScanState.RUNNING,
            progress_percent=45,
            hosts_total=10,
            hosts_completed=4,
            current_host="192.168.1.5",
            message="Scanning host 5 of 10",
        )

        assert progress.scan_id == "scan-123"
        assert progress.state == ScanState.RUNNING
        assert progress.progress_percent == 45
        assert progress.hosts_total == 10
        assert progress.hosts_completed == 4


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_create_result_empty(self):
        """Test creating empty result."""
        result = ScanResult(
            scan_id="scan-123",
            state=ScanState.COMPLETED,
        )

        assert result.scan_id == "scan-123"
        assert result.state == ScanState.COMPLETED
        assert result.findings == []
        assert result.critical_count == 0

    def test_count_severities(self):
        """Test counting severities."""
        findings = [
            NormalizedFinding(title="V1", description="", severity="critical"),
            NormalizedFinding(title="V2", description="", severity="critical"),
            NormalizedFinding(title="V3", description="", severity="high"),
            NormalizedFinding(title="V4", description="", severity="medium"),
            NormalizedFinding(title="V5", description="", severity="low"),
            NormalizedFinding(title="V6", description="", severity="info"),
            NormalizedFinding(title="V7", description="", severity="info"),
        ]

        result = ScanResult(
            scan_id="scan-123",
            state=ScanState.COMPLETED,
            findings=findings,
        )
        result.count_severities()

        assert result.critical_count == 2
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 1
        assert result.info_count == 2


class TestScannerExceptions:
    """Tests for scanner exceptions."""

    def test_scanner_error(self):
        """Test base ScannerError."""
        error = ScannerError("Test error", scanner_type="nessus")

        assert str(error) == "Test error"
        assert error.scanner_type == "nessus"

    def test_scanner_connection_error(self):
        """Test ScannerConnectionError."""
        error = ScannerConnectionError(
            "Connection refused", scanner_type="openvas"
        )

        assert isinstance(error, ScannerError)
        assert error.scanner_type == "openvas"

    def test_scanner_api_error(self):
        """Test ScannerAPIError with status code."""
        error = ScannerAPIError(
            "API error", scanner_type="qualys", status_code=401
        )

        assert error.status_code == 401

    def test_scan_not_found_error(self):
        """Test ScanNotFoundError."""
        error = ScanNotFoundError(
            "Scan not found", scanner_type="nessus", scan_id="scan-999"
        )

        assert error.scan_id == "scan-999"


class TestGetScannerAdapter:
    """Tests for get_scanner_adapter factory function."""

    def test_get_nessus_adapter(self):
        """Test getting Nessus adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            api_key="key",
            api_secret="secret",
        )

        adapter = get_scanner_adapter(config)

        from src.integrations.scanners.nessus_scanner import NessusAdapter
        assert isinstance(adapter, NessusAdapter)

    def test_get_openvas_adapter(self):
        """Test getting OpenVAS adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            base_url="https://gvm.example.com",
            username="admin",
            password="admin",
        )

        adapter = get_scanner_adapter(config)

        from src.integrations.scanners.openvas_scanner import OpenVASAdapter
        assert isinstance(adapter, OpenVASAdapter)

    def test_get_qualys_adapter(self):
        """Test getting Qualys adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.QUALYS,
            base_url="https://qualys.example.com",
            username="user",
            password="pass",
        )

        adapter = get_scanner_adapter(config)

        from src.integrations.scanners.qualys_scanner import QualysAdapter
        assert isinstance(adapter, QualysAdapter)

    def test_invalid_scanner_type(self):
        """Test that invalid scanner type raises error."""
        config = ScannerConfig(scanner_type=ScannerType.NESSUS)
        # Manually set invalid type to test error handling
        config.scanner_type = "invalid"

        with pytest.raises(ValueError, match="Unsupported scanner type"):
            get_scanner_adapter(config)
