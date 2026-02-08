"""Tests for CRD RESTful API endpoints.

Tests: 40 tests covering all CRD endpoints
- Ghost endpoints: 7 tests
- Model endpoints: 7 tests
- Shell endpoints: 7 tests
- Bot endpoints: 7 tests
- Team endpoints: 7 tests
- Skill endpoints: 7 tests
- HTTP status code tests: included in endpoint tests
- Namespace filtering tests: included in list tests

Epic 10: RESTful API Endpoints
"""

import pytest
from httpx import AsyncClient

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_10,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


# =============================================================================
# Ghost API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestGhostAPI:
    """Test suite for Ghost API endpoints - 7 tests."""

    async def test_create_ghost_success(self, async_client: AsyncClient):
        """Test creating a Ghost returns 201 with correct data."""
        response = await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {
                    "name": "test-ghost",
                },
                "spec": {
                    "systemPrompt": "You are a helpful assistant",
                    "contextWindow": 4096,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-ghost"
        assert data["spec"]["systemPrompt"] == "You are a helpful assistant"
        assert "id" in data

    async def test_create_ghost_duplicate_returns_409(self, async_client: AsyncClient):
        """Test creating duplicate Ghost returns 409 Conflict."""
        # Create first ghost
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "duplicate-ghost"},
                "spec": {"systemPrompt": "First"},
            },
        )

        # Try to create duplicate
        response = await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "duplicate-ghost"},
                "spec": {"systemPrompt": "Second"},
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_list_ghosts(self, async_client: AsyncClient):
        """Test listing Ghosts returns list with created resources."""
        # Create a ghost first
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "list-test-ghost"},
                "spec": {"systemPrompt": "Test"},
            },
        )

        response = await async_client.get("/api/v1/kinds/ghosts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_ghosts_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Ghosts with namespace filter."""
        # Create ghost in custom namespace
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "ns-test-ghost", "namespace": "custom-ns"},
                "spec": {"systemPrompt": "Test"},
            },
        )

        # List with namespace filter
        response = await async_client.get("/api/v1/kinds/ghosts?namespace=custom-ns")
        assert response.status_code == 200
        data = response.json()
        assert all(g["metadata"]["namespace"] == "custom-ns" for g in data)

    async def test_get_ghost_success(self, async_client: AsyncClient):
        """Test getting a Ghost by name returns correct data."""
        # Create ghost
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "get-test-ghost"},
                "spec": {"systemPrompt": "Test get"},
            },
        )

        response = await async_client.get("/api/v1/kinds/ghosts/get-test-ghost")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-ghost"
        assert data["spec"]["systemPrompt"] == "Test get"

    async def test_get_ghost_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Ghost returns 404."""
        response = await async_client.get("/api/v1/kinds/ghosts/nonexistent-ghost")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_ghost_success(self, async_client: AsyncClient):
        """Test deleting a Ghost returns 204 and removes resource."""
        # Create ghost
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "delete-test-ghost"},
                "spec": {"systemPrompt": "Test delete"},
            },
        )

        # Delete ghost
        response = await async_client.delete("/api/v1/kinds/ghosts/delete-test-ghost")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await async_client.get("/api/v1/kinds/ghosts/delete-test-ghost")
        assert get_response.status_code == 404


# =============================================================================
# Model API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestModelAPI:
    """Test suite for Model API endpoints - 7 tests."""

    async def test_create_model_success(self, async_client: AsyncClient):
        """Test creating a Model returns 201 with correct data."""
        response = await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "test-model"},
                "spec": {
                    "config": {
                        "provider": "openai",
                        "modelName": "gpt-4",
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-model"
        assert data["spec"]["config"]["provider"] == "openai"
        assert "id" in data

    async def test_create_model_duplicate_returns_409(self, async_client: AsyncClient):
        """Test creating duplicate Model returns 409 Conflict."""
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "duplicate-model"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-4"},
                },
            },
        )

        response = await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "duplicate-model"},
                "spec": {
                    "config": {"provider": "anthropic", "modelName": "claude-3"},
                },
            },
        )
        assert response.status_code == 409

    async def test_list_models(self, async_client: AsyncClient):
        """Test listing Models returns list with created resources."""
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "list-test-model"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-3.5"},
                },
            },
        )

        response = await async_client.get("/api/v1/kinds/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_models_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Models with namespace filter."""
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "ns-test-model", "namespace": "model-ns"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-4"},
                },
            },
        )

        response = await async_client.get("/api/v1/kinds/models?namespace=model-ns")
        assert response.status_code == 200
        data = response.json()
        assert all(m["metadata"]["namespace"] == "model-ns" for m in data)

    async def test_get_model_success(self, async_client: AsyncClient):
        """Test getting a Model by name returns correct data."""
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "get-test-model"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-4"},
                },
            },
        )

        response = await async_client.get("/api/v1/kinds/models/get-test-model")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-model"

    async def test_get_model_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Model returns 404."""
        response = await async_client.get("/api/v1/kinds/models/nonexistent-model")
        assert response.status_code == 404

    async def test_delete_model_success(self, async_client: AsyncClient):
        """Test deleting a Model returns 204 and removes resource."""
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "delete-test-model"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-4"},
                },
            },
        )

        response = await async_client.delete("/api/v1/kinds/models/delete-test-model")
        assert response.status_code == 204

        get_response = await async_client.get("/api/v1/kinds/models/delete-test-model")
        assert get_response.status_code == 404


# =============================================================================
# Shell API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestShellAPI:
    """Test suite for Shell API endpoints - 7 tests."""

    async def test_create_shell_success(self, async_client: AsyncClient):
        """Test creating a Shell returns 201 with correct data."""
        response = await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "test-shell"},
                "spec": {
                    "type": "chat",
                    "description": "Test shell",
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-shell"
        assert data["spec"]["type"] == "chat"
        assert "id" in data

    async def test_create_shell_duplicate_returns_409(self, async_client: AsyncClient):
        """Test creating duplicate Shell returns 409 Conflict."""
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "duplicate-shell"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "duplicate-shell"},
                "spec": {"type": "code"},
            },
        )
        assert response.status_code == 409

    async def test_list_shells(self, async_client: AsyncClient):
        """Test listing Shells returns list with created resources."""
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "list-test-shell"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.get("/api/v1/kinds/shells")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_shells_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Shells with namespace filter."""
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "ns-test-shell", "namespace": "shell-ns"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.get("/api/v1/kinds/shells?namespace=shell-ns")
        assert response.status_code == 200
        data = response.json()
        assert all(s["metadata"]["namespace"] == "shell-ns" for s in data)

    async def test_get_shell_success(self, async_client: AsyncClient):
        """Test getting a Shell by name returns correct data."""
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "get-test-shell"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.get("/api/v1/kinds/shells/get-test-shell")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-shell"

    async def test_get_shell_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Shell returns 404."""
        response = await async_client.get("/api/v1/kinds/shells/nonexistent-shell")
        assert response.status_code == 404

    async def test_delete_shell_success(self, async_client: AsyncClient):
        """Test deleting a Shell returns 204 and removes resource."""
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "delete-test-shell"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.delete("/api/v1/kinds/shells/delete-test-shell")
        assert response.status_code == 204

        get_response = await async_client.get("/api/v1/kinds/shells/delete-test-shell")
        assert get_response.status_code == 404


# =============================================================================
# Bot API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestBotAPI:
    """Test suite for Bot API endpoints - 7 tests."""

    async def test_create_bot_success(self, async_client: AsyncClient):
        """Test creating a Bot with valid references returns 201."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "bot-test-ghost"},
                "spec": {"systemPrompt": "Test"},
            },
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={
                "metadata": {"name": "bot-test-model"},
                "spec": {
                    "config": {"provider": "openai", "modelName": "gpt-4"},
                },
            },
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={
                "metadata": {"name": "bot-test-shell"},
                "spec": {"type": "chat"},
            },
        )

        response = await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "test-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "bot-test-ghost"},
                    "modelRef": {"kind": "model", "name": "bot-test-model"},
                    "shellRef": {"kind": "shell", "name": "bot-test-shell"},
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-bot"
        assert "id" in data

    async def test_create_bot_invalid_reference_returns_400(self, async_client: AsyncClient):
        """Test creating Bot with invalid reference returns 400."""
        response = await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "invalid-ref-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "nonexistent"},
                    "modelRef": {"kind": "model", "name": "nonexistent"},
                    "shellRef": {"kind": "shell", "name": "nonexistent"},
                },
            },
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    async def test_list_bots(self, async_client: AsyncClient):
        """Test listing Bots returns list with created resources."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "list-bot-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "list-bot-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "list-bot-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "list-test-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "list-bot-ghost"},
                    "modelRef": {"kind": "model", "name": "list-bot-model"},
                    "shellRef": {"kind": "shell", "name": "list-bot-shell"},
                },
            },
        )

        response = await async_client.get("/api/v1/kinds/bots")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_bots_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Bots with namespace filter."""
        response = await async_client.get("/api/v1/kinds/bots?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_bot_success(self, async_client: AsyncClient):
        """Test getting a Bot by name returns correct data."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "get-bot-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "get-bot-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "get-bot-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "get-test-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "get-bot-ghost"},
                    "modelRef": {"kind": "model", "name": "get-bot-model"},
                    "shellRef": {"kind": "shell", "name": "get-bot-shell"},
                },
            },
        )

        response = await async_client.get("/api/v1/kinds/bots/get-test-bot")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-bot"

    async def test_get_bot_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Bot returns 404."""
        response = await async_client.get("/api/v1/kinds/bots/nonexistent-bot")
        assert response.status_code == 404

    async def test_delete_bot_success(self, async_client: AsyncClient):
        """Test deleting a Bot returns 204."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "del-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "del-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "del-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "delete-test-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "del-ghost"},
                    "modelRef": {"kind": "model", "name": "del-model"},
                    "shellRef": {"kind": "shell", "name": "del-shell"},
                },
            },
        )

        response = await async_client.delete("/api/v1/kinds/bots/delete-test-bot")
        assert response.status_code == 204


# =============================================================================
# Team API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestTeamAPI:
    """Test suite for Team API endpoints - 7 tests."""

    async def test_create_team_success(self, async_client: AsyncClient):
        """Test creating a Team with valid bot references returns 201."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "team-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "team-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "team-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "team-test-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "team-ghost"},
                    "modelRef": {"kind": "model", "name": "team-model"},
                    "shellRef": {"kind": "shell", "name": "team-shell"},
                },
            },
        )

        response = await async_client.post(
            "/api/v1/kinds/teams",
            json={
                "metadata": {"name": "test-team"},
                "spec": {
                    "members": [{"botRef": {"kind": "bot", "name": "team-test-bot"}, "role": "leader"}],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-team"
        assert "id" in data

    async def test_create_team_invalid_bot_returns_400(self, async_client: AsyncClient):
        """Test creating Team with invalid bot reference returns 400."""
        response = await async_client.post(
            "/api/v1/kinds/teams",
            json={
                "metadata": {"name": "invalid-team"},
                "spec": {
                    "members": [{"botRef": {"kind": "bot", "name": "nonexistent-bot"}, "role": "leader"}],
                },
            },
        )
        assert response.status_code == 400

    async def test_list_teams(self, async_client: AsyncClient):
        """Test listing Teams returns list with created resources."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "list-team-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "list-team-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "list-team-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "list-team-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "list-team-ghost"},
                    "modelRef": {"kind": "model", "name": "list-team-model"},
                    "shellRef": {"kind": "shell", "name": "list-team-shell"},
                },
            },
        )
        await async_client.post(
            "/api/v1/kinds/teams",
            json={
                "metadata": {"name": "list-test-team"},
                "spec": {"members": [{"botRef": {"kind": "bot", "name": "list-team-bot"}, "role": "leader"}]},
            },
        )

        response = await async_client.get("/api/v1/kinds/teams")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_teams_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Teams with namespace filter."""
        response = await async_client.get("/api/v1/kinds/teams?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_team_success(self, async_client: AsyncClient):
        """Test getting a Team by name returns correct data."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "get-team-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "get-team-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "get-team-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "get-team-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "get-team-ghost"},
                    "modelRef": {"kind": "model", "name": "get-team-model"},
                    "shellRef": {"kind": "shell", "name": "get-team-shell"},
                },
            },
        )
        await async_client.post(
            "/api/v1/kinds/teams",
            json={
                "metadata": {"name": "get-test-team"},
                "spec": {"members": [{"botRef": {"kind": "bot", "name": "get-team-bot"}, "role": "leader"}]},
            },
        )

        response = await async_client.get("/api/v1/kinds/teams/get-test-team")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-team"

    async def test_get_team_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Team returns 404."""
        response = await async_client.get("/api/v1/kinds/teams/nonexistent-team")
        assert response.status_code == 404

    async def test_delete_team_success(self, async_client: AsyncClient):
        """Test deleting a Team returns 204."""
        # Create prerequisites
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "del-t-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        await async_client.post(
            "/api/v1/kinds/models",
            json={"metadata": {"name": "del-t-model"}, "spec": {"config": {"provider": "openai", "modelName": "gpt-4"}}},
        )
        await async_client.post(
            "/api/v1/kinds/shells",
            json={"metadata": {"name": "del-t-shell"}, "spec": {"type": "chat"}},
        )
        await async_client.post(
            "/api/v1/kinds/bots",
            json={
                "metadata": {"name": "del-t-bot"},
                "spec": {
                    "ghostRef": {"kind": "ghost", "name": "del-t-ghost"},
                    "modelRef": {"kind": "model", "name": "del-t-model"},
                    "shellRef": {"kind": "shell", "name": "del-t-shell"},
                },
            },
        )
        await async_client.post(
            "/api/v1/kinds/teams",
            json={
                "metadata": {"name": "delete-test-team"},
                "spec": {"members": [{"botRef": {"kind": "bot", "name": "del-t-bot"}, "role": "leader"}]},
            },
        )

        response = await async_client.delete("/api/v1/kinds/teams/delete-test-team")
        assert response.status_code == 204


# =============================================================================
# Skill API Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestSkillAPI:
    """Test suite for Skill API endpoints - 7 tests."""

    async def test_create_skill_success(self, async_client: AsyncClient):
        """Test creating a Skill returns 201 with correct data."""
        response = await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "test-skill"},
                "spec": {
                    "version": "1.0.0",
                    "tools": [
                        {
                            "name": "test-tool",
                            "description": "A test tool",
                            "parameters": {"type": "object"},
                        }
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-skill"
        assert data["spec"]["version"] == "1.0.0"
        assert "id" in data

    async def test_create_skill_duplicate_returns_409(self, async_client: AsyncClient):
        """Test creating duplicate Skill returns 409 Conflict."""
        await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "duplicate-skill"},
                "spec": {"version": "1.0.0", "tools": []},
            },
        )

        response = await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "duplicate-skill"},
                "spec": {"version": "2.0.0", "tools": []},
            },
        )
        assert response.status_code == 409

    async def test_list_skills(self, async_client: AsyncClient):
        """Test listing Skills returns list with created resources."""
        await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "list-test-skill"},
                "spec": {"version": "1.0.0", "tools": []},
            },
        )

        response = await async_client.get("/api/v1/kinds/skills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_skills_with_namespace_filter(self, async_client: AsyncClient):
        """Test listing Skills with namespace filter."""
        await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "ns-test-skill", "namespace": "skill-ns"},
                "spec": {"version": "1.0.0", "tools": []},
            },
        )

        response = await async_client.get("/api/v1/kinds/skills?namespace=skill-ns")
        assert response.status_code == 200
        data = response.json()
        assert all(s["metadata"]["namespace"] == "skill-ns" for s in data)

    async def test_get_skill_success(self, async_client: AsyncClient):
        """Test getting a Skill by name returns correct data."""
        await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "get-test-skill"},
                "spec": {"version": "1.0.0", "tools": []},
            },
        )

        response = await async_client.get("/api/v1/kinds/skills/get-test-skill")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-skill"

    async def test_get_skill_not_found_returns_404(self, async_client: AsyncClient):
        """Test getting non-existent Skill returns 404."""
        response = await async_client.get("/api/v1/kinds/skills/nonexistent-skill")
        assert response.status_code == 404

    async def test_delete_skill_success(self, async_client: AsyncClient):
        """Test deleting a Skill returns 204 and removes resource."""
        await async_client.post(
            "/api/v1/kinds/skills",
            json={
                "metadata": {"name": "delete-test-skill"},
                "spec": {"version": "1.0.0", "tools": []},
            },
        )

        response = await async_client.delete("/api/v1/kinds/skills/delete-test-skill")
        assert response.status_code == 204

        get_response = await async_client.get("/api/v1/kinds/skills/delete-test-skill")
        assert get_response.status_code == 404


