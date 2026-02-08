# ADR 013: Chat Shell Integration

## Status

Accepted

## Context

With the Backend API providing CRD management for Bots, Ghosts, Models, and Shells (Phase 1), and the Task Management API in place (Epic 12), we needed to integrate the chat_shell module to enable actual AI conversation execution (Epic 13). The integration needed to:

1. **Bridge two architectures**: Connect the Backend's CRD-based configuration with chat_shell's AgentConfig/ChatAgent pattern
2. **Resource mapping**: Transform Bot/Ghost/Model/Shell CRDs into chat_shell configuration
3. **Execution patterns**: Support both streaming (for real-time UIs) and non-streaming (for simple requests) chat
4. **Error handling**: Handle configuration errors, execution failures, and missing references gracefully
5. **Session management**: Leverage chat_shell's checkpointing for conversation persistence

Key questions to resolve:
- How to map Backend CRD fields to chat_shell AgentConfig?
- Should the integration be service-layer or API-layer?
- How to handle chat_shell initialization (lazy vs eager)?
- What execution pattern to expose (streaming vs non-streaming vs both)?
- How to validate Bot configuration before execution?

## Decision

We implemented a service-layer integration with ChatService orchestrating chat_shell execution, supporting both streaming and non-streaming patterns.

### 1. Service-Layer Integration

**Decision:** Create a `ChatService` class that encapsulates all chat_shell interactions.

**Rationale:**
- Clean separation between API layer and chat_shell implementation
- Reusable across different API endpoints (REST, WebSocket, future gRPC)
- Easier to test with mocked dependencies
- Centralizes error handling and logging
- Allows caching/reuse of ChatAgent instances if needed

**Implementation:**
```python
class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bot_service = BotService(session)
        self.ghost_service = GhostService(session)
        self.model_service = ModelService(session)
        self.shell_service = ShellService(session)

    async def create_chat_agent(
        self, bot_name: str, namespace: str = "default"
    ) -> ChatAgent:
        # Fetch Bot and referenced resources
        bot = await self.bot_service.get(bot_name, namespace)
        ghost = await self._get_ghost(bot)
        model = await self._get_model(bot)
        shell = await self._get_shell(bot)

        # Build AgentConfig
        config = self._build_agent_config(ghost, model, shell, bot)

        # Create and initialize ChatAgent
        agent = ChatAgent(config)
        await agent.initialize()
        return agent
```

**Location:** `backend/services/chat.py`

### 2. Resource-to-Configuration Mapping

**Decision:** Map Backend CRD fields to chat_shell AgentConfig with clear precedence rules.

**Rationale:**
- Each CRD contributes specific configuration aspects
- Ghost provides personality (system_prompt, temperature)
- Model provides LLM settings (provider, model_name, context_length)
- Shell provides tool restrictions (allowed_tools)
- Bot provides execution parameters (max_iterations)
- Clear precedence avoids configuration conflicts

**Mapping Rules:**

| Backend Resource | AgentConfig Field | Precedence |
|-----------------|-------------------|------------|
| Ghost.spec.system_prompt | system_prompt | Ghost only |
| Ghost.spec.temperature | temperature | Ghost > Model > default(0.7) |
| Ghost.spec.tools_enabled | tools | Ghost fallback if Shell empty |
| Model.spec.config.provider | provider | Model only |
| Model.spec.config.model_name | model | Model only |
| Model.spec.context_length | max_tokens | Ghost > Model > default(4096) |
| Shell.spec.allowed_tools | tools | Shell > Ghost > all tools |
| Bot.spec.max_iterations | max_iterations | Bot > default(10) |

**Implementation:**
```python
def _build_agent_config(
    self, ghost: GhostResponse, model: ModelResponse,
    shell: ShellResponse, bot: BotResponse
) -> AgentConfig:
    # Extract with precedence
    temperature = (
        ghost.spec.temperature
        or model.spec.default_temperature
        or 0.7
    )
    max_tokens = (
        ghost.spec.context_window
        or model.spec.context_length
        or 4096
    )
    tools = shell.spec.allowed_tools or ghost.spec.tools_enabled or []

    return AgentConfig(
        provider=model.spec.config.provider,
        model=model.spec.config.model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=ghost.spec.system_prompt,
        max_iterations=bot.spec.max_iterations or 10,
        tools=tools,
        checkpoint_enabled=True,
        checkpoint_type="memory",
        compress_context=True,
    )
```

