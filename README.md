# Novelist - AI小説創作支援システム

学習なしで「AIのべりすと」級の創作体験を提供するローカル指向プロダクト。

## 概要

Novelistは、DAPT/SFT/LoRAなどの重み更新を行わず、推論時の構造（ICL、ルール、記憶、検査・修正ループ）で品質を作るAI小説創作支援システムです。

## 特徴

- **学習不要**: 推論時の設計で品質を担保
- **ローカルファースト**: 基本ローカル推論、必要にらクラウドへ差し替え可能
- **破綻しにくい**: 章を跨いでキャラ・事実・伏線が崩れにくい
- **ワンクリック起動**: ローカルで起動→ブラウザUIで即執筆開始

## アーキテクチャ

### Agent Swarm (5体)
- **Director**: SceneSpec（設計図）を生成
- **Writer**: SceneSpecを入力に本文生成
- **ContinuityChecker**: 矛盾・逸脱を検出
- **StyleEditor**: 文章整形
- **Committer**: Memory更新・成果物保存

### Single Source of Truth (SSOT)
```
Project/
├── bible.md              # 世界観・文体規約
├── characters/*.json     # キャラクターカード
├── chapters/*.md         # 本文
├── memory/
│   ├── episodic.md      # 直近要約（可変）
│   ├── facts.json       # 確定事実（不変）
│   └── foreshadow.json  # 伏線管理
└── config.yaml          # プロバイダー設定
```

## クイックスタート

```bash
# プロジェクト作成
novelist init my-novel

# シーン生成
novelist generate --chapter 1 --scene 1

# テスト実行
python .agents/skills/novelist-tester/scripts/run_tests.py --all

# 進捗確認
python .agents/skills/project-roadmap/scripts/roadmap.py status
```

## ドキュメント

- [設計書](docs/keikaku.md) - 詳細設計仕様
- [AGENTS.md](AGENTS.md) - AIエージェント用ガイド
- [テンプレート](templates/) - SSOT文書テンプレート

## 開発ロードマップ

- **Phase 0** (2-3日): 骨格実装
- **Phase 1** (+3-5日): 2段生成と記憶管理
- **Phase 2** (+1-2週間): Swarmと多プロバイダ対応

## ライセンス

[ライセンス表記]
