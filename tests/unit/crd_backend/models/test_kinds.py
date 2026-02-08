"""Unit tests for SQLAlchemy Kind model.

Tests: 6 tests covering Kind model functionality
"""

import uuid
from datetime import datetime

import pytest

from backend.models.kinds import Kind, KindType


@pytest.mark.epic_7
@pytest.mark.unit
@pytest.mark.backend
class TestKindModel:
    """Test suite for Kind model - 6 tests."""

    def test_kind_creation(self, db_session):
        """Test basic Kind creation with all required fields."""
        kind = Kind(
            kind=KindType.GHOST,
            api_version="v1",
            name="test-ghost",
            namespace="default",
            spec={"system_prompt": "You are a helpful assistant"},
        )
        db_session.add(kind)
        db_session.commit()

        assert kind.id is not None
        assert isinstance(kind.id, uuid.UUID)
        assert kind.kind == KindType.GHOST
        assert kind.name == "test-ghost"
        assert kind.namespace == "default"
        assert kind.spec == {"system_prompt": "You are a helpful assistant"}
        assert kind.created_at is not None
        assert kind.updated_at is not None

    def test_kind_unique_constraint(self, db_session):
        """Test unique constraint on (kind, name, namespace)."""
        kind1 = Kind(
            kind=KindType.GHOST,
            name="unique-ghost",
            namespace="default",
            spec={},
        )
        db_session.add(kind1)
        db_session.commit()

        # Attempt to create duplicate should fail
        kind2 = Kind(
            kind=KindType.GHOST,
            name="unique-ghost",
            namespace="default",
            spec={},
        )
        db_session.add(kind2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_kind_soft_delete(self, db_session):
        """Test soft delete functionality."""
        kind = Kind(
            kind=KindType.MODEL,
            name="test-model",
            namespace="default",
            spec={"provider": "openai"},
        )
        db_session.add(kind)
        db_session.commit()

        # Initially not deleted
        assert kind.deleted_at is None
        assert not kind.is_deleted

        # Soft delete
        kind.soft_delete()
        db_session.commit()

        assert kind.deleted_at is not None
        assert kind.is_deleted
        assert isinstance(kind.deleted_at, datetime)

        # Restore
        kind.restore()
        db_session.commit()

        assert kind.deleted_at is None
        assert not kind.is_deleted

    def test_kind_all_types(self, db_session):
        """Test creating all Kind types."""
        types = [
            (KindType.GHOST, "my-ghost", {"prompt": "test"}),
            (KindType.MODEL, "my-model", {"model": "gpt-4"}),
            (KindType.SHELL, "my-shell", {"type": "chat"}),
            (KindType.BOT, "my-bot", {"ghost": "my-ghost"}),
            (KindType.TEAM, "my-team", {"bots": ["my-bot"]}),
            (KindType.SKILL, "my-skill", {"code": "print('hello')"}),
        ]

        for kind_type, name, spec in types:
            kind = Kind(
                kind=kind_type,
                name=name,
                namespace="test-ns",
                spec=spec,
            )
            db_session.add(kind)

        db_session.commit()

        # Verify all were created
        all_kinds = db_session.query(Kind).all()
        assert len(all_kinds) == 6

        for kind in all_kinds:
            assert kind.kind in [t[0] for t in types]

    def test_kind_name_validation(self, db_session):
        """Test name validation rules."""
        # Valid names
        valid_names = ["valid-name", "name123", "a", "a-b-c"]
        for name in valid_names:
            kind = Kind(
                kind=KindType.GHOST,
                name=name,
                namespace="default",
                spec={},
            )
            db_session.add(kind)
            db_session.commit()
            db_session.delete(kind)
            db_session.commit()

        # Invalid names
        invalid_names = ["", "Invalid-Name", "name_123", "-invalid", "invalid-"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                Kind(
                    kind=KindType.GHOST,
                    name=name,
                    namespace="default",
                    spec={},
                )

    def test_kind_to_dict(self, db_session):
        """Test dictionary serialization."""
        kind = Kind(
            kind=KindType.BOT,
            api_version="v1",
            name="test-bot",
            namespace="production",
            spec={"ghost": "my-ghost", "model": "my-model"},
            created_by="user123",
        )
        db_session.add(kind)
        db_session.commit()

        data = kind.to_dict()

        assert data["apiVersion"] == "v1"
        assert data["kind"] == "bot"
        assert data["metadata"]["name"] == "test-bot"
        assert data["metadata"]["namespace"] == "production"
        assert data["metadata"]["createdBy"] == "user123"
        assert data["spec"] == {"ghost": "my-ghost", "model": "my-model"}
        assert "id" in data["metadata"]
        assert "createdAt" in data["metadata"]
        assert "updatedAt" in data["metadata"]
