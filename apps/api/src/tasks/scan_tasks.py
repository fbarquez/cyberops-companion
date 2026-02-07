"""
Vulnerability scan background tasks.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from src.celery_app import celery_app, TaskState
from src.config import settings
from src.core.scan_progress import publish_scan_progress

if TYPE_CHECKING:
    from src.integrations.scanners import BaseScannerAdapter
    from src.models.vulnerability import VulnerabilityScan

logger = logging.getLogger(__name__)

# Scanner polling settings
SCANNER_POLL_INTERVAL = getattr(settings, "SCANNER_POLL_INTERVAL", 30)
SCANNER_MAX_RUNTIME = getattr(settings, "SCANNER_MAX_RUNTIME", 14400)  # 4 hours


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_db_session():
    """Get a database session for async operations."""
    from src.db.database import async_session_maker
    async with async_session_maker() as session:
        yield session


async def _get_scanner_integration(db, scanner: str, tenant_id: str = None):
    """
    Get integration configuration for a scanner type.

    Returns the Integration model if configured, None otherwise.
    """
    from src.models.integrations import Integration, IntegrationType, IntegrationStatus
    from sqlalchemy import select

    # Map scanner names to IntegrationType
    scanner_type_map = {
        "nessus": IntegrationType.NESSUS,
        "openvas": IntegrationType.OPENVAS,
        "qualys": IntegrationType.QUALYS,
        "rapid7": IntegrationType.RAPID7,
    }

    integration_type = scanner_type_map.get(scanner.lower())
    if not integration_type:
        return None

    # Query for active integration
    query = select(Integration).where(
        Integration.integration_type == integration_type,
        Integration.status == IntegrationStatus.ACTIVE,
        Integration.is_enabled == True,
    )

    if tenant_id:
        query = query.where(Integration.tenant_id == tenant_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _execute_real_scan(
    adapter: "BaseScannerAdapter",
    scan: "VulnerabilityScan",
    db,
    task_instance=None,
) -> List[Dict[str, Any]]:
    """
    Execute a real scan using a scanner adapter.

    Args:
        adapter: The scanner adapter to use.
        scan: The VulnerabilityScan model instance.
        db: Database session.
        task_instance: Celery task instance for progress updates.

    Returns:
        List of finding dictionaries.
    """
    from src.integrations.scanners import ScanState, summarize_results

    # Parse targets from scan configuration
    targets = []
    if scan.targets:
        if isinstance(scan.targets, list):
            targets = scan.targets
        elif isinstance(scan.targets, str):
            targets = [t.strip() for t in scan.targets.split(",")]

    if not targets:
        raise ValueError("No targets specified for scan")

    # Publish scan started event
    publish_scan_progress(
        scan_id=scan.id,
        event="started",
        progress_percent=0,
        state="running",
        hosts_total=len(targets),
        hosts_completed=0,
        message=f"Launching {adapter.scanner_type.value} scan",
    )

    # Launch the scan
    logger.info(f"Launching {adapter.scanner_type.value} scan for targets: {targets}")
    external_scan_id = await adapter.launch_scan(
        targets=targets,
        scan_name=scan.name,
        policy_id=scan.policy_id if hasattr(scan, "policy_id") else None,
    )

    logger.info(f"External scan ID: {external_scan_id}")

    # Poll for completion
    start_time = datetime.utcnow()
    poll_count = 0
    max_polls = SCANNER_MAX_RUNTIME // SCANNER_POLL_INTERVAL

    while poll_count < max_polls:
        poll_count += 1
        await asyncio.sleep(SCANNER_POLL_INTERVAL)

        # Get scan status
        progress = await adapter.get_scan_status(external_scan_id)
        logger.info(
            f"Scan {external_scan_id} progress: {progress.progress_percent}% "
            f"({progress.state.value})"
        )

        # Update Celery task state
        if task_instance:
            task_instance.update_state(
                state=TaskState.PROGRESS,
                meta={
                    "scan_id": scan.id,
                    "external_scan_id": external_scan_id,
                    "progress_percent": progress.progress_percent,
                    "hosts_total": progress.hosts_total,
                    "hosts_completed": progress.hosts_completed,
                    "status": progress.state.value,
                },
            )

        # Publish progress to WebSocket via Redis
        publish_scan_progress(
            scan_id=scan.id,
            event="progress",
            progress_percent=progress.progress_percent,
            state=progress.state.value,
            hosts_total=progress.hosts_total,
            hosts_completed=progress.hosts_completed,
            current_host=progress.current_host,
            message=progress.message or f"Scanning... {progress.progress_percent}%",
        )

        # Check if complete
        if progress.state == ScanState.COMPLETED:
            break
        elif progress.state == ScanState.FAILED:
            raise Exception(f"Scan failed: {progress.message}")
        elif progress.state == ScanState.CANCELLED:
            raise Exception("Scan was cancelled")

        # Check timeout
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        if elapsed >= SCANNER_MAX_RUNTIME:
            logger.warning(f"Scan {external_scan_id} timed out after {elapsed}s")
            await adapter.stop_scan(external_scan_id)
            raise TimeoutError(f"Scan timed out after {SCANNER_MAX_RUNTIME} seconds")

    # Get results
    result = await adapter.get_scan_results(external_scan_id)
    logger.info(f"Scan results: {summarize_results(result)}")

    # Convert NormalizedFinding to dicts
    findings = [f.to_dict() for f in result.findings]
    return findings


async def _execute_scan_async(scan_id: str, task_id: str, task_instance=None) -> Dict[str, Any]:
    """
    Execute vulnerability scan asynchronously.

    This function:
    1. Checks for configured scanner integration
    2. If integration exists, uses real scanner adapter
    3. Otherwise falls back to simulation
    """
    from src.db.database import async_session_maker
    from src.models.vulnerability import VulnerabilityScan, ScanStatus, Vulnerability, VulnerabilitySeverity
    from sqlalchemy import select

    async with async_session_maker() as db:
        # Get scan details
        result = await db.execute(
            select(VulnerabilityScan).where(VulnerabilityScan.id == scan_id)
        )
        scan = result.scalar_one_or_none()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        if scan.status != ScanStatus.RUNNING:
            raise ValueError(f"Scan {scan_id} is not in RUNNING state")

        logger.info(f"Executing scan: {scan.name} (type: {scan.scan_type}, scanner: {scan.scanner})")

        # Store task ID for tracking
        scan.celery_task_id = task_id
        await db.commit()

        adapter = None
        try:
            # Check for scanner integration
            integration = await _get_scanner_integration(
                db, scan.scanner, getattr(scan, "tenant_id", None)
            )

            if integration:
                # Use real scanner
                logger.info(f"Using real scanner integration: {integration.name}")
                from src.integrations.scanners import get_scanner_adapter, ScannerConfig

                config = ScannerConfig.from_integration(integration)
                adapter = get_scanner_adapter(config)

                # Test connection first
                await adapter.test_connection()

                # Execute real scan
                findings = await _execute_real_scan(adapter, scan, db, task_instance)
            else:
                # Fallback to simulation
                logger.info("No scanner integration configured, using simulation")
                findings = await _simulate_scan_execution(scan)

            # Process findings
            findings_count = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }

            for finding in findings:
                # Create vulnerability record
                vuln = Vulnerability(
                    title=finding["title"],
                    description=finding["description"],
                    severity=VulnerabilitySeverity(finding["severity"]),
                    cve_id=finding.get("cve_id"),
                    cvss_score=finding.get("cvss_score"),
                    affected_asset_id=scan.target_asset_id,
                    discovered_by=scan.scanner,
                    discovered_at=datetime.utcnow(),
                    source="scan",
                )
                db.add(vuln)

                # Count by severity
                severity = finding["severity"]
                if severity in findings_count:
                    findings_count[severity] += 1

            # Update scan with results
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.total_findings = sum(findings_count.values())
            scan.critical_count = findings_count["critical"]
            scan.high_count = findings_count["high"]
            scan.medium_count = findings_count["medium"]
            scan.low_count = findings_count["low"]
            scan.info_count = findings_count["info"]

            await db.commit()

            logger.info(f"Scan {scan_id} completed: {scan.total_findings} findings")

            # Publish scan completed event
            publish_scan_progress(
                scan_id=scan_id,
                event="completed",
                progress_percent=100,
                state="completed",
                message="Scan completed successfully",
                total_findings=scan.total_findings,
                severity_counts=findings_count,
            )

            return {
                "scan_id": scan_id,
                "status": "completed",
                "findings_count": findings_count,
                "total_findings": scan.total_findings,
                "used_real_scanner": integration is not None,
            }

        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {str(e)}")

            # Mark scan as failed
            scan.status = ScanStatus.FAILED
            scan.completed_at = datetime.utcnow()
            scan.error_message = str(e)
            await db.commit()

            # Publish scan failed event
            publish_scan_progress(
                scan_id=scan_id,
                event="failed",
                progress_percent=0,
                state="failed",
                error=str(e),
                message="Scan failed",
            )

            raise

        finally:
            # Clean up adapter
            if adapter:
                await adapter.close()


async def _simulate_scan_execution(scan) -> List[Dict[str, Any]]:
    """
    Simulate scan execution for demo purposes.

    In production, replace this with actual scanner integration:
    - Nessus: Use pyTenable library
    - OpenVAS: Use python-gvm library
    - Qualys: Use Qualys API
    - Trivy: Use trivy CLI for container scans
    """
    import random
    import asyncio

    # Parse targets for progress simulation
    targets = []
    if scan.targets:
        if isinstance(scan.targets, list):
            targets = scan.targets
        elif isinstance(scan.targets, str):
            targets = [t.strip() for t in scan.targets.split(",")]
    hosts_total = max(len(targets), 3)

    # Publish scan started
    publish_scan_progress(
        scan_id=scan.id,
        event="started",
        progress_percent=0,
        state="running",
        hosts_total=hosts_total,
        hosts_completed=0,
        message="Starting simulated scan",
    )

    # Simulate scan duration with progress updates
    total_duration = random.uniform(5, 15)
    steps = 5
    step_duration = total_duration / steps

    for i in range(steps):
        await asyncio.sleep(step_duration)
        progress = int((i + 1) / steps * 100)
        hosts_completed = int(hosts_total * progress / 100)

        publish_scan_progress(
            scan_id=scan.id,
            event="progress",
            progress_percent=progress,
            state="running",
            hosts_total=hosts_total,
            hosts_completed=hosts_completed,
            message=f"Simulated scan progress: {progress}%",
        )

    # Generate sample findings based on scan type
    sample_vulns = {
        "network": [
            {"title": "SSH Weak Cipher Suites", "severity": "medium", "cve_id": None, "cvss_score": 5.3},
            {"title": "SSL/TLS Certificate Expiring Soon", "severity": "low", "cve_id": None, "cvss_score": 3.1},
            {"title": "Open SMB Port", "severity": "high", "cve_id": "CVE-2017-0144", "cvss_score": 8.1},
        ],
        "web_app": [
            {"title": "Cross-Site Scripting (XSS)", "severity": "high", "cve_id": None, "cvss_score": 6.1},
            {"title": "SQL Injection", "severity": "critical", "cve_id": None, "cvss_score": 9.8},
            {"title": "Missing Security Headers", "severity": "low", "cve_id": None, "cvss_score": 2.5},
            {"title": "Outdated jQuery Version", "severity": "medium", "cve_id": "CVE-2020-11022", "cvss_score": 6.1},
        ],
        "container": [
            {"title": "Base Image Vulnerability", "severity": "high", "cve_id": "CVE-2024-1234", "cvss_score": 7.5},
            {"title": "Exposed Secrets in Layer", "severity": "critical", "cve_id": None, "cvss_score": 9.1},
            {"title": "Outdated Package", "severity": "medium", "cve_id": "CVE-2023-5678", "cvss_score": 5.5},
        ],
        "code": [
            {"title": "Hardcoded Credentials", "severity": "critical", "cve_id": None, "cvss_score": 9.0},
            {"title": "Insecure Deserialization", "severity": "high", "cve_id": None, "cvss_score": 8.0},
            {"title": "Use of Deprecated Function", "severity": "low", "cve_id": None, "cvss_score": 3.0},
        ],
        "cloud": [
            {"title": "S3 Bucket Public Access", "severity": "critical", "cve_id": None, "cvss_score": 9.5},
            {"title": "IAM Policy Too Permissive", "severity": "high", "cve_id": None, "cvss_score": 7.8},
            {"title": "Unencrypted EBS Volume", "severity": "medium", "cve_id": None, "cvss_score": 5.0},
        ],
        "compliance": [
            {"title": "Password Policy Non-Compliant", "severity": "medium", "cve_id": None, "cvss_score": 4.5},
            {"title": "Missing MFA Configuration", "severity": "high", "cve_id": None, "cvss_score": 7.0},
            {"title": "Audit Logging Disabled", "severity": "medium", "cve_id": None, "cvss_score": 5.5},
        ],
    }

    scan_type = scan.scan_type.value if hasattr(scan.scan_type, 'value') else str(scan.scan_type)
    base_findings = sample_vulns.get(scan_type, sample_vulns["network"])

    # Randomly select some findings
    num_findings = random.randint(1, len(base_findings))
    selected = random.sample(base_findings, num_findings)

    # Add description to each finding
    for finding in selected:
        finding["description"] = f"Vulnerability detected during {scan_type} scan: {finding['title']}"

    return selected


@celery_app.task(
    bind=True,
    name="src.tasks.scan_tasks.execute_vulnerability_scan",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def execute_vulnerability_scan(self, scan_id: str) -> Dict[str, Any]:
    """
    Execute a vulnerability scan.

    Args:
        scan_id: The ID of the scan to execute

    Returns:
        Dict with scan results
    """
    logger.info(f"Starting scan task for scan_id: {scan_id}, task_id: {self.request.id}")

    try:
        # Update task state to show progress
        self.update_state(
            state=TaskState.PROGRESS,
            meta={"scan_id": scan_id, "status": "initializing"}
        )

        # Run the async scan execution (pass self for progress updates)
        result = run_async(_execute_scan_async(scan_id, self.request.id, self))

        return result

    except ValueError as e:
        # Don't retry on validation errors
        logger.error(f"Scan {scan_id} validation error: {str(e)}")
        return {"scan_id": scan_id, "status": "failed", "error": str(e)}

    except Exception as e:
        logger.error(f"Scan {scan_id} error: {str(e)}")
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            return {"scan_id": scan_id, "status": "failed", "error": f"Max retries exceeded: {str(e)}"}


@celery_app.task(
    bind=True,
    name="src.tasks.scan_tasks.sync_nvd_updates",
    max_retries=3,
    default_retry_delay=300,
)
def sync_nvd_updates(self, days_back: int = 7) -> Dict[str, Any]:
    """
    Sync recent CVE updates from NVD.

    Args:
        days_back: Number of days to look back for updates

    Returns:
        Dict with sync results
    """
    logger.info(f"Starting NVD sync for last {days_back} days")

    async def _sync():
        from src.services.nvd_service import get_nvd_service
        from src.db.database import async_session_maker
        from datetime import datetime, timedelta

        nvd_service = get_nvd_service()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Search for recently modified CVEs
        results = await nvd_service.search_cves(
            last_mod_start_date=start_date.strftime("%Y-%m-%dT00:00:00.000"),
            last_mod_end_date=end_date.strftime("%Y-%m-%dT23:59:59.999"),
            results_per_page=100,
        )

        updated_count = 0
        if results and "vulnerabilities" in results:
            from src.services.vulnerability_service import VulnerabilityService

            async with async_session_maker() as db:
                vuln_service = VulnerabilityService()
                for cve_item in results["vulnerabilities"]:
                    cve_id = cve_item.get("cve", {}).get("id")
                    if cve_id:
                        await vuln_service.enrich_cve(db, cve_id, create_if_missing=False)
                        updated_count += 1

        return {
            "status": "completed",
            "days_back": days_back,
            "cves_checked": results.get("totalResults", 0) if results else 0,
            "cves_updated": updated_count,
        }

    try:
        result = run_async(_sync())
        logger.info(f"NVD sync completed: {result}")
        return result
    except Exception as e:
        logger.error(f"NVD sync failed: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    name="src.tasks.scan_tasks.cancel_scan",
)
def cancel_scan(scan_id: str) -> Dict[str, Any]:
    """
    Cancel a running scan.

    Args:
        scan_id: The ID of the scan to cancel

    Returns:
        Dict with cancellation status
    """
    logger.info(f"Cancelling scan: {scan_id}")

    async def _cancel():
        from src.db.database import async_session_maker
        from src.models.vulnerability import VulnerabilityScan, ScanStatus
        from sqlalchemy import select

        async with async_session_maker() as db:
            result = await db.execute(
                select(VulnerabilityScan).where(VulnerabilityScan.id == scan_id)
            )
            scan = result.scalar_one_or_none()

            if not scan:
                return {"scan_id": scan_id, "status": "not_found"}

            if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
                return {"scan_id": scan_id, "status": "already_finished"}

            # Revoke Celery task if running
            if scan.celery_task_id:
                celery_app.control.revoke(scan.celery_task_id, terminate=True)

            scan.status = ScanStatus.CANCELLED
            scan.completed_at = datetime.utcnow()
            scan.error_message = "Scan cancelled by user"
            await db.commit()

            # Publish scan cancelled event
            publish_scan_progress(
                scan_id=scan_id,
                event="cancelled",
                progress_percent=0,
                state="cancelled",
                message="Scan cancelled by user",
            )

            return {"scan_id": scan_id, "status": "cancelled"}

    return run_async(_cancel())
