#!/usr/bin/env python3
"""
Run regression tests for novelist project
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from metrics import MetricsCalculator, format_metrics


# Test case definitions
TEST_CASES = {
    "F1": {"name": "Magic System Introduction", "genre": "fantasy", "difficulty": "easy"},
    "F2": {"name": "Dungeon Exploration", "genre": "fantasy", "difficulty": "medium"},
    "F3": {"name": "Royal Court Intrigue", "genre": "fantasy", "difficulty": "hard"},
    "F4": {"name": "Monster Encounter", "genre": "fantasy", "difficulty": "easy"},
    "F5": {"name": "Prophecy Revelation", "genre": "fantasy", "difficulty": "hard"},
    "SF1": {"name": "Space Station Routine", "genre": "sci-fi", "difficulty": "easy"},
    "SF2": {"name": "First Contact", "genre": "sci-fi", "difficulty": "medium"},
    "SF3": {"name": "Cyberpunk Chase", "genre": "sci-fi", "difficulty": "medium"},
    "SF4": {"name": "AI Ethics Debate", "genre": "sci-fi", "difficulty": "hard"},
    "SF5": {"name": "Time Paradox", "genre": "sci-fi", "difficulty": "hard"},
    "M1": {"name": "Coffee Shop Reunion", "genre": "modern", "difficulty": "easy"},
    "M2": {"name": "Family Conflict", "genre": "modern", "difficulty": "medium"},
    "M3": {"name": "Workplace Drama", "genre": "modern", "difficulty": "medium"},
    "M4": {"name": "Interior Monologue", "genre": "literary", "difficulty": "hard"},
    "M5": {"name": "Epistolary Format", "genre": "literary", "difficulty": "hard"},
    "S1": {"name": "Long Context", "genre": "stress", "difficulty": "hard"},
    "S2": {"name": "Many Characters", "genre": "stress", "difficulty": "hard"},
    "S3": {"name": "Style Switch", "genre": "stress", "difficulty": "hard"},
    "S4": {"name": "Foreshadowing Payoff", "genre": "stress", "difficulty": "hard"},
    "S5": {"name": "Minimal Prompt", "genre": "stress", "difficulty": "medium"},
}


class TestRunner:
    """Run regression tests and collect results"""
    
    def __init__(self, provider: str = "default"):
        self.provider = provider
        self.results: List[Dict] = []
        self.start_time: Optional[float] = None
        
    def run_test(self, test_id: str, project_path: Path = Path(".")) -> Dict:
        """Run a single test case"""
        test_case = TEST_CASES.get(test_id)
        if not test_case:
            return {"id": test_id, "status": "error", "error": "Unknown test ID"}
        
        print(f"\nRunning test {test_id}: {test_case['name']}...")
        
        start = time.time()
        
        # Load test case spec
        spec = self._load_test_spec(test_id)
        
        # Run generation (placeholder - integrate with actual API)
        generated = self._generate(spec, project_path)
        
        # Calculate metrics
        calc = MetricsCalculator(generated)
        metrics = calc.calculate_all()
        
        # Evaluate against thresholds
        status = "passed"
        issues = []
        
        if metrics['meta_speech_rate'] > 0.01:
            status = "failed" if test_case['difficulty'] != 'hard' else "warning"
            issues.append(f"Meta-speech rate {metrics['meta_speech_rate']:.2%} exceeds 1%")
        
        if metrics['repetition_rate'] > 0.05:
            status = "failed" if test_case['difficulty'] != 'hard' else "warning"
            issues.append(f"Repetition rate {metrics['repetition_rate']:.2%} exceeds 5%")
        
        duration = int((time.time() - start) * 1000)
        
        result = {
            "id": test_id,
            "name": test_case['name'],
            "genre": test_case['genre'],
            "difficulty": test_case['difficulty'],
            "status": status,
            "metrics": metrics,
            "issues": issues,
            "duration_ms": duration,
            "timestamp": datetime.now().isoformat(),
        }
        
        print(f"  Status: {status}")
        if issues:
            for issue in issues:
                print(f"  - {issue}")
        
        return result
    
    def _load_test_spec(self, test_id: str) -> Dict:
        """Load test case specification"""
        # Load from references/test_cases.md (parsed)
        # Simplified: return minimal spec
        return {
            "id": test_id,
            "prompt": f"Test case {test_id}",
        }
    
    def _generate(self, spec: Dict, project_path: Path) -> str:
        """Generate text using the novelist system"""
        # Placeholder - integrate with actual implementation
        # This should call the actual Writer/Dir/ector pipeline
        return "Generated text placeholder"
    
    def run_all(self) -> Dict:
        """Run all 20 tests"""
        self.start_time = time.time()
        
        for test_id in TEST_CASES.keys():
            result = self.run_test(test_id)
            self.results.append(result)
        
        return self._summarize()
    
    def run_genre(self, genre: str) -> Dict:
        """Run tests for a specific genre"""
        self.start_time = time.time()
        
        for test_id, spec in TEST_CASES.items():
            if spec['genre'] == genre:
                result = self.run_test(test_id)
                self.results.append(result)
        
        return self._summarize()
    
    def _summarize(self) -> Dict:
        """Generate summary report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        warnings = sum(1 for r in self.results if r['status'] == 'warning')
        
        total_duration = int((time.time() - self.start_time) * 1000) if self.start_time else 0
        
        # Get git version
        version = self._get_git_version()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "provider": self.provider,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "duration_ms": total_duration,
            },
            "results": self.results,
        }
    
    def _get_git_version(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    def save_report(self, path: Path):
        """Save report to file"""
        report = self._summarize()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport saved to: {path}")


def compare_reports(old_path: Path, new_path: Path):
    """Compare two test reports"""
    old = json.loads(old_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    
    print("\n" + "=" * 60)
    print("Comparison Report")
    print("=" * 60)
    print(f"Old: {old['version']} ({old['timestamp'][:10]})")
    print(f"New: {new['version']} ({new['timestamp'][:10]})")
    
    old_summary = old['summary']
    new_summary = new['summary']
    
    print(f"\nPass rate: {old_summary['passed']}/{old_summary['total']} → "
          f"{new_summary['passed']}/{new_summary['total']}")
    
    # Find changes
    old_results = {r['id']: r for r in old['results']}
    new_results = {r['id']: r for r in new['results']}
    
    improvements = []
    regressions = []
    
    for test_id in old_results:
        old_status = old_results[test_id]['status']
        new_status = new_results.get(test_id, {}).get('status', 'missing')
        
        if old_status != 'passed' and new_status == 'passed':
            improvements.append(test_id)
        elif old_status == 'passed' and new_status != 'passed':
            regressions.append(test_id)
    
    if improvements:
        print(f"\n✓ Improvements: {', '.join(improvements)}")
    if regressions:
        print(f"\n✗ Regressions: {', '.join(regressions)}")
    
    if not improvements and not regressions:
        print("\n→ No significant changes")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run regression tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", help="Run specific test ID")
    parser.add_argument("--genre", help="Run tests for genre (fantasy, sci-fi, modern, literary, stress)")
    parser.add_argument("--provider", default="default", help="Provider to use")
    parser.add_argument("--output", help="Save report to file")
    parser.add_argument("--compare", help="Compare with previous report")
    
    args = parser.parse_args()
    
    runner = TestRunner(provider=args.provider)
    
    if args.compare:
        compare_reports(Path(args.compare), Path(args.output or "runs/latest.json"))
        return
    
    if args.test:
        result = runner.run_test(args.test)
        print("\n" + format_metrics(result['metrics']))
    elif args.genre:
        report = runner.run_genre(args.genre)
        print(f"\n{report['summary']['passed']}/{report['summary']['total']} tests passed")
    elif args.all:
        report = runner.run_all()
        s = report['summary']
        print(f"\n{s['passed']}/{s['total']} passed, {s['failed']} failed, {s['warnings']} warnings")
        print(f"Duration: {s['duration_ms']}ms")
    else:
        parser.print_help()
        return
    
    if args.output:
        runner.save_report(Path(args.output))


if __name__ == "__main__":
    main()
