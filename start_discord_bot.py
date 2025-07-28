#!/usr/bin/env python3
"""
Discord Bot起動スクリプト
相対インポートの問題を解決してDiscord Botを起動
"""

import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Discord Bot関連のモジュールを直接実行
if __name__ == "__main__":
    from src.discord_bot.simple_discord_bot import SimpleMovieBot
    import asyncio
    import logging
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Discord Bot起動
    bot = SimpleMovieBot()
    
    try:
        asyncio.run(bot.run_bot())
    except KeyboardInterrupt:
        print("\nBot停止中...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()