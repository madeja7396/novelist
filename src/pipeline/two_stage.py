"""
2-Stage Pipeline: Director → Writer

Reference: docs/keikaku.md Section 3 - Execution Pipeline
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional

from agents.director import DirectorAgent, SimpleDirector
from agents.writer import WriterAgent, SimpleWriter
from session.manager import Session
from memory.episodic import EpisodicMemoryManager, SimpleSummarizer
from memory.facts import FactsManager
from memory.foreshadowing import ForeshadowingManager
from core.project import ChapterManager


class TwoStagePipeline:
    """
    Director → Writer pipeline.
    
    1. Director generates SceneSpec from context
    2. Writer generates prose from SceneSpec
    """
    
    def __init__(self, project_path: Path, session: Optional[Session] = None):
        self.project_path = Path(project_path)
        self.session = session or Session(project_path)
        
        # Agents
        self.director = DirectorAgent(project_path, session)
        self.writer = WriterAgent(project_path)
        
        # Memory managers
        self.episodic = EpisodicMemoryManager(project_path)
        self.facts = FactsManager(project_path)
        self.foreshadowing = ForeshadowingManager(project_path)
    
    def generate_scene(
        self,
        user_intention: str,
        chapter: Optional[int] = None,
        scene: Optional[int] = None,
        pov_character: Optional[str] = None,
        word_count: int = 1000,
    ) -> Dict:
        """
        Generate scene using 2-stage pipeline.
        
        Args:
            user_intention: What should happen in this scene
            chapter: Chapter number (auto-detected if None)
            scene: Scene number (auto-detected if None)
            pov_character: POV character
            word_count: Target word count
        
        Returns:
            Dict with scenespec, text, and metadata
        """
        # Auto-detect chapter/scene if not specified
        if chapter is None:
            chapter = self.session.context.current_chapter if self.session else 1
        if scene is None:
            scene = self.session.context.current_scene if self.session else 1
        
        print(f"[Pipeline] Generating Chapter {chapter}, Scene {scene}")
        
        # Stage 1: Director
        print("[Director] Designing scene...")
        start = time.time()
        
        director_result = self.director.design_scene(
            user_intention=user_intention,
            chapter=chapter,
            scene_num=scene,
            pov_character=pov_character,
        )
        
        director_time = time.time() - start
        print(f"[Director] Done in {director_time:.1f}s")
        
        # Parse SceneSpec
        try:
            scenespec = json.loads(director_result.text)
        except json.JSONDecodeError:
            print(f"[Warning] Failed to parse SceneSpec as JSON, using raw")
            scenespec = {"raw": director_result.text}
        
        # Stage 2: Writer
        print("[Writer] Generating prose...")
        start = time.time()
        
        # Convert SceneSpec to description for writer
        scene_description = self._scenespec_to_description(scenespec)
        
        from ..parsers.bible_parser import BibleLoader
        from ..parsers.character_loader import CharacterLoader
        
        bible = BibleLoader.load(self.project_path)
        characters = CharacterLoader.load_all(self.project_path)
        
        writer_result = self.writer.generate(
            scene_description=scene_description,
            bible=bible,
            characters=characters,
            pov_character=pov_character or scenespec.get("constraints", {}).get("pov_character"),
            word_count=word_count,
        )
        
        writer_time = time.time() - start
        print(f"[Writer] Done in {writer_time:.1f}s")
        
        # Update session
        if self.session:
            self.session.context.current_scene = scene + 1
        
        return {
            "scenespec": scenespec,
            "text": writer_result.text,
            "metadata": {
                "chapter": chapter,
                "scene": scene,
                "director_time": director_time,
                "writer_time": writer_time,
                "total_tokens": director_result.prompt_tokens + writer_result.completion_tokens,
            }
        }
    
    def _scenespec_to_description(self, scenespec: Dict) -> str:
        """Convert SceneSpec to natural description for Writer."""
        parts = []
        
        narrative = scenespec.get("narrative", {})
        if "objective" in narrative:
            parts.append(f"目的: {narrative['objective']}")
        if "summary" in narrative:
            parts.append(f"概要: {narrative['summary']}")
        if "key_events" in narrative:
            parts.append(f"必須の出来事: {', '.join(narrative['key_events'])}")
        
        constraints = scenespec.get("constraints", {})
        if "mood" in constraints:
            parts.append(f"雰囲気: {constraints['mood']}")
        if "location" in constraints:
            parts.append(f"場所: {constraints['location']}")
        
        return '\n'.join(parts)
    
    def save_and_commit(self, result: Dict, auto_commit: bool = True):
        """
        Save scene and update memory.
        
        Args:
            result: Pipeline result dict
            auto_commit: Whether to auto-update memory
        """
        chapter = result["metadata"]["chapter"]
        scene = result["metadata"]["scene"]
        text = result["text"]
        scenespec = result["scenespec"]
        
        # Save to chapter file
        ChapterManager.save_chapter(self.project_path, chapter, text)
        print(f"[Pipeline] Saved to chapter {chapter}")
        
        if auto_commit:
            self._update_memory(scene, text, scenespec)
    
    def _update_memory(self, scene_num: int, text: str, scenespec: Dict):
        """Update episodic memory, facts, etc."""
        # Episodic summary
        summary = SimpleSummarizer.summarize(text)
        
        narrative = scenespec.get("narrative", {})
        key_events = narrative.get("key_events", [])
        
        self.episodic.add_scene_summary(
            chapter=1,  # TODO: dynamic chapter
            scene=scene_num,
            summary=summary,
            key_events=key_events
        )
        print(f"[Memory] Updated episodic memory")
        
        # Extract and add facts
        chapter = f"chapter_{1:03d}"
        extracted_facts = self.facts.extract_facts_from_text(text, chapter)
        for fact_content in extracted_facts:
            self.facts.add_fact(fact_content, chapter)
        if extracted_facts:
            print(f"[Memory] Added {len(extracted_facts)} facts")
        
        # Update foreshadowing
        continuity = scenespec.get("continuity", {})
        
        # Resolve foreshadowing
        to_resolve = continuity.get("foreshadowing_to_resolve", [])
        for fs_id in to_resolve:
            self.foreshadowing.resolve_foreshadowing(fs_id, chapter)
        if to_resolve:
            print(f"[Memory] Resolved {len(to_resolve)} foreshadowing")
        
        # Plant new foreshadowing
        to_plant = continuity.get("foreshadowing_to_plant", [])
        for fs_content in to_plant:
            if isinstance(fs_content, str):
                self.foreshadowing.plant_foreshadowing(fs_content, chapter)
        if to_plant:
            print(f"[Memory] Planted {len(to_plant)} new foreshadowing")


class SimplePipeline:
    """Simplified pipeline interface."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.session = Session(project_path)
        self.pipeline = TwoStagePipeline(project_path, self.session)
    
    def write_scene(self, description: str, chapter: int = 1, 
                    word_count: int = 1000) -> str:
        """
        Simple interface: write a scene.
        
        Returns:
            Generated text
        """
        result = self.pipeline.generate_scene(
            user_intention=description,
            chapter=chapter,
            word_count=word_count
        )
        
        # Save
        self.pipeline.save_and_commit(result)
        
        return result["text"]
