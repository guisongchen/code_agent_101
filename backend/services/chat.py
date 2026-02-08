"""Chat service for integrating chat_shell module with Backend API.

Provides chat execution capabilities by orchestrating Bot, Ghost, Model, and Shell resources.

Epic 13: Chat Shell Integration
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import BotResponse, GhostResponse, ModelResponse, ShellResponse
from backend.services.bot import BotService
from backend.services.ghost import GhostService
from backend.services.model import ModelService
from backend.services.shell import ShellService


class ChatServiceError(Exception):
    """Base exception for chat service errors."""

    pass


class BotConfigurationError(ChatServiceError):
    """Raised when bot configuration is invalid or references are missing."""

    pass


class ChatExecutionError(ChatServiceError):
    """Raised when chat execution fails."""

    pass


class ChatService:
    """Service for chat execution using chat_shell module.

    Orchestrates Bot, Ghost, Model, and Shell resources to create and execute
    chat agents using the chat_shell package.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session
        self.bot_service = BotService(session)
        self.ghost_service = GhostService(session)
        self.model_service = ModelService(session)
        self.shell_service = ShellService(session)

    async def create_chat_agent(
        self,
        bot_name: str,
        namespace: str = "default",
    ) -> "ChatAgent":
        """Create and configure a ChatAgent from Bot configuration.

        Fetches the Bot and its referenced resources (Ghost, Model, Shell)
        and builds a configured ChatAgent instance.

        Args:
            bot_name: Name of the Bot resource.
            namespace: Namespace for the Bot resource.

        Returns:
            Configured and initialized ChatAgent instance.

        Raises:
            BotConfigurationError: If bot or referenced resources not found.
            ChatExecutionError: If agent initialization fails.
        """
        # Import chat_shell components here to avoid circular imports
        try:
            from chat_shell.agent import AgentConfig, ChatAgent
        except ImportError as e:
            raise ChatServiceError(
                f"chat_shell module not available: {e}. "
                "Ensure chat_shell is installed and accessible."
            ) from e

        # Fetch Bot
        bot = await self.bot_service.get(bot_name, namespace)
        if not bot:
            raise BotConfigurationError(
                f"Bot '{bot_name}' not found in namespace '{namespace}'"
            )

        # Fetch referenced resources
        try:
            ghost = await self._get_ghost(bot)
            model = await self._get_model(bot)
            shell = await self._get_shell(bot)
        except ValueError as e:
            raise BotConfigurationError(f"Failed to resolve bot references: {e}") from e

        # Build AgentConfig from resources
        config = self._build_agent_config(ghost, model, shell, bot)

        # Create and initialize ChatAgent
        try:
            agent = ChatAgent(config)
            await agent.initialize()
            return agent
        except Exception as e:
            raise ChatExecutionError(f"Failed to initialize chat agent: {e}") from e

    async def execute_chat(
        self,
        bot_name: str,
        messages: List[Dict[str, str]],
        namespace: str = "default",
        thread_id: Optional[str] = None,
        show_thinking: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a chat session with a Bot.

        Streams chat events (content, tool calls, etc.) from the agent.

        Args:
            bot_name: Name of the Bot resource to use.
            messages: List of message dicts with 'role' and 'content' keys.
            namespace: Namespace for the Bot resource.
            thread_id: Optional thread ID for session persistence.
            show_thinking: Whether to emit thinking/tool call events.

        Yields:
            Event dictionaries with 'type' and 'data' keys.

        Raises:
            BotConfigurationError: If bot configuration is invalid.
            ChatExecutionError: If chat execution fails.

        Example:
            ```python
            async for event in chat_service.execute_chat(
                bot_name="my-bot",
                messages=[{"role": "user", "content": "Hello!"}],
            ):
                if event["type"] == "content":
                    print(event["data"]["text"], end="")
                elif event["type"] == "tool_call":
                    print(f"\n[Tool: {event['data']['tool']}]")
            ```
        """
        agent = await self.create_chat_agent(bot_name, namespace)

        try:
            async for event in agent.stream(
                messages=messages,
                thread_id=thread_id or f"{namespace}/{bot_name}",
                show_thinking=show_thinking,
            ):
                yield event
        except Exception as e:
            raise ChatExecutionError(f"Chat execution failed: {e}") from e

    async def execute_chat_sync(
        self,
        bot_name: str,
        messages: List[Dict[str, str]],
        namespace: str = "default",
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a chat session and return the complete response.

        Non-streaming version that accumulates all events into a single response.

        Args:
            bot_name: Name of the Bot resource to use.
            messages: List of message dicts with 'role' and 'content' keys.
            namespace: Namespace for the Bot resource.
            thread_id: Optional thread ID for session persistence.

        Returns:
            Dictionary with 'content', 'tool_calls', and metadata.

        Raises:
            BotConfigurationError: If bot configuration is invalid.
            ChatExecutionError: If chat execution fails.
        """
        content_parts = []
        tool_calls = []
        thinking_parts = []
        error = None

        try:
            async for event in self.execute_chat(
                bot_name=bot_name,
                messages=messages,
                namespace=namespace,
                thread_id=thread_id,
                show_thinking=True,
            ):
                event_type = event.get("type")
                event_data = event.get("data", {})

                if event_type == "content":
                    content_parts.append(event_data.get("text", ""))
                elif event_type == "tool_call":
                    tool_calls.append({
                        "tool": event_data.get("tool"),
                        "args": event_data.get("args"),
                    })
                elif event_type == "tool_result":
                    if tool_calls:
                        tool_calls[-1]["result"] = event_data.get("result")
                elif event_type == "thinking":
                    thinking_parts.append(event_data.get("text", ""))
                elif event_type == "error":
                    error = event_data.get("error", "Unknown error")

        except ChatServiceError:
            raise
        except Exception as e:
            raise ChatExecutionError(f"Chat execution failed: {e}") from e

        return {
            "content": "".join(content_parts),
            "tool_calls": tool_calls,
            "thinking": "".join(thinking_parts) if thinking_parts else None,
            "error": error,
            "bot_name": bot_name,
            "namespace": namespace,
            "thread_id": thread_id,
        }

    async def _get_ghost(self, bot: BotResponse) -> GhostResponse:
        """Fetch Ghost resource referenced by Bot.

        Args:
            bot: Bot response with ghost_ref.

        Returns:
            GhostResponse.

        Raises:
            ValueError: If Ghost not found.
        """
        ghost_ref = bot.spec.ghost_ref
        ghost = await self.ghost_service.get(
            ghost_ref.name,
            ghost_ref.namespace or bot.metadata.namespace,
        )
        if not ghost:
            raise ValueError(
                f"Ghost '{ghost_ref.name}' not found in namespace '{ghost_ref.namespace}'"
            )
        return ghost

    async def _get_model(self, bot: BotResponse) -> ModelResponse:
        """Fetch Model resource referenced by Bot.

        Args:
            bot: Bot response with model_ref.

        Returns:
            ModelResponse.

        Raises:
            ValueError: If Model not found.
        """
        model_ref = bot.spec.model_ref
        model = await self.model_service.get(
            model_ref.name,
            model_ref.namespace or bot.metadata.namespace,
        )
        if not model:
            raise ValueError(
                f"Model '{model_ref.name}' not found in namespace '{model_ref.namespace}'"
            )
        return model

    async def _get_shell(self, bot: BotResponse) -> ShellResponse:
        """Fetch Shell resource referenced by Bot.

        Args:
            bot: Bot response with shell_ref.

        Returns:
            ShellResponse.

        Raises:
            ValueError: If Shell not found.
        """
        shell_ref = bot.spec.shell_ref
        shell = await self.shell_service.get(
            shell_ref.name,
            shell_ref.namespace or bot.metadata.namespace,
        )
        if not shell:
            raise ValueError(
                f"Shell '{shell_ref.name}' not found in namespace '{shell_ref.namespace}'"
            )
        return shell

    def _build_agent_config(
        self,
        ghost: GhostResponse,
        model: ModelResponse,
        shell: ShellResponse,
        bot: BotResponse,
    ) -> "AgentConfig":
        """Build AgentConfig from Backend resources.

        Maps Ghost, Model, Shell, and Bot configurations to chat_shell's
        AgentConfig dataclass.

        Args:
            ghost: Ghost resource for system prompt.
            model: Model resource for LLM configuration.
            shell: Shell resource for tool/environment configuration.
            bot: Bot resource for execution parameters.

        Returns:
            Configured AgentConfig instance.
        """
        from chat_shell.agent import AgentConfig

        # Extract model configuration
        model_config = model.spec.config
        provider = model_config.provider
        model_name = model_config.model_name

        # Extract ghost configuration
        system_prompt = ghost.spec.system_prompt
        temperature = ghost.spec.temperature or model.spec.default_temperature or 0.7
        max_tokens = ghost.spec.context_window or model.spec.context_length or 4096

        # Extract shell configuration for tools
        # Priority: Shell.allowed_tools > Ghost.tools_enabled > all tools
        tools = []
        if shell.spec.allowed_tools:
            tools = shell.spec.allowed_tools
        elif ghost.spec.tools_enabled:
            tools = ghost.spec.tools_enabled

        # Extract bot configuration
        max_iterations = bot.spec.max_iterations or 10

        return AgentConfig(
            provider=provider,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
            tools=tools,
            # Checkpointing enabled by default for session persistence
            checkpoint_enabled=True,
            checkpoint_type="memory",
            # Context compression enabled by default
            compress_context=True,
            max_context_tokens=max_tokens,
            compression_threshold=0.8,
            keep_recent_messages=4,
        )

    async def validate_bot_configuration(
        self,
        bot_name: str,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        """Validate that a Bot has valid configuration and all references exist.

        Args:
            bot_name: Name of the Bot resource.
            namespace: Namespace for the Bot resource.

        Returns:
            Dictionary with validation results.

        Raises:
            BotConfigurationError: If configuration is invalid.
        """
        errors = []
        warnings = []

        # Fetch Bot
        bot = await self.bot_service.get(bot_name, namespace)
        if not bot:
            raise BotConfigurationError(
                f"Bot '{bot_name}' not found in namespace '{namespace}'"
            )

        # Validate Ghost reference
        try:
            ghost = await self._get_ghost(bot)
            if not ghost.spec.system_prompt:
                warnings.append("Ghost has empty system_prompt")
        except ValueError as e:
            errors.append(str(e))
            ghost = None

        # Validate Model reference
        try:
            model = await self._get_model(bot)
            if not model.spec.config.provider:
                errors.append("Model has no provider specified")
            if not model.spec.config.model_name:
                errors.append("Model has no model_name specified")
        except ValueError as e:
            errors.append(str(e))
            model = None

        # Validate Shell reference
        try:
            shell = await self._get_shell(bot)
        except ValueError as e:
            errors.append(str(e))
            shell = None

        # Check chat_shell availability
        try:
            from chat_shell.agent import AgentConfig, ChatAgent
        except ImportError:
            errors.append("chat_shell module not available")

        return {
            "valid": len(errors) == 0,
            "bot": bot_name,
            "namespace": namespace,
            "errors": errors,
            "warnings": warnings,
            "ghost": ghost.metadata.name if ghost else None,
            "model": model.metadata.name if model else None,
            "shell": shell.metadata.name if shell else None,
        }
