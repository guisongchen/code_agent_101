# Backend MVP - Epic Phase 1: CRD Management System

## Overview

Build the Backend Core CRD (Custom Resource Definition) management system to enable basic agent creation through RESTful APIs. This phase focuses on creating the foundational backend infrastructure that connects all modules, allowing users to define agents via Ghost (system prompt), Model, Shell, Bot, and Team resources.

---

## Epic 1: Ghost Resource Management

**Goal**: Implement CRD endpoints for Ghost (system prompt) resources

### User Stories

- [ ] Implement POST /api/v1/kinds/ghosts - Create Ghost with name, description, system_prompt
- [ ] Implement GET /api/v1/kinds/ghosts - List all Ghosts with pagination
- [ ] Implement GET /api/v1/kinds/ghosts/{id} - Get specific Ghost
- [ ] Implement PUT /api/v1/kinds/ghosts/{id} - Update Ghost
- [ ] Implement DELETE /api/v1/kinds/ghosts/{id} - Delete Ghost
- [ ] Create database model for Ghost with fields: id, name, description, system_prompt, created_at, updated_at

### Tests

- [ ] Unit tests for Ghost model validation (8 tests)
- [ ] Unit tests for Ghost CRUD endpoints (15 tests)
- [ ] Integration tests for Ghost API (6 tests)
- [ ] **Total: 29 tests passing**

---

## Epic 2: Model Resource Management

**Goal**: Implement CRD endpoints for Model configuration resources

### User Stories

- [ ] Implement POST /api/v1/kinds/models - Create Model config (provider, model_name, temperature, max_tokens, api_key_ref)
- [ ] Implement GET /api/v1/kinds/models - List all Models
- [ ] Implement GET /api/v1/kinds/models/{id} - Get specific Model
- [ ] Implement PUT /api/v1/kinds/models/{id} - Update Model
- [ ] Implement DELETE /api/v1/kinds/models/{id} - Delete Model
- [ ] Support providers: openai, anthropic, google
- [ ] Create database model for Model config

### Tests

- [ ] Unit tests for Model config validation (10 tests)
- [ ] Unit tests for Model CRUD endpoints (15 tests)
- [ ] Integration tests for Model provider validation (5 tests)
- [ ] **Total: 30 tests passing**

---

## Epic 3: Shell Resource Management

**Goal**: Implement CRD endpoints for Shell (execution environment) resources

### User Stories

- [ ] Implement POST /api/v1/kinds/shells - Create Shell (type: Chat for MVP, config)
- [ ] Implement GET /api/v1/kinds/shells - List all Shells
- [ ] Implement GET /api/v1/kinds/shells/{id} - Get specific Shell
- [ ] Implement PUT /api/v1/kinds/shells/{id} - Update Shell
- [ ] Implement DELETE /api/v1/kinds/shells/{id} - Delete Shell
- [ ] MVP supports only 'Chat' type (direct chat_shell integration)
- [ ] Skip Docker-based executors for post-MVP

### Tests

- [ ] Unit tests for Shell model validation (6 tests)
- [ ] Unit tests for Shell CRUD endpoints (12 tests)
- [ ] Integration tests for Shell type validation (4 tests)
- [ ] **Total: 22 tests passing**

---

## Epic 4: Bot Resource Management

**Goal**: Implement CRD endpoints for Bot (Ghost + Shell + Model) resources

### User Stories

- [ ] Implement POST /api/v1/kinds/bots - Create Bot by referencing Ghost, Shell, and Model
- [ ] Implement GET /api/v1/kinds/bots - List all Bots
- [ ] Implement GET /api/v1/kinds/bots/{id} - Get specific Bot with resolved references
- [ ] Implement PUT /api/v1/kinds/bots/{id} - Update Bot
- [ ] Implement DELETE /api/v1/kinds/bots/{id} - Delete Bot
- [ ] Create Bot model linking ghost_id, shell_id, model_id
- [ ] Implement validation that referenced resources exist

### Tests

- [ ] Unit tests for Bot model validation (8 tests)
- [ ] Unit tests for Bot CRUD endpoints (15 tests)
- [ ] Integration tests for Bot reference validation (6 tests)
- [ ] **Total: 29 tests passing**

---

## Epic 5: Team Resource Management

**Goal**: Implement CRD endpoints for Team (group of Bots) resources

### User Stories

- [ ] Implement POST /api/v1/kinds/teams - Create Team with members (single Bot for MVP)
- [ ] Implement GET /api/v1/kinds/teams - List all Teams
- [ ] Implement GET /api/v1/kinds/teams/{id} - Get specific Team with member details
- [ ] Implement PUT /api/v1/kinds/teams/{id} - Update Team
- [ ] Implement DELETE /api/v1/kinds/teams/{id} - Delete Team
- [ ] Create Team model with members array (JSON field for future multi-bot support)
- [ ] Implement validation that referenced bots exist

### Tests

- [ ] Unit tests for Team model validation (6 tests)
- [ ] Unit tests for Team CRUD endpoints (12 tests)
- [ ] Integration tests for Team member validation (4 tests)
- [ ] **Total: 22 tests passing**

---

## Epic 6: Database Schema & Infrastructure

**Goal**: Set up database infrastructure and shared CRD patterns

### User Stories

- [ ] Design CRD base model with common fields (id, created_at, updated_at, owner_id)
- [ ] Implement database migrations using Alembic
- [ ] Create CRD service layer with common CRUD operations
- [ ] Implement API pagination and filtering
- [ ] Add API authentication middleware (JWT token validation)
- [ ] Create CRD event hooks (pre/post create, update, delete)
- [ ] Configure database connection pooling and configuration

### Tests

- [ ] Unit tests for CRD base model (5 tests)
- [ ] Unit tests for CRD service layer (10 tests)
- [ ] Integration tests for authentication middleware (6 tests)
- [ ] Integration tests for database migrations (4 tests)
- [ ] **Total: 25 tests passing**

---

## Success Criteria for Phase 1

- All CRD endpoints for Ghost, Model, Shell, Bot, and Team are implemented and functional
- Database schema supports all CRD resources with proper relationships
- API authentication protects all endpoints
- Users can create a complete agent definition: Ghost → Model → Shell → Bot → Team
- API returns proper error messages and validation feedback
- Unit tests cover all CRUD operations with 80%+ coverage
