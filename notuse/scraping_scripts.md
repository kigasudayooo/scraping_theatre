# HTMLスクレイピングスクリプト ドキュメント

このドキュメントでは、映画館のウェブサイトから映画情報を抽出するために作成されたHTMLスクレイピングスクリプトについて説明します。

## 概要

`html/`ディレクトリ内のHTMLファイルから映画情報をスクレイピングするために、4つのPythonスクリプトが作成されました：

1. **`scrape_single_html.py`** - 単一のHTMLファイルを処理
2. **`scrape_all_html.py`** - htmlディレクトリ内のすべてのHTMLファイルを処理
3. **`batch_scraper.py`** - コマンドラインオプション付きの高度なバッチ処理
4. **`html_analyzer.py`** - HTMLファイルの構造と内容を分析

## スクリプト詳細

### 1. scrape_single_html.py

**目的:** 単一のHTMLファイルから映画データを抽出

**使用方法:**
```bash
python scrape_single_html.py <html_file_path>
uv run python scrape_single_html.py html/filename.html
```

**機能:**
- 一度に1つのHTMLファイルを処理
- 入力HTMLファイルと同じ名前のCSVファイルを出力
- 抽出されたサンプルデータを表示
- シンプルなエラーハンドリング

**実行例:**
```bash
uv run python scrape_single_html.py "html/上映スケジュール _ 下高井戸シネマ.html"
```

### 2. scrape_all_html.py

**目的:** htmlディレクトリ内のすべてのHTMLファイルを自動的に処理

**使用方法:**
```bash
python scrape_all_html.py
uv run python scrape_all_html.py
```

**機能:**
- `html/`ディレクトリ内のすべての`.html`ファイルを自動検出
- 各映画館の個別CSVファイルを作成
- タイムスタンプ付きの統合CSVファイルを生成
- ソースを識別するためのシネマ名列を追加
- 各ファイルの進捗報告

**出力ファイル:**
- 個別: `data/{cinema_name}.csv`
- 統合: `data/all_cinemas_{timestamp}.csv`

### 3. batch_scraper.py

**目的:** コマンドラインオプション付きの高度なバッチ処理

**使用方法:**
```bash
python batch_scraper.py [files...] [options]
uv run python batch_scraper.py file1.html file2.html -c --verbose
```

**コマンドラインオプション:**
- `-o, --output DIR`: 出力ディレクトリ（デフォルト: data）
- `-c, --combine`: すべての結果を1つのファイルに統合
- `-v, --verbose`: サンプルデータ付きの詳細出力
- `files`: 処理するHTMLファイルのリスト

**機能:**
- 柔軟なファイル選択
- オプションのファイル統合
- 詳細な進捗報告
- シネマ名とファイル名の両方の列を追加
- タイムスタンプ付き出力ファイル

**実行例:**
```bash
# 特定ファイルを統合して処理
uv run python batch_scraper.py "html/下高井戸シネマ.html" "html/ユーロスペース.html" -c -v

# カスタムディレクトリにファイルを処理
uv run python batch_scraper.py html/*.html -o results
```

### 4. html_analyzer.py

**目的:** HTMLファイルの構造を分析し、スクレイピング互換性を識別

**使用方法:**
```bash
python html_analyzer.py all                    # すべてのファイルを分析
python html_analyzer.py <file_path>            # 単一ファイルを分析
python html_analyzer.py <file_path> detailed   # 単一ファイルの詳細分析
```

**機能:**
- HTMLファイルの構造分析
- CSSクラス使用統計
- 映画コンテンツの検出
- サンプルコンテンツの抽出
- スクレイピング互換性の評価

**分析出力:**
- ファイルサイズと基本情報
- 映画関連要素の数
- CSSクラス統計
- サンプル映画タイトルとスケジュール
- 全ファイルの統計サマリー

## データ構造

すべてのスクレイパーは以下の映画情報を抽出します：

