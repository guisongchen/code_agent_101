"""
Tests for SkillManager - Epic 3: Tools System.
"""

import pytest
from chat_shell_101.skills.manager import SkillManager
from chat_shell_101.skills.base import BaseSkill, SkillConfig, SkillContext
from chat_shell_101.skills.exceptions import SkillNotFoundError, SkillAlreadyLoadedError


pytestmark = [pytest.mark.unit, pytest.mark.epic_3]


class MockSkill(BaseSkill):
    """Mock skill for testing."""

    def __init__(self, name="mock_skill"):
        self.config = SkillConfig(name=name)
        self.initialized = False
        self.shutdown_called = False

    async def initialize(self, context: SkillContext) -> None:
        self.initialized = True
        self._initialized = True

    async def shutdown(self) -> None:
        self.shutdown_called = True


class TestSkillManager:
    """Test cases for SkillManager."""

    @pytest.fixture
    def manager(self):
        return SkillManager()

    @pytest.fixture
    def context(self):
        return SkillContext(session_id="test_session")

    def test_initial_state(self, manager):
        """Test initial manager state."""
        assert manager.get_loaded_skills() == []
        assert manager.get_active_skills() == []

    @pytest.mark.asyncio
    async def test_load_skill(self, manager, context):
        """Test loading a skill."""
        manager.set_context(context)
        skill = MockSkill("test_skill")

        loaded = await manager.load_skill("test_skill", skill_class=lambda: skill)

        assert loaded is skill
        assert "test_skill" in manager.get_loaded_skills()

    @pytest.mark.asyncio
    async def test_load_duplicate_skill(self, manager, context):
        """Test loading duplicate skill raises error."""
        manager.set_context(context)
        skill = MockSkill("dup_skill")

        await manager.load_skill("dup_skill", skill_class=lambda: skill)

        with pytest.raises(SkillAlreadyLoadedError):
            await manager.load_skill("dup_skill", skill_class=lambda: skill)

    @pytest.mark.asyncio
    async def test_activate_skill(self, manager, context):
        """Test activating a skill."""
        manager.set_context(context)
        skill = MockSkill("active_skill")

        await manager.load_skill("active_skill", skill_class=lambda: skill)
        await manager.activate_skill("active_skill")

        assert "active_skill" in manager.get_active_skills()

    @pytest.mark.asyncio
    async def test_activate_not_loaded_skill(self, manager):
        """Test activating a skill that isn't loaded."""
        with pytest.raises(SkillNotFoundError):
            await manager.activate_skill("not_loaded")

    @pytest.mark.asyncio
    async def test_deactivate_skill(self, manager, context):
        """Test deactivating a skill."""
        manager.set_context(context)
        skill = MockSkill("deactivate_skill")

        await manager.load_skill("deactivate_skill", skill_class=lambda: skill)
        await manager.activate_skill("deactivate_skill")
        await manager.deactivate_skill("deactivate_skill")

        assert "deactivate_skill" not in manager.get_active_skills()

    @pytest.mark.asyncio
    async def test_unload_skill(self, manager, context):
        """Test unloading a skill."""
        manager.set_context(context)
        skill = MockSkill("unload_skill")

        await manager.load_skill("unload_skill", skill_class=lambda: skill)
        await manager.unload_skill("unload_skill")

        assert "unload_skill" not in manager.get_loaded_skills()

    @pytest.mark.asyncio
    async def test_unload_not_loaded_skill(self, manager):
        """Test unloading a skill that isn't loaded."""
        with pytest.raises(SkillNotFoundError):
            await manager.unload_skill("not_loaded")

    @pytest.mark.asyncio
    async def test_get_active_tools(self, manager, context):
        """Test getting tools from active skills."""
        manager.set_context(context)
        skill = MockSkill("tools_skill")

        await manager.load_skill("tools_skill", skill_class=lambda: skill)
        await manager.activate_skill("tools_skill")

        tools = manager.get_active_tools()
        assert tools == []  # Mock skill returns empty list

    @pytest.mark.asyncio
    async def test_unload_all(self, manager, context):
        """Test unloading all skills."""
        manager.set_context(context)

        await manager.load_skill("skill1", skill_class=lambda: MockSkill("skill1"))
        await manager.load_skill("skill2", skill_class=lambda: MockSkill("skill2"))

        await manager.unload_all()

        assert manager.get_loaded_skills() == []
