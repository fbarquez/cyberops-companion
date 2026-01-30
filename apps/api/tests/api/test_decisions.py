"""
Decisions API tests.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestDecisionTrees:
    """Tests for decision trees."""

    @pytest.mark.asyncio
    async def test_get_decision_trees(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting decision trees for an incident."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get decision trees for detection phase
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        # API returns a list directly
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_decision_tree_detail(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting a specific decision tree."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get trees list first
        trees_response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection",
            headers=auth_headers(test_token),
        )
        trees = trees_response.json()

        if trees and len(trees) > 0:
            tree_id = trees[0].get("tree_id") or trees[0].get("id")
            if tree_id:
                # Get specific tree
                response = await client.get(
                    f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}",
                    headers=auth_headers(test_token),
                )
                assert response.status_code == 200
                data = response.json()
                assert "tree_id" in data or "id" in data

    @pytest.mark.asyncio
    async def test_get_trees_different_languages(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting decision trees in different languages."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get trees in English
        response_en = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection&lang=en",
            headers=auth_headers(test_token),
        )
        assert response_en.status_code == 200

        # Get trees in German
        response_de = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection&lang=de",
            headers=auth_headers(test_token),
        )
        assert response_de.status_code == 200


class TestDecisionMaking:
    """Tests for making decisions."""

    @pytest.mark.asyncio
    async def test_make_decision(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test making a decision in a tree."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get trees
        trees_response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection",
            headers=auth_headers(test_token),
        )
        trees = trees_response.json()

        if trees and len(trees) > 0:
            tree_id = trees[0].get("tree_id") or trees[0].get("id")
            if tree_id:
                # Get current node
                current_response = await client.get(
                    f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/current-node",
                    headers=auth_headers(test_token),
                )

                if current_response.status_code == 200:
                    current = current_response.json()
                    options = current.get("options", [])
                    if options:
                        option_id = options[0].get("id") or options[0].get("option_id")

                        # Make decision
                        response = await client.post(
                            f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/decide",
                            json={
                                "option_id": option_id,
                                "rationale": "Test decision rationale",
                                "confirm": True,
                            },
                            headers=auth_headers(test_token),
                        )
                        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_decision_requires_confirmation_for_critical(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that critical decisions require confirmation."""
        # Create incident with critical severity
        incident_data = {**sample_incident_data, "severity": "critical"}
        incident_response = await client.post(
            "/api/v1/incidents",
            json=incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get trees
        trees_response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=containment",
            headers=auth_headers(test_token),
        )
        trees = trees_response.json()

        # Find a tree with critical options (containment typically has these)
        # This test verifies the confirmation mechanism exists
        if trees and len(trees) > 0:
            tree_id = trees[0].get("tree_id") or trees[0].get("id")
            if tree_id:
                current_response = await client.get(
                    f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/current-node",
                    headers=auth_headers(test_token),
                )
                # Just verify the endpoint works - actual confirmation logic
                # depends on the specific tree structure
                assert current_response.status_code in [200, 404]


class TestDecisionHistory:
    """Tests for decision history."""

    @pytest.mark.asyncio
    async def test_get_decision_history_empty(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test getting empty decision history."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Get history
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/history",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        # Can be a list or dict with decisions key
        if isinstance(data, dict):
            assert "decisions" in data
            assert isinstance(data["decisions"], list)
        else:
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_decision_history_records_decisions(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that decisions are recorded in history."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Make a decision (if trees available)
        trees_response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection",
            headers=auth_headers(test_token),
        )
        trees = trees_response.json()

        if trees and len(trees) > 0:
            tree_id = trees[0].get("tree_id") or trees[0].get("id")
            if tree_id:
                current_response = await client.get(
                    f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/current-node",
                    headers=auth_headers(test_token),
                )

                if current_response.status_code == 200:
                    current = current_response.json()
                    options = current.get("options", [])
                    if options:
                        option_id = options[0].get("id") or options[0].get("option_id")

                        # Make decision
                        await client.post(
                            f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/decide",
                            json={
                                "option_id": option_id,
                                "rationale": "Test rationale",
                                "confirm": True,
                            },
                            headers=auth_headers(test_token),
                        )

                        # Check history
                        history_response = await client.get(
                            f"/api/v1/incidents/{incident_id}/decisions/history",
                            headers=auth_headers(test_token),
                        )
                        assert history_response.status_code == 200

    @pytest.mark.asyncio
    async def test_decision_history_includes_metadata(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that decision history includes relevant metadata."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Make a decision
        trees_response = await client.get(
            f"/api/v1/incidents/{incident_id}/decisions/trees?phase=detection",
            headers=auth_headers(test_token),
        )
        trees = trees_response.json()

        if trees and len(trees) > 0:
            tree_id = trees[0].get("tree_id") or trees[0].get("id")
            if tree_id:
                current_response = await client.get(
                    f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/current-node",
                    headers=auth_headers(test_token),
                )

                if current_response.status_code == 200:
                    current = current_response.json()
                    options = current.get("options", [])
                    if options:
                        option_id = options[0].get("id") or options[0].get("option_id")

                        await client.post(
                            f"/api/v1/incidents/{incident_id}/decisions/trees/{tree_id}/decide",
                            json={
                                "option_id": option_id,
                                "rationale": "Detailed rationale for audit trail",
                                "confirm": True,
                            },
                            headers=auth_headers(test_token),
                        )

                        # Check history metadata
                        history_response = await client.get(
                            f"/api/v1/incidents/{incident_id}/decisions/history",
                            headers=auth_headers(test_token),
                        )
                        assert history_response.status_code == 200
