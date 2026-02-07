"""
Utility functions for Chat Shell 101.
"""

import asyncio
from typing import Any, Dict


async def async_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying async functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def format_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Format tool call for display."""
    return f"🔧 [工具] {tool_name}({tool_input})"


def format_tool_result(result: Any) -> str:
    """Format tool result for display."""
    return f"✅ [结果] {result}"


def format_thinking(text: str) -> str:
    """Format thinking text for display."""
    return f"💭 [思考] {text}"