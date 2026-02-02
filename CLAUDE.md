# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat Shell 101 is a Python 3.10+ CLI chat tool built on LangGraph/LangChain with OpenAI/DeepSeek integration. It implements a ReAct (Reasoning + Acting) agent pattern with tool execution capabilities. The project follows an async-first architecture with pluggable storage backends and extensible tool system.

## Key Architecture Components

### Agent System (`chat_shell_101/agent.py`)
- **ReAct pattern** using LangGraph state machine with agent and tools nodes
- **Streaming support** for real-time responses with thinking process visualization
- **Tool execution** with error handling and thinking process visualization
- **State management** through LangGraph's graph execution model
- **Singleton pattern** via `get_agent()` function for global agent instance

### Tool System (`chat_shell_101/tools/`)
- **Abstract base class** (`BaseTool`) defines tool interface with `ToolInput`/`ToolOutput` schemas
- **Tool registry** (`registry.py`) manages dynamic tool registration with global `tool_registry` instance
- **Calculator tool** (`calculator.py`) demonstrates safe expression evaluation using AST parsing
- **LangChain integration** for tool binding and execution via `to_langchain_tool()` method

### Storage Abstraction (`chat_shell_101/storage/`)
- **Interfaces** (`interfaces.py`): `StorageProvider` and `HistoryStorage` abstract classes with `Message` model
- **JSON storage** (`json_storage.py`): Persistent session storage with async file operations and path management
- **Memory storage** (`memory_storage.py`): In-memory session storage for temporary use
- **Message serialization** with timestamps and metadata using Pydantic models

### Configuration Management (`chat_shell_101/config.py`)
- **Pydantic models** for type-safe configuration with environment variable support via `python-dotenv`
- **Hierarchical overrides**: CLI options > environment variables > defaults
- **OpenAI/DeepSeek API configuration** with validation and custom base URL support
- **Global config instance** accessible via `config` singleton with `Config.get_instance()` pattern

### CLI Interface (`chat_shell_101/cli.py`)
- **Click framework** for command-line interface with command groups
- **Interactive chat loop** with command history and special commands (`/clear`, `/history`, `exit`, `quit`)
- **Session management** with auto-generated IDs and storage backend selection (JSON or memory)
- **Configuration overrides** via command-line flags for model, temperature, storage type, etc.

## Development Commands

### Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management.

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install with development dependencies
uv sync --extra dev

# Copy environment template and configure API key
cp .env.example .env
# Edit .env to add OPENAI_API_KEY and optional BASE_URL for DeepSeek
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
# Format code with black (configured for 88 line length)
black chat_shell_101/

# Sort imports with isort (configured to be black-compatible)
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

# Install package locally
uv pip install -e .

# Run CLI directly
python -m chat_shell_101 chat

# Or use installed command
chat-shell chat
```

### Common Development Tasks
```bash
# Start interactive chat session
chat-shell chat

# Chat with thinking process shown
chat-shell chat --show-thinking

# Use specific model (default: deepseek-chat)
chat-shell chat --model gpt-4-turbo

# Use memory storage (no persistence)
chat-shell chat --storage memory

# Use custom API endpoint (e.g., DeepSeek)
export BASE_URL=https://api.deepseek.com
export OPENAI_API_KEY=your-deepseek-api-key
chat-shell chat

# Run with debug output
CHAT_SHELL_DEBUG=1 chat-shell chat
```

### Example Scripts
Two comprehensive example scripts are available in the `examples/` directory:

```bash
# Basic usage patterns: agent initialization, streaming, calculator tool
python examples/basic_usage.py

