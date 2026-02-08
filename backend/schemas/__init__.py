"""Pydantic schemas for Backend CRD API.

Epic 8: Pydantic Schemas & Validation
"""

from backend.schemas.base import Metadata, ResourceRef, BaseCRD, BaseSpec
from backend.schemas.ghost import GhostSpec, GhostCRD, GhostCreateRequest, GhostResponse
from backend.schemas.model import ModelSpec, ModelCRD, ModelCreateRequest, ModelResponse
from backend.schemas.shell import ShellSpec, ShellCRD, ShellCreateRequest, ShellResponse
from backend.schemas.bot import BotSpec, BotCRD, BotCreateRequest, BotResponse
from backend.schemas.team import TeamSpec, TeamCRD, TeamCreateRequest, TeamResponse
from backend.schemas.skill import SkillSpec, SkillCRD, SkillCreateRequest, SkillResponse
from backend.schemas.task import TaskCreateRequest, TaskResponse, TaskStatusUpdate

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
]
