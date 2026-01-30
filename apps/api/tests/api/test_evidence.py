"""
Evidence API tests including hash chain integrity.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestEvidenceCreate:
    """Tests for evidence creation."""

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_create_evidence_success(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test successful evidence creation."""
        # Create incident first
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=sample_evidence_data,
            headers=auth_headers(test_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["entry_type"] == sample_evidence_data["entry_type"]
        assert data["description"] == sample_evidence_data["description"]
        assert "id" in data
        assert "entry_hash" in data

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_create_evidence_generates_hash(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test that evidence creation generates a valid hash."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=sample_evidence_data,
            headers=auth_headers(test_token),
        )
        data = response.json()

        # Verify hash exists and has correct format (SHA-256 = 64 hex chars)
        assert "entry_hash" in data
        assert len(data["entry_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in data["entry_hash"])


class TestEvidenceList:
    """Tests for evidence listing."""

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_list_evidence(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test listing evidence for an incident."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create multiple evidence entries
        for i in range(3):
            evidence = {**sample_evidence_data, "description": f"Evidence entry {i}"}
            await client.post(
                f"/api/v1/incidents/{incident_id}/evidence",
                json=evidence,
                headers=auth_headers(test_token),
            )

        # List evidence
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/evidence",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_list_evidence_filter_by_type(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test filtering evidence by type."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create different evidence types
        types = ["observation", "artifact", "action"]
        for entry_type in types:
            await client.post(
                f"/api/v1/incidents/{incident_id}/evidence",
                json={
                    "entry_type": entry_type,
                    "phase": "detection",
                    "description": f"Test {entry_type}",
                },
                headers=auth_headers(test_token),
            )

        # Filter by type
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/evidence?entry_type=observation",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert all(e["entry_type"] == "observation" for e in data)


class TestEvidenceHashChain:
    """Tests for evidence hash chain integrity - CRITICAL for forensic validity."""

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_hash_chain_links(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test that evidence entries are linked via hash chain."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create multiple evidence entries
        evidence_ids = []
        for i in range(5):
            response = await client.post(
                f"/api/v1/incidents/{incident_id}/evidence",
                json={
                    "entry_type": "observation",
                    "phase": "detection",
                    "description": f"Evidence entry {i}",
                },
                headers=auth_headers(test_token),
            )
            if response.status_code == 201:
                evidence_ids.append(response.json()["id"])

        # Get evidence chain
        chain_response = await client.get(
            f"/api/v1/incidents/{incident_id}/evidence/chain",
            headers=auth_headers(test_token),
        )
        assert chain_response.status_code == 200
        chain = chain_response.json()

        # Verify chain structure
        assert "entries" in chain
        assert len(chain["entries"]) >= 5

        # Verify each entry has hash and previous_hash
        entries = chain["entries"]
        for i, entry in enumerate(entries):
            assert "entry_hash" in entry
            assert "previous_hash" in entry

            # First entry should have no previous hash
            if i == 0:
                assert entry["previous_hash"] is None or entry["previous_hash"] == ""
            else:
                # Each subsequent entry should reference the previous hash
                assert entry["previous_hash"] == entries[i - 1]["entry_hash"]

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_hash_chain_verification(
        self, client: AsyncClient, test_token, sample_incident_data
    ):
        """Test hash chain verification endpoint."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence entries
        for i in range(3):
            await client.post(
                f"/api/v1/incidents/{incident_id}/evidence",
                json={
                    "entry_type": "observation",
                    "phase": "detection",
                    "description": f"Evidence entry {i}",
                },
                headers=auth_headers(test_token),
            )

        # Verify chain integrity
        response = await client.post(
            f"/api/v1/incidents/{incident_id}/evidence/verify",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "verified_entries" in data
        assert data["verified_entries"] >= 3

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_evidence_immutability(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test that evidence entries cannot be modified after creation."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence
        evidence_response = await client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=sample_evidence_data,
            headers=auth_headers(test_token),
        )
        evidence_id = evidence_response.json()["id"]
        original_hash = evidence_response.json()["entry_hash"]

        # Attempt to modify evidence (should fail or be prevented)
        # The API should not expose an update endpoint for evidence
        # Trying PATCH should return 405 Method Not Allowed
        response = await client.patch(
            f"/api/v1/incidents/{incident_id}/evidence/{evidence_id}",
            json={"description": "Modified content"},
            headers=auth_headers(test_token),
        )
        # Should be 404 (no route) or 405 (method not allowed)
        assert response.status_code in [404, 405]


class TestEvidenceExport:
    """Tests for evidence export."""

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_export_evidence_markdown(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test exporting evidence as Markdown."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence
        await client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=sample_evidence_data,
            headers=auth_headers(test_token),
        )

        # Export
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/evidence/export?format=markdown",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        # Response might be plain text for markdown
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            assert "content" in data or isinstance(data, str)
        else:
            # Plain text response
            assert len(response.text) > 0

    @pytest.mark.asyncio
    @pytest.mark.evidence
    async def test_export_evidence_json(
        self, client: AsyncClient, test_token, sample_incident_data, sample_evidence_data
    ):
        """Test exporting evidence as JSON."""
        # Create incident
        incident_response = await client.post(
            "/api/v1/incidents",
            json=sample_incident_data,
            headers=auth_headers(test_token),
        )
        incident_id = incident_response.json()["id"]

        # Create evidence
        await client.post(
            f"/api/v1/incidents/{incident_id}/evidence",
            json=sample_evidence_data,
            headers=auth_headers(test_token),
        )

        # Export
        response = await client.get(
            f"/api/v1/incidents/{incident_id}/evidence/export?format=json",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        # JSON export should return exportable data
        assert isinstance(data, (list, dict))
