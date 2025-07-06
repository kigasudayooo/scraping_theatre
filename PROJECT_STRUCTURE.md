# プロジェクト構造ドキュメント

映画館スクレイピング＋Discord Botシステムの整理されたディレクトリ構造です。

## 📁 **整理後のディレクトリ構造**

```
scraping_theatre/
├── 📚 **ルートレベル**
│   ├── README.md                    # プロジェクト概要
│   ├── CLAUDE.md                    # Claude指示書
│   ├── LICENSE                      # ライセンス
│   ├── pyproject.toml              # Python設定
│   ├── requirements.txt            # 依存関係
│   ├── uv.lock                     # 依存関係ロック
│   ├── run_scraping.py            # スクレイピング実行
│   └── run_discord_bot.py         # Discord Bot実行
│
├── 📦 **src/ - ソースコード**
│   ├── __init__.py
│   ├── scraping/                   # スクレイピングモジュール
│   │   ├── __init__.py
│   │   ├── models.py              # データモデル
│   │   ├── base_scraper.py        # 基底スクレイパー
│   │   ├── main.py                # メイン実行ファイル
│   │   └── scrapers/              # 映画館別スクレイパー
│   │       ├── __init__.py
│   │       ├── ks_cinema_scraper.py
│   │       ├── pole_pole_scraper.py
│   │       ├── eurospace_scraper.py
│   │       ├── shimotakaido_scraper.py
│   │       ├── waseda_shochiku_scraper.py
│   │       └── shinjuku_musashino_scraper.py
│   │
│   ├── discord_bot/               # Discord Botモジュール
│   │   ├── __init__.py
│   │   ├── discord_bot_main.py    # Bot統合実行
│   │   ├── weekly_notifier.py     # 週次通知機能
│   │   ├── interactive_bot.py     # インタラクティブ機能
│   │   ├── discord_config.py      # 設定管理
│   │   └── discord_models.py      # Discordデータモデル
│   │
│   └── utils/                     # ユーティリティ
│       ├── __init__.py
│       ├── html_analyzer.py       # HTML構造解析
│       ├── batch_scraper.py       # バッチ処理
│       ├── scrape_all_html.py     # 全HTML処理
│       └── scrape_single_html.py  # 単一HTML処理
│
├── 📖 **docs/ - ドキュメント**
│   ├── README_scraping.md         # スクレイピング詳細
│   ├── README_discord_bot.md      # Discord Bot詳細
│   ├── DISCORD_BOT_SETUP_GUIDE.md # Bot設定ガイド
│   └── scraping_scripts.md       # 日本語ドキュメント
│
├── ⚙️ **config/ - 設定ファイル**
│   ├── .env.example              # 環境変数テンプレート
│   └── discord_requirements.txt  # Discord専用依存関係
│
├── 📊 **data/ - データ保存**
│   └── (実行時にファイルが生成される)
│
├── 📝 **logs/ - ログファイル**
│   └── (実行時にファイルが生成される)
│
└── 📄 **html/ - 参考HTMLファイル**
    ├── ポレポレ東中野：オフィシャルサイト.html
    ├── ユーロスペース.html
    ├── 上映スケジュール _ ケイズシネマ.html
    ├── 上映スケジュール _ 下高井戸シネマ.html
    ├── 新宿武蔵野館上映スケジュール.html
    └── 早稲田松竹 official web site _ 高田馬場の名画座.html
```

## 🔧 **モジュール分割の利点**

### **1. 関心の分離**
- **scraping/**: 映画館データ取得に特化
- **discord_bot/**: Discord機能に特化  
- **utils/**: 共通ユーティリティ

### **2. 保守性向上**
- 機能別にファイルが整理されている
- 依存関係が明確
- テストが書きやすい構造

### **3. 拡張性**
- 新しい映画館の追加が容易
- Discord機能の拡張が独立
- ユーティリティの再利用性

## 📋 **インポートパス変更**

### **スクレイピング関連**
```python
# 変更前
from models import MovieInfo
from base_scraper import BaseScraper

# 変更後
from src.scraping.models import MovieInfo
from src.scraping.base_scraper import BaseScraper
```

### **Discord Bot関連**
```python
# 変更前
from discord_models import BotQuery
from discord_config import load_config

# 変更後
from src.discord_bot.discord_models import BotQuery
from src.discord_bot.discord_config import load_config
```

## 🚀 **実行方法**

### **スクレイピング実行**
```bash
# 変更なし（run_scraping.pyが自動でパス調整）
python run_scraping.py all
```

### **Discord Bot実行**
```bash
# 変更なし（run_discord_bot.pyが自動でパス調整）
python run_discord_bot.py
```

## 📦 **設定ファイルの場所**

### **環境変数設定**
```bash
# 設定ファイルをルートにコピー
cp config/.env.example .env
```

### **Discord専用設定**
```bash
# Discord専用依存関係
pip install -r config/discord_requirements.txt
```

## 🔄 **移行済み変更点**

1. **ファイル移動完了**
   - 全ファイルが適切なディレクトリに配置
   - `__init__.py` ファイル追加完了

2. **インポートパス修正完了**
   - 相対インポートに変更
   - 実行スクリプトのパス調整完了

3. **ディレクトリ構造最適化**
   - src/配下にモジュール整理
   - docs/に全ドキュメント集約
   - config/に設定ファイル集約

これで、プロフェッショナルなPythonプロジェクト構造に整理されました！