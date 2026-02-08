"""Unit tests for Team Pydantic schemas.

Tests: 5 tests covering TeamSpec, TeamMember, TeamCRD with member validation
"""

import pytest
from pydantic import ValidationError

from backend.schemas.team import TeamMember, TeamSpec, TeamCRD, TeamCreateRequest, TeamResponse
from backend.schemas.base import Metadata, ResourceRef
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTeamMember:
    """Test suite for TeamMember - 2 tests."""

    def test_valid_member(self):
        """Test creating valid team member."""
        member = TeamMember(
            bot_ref=ResourceRef(kind=KindType.BOT, name="my-bot"),
            role="worker",
            priority=1,
        )
        assert member.bot_ref.name == "my-bot"
        assert member.role == "worker"
        assert member.priority == 1

    def test_default_priority(self):
        """Test default priority."""
        member = TeamMember(
            bot_ref=ResourceRef(kind=KindType.BOT, name="bot"),
            role="leader",
        )
        assert member.priority == 0


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTeamSpec:
    """Test suite for TeamSpec - 4 tests."""

    def test_valid_spec(self):
        """Test creating valid team spec."""
        spec = TeamSpec(
            members=[
                TeamMember(
                    bot_ref=ResourceRef(kind=KindType.BOT, name="leader-bot"),
                    role="leader",
                ),
            ],
            coordination_strategy="hierarchical",
        )
        assert len(spec.members) == 1
        assert spec.coordination_strategy == "hierarchical"

    def test_member_validation(self):
        """Test members must reference Bot resources."""
        with pytest.raises(ValidationError) as exc_info:
            TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.GHOST, name="not-a-bot"),
                        role="worker",
                    ),
                ],
            )
        assert "Team members must reference Bot resources" in str(exc_info.value)

    def test_min_members(self):
        """Test at least one member required."""
        with pytest.raises(ValidationError):
            TeamSpec(members=[])

    def test_default_coordination(self):
        """Test default coordination strategy."""
        spec = TeamSpec(
            members=[
                TeamMember(
                    bot_ref=ResourceRef(kind=KindType.BOT, name="bot"),
                    role="worker",
                ),
            ],
        )
        assert spec.coordination_strategy == "sequential"
        assert spec.shared_context is True


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTeamCRD:
    """Test suite for TeamCRD - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Team CRD."""
        crd = TeamCRD(
            metadata=Metadata(name="my-team"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot1"),
                        role="leader",
                    ),
                ],
            ),
        )
        assert crd.kind == KindType.TEAM
        assert crd.metadata.name == "my-team"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTeamCreateRequest:
    """Test suite for TeamCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = TeamCreateRequest(
            metadata=Metadata(name="new-team"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot1"),
                        role="leader",
                    ),
                ],
            ),
        )
        assert request.metadata.name == "new-team"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTeamResponse:
    """Test suite for TeamResponse - 2 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = TeamResponse(
            id=uuid4(),
            metadata=Metadata(name="response-team"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot1"),
                        role="leader",
                    ),
                ],
            ),
        )
        assert response.kind == "team"
        assert len(response.spec.members) == 1
