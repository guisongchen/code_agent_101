# Test Structure Guide

This document describes the organization and usage of the test suite for the Wegent project.

## Overview

The test suite is organized in a unified structure under the `tests/` directory, with clear separation between:
- **Unit tests** - Fast, isolated component tests
- **Integration tests** - Component interaction tests
- **Backend tests** - CRD management system tests (Epics 7-11)
- **Chat shell tests** - Core agent system tests (Epics 1-6)

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures and pytest configuration
├── README.md                      # This file
├── unit/                          # Unit tests - fast, isolated
│   ├── crd_backend/               # Backend CRD tests (renamed to avoid import conflict)
│   │   ├── models/
│   │   │   ├── test_kinds.py      # Kind model tests (6 tests)
│   │   │   └── test_tasks.py      # Task model tests (4 tests)
│   │   └── schemas/               # Pydantic schema tests (Epic 8)
│   │       ├── test_base_schemas.py # Base schemas (10 tests)
│   │       ├── test_ghost.py      # Ghost schemas (5 tests)
│   │       ├── test_model.py      # Model schemas (5 tests)
│   │       ├── test_shell.py      # Shell schemas (5 tests)
│   │       ├── test_bot.py        # Bot schemas with ref validation (6 tests)
│   │       ├── test_team.py       # Team schemas (5 tests)
│   │       ├── test_skill.py      # Skill schemas (5 tests)
│   │       └── test_task.py       # Task schemas (5 tests)
│   └── chat_shell/                # Chat shell tests
│       ├── agent/                 # Agent system tests (Epic 1)
│       ├── api/                   # API tests (Epic 4)
│       ├── models/                # Model tests (Epic 2)
│       ├── skills/                # Skills tests (Epic 3)
│       ├── storage/               # Storage tests (Epic 6)
│       ├── streaming/             # Streaming tests (Epic 5)
│       ├── tools/                 # Tools tests (Epic 3)
│       └── package/               # Package tests
└── integration/                   # Integration tests
    └── crd_backend/
        ├── migrations/
        │   └── test_migrations.py # Database migration tests (5 tests)
        └── test_database_connection.py # Connection tests (3 tests)
```

## Test Counts

| Category | Count |
|----------|-------|
| **Total** | 441 tests |
| **Backend** | 94 tests |
| **Chat Shell** | 324+ tests |
| **Unit** | 410 tests |
| **Integration** | 8 tests |

### Backend Test Breakdown

| Component | Count |
|-----------|-------|
| **Models** | 10 tests (Epic 7) |
| **Schemas** | 76 tests (Epic 8) |
| **Migrations** | 5 tests |
| **Database Connection** | 3 tests |
| **Total Backend** | 94 tests |

## pytest Markers

Markers are used to categorize tests for selective execution.

### Test Type Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Fast, isolated component tests |
| `@pytest.mark.integration` | Component interaction tests |
| `@pytest.mark.e2e` | End-to-end system tests |
| `@pytest.mark.slow` | Slow tests to run separately |
| `@pytest.mark.async` | Async tests requiring asyncio |

### Component Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.backend` | Backend CRD management tests |
| `@pytest.mark.chat_shell` | Chat shell tests |

### Epic Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.epic_1` | Core Agent System |
| `@pytest.mark.epic_2` | Multi-Model LLM Integration |
| `@pytest.mark.epic_3` | Tools System |
| `@pytest.mark.epic_4` | Deployment Modes |
| `@pytest.mark.epic_5` | Streaming Response System |
| `@pytest.mark.epic_6` | Storage Layer |
| `@pytest.mark.epic_7` | Database Schema & Models |
| `@pytest.mark.epic_8` | Pydantic Schemas & Validation |
| `@pytest.mark.epic_9` | CRUD Service Layer |
| `@pytest.mark.epic_10` | RESTful API Endpoints |
| `@pytest.mark.epic_11` | Authentication & Authorization |

## Usage Examples

### Run All Tests

```bash
pytest tests/
```

### Run by Component

```bash
# Run only backend tests (by directory)
pytest tests/unit/crd_backend tests/integration/crd_backend

# Or by marker
pytest tests/ -m backend

# Run only chat_shell tests
pytest tests/ -m chat_shell
```

### Run by Test Type

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run unit tests excluding slow ones
pytest tests/ -m "unit and not slow"
```

### Run by Epic

```bash
# Run tests for Epic 7 (Database Schema)
pytest tests/ -m epic_7

# Run tests for Epic 1 (Core Agent)
pytest tests/ -m epic_1
```

### Combined Filters

```bash
# Run backend unit tests only
pytest tests/ -m "backend and unit"

# Run chat_shell integration tests
pytest tests/ -m "chat_shell and integration"

# Run all tests except slow ones
pytest tests/ -m "not slow"

# Run specific epic's unit tests
pytest tests/ -m "epic_7 and unit"
```

### Run by Directory

```bash
# Run all backend tests
pytest tests/unit/backend/ tests/integration/backend/

# Run all chat_shell tests
pytest tests/unit/chat_shell/

# Run specific module
pytest tests/unit/backend/models/test_kinds.py
```

## Shared Fixtures

Common fixtures are defined in `conftest.py` and available to all tests:

### Chat Shell Fixtures

- `agent_config()` - Default agent configuration
- `agent_config_with_compression()` - Agent config with compression enabled

### Backend Fixtures

- `db_session()` - Fresh database session (SQLite in-memory)
- `team(db_session)` - Pre-created Team kind for task relationships

## Writing New Tests

### Test File Template

```python
"""Description of what these tests cover.

Tests: N tests covering functionality
"""

import pytest

# Apply markers at module level (optional)
pytestmark = [pytest.mark.unit, pytest.mark.epic_N, pytest.mark.backend]


@pytest.mark.epic_N
@pytest.mark.unit
@pytest.mark.backend
class TestFeatureName:
    """Test suite for Feature - N tests."""

    def test_specific_behavior(self, db_session):
        """Test description."""
        # Test code
        pass
```

### Guidelines

1. **Use markers**: Always apply appropriate markers (`unit`/`integration`, component, epic)
2. **Descriptive names**: Test class and method names should clearly describe what's being tested
3. **Docstrings**: Include docstrings explaining what each test verifies
4. **Fixtures**: Use shared fixtures from `conftest.py` when available
5. **Isolation**: Unit tests should be fast and not depend on external services

## Configuration

Test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--disable-warnings",
    "--asyncio-mode=auto",
]
```

## Running Tests with Coverage

```bash
# Run all tests with coverage
pytest tests/ --cov=chat_shell --cov=backend --cov-report=html

# Run backend tests with coverage
pytest tests/ -m backend --cov=backend --cov-report=term-missing
```

## Troubleshooting

### Tests Not Found

If tests aren't being discovered:
- Ensure `__init__.py` files exist in test directories
- Check that test files follow the `test_*.py` naming pattern
- Verify test classes start with `Test`

### Marker Warnings

If you see warnings about unknown markers, ensure markers are registered in `pyproject.toml` under `[tool.pytest.ini_options].markers`.

### Database Tests Failing

Backend tests use SQLite by default. For PostgreSQL-specific testing, set the `DATABASE_URL` environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname pytest tests/ -m backend
```
