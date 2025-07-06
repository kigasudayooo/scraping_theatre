#!/usr/bin/env python3
"""
Discord Bot実行スクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def check_environment():
    """環境設定チェック"""
    required_env_vars = {
        'DISCORD_BOT_TOKEN': 'Discord Botトークン'
    }
    
    missing_vars = []
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  • {var}: {description}")
    
    if missing_vars:
        print("❌ 必要な環境変数が設定されていません:")
        print("\n".join(missing_vars))
        print("\n.env ファイルを作成するか、環境変数を設定してください。")
        print("例: .env.example を参考にしてください。")
        return False
    
    return True

def load_env_file():
    """環境変数ファイル読み込み"""
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✅ 環境変数を読み込みました: {env_file}")
        except ImportError:
            print("⚠️  python-dotenv がインストールされていません")
            print("pip install python-dotenv を実行してください")
    else:
        print("ℹ️  .env ファイルが見つかりません（環境変数で設定済みの場合は正常です）")

def main():
    """メイン実行"""
    print("🤖 Discord 映画館Bot 起動中...")
    
    # 環境変数読み込み
    load_env_file()
    
    # 環境設定チェック
    if not check_environment():
        return
    
    # 設定表示
    from src.discord_bot.discord_config import load_config
    discord_config, schedule_config, bot_config = load_config()
    
    print("\n📋 Bot設定:")
    print(f"  • メインチャンネル: {discord_config.main_channel_name}")
    print(f"  • 質問チャンネル: {discord_config.detail_channel_name}")
    print(f"  • 週次レポート時刻: {schedule_config.weekly_report_time}")
    print(f"  • Playwright検索: {'有効' if bot_config.enable_playwright_search else '無効'}")
    
    # Bot実行
    print("\n🚀 Bot を起動しています...")
    
    try:
        from src.discord_bot.discord_bot_main import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Bot を停止しています...")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()