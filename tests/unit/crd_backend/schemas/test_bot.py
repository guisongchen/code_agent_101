"""Unit tests for Bot Pydantic schemas.

Tests: 6 tests covering BotSpec, BotCRD, BotResponse with reference validation
"""

import pytest
from pydantic import ValidationError

from backend.schemas.bot import BotSpec, BotCRD, BotCreateRequest, BotResponse
from backend.schemas.base import Metadata, ResourceRef
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestBotSpec:
    """Test suite for BotSpec schema - 5 tests."""

    def test_valid_spec(self):
        """Test creating valid bot spec with all references."""
        spec = BotSpec(
            ghost_ref=ResourceRef(kind=KindType.GHOST, name="my-ghost"),
            model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
            shell_ref=ResourceRef(kind=KindType.SHELL, name="chat-shell"),
        )
        assert spec.ghost_ref.name == "my-ghost"
        assert spec.model_ref.name == "gpt-4"
        assert spec.shell_ref.name == "chat-shell"

    def test_ghost_ref_validation(self):
        """Test ghost_ref must reference a Ghost resource."""
        with pytest.raises(ValidationError) as exc_info:
            BotSpec(
                ghost_ref=ResourceRef(kind=KindType.MODEL, name="wrong-kind"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            )
        assert "ghostRef must reference a Ghost resource" in str(exc_info.value)

    def test_model_ref_validation(self):
        """Test model_ref must reference a Model resource."""
        with pytest.raises(ValidationError) as exc_info:
            BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.SHELL, name="wrong-kind"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            )
        assert "modelRef must reference a Model resource" in str(exc_info.value)

    def test_shell_ref_validation(self):
        """Test shell_ref must reference a Shell resource."""
        with pytest.raises(ValidationError) as exc_info:
            BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.BOT, name="wrong-kind"),
            )
        assert "shellRef must reference a Shell resource" in str(exc_info.value)

    def test_skills_validation(self):
        """Test skills must reference Skill resources."""
        with pytest.raises(ValidationError) as exc_info:
            BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
                skills=[ResourceRef(kind=KindType.GHOST, name="wrong")],
            )
        assert "skills must reference Skill resources" in str(exc_info.value)

    def test_valid_skills(self):
        """Test valid skills list."""
        spec = BotSpec(
            ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
            model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
            shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            skills=[
                ResourceRef(kind=KindType.SKILL, name="file-reader"),
                ResourceRef(kind=KindType.SKILL, name="web-search"),
            ],
        )
        assert len(spec.skills) == 2
        assert spec.skills[0].name == "file-reader"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestBotCRD:
    """Test suite for BotCRD - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Bot CRD."""
        crd = BotCRD(
            metadata=Metadata(name="my-bot"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            ),
        )
        assert crd.kind == KindType.BOT
        assert crd.metadata.name == "my-bot"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestBotCreateRequest:
    """Test suite for BotCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = BotCreateRequest(
            metadata=Metadata(name="new-bot"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            ),
        )
        assert request.metadata.name == "new-bot"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestBotResponse:
    """Test suite for BotResponse - 2 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = BotResponse(
            id=uuid4(),
            metadata=Metadata(name="response-bot"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name="ghost"),
                model_ref=ResourceRef(kind=KindType.MODEL, name="gpt-4"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name="shell"),
            ),
        )
        assert response.kind == "bot"
        assert response.spec.ghost_ref.name == "ghost"