**Location:** `backend/services/chat.py:320-363`

### 3. Dual Execution Patterns

**Decision:** Support both streaming (async generator) and non-streaming (sync response) execution.

**Rationale:**
- Streaming: Required for real-time chat UIs, shows progress as AI generates
- Non-streaming: Simpler for API clients, scripting, or when complete response needed
- Same underlying chat_shell.stream() used for both
- Non-streaming accumulates streaming events internally

**Implementation:**
```python
# Streaming - yields events as they occur
async def execute_chat(...) -> AsyncGenerator[Dict[str, Any], None]:
    agent = await self.create_chat_agent(bot_name, namespace)
    async for event in agent.stream(
        messages=messages,
        thread_id=thread_id,
        show_thinking=show_thinking,
    ):
        yield event

# Non-streaming - accumulates and returns complete response
async def execute_chat_sync(...) -> Dict[str, Any]:
    content_parts = []
    tool_calls = []
    async for event in self.execute_chat(...):
        if event["type"] == "content":
            content_parts.append(event["data"]["text"])
        elif event["type"] == "tool_call":
            tool_calls.append({...})
    return {
        "content": "".join(content_parts),
        "tool_calls": tool_calls,
    }
```

**Location:** `backend/services/chat.py:104-217`

### 4. Bot Configuration Validation

**Decision:** Implement explicit validation endpoint that checks all references before execution.

**Rationale:**
- Fail fast before attempting expensive LLM calls
- Provide clear error messages for missing resources
- Allow UI to show configuration status
- Check chat_shell availability

**Implementation:**
```python
async def validate_bot_configuration(
    self, bot_name: str, namespace: str = "default"
) -> Dict[str, Any]:
    errors = []
    warnings = []

    # Fetch Bot
    bot = await self.bot_service.get(bot_name, namespace)
    if not bot:
        raise BotConfigurationError(f"Bot '{bot_name}' not found")

    # Validate each reference
    try:
        ghost = await self._get_ghost(bot)
        if not ghost.spec.system_prompt:
            warnings.append("Ghost has empty system_prompt")
    except ValueError as e:
        errors.append(str(e))

    # ... similar for model and shell

    # Check chat_shell availability
    try:
        from chat_shell.agent import AgentConfig, ChatAgent
    except ImportError:
        errors.append("chat_shell module not available")

    return {
        "valid": len(errors) == 0,
        "bot": bot_name,
        "namespace": namespace,
        "errors": errors,
        "warnings": warnings,
        "ghost": ghost.metadata.name if ghost else None,
        "model": model.metadata.name if model else None,
        "shell": shell.metadata.name if shell else None,
    }
```

**Location:** `backend/services/chat.py:365-434`

### 5. Custom Exception Hierarchy

**Decision:** Create custom exceptions for different error types with clear hierarchy.

**Rationale:**
- Distinguish configuration errors from execution errors
- Allow API layer to return appropriate HTTP status codes
- Provide meaningful error messages to API consumers
- Enable specific error handling in callers

**Implementation:**
```python
class ChatServiceError(Exception):
    """Base exception for chat service errors."""
    pass

class BotConfigurationError(ChatServiceError):
    """Raised when bot configuration is invalid."""
    pass

class ChatExecutionError(ChatServiceError):
    """Raised when chat execution fails."""
    pass
```

**HTTP Mapping:**
- `BotConfigurationError` → 400 Bad Request
- `ChatExecutionError` → 500 Internal Server Error
- Bot not found → 404 Not Found

**Location:** `backend/services/chat.py:17-30`

### 6. Lazy chat_shell Import

**Decision:** Import chat_shell components at method call time, not module load time.

**Rationale:**
- Allows Backend API to start even if chat_shell has issues
- Easier testing with mocked dependencies
- Clear error messages when chat_shell unavailable
- Avoids circular import issues

**Implementation:**
```python
async def create_chat_agent(self, bot_name: str, namespace: str = "default"):
    # Import here to avoid circular imports and allow lazy loading
    try:
        from chat_shell.agent import AgentConfig, ChatAgent
    except ImportError as e:
        raise ChatServiceError(
            f"chat_shell module not available: {e}"
        ) from e
    # ... rest of implementation
```

