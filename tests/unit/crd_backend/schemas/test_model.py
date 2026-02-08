"""Unit tests for Model Pydantic schemas.

Tests: 5 tests covering ModelSpec, ModelConfig, ModelCRD, ModelResponse
"""

import pytest
from pydantic import ValidationError

from backend.schemas.model import ModelConfig, ModelSpec, ModelCRD, ModelCreateRequest, ModelResponse
from backend.schemas.base import Metadata
from backend.models.kinds import KindType


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestModelConfig:
    """Test suite for ModelConfig schema - 3 tests."""

    def test_valid_config(self):
        """Test creating valid model config."""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4",
            timeout=60,
            max_retries=5,
        )
        assert config.provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_required_fields(self):
        """Test required fields."""
        with pytest.raises(ValidationError):
            ModelConfig()

    def test_optional_defaults(self):
        """Test optional field defaults."""
        config = ModelConfig(provider="anthropic", model_name="claude-3")
        assert config.timeout == 30
        assert config.max_retries == 3


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestModelSpec:
    """Test suite for ModelSpec schema - 4 tests."""

    def test_valid_spec(self):
        """Test creating valid model spec."""
        spec = ModelSpec(
            config=ModelConfig(provider="openai", model_name="gpt-4"),
            capabilities=["chat", "vision"],
            context_length=8192,
        )
        assert spec.config.provider == "openai"
        assert spec.capabilities == ["chat", "vision"]
        assert spec.context_length == 8192

    def test_default_temperature(self):
        """Test default temperature."""
        spec = ModelSpec(
            config=ModelConfig(provider="openai", model_name="gpt-3.5"),
        )
        assert spec.default_temperature == 0.7

    def test_temperature_range(self):
        """Test temperature validation."""
        with pytest.raises(ValidationError):
            ModelSpec(
                config=ModelConfig(provider="openai", model_name="gpt-4"),
                default_temperature=3.0,
            )

    def test_cost_structure(self):
        """Test cost per token structure."""
        spec = ModelSpec(
            config=ModelConfig(provider="openai", model_name="gpt-4"),
            cost_per_1k_tokens={"input": 0.01, "output": 0.03},
        )
        assert spec.cost_per_1k_tokens["input"] == 0.01


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestModelCRD:
    """Test suite for ModelCRD schema - 2 tests."""

    def test_valid_crd(self):
        """Test creating valid Model CRD."""
        crd = ModelCRD(
            metadata=Metadata(name="my-model"),
            spec=ModelSpec(
                config=ModelConfig(provider="openai", model_name="gpt-4"),
            ),
        )
        assert crd.kind == KindType.MODEL
        assert crd.metadata.name == "my-model"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestModelCreateRequest:
    """Test suite for ModelCreateRequest - 2 tests."""

    def test_valid_request(self):
        """Test valid create request."""
        request = ModelCreateRequest(
            metadata=Metadata(name="new-model"),
            spec=ModelSpec(
                config=ModelConfig(provider="anthropic", model_name="claude-3"),
            ),
        )
        assert request.metadata.name == "new-model"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestModelResponse:
    """Test suite for ModelResponse - 2 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4

        response = ModelResponse(
            id=uuid4(),
            metadata=Metadata(name="response-model"),
            spec=ModelSpec(
                config=ModelConfig(provider="openai", model_name="gpt-4"),
            ),
        )
        assert response.kind == "model"
        assert response.spec.config.provider == "openai"
