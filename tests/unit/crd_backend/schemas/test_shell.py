"""Unit tests for Shell Pydantic schemas.

Tests: 5 tests covering ShellSpec, EnvironmentVariable, ResourceLimits, ShellCRD
"""

import pytest
from pydantic import ValidationError

from backend.schemas.shell import (
    EnvironmentVariable,
    ResourceLimits,
    ShellSpec,
    ShellCRD,
    ShellCreateRequest,
    ShellResponse,
)
from backend.schemas.base import Metadata
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestEnvironmentVariable:
    """Test suite for EnvironmentVariable - 2 tests."""

    def test_with_value(self):
        """Test env var with direct value."""
        env = EnvironmentVariable(name="API_KEY", value="secret123")
        assert env.name == "API_KEY"
        assert env.value == "secret123"
        assert env.secret_ref is None

    def test_with_secret_ref(self):
        """Test env var with secret reference."""
        env = EnvironmentVariable(name="DATABASE_URL", secret_ref="db-secret")
        assert env.name == "DATABASE_URL"
        assert env.secret_ref == "db-secret"
        assert env.value is None


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestResourceLimits:
    """Test suite for ResourceLimits - 3 tests."""

    def test_valid_limits(self):
        """Test valid resource limits."""
        limits = ResourceLimits(cpu="1", memory="2Gi", timeout=600)
        assert limits.cpu == "1"
        assert limits.memory == "2Gi"
        assert limits.timeout == 600

    def test_default_timeout(self):
        """Test default timeout."""
        limits = ResourceLimits()
        assert limits.timeout == 300

    def test_timeout_range(self):
        """Test timeout validation."""
        with pytest.raises(ValidationError):
            ResourceLimits(timeout=0)
        with pytest.raises(ValidationError):
            ResourceLimits(timeout=3601)


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestShellSpec:
    """Test suite for ShellSpec - 4 tests."""

    def test_valid_spec(self):
        """Test creating valid shell spec."""
        spec = ShellSpec(
            type="chat",
            image="python:3.11",
            network_access=True,
        )
        assert spec.type == "chat"
        assert spec.image == "python:3.11"
        assert spec.network_access is True

    def test_default_type(self):
        """Test default shell type."""
        spec = ShellSpec()
        assert spec.type == "chat"

    def test_valid_types(self):
        """Test all valid shell types."""
        for shell_type in ["chat", "code", "notebook"]:
            spec = ShellSpec(type=shell_type)
            assert spec.type == shell_type

    def test_with_env_vars(self):
        """Test shell spec with environment variables."""
        spec = ShellSpec(
            env=[
                EnvironmentVariable(name="KEY1", value="value1"),
                EnvironmentVariable(name="KEY2", secret_ref="secret2"),
            ],
        )
        assert len(spec.env) == 2
        assert spec.env[0].name == "KEY1"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestShellCRD:
    """Test suite for ShellCRD - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Shell CRD."""
        crd = ShellCRD(
            metadata=Metadata(name="my-shell"),
            spec=ShellSpec(type="code", image="node:18"),
        )
        assert crd.kind == KindType.SHELL
        assert crd.spec.type == "code"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestShellCreateRequest:
    """Test suite for ShellCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = ShellCreateRequest(
            metadata=Metadata(name="new-shell"),
            spec=ShellSpec(type="notebook"),
        )
        assert request.metadata.name == "new-shell"
        assert request.spec.type == "notebook"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestShellResponse:
    """Test suite for ShellResponse - 2 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = ShellResponse(
            id=uuid4(),
            metadata=Metadata(name="response-shell"),
            spec=ShellSpec(type="chat"),
        )
        assert response.kind == "shell"
        assert response.spec.type == "chat"
