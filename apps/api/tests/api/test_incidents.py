"""
Incidents API tests.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestIncidentCreate:
    """Tests for incident creation."""

    @pytest.mark.asyncio
    async def test_create_incident_success(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test successful incident creation."""
        response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_incident_data["title"]
        assert data["severity"] == sample_incident_data["severity"]
        assert data["current_phase"] == "detection"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_incident_unauthorized(
        self, client: AsyncClient, sample_incident_data
    ):
        """Test incident creation without auth fails."""
        response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_incident_missing_title(
        self, client: AsyncClient, test_token
    ):
        """Test incident creation without title fails."""
        response = await client.post(
            "/api/v1/incidents",
            json={"description": "Test", "severity": "high"},
            headers=auth_headers(test_token),
        )
        assert response.status_code == 422


class TestIncidentList:
    """Tests for incident listing."""

    @pytest.mark.asyncio
    async def test_list_incidents_empty(self, client: AsyncClient, test_token):
        """Test listing incidents when none exist."""
        response = await client.get(
            "/api/v1/incidents",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_list_incidents_with_data(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test listing incidents with data."""
        # Create an incident first
        await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )

        response = await client.get(
            "/api/v1/incidents",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_incidents_pagination(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test incident listing pagination."""
        # Create multiple incidents
        for i in range(5):
            incident = {**sample_incident_data, "title": f"Incident {i}"}
            await client.post(
                "/api/v1/incidents",
                json=incident,
                headers=auth_headers(test_token),
            )

        # Test pagination
        response = await client.get(
            "/api/v1/incidents?page=1&size=2",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5


class TestIncidentGet:
    """Tests for getting individual incidents."""

    @pytest.mark.asyncio
    async def test_get_incident_success(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting an incident by ID."""
        # Create incident
        create_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = create_response.json()["id"]

        # Get incident
        response = await client.get(
            f"/api/v1/incidents/{incident_id}",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == incident_id
        assert data["title"] == sample_incident_data["title"]

    @pytest.mark.asyncio
    async def test_get_incident_not_found(self, client: AsyncClient, test_token):
        """Test getting nonexistent incident fails."""
        response = await client.get(
            "/api/v1/incidents/nonexistent-id",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 404


class TestIncidentUpdate:
    """Tests for updating incidents."""

    @pytest.mark.asyncio
    async def test_update_incident_success(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test updating an incident."""
        # Create incident
        create_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = create_response.json()["id"]

        # Update incident
        response = await client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"title": "Updated Title", "severity": "critical"},
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["severity"] == "critical"


class TestPhaseAdvancement:
    """Tests for phase advancement."""

    @pytest.mark.asyncio
    async def test_advance_phase_success(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test advancing incident phase."""
        # Create incident
        create_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = create_response.json()["id"]
        assert create_response.json()["current_phase"] == "detection"

        # Advance phase (force to skip checklist)
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/advance-phase?force=true",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "analysis"

    @pytest.mark.asyncio
    async def test_phase_sequence(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that phases advance in correct sequence."""
        expected_phases = [
            "detection",
            "analysis",
            "containment",
            "eradication",
            "recovery",
            "post_incident",
        ]

        # Create incident
        create_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = create_response.json()["id"]

        # Advance through all phases
        for i, expected_phase in enumerate(expected_phases):
            # Get current phase
            get_response = await client.get(
                f"/api/v1/incidents/{incident_id}",
                headers=auth_headers(test_token),
            )
            assert get_response.json()["current_phase"] == expected_phase

            # Advance to next phase (except for last)
            if i < len(expected_phases) - 1:
                await client.post(
                    f"/api/v1/incidents/{incident_id}/advance-phase?force=true",
                    headers=auth_headers(test_token),
                )


class TestIncidentTimeline:
    """Tests for incident timeline."""

    @pytest.mark.asyncio
    async def test_get_timeline(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting incident timeline."""
        # Create incident
        create_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = create_response.json()["id"]

        # Get timeline
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/timeline",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        # API returns "timeline" not "events"
        assert "timeline" in data
        # Should have phases in the timeline
        assert len(data["timeline"]) >= 1
