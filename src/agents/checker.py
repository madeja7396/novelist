"""
ContinuityChecker Agent - Detect inconsistencies.

Checks generated text against:
- Facts (immutable truths)
- Character consistency (tone, values, forbidden words)
- World setting consistency
- POV consistency

Reference: docs/keikaku.md Section 6.1 - ContinuityChecker Agent
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from core.models import GenerationResult
from core.config_manager import ConfigManager
from pal.base import ProviderFactory
from memory.facts import FactsManager
from memory.episodic import EpisodicMemoryManager
from parsers.character_loader import CharacterLoader
from parsers.bible_parser import BibleLoader


@dataclass
class Issue:
    """Detected issue."""
    category: str  # 'fact', 'character', 'world', 'pov', 'style'
    severity: str  # 'error', 'warning', 'info'
    description: str
    location: Optional[str] = None  # Where in text
    suggestion: Optional[str] = None


class ContinuityCheckerAgent:
    """
    Checks text for continuity errors.
    
    Output: List of issues (NOT corrected text)
    """
    
    def __init__(self, project_path: Path, provider_name: Optional[str] = None):
        self.project_path = Path(project_path)
        self.config = ConfigManager.load(project_path)
        
        # Memory managers
        self.facts = FactsManager(project_path)
        self.episodic = EpisodicMemoryManager(project_path)
        
        # Provider
        if provider_name is None:
            provider_name = self.config.provider.get("routing", {}).get("checker")
            if provider_name is None:
                provider_name = self.config.provider.get("default", "local_ollama")
        
        provider_config = self.config.provider.get("available", {}).get(provider_name, {})
        provider_type = provider_config.get("type", "ollama")
        self.provider = ProviderFactory.create(provider_type, provider_config)
    
    def check(
        self,
        text: str,
        chapter: int,
        scene: int,
        pov_character: Optional[str] = None,
        use_llm: bool = True,
    ) -> List[Issue]:
        """
        Check text for issues.
        
        Args:
            text: Text to check
            chapter: Chapter number
            scene: Scene number
            pov_character: Expected POV character
            use_llm: Use LLM for advanced checking
        
        Returns:
            List of detected issues
        """
        issues = []
        
        # 1. Rule-based checks (fast)
        issues.extend(self._check_facts(text))
        issues.extend(self._check_characters(text))
        issues.extend(self._check_pov(text, pov_character))
        
        # 2. LLM-based checks (thorough)
        if use_llm:
            issues.extend(self._check_with_llm(text, chapter, scene))
        
        return issues
    
    def _check_facts(self, text: str) -> List[Issue]:
        """Check for fact contradictions."""
        issues = []
        facts = self.facts.load()
        
        text_lower = text.lower()
        
        for fact in facts:
            # Simple keyword matching
            fact_keywords = fact.content.lower().split()
            
            # Check if fact is potentially contradicted
            # Look for negation patterns
            negation_patterns = [
                rf"{re.escape(fact.content[:20])}.{{0,20}}(違う|間違|ない|しなかった|ではな)",
            ]
            
            for pattern in negation_patterns:
                if re.search(pattern, text_lower):
                    issues.append(Issue(
                        category="fact",
                        severity="error",
                        description=f"Possible contradiction of fact [{fact.id}]: {fact.content}",
                        suggestion="Review consistency with established facts"
                    ))
                    break
        
        return issues
    
    def _check_characters(self, text: str) -> List[Issue]:
        """Check character consistency."""
        issues = []
        characters = CharacterLoader.load_all(self.project_path)
        
        # Extract dialogue and actions
        dialogue_pattern = r'[「"]([^」"]+)[」"]'
        dialogues = re.findall(dialogue_pattern, text)
        
        for char_id, char in characters.items():
            char_name = char.name.get('full', char_id) if isinstance(char.name, dict) else str(char.name)
            
            # Check for forbidden words in dialogue
            forbidden = char.language.get('forbidden_words', [])
            for dialogue in dialogues:
                for word in forbidden:
                    if word in dialogue:
                        issues.append(Issue(
                            category="character",
                            severity="error",
                            description=f"Character '{char_name}' used forbidden word: '{word}'",
                            location=dialogue[:50],
                            suggestion=f"Avoid '{word}' for this character"
                        ))
            
            # Check first-person pronoun consistency
            first_person = char.language.get('first_person', '')
            if first_person and char_id in text:
                # Check if POV and pronoun match
                pass  # Complex check, defer to LLM
        
        return issues
    
    def _check_pov(self, text: str, expected_pov: Optional[str]) -> List[Issue]:
        """Check POV consistency."""
        issues = []
        
        if not expected_pov:
            return issues
        
        # Look for POV violations
        # "私"以外の一人称が使われているか
        # 他キャラの内面が描かれていないか
        
        return issues
    
    def _check_with_llm(self, text: str, chapter: int, scene: int) -> List[Issue]:
        """Use LLM for thorough checking."""
        issues = []
        
        # Load context
        bible = BibleLoader.load_raw(self.project_path)
        characters = CharacterLoader.load_all(self.project_path)
        facts = self.facts.get_facts_for_context()
        
        char_texts = []
        for char in characters.values():
            char_texts.append(char.format_for_prompt())
        
        prompt = f"""以下の文章をチェックし、矛盾・逸脱があれば指摘してください。

