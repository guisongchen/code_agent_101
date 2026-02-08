"""Pydantic schemas for Backend CRD API.

Epic 8: Pydantic Schemas & Validation
"""

from backend.schemas.auth import (
    CurrentUser,
    LoginRequest,
    RegisterRequest,
    Token,
    TokenPayload,
    UserResponse,
)
from backend.schemas.base import BaseCRD, BaseSpec, Metadata, ResourceRef
from backend.schemas.bot import BotCRD, BotCreateRequest, BotResponse, BotSpec
from backend.schemas.chat import (
    ChatEvent,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionInfo,
    ChatValidationResponse,
)
from backend.schemas.ghost import GhostCRD, GhostCreateRequest, GhostResponse, GhostSpec
from backend.schemas.model import ModelCRD, ModelCreateRequest, ModelResponse, ModelSpec
from backend.schemas.shell import ShellCRD, ShellCreateRequest, ShellResponse, ShellSpec
from backend.schemas.skill import SkillCRD, SkillCreateRequest, SkillResponse, SkillSpec
from backend.schemas.message import (
    MessageCreateRequest,
    MessageHistoryRequest,
    MessageHistoryResponse,
    MessageHistoryRequestEvent,
    MessageHistorySyncEvent,
    MessageResponse,
)
from backend.schemas.session import (
    SessionCreateRequest,
    SessionListRequest,
    SessionListResponse,
    SessionMetrics,
    SessionRecoveryRequest,
    SessionRecoveryResponse,
    SessionResponse,
    SessionUpdateRequest,
    WebSocketSessionEvent,
    WebSocketSessionRecoveryEvent,
)
from backend.schemas.task import TaskCreateRequest, TaskResponse, TaskStatusUpdate
from backend.schemas.team import TeamCRD, TeamCreateRequest, TeamResponse, TeamSpec
from backend.schemas.websocket import (
    ChatCancelledEvent,
    ChatChunkEvent,
    ChatDoneEvent,
    ChatErrorEvent,
    ChatSendEvent,
    ChatStartEvent,
    ChatThinkingEvent,
    ChatToolResultEvent,
    ChatToolStartEvent,
    HistoryRequestEvent,
    HistorySyncEvent,
    PongEvent,
    RoomInfo,
    TaskStatusEvent,
    WebSocketConnectionInfo,
)

__all__ = [
    # Base schemas
    "Metadata",
    "ResourceRef",
    "BaseCRD",
    "BaseSpec",
    # Ghost schemas
    "GhostSpec",
    "GhostCRD",
    "GhostCreateRequest",
    "GhostResponse",
    # Model schemas
    "ModelSpec",
    "ModelCRD",
    "ModelCreateRequest",
    "ModelResponse",
    # Shell schemas
    "ShellSpec",
    "ShellCRD",
    "ShellCreateRequest",
    "ShellResponse",
    # Bot schemas
    "BotSpec",
    "BotCRD",
    "BotCreateRequest",
    "BotResponse",
    # Team schemas
    "TeamSpec",
    "TeamCRD",
    "TeamCreateRequest",
    "TeamResponse",
    # Skill schemas
    "SkillSpec",
    "SkillCRD",
    "SkillCreateRequest",
    "SkillResponse",
    # Task schemas
    "TaskCreateRequest",
    "TaskResponse",
    "TaskStatusUpdate",
    # Message schemas
    "MessageCreateRequest",
    "MessageResponse",
    "MessageHistoryRequest",
    "MessageHistoryResponse",
    "MessageHistoryRequestEvent",
    "MessageHistorySyncEvent",
    # Session schemas
    "SessionCreateRequest",
    "SessionResponse",
    "SessionListRequest",
    "SessionListResponse",
    "SessionUpdateRequest",
    "SessionRecoveryRequest",
    "SessionRecoveryResponse",
    "SessionMetrics",
    "WebSocketSessionEvent",
    "WebSocketSessionRecoveryEvent",
    # Chat schemas
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ChatEvent",
    "ChatValidationResponse",
    "ChatSessionInfo",
    # WebSocket schemas
    "ChatSendEvent",
    "ChatStartEvent",
    "ChatChunkEvent",
    "ChatDoneEvent",
    "ChatErrorEvent",
    "ChatCancelledEvent",
    "ChatToolStartEvent",
    "ChatToolResultEvent",
    "ChatThinkingEvent",
    "TaskStatusEvent",
    "PongEvent",
    "HistoryRequestEvent",
    "HistorySyncEvent",
    "WebSocketConnectionInfo",
    "RoomInfo",
    # Auth schemas
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "UserResponse",
    "CurrentUser",
]
