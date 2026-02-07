"""Nessus/Tenable scanner adapter using pyTenable."""
import logging
import re
from typing import Any, Dict, List, Optional

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
    ScannerConnectionError,
    ScanNotFoundError,
)

logger = logging.getLogger(__name__)


class NessusAdapter(BaseScannerAdapter):
    """Adapter for Tenable Nessus scanner using pyTenable library."""

    scanner_type = ScannerType.NESSUS

    # Nessus severity mapping (0-4 to standard severities)
    SEVERITY_MAP = {
        0: "info",
        1: "low",
        2: "medium",
        3: "high",
        4: "critical",
    }

    def __init__(self, config: ScannerConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """Get or create Nessus client."""
        if self._client is None:
            try:
                from tenable.nessus import Nessus
            except ImportError:
                raise ScannerConnectionError(
                    "pyTenable library is not installed. Run: pip install pyTenable",
                    scanner_type="nessus",
                )

            try:
                # Nessus can authenticate with API keys or username/password
                if self.config.api_key and self.config.api_secret:
                    self._client = Nessus(
                        url=self.config.base_url,
                        access_key=self.config.api_key,
                        secret_key=self.config.api_secret,
                        ssl_verify=self.config.verify_ssl,
                    )
                elif self.config.username and self.config.password:
                    self._client = Nessus(
                        url=self.config.base_url,
                        username=self.config.username,
                        password=self.config.password,
                        ssl_verify=self.config.verify_ssl,
                    )
                else:
                    raise ScannerAuthenticationError(
                        "Nessus requires either API keys (access_key/secret_key) or username/password",
                        scanner_type="nessus",
                    )
            except Exception as e:
                raise ScannerConnectionError(
                    f"Failed to connect to Nessus: {str(e)}",
                    scanner_type="nessus",
                )

        return self._client

    async def test_connection(self) -> bool:
        """Test connection to Nessus server."""
        try:
            client = self._get_client()
            # Try to get server info to verify connection
            server_info = client.server.properties()
            logger.info(
                f"Connected to Nessus: {server_info.get('nessus_ui_version', 'unknown version')}"
            )
            return True
        except ScannerConnectionError:
            raise
        except Exception as e:
            raise ScannerConnectionError(
                f"Failed to connect to Nessus: {str(e)}",
                scanner_type="nessus",
            )

    async def launch_scan(
        self,
        targets: List[str],
        scan_name: str,
        policy_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Launch a new Nessus scan."""
        try:
            client = self._get_client()

            # Get template/policy
            template = kwargs.get("template", "basic")
            folder_id = kwargs.get("folder_id")

            # Create the scan
            scan_config = {
                "name": scan_name,
                "text_targets": ",".join(targets),
            }

            if policy_id:
                scan_config["policy_id"] = int(policy_id)

            # Use built-in template if no policy specified
            if not policy_id:
                # Find template UUID
                templates = client.editor.template_list("scan")
                template_uuid = None
                for t in templates:
                    if t.get("name", "").lower() == template.lower():
                        template_uuid = t.get("uuid")
                        break
                if template_uuid:
                    scan_config["uuid"] = template_uuid

            if folder_id:
                scan_config["folder_id"] = int(folder_id)

            # Create and launch scan
            scan = client.scans.create(**scan_config)
            scan_id = str(scan.get("id") or scan.get("scan", {}).get("id"))

            # Launch the scan
            client.scans.launch(int(scan_id))
            logger.info(f"Launched Nessus scan: {scan_id}")

            return scan_id

        except ScannerConnectionError:
            raise
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to launch Nessus scan: {str(e)}",
                scanner_type="nessus",
            )

    async def get_scan_status(self, scan_id: str) -> ScanProgress:
        """Get the status of a Nessus scan."""
        try:
            client = self._get_client()
            details = client.scans.details(int(scan_id))

            info = details.get("info", {})
            status = info.get("status", "unknown")

            # Map Nessus status to ScanState
            state_map = {
                "pending": ScanState.PENDING,
                "running": ScanState.RUNNING,
                "completed": ScanState.COMPLETED,
                "canceled": ScanState.CANCELLED,
                "aborted": ScanState.CANCELLED,
                "stopped": ScanState.CANCELLED,
                "imported": ScanState.COMPLETED,
                "paused": ScanState.PAUSED,
            }
            state = state_map.get(status.lower(), ScanState.RUNNING)

            # Calculate progress
            hosts = details.get("hosts", [])
            hosts_total = len(hosts)
            hosts_completed = sum(
                1 for h in hosts if h.get("scanprogresscurrent") == "100"
            )

            progress_percent = 0
            if hosts_total > 0:
                progress_percent = int((hosts_completed / hosts_total) * 100)

            return ScanProgress(
                scan_id=scan_id,
                state=state,
                progress_percent=progress_percent,
                hosts_total=hosts_total,
                hosts_completed=hosts_completed,
                message=f"Status: {status}",
            )

        except Exception as e:
            if "not found" in str(e).lower():
                raise ScanNotFoundError(
                    f"Scan {scan_id} not found",
                    scanner_type="nessus",
                    scan_id=scan_id,
                )
            raise ScannerAPIError(
                f"Failed to get scan status: {str(e)}",
                scanner_type="nessus",
            )

    async def get_scan_results(self, scan_id: str) -> ScanResult:
        """Get results from a completed Nessus scan."""
        try:
            client = self._get_client()
            details = client.scans.details(int(scan_id))

            info = details.get("info", {})
            hosts = details.get("hosts", [])
            findings: List[NormalizedFinding] = []

            # Get vulnerabilities for each host
            for host in hosts:
                host_id = host.get("host_id")
                hostname = host.get("hostname") or host.get("host-ip")

                if not host_id:
                    continue

                try:
                    # Get host vulnerabilities
                    host_details = client.scans.host_details(
                        int(scan_id), int(host_id)
                    )
                    vulnerabilities = host_details.get("vulnerabilities", [])

                    for vuln in vulnerabilities:
                        plugin_id = vuln.get("plugin_id")
                        severity = vuln.get("severity", 0)

                        # Get plugin details
                        try:
                            plugin_output = client.scans.plugin_output(
                                int(scan_id), int(host_id), int(plugin_id)
                            )
                        except Exception:
                            plugin_output = {}

                        # Extract CVE from plugin info
                        cve_id = self._extract_cve(vuln, plugin_output)

                        finding = NormalizedFinding(
                            title=vuln.get("plugin_name", "Unknown Vulnerability"),
                            description=plugin_output.get("output", "")
                            or vuln.get("plugin_name", ""),
                            severity=self.SEVERITY_MAP.get(severity, "info"),
                            cvss_score=vuln.get("cvss_score"),
                            cve_id=cve_id,
                            affected_host=hostname,
                            affected_port=vuln.get("port"),
                            protocol=vuln.get("protocol"),
                            solution=plugin_output.get("solution"),
                            plugin_id=str(plugin_id),
                            plugin_name=vuln.get("plugin_name"),
                            plugin_family=vuln.get("plugin_family"),
                            raw_data=vuln,
                        )
                        findings.append(finding)

                except Exception as e:
                    logger.warning(f"Failed to get host details for {hostname}: {e}")
                    continue

            result = ScanResult(
                scan_id=scan_id,
                state=ScanState.COMPLETED,
                findings=findings,
                hosts_scanned=len(hosts),
            )
            result.count_severities()

            return result

        except ScanNotFoundError:
            raise
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to get scan results: {str(e)}",
                scanner_type="nessus",
            )

    async def stop_scan(self, scan_id: str) -> bool:
        """Stop a running Nessus scan."""
        try:
            client = self._get_client()
            client.scans.stop(int(scan_id))
            logger.info(f"Stopped Nessus scan: {scan_id}")
            return True
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to stop scan: {str(e)}",
                scanner_type="nessus",
            )

    def _extract_cve(
        self, vuln: Dict[str, Any], plugin_output: Dict[str, Any]
    ) -> Optional[str]:
        """Extract CVE ID from vulnerability data."""
        # Check common CVE locations
        cve = vuln.get("cve")
        if cve:
            if isinstance(cve, list) and cve:
                return cve[0]
            return str(cve)

        # Try to extract from plugin output
        output = plugin_output.get("output", "")
        if output:
            cve_pattern = r"CVE-\d{4}-\d{4,7}"
            match = re.search(cve_pattern, output)
            if match:
                return match.group(0)

        return None

    async def close(self):
        """Close the Nessus client connection."""
        if self._client:
            try:
                self._client.session.close()
            except Exception:
                pass
            self._client = None
