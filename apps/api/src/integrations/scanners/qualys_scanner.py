"""Qualys VMDR scanner adapter using httpx."""
import logging
import re
from typing import Any, Dict, List, Optional

import defusedxml.ElementTree as ET  # noqa: N817

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
    ScannerTimeoutError,
    ScanNotFoundError,
)

logger = logging.getLogger(__name__)


class QualysAdapter(BaseScannerAdapter):
    """Adapter for Qualys VMDR scanner using httpx async client."""

    scanner_type = ScannerType.QUALYS

    # Qualys severity mapping (1-5 to standard severities)
    SEVERITY_MAP = {
        1: "info",
        2: "low",
        3: "medium",
        4: "high",
        5: "critical",
    }

    def __init__(self, config: ScannerConfig):
        super().__init__(config)
        self._client = None

    async def _get_client(self):
        """Get or create httpx async client."""
        if self._client is None:
            try:
                import httpx
            except ImportError:
                raise ScannerConnectionError(
                    "httpx library is not installed. Run: pip install httpx",
                    scanner_type="qualys",
                )

            if not self.config.username or not self.config.password:
                raise ScannerAuthenticationError(
                    "Qualys requires username and password",
                    scanner_type="qualys",
                )

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                auth=(self.config.username, self.config.password),
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
                headers={
                    "X-Requested-With": "ISORA",
                    "Accept": "application/xml",
                },
            )

        return self._client

    async def test_connection(self) -> bool:
        """Test connection to Qualys API."""
        try:
            client = await self._get_client()

            # Test with a simple API call
            response = await client.get("/api/2.0/fo/session/")

            if response.status_code == 401:
                raise ScannerAuthenticationError(
                    "Invalid Qualys credentials",
                    scanner_type="qualys",
                )

            if response.status_code != 200:
                raise ScannerAPIError(
                    f"Qualys API returned status {response.status_code}",
                    scanner_type="qualys",
                    status_code=response.status_code,
                )

            logger.info("Connected to Qualys API")
            return True

        except ScannerAuthenticationError:
            raise
        except ScannerAPIError:
            raise
        except Exception as e:
            raise ScannerConnectionError(
                f"Failed to connect to Qualys: {str(e)}",
                scanner_type="qualys",
            )

    async def launch_scan(
        self,
        targets: List[str],
        scan_name: str,
        policy_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Launch a new Qualys vulnerability scan."""
        try:
            client = await self._get_client()

            # Build scan parameters
            params = {
                "action": "launch",
                "scan_title": scan_name,
                "ip": ",".join(targets),
                "iscanner_name": kwargs.get("scanner_name", "External"),
            }

            # Add option profile if specified
            if policy_id:
                params["option_id"] = policy_id
            elif kwargs.get("option_title"):
                params["option_title"] = kwargs["option_title"]

            # Add priority
            if kwargs.get("priority"):
                params["priority"] = kwargs["priority"]

            response = await client.post(
                "/api/2.0/fo/scan/",
                data=params,
            )

            if response.status_code != 200:
                raise ScannerAPIError(
                    f"Qualys API returned status {response.status_code}: {response.text}",
                    scanner_type="qualys",
                    status_code=response.status_code,
                )

            # Parse XML response
            root = ET.fromstring(response.text)
            scan_ref = root.find(".//VALUE")
            if scan_ref is None or not scan_ref.text:
                # Check for error
                error = root.find(".//TEXT")
                error_msg = error.text if error is not None else "Unknown error"
                raise ScannerAPIError(
                    f"Failed to launch Qualys scan: {error_msg}",
                    scanner_type="qualys",
                )

            scan_id = scan_ref.text
            logger.info(f"Launched Qualys scan: {scan_id}")

            return scan_id

        except ScannerConnectionError:
            raise
        except ScannerAPIError:
            raise
        except ET.ParseError as e:
            raise ScannerAPIError(
                f"Failed to parse Qualys response: {str(e)}",
                scanner_type="qualys",
            )
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to launch Qualys scan: {str(e)}",
                scanner_type="qualys",
            )

    async def get_scan_status(self, scan_id: str) -> ScanProgress:
        """Get the status of a Qualys scan."""
        try:
            client = await self._get_client()

            response = await client.get(
                "/api/2.0/fo/scan/",
                params={
                    "action": "list",
                    "scan_ref": scan_id,
                },
            )

            if response.status_code != 200:
                raise ScannerAPIError(
                    f"Qualys API returned status {response.status_code}",
                    scanner_type="qualys",
                    status_code=response.status_code,
                )

            root = ET.fromstring(response.text)
            scan = root.find(".//SCAN")

            if scan is None:
                raise ScanNotFoundError(
                    f"Scan {scan_id} not found",
                    scanner_type="qualys",
                    scan_id=scan_id,
                )

            status_elem = scan.find("STATUS/STATE")
            status = status_elem.text if status_elem is not None else "Unknown"

            # Map Qualys status to ScanState
            state_map = {
                "Running": ScanState.RUNNING,
                "Paused": ScanState.PAUSED,
                "Canceled": ScanState.CANCELLED,
                "Finished": ScanState.COMPLETED,
                "Error": ScanState.FAILED,
                "Queued": ScanState.PENDING,
                "Loading": ScanState.PENDING,
            }
            state = state_map.get(status, ScanState.RUNNING)

            # Get progress if available
            progress_percent = 0
            if state == ScanState.COMPLETED:
                progress_percent = 100

            # Count hosts
            hosts_total = 0
            hosts_completed = 0
            target_elem = scan.find("TARGET")
            if target_elem is not None and target_elem.text:
                # Estimate from IP list
                hosts_total = len(target_elem.text.split(","))
                if state == ScanState.COMPLETED:
                    hosts_completed = hosts_total

            return ScanProgress(
                scan_id=scan_id,
                state=state,
                progress_percent=progress_percent,
                hosts_total=hosts_total,
                hosts_completed=hosts_completed,
                message=f"Status: {status}",
            )

        except ScanNotFoundError:
            raise
        except ET.ParseError as e:
            raise ScannerAPIError(
                f"Failed to parse Qualys response: {str(e)}",
                scanner_type="qualys",
            )
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to get scan status: {str(e)}",
                scanner_type="qualys",
            )

    async def get_scan_results(self, scan_id: str) -> ScanResult:
        """Get results from a completed Qualys scan."""
        try:
            client = await self._get_client()

            # Fetch scan results
            response = await client.post(
                "/api/2.0/fo/scan/",
                data={
                    "action": "fetch",
                    "scan_ref": scan_id,
                    "output_format": "xml",
                },
            )

            if response.status_code != 200:
                raise ScannerAPIError(
                    f"Qualys API returned status {response.status_code}",
                    scanner_type="qualys",
                    status_code=response.status_code,
                )

            root = ET.fromstring(response.text)
            findings: List[NormalizedFinding] = []
            hosts_scanned = 0

            # Parse hosts and their vulnerabilities
            for host in root.findall(".//IP"):
                hosts_scanned += 1
                host_ip = host.get("value") or host.get("name")

                # Parse vulnerabilities (VULN elements)
                for vuln in host.findall(".//VULN"):
                    finding = self._parse_vuln(vuln, host_ip)
                    if finding:
                        findings.append(finding)

                # Parse CAT elements (vulnerability categories)
                for cat in host.findall(".//CAT"):
                    for vuln in cat.findall(".//VULN"):
                        finding = self._parse_vuln(vuln, host_ip)
                        if finding:
                            findings.append(finding)

            result = ScanResult(
                scan_id=scan_id,
                state=ScanState.COMPLETED,
                findings=findings,
                hosts_scanned=hosts_scanned,
            )
            result.count_severities()

            return result

        except ScanNotFoundError:
            raise
        except ET.ParseError as e:
            raise ScannerAPIError(
                f"Failed to parse Qualys response: {str(e)}",
                scanner_type="qualys",
            )
        except Exception as e:
            raise ScannerAPIError(
                f"Failed to get scan results: {str(e)}",
                scanner_type="qualys",
            )

    def _parse_vuln(
        self, vuln_elem, host_ip: str
    ) -> Optional[NormalizedFinding]:
        """Parse a Qualys VULN element into a NormalizedFinding."""
        try:
            qid = vuln_elem.get("number") or vuln_elem.find("QID")
            if qid is not None and hasattr(qid, "text"):
                qid = qid.text

            title = self._get_text(vuln_elem, "TITLE") or f"QID {qid}"
            description = self._get_text(vuln_elem, "DIAGNOSIS") or ""

            # Get severity
            severity_elem = vuln_elem.find("SEVERITY")
            severity_num = 1
            if severity_elem is not None and severity_elem.text:
                try:
                    severity_num = int(severity_elem.text)
                except ValueError:
                    pass
            severity = self.SEVERITY_MAP.get(severity_num, "info")

            # Get CVSS score
            cvss_score = None
            cvss_elem = vuln_elem.find("CVSS_SCORE") or vuln_elem.find("CVSS/BASE")
            if cvss_elem is not None and cvss_elem.text:
                try:
                    cvss_score = float(cvss_elem.text)
                except ValueError:
                    pass

            # Get CVE
            cve_id = None
            cve_elem = vuln_elem.find("CVE_ID_LIST/CVE_ID/ID")
            if cve_elem is not None and cve_elem.text:
                cve_id = cve_elem.text
            else:
                # Try alternate location
                cve_elem = vuln_elem.find("CVE_ID")
                if cve_elem is not None and cve_elem.text:
                    cve_id = cve_elem.text

            # Get port
            port = None
            protocol = None
            port_elem = vuln_elem.find("PORT")
            if port_elem is not None and port_elem.text:
                try:
                    port = int(port_elem.text)
                except ValueError:
                    pass
            protocol_elem = vuln_elem.find("PROTOCOL")
            if protocol_elem is not None:
                protocol = protocol_elem.text

            # Get solution
            solution = self._get_text(vuln_elem, "SOLUTION")

            return NormalizedFinding(
                title=title,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                cve_id=cve_id,
                affected_host=host_ip,
                affected_port=port,
                protocol=protocol,
                solution=solution,
                plugin_id=str(qid) if qid else None,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Qualys vuln: {e}")
            return None

    def _get_text(self, elem, tag: str) -> Optional[str]:
        """Safely get text from an XML element."""
        child = elem.find(tag)
        return child.text if child is not None else None

    async def stop_scan(self, scan_id: str) -> bool:
        """Stop a running Qualys scan."""
        try:
            client = await self._get_client()

            response = await client.post(
                "/api/2.0/fo/scan/",
                data={
                    "action": "cancel",
                    "scan_ref": scan_id,
                },
            )

            if response.status_code != 200:
                raise ScannerAPIError(
                    f"Failed to cancel scan: {response.text}",
                    scanner_type="qualys",
                    status_code=response.status_code,
                )

            logger.info(f"Stopped Qualys scan: {scan_id}")
            return True

        except Exception as e:
            raise ScannerAPIError(
                f"Failed to stop scan: {str(e)}",
                scanner_type="qualys",
            )

    async def close(self):
        """Close the httpx client."""
        if self._client:
            await self._client.aclose()
            self._client = None
