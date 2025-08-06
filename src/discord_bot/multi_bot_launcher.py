#!/usr/bin/env python3
"""
マルチBot起動スクリプト
映画館情報BotとチャットBotを同時または選択的に起動する
"""

import asyncio
import logging
import argparse
import sys
from pathlib import Path

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_bot_main import CombinedMovieBot
from chat_bot import ChatBot
from discord_config import load_config

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('multi_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def run_movie_bot():
    """映画館情報Botを起動"""
    logger = logging.getLogger("movie_bot_runner")
    logger.info("Starting Movie Bot...")
    
    try:
        bot = CombinedMovieBot()
        await bot.start(bot.discord_config.token)
    except Exception as e:
        logger.error(f"Movie Bot error: {e}")
        raise

async def run_chat_bot():
    """チャットBotを起動"""
    logger = logging.getLogger("chat_bot_runner")
    logger.info("Starting Chat Bot...")
    
    try:
        bot = ChatBot()
        discord_config, _, _ = load_config()
        await bot.start(discord_config.token)
    except Exception as e:
        logger.error(f"Chat Bot error: {e}")
        raise

async def run_both_bots():
    """両方のBotを同時起動（同一トークンの場合は不可）"""
    logger = logging.getLogger("multi_bot_runner")
    logger.warning("注意: 同一のDiscordトークンでは複数のBotを同時実行できません")
    logger.info("映画館情報Botのみを起動します...")
    await run_movie_bot()

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="Discord Bot起動スクリプト")
    parser.add_argument(
        '--bot', 
        choices=['movie', 'chat', 'both'], 
        default='movie',
        help='起動するBot種別 (default: movie)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 設定チェック
    try:
        discord_config, _, bot_config = load_config()
        if not discord_config.token:
            logger.error("Discord bot token not provided")
            print("❌ Discord bot token not provided")
            print("環境変数 DISCORD_BOT_TOKEN を設定してください")
            return 1
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ 設定エラー: {e}")
        return 1
    
    # Bot起動
    try:
        if args.bot == 'movie':
            logger.info("🎬 映画館情報Botを起動します...")
            asyncio.run(run_movie_bot())
        elif args.bot == 'chat':
            logger.info("💬 チャットBotを起動します...")
            asyncio.run(run_chat_bot())
        elif args.bot == 'both':
            logger.info("🤖 両方のBotを起動します...")
            asyncio.run(run_both_bots())
            
    except KeyboardInterrupt:
        logger.info("Bot停止中...")
        print("\n✅ Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"❌ エラーが発生しました: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())