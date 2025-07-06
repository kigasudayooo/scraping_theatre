# 映画館スクレイピングシステム

このシステムは東京の独立系映画館から映画情報とスケジュール情報を自動取得します。

## 対応映画館

1. **ケイズシネマ** (ks_cinema) - https://www.ks-cinema.com
2. **ポレポレ東中野** (pole_pole) - https://pole2.co.jp  
3. **ユーロスペース** (eurospace) - https://www.eurospace.co.jp
4. **下高井戸シネマ** (shimotakaido) - https://shimotakaido-cinema.stores.jp
5. **早稲田松竹** (waseda_shochiku) - http://wasedashochiku.co.jp
6. **新宿武蔵野館** (shinjuku_musashino) - https://shinjuku.musashino-k.jp

## 取得データ

### 1. 基本映画情報
- タイトル（日本語・英語）
- 監督
- 出演者
- ジャンル
- 上映時間
- レーティング
- あらすじ
- ポスター画像URL

### 2. 上映スケジュール
- 映画館名
- 映画タイトル
- 上映日時
- スクリーン情報
- チケット購入URL

### 3. 映画館情報
- 名前
- 公式サイトURL
- 住所
- 電話番号
- アクセス情報
- スクリーン数

## システム構成

```
scraping_theatre/
├── models.py                    # データモデル定義
├── base_scraper.py             # 基底スクレイパークラス
├── scrapers/                   # 各映画館専用スクレイパー
│   ├── ks_cinema_scraper.py
│   ├── pole_pole_scraper.py
│   ├── eurospace_scraper.py
│   ├── shimotakaido_scraper.py
│   ├── waseda_shochiku_scraper.py
│   └── shinjuku_musashino_scraper.py
├── main.py                     # メイン実行ファイル
├── run_scraping.py            # 実行スクリプト
└── requirements.txt           # 依存関係
```

## 使用方法

### 1. 環境設定

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# Chrome WebDriverの設定（Seleniumを使用する場合）
# ChromeDriverをPATHに追加するか、適切な場所に配置
```

### 2. 実行コマンド

```bash
# 利用可能な映画館一覧表示
python run_scraping.py list

# 単一映画館でテスト実行
python run_scraping.py test

# 特定映画館のスクレイピング
python run_scraping.py ks_cinema

# 全映画館のスクレイピング
python run_scraping.py all
```

### 3. 出力ファイル

スクレイピング結果は `output/` ディレクトリに保存されます：

- `{theater_key}_{timestamp}.json` - 個別映画館データ
- `all_theaters_{timestamp}.json` - 全映画館統合データ
- `summary_report_{timestamp}.json` - サマリーレポート
- `scraping.log` - 実行ログ

## データ形式例

```json
{
  "theater_info": {
    "name": "ケイズシネマ",
    "url": "https://www.ks-cinema.com",
    "address": "東京都新宿区...",
    "phone": "03-xxxx-xxxx",
    "access": "JR新宿駅より...",
    "screens": 1
  },
  "movies": [
    {
      "title": "映画タイトル",
      "title_en": "Movie Title",
      "director": "監督名",
      "cast": ["出演者1", "出演者2"],
      "genre": "ドラマ",
      "duration": 120,
      "synopsis": "あらすじ...",
      "poster_url": "https://..."
    }
  ],
  "schedules": [
    {
      "theater_name": "ケイズシネマ",
      "movie_title": "映画タイトル",
      "showtimes": [
        {
          "date": "2024-07-06",
          "times": ["10:00", "14:30", "19:00"],
          "screen": "スクリーン1",
          "ticket_url": "https://..."
        }
      ]
    }
  ],
  "scraped_at": "2024-07-06T15:30:00"
}
```

## 技術的特徴

### 抽象化設計
- `BaseScraper` クラスによる共通機能の実装
- 各映画館専用のスクレイパークラスで個別対応
- データモデルによる型安全性の確保

### 堅牢性対策
- リクエスト間隔の調整
- エラーハンドリング
- ログ出力
- Selenium使用によるJavaScript対応

### 拡張性
- 新しい映画館の追加が容易
- 設定ベースでのカスタマイズ
- モジュラー設計

## 注意事項

1. **利用規約の遵守**: 各サイトの利用規約を確認してください
2. **アクセス頻度**: サーバーに負荷をかけないよう適切な間隔でアクセス
3. **データの精度**: サイト構造の変更により取得できない場合があります
4. **セレニウム設定**: 一部サイトではWebDriverが必要です

## トラブルシューティング

### SSL/TLS エラー
一部のサイトでSSL証明書の問題が発生する場合があります。

### アクセス拒否（403エラー）
サイトによってはBot検知により拒否される場合があります。

### データ取得失敗
サイト構造の変更により、セレクタの更新が必要な場合があります。

## 今後の改善予定

- [ ] より堅牢なエラーハンドリング
- [ ] 並列処理による高速化
- [ ] データベース連携
- [ ] API化
- [ ] 定期実行スケジュール機能