# Advanced configuration: custom tools, storage backends, batch processing
python examples/advanced_config.py
```

**Script Descriptions**:
- `basic_usage.py`: Core library usage patterns, agent initialization, streaming vs invoke, calculator tool usage, error handling, CLI integration
- `advanced_config.py`: Custom tool creation, storage backend comparison, batch processing with asyncio.gather(), programmatic configuration, tool registration lifecycle

## Extension Points

### Adding New Tools
1. Implement `BaseTool` abstract class in `chat_shell_101/tools/base.py`
2. Create Pydantic `ToolInput` schema for tool parameters
3. Create tool class with `name`, `description`, `input_schema`, and `execute()` method
4. Register tool using `tool_registry.register()` (see `examples/advanced_config.py` for examples)
5. Tools automatically become available to the agent after registration

### Adding New Storage Backends
1. Implement `StorageProvider` and `HistoryStorage` interfaces from `storage/interfaces.py`
2. Create storage implementation with `initialize()`, `close()`, and `history` property
3. Update `StorageType` enum in `config.py` to include new backend
4. Modify `get_storage()` function in `config.py` to instantiate new backend
5. Update CLI options in `cli.py` if needed

### Configuration Extensions
- Add new environment variables in `.env.example` and `config.py`
- Update `Config` model in `config.py` with new Pydantic fields
- Add CLI options in `cli.py` using Click decorators
- Configuration supports environment variables with `CHAT_SHELL_` prefix

## Project Structure Patterns

### Async-First Design
- All I/O operations use `async/await` patterns
- File operations use `asyncio.to_thread()` for non-blocking execution
- Agent execution and tool calls are asynchronous
- Storage operations are async throughout

### Dependency Injection
- Storage backends are selected via configuration (`json` or `memory`)
- Tools are dynamically registered and discovered via global registry
- Configuration is managed through singleton pattern with environment variable support

### Separation of Concerns
- Agent logic (`agent.py`) handles AI interaction and tool orchestration
- Tools (`tools/`) implement specific capabilities with clean interfaces
- Storage (`storage/`) manages data persistence with abstract interfaces
- CLI (`cli.py`) handles user interaction and session management
- Configuration (`config.py`) centralizes settings management

## Environment Variables

Key environment variables (see `.env.example`):
- `OPENAI_API_KEY` (required): OpenAI/DeepSeek API key
- `BASE_URL` (optional): Custom API endpoint URL (e.g., `https://api.deepseek.com`)
- `CHAT_SHELL_STORAGE_PATH`: Storage directory (default: `~/.chat_shell_101`)
- `CHAT_SHELL_DEFAULT_MODEL`: Default model (default: `deepseek-chat`)
- `CHAT_SHELL_SHOW_THINKING`: Show thinking process (default: `true`)
- `CHAT_SHELL_STORAGE_TYPE`: Storage backend (`json` or `memory`, default: `json`)

## Current Development Status

**Version**: v0.1.0 (MVP with basic functionality)

**Implemented**:
- Interactive CLI chat with history persistence
- Calculator tool with safe AST-based expression evaluation
- JSON file storage and memory storage backends
- Thinking process visualization with streaming
- Configuration management with environment variables
- Comprehensive example scripts demonstrating library usage
- Support for custom API endpoints (DeepSeek compatible)

**High Priority Tasks** (from `todo.md`):
1. Add unit tests for tools, storage, and configuration
2. ✅ Create example scripts in `examples/` directory (completed)
3. Set up CI/CD with GitHub Actions
4. Enhance documentation
5. Add web search tool integration
6. Support more LLM providers (Claude, Gemini)

**Architecture Notes**:
- Uses `uv` for dependency management and `hatchling` as build system
- Development dependencies: pytest, pytest-asyncio, black, isort, flake8
- License: Apache 2.0
- Entry point: `chat-shell` CLI command via `chat_shell_101.cli:main`
- Python 3.10+ required for modern async features

## Important Files for Understanding

1. `chat_shell_101/agent.py` - Core ReAct agent implementation with LangGraph state machine
2. `chat_shell_101/tools/registry.py` - Tool registration and management system
3. `chat_shell_101/storage/interfaces.py` - Storage abstraction interfaces and Message model
4. `chat_shell_101/config.py` - Configuration management with Pydantic and environment variables
5. `chat_shell_101/cli.py` - User interaction flow, session management, and command parsing
6. `examples/advanced_config.py` - Comprehensive examples of custom tools, storage backends, and configuration
7. `pyproject.toml` - Project configuration, dependencies, and tool configurations

## Security Considerations

- Calculator tool uses AST parsing instead of `eval()` for safe expression evaluation
- Environment variables for sensitive data (API keys)
- Input validation in configuration system via Pydantic
- Async file operations with proper error handling
- Tool execution with error capture and safe result handling