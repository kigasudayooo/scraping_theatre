#!/bin/bash
set -e

echo "🎬 Cinema Scheduler インストール開始"

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📂 プロジェクトディレクトリ: $PROJECT_DIR"

# ログディレクトリ作成
mkdir -p "$PROJECT_DIR/logs"
echo "✅ ログディレクトリ作成完了"

# Pythonの依存関係を確認
echo "🐍 Python依存関係を確認中..."
cd "$PROJECT_DIR"

if ! command -v uv &> /dev/null; then
    echo "❌ uv が見つかりません。uvをインストールしてください。"
    exit 1
fi

# schedule パッケージをインストール
uv add schedule
echo "✅ schedule パッケージインストール完了"

# systemd サービスファイルをコピー
if [ "$EUID" -eq 0 ]; then
    echo "🔧 systemd サービスファイルをインストール中..."
    cp "$PROJECT_DIR/systemd/cinema-scheduler.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "✅ systemd サービスファイルインストール完了"
    
    echo "🚀 サービスを有効化・開始中..."
    systemctl enable cinema-scheduler.service
    systemctl start cinema-scheduler.service
    
    echo "📊 サービス状態確認:"
    systemctl status cinema-scheduler.service --no-pager
else
    echo "⚠️  root権限が必要です。systemdサービスをインストールするには以下を実行してください:"
    echo "sudo $0"
    echo ""
    echo "または手動でスケジューラーを起動:"
    echo "cd $PROJECT_DIR && uv run python src/scheduler/cinema_scheduler.py"
fi

echo ""
echo "🎯 インストール完了!"
echo ""
echo "📅 スケジュール:"
echo "  - 毎週日曜日 23:00: スクレイピング実行"
echo "  - 毎週月曜日 07:30: Discord通知送信"
echo ""
echo "🧪 テスト実行:"
echo "  スクレイピングテスト: uv run python src/scheduler/cinema_scheduler.py --test scraping"
echo "  通知テスト: uv run python src/scheduler/cinema_scheduler.py --test notification"
echo "  完全テスト: uv run python src/scheduler/cinema_scheduler.py --test full"
echo ""
echo "📝 ログ確認:"
echo "  tail -f $PROJECT_DIR/logs/scheduler.log"
echo "  journalctl -u cinema-scheduler.service -f"