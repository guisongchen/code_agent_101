# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat Shell 101 is a Python 3.10+ CLI chat tool built on LangGraph/LangChain with OpenAI GPT-4 integration. It implements a ReAct (Reasoning + Acting) agent pattern with tool execution capabilities. The project follows an async-first architecture with pluggable storage backends and extensible tool system.

## Key Architecture Components

### Agent System (`chat_shell_101/agent.py`)
- **ReAct pattern** using LangGraph state machine with agent and tools nodes
- **Streaming support** for real-time responses
- **Tool execution** with error handling and thinking process visualization
- **State management** through LangGraph's graph execution model

### Tool System (`chat_shell_101/tools/`)
- **Abstract base class** (`BaseTool`) defines tool interface
- **Tool registry** (`registry.py`) manages dynamic tool registration
- **Calculator tool** (`calculator.py`) demonstrates safe expression evaluation using AST parsing
- **LangChain integration** for tool binding and execution

### Storage Abstraction (`chat_shell_101/storage/`)
- **Interfaces** (`interfaces.py`): `StorageProvider` and `HistoryStorage` abstract classes
- **JSON storage** (`json_storage.py`): Persistent session storage with async file operations
- **Memory storage** (`memory_storage.py`): In-memory session storage for temporary use
- **Message serialization** with timestamps and metadata

### Configuration Management (`chat_shell_101/config.py`)
- **Pydantic models** for type-safe configuration with environment variable support
- **Hierarchical overrides**: CLI options > environment variables > defaults
- **OpenAI API configuration** with validation
- **Global config instance** accessible via `Config.get_instance()`

### CLI Interface (`chat_shell_101/cli.py`)
- **Click framework** for command-line interface with command groups
- **Interactive chat loop** with command history and special commands (`/clear`, `/history`, `exit`, `quit`)
- **Session management** with auto-generated IDs and storage backend selection
- **Configuration overrides** via command-line flags

## Development Commands

### Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management. Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh` if not already installed.

```bash
# Create virtual environment (use Python 3.10-3.13, as Python 3.14 has compatibility issues with LangChain)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install package with development dependencies using uv
uv sync --extra dev

# Copy environment template and add OpenAI API key
cp .env.example .env
# Edit .env to add OPENAI_API_KEY
```

### Testing
```bash
# Run all tests (tests directory currently empty - see todo.md)
pytest

# Run tests with coverage
pytest --cov=chat_shell_101

# Run specific test file
pytest tests/test_calculator.py

# Run async tests
pytest --asyncio-mode=auto
```

### Code Quality
```bash
# Format code with black
black chat_shell_101/

# Sort imports with isort
isort chat_shell_101/

# Lint with flake8
flake8 chat_shell_101/

# Run all formatting and linting
black chat_shell_101/ && isort chat_shell_101/ && flake8 chat_shell_101/
```

### Building and Distribution
```bash
# Build package using uv
uv build

# Install locally using uv
uv sync

# Run CLI directly
python -m chat_shell_101 chat
```

### Common Development Tasks
```bash
# Start interactive chat session
chat-shell chat

# Chat with thinking process shown
chat-shell chat --show-thinking

# Use specific model
chat-shell chat --model gpt-4-turbo

# Use memory storage (no persistence)
chat-shell chat --storage memory

# Run with debug output
CHAT_SHELL_DEBUG=1 chat-shell chat
```

## Extension Points

### Adding New Tools
1. Implement `BaseTool` abstract class in `chat_shell_101/tools/base.py`
2. Create tool implementation (see `calculator.py` for example)
3. Register tool in `tools/registry.py` using `register_tool()` decorator
4. Tools must implement `execute()` method and provide `name`, `description`, and `parameters` schema

### Adding New Storage Backends
1. Implement `StorageProvider` and `HistoryStorage` interfaces from `storage/interfaces.py`
2. Create storage implementation (see `json_storage.py` and `memory_storage.py`)
3. Update `config.py` to support new storage type in `StorageType` enum
4. Modify `cli.py` to accept new storage option if needed

### Configuration Extensions
- Add new environment variables in `.env.example` and `config.py`
- Update `Config` model in `config.py` with new Pydantic fields
- Add CLI options in `cli.py` using Click decorators

## Project Structure Patterns

### Async-First Design
- All I/O operations use `async/await` patterns
- File operations use `asyncio.to_thread()` for non-blocking execution
- Agent execution and tool calls are asynchronous

### Dependency Injection
- Storage backends are selected via configuration
- Tools are dynamically registered and discovered
- Configuration is managed through singleton pattern

### Separation of Concerns
- Agent logic (`agent.py`) handles AI interaction and tool orchestration
- Tools (`tools/`) implement specific capabilities
- Storage (`storage/`) manages data persistence
- CLI (`cli.py`) handles user interaction

## Environment Variables

Key environment variables (see `.env.example`):
- `OPENAI_API_KEY` (required): OpenAI API key for GPT-4 access
- `CHAT_SHELL_STORAGE_PATH`: Storage directory (default: `~/.chat_shell_101`)
- `CHAT_SHELL_DEFAULT_MODEL`: Default model (default: `gpt-4`)
- `CHAT_SHELL_SHOW_THINKING`: Show thinking process (default: `true`)
- `CHAT_SHELL_STORAGE_TYPE`: Storage backend (`json` or `memory`, default: `json`)

## Current Development Status

**Version**: v0.1.0 (MVP with basic functionality)

**Implemented**:
- Interactive CLI chat with history
- Calculator tool with safe expression evaluation
- JSON file storage for session persistence
- Thinking process visualization
- Configuration management

**High Priority Tasks** (from `todo.md`):
1. Add unit tests for tools, storage, and configuration
2. Create example scripts in `examples/` directory
3. Set up CI/CD with GitHub Actions
4. Enhance documentation

**Architecture Notes**:
- Uses `uv` for dependency management and `hatchling` as build system (configured in `pyproject.toml`)
- Development dependencies: pytest, black, isort, flake8
- License: Apache 2.0
- Entry points: `chat-shell` CLI command and `chat_shell_101.cli:main`

## Important Files for Understanding

1. `chat_shell_101/agent.py` - Core ReAct agent implementation with LangGraph
2. `chat_shell_101/tools/registry.py` - Tool registration and management
3. `chat_shell_101/storage/interfaces.py` - Storage abstraction interfaces
4. `chat_shell_101/config.py` - Configuration management with Pydantic
5. `chat_shell_101/cli.py` - User interaction flow and command parsing

## Security Considerations

- Calculator tool uses AST parsing instead of `eval()` for safe expression evaluation
- Environment variables for sensitive data (API keys)
- Input validation in configuration system
- Async file operations with proper error handling