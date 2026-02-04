# Chat Shell 101

A simplified CLI chat tool with LangGraph and OpenAI/DeepSeek integration.

## Features

- Interactive command-line chat interface
- Multi-turn conversation with history persistence
- Visualize AI thinking process (optional)
- Built-in calculator tool with safe expression evaluation
- JSON file storage for session history
- Memory storage for temporary sessions
- Support for custom API endpoints (DeepSeek compatible)
- Extensible tool system and storage backends

## Installation

1. Clone the repository:
```bash
git clone https://github.com/guisongchen/chat_shell_101.git
cd chat_shell_101
```

2. Install dependencies using uv (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env file to set your OpenAI/DeepSeek API key
```

## Usage

Start interactive chat:
```bash
chat-shell chat
```

Start chat with thinking process shown:
```bash
chat-shell chat --show-thinking
```

Use specific model (default: deepseek-chat):
```bash
chat-shell chat --model gpt-4-turbo
```

Use memory storage (no persistence):
```bash
chat-shell chat --storage memory
```

Use with DeepSeek API:
```bash
export BASE_URL=https://api.deepseek.com
export OPENAI_API_KEY=your-deepseek-api-key
chat-shell chat
```

## Commands in Chat Session

- `exit` or `quit`: Exit chat
- `/clear`: Clear current session history
- `/history`: Show current session history

## Example Scripts

The project includes comprehensive example scripts in the `examples/` directory:

```bash
# Basic usage patterns
python examples/basic_usage.py

# Advanced configuration and custom tools
python examples/advanced_config.py
```

## Project Structure

```
chat_shell_101/
├── chat_shell_101/          # Main package
│   ├── agent.py            # LangGraph ReAct agent
│   ├── cli.py              # CLI interface with Click
│   ├── config.py           # Configuration management
│   ├── storage/            # Storage abstractions
│   └── tools/              # Tool system
├── examples/               # Usage examples
├── doc/                    # Documentation
├── pyproject.toml          # Project configuration (uv/hatch)
├── .env.example           # Environment template
└── README.md              # Project documentation
```

## Development

Install development dependencies:
```bash
uv sync --extra dev
```

Run tests:
```bash
pytest
```

Format code:
```bash
black chat_shell_101/
isort chat_shell_101/
flake8 chat_shell_101/
```

## License

Apache 2.0