**Location:** `backend/services/chat.py:48-60`

## Consequences

### Positive

- **Clean Architecture**: Service layer separates concerns between API and chat_shell
- **Flexible Execution**: Both streaming and non-streaming patterns available
- **Fail Fast**: Validation endpoint catches configuration issues before execution
- **Clear Errors**: Custom exceptions enable appropriate HTTP responses
- **Testable**: Easy to mock chat_shell for unit testing
- **Resource Mapping**: Clear precedence rules avoid configuration conflicts
- **Session Persistence**: Leverages chat_shell's checkpointing for conversation state

### Negative

- **Dependency on chat_shell**: Backend now requires chat_shell module to be available
- **Configuration Complexity**: Multiple resources must be properly configured
- **Agent Initialization Cost**: ChatAgent initialization may be expensive (can optimize with caching)
- **Error Translation**: Need to map chat_shell errors to Backend exceptions
- **Version Coupling**: Changes to chat_shell AgentConfig require updates to mapping logic

## Alternatives Considered

### Alternative 1: Direct API Integration

Call chat_shell directly from API endpoints without ChatService layer.

**Rejected:**
- Would duplicate resource fetching logic across endpoints
- Harder to test (would need to mock at API layer)
- No centralized error handling
- Difficult to reuse for WebSocket endpoints (Epic 14)

### Alternative 2: ChatAgent Caching

Cache ChatAgent instances per Bot to avoid re-initialization.

**Rejected (for initial implementation):**
- Adds complexity (cache invalidation, memory management)
- ChatAgent may hold resources that shouldn't be long-lived
- Premature optimization - can add later if needed
- Checkpointing already provides session persistence

### Alternative 3: Configuration File Mapping

Use configuration files instead of code for CRD-to-AgentConfig mapping.

**Rejected:**
- Adds indirection without clear benefit
- Code is more type-safe and testable
- Mapping logic is straightforward and unlikely to change frequently
- Would require additional configuration management

### Alternative 4: Only Streaming API

Provide only streaming execution, force clients to accumulate if needed.

**Rejected:**
- Non-streaming is simpler for many use cases
- Some clients can't handle streaming (simple scripts, webhooks)
- Easy to implement both from same underlying stream
- Different endpoints allow different timeout/connection handling

## Implementation Notes

### Dependencies

No new dependencies - uses existing chat_shell module:
```toml
[project.dependencies]
chat_shell = { path = "." }  # Same project
```

### Testing Strategy

```bash
# Run ChatService tests
pytest tests/unit/crd_backend/services/test_chat_service.py -v

# Run by epic marker
pytest tests/ -m epic_13 -v

# Total: 10 service tests
```

**Test Categories:**
- Service initialization (1 test)
- Configuration validation (3 tests)
- AgentConfig building (4 tests)
- Error handling (2 tests)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/{bot_name}` | Execute chat (non-streaming) |
| POST | `/api/v1/chat/{bot_name}/stream` | Execute chat (SSE streaming) |
| POST | `/api/v1/chat/{bot_name}/validate` | Validate Bot configuration |

### Configuration Precedence Summary

```
temperature: Ghost > Model > 0.7 (default)
max_tokens: Ghost.context_window > Model.context_length > 4096
tools: Shell.allowed_tools > Ghost.tools_enabled > [] (all tools)
max_iterations: Bot.max_iterations > 10 (default)
```

### Error Handling Flow

```
1. API endpoint receives request
2. ChatService.validate_bot_configuration() (optional)
3. ChatService.create_chat_agent()
   - Fetch Bot/Ghost/Model/Shell
   - Build AgentConfig
   - Initialize ChatAgent
4. ChatService.execute_chat() or execute_chat_sync()
   - Stream events from chat_shell
   - Handle errors, translate to ChatServiceError
5. API layer catches exceptions, returns HTTP response
   - BotConfigurationError -> 400
   - ChatExecutionError -> 500
   - Generic Exception -> 500
```

## References

- [Epic 13: Chat Shell Integration](/doc/epic/backend_phase_2_chat_execution.md)
- [ADR 012: Task Management API](/doc/adr/012-task-management-api.md)
- [chat_shell AgentConfig](/chat_shell/agent/config.py)
- [chat_shell ChatAgent](/chat_shell/agent/agent.py)
- [Backend Bot Schema](/backend/schemas/bot.py)
