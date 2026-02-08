# ADR 003: Tools System Architecture

## Status

Accepted

## Context

Epic 1 and 2 provided a solid agent foundation and multi-model support, but the system needed a comprehensive tool ecosystem to handle real-world tasks. The requirements included:
- File parsing capabilities (PDF, Word, Excel, etc.)
- External data access (web search, knowledge bases)
- Data analysis tools
- Task management (subscriptions)
- Dynamic extensibility (skills, MCP protocol)
- Proper error handling and lifecycle management

## Decision

We implemented a multi-layered tools architecture consisting of built-in tools, enhanced registry infrastructure, MCP protocol integration, and a skills system for extensibility.

### 1. Built-in Tools Architecture

**Decision:** Implement 8 built-in tools covering common use cases, each with Pydantic input/output schemas.

**Rationale:**
- Pydantic schemas provide validation, serialization, and OpenAPI-compatible documentation
- Each tool is self-contained with clear input/output contracts
- Async execution support for I/O-bound operations
- Consistent error handling via ToolOutput with error field

**Tool Categories:**

| Category | Tools | Purpose |
|----------|-------|---------|
| Information Retrieval | WebSearchTool, KnowledgeBaseTool | Access external information |
| File Processing | FileReaderTool | Parse multiple document formats |
| Data Analysis | DataTableTool | Query and analyze structured data |
| Task Management | CreateSubscriptionTool, SilentExitTool | Background task handling |
| Extension | LoadSkillTool, EvaluationTool | System extensibility |

**Implementation Pattern:**
```python
class ToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

class ToolOutput(BaseModel):
    result: Any
    error: str = ""

class MyTool(BaseTool):
    name = "tool_name"
    description = "Tool description"
    input_schema = ToolInput

    async def execute(self, input_data: ToolInput) -> ToolOutput:
        try:
            result = await self._do_work(input_data)
            return ToolOutput(result=result)
        except Exception as e:
            return ToolOutput(result="", error=str(e))
```

**Key Design Points:**
- All tools use Pydantic v2 for validation
- FileReaderTool uses optional dependencies (chardet, PyPDF2, python-docx, pandas)
- WebSearchTool has pluggable search providers (default: DuckDuckGo)
- DataTableTool leverages pandas for powerful query capabilities

**Location:** `chat_shell_101/tools/{tool_name}.py`

### 2. Enhanced Tool Registry

**Decision:** Extend the basic registry with lifecycle management, dynamic loading, and hooks.

**Rationale:**
- Original registry only supported static registration
- Need for runtime tool loading/unloading for skills and MCP
- Lifecycle hooks enable pre/post processing (logging, validation, etc.)
- Dynamic loading from modules enables plugin architecture

**Registry Features:**
```python
class ToolRegistry:
    # Basic operations
    register(tool, allow_replace=False)
    unregister(name)
    get_tool(name)
    get_all_tools()

    # Dynamic loading
    load_from_module(module_path, class_name=None)
    load_from_directory(directory, pattern="*.py")

    # Lifecycle hooks
    add_pre_load_hook(callable)
    add_post_load_hook(callable)
    add_pre_unload_hook(callable)
```

**Singleton Pattern:**
- Global registry via `get_tool_registry()` / `set_tool_registry()`
- Backward compatible with existing `tool_registry` global

**Location:** `chat_shell_101/tools/enhanced_registry.py`

### 3. Tool Exception Hierarchy

**Decision:** Create comprehensive exception hierarchy with tool context.

**Rationale:**
- Different error types need different handling
- Tool name context helps debugging
- Separate exceptions for user errors vs system errors
- MCP and Skills need their own exception types

**Exception Hierarchy:**
```
ToolError (base)
├── ToolNotFoundError          # Requested tool doesn't exist
├── ToolValidationError        # Input validation failed
│   └── field: str             # Which field failed
├── ToolExecutionError         # Runtime execution failure
│   └── cause: Exception       # Original exception
├── ToolRegistrationError      # Registration-time failure
├── MCPToolError              # MCP-specific errors
│   └── MCPConnectionError    # Server connection failed
│       └── server_url: str
└── SkillError (also in skills)
    ├── SkillLoadError
    ├── SkillNotFoundError
    └── SkillAlreadyLoadedError
```

**Usage:**
```python
try:
    tool = registry.get_tool("unknown")
except ToolNotFoundError as e:
    # e.tool_name == "unknown"
    logger.error(f"Tool {e.tool_name} not found")
```

**Location:** `chat_shell_101/tools/exceptions.py`

### 4. MCP Protocol Integration

**Decision:** Implement MCP (Model Context Protocol) client for remote tool access.

**Rationale:**
- MCP is emerging standard for tool interoperability
- Allows connecting to external tool servers
- Enables dynamic tool discovery from remote sources
- Adapter pattern makes remote tools look like local tools

**Architecture:**
```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐
│   MCPClient     │ ◄────────────────► │   MCP Server    │
│                 │    MCP Protocol    │                 │
│ - discover()    │                    │ - Tool Registry │
│ - execute()     │                    │ - Execution     │
└────────┬────────┘                    └─────────────────┘
         │
         │ wraps
         ▼
┌─────────────────┐
│ MCPAdapterTool  │  ←  Implements BaseTool interface
│                 │     (Transparent to agent)
│ - execute()     │
└─────────────────┘
```

**Key Components:**
- **MCPClient**: Handles HTTP communication with MCP servers
- **MCPManager**: Manages multiple MCP server connections
- **MCPAdapterTool**: Wraps remote tools as local BaseTool instances
- **Dynamic Input Schema**: Creates Pydantic models from MCP parameter specs

