# 新しいリポジトリへのPush手順

## 1. GitHubで新しいリポジトリを作成
https://github.com/new

- リポジトリ名: `novelist` (任意)
- PublicまたはPrivateを選択
- READMEや.gitignoreは作成しない（既に存在するため）

## 2. リモートURLを設定

```bash
# HTTPSの場合
git remote add origin https://github.com/YOUR_USERNAME/novelist.git

# SSHの場合
git remote add origin git@github.com:YOUR_USERNAME/novelist.git
```

## 3. Push実行

```bash
# mainブランチをpush
git push -u origin main

# すべてのタグもpush
git push --tags
```

## 4. 確認

```bash
# リモート設定確認
git remote -v

# GitHubでリポジトリを開く
open https://github.com/YOUR_USERNAME/novelist
```

---

## ワンライナーで実行

```bash
# 1. リモート追加（HTTPS例）
git remote add origin https://github.com/YOUR_USERNAME/novelist.git

# 2. Push
git push -u origin main

# 完了！
```

## トラブルシューティング

### 認証エラー
```bash
# GitHub CLIでログイン
gh auth login

# またはトークンを設定
export GITHUB_TOKEN=your_token_here
```

### リモートが既に存在する場合
```bash
# 既存のリモートを削除
git remote remove origin

# 新しいリモートを追加
git remote add origin https://github.com/YOUR_USERNAME/novelist.git
```

### 強制Push（既存リポジトリを上書きする場合）
⚠️ 注意：既存のデータが失われます
```bash
git push -u origin main --force
```
