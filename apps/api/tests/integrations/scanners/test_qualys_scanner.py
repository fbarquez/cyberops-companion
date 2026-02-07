"""Tests for Qualys scanner adapter."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.integrations.scanners import ScannerConfig, ScannerType, ScanState
from src.integrations.scanners.qualys_scanner import QualysAdapter
from src.integrations.scanners.exceptions import (
    ScannerConnectionError,
    ScannerAuthenticationError,
    ScannerAPIError,
    ScanNotFoundError,
)


class TestQualysAdapter:
    """Tests for QualysAdapter."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ScannerConfig(
            scanner_type=ScannerType.QUALYS,
            base_url="https://qualysapi.qualys.com",
            username="user",
            password="pass",
            verify_ssl=True,
        )

    @pytest.fixture
    def adapter(self, config):
        """Create adapter instance."""
        return QualysAdapter(config)

    def test_init(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.scanner_type == ScannerType.QUALYS
        assert adapter._client is None

    def test_severity_mapping(self):
        """Test Qualys severity mapping."""
        assert QualysAdapter.SEVERITY_MAP[1] == "info"
        assert QualysAdapter.SEVERITY_MAP[2] == "low"
        assert QualysAdapter.SEVERITY_MAP[3] == "medium"
        assert QualysAdapter.SEVERITY_MAP[4] == "high"
        assert QualysAdapter.SEVERITY_MAP[5] == "critical"


class TestQualysAdapterOperations:
    """Tests for Qualys adapter operations with mocked httpx client."""

    @pytest.fixture
    def mock_response(self):
        """Create mock response factory."""
        def _create_response(status_code=200, text=""):
            response = MagicMock()
            response.status_code = status_code
            response.text = text
            return response
        return _create_response

    @pytest.fixture
    def mock_client(self, mock_response):
        """Create mock httpx client."""
        client = AsyncMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.aclose = AsyncMock()
        return client

    @pytest.fixture
    def adapter_with_client(self, mock_client):
        """Create adapter with mocked client."""
        config = ScannerConfig(
            scanner_type=ScannerType.QUALYS,
            base_url="https://qualysapi.qualys.com",
            username="user",
            password="pass",
        )
        adapter = QualysAdapter(config)
        adapter._client = mock_client
        return adapter

    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter_with_client, mock_client, mock_response):
        """Test successful connection test."""
        mock_client.get.return_value = mock_response(200, "<SESSION>active</SESSION>")

        result = await adapter_with_client.test_connection()

        assert result is True
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_auth_failure(self, adapter_with_client, mock_client, mock_response):
        """Test connection with auth failure."""
        mock_client.get.return_value = mock_response(401, "Unauthorized")

        with pytest.raises(ScannerAuthenticationError):
            await adapter_with_client.test_connection()

    @pytest.mark.asyncio
    async def test_launch_scan(self, adapter_with_client, mock_client, mock_response):
        """Test launching a scan."""
        mock_client.post.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SIMPLE_RETURN>
                <RESPONSE>
                    <ITEM_LIST>
                        <ITEM><VALUE>scan/1234567890.12345</VALUE></ITEM>
                    </ITEM_LIST>
                </RESPONSE>
            </SIMPLE_RETURN>"""
        )

        scan_id = await adapter_with_client.launch_scan(
            targets=["192.168.1.1", "192.168.1.2"],
            scan_name="Test Scan",
        )

        assert scan_id == "scan/1234567890.12345"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_scan_error(self, adapter_with_client, mock_client, mock_response):
        """Test launch scan with error."""
        mock_client.post.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SIMPLE_RETURN>
                <RESPONSE>
                    <TEXT>Invalid IP address</TEXT>
                </RESPONSE>
            </SIMPLE_RETURN>"""
        )

        with pytest.raises(ScannerAPIError, match="Invalid IP"):
            await adapter_with_client.launch_scan(
                targets=["invalid"],
                scan_name="Test Scan",
            )

    @pytest.mark.asyncio
    async def test_get_scan_status_running(self, adapter_with_client, mock_client, mock_response):
        """Test getting running scan status."""
        mock_client.get.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SCAN_LIST_OUTPUT>
                <SCAN>
                    <REF>scan/123</REF>
                    <STATUS><STATE>Running</STATE></STATUS>
                    <TARGET>192.168.1.1,192.168.1.2</TARGET>
                </SCAN>
            </SCAN_LIST_OUTPUT>"""
        )

        progress = await adapter_with_client.get_scan_status("scan/123")

        assert progress.scan_id == "scan/123"
        assert progress.state == ScanState.RUNNING
        assert progress.hosts_total == 2

    @pytest.mark.asyncio
    async def test_get_scan_status_completed(self, adapter_with_client, mock_client, mock_response):
        """Test getting completed scan status."""
        mock_client.get.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SCAN_LIST_OUTPUT>
                <SCAN>
                    <REF>scan/123</REF>
                    <STATUS><STATE>Finished</STATE></STATUS>
                    <TARGET>192.168.1.1</TARGET>
                </SCAN>
            </SCAN_LIST_OUTPUT>"""
        )

        progress = await adapter_with_client.get_scan_status("scan/123")

        assert progress.state == ScanState.COMPLETED
        assert progress.progress_percent == 100

    @pytest.mark.asyncio
    async def test_get_scan_status_not_found(self, adapter_with_client, mock_client, mock_response):
        """Test scan not found."""
        mock_client.get.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SCAN_LIST_OUTPUT></SCAN_LIST_OUTPUT>"""
        )

        with pytest.raises(ScanNotFoundError):
            await adapter_with_client.get_scan_status("nonexistent")

    @pytest.mark.asyncio
    async def test_get_scan_results(self, adapter_with_client, mock_client, mock_response):
        """Test getting scan results."""
        mock_client.post.return_value = mock_response(
            200,
            """<?xml version="1.0"?>
            <SCAN_RESULT>
                <IP value="192.168.1.10">
                    <VULN number="12345">
                        <TITLE>SQL Injection</TITLE>
                        <DIAGNOSIS>SQL injection in login form</DIAGNOSIS>
                        <SEVERITY>5</SEVERITY>
                        <CVE_ID_LIST>
                            <CVE_ID><ID>CVE-2024-1234</ID></CVE_ID>
                        </CVE_ID_LIST>
                        <PORT>443</PORT>
                        <PROTOCOL>tcp</PROTOCOL>
                        <SOLUTION>Use parameterized queries</SOLUTION>
                    </VULN>
                </IP>
            </SCAN_RESULT>"""
        )

        result = await adapter_with_client.get_scan_results("scan/123")

        assert result.scan_id == "scan/123"
        assert result.state == ScanState.COMPLETED
        assert result.hosts_scanned == 1
        assert len(result.findings) == 1

        finding = result.findings[0]
        assert finding.title == "SQL Injection"
        assert finding.severity == "critical"
        assert finding.cve_id == "CVE-2024-1234"
        assert finding.affected_host == "192.168.1.10"
        assert finding.affected_port == 443

    @pytest.mark.asyncio
    async def test_stop_scan(self, adapter_with_client, mock_client, mock_response):
        """Test stopping a scan."""
        mock_client.post.return_value = mock_response(200, "<RESPONSE>Cancelled</RESPONSE>")

        result = await adapter_with_client.stop_scan("scan/123")

        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, adapter_with_client, mock_client):
        """Test closing connection."""
        await adapter_with_client.close()

        mock_client.aclose.assert_called_once()
        assert adapter_with_client._client is None


class TestQualysVulnParsing:
    """Tests for Qualys vulnerability parsing."""

    @pytest.fixture
    def adapter(self):
        """Create adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.QUALYS,
            base_url="https://qualysapi.qualys.com",
            username="user",
            password="pass",
        )
        return QualysAdapter(config)

    def test_parse_vuln_full(self, adapter):
        """Test parsing full vulnerability."""
        import defusedxml.ElementTree as DET  # noqa: N814

        vuln_xml = DET.fromstring("""
            <VULN number="54321">
                <TITLE>Cross-Site Scripting</TITLE>
                <DIAGNOSIS>XSS in search field</DIAGNOSIS>
                <SEVERITY>4</SEVERITY>
                <CVE_ID_LIST>
                    <CVE_ID><ID>CVE-2024-9999</ID></CVE_ID>
                </CVE_ID_LIST>
                <PORT>80</PORT>
                <PROTOCOL>tcp</PROTOCOL>
                <SOLUTION>Escape output</SOLUTION>
            </VULN>
        """)

        finding = adapter._parse_vuln(vuln_xml, "10.0.0.1")

        assert finding is not None
        assert finding.title == "Cross-Site Scripting"
        assert finding.severity == "high"
        assert finding.cve_id == "CVE-2024-9999"
        assert finding.affected_host == "10.0.0.1"
        assert finding.affected_port == 80
        assert finding.plugin_id == "54321"

    def test_parse_vuln_minimal(self, adapter):
        """Test parsing minimal vulnerability."""
        import defusedxml.ElementTree as DET  # noqa: N814

        vuln_xml = DET.fromstring("""
            <VULN number="11111">
                <TITLE>Info Finding</TITLE>
                <SEVERITY>1</SEVERITY>
            </VULN>
        """)

        finding = adapter._parse_vuln(vuln_xml, "10.0.0.2")

        assert finding is not None
        assert finding.title == "Info Finding"
        assert finding.severity == "info"
        assert finding.cve_id is None

    def test_parse_vuln_no_title(self, adapter):
        """Test parsing vulnerability without title uses QID."""
        import defusedxml.ElementTree as DET  # noqa: N814

        vuln_xml = DET.fromstring("""
            <VULN number="99999">
                <SEVERITY>3</SEVERITY>
            </VULN>
        """)

        finding = adapter._parse_vuln(vuln_xml, "10.0.0.3")

        assert finding.title == "QID 99999"
