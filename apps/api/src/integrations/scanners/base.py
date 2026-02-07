"""Base classes and dataclasses for scanner integrations."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScannerType(str, Enum):
    """Supported scanner types."""

    NESSUS = "nessus"
    OPENVAS = "openvas"
    QUALYS = "qualys"


class ScanState(str, Enum):
    """State of a scan in the external scanner."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ScannerConfig:
    """Configuration for connecting to a scanner."""

    scanner_type: ScannerType
    base_url: str = ""
    api_key: str = ""
    api_secret: str = ""
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    timeout: int = 60
    extra_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_integration(cls, integration) -> "ScannerConfig":
        """Create ScannerConfig from an Integration model instance."""
        config = integration.config or {}
        return cls(
            scanner_type=ScannerType(integration.integration_type.value),
            base_url=integration.base_url or "",
            api_key=integration.api_key or "",
            api_secret=integration.api_secret or "",
            username=integration.username or "",
            password=integration.password or "",
            verify_ssl=config.get("verify_ssl", True),
            timeout=config.get("timeout_seconds", 60),
            extra_config=config,
        )


@dataclass
class NormalizedFinding:
    """Normalized vulnerability finding from any scanner."""

    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    affected_host: Optional[str] = None
    affected_port: Optional[int] = None
    protocol: Optional[str] = None
    solution: Optional[str] = None
    plugin_id: Optional[str] = None
    plugin_name: Optional[str] = None
    plugin_family: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    references: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "cve_id": self.cve_id,
            "affected_host": self.affected_host,
            "affected_port": self.affected_port,
            "protocol": self.protocol,
            "solution": self.solution,
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "plugin_family": self.plugin_family,
            "references": self.references,
        }


@dataclass
class ScanProgress:
    """Progress information for a running scan."""

    scan_id: str
    state: ScanState
    progress_percent: int = 0
    hosts_total: int = 0
    hosts_completed: int = 0
    current_host: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ScanResult:
    """Complete results from a finished scan."""

    scan_id: str
    state: ScanState
    findings: List[NormalizedFinding] = field(default_factory=list)
    hosts_scanned: int = 0
    duration_seconds: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    error_message: Optional[str] = None

    def count_severities(self):
        """Count findings by severity."""
        self.critical_count = sum(1 for f in self.findings if f.severity == "critical")
        self.high_count = sum(1 for f in self.findings if f.severity == "high")
        self.medium_count = sum(1 for f in self.findings if f.severity == "medium")
        self.low_count = sum(1 for f in self.findings if f.severity == "low")
        self.info_count = sum(1 for f in self.findings if f.severity == "info")


class BaseScannerAdapter(ABC):
    """Abstract base class for scanner adapters."""

    scanner_type: ScannerType

    def __init__(self, config: ScannerConfig):
        """Initialize the adapter with configuration."""
        self.config = config

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the scanner.

        Returns:
            True if connection is successful, raises exception otherwise.
        """
        pass

    @abstractmethod
    async def launch_scan(
        self,
        targets: List[str],
        scan_name: str,
        policy_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Launch a new scan.

        Args:
            targets: List of IP addresses, hostnames, or CIDR ranges.
            scan_name: Name for the scan.
            policy_id: Scanner-specific policy/template ID.
            **kwargs: Additional scanner-specific options.

        Returns:
            The scan ID from the scanner.
        """
        pass

    @abstractmethod
    async def get_scan_status(self, scan_id: str) -> ScanProgress:
        """
        Get the current status of a scan.

        Args:
            scan_id: The scan ID returned from launch_scan.

        Returns:
            ScanProgress with current state and progress.
        """
        pass

    @abstractmethod
    async def get_scan_results(self, scan_id: str) -> ScanResult:
        """
        Get the results of a completed scan.

        Args:
            scan_id: The scan ID returned from launch_scan.

        Returns:
            ScanResult with all findings.
        """
        pass

    @abstractmethod
    async def stop_scan(self, scan_id: str) -> bool:
        """
        Stop a running scan.

        Args:
            scan_id: The scan ID to stop.

        Returns:
            True if scan was stopped successfully.
        """
        pass

    async def close(self):
        """Clean up resources. Override if needed."""
        pass
