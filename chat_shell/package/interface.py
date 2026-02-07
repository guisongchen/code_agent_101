"""
ChatInterface for Package Mode - direct Python API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from pydantic import BaseModel


class ChatInput(BaseModel):
    """Input for chat interface."""

    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    context: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatOutput(BaseModel):
    """Output from chat interface."""

    content: str
    session_id: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class StreamingChatOutput(BaseModel):
    """Streaming output chunk."""

    chunk: str
    is_tool_call: bool = False
    tool_name: Optional[str] = None
    is_complete: bool = False


@dataclass
class InterfaceConfig:
    """Configuration for ChatInterface."""

    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_iterations: int = 10
    tools: Optional[List[str]] = None
    enable_streaming: bool = True


class ChatInterface(ABC):
    """
    Abstract interface for chat interactions in Package Mode.

    This interface provides a clean Python API for embedding the chat agent
    into other applications without HTTP overhead or CLI interaction.

    Usage:
        interface = DirectChatInterface(config)
        await interface.initialize()

        # Non-streaming
        response = await interface.chat("Hello!")

        # Streaming
        async for chunk in interface.stream_chat("Hello!"):
            print(chunk.chunk, end="")
    """

    def __init__(self, config: Optional[InterfaceConfig] = None):
        self.config = config or InterfaceConfig()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the interface."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        pass

    @abstractmethod
    async def chat(
        self,
        input_data: Union[str, ChatInput],
        **kwargs,
    ) -> ChatOutput:
        """
        Send a message and get a complete response.

        Args:
            input_data: Message string or ChatInput object
            **kwargs: Additional parameters (temperature, model, etc.)

        Returns:
            ChatOutput with complete response
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        input_data: Union[str, ChatInput],
        **kwargs,
    ) -> AsyncGenerator[StreamingChatOutput, None]:
        """
        Send a message and stream the response.

        Args:
            input_data: Message string or ChatInput object
            **kwargs: Additional parameters

        Yields:
            StreamingChatOutput chunks
        """
        pass

    @abstractmethod
    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history for a session."""
        pass

    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """Clear chat history for a session."""
        pass

    @abstractmethod
    async def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        pass


class DirectChatInterface(ChatInterface):
    """
    Direct implementation using in-process agent.

    This implementation uses the ChatAgent directly without any
    storage layer - messages are passed in-memory.
    """

    def __init__(self, config: Optional[InterfaceConfig] = None):
        super().__init__(config)
        self._agent = None
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    async def initialize(self) -> None:
        """Initialize the agent."""
        from ..agent.agent import ChatAgent
        from ..agent.config import AgentConfig

        agent_config = AgentConfig(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            max_iterations=self.config.max_iterations,
            tools=self.config.tools or [],
        )
        self._agent = ChatAgent(agent_config)
        await self._agent.initialize()
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown - nothing to clean up for in-memory."""
        self._sessions.clear()
        self._initialized = False

    async def chat(
        self, input_data: Union[str, ChatInput], **kwargs
    ) -> ChatOutput:
        """Non-streaming chat."""
        if not self._initialized:
            raise RuntimeError("Interface not initialized")

        chat_input = self._normalize_input(input_data)
        session_id = chat_input.session_id or self._generate_session_id()

        # Build message history
        messages = self._build_messages(chat_input, session_id)

        # Get response
        response_text = ""
        tool_calls = []

        async for event in self._agent.stream(messages, thread_id=session_id):
            if event["type"] == "content":
                response_text += event["data"]["text"]
            elif event["type"] == "tool_call":
                tool_calls.append(
                    {
                        "tool": event["data"]["tool"],
                        "input": event["data"]["input"],
                    }
                )

        # Store in session
        self._store_messages(session_id, chat_input.message, response_text)

        return ChatOutput(
            content=response_text,
            session_id=session_id,
            tool_calls=tool_calls if tool_calls else None,
        )

    async def stream_chat(
        self,
        input_data: Union[str, ChatInput],
        **kwargs,
    ) -> AsyncGenerator[StreamingChatOutput, None]:
        """Streaming chat."""
        if not self._initialized:
            raise RuntimeError("Interface not initialized")

        chat_input = self._normalize_input(input_data)
        session_id = chat_input.session_id or self._generate_session_id()

        messages = self._build_messages(chat_input, session_id)

        full_response = ""

        async for event in self._agent.stream(messages, thread_id=session_id):
            if event["type"] == "content":
                text = event["data"]["text"]
                full_response += text
                yield StreamingChatOutput(chunk=text)
            elif event["type"] == "tool_call":
                yield StreamingChatOutput(
                    chunk="",
                    is_tool_call=True,
                    tool_name=event["data"]["tool"],
                )

        self._store_messages(session_id, chat_input.message, full_response)
        yield StreamingChatOutput(chunk="", is_complete=True)

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get session history."""
        return self._sessions.get(session_id, [])

    async def clear_history(self, session_id: str) -> None:
        """Clear session history."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def list_sessions(self) -> List[str]:
        """List all sessions."""
        return list(self._sessions.keys())

    def _normalize_input(self, input_data: Union[str, ChatInput]) -> ChatInput:
        """Normalize string input to ChatInput."""
        if isinstance(input_data, str):
            return ChatInput(message=input_data)
        return input_data

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid

        return str(uuid.uuid4())

    def _build_messages(
        self,
        chat_input: ChatInput,
        session_id: str,
    ) -> List[Dict[str, str]]:
        """Build message list from input and history."""
        messages = []

        # Add system prompt if provided
        if chat_input.system_prompt:
            messages.append({"role": "system", "content": chat_input.system_prompt})

        # Add context or history
        if chat_input.context:
            messages.extend(chat_input.context)
        elif session_id in self._sessions:
            for msg in self._sessions[session_id]:
                messages.append(msg)

        # Add current message
        messages.append({"role": "user", "content": chat_input.message})

        return messages

    def _store_messages(
        self, session_id: str, user_msg: str, assistant_msg: str
    ) -> None:
        """Store messages in session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({"role": "user", "content": user_msg})
        self._sessions[session_id].append(
            {"role": "assistant", "content": assistant_msg}
        )
