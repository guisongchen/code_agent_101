"""Unit tests for base Pydantic schemas.

Tests: 8 tests covering Metadata, ResourceRef, BaseCRD
"""

import pytest
from pydantic import ValidationError

from backend.schemas.base import Metadata, ResourceRef, BaseSpec
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestMetadata:
    """Test suite for Metadata schema - 4 tests."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = Metadata(
            name="my-resource",
            namespace="default",
            created_by="user@example.com",
        )
        assert metadata.name == "my-resource"
        assert metadata.namespace == "default"
        assert metadata.created_by == "user@example.com"

    def test_default_namespace(self):
        """Test default namespace is 'default'."""
        metadata = Metadata(name="test-resource")
        assert metadata.namespace == "default"
        assert metadata.created_by is None

    def test_invalid_name_format(self):
        """Test name validation rejects invalid formats."""
        with pytest.raises(ValidationError) as exc_info:
            Metadata(name="Invalid_Name")
        assert "Name must consist of lowercase alphanumeric" in str(exc_info.value)

    def test_invalid_namespace_format(self):
        """Test namespace validation rejects invalid formats."""
        with pytest.raises(ValidationError) as exc_info:
            Metadata(name="valid-name", namespace="Invalid_Namespace")
        assert "Namespace must consist of lowercase alphanumeric" in str(exc_info.value)


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestResourceRef:
    """Test suite for ResourceRef schema - 4 tests."""

    def test_valid_resource_ref(self):
        """Test creating valid resource reference."""
        ref = ResourceRef(
            kind=KindType.GHOST,
            name="my-ghost",
            namespace="production",
        )
        assert ref.kind == KindType.GHOST
        assert ref.name == "my-ghost"
        assert ref.namespace == "production"

    def test_default_namespace(self):
        """Test default namespace for resource reference."""
        ref = ResourceRef(kind=KindType.MODEL, name="gpt-4")
        assert ref.namespace == "default"

    def test_all_kind_types(self):
        """Test resource references for all kind types."""
        for kind in KindType:
            ref = ResourceRef(kind=kind, name=f"test-{kind.value}")
            assert ref.kind == kind

    def test_invalid_name_format(self):
        """Test name validation in resource reference."""
        with pytest.raises(ValidationError) as exc_info:
            ResourceRef(kind=KindType.BOT, name="InvalidName")
        assert "Name must consist of lowercase alphanumeric" in str(exc_info.value)


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestBaseSpec:
    """Test suite for BaseSpec schema - 2 tests."""

    def test_default_description(self):
        """Test default description is None."""
        spec = BaseSpec()
        assert spec.description is None

    def test_custom_description(self):
        """Test setting custom description."""
        spec = BaseSpec(description="Test description")
        assert spec.description == "Test description"
