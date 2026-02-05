"""
Director Agent - Generate SceneSpec from context.

Uses RAG to retrieve relevant context and generates structured scene specification.
Reference: docs/keikaku.md Section 6.1 - Director Agent
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.models import SceneSpec, GenerationResult, ProjectConfig
from core.config_manager import ConfigManager
from pal.base import ProviderFactory
from session.manager import Session
from rag.retriever import RAGContextBuilder


class DirectorAgent:
    """
    Director Agent creates SceneSpec (scene design document).
    
    Input: User intention + Bible + Characters + Facts + Episodic + Foreshadowing + RAG
    Output: SceneSpec JSON
    """
    
    def __init__(self, project_path: Path, session: Optional[Session] = None,
                 provider_name: Optional[str] = None):
        """
        Initialize Director Agent.
        
        Args:
            project_path: Path to project root
            session: Optional session for context persistence
            provider_name: Override provider
        """
        self.project_path = project_path
        self.config = ConfigManager.load(project_path)
        self.session = session
        
        # Get provider
        if provider_name is None:
            provider_name = self.config.provider.get("routing", {}).get("director")
            if provider_name is None:
                provider_name = self.config.provider.get("default", "local_ollama")
        
        provider_config = self.config.provider.get("available", {}).get(provider_name, {})
        provider_type = provider_config.get("type", "ollama")
        self.provider = ProviderFactory.create(provider_type, provider_config)
        
        # RAG context builder
        if session and session.rag_builder:
            self.rag = session.rag_builder
        else:
            from ..rag.retriever import SimpleRetriever
            retriever = SimpleRetriever(project_path)
            retriever.index_project()
            self.rag = RAGContextBuilder(retriever)
    
    def design_scene(
        self,
        user_intention: str,
        chapter: int,
        scene_num: int,
        pov_character: Optional[str] = None,
        required_events: Optional[List[str]] = None,
        mood: Optional[str] = None,
    ) -> GenerationResult:
        """
        Design a scene based on user intention and context.
        
        Args:
            user_intention: What the user wants in this scene
            chapter: Chapter number
            scene_num: Scene number
            pov_character: Desired POV character
            required_events: Events that must happen
            mood: Desired mood/atmosphere
        
        Returns:
            GenerationResult containing SceneSpec JSON
        """
        # Build prompt with all context
        prompt = self._build_prompt(
            user_intention=user_intention,
            chapter=chapter,
            scene_num=scene_num,
            pov_character=pov_character,
            required_events=required_events,
            mood=mood,
        )
        
        # Generate
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        params = {
            "temperature": 0.5,  # Lower for structured output
            "max_tokens": 2000,
            "top_p": 0.9,
        }
        
        start_time = time.time()
        try:
            text = self.provider.generate(messages, params)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract JSON
            scenespec_json = self._extract_json(text)
            
            # Log to session
            if self.session:
                self.session.log_turn(
                    agent="director",
                    operation="design_scene",
                    input_data={"intention": user_intention, "chapter": chapter},
                    output_data={"scenespec": scenespec_json},
                    duration_ms=duration_ms
                )
            
            return GenerationResult(
                text=scenespec_json,
                prompt_tokens=len(prompt),
                completion_tokens=len(text),
                model=self.provider.model,
                provider=self.provider.config.get("type", "unknown"),
                duration_ms=duration_ms,
            )
        
        except Exception as e:
            raise RuntimeError(f"Scene design failed: {e}")
    
    def _system_prompt(self) -> str:
        """System prompt for Director."""
        return """あなたは小説の演出家（Director）です。
与えられた設定と意図から、次のシーンの詳細設計図（SceneSpec）をJSON形式で作成してください。

重要：
- 必ず有効なJSONのみを出力してください
- マークダウンの装飾（```json）は不要です
- 世界観・キャラクター設定に矛盾がないようにしてください
- 伏線の回収や新しい伏線の設置を考慮してください

SceneSpecの構造：
{
  "scene": {
    "id": "シーンID",
    "chapter": 章番号,
    "sequence_in_chapter": シーン番号,
    "title": "シーンタイトル"
  },
  "narrative": {
    "objective": "このシーンの目的",
    "summary": "概要",
    "key_events": ["出来事1", "出来事2"],
    "revelations": ["明かされる情報"],
    "hooks": ["次へのフック"]
  },
  "constraints": {
    "pov_character": "視点キャラクター",
    "location": "場所",
    "mood": "雰囲気",
    "characters_present": ["登場キャラ"]
  },
  "continuity": {
    "facts_to_reinforce": ["強化する事実"],
    "foreshadowing_to_resolve": ["回収する伏線ID"],
    "foreshadowing_to_plant": ["新規伏線"]
  },
  "style": {
    "pacing": "fast|normal|slow",
    "dialogue_ratio": "high|medium|low"
  }
}"""
    
    def _build_prompt(
        self,
        user_intention: str,
        chapter: int,
        scene_num: int,
        pov_character: Optional[str],
        required_events: Optional[List[str]],
        mood: Optional[str],
    ) -> str:
        """Build comprehensive prompt with all context."""
        parts = []
        
        # 1. User intention
        parts.append("## User Intention（ユーザーの意図）")
        parts.append(user_intention)
        parts.append("")
        
        # 2. RAG retrieved context
        if self.rag:
            rag_context = self.rag.build_context(user_intention, "director")
            if rag_context:
                parts.append(rag_context)
                parts.append("")
        
        # 3. Session context if available
        if self.session:
            ctx = self.session.get_prompt_context()
            
            if ctx.get('bible'):
                parts.append("## World & Style Bible")
                parts.append(ctx['bible'][:1500])
                parts.append("")
            
            if ctx.get('characters'):
                parts.append("## Characters")
                parts.append(ctx['characters'][:1200])
                parts.append("")
            
            if ctx.get('facts'):
                parts.append("## Facts")
                parts.append(ctx['facts'])
                parts.append("")
            
            if ctx.get('recap'):
                parts.append("## Recent Events（直近の出来事）")
                parts.append(ctx['recap'])
                parts.append("")
        
        # 4. Scene requirements
        parts.append("## Scene Requirements（シーン要件）")
        parts.append(f"- Chapter: {chapter}")
        parts.append(f"- Scene: {scene_num}")
        if pov_character:
            parts.append(f"- POV Character: {pov_character}")
        if mood:
            parts.append(f"- Mood: {mood}")
        if required_events:
            parts.append(f"- Required Events: {', '.join(required_events)}")
        parts.append("")
        
        # 5. Output instruction
        parts.append("## Output")
        parts.append("上記の情報に基づいて、SceneSpec JSONを作成してください。")
        parts.append("JSONのみを出力し、説明やマークダウンは含めないでください。")
        
        return '\n'.join(parts)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text."""
        # Try to find JSON block
        if "```json" in text:
            # Extract from code block
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start:end+1]
        
        return text
    
    def parse_scenespec(self, json_text: str) -> SceneSpec:
        """Parse SceneSpec from JSON."""
        data = json.loads(json_text)
        return SceneSpec(**data)


class SimpleDirector:
    """Simplified Director for quick scene design."""
    
    def __init__(self, project_path: Path, session: Optional[Session] = None):
        self.agent = DirectorAgent(project_path, session)
    
    def design(self, description: str, chapter: int = 1, scene: int = 1) -> Dict:
        """
        Quick scene design.
        
        Returns:
            SceneSpec as dict
        """
        result = self.agent.design_scene(
            user_intention=description,
            chapter=chapter,
            scene_num=scene
        )
        
        return json.loads(result.text)
