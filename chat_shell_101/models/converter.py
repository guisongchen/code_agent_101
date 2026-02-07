"""
Message format conversion for different LLM providers.

Different providers have different message format requirements:
- OpenAI: Standard format with system/user/assistant/tool roles
- Anthropic: Uses 'human' instead of 'user', no system messages in list
- Google: Uses 'user'/'model' roles, different content structure

This module handles conversions between formats.
"""

from typing import List, Dict, Any, Optional, Union
from copy import deepcopy

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from .exceptions import MessageConversionError


class MessageConverter:
    """Converter for message formats across different providers.

    This class provides methods to convert messages to formats suitable
    for different LLM providers.
    """

    @classmethod
    def to_openai_format(cls, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI format.

        OpenAI format is the standard LangChain format, so this is mostly
        a pass-through, but we ensure proper structure.

        Args:
            messages: List of LangChain messages

        Returns:
            List of message dictionaries in OpenAI format
        """
        result = []
        for msg in messages:
            converted = cls._convert_single_to_openai(msg)
            if converted:
                result.append(converted)
        return result

    @classmethod
    def to_anthropic_format(
        cls, messages: List[BaseMessage], system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert messages to Anthropic format.

        Anthropic format requires:
        - 'human' instead of 'user'
        - 'assistant' for AI responses
        - System prompt passed separately, not in the message list

        Args:
            messages: List of LangChain messages
            system_prompt: Optional system prompt to include

        Returns:
            Dictionary with 'messages' and optional 'system' keys
        """
        formatted_messages = []
        extracted_system = system_prompt

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Extract system message if not already provided
                if extracted_system is None:
                    extracted_system = msg.content
                continue

            converted = cls._convert_single_to_anthropic(msg)
            if converted:
                formatted_messages.append(converted)

        result = {"messages": formatted_messages}
        if extracted_system:
            result["system"] = extracted_system

        return result

    @classmethod
    def to_google_format(cls, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Convert messages to Google Gemini format.

        Google format uses:
        - 'user' and 'model' roles
        - Content as string or list of parts
        - No system messages (converted to user messages)

        Args:
            messages: List of LangChain messages

        Returns:
            List of message dictionaries in Google format
        """
        result = []
        for msg in messages:
            converted = cls._convert_single_to_google(msg)
            if converted:
                result.append(converted)
        return result

    @classmethod
    def _convert_single_to_openai(cls, msg: BaseMessage) -> Optional[Dict[str, Any]]:
        """Convert a single message to OpenAI format."""
        if isinstance(msg, SystemMessage):
            return {"role": "system", "content": msg.content}
        elif isinstance(msg, HumanMessage):
            return {"role": "user", "content": msg.content}
        elif isinstance(msg, AIMessage):
            message_dict: Dict[str, Any] = {"role": "assistant", "content": msg.content}
            # Include tool calls if present
            if msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": str(tc.get("args", "")),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            return message_dict
        elif isinstance(msg, ToolMessage):
            return {
                "role": "tool",
                "content": msg.content,
                "tool_call_id": msg.tool_call_id,
            }
        return None

    @classmethod
    def _convert_single_to_anthropic(cls, msg: BaseMessage) -> Optional[Dict[str, Any]]:
        """Convert a single message to Anthropic format."""
        if isinstance(msg, HumanMessage):
            return {"role": "human", "content": msg.content}
        elif isinstance(msg, AIMessage):
            # Handle tool calls
            if msg.tool_calls:
                content = []
                # Add text content if present
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                # Add tool use blocks
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "input": tc.get("args", {}),
                    })
                return {"role": "assistant", "content": content}
            return {"role": "assistant", "content": msg.content}
        elif isinstance(msg, ToolMessage):
            # Tool results in Anthropic format
            return {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content,
                }],
            }
        return None

    @classmethod
    def _convert_single_to_google(cls, msg: BaseMessage) -> Optional[Dict[str, Any]]:
        """Convert a single message to Google format."""
        if isinstance(msg, SystemMessage):
            # Google doesn't have system messages, convert to user
            return {
                "role": "user",
                "parts": [{"text": f"System instruction: {msg.content}"}],
            }
        elif isinstance(msg, HumanMessage):
            return {"role": "user", "parts": [{"text": msg.content}]}
        elif isinstance(msg, AIMessage):
            return {"role": "model", "parts": [{"text": msg.content}]}
        elif isinstance(msg, ToolMessage):
            # Tool messages as user messages in Google format
            return {
                "role": "user",
                "parts": [{"text": f"Tool result: {msg.content}"}],
            }
        return None

    @classmethod
    def merge_system_messages(
        cls, messages: List[BaseMessage], default_system: Optional[str] = None
    ) -> tuple:
        """Extract and merge system messages.

        Args:
            messages: List of messages
            default_system: Default system prompt if none found

        Returns:
            Tuple of (system_prompt, non_system_messages)
        """
        system_parts = []
        non_system = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_parts.append(msg.content)
            else:
                non_system.append(msg)

        if system_parts:
            system_prompt = "\n\n".join(system_parts)
        else:
            system_prompt = default_system

        return system_prompt, non_system

    @classmethod
    def validate_messages(cls, messages: List[BaseMessage]) -> None:
        """Validate a list of messages for common issues.

        Args:
            messages: List of messages to validate

        Raises:
            MessageConversionError: If messages are invalid
        """
        if not messages:
            raise MessageConversionError("Message list cannot be empty")

        for i, msg in enumerate(messages):
            if not isinstance(msg, BaseMessage):
                raise MessageConversionError(
                    f"Message at index {i} is not a BaseMessage: {type(msg)}"
                )

            # Check for empty content (warning, not error)
            if not msg.content and not getattr(msg, "tool_calls", None):
                # Empty content is okay for AI messages with tool calls
                if not isinstance(msg, AIMessage):
                    # This is just a warning, we don't raise
                    pass

        # Check message alternation for providers that require it
        cls._check_message_alternation(messages)

    @classmethod
    def _check_message_alternation(cls, messages: List[BaseMessage]) -> None:
        """Check that messages alternate between user and assistant.

        Some providers require strict alternation. This method checks
        for common issues like consecutive user messages.

        Args:
            messages: List of messages to check
        """
        # Skip if empty or only system messages
        non_system = [m for m in messages if not isinstance(m, SystemMessage)]
        if len(non_system) < 2:
            return

        # Check for consecutive human messages
        for i in range(len(non_system) - 1):
            curr, next_msg = non_system[i], non_system[i + 1]
            if isinstance(curr, HumanMessage) and isinstance(next_msg, HumanMessage):
                # Consecutive human messages - some providers don't allow this
                # But it's generally okay, so we just note it
                pass


class FormatPreservingWrapper:
    """Wrapper that preserves message format during conversions.

    This wrapper can be used around a LangChain model to automatically
    handle message format conversions for the target provider.
    """

    def __init__(self, base_model: Any, provider: str):
        """Initialize the wrapper.

        Args:
            base_model: The underlying LangChain model
            provider: The provider name (openai, anthropic, google)
        """
        self.base_model = base_model
        self.provider = provider.lower()

    def _convert_messages(self, messages: List[BaseMessage]) -> Any:
        """Convert messages to the appropriate format."""
        if self.provider == "anthropic":
            return MessageConverter.to_anthropic_format(messages)
        elif self.provider == "google":
            return MessageConverter.to_google_format(messages)
        else:
            # OpenAI and others use standard format
            return MessageConverter.to_openai_format(messages)

    async def ainvoke(self, messages: List[BaseMessage], **kwargs):
        """Invoke with automatic format conversion."""
        converted = self._convert_messages(messages)

        if self.provider == "anthropic":
            # Anthropic format is a dict with 'messages' and 'system'
            kwargs["system"] = converted.get("system")
            return await self.base_model.ainvoke(converted["messages"], **kwargs)
        else:
            return await self.base_model.ainvoke(converted, **kwargs)

    async def astream(self, messages: List[BaseMessage], **kwargs):
        """Stream with automatic format conversion."""
        converted = self._convert_messages(messages)

        if self.provider == "anthropic":
            kwargs["system"] = converted.get("system")
            async for chunk in self.base_model.astream(converted["messages"], **kwargs):
                yield chunk
        else:
            async for chunk in self.base_model.astream(converted, **kwargs):
                yield chunk
