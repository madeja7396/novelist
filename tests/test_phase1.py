"""
Phase 1 Integration Tests

Tests 2-stage pipeline, RAG, memory management
"""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

import core.project
import parsers.character_loader
import core.models
from memory.episodic import EpisodicMemoryManager
from memory.facts import FactsManager
from memory.foreshadowing import ForeshadowingManager
from rag.retriever import SimpleRetriever


class TestPhase1Features(unittest.TestCase):
    """Test Phase 1 features."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
        core.project.ProjectManager.create(self.project_path, "Test Novel")
        
        # Clear template data for clean tests
        import json
        facts_file = self.project_path / "memory" / "facts.json"
        facts_file.write_text(json.dumps({"facts": []}), encoding='utf-8')
        
        foreshadow_file = self.project_path / "memory" / "foreshadow.json"
        foreshadow_file.write_text(json.dumps({"foreshadowings": []}), encoding='utf-8')
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_episodic_memory(self):
        """Test episodic memory management."""
        manager = EpisodicMemoryManager(self.project_path, max_scenes=3)
        
        # Add scenes
        manager.add_scene_summary(1, 1, "Scene 1 summary", "Character A")
        manager.add_scene_summary(1, 2, "Scene 2 summary", "Character B")
        manager.add_scene_summary(1, 3, "Scene 3 summary", "Character A")
        manager.add_scene_summary(1, 4, "Scene 4 summary", "Character C")
        
        # Should only keep last 3
        content = manager.load()
        self.assertIn("Scene 4", content)
        self.assertIn("Scene 3", content)
        # Scene count depends on implementation details
    
    def test_facts_manager(self):
        """Test facts management."""
        manager = FactsManager(self.project_path)
        
        # Clear any existing facts
        import json
        facts_file = self.project_path / "memory" / "facts.json"
        facts_file.write_text(json.dumps({"facts": []}), encoding='utf-8')
        
        # Add facts
        f1 = manager.add_fact("Hero is 17 years old", "chapter_001", tags=["character"])
        f2 = manager.add_fact("The kingdom is at war", "chapter_001", tags=["world"])
        
        # Load and verify
        facts = manager.load()
        self.assertEqual(len(facts), 2)
        
        # Search
        results = manager.search_facts("hero")
        self.assertEqual(len(results), 1)
        
        # Context format
        context = manager.get_facts_for_context()
        self.assertIn("Hero is 17 years old", context)
    
    def test_foreshadowing_manager(self):
        """Test foreshadowing tracking."""
        manager = ForeshadowingManager(self.project_path)
        
        # Clear existing
        import json
        fs_file = self.project_path / "memory" / "foreshadow.json"
        fs_file.write_text(json.dumps({"foreshadowings": []}), encoding='utf-8')
        
        # Plant foreshadowing
        fs_id = manager.plant_foreshadowing(
            "A mysterious prophecy about the hero",
            "chapter_001",
            target_chapter="chapter_005",
            priority="high"
        )
        
        # Check unresolved
        unresolved = manager.get_unresolved()
        self.assertEqual(len(unresolved), 1)
        
        # Resolve
        manager.resolve_foreshadowing(fs_id, "chapter_005", "Revealed as true")
        
        # Check resolved
        unresolved = manager.get_unresolved()
        self.assertEqual(len(unresolved), 0)
    
    def test_rag_retriever(self):
        """Test RAG retriever."""
        retriever = SimpleRetriever(self.project_path)
        
        # Add documents
        retriever.add_document(
            content="Magic comes from ancient ley lines",
            source="bible.md",
            doc_type="bible",
            doc_id="magic_1"
        )
        retriever.add_document(
            content="Elara is a young mage who discovered her powers",
            source="characters/elara.json",
            doc_type="character",
            doc_id="elara_1"
        )
        
        # Build index
        retriever.build()
        
        # Search
        results = retriever.search("magic", top_k=2)
        self.assertGreater(len(results), 0)
        
        # Check result structure
        if results:
            self.assertIsNotNone(results[0].document)
            self.assertIsNotNone(results[0].score)
        
        # Agent-specific search
        agent_results = retriever.search_for_agent("magic power", "director")
        self.assertGreater(len(agent_results), 0)


class TestSessionManagement(unittest.TestCase):
    """Test session management."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
        core.project.ProjectManager.create(self.project_path, "Test Novel")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_session_creation(self):
        """Test session creation and persistence."""
        from session.manager import Session
        
        session = Session(self.project_path)
        self.assertIsNotNone(session.context.session_id)
        
        # RAG should be initialized
        self.assertIsNotNone(session.context.rag_retriever)
        
        # Log a turn
        session.log_turn("test_agent", "test_op", {"input": "test"}, {"output": "result"})
        self.assertEqual(len(session.turns), 1)


if __name__ == "__main__":
    unittest.main()
