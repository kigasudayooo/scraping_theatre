# Discord Bot 完全セットアップガイド

映画館スクレイピングシステム用Discord Botの設定を、迷いなく完了できる詳細マニュアルです。

## 📋 **事前準備チェックリスト**

実行前に以下を確認してください：

- [ ] Discordアカウントを持っている
- [ ] Discord Botを設置するサーバーの管理者権限がある
- [ ] Ubuntu Server環境が用意されている
- [ ] インターネット接続が安定している
- [ ] スクレイピングシステムが正常に動作している

## 🎯 **Phase 1: Discord Developer Portal でのBot作成**

### **Step 1-1: Discord Developer Portal にアクセス**

1. **ブラウザで以下のURLを開く**
   ```
   https://discord.com/developers/applications
   ```

2. **Discordアカウントでログイン**
   - 「Log In」ボタンをクリック
   - メールアドレスとパスワードを入力
   - 2要素認証が設定されている場合は認証コードを入力

3. **ログイン完了の確認**
   - 画面上部に「My Applications」と表示されることを確認

### **Step 1-2: 新しいアプリケーションの作成**

1. **「New Application」ボタンをクリック**
   - 画面右上の青い「New Application」ボタンを探してクリック

2. **アプリケーション名を入力**
   ```
   名前例: MovieTheaterBot
   または: 映画館情報Bot
   または: CinemaScheduleBot
   ```
   - 半角英数字推奨（日本語も可能）
   - 後から変更可能

3. **「Create」ボタンをクリック**

4. **作成完了の確認**
   - アプリケーションの詳細画面が表示されることを確認
   - 左側にメニューが表示されていることを確認

### **Step 1-3: Botユーザーの作成**

1. **左メニューから「Bot」を選択**
   - 左側のメニューリストから「Bot」をクリック

2. **「Add Bot」ボタンをクリック**
   - 「Add Bot」または「Create a Bot User」ボタンを探してクリック

3. **確認ダイアログで「Yes, do it!」をクリック**
   - Bot作成の最終確認ダイアログが表示される
   - 「Yes, do it!」ボタンをクリック

4. **Bot作成完了の確認**
   - 画面上部に「A wild bot has appeared!」のメッセージが表示される
   - Botのアイコンとユーザー名が表示される

### **Step 1-4: Bot詳細設定**

1. **Botの基本情報設定**
   
   **Username（必須）:**
   ```
   推奨名: MovieTheaterBot
   または: CinemaBot
   または: 映画館Bot
   ```
   - 変更は「Username」欄で直接編集
   - 変更後「Save Changes」をクリック

   **About Me（オプション）:**
   ```
   東京の独立系映画館情報を自動配信するBotです。
   週次通知と映画情報検索機能を提供します。
   ```

2. **Botアイコン設定（オプション）**
   - 「Click to upload an avatar」をクリック
   - 映画関連の画像ファイル（PNG/JPG、推奨サイズ：512x512px）を選択
   - アップロード完了後「Save Changes」をクリック

3. **重要な権限設定**
   
   **以下の設定を必ず確認・変更してください：**

   **Public Bot:**
   - ☑️ **ONにする**（チェックを入れる）
   - 理由：招待URL生成に必要（個人使用でもONが必要）

   **Requires OAuth2 Code Grant:**
   - ☑️ **OFFのまま**（チェックしない）

   **Privileged Gateway Intents:**
   - **Presence Intent:** ☑️ OFF（チェックしない）
   - **Server Members Intent:** ☑️ OFF（チェックしない）
   - **Message Content Intent:** ☑️ **ONにする**（チェックする）★重要

4. **設定保存**
   - すべての設定完了後「Save Changes」をクリック

### **Step 1-5: Botトークンの取得**

⚠️ **重要：トークンは秘密情報です。第三者に教えないでください。**

1. **「Token」セクションを探す**
   - Bot設定画面の中央部分にある「Token」セクション

2. **トークンの表示**
   - 「Click to Reveal Token」または「Copy」ボタンをクリック
   - トークンが表示される（例：MTI4O...長いランダムな文字列）

3. **トークンのコピーと保存**
   ```bash
   # トークンをメモ帳などに一時保存
   例: DISCORD_BOT_TOKEN=MTI4O...あなたの実際のボットトークン
   ```
   - 「Copy」ボタンでクリップボードにコピー
   - テキストファイルに一時保存（後で使用）

