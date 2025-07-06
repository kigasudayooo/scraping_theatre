# 映画館スクレイピングシステム

東京の独立系映画館から映画情報とスケジュール情報を自動取得するPythonシステムです。

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

## 📁 プロジェクト構成

```
scraping_theatre/
├── models.py                 # データモデル定義
├── base_scraper.py          # 基底スクレイパークラス
├── main.py                  # メイン実行ファイル
├── run_scraping.py         # 実行スクリプト
├── scrapers/               # 映画館別スクレイパー
│   ├── ks_cinema_scraper.py
│   ├── pole_pole_scraper.py
│   ├── eurospace_scraper.py
│   ├── shimotakaido_scraper.py
│   ├── waseda_shochiku_scraper.py
│   └── shinjuku_musashino_scraper.py
├── html/                   # 参考HTMLファイル
└── README_scraping.md      # 詳細技術仕様
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

## 🛠️ 技術的特徴

- **抽象化設計**: 基底クラスによる共通機能実装
- **堅牢性**: エラーハンドリング・リクエスト間隔調整
- **拡張性**: 新映画館の追加が容易
- **JavaScript対応**: Selenium使用でSPA対応

## 📋 要件

- Python 3.8+
- BeautifulSoup4, Selenium, requests
- Chrome WebDriver（一部サイト用）

## ⚠️ 注意事項

- 各サイトの利用規約を遵守してください
- サーバーに負荷をかけないよう適切な間隔でアクセス
- サイト構造変更により取得できない場合があります

## 📖 詳細仕様

技術的な詳細については [README_scraping.md](README_scraping.md) をご覧ください。