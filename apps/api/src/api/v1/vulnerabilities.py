"""
Vulnerability Management API Endpoints.

REST API for vulnerability management operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.services.vulnerability_service import VulnerabilityService
from src.schemas.vulnerability import (
    # Asset schemas
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse,
    # Vulnerability schemas
    VulnerabilityCreate, VulnerabilityUpdate, VulnerabilityStatusUpdate,
    VulnerabilityResponse, VulnerabilityListResponse,
    VulnerabilityCommentCreate, VulnerabilityCommentResponse,
    # Scan schemas
    ScanCreate, ScanResponse, ScanListResponse,
    ScanScheduleCreate, ScanScheduleResponse,
    # Other schemas
    CVEResponse, VulnerabilityStats, VulnerabilityImport, ImportResult
)

router = APIRouter()
service = VulnerabilityService()


# ==================== Asset Endpoints ====================

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new asset."""
    asset = await service.create_asset(db, data, current_user.id)
    return AssetResponse(
        **{k: v for k, v in asset.__dict__.items() if not k.startswith('_')},
        vulnerability_count=len(asset.vulnerabilities) if asset.vulnerabilities else 0
    )


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    search: Optional[str] = Query(None, description="Search by name, hostname, IP"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List assets with filtering and pagination."""
    assets, total = await service.list_assets(
        db, search=search, asset_type=asset_type, criticality=criticality,
        environment=environment, is_active=is_active, page=page, page_size=page_size
    )
    return AssetListResponse(
        assets=[
            AssetResponse(
                **{k: v for k, v in a.__dict__.items() if not k.startswith('_')},
                vulnerability_count=len(a.vulnerabilities) if hasattr(a, 'vulnerabilities') and a.vulnerabilities else 0
            )
            for a in assets
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an asset by ID."""
    asset = await service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse(
        **{k: v for k, v in asset.__dict__.items() if not k.startswith('_')},
        vulnerability_count=len(asset.vulnerabilities) if asset.vulnerabilities else 0
    )


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an asset."""
    asset = await service.update_asset(db, asset_id, data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse(
        **{k: v for k, v in asset.__dict__.items() if not k.startswith('_')},
        vulnerability_count=len(asset.vulnerabilities) if asset.vulnerabilities else 0
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an asset."""
    if not await service.delete_asset(db, asset_id):
        raise HTTPException(status_code=404, detail="Asset not found")


# ==================== Vulnerability Endpoints ====================

@router.post("/", response_model=VulnerabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_vulnerability(
    data: VulnerabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vulnerability."""
    vuln = await service.create_vulnerability(db, data, current_user.id)
    return _vuln_to_response(vuln)


@router.get("/", response_model=VulnerabilityListResponse)
async def list_vulnerabilities(
    search: Optional[str] = Query(None, description="Search by title, description"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    scan_id: Optional[str] = Query(None, description="Filter by scan"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    overdue_only: bool = Query(False, description="Show only overdue vulnerabilities"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List vulnerabilities with filtering and pagination."""
    vulns, total = await service.list_vulnerabilities(
        db, search=search, severity=severity, status=status,
        asset_id=asset_id, scan_id=scan_id, assigned_to=assigned_to,
        overdue_only=overdue_only, page=page, page_size=page_size
    )
    return VulnerabilityListResponse(
        vulnerabilities=[_vuln_to_response(v) for v in vulns],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=VulnerabilityStats)
async def get_vulnerability_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vulnerability management statistics."""
    stats = await service.get_statistics(db)
    # Convert recent vulnerabilities to response format
    stats['recent_vulnerabilities'] = [_vuln_to_response(v) for v in stats.get('recent_vulnerabilities', [])]
    return VulnerabilityStats(**stats)


@router.get("/{vuln_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vuln_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a vulnerability by ID."""
    vuln = await service.get_vulnerability(db, vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return _vuln_to_response(vuln)


@router.patch("/{vuln_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vuln_id: str,
    data: VulnerabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a vulnerability."""
    vuln = await service.update_vulnerability(db, vuln_id, data, current_user.id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return _vuln_to_response(vuln)


@router.post("/{vuln_id}/status", response_model=VulnerabilityResponse)
async def update_vulnerability_status(
    vuln_id: str,
    data: VulnerabilityStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update vulnerability status."""
    vuln = await service.update_vulnerability_status(db, vuln_id, data, current_user.id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return _vuln_to_response(vuln)


@router.post("/{vuln_id}/comments", response_model=VulnerabilityCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_vulnerability_comment(
    vuln_id: str,
    data: VulnerabilityCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a vulnerability."""
    # Verify vulnerability exists
    vuln = await service.get_vulnerability(db, vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    comment = await service.add_comment(db, vuln_id, data, current_user.id)
    return VulnerabilityCommentResponse(
        id=comment.id,
        vulnerability_id=comment.vulnerability_id,
        content=comment.content,
        comment_type=comment.comment_type,
        created_at=comment.created_at,
        created_by=comment.created_by
    )


@router.delete("/{vuln_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vulnerability(
    vuln_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a vulnerability."""
    if not await service.delete_vulnerability(db, vuln_id):
        raise HTTPException(status_code=404, detail="Vulnerability not found")


# ==================== Scan Endpoints ====================

@router.post("/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    data: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vulnerability scan."""
    scan = await service.create_scan(db, data, current_user.id)
    return ScanResponse(**{k: v for k, v in scan.__dict__.items() if not k.startswith('_')})


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    scan_type: Optional[str] = Query(None, description="Filter by scan type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List vulnerability scans."""
    scans, total = await service.list_scans(
        db, scan_type=scan_type, status=status, page=page, page_size=page_size
    )
    return ScanListResponse(
        scans=[ScanResponse(**{k: v for k, v in s.__dict__.items() if not k.startswith('_')}) for s in scans],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a scan by ID."""
    scan = await service.get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResponse(**{k: v for k, v in scan.__dict__.items() if not k.startswith('_')})


@router.post("/scans/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a pending scan."""
    scan = await service.start_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=400, detail="Scan cannot be started")
    return ScanResponse(**{k: v for k, v in scan.__dict__.items() if not k.startswith('_')})


# ==================== Import Endpoints ====================

@router.post("/import", response_model=ImportResult)
async def import_vulnerabilities(
    data: VulnerabilityImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import vulnerabilities from scanner output."""
    result = await service.import_scan_results(db, data, current_user.id)
    return ImportResult(**result)


# ==================== CVE / NVD Endpoints ====================

@router.get("/cve/{cve_id}")
async def lookup_cve(
    cve_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lookup CVE information from NVD (National Vulnerability Database).

    Fetches comprehensive data including:
    - CVE details and description
    - CVSS scores (v2.0, v3.0, v3.1)
    - EPSS (Exploit Prediction Scoring System) data
    - CISA KEV (Known Exploited Vulnerabilities) status
    - CWE mappings
    - References and affected products

    Rate limits apply (5 requests/30s without API key, 50 with key).
    """
    result = await service.lookup_cve(db, cve_id.upper())
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"CVE {cve_id} not found in NVD or invalid format"
        )
    return result


@router.post("/cve/{cve_id}/enrich")
async def enrich_cve(
    cve_id: str,
    create_if_missing: bool = Query(True, description="Create CVE entry if not in database"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enrich a CVE entry with data from NVD.

    If the CVE exists in the database, updates it with fresh data.
    If create_if_missing is True and CVE doesn't exist, creates a new entry.

    Returns the enriched CVE entry.
    """
    cve_entry = await service.enrich_cve(db, cve_id.upper(), create_if_missing)
    if not cve_entry:
        raise HTTPException(
            status_code=404,
            detail=f"CVE {cve_id} not found in NVD"
        )
    return CVEResponse(**{k: v for k, v in cve_entry.__dict__.items() if not k.startswith('_')})


@router.get("/cve/search/")
async def search_cves(
    keyword: Optional[str] = Query(None, description="Keyword search in CVE descriptions"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    days: Optional[int] = Query(None, ge=1, le=365, description="CVEs published in last N days"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Search CVEs in NVD database.

    Supports filtering by:
    - Keyword search in descriptions
    - Severity level
    - Publication date range

    Note: Rate limits apply. Consider caching results.
    """
    from src.services.nvd_service import get_nvd_service
    from datetime import datetime, timedelta

    nvd_service = get_nvd_service()

    pub_start = None
    pub_end = None
    if days:
        pub_end = datetime.utcnow()
        pub_start = pub_end - timedelta(days=days)

    result = await nvd_service.search_cves(
        keyword=keyword,
        cvss_severity=severity,
        pub_start_date=pub_start,
        pub_end_date=pub_end,
        results_per_page=limit
    )

    return result


@router.get("/kev/catalog")
async def get_kev_catalog(
    current_user: User = Depends(get_current_user)
):
    """
    Get CISA KEV (Known Exploited Vulnerabilities) catalog.

    Returns a list of all known exploited vulnerabilities that
    require immediate attention according to CISA.

    This endpoint is cached for 1 hour.
    """
    from src.services.nvd_service import get_nvd_service

    nvd_service = get_nvd_service()
    catalog = await nvd_service.get_kev_catalog()

    return {
        "total": len(catalog),
        "vulnerabilities": catalog
    }


@router.get("/nvd/status")
async def nvd_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check NVD API configuration status.
    """
    from src.config import settings

    return {
        "api_key_configured": bool(settings.NVD_API_KEY),
        "rate_limit": "50 requests/30s" if settings.NVD_API_KEY else "5 requests/30s",
        "endpoints": {
            "nvd_api": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "epss_api": "https://api.first.org/data/v1/epss",
            "kev_catalog": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        }
    }


# ==================== Helper Functions ====================

def _vuln_to_response(vuln) -> VulnerabilityResponse:
    """Convert vulnerability model to response schema."""
    return VulnerabilityResponse(
        id=vuln.id,
        title=vuln.title,
        description=vuln.description,
        severity=vuln.severity,
        status=vuln.status,
        cvss_score=vuln.cvss_score,
        cvss_vector=vuln.cvss_vector,
        risk_score=vuln.risk_score,
        vulnerability_type=vuln.vulnerability_type,
        affected_component=vuln.affected_component,
        affected_version=vuln.affected_version,
        detected_by=vuln.detected_by,
        detection_method=vuln.detection_method,
        first_detected=vuln.first_detected,
        last_detected=vuln.last_detected,
        proof=vuln.proof,
        remediation_steps=vuln.remediation_steps,
        remediation_deadline=vuln.remediation_deadline,
        remediated_at=vuln.remediated_at,
        risk_accepted_at=vuln.risk_accepted_at,
        risk_acceptance_reason=vuln.risk_acceptance_reason,
        scan_id=vuln.scan_id,
        assigned_to=vuln.assigned_to,
        tags=vuln.tags or [],
        created_at=vuln.created_at,
        updated_at=vuln.updated_at,
        affected_assets=[
            AssetResponse(
                **{k: v for k, v in a.__dict__.items() if not k.startswith('_')},
                vulnerability_count=0
            )
            for a in (vuln.affected_assets or [])
        ],
        cves=[
            CVEResponse(**{k: v for k, v in c.__dict__.items() if not k.startswith('_')})
            for c in (vuln.cves or [])
        ]
    )