# =============================================================================
# HTTP Status Code Tests
# =============================================================================


@pytest.mark.epic_10
@pytest.mark.unit
@pytest.mark.backend
class TestHTTPStatusCodes:
    """Test suite for HTTP status codes - 5 tests."""

    async def test_create_returns_201(self, async_client: AsyncClient):
        """Test POST creates return 201 Created."""
        response = await async_client.post(
            "/api/v1/kinds/ghosts",
            json={
                "metadata": {"name": "status-test-ghost"},
                "spec": {"systemPrompt": "Test"},
            },
        )
        assert response.status_code == 201

    async def test_get_returns_200(self, async_client: AsyncClient):
        """Test GET returns 200 OK for existing resource."""
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "status-get-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        response = await async_client.get("/api/v1/kinds/ghosts/status-get-ghost")
        assert response.status_code == 200

    async def test_get_not_found_returns_404(self, async_client: AsyncClient):
        """Test GET returns 404 Not Found for missing resource."""
        response = await async_client.get("/api/v1/kinds/ghosts/missing-ghost-xyz")
        assert response.status_code == 404

    async def test_delete_returns_204(self, async_client: AsyncClient):
        """Test DELETE returns 204 No Content."""
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "status-del-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        response = await async_client.delete("/api/v1/kinds/ghosts/status-del-ghost")
        assert response.status_code == 204

    async def test_create_duplicate_returns_409(self, async_client: AsyncClient):
        """Test POST duplicate returns 409 Conflict."""
        await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "status-dup-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        response = await async_client.post(
            "/api/v1/kinds/ghosts",
            json={"metadata": {"name": "status-dup-ghost"}, "spec": {"systemPrompt": "Test"}},
        )
        assert response.status_code == 409
