"""
Package mode - direct Python interface for embedding Chat Shell 101.

This module provides a clean Python API for using the chat agent
in other applications without HTTP overhead or CLI interaction.

Example:
    from chat_shell_101.package import DirectChatInterface, InterfaceConfig
    import asyncio

    async def main():
        config = InterfaceConfig(model="gpt-4", temperature=0.7)
        interface = DirectChatInterface(config)
        await interface.initialize()

        # Non-streaming chat
        result = await interface.chat("Hello, world!")
        print(result.content)

        # Streaming chat
        async for chunk in interface.stream_chat("Tell me a story"):
            print(chunk.chunk, end="")

        await interface.shutdown()

    asyncio.run(main())
"""

from .interface import (
    ChatInput,
    ChatInterface,
    ChatOutput,
    DirectChatInterface,
    InterfaceConfig,
    StreamingChatOutput,
)

__all__ = [
    "ChatInput",
    "ChatInterface",
    "ChatOutput",
    "DirectChatInterface",
    "InterfaceConfig",
    "StreamingChatOutput",
]
