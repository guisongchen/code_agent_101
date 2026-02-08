# Wegent Backend - Epic Phase 1 (Core CRD Management)

## Overview
This phase implements the foundational Backend CRD (Custom Resource Definition) management system that enables users to create and manage Ghost, Model, Shell, Bot, and Team resources. This is the critical integration hub that connects all modules and provides the declarative API for the Wegent platform.

---

## Epic 7: Database Schema & Models
**Goal**: Design and implement the database schema for CRD storage with proper SQLAlchemy models

### User Stories
- [ ] Create `kinds` table schema for Ghost, Model, Shell, Bot, Team, Skill resources
- [ ] Create `tasks` table schema for Task resources (separate lifecycle)
- [ ] Implement SQLAlchemy 2.0 models with JSON support for flexible spec storage
- [ ] Add soft delete support via `deleted_at` timestamp
- [ ] Create unique constraints for (kind, name, namespace) combination
- [ ] Implement database migration scripts with Alembic
- [ ] Add database connection pooling and session management

### Tests
- [ ] Unit tests for SQLAlchemy models (10 tests)
- [ ] Migration tests (5 tests)
- [ ] Database connection tests (3 tests)
- [ ] **Total: 18 tests passing**

---

## Epic 8: Pydantic Schemas & Validation
**Goal**: Define Pydantic v2 schemas for all CRD types with proper validation

### User Stories
- [ ] Create base `Metadata` and `ResourceRef` schemas
- [ ] Implement `GhostSpec` and `GhostCRD` schemas with field aliases
- [ ] Implement `ModelSpec` and `ModelCRD` schemas for AI model configuration
- [ ] Implement `ShellSpec` and `ShellCRD` schemas for runtime environments
- [ ] Implement `BotSpec` and `BotCRD` schemas with reference validation
- [ ] Implement `TeamSpec` and `TeamCRD` schemas for multi-bot teams
- [ ] Create response schemas with `from_orm` support
- [ ] Add custom validators for resource references

### Tests
- [ ] Schema validation tests (15 tests)
- [ ] Field alias tests (8 tests)
- [ ] Reference validation tests (6 tests)
- [ ] **Total: 29 tests passing**

---

## Epic 9: CRUD Service Layer
**Goal**: Implement generic CRUD service base class with resource-specific subclasses

### User Stories
- [ ] Create generic `CRDService` base class with type parameters
- [ ] Implement `get`, `list`, `create`, `delete` methods
- [ ] Create `GhostService` with Ghost-specific logic
- [ ] Create `ModelService` for Model resource management
- [ ] Create `ShellService` for Shell resource management
- [ ] Create `BotService` with reference validation (Ghost, Shell, Model)
- [ ] Create `TeamService` with member validation
- [ ] Implement soft delete logic in delete operations

### Tests
- [ ] Service layer unit tests (20 tests)
- [ ] Reference validation tests (8 tests)
- [ ] Soft delete tests (4 tests)
- [ ] **Total: 32 tests passing**

---

## Epic 10: RESTful API Endpoints
**Goal**: Implement Kubernetes-style RESTful API endpoints for all CRD types

### User Stories
- [ ] Create `POST /api/v1/kinds/ghosts` endpoint for Ghost creation
- [ ] Create `GET /api/v1/kinds/ghosts` endpoint for listing Ghosts
- [ ] Create `GET /api/v1/kinds/ghosts/{name}` endpoint for Ghost retrieval
- [ ] Create `DELETE /api/v1/kinds/ghosts/{name}` endpoint for Ghost deletion
- [ ] Create `POST /api/v1/kinds/models` endpoint for Model creation
- [ ] Create `GET /api/v1/kinds/models` endpoint for listing Models
- [ ] Create `POST /api/v1/kinds/shells` endpoint for Shell creation
- [ ] Create `GET /api/v1/kinds/shells` endpoint for listing Shells
- [ ] Create `POST /api/v1/kinds/bots` endpoint for Bot creation with reference validation
- [ ] Create `GET /api/v1/kinds/bots` endpoint for listing Bots
- [ ] Create `POST /api/v1/kinds/teams` endpoint for Team creation
- [ ] Create `GET /api/v1/kinds/teams` endpoint for listing Teams
- [ ] Create `GET /api/v1/kinds/teams/{name}` endpoint for Team retrieval
- [ ] Implement proper HTTP status codes (201, 404, 409, 204)
- [ ] Add namespace query parameter support

### Tests
- [ ] API endpoint tests (25 tests)
- [ ] HTTP status code tests (10 tests)
- [ ] Namespace filtering tests (5 tests)
- [ ] **Total: 40 tests passing**

---

## Epic 11: Authentication & Authorization
**Goal**: Implement JWT-based authentication and role-based access control

### User Stories
- [ ] Implement JWT token generation and validation
- [ ] Create `POST /api/v1/auth/login` endpoint
- [ ] Create `POST /api/v1/auth/register` endpoint
- [ ] Add `created_by` tracking to CRD resources
- [ ] Implement namespace-based resource isolation
- [ ] Add admin/user role distinction
- [ ] Create dependency injection for current user
- [ ] Protect all CRD endpoints with authentication

### Tests
- [ ] Authentication tests (10 tests)
- [ ] Authorization tests (8 tests)
- [ ] JWT token tests (6 tests)
- [ ] **Total: 24 tests passing**

---

## Success Criteria for Phase 1

- Users can create Ghost resources with system prompts via REST API
- Users can create Model resources with AI configuration
- Users can create Shell resources (Chat type for MVP)
- Users can create Bot resources that reference Ghost, Shell, and Model
- Users can create Team resources with single Bot for MVP
- All resources support namespace isolation
- JWT authentication protects all endpoints
- Soft delete allows resource recovery
- API follows Kubernetes-style conventions
- 143+ tests passing with >80% code coverage
