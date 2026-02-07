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
- [ ] Integrate OpenAI models via langchain-openai
- [ ] Integrate Anthropic Claude via langchain-anthropic
- [ ] Integrate Google Gemini via langchain-google-genai
- [ ] Create unified model factory for provider abstraction
- [ ] Implement model configuration management (temperature, max_tokens, etc.)
- [ ] Support model-specific message format conversions
- [ ] Add fallback mechanisms for model failures

---

## Epic 3: Tools System
**Goal**: Build extensible tool system with multiple tool types

### Built-in Tools
- [ ] Implement WebSearchTool for internet search
- [ ] Implement KnowledgeBaseTool for RAG knowledge retrieval
- [ ] Implement DataTableTool for data table queries
- [ ] Implement FileReaderTool for file parsing (PDF, Word, Excel, Markdown)
- [ ] Implement LoadSkillTool for dynamic skill loading
- [ ] Implement CreateSubscriptionTool for subscription tasks
- [ ] Implement SilentExitTool for graceful subscription exits
- [ ] Implement EvaluationTool for assessment capabilities

### Tool Infrastructure
- [ ] Create ToolRegistry for tool management
- [ ] Implement PromptModifierTool protocol interface
- [ ] Support dynamic tool loading and unloading
- [ ] Add tool parameter validation
- [ ] Implement tool execution error handling

### MCP Protocol Integration
- [ ] Integrate Model Context Protocol for dynamic tool loading
- [ ] Support remote tool server connections
- [ ] Implement MCP tool adapter
- [ ] Add MCP tool discovery and registration

### Skills System
- [ ] Implement skill factory for custom tools
- [ ] Support dynamic skill loading from backend
- [ ] Add skill preload mechanism
- [ ] Implement skill lifecycle management

---

## Epic 4: Three Deployment Modes
**Goal**: Support HTTP, Package, and CLI deployment modes

### HTTP Mode
- [ ] Create FastAPI application structure
- [ ] Implement POST /v1/response endpoint for chat sessions
- [ ] Implement GET /v1/response/{subtask_id} for session recovery
- [ ] Implement DELETE /v1/response/{subtask_id} for session cancellation
- [ ] Add health check endpoint
- [ ] Configure Uvicorn server with proper settings
- [ ] Implement RemoteStorage integration with backend APIs

### Package Mode
- [ ] Design ChatInterface abstract interface
- [ ] Implement direct Python function calls
- [ ] Support in-process message passing without storage layer
- [ ] Create package import entry points
- [ ] Add usage examples and documentation

### CLI Mode
- [ ] Implement `chat-shell serve` command to start HTTP server
- [ ] Implement `chat-shell chat` command for interactive sessions
- [ ] Implement `chat-shell query` command for single queries
- [ ] Implement `chat-shell history` command for history viewing
- [ ] Implement `chat-shell config` command for configuration management
- [ ] Add SQLite local storage (~/.chat_shell/history.db)
- [ ] Create rich CLI interface with proper formatting

---

## Epic 5: Streaming Response System
**Goal**: Implement real-time streaming responses via SSE

### User Stories
- [ ] Implement SSEEmitter for Server-Sent Events
- [ ] Create StreamingCore for stream coordination
- [ ] Implement StreamingState for session state management
- [ ] Support token-level streaming (chunk events)
- [ ] Support tool execution event streaming (ToolStart/ToolResult)
- [ ] Support thinking process event streaming
- [ ] Implement session recovery with offset continuation
- [ ] Add support for canceling running sessions
- [ ] Handle client disconnection gracefully

---

## Epic 6: Storage Layer
**Goal**: Build flexible storage system with multiple backends

### User Stories
- [ ] Design StorageProvider abstract interface
- [ ] Implement MemoryStorage for testing
- [ ] Implement SQLiteStorage for CLI mode
- [ ] Implement RemoteStorage for HTTP mode with backend integration
- [ ] Create SessionManager for session lifecycle management
- [ ] Support message persistence and retrieval
- [ ] Implement history truncation and limits
- [ ] Add conversation metadata management

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
