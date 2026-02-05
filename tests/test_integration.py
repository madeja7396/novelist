"""
Integration test for Phase 0.
Tests end-to-end flow: project creation -> generation
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Setup path - Add src to Python path
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

# Now import modules
import core.models
import core.project
import core.config_manager
import parsers.bible_parser
import parsers.character_loader


class TestPhase0Integration(unittest.TestCase):
    """Phase 0 integration tests."""
    
    def setUp(self):
        """Create temporary project for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
    
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_project_creation(self):
        """Test project structure creation."""
        # Create project
        core.project.ProjectManager.create(self.project_path, "Test Novel")
        
        # Validate structure
        is_valid, issues = core.project.ProjectManager.validate(self.project_path)
        self.assertTrue(is_valid, f"Issues: {issues}")
        
        # Check key files exist
        self.assertTrue((self.project_path / "bible.md").exists())
        self.assertTrue((self.project_path / "config.yaml").exists())
        self.assertTrue((self.project_path / "characters").exists())
        self.assertTrue((self.project_path / "chapters").exists())
        self.assertTrue((self.project_path / "memory" / "facts.json").exists())
    
    def test_bible_loading(self):
        """Test bible parsing."""
        core.project.ProjectManager.create(self.project_path, "Test Novel")
        
        # Load bible
        bible = parsers.bible_parser.BibleLoader.load(self.project_path)
        
        # Should have some content (even if empty dicts)
        self.assertIsNotNone(bible.style_rules)
        self.assertIsNotNone(bible.world_settings)
    
    def test_character_loading(self):
        """Test character loading."""
        core.project.ProjectManager.create(self.project_path, "Test Novel")
        
        # Initially no characters
        chars = parsers.character_loader.CharacterLoader.load_all(self.project_path)
        self.assertEqual(len(chars), 0)
        
        # Add a character
        char = core.models.CharacterCard(
            id="test_char",
            name={"full": "Test Character", "short": "Test"},
            language={
                "first_person": "私",
                "tone": "丁寧",
                "speech_pattern": "敬語",
                "forbidden_words": []
            }
        )
        parsers.character_loader.CharacterLoader.save(char, self.project_path, "test_char.json")
        
        # Reload
        chars = parsers.character_loader.CharacterLoader.load_all(self.project_path)
        self.assertEqual(len(chars), 1)
        self.assertIn("test_char", chars)


class TestProjectStructure(unittest.TestCase):
    """Test SSOT structure validation."""
    
    def test_empty_directory_validation(self):
        """Test validation catches missing files."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            is_valid, issues = core.project.ProjectManager.validate(tmp_path)
            
            self.assertFalse(is_valid)
            self.assertTrue(len(issues) > 0)


if __name__ == "__main__":
    unittest.main()
