"""Result normalization utilities for scanner findings."""
import logging
import re
from typing import Any, Dict, List, Optional

from .base import NormalizedFinding, ScanResult

logger = logging.getLogger(__name__)


def normalize_severity(severity: str) -> str:
    """
    Normalize severity strings to standard values.

    Args:
        severity: Any severity string from scanners.

    Returns:
        One of: critical, high, medium, low, info
    """
    if not severity:
        return "info"

    severity_lower = severity.lower().strip()

    # Direct mappings
    if severity_lower in ("critical", "crit", "urgent", "severe"):
        return "critical"
    if severity_lower in ("high", "hi", "important"):
        return "high"
    if severity_lower in ("medium", "med", "moderate", "warning"):
        return "medium"
    if severity_lower in ("low", "lo", "minor"):
        return "low"
    if severity_lower in ("info", "informational", "none", "log", "debug"):
        return "info"

    # Numeric mappings (common in some scanners)
    try:
        num = int(severity_lower)
        if num >= 4:
            return "critical"
        if num == 3:
            return "high"
        if num == 2:
            return "medium"
        if num == 1:
            return "low"
        return "info"
    except ValueError:
        pass

    return "info"


def cvss_to_severity(cvss_score: Optional[float]) -> str:
    """
    Convert CVSS score to severity level.

    Args:
        cvss_score: CVSS score (0.0-10.0)

    Returns:
        Severity level string.
    """
    if cvss_score is None:
        return "info"

    if cvss_score >= 9.0:
        return "critical"
    if cvss_score >= 7.0:
        return "high"
    if cvss_score >= 4.0:
        return "medium"
    if cvss_score >= 0.1:
        return "low"
    return "info"


def extract_cve_ids(text: str) -> List[str]:
    """
    Extract all CVE IDs from a text string.

    Args:
        text: Text that may contain CVE IDs.

    Returns:
        List of CVE IDs found.
    """
    if not text:
        return []

    pattern = r"CVE-\d{4}-\d{4,7}"
    matches = re.findall(pattern, text, re.IGNORECASE)
    # Normalize to uppercase and deduplicate
    return list(set(m.upper() for m in matches))


def deduplicate_findings(findings: List[NormalizedFinding]) -> List[NormalizedFinding]:
    """
    Remove duplicate findings based on title and host.

    Args:
        findings: List of findings that may contain duplicates.

    Returns:
        Deduplicated list of findings.
    """
    seen = set()
    unique_findings = []

    for finding in findings:
        key = (
            finding.title,
            finding.affected_host,
            finding.affected_port,
            finding.cve_id,
        )

        if key not in seen:
            seen.add(key)
            unique_findings.append(finding)

    return unique_findings


def merge_findings(
    findings: List[NormalizedFinding],
    merge_by_cve: bool = False,
) -> List[NormalizedFinding]:
    """
    Merge related findings.

    Args:
        findings: List of findings to merge.
        merge_by_cve: If True, merge findings with same CVE across hosts.

    Returns:
        Merged list of findings.
    """
    if not merge_by_cve:
        return deduplicate_findings(findings)

    # Group by CVE
    cve_groups: Dict[str, List[NormalizedFinding]] = {}
    no_cve_findings: List[NormalizedFinding] = []

    for finding in findings:
        if finding.cve_id:
            if finding.cve_id not in cve_groups:
                cve_groups[finding.cve_id] = []
            cve_groups[finding.cve_id].append(finding)
        else:
            no_cve_findings.append(finding)

    merged = []

    for cve_id, group in cve_groups.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # Merge into single finding with multiple hosts
            base = group[0]
            hosts = set()
            for f in group:
                if f.affected_host:
                    hosts.add(f.affected_host)

            # Use highest severity
            severities = ["critical", "high", "medium", "low", "info"]
            best_severity = base.severity
            for f in group:
                if severities.index(f.severity) < severities.index(best_severity):
                    best_severity = f.severity

            merged_finding = NormalizedFinding(
                title=base.title,
                description=base.description,
                severity=best_severity,
                cvss_score=base.cvss_score,
                cve_id=cve_id,
                affected_host=", ".join(sorted(hosts)) if hosts else None,
                solution=base.solution,
                plugin_id=base.plugin_id,
                plugin_name=base.plugin_name,
                references=list(
                    set(ref for f in group for ref in (f.references or []))
                ),
            )
            merged.append(merged_finding)

    merged.extend(deduplicate_findings(no_cve_findings))
    return merged


def findings_to_dicts(findings: List[NormalizedFinding]) -> List[Dict[str, Any]]:
    """
    Convert list of NormalizedFinding to list of dicts for database storage.

    Args:
        findings: List of NormalizedFinding objects.

    Returns:
        List of dictionaries.
    """
    return [f.to_dict() for f in findings]


def filter_findings_by_severity(
    findings: List[NormalizedFinding],
    min_severity: str = "info",
) -> List[NormalizedFinding]:
    """
    Filter findings to only include those at or above a minimum severity.

    Args:
        findings: List of findings to filter.
        min_severity: Minimum severity to include.

    Returns:
        Filtered list of findings.
    """
    severity_order = ["critical", "high", "medium", "low", "info"]
    min_index = severity_order.index(min_severity)

    return [
        f
        for f in findings
        if severity_order.index(f.severity) <= min_index
    ]


def summarize_results(result: ScanResult) -> Dict[str, Any]:
    """
    Create a summary of scan results for logging/reporting.

    Args:
        result: ScanResult to summarize.

    Returns:
        Summary dictionary.
    """
    return {
        "scan_id": result.scan_id,
        "state": result.state.value,
        "total_findings": len(result.findings),
        "hosts_scanned": result.hosts_scanned,
        "duration_seconds": result.duration_seconds,
        "severity_counts": {
            "critical": result.critical_count,
            "high": result.high_count,
            "medium": result.medium_count,
            "low": result.low_count,
            "info": result.info_count,
        },
        "unique_cves": len(
            set(f.cve_id for f in result.findings if f.cve_id)
        ),
        "affected_hosts": len(
            set(f.affected_host for f in result.findings if f.affected_host)
        ),
    }
