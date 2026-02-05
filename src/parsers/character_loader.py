"""
Character loader for parsing character JSON files.

Reference: docs/keikaku.md Section 5.1 - Character Cards
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from core.models import CharacterCard


class CharacterLoader:
    """
    Loader for character card files.
    
    Handles loading and validation of characters/*.json files.
    """
    
    CHARACTERS_DIR = "characters"
    
    @classmethod
    def load(cls, character_path: Path) -> CharacterCard:
        """
        Load single character from JSON file.
        
        Args:
            character_path: Path to character JSON file.
        
        Returns:
            CharacterCard: Loaded character data.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If JSON is invalid.
        """
        if not character_path.exists():
            raise FileNotFoundError(f"Character file not found: {character_path}")
        
        with open(character_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different schema versions
        if "_meta" in data:
            data.pop("_meta")
        
        return CharacterCard(**data)
    
    @classmethod
    def load_all(cls, project_path: Path) -> Dict[str, CharacterCard]:
        """
        Load all characters from project.
        
        Args:
            project_path: Path to project root.
        
        Returns:
            Dict mapping character ID to CharacterCard.
        """
        characters_dir = project_path / cls.CHARACTERS_DIR
        
        if not characters_dir.exists():
            return {}
        
        characters = {}
        for char_file in characters_dir.glob("*.json"):
            try:
                char = cls.load(char_file)
                char_id = char.id if char.id else char_file.stem
                characters[char_id] = char
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Failed to load {char_file}: {e}")
                continue
        
        return characters
    
    @classmethod
    def load_by_name(cls, project_path: Path, name: str) -> Optional[CharacterCard]:
        """
        Load character by name (fuzzy matching).
        
        Args:
            project_path: Path to project root.
            name: Character name or ID to search for.
        
        Returns:
            CharacterCard if found, None otherwise.
        """
        characters = cls.load_all(project_path)
        
        # Try exact ID match
        if name in characters:
            return characters[name]
        
        # Try name match
        name_lower = name.lower()
        for char in characters.values():
            char_name = char.name.get('full', '') if isinstance(char.name, dict) else str(char.name)
            if name_lower == char_name.lower():
                return char
            
            # Try short name
            short_name = char.name.get('short', '') if isinstance(char.name, dict) else ''
            if name_lower == short_name.lower():
                return char
        
        return None
    
    @classmethod
    def save(cls, character: CharacterCard, project_path: Path, filename: Optional[str] = None):
        """
        Save character to JSON file.
        
        Args:
            character: Character to save.
            project_path: Path to project root.
            filename: Optional filename (default: uses character ID).
        """
        characters_dir = project_path / cls.CHARACTERS_DIR
        characters_dir.mkdir(exist_ok=True)
        
        if filename is None:
            filename = f"{character.id or 'character'}.json"
        
        char_path = characters_dir / filename
        
        with open(char_path, 'w', encoding='utf-8') as f:
            json.dump(character.model_dump(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def list_characters(cls, project_path: Path) -> List[str]:
        """
        List all character IDs in project.
        
        Args:
            project_path: Path to project root.
        
        Returns:
            List of character IDs.
        """
        characters_dir = project_path / cls.CHARACTERS_DIR
        
        if not characters_dir.exists():
            return []
        
        ids = []
        for char_file in characters_dir.glob("*.json"):
            try:
                with open(char_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    char_id = data.get('id', char_file.stem)
                    ids.append(char_id)
            except json.JSONDecodeError:
                continue
        
        return sorted(ids)
    
    @classmethod
    def validate_schema(cls, character_path: Path) -> tuple[bool, List[str]]:
        """
        Validate character JSON against required schema.
        
        Args:
            character_path: Path to character JSON file.
        
        Returns:
            Tuple of (is_valid, list_of_issues).
        """
        issues = []
        
        try:
            with open(character_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        
        # Required fields per keikaku.md
        required = {
            "name": "Character name",
            "language.tone": "Speech tone",
            "language.first_person": "First person pronoun",
            "language.speech_pattern": "Speech pattern description",
            "personality.values": "Character values",
            "language.forbidden_words": "Forbidden words list"
        }
        
        for field, description in required.items():
            if "." in field:
                # Nested field
                parts = field.split(".")
                current = data
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        issues.append(f"Missing required field: {field} ({description})")
                        break
            else:
                if field not in data:
                    issues.append(f"Missing required field: {field} ({description})")
        
        return len(issues) == 0, issues


class CharacterFormatter:
    """Format characters for inclusion in prompts."""
    
    @staticmethod
    def format_all(characters: Dict[str, CharacterCard]) -> str:
        """
        Format all characters for prompt.
        
        Args:
            characters: Dictionary of characters.
        
        Returns:
            Formatted string for inclusion in prompts.
        """
        if not characters:
            return "（キャラクター未定義）"
        
        lines = ["## Characters", ""]
        
        for char_id, char in characters.items():
            lines.append(char.format_for_prompt())
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_by_role(characters: Dict[str, CharacterCard], role: str) -> str:
        """
        Format characters by narrative role.
        
        Args:
            characters: Dictionary of characters.
            role: Role to filter by (protagonist, antagonist, etc.).
        
        Returns:
            Formatted string.
        """
        filtered = {
            k: v for k, v in characters.items()
            if v.narrative.get('role') == role
        }
        return CharacterFormatter.format_all(filtered)