| カラム | 説明 | 例 |
|--------|------|-----|
| タイトル | 映画タイトル | "ザ・ルーム・ネクスト・ドア" |
| 特集名 | 特集企画名 | "ジャンヌ・モロー特集" |
| 制作年/国/時間 | 制作年/国/上映時間 | "2024年/スペイン/1h47" |
| 監督/出演 | 監督・出演者 | "監督：ペドロ・アルモドバル" |
| 概要 | あらすじ | "病に侵され安楽死を望む女性と..." |
| 上映スケジュール | 上映日程 | "6/7(土)～6/13(金) 16:10～" |
| 料金 | 料金情報 | "一般1700円 / 大学・専門1300円" |
| 受賞歴 | 受賞情報 | "ヴェネチア国際映画祭 金獅子賞" |
| イベント情報 | イベント・舞台挨拶等 | "監督舞台挨拶あり" |
| シネマ名 | 映画館名 | "下高井戸シネマ" |
| ファイル名 | ソースファイル名 | "下高井戸シネマ.html" |

## 互換性結果

`html/`ディレクトリ内の6つのHTMLファイルの分析結果：

| 映画館 | ファイル | ステータス | 検出映画数 |
|--------|----------|------------|------------|
| 下高井戸シネマ | 上映スケジュール _ 下高井戸シネマ.html | ✅ **対応** | 65本 |
| ケイズシネマ | 上映スケジュール _ ケイズシネマ.html | ❌ 非対応 | 0本 |
| ポレポレ東中野 | ポレポレ東中野：オフィシャルサイト.html | ❌ 非対応 | 0本 |
| 早稲田松竹 | 早稲田松竹 official web site _ 高田馬場の名画座.html | ❌ 非対応 | 0本 |
| ユーロスペース | ユーロスペース.html | ❌ 非対応 | 0本 |
| 新宿武蔵野館 | 新宿武蔵野館上映スケジュール.html | ❌ 非対応 | 0本 |

### なぜ1つの映画館のみ対応しているのか

現在のスクレイパーは**下高井戸シネマ**のHTML構造専用に設計されており、以下の要素を使用しています：
- 各映画の`div.box`コンテナ
- 映画タイトルの`span.eiga-title`
- 特集タイトルの`span.title-s`
- 特定のCSSクラス: `.stuff`, `.note`, `.day`, `.price`, `.syo`, `.p3`

他の映画館のウェブサイトは完全に異なるHTML構造とCSSクラスを使用しており、各サイト用のカスタムスクレイパーが必要です。

## uvでの実行

すべてのスクリプトは依存関係管理にuvを使用して実行できます：

```bash
# 依存関係のインストール
uv sync

# 任意のスクリプトの実行
uv run python scrape_single_html.py "html/filename.html"
uv run python scrape_all_html.py
uv run python batch_scraper.py html/*.html -c -v
uv run python html_analyzer.py all
```

## 出力ファイル

生成されたCSVファイルは`data/`ディレクトリに保存されます：

- 個別映画館ファイル: `{cinema_name}.csv`
- 統合ファイル: `all_cinemas_{timestamp}.csv` または `batch_scraped_{timestamp}.csv`
- エンコーディング: UTF-8（日本語テキストを適切に処理）
- フォーマット: ヘッダー付き標準CSV

## エラーハンドリング

すべてのスクリプトに以下が含まれています：
- ファイル存在確認
- HTML解析エラーハンドリング
- 空データの検出
- 進捗報告
- 適切な失敗処理

## 今後の改善

他の映画館ウェブサイトをサポートするには：
1. `html_analyzer.py`を使用してHTML構造を分析
2. 映画情報のCSSセレクタを特定
3. 各映画館フォーマット用のカスタム解析関数を作成
4. 映画館固有のロジックでスクレイパーを拡張
5. 異なる映画館フォーマット用の設定ファイルを追加