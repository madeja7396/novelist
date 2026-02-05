"""
StyleEditor Agent - Improve prose quality.

Fixes:
- Redundancy
- Repetition
- Tempo/pacing
- Line break rules
- Dialogue attribution

Reference: docs/keikaku.md Section 6.1 - StyleEditor Agent
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from core.models import GenerationResult
from core.config_manager import ConfigManager
from pal.base import ProviderFactory


class StyleEditorAgent:
    """
    Improves prose quality based on style guide.
    
    Can output:
    - Full corrected text
    - Diff/patch format
    - Specific edit instructions
    """
    
    def __init__(self, project_path: Path, provider_name: Optional[str] = None):
        self.project_path = Path(project_path)
        self.config = ConfigManager.load(project_path)
        
        # Provider
        if provider_name is None:
            provider_name = self.config.provider.get("routing", {}).get("editor")
            if provider_name is None:
                provider_name = self.config.provider.get("default", "local_ollama")
        
        provider_config = self.config.provider.get("available", {}).get(provider_name, {})
        provider_type = provider_config.get("type", "ollama")
        self.provider = ProviderFactory.create(provider_type, provider_config)
    
    def edit(
        self,
        text: str,
        issues: Optional[List[Dict]] = None,
        style_rules: Optional[str] = None,
        output_format: str = "full",  # 'full', 'diff', 'instructions'
    ) -> str:
        """
        Edit text to improve quality.
        
        Args:
            text: Text to edit
            issues: Optional list of issues to fix
            style_rules: Style guide to follow
            output_format: Output format
        
        Returns:
            Edited text or diff
        """
        # Build prompt
        prompt = self._build_prompt(text, issues, style_rules, output_format)
        
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self.provider.generate(messages, {
                "temperature": 0.4,
                "max_tokens": len(text) + 500,
            })
            
            return self._clean_output(result, output_format)
        
        except Exception as e:
            # If editing fails, return original
            print(f"[Editor] Editing failed: {e}")
            return text
    
    def _system_prompt(self) -> str:
        """System prompt for editor."""
        return """あなたは熟練した小説編集者です。
与えられた文章を改善し、冗長さ・反復・テンポの問題を修正してください。

改善の指針：
- 冗長な表現を簡潔に
- 同じ語句の過度な反復を削除
- テンポを改善（短い文と長い文のバランス）
- 地の文とセリフのリズムを整える
- 原作の意味・意図は保持する
- メタ的なコメントを含めない

出力は本文のみとし、解説は不要です。"""
    
    def _build_prompt(
        self,
        text: str,
        issues: Optional[List[Dict]],
        style_rules: Optional[str],
        output_format: str,
    ) -> str:
        """Build editing prompt."""
        parts = []
        
        parts.append("## 編集対象の文章")
        parts.append(text)
        parts.append("")
        
        if style_rules:
            parts.append("## スタイルガイド")
            parts.append(style_rules)
            parts.append("")
        
        if issues:
            parts.append("## 修正すべき問題")
            for issue in issues:
                parts.append(f"- [{issue.get('category', 'general')}] {issue.get('description', '')}")
            parts.append("")
        
        parts.append("## 指示")
        if output_format == "full":
            parts.append("文章全体を改善したバージョンを出力してください。")
        elif output_format == "diff":
            parts.append("変更点をdiff形式で示してください。")
        else:
            parts.append("具体的な修正指示を箇条書きで出力してください。")
        
        return '\n'.join(parts)
    
    def _clean_output(self, text: str, output_format: str) -> str:
        """Clean editor output."""
        # Remove markdown code blocks if present
        if "```" in text:
            lines = text.split('\n')
            in_block = False
            cleaned = []
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or not line.strip().startswith("```"):
                    cleaned.append(line)
            text = '\n'.join(cleaned)
        
        return text.strip()
    
    def quick_fix(self, text: str, fix_type: str = "all") -> str:
        """
        Quick fix for common issues.
        
        Args:
            text: Text to fix
            fix_type: 'redundancy', 'repetition', 'tempo', 'all'
        """
        if fix_type == "redundancy":
            return self._fix_redundancy(text)
        elif fix_type == "repetition":
            return self._fix_repetition(text)
        elif fix_type == "tempo":
            return self._fix_tempo(text)
        else:
            # Apply all quick fixes
            text = self._fix_redundancy(text)
            text = self._fix_repetition(text)
            text = self._fix_tempo(text)
            return text
    
    def _fix_redundancy(self, text: str) -> str:
        """Fix redundant expressions (rule-based)."""
        # Common redundant patterns in Japanese
        replacements = [
            (r'非常に\s*大きい', '巨大な'),
            (r'完全に\s*同じ', '同一の'),
            (r'独自の\s*特有の', '独自の'),
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _fix_repetition(self, text: str) -> str:
        """Fix word repetition (rule-based)."""
        # Detect immediate repetition
        # e.g., "走る。走る。" -> "走る。"
        text = re.sub(r'([\u4e00-\u9fa5]{2,5})[。！？]\s*\1[。！？]', r'\1。', text)
        
        return text
    
    def _fix_tempo(self, text: str) -> str:
        """Fix pacing (rule-based)."""
        # Add paragraph breaks for dialogue-heavy sections
        lines = text.split('\n')
        result = []
        
        dialogue_count = 0
        for line in lines:
            if '「' in line:
                dialogue_count += 1
                if dialogue_count >= 3:
                    result.append('')  # Add paragraph break
                    dialogue_count = 0
            else:
                dialogue_count = 0
            result.append(line)
        
        return '\n'.join(result)


class SimpleEditor:
    """Simplified editor interface."""
    
    def __init__(self, project_path: Path):
        self.agent = StyleEditorAgent(project_path)
    
    def improve(self, text: str) -> str:
        """Quick improvement."""
        return self.agent.edit(text, use_llm=True)
    
    def fix_issues(self, text: str, issues: List[Dict]) -> str:
        """Fix specific issues."""
        return self.agent.edit(text, issues=issues, use_llm=True)
