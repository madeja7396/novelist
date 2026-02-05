"""
Phase 2 Integration Tests

Tests cloud providers, swarm pipeline, revision loop
"""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

# Import providers to register them
import pal.ollama_provider
import pal.openai_provider
import pal.anthropic_provider

import core.project
from pal.base import ProviderFactory
from pal.router import ProviderRouter, CostTracker, TokenEstimator
from core.logger import ExecutionLogger


class TestCloudProviders(unittest.TestCase):
    """Test cloud provider configuration (without API calls)."""
    
    def test_provider_factory_registration(self):
        """Test that providers are registered."""
        providers = ProviderFactory.list_providers()
        self.assertIn("ollama", providers)
        self.assertIn("openai", providers)
        self.assertIn("anthropic", providers)
    
    def test_token_estimator(self):
        """Test token estimation."""
        estimator = TokenEstimator()
        
        # English
        english = "This is a test sentence."
        tokens = estimator.estimate(english)
        self.assertGreater(tokens, 0)
        
        # Japanese
        japanese = "これはテスト文章です。"
        tokens = estimator.estimate(japanese)
        self.assertGreater(tokens, 0)
        
        # Messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        tokens = estimator.estimate_messages(messages)
        self.assertGreater(tokens, 0)


class TestCostTracker(unittest.TestCase):
    """Test cost tracking."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
        core.project.ProjectManager.create(self.project_path, "Test Novel")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_cost_tracking(self):
        """Test cost logging."""
        tracker = CostTracker(self.project_path)
        
        # Log some usage
        tracker.log_usage("director", "openai", "gpt-4", 1000, 500, 0.05, 2000)
        tracker.log_usage("writer", "openai", "gpt-4", 2000, 1000, 0.10, 3000)
        tracker.log_usage("checker", "ollama", "qwen3", 500, 200, None, 1000)
        
        # Get summary
        summary = tracker.get_summary()
        self.assertEqual(summary["total_requests"], 3)
        self.assertEqual(summary["total_cost"], 0.15)
        self.assertEqual(summary["total_tokens"], 5200)
        
        # By agent
        self.assertIn("director", summary["by_agent"])
        self.assertIn("writer", summary["by_agent"])


class TestExecutionLogger(unittest.TestCase):
    """Test execution logging."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
        core.project.ProjectManager.create(self.project_path, "Test Novel")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_logging(self):
        """Test execution logging."""
        logger = ExecutionLogger(self.project_path)
        
        # Log some entries
        logger.log(
            agent="director",
            operation="design_scene",
            prompt="Design a scene...",
            output='{"scene": 1}',
            metrics={"total_tokens": 1000, "duration_ms": 2000},
        )
        
        logger.log(
            agent="writer",
            operation="generate",
            prompt="Write prose...",
            output="Once upon a time...",
            metrics={"total_tokens": 2000, "duration_ms": 3000},
        )
        
        logger.flush()
        
        # Check stats
        stats = logger.get_stats()
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["total_tokens"], 3000)
        self.assertEqual(stats["total_time_ms"], 5000)


class TestProviderRouter(unittest.TestCase):
    """Test provider routing."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "test_novel"
        core.project.ProjectManager.create(self.project_path, "Test Novel")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_router_creation(self):
        """Test router initialization."""
        router = ProviderRouter(self.project_path)
        self.assertIsNotNone(router)
        
        # Check providers info
        providers = router.get_all_providers()
        # Should have at least local_ollama
        self.assertIn("local_ollama", providers)


if __name__ == "__main__":
    unittest.main()
