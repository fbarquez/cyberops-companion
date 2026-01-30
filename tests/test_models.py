"""Tests for data models."""

import pytest
from datetime import datetime, timezone

from src.models.incident import Incident, IncidentStatus, IncidentSeverity, AffectedSystem
from src.models.evidence import EvidenceEntry, EvidenceType, EvidenceChain
from src.models.checklist import ChecklistItem, ChecklistPhase, ChecklistStatus
from src.models.decision import DecisionNode, DecisionOption, DecisionTree, ConfidenceLevel
from src.models.phase import IRPhase, PhaseProgress, IncidentPhaseTracker


class TestIncidentModel:
    """Tests for Incident model."""

    def test_incident_creation(self):
        """Test basic incident creation."""
        incident = Incident(
            title="Test Ransomware Incident",
            analyst_name="Test Analyst",
        )

        assert incident.title == "Test Ransomware Incident"
        assert incident.analyst_name == "Test Analyst"
        assert incident.status == IncidentStatus.DRAFT
        assert incident.severity == IncidentSeverity.MEDIUM
        assert incident.id.startswith("INC-")

    def test_incident_add_affected_system(self):
        """Test adding affected systems."""
        incident = Incident(title="Test", analyst_name="Analyst")
        system = AffectedSystem(hostname="WS-PC-001", ip_address="192.168.1.100")

        incident.add_affected_system(system)

        assert len(incident.affected_systems) == 1
        assert incident.affected_systems[0].hostname == "WS-PC-001"

    def test_incident_status_transition(self):
        """Test status transitions."""
        incident = Incident(title="Test", analyst_name="Analyst")

        incident.update_status(IncidentStatus.ACTIVE)
        assert incident.status == IncidentStatus.ACTIVE

        incident.update_status(IncidentStatus.CONTAINED)
        assert incident.status == IncidentStatus.CONTAINED
        assert incident.contained_at is not None


class TestEvidenceModel:
    """Tests for Evidence models."""

    def test_evidence_entry_creation(self):
        """Test basic evidence entry creation."""
        entry = EvidenceEntry(
            incident_id="INC-2024-TEST",
            description="Test observation",
            entry_type=EvidenceType.OBSERVATION,
        )

        assert entry.incident_id == "INC-2024-TEST"
        assert entry.description == "Test observation"
        assert entry.entry_type == EvidenceType.OBSERVATION

    def test_evidence_hash_computation(self):
        """Test entry hash computation."""
        entry = EvidenceEntry(
            incident_id="INC-2024-TEST",
            description="Test entry",
        )

        entry.finalize(sequence=0, previous_hash=None)

        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64  # SHA-256 hex

    def test_evidence_chain_integrity(self):
        """Test evidence chain hash verification."""
        chain = EvidenceChain(incident_id="INC-2024-TEST")

        # Add entries
        entry1 = EvidenceEntry(
            incident_id="INC-2024-TEST",
            description="First entry",
        )
        entry2 = EvidenceEntry(
            incident_id="INC-2024-TEST",
            description="Second entry",
        )

        chain.append(entry1)
        chain.append(entry2)

        # Verify chain
        is_valid, invalid_idx = chain.verify_chain()

        assert is_valid is True
        assert invalid_idx is None
        assert entry2.previous_hash == entry1.entry_hash


class TestChecklistModel:
    """Tests for Checklist models."""

    def test_checklist_item_completion(self):
        """Test completing a checklist item."""
        item = ChecklistItem(
            id="TEST-001",
            phase="detection",
            text="Test item",
        )

        item.complete(operator="Test Analyst", notes="Completed successfully")

        assert item.status == ChecklistStatus.COMPLETED
        assert item.completed_by == "Test Analyst"
        assert item.notes == "Completed successfully"
        assert item.completed_at is not None

    def test_checklist_item_skip(self):
        """Test skipping a checklist item."""
        item = ChecklistItem(
            id="TEST-001",
            phase="detection",
            text="Test item",
            mandatory=False,
        )

        item.skip(operator="Test Analyst", reason="Not applicable")

        assert item.status == ChecklistStatus.SKIPPED
        assert item.skip_reason == "Not applicable"

    def test_checklist_phase_progress(self):
        """Test phase progress calculation."""
        phase = ChecklistPhase(
            phase_id="detection",
            phase_name="Detection",
            description="Test phase",
            items=[
                ChecklistItem(id="T1", phase="detection", text="Item 1"),
                ChecklistItem(id="T2", phase="detection", text="Item 2"),
                ChecklistItem(id="T3", phase="detection", text="Item 3"),
            ],
        )

        # Complete one item
        phase.items[0].complete(operator="Analyst")

        progress = phase.get_progress()

        assert progress["total"] == 3
        assert progress["completed"] == 1
        assert progress["percentage"] == 33


class TestDecisionModel:
    """Tests for Decision models."""

    def test_decision_option_creation(self):
        """Test decision option creation."""
        option = DecisionOption(
            id="opt1",
            label="Test Option",
            description="A test option",
            confidence=ConfidenceLevel.HIGH,
            recommended=True,
        )

        assert option.id == "opt1"
        assert option.confidence == ConfidenceLevel.HIGH
        assert option.recommended is True

    def test_decision_tree_navigation(self):
        """Test decision tree navigation."""
        tree = DecisionTree(
            id="test_tree",
            name="Test Tree",
            description="A test decision tree",
            phase="containment",
            entry_node_id="node1",
            nodes=[
                DecisionNode(
                    id="node1",
                    phase="containment",
                    title="Test Node",
                    question="Test question?",
                    options=[
                        DecisionOption(
                            id="opt1",
                            label="Option 1",
                            description="First option",
                            confidence=ConfidenceLevel.HIGH,
                            next_node_id=None,
                        ),
                    ],
                ),
            ],
        )

        current = tree.get_current_node()
        assert current.id == "node1"

        path = tree.record_decision(
            incident_id="INC-TEST",
            option_id="opt1",
            operator="Analyst",
            rationale="Test rationale",
        )

        assert path.selected_option_id == "opt1"
        assert tree.completed is True


class TestPhaseModel:
    """Tests for Phase models."""

    def test_phase_tracker_creation(self):
        """Test phase tracker initialization."""
        tracker = IncidentPhaseTracker(incident_id="INC-TEST")

        assert tracker.current_phase == IRPhase.DETECTION
        assert len(tracker.phases) == 6  # All IR phases

    def test_phase_advancement(self):
        """Test advancing through phases."""
        tracker = IncidentPhaseTracker(incident_id="INC-TEST")

        # Start the first phase
        tracker.get_current_progress().start()

        # Advance to next phase
        new_phase = tracker.advance_phase(completion_notes="Detection complete")

        assert new_phase == IRPhase.ANALYSIS
        assert tracker.current_phase == IRPhase.ANALYSIS

    def test_overall_progress(self):
        """Test overall progress calculation."""
        tracker = IncidentPhaseTracker(incident_id="INC-TEST")

        progress = tracker.get_overall_progress()

        assert progress["total_phases"] == 6
        assert progress["percentage"] == 0
