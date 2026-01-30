"""
NIS2 Directive integration tests.
"""

import pytest
from datetime import datetime, timezone, timedelta

from src.integrations.nis2_directive import (
    NIS2DirectiveManager,
    get_nis2_manager,
    get_entity_type_for_sector,
)
from src.integrations.nis2_models import (
    NIS2EntityType,
    NIS2Sector,
    NIS2IncidentSeverity,
    NIS2NotificationStatus,
    NIS2ContactPerson,
    NIS2IncidentImpact,
    EU_MEMBER_STATES,
    SECTOR_ENTITY_TYPE,
)


class TestNIS2DirectiveManager:
    """Tests for NIS2 Directive Manager."""

    @pytest.fixture
    def manager(self):
        """Get NIS2 manager instance."""
        return get_nis2_manager()

    @pytest.fixture
    def sample_contact(self):
        """Sample contact person."""
        return NIS2ContactPerson(
            name="Max Mustermann",
            email="max@example.de",
            phone="+49 123 456789",
            role="CISO",
        )

    def test_create_notification(self, manager, sample_contact):
        """Test creating a NIS2 notification."""
        notification = manager.create_notification(
            incident_id="test-incident-123",
            entity_type=NIS2EntityType.ESSENTIAL,
            sector=NIS2Sector.DIGITAL_INFRASTRUCTURE,
            organization_name="Test GmbH",
            member_state="DE",
            detection_time=datetime.now(timezone.utc),
            primary_contact=sample_contact,
        )

        assert notification is not None

    def test_calculate_deadlines(self, manager):
        """Test deadline calculation."""
        detected_at = datetime.now(timezone.utc)
        deadlines = manager.calculate_deadlines(detected_at)

        # Check for deadline keys (actual format varies)
        assert "early_warning" in deadlines or "early_warning_deadline" in deadlines
        assert "notification" in deadlines or "notification_deadline" in deadlines
        assert "final_report" in deadlines or "final_report_deadline" in deadlines

    def test_submit_early_warning(self, manager, sample_contact):
        """Test submitting early warning."""
        # Create notification first
        notification = manager.create_notification(
            incident_id="test-incident-456",
            entity_type=NIS2EntityType.ESSENTIAL,
            sector=NIS2Sector.DIGITAL_INFRASTRUCTURE,
            organization_name="Test GmbH",
            member_state="DE",
            detection_time=datetime.now(timezone.utc),
            primary_contact=sample_contact,
        )

        # Submit early warning
        early_warning = manager.submit_early_warning(
            incident_id="test-incident-456",
            initial_assessment="Suspected ransomware attack",
            suspected_cause="Phishing email",
            cross_border_suspected=True,
        )

        assert early_warning is not None

    def test_submit_incident_notification(self, manager, sample_contact):
        """Test submitting incident notification."""
        # Create notification first
        notification = manager.create_notification(
            incident_id="test-incident-789",
            entity_type=NIS2EntityType.ESSENTIAL,
            sector=NIS2Sector.DIGITAL_INFRASTRUCTURE,
            organization_name="Test GmbH",
            member_state="DE",
            detection_time=datetime.now(timezone.utc),
            primary_contact=sample_contact,
        )

        # Submit early warning first
        manager.submit_early_warning(
            incident_id="test-incident-789",
            initial_assessment="Initial assessment",
        )

        # Then submit incident notification
        incident_notification = manager.submit_incident_notification(
            incident_id="test-incident-789",
            incident_description="Detailed description of the incident",
            severity=NIS2IncidentSeverity.SIGNIFICANT,
            incident_type="ransomware",
            impact=NIS2IncidentImpact(
                affected_users=100,
                affected_services=["email", "file_storage"],
                geographic_scope="national",
                economic_impact="significant",
            ),
            mitigation_measures=["Isolated affected systems", "Restored from backup"],
            containment_status="ongoing",
            root_cause_preliminary="Phishing leading to ransomware",
        )

        assert incident_notification is not None

    def test_submit_final_report(self, manager, sample_contact):
        """Test submitting final report."""
        # Create notification
        notification = manager.create_notification(
            incident_id="test-incident-final",
            entity_type=NIS2EntityType.ESSENTIAL,
            sector=NIS2Sector.DIGITAL_INFRASTRUCTURE,
            organization_name="Test GmbH",
            member_state="DE",
            detection_time=datetime.now(timezone.utc),
            primary_contact=sample_contact,
        )

        final_report = manager.submit_final_report(
            incident_id="test-incident-final",
            incident_description="Full incident timeline and impact",
            root_cause_analysis="Phishing email with malicious attachment",
            threat_type="Ransomware",
            attack_techniques=["T1566.001", "T1486"],
            total_impact_assessment="Significant impact on operations",
            services_affected=["email", "file_storage"],
            lessons_learned="Need better phishing detection",
            preventive_measures=["Enhanced email filtering", "User training"],
            security_improvements=["MFA enforcement", "Email gateway upgrade"],
        )

        assert final_report is not None


class TestNIS2EntityTypes:
    """Tests for NIS2 entity type classification."""

    def test_essential_sectors(self):
        """Test that certain sectors are classified as essential."""
        essential_sectors = [
            NIS2Sector.ENERGY,
            NIS2Sector.TRANSPORT,
            NIS2Sector.BANKING,
            NIS2Sector.HEALTH,
            NIS2Sector.DRINKING_WATER,
            NIS2Sector.DIGITAL_INFRASTRUCTURE,
            NIS2Sector.PUBLIC_ADMINISTRATION,
            NIS2Sector.SPACE,
        ]

        for sector in essential_sectors:
            entity_type = get_entity_type_for_sector(sector)
            assert entity_type == NIS2EntityType.ESSENTIAL, f"{sector} should be essential"

    def test_important_sectors(self):
        """Test that certain sectors are classified as important."""
        important_sectors = [
            NIS2Sector.POSTAL,
            NIS2Sector.WASTE_MANAGEMENT,
            NIS2Sector.CHEMICALS,
            NIS2Sector.FOOD,
            NIS2Sector.MANUFACTURING,
            NIS2Sector.DIGITAL_PROVIDERS,
            NIS2Sector.RESEARCH,
        ]

        for sector in important_sectors:
            entity_type = get_entity_type_for_sector(sector)
            assert entity_type == NIS2EntityType.IMPORTANT, f"{sector} should be important"


class TestNIS2MemberStates:
    """Tests for EU member states."""

    def test_member_states_exist(self):
        """Test that member states dictionary exists."""
        assert len(EU_MEMBER_STATES) > 0

    def test_germany_exists(self):
        """Test that Germany (DE) exists in member states."""
        assert "DE" in EU_MEMBER_STATES
        assert EU_MEMBER_STATES["DE"]["name"] == "Germany"

    def test_member_states_have_csirt(self):
        """Test that member states have CSIRT information."""
        for code, info in EU_MEMBER_STATES.items():
            assert "name" in info
            assert "csirt" in info


class TestNIS2Sectors:
    """Tests for NIS2 sectors."""

    def test_all_sectors_have_entity_type(self):
        """Test that all sectors have an entity type mapping."""
        for sector in NIS2Sector:
            assert sector in SECTOR_ENTITY_TYPE

    def test_sector_enum_values(self):
        """Test sector enum has expected values."""
        assert NIS2Sector.ENERGY.value == "energy"
        assert NIS2Sector.HEALTH.value == "health"
        assert NIS2Sector.DIGITAL_INFRASTRUCTURE.value == "digital_infrastructure"
