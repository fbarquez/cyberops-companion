"""Tests for core modules."""

import pytest
import tempfile
from pathlib import Path

from src.core.workflow import WorkflowEngine
from src.core.evidence_logger import EvidenceLogger
from src.core.checklist_manager import ChecklistManager
from src.core.decision_engine import DecisionEngine
from src.models.evidence import EvidenceType
from src.models.phase import IRPhase


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    def test_workflow_engine_initialization(self):
        """Test workflow engine initializes with default playbook."""
        engine = WorkflowEngine()

        assert engine.playbook_name == "ransomware"
        assert len(engine.phase_definitions) > 0

    def test_create_incident(self):
        """Test incident creation through workflow engine."""
        engine = WorkflowEngine()

        incident, tracker = engine.create_incident(
            title="Test Incident",
            analyst_name="Test Analyst",
            detection_source="user_report",
        )

        assert incident.title == "Test Incident"
        assert tracker.current_phase == IRPhase.DETECTION

    def test_get_phase_definition(self):
        """Test retrieving phase definitions."""
        engine = WorkflowEngine()

        definition = engine.get_phase_definition(IRPhase.DETECTION)

        assert definition is not None
        assert definition.phase == IRPhase.DETECTION
        assert "objective" in definition.model_dump()


class TestEvidenceLogger:
    """Tests for EvidenceLogger."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield db_path

    def test_evidence_logger_initialization(self, temp_db):
        """Test evidence logger initializes database."""
        logger = EvidenceLogger(db_path=temp_db)

        assert temp_db.exists()

    def test_log_entry(self, temp_db):
        """Test logging an evidence entry."""
        logger = EvidenceLogger(db_path=temp_db)

        entry = logger.log_entry(
            incident_id="INC-TEST",
            description="Test observation",
            entry_type=EvidenceType.OBSERVATION,
            phase="detection",
            operator="Analyst",
        )

        assert entry.entry_id is not None
        assert entry.entry_hash is not None

    def test_get_entries(self, temp_db):
        """Test retrieving evidence entries."""
        logger = EvidenceLogger(db_path=temp_db)

        # Log some entries
        logger.log_entry(
            incident_id="INC-TEST",
            description="Entry 1",
            entry_type=EvidenceType.OBSERVATION,
        )
        logger.log_entry(
            incident_id="INC-TEST",
            description="Entry 2",
            entry_type=EvidenceType.ACTION,
        )

        entries = logger.get_entries("INC-TEST")

        assert len(entries) == 2

    def test_verify_chain(self, temp_db):
        """Test chain verification."""
        logger = EvidenceLogger(db_path=temp_db)

        # Log entries
        for i in range(5):
            logger.log_entry(
                incident_id="INC-TEST",
                description=f"Entry {i}",
            )

        is_valid, invalid_idx, message = logger.verify_chain("INC-TEST")

        assert is_valid is True
        assert "5 entries" in message


class TestChecklistManager:
    """Tests for ChecklistManager."""

    def test_checklist_manager_initialization(self):
        """Test checklist manager initializes with default checklists."""
        manager = ChecklistManager()

        assert len(manager.phase_checklists) > 0
        assert "detection" in manager.phase_checklists

    def test_create_incident_checklist(self):
        """Test creating checklists for an incident."""
        manager = ChecklistManager()

        checklists = manager.create_incident_checklist("INC-TEST")

        assert len(checklists) > 0
        # Each checklist should be independent
        assert checklists["detection"] is not manager.phase_checklists["detection"]

    def test_complete_item(self):
        """Test completing a checklist item."""
        manager = ChecklistManager()
        checklists = manager.create_incident_checklist("INC-TEST")

        checklist = checklists["detection"]
        first_item_id = checklist.items[0].id

        item = manager.complete_item(
            checklist,
            first_item_id,
            operator="Analyst",
            notes="Done",
        )

        assert item.status.value == "completed"


class TestDecisionEngine:
    """Tests for DecisionEngine."""

    def test_decision_engine_initialization(self):
        """Test decision engine initializes with default trees."""
        engine = DecisionEngine()

        assert len(engine.decision_trees) > 0

    def test_get_trees_for_phase(self):
        """Test retrieving trees for a specific phase."""
        engine = DecisionEngine()

        containment_trees = engine.get_trees_for_phase("containment")

        assert len(containment_trees) > 0

    def test_create_incident_tree(self):
        """Test creating a tree instance for an incident."""
        engine = DecisionEngine()

        tree = engine.create_incident_tree("containment_strategy")

        assert tree is not None
        assert tree.id == "containment_strategy"
        # Should be independent copy
        assert tree is not engine.decision_trees.get("containment_strategy")

    def test_make_decision(self):
        """Test making a decision in a tree."""
        engine = DecisionEngine()
        tree = engine.create_incident_tree("containment_strategy")

        current_node = tree.get_current_node()
        first_option = current_node.options[0].id

        path = engine.make_decision(
            tree=tree,
            incident_id="INC-TEST",
            option_id=first_option,
            operator="Analyst",
            rationale="Test decision",
        )

        assert path.selected_option_id == first_option
        assert len(tree.path_taken) == 1
