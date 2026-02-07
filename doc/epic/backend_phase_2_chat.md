# Backend MVP - Epic Phase 2: Chat Execution System

## Overview

Build the chat execution system that integrates the completed chat_shell module with the Backend CRD system. This phase enables users to create Tasks and interact with AI agents through WebSocket connections, completing the end-to-end MVP functionality.

---

## Epic 1: Task Resource Management

**Goal**: Implement CRD endpoints for Task resources

### User Stories

- [ ] Implement POST /api/v1/kinds/tasks - Create Task referencing a Team and optional Workspace
- [ ] Implement GET /api/v1/kinds/tasks - List all Tasks with filtering by status
- [ ] Implement GET /api/v1/kinds/tasks/{id} - Get specific Task details
- [ ] Implement PUT /api/v1/kinds/tasks/{id} - Update Task (title, description)
- [ ] Implement DELETE /api/v1/kinds/tasks/{id} - Delete Task
- [ ] Create Task model with fields: id, title, description, team_id, workspace_id, status, created_by, created_at, updated_at
- [ ] Define Task status enum: pending, running, completed, failed, cancelled

### Tests

- [ ] Unit tests for Task model validation (8 tests)
- [ ] Unit tests for Task CRUD endpoints (15 tests)
- [ ] Integration tests for Task status transitions (6 tests)
- [ ] **Total: 29 tests passing**

---

## Epic 2: Chat Service Integration

**Goal**: Integrate chat_shell as a package for chat execution

### User Stories

- [ ] Create ChatService that imports chat_shell.main.process_messages
- [ ] Implement async wrapper for chat_shell execution
- [ ] Map Bot configuration to chat_shell AgentConfig
- [ ] Handle model config conversion (provider, temperature, max_tokens)
- [ ] Map Ghost system_prompt to chat_shell
- [ ] Implement error handling for chat_shell failures
- [ ] Create chat session state tracking in database

### Tests

- [ ] Unit tests for ChatService (12 tests)
- [ ] Unit tests for configuration mapping (8 tests)
- [ ] Integration tests for chat_shell integration (6 tests)
- [ ] **Total: 26 tests passing**

---

## Epic 3: WebSocket Chat Endpoint

**Goal**: Implement WebSocket endpoint for real-time chat

### User Stories

- [ ] Implement WS /api/v1/tasks/{id}/chat - WebSocket endpoint for chat
- [ ] Authenticate WebSocket connections with JWT
- [ ] Handle incoming user messages
- [ ] Stream chat_shell responses via WebSocket
- [ ] Support message history loading on connection
- [ ] Handle client disconnect gracefully
- [ ] Implement rate limiting per connection
- [ ] Broadcast typing indicators (optional for MVP)

### Tests

- [ ] Unit tests for WebSocket connection handling (8 tests)
- [ ] Unit tests for message streaming (10 tests)
- [ ] Integration tests for WebSocket chat flow (6 tests)
- [ ] **Total: 24 tests passing**

---

## Epic 4: Message Persistence

**Goal**: Store chat messages for history and recovery

### User Stories

- [ ] Create Message model for task chat history
- [ ] Store user messages on receive
- [ ] Store AI responses from chat_shell
- [ ] Support message pagination for history loading
- [ ] Implement message metadata (tokens used, latency)
- [ ] Create Message model fields: id, task_id, role (user/assistant), content, metadata, created_at

### Tests

- [ ] Unit tests for Message model (6 tests)
- [ ] Unit tests for message persistence (10 tests)
- [ ] Integration tests for message history API (6 tests)
- [ ] **Total: 22 tests passing**

---

## Epic 5: Task Execution Lifecycle

**Goal**: Manage task execution state and lifecycle

### User Stories

- [ ] Implement task status transitions (pending → running → completed/failed)
- [ ] Handle concurrent task execution limits
- [ ] Implement task timeout handling
- [ ] Support task cancellation during execution
- [ ] Create task execution logs
- [ ] Handle chat_shell errors and update task status

### Tests

- [ ] Unit tests for task lifecycle management (10 tests)
- [ ] Unit tests for task cancellation (6 tests)
- [ ] Integration tests for concurrent execution (4 tests)
- [ ] **Total: 20 tests passing**

---

## Epic 6: Basic Frontend API Support

**Goal**: Provide APIs needed for basic frontend

### User Stories

- [ ] Implement GET /api/v1/tasks/{id}/messages - Get chat history with pagination
- [ ] Implement POST /api/v1/tasks/{id}/cancel - Cancel running task
- [ ] Implement CORS for frontend integration
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Add health check endpoint for monitoring

### Tests

- [ ] Unit tests for message history API (6 tests)
- [ ] Unit tests for task cancellation API (4 tests)
- [ ] Integration tests for frontend API flow (6 tests)
- [ ] **Total: 16 tests passing**

---

## Success Criteria for Phase 2

- Users can create a Task referencing a Team
- WebSocket chat endpoint delivers real-time AI responses
- chat_shell is successfully integrated as a package
- Messages are persisted and can be retrieved
- Task lifecycle is properly managed (status transitions)
- Users can cancel running tasks
- Frontend can display chat history
- End-to-end flow works: Create Ghost → Model → Shell → Bot → Team → Task → Chat
