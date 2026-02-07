"""Tests for OpenVAS scanner adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import defusedxml.ElementTree as ET  # noqa: N817
import pytest

from src.integrations.scanners import ScannerConfig, ScannerType, ScanState
from src.integrations.scanners.openvas_scanner import OpenVASAdapter
from src.integrations.scanners.exceptions import (
    ScannerConnectionError,
    ScannerAuthenticationError,
    ScannerConfigurationError,
    ScanNotFoundError,
)


class TestOpenVASAdapter:
    """Tests for OpenVASAdapter."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            base_url="https://gvm.example.com:9390",
            username="admin",
            password="admin",
            extra_config={},
        )

    @pytest.fixture
    def config_socket(self):
        """Create config with socket path."""
        return ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            username="admin",
            password="admin",
            extra_config={"socket_path": "/var/run/gvmd.sock"},
        )

    @pytest.fixture
    def adapter(self, config):
        """Create adapter instance."""
        return OpenVASAdapter(config)

    def test_init(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.scanner_type == ScannerType.OPENVAS
        assert adapter._gmp is None
        assert adapter._connection is None

    def test_default_config_ids(self):
        """Test default scan config and scanner IDs."""
        assert OpenVASAdapter.DEFAULT_SCAN_CONFIG == "daba56c8-73ec-11df-a475-002264764cea"
        assert OpenVASAdapter.DEFAULT_SCANNER == "08b69003-5fc2-4037-a479-93b440211c73"


class TestOpenVASAdapterHelpers:
    """Tests for OpenVAS adapter helper methods."""

    @pytest.fixture
    def adapter(self):
        """Create adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            base_url="https://gvm.example.com",
            username="admin",
            password="admin",
        )
        return OpenVASAdapter(config)

    def test_cvss_to_severity_critical(self, adapter):
        """Test CVSS to severity mapping - critical."""
        assert adapter._cvss_to_severity(9.0) == "critical"
        assert adapter._cvss_to_severity(10.0) == "critical"

    def test_cvss_to_severity_high(self, adapter):
        """Test CVSS to severity mapping - high."""
        assert adapter._cvss_to_severity(7.0) == "high"
        assert adapter._cvss_to_severity(8.9) == "high"

    def test_cvss_to_severity_medium(self, adapter):
        """Test CVSS to severity mapping - medium."""
        assert adapter._cvss_to_severity(4.0) == "medium"
        assert adapter._cvss_to_severity(6.9) == "medium"

    def test_cvss_to_severity_low(self, adapter):
        """Test CVSS to severity mapping - low."""
        assert adapter._cvss_to_severity(0.1) == "low"
        assert adapter._cvss_to_severity(3.9) == "low"

    def test_cvss_to_severity_info(self, adapter):
        """Test CVSS to severity mapping - info."""
        assert adapter._cvss_to_severity(0.0) == "info"

    def test_threat_to_severity(self, adapter):
        """Test threat level to severity mapping."""
        assert adapter._threat_to_severity("High") == "high"
        assert adapter._threat_to_severity("Medium") == "medium"
        assert adapter._threat_to_severity("Low") == "low"
        assert adapter._threat_to_severity("Log") == "info"
        assert adapter._threat_to_severity("Unknown") == "info"

    def test_get_text_helper(self, adapter):
        """Test XML text extraction helper."""
        xml_str = "<root><child>Hello</child><empty/></root>"
        root = ET.fromstring(xml_str)

        assert adapter._get_text(root, "child") == "Hello"
        assert adapter._get_text(root, "empty") is None
        assert adapter._get_text(root, "missing") is None


class TestOpenVASAdapterOperations:
    """Tests for OpenVAS adapter operations with mocked GMP."""

    @pytest.fixture
    def mock_gmp(self):
        """Create mock GMP client."""
        gmp = MagicMock()

        # Version response
        version_xml = ET.fromstring("<version>22.4</version>")
        gmp.get_version.return_value = version_xml

        # Create target response
        target_response = MagicMock()
        target_response.get.return_value = "target-uuid-123"
        gmp.create_target.return_value = target_response

        # Create task response
        task_response = MagicMock()
        task_response.get.return_value = "task-uuid-456"
        gmp.create_task.return_value = task_response

        # Start task
        gmp.start_task.return_value = None

        # Stop task
        gmp.stop_task.return_value = None

        return gmp

    @pytest.fixture
    def adapter_with_gmp(self, mock_gmp):
        """Create adapter with mocked GMP."""
        config = ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            base_url="https://gvm.example.com",
            username="admin",
            password="admin",
        )
        adapter = OpenVASAdapter(config)
        adapter._gmp = mock_gmp
        adapter._connection = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_test_connection(self, adapter_with_gmp, mock_gmp):
        """Test connection test."""
        result = await adapter_with_gmp.test_connection()

        assert result is True
        mock_gmp.get_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_scan(self, adapter_with_gmp, mock_gmp):
        """Test launching a scan."""
        scan_id = await adapter_with_gmp.launch_scan(
            targets=["192.168.1.0/24"],
            scan_name="Network Scan",
        )

        assert scan_id == "task-uuid-456"
        mock_gmp.create_target.assert_called_once()
        mock_gmp.create_task.assert_called_once()
        mock_gmp.start_task.assert_called_once_with("task-uuid-456")

    @pytest.mark.asyncio
    async def test_get_scan_status_running(self, adapter_with_gmp, mock_gmp):
        """Test getting running scan status."""
        task_xml = ET.fromstring("""
            <get_tasks_response>
                <task id="task-123">
                    <status>Running</status>
                    <progress>45</progress>
                    <target><hosts>10</hosts></target>
                </task>
            </get_tasks_response>
        """)
        mock_gmp.get_task.return_value = task_xml

        progress = await adapter_with_gmp.get_scan_status("task-123")

        assert progress.scan_id == "task-123"
        assert progress.state == ScanState.RUNNING
        assert progress.progress_percent == 45

    @pytest.mark.asyncio
    async def test_get_scan_status_completed(self, adapter_with_gmp, mock_gmp):
        """Test getting completed scan status."""
        task_xml = ET.fromstring("""
            <get_tasks_response>
                <task id="task-123">
                    <status>Done</status>
                    <progress>100</progress>
                </task>
            </get_tasks_response>
        """)
        mock_gmp.get_task.return_value = task_xml

        progress = await adapter_with_gmp.get_scan_status("task-123")

        assert progress.state == ScanState.COMPLETED

    @pytest.mark.asyncio
    async def test_get_scan_status_not_found(self, adapter_with_gmp, mock_gmp):
        """Test scan not found."""
        task_xml = ET.fromstring("<get_tasks_response></get_tasks_response>")
        mock_gmp.get_task.return_value = task_xml

        with pytest.raises(ScanNotFoundError):
            await adapter_with_gmp.get_scan_status("nonexistent")

    @pytest.mark.asyncio
    async def test_get_scan_results(self, adapter_with_gmp, mock_gmp):
        """Test getting scan results."""
        task_xml = ET.fromstring("""
            <get_tasks_response>
                <task id="task-123">
                    <last_report>
                        <report id="report-789"/>
                    </last_report>
                </task>
            </get_tasks_response>
        """)
        mock_gmp.get_task.return_value = task_xml

        report_xml = ET.fromstring("""
            <get_reports_response>
                <report>
                    <results>
                        <result>
                            <name>Test Vulnerability</name>
                            <description>A test vulnerability</description>
                            <severity>7.5</severity>
                            <host>192.168.1.10</host>
                            <port>443/tcp</port>
                            <nvt oid="1.2.3.4">
                                <cve>CVE-2024-1234</cve>
                                <solution>Apply update</solution>
                            </nvt>
                        </result>
                    </results>
                </report>
            </get_reports_response>
        """)
        mock_gmp.get_report.return_value = report_xml

        result = await adapter_with_gmp.get_scan_results("task-123")

        assert result.scan_id == "task-123"
        assert result.state == ScanState.COMPLETED
        assert len(result.findings) == 1

        finding = result.findings[0]
        assert finding.title == "Test Vulnerability"
        assert finding.severity == "high"
        assert finding.cvss_score == 7.5
        assert finding.cve_id == "CVE-2024-1234"
        assert finding.affected_host == "192.168.1.10"
        assert finding.affected_port == 443
        assert finding.protocol == "tcp"

    @pytest.mark.asyncio
    async def test_stop_scan(self, adapter_with_gmp, mock_gmp):
        """Test stopping a scan."""
        result = await adapter_with_gmp.stop_scan("task-123")

        assert result is True
        mock_gmp.stop_task.assert_called_once_with(task_id="task-123")

    @pytest.mark.asyncio
    async def test_close(self, adapter_with_gmp):
        """Test closing connection."""
        mock_connection = adapter_with_gmp._connection

        await adapter_with_gmp.close()

        mock_connection.disconnect.assert_called_once()
        assert adapter_with_gmp._connection is None
        assert adapter_with_gmp._gmp is None


class TestOpenVASResultParsing:
    """Tests for OpenVAS result parsing."""

    @pytest.fixture
    def adapter(self):
        """Create adapter."""
        config = ScannerConfig(
            scanner_type=ScannerType.OPENVAS,
            base_url="https://gvm.example.com",
            username="admin",
            password="admin",
        )
        return OpenVASAdapter(config)

    def test_parse_result_full(self, adapter):
        """Test parsing full result."""
        result_xml = ET.fromstring("""
            <result>
                <name>SQL Injection</name>
                <description>SQL injection vulnerability</description>
                <severity>9.8</severity>
                <host>10.0.0.5</host>
                <port>80/tcp</port>
                <nvt oid="1.2.3.4.5">
                    <cve>CVE-2024-5678</cve>
                    <solution>Use prepared statements</solution>
                </nvt>
            </result>
        """)

        finding = adapter._parse_result(result_xml)

        assert finding is not None
        assert finding.title == "SQL Injection"
        assert finding.severity == "critical"
        assert finding.cvss_score == 9.8
        assert finding.cve_id == "CVE-2024-5678"
        assert finding.affected_host == "10.0.0.5"
        assert finding.affected_port == 80
        assert finding.protocol == "tcp"

    def test_parse_result_minimal(self, adapter):
        """Test parsing minimal result."""
        result_xml = ET.fromstring("""
            <result>
                <name>Info Finding</name>
                <description>Informational</description>
            </result>
        """)

        finding = adapter._parse_result(result_xml)

        assert finding is not None
        assert finding.title == "Info Finding"
        assert finding.severity == "info"
        assert finding.cvss_score is None

    def test_parse_result_nocve(self, adapter):
        """Test parsing result with NOCVE."""
        result_xml = ET.fromstring("""
            <result>
                <name>Test</name>
                <description>Test</description>
                <nvt oid="1.2.3">
                    <cve>NOCVE</cve>
                </nvt>
            </result>
        """)

        finding = adapter._parse_result(result_xml)

        assert finding.cve_id is None
