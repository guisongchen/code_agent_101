# Chat Shell - Epic Phase 0 (MVP)

## Overview
This phase focuses on building the foundational components required for a working AI chat agent service. The goal is to deliver a minimal viable product with core functionality.

---

## Epic 1: Core Agent System
**Goal**: Build the foundational AI agent system with LangGraph integration

### User Stories
- [x] Implement ChatAgent with ReAct (Reasoning + Acting) workflow
- [x] Create AgentConfig data class for flexible configuration
- [x] Develop LangGraphAgentBuilder using `create_react_agent`
- [x] Implement MessageCompressor for automatic context management
- [x] Support tool iteration limits (default 10 cycles)
- [x] Implement dynamic prompt injection via PromptModifierTool
- [x] Add state checkpointing for session recovery

### Tests
- [x] Unit tests for AgentConfig validation (10 tests)
- [x] Unit tests for MessageCompressor with all 3 strategies (29 tests)
- [x] Unit tests for LangGraphAgentBuilder including SQLite checkpoint (12 tests)
- [x] Unit tests for ChatAgent (15 tests)
- [x] Unit tests for PromptModifierTool protocol (4 tests)
- [x] **Total: 70 tests passing**

---

## Epic 2: Multi-Model LLM Integration
**Goal**: Support multiple LLM providers with unified interface

### User Stories
- [x] Integrate OpenAI models via langchain-openai
- [x] Integrate Anthropic Claude via langchain-anthropic
- [x] Integrate Google Gemini via langchain-google-genai
- [x] Create unified model factory for provider abstraction
- [x] Implement model configuration management (temperature, max_tokens, etc.)
- [x] Support model-specific message format conversions
- [x] Add fallback mechanisms for model failures

### Tests
- [x] Unit tests for ModelConfig and ProviderConfig (21 tests)
- [x] Unit tests for ModelFactory including provider detection (21 tests)
- [x] Unit tests for MessageConverter with all 3 formats (18 tests)
- [x] Unit tests for model exceptions (6 tests)
- [x] **Total: 66 tests passing**

---

## Epic 3: Tools System
**Goal**: Build extensible tool system with multiple tool types

### Built-in Tools
- [x] Implement WebSearchTool for internet search
- [x] Implement KnowledgeBaseTool for RAG knowledge retrieval
- [x] Implement DataTableTool for data table queries
- [x] Implement FileReaderTool for file parsing (PDF, Word, Excel, Markdown)
- [x] Implement LoadSkillTool for dynamic skill loading
- [x] Implement CreateSubscriptionTool for subscription tasks
- [x] Implement SilentExitTool for graceful subscription exits
- [x] Implement EvaluationTool for assessment capabilities

### Tool Infrastructure
- [x] Create ToolRegistry for tool management
- [x] Implement PromptModifierTool protocol interface
- [x] Support dynamic tool loading and unloading
- [x] Add tool parameter validation
- [x] Implement tool execution error handling

### MCP Protocol Integration
- [x] Integrate Model Context Protocol for dynamic tool loading
- [x] Support remote tool server connections
- [x] Implement MCP tool adapter
- [x] Add MCP tool discovery and registration

### Skills System
- [x] Implement skill factory for custom tools
- [x] Support dynamic skill loading from backend
- [x] Add skill preload mechanism
- [x] Implement skill lifecycle management

### Tests
- [x] Unit tests for tool exceptions (6 tests)
- [x] Unit tests for WebSearchTool (4 tests)
- [x] Unit tests for FileReaderTool (8 tests)
- [x] Unit tests for skills base classes (8 tests)
- [x] Unit tests for skills exceptions (6 tests)
- [x] Unit tests for SkillManager (11 tests)
- [x] **Total: 43 new tests passing**

---

## Epic 4: Three Deployment Modes
**Goal**: Support HTTP, Package, and CLI deployment modes

### HTTP Mode
- [x] Create FastAPI application structure
- [x] Implement POST /v1/response endpoint for chat sessions
- [x] Implement GET /v1/response/{subtask_id} for session recovery
- [x] Implement DELETE /v1/response/{subtask_id} for session cancellation
- [x] Add health check endpoint
- [x] Configure Uvicorn server with proper settings
- [x] Implement RemoteStorage integration with backend APIs

### Package Mode
- [x] Design ChatInterface abstract interface
- [x] Implement direct Python function calls
- [x] Support in-process message passing without storage layer
- [x] Create package import entry points
- [x] Add usage examples and documentation

### CLI Mode
- [x] Implement `chat-shell serve` command to start HTTP server
- [x] Implement `chat-shell chat` command for interactive sessions
- [x] Implement `chat-shell query` command for single queries
- [x] Implement `chat-shell history` command for history viewing
- [x] Implement `chat-shell config` command for configuration management
- [x] Add SQLite local storage (~/.chat_shell/history.db)
- [x] Create rich CLI interface with proper formatting

### Tests
- [x] Unit tests for SQLiteStorage (11 tests)
- [x] Unit tests for Package Mode interface (17 tests)
- [x] Unit tests for API schemas (13 tests)
- [x] **Total: 41 new tests passing**

---

## Epic 5: Streaming Response System
**Goal**: Implement real-time streaming responses via SSE

### User Stories
- [x] Implement SSEEmitter for Server-Sent Events
- [x] Create StreamingCore for stream coordination
- [x] Implement StreamingState for session state management
- [x] Support token-level streaming (chunk events)
- [x] Support tool execution event streaming (ToolStart/ToolResult)
- [x] Support thinking process event streaming
- [x] Implement session recovery with offset continuation
- [x] Add support for canceling running sessions
- [x] Handle client disconnection gracefully

### Tests
- [x] Unit tests for StreamConfig (2 tests)
- [x] Unit tests for StreamingCore (16 tests)
- [x] Integration tests for streaming lifecycle (3 tests)
- [x] Unit tests for global streaming core (3 tests)
- [x] **Total: 23 tests passing**

---

## Epic 6: Storage Layer
**Goal**: Build flexible storage system with multiple backends

### User Stories
- [x] Design StorageProvider abstract interface
- [x] Implement MemoryStorage for testing
- [x] Implement SQLiteStorage for CLI mode
- [x] Implement RemoteStorage for HTTP mode with backend integration
- [x] Create SessionManager for session lifecycle management
- [x] Support message persistence and retrieval
- [x] Implement history truncation and limits
- [x] Add conversation metadata management

---

## Success Criteria for Phase 0

- Core agent system operational with LangGraph integration
- At least 2 LLM providers working (OpenAI + one other)
- Basic tools functional (WebSearch, FileReader minimum)
- HTTP mode fully operational with FastAPI
- CLI mode working with local SQLite storage
- Streaming responses functional via SSE
- Basic storage layer with Memory, SQLite, and Remote backends
- Can handle basic chat sessions end-to-end