⚠️ **セキュリティ注意：**
- トークンを他人に見せない
- GitHubなどに公開しない
- 漏洩した場合は「Regenerate」で新しいトークンを生成

## 🔐 **Phase 2: Bot権限とOAuth2設定**

### **Step 2-1: OAuth2設定画面に移動**

1. **左メニューから「OAuth2」を選択**
   - 「OAuth2」→「URL Generator」をクリック

### **Step 2-2: Scopesの設定**

**Scopesセクションで以下をチェック：**
- ☑️ **bot** ★必須
- ☐ applications.commands（オプション、今回は不要）

### **Step 2-3: Bot Permissions の詳細設定**

**Scopesで「bot」を選択すると「Bot Permissions」セクションが表示されます。**

**必須権限（必ずチェック）：**
- ☑️ **Send Messages** - メッセージ送信
- ☑️ **Send Messages in Threads** - スレッド内メッセージ送信
- ☑️ **Embed Links** - リッチメッセージ送信
- ☑️ **Read Message History** - メッセージ履歴読み取り

**推奨権限（機能向上のため）：**
- ☑️ **Attach Files** - ファイル添付
- ☑️ **Use External Emojis** - 外部絵文字使用
- ☑️ **Add Reactions** - リアクション追加

**不要な権限（チェックしない）：**
- ☐ Administrator
- ☐ Manage Server
- ☐ Manage Channels
- ☐ Kick Members
- ☐ Ban Members

### **Step 2-4: 招待URLの生成**

1. **URLのコピー**
   - 画面下部の「Generated URL」欄に自動生成されたURLが表示される
   - URLをコピー（例：https://discord.com/api/oauth2/authorize?client_id=123456789&permissions=274877908992&scope=bot）

2. **URLの保存**
   - このURLを一時的にメモ帳に保存
   - Bot招待時に使用します

## 🏠 **Phase 3: Discordサーバーでの設定**

### **Step 3-1: サーバーでのチャンネル作成**

1. **対象サーバーを選択**
   - Bot設置予定のDiscordサーバーを開く
   - サーバー管理者権限があることを確認

2. **週次通知用チャンネル作成**
   
   **チャンネル作成手順：**
   - サーバー名の右にある「+」ボタンをクリック
   - 「テキストチャンネルを作成」を選択
   
   **チャンネル設定：**
   ```
   チャンネル名: weekly-movies
   チャンネルトピック: 映画館の週次上映情報をお届けします
   カテゴリ: お好みで選択
   プライベートチャンネル: 必要に応じて設定
   ```
   - 「チャンネルを作成」をクリック

3. **質問対応用チャンネル作成**
   
   **同様の手順で2つ目のチャンネル作成：**
   ```
   チャンネル名: movie-questions
   チャンネルトピック: 映画に関する質問をお気軽にどうぞ
   カテゴリ: 上記と同じカテゴリ推奨
   ```

4. **チャンネル作成完了確認**
   - 2つのチャンネルが作成されていることを確認
   - チャンネル名が設定と完全に一致していることを確認

### **Step 3-2: Botのサーバー招待**

1. **招待URLにアクセス**
   - Phase 2-4で取得したURLをブラウザで開く
   - 例：https://discord.com/api/oauth2/authorize?client_id=123456789&permissions=274877908992&scope=bot

2. **サーバー選択**
   - 「サーバーを選択」ドロップダウンから対象サーバーを選択
   - 管理者権限があるサーバーのみ表示される

3. **権限確認**
   - 表示される権限リストを確認
   - 以下の権限が含まれていることを確認：
     ```
     ✓ メッセージを送信
     ✓ メッセージ履歴を読む  
     ✓ リンクを埋め込む
     ✓ ファイルを添付
     ✓ スレッドでメッセージを送信
     ```

4. **Bot招待実行**
   - 「はい」または「認証」ボタンをクリック
   - reCAPTCHA認証が表示された場合は完了

5. **招待完了確認**
   - サーバーにBotが参加していることを確認
   - メンバーリストにBotが表示される
   - Botがオフライン状態であることを確認（まだ起動していないため）

## 💻 **Phase 4: サーバー環境での設定**

### **Step 4-1: プロジェクトディレクトリの確認**

```bash
# scraping_theatreディレクトリに移動
cd /home/ubuntu/scraping_theatre

# ファイル構成確認
ls -la
```

