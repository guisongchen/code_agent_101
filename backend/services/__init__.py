"""Backend CRUD services for CRD resources.

Epic 9: CRUD Service Layer
"""

from backend.services.base import CRDService
from backend.services.ghost import GhostService
from backend.services.model import ModelService
from backend.services.shell import ShellService
from backend.services.bot import BotService
from backend.services.team import TeamService
from backend.services.skill import SkillService
from backend.services.task import TaskService

__all__ = [
    "CRDService",
    "GhostService",
    "ModelService",
    "ShellService",
    "BotService",
    "TeamService",
    "SkillService",
    "TaskService",
]
