"""
CLI entry point for Chat Shell 101.
"""

import asyncio
import json
import time
from pathlib import Path

import click

from .agent.agent import ChatAgent
from .agent.config import AgentConfig
from .config import config
from .storage import JSONStorage, MemoryStorage, SQLiteStorage
from .storage.interfaces import Message
from .utils import format_thinking, format_tool_call, format_tool_result


@click.group()
@click.version_option(version="0.1.0", prog_name="chat-shell")
def cli():
    """Chat Shell 101 - AI chat tool with multiple deployment modes."""
    pass


@cli.command()
@click.option(
    "--model",
    "-m",
    default="deepseek-chat",
    help="llm model to use",
)
@click.option(
    "--session",
    "-s",
    default=None,
    help="Session ID for multi-turn chat (default: auto-generated)",
)
@click.option(
    "--storage",
    default="json",
    type=click.Choice(["json", "memory", "sqlite"]),
    help="Storage backend",
)
@click.option(
    "--temperature",
    "-t",
    default=1.0,
    type=float,
    help="Sampling temperature (0.0-2.0)",
)
@click.option(
    "--show-thinking",
    is_flag=True,
    help="Show model thinking process",
)
@click.option(
    "--base-url",
    default="https://api.deepseek.com",
    help="OpenAI API base URL (optional, e.g., https://api.deepseek.com)",
)
def chat(
    model: str,
    session: str,
    storage: str,
    temperature: float,
    show_thinking: bool,
    base_url: str,
):
    """Start interactive chat session."""
    asyncio.run(
        _chat_interactive(
            model=model,
            session=session,
            storage=storage,
            temperature=temperature,
            show_thinking=show_thinking,
            base_url=base_url,
        )
    )


@cli.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8000, type=int, help="Port to listen on")
@click.option("--workers", "-w", default=1, type=int, help="Number of worker processes")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
def serve(host: str, port: int, workers: int, reload: bool):
    """
    Start HTTP server for API access.

    Starts a FastAPI/uvicorn server providing HTTP endpoints
    for chat sessions, history, and session management.
    """
    import uvicorn

    click.echo(f"Starting Chat Shell 101 server on {host}:{port}")

    uvicorn.run(
        "chat_shell_101.api.app:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
    )


@cli.command()
@click.option("--model", "-m", default="deepseek-chat", help="LLM model")
@click.option("--temperature", "-t", default=0.7, type=float)
@click.option("--system", "-s", default=None, help="System prompt")
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
)
@click.argument("message")
def query(
    model: str, temperature: float, system: str, output_format: str, message: str
):
    """
    Send a single query and get response.

    Example:
        chat-shell query "What is the capital of France?"
        chat-shell query --format json "Explain quantum computing"
    """
    asyncio.run(
        _query_single(
            message=message,
            model=model,
            temperature=temperature,
            system_prompt=system,
            output_format=output_format,
        )
    )


@cli.command()
@click.option(
    "--storage", default="sqlite", type=click.Choice(["json", "sqlite"])
)
@click.option("--session", "-s", default=None, help="Filter by session ID")
@click.option("--limit", "-n", default=20, type=int, help="Number of sessions to show")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "raw"]),
)
def history(storage: str, session: str, limit: int, output_format: str):
    """
    View chat history.

    Examples:
        chat-shell history                    # Show recent sessions
        chat-shell history -s <session_id>    # Show specific session
        chat-shell history --format json      # JSON output
    """
    asyncio.run(_view_history(storage, session, limit, output_format))


@cli.group("config")
def config_cmd():
    """Configuration management commands."""
    pass


@config_cmd.command("show")
def config_show():
    """Show current configuration."""
    cfg = {
        "model": config.openai.model,
        "temperature": config.openai.temperature,
        "base_url": config.openai.base_url,
        "storage_path": str(config.storage.path),
        "show_thinking": config.show_thinking,
    }
    click.echo(json.dumps(cfg, indent=2))


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """
    Set a configuration value.

    Examples:
        chat-shell config set model gpt-4
        chat-shell config set temperature 0.5
    """
    config_path = config.get_storage_path() / "config.json"

    # Load existing config
    if config_path.exists():
        cfg = json.loads(config_path.read_text())
    else:
        cfg = {}

    # Update value
    cfg[key] = value

    # Save config
    config_path.write_text(json.dumps(cfg, indent=2))
    click.echo(f"Set {key} = {value}")
    click.echo(f"Config saved to {config_path}")


@config_cmd.command("init")
@click.option("--path", default="~/.chat_shell_101", help="Config directory")
def config_init(path: str):
    """Initialize configuration directory."""
    config_path = Path(path).expanduser()
    config_path.mkdir(parents=True, exist_ok=True)

    # Create default config file
    config_file = config_path / "config.json"
    if not config_file.exists():
        default_config = {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "storage_type": "sqlite",
        }
        config_file.write_text(json.dumps(default_config, indent=2))
        click.echo(f"Created config at {config_file}")
    else:
        click.echo(f"Config already exists at {config_file}")


