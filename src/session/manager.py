"""
Session management for agent conversations.

Manages conversation state, context, and RAG retrieval across agent interactions.
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from core.models import SceneSpec, GenerationResult
from rag.retriever import SimpleRetriever, RAGContextBuilder


@dataclass
class SessionContext:
    """Context maintained throughout a session."""
    project_path: Path
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Current story state
    current_chapter: int = 1
    current_scene: int = 1
    active_characters: List[str] = field(default_factory=list)
    
    # Accumulated context
    episode_summary: str = ""  # Running summary
    key_facts: List[str] = field(default_factory=list)  # Important facts this session
    active_foreshadowing: List[str] = field(default_factory=list)
    
    # RAG
    rag_retriever: Optional[SimpleRetriever] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict:
        """Convert to dict for serialization."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'current_chapter': self.current_chapter,
            'current_scene': self.current_scene,
            'active_characters': self.active_characters,
            'episode_summary': self.episode_summary,
            'key_facts': self.key_facts,
            'active_foreshadowing': self.active_foreshadowing,
        }


@dataclass
class AgentTurn:
    """Single agent interaction."""
    agent: str  # Agent name
    operation: str  # What was done
    input_data: Dict = field(default_factory=dict)
    output_data: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = 0
    metadata: Dict = field(default_factory=dict)


class Session:
    """
    A working session for novel generation.
    
    Maintains context across multiple agent calls and provides RAG retrieval.
    """
    
    def __init__(self, project_path: Path, session_id: Optional[str] = None):
        self.project_path = Path(project_path)
        
        # Load or create context
        if session_id:
            self.context = self._load_session(session_id)
        else:
            self.context = SessionContext(project_path=self.project_path)
            self._init_rag()
        
        # Conversation history
        self.turns: List[AgentTurn] = []
        
        # RAG context builder
        self.rag_builder = RAGContextBuilder(self.context.rag_retriever) if self.context.rag_retriever else None
        
        # Ensure runs directory exists
        self.runs_dir = self.project_path / "runs"
        self.runs_dir.mkdir(exist_ok=True)
    
    def _init_rag(self):
        """Initialize RAG retriever."""
        self.context.rag_retriever = SimpleRetriever(self.project_path)
        self.context.rag_retriever.index_project()
    
    def _load_session(self, session_id: str) -> SessionContext:
        """Load session from disk."""
        session_file = self.project_path / ".sessions" / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            ctx = SessionContext(
                project_path=self.project_path,
                **{k: v for k, v in data.items() if k != 'rag_retriever'}
            )
            
            # Re-init RAG
            ctx.rag_retriever = SimpleRetriever(self.project_path)
            return ctx
        
        # Create new if not found
        return SessionContext(project_path=self.project_path, session_id=session_id)
    
    def _save_session(self):
        """Save session to disk."""
        sessions_dir = self.project_path / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        
        session_file = sessions_dir / f"{self.context.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.context.to_dict(), f, ensure_ascii=False, indent=2)
    
    def log_turn(self, agent: str, operation: str, 
                 input_data: Dict = None, output_data: Dict = None,
                 duration_ms: int = 0, metadata: Dict = None):
        """Log an agent turn."""
        turn = AgentTurn(
            agent=agent,
            operation=operation,
            input_data=input_data or {},
            output_data=output_data or {},
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.turns.append(turn)
        
        # Also write to runs file (for persistence)
        self._append_to_runs(turn)
    
    def _append_to_runs(self, turn: AgentTurn):
        """Append turn to runs JSONL file."""
        run_file = self.runs_dir / f"session_{self.context.session_id}.jsonl"
        
        with open(run_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(turn), ensure_ascii=False) + '\n')
    
    def retrieve_context(self, query: str, agent_type: str) -> str:
        """
        Retrieve relevant context for an agent.
        
        Args:
            query: Search query
            agent_type: Type of agent
        
        Returns:
            Formatted context string
        """
        if not self.rag_builder:
            return ""
        
        return self.rag_builder.build_context(query, agent_type)
    
    def update_episode_summary(self, new_content: str):
        """Update running episode summary."""
        # Simple concatenation with limit
        # In production, use summarization
        max_len = 1000
        self.context.episode_summary += f"\n\n[Scene {self.context.current_scene}]\n{new_content[:500]}"
        
        if len(self.context.episode_summary) > max_len:
            # Keep last portion
            self.context.episode_summary = self.context.episode_summary[-max_len:]
        
        self._save_session()
    
    def add_fact(self, fact: str):
        """Add a key fact discovered this session."""
        self.context.key_facts.append(fact)
        self._save_session()
    
    def increment_scene(self):
        """Move to next scene."""
        self.context.current_scene += 1
        self._save_session()
    
    def get_prompt_context(self) -> Dict[str, str]:
        """
        Get context for prompt assembly.
        
        Returns:
            Dict with keys: bible, characters, facts, recap, rag
        """
        from ..parsers.bible_parser import BibleLoader
        from ..parsers.character_loader import CharacterLoader
        
        context = {}
        
        # Bible
        try:
            bible = BibleLoader.load(self.project_path)
            context['bible'] = bible.raw_content[:2000]  # Truncated
        except Exception:
            context['bible'] = ""
        
        # Characters
        try:
            chars = CharacterLoader.load_all(self.project_path)
            char_texts = [c.format_for_prompt() for c in chars.values()]
            context['characters'] = '\n\n'.join(char_texts)[:1500]
        except Exception:
            context['characters'] = ""
        
        # Facts (from session)
        context['facts'] = '\n'.join(f"- {f}" for f in self.context.key_facts[-10:])
        
        # Recap
        context['recap'] = self.context.episode_summary[-800:]
        
        return context


class SessionManager:
    """Manages multiple sessions."""
    
    @staticmethod
    def list_sessions(project_path: Path) -> List[Dict]:
        """List all sessions for a project."""
        sessions_dir = project_path / ".sessions"
        if not sessions_dir.exists():
            return []
        
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append({
                    'session_id': data.get('session_id'),
                    'created_at': data.get('created_at'),
                    'chapter': data.get('current_chapter', 1),
                    'scene': data.get('current_scene', 1),
                })
            except json.JSONDecodeError:
                continue
        
        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)
    
    @staticmethod
    def delete_session(project_path: Path, session_id: str):
        """Delete a session."""
        sessions_dir = project_path / ".sessions"
        session_file = sessions_dir / f"{session_id}.json"
        
        if session_file.exists():
            session_file.unlink()
        
        # Also delete runs
        run_file = project_path / "runs" / f"session_{session_id}.jsonl"
        if run_file.exists():
            run_file.unlink()
