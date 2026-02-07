"""Tests for Nessus scanner adapter."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.integrations.scanners import ScannerConfig, ScannerType, ScanState
from src.integrations.scanners.nessus_scanner import NessusAdapter
from src.integrations.scanners.exceptions import (
    ScannerConnectionError,
    ScannerAuthenticationError,
    ScannerAPIError,
    ScanNotFoundError,
)


class TestNessusAdapter:
    """Tests for NessusAdapter."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            api_key="access-key",
            api_secret="secret-key",
            verify_ssl=False,
        )

    @pytest.fixture
    def adapter(self, config):
        """Create adapter instance."""
        return NessusAdapter(config)

    def test_init(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.scanner_type == ScannerType.NESSUS
        assert adapter._client is None

    def test_severity_mapping(self):
        """Test Nessus severity mapping."""
        assert NessusAdapter.SEVERITY_MAP[0] == "info"
        assert NessusAdapter.SEVERITY_MAP[1] == "low"
        assert NessusAdapter.SEVERITY_MAP[2] == "medium"
        assert NessusAdapter.SEVERITY_MAP[3] == "high"
        assert NessusAdapter.SEVERITY_MAP[4] == "critical"


class TestNessusAdapterConnection:
    """Tests for Nessus adapter connection."""

    @pytest.fixture
    def config_api_key(self):
        """Config with API keys."""
        return ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            api_key="access-key",
            api_secret="secret-key",
        )

    @pytest.fixture
    def config_username(self):
        """Config with username/password."""
        return ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            username="admin",
            password="password",
        )

    @pytest.fixture
    def config_no_auth(self):
        """Config without authentication."""
        return ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
        )

    def test_get_client_missing_library(self, config_api_key):
        """Test error when pyTenable is not installed."""
        adapter = NessusAdapter(config_api_key)

        with patch.dict("sys.modules", {"tenable": None, "tenable.nessus": None}):
            with pytest.raises(ScannerConnectionError, match="pyTenable"):
                adapter._get_client()

    def test_get_client_no_auth(self, config_no_auth):
        """Test error when no authentication provided."""
        adapter = NessusAdapter(config_no_auth)

        with patch("src.integrations.scanners.nessus_scanner.NessusAdapter._get_client") as mock:
            mock.side_effect = ScannerAuthenticationError(
                "Nessus requires either API keys or username/password",
                scanner_type="nessus",
            )
            with pytest.raises(ScannerAuthenticationError):
                adapter._get_client()