**Configuration:**
```python
config = MCPServerConfig(
    url="https://tools.example.com/mcp",
    api_key="secret",
    timeout=30.0
)
```

**Location:** `chat_shell_101/tools/mcp.py`

### 5. Skills System

**Decision:** Implement skills as pluggable capability modules with lifecycle management.

**Rationale:**
- Tools are single operations, skills are capability bundles
- Skills can provide multiple tools, prompts, and prompt modifications
- Need lifecycle management (load → initialize → activate → deactivate → unload)
- Skills can modify agent behavior (system prompts)

**Skill Architecture:**
```
BaseSkill (abstract)
├── config: SkillConfig         # Name, version, dependencies
├── initialize(context)         # Setup with execution context
├── shutdown()                  # Cleanup
├── get_tools() → List[Tool]    # Tools provided by skill
├── get_prompts() → Dict        # Custom prompt templates
└── modify_system_prompt()      # Inject skill context into prompts

SkillManager
├── load_skill()                # Load and initialize
├── unload_skill()              # Shutdown and remove
├── activate_skill()            # Make tools available
├── deactivate_skill()          # Hide tools but keep loaded
└── get_active_tools()          # Aggregate from active skills
```

**Skill vs Tool Relationship:**
| Aspect | Tool | Skill |
|--------|------|-------|
| Granularity | Single operation | Capability bundle |
| Lifecycle | Register/Unregister | Load/Initialize/Activate |
| Can modify prompts? | Yes (via PromptModifierTool) | Yes |
| Provides multiple capabilities? | No | Yes |
| Has state? | No | Yes (can maintain state) |

**Example Skill:**
```python
class DataAnalysisSkill(BaseSkill):
    def __init__(self):
        self.config = SkillConfig(
            name="data_analysis",
            version="1.0.0",
            description="Data analysis capabilities",
            dependencies=["pandas", "numpy"]
        )

    async def initialize(self, context: SkillContext):
        # Setup resources
        pass

    def get_tools(self):
        return [DataTableTool(), ChartTool()]

    def modify_system_prompt(self, prompt):
        return prompt + "\n\nYou have data analysis capabilities."
```

**Location:** `chat_shell_101/skills/{base,manager,exceptions}.py`

### 6. File Format Support Strategy

**Decision:** Support multiple file formats with optional dependencies.

**Rationale:**
- Not all users need all file formats
- Keep core lightweight, install extras as needed
- Graceful degradation when dependencies missing
- Clear error messages indicating required packages

**Supported Formats:**
| Format | Extension | Required Package |
|--------|-----------|------------------|
| Text | .txt, .md, .py, etc. | (built-in) |
| JSON | .json | (built-in) |
| CSV | .csv | pandas |
| Excel | .xlsx | pandas, openpyxl |
| PDF | .pdf | PyPDF2 |
| Word | .docx | python-docx |

**Dependency Management:**
```python
try:
    import PyPDF2
except ImportError:
    return ToolOutput(
        result="",
        error="PyPDF2 is required for PDF reading. Install with: pip install PyPDF2"
    )
```

**Location:** `chat_shell_101/tools/file_reader.py`

## Consequences

### Positive

- **Comprehensive tool coverage**: 8 built-in tools cover most common use cases
- **Extensibility**: Skills and MCP enable unlimited expansion
- **Type safety**: Pydantic schemas ensure validated inputs/outputs
- **Error handling**: Structured exceptions with context aid debugging
- **Async support**: All tools support async execution for I/O operations
- **Plugin architecture**: Dynamic loading enables runtime extension
- **Interoperability**: MCP support connects to external tool ecosystems

### Negative

- **Complexity**: Multiple layers (tools, skills, MCP) increase cognitive load
- **Dependency management**: Optional dependencies require documentation
- **Testing surface**: Many tools with external dependencies need mocking
- **Performance**: File parsing and web searches can be slow
- **Security**: File reader and web search need sandboxing in production

## Alternatives Considered

### Alternative 1: LangChain Tools Only

Use LangChain's built-in tool ecosystem exclusively.

**Rejected:**
- Less control over tool behavior
- No custom exception hierarchy
- Limited support for our specific use cases
- No skills/MCP concept

### Alternative 2: Function-based Tools

Use simple functions instead of class-based tools.

**Rejected:**
- Harder to manage state (e.g., HTTP clients)
- Less consistent interface
- Harder to implement lifecycle methods
- No natural place for helper methods

### Alternative 3: No Skills Layer

Only have tools, no skills abstraction.

**Rejected:**
- Skills provide useful bundling of related capabilities
- Skills can modify prompts, tools alone cannot (only PromptModifierTool)
- Skills have lifecycle (init/shutdown), tools are stateless
- Skills enable/disable as a group, useful for feature flags

## Implementation Notes

### Dependencies

```toml
# Core (always required)
pydantic>=2.0.0
httpx>=0.28.1

# Optional for file reading
chardet          # Encoding detection
PyPDF2          # PDF parsing
python-docx     # Word documents
pandas          # Excel, CSV analysis

# Optional for web search
# (uses standard library + httpx)
```

### Testing Strategy

- Unit tests for each tool with mocked external dependencies
- File-based tests use temporary files
- Network tests are optional (skip if no connection)
- Skills tests use mock skill implementations

### Migration Path

Existing tools continue to work:
```python
# Old style (still works)
from chat_shell_101.tools import CalculatorTool

# New style (additional capabilities)
from chat_shell_101.tools import WebSearchTool, FileReaderTool
from chat_shell_101.skills import SkillManager
```

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [Python Abstract Base Classes](https://docs.python.org/3/library/abc.html)
