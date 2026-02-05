"""Attack Path Analysis API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import (
    CurrentUser, DBSession, UserWithTenant,
    get_current_user_with_tenant
)
from src.services.attack_path_service import AttackPathService
from src.services.pdf_reports import AttackPathReportGenerator
from src.schemas.attack_paths import (
    GraphScopeType, GraphStatus, PathStatus, SimulationType,
    JewelType, EntryType, ExposureLevel,
    AttackGraphCreate, AttackGraphUpdate, AttackGraphResponse,
    AttackGraphListResponse, AttackGraphStatistics,
    AttackPathResponse, AttackPathListResponse, AttackPathStatusUpdate,
    CrownJewelCreate, CrownJewelUpdate, CrownJewelResponse, CrownJewelListResponse,
    EntryPointCreate, EntryPointUpdate, EntryPointResponse, EntryPointListResponse,
    AttackPathDashboard, ChokepointListResponse, ChokepointInfo,
    AttackPathSimulationCreate, AttackPathSimulationResponse, AttackPathSimulationListResponse,
)

router = APIRouter(prefix="/attack-paths")


def get_service(db: AsyncSession) -> AttackPathService:
    """Get Attack Path service instance."""
    return AttackPathService(db)


# ========== Dashboard Endpoint ==========

@router.get("/dashboard", response_model=AttackPathDashboard)
async def get_dashboard(
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Get attack path analysis dashboard statistics.

    Returns overview of:
    - Total graphs, paths, and risk distribution
    - Entry points and crown jewels counts
    - Top chokepoints
    - Paths by status
    """
    user, context = user_context
    service = get_service(db)
    stats = await service.get_dashboard(context.tenant_id)

    return AttackPathDashboard(
        total_graphs=stats["total_graphs"],
        total_paths=stats["total_paths"],
        critical_paths=stats["critical_paths"],
        high_risk_paths=stats["high_risk_paths"],
        entry_points_count=stats["entry_points_count"],
        crown_jewels_count=stats["crown_jewels_count"],
        top_chokepoints=stats["top_chokepoints"],
        recent_simulations=[],
        risk_distribution=stats["risk_distribution"],
        paths_by_status=stats["paths_by_status"],
    )


@router.get("/chokepoints", response_model=ChokepointListResponse)
async def get_chokepoints(
    db: DBSession,
    user_context: UserWithTenant,
    limit: int = Query(10, ge=1, le=50, description="Number of chokepoints to return"),
):
    """
    Get top chokepoints for remediation priority.

    Chokepoints are assets that appear in multiple attack paths.
    Securing these assets has the highest impact on reducing attack surface.
    """
    user, context = user_context
    service = get_service(db)
    chokepoints = await service.get_chokepoints(context.tenant_id, limit)

    return ChokepointListResponse(
        chokepoints=[ChokepointInfo(**c) for c in chokepoints],
        total=len(chokepoints)
    )


# ========== Attack Graph Endpoints ==========

