"""Unit tests for Skill Pydantic schemas.

Tests: 5 tests covering SkillSpec, ToolDefinition, SkillCRD with version validation
"""

import pytest
from pydantic import ValidationError

from backend.schemas.skill import ToolDefinition, SkillSpec, SkillCRD, SkillCreateRequest, SkillResponse
from backend.schemas.base import Metadata
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestToolDefinition:
    """Test suite for ToolDefinition - 2 tests."""

    def test_valid_tool(self):
        """Test creating valid tool definition."""
        tool = ToolDefinition(
            name="file_reader",
            description="Reads files from the filesystem",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
            },
        )
        assert tool.name == "file_reader"
        assert tool.description == "Reads files from the filesystem"

    def test_required_fields(self):
        """Test required fields."""
        with pytest.raises(ValidationError):
            ToolDefinition()


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestSkillSpec:
    """Test suite for SkillSpec - 4 tests."""

    def test_valid_spec(self):
        """Test creating valid skill spec."""
        spec = SkillSpec(
            version="1.0.0",
            author="Test Author",
            tools=[
                ToolDefinition(name="tool1", description="Tool 1"),
            ],
        )
        assert spec.version == "1.0.0"
        assert spec.author == "Test Author"
        assert len(spec.tools) == 1

    def test_default_version(self):
        """Test default version."""
        spec = SkillSpec()
        assert spec.version == "1.0.0"

    def test_version_validation(self):
        """Test version must follow semver."""
        with pytest.raises(ValidationError) as exc_info:
            SkillSpec(version="invalid")
        assert "semantic versioning" in str(exc_info.value)

    def test_valid_semver_versions(self):
        """Test various valid semver versions."""
        for version in ["1.0.0", "2.1.3", "1.0.0-alpha", "1.0.0+build.123"]:
            spec = SkillSpec(version=version)
            assert spec.version == version


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestSkillCRD:
    """Test suite for SkillCRD - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Skill CRD."""
        crd = SkillCRD(
            metadata=Metadata(name="my-skill"),
            spec=SkillSpec(
                version="2.0.0",
                tools=[ToolDefinition(name="tool1", description="Tool 1")],
            ),
        )
        assert crd.kind == KindType.SKILL
        assert crd.spec.version == "2.0.0"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestSkillCreateRequest:
    """Test suite for SkillCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = SkillCreateRequest(
            metadata=Metadata(name="new-skill"),
            spec=SkillSpec(
                version="1.5.0",
                author="Developer",
            ),
        )
        assert request.metadata.name == "new-skill"
        assert request.spec.author == "Developer"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestSkillResponse:
    """Test suite for SkillResponse - 2 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = SkillResponse(
            id=uuid4(),
            metadata=Metadata(name="response-skill"),
            spec=SkillSpec(
                version="3.0.0",
                tools=[ToolDefinition(name="test-tool", description="Test")],
            ),
        )
        assert response.kind == "skill"
        assert response.spec.version == "3.0.0"
