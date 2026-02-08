"""
Tests for skills base classes - Epic 3: Tools System.
"""

import pytest
from chat_shell.skills.base import BaseSkill, SkillConfig, SkillContext


pytestmark = [pytest.mark.chat_shell, pytest.mark.unit, pytest.mark.epic_3]


class TestSkillConfig:
    """Test cases for SkillConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SkillConfig(name="test_skill")
        assert config.name == "test_skill"
        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.author is None
        assert config.dependencies == []
        assert config.config == {}

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SkillConfig(
            name="my_skill",
            version="2.0.0",
            description="A test skill",
            author="Test Author",
            dependencies=["numpy", "pandas"],
            config={"setting": "value"}
        )
        assert config.name == "my_skill"
        assert config.version == "2.0.0"
        assert config.description == "A test skill"
        assert config.author == "Test Author"
        assert config.dependencies == ["numpy", "pandas"]
        assert config.config == {"setting": "value"}


class TestSkillContext:
    """Test cases for SkillContext."""

    def test_default_values(self):
        """Test default context values."""
        context = SkillContext()
        assert context.session_id is None
        assert context.user_id is None
        assert context.metadata == {}

    def test_custom_values(self):
        """Test custom context values."""
        context = SkillContext(
            session_id="sess_123",
            user_id="user_456",
            metadata={"key": "value"}
        )
        assert context.session_id == "sess_123"
        assert context.user_id == "user_456"
        assert context.metadata == {"key": "value"}


class TestBaseSkill:
    """Test cases for BaseSkill."""

    def test_skill_is_abstract(self):
        """Test that BaseSkill is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSkill()

    def test_concrete_skill(self):
        """Test creating a concrete skill implementation."""
        class TestSkill(BaseSkill):
            def __init__(self):
                self.config = SkillConfig(name="test")

            async def initialize(self, context: SkillContext) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        skill = TestSkill()
        assert skill.config.name == "test"
        assert skill.is_initialized is False

    def test_get_tools_default(self):
        """Test default get_tools returns empty list."""
        class TestSkill(BaseSkill):
            def __init__(self):
                self.config = SkillConfig(name="test")

            async def initialize(self, context: SkillContext) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        skill = TestSkill()
        assert skill.get_tools() == []

    def test_get_prompts_default(self):
        """Test default get_prompts returns empty dict."""
        class TestSkill(BaseSkill):
            def __init__(self):
                self.config = SkillConfig(name="test")

            async def initialize(self, context: SkillContext) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        skill = TestSkill()
        assert skill.get_prompts() == {}

    def test_modify_system_prompt_default(self):
        """Test default modify_system_prompt returns unchanged prompt."""
        class TestSkill(BaseSkill):
            def __init__(self):
                self.config = SkillConfig(name="test")

            async def initialize(self, context: SkillContext) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        skill = TestSkill()
        prompt = "Original prompt"
        assert skill.modify_system_prompt(prompt) == prompt