class TestNessusAdapterOperations:
    """Tests for Nessus adapter operations with mocked client."""

    @pytest.fixture
    def mock_nessus_client(self):
        """Create mock Nessus client."""
        client = MagicMock()
        client.server.properties.return_value = {"nessus_ui_version": "10.0.0"}
        client.scans.create.return_value = {"id": "123"}
        client.scans.launch.return_value = None
        client.scans.details.return_value = {
            "info": {"status": "completed"},
            "hosts": [
                {"host_id": 1, "hostname": "192.168.1.1", "scanprogresscurrent": "100"},
                {"host_id": 2, "hostname": "192.168.1.2", "scanprogresscurrent": "100"},
            ],
        }
        client.scans.host_details.return_value = {
            "vulnerabilities": [
                {
                    "plugin_id": 12345,
                    "plugin_name": "Test Vulnerability",
                    "severity": 3,
                    "cvss_score": 7.5,
                    "port": 443,
                    "protocol": "tcp",
                },
            ],
        }
        client.scans.plugin_output.return_value = {
            "output": "CVE-2024-1234 detected",
            "solution": "Apply patch",
        }
        client.scans.stop.return_value = None
        client.editor.template_list.return_value = [
            {"name": "basic", "uuid": "template-uuid-123"},
        ]
        return client

    @pytest.fixture
    def adapter_with_client(self, mock_nessus_client):
        """Create adapter with mocked client."""
        config = ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            api_key="key",
            api_secret="secret",
        )
        adapter = NessusAdapter(config)
        adapter._client = mock_nessus_client
        return adapter

    @pytest.mark.asyncio
    async def test_test_connection(self, adapter_with_client, mock_nessus_client):
        """Test connection test."""
        result = await adapter_with_client.test_connection()

        assert result is True
        mock_nessus_client.server.properties.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_scan(self, adapter_with_client, mock_nessus_client):
        """Test launching a scan."""
        scan_id = await adapter_with_client.launch_scan(
            targets=["192.168.1.1", "192.168.1.2"],
            scan_name="Test Scan",
        )

        assert scan_id == "123"
        mock_nessus_client.scans.create.assert_called_once()
        mock_nessus_client.scans.launch.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_scan_status_completed(self, adapter_with_client, mock_nessus_client):
        """Test getting completed scan status."""
        progress = await adapter_with_client.get_scan_status("123")

        assert progress.scan_id == "123"
        assert progress.state == ScanState.COMPLETED
        assert progress.progress_percent == 100
        assert progress.hosts_total == 2
        assert progress.hosts_completed == 2

    @pytest.mark.asyncio
    async def test_get_scan_status_running(self, adapter_with_client, mock_nessus_client):
        """Test getting running scan status."""
        mock_nessus_client.scans.details.return_value = {
            "info": {"status": "running"},
            "hosts": [
                {"host_id": 1, "hostname": "192.168.1.1", "scanprogresscurrent": "100"},
                {"host_id": 2, "hostname": "192.168.1.2", "scanprogresscurrent": "50"},
            ],
        }

        progress = await adapter_with_client.get_scan_status("123")

        assert progress.state == ScanState.RUNNING
        assert progress.hosts_completed == 1

    @pytest.mark.asyncio
    async def test_get_scan_results(self, adapter_with_client, mock_nessus_client):
        """Test getting scan results."""
        result = await adapter_with_client.get_scan_results("123")

        assert result.scan_id == "123"
        assert result.state == ScanState.COMPLETED
        assert len(result.findings) > 0
        assert result.hosts_scanned == 2

        # Check finding details
        finding = result.findings[0]
        assert finding.title == "Test Vulnerability"
        assert finding.severity == "high"
        assert finding.cvss_score == 7.5
        assert finding.cve_id == "CVE-2024-1234"

    @pytest.mark.asyncio
    async def test_stop_scan(self, adapter_with_client, mock_nessus_client):
        """Test stopping a scan."""
        result = await adapter_with_client.stop_scan("123")

        assert result is True
        mock_nessus_client.scans.stop.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_close(self, adapter_with_client, mock_nessus_client):
        """Test closing connection."""
        await adapter_with_client.close()

        mock_nessus_client.session.close.assert_called_once()
        assert adapter_with_client._client is None


class TestNessusCVEExtraction:
    """Tests for CVE extraction from Nessus data."""

    @pytest.fixture
    def adapter(self):
        """Create adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.NESSUS,
            base_url="https://nessus.example.com",
            api_key="key",
            api_secret="secret",
        )
        return NessusAdapter(config)

    def test_extract_cve_from_vuln(self, adapter):
        """Test extracting CVE from vulnerability data."""
        vuln = {"cve": "CVE-2024-1234"}
        result = adapter._extract_cve(vuln, {})
        assert result == "CVE-2024-1234"

    def test_extract_cve_from_list(self, adapter):
        """Test extracting CVE from list."""
        vuln = {"cve": ["CVE-2024-1234", "CVE-2024-5678"]}
        result = adapter._extract_cve(vuln, {})
        assert result == "CVE-2024-1234"

    def test_extract_cve_from_output(self, adapter):
        """Test extracting CVE from plugin output."""
        vuln = {}
        plugin_output = {"output": "Vulnerability CVE-2024-9999 was detected"}
        result = adapter._extract_cve(vuln, plugin_output)
        assert result == "CVE-2024-9999"

    def test_extract_cve_none(self, adapter):
        """Test no CVE found."""
        result = adapter._extract_cve({}, {})
        assert result is None