**確認すべきファイル・ディレクトリ：**
```
drwxr-xr-x  ubuntu ubuntu    config/           # 設定ファイル(.env.example)
drwxr-xr-x  ubuntu ubuntu    src/              # メインソースコード
drwxr-xr-x  ubuntu ubuntu    docs/             # ドキュメント
drwxr-xr-x  ubuntu ubuntu    data/             # データ出力先
drwxr-xr-x  ubuntu ubuntu    logs/             # ログファイル
-rw-r--r--  ubuntu ubuntu    run_discord_bot.py   # Discord Bot実行スクリプト
-rw-r--r--  ubuntu ubuntu    run_scraping.py     # スクレイピング実行スクリプト
-rw-r--r--  ubuntu ubuntu    pyproject.toml      # Python設定とパッケージ管理
-rw-r--r--  ubuntu ubuntu    uv.lock             # 依存関係ロックファイル
```

### **Step 4-2: 環境変数ファイルの作成**

1. **テンプレートファイルのコピー**
   ```bash
   cp config/.env.example .env
   ```

2. **権限設定**
   ```bash
   chmod 600 .env
   ```

3. **所有者確認**
   ```bash
   ls -la .env
   ```
   結果例：`-rw------- 1 ubuntu ubuntu 356 Dec 25 10:00 .env`

### **Step 4-3: 環境変数の設定**

1. **.envファイルを開く**
   ```bash
   nano .env
   ```

2. **設定値の入力**
   
   **Phase 1-5で取得したBotトークンを設定：**
   ```bash
   # Discord Bot設定（必須）
   DISCORD_BOT_TOKEN=ここにPhase1-5で取得したトークンを貼り付け
   
   # 例（実際のトークンに置き換えてください）：
   # DISCORD_BOT_TOKEN=MTI4O...あなたの実際のボットトークン
   ```

   **チャンネル設定（Phase 3-1で作成したチャンネル名と一致させる）：**
   ```bash
   DISCORD_MAIN_CHANNEL_NAME=weekly-movies
   DISCORD_DETAIL_CHANNEL_NAME=movie-questions
   ```

   **スケジュール設定：**
   ```bash
   WEEKLY_REPORT_TIME=MON 07:30
   DATA_UPDATE_INTERVAL=6
   TIMEZONE=Asia/Tokyo
   ```

   **機能設定：**
   ```bash
   ENABLE_PLAYWRIGHT_SEARCH=true
   ENABLE_AI_RESPONSES=false
   CACHE_DURATION_HOURS=24
   MAX_SEARCH_RESULTS=10
   ```

3. **ファイル保存と終了**
   - `Ctrl + X` でnano終了
   - `Y` で保存確認
   - `Enter` でファイル名確定

4. **設定内容の確認**
   ```bash
   cat .env
   ```
   - BOTトークンが正しく設定されていることを確認
   - チャンネル名が作成したものと一致していることを確認

### **Step 4-4: 依存関係のインストール**

