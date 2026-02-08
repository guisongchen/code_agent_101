# ADR 001: Core Agent System Architecture

## Status

Accepted

## Context

The Chat Shell 101 project needed a robust core agent system built on LangGraph that provides:
- Automatic context management for long conversations
- Dynamic prompt modification capabilities
- Session persistence and recovery
- Protection against infinite tool execution loops
- Clean configuration and builder patterns

## Decision

We implemented six core components to address these requirements:

### 1. AgentConfig Data Class

**Decision:** Use a `@dataclass` with validation logic in `__post_init__` rather than Pydantic BaseModel.

**Rationale:**
- Dataclasses are lighter weight for configuration objects
- Custom validation in `__post_init__` provides fine-grained control over error messages
- Easier to use with `frozen=True` if immutability is desired later
- Better compatibility with CLI argument parsing

**Location:** `chat_shell_101/agent/config.py`

### 2. MessageCompressor with Multiple Strategies

**Decision:** Implement three compression strategies (SUMMARIZE, TRUNCATE, WINDOW) with a pluggable strategy pattern using rule-based algorithms.

**Rationale:**
- **SUMMARIZE**: Creates heuristic summary of older messages by extracting key Q&A pairs, preserves semantic meaning without LLM calls
- **TRUNCATE**: Fastest option, simply drops older messages, deterministic behavior
- **WINDOW**: Balanced approach, keeps recent messages verbatim, summarizes older ones using heuristics
- Strategy enum allows runtime selection based on use case
- Token counting uses tiktoken with character-based fallback for unknown models

**Important Note on Compression Approach:**
The current implementation uses **rule-based compression** rather than LLM-based semantic compression:
- Summarization extracts the last 3 user queries and truncates them to 100 characters each
- No LLM calls are made during compression (avoids latency and cost)
- Trade-off: faster execution but less sophisticated summarization
- Future enhancement: Optional LLM-based semantic compression for higher quality summaries

**Key Design Points:**
- Compression threshold (0.0-1.0) determines when to trigger compression
- `keep_recent_messages` preserves N most recent messages uncompressed
- System messages are always preserved
- Rule-based approach ensures deterministic, fast compression without additional LLM latency

**Location:** `chat_shell_101/agent/compressor.py`

### 3. PromptModifierTool Protocol

**Decision:** Use Python's `typing.Protocol` with `@runtime_checkable` for dynamic prompt injection.

**Rationale:**
- Protocols enable structural subtyping (duck typing) without inheritance
- `@runtime_checkable` allows `isinstance()` checks at runtime
- Tools can optionally implement this protocol to inject context into system prompts
- Decouples tool implementation from agent prompt construction

**Example Use Case:**
```python
class ContextTool(BaseTool, PromptModifierTool):
    def modify_prompt(self, current_prompt: str, state: AgentState) -> str:
        return f"{current_prompt}\n\nContext: {self.get_context()}"
```

**Location:** `chat_shell_101/tools/base.py`

### 4. LangGraph Checkpointing

**Decision:** Support both in-memory (MemorySaver) and persistent (SqliteSaver) checkpointing.

**Rationale:**
- Memory checkpointing is default for development and ephemeral sessions
- SQLite checkpointing enables session recovery across restarts
- `langgraph-checkpoint-sqlite` package provides AsyncSqliteSaver for async compatibility
- `thread_id` in config identifies sessions for recovery

**Integration:**
```python
checkpointer = AsyncSqliteSaver(conn) if config.checkpoint_type == "sqlite" else MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**Location:** `chat_shell_101/agent/builder.py`

### 5. Tool Iteration Limits

**Decision:** Implement iteration counting in AgentState with configurable max_iterations.

**Rationale:**
- Prevents infinite loops from self-calling tools or cyclic tool chains
- Default limit of 10 balances flexibility with safety
- Error is raised as ToolIterationLimitError for specific handling
- Count tracked in state, checked in `should_continue` edge function

**State Management:**
```python
class AgentState(BaseModel):
    messages: List[BaseMessage]
    iteration_count: int = 0
```

**Location:** `chat_shell_101/agent/agent.py`

### 6. LangGraphAgentBuilder (Fluent API)

**Decision:** Use builder pattern with method chaining for agent configuration.

**Rationale:**
- Fluent API reads like natural language: `builder.with_model("gpt-4").with_tools([...]).build()`
- Encapsulates complex graph construction from user
- Each `with_*` method returns `self` for chaining
- Separates configuration from construction from execution

**Alternative Considered:**
- Direct `ChatAgent` instantiation - rejected because graph compilation requires multiple steps
- Factory function - rejected because builder provides better discoverability via IDE autocomplete

**Location:** `chat_shell_101/agent/builder.py`

### 7. Test Organization

**Decision:** Mirror source structure in tests with pytest markers for epic filtering.

**Rationale:**
- `tests/agent/test_*.py` mirrors `chat_shell_101/agent/*.py`
- Easier to locate tests for specific modules
- pytest markers (`epic_1`, `epic_2`, etc.) allow running tests by epic: `pytest -m epic_1`
- `pytestmark = [pytest.mark.unit, pytest.mark.epic_1]` in each test file

**Structure:**
```
tests/
├── agent/
│   ├── test_agent.py      # ChatAgent, AgentState
│   ├── test_builder.py    # LangGraphAgentBuilder
│   ├── test_config.py     # AgentConfig
│   └── test_compressor.py # MessageCompressor
└── tools/
    └── test_base.py       # PromptModifierTool
```

## Consequences

### Positive

- Agent configuration is type-safe and validated
- Context compression prevents token limit errors automatically
- Session persistence enables long-running conversations
- Tool iteration limits prevent runaway execution
- Builder pattern makes agent creation intuitive
- Protocol-based tool extensions are decoupled and testable

### Negative

- AsyncSqliteSaver requires optional dependency (`langgraph-checkpoint-sqlite`)
- Token counting is approximate for non-OpenAI models (uses gpt-4 tokenizer as fallback)
- Compression strategies may lose information (inherent trade-off)
- Rule-based compression is less sophisticated than LLM-based semantic compression (quality vs speed trade-off)

## Implementation Notes

### Dependencies Added

```toml
dependencies = [
    "tiktoken>=0.5.0",  # For token counting
    "langgraph-checkpoint-sqlite>=3.0.3",  # For persistent checkpointing
]
```

### Backward Compatibility

Epic 1 removed the singleton `get_agent()` pattern from the original codebase. The CLI now creates agents directly:

```python
# Old (removed)
agent = get_agent(config)

# New
agent_config = AgentConfig(...)
agent = LangGraphAgentBuilder().with_config(agent_config).build()
```

## References

- [LangGraph Checkpointing Documentation](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Python Protocol Documentation](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Builder Pattern](https://refactoring.guru/design-patterns/builder)
