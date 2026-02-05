"""
Project structure management.

Handles creation and validation of SSOT (Single Source of Truth) structure.
"""

import shutil
from pathlib import Path
from typing import Optional

from .config_manager import ConfigManager


class ProjectManager:
    """
    Manages novelist project lifecycle.
    
    Reference: docs/keikaku.md Section 3 - Data Structure
    """
    
    # Required directories for SSOT
    REQUIRED_DIRS = [
        "characters",
        "chapters", 
        "memory",
        "runs"
    ]
    
    # Required files for SSOT
    REQUIRED_FILES = [
        "bible.md",
        "memory/episodic.md",
        "memory/facts.json",
        "memory/foreshadow.json"
    ]
    
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"
    
    @classmethod
    def create(cls, project_path: Path, project_name: Optional[str] = None) -> Path:
        """
        Create new novelist project with SSOT structure.
        
        Args:
            project_path: Directory to create project in.
            project_name: Name of the project (default: directory name).
        
        Returns:
            Path: Path to created project root.
        
        Raises:
            FileExistsError: If project directory already exists and is not empty.
        """
        if project_path.exists() and any(project_path.iterdir()):
            raise FileExistsError(f"Directory not empty: {project_path}")
        
        project_path.mkdir(parents=True, exist_ok=True)
        
        if project_name is None:
            project_name = project_path.name
        
        # Create directories
        for dir_name in cls.REQUIRED_DIRS:
            (project_path / dir_name).mkdir(exist_ok=True)
        
        # Create config.yaml
        ConfigManager.create_default(project_path, project_name)
        
        # Copy templates
        cls._copy_templates(project_path, project_name)
        
        return project_path
    
    @classmethod
    def _copy_templates(cls, project_path: Path, project_name: str):
        """Copy and customize template files."""
        
        # bible.md
        bible_template = cls.TEMPLATE_DIR / "bible.md.template"
        if bible_template.exists():
            content = bible_template.read_text(encoding='utf-8')
            content = content.replace("{PROJECT_NAME}", project_name)
            (project_path / "bible.md").write_text(content, encoding='utf-8')
        
        # memory files
        facts_template = cls.TEMPLATE_DIR / "facts.json.template"
        if facts_template.exists():
            shutil.copy(facts_template, project_path / "memory" / "facts.json")
        
        foreshadow_template = cls.TEMPLATE_DIR / "foreshadow.json.template"
        if foreshadow_template.exists():
            shutil.copy(foreshadow_template, project_path / "memory" / "foreshadow.json")
        
        episodic_template = cls.TEMPLATE_DIR / "episodic.md.template"
        if episodic_template.exists():
            (project_path / "memory" / "episodic.md").write_text(
                f"# Episodic Memory\n\nProject: {project_name}\n\n## Recent Scenes\n\n",
                encoding='utf-8'
            )
    
    @classmethod
    def validate(cls, project_path: Optional[Path] = None) -> tuple[bool, list[str]]:
        """
        Validate SSOT structure.
        
        Args:
            project_path: Path to project root. If None, uses current directory.
        
        Returns:
            Tuple of (is_valid, list_of_issues).
        """
        if project_path is None:
            project_path = Path(".")
        
        issues = []
        
        # Check directories
        for dir_name in cls.REQUIRED_DIRS:
            if not (project_path / dir_name).exists():
                issues.append(f"Missing directory: {dir_name}")
        
        # Check files
        for file_name in cls.REQUIRED_FILES:
            if not (project_path / file_name).exists():
                issues.append(f"Missing file: {file_name}")
        
        # Check config
        if not (project_path / "config.yaml").exists():
            issues.append("Missing config.yaml")
        
        return len(issues) == 0, issues
    
    @classmethod
    def is_project_directory(cls, path: Optional[Path] = None) -> bool:
        """
        Check if directory is a valid novelist project.
        
        Args:
            path: Path to check. If None, uses current directory.
        
        Returns:
            bool: True if valid project directory.
        """
        is_valid, _ = cls.validate(path)
        return is_valid


class ChapterManager:
    """Manages chapter files."""
    
    @staticmethod
    def get_chapter_path(project_path: Path, chapter_number: int) -> Path:
        """Get path for chapter file."""
        return project_path / "chapters" / f"chapter_{chapter_number:03d}.md"
    
    @staticmethod
    def chapter_exists(project_path: Path, chapter_number: int) -> bool:
        """Check if chapter exists."""
        return ChapterManager.get_chapter_path(project_path, chapter_number).exists()
    
    @staticmethod
    def save_chapter(project_path: Path, chapter_number: int, content: str):
        """Save chapter content."""
        path = ChapterManager.get_chapter_path(project_path, chapter_number)
        path.write_text(content, encoding='utf-8')
    
    @staticmethod
    def load_chapter(project_path: Path, chapter_number: int) -> str:
        """Load chapter content."""
        path = ChapterManager.get_chapter_path(project_path, chapter_number)
        if not path.exists():
            raise FileNotFoundError(f"Chapter {chapter_number} not found")
        return path.read_text(encoding='utf-8')
    
    @staticmethod
    def list_chapters(project_path: Path) -> list[int]:
        """List all chapter numbers."""
        chapters_dir = project_path / "chapters"
        if not chapters_dir.exists():
            return []
        
        chapters = []
        for f in chapters_dir.glob("chapter_*.md"):
            try:
                num = int(f.stem.split("_")[1])
                chapters.append(num)
            except (IndexError, ValueError):
                continue
        
        return sorted(chapters)