1. **uvのインストール（未インストールの場合）**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```

2. **プロジェクト依存関係のインストール**
   ```bash
   uv sync
   ```

3. **インストール確認**
   ```bash
   uv run python -c "import discord; print(f'discord.py {discord.__version__}')"
   ```
   結果例：`discord.py 2.3.2`

## 🧪 **Phase 5: 動作テストと検証**

### **Step 5-1: Bot起動テスト**

1. **テスト起動実行**
   ```bash
   uv run python run_discord_bot.py
   ```

2. **起動ログの確認**
   
   **正常な起動ログ例：**
   ```
   🤖 Discord 映画館Bot 起動中...
   ✅ 環境変数を読み込みました: /home/ubuntu/scraping_theatre/.env
   
   📋 Bot設定:
     • メインチャンネル: weekly-movies
     • 質問チャンネル: movie-questions
     • 週次レポート時刻: MON 07:30
     • Playwright検索: 有効
   
   🚀 Bot を起動しています...
   Combined Movie Bot logged in as MovieTheaterBot#1234
   Found main channel: weekly-movies (123456789012345678)
   Found detail channel: movie-questions (987654321098765432)
   ```

3. **エラーが発生した場合の対処**
   
   **エラー例1: 認証エラー**
   ```
   discord.errors.LoginFailure: Improper token has been passed.
   ```
   **対処法：**
   - .envファイルのDISCORD_BOT_TOKENを再確認
   - トークンにスペースや改行が含まれていないか確認
   - Discord Developer Portalで新しいトークンを生成

   **エラー例2: チャンネルが見つからない**
   ```
   Channel not found: weekly-movies
   ```
   **対処法：**
   - Discordサーバーでチャンネル名を再確認
   - .envファイルのチャンネル名設定を確認
   - Botが該当サーバーに参加しているか確認

### **Step 5-2: Discord側での動作確認**

1. **Botのオンライン状態確認**
   - Discordサーバーのメンバーリストを確認
   - Bot名の横に緑色の「オンライン」マークが表示されていることを確認

2. **ステータスメッセージ確認**
   - Botのステータスに「東京の映画館情報 | !help でコマンド一覧」が表示されることを確認

### **Step 5-3: コマンド機能テスト**

1. **ヘルプコマンドテスト**
   - どちらかのチャンネルで以下を入力：
   ```
   !help
   ```
   
   **期待される応答：**
   ```
   🤖 映画館Bot ヘルプ
   
   📅 週次通知
   毎週月曜日 7:30 に今週・来週の上映映画をお知らせ
   
   💬 映画質問（#映画-質問チャンネル）
   • 「映画タイトル」について教えて
   • 映画館名の今週の上映予定は？
   • 監督「監督名」の作品を教えて
   
   🎭 対応映画館
   ケイズシネマ、ポレポレ東中野、ユーロスペース
   下高井戸シネマ、早稲田松竹、新宿武蔵野館
   
   Powered by 映画館スクレイピングシステム
   ```

2. **ステータスコマンドテスト**
   ```
   !status
   ```
   
   **期待される応答：**
   ```
   📊 Bot ステータス
   
   🤖 Bot: ✅ 稼働中
   📅 週次通知: ✅ アクティブ
   💬 質問対応: ✅ アクティブ
   📢 メインチャンネル: #weekly-movies
   ❓ 質問チャンネル: #movie-questions
   🎬 対応映画館: 6館
   ```

### **Step 5-4: 質問機能テスト**

1. **movie-questionsチャンネルでテスト**
   - `#movie-questions` チャンネルに移動
   - 以下のメッセージを送信：
   ```
   ケイズシネマについて教えて
   ```

2. **Bot応答の確認**
   - Botが「入力中...」状態になることを確認
   - 数秒後にBot応答が表示されることを確認

3. **応答内容の確認**
   - 映画館情報または「情報が見つかりませんでした」のメッセージが表示される
   - エラーメッセージが表示されないことを確認

## 🔄 **Phase 6: 自動起動とプロセス管理**

### **Step 6-1: systemdサービスファイル作成**

1. **サービスファイル作成**
   ```bash
   sudo nano /etc/systemd/system/discord-movie-bot.service
   ```

2. **サービス設定記述**
   ```ini
   [Unit]
   Description=Discord Movie Theater Bot
   After=network.target
   Wants=network-online.target
   
   [Service]
   Type=simple
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/home/ubuntu/scraping_theatre
   Environment=PATH=/home/ubuntu/.cargo/bin:/usr/local/bin:/usr/bin:/bin
   ExecStart=/home/ubuntu/.cargo/bin/uv run python run_discord_bot.py
   Restart=always
   RestartSec=10
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **ファイル保存**
   - `Ctrl + X` → `Y` → `Enter`

### **Step 6-2: systemdサービス有効化**

1. **systemd設定再読み込み**
   ```bash
   sudo systemctl daemon-reload
   ```

2. **サービス有効化**
   ```bash
   sudo systemctl enable discord-movie-bot.service
   ```

3. **サービス開始**
   ```bash
   sudo systemctl start discord-movie-bot.service
   ```

4. **サービス状態確認**
   ```bash
   sudo systemctl status discord-movie-bot.service
   ```
   
   **正常な状態表示例：**
   ```
   ● discord-movie-bot.service - Discord Movie Theater Bot
        Loaded: loaded (/etc/systemd/system/discord-movie-bot.service; enabled; vendor preset: enabled)
        Active: active (running) since Mon 2024-12-25 10:00:00 JST; 5min ago
      Main PID: 12345 (python)
         Tasks: 3 (limit: 1137)
        Memory: 45.2M
        CGroup: /system.slice/discord-movie-bot.service
                └─12345 /home/ubuntu/scraping_theatre/venv/bin/python run_discord_bot.py
   ```

### **Step 6-3: ログ監視設定**

1. **リアルタイムログ確認**
   ```bash
   sudo journalctl -u discord-movie-bot.service -f
   ```

2. **ログローテーション設定**
   ```bash
   sudo nano /etc/logrotate.d/discord-movie-bot
   ```
   
   ```
   /var/log/discord_bot.log {
       daily
       missingok
       rotate 7
       compress
       delaycompress
       notifempty
       copytruncate
   }
   ```

## 🔧 **Phase 7: 週次通知テスト**

### **Step 7-1: 手動週次レポート送信テスト**

1. **テスト用スクリプト作成**
   ```bash
   nano test_weekly_report.py
   ```

2. **テストスクリプト内容**
   ```python
   #!/usr/bin/env python3
   import asyncio
   from src.discord_bot.discord_bot_main import CombinedMovieBot
   
   async def test_weekly_report():
       bot = CombinedMovieBot()
       await bot.setup_hook()
       await bot._send_weekly_report()
       print("週次レポート送信テスト完了")
   
   if __name__ == "__main__":
       asyncio.run(test_weekly_report())
   ```

3. **テスト実行**
   ```bash
   uv run python test_weekly_report.py
   ```

4. **結果確認**
   - `#weekly-movies` チャンネルに週次レポートが投稿されることを確認

