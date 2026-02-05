#!/usr/bin/env python3
"""
Quality Metrics Calculator for Novelist Project
生成テキストの品質メトリクスを計算するモジュール

本モジュールは、設計書セクション7に定義された以下の品質メトリクスを計算します：
- メタ発言率（メタ的発言の検出）
- 反復率（n-gram重複の検出）
- 事実矛盾数（Factsとの照合）
- キャラ逸脱数（Character Cardsとの照合）

使用例:
    from metrics import MetricsCalculator
    
    calc = MetricsCalculator(text, facts, characters)
    metrics = calc.calculate_all()
    
    print(f"Meta-speech rate: {metrics['meta_speech_rate']:.2%}")
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MetricsCalculator:
    """
    品質メトリクス計算クラス
    
    生成されたテキストの品質を多角的に評価します。
    各メトリクスは独立して計算可能です。
    """
    
    # メタ発言パターン（日本語小説で避けるべき表現）
    # 設計書セクション7「自動メトリクス」参照
    META_PATTERNS = [
        r"この物語",           # 物語について言及
        r"この小説",           # 小説について言及
        r"読者",               # 読者への言及
        r"次の章",             # 次の章について言及
        r"前の章",             # 前の章について言及
        r"AIとして",           # AIであることの言及
        r"私は生成",           # 生成について言及
        r"物語として",         # メタ的表現
        r"設定では",           # 設定について言及
        r"作者",               # 作者について言及
    ]
    
    def __init__(
        self, 
        text: str, 
        facts: Optional[Dict] = None, 
        characters: Optional[List[Dict]] = None
    ):
        """
        Args:
            text: 評価対象のテキスト
            facts: 照合するFactsデータ（省略可）
            characters: 照合するCharacterデータ（省略可）
        """
        self.text = text
        self.facts = facts or {}
        self.characters = characters or []
        
    def calculate_all(self) -> Dict[str, float]:
        """
        全メトリクスを一括計算
        
        Returns:
            Dict containing all metrics:
                - meta_speech_rate: メタ発言率 (target: < 1%)
                - repetition_rate: 反復率 (target: < 5%)
                - fact_contradictions: 事実矛盾数 (target: 0)
                - char_deviations: キャラ逸脱数 (target: 0)
                - sentence_count: 文数
                - word_count: 文字数
        """
        return {
            "meta_speech_rate": self.meta_speech_rate(),
            "repetition_rate": self.repetition_rate(),
            "fact_contradictions": len(self.fact_contradictions()),
            "char_deviations": len(self.character_deviations()),
            "sentence_count": self.sentence_count(),
            "word_count": self.word_count(),
        }
    
    def sentence_count(self) -> int:
        """
        文数をカウント（日本語対応）
        
        句点（。）、感嘆符（！）、疑問符（？）を文の区切りとしてカウントします。
        
        Returns:
            int: 文の総数
        """
        # 文末記号でカウント
        endings = re.findall(r'[。！？\.\!\?]', self.text)
        return len(endings)
    
    def word_count(self) -> int:
        """
        文字数をカウント
        
        Returns:
            int: 文字総数
        """
        return len(self.text)
    
    def meta_speech_rate(self) -> float:
        """
        メタ発言率を計算
        
        メタ的な発言（「この物語」「読者」など）の出現率を計算します。
        設計書では1%未満が目標値です。
        
        Returns:
            float: メタ発言率（0.0〜1.0）
        """
        sentences = self.sentence_count()
        if sentences == 0:
            return 0.0
        
        # 各パターンの出現回数をカウント
        meta_count = 0
        for pattern in self.META_PATTERNS:
            matches = re.findall(pattern, self.text)
            meta_count += len(matches)
        
        return meta_count / sentences
    
    def repetition_rate(self, n: int = 3, window: Optional[int] = None) -> float:
        """
        n-gram反復率を計算
        
        短い区間での文字列重複（反復表現）を検出します。
        設計書では5%未満が目標値です。
        
        Args:
            n: n-gramのサイズ（デフォルト: 3文字）
            window: 検出ウィンドウ（未指定時は全文）
        
        Returns:
            float: 反復率（0.0〜1.0）
        """
        # 空白と改行を除去
        text = self.text.replace('\n', '').replace(' ', '')
        
        if len(text) < n:
            return 0.0
        
        # n-gramを生成
        ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
        
        if len(ngrams) == 0:
            return 0.0
        
        # 出現頻度をカウント
        counts = Counter(ngrams)
        
        # 反復率を計算（2回以上出現するn-gramの比率）
        repeated = sum(1 for count in counts.values() if count > 1)
        return repeated / len(ngrams)
    
    def fact_contradictions(self) -> List[Dict]:
        """
        事実矛盾を検出
        
        生成テキストがfacts.jsonに定義された事実と矛盾していないか検証します。
        現状は簡易的なキーワードマッチングですが、本番環境では
        LLMまたは埋め込みベクトルによる検証を推奨します。
        
        Returns:
            List[Dict]: 検出された矛盾のリスト
                - fact_id: 矛盾したFactのID
                - content: Factの内容
                - type: 矛盾タイプ
        """
        contradictions = []
        
        facts_data = self.facts.get('facts', [])
        for fact in facts_data:
            content = fact.get('content', '')
            fact_id = fact.get('id', 'unknown')
            
            # 簡易的な矛盾検出（本番ではより高度なNLPを使用）
            if self._check_contradiction(content):
                contradictions.append({
                    'fact_id': fact_id,
                    'content': content,
                    'type': 'potential_contradiction'
                })
        
        return contradictions
    
    def _check_contradiction(self, fact_content: str) -> bool:
        """
        簡易的な矛盾検出（内部メソッド）
        
        否定パターンを用いて、Factの内容が否定されていないかチェックします。
        
        Args:
            fact_content: 検証するFactの内容
        
        Returns:
            bool: 矛盾の可能性があるか
        """
        # 否定パターンマッチング（簡易実装）
        negation_patterns = [
            rf"{re.escape(fact_content)}.+?違う",
            rf"{re.escape(fact_content)}.+?間違い",
            rf"{re.escape(fact_content)}.+?ない",
        ]
        
        for pattern in negation_patterns:
            if re.search(pattern, self.text, re.DOTALL):
                return True
        
        return False
    
    def character_deviations(self) -> List[Dict]:
        """
        キャラクター逸脱を検出
        
        生成テキストがCharacter Cardsに定義された設定から逸脱していないか検証します。
        
        Returns:
            List[Dict]: 検出された逸脱のリスト
                - character: キャラクター名
                - type: 逸脱タイプ（first_person_mismatch, forbidden_word等）
        """
        deviations = []
        
        for char in self.characters:
            char_name = char.get('name', '')
            first_person = char.get('first_person', '')
            forbidden_words = char.get('forbidden_words', [])
            speech_pattern = char.get('speech_pattern', '')
            
            # 一人称の一致チェック
            if first_person and not self._check_first_person(char_name, first_person):
                deviations.append({
                    'character': char_name,
                    'type': 'first_person_mismatch',
                    'expected': first_person
                })
            
            # 禁止ワードの使用チェック
            for word in forbidden_words:
                if word in self.text:
                    # キャラクターのセリフ内でのみ使用かチェック
                    if self._word_in_character_speech(char_name, word):
                        deviations.append({
                            'character': char_name,
                            'type': 'forbidden_word',
                            'word': word
                        })
        
        return deviations
    
    def _check_first_person(self, char_name: str, expected: str) -> bool:
        """
        一人称の一致をチェック（内部メソッド）
        
        Args:
            char_name: キャラクター名
            expected: 期待される一人称
        
        Returns:
            bool: 一致しているか（現状は常にTrueを返す簡易実装）
        """
        # 本番実装ではセリフを抽出して一人称を検証
        # 現状はプレースホルダー
        return True
    
    def _word_in_character_speech(self, char_name: str, word: str) -> bool:
        """
        単語がキャラクターのセリフ内にあるかチェック（内部メソッド）
        
        Args:
            char_name: キャラクター名
            word: 検索する単語
        
        Returns:
            bool: セリフ内に含まれるか（簡易実装）
        """
        # 本番実装ではセリフを正確に抽出
        # 現状は単純な包含チェック
        return word in self.text


def format_metrics(metrics: Dict[str, float]) -> str:
    """
    メトリクスを整形して表示用文字列を生成
    
    Args:
        metrics: calculate_all()の結果
    
    Returns:
        str: 整形されたレポート文字列
    """
    lines = [
        "Quality Metrics:",
        f"  Meta-speech rate: {metrics['meta_speech_rate']:.2%} (target: <1%)",
        f"  Repetition rate: {metrics['repetition_rate']:.2%} (target: <5%)",
        f"  Fact contradictions: {metrics['fact_contradictions']} (target: 0)",
        f"  Character deviations: {metrics['char_deviations']} (target: 0)",
        f"  Sentences: {metrics['sentence_count']}",
        f"  Characters: {metrics['word_count']}",
    ]
    
    # 合格/不合格の判定
    status = []
    if metrics['meta_speech_rate'] < 0.01:
        status.append("✓ Meta-speech")
    else:
        status.append("✗ Meta-speech")
    
    if metrics['repetition_rate'] < 0.05:
        status.append("✓ Repetition")
    else:
        status.append("✗ Repetition")
    
    if metrics['fact_contradictions'] == 0:
        status.append("✓ Facts")
    else:
        status.append("✗ Facts")
    
    if metrics['char_deviations'] == 0:
        status.append("✓ Characters")
    else:
        status.append("✗ Characters")
    
    lines.append(f"\nStatus: {' '.join(status)}")
    
    return '\n'.join(lines)


def main():
    """コマンドラインインターフェース"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calculate quality metrics for generated text"
    )
    parser.add_argument("file", help="Text file to analyze")
    parser.add_argument("--facts", help="facts.json file path")
    parser.add_argument("--characters", help="characters directory path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # テキストファイル読み込み
    text = Path(args.file).read_text(encoding="utf-8")
    
    # Facts読み込み
    facts = {}
    if args.facts:
        facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
    
    # Characters読み込み
    characters = []
    if args.characters:
        char_dir = Path(args.characters)
        for char_file in char_dir.glob("*.json"):
            characters.append(json.loads(char_file.read_text(encoding="utf-8")))
    
    # メトリクス計算
    calc = MetricsCalculator(text, facts, characters)
    metrics = calc.calculate_all()
    
    # 結果出力
    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        print(format_metrics(metrics))


if __name__ == "__main__":
    main()
