"""
Full Swarm Pipeline with Revision Loop.

Director → Writer → Checker → (Editor) → Committer

Reference: docs/keikaku.md Section 6.2 - Revision Loop (max 1)
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agents.director import DirectorAgent
from agents.writer import WriterAgent
from agents.checker import ContinuityCheckerAgent, Issue
from agents.editor import StyleEditorAgent
from agents.committer import CommitterAgent
from session.manager import Session
from pal.router import ProviderRouter, CostTracker
from core.project import ChapterManager
from core.models import GenerationResult


class SwarmPipeline:
    """
    Full agent swarm with revision loop.
    
    Pipeline:
    1. Director → SceneSpec
    2. Writer → Prose
    3. Checker → Issues (if any)
    4. Editor → Fixed prose (if issues found, max 1 revision)
    5. Committer → Memory update
    
    Max 1 revision to prevent infinite loops.
    """
    
    def __init__(self, project_path: Path, session: Optional[Session] = None,
                 enable_revision: bool = True):
        self.project_path = Path(project_path)
        self.session = session or Session(project_path)
        self.enable_revision = enable_revision
        
        # Provider router for multi-provider support
        self.router = ProviderRouter(project_path)
        self.cost_tracker = CostTracker(project_path)
        
        # Agents (with routing)
        self.director = DirectorAgent(project_path, session)
        self.writer = WriterAgent(project_path)
        self.checker = ContinuityCheckerAgent(project_path)
        self.editor = StyleEditorAgent(project_path)
        self.committer = CommitterAgent(project_path)
        
        # Override providers with routed ones
        self._setup_routed_providers()
    
    def _setup_routed_providers(self):
        """Setup providers with routing."""
        # Get routed providers for each agent
        try:
            self.director.provider = self.router.get_provider("director")
        except Exception:
            pass
        
        try:
            self.writer.provider = self.router.get_provider("writer")
        except Exception:
            pass
        
        try:
            self.checker.provider = self.router.get_provider("checker")
        except Exception:
            pass
        
        try:
            self.editor.provider = self.router.get_provider("editor")
        except Exception:
            pass
        
        try:
            self.committer.provider = self.router.get_provider("committer")
        except Exception:
            pass
    
    def generate_scene(
        self,
        user_intention: str,
        chapter: Optional[int] = None,
        scene: Optional[int] = None,
        pov_character: Optional[str] = None,
        word_count: int = 1000,
    ) -> Dict:
        """
        Generate scene with full swarm.
        
        Returns:
            Dict with full execution trace
        """
        if chapter is None:
            chapter = self.session.context.current_chapter
        if scene is None:
            scene = self.session.context.current_scene
        
        trace = {
            "chapter": chapter,
            "scene": scene,
            "stages": [],
            "final_text": "",
            "issues_found": 0,
            "revision_made": False,
            "total_cost": 0.0,
            "total_duration_ms": 0,
        }
        
        total_start = time.time()
        
        # Stage 1: Director
        print("[Swarm] Stage 1: Director designing scene...")
        stage_start = time.time()
        
        director_result = self.director.design_scene(
            user_intention=user_intention,
            chapter=chapter,
            scene_num=scene,
            pov_character=pov_character,
        )
        
        self._log_usage("director", director_result)
        
        trace["stages"].append({
            "agent": "director",
            "duration_ms": director_result.duration_ms,
            "tokens": director_result.prompt_tokens + director_result.completion_tokens,
        })
        
        try:
            scenespec = json.loads(director_result.text)
        except json.JSONDecodeError:
            scenespec = {"raw": director_result.text}
        
        print(f"[Swarm] Director done: {director_result.duration_ms}ms")
        
        # Stage 2: Writer
        print("[Swarm] Stage 2: Writer generating prose...")
        
        from ..parsers.bible_parser import BibleLoader
        from ..parsers.character_loader import CharacterLoader
        
        bible = BibleLoader.load(self.project_path)
        characters = CharacterLoader.load_all(self.project_path)
        
        scene_desc = self._scenespec_to_description(scenespec)
        
        writer_result = self.writer.generate(
            scene_description=scene_desc,
            bible=bible,
            characters=characters,
            pov_character=pov_character or scenespec.get("constraints", {}).get("pov_character"),
            word_count=word_count,
        )
        
        self._log_usage("writer", writer_result)
        
        trace["stages"].append({
            "agent": "writer",
            "duration_ms": writer_result.duration_ms,
            "tokens": writer_result.prompt_tokens + writer_result.completion_tokens,
        })
        
        text = writer_result.text
        print(f"[Swarm] Writer done: {writer_result.duration_ms}ms")
        
        # Stage 3: Checker
        print("[Swarm] Stage 3: Checker validating...")
        
        issues = self.checker.check(
            text=text,
            chapter=chapter,
            scene=scene,
            pov_character=pov_character,
        )
        
        trace["issues_found"] = len(issues)
        print(f"[Swarm] Checker found {len(issues)} issues")
        
        if issues:
            print(self.checker.format_report(issues))
        
        # Stage 4: Editor (if issues and revision enabled)
        if issues and self.enable_revision and len(issues) > 0:
            print("[Swarm] Stage 4: Editor fixing issues...")
            
            # Convert issues to dicts
            issue_dicts = [
                {
                    "category": i.category,
                    "description": i.description,
                    "severity": i.severity,
                }
                for i in issues if i.severity in ("error", "warning")
            ]
            
            if issue_dicts:
                edited_text = self.editor.edit(
                    text=text,
                    issues=issue_dicts,
                )
                
                trace["revision_made"] = True
                text = edited_text
                print("[Swarm] Editor applied fixes")
        
        # Stage 5: Committer
        print("[Swarm] Stage 5: Committer updating memory...")
        
        commit_report = self.committer.commit(
            text=text,
            chapter=chapter,
            scene=scene,
            scenespec=scenespec,
        )
        
        trace["commit"] = commit_report
        
        # Save to chapter
        ChapterManager.save_chapter(self.project_path, chapter, text)
        
        # Update session
        self.session.context.current_scene = scene + 1
        
        # Finalize trace
        trace["final_text"] = text
        trace["total_duration_ms"] = int((time.time() - total_start) * 1000)
        
        cost_summary = self.cost_tracker.get_summary()
        trace["total_cost"] = cost_summary.get("total_cost", 0)
        
        print(f"[Swarm] Complete in {trace['total_duration_ms']}ms")
        print(f"[Swarm] Issues: {trace['issues_found']}, Revision: {trace['revision_made']}")
        
        return trace
    
    def _log_usage(self, agent: str, result: GenerationResult):
        """Log token usage."""
        # Estimate cost if provider supports it
        cost = None
        try:
            provider = self.router.get_provider(agent)
            cost = provider.price_estimate(result.prompt_tokens, result.completion_tokens)
        except Exception:
            pass
        
        self.cost_tracker.log_usage(
            agent=agent,
            provider=result.provider,
            model=result.model,
            input_tokens=result.prompt_tokens,
            output_tokens=result.completion_tokens,
            cost=cost,
            duration_ms=result.duration_ms,
        )
    
    def _scenespec_to_description(self, scenespec: Dict) -> str:
        """Convert SceneSpec to description."""
        parts = []
        
        narrative = scenespec.get("narrative", {})
        if "objective" in narrative:
            parts.append(f"目的: {narrative['objective']}")
        if "summary" in narrative:
            parts.append(f"概要: {narrative['summary']}")
        if "key_events" in narrative:
            parts.append(f"必須: {', '.join(narrative['key_events'])}")
        
        constraints = scenespec.get("constraints", {})
        if "mood" in constraints:
            parts.append(f"雰囲気: {constraints['mood']}")
        
        return '\n'.join(parts)


class SimpleSwarm:
    """Simplified swarm interface."""
    
    def __init__(self, project_path: Path, enable_revision: bool = True):
        self.project_path = Path(project_path)
        self.session = Session(project_path)
        self.swarm = SwarmPipeline(project_path, self.session, enable_revision)
    
    def write_scene(self, description: str, chapter: int = 1, 
                    word_count: int = 1000) -> str:
        """
        Simple interface: write scene with full swarm.
        
        Returns:
            Generated text
        """
        trace = self.swarm.generate_scene(
            user_intention=description,
            chapter=chapter,
            word_count=word_count,
        )
        
        return trace["final_text"]
    
    def print_cost_report(self):
        """Print cost/usage report."""
        self.swarm.cost_tracker.print_summary()
