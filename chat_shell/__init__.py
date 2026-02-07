"""
Chat Shell 101 - Simplified CLI chat tool with LangGraph and OpenAI.
"""

__version__ = "0.1.0"
__author__ = "Chat Shell Team"

from .cli import main
from .agent import ChatAgent
from .config import Config

__all__ = ["main", "ChatAgent", "Config", "__version__"]