# Wegent Backend - Epic Phase 2 (Chat Execution Engine)

## Overview
This phase implements the chat execution engine that integrates the completed chat_shell module with the Backend API. This includes Task management, WebSocket-based real-time chat communication, and the service layer that orchestrates AI agent conversations.

---

## Epic 12: Task Management API
**Goal**: Implement Task CRUD operations and lifecycle management

### User Stories
- [ ] Create `POST /api/v1/tasks` endpoint for Task creation
- [ ] Create `GET /api/v1/tasks` endpoint for listing Tasks
- [ ] Create `GET /api/v1/tasks/{id}` endpoint for Task retrieval
- [ ] Create `DELETE /api/v1/tasks/{id}` endpoint for Task deletion
- [ ] Implement Task status tracking (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- [ ] Add Team reference validation during Task creation
- [ ] Implement Task history persistence
- [ ] Create Task query filters (by status, by team, by date range)

### Tests
- [ ] Task API endpoint tests (12 tests)
- [ ] Task status transition tests (8 tests)
- [ ] Task validation tests (6 tests)
- [ ] **Total: 26 tests passing**

---

## Epic 13: Chat Shell Integration
**Goal**: Integrate chat_shell module as a package for AI conversation execution

### User Stories
- [ ] Import chat_shell as a package dependency
- [ ] Create `ChatService` to orchestrate chat execution
- [ ] Implement `execute_chat` method that calls chat_shell.process_messages
- [ ] Map Bot configuration to chat_shell AgentConfig
- [ ] Extract model configuration from Model CRD spec
- [ ] Extract system prompt from Ghost CRD spec
- [ ] Handle chat_shell initialization and cleanup
- [ ] Implement error handling for chat execution failures

### Tests
- [ ] Chat service unit tests (10 tests)
- [ ] chat_shell integration tests (8 tests)
- [ ] Error handling tests (6 tests)
- [ ] **Total: 24 tests passing**

---

## Epic 14: WebSocket Chat Endpoint
**Goal**: Implement WebSocket endpoint for real-time bidirectional chat communication

### User Stories
- [ ] Create `WS /api/v1/tasks/{id}/chat` WebSocket endpoint
- [ ] Implement Socket.IO namespace `/chat` for chat events
- [ ] Handle `chat:send` event from client to server
- [ ] Emit `chat:start` event when AI begins generating response
- [ ] Emit `chat:chunk` events for streaming content
- [ ] Emit `chat:done` event when AI response completes
- [ ] Emit `chat:error` event for error handling
- [ ] Handle `chat:cancel` event to stop ongoing generation
- [ ] Implement `task:join` and `task:leave` room management
- [ ] Add Redis adapter for multi-worker support

### Tests
- [ ] WebSocket connection tests (8 tests)
- [ ] Event handling tests (12 tests)
- [ ] Room management tests (6 tests)
- [ ] **Total: 26 tests passing**

---

## Epic 15: Message History Management
**Goal**: Persist and retrieve chat message history for tasks

### User Stories
- [ ] Create message history schema and storage
- [ ] Implement `history:sync` event for client synchronization
- [ ] Store user messages in database
- [ ] Store AI responses in database
- [ ] Retrieve message history for a Task
- [ ] Implement pagination for large message histories
- [ ] Add message metadata (timestamp, tokens used)
- [ ] Handle message history for resumed sessions

### Tests
- [ ] Message storage tests (8 tests)
- [ ] History retrieval tests (6 tests)
- [ ] Pagination tests (4 tests)
- [ ] **Total: 18 tests passing**

---

## Epic 16: Chat Session State Management
**Goal**: Manage chat session lifecycle and state persistence

### User Stories
- [ ] Implement session creation on first chat connection
- [ ] Store session state in Redis cache
- [ ] Handle session recovery on reconnect
- [ ] Implement session timeout handling (2-hour expiration)
- [ ] Add concurrent session limits per user
- [ ] Implement graceful session cleanup
- [ ] Handle session persistence across server restarts
- [ ] Add session metrics and monitoring

### Tests
- [ ] Session lifecycle tests (10 tests)
- [ ] Session recovery tests (6 tests)
- [ ] Timeout handling tests (4 tests)
- [ ] **Total: 20 tests passing**

---

## Epic 17: Real-time Event Broadcasting
**Goal**: Implement room-based message routing for multi-user scenarios

### User Stories
- [ ] Create user rooms (`user:{user_id}`) for personal notifications
- [ ] Create task rooms (`task:{task_id}`) for chat streaming
- [ ] Implement `task:created` event broadcasting
- [ ] Implement `task:status` update events
- [ ] Handle multiple clients in same task room
- [ ] Implement event filtering by room membership
- [ ] Add Redis pub/sub for cross-instance broadcasting
- [ ] Handle client disconnections gracefully

### Tests
- [ ] Room broadcasting tests (8 tests)
- [ ] Multi-client tests (6 tests)
- [ ] Redis pub/sub tests (4 tests)
- [ ] **Total: 18 tests passing**

---

## Success Criteria for Phase 2

- Users can create Tasks via REST API with Team reference
- WebSocket endpoint accepts connections at `/api/v1/tasks/{id}/chat`
- Real-time chat streaming works with `chat:start`, `chat:chunk`, `chat:done` events
- chat_shell integration executes AI conversations correctly
- Message history persists and can be retrieved
- Session state management handles reconnections
- Redis adapter enables horizontal scaling
- 132+ tests passing with >80% code coverage
- End-to-end chat flow works: Task creation → WebSocket connection → Message send → AI response → History persistence
