"""
Facts manager for immutable knowledge.

Reference: docs/keikaku.md Section 5.1 - Facts
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from core.models import Fact


class FactsManager:
    """
    Manages immutable facts extracted from narrative.
    
    Facts are append-only. Never delete or modify existing facts.
    Reference: docs/keikaku.md Section 5.2 - Context Compression Strategy
    """
    
    def __init__(self, project_path: Path, max_facts: int = 50):
        self.project_path = project_path
        self.facts_file = project_path / "memory" / "facts.json"
        self.max_facts = max_facts
    
    def load(self) -> List[Fact]:
        """Load all facts."""
        if not self.facts_file.exists():
            return []
        
        try:
            with open(self.facts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            facts_data = data.get('facts', [])
            return [Fact(**f) for f in facts_data]
        
        except (json.JSONDecodeError, KeyError):
            return []
    
    def save(self, facts: List[Fact]):
        """Save facts to file."""
        data = {
            "_meta": {
                "description": "Immutable Facts - SSOT",
                "count": len(facts)
            },
            "facts": [
                {
                    "id": f.id,
                    "content": f.content,
                    "category": f.category,
                    "source": f.source,
                    "created_at": f.created_at,
                    "tags": f.tags
                }
                for f in facts
            ]
        }
        
        with open(self.facts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_fact(self, content: str, source: str, 
                 category: str = "immutable",
                 tags: Optional[List[str]] = None) -> str:
        """
        Add a new fact.
        
        Args:
            content: Fact statement
            source: Chapter/scene where established
            category: 'immutable' or 'variable'
            tags: Optional tags
        
        Returns:
            Fact ID
        """
        facts = self.load()
        
        # Generate ID
        fact_id = f"f{len(facts) + 1:03d}"
        
        fact = Fact(
            id=fact_id,
            content=content,
            category=category,
            source=source,
            tags=tags or []
        )
        
        facts.append(fact)
        
        # Check limit
        if len(facts) > self.max_facts:
            # Archive oldest facts
            archived = facts[:-self.max_facts]
            self._archive_facts(archived)
            facts = facts[-self.max_facts:]
        
        self.save(facts)
        return fact_id
    
    def _archive_facts(self, facts: List[Fact]):
        """Archive old facts to separate file."""
        archive_file = self.project_path / "memory" / "facts_archive.json"
        
        existing = []
        if archive_file.exists():
            with open(archive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing = data.get('facts', [])
        
        existing.extend([f.model_dump() for f in facts])
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump({"facts": existing}, f, ensure_ascii=False, indent=2)
    
    def get_facts_for_context(self, max_chars: int = 600) -> str:
        """
        Get facts formatted for prompt context.
        
        Args:
            max_chars: Maximum characters
        
        Returns:
            Formatted facts string
        """
        facts = self.load()
        
        lines = ["## Facts（確定事実）", ""]
        
        current_len = len('\n'.join(lines))
        
        for fact in facts:
            line = f"- {fact.content}"
            if current_len + len(line) > max_chars:
                lines.append("...")
                break
            
            lines.append(line)
            current_len += len(line) + 1
        
        return '\n'.join(lines)
    
    def search_facts(self, query: str) -> List[Fact]:
        """Search facts by keyword."""
        facts = self.load()
        query_lower = query.lower()
        
        return [
            f for f in facts
            if query_lower in f.content.lower() or
            any(query_lower in t.lower() for t in f.tags)
        ]
    
    def extract_facts_from_text(self, text: str, chapter: str) -> List[str]:
        """
        Simple fact extraction from text.
        
        In production, use LLM for extraction.
        For now, extract declarative sentences.
        
        Args:
            text: Text to analyze
            chapter: Source chapter
        
        Returns:
            List of extracted fact contents
        """
        # Simple pattern: "XはYである" or "XはYだった"
        patterns = [
            r'([^。]+?)(?:は|が)([^。]+?)(?:である|だった|である|で|に|を)',
        ]
        
        extracted = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    fact = f"{match[0]}は{match[1]}"
                else:
                    fact = match
                
                # Filter: only meaningful facts (length, no dialogue markers)
                if 10 < len(fact) < 100 and '「' not in fact:
                    extracted.append(fact)
        
        return extracted[:5]  # Limit per extraction
