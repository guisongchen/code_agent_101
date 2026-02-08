"""Unit tests for SkillService.

Tests: 6 tests covering SkillService CRUD operations
"""

import pytest
import pytest_asyncio

from backend.services.skill import SkillService
from backend.models.kinds import KindType
from backend.schemas.skill import SkillSpec, SkillCRD, ToolDefinition, Metadata


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestSkillService:
    """Test suite for SkillService - 6 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create SkillService instance."""
        return SkillService(async_session)

    async def test_create_skill(self, service):
        """Test creating a skill resource."""
        skill = SkillCRD(
            metadata=Metadata(name="test-skill", namespace="default"),
            spec=SkillSpec(
                version="1.0.0",
                author="Test Author",
            ),
        )

        result = await service.create(skill, created_by="test-user")
        assert result.metadata.name == "test-skill"
        assert result.spec.version == "1.0.0"
        assert result.spec.author == "Test Author"
        assert result.kind == KindType.SKILL

    async def test_get_skill(self, service):
        """Test retrieving a skill by name."""
        skill = SkillCRD(
            metadata=Metadata(name="test-skill", namespace="default"),
            spec=SkillSpec(),
        )
        created = await service.create(skill)
        result = await service.get("test-skill", "default")

        assert result is not None
        assert result.metadata.name == "test-skill"
        assert result.id == created.id

    async def test_list_skills(self, service):
        """Test listing skill resources."""
        skill1 = SkillCRD(
            metadata=Metadata(name="skill-1", namespace="default"),
            spec=SkillSpec(),
        )
        skill2 = SkillCRD(
            metadata=Metadata(name="skill-2", namespace="default"),
            spec=SkillSpec(),
        )

        await service.create(skill1)
        await service.create(skill2)

        results = await service.list()
        assert len(results) == 2

    async def test_find_by_author(self, service):
        """Test finding skills by author."""
        skill = SkillCRD(
            metadata=Metadata(name="author-skill", namespace="default"),
            spec=SkillSpec(author="John Doe"),
        )
        await service.create(skill)

        # Create another skill with different author
        skill2 = SkillCRD(
            metadata=Metadata(name="other-skill", namespace="default"),
            spec=SkillSpec(author="Jane Smith"),
        )
        await service.create(skill2)

        john_skills = await service.find_by_author("John Doe")
        assert len(john_skills) == 1
        assert john_skills[0].metadata.name == "author-skill"

    async def test_find_by_tool_name(self, service):
        """Test finding skills by tool name."""
        skill = SkillCRD(
            metadata=Metadata(name="file-skill", namespace="default"),
            spec=SkillSpec(
                tools=[
                    ToolDefinition(name="file_reader", description="Reads files"),
                    ToolDefinition(name="file_writer", description="Writes files"),
                ],
            ),
        )
        await service.create(skill)

        # Create skill without the tool
        skill2 = SkillCRD(
            metadata=Metadata(name="web-skill", namespace="default"),
            spec=SkillSpec(
                tools=[
                    ToolDefinition(name="web_search", description="Searches web"),
                ],
            ),
        )
        await service.create(skill2)

        file_skills = await service.find_by_tool_name("file_reader")
        assert len(file_skills) == 1
        assert file_skills[0].metadata.name == "file-skill"

    async def test_delete_skill(self, service):
        """Test soft deleting a skill resource."""
        skill = SkillCRD(
            metadata=Metadata(name="test-skill", namespace="default"),
            spec=SkillSpec(),
        )
        await service.create(skill)

        deleted = await service.delete("test-skill", "default")
        assert deleted is True

        result = await service.get("test-skill", "default")
        assert result is None
