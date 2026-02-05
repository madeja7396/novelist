"""
Bible parser for extracting structured data from bible.md.

Reference: docs/keikaku.md Section 5.1 - Style/World Bible
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from core.models import Bible


class BibleParser:
    """
    Parser for bible.md files.
    
    Extracts Style Bible and World Bible sections into structured format.
    """
    
    @classmethod
    def parse(cls, bible_path: Path) -> Bible:
        """
        Parse bible.md file.
        
        Args:
            bible_path: Path to bible.md file.
        
        Returns:
            Bible: Structured bible data.
        
        Raises:
            FileNotFoundError: If bible.md doesn't exist.
        """
        if not bible_path.exists():
            raise FileNotFoundError(f"Bible not found: {bible_path}")
        
        content = bible_path.read_text(encoding='utf-8')
        
        style_rules = cls._extract_style_bible(content)
        world_settings = cls._extract_world_bible(content)
        
        return Bible(
            style_rules=style_rules,
            world_settings=world_settings,
            raw_content=content
        )
    
    @classmethod
    def _extract_style_bible(cls, content: str) -> Dict[str, Any]:
        """
        Extract Style Bible section.
        
        Looks for "## Style Bible" or "## 文体規約" section.
        """
        rules = {}
        
        # Find Style Bible section
        pattern = r'##\s*(?:Style Bible|文体規約).*?(?=##|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            section = match.group(0)
            
            # Extract viewpoint
            if '一人称' in section or 'first person' in section.lower():
                rules['viewpoint'] = cls._extract_value(section, ['視点', 'viewpoint', '一人称'])
            
            # Extract first person pronoun
            first_person = cls._extract_value(section, ['一人称', 'first person'])
            if first_person:
                rules['first_person'] = first_person
            
            # Extract sentence ending
            ending = cls._extract_value(section, ['文末', 'sentence ending', '文末詞'])
            if ending:
                rules['sentence_ending'] = ending
            
            # Extract metaphors
            metaphors = cls._extract_value(section, ['比喩', 'metaphors', '喩え'])
            if metaphors:
                rules['metaphors'] = metaphors
            
            # Extract forbidden items
            forbidden = cls._extract_list(section, ['禁則', 'forbidden', '禁止'])
            if forbidden:
                rules['forbidden'] = forbidden
        
        return rules
    
    @classmethod
    def _extract_world_bible(cls, content: str) -> Dict[str, Any]:
        """
        Extract World Bible section.
        
        Looks for "## World Bible" or "## 世界観" section.
        """
        settings = {}
        
        # Find World Bible section
        pattern = r'##\s*(?:World Bible|世界観).*?(?=##|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            section = match.group(0)
            
            # Extract overview
            overview = cls._extract_value(section, ['概要', 'overview', '世界名'])
            if overview:
                settings['overview'] = overview
            
            # Extract magic system
            magic = cls._extract_value(section, ['魔法', 'magic', 'mana'])
            if magic:
                settings['magic_system'] = magic
            
            # Extract technology level
            tech = cls._extract_value(section, ['技術', 'technology', '技術水準'])
            if tech:
                settings['technology'] = tech
            
            # Extract glossary
            glossary = cls._extract_table(section, '用語集|glossary')
            if glossary:
                settings['glossary'] = glossary
        
        return settings
    
    @classmethod
    def _extract_value(cls, content: str, keys: list[str]) -> Optional[str]:
        """Extract value following key pattern."""
        for key in keys:
            # Pattern: key: value or key** value or - key: value
            patterns = [
                rf'{key}[：:\*\s]+([^\n]+)',
                rf'-\s*{key}[：:\*\s]+([^\n]+)',
                rf'\*\s*{key}[：:\*\s]+([^\n]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return None
    
    @classmethod
    def _extract_list(cls, content: str, keys: list[str]) -> list[str]:
        """Extract list items following key pattern."""
        for key in keys:
            # Find section with this key
            pattern = rf'{key}.*?(?=##|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                section = match.group(0)
                # Extract list items
                items = re.findall(r'[-\*]\s*([^\n]+)', section)
                return [item.strip() for item in items if item.strip()]
        return []
    
    @classmethod
    def _extract_table(cls, content: str, header_pattern: str) -> Dict[str, str]:
        """Extract markdown table."""
        # Find table section
        pattern = rf'{header_pattern}.*?\n\|(.+?)\|(.+?)\|\n\|[-\s|]+\n((?:\|.+\|\n)+)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return {}
        
        # Parse table rows
        rows_text = match.group(3)
        result = {}
        
        for row in rows_text.strip().split('\n'):
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            if len(cells) >= 2:
                result[cells[0]] = cells[1]
        
        return result


class BibleLoader:
    """Convenience loader for project bibles."""
    
    @staticmethod
    def load(project_path: Path):
        """Load bible from project directory."""
        bible_path = project_path / "bible.md"
        return BibleParser.parse(bible_path)
    
    @staticmethod
    def load_raw(project_path: Path) -> str:
        """Load raw bible content."""
        bible_path = project_path / "bible.md"
        if not bible_path.exists():
            raise FileNotFoundError(f"bible.md not found in {project_path}")
        return bible_path.read_text(encoding='utf-8')