async def _chat_interactive(
    model: str,
    session: str,
    storage: str,
    temperature: float,
    show_thinking: bool,
    base_url: str,
):
    """Interactive chat main loop."""
    # Update config with CLI options
    config.openai.model = model
    config.openai.temperature = temperature
    if show_thinking:
        config.show_thinking = show_thinking
    if base_url:
        config.openai.base_url = base_url

    # Initialize storage
    if storage == "json":
        storage_provider = JSONStorage()
    elif storage == "sqlite":
        storage_provider = SQLiteStorage()
    else:
        storage_provider = MemoryStorage()

    await storage_provider.initialize()

    # Initialize agent with configuration
    agent_config = AgentConfig(
        model=model,
        temperature=temperature,
    )
    agent = ChatAgent(agent_config)
    await agent.initialize()

    # Generate session ID if not provided
    session_id = session or f"cli-{int(time.time())}"

    # Print welcome message
    print("\n" + "=" * 50)
    print(f"Chat Shell 101 v0.1.0")
    print(f"Model: {model}")
    print(f"Session: {session_id}")
    print(f"Storage: {storage}")
    print("\nType 'exit' or 'quit' to end the session.")
    print("Type '/clear' to clear history.")
    print("Type '/history' to show history.")
    print("=" * 50 + "\n")

    try:
        while True:
            # Get user input
            try:
                user_input = input("You: ")
            except (EOFError, KeyboardInterrupt):
                break

            # Handle special commands
            if user_input.lower() in ("exit", "quit"):
                break

            if user_input.strip() == "/clear":
                await storage_provider.history.clear_history(session_id)
                print("History cleared.")
                continue

            if user_input.strip() == "/history":
                history = await storage_provider.history.get_history(session_id)
                if not history:
                    print("No history.")
                else:
                    for msg in history:
                        role_prefix = (
                            "user: " if msg.role == "user" else "assistant: "
                        )
                        content = str(msg.content)
                        # Truncate long content
                        if len(content) > 100:
                            content = content[:100] + "..."
                        print(f"{role_prefix}{content}")
                continue

            if not user_input.strip():
                continue

            # Load history
            history = await storage_provider.history.get_history(session_id)
            messages = []
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": user_input})

            # Stream response
            print("Assistant: ", end="", flush=True)

            full_response = ""

            try:
                async for event in agent.stream(
                    messages=messages,
                    show_thinking=config.show_thinking,
                ):
                    event_type = event.get("type", "")
                    data = event.get("data", {})

                    if event_type == "content":
                        text = data.get("text", "")
                        print(text, end="", flush=True)
                        full_response += text

                    elif event_type == "thinking":
                        text = data.get("text", "")
                        print(f"\n{format_thinking(text)}", end="", flush=True)

                    elif event_type == "tool_call":
                        tool = data.get("tool", "")
                        tool_input = data.get("input", {})
                        print(
                            f"\n{format_tool_call(tool, tool_input)}",
                            end="",
                            flush=True,
                        )

                    elif event_type == "tool_result":
                        result = data.get("result", "")
                        print(
                            f"\n{format_tool_result(result)}", end=". ", flush=True
                        )

                    elif event_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        print(f"\nError: {error_msg}")

            except Exception as e:
                print(f"\nError: {e}")
                continue

            print()  # Newline after response

            # Save to history
            await storage_provider.history.append_messages(
                session_id,
                [
                    Message(role="user", content=user_input),
                    Message(role="assistant", content=full_response),
                ],
            )

    finally:
        await storage_provider.close()
        print("\nSession ended.")


async def _query_single(
    message: str, model: str, temperature: float, system_prompt: str, output_format: str
):
    """Execute single query."""
    # Update config
    config.openai.model = model
    config.openai.temperature = temperature

    # Initialize agent
    agent_config = AgentConfig(
        model=model,
        temperature=temperature,
    )
    agent = ChatAgent(agent_config)
    await agent.initialize()

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    # Get response
    response = ""
    try:
        async for event in agent.stream(messages):
            if event["type"] == "content":
                response += event["data"]["text"]
                if output_format == "text":
                    print(event["data"]["text"], end="", flush=True)

        if output_format == "json":
            output = {
                "response": response,
                "model": model,
            }
            print(json.dumps(output))
        else:
            print()  # Newline

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


async def _view_history(storage: str, session: str, limit: int, output_format: str):
    """View history implementation."""
    # Initialize storage
    if storage == "sqlite":
        storage_provider = SQLiteStorage()
    elif storage == "json":
        storage_provider = JSONStorage()
    else:
        click.echo(f"Storage type '{storage}' not supported for history", err=True)
        return

    await storage_provider.initialize()

    try:
        if session:
            # Show specific session
            messages = await storage_provider.history.get_history(session)
            _display_messages(messages, session, output_format)
        else:
            # List sessions
            if hasattr(storage_provider.history, "list_sessions"):
                sessions = await storage_provider.history.list_sessions()
                sessions = sessions[:limit]
                _display_session_list(sessions, output_format)
            else:
                click.echo("Session listing not supported for this storage type")
    finally:
        await storage_provider.close()


def _display_messages(messages, session_id, output_format):
    """Display messages."""
    if output_format == "json":
        data = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in messages
        ]
        print(json.dumps(data, indent=2))
    else:
        click.echo(f"\nSession: {session_id}")
        click.echo("-" * 50)
        for msg in messages:
            role_color = {
                "user": "green",
                "assistant": "blue",
                "system": "yellow",
            }.get(msg.role, "white")
            click.echo(click.style(f"{msg.role}: ", fg=role_color), nl=False)
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            click.echo(content)


def _display_session_list(sessions, output_format):
    """Display session list."""
    if output_format == "json":
        print(json.dumps(sessions, indent=2))
    else:
        click.echo(f"\nRecent Sessions ({len(sessions)})")
        click.echo("-" * 50)
        for sid in sessions:
            click.echo(f"  - {sid}")


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
