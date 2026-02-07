"""
Scanner integrations for vulnerability scanning.

This module provides adapters for various vulnerability scanners:
- Nessus/Tenable (using pyTenable)
- OpenVAS/GVM (using python-gvm)
- Qualys VMDR (using httpx)

Usage:
    from src.integrations.scanners import get_scanner_adapter, ScannerConfig, ScannerType

    # Create config from Integration model
    config = ScannerConfig.from_integration(integration)

    # Get appropriate adapter
    adapter = get_scanner_adapter(config)

    # Use adapter
    scan_id = await adapter.launch_scan(["192.168.1.1"], "My Scan")
    status = await adapter.get_scan_status(scan_id)
    results = await adapter.get_scan_results(scan_id)
"""
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
    ScannerError,
    ScannerAPIError,
    ScannerAuthenticationError,
    ScannerConfigurationError,
    ScannerConnectionError,
    ScannerTimeoutError,
    ScanNotFoundError,
)
from .result_normalizer import (
    normalize_severity,
    cvss_to_severity,
    extract_cve_ids,
    deduplicate_findings,
    merge_findings,
    findings_to_dicts,
    filter_findings_by_severity,
    summarize_results,
)


def get_scanner_adapter(config: ScannerConfig) -> BaseScannerAdapter:
    """
    Factory function to get the appropriate scanner adapter.

    Args:
        config: ScannerConfig with connection details and scanner type.

    Returns:
        Appropriate scanner adapter instance.

    Raises:
        ValueError: If scanner type is not supported.
    """
    if config.scanner_type == ScannerType.NESSUS:
        from .nessus_scanner import NessusAdapter

        return NessusAdapter(config)

    elif config.scanner_type == ScannerType.OPENVAS:
        from .openvas_scanner import OpenVASAdapter

        return OpenVASAdapter(config)

    elif config.scanner_type == ScannerType.QUALYS:
        from .qualys_scanner import QualysAdapter

        return QualysAdapter(config)

    else:
        raise ValueError(f"Unsupported scanner type: {config.scanner_type}")


__all__ = [
    # Base classes
    "BaseScannerAdapter",
    "NormalizedFinding",
    "ScannerConfig",
    "ScannerType",
    "ScanProgress",
    "ScanResult",
    "ScanState",
    # Exceptions
    "ScannerError",
    "ScannerAPIError",
    "ScannerAuthenticationError",
    "ScannerConfigurationError",
    "ScannerConnectionError",
    "ScannerTimeoutError",
    "ScanNotFoundError",
    # Factory
    "get_scanner_adapter",
    # Normalizer utilities
    "normalize_severity",
    "cvss_to_severity",
    "extract_cve_ids",
    "deduplicate_findings",
    "merge_findings",
    "findings_to_dicts",
    "filter_findings_by_severity",
    "summarize_results",
]
