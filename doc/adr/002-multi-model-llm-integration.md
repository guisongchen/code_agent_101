# ADR 002: Multi-Model LLM Integration

## Status

Accepted

## Context

Epic 1 provided a solid core agent system, but it was tightly coupled to OpenAI models. The system needed to support multiple LLM providers (OpenAI, Anthropic, Google) to:
- Provide flexibility for users with different provider preferences
- Enable fallback mechanisms when one provider is unavailable
- Support model-specific features while maintaining a unified interface
- Handle provider-specific message formats transparently

## Decision

We implemented a dedicated `models` module that abstracts provider differences through a factory pattern with configuration management and message format conversion.

### 1. ModelFactory with Provider Detection

**Decision:** Use a factory pattern with automatic provider detection from model names.

**Rationale:**
- Users shouldn't need to specify provider explicitly for common models
- Model names are unique identifiers that map to specific providers
- Pattern-based detection (e.g., "gpt-*" → OpenAI, "claude*" → Anthropic) is reliable
- Factory encapsulates provider-specific instantiation logic

**Implementation:**
```python
# Auto-detection based on model name
llm = ModelFactory.create_model(model="claude-3-opus-20240229")  # Detects Anthropic
llm = ModelFactory.create_model(model="gpt-4")                   # Detects OpenAI
llm = ModelFactory.create_model(model="gemini-pro")              # Detects Google

# Explicit provider override when needed
llm = ModelFactory.create_model(
    model="custom-model",
    provider=ModelProvider.OPENAI
)
```

**Provider Detection Patterns:**
| Provider | Patterns |
|----------|----------|
| OpenAI | `gpt-*`, `text-davinci*`, `text-curie*`, `text-babbage*`, `text-ada*` |
| Anthropic | `claude*`, `anthropic*` |
| Google | `gemini*`, `palm*`, `bison*` |

**Location:** `chat_shell_101/models/factory.py`

### 2. ModelConfig and ProviderConfig Dataclasses

**Decision:** Use dataclasses for configuration with validation in `__post_init__`.

**Rationale:**
- Type-safe configuration with IDE autocomplete support
- Validation at creation time prevents runtime errors
- Immutable-by-default with `frozen` option possible
- Clear separation between model params and provider settings

**Configuration Hierarchy:**
```
ModelConfig
├── provider: Optional[str]              # Auto-detected if None
├── model: str                           # Model identifier
├── temperature: float                   # Generation params
├── max_tokens: int
├── top_p: Optional[float]
├── frequency_penalty: Optional[float]
├── presence_penalty: Optional[float]
├── streaming: bool
├── timeout: float
├── provider_config: ProviderConfig      # Provider-specific settings
│   ├── api_key: Optional[str]
│   ├── base_url: Optional[str]         # For custom endpoints
│   ├── timeout: float
│   ├── max_retries: int
│   ├── extra_headers: Optional[Dict]
│   ├── organization: Optional[str]     # OpenAI-specific
│   └── project: Optional[str]          # OpenAI-specific
├── fallback_models: List[str]           # Failover chain
└── fallback_providers: List[str]
```

**Fluent API for Fallbacks:**
```python
config = ModelConfig(
    model="gpt-4",
    temperature=0.7
).with_fallback("gpt-3.5-turbo", "claude-3-haiku-20240307")
```

**Location:** `chat_shell_101/models/config.py`

### 3. FallbackModelWrapper

**Decision:** Implement fallback as a wrapper that implements the same interface as LangChain models.

**Rationale:**
- Transparent fallback without changing caller code
- Lazy initialization of fallback models (only create if needed)
- Supports both sync (`invoke`) and async (`ainvoke`, `astream`) operations
- Tool binding propagated to all fallback models

**Fallback Chain:**
```
Primary Model → Fallback 1 → Fallback 2 → ... → Error
   (gpt-4)      (gpt-3.5)     (claude-haiku)
```

**Usage:**
```python
config = ModelConfig(
    model="gpt-4",
    fallback_models=["gpt-3.5-turbo", "claude-3-haiku-20240307"]
)
wrapper = ModelFactory.create_model_with_fallbacks(config)

# Uses gpt-4 if available, falls back automatically on failure
response = await wrapper.ainvoke(messages)
```

**Error Reporting:**
- `FallbackError` raised when all models fail
- Includes error details from each attempted model
- Helps diagnose whether issue is provider-specific

**Location:** `chat_shell_101/models/factory.py` (FallbackModelWrapper class)

### 4. Message Format Conversion

**Decision:** Implement explicit message converters for provider-specific formats.

**Rationale:**
- Different providers have incompatible message formats
- Anthropic: Uses `human`/`assistant` roles, separate system prompt
- Google: Uses `user`/`model` roles, no system messages
- OpenAI: Standard format with tool call schema
- Converting at the boundary keeps provider-specific code isolated

**Conversion Matrix:**

| Feature | OpenAI | Anthropic | Google |
|---------|--------|-----------|--------|
| User role | `user` | `human` | `user` |
| AI role | `assistant` | `assistant` | `model` |
| System | In message list | Separate param | Converted to user |
| Tool calls | `tool_calls` array | `tool_use` blocks | Not supported |
| Tool results | `tool` role | `tool_result` blocks | User message |

