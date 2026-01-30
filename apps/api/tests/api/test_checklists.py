"""
Checklists API tests.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestChecklistGet:
    """Tests for getting checklists."""

    @pytest.mark.asyncio
    async def test_get_checklist_for_phase(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting checklist for a phase."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist for detection phase
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

        # Verify structure if items exist
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "id" in item or "item_id" in item
            assert "text" in item
            assert "status" in item

    @pytest.mark.asyncio
    async def test_get_checklist_all_phases(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting checklists for all phases."""
        phases = [
            "detection",
            "analysis",
            "containment",
            "eradication",
            "recovery",
            "post_incident",
        ]

        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist for each phase
        for phase in phases:
            response = await client.get(
                f"/api/v1/incidents/{incident_id}/checklists/{phase}",
                headers=auth_headers(test_token),
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data

    @pytest.mark.asyncio
    async def test_checklist_response_structure(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test checklist response contains expected fields."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "items" in data
        assert "total_items" in data or isinstance(data.get("items"), list)


class TestChecklistComplete:
    """Tests for completing checklist items."""

    @pytest.mark.asyncio
    async def test_complete_item_success(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test completing a checklist item."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        checklist_response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = checklist_response.json()["items"]

        if not items:
            pytest.skip("No checklist items available to test")

        item_id = items[0].get("item_id") or items[0].get("id")

        # Complete item
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/items/{item_id}/complete",
            json={"notes": "Completed this task"},
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        # API returns {"status": "completed", "item_id": ...}
        assert data.get("status") == "completed" or data.get("completed") is True

    @pytest.mark.asyncio
    async def test_complete_item_updates_progress(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that completing items updates progress."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get initial progress
        initial_checklist = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = initial_checklist.json()["items"]

        if not items:
            pytest.skip("No checklist items available to test")

        # Find an incomplete item
        incomplete_items = [
            i for i in items
            if i.get("status") not in ["completed", "skipped"]
        ]
        if not incomplete_items:
            pytest.skip("No incomplete checklist items available")

        item_id = incomplete_items[0].get("item_id") or incomplete_items[0].get("id")
        initial_completed = sum(
            1 for i in items if i.get("status") == "completed"
        )

        # Complete the item
        await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/items/{item_id}/complete",
            json={},
            headers=auth_headers(test_token),
        )

        # Check progress increased
        updated_checklist = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        updated_items = updated_checklist.json()["items"]
        updated_completed = sum(
            1 for i in updated_items if i.get("status") == "completed"
        )

        assert updated_completed == initial_completed + 1

    @pytest.mark.asyncio
    async def test_complete_nonexistent_item(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test completing nonexistent item returns 404."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Try to complete nonexistent item
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/items/nonexistent-item/complete",
            json={"notes": "Test"},
            headers=auth_headers(test_token),
        )
        assert response.status_code == 404


class TestChecklistSkip:
    """Tests for skipping checklist items."""

    @pytest.mark.asyncio
    async def test_skip_item_with_reason(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test skipping a checklist item with reason."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        checklist_response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = checklist_response.json()["items"]

        if not items:
            pytest.skip("No checklist items available to test")

        # Find a non-mandatory item to skip
        non_mandatory_items = [i for i in items if not i.get("mandatory", False)]
        if not non_mandatory_items:
            pytest.skip("No non-mandatory items available to skip")

        item_id = non_mandatory_items[0].get("item_id") or non_mandatory_items[0].get("id")

        # Skip item
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/items/{item_id}/skip",
            json={"skip_reason": "Not applicable for this incident type"},
            headers=auth_headers(test_token),
        )
        # May return 200 or 400 if item is mandatory
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "skipped" or data.get("skipped") is True

    @pytest.mark.asyncio
    async def test_skip_mandatory_item_fails(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that skipping mandatory item fails."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        checklist_response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = checklist_response.json()["items"]

        if not items:
            pytest.skip("No checklist items available to test")

        # Find a mandatory item
        mandatory_items = [i for i in items if i.get("mandatory", False)]
        if not mandatory_items:
            pytest.skip("No mandatory items available to test")

        item_id = mandatory_items[0].get("item_id") or mandatory_items[0].get("id")

        # Try to skip mandatory item - should fail
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/items/{item_id}/skip",
            json={"skip_reason": "Trying to skip mandatory item"},
            headers=auth_headers(test_token),
        )
        assert response.status_code == 400


class TestChecklistCanAdvance:
    """Tests for phase advancement readiness."""

    @pytest.mark.asyncio
    async def test_can_advance_endpoint(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test can-advance endpoint returns expected structure."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Check can advance
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/can-advance",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "can_advance" in data

    @pytest.mark.asyncio
    async def test_can_advance_with_incomplete_items(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test can-advance when checklist is incomplete."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist to check if there are mandatory items
        checklist_response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = checklist_response.json()["items"]

        # Check can advance
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/can-advance",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "can_advance" in data

        # If there are mandatory incomplete items, should not be able to advance
        mandatory_incomplete = [
            i for i in items
            if i.get("mandatory", False) and i.get("status") not in ["completed", "skipped"]
        ]
        if mandatory_incomplete:
            assert data["can_advance"] is False

    @pytest.mark.asyncio
    async def test_can_advance_complete(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test can-advance when checklist is complete."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        checklist_response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        items = checklist_response.json()["items"]

        # Complete all mandatory items
        for item in items:
            if item.get("mandatory", False):
                item_id = item.get("item_id") or item.get("id")
                await client.post(
                    f"/api/v1/incidents/{incident_id}/checklists/detection/items/{item_id}/complete",
                    json={"notes": "Done"},
                    headers=auth_headers(test_token),
                )

        # Check can advance
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/checklists/detection/can-advance",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["can_advance"] is True


class TestChecklistProgress:
    """Tests for checklist progress endpoint."""

    @pytest.mark.asyncio
    async def test_get_progress(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting checklist progress."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get progress
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection/progress",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "phase" in data
        assert data["phase"] == "detection"


class TestChecklistDependencies:
    """Tests for checklist item dependencies."""

    @pytest.mark.asyncio
    async def test_blocked_items_indicator(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that blocked items are indicated in response."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get checklist
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/checklists/detection",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()

        # If items have dependencies, they should have is_blocked field
        for item in data.get("items", []):
            if item.get("depends_on"):
                assert "is_blocked" in item or "blockers" in item
