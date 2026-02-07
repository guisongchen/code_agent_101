"""
Exceptions for the skills system.
"""


class SkillError(Exception):
    """Base exception for skill-related errors."""

    def __init__(self, message: str, skill_name: str = None):
        super().__init__(message)
        self.skill_name = skill_name
        self.message = message

    def __str__(self):
        if self.skill_name:
            return f"[{self.skill_name}] {self.message}"
        return self.message


class SkillNotFoundError(SkillError):
    """Raised when a skill is not found."""

    def __init__(self, skill_name: str):
        super().__init__(f"Skill not found: {skill_name}", skill_name=skill_name)


class SkillLoadError(SkillError):
    """Raised when skill loading fails."""

    def __init__(self, message: str, skill_name: str = None):
        super().__init__(message, skill_name=skill_name)


class SkillAlreadyLoadedError(SkillError):
    """Raised when trying to load an already loaded skill."""

    def __init__(self, skill_name: str):
        super().__init__(f"Skill already loaded: {skill_name}", skill_name=skill_name)


class SkillInitializationError(SkillError):
    """Raised when skill initialization fails."""

    def __init__(self, message: str, skill_name: str):
        super().__init__(f"Initialization failed: {message}", skill_name=skill_name)