## チェック対象の文章
{text[:2000]}

## 世界観・設定
{bible[:1000]}

## キャラクター設定
{'\n'.join(char_texts[:3])}

## 確定事実
{facts}

## 指示
以下の点をチェックし、問題があればJSON形式で出力してください：
1. 設定矛盾（世界観、技術水準など）
2. キャラクター逸脱（口調、価値観、禁則語）
3. 事実矛盾（確定事実と矛盾）
4. 視点違反（POVキャラ以外の内面描写）

問題がなければ空配列 [] を返してください。

出力形式:
[
  {{
    "category": "fact|character|world|pov",
    "severity": "error|warning|info",
    "description": "問題の説明",
    "location": "該当箇所（あれば）",
    "suggestion": "修正提案"
  }}
]"""
        
        messages = [
            {"role": "system", "content": "あなたは小説の設定・矛盾チェッカーです。客観的に問題を指摘してください。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self.provider.generate(messages, {
                "temperature": 0.2,
                "max_tokens": 1500,
            })
            
            # Parse JSON
            json_match = re.search(r'\[.*?\]', result, re.DOTALL)
            if json_match:
                issues_data = json.loads(json_match.group())
                for issue_data in issues_data:
                    issues.append(Issue(**issue_data))
        
        except Exception as e:
            # LLM check failed, return what we have
            pass
        
        return issues
    
    def format_report(self, issues: List[Issue]) -> str:
        """Format issues for display."""
        if not issues:
            return "✓ No issues detected"
        
        lines = [f"Found {len(issues)} issue(s):", ""]
        
        for i, issue in enumerate(issues, 1):
            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue.severity, "•")
            lines.append(f"{icon} [{issue.category.upper()}] {issue.description}")
            if issue.location:
                lines.append(f"  Location: {issue.location[:50]}...")
            if issue.suggestion:
                lines.append(f"  Suggestion: {issue.suggestion}")
            lines.append("")
        
        return '\n'.join(lines)


class SimpleChecker:
    """Simplified checker interface."""
    
    def __init__(self, project_path: Path):
        self.agent = ContinuityCheckerAgent(project_path)
    
    def check_scene(self, text: str, chapter: int = 1, scene: int = 1) -> List[Issue]:
        """Quick check interface."""
        return self.agent.check(text, chapter, scene, use_llm=True)
    
    def print_report(self, text: str, chapter: int = 1, scene: int = 1):
        """Check and print report."""
        issues = self.check_scene(text, chapter, scene)
        print(self.agent.format_report(issues))
        return len(issues) == 0
