#!/usr/bin/env python3
"""
Design Compliance Checker for Novelist Project
設計書(keikaku.md)への準拠を検証するスクリプト

本スクリプトは、novelistプロジェクトの実装が設計書に従っているかを自動検証します。
SSOT構造、PALインターフェース、Agent設定、データスキーマなどをチェックします。

使用例:
    # 全チェック実行
    python check_compliance.py --all
    
    # SSOT構造のみチェック
    python check_compliance.py --ssot
    
    # PAL実装のみチェック
    python check_compliance.py --pal

終了コード:
    0: 全チェック合格
    1: 問題が検出された
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 設計書のパス（プロジェクトルートからの相対パス）
DESIGN_DOC = Path("docs/keikaku.md")
PROJECT_ROOT = Path(".")


class ComplianceChecker:
    """
    設計書準拠チェックのメインクラス
    
    各種検証メソッドを提供し、検出された問題を収集してレポートします。
    """
    
    def __init__(self, project_root: Path = PROJECT_ROOT):
        """
        Args:
            project_root: プロジェクトのルートディレクトリパス
        """
        self.project_root = project_root
        # 問題リスト: [(カテゴリ, メッセージ), ...]
        self.issues: List[Tuple[str, str]] = []
        # 警告リスト（軽微な問題）
        self.warnings: List[Tuple[str, str]] = []
        
    def check_ssot_structure(self) -> bool:
        """
        SSOT(Single Source of Truth)のファイル構造をチェック
        
        設計書セクション3に定義された必須ファイル・ディレクトリの存在を確認します。
        bible.mdの内容も検証します。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        ok = True
        
        # 必須ファイル・ディレクトリ定義
        # key: パス, value: "file"または"dir"
        required = {
            "bible.md": "file",
            "characters": "dir",
            "chapters": "dir",
            "memory": "dir",
            "memory/episodic.md": "file",
            "memory/facts.json": "file",
            "memory/foreshadow.json": "file",
            "runs": "dir",
            "config.yaml": "file"
        }
        
        for path, type_ in required.items():
            full_path = self.project_root / path
            if type_ == "file":
                if not full_path.exists():
                    self.issues.append(("SSOT", f"Missing required file: {path}"))
                    ok = False
                elif path == "bible.md":
                    # bible.mdの内容チェック
                    content = full_path.read_text(encoding="utf-8")
                    # Style Bibleセクションの存在確認
                    if "Style Bible" not in content and "文体規約" not in content:
                        self.issues.append(("SSOT", "bible.md missing Style Bible section"))
                    # World Bibleセクションの存在確認
                    if "World Bible" not in content and "世界観" not in content:
                        self.issues.append(("SSOT", "bible.md missing World Bible section"))
            else:
                if not full_path.exists():
                    self.issues.append(("SSOT", f"Missing required directory: {path}"))
                    ok = False
                    
        return ok
    
    def check_character_files(self) -> bool:
        """
        キャラクターファイルのスキーマチェック
        
        characters/*.json が必須フィールドを含むか検証します。
        設計書セクション5.1のCharacter Cardスキーマに準拠。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        chars_dir = self.project_root / "characters"
        if not chars_dir.exists():
            return False
            
        ok = True
        # 必須フィールド定義（設計書準拠）
        required_fields = [
            "name",      # キャラクター名
            "tone",      # 口調
            "values",    # 価値観
            "relationships",  # 関係性
            "forbidden_words",  # 禁止ワード
            "first_person",     # 一人称
            "speech_pattern"    # 話し方の特徴
        ]
        
        for char_file in chars_dir.glob("*.json"):
            try:
                data = json.loads(char_file.read_text(encoding="utf-8"))
                # 必須フィールドの存在チェック
                missing = [f for f in required_fields if f not in data]
                if missing:
                    self.issues.append(
                        ("CHARACTER", f"{char_file.name} missing fields: {missing}")
                    )
                    ok = False
            except json.JSONDecodeError as e:
                self.issues.append(
                    ("CHARACTER", f"{char_file.name} invalid JSON: {e}")
                )
                ok = False
                
        return ok
    
    def check_memory_files(self) -> bool:
        """
        Memoryファイルのスキーマチェック
        
        memory/facts.json と memory/foreshadow.json の構造を検証します。
        設計書セクション5.1のデータスキーマに準拠。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        ok = True
        
        # facts.json のチェック
        facts_file = self.project_root / "memory" / "facts.json"
        if facts_file.exists():
            try:
                data = json.loads(facts_file.read_text(encoding="utf-8"))
                # facts配列の存在確認
                if "facts" not in data:
                    self.issues.append(("MEMORY", "facts.json missing 'facts' array"))
                    ok = False
                else:
                    # 各factの必須フィールドチェック
                    for i, fact in enumerate(data["facts"]):
                        for field in ["id", "content", "source"]:
                            if field not in fact:
                                self.issues.append(
                                    ("MEMORY", f"facts.json[{i}] missing '{field}'")
                                )
                                ok = False
            except json.JSONDecodeError as e:
                self.issues.append(("MEMORY", f"facts.json invalid JSON: {e}"))
                ok = False
        
        # foreshadow.json のチェック
        fore_file = self.project_root / "memory" / "foreshadow.json"
        if fore_file.exists():
            try:
                data = json.loads(fore_file.read_text(encoding="utf-8"))
                # foreshadowings配列の存在確認
                if "foreshadowings" not in data:
                    self.issues.append(
                        ("MEMORY", "foreshadow.json missing 'foreshadowings' array")
                    )
                    ok = False
                else:
                    for i, fs in enumerate(data["foreshadowings"]):
                        # 必須フィールドチェック
                        for field in ["id", "content", "status"]:
                            if field not in fs:
                                self.issues.append(
                                    ("MEMORY", f"foreshadow.json[{i}] missing '{field}'")
                                )
                                ok = False
                        # status値の検証
                        if "status" in fs and fs["status"] not in [
                            "unresolved", "resolved", "abandoned"
                        ]:
                            self.issues.append(
                                ("MEMORY", f"foreshadow.json[{i}] invalid status: {fs['status']}")
                            )
                            ok = False
            except json.JSONDecodeError as e:
                self.issues.append(("MEMORY", f"foreshadow.json invalid JSON: {e}"))
                ok = False
                
        return ok
    
    def check_config_yaml(self) -> bool:
        """
        config.yaml の構造チェック
        
        Provider設定、Context Budgets、Swarm設定などを検証します。
        設計書セクション10の設定ファイル仕様に準拠。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        try:
            import yaml
        except ImportError:
            self.warnings.append(("CONFIG", "PyYAML not installed, skipping YAML checks"))
            return True
            
        config_file = self.project_root / "config.yaml"
        if not config_file.exists():
            return False
            
        ok = True
        try:
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if not config:
                self.issues.append(("CONFIG", "config.yaml is empty"))
                return False
            
            # providerセクションのチェック
            if "provider" not in config:
                self.issues.append(("CONFIG", "Missing 'provider' section"))
                ok = False
            else:
                if "default" not in config["provider"]:
                    self.warnings.append(("CONFIG", "provider.default not specified"))
                if "routing" not in config["provider"]:
                    self.warnings.append(
                        ("CONFIG", "provider.routing not specified (agents use default)")
                    )
            
            # context budgetsセクションのチェック
            if "context" not in config or "budgets" not in config.get("context", {}):
                self.warnings.append(
                    ("CONFIG", "context.budgets not specified (using defaults)")
                )
            
            # swarm設定のチェック
            if "swarm" not in config or "max_revision" not in config.get("swarm", {}):
                self.warnings.append(
                    ("CONFIG", "swarm.max_revision not specified (default: 1)")
                )
                
        except Exception as e:
            self.issues.append(("CONFIG", f"config.yaml parse error: {e}"))
            ok = False
            
        return ok
    
    def check_pal_interface(self) -> bool:
        """
        PAL(Provider Abstraction Layer)実装のチェック
        
        必須メソッド（generate, capabilities, healthcheck）の存在を確認します。
        設計書セクション4.1のPAL仕様に準拠。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        ok = True
        
        # provider/pal関連のPythonファイルを検索
        pal_files = list(self.project_root.rglob("*provider*.py")) + \
                   list(self.project_root.rglob("*pal*.py"))
        
        if not pal_files:
            self.issues.append(("PAL", "No provider/pal module found"))
            return False
        
        # 必須メソッド定義（設計書準拠）
        required_methods = ["generate", "capabilities", "healthcheck"]
        
        for pal_file in pal_files:
            content = pal_file.read_text(encoding="utf-8")
            for method in required_methods:
                if f"def {method}" not in content:
                    self.warnings.append(
                        ("PAL", f"{pal_file} may be missing '{method}' method")
                    )
        
        return ok
    
    def check_agents(self) -> bool:
        """
        Agent実装のチェック
        
        5つのMVP Agent（Director, Writer, Checker, Editor, Committer）の存在を確認します。
        設計書セクション6.1のAgent構成に準拠。
        
        Returns:
            bool: 全チェックが合格したかどうか
        """
        ok = True
        
        # Agent関連のPythonファイルを検索
        agent_files = list(self.project_root.rglob("*agent*.py"))
        
        if not agent_files:
            self.issues.append(("AGENTS", "No agent module found"))
            return False
        
        # 期待される5つのAgent
        expected_agents = ["director", "writer", "checker", "editor", "committer"]
        found_agents = set()
        
        for agent_file in agent_files:
            name = agent_file.stem.lower()
            for agent in expected_agents:
                if agent in name:
                    found_agents.add(agent)
        
        # 不足しているAgentを検出
        missing = set(expected_agents) - found_agents
        if missing:
            self.warnings.append(("AGENTS", f"Potentially missing agents: {missing}"))
        
        return ok
    
    def report(self) -> int:
        """
        検証結果レポートを出力
        
        収集された問題と警告を整形して表示し、終了コードを返します。
        
        Returns:
            int: 終了コード（0=成功, 1=失敗）
        """
        print("=" * 60)
        print("Design Compliance Report")
        print("=" * 60)
        
        if not self.issues and not self.warnings:
            print("\n✓ All checks passed!")
            return 0
        
        # 問題の表示
        if self.issues:
            print(f"\n✗ Issues found: {len(self.issues)}")
            # カテゴリ別にグループ化
            by_category: Dict[str, List[str]] = {}
            for cat, msg in self.issues:
                by_category.setdefault(cat, []).append(msg)
            
            for cat, msgs in sorted(by_category.items()):
                print(f"\n[{cat}]")
                for msg in msgs:
                    print(f"  - {msg}")
        
        # 警告の表示
        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            by_category: Dict[str, List[str]] = {}
            for cat, msg in self.warnings:
                by_category.setdefault(cat, []).append(msg)
            
            for cat, msgs in sorted(by_category.items()):
                print(f"\n[{cat}]")
                for msg in msgs:
                    print(f"  - {msg}")
        
        print("\n" + "=" * 60)
        return 1 if self.issues else 0


def main():
    """メインエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check novelist project compliance with keikaku.md design spec"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all compliance checks"
    )
    parser.add_argument(
        "--ssot", 
        action="store_true", 
        help="Check SSOT structure only"
    )
    parser.add_argument(
        "--pal", 
        action="store_true", 
        help="Check PAL interface only"
    )
    parser.add_argument(
        "--agents", 
        action="store_true", 
        help="Check Agent configuration only"
    )
    parser.add_argument(
        "--config", 
        action="store_true", 
        help="Check config.yaml only"
    )
    
    args = parser.parse_args()
    
    # 特定のチェックが指定されなければ全チェック
    if not any([args.ssot, args.pal, args.agents, args.config]):
        args.all = True
    
    checker = ComplianceChecker()
    
    # 選択されたチェックを実行
    if args.all or args.ssot:
        checker.check_ssot_structure()
        checker.check_character_files()
        checker.check_memory_files()
    
    if args.all or args.config:
        checker.check_config_yaml()
    
    if args.all or args.pal:
        checker.check_pal_interface()
    
    if args.all or args.agents:
        checker.check_agents()
    
    # レポート出力して終了
    sys.exit(checker.report())


if __name__ == "__main__":
    main()
