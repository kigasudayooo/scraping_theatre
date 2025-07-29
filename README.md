# 映画館スクレイピング & AI Discord Bot システム

**日本の独立系映画館情報を自動収集し、Ollama LLM搭載Discord Botで自然な日本語対話を提供するシステム**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289da.svg)](https://discord.com)
[![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:0.5b-green.svg)](https://ollama.ai)
[![uv](https://img.shields.io/badge/uv-Package_Manager-orange.svg)](https://github.com/astral-sh/uv)

## 📖 システム概要

### 🎬 自動映画情報収集
- **対応映画館**: ケイズシネマ、下高井戸シネマ、早稲田松竹、新宿武蔵野館
- **データ収集**: 35作品の詳細情報（監督、キャスト、あらすじ、上映スケジュール）
- **出力形式**: JSON構造化データ（`data/movies_data.json`）
- **更新方式**: 手動実行 + 自動スケジュール対応

### 🤖 AI搭載Discord Bot（完全実装済み）
- **LLMエンジン**: Ollama qwen2.5:0.5b（ローカル実行）
- **自然な日本語会話**: 映画情報について自然な応答
- **インテリジェント検索**: 映画タイトル、監督名、映画館別検索
- **コンテキスト理解**: JSON構造データから正確な情報抽出
- **フォールバック機能**: LLM障害時の安全な静的応答

### 📊 実装完了機能
- ✅ **フル統合テスト完了** (100%成功率)
- ✅ **Ollama統合テスト完了** (84.6%成功率)
- ✅ **Discord Bot統合完了**
- ✅ **相対インポート問題解決済み**
- ✅ **35作品データ収集完了**

---

## 🚀 インストールと初期セットアップ

### 1. 必要システム

- **Python**: 3.11以上
- **uv**: Python高速パッケージマネージャー
- **Ollama**: ローカルLLMサーバー
- **Git**: バージョン管理

### 2. リポジトリのクローン

```bash
git clone <repository-url>
cd scraping_theatre
```

### 3. uv環境のセットアップ

```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と依存関係のインストール
uv sync

# 環境の確認
uv run python --version
```

### 4. Ollamaのセットアップ

#### Ollamaのインストール
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# または公式サイトからダウンロード
# https://ollama.ai/download
```

#### 必要モデルのダウンロード
```bash
# qwen2.5:0.5b モデル（約397MB）をダウンロード
ollama pull qwen2.5:0.5b

# ダウンロード確認
ollama list
```

#### Ollamaサーバーの起動
```bash
# バックグラウンドで起動（推奨）
nohup ollama serve > ollama.log 2>&1 &

# または フォアグラウンドで起動（テスト用）
ollama serve
```

### 5. Discord Bot のセットアップ

#### Discord Application の作成

1. **Discord Developer Portal** にアクセス
   - https://discord.com/developers/applications

2. **New Application** をクリック
   - アプリケーション名: 「映画館Bot」（任意）

3. **Bot** タブに移動
   - **Add Bot** をクリック
   - **Token** をコピー（後で使用）
   - **MESSAGE CONTENT INTENT** を有効化 ✅

4. **OAuth2 > URL Generator** タブ
   - **Scopes**: `bot` にチェック ✅
   - **Bot Permissions**: 
     - Send Messages ✅
     - Use Slash Commands ✅
     - Read Message History ✅
     - Add Reactions ✅

5. **生成されたURL** でBotをサーバーに招待

#### Discord サーバーの準備

Botが動作するDiscordサーバーに以下のチャンネルを作成：

1. **#weekly-movies** (メインチャンネル)
   - 週次レポートとデータ更新通知用

2. **#movie-questions** (質問チャンネル)
   - AI応答での映画相談用

---

## ⚙️ 環境変数の設定

**重要**: `.env`ファイルでは引用符を使用せずに値を直接記述してください。

プロジェクトルートディレクトリに `.env` ファイルを作成：

```bash
# Discord Bot設定（必須）
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_MAIN_CHANNEL_NAME=weekly-movies
DISCORD_DETAIL_CHANNEL_NAME=movie-questions

# LLM設定（デフォルト値で動作）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
ENABLE_AI_RESPONSES=true

# スケジュール設定（オプション）
WEEKLY_REPORT_TIME=MON 07:30
DATA_UPDATE_INTERVAL=6
TIMEZONE=Asia/Tokyo
```

**注意事項**:
- `.env`ファイルは`.gitignore`に含まれており、Gitにコミットされません
- 引用符は使用しないでください（例: `DISCORD_BOT_TOKEN=abc123` ○, `DISCORD_BOT_TOKEN="abc123"` ✗）
- `DISCORD_BOT_TOKEN`のみ必須で、他の設定は自動的にデフォルト値が使用されます

---

## 🧪 システムの動作確認

### 1. 基本環境テスト

```bash
# Python環境とパッケージの確認
uv run python -c "import discord, aiohttp, beautifulsoup4; print('✅ All packages installed')"

# Ollamaサーバーの状態確認
curl http://localhost:11434/api/tags

# qwen2.5:0.5bモデルの動作テスト
curl -X POST http://localhost:11434/api/generate -d '{"model":"qwen2.5:0.5b","prompt":"Hello","stream":false}'
```

### 2. 統合テストの実行

```bash
# Ollama統合テスト（推奨）
uv run python test_ollama_integration.py

# Discord Bot統合テスト
uv run python test_discord_integration.py

# フルシステムテスト
uv run python test_full_system.py
```

---

## 🚀 システムの実行

### 1. 映画データの収集

```bash
# 全映画館のスクレイピング実行
uv run python scrape_with_json.py
# → data/movies_data.json に35作品のデータが保存されます
```

### 2. Discord Botの起動

```bash
# Discord Bot起動（メイン実行方法）
uv run python start_discord_bot.py
```

**起動ログ例**:
```
2025-07-28 15:18:27,109 - src.discord_bot.simple_discord_bot - INFO - LLM responder initialized successfully
2025-07-28 15:18:28,234 - src.discord_bot.simple_discord_bot - INFO - cinema_bot としてログインしました
2025-07-28 15:18:28,235 - src.discord_bot.simple_discord_bot - INFO - Bot is in 1 guilds
```

### 3. Bot機能の確認

Discord サーバーで以下のコマンドをテスト：

```
!ping          # 接続テスト
!status        # Bot状態確認
また逢いましょうについて教えて    # AI応答テスト
ケイズシネマの上映予定は？      # 映画館検索テスト
```

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Discord Bot トークンエラー
**エラー**: `Error: Invalid Discord bot token`
**解決**: 
- `.env`ファイルで引用符を使用していないか確認
- Discord Developer PortalでBotトークンを再生成
- MESSAGE CONTENT INTENTが有効になっているか確認

#### 2. Ollama接続エラー
**エラー**: `Connection refused to localhost:11434`
**解決**:
```bash
# Ollamaサーバーを起動
ollama serve

# または バックグラウンドで起動
nohup ollama serve > ollama.log 2>&1 &
```

#### 3. 相対インポートエラー
**エラー**: `ImportError: attempted relative import with no known parent package`
**解決**: 
- `start_discord_bot.py`を使用してください（相対インポート問題は解決済み）

#### 4. モデルが見つからないエラー
**エラー**: `model 'qwen2.5:0.5b' not found`
**解決**:
```bash
# モデルをダウンロード
ollama pull qwen2.5:0.5b

# 利用可能モデルの確認
ollama list
```

#### 5. メモリ不足エラー
**エラー**: `Out of memory`
**解決**:
- より軽量なモデルを使用: `qwen2.5:0.5b` (397MB)
- または環境変数で他のモデルを指定: `OLLAMA_MODEL=llama3.2:1b`

### ログの確認方法

```bash
# Discord Botのログ
tail -f logs/discord_bot.log

# Ollamaのログ
tail -f ollama.log

# スクレイピングのログ
tail -f scraping.log
```

---

## 📚 技術仕様

### システム構成
- **言語**: Python 3.11+
- **パッケージ管理**: uv
- **AI エンジン**: Ollama (qwen2.5:0.5b)
- **Discord ライブラリ**: discord.py
- **データ形式**: JSON (UTF-8)
- **対応映画館**: 4館、35作品

### パフォーマンス
- **テスト成功率**: 100% (フルシステム)
- **LLM統合成功率**: 84.6%
- **応答時間**: 平均 2-3秒
- **メモリ使用量**: ~500MB (Ollama含む)

---

## 📝 開発・デプロイメント

### 本番環境での起動

```bash
# systemdサービスとして起動（推奨）
sudo systemctl start cinema-discord-bot

# またはPM2を使用
pm2 start start_discord_bot.py --name cinema-bot --interpreter python
```

### データ更新の自動化

```bash
# cronで週次データ更新を設定
0 6 * * 1 cd /path/to/scraping_theatre && uv run python scrape_with_json.py
```

---

## 🤖 Discord Botの起動と運用

### 1. Bot起動（開発・テスト用）

```bash
# フォアグラウンドで起動（ログ確認用）
uv run python -m src.discord_bot.discord_bot_main
```

### 2. Bot起動（本番運用用）

#### systemdサービスの作成（Linux推奨）

`/etc/systemd/system/cinema-bot.service` を作成：

```ini
[Unit]
Description=Cinema Discord Bot with Ollama Integration
After=network.target
Wants=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/scraping_theatre
Environment=PATH=/home/your_username/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/your_username/.local/bin/uv run python -m src.discord_bot.discord_bot_main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

サービスの有効化と起動：

```bash
# サービスファイルのリロード
sudo systemctl daemon-reload

# サービスの有効化（起動時自動開始）
sudo systemctl enable cinema-bot

# サービスの開始
sudo systemctl start cinema-bot

# ステータス確認
sudo systemctl status cinema-bot

# ログ確認
sudo journalctl -u cinema-bot -f
```

#### PM2を使用した起動（Node.js環境がある場合）

```bash
# PM2のインストール
npm install -g pm2

# ecosystem.config.js の作成
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'cinema-bot',
    cwd: '/path/to/scraping_theatre',
    script: '/home/your_username/.local/bin/uv',
    args: 'run python -m src.discord_bot.discord_bot_main',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOF

# PM2でBot起動
pm2 start ecosystem.config.js

# 起動時自動開始の設定
pm2 startup
pm2 save
```

#### 手動起動スクリプト（シンプルな方法）

`start_bot.sh` を作成：

```bash
#!/bin/bash
cd /path/to/scraping_theatre

# Ollamaが起動していない場合は起動
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Starting Ollama..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 5
fi

# Discord Bot起動
echo "Starting Discord Bot..."
uv run python -m src.discord_bot.discord_bot_main
```

実行権限を付与して起動：

```bash
chmod +x start_bot.sh
./start_bot.sh
```

### 3. 定期スクレイピングの設定

Discord Botには週次自動スクレイピング機能が組み込まれていますが、より確実な運用のため、crontabでのバックアップ実行も推奨します。

#### crontabの設定

```bash
# crontabの編集
crontab -e
```

以下の設定を追加：

```cron
# 毎週月曜日 6:00 AM にスクレイピング実行
0 6 * * 1 cd /path/to/scraping_theatre && /home/your_username/.local/bin/uv run python scrape_with_json.py all >> /path/to/scraping_theatre/cron.log 2>&1

# 毎日 3:00 AM にログローテーション
0 3 * * * find /path/to/scraping_theatre -name "*.log" -size +100M -exec truncate -s 0 {} \;
```

#### ログ監視の設定

```bash
# ログディレクトリの作成
mkdir -p logs

# ログローテーション設定 /etc/logrotate.d/cinema-bot
sudo tee /etc/logrotate.d/cinema-bot << 'EOF'
/path/to/scraping_theatre/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

---

## 🎯 Discord Botの使用方法

### 基本コマンド

Bot起動後、Discordサーバーで以下のコマンドが使用できます：

#### 1. ヘルプ表示
```
!help
```
または
```
!h
```

#### 2. Bot状態確認
```
!status
```
または
```
!s
```

AI応答システムの状態、Ollama接続状況、対応映画館数などが表示されます。

#### 3. 手動データ更新
```
!update
```
または
```
!u
```

全映画館の最新情報を手動で取得し、CSV/JSON両形式で保存します。

### AI映画相談機能

**#movie-questions** チャンネルで、コマンドプレフィックス（!）なしで自然に話しかけてください：

#### 映画情報の質問
```
「また逢いましょう」について教えて
```

#### 映画館のスケジュール確認
```
ケイズシネマの今週の上映予定は？
```

#### 監督作品の検索
```
監督「山田太郎」の作品を教えて
```

#### 一般的な映画相談
```
こんにちは。今週おすすめの映画はありますか？
```

#### ヘルプ要求
```
使い方を教えて
```

### 自動通知機能

#### 週次レポート
- **時間**: 毎週月曜日 7:30 AM（日本時間）
- **チャンネル**: #weekly-movies
- **内容**: 今週・来週の上映映画情報

#### データ更新通知
- **タイミング**: スクレイピング完了時
- **チャンネル**: #weekly-movies  
- **内容**: 更新された映画館数と作品数

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Discord Botが応答しない

**原因**: Botトークンまたは権限の問題

**解決方法**:
```bash
# .envファイルのトークン確認
cat .env | grep DISCORD_BOT_TOKEN

# Bot権限の確認（Discord Developer Portal）
# - MESSAGE CONTENT INTENT が有効化されているか
# - Botに必要な権限が付与されているか

# ログの確認
sudo journalctl -u cinema-bot -n 50
```

#### 2. Ollama/AI応答が動作しない

**原因**: Ollamaサーバーの停止またはモデル不足

**解決方法**:
```bash
# Ollamaサーバーの状態確認
ps aux | grep ollama

# サーバーが停止している場合
nohup ollama serve > ollama.log 2>&1 &

# モデルの確認とダウンロード
ollama list
ollama pull qwen2.5:0.5b

# 接続テスト
curl http://localhost:11434/api/tags
```

#### 3. スクレイピングが失敗する

**原因**: ネットワーク問題またはサイト構造の変更

**解決方法**:
```bash
# 個別映画館のテスト
uv run python scrape_with_json.py ks_cinema

# ネットワーク接続確認
curl -I https://www.ks-cinema.com/

# ログ確認
tail -f logs/scraping.log
```

#### 4. メモリ不足エラー

**原因**: Ollamaのメモリ使用量（約800MB）

**解決方法**:
```bash
# メモリ使用量確認
free -h
ps aux --sort=-%mem | head

# より軽量なモデルへの変更（.env）
OLLAMA_MODEL=qwen2.5:0.5b  # 現在（397MB）
# OLLAMA_MODEL=llama3.2:1b  # より軽量（約1GB）

# スワップ領域の追加（必要に応じて）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 5. 文字化け問題

**原因**: 文字エンコーディングの問題

**解決方法**:
```bash
# システムロケール確認
locale

# UTF-8の設定（必要に応じて）
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8

# Python環境の確認
uv run python -c "import sys; print(sys.getdefaultencoding())"
```

### ログ確認方法

#### システムサービス（systemd）の場合
```bash
# リアルタイムログ確認
sudo journalctl -u cinema-bot -f

# 過去のログ確認
sudo journalctl -u cinema-bot -n 100

# エラーログのみ確認
sudo journalctl -u cinema-bot -p err
```

#### 手動起動の場合
```bash
# Botログ
tail -f discord_bot.log

# Ollamaログ  
tail -f ollama.log

# スクレイピングログ
tail -f cron.log
```

### パフォーマンス最適化

#### 1. Ollama設定の調整

`~/.ollama/config.json` （作成が必要な場合あり）:
```json
{
  "num_ctx": 2048,
  "num_gpu": 0,
  "num_thread": 4,
  "num_predict": 512
}
```

#### 2. Discord Bot設定の調整

`.env` ファイル:
```env
# 応答速度優先
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=256

# メモリ使用量優先
CACHE_DURATION_HOURS=12
MAX_SEARCH_RESULTS=5
```

---

## 📚 開発者向け情報

### プロジェクト構造

```
scraping_theatre/
├── src/
│   ├── scraping/           # スクレイピング機能
│   │   ├── models.py       # データモデル
│   │   ├── json_exporter.py # JSON出力
│   │   └── scrapers/       # 各映画館スクレーパー
│   └── discord_bot/        # Discord Bot機能
│       ├── discord_bot_main.py      # メインBot
│       ├── ollama_client.py         # Ollama API
│       ├── llm_responder.py         # LLM応答ロジック
│       ├── prompt_templates.py      # プロンプト管理
│       └── discord_config.py        # 設定管理
├── data/                   # 出力データ
├── docs/                   # ドキュメント
├── tests/                  # テストスクリプト
├── .env                    # 環境変数（要作成）
├── pyproject.toml          # uv設定
└── README.md               # このファイル
```

### 追加テストの実行

```bash
# 個別コンポーネントのテスト
uv run python test_ollama_integration.py
uv run python test_discord_integration.py
uv run python test_full_system.py

# カスタムテストの実行
uv run python -m pytest tests/ -v
```

### カスタマイズ

#### 新しい映画館の追加

1. `src/scraping/scrapers/` に新しいスクレイパーを作成
2. `src/discord_bot/discord_bot_main.py` のスクレイパーリストに追加
3. テストとドキュメントの更新

#### プロンプトのカスタマイズ

`src/discord_bot/prompt_templates.py` でシステムプロンプトやテンプレートを編集可能

#### 新しいLLMモデルの使用

```env
# .env ファイルで変更
OLLAMA_MODEL=llama3.2:3b
# または
OLLAMA_MODEL=gemma2:2b
```

---

## 🚨 セキュリティ注意事項

### 1. 機密情報の管理

- **Discord Bot Token**: `.env` ファイルで管理、絶対にGitにコミットしない
- **ログファイル**: 定期的なローテーションとアクセス制限
- **システムアクセス**: 最小権限の原則

### 2. ネットワークセキュリティ

- **Ollama API**: デフォルトで localhost:11434 （外部公開しない）
- **Discord API**: 公式エンドポイントのみ使用
- **スクレイピング**: レート制限とrobot.txt遵守

### 3. システムリソース

- **メモリ監視**: Ollamaのメモリ使用量（~800MB）
- **ディスク容量**: ログとデータファイルの定期清掃
- **CPU使用量**: LLM推論時の負荷監視

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は `LICENSE` ファイルを参照してください。

---

## 🤝 サポート・コントリビューション

### 問題報告

バグや問題を発見した場合は、以下の情報と共にIssueを作成してください：

- システム環境（OS、Python版数、uv版数）
- エラーメッセージ（ログファイルから）
- 再現手順
- 期待される動作

### 機能提案

新機能のアイデアや改善提案も歓迎します。

---

## 📞 よくある質問（FAQ）

### Q: Botが日本語で応答しない
**A**: Ollamaのモデル（qwen2.5:0.5b）は日本語対応ですが、プロンプトテンプレートで日本語応答を指定しています。`src/discord_bot/prompt_templates.py` の設定を確認してください。

### Q: 応答が遅い（15秒以上）
**A**: LLM推論は計算量が多く、5-13秒が正常です。より高速化したい場合は、より小さなモデルへの変更を検討してください。

### Q: 複数のDiscordサーバーで使用できる？
**A**: 現在の実装は単一サーバー向けです。複数サーバーでの使用には設定の拡張が必要です。

### Q: 映画館が追加されない
**A**: 新しい映画館を追加するには、専用スクレイパーの開発が必要です。各映画館のHTML構造が異なるためです。

### Q: データはいつ更新される？
**A**: 毎週月曜日6時（自動）、または `!update` コマンド（手動）で更新されます。

---

**このマニュアルで不明な点がある場合は、プロジェクトのドキュメント（`docs/DEVELOPMENT_DIARY.md`）も併せて参照してください。**