@router.get("/graphs", response_model=AttackGraphListResponse)
async def list_graphs(
    db: DBSession,
    user_context: UserWithTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[GraphStatus] = Query(None, description="Filter by status"),
):
    """List attack graphs for the current tenant."""
    user, context = user_context
    service = get_service(db)
    graphs, total = await service.list_graphs(
        context.tenant_id, page, page_size, status
    )

    return AttackGraphListResponse(
        graphs=[AttackGraphResponse.model_validate(g) for g in graphs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/graphs", response_model=AttackGraphResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(
    data: AttackGraphCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Create and compute a new attack graph.

    This initiates the graph building process which:
    - Loads assets from CMDB
    - Builds edges from relationships
    - Enriches with vulnerabilities
    - Computes attack paths
    """
    user, context = user_context
    service = get_service(db)
    graph = await service.create_graph(context.tenant_id, str(user.id), data)
    return AttackGraphResponse.model_validate(graph)


@router.get("/graphs/{graph_id}", response_model=AttackGraphResponse)
async def get_graph(
    graph_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific attack graph."""
    user, context = user_context
    service = get_service(db)
    graph = await service.get_graph(context.tenant_id, graph_id)

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack graph not found"
        )

    return AttackGraphResponse.model_validate(graph)


@router.put("/graphs/{graph_id}", response_model=AttackGraphResponse)
async def update_graph(
    graph_id: str,
    data: AttackGraphUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update an attack graph."""
    user, context = user_context
    service = get_service(db)
    graph = await service.update_graph(context.tenant_id, graph_id, data)

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack graph not found"
        )

    return AttackGraphResponse.model_validate(graph)


@router.delete("/graphs/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(
    graph_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Delete an attack graph and all associated paths."""
    user, context = user_context
    service = get_service(db)
    deleted = await service.delete_graph(context.tenant_id, graph_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack graph not found"
        )


@router.post("/graphs/{graph_id}/refresh", response_model=AttackGraphResponse)
async def refresh_graph(
    graph_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Recompute an attack graph with latest data.

    Use this when underlying CMDB or vulnerability data has changed.
    """
    user, context = user_context
    service = get_service(db)
    graph = await service.refresh_graph(context.tenant_id, graph_id)

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack graph not found"
        )

    return AttackGraphResponse.model_validate(graph)


# ========== Attack Path Endpoints ==========

@router.get("/graphs/{graph_id}/paths", response_model=AttackPathListResponse)
async def list_paths(
    graph_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_risk_score: Optional[float] = Query(None, ge=0, le=10, description="Minimum risk score"),
    status: Optional[PathStatus] = Query(None, description="Filter by status"),
):
    """List attack paths for a graph, ordered by risk score."""
    user, context = user_context
    service = get_service(db)
    paths, total = await service.list_paths(
        context.tenant_id, graph_id, page, page_size, min_risk_score, status
    )

    return AttackPathListResponse(
        paths=[AttackPathResponse.model_validate(p) for p in paths],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/paths/{path_id}", response_model=AttackPathResponse)
async def get_path(
    path_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get detailed information about a specific attack path."""
    user, context = user_context
    service = get_service(db)
    path = await service.get_path(context.tenant_id, path_id)

    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack path not found"
        )

    return AttackPathResponse.model_validate(path)


@router.put("/paths/{path_id}/status", response_model=AttackPathResponse)
async def update_path_status(
    path_id: str,
    data: AttackPathStatusUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Update the status of an attack path.

    Status options:
    - active: Path is valid and needs attention
    - mitigated: Path has been remediated
    - accepted: Risk has been accepted
    - false_positive: Path is not actually exploitable
    """
    user, context = user_context
    service = get_service(db)
    path = await service.update_path_status(
        context.tenant_id, path_id, data, user.full_name or user.email
    )

    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack path not found"
        )

    return AttackPathResponse.model_validate(path)


# ========== Crown Jewel Endpoints ==========

@router.get("/crown-jewels", response_model=CrownJewelListResponse)
async def list_crown_jewels(
    db: DBSession,
    user_context: UserWithTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    jewel_type: Optional[JewelType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List all designated crown jewels."""
    user, context = user_context
    service = get_service(db)
    jewels, total = await service.list_crown_jewels(
        context.tenant_id, page, page_size, jewel_type, is_active
    )

    return CrownJewelListResponse(
        crown_jewels=[CrownJewelResponse.model_validate(j) for j in jewels],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/crown-jewels", response_model=CrownJewelResponse, status_code=status.HTTP_201_CREATED)
async def create_crown_jewel(
    data: CrownJewelCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Designate an asset as a crown jewel.

    Crown jewels are critical assets that represent high-value targets
    for attackers (databases with PII, AD controllers, key systems, etc.)
    """
    user, context = user_context
    service = get_service(db)
    jewel = await service.create_crown_jewel(context.tenant_id, str(user.id), data)
    return CrownJewelResponse.model_validate(jewel)


@router.get("/crown-jewels/{jewel_id}", response_model=CrownJewelResponse)
async def get_crown_jewel(
    jewel_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific crown jewel."""
    user, context = user_context
    service = get_service(db)
    jewel = await service.get_crown_jewel(context.tenant_id, jewel_id)

    if not jewel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crown jewel not found"
        )

    return CrownJewelResponse.model_validate(jewel)


@router.put("/crown-jewels/{jewel_id}", response_model=CrownJewelResponse)
async def update_crown_jewel(
    jewel_id: str,
    data: CrownJewelUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update a crown jewel."""
    user, context = user_context
    service = get_service(db)
    jewel = await service.update_crown_jewel(context.tenant_id, jewel_id, data)

    if not jewel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crown jewel not found"
        )

    return CrownJewelResponse.model_validate(jewel)


@router.delete("/crown-jewels/{jewel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crown_jewel(
    jewel_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Remove a crown jewel designation."""
    user, context = user_context
    service = get_service(db)
    deleted = await service.delete_crown_jewel(context.tenant_id, jewel_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crown jewel not found"
        )


# ========== Entry Point Endpoints ==========

@router.get("/entry-points", response_model=EntryPointListResponse)
async def list_entry_points(
    db: DBSession,
    user_context: UserWithTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entry_type: Optional[EntryType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """List all designated entry points."""
    user, context = user_context
    service = get_service(db)
    points, total = await service.list_entry_points(
        context.tenant_id, page, page_size, entry_type, is_active
    )

    return EntryPointListResponse(
        entry_points=[EntryPointResponse.model_validate(p) for p in points],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/entry-points", response_model=EntryPointResponse, status_code=status.HTTP_201_CREATED)
async def create_entry_point(
    data: EntryPointCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Designate an asset as an entry point.

    Entry points are assets that could be the initial foothold for an attacker
    (internet-facing servers, VPN gateways, email servers, etc.)
    """
    user, context = user_context
    service = get_service(db)
    point = await service.create_entry_point(context.tenant_id, str(user.id), data)
    return EntryPointResponse.model_validate(point)


@router.get("/entry-points/{point_id}", response_model=EntryPointResponse)
async def get_entry_point(
    point_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific entry point."""
    user, context = user_context
    service = get_service(db)
    point = await service.get_entry_point(context.tenant_id, point_id)

    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry point not found"
        )

    return EntryPointResponse.model_validate(point)


@router.put("/entry-points/{point_id}", response_model=EntryPointResponse)
async def update_entry_point(
    point_id: str,
    data: EntryPointUpdate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Update an entry point."""
    user, context = user_context
    service = get_service(db)
    point = await service.update_entry_point(context.tenant_id, point_id, data)

    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry point not found"
        )

    return EntryPointResponse.model_validate(point)


@router.delete("/entry-points/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry_point(
    point_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Remove an entry point designation."""
    user, context = user_context
    service = get_service(db)
    deleted = await service.delete_entry_point(context.tenant_id, point_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry point not found"
        )


# ========== Simulation Endpoints ==========

@router.get("/simulations", response_model=AttackPathSimulationListResponse)
async def list_simulations(
    db: DBSession,
    user_context: UserWithTenant,
    graph_id: Optional[str] = Query(None, description="Filter by graph ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List what-if simulations."""
    user, context = user_context
    service = get_service(db)
    simulations, total = await service.list_simulations(
        context.tenant_id, graph_id, page, page_size
    )

    return AttackPathSimulationListResponse(
        simulations=[AttackPathSimulationResponse.model_validate(s) for s in simulations],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/simulations", response_model=AttackPathSimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    data: AttackPathSimulationCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    """
    Create and run a what-if simulation.

    Simulation types:
    - patch_vulnerability: Simulate patching specific CVEs
    - segment_network: Simulate isolating an asset
    - add_control: Simulate adding a security control (MFA, firewall, etc.)
    - compromise_asset: Simulate what happens if an asset is compromised
    """
    user, context = user_context
    service = get_service(db)
    simulation = await service.create_simulation(context.tenant_id, str(user.id), data)
    return AttackPathSimulationResponse.model_validate(simulation)


@router.get("/simulations/{simulation_id}", response_model=AttackPathSimulationResponse)
async def get_simulation(
    simulation_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Get a specific simulation and its results."""
    user, context = user_context
    service = get_service(db)
    simulation = await service.get_simulation(context.tenant_id, simulation_id)

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )

    return AttackPathSimulationResponse.model_validate(simulation)


@router.delete("/simulations/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simulation(
    simulation_id: str,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Delete a simulation."""
    user, context = user_context
    service = get_service(db)
    deleted = await service.delete_simulation(context.tenant_id, simulation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )


# ========== Export Endpoints ==========

@router.get("/graphs/{graph_id}/export")
async def export_graph_report(
    graph_id: str,
    db: DBSession,
    user_context: UserWithTenant,
    include_paths: bool = Query(True, description="Include attack paths section"),
    include_assets: bool = Query(True, description="Include crown jewels and entry points"),
    include_recommendations: bool = Query(True, description="Include recommendations section"),
):
    """
    Export attack path analysis as a PDF report.

    Generates a comprehensive PDF report including:
    - Executive summary with risk overview
    - Attack graph statistics
    - Critical attack paths listing
    - Crown jewels and entry points inventory
    - Chokepoint analysis
    - Remediation recommendations
    """
    user, context = user_context
    service = get_service(db)

    # Get graph
    graph = await service.get_graph(context.tenant_id, graph_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack graph not found"
        )

    # Get paths
    paths, _ = await service.list_paths(
        context.tenant_id, graph_id, page=1, page_size=100
    )

    # Get crown jewels
    crown_jewels, _ = await service.list_crown_jewels(
        context.tenant_id, page=1, page_size=50
    )

    # Get entry points
    entry_points, _ = await service.list_entry_points(
        context.tenant_id, page=1, page_size=50
    )

    # Get chokepoints
    chokepoints = await service.get_chokepoints(context.tenant_id, limit=20)

    # Get simulations for this graph
    simulations, _ = await service.list_simulations(
        context.tenant_id, graph_id, page=1, page_size=20
    )

    # Convert models to dicts
    graph_dict = {
        "id": str(graph.id),
        "name": graph.name,
        "description": graph.description,
        "status": graph.status.value if hasattr(graph.status, 'value') else str(graph.status),
        "total_nodes": graph.total_nodes,
        "total_edges": graph.total_edges,
        "computed_at": graph.computed_at,
    }

    paths_list = [
        {
            "id": str(p.id),
            "name": p.name,
            "entry_point_name": p.entry_point_name,
            "target_name": p.target_name,
            "hop_count": p.hop_count,
            "risk_score": float(p.risk_score) if p.risk_score else 0,
            "exploitable_vulns": p.exploitable_vulns,
            "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
        }
        for p in paths
    ]

    crown_jewels_list = [
        {
            "id": str(j.id),
            "asset_id": j.asset_id,
            "asset_name": getattr(j, 'asset_name', None),
            "jewel_type": j.jewel_type.value if hasattr(j.jewel_type, 'value') else str(j.jewel_type),
            "business_impact": j.business_impact.value if hasattr(j.business_impact, 'value') else str(j.business_impact),
            "data_classification": j.data_classification.value if hasattr(j.data_classification, 'value') else None,
            "business_owner": j.business_owner,
        }
        for j in crown_jewels
    ]

    entry_points_list = [
        {
            "id": str(e.id),
            "asset_id": e.asset_id,
            "asset_name": getattr(e, 'asset_name', None),
            "entry_type": e.entry_type.value if hasattr(e.entry_type, 'value') else str(e.entry_type),
            "exposure_level": e.exposure_level.value if hasattr(e.exposure_level, 'value') else str(e.exposure_level),
            "authentication_required": e.authentication_required,
            "mfa_enabled": e.mfa_enabled,
            "known_vulnerabilities": e.known_vulnerabilities,
        }
        for e in entry_points
    ]

    simulations_list = [
        {
            "id": str(s.id),
            "name": s.name,
            "simulation_type": s.simulation_type.value if hasattr(s.simulation_type, 'value') else str(s.simulation_type),
            "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
            "original_paths_count": s.original_paths_count,
            "paths_eliminated": s.paths_eliminated,
            "risk_reduction_percent": float(s.risk_reduction_percent) if s.risk_reduction_percent else 0,
            "recommendation": s.recommendation,
        }
        for s in simulations
    ]

    # Generate PDF
    try:
        generator = AttackPathReportGenerator()
        pdf_content = generator.generate_report(
            graph=graph_dict,
            paths=paths_list,
            crown_jewels=crown_jewels_list,
            entry_points=entry_points_list,
            chokepoints=chokepoints,
            simulations=simulations_list,
            include_paths=include_paths,
            include_assets=include_assets,
            include_recommendations=include_recommendations,
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF generation is not available. Please install reportlab."
        )

    # Return PDF
    filename = f"attack-path-report-{graph.name.replace(' ', '-').lower()}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
