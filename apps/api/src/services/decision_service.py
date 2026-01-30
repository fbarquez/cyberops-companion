"""Decision tree service."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.decision import (
    DecisionNode, DecisionTree, DecisionPath, IncidentDecisionState,
    ConfidenceLevel,
)
from src.models.checklist import ChecklistItem, ChecklistStatus
from src.schemas.decision import DecisionMake, DecisionTreeResponse


class DecisionService:
    """Service for decision tree operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trees_for_phase(self, phase: str) -> List[DecisionTree]:
        """Get all decision trees for a phase."""
        result = await self.db.execute(
            select(DecisionTree).where(DecisionTree.phase == phase)
        )
        return list(result.scalars().all())

    async def get_tree(self, tree_id: str) -> Optional[DecisionTree]:
        """Get a decision tree by ID."""
        result = await self.db.execute(
            select(DecisionTree).where(DecisionTree.tree_id == tree_id)
        )
        return result.scalar_one_or_none()

    async def get_node(self, node_id: str) -> Optional[DecisionNode]:
        """Get a decision node by ID."""
        result = await self.db.execute(
            select(DecisionNode).where(DecisionNode.node_id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_incident_state(
        self, incident_id: str, tree_id: str
    ) -> Optional[IncidentDecisionState]:
        """Get current decision state for an incident."""
        result = await self.db.execute(
            select(IncidentDecisionState).where(
                and_(
                    IncidentDecisionState.incident_id == incident_id,
                    IncidentDecisionState.tree_id == tree_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_state(
        self, incident_id: str, tree_id: str
    ) -> IncidentDecisionState:
        """Get or create decision state for an incident."""
        state = await self.get_incident_state(incident_id, tree_id)
        if state:
            return state

        tree = await self.get_tree(tree_id)
        if not tree:
            raise ValueError(f"Tree not found: {tree_id}")

        state = IncidentDecisionState(
            id=str(uuid4()),
            incident_id=incident_id,
            tree_id=tree_id,
            current_node_id=tree.entry_node_id,
            completed=False,
            path_taken=[],
        )
        self.db.add(state)
        await self.db.flush()
        await self.db.refresh(state)
        return state

    async def get_current_node(
        self, incident_id: str, tree_id: str
    ) -> Optional[DecisionNode]:
        """Get the current node for an incident's decision tree."""
        state = await self.get_incident_state(incident_id, tree_id)
        if not state or not state.current_node_id:
            tree = await self.get_tree(tree_id)
            if tree:
                return await self.get_node(tree.entry_node_id)
            return None

        return await self.get_node(state.current_node_id)

    async def check_prerequisites(
        self, incident_id: str, node: DecisionNode
    ) -> dict:
        """Check if prerequisites for a node are met."""
        missing_checklist = []
        missing_decisions = []

        # Check required checklist items
        if node.requires_checklist_items:
            result = await self.db.execute(
                select(ChecklistItem).where(
                    and_(
                        ChecklistItem.incident_id == incident_id,
                        ChecklistItem.item_id.in_(node.requires_checklist_items),
                    )
                )
            )
            items = {i.item_id: i for i in result.scalars().all()}

            for item_id in node.requires_checklist_items:
                if item_id not in items:
                    missing_checklist.append(item_id)
                elif items[item_id].status not in [
                    ChecklistStatus.COMPLETED,
                    ChecklistStatus.SKIPPED,
                ]:
                    missing_checklist.append(item_id)

        # Check required decisions
        if node.requires_decisions:
            result = await self.db.execute(
                select(DecisionPath).where(
                    and_(
                        DecisionPath.incident_id == incident_id,
                        DecisionPath.node_id.in_(node.requires_decisions),
                    )
                )
            )
            made_decisions = {d.node_id for d in result.scalars().all()}

            for decision_id in node.requires_decisions:
                if decision_id not in made_decisions:
                    missing_decisions.append(decision_id)

        return {
            "is_available": len(missing_checklist) == 0 and len(missing_decisions) == 0,
            "missing_checklist": missing_checklist,
            "missing_decisions": missing_decisions,
        }

    async def make_decision(
        self,
        incident_id: str,
        tree_id: str,
        node_id: str,
        data: DecisionMake,
        user_id: str,
    ) -> DecisionPath:
        """Record a decision."""
        node = await self.get_node(node_id)
        if not node:
            raise ValueError(f"Node not found: {node_id}")

        # Find selected option
        selected_option = None
        for opt in node.options:
            if opt["id"] == data.option_id:
                selected_option = opt
                break

        if not selected_option:
            raise ValueError(f"Option not found: {data.option_id}")

        # Check if confirmation required
        if selected_option.get("requires_confirmation") and not data.confirm:
            raise ValueError("This decision requires confirmation")

        # Create decision path record
        path = DecisionPath(
            id=str(uuid4()),
            incident_id=incident_id,
            tree_id=tree_id,
            node_id=node_id,
            selected_option_id=data.option_id,
            selected_option_label=selected_option["label"],
            confidence=ConfidenceLevel(selected_option["confidence"]) if selected_option.get("confidence") else None,
            rationale=data.rationale,
            decided_by=user_id,
            decided_at=datetime.utcnow(),
            next_node_id=selected_option.get("next_node_id"),
            next_phase=selected_option.get("next_phase"),
            modifies_evidence=selected_option.get("modifies_evidence", False),
            requires_confirmation=selected_option.get("requires_confirmation", False),
            was_confirmed=data.confirm,
        )
        self.db.add(path)

        # Update incident state
        state = await self.get_or_create_state(incident_id, tree_id)
        state.current_node_id = selected_option.get("next_node_id")
        state.path_taken = state.path_taken + [node_id]
        state.updated_at = datetime.utcnow()

        # Check if tree is completed
        if not selected_option.get("next_node_id"):
            state.completed = True

        await self.db.flush()
        await self.db.refresh(path)
        return path

    async def get_decision_history(
        self, incident_id: str
    ) -> List[DecisionPath]:
        """Get all decisions made for an incident."""
        result = await self.db.execute(
            select(DecisionPath)
            .where(DecisionPath.incident_id == incident_id)
            .order_by(DecisionPath.decided_at)
        )
        return list(result.scalars().all())

    async def get_tree_status(
        self, incident_id: str, tree_id: str, lang: str = "en"
    ) -> DecisionTreeResponse:
        """Get tree status for an incident."""
        tree = await self.get_tree(tree_id)
        if not tree:
            raise ValueError(f"Tree not found: {tree_id}")

        state = await self.get_incident_state(incident_id, tree_id)

        # Count nodes
        result = await self.db.execute(
            select(DecisionNode).where(DecisionNode.tree_id == tree_id)
        )
        total_nodes = len(list(result.scalars().all()))

        completed_nodes = len(state.path_taken) if state else 0

        return DecisionTreeResponse(
            id=tree.id,
            tree_id=tree.tree_id,
            phase=tree.phase,
            name=tree.name if lang == "en" else tree.name_de,
            description=tree.description if lang == "en" else tree.description_de,
            entry_node_id=tree.entry_node_id,
            current_node_id=state.current_node_id if state else tree.entry_node_id,
            completed=state.completed if state else False,
            path_taken=state.path_taken if state else [],
            total_nodes=total_nodes,
            completed_nodes=completed_nodes,
        )
