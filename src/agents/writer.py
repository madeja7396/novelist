"""
Writer Agent - Generate prose from scene specifications.

Reference: docs/keikaku.md Section 6.1 - Writer Agent
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from core.models import Bible, CharacterCard, GenerationResult, ProjectConfig
from core.config_manager import ConfigManager
from pal.base import ProviderFactory


class WriterAgent:
    """
    Writer Agent generates narrative prose.
    
    Input: Scene specification + context (Bible, Characters)
    Output: Prose only (no meta-thoughts, no JSON)
    
    Design principles:
    - Follows Style Bible strictly
    - Respects Character Cards
    - No meta-commentary
    - No thinking out loud
    """
    
    def __init__(self, project_path: Path, provider_name: Optional[str] = None):
        """
        Initialize Writer Agent.
        
        Args:
            project_path: Path to project root.
            provider_name: Override provider (default from config).
        """
        self.project_path = project_path
        self.config = ConfigManager.load(project_path)
        
        # Get provider configuration
        if provider_name is None:
            provider_name = self.config.provider.get("routing", {}).get("writer")
            if provider_name is None:
                provider_name = self.config.provider.get("default", "local_ollama")
        
        provider_config = self.config.provider.get("available", {}).get(provider_name, {})
        
        # Create provider instance
        provider_type = provider_config.get("type", "ollama")
        self.provider = ProviderFactory.create(provider_type, provider_config)
    
    def generate(
        self,
        scene_description: str,
        bible: Bible,
        characters: Dict[str, CharacterCard],
        pov_character: Optional[str] = None,
        word_count: int = 1000,
        temperature: float = 0.8,
    ) -> GenerationResult:
        """
        Generate a scene.
        
        Args:
            scene_description: Description of what should happen.
            bible: Style and world bible.
            characters: Character cards for the scene.
            pov_character: POV character ID/name.
            word_count: Target word count.
            temperature: Creativity parameter.
        
        Returns:
            GenerationResult with generated text and metadata.
        """
        # Build prompt
        prompt = self._build_prompt(
            scene_description=scene_description,
            bible=bible,
            characters=characters,
            pov_character=pov_character,
            word_count=word_count,
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        # Generation parameters
        params = {
            "temperature": temperature,
            "max_tokens": min(word_count * 2, 4000),  # Rough estimate: 2 tokens per char
            "top_p": 0.9,
        }
        
        # Generate
        start_time = time.time()
        try:
            text = self.provider.generate(messages, params)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Clean output
            text = self._clean_output(text)
            
            return GenerationResult(
                text=text,
                prompt_tokens=len(prompt),  # Approximate
                completion_tokens=len(text),
                model=self.provider.model,
                provider=self.provider.config.get("type", "unknown"),
                duration_ms=duration_ms,
            )
        
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")
    
    def _system_prompt(self) -> str:
        """
        System prompt for Writer Agent.
        
        Emphasizes constraints: no meta-thoughts, no JSON, follow style.
        """
        return """あなたはプロの小説家です。与えられた設定と文体に従って、小説の本文を書いてください。

重要な制約：
- 本文のみを出力してください。思考プロセス、注釈、解説は一切含めないでください。
- JSON形式やマークダウンの見出しを使わないでください。
- 「この物語では」「読者の皆さん」といったメタ的な言及は禁止です。
- 与えられた文体（一人称、文末、比喩表現）を厳密に守ってください。
- キャラクターの口調、価値観、禁則事項を厳守してください。

出力は自然な小説の文章のみとし、前置き・後書きは不要です。"""
    
    def _build_prompt(
        self,
        scene_description: str,
        bible: Bible,
        characters: Dict[str, CharacterCard],
        pov_character: Optional[str],
        word_count: int,
    ) -> str:
        """
        Build generation prompt from context.
        
        Follows Prompt Program structure from keikaku.md Section 5.1
        """
        parts = []
        
        # 1. Style Bible
        parts.append(bible.format_style_section())
        parts.append("")
        
        # 2. World Bible
        parts.append(bible.format_world_section())
        parts.append("")
        
        # 3. Characters
        parts.append("## Characters")
        for char_id, char in characters.items():
            parts.append(char.format_for_prompt())
        parts.append("")
        
        # 4. Scene Specification
        parts.append("## Scene Specification")
        parts.append(f"{scene_description}")
        parts.append("")
        
        if pov_character:
            parts.append(f"**視点**: {pov_character}の一人称視点")
        
        parts.append(f"**目標文字数**: {word_count}文字程度")
        parts.append("")
        
        # 5. Instruction
        parts.append("## Instruction")
        parts.append("上記の設定に従って、シーンの本文を書いてください。")
        parts.append("- 地の文とセリフを含む自然な文章")
        parts.append("- メタ的な言及を含めない")
        parts.append("- 設定に矛盾がないように注意")
        
        return '\n'.join(parts)
    
    def _clean_output(self, text: str) -> str:
        """
        Clean generated output.
        
        Removes meta-commentary, JSON markers, etc.
        """
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split('\n')
            # Find first and last ```
            start = None
            end = None
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start is None:
                        start = i
                    else:
                        end = i
                        break
            
            if start is not None and end is not None:
                text = '\n'.join(lines[start+1:end])
        
        # Strip whitespace
        text = text.strip()
        
        # Remove common meta-prefixes
        meta_prefixes = [
            "本文：", "本文:", "出力：", "出力:",
            "シーン：", "シーン:", "小説：", "小説:"
        ]
        for prefix in meta_prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text


class SimpleWriter:
    """
    Simplified writer for Phase 0 (basic generation without full context).
    
    Used for quick testing and basic scene generation.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.agent = WriterAgent(project_path)
    
    def write_scene(
        self,
        description: str,
        word_count: int = 1000,
        bible: Optional[Bible] = None,
        characters: Optional[Dict[str, CharacterCard]] = None,
    ) -> str:
        """
        Simple scene writing interface.
        
        Args:
            description: Scene description.
            word_count: Target word count.
            bible: Optional bible (loads from project if not provided).
            characters: Optional characters (loads from project if not provided).
        
        Returns:
            Generated text.
        """
        # Load defaults if not provided
        if bible is None:
            from parsers.bible_parser import BibleLoader
            bible = BibleLoader.load(self.project_path)
        
        if characters is None:
            from parsers.character_loader import CharacterLoader
            characters = CharacterLoader.load_all(self.project_path)
        
        result = self.agent.generate(
            scene_description=description,
            bible=bible,
            characters=characters,
            word_count=word_count,
        )
        
        return result.text
