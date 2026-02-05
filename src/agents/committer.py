"""
Committer Agent - Update memory after generation.

Reference: docs/keikaku.md Section 6.1 - Committer Agent
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.models import GenerationResult
from core.config_manager import ConfigManager
from pal.base import ProviderFactory
from memory.episodic import EpisodicMemoryManager, SimpleSummarizer
from memory.facts import FactsManager
from memory.foreshadowing import ForeshadowingManager


class CommitterAgent:
    """
    Committer Agent updates memory after scene generation.
    
    Tasks:
    1. Summarize scene for episodic memory
    2. Extract new facts
    3. Update foreshadowing status
    4. Log execution
    """
    
    def __init__(self, project_path: Path, provider_name: Optional[str] = None):
        self.project_path = Path(project_path)
        self.config = ConfigManager.load(project_path)
        
        # Memory managers
        self.episodic = EpisodicMemoryManager(project_path)
        self.facts = FactsManager(project_path)
        self.foreshadowing = ForeshadowingManager(project_path)
        
        # Provider (for LLM-based extraction)
        if provider_name is None:
            provider_name = self.config.provider.get("routing", {}).get("committer")
            if provider_name is None:
                provider_name = self.config.provider.get("default", "local_ollama")
        
        provider_config = self.config.provider.get("available", {}).get(provider_name, {})
        provider_type = provider_config.get("type", "ollama")
        self.provider = ProviderFactory.create(provider_type, provider_config)
    
    def commit(
        self,
        text: str,
        chapter: int,
        scene: int,
        scenespec: Optional[Dict] = None,
        use_llm_extraction: bool = False,
    ) -> Dict:
        """
        Commit scene and update all memory.
        
        Args:
            text: Generated scene text
            chapter: Chapter number
            scene: Scene number
            scenespec: Optional SceneSpec for structured extraction
            use_llm_extraction: Use LLM for better extraction (slower)
        
        Returns:
            Commit report
        """
        report = {
            "chapter": chapter,
            "scene": scene,
            "episodic_updated": False,
            "facts_added": [],
            "foreshadowing_resolved": [],
            "foreshadowing_planted": [],
        }
        
        # 1. Update episodic memory
        summary = SimpleSummarizer.summarize(text)
        
        key_events = []
        if scenespec and "narrative" in scenespec:
            key_events = scenespec["narrary"].get("key_events", [])
        
        pov = None
        if scenespec and "constraints" in scenespec:
            pov = scenespec["constraints"].get("pov_character")
        
        self.episodic.add_scene_summary(
            chapter=chapter,
            scene=scene,
            summary=summary,
            pov_character=pov,
            key_events=key_events
        )
        report["episodic_updated"] = True
        
        # 2. Extract facts
        if use_llm_extraction:
            facts = self._extract_facts_with_llm(text, chapter)
        else:
            facts = self.facts.extract_facts_from_text(text, f"chapter_{chapter:03d}")
        
        for fact_content in facts:
            fact_id = self.facts.add_fact(fact_content, f"chapter_{chapter:03d}")
            report["facts_added"].append(fact_id)
        
        # 3. Update foreshadowing
        if scenespec and "continuity" in scenespec:
            continuity = scenespec["continuity"]
            
            # Resolve
            to_resolve = continuity.get("foreshadowing_to_resolve", [])
            for fs_id in to_resolve:
                if isinstance(fs_id, str):
                    self.foreshadowing.resolve_foreshadowing(
                        fs_id, f"chapter_{chapter:03d}"
                    )
                    report["foreshadowing_resolved"].append(fs_id)
            
            # Plant
            to_plant = continuity.get("foreshadowing_to_plant", [])
            for fs_content in to_plant:
                if isinstance(fs_content, str):
                    fs_id = self.foreshadowing.plant_foreshadowing(
                        fs_content, f"chapter_{chapter:03d}"
                    )
                    report["foreshadowing_planted"].append(fs_id)
        
        return report
    
    def _extract_facts_with_llm(self, text: str, chapter: int) -> List[str]:
        """Use LLM to extract facts from text."""
        prompt = f"""以下の文章から、確定した事実を抽出してください。

文章:
{text[:2000]}

指示:
- 事実は簡潔な一文で記述してください
- キャラクターの属性、出来事、設定などを含めてください
- 主観的な表現や推測は除外してください
- 最大5つまで

出力形式（JSON配列）:
["事実1", "事実2", "事実3"]"""
        
        messages = [
            {"role": "system", "content": "あなたは正確な情報抽出の専門家です。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self.provider.generate(messages, {"temperature": 0.2, "max_tokens": 1000})
            
            # Extract JSON array
            if "[" in result and "]" in result:
                start = result.find("[")
                end = result.rfind("]") + 1
                facts = json.loads(result[start:end])
                return [f for f in facts if isinstance(f, str)]
        
        except Exception as e:
            print(f"[Committer] LLM extraction failed: {e}, using fallback")
        
        return self.facts.extract_facts_from_text(text, f"chapter_{chapter:03d}")
    
    def suggest_memory_updates(self, text: str) -> Dict:
        """
        Suggest what memory updates are needed.
        
        For manual review before committing.
        
        Returns:
            Dict with suggestions
        """
        # Simple heuristic suggestions
        suggestions = {
            "facts": [],
            "character_updates": [],
            "foreshadowing": [],
        }
        
        # Extract potential facts
        potential_facts = self.facts.extract_facts_from_text(text, "preview")
        suggestions["facts"] = potential_facts
        
        # Check for unresolved foreshadowing
        unresolved = self.foreshadowing.get_unresolved()
        if unresolved:
            # Check if any are mentioned in text
            text_lower = text.lower()
            for fs in unresolved:
                if fs.content.lower() in text_lower:
                    suggestions["foreshadowing"].append({
                        "id": fs.id,
                        "content": fs.content,
                        "action": "consider_resolving"
                    })
        
        return suggestions


class SimpleCommitter:
    """Simplified committer interface."""
    
    def __init__(self, project_path: Path):
        self.agent = CommitterAgent(project_path)
    
    def commit_scene(self, text: str, chapter: int, scene: int):
        """Simple commit interface."""
        report = self.agent.commit(text, chapter, scene)
        
        print(f"[Committer] Committed scene {chapter}.{scene}")
        print(f"  - Episodic: updated")
        print(f"  - Facts: {len(report['facts_added'])} added")
        print(f"  - Foreshadowing: {len(report['foreshadowing_resolved'])} resolved, "
              f"{len(report['foreshadowing_planted'])} planted")
        
        return report
