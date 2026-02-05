"""
Episodic memory manager for scene summaries.

Maintains recent scene summaries for context continuity.
Reference: docs/keikaku.md Section 5.1 - Episodic Recap
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class EpisodicMemoryManager:
    """
    Manages episodic memory (recent scene summaries).
    
    Keeps last N scenes, discards older ones.
    Reference: docs/keikaku.md Section 5.2 - Context Compression Strategy
    """
    
    def __init__(self, project_path: Path, max_scenes: int = 5):
        self.project_path = project_path
        self.memory_file = project_path / "memory" / "episodic.md"
        self.max_scenes = max_scenes
    
    def load(self) -> str:
        """Load episodic memory content."""
        if not self.memory_file.exists():
            return ""
        return self.memory_file.read_text(encoding='utf-8')
    
    def save(self, content: str):
        """Save episodic memory content."""
        self.memory_file.write_text(content, encoding='utf-8')
    
    def add_scene_summary(self, chapter: int, scene: int, summary: str,
                          pov_character: Optional[str] = None,
                          key_events: Optional[List[str]] = None):
        """
        Add a new scene summary.
        
        Args:
            chapter: Chapter number
            scene: Scene number
            summary: Summary text (200-400 chars recommended)
            pov_character: POV character name
            key_events: List of key events
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Format entry
        lines = [
            f"### Scene {scene} (Chapter {chapter})",
            f"**Time**: {timestamp}",
        ]
        
        if pov_character:
            lines.append(f"**POV**: {pov_character}")
        
        if key_events:
            lines.append(f"**Events**: {', '.join(key_events)}")
        
        lines.extend([
            "",
            summary,
            "",
            "---",
            ""
        ])
        
        new_entry = '\n'.join(lines)
        
        # Load existing and add new
        current = self.load()
        
        # Add to beginning (most recent first)
        if current:
            updated = new_entry + '\n' + current
        else:
            updated = new_entry
        
        # Trim to max scenes
        updated = self._trim_scenes(updated)
        
        self.save(updated)
    
    def _trim_scenes(self, content: str) -> str:
        """Keep only last N scenes."""
        # Split by scene headers
        scenes = re.split(r'\n### Scene \d+', content)
        
        if len(scenes) <= self.max_scenes + 1:  # +1 for preamble
            return content
        
        # Keep preamble + last N scenes
        preamble = scenes[0]
        kept_scenes = scenes[-self.max_scenes:]
        
        # Reconstruct
        result = preamble
        for i, scene in enumerate(kept_scenes, start=len(scenes) - self.max_scenes):
            if scene.strip():
                result += f"\n### Scene {i}" + scene
        
        return result
    
    def get_recent_summary(self, max_chars: int = 800) -> str:
        """
        Get recent summary for context.
        
        Args:
            max_chars: Maximum characters to return
        
        Returns:
            Recent scenes summary
        """
        content = self.load()
        
        # Extract just the summaries (remove headers)
        lines = content.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if line.startswith('### Scene'):
                in_summary = True
                summary_lines.append(line)
            elif in_summary and line.startswith('---'):
                in_summary = False
                summary_lines.append('')
            elif in_summary:
                summary_lines.append(line)
        
        summary = '\n'.join(summary_lines)
        
        # Truncate if needed
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "..."
        
        return summary
    
    def update_character_status(self, character: str, status: str, location: str = ""):
        """
        Update character status table.
        
        Args:
            character: Character name
            status: Current status/condition
            location: Current location
        """
        content = self.load()
        
        # Find or create Character Status section
        if "## Character Status" not in content:
            content += "\n\n## Character Status\n\n"
            content += "| Character | Location | Status | Updated |\n"
            content += "|-----------|----------|--------|---------|\n"
        
        # Check if character exists
        pattern = rf"\| {re.escape(character)} \|.*\n"
        updated = datetime.now().strftime("%Y-%m-%d")
        new_line = f"| {character} | {location} | {status} | {updated} |\n"
        
        if re.search(pattern, content):
            # Update existing
            content = re.sub(pattern, new_line, content)
        else:
            # Add new
            # Find table and append
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('|') and i > 0 and lines[i-1].startswith('|-'):
                    lines.insert(i + 1, new_line.rstrip())
                    break
            content = '\n'.join(lines)
        
        self.save(content)


class SimpleSummarizer:
    """Simple extractive summarizer for scenes."""
    
    @staticmethod
    def summarize(text: str, max_sentences: int = 3) -> str:
        """
        Create simple summary of scene.
        
        Args:
            text: Scene text
            max_sentences: Number of sentences to extract
        
        Returns:
            Summary
        """
        # Simple sentence splitting
        sentences = re.split(r'[。！？\.\!\?]\s*', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return text[:200]
        
        # Take first, middle, and last sentences
        indices = [
            0,
            len(sentences) // 2,
            len(sentences) - 1
        ]
        
        selected = []
        for idx in sorted(set(indices))[:max_sentences]:
            if idx < len(sentences):
                selected.append(sentences[idx] + '。')
        
        return ''.join(selected)
