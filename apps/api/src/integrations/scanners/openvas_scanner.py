"""OpenVAS/GVM scanner adapter using python-gvm."""
import logging
import re
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from .base import (
    BaseScannerAdapter,
    NormalizedFinding,
    ScannerConfig,
    ScannerType,
    ScanProgress,
    ScanResult,
    ScanState,
)
from .exceptions import (
    ScannerAPIError,
    ScannerAuthenticationError,
    ScannerConfigurationError,
    ScannerConnectionError,
    ScanNotFoundError,
)

logger = logging.getLogger(__name__)


class OpenVASAdapter(BaseScannerAdapter):
    """Adapter for OpenVAS/GVM scanner using python-gvm library."""

    scanner_type = ScannerType.OPENVAS

    # Default scan config and scanner IDs (GVM defaults)
    DEFAULT_SCAN_CONFIG = "daba56c8-73ec-11df-a475-002264764cea"  # Full and fast
    DEFAULT_SCANNER = "08b69003-5fc2-4037-a479-93b440211c73"  # OpenVAS Default

    def __init__(self, config: ScannerConfig):
        super().__init__(config)
        self._connection = None
        self._gmp = None

    def _get_connection(self):
        """Get or create GVM connection."""
        if self._gmp is None:
            try:
                from gvm.connections import UnixSocketConnection, TLSConnection
                from gvm.protocols.gmp import Gmp
                from gvm.transforms import EtreeTransform
            except ImportError:
                raise ScannerConnectionError(
                    "python-gvm library is not installed. Run: pip install python-gvm",
                    scanner_type="openvas",
                )

            try:
                socket_path = self.config.extra_config.get("socket_path")
                transform = EtreeTransform()

                if socket_path:
                    # Unix socket connection (local)
                    self._connection = UnixSocketConnection(path=socket_path)
                else:
                    # TLS connection (remote)
                    if not self.config.base_url:
                        raise ScannerConfigurationError(
                            "OpenVAS requires either socket_path or base_url",
                            scanner_type="openvas",
                        )

                    # Parse host and port from base_url
                    host = self.config.base_url.replace("https://", "").replace(
                        "http://", ""
                    )
                    port = 9390  # Default GVM port
                    if ":" in host:
                        host, port_str = host.split(":", 1)
                        port = int(port_str.split("/")[0])

                    self._connection = TLSConnection(
                        hostname=host,
                        port=port,
                        certfile=self.config.extra_config.get("certfile"),
                        keyfile=self.config.extra_config.get("keyfile"),
                        cafile=self.config.extra_config.get("cafile"),
                    )

                self._gmp = Gmp(connection=self._connection, transform=transform)

                # Authenticate
                if not self.config.username or not self.config.password:
                    raise ScannerAuthenticationError(
                        "OpenVAS requires username and password",
                        scanner_type="openvas",
                    )

                self._gmp.authenticate(
                    username=self.config.username, password=self.config.password
                )

            except ScannerConnectionError:
                raise
            except ScannerAuthenticationError:
                raise
            except ScannerConfigurationError:
                raise
            except Exception as e:
                raise ScannerConnectionError(
                    f"Failed to connect to OpenVAS: {str(e)}",
                    scanner_type="openvas",
                )

        return self._gmp

    async def test_connection(self) -> bool:
        """Test connection to OpenVAS/GVM."""
        try:
            gmp = self._get_connection()
            version = gmp.get_version()
            version_text = version.find("version").text if version.find("version") is not None else "unknown"
            logger.info(f"Connected to OpenVAS/GVM version: {version_text}")
            return True
        except ScannerConnectionError:
            raise
        except Exception as e:
            raise ScannerConnectionError(
                f"Failed to connect to OpenVAS: {str(e)}",
                scanner_type="openvas",
            )

    async def launch_scan(
        self,
        targets: List[str],
        scan_name: str,
        policy_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Launch a new OpenVAS scan."""
        try:
            gmp = self._get_connection()

            # Create target
            target_name = f"{scan_name}_target"
            hosts = ",".join(targets)

            # Port list (optional)
            port_list_id = kwargs.get(
                "port_list_id", "33d0cd82-57c6-11e1-8ed1-406186ea4fc5"
            )  # All TCP and Nmap

            target_response = gmp.create_target(
                name=target_name,
                hosts=[hosts],
                port_list_id=port_list_id,
            )

            target_id = target_response.get("id")
            if not target_id:
                raise ScannerAPIError(
                    "Failed to create target in OpenVAS",
                    scanner_type="openvas",
                )

            # Get scan config and scanner IDs
            config_id = policy_id or kwargs.get(
                "config_id", self.DEFAULT_SCAN_CONFIG
            )
            scanner_id = kwargs.get("scanner_id", self.DEFAULT_SCANNER)

            # Create task
            task_response = gmp.create_task(
                name=scan_name,
                config_id=config_id,
                target_id=target_id,
                scanner_id=scanner_id,
            )

            task_id = task_response.get("id")
            if not task_id:
                raise ScannerAPIError(
                    "Failed to create task in OpenVAS",
                    scanner_type="openvas",
                )

            # Start the task
            gmp.start_task(task_id)
            logger.info(f"Launched OpenVAS scan: {task_id}")

            return task_id

        except ScannerConnectionError:
            raise
        except ScannerAPIError:
            raise
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to launch OpenVAS scan: {str(e)}",
                scanner_type="openvas",
            )

    async def get_scan_status(self, scan_id: str) -> ScanProgress:
        """Get the status of an OpenVAS scan."""
        try:
            gmp = self._get_connection()
            task = gmp.get_task(task_id=scan_id)

            # Extract task info
            task_elem = task.find("task")
            if task_elem is None:
                raise ScanNotFoundError(
                    f"Task {scan_id} not found",
                    scanner_type="openvas",
                    scan_id=scan_id,
                )

            status_elem = task_elem.find("status")
            status = status_elem.text if status_elem is not None else "Unknown"

            progress_elem = task_elem.find("progress")
            progress = 0
            if progress_elem is not None and progress_elem.text:
                try:
                    progress = int(progress_elem.text)
                except ValueError:
                    pass

            # Map OpenVAS status to ScanState
            state_map = {
                "New": ScanState.PENDING,
                "Requested": ScanState.PENDING,
                "Running": ScanState.RUNNING,
                "Stop Requested": ScanState.RUNNING,
                "Delete Requested": ScanState.CANCELLED,
                "Done": ScanState.COMPLETED,
                "Stopped": ScanState.CANCELLED,
            }
            state = state_map.get(status, ScanState.RUNNING)

            # Get hosts info from target
            hosts_total = 0
            hosts_completed = 0
            target_elem = task_elem.find("target")
            if target_elem is not None:
                host_count_elem = target_elem.find("hosts")
                if host_count_elem is not None and host_count_elem.text:
                    try:
                        hosts_total = int(host_count_elem.text)
                        hosts_completed = int(hosts_total * progress / 100)
                    except ValueError:
                        pass

            return ScanProgress(
                scan_id=scan_id,
                state=state,
                progress_percent=progress,
                hosts_total=hosts_total,
                hosts_completed=hosts_completed,
                message=f"Status: {status}",
            )

        except ScanNotFoundError:
            raise
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to get scan status: {str(e)}",
                scanner_type="openvas",
            )

    async def get_scan_results(self, scan_id: str) -> ScanResult:
        """Get results from a completed OpenVAS scan."""
        try:
            gmp = self._get_connection()

            # Get task to find report ID
            task = gmp.get_task(task_id=scan_id)
            task_elem = task.find("task")
            if task_elem is None:
                raise ScanNotFoundError(
                    f"Task {scan_id} not found",
                    scanner_type="openvas",
                    scan_id=scan_id,
                )

            # Get the latest report
            last_report_elem = task_elem.find("last_report/report")
            if last_report_elem is None:
                return ScanResult(
                    scan_id=scan_id,
                    state=ScanState.COMPLETED,
                    findings=[],
                )

            report_id = last_report_elem.get("id")
            if not report_id:
                return ScanResult(
                    scan_id=scan_id,
                    state=ScanState.COMPLETED,
                    findings=[],
                )

            # Get full report
            report = gmp.get_report(
                report_id=report_id,
                filter_string="levels=hml",  # High, Medium, Low
                ignore_pagination=True,
            )

            findings: List[NormalizedFinding] = []
            results = report.findall(".//result")

            for result in results:
                finding = self._parse_result(result)
                if finding:
                    findings.append(finding)

            scan_result = ScanResult(
                scan_id=scan_id,
                state=ScanState.COMPLETED,
                findings=findings,
            )
            scan_result.count_severities()

            return scan_result

        except ScanNotFoundError:
            raise
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to get scan results: {str(e)}",
                scanner_type="openvas",
            )

    def _parse_result(self, result_elem) -> Optional[NormalizedFinding]:
        """Parse an OpenVAS result element into a NormalizedFinding."""
        try:
            # Extract basic info
            name = self._get_text(result_elem, "name") or "Unknown Vulnerability"
            description = self._get_text(result_elem, "description") or ""

            # Get severity from CVSS or threat level
            cvss_score = None
            severity = "info"

            severity_elem = result_elem.find("severity")
            if severity_elem is not None and severity_elem.text:
                try:
                    cvss_score = float(severity_elem.text)
                    severity = self._cvss_to_severity(cvss_score)
                except ValueError:
                    pass

            if not cvss_score:
                threat = self._get_text(result_elem, "threat") or ""
                severity = self._threat_to_severity(threat)

            # Extract host and port
            host_elem = result_elem.find("host")
            host = host_elem.text if host_elem is not None else None
            port_str = self._get_text(result_elem, "port") or ""
            port = None
            protocol = None
            if port_str and "/" in port_str:
                parts = port_str.split("/")
                try:
                    port = int(parts[0])
                except ValueError:
                    pass
                if len(parts) > 1:
                    protocol = parts[1]

            # Extract CVE
            nvt_elem = result_elem.find("nvt")
            cve_id = None
            plugin_id = None
            solution = None
            references = []

            if nvt_elem is not None:
                plugin_id = nvt_elem.get("oid")

                cve_elem = nvt_elem.find("cve")
                if cve_elem is not None and cve_elem.text and cve_elem.text != "NOCVE":
                    cve_id = cve_elem.text.split(",")[0].strip()

                solution = self._get_text(nvt_elem, "solution")

                # Get references
                refs_elem = nvt_elem.find("refs")
                if refs_elem is not None:
                    for ref in refs_elem.findall("ref"):
                        ref_id = ref.get("id")
                        if ref_id:
                            references.append(ref_id)

            return NormalizedFinding(
                title=name,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                cve_id=cve_id,
                affected_host=host,
                affected_port=port,
                protocol=protocol,
                solution=solution,
                plugin_id=plugin_id,
                references=references,
            )

        except Exception as e:
            logger.warning(f"Failed to parse OpenVAS result: {e}")
            return None

    def _get_text(self, elem, tag: str) -> Optional[str]:
        """Safely get text from an XML element."""
        child = elem.find(tag)
        return child.text if child is not None else None

    def _cvss_to_severity(self, cvss: float) -> str:
        """Convert CVSS score to severity level."""
        if cvss >= 9.0:
            return "critical"
        elif cvss >= 7.0:
            return "high"
        elif cvss >= 4.0:
            return "medium"
        elif cvss >= 0.1:
            return "low"
        return "info"

    def _threat_to_severity(self, threat: str) -> str:
        """Convert OpenVAS threat level to severity."""
        threat_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Log": "info",
            "Debug": "info",
            "False Positive": "info",
        }
        return threat_map.get(threat, "info")

    async def stop_scan(self, scan_id: str) -> bool:
        """Stop a running OpenVAS scan."""
        try:
            gmp = self._get_connection()
            gmp.stop_task(task_id=scan_id)
            logger.info(f"Stopped OpenVAS scan: {scan_id}")
            return True
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to stop scan: {str(e)}",
                scanner_type="openvas",
            )

    async def close(self):
        """Close the GVM connection."""
        if self._connection:
            try:
                self._connection.disconnect()
            except Exception:
                pass
            self._connection = None
            self._gmp = None
