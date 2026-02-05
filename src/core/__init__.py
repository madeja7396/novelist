"""Core modules for novelist."""

from .models import (
    Bible,
    CharacterCard,
    Fact,
    Foreshadowing,
    SceneSpec,
    GenerationResult,
    ProjectConfig,
)

from .project import ProjectManager, ChapterManager
from .config_manager import ConfigManager

__all__ = [
    "Bible",
    "CharacterCard",
    "Fact",
    "Foreshadowing",
    "SceneSpec",
    "GenerationResult",
    "ProjectConfig",
    "ProjectManager",
    "ChapterManager",
    "ConfigManager",
]
