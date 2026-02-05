#!/usr/bin/env python3
"""
Project Roadmap Manager for Novelist
設計書(keikaku.md)のロードマップに基づく進捗管理スクリプト

本スクリプトは、Phase 0/1/2のタスク進捗を追跡し、次に取り組むべきタスクを提示します。
進捗データは progress.json に保存されます。

使用例:
    # 現在の進捗を表示
    python roadmap.py status
    
    # 次にやるべきタスクを表示
    python roadmap.py next
    
    # タスクを完了としてマーク
    python roadmap.py complete "Project Structure Setup"

設計書参照:
    - Phase 0: セクション11（2-3日）
    - Phase 1: セクション11（+3-5日）
    - Phase 2: セクション11（+1-2週間）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# デフォルトのタスクリスト（設計書セクション11準拠）
# Phase 0: 基盤構築, Phase 1: 2段生成+記憶, Phase 2: Swarm+多プロバイダ
DEFAULT_TASKS = [
    # Phase 0: Skeleton (2-3 days)
    # 目標: 基本的な機能構造でシーン生成が可能になること
    {"id": "P0-01", "phase": 0, "name": "Project Structure Setup", "category": "infrastructure", "status": "pending"},
    {"id": "P0-02", "phase": 0, "name": "Bible Parser", "category": "infrastructure", "status": "pending"},
    {"id": "P0-03", "phase": 0, "name": "Character Loader", "category": "infrastructure", "status": "pending"},
    {"id": "P0-04", "phase": 0, "name": "Local Provider (Ollama)", "category": "pal", "status": "pending"},
    {"id": "P0-05", "phase": 0, "name": "Writer Agent (Basic)", "category": "agent", "status": "pending"},
    {"id": "P0-06", "phase": 0, "name": "CLI Interface", "category": "ui", "status": "pending"},
    {"id": "P0-07", "phase": 0, "name": "Integration Test", "category": "testing", "status": "pending"},
    
    # Phase 1: 2-Stage & Memory (+3-5 days)
    # 目標: Director→Writerパイプラインと記憶管理の実装
    {"id": "P1-01", "phase": 1, "name": "SceneSpec Schema", "category": "infrastructure", "status": "pending"},
    {"id": "P1-02", "phase": 1, "name": "Director Agent", "category": "agent", "status": "pending"},
    {"id": "P1-03", "phase": 1, "name": "Memory: Episodic", "category": "memory", "status": "pending"},
    {"id": "P1-04", "phase": 1, "name": "Memory: Facts", "category": "memory", "status": "pending"},
    {"id": "P1-05", "phase": 1, "name": "Memory: Foreshadowing", "category": "memory", "status": "pending"},
    {"id": "P1-06", "phase": 1, "name": "Writer Agent (SceneSpec)", "category": "agent", "status": "pending"},
    {"id": "P1-07", "phase": 1, "name": "Prompt Assembler", "category": "infrastructure", "status": "pending"},
    {"id": "P1-08", "phase": 1, "name": "2-Stage Pipeline", "category": "infrastructure", "status": "pending"},
    {"id": "P1-09", "phase": 1, "name": "Committer Agent (Basic)", "category": "agent", "status": "pending"},
    {"id": "P1-10", "phase": 1, "name": "Regression Test Suite", "category": "testing", "status": "pending"},
    {"id": "P1-11", "phase": 1, "name": "Metrics Calculator", "category": "testing", "status": "pending"},
    {"id": "P1-12", "phase": 1, "name": "Test Runner", "category": "testing", "status": "pending"},
    {"id": "P1-13", "phase": 1, "name": "ICL Examples", "category": "infrastructure", "status": "pending"},
    {"id": "P1-14", "phase": 1, "name": "Web UI (Basic)", "category": "ui", "status": "pending"},
    {"id": "P1-15", "phase": 1, "name": "Phase 1 Integration", "category": "testing", "status": "pending"},
    
    # Phase 2: Swarm & Multi-Provider (+1-2 weeks)
    # 目標: 完全なAgent SwarmとProvider抽象化
    {"id": "P2-01", "phase": 2, "name": "PAL Interface Definition", "category": "pal", "status": "pending"},
    {"id": "P2-02", "phase": 2, "name": "Cloud Provider (OpenAI)", "category": "pal", "status": "pending"},
    {"id": "P2-03", "phase": 2, "name": "Cloud Provider (Anthropic)", "category": "pal", "status": "pending"},
    {"id": "P2-04", "phase": 2, "name": "Provider Routing", "category": "pal", "status": "pending"},
    {"id": "P2-05", "phase": 2, "name": "ContinuityChecker Agent", "category": "agent", "status": "pending"},
    {"id": "P2-06", "phase": 2, "name": "StyleEditor Agent", "category": "agent", "status": "pending"},
    {"id": "P2-07", "phase": 2, "name": "Committer Agent (Full)", "category": "agent", "status": "pending"},
    {"id": "P2-08", "phase": 2, "name": "Revision Loop", "category": "infrastructure", "status": "pending"},
    {"id": "P2-09", "phase": 2, "name": "Token/Cost Tracking", "category": "infrastructure", "status": "pending"},
    {"id": "P2-10", "phase": 2, "name": "Execution Log", "category": "infrastructure", "status": "pending"},
    {"id": "P2-11", "phase": 2, "name": "Web UI (Enhanced)", "category": "ui", "status": "pending"},
    {"id": "P2-12", "phase": 2, "name": "Security Implementation", "category": "infrastructure", "status": "pending"},
    {"id": "P2-13", "phase": 2, "name": "Export/Import", "category": "infrastructure", "status": "pending"},
    {"id": "P2-14", "phase": 2, "name": "Performance Optimization", "category": "infrastructure", "status": "pending"},
    {"id": "P2-15", "phase": 2, "name": "Phase 2 Integration", "category": "testing", "status": "pending"},
]


class RoadmapManager:
    """
    ロードマップ進捗管理クラス
    
    タスクの読み込み、更新、進捗計算を行います。
    進捗データはJSONファイルに永続化されます。
    """
    
    # 進捗ファイルのパス
    PROGRESS_FILE = Path(__file__).parent.parent / "progress.json"
    
    # Phase表示名
    PHASE_NAMES = {
        0: "Phase 0: Skeleton",
        1: "Phase 1: 2-Stage & Memory", 
        2: "Phase 2: Swarm & Multi-Provider",
    }
    
    def __init__(self):
        """初期化。進捗ファイルが存在すれば読み込み、なければデフォルトを作成。"""
        self.tasks: List[Dict] = []
        self.load()
    
    def load(self):
        """
        進捗ファイルからデータを読み込み
        
        ファイルが存在しない場合はデフォルトタスクを作成して保存します。
        """
        if self.PROGRESS_FILE.exists():
            data = json.loads(self.PROGRESS_FILE.read_text(encoding="utf-8"))
            self.tasks = data.get("tasks", [])
        else:
            self.tasks = DEFAULT_TASKS.copy()
            self.save()
    
    def save(self):
        """
        現在の進捗をファイルに保存
        
        JSON形式で整形して保存します。
        """
        data = {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "tasks": self.tasks,
        }
        self.PROGRESS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), 
            encoding="utf-8"
        )
    
    def get_current_phase(self) -> int:
        """
        現在のPhaseを判定
        
        完了していないタスクがある最初のPhaseを返します。
        全て完了していればPhase 2を返します。
        
        Returns:
            int: 現在のPhase番号（0, 1, or 2）
        """
        for phase in [0, 1, 2]:
            phase_tasks = [t for t in self.tasks if t["phase"] == phase]
            incomplete = [t for t in phase_tasks if t["status"] != "completed"]
            if incomplete:
                return phase
        return 2  # 全完了
    
    def get_tasks(
        self, 
        phase: Optional[int] = None, 
        category: Optional[str] = None, 
        status: Optional[str] = None, 
        incomplete: bool = False
    ) -> List[Dict]:
        """
        タスクをフィルタリングして取得
        
        Args:
            phase: 特定のPhase（0, 1, 2）
            category: カテゴリ（infrastructure, agent, pal等）
            status: 特定のステータス
            incomplete: 未完了のみ取得
        
        Returns:
            List[Dict]: フィルタリングされたタスクリスト
        """
        tasks = self.tasks
        
        if phase is not None:
            tasks = [t for t in tasks if t["phase"] == phase]
        
        if category:
            tasks = [t for t in tasks if t["category"] == category]
        
        if incomplete:
            tasks = [t for t in tasks if t["status"] != "completed"]
        elif status:
            tasks = [t for t in tasks if t["status"] == status]
        
        return tasks
    
    def get_task(self, name: str) -> Optional[Dict]:
        """
        名前またはIDでタスクを検索
        
        Args:
            name: タスク名またはID
        
        Returns:
            Optional[Dict]: 見つかったタスク、またはNone
        """
        for task in self.tasks:
            if task["id"].lower() == name.lower() or task["name"].lower() == name.lower():
                return task
        return None
    
    def update_status(self, name: str, status: str, reason: str = None):
        """
        タスクのステータスを更新
        
        Args:
            name: タスク名またはID
            status: 新しいステータス（pending/in_progress/completed/blocked）
            reason: blocked時の理由（オプション）
        
        Returns:
            bool: 更新が成功したか
        """
        task = self.get_task(name)
        if not task:
            print(f"Task not found: {name}")
            return False
        
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        
        if status == "completed":
            task["completed_at"] = datetime.now().isoformat()
        
        if reason:
            task["reason"] = reason
        
        self.save()
        print(f"Updated {task['id']}: {task['name']} → {status}")
        return True
    
    def get_progress(self, phase: Optional[int] = None) -> Dict:
        """
        進捗統計を計算
        
        Args:
            phase: 特定のPhase（Noneなら全Phase）
        
        Returns:
            Dict: 進捗統計
                - total: 総タスク数
                - completed: 完了数
                - in_progress: 進行中数
                - blocked: ブロック数
                - pending: 未着手数
                - percent: 完了率
        """
        if phase is not None:
            tasks = [t for t in self.tasks if t["phase"] == phase]
        else:
            tasks = self.tasks
        
        total = len(tasks)
        completed = len([t for t in tasks if t["status"] == "completed"])
        in_progress = len([t for t in tasks if t["status"] == "in_progress"])
        blocked = len([t for t in tasks if t["status"] == "blocked"])
        pending = total - completed - in_progress - blocked
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "pending": pending,
            "percent": (completed / total * 100) if total > 0 else 0,
        }
    
    def estimate_remaining(self) -> str:
        """
        残り工数を見積もり
        
        Phaseごとの残りタスク数と推定日数を計算します。
        1タスク=0.7日×20%バッファを想定。
        
        Returns:
            str: 整形された見積もり文字列
        """
        lines = []
        
        for phase in [0, 1, 2]:
            progress = self.get_progress(phase)
            name = self.PHASE_NAMES[phase]
            
            if progress["percent"] == 100:
                lines.append(f"{name}: Complete ✓")
            else:
                remaining = progress["total"] - progress["completed"]
                # 1タスク0.7日 + 20%バッファ
                days = remaining * 0.7 * 1.2
                lines.append(f"{name}: {remaining} tasks (~{days:.0f} days)")
        
        return "\n".join(lines)
    
    def get_next_tasks(self, count: int = 3) -> List[Dict]:
        """
        次に取り組むべきタスクを取得
        
        優先順位：
        1. 現在のPhaseの未完了タスク
        2. infrastructure → pal → memory → agent → ui → testing の順
        3. ID順
        
        Args:
            count: 取得するタスク数
        
        Returns:
            List[Dict]: 優先順にソートされたタスクリスト
        """
        current_phase = self.get_current_phase()
        
        # 現在のPhaseの未完了タスクを取得
        tasks = self.get_tasks(phase=current_phase, incomplete=True)
        
        # 優先度でソート（infrastructure優先）
        priority = {
            "infrastructure": 0, 
            "pal": 1, 
            "memory": 2, 
            "agent": 3, 
            "ui": 4, 
            "testing": 5
        }
        tasks.sort(key=lambda t: (priority.get(t["category"], 9), t["id"]))
        
        return tasks[:count]


def print_status(manager: RoadmapManager):
    """
    現在の進捗を整形して表示
    
    Args:
        manager: RoadmapManagerインスタンス
    """
    current = manager.get_current_phase()
    print(f"Current Phase: {manager.PHASE_NAMES[current]}")
    
    # Phaseごとのプログレスバー
    for phase in [0, 1, 2]:
        p = manager.get_progress(phase)
        bar = "█" * int(p["percent"] / 10) + "░" * (10 - int(p["percent"] / 10))
        print(f"  Phase {phase}: [{bar}] {p['completed']}/{p['total']} ({p['percent']:.0f}%)")
    
    # 残り工数見積もり
    print(f"\n{manager.estimate_remaining()}")


def main():
    """メインエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage novelist project development roadmap"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # status コマンド
    subparsers.add_parser("status", help="Show current status")
    
    # phase コマンド
    subparsers.add_parser("phase", help="Show current phase")
    
    # show コマンド
    show_parser = subparsers.add_parser("show", help="Show full roadmap")
    show_parser.add_argument("--phase", type=int, choices=[0, 1, 2])
    
    # tasks コマンド
    tasks_parser = subparsers.add_parser("tasks", help="List tasks")
    tasks_parser.add_argument("--phase", type=int, choices=[0, 1, 2])
    tasks_parser.add_argument("--category")
    tasks_parser.add_argument("--incomplete", action="store_true")
    
    # next コマンド
    next_parser = subparsers.add_parser("next", help="Show next tasks")
    next_parser.add_argument("--count", type=int, default=3)
    next_parser.add_argument("--verbose", action="store_true")
    
    # complete コマンド
    complete_parser = subparsers.add_parser("complete", help="Mark task complete")
    complete_parser.add_argument("task", help="Task name or ID")
    
    # start コマンド
    start_parser = subparsers.add_parser("start", help="Mark task in-progress")
    start_parser.add_argument("task", help="Task name or ID")
    
    # block コマンド
    block_parser = subparsers.add_parser("block", help="Mark task blocked")
    block_parser.add_argument("task", help="Task name or ID")
    block_parser.add_argument("--reason", help="Block reason")
    
    # reset コマンド
    reset_parser = subparsers.add_parser("reset", help="Reset task to pending")
    reset_parser.add_argument("task", help="Task name or ID")
    
    # estimate コマンド
    subparsers.add_parser("estimate", help="Estimate remaining work")
    
    args = parser.parse_args()
    
    manager = RoadmapManager()
    
    # コマンド振り分け
    if args.command == "status":
        print_status(manager)
    
    elif args.command == "phase":
        current = manager.get_current_phase()
        p = manager.get_progress(current)
        remaining = p["total"] - p["completed"]
        print(f"Current Phase: {manager.PHASE_NAMES[current]}")
        print(f"Progress: {p['completed']}/{p['total']} tasks ({p['percent']:.0f}%)")
        print(f"Estimated remaining: {remaining * 0.8:.0f} days")
    
    elif args.command == "show":
        # ロードマップ全体表示
        for phase in [0, 1, 2]:
            if args.phase is not None and phase != args.phase:
                continue
            print(f"\n{'='*60}")
            print(f"{manager.PHASE_NAMES[phase]}")
            print("="*60)
            for task in manager.get_tasks(phase=phase):
                status_icon = {
                    "completed": "✓",
                    "in_progress": "▶",
                    "blocked": "✗",
                    "pending": "○",
                }.get(task["status"], "?")
                print(f"  {status_icon} [{task['id']}] {task['name']} ({task['category']})")
    
    elif args.command == "tasks":
        tasks = manager.get_tasks(
            phase=args.phase,
            category=args.category,
            incomplete=args.incomplete
        )
        for task in tasks:
            print(f"[{task['id']}] {task['name']}")
            print(f"  Status: {task['status']}, Category: {task['category']}")
    
    elif args.command == "next":
        tasks = manager.get_next_tasks(args.count)
        print(f"Next {len(tasks)} tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. [{task['id']}] {task['name']}")
            print(f"   Category: {task['category']}, Phase: {task['phase']}")
            if args.verbose:
                # 詳細表示（必要に応じてreferences/roadmap.mdから読み込み）
                pass
    
    elif args.command == "complete":
        manager.update_status(args.task, "completed")
    
    elif args.command == "start":
        manager.update_status(args.task, "in_progress")
    
    elif args.command == "block":
        manager.update_status(args.task, "blocked", args.reason)
    
    elif args.command == "reset":
        manager.update_status(args.task, "pending")
    
    elif args.command == "estimate":
        print(manager.estimate_remaining())
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
