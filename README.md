# 映画館スクレイピング＋Discord Bot システム

東京の独立系映画館から映画情報とスケジュール情報を自動取得し、Discord経由で通知・検索できる統合システムです。

## 🎬 対応映画館

| 映画館名 | キー | URL |
|---------|-----|-----|
| ケイズシネマ | `ks_cinema` | https://www.ks-cinema.com |
| ポレポレ東中野 | `pole_pole` | https://pole2.co.jp |
| ユーロスペース | `eurospace` | https://www.eurospace.co.jp |
| 下高井戸シネマ | `shimotakaido` | https://shimotakaido-cinema.stores.jp |
| 早稲田松竹 | `waseda_shochiku` | http://wasedashochiku.co.jp |
| 新宿武蔵野館 | `shinjuku_musashino` | https://shinjuku.musashino-k.jp |

## 📊 取得データ

### 1. 基本映画情報
- タイトル（日本語・英語）
- 監督・出演者
- ジャンル・上映時間
- あらすじ・ポスター画像

### 2. 上映スケジュール
- 上映日時・スクリーン情報
- チケット購入URL

### 3. 映画館情報
- 住所・電話番号
- アクセス情報・スクリーン数

## 🚀 クイックスタート

### 基本スクレイピング
```bash
# 依存関係インストール
pip install -r requirements.txt

# 利用可能映画館一覧
python run_scraping.py list

# 単一映画館テスト
python run_scraping.py test

# 特定映画館スクレイピング
python run_scraping.py ks_cinema

# 全映画館一括実行
python run_scraping.py all
```

### Discord Bot起動
```bash
# .envファイル作成（Botトークン設定）
cp .env.example .env

# Discord Bot起動
python run_discord_bot.py
```

## 📁 プロジェクト構成

```
scraping_theatre/
├── 🎯 スクレイピング機能
│   ├── models.py                 # データモデル定義
│   ├── base_scraper.py          # 基底スクレイパークラス
│   ├── main.py                  # メイン実行ファイル
│   ├── run_scraping.py         # 実行スクリプト
│   └── scrapers/               # 映画館別スクレイパー
│       ├── ks_cinema_scraper.py
│       ├── pole_pole_scraper.py
│       ├── eurospace_scraper.py
│       ├── shimotakaido_scraper.py
│       ├── waseda_shochiku_scraper.py
│       └── shinjuku_musashino_scraper.py
├── 🤖 Discord Bot機能
│   ├── discord_bot_main.py     # Bot統合実行ファイル
│   ├── weekly_notifier.py      # 週次通知システム
│   ├── interactive_bot.py      # インタラクティブ機能
│   ├── discord_config.py       # 設定管理
│   ├── discord_models.py       # Discordデータモデル
│   └── run_discord_bot.py     # Bot実行スクリプト
├── 📚 ドキュメント
│   ├── README_scraping.md      # スクレイピング詳細仕様
│   └── README_discord_bot.md   # Discord Bot詳細マニュアル
├── 🗂️ その他
│   ├── html/                   # 参考HTMLファイル
│   ├── .env.example           # 環境変数テンプレート
│   └── requirements.txt       # 依存関係
```

## 💾 出力形式

```json
{
  "theater_info": {
    "name": "ケイズシネマ",
    "address": "東京都新宿区...",
    "phone": "03-xxxx-xxxx"
  },
  "movies": [
    {
      "title": "映画タイトル",
      "director": "監督名",
      "cast": ["出演者1", "出演者2"],
      "synopsis": "あらすじ..."
    }
  ],
  "schedules": [
    {
      "movie_title": "映画タイトル",
      "showtimes": [
        {
          "date": "2024-07-06",
          "times": ["10:00", "14:30", "19:00"]
        }
      ]
    }
  ]
}
```

## 🤖 Discord Bot機能

### 📅 週次通知
- **送信時刻**: 毎週月曜日 朝7:30 JST
- **内容**: 今週・来週の上映映画一覧とあらすじ
- **チャンネル**: `#weekly-movies`

### 💬 インタラクティブ質問
- **チャンネル**: `#movie-questions`
- **対応質問**:
  - `「映画名」について教えて`
  - `ケイズシネマの今週の上映予定は？`
  - `監督「山田太郎」の作品を教えて`

### 🔧 Botコマンド
- `!help` - ヘルプ表示
- `!status` - Bot稼働状況
- `!update` - 手動データ更新

## 🛠️ 技術的特徴

### スクレイピングシステム
- **抽象化設計**: 基底クラスによる共通機能実装
- **堅牢性**: エラーハンドリング・リクエスト間隔調整
- **拡張性**: 新映画館の追加が容易
- **JavaScript対応**: Selenium使用でSPA対応

### Discord Bot
- **週次スケジュール通知**: 自動化された定期通知
- **自然言語処理**: 日本語質問の理解と応答
- **リアルタイム検索**: 最新映画情報の提供
- **Playwright統合**: 外部サイトからの追加情報取得

## 📋 要件

### 基本環境
- Python 3.8+
- BeautifulSoup4, Selenium, requests
- Chrome WebDriver（一部サイト用）

### Discord Bot用
- Discord Bot Token
- discord.py, python-dotenv
- Discordサーバーとチャンネル設定

## ⚠️ 注意事項

- 各サイトの利用規約を遵守してください
- サーバーに負荷をかけないよう適切な間隔でアクセス
- サイト構造変更により取得できない場合があります

## 📖 詳細マニュアル

### スクレイピングシステム
技術的な詳細については [README_scraping.md](README_scraping.md) をご覧ください。

### Discord Bot
セットアップと詳細機能については [README_discord_bot.md](README_discord_bot.md) をご覧ください。

## 🎯 使用例

### スクレイピングのみ使用
```bash
# 映画館データを取得してJSONで保存
python run_scraping.py all
```

### Discord Botのみ使用
```bash
# 環境変数設定後、Bot起動
python run_discord_bot.py
```

### 統合使用（推奨）
1. スクレイピングでデータ取得
2. Discord Botで自動通知＋質問対応
3. 定期的なデータ更新で最新情報を提供

## 📞 サポート

- **スクレイピング**: サイト構造変更により取得できない場合は、該当スクレイパーの更新が必要
- **Discord Bot**: ログファイル確認、権限・チャンネル設定の見直し
- **その他**: 各README文書を参照してください