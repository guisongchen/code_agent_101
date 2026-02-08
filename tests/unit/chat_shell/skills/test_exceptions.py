"""
Tests for skills exceptions - Epic 3: Tools System.
"""

import pytest
from chat_shell.skills.exceptions import (
    SkillError,
    SkillNotFoundError,
    SkillLoadError,
    SkillAlreadyLoadedError,
    SkillInitializationError,
)


pytestmark = [pytest.mark.chat_shell, pytest.mark.unit, pytest.mark.epic_3]


class TestSkillExceptions:
    """Test cases for skill exceptions."""

    def test_skill_error_basic(self):
        """Test basic skill error."""
        error = SkillError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.skill_name is None

    def test_skill_error_with_name(self):
        """Test skill error with skill name."""
        error = SkillError("Load failed", skill_name="data_analysis")
        assert "data_analysis" in str(error)
        assert "Load failed" in str(error)
        assert error.skill_name == "data_analysis"

    def test_skill_not_found_error(self):
        """Test skill not found error."""
        error = SkillNotFoundError("unknown_skill")
        assert "unknown_skill" in str(error)
        assert error.skill_name == "unknown_skill"

    def test_skill_load_error(self):
        """Test skill load error."""
        error = SkillLoadError("Module import failed", skill_name="broken_skill")
        assert error.skill_name == "broken_skill"

    def test_skill_already_loaded_error(self):
        """Test skill already loaded error."""
        error = SkillAlreadyLoadedError("duplicate_skill")
        assert "duplicate_skill" in str(error)
        assert error.skill_name == "duplicate_skill"

    def test_skill_initialization_error(self):
        """Test skill initialization error."""
        error = SkillInitializationError("Config missing", skill_name="init_skill")
        assert error.skill_name == "init_skill"
        assert "Config missing" in str(error)
