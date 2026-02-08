"""Pydantic schemas for Model CRD resources.

Model resources define AI model configurations and API settings.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata


class ModelConfig(BaseModel):
    """Configuration specific to a model provider.

    Contains provider-specific settings like API keys, endpoints, etc.
    """

    model_config = ConfigDict(populate_by_name=True)

    provider: str = Field(
        ...,
        description="Model provider (openai, anthropic, local, etc.)",
        examples=["openai", "anthropic", "ollama"],
    )
    model_name: str = Field(
        ...,
        alias="modelName",
        description="Specific model identifier",
        examples=["gpt-4", "claude-3-opus-20240229", "llama2"],
    )
    api_key: Optional[str] = Field(
        default=None,
        alias="apiKey",
        description="API key for the provider (stored securely)",
    )
    base_url: Optional[str] = Field(
        default=None,
        alias="baseUrl",
        description="Custom base URL for API endpoint",
        examples=["https://api.openai.com/v1", "http://localhost:11434"],
    )
    timeout: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    max_retries: Optional[int] = Field(
        default=3,
        alias="maxRetries",
        ge=0,
        le=10,
        description="Maximum number of retry attempts",
    )


class ModelSpec(BaseSpec):
    """Specification for Model resources.

    Defines AI model configuration including provider settings and capabilities.
    """

    model_config = ConfigDict(populate_by_name=True)

    config: ModelConfig = Field(
        ...,
        description="Model provider configuration",
    )
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="List of model capabilities (chat, completion, embedding, vision)",
        examples=[["chat", "vision"], ["chat", "completion"]],
    )
    context_length: Optional[int] = Field(
        default=None,
        alias="contextLength",
        ge=1,
        description="Maximum context length in tokens",
        examples=[4096, 8192, 100000],
    )
    cost_per_1k_tokens: Optional[Dict[str, float]] = Field(
        default=None,
        alias="costPer1kTokens",
        description="Cost per 1000 tokens (input and output)",
        examples=[{"input": 0.01, "output": 0.03}],
    )
    default_temperature: Optional[float] = Field(
        default=0.7,
        alias="defaultTemperature",
        ge=0.0,
        le=2.0,
        description="Default temperature for this model",
    )
    supports_streaming: Optional[bool] = Field(
        default=True,
        alias="supportsStreaming",
        description="Whether the model supports streaming responses",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional model-specific metadata",
    )


class ModelCRD(BaseCRD):
    """Complete Model CRD schema.

    Represents a Model resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.MODEL
    spec: ModelSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "ModelCRD":
        """Create ModelCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='model'.

        Returns:
            ModelCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            api_version=db_model.api_version,
            kind=KindType.MODEL,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=ModelSpec(**spec_data),
        )


class ModelCreateRequest(BaseModel):
    """Request schema for creating a Model resource.

    Used in POST /api/v1/kinds/models endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Model metadata (name, namespace)",
    )
    spec: ModelSpec = Field(
        ...,
        description="Model specification (configuration, capabilities)",
    )


class ModelResponse(BaseModel):
    """Response schema for Model resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the model",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="model",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Model metadata",
    )
    spec: ModelSpec = Field(
        ...,
        description="Model specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "ModelResponse":
        """Create ModelResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='model'.

        Returns:
            ModelResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="model",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=ModelSpec(**spec_data),
        )
