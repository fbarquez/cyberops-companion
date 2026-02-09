"""Decision tree endpoints."""
from fastapi import APIRouter, HTTPException, status, Query

from src.api.deps import DBSession, CurrentUser, UserWithTenant
from src.schemas.decision import (
    DecisionTreeResponse, DecisionNodeResponse, DecisionMake,
    DecisionPathResponse, DecisionHistoryResponse,
)
from src.services.decision_service import DecisionService
from src.services.evidence_service import EvidenceService


router = APIRouter()


@router.get("/incidents/{incident_id}/decisions/trees")
async def get_decision_trees(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
    phase: str = Query(...),
    lang: str = Query("en", pattern="^(en|de)$"),
):
    """Get all decision trees for a phase."""
    service = DecisionService(db)
    trees = await service.get_trees_for_phase(phase)

    result = []
    for tree in trees:
        tree_status = await service.get_tree_status(incident_id, tree.tree_id, lang)
        result.append(tree_status)

    return result


@router.get(
    "/incidents/{incident_id}/decisions/trees/{tree_id}",
    response_model=DecisionTreeResponse,
)
async def get_decision_tree(
    incident_id: str,
    tree_id: str,
    db: DBSession,
    current_user: CurrentUser,
    lang: str = Query("en", pattern="^(en|de)$"),
):
    """Get a specific decision tree with current state."""
    service = DecisionService(db)

    try:
        tree_status = await service.get_tree_status(incident_id, tree_id, lang)
        return tree_status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/incidents/{incident_id}/decisions/trees/{tree_id}/current-node")
async def get_current_node(
    incident_id: str,
    tree_id: str,
    db: DBSession,
    current_user: CurrentUser,
    lang: str = Query("en", pattern="^(en|de)$"),
):
    """Get the current decision node for an incident."""
    service = DecisionService(db)

    node = await service.get_current_node(incident_id, tree_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current node found",
        )

    # Check prerequisites
    prereqs = await service.check_prerequisites(incident_id, node)

    # Get localized content
    is_german = lang == "de"

    return {
        "id": node.id,
        "node_id": node.node_id,
        "tree_id": node.tree_id,
        "phase": node.phase,
        "title": node.title_de if is_german else node.title,
        "question": node.question_de if is_german else node.question,
        "context": node.context_de if is_german else node.context,
        "help_text": node.help_text_de if is_german else node.help_text,
        "options": node.options,
        "is_entry_node": node.is_entry_node,
        "is_available": prereqs["is_available"],
        "blocked_by": prereqs["missing_checklist"] + prereqs["missing_decisions"],
    }


@router.post(
    "/incidents/{incident_id}/decisions/trees/{tree_id}/decide",
    response_model=DecisionPathResponse,
)
async def make_decision(
    incident_id: str,
    tree_id: str,
    data: DecisionMake,
    db: DBSession,
    user_context: UserWithTenant,
):
    """Make a decision in the tree."""
    current_user, context = user_context
    decision_service = DecisionService(db)
    evidence_service = EvidenceService(db)

    # Get current node
    current_node = await decision_service.get_current_node(incident_id, tree_id)
    if not current_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current decision node",
        )

    try:
        # Record decision
        path = await decision_service.make_decision(
            incident_id=incident_id,
            tree_id=tree_id,
            node_id=current_node.node_id,
            data=data,
            user_id=current_user.id,
        )

        # Log as evidence
        await evidence_service.log_decision(
            incident_id=incident_id,
            decision_id=current_node.node_id,
            option_id=path.selected_option_id,
            option_label=path.selected_option_label,
            rationale=path.rationale,
            user_id=current_user.id,
            operator_name=current_user.full_name,
            phase=current_node.phase,
            tenant_id=context.tenant_id,
        )

        return path

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/incidents/{incident_id}/decisions/history",
    response_model=DecisionHistoryResponse,
)
async def get_decision_history(
    incident_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get all decisions made for an incident."""
    service = DecisionService(db)
    decisions = await service.get_decision_history(incident_id)

    # Determine completed and in-progress trees
    tree_states = {}
    for decision in decisions:
        if decision.tree_id not in tree_states:
            tree_states[decision.tree_id] = False
        if not decision.next_node_id:
            tree_states[decision.tree_id] = True

    trees_completed = [tid for tid, completed in tree_states.items() if completed]
    trees_in_progress = [tid for tid, completed in tree_states.items() if not completed]

    return DecisionHistoryResponse(
        incident_id=incident_id,
        total_decisions=len(decisions),
        decisions=decisions,
        trees_completed=trees_completed,
        trees_in_progress=trees_in_progress,
    )