**Implementation:**
```python
# OpenAI format (standard)
[{"role": "system", "content": "..."},
 {"role": "user", "content": "..."}]

# Anthropic format (system extracted)
{"system": "...",
 "messages": [{"role": "human", "content": "..."}]}

# Google format (system converted to user)
[{"role": "user", "parts": [{"text": "System instruction: ..."}]},
 {"role": "user", "parts": [{"text": "..."}]}]
```

**Location:** `chat_shell_101/models/converter.py`

### 5. Optional Dependencies

**Decision:** Make non-OpenAI providers optional dependencies.

**Rationale:**
- Keep core package lightweight
- Users install only what they need
- Prevents import errors when optional providers not used
- Clear error messages when trying to use uninstalled provider

**pyproject.toml:**
```toml
[project.optional-dependencies]
anthropic = ["langchain-anthropic>=0.1.0"]
google = ["langchain-google-genai>=1.0.0"]
all = ["langchain-anthropic>=0.1.0", "langchain-google-genai>=1.0.0"]
```

**Runtime Check:**
```python
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    raise ModelInitializationError(
        "langchain-anthropic is not installed. "
        "Install with: pip install langchain-anthropic"
    )
```

### 6. Custom Exception Hierarchy

**Decision:** Create provider-aware exception hierarchy.

**Rationale:**
- Distinguish between model errors and other errors
- Include provider/model context for debugging
- Specific error types for different failure modes
- FallbackError aggregates multiple errors

**Exception Hierarchy:**
```
ModelError (base)
├── ModelNotSupportedError    # Unknown provider/model
├── ModelInitializationError  # Setup/connection failures
│   └── cause: original exception
├── ModelAPIError            # Runtime API failures
│   ├── status_code: HTTP status
│   └── cause: original exception
├── FallbackError            # All models failed
│   └── errors: List[str]    # Per-model errors
└── MessageConversionError   # Format conversion failures
    ├── source_format
    └── target_format
```

**Location:** `chat_shell_101/models/exceptions.py`

### 7. Integration with Agent System

**Decision:** Integrate model factory into existing AgentConfig and LangGraphAgentBuilder.

**Rationale:**
- Maintain backward compatibility with Epic 1
- Provider selection is just another configuration option
- Fallback support added without changing agent logic
- Builder pattern extended with `with_provider()`, `with_fallbacks()`

**AgentConfig additions:**
```python
@dataclass
class AgentConfig:
    provider: Optional[str] = None  # Auto-detected if None
    fallback_models: List[str] = field(default_factory=list)
    enable_fallback: bool = False
```

**Builder API:**
```python
agent = (LangGraphAgentBuilder()
    .with_model("claude-3-opus-20240229")
    .with_provider("anthropic")  # Optional, can auto-detect
    .with_fallbacks(["gpt-4", "claude-3-sonnet"])
    .build())
```

**Location:** `chat_shell_101/agent/config.py`, `chat_shell_101/agent/builder.py`, `chat_shell_101/agent/agent.py`

## Consequences

### Positive

- **Provider flexibility**: Users can switch models by changing a string
- **Automatic fallback**: System resilience against provider outages
- **Clean abstraction**: Provider details hidden behind unified interface
- **Type safety**: Configuration validated at creation time
- **Extensibility**: New providers added by extending factory
- **Error clarity**: Provider-specific context in error messages

### Negative

- **Complexity**: Additional abstraction layer to understand
- **Conversion overhead**: Message format conversion adds processing
- **Dependency management**: Optional dependencies require explicit installation
- **Testing surface**: More combinations to test (N providers × M models)
- **Feature parity**: Not all provider features exposed through unified interface

## Alternatives Considered

### Alternative 1: LangChain's Built-in Model Selection

LangChain provides some abstraction, but:
- No automatic provider detection from model names
- No built-in fallback mechanism
- Less control over provider-specific configuration

**Rejected**: Needed more control over configuration and fallback behavior.

### Alternative 2: Adapter Pattern

Create adapter classes for each provider:

```python
class AnthropicAdapter(BaseModelAdapter):
    def invoke(self, messages): ...
```

**Rejected**: LangChain models already provide a common interface. Additional adapter layer would add complexity without benefit.

### Alternative 3: Configuration via Environment Only

Use environment variables exclusively for provider configuration:

```bash
export PROVIDER=anthropic
export MODEL=claude-3-opus
```

**Rejected**: Programmatic configuration needed for multi-tenant use cases and dynamic provider selection.

## Implementation Notes

### Dependencies

```toml
# Core (always required)
langchain-openai>=0.0.1

# Optional
langchain-anthropic>=0.1.0  # For Anthropic models
langchain-google-genai>=1.0.0  # For Google Gemini
```

### Testing Strategy

- Unit tests for each provider's configuration
- Mock-based tests for factory (no API calls)
- Message conversion tests with fixtures
- Fallback wrapper tests with mock failures

### Migration from Epic 1

Existing code continues to work:
```python
# Epic 1 style (still works)
agent = LangGraphAgentBuilder().with_model("gpt-4").build()

# Epic 2 style (new capabilities)
agent = (LangGraphAgentBuilder()
    .with_model("claude-3-opus-20240229")
    .with_fallbacks(["gpt-4"])
    .build())
```

## References

- [LangChain Chat Models Documentation](https://python.langchain.com/docs/integrations/chat/)
- [Anthropic Message Format](https://docs.anthropic.com/claude/reference/messages_post)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [Google Gemini API](https://ai.google.dev/docs/gemini_api_overview)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
