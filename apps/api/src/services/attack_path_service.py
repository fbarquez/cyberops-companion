"""
Attack Path Analysis Service.

Business logic for attack path analysis, graph building, and risk scoring.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from collections import defaultdict
import logging

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.attack_paths import (
    AttackGraph, AttackPath, AttackPathSimulation, CrownJewel, EntryPoint,
    GraphScopeType, GraphStatus, PathStatus, SimulationType, SimulationStatus,
    JewelType, BusinessImpact, EntryType, ExposureLevel, TargetCriticality
)
from src.models.vulnerability import Asset, Vulnerability, CVEEntry
from src.schemas.attack_paths import (
    AttackGraphCreate, AttackGraphUpdate,
    CrownJewelCreate, CrownJewelUpdate,
    EntryPointCreate, EntryPointUpdate,
    AttackPathSimulationCreate, AttackPathStatusUpdate,
)

logger = logging.getLogger(__name__)


class AttackPathService:
    """Service for Attack Path Analysis operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Attack Graph Operations ==========

    async def list_graphs(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[GraphStatus] = None,
    ) -> Tuple[List[AttackGraph], int]:
        """List attack graphs for a tenant."""
        query = select(AttackGraph).where(AttackGraph.tenant_id == tenant_id)

        if status:
            query = query.where(AttackGraph.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Paginate
        query = query.order_by(AttackGraph.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        graphs = list(result.scalars().all())

        return graphs, total or 0

    async def get_graph(self, tenant_id: str, graph_id: str) -> Optional[AttackGraph]:
        """Get a specific attack graph."""
        query = select(AttackGraph).where(
            and_(
                AttackGraph.id == graph_id,
                AttackGraph.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_graph(
        self,
        tenant_id: str,
        user_id: str,
        data: AttackGraphCreate,
    ) -> AttackGraph:
        """Create a new attack graph and initiate computation."""
        graph = AttackGraph(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            scope_type=data.scope_type,
            scope_filter=data.scope_filter,
            status=GraphStatus.COMPUTING,
            created_by=user_id,
        )

        self.db.add(graph)
        await self.db.commit()
        await self.db.refresh(graph)

        # Build the graph
        await self.build_graph(graph)

        return graph

    async def update_graph(
        self,
        tenant_id: str,
        graph_id: str,
        data: AttackGraphUpdate,
    ) -> Optional[AttackGraph]:
        """Update an attack graph."""
        graph = await self.get_graph(tenant_id, graph_id)
        if not graph:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(graph, field, value)

        await self.db.commit()
        await self.db.refresh(graph)
        return graph

    async def delete_graph(self, tenant_id: str, graph_id: str) -> bool:
        """Delete an attack graph."""
        graph = await self.get_graph(tenant_id, graph_id)
        if not graph:
            return False

        await self.db.delete(graph)
        await self.db.commit()
        return True

    async def refresh_graph(self, tenant_id: str, graph_id: str) -> Optional[AttackGraph]:
        """Recompute an attack graph."""
        graph = await self.get_graph(tenant_id, graph_id)
        if not graph:
            return None

        graph.status = GraphStatus.COMPUTING
        await self.db.commit()

        await self.build_graph(graph)
        return graph

    async def build_graph(self, graph: AttackGraph) -> None:
        """
        Build the attack graph from CMDB assets and relationships.

        This method:
        1. Loads assets as nodes
        2. Builds edges from relationships
        3. Enriches with vulnerabilities
        4. Marks entry points and crown jewels
        5. Calculates node risk scores
        """
        start_time = datetime.utcnow()

        try:
            # Get entry points and crown jewels for this tenant
            entry_points = await self.list_entry_points_internal(graph.tenant_id)
            crown_jewels = await self.list_crown_jewels_internal(graph.tenant_id)

            entry_point_ids = {ep.asset_id for ep in entry_points if ep.is_active}
            crown_jewel_ids = {cj.asset_id for cj in crown_jewels if cj.is_active}

            # Load assets
            asset_query = select(Asset).where(
                and_(
                    Asset.tenant_id == graph.tenant_id,
                    Asset.is_active == True
                )
            )
            result = await self.db.execute(asset_query)
            assets = list(result.scalars().all())

            # Build nodes
            nodes = []
            for asset in assets:
                # Get vulnerabilities for this asset
                vulns = await self._get_asset_vulnerabilities(str(asset.id))

                node = {
                    "id": str(asset.id),
                    "name": asset.name,
                    "type": asset.asset_type.value if asset.asset_type else "unknown",
                    "criticality": asset.criticality.value if asset.criticality else "medium",
                    "zone": asset.network_zone or "default",
                    "trust_level": asset.trust_level.value if asset.trust_level else "medium",
                    "vulnerabilities": vulns,
                    "is_entry_point": str(asset.id) in entry_point_ids,
                    "is_crown_jewel": str(asset.id) in crown_jewel_ids,
                    "risk_score": self._calculate_node_risk(asset, vulns),
                    "ip_address": asset.ip_address,
                    "hostname": asset.hostname,
                }
                nodes.append(node)

            # Build edges from connection data and relationships
            edges = await self._build_edges(graph.tenant_id, assets)

            # Update graph with computed data
            graph.nodes = nodes
            graph.edges = edges
            graph.total_nodes = len(nodes)
            graph.total_edges = len(edges)
            graph.entry_points_count = len(entry_point_ids)
            graph.crown_jewels_count = len(crown_jewel_ids)
            graph.computed_at = datetime.utcnow()
            graph.computation_duration_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            graph.status = GraphStatus.READY
            graph.last_cmdb_sync = datetime.utcnow()
            graph.is_stale = False
            graph.data_sources = {
                "cmdb": True,
                "vulnerabilities": True,
                "entry_points": len(entry_point_ids),
                "crown_jewels": len(crown_jewel_ids),
            }

            await self.db.commit()

            # Now compute attack paths
            await self._compute_attack_paths(graph)

        except Exception as e:
            logger.error(f"Error building graph {graph.id}: {e}")
            graph.status = GraphStatus.ERROR
            graph.error_message = str(e)
            await self.db.commit()
            raise

    async def _get_asset_vulnerabilities(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get vulnerabilities for an asset."""
        query = select(Vulnerability).where(
            Vulnerability.affected_assets.any(Asset.id == asset_id)
        )
        result = await self.db.execute(query)
        vulns = result.scalars().all()

        return [
            {
                "id": str(v.id),
                "cve_id": None,  # Would need to join with CVE
                "cvss_score": v.cvss_score or 0,
                "severity": v.severity.value if v.severity else "medium",
                "status": v.status.value if v.status else "open",
                "epss_score": 0,  # Would need to get from CVE
                "in_kev": False,  # Would need to check
            }
            for v in vulns
        ]

    def _calculate_node_risk(self, asset: Asset, vulns: List[Dict]) -> float:
        """Calculate risk score for a node based on criticality and vulnerabilities."""
        # Base score from criticality
        criticality_scores = {
            "critical": 4.0,
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0,
        }
        base_score = criticality_scores.get(
            asset.criticality.value if asset.criticality else "medium", 2.0
        )

        # Add vulnerability contribution
        vuln_score = 0.0
        for vuln in vulns:
            cvss = vuln.get("cvss_score", 0)
            if cvss >= 9.0:
                vuln_score += 2.0
            elif cvss >= 7.0:
                vuln_score += 1.5
            elif cvss >= 4.0:
                vuln_score += 1.0
            else:
                vuln_score += 0.5

        # Combine scores (max 10)
        return min(base_score + vuln_score, 10.0)

    async def _build_edges(self, tenant_id: str, assets: List[Asset]) -> List[Dict]:
        """Build edges from asset connectivity data."""
        edges = []
        asset_map = {str(a.id): a for a in assets}

        for asset in assets:
            asset_id = str(asset.id)

            # Outbound connections
            outbound = asset.outbound_connections or []
            for target_id in outbound:
                if target_id in asset_map:
                    edges.append({
                        "source": asset_id,
                        "target": target_id,
                        "type": "network",
                        "direction": "unidirectional",
                        "requires_auth": True,
                        "traversal_difficulty": 1.0,
                    })

            # Admin access relationships
            admin_access = asset.admin_access_from or []
            for source_id in admin_access:
                if source_id in asset_map:
                    edges.append({
                        "source": source_id,
                        "target": asset_id,
                        "type": "admin_access",
                        "direction": "unidirectional",
                        "requires_auth": True,
                        "traversal_difficulty": 0.5,  # Easier with admin access
                    })

            # User access relationships
            user_access = asset.user_access_from or []
            for source_id in user_access:
                if source_id in asset_map:
                    edges.append({
                        "source": source_id,
                        "target": asset_id,
                        "type": "user_access",
                        "direction": "unidirectional",
                        "requires_auth": True,
                        "traversal_difficulty": 1.5,  # Harder with just user access
                    })

        return edges

    async def _compute_attack_paths(self, graph: AttackGraph) -> None:
        """Compute all attack paths in the graph."""
        nodes = graph.nodes or []
        edges = graph.edges or []

        entry_points = [n for n in nodes if n.get("is_entry_point")]
        crown_jewels = [n for n in nodes if n.get("is_crown_jewel")]

        if not entry_points or not crown_jewels:
            return

        # Build adjacency list
        adjacency = defaultdict(list)
        for edge in edges:
            adjacency[edge["source"]].append({
                "target": edge["target"],
                "edge": edge,
            })

        # Find paths using BFS
        path_counter = 0
        for entry in entry_points:
            for jewel in crown_jewels:
                paths = self._bfs_find_paths(
                    adjacency,
                    entry["id"],
                    jewel["id"],
                    max_depth=10
                )

                for path_nodes in paths:
                    path_counter += 1
                    path_edges = self._get_path_edges(path_nodes, edges)

                    # Calculate risk score
                    risk_score = self._calculate_path_risk(
                        path_nodes, path_edges, nodes
                    )

                    if risk_score >= 3.0:  # Only save significant paths
                        attack_path = AttackPath(
                            id=str(uuid4()),
                            tenant_id=graph.tenant_id,
                            graph_id=str(graph.id),
                            path_id=f"PATH-{path_counter:04d}",
                            name=f"{entry['name']} → {jewel['name']}",
                            entry_point_id=entry["id"],
                            entry_point_name=entry["name"],
                            entry_point_type=entry["type"],
                            target_id=jewel["id"],
                            target_name=jewel["name"],
                            target_type=jewel["type"],
                            target_criticality=TargetCriticality(
                                jewel.get("criticality", "high")
                            ),
                            path_nodes=path_nodes,
                            path_edges=path_edges,
                            hop_count=len(path_nodes) - 1,
                            risk_score=risk_score,
                            exploitability_score=self._calculate_exploitability(
                                path_nodes, nodes
                            ),
                            impact_score=self._calculate_impact(jewel),
                            vulns_in_path=self._get_vulns_in_path(path_nodes, nodes),
                            exploitable_vulns=self._count_exploitable_vulns(
                                path_nodes, nodes
                            ),
                            chokepoints=self._identify_path_chokepoints(
                                path_nodes, nodes
                            ),
                            status=PathStatus.ACTIVE,
                        )
                        self.db.add(attack_path)

        await self.db.commit()

    def _bfs_find_paths(
        self,
        adjacency: Dict,
        start: str,
        end: str,
        max_depth: int = 10
    ) -> List[List[str]]:
        """Find all paths from start to end using BFS."""
        all_paths = []
        queue = [(start, [start])]
        visited_states = set()

        while queue:
            current, path = queue.pop(0)

            if current == end:
                all_paths.append(path)
                if len(all_paths) >= 10:  # Limit paths per entry-target pair
                    break
                continue

            if len(path) >= max_depth:
                continue

            state = (current, len(path))
            if state in visited_states:
                continue
            visited_states.add(state)

            for neighbor_info in adjacency.get(current, []):
                neighbor = neighbor_info["target"]
                if neighbor not in path:  # Avoid cycles
                    queue.append((neighbor, path + [neighbor]))

        return all_paths

    def _get_path_edges(self, path_nodes: List[str], edges: List[Dict]) -> List[Dict]:
        """Get edges for a path."""
        path_edges = []
        for i in range(len(path_nodes) - 1):
            source = path_nodes[i]
            target = path_nodes[i + 1]
            for edge in edges:
                if edge["source"] == source and edge["target"] == target:
                    path_edges.append(edge)
                    break
        return path_edges

    def _calculate_path_risk(
        self,
        path_nodes: List[str],
        path_edges: List[Dict],
        nodes: List[Dict]
    ) -> float:
        """
        Calculate risk score for a path.

        Formula: (Exploitability × Impact × Accessibility) / Difficulty
        """
        node_map = {n["id"]: n for n in nodes}

        # Exploitability
        exploitability = self._calculate_exploitability(path_nodes, nodes)

        # Impact (based on target criticality)
        target = node_map.get(path_nodes[-1], {})
        impact_map = {"critical": 10, "high": 8, "medium": 5, "low": 2}
        impact = impact_map.get(target.get("criticality", "medium"), 5)

        # Accessibility (fewer hops = more accessible)
        hop_factor = max(0, 10 - len(path_nodes) + 1)
        auth_factor = sum(1 for e in path_edges if not e.get("requires_auth", True))
        accessibility = (hop_factor + auth_factor * 2) / 2

        # Difficulty (based on controls)
        difficulty = 1.0
        for edge in path_edges:
            difficulty += edge.get("traversal_difficulty", 1.0) * 0.5

        # Final calculation
        raw_score = (exploitability * impact * accessibility) / (difficulty * 10)
        return round(min(raw_score, 10.0), 2)

    def _calculate_exploitability(self, path_nodes: List[str], nodes: List[Dict]) -> float:
        """Calculate exploitability score based on vulnerabilities in path."""
        node_map = {n["id"]: n for n in nodes}
        score = 0.0

        for node_id in path_nodes:
            node = node_map.get(node_id, {})
            for vuln in node.get("vulnerabilities", []):
                cvss = vuln.get("cvss_score", 0)
                if cvss >= 9.0:
                    score += 2.0
                elif cvss >= 7.0:
                    score += 1.5
                elif cvss >= 4.0:
                    score += 1.0

        return min(score, 10.0)

    def _calculate_impact(self, target: Dict) -> float:
        """Calculate impact score based on target criticality."""
        impact_map = {"critical": 10, "high": 8, "medium": 5, "low": 2}
        return impact_map.get(target.get("criticality", "medium"), 5)

    def _get_vulns_in_path(self, path_nodes: List[str], nodes: List[Dict]) -> List[Dict]:
        """Get all vulnerabilities in a path."""
        node_map = {n["id"]: n for n in nodes}
        vulns = []
        for node_id in path_nodes:
            node = node_map.get(node_id, {})
            for vuln in node.get("vulnerabilities", []):
                vulns.append({**vuln, "node_id": node_id})
        return vulns

    def _count_exploitable_vulns(self, path_nodes: List[str], nodes: List[Dict]) -> int:
        """Count exploitable vulnerabilities in path."""
        node_map = {n["id"]: n for n in nodes}
        count = 0
        for node_id in path_nodes:
            node = node_map.get(node_id, {})
            for vuln in node.get("vulnerabilities", []):
                if vuln.get("epss_score", 0) > 0.1 or vuln.get("in_kev"):
                    count += 1
        return count

    def _identify_path_chokepoints(
        self, path_nodes: List[str], nodes: List[Dict]
    ) -> List[Dict]:
        """Identify potential chokepoints in a path."""
        node_map = {n["id"]: n for n in nodes}
        chokepoints = []

        # Middle nodes (not entry or target) are potential chokepoints
        for node_id in path_nodes[1:-1]:
            node = node_map.get(node_id, {})
            chokepoints.append({
                "asset_id": node_id,
                "asset_name": node.get("name", "Unknown"),
                "reason": "Intermediate node in attack path",
            })

        return chokepoints

    # ========== Attack Path Operations ==========

    async def list_paths(
        self,
        tenant_id: str,
        graph_id: str,
        page: int = 1,
        page_size: int = 20,
        min_risk_score: Optional[float] = None,
        status: Optional[PathStatus] = None,
    ) -> Tuple[List[AttackPath], int]:
        """List attack paths for a graph."""
        query = select(AttackPath).where(
            and_(
                AttackPath.tenant_id == tenant_id,
                AttackPath.graph_id == graph_id
            )
        )

        if min_risk_score is not None:
            query = query.where(AttackPath.risk_score >= min_risk_score)

        if status:
            query = query.where(AttackPath.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Paginate and order by risk
        query = query.order_by(AttackPath.risk_score.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        paths = list(result.scalars().all())

        return paths, total or 0

    async def get_path(self, tenant_id: str, path_id: str) -> Optional[AttackPath]:
        """Get a specific attack path."""
        query = select(AttackPath).where(
            and_(
                AttackPath.id == path_id,
                AttackPath.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_path_status(
        self,
        tenant_id: str,
        path_id: str,
        data: AttackPathStatusUpdate,
        user_name: str,
    ) -> Optional[AttackPath]:
        """Update attack path status."""
        path = await self.get_path(tenant_id, path_id)
        if not path:
            return None

        path.status = data.status
        if data.status == PathStatus.MITIGATED:
            path.mitigated_at = datetime.utcnow()
            path.mitigated_by = user_name

        await self.db.commit()
        await self.db.refresh(path)
        return path

    # ========== Crown Jewel Operations ==========

    async def list_crown_jewels_internal(self, tenant_id: str) -> List[CrownJewel]:
        """Internal method to list all crown jewels."""
        query = select(CrownJewel).where(CrownJewel.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_crown_jewels(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        jewel_type: Optional[JewelType] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[CrownJewel], int]:
        """List crown jewels with pagination."""
        query = select(CrownJewel).where(CrownJewel.tenant_id == tenant_id)

        if jewel_type:
            query = query.where(CrownJewel.jewel_type == jewel_type)
        if is_active is not None:
            query = query.where(CrownJewel.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(CrownJewel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        jewels = list(result.scalars().all())

        return jewels, total or 0

    async def get_crown_jewel(self, tenant_id: str, jewel_id: str) -> Optional[CrownJewel]:
        """Get a specific crown jewel."""
        query = select(CrownJewel).where(
            and_(
                CrownJewel.id == jewel_id,
                CrownJewel.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_crown_jewel(
        self,
        tenant_id: str,
        user_id: str,
        data: CrownJewelCreate,
    ) -> CrownJewel:
        """Create a new crown jewel."""
        jewel = CrownJewel(
            id=str(uuid4()),
            tenant_id=tenant_id,
            asset_id=data.asset_id,
            jewel_type=data.jewel_type,
            business_impact=data.business_impact,
            data_classification=data.data_classification,
            description=data.description,
            business_owner=data.business_owner,
            data_types=data.data_types,
            compliance_scope=data.compliance_scope,
            estimated_value=data.estimated_value,
            created_by=user_id,
        )

        self.db.add(jewel)
        await self.db.commit()
        await self.db.refresh(jewel)
        return jewel

    async def update_crown_jewel(
        self,
        tenant_id: str,
        jewel_id: str,
        data: CrownJewelUpdate,
    ) -> Optional[CrownJewel]:
        """Update a crown jewel."""
        jewel = await self.get_crown_jewel(tenant_id, jewel_id)
        if not jewel:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(jewel, field, value)

        await self.db.commit()
        await self.db.refresh(jewel)
        return jewel

    async def delete_crown_jewel(self, tenant_id: str, jewel_id: str) -> bool:
        """Delete a crown jewel."""
        jewel = await self.get_crown_jewel(tenant_id, jewel_id)
        if not jewel:
            return False

        await self.db.delete(jewel)
        await self.db.commit()
        return True

    # ========== Entry Point Operations ==========

    async def list_entry_points_internal(self, tenant_id: str) -> List[EntryPoint]:
        """Internal method to list all entry points."""
        query = select(EntryPoint).where(EntryPoint.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_entry_points(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        entry_type: Optional[EntryType] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[EntryPoint], int]:
        """List entry points with pagination."""
        query = select(EntryPoint).where(EntryPoint.tenant_id == tenant_id)

        if entry_type:
            query = query.where(EntryPoint.entry_type == entry_type)
        if is_active is not None:
            query = query.where(EntryPoint.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(EntryPoint.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        points = list(result.scalars().all())

        return points, total or 0

    async def get_entry_point(self, tenant_id: str, point_id: str) -> Optional[EntryPoint]:
        """Get a specific entry point."""
        query = select(EntryPoint).where(
            and_(
                EntryPoint.id == point_id,
                EntryPoint.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_entry_point(
        self,
        tenant_id: str,
        user_id: str,
        data: EntryPointCreate,
    ) -> EntryPoint:
        """Create a new entry point."""
        point = EntryPoint(
            id=str(uuid4()),
            tenant_id=tenant_id,
            asset_id=data.asset_id,
            entry_type=data.entry_type,
            exposure_level=data.exposure_level,
            protocols_exposed=data.protocols_exposed,
            ports_exposed=data.ports_exposed,
            authentication_required=data.authentication_required,
            mfa_enabled=data.mfa_enabled,
            description=data.description,
            last_pentest_date=data.last_pentest_date,
            created_by=user_id,
        )

        self.db.add(point)
        await self.db.commit()
        await self.db.refresh(point)
        return point

    async def update_entry_point(
        self,
        tenant_id: str,
        point_id: str,
        data: EntryPointUpdate,
    ) -> Optional[EntryPoint]:
        """Update an entry point."""
        point = await self.get_entry_point(tenant_id, point_id)
        if not point:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(point, field, value)

        await self.db.commit()
        await self.db.refresh(point)
        return point

    async def delete_entry_point(self, tenant_id: str, point_id: str) -> bool:
        """Delete an entry point."""
        point = await self.get_entry_point(tenant_id, point_id)
        if not point:
            return False

        await self.db.delete(point)
        await self.db.commit()
        return True

    # ========== Dashboard & Statistics ==========

    async def get_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get attack path analysis dashboard statistics."""
        # Count graphs
        graph_count = await self.db.scalar(
            select(func.count()).where(AttackGraph.tenant_id == tenant_id)
        )

        # Count paths by risk level
        path_query = select(AttackPath).where(AttackPath.tenant_id == tenant_id)
        result = await self.db.execute(path_query)
        paths = list(result.scalars().all())

        total_paths = len(paths)
        critical_paths = sum(1 for p in paths if p.risk_score >= 8.0)
        high_risk_paths = sum(1 for p in paths if 5.0 <= p.risk_score < 8.0)

        # Count by status
        paths_by_status = {
            "active": sum(1 for p in paths if p.status == PathStatus.ACTIVE),
            "mitigated": sum(1 for p in paths if p.status == PathStatus.MITIGATED),
            "accepted": sum(1 for p in paths if p.status == PathStatus.ACCEPTED),
            "false_positive": sum(1 for p in paths if p.status == PathStatus.FALSE_POSITIVE),
        }

        # Risk distribution
        risk_distribution = {
            "critical": critical_paths,
            "high": high_risk_paths,
            "medium": sum(1 for p in paths if 3.0 <= p.risk_score < 5.0),
            "low": sum(1 for p in paths if p.risk_score < 3.0),
        }

        # Count entry points and crown jewels
        entry_points_count = await self.db.scalar(
            select(func.count()).where(
                and_(
                    EntryPoint.tenant_id == tenant_id,
                    EntryPoint.is_active == True
                )
            )
        )

        crown_jewels_count = await self.db.scalar(
            select(func.count()).where(
                and_(
                    CrownJewel.tenant_id == tenant_id,
                    CrownJewel.is_active == True
                )
            )
        )

        # Get top chokepoints
        chokepoints = await self.get_chokepoints(tenant_id, limit=5)

        return {
            "total_graphs": graph_count or 0,
            "total_paths": total_paths,
            "critical_paths": critical_paths,
            "high_risk_paths": high_risk_paths,
            "entry_points_count": entry_points_count or 0,
            "crown_jewels_count": crown_jewels_count or 0,
            "top_chokepoints": chokepoints,
            "risk_distribution": risk_distribution,
            "paths_by_status": paths_by_status,
        }

    async def get_chokepoints(
        self, tenant_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top chokepoints based on path analysis."""
        # Get all active paths
        query = select(AttackPath).where(
            and_(
                AttackPath.tenant_id == tenant_id,
                AttackPath.status == PathStatus.ACTIVE
            )
        )
        result = await self.db.execute(query)
        paths = list(result.scalars().all())

        # Count asset appearances
        asset_frequency = defaultdict(lambda: {"count": 0, "paths": [], "risk_sum": 0})

        for path in paths:
            for node_id in path.path_nodes[1:-1]:  # Exclude entry and target
                asset_frequency[node_id]["count"] += 1
                asset_frequency[node_id]["paths"].append(str(path.id))
                asset_frequency[node_id]["risk_sum"] += path.risk_score

        # Calculate priority scores
        chokepoints = []
        for asset_id, data in asset_frequency.items():
            if data["count"] >= 2:
                chokepoints.append({
                    "asset_id": asset_id,
                    "asset_name": "Unknown",  # Would need to fetch from CMDB
                    "asset_type": "unknown",
                    "paths_affected": data["count"],
                    "total_risk_mitigated": round(data["risk_sum"], 2),
                    "priority_score": round(data["count"] * data["risk_sum"], 2),
                    "vulnerabilities_count": 0,
                    "recommendations": [
                        "Secure this asset to break multiple attack paths",
                        "Consider network segmentation",
                        "Enable MFA for access to this asset"
                    ]
                })

        # Sort by priority
        chokepoints.sort(key=lambda x: x["priority_score"], reverse=True)

        return chokepoints[:limit]