### **Step 7-2: 週次スケジュール確認**

1. **crontab確認**
   ```bash
   sudo systemctl status cron
   ```

2. **時刻設定確認**
   ```bash
   timedatectl
   ```
   - TimeZone が Asia/Tokyo になっていることを確認

## ✅ **Phase 8: 最終動作確認チェックリスト**

### **必須確認項目**

- [ ] **Discord Developer Portal設定完了**
  - [ ] Bot作成済み
  - [ ] Message Content Intent有効
  - [ ] トークン取得済み

- [ ] **Discordサーバー設定完了**
  - [ ] #weekly-movies チャンネル作成済み
  - [ ] #movie-questions チャンネル作成済み
  - [ ] Bot招待済み
  - [ ] Bot権限設定済み

- [ ] **サーバー環境設定完了**
  - [ ] .envファイル設定済み
  - [ ] 依存関係インストール済み
  - [ ] 環境変数正常読み込み

- [ ] **Bot機能動作確認済み**
  - [ ] Bot起動成功
  - [ ] !helpコマンド応答
  - [ ] !statusコマンド応答
  - [ ] 質問機能動作

- [ ] **自動化設定完了**
  - [ ] systemdサービス設定
  - [ ] 自動起動有効化
  - [ ] ログ出力正常

- [ ] **週次機能確認済み**
  - [ ] 手動週次レポート送信成功
  - [ ] 時刻設定確認済み

## 🆘 **トラブルシューティング**

### **よくある問題と解決法**

#### **問題1: Botトークンエラー**
```
discord.errors.LoginFailure: Improper token has been passed.
```
**解決手順：**
1. Discord Developer Portalでトークンを再生成
2. .envファイルの更新
3. Bot再起動

#### **問題2: チャンネル権限エラー**
```
discord.errors.Forbidden: 403 Forbidden
```
**解決手順：**
1. Botロールの権限確認
2. チャンネル固有権限の確認
3. Bot再招待

#### **問題3: 週次通知が送信されない**
**確認手順：**
1. システム時刻確認：`date`
2. cron動作確認：`sudo systemctl status cron`
3. Bot起動状態確認：`sudo systemctl status discord-movie-bot`
4. ログ確認：`sudo journalctl -u discord-movie-bot -f`

#### **問題4: メモリ不足エラー**
**対処法：**
1. システムリソース確認：`htop`
2. 不要プロセス停止
3. スワップ領域追加

### **緊急時の連絡先・参考資料**

- **Discord Developer Documentation**: https://discord.com/developers/docs
- **discord.py Documentation**: https://discordpy.readthedocs.io/
- **Ubuntu Server ガイド**: https://ubuntu.com/server/docs

## 🎉 **セットアップ完了おめでとうございます！**

このガイドに従って設定を完了すると、以下の機能が利用可能になります：

- ✅ **週次映画情報自動配信**（毎週月曜日7:30）
- ✅ **映画情報インタラクティブ検索**
- ✅ **6つの独立系映画館対応**
- ✅ **24時間自動稼働**
- ✅ **安全な温度監視付き**

何かご不明な点がございましたら、このガイドの該当セクションを再度ご確認ください。

---
*最終更新: 2024年12月25日*
*作成者: Claude (Anthropic)*