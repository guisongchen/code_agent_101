"""Unit tests for ModelService.

Tests: 6 tests covering ModelService CRUD operations
"""

import pytest
import pytest_asyncio

from backend.services.model import ModelService
from backend.models.kinds import KindType
from backend.schemas.model import ModelConfig, ModelSpec, ModelCRD, Metadata


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestModelService:
    """Test suite for ModelService - 6 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create ModelService instance."""
        return ModelService(async_session)

    async def test_create_model(self, service, model_schema):
        """Test creating a model resource."""
        result = await service.create(model_schema, created_by="test-user")

        assert result.metadata.name == "test-model"
        assert result.spec.config.provider == "openai"
        assert result.spec.config.model_name == "gpt-4"
        assert result.kind == KindType.MODEL

    async def test_get_model(self, service, model_schema):
        """Test retrieving a model by name."""
        created = await service.create(model_schema)
        result = await service.get("test-model", "default")

        assert result is not None
        assert result.metadata.name == "test-model"
        assert result.id == created.id

    async def test_list_models(self, service, model_schema):
        """Test listing model resources."""
        await service.create(model_schema)

        # Create another model
        model2 = ModelCRD(
            metadata=Metadata(name="another-model", namespace="default"),
            spec=ModelSpec(
                config=ModelConfig(provider="anthropic", model_name="claude-3"),
            ),
        )
        await service.create(model2)

        results = await service.list()
        assert len(results) == 2

    async def test_find_by_provider(self, service, model_schema):
        """Test finding models by provider."""
        await service.create(model_schema)

        # Create model with different provider
        model2 = ModelCRD(
            metadata=Metadata(name="anthropic-model", namespace="default"),
            spec=ModelSpec(
                config=ModelConfig(provider="anthropic", model_name="claude-3"),
            ),
        )
        await service.create(model2)

        openai_models = await service.find_by_provider("openai")
        assert len(openai_models) == 1
        assert openai_models[0].metadata.name == "test-model"

    async def test_find_by_capability(self, service, model_schema):
        """Test finding models by capability."""
        # Create model with capabilities
        model_with_caps = ModelCRD(
            metadata=Metadata(name="vision-model", namespace="default"),
            spec=ModelSpec(
                config=ModelConfig(provider="openai", model_name="gpt-4-vision"),
                capabilities=["chat", "vision"],
            ),
        )
        await service.create(model_with_caps)

        vision_models = await service.find_by_capability("vision")
        assert len(vision_models) == 1
        assert vision_models[0].metadata.name == "vision-model"

    async def test_delete_model(self, service, model_schema):
        """Test soft deleting a model resource."""
        await service.create(model_schema)

        deleted = await service.delete("test-model", "default")
        assert deleted is True

        result = await service.get("test-model", "default")
        assert result is None
