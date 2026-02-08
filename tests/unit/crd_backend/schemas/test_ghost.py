"""Unit tests for Ghost Pydantic schemas.

Tests: 5 tests covering GhostSpec, GhostCRD, GhostResponse
"""

import pytest
from pydantic import ValidationError

from backend.schemas.ghost import GhostSpec, GhostCRD, GhostCreateRequest, GhostResponse
from backend.schemas.base import Metadata
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestGhostSpec:
    """Test suite for GhostSpec schema - 3 tests."""

    def test_valid_spec(self):
        """Test creating valid ghost spec."""
        spec = GhostSpec(
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
            context_window=4096,
        )
        assert spec.system_prompt == "You are a helpful assistant."
        assert spec.temperature == 0.7
        assert spec.context_window == 4096

    def test_required_system_prompt(self):
        """Test system_prompt is required."""
        with pytest.raises(ValidationError) as exc_info:
            GhostSpec()
        assert "systemPrompt" in str(exc_info.value)

    def test_temperature_range(self):
        """Test temperature validation."""
        # Valid temperatures
        GhostSpec(system_prompt="Test", temperature=0.0)
        GhostSpec(system_prompt="Test", temperature=2.0)

        # Invalid temperature
        with pytest.raises(ValidationError):
            GhostSpec(system_prompt="Test", temperature=2.5)


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestGhostCRD:
    """Test suite for GhostCRD schema - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Ghost CRD."""
        crd = GhostCRD(
            metadata=Metadata(name="my-ghost"),
            spec=GhostSpec(system_prompt="Be helpful."),
        )
        assert crd.kind == KindType.GHOST
        assert crd.api_version == "v1"
        assert crd.metadata.name == "my-ghost"

    def test_to_db_dict(self):
        """Test conversion to database dictionary."""
        crd = GhostCRD(
            metadata=Metadata(name="test-ghost", created_by="user@test.com"),
            spec=GhostSpec(system_prompt="Test prompt."),
        )
        db_dict = crd.to_db_dict()
        assert db_dict["kind"] == "ghost"
        assert db_dict["name"] == "test-ghost"
        assert db_dict["api_version"] == "v1"
        assert db_dict["spec"]["systemPrompt"] == "Test prompt."


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestGhostCreateRequest:
    """Test suite for GhostCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = GhostCreateRequest(
            metadata=Metadata(name="new-ghost"),
            spec=GhostSpec(system_prompt="New ghost prompt."),
        )
        assert request.metadata.name == "new-ghost"
        assert request.spec.system_prompt == "New ghost prompt."


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestGhostResponse:
    """Test suite for GhostResponse - 3 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = GhostResponse(
            id=uuid4(),
            metadata=Metadata(name="response-ghost"),
            spec=GhostSpec(system_prompt="Response test."),
        )
        assert response.kind == "ghost"
        assert response.api_version == "v1"
        assert response.spec.system_prompt == "Response test."
