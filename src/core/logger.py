"""
Execution logger for detailed run tracking.

Logs all prompts, outputs, metrics, and errors.
Reference: docs/keikaku.md Section 2.5 - Execution Log
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExecutionLogger:
    """
    Detailed execution logging.
    
    Logs to JSONL format for easy analysis.
    Each line is a separate log entry.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.runs_dir = project_path / "runs"
        self.runs_dir.mkdir(exist_ok=True)
        
        # Current run file
        self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.log_file = self.runs_dir / f"{self.run_id}.jsonl"
        
        # In-memory buffer
        self.buffer: List[Dict] = []
        self.buffer_size = 10  # Flush every N entries
    
    def log(
        self,
        agent: str,
        operation: str,
        prompt: Optional[str] = None,
        output: Optional[str] = None,
        metrics: Optional[Dict] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Log an execution step.
        
        Args:
            agent: Agent name (director, writer, etc.)
            operation: Operation type (generate, check, etc.)
            prompt: Input prompt (optional, can be large)
            output: Generated output (optional, can be large)
            metrics: Metrics dict (tokens, cost, time, etc.)
            error: Error message if failed
            metadata: Additional metadata
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "agent": agent,
            "operation": operation,
            "metrics": metrics or {},
            "metadata": metadata or {},
        }
        
        if prompt is not None:
            entry["prompt_length"] = len(prompt)
            # Truncate if very large
            if len(prompt) > 10000:
                entry["prompt"] = prompt[:5000] + "... [truncated] ..." + prompt[-1000:]
            else:
                entry["prompt"] = prompt
        
        if output is not None:
            entry["output_length"] = len(output)
            if len(output) > 10000:
                entry["output"] = output[:5000] + "... [truncated] ..." + output[-1000:]
            else:
                entry["output"] = output
        
        if error:
            entry["error"] = error
            entry["status"] = "error"
        else:
            entry["status"] = "success"
        
        self.buffer.append(entry)
        
        # Flush if buffer full
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """Write buffer to disk."""
        if not self.buffer:
            return
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            for entry in self.buffer:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        self.buffer = []
    
    def close(self):
        """Close logger and flush remaining entries."""
        self.flush()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_stats(self) -> Dict:
        """Get statistics for current run."""
        self.flush()  # Ensure all written
        
        if not self.log_file.exists():
            return {}
        
        entries = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        if not entries:
            return {}
        
        # Calculate stats
        total_tokens = sum(
            e.get("metrics", {}).get("total_tokens", 0)
            for e in entries
        )
        
        total_cost = sum(
            e.get("metrics", {}).get("cost", 0) or 0
            for e in entries
        )
        
        total_time = sum(
            e.get("metrics", {}).get("duration_ms", 0)
            for e in entries
        )
        
        # By agent
        by_agent = {}
        for e in entries:
            agent = e.get("agent", "unknown")
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "tokens": 0, "errors": 0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["tokens"] += e.get("metrics", {}).get("total_tokens", 0)
            if e.get("status") == "error":
                by_agent[agent]["errors"] += 1
        
        return {
            "run_id": self.run_id,
            "total_entries": len(entries),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "total_time_ms": total_time,
            "by_agent": by_agent,
        }
    
    def print_stats(self):
        """Print run statistics."""
        stats = self.get_stats()
        
        print("=" * 60)
        print(f"Execution Log: {stats.get('run_id', 'N/A')}")
        print("=" * 60)
        print(f"Total Calls: {stats.get('total_entries', 0)}")
        print(f"Total Tokens: {stats.get('total_tokens', 0):,}")
        print(f"Total Cost: ${stats.get('total_cost', 0):.4f}")
        print(f"Total Time: {stats.get('total_time_ms', 0):,}ms")
        print()
        
        by_agent = stats.get("by_agent", {})
        if by_agent:
            print("By Agent:")
            for agent, data in sorted(by_agent.items()):
                error_str = f" ({data['errors']} errors)" if data['errors'] > 0 else ""
                print(f"  {agent:12s}: {data['calls']:3d} calls, "
                      f"{data['tokens']:6,} tokens{error_str}")


class RunAnalyzer:
    """Analyze past runs."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.runs_dir = project_path / "runs"
    
    def list_runs(self) -> List[Dict]:
        """List all runs."""
        if not self.runs_dir.exists():
            return []
        
        runs = []
        for log_file in self.runs_dir.glob("*.jsonl"):
            # Get first entry for metadata
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    entry = json.loads(first_line)
                    
                    runs.append({
                        "run_id": entry.get("run_id", log_file.stem),
                        "timestamp": entry.get("timestamp", ""),
                        "file": str(log_file),
                    })
            except (json.JSONDecodeError, IOError):
                continue
        
        return sorted(runs, key=lambda x: x["timestamp"], reverse=True)
    
    def compare_runs(self, run_id1: str, run_id2: str) -> Dict:
        """Compare two runs."""
        # Load both runs
        run1 = self._load_run(run_id1)
        run2 = self._load_run(run_id2)
        
        # Calculate metrics
        stats1 = self._calc_run_stats(run1)
        stats2 = self._calc_run_stats(run2)
        
        return {
            "run1": stats1,
            "run2": stats2,
            "differences": {
                "token_delta": stats2["total_tokens"] - stats1["total_tokens"],
                "cost_delta": stats2["total_cost"] - stats1["total_cost"],
                "time_delta": stats2["total_time_ms"] - stats1["total_time_ms"],
            }
        }
    
    def _load_run(self, run_id: str) -> List[Dict]:
        """Load run entries."""
        log_file = self.runs_dir / f"{run_id}.jsonl"
        if not log_file.exists():
            # Try finding by prefix
            matches = list(self.runs_dir.glob(f"*{run_id}*.jsonl"))
            if matches:
                log_file = matches[0]
            else:
                return []
        
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return entries
    
    def _calc_run_stats(self, entries: List[Dict]) -> Dict:
        """Calculate stats for run."""
        if not entries:
            return {"total_tokens": 0, "total_cost": 0, "total_time_ms": 0}
        
        return {
            "total_tokens": sum(e.get("metrics", {}).get("total_tokens", 0) for e in entries),
            "total_cost": sum(e.get("metrics", {}).get("cost", 0) or 0 for e in entries),
            "total_time_ms": sum(e.get("metrics", {}).get("duration_ms", 0) for e in entries),
        }
