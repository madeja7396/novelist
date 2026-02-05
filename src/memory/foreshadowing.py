"""
Foreshadowing tracker for plot consistency.

Reference: docs/keikaku.md Section 5.1 - Foreshadowing
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from core.models import Foreshadowing


class ForeshadowingManager:
    """
    Manages foreshadowing tracking.
    
    Tracks unresolved, resolved, and abandoned foreshadowing.
    Helps Director know which hooks to resolve or plant.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.foreshadow_file = project_path / "memory" / "foreshadow.json"
    
    def load(self) -> List[Foreshadowing]:
        """Load all foreshadowing entries."""
        if not self.foreshadow_file.exists():
            return []
        
        try:
            with open(self.foreshadow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            fs_data = data.get('foreshadowings', [])
            return [Foreshadowing(**f) for f in fs_data]
        
        except (json.JSONDecodeError, KeyError):
            return []
    
    def save(self, foreshadowings: List[Foreshadowing]):
        """Save foreshadowing data."""
        # Calculate stats
        unresolved = sum(1 for f in foreshadowings if f.status == "unresolved")
        resolved = sum(1 for f in foreshadowings if f.status == "resolved")
        abandoned = sum(1 for f in foreshadowings if f.status == "abandoned")
        
        data = {
            "_meta": {
                "description": "Foreshadowing Tracker - SSOT",
                "total": len(foreshadowings),
                "unresolved": unresolved,
                "resolved": resolved,
                "abandoned": abandoned
            },
            "foreshadowings": [
                {
                    "id": f.id,
                    "content": f.content,
                    "status": f.status,
                    "created_in": f.created_in,
                    "target_resolution": f.target_resolution,
                    "related_chapters": f.related_chapters,
                    "resolution_chapter": f.resolution_chapter,
                    "resolution_note": f.resolution_note,
                    "priority": f.priority,
                    "tags": f.tags
                }
                for f in foreshadowings
            ]
        }
        
        with open(self.foreshadow_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def plant_foreshadowing(self, content: str, chapter: str,
                           target_chapter: Optional[str] = None,
                           priority: str = "medium",
                           tags: Optional[List[str]] = None) -> str:
        """
        Plant new foreshadowing.
        
        Args:
            content: Description of the foreshadowing
            chapter: Chapter where planted
            target_chapter: Intended resolution chapter
            priority: high/medium/low
            tags: Optional tags
        
        Returns:
            Foreshadowing ID
        """
        foreshadowings = self.load()
        
        # Generate ID
        fs_id = f"fs{len(foreshadowings) + 1:03d}"
        
        fs = Foreshadowing(
            id=fs_id,
            content=content,
            status="unresolved",
            created_in=chapter,
            target_resolution=target_chapter,
            related_chapters=[chapter],
            priority=priority,
            tags=tags or []
        )
        
        foreshadowings.append(fs)
        self.save(foreshadowings)
        
        return fs_id
    
    def resolve_foreshadowing(self, fs_id: str, chapter: str,
                              note: Optional[str] = None):
        """
        Mark foreshadowing as resolved.
        
        Args:
            fs_id: Foreshadowing ID
            chapter: Chapter where resolved
            note: Optional resolution note
        """
        foreshadowings = self.load()
        
        for fs in foreshadowings:
            if fs.id == fs_id:
                fs.status = "resolved"
                fs.resolution_chapter = chapter
                fs.resolution_note = note or ""
                if chapter not in fs.related_chapters:
                    fs.related_chapters.append(chapter)
                break
        
        self.save(foreshadowings)
    
    def abandon_foreshadowing(self, fs_id: str, chapter: str,
                             reason: Optional[str] = None):
        """Mark foreshadowing as abandoned (will not be resolved)."""
        foreshadowings = self.load()
        
        for fs in foreshadowings:
            if fs.id == fs_id:
                fs.status = "abandoned"
                fs.resolution_chapter = chapter
                fs.resolution_note = reason or "Abandoned"
                break
        
        self.save(foreshadowings)
    
    def get_unresolved(self, priority: Optional[str] = None) -> List[Foreshadowing]:
        """
        Get unresolved foreshadowing.
        
        Args:
            priority: Filter by priority (optional)
        
        Returns:
            List of unresolved foreshadowing
        """
        foreshadowings = self.load()
        
        unresolved = [f for f in foreshadowings if f.status == "unresolved"]
        
        if priority:
            unresolved = [f for f in unresolved if f.priority == priority]
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unresolved.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return unresolved
    
    def get_for_context(self, max_items: int = 10) -> str:
        """
        Get foreshadowing formatted for prompt context.
        
        Args:
            max_items: Maximum items to include
        
        Returns:
            Formatted string
        """
        foreshadowings = self.load()
        
        if not foreshadowings:
            return ""
        
        lines = ["## Foreshadowing（伏線）", ""]
        
        # Unresolved first
        unresolved = [f for f in foreshadowings if f.status == "unresolved"][:max_items]
        if unresolved:
            lines.append("### Unresolved（未回収）")
            for fs in unresolved:
                lines.append(f"- [{fs.id}] {fs.content} (priority: {fs.priority})")
            lines.append("")
        
        # Recently resolved
        resolved = [f for f in foreshadowings if f.status == "resolved"][-3:]
        if resolved:
            lines.append("### Recently Resolved（最近回収）")
            for fs in resolved:
                lines.append(f"- [{fs.id}] {fs.content} → {fs.resolution_chapter}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def suggest_resolutions(self, chapter: str) -> List[Foreshadowing]:
        """
        Suggest foreshadowing to resolve in this chapter.
        
        Args:
            chapter: Current chapter
        
        Returns:
            List of foreshadowing that should be resolved
        """
        foreshadowings = self.load()
        
        suggestions = []
        for fs in foreshadowings:
            if fs.status != "unresolved":
                continue
            
            # Check if target chapter matches
            if fs.target_resolution == chapter:
                suggestions.append(fs)
            
            # Check if overdue (too many chapters passed)
            # Simple check: if related_chapters has many entries
            elif len(fs.related_chapters) >= 3 and fs.priority == "high":
                suggestions.append(fs)
        
        return suggestions
