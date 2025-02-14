# 下高井戸シネマ 上映スケジュール取得・管理マニュアル

## 目次
1. [概要](#概要)
2. [環境セットアップ](#環境セットアップ)
3. [Google Cloud Platform設定](#google-cloud-platform設定)
4. [スクレイピングスクリプトの実行](#スクレイピングスクリプトの実行)
5. [トラブルシューティング](#トラブルシューティング)

## 概要

このシステムでは、下高井戸シネマの上映スケジュールをウェブサイトから自動取得し、整理された形式でGoogle Spreadsheetに保存します。

### 主な機能
- ウェブサイトからの映画情報の自動取得
- 以下の情報を構造化されたデータとして整理
  - 映画タイトル
  - 制作年/国/時間
  - 監督/出演者情報
  - 概要
  - 上映スケジュール
  - 料金情報
  - 受賞歴
  - イベント情報（舞台挨拶など）
- Google Spreadsheetへの自動アップロード
- 日付別のシート管理

## 環境セットアップ

### 1. Pythonのインストール
1. [Python公式サイト](https://www.python.org/downloads/)から最新版をダウンロード
2. インストーラーを実行（「Add Python to PATH」にチェックを入れる）
3. コマンドプロンプトで確認:
   ```bash
   python --version
   ```

### 2. 必要なパッケージのインストール
コマンドプロンプトで以下を実行:
```bash
pip install pandas beautifulsoup4 requests gspread oauth2client
```

各パッケージの役割:
- pandas: データ処理用
- beautifulsoup4: HTMLパース用
- requests: ウェブリクエスト用
- gspread: Google Sheets API操作用
- oauth2client: Google認証用

## Google Cloud Platform設定

### 1. プロジェクトの作成
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新規プロジェクトを作成
   - 右上のプロジェクト選択 → 「新しいプロジェクト」
   - プロジェクト名を入力（例：「cinema-schedule」）
   - 「作成」をクリック

### 2. APIの有効化
1. 左メニューから「APIとサービス」→「ライブラリ」
2. 以下のAPIを検索し有効化:
   - Google Sheets API
   - Google Drive API

### 3. サービスアカウントの作成
1. 左メニューから「IAM と管理」→「サービスアカウント」
2. 「サービスアカウントを作成」をクリック
3. 必要事項を入力:
   - サービスアカウント名（例：「cinema-schedule」）
   - 説明（任意）
4. 役割を選択:
   - 「基本」→「編集者」を選択

### 4. 認証情報の取得
1. 作成したサービスアカウントをクリック
2. 「鍵」タブ→「鍵を追加」→「新しい鍵を作成」
3. JSONを選択してダウンロード
4. ダウンロードしたJSONファイルを安全な場所に保存
5. ファイル名を`credentials.json`に変更

## スクレイピングスクリプトの実行

### 1. スクリプトの準備
提供したPythonコードを`movie_scraper.py`として保存

### 2. 認証情報の設定
1. `credentials.json`をスクリプトと同じフォルダに配置
2. スクリプト内の以下の部分を編集:
```python
credentials_path = 'credentials.json'  # 認証情報ファイルのパス
spreadsheet_name = '下高井戸シネマ上映スケジュール'  # 任意のスプレッドシート名
```

### 3. スクリプトの実行
コマンドプロンプトで以下を実行:
```bash
python movie_scraper.py
```

### 4. 結果の確認
- 実行が成功すると、Google Driveに新しいスプレッドシートが作成されます
- スプレッドシートには日付付きのシートが作成され、最新の上映スケジュールが反映されます

## トラブルシューティング

### よくあるエラーと解決方法

1. ModuleNotFoundError
```
エラー: ModuleNotFoundError: No module named 'xxx'
解決: pip install xxxで必要なパッケージをインストール
```

2. 認証エラー
```
エラー: google.auth.exceptions.DefaultCredentialsError
解決: credentials.jsonの配置場所と内容を確認
```

3. スプレッドシートアクセスエラー
```
エラー: gspread.exceptions.SpreadsheetNotFound
解決: スプレッドシート名が正しいか確認
```

### 補足情報

- スクリプトは定期的に実行することで、最新の上映スケジュールを自動的に取得できます
- 取得したデータは日付別のシートとして保存されるため、履歴管理も可能です
- エラーが発生した場合は、エラーメッセージを確認し、上記のトラブルシューティングを参照してください

## サポート

問題が解決しない場合は、以下の情報を添えてご連絡ください：
1. 発生したエラーメッセージ
2. 実行環境（OS、Pythonバージョン）
3. 実行したコマンド

# コード解説

## スクレイピング部分の解説

### 主要な関数と役割

#### 1. `scrape_movie_info` 関数
```python
def scrape_movie_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    movies_data = []
    # ...
```
- HTMLコンテンツを解析して映画情報を抽出する主要な関数
- BeautifulSoupを使用してHTMLを解析
- 各映画の情報を辞書形式で保存

#### 2. `process_movie_box` 関数
```python
def process_movie_box(box, is_special=False, special_title=None):
    title_elem = box.find('span', class_='eiga-title')
    # ...
```
- 個々の映画情報ブロックを処理
- 通常の映画と特集上映で異なる処理を実行
- 以下の要素を抽出:
  - タイトル: `class='eiga-title'`
  - 基本情報: `class='stuff'`
  - 概要: `class='note'`
  - 上映時間: `class='day'`
  - 料金: `class='price'`
  - 受賞歴: `class='syo'`
  - イベント情報: `class='p3'`

#### 3. `clean_text` 関数
```python
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    return text
```
- テキストデータのクリーニング
- 余分な空白や改行を整理
- nullの場合は空文字を返す

## Google Sheets連携部分の解説

### 1. `upload_to_sheets` 関数
```python
def upload_to_sheets(df, credentials_path, spreadsheet_name):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    # ...
```
- DataFrameをGoogle Sheetsにアップロード
- 認証情報を使用してGoogle APIに接続
- 新しいスプレッドシートまたはシートを作成

### 主要なコード要素の説明

#### 1. スコープの設定
```python
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
```
- Google APIへのアクセス権限を定義
- Sheets APIとDrive APIの両方にアクセス

#### 2. 認証処理
```python
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
gc = gspread.authorize(credentials)
```
- JSONファイルから認証情報を読み込み
- gspreadクライアントを認証

#### 3. スプレッドシート作成/オープン
```python
try:
    workbook = gc.open(spreadsheet_name)
except gspread.SpreadsheetNotFound:
    workbook = gc.create(spreadsheet_name)
```
- 指定名のスプレッドシートを開く
- 存在しない場合は新規作成

#### 4. データ更新
```python
worksheet.update('A1', [headers])
worksheet.update('A2', data)
```
- ヘッダー行とデータを更新
- A1セルから開始してデータを配置

## エラーハンドリング

### 1. try-except文の使用
```python
try:
    # 処理
except Exception as e:
    print(f"エラーが発生しました: {e}")
```
- 各処理でエラーをキャッチ
- エラーメッセージを出力

### 2. データ検証
```python
if not title_elem:
    return None
```
- 必要なデータが存在しない場合の処理
- 無効なデータのスキップ

## 実行フロー

1. HTMLファイルの読み込み
2. BeautifulSoupでのHTML解析
3. 映画情報の抽出と整理
4. DataFrameの作成
5. Google Sheets認証
6. スプレッドシートへのデータアップロード

## カスタマイズのポイント

1. スプレッドシート名の変更:
```python
spreadsheet_name = '任意の名前'
```

2. シート名のフォーマット変更:
```python
sheet_name = f'映画情報_{datetime.now().strftime("%Y%m%d")}'
```

3. 列の並び順の変更:
```python
columns = ['タイトル', '特集名', ...]  # 任意の順序で指定
```

このコードは必要に応じて拡張や修正が可能です。例えば、データの加工処理を追加したり、異なる形式での出力を追加したりできます。