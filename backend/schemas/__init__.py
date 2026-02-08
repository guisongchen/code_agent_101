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
from backend.schemas.ghost import GhostCRD, GhostCreateRequest, GhostResponse, GhostSpec
from backend.schemas.model import ModelCRD, ModelCreateRequest, ModelResponse, ModelSpec
from backend.schemas.shell import ShellCRD, ShellCreateRequest, ShellResponse, ShellSpec
from backend.schemas.skill import SkillCRD, SkillCreateRequest, SkillResponse, SkillSpec
from backend.schemas.task import TaskCreateRequest, TaskResponse, TaskStatusUpdate
from backend.schemas.team import TeamCRD, TeamCreateRequest, TeamResponse, TeamSpec

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
    # Auth schemas
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "UserResponse",
    "CurrentUser",
]
