#!/usr/bin/env python3
"""
簡素化されたDiscord Bot
相対インポートの問題を回避してBot機能を提供
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_config import load_config
from hybrid_cinema_system import HybridCinemaSystem
from ollama_client import OllamaClient

# 環境変数読み込み
load_dotenv()

class SimpleMovieBot(commands.Bot):
    """簡素化されたDiscord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # 設定読み込み
        self.discord_config, self.schedule_config, self.bot_config = load_config()
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_conversation_logging()
        
        # ハイブリッド映画システム初期化
        try:
            # Ollamaクライアント設定
            ollama_client = OllamaClient(
                model="llama3.2:3b",  # 最新のモデル
                timeout=30
            )
            self.cinema_system = HybridCinemaSystem(ollama_client)
            self.logger.info("Hybrid cinema system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize hybrid cinema system: {e}")
            self.cinema_system = None
    
    def _setup_conversation_logging(self):
        """会話ログの設定"""
        # 会話ログ用のディレクトリ作成
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # 会話ログファイルパス
        today = datetime.now().strftime("%Y-%m-%d")
        self.conversation_log_file = self.logs_dir / f"discord_conversations_{today}.jsonl"
        
        # 会話ログ用logger
        self.conversation_logger = logging.getLogger("conversation")
        handler = logging.FileHandler(self.conversation_log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.conversation_logger.addHandler(handler)
        self.conversation_logger.setLevel(logging.INFO)
        self.conversation_logger.propagate = False
    
    def log_conversation(self, user_message, bot_response, metadata=None):
        """会話をログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "metadata": metadata or {}
        }
        self.conversation_logger.info(json.dumps(log_entry, ensure_ascii=False))
            
    async def on_ready(self):
        """Bot準備完了時の処理"""
        self.logger.info(f'{self.user} としてログインしました')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # チャンネルID取得
        await self._find_channels()
        
    async def _find_channels(self):
        """チャンネル名からIDを取得"""
        for guild in self.guilds:
            self.logger.info(f'Checking guild: {guild.name}')
            for channel in guild.channels:
                if channel.name == self.discord_config.main_channel_name:
                    self.discord_config.main_channel_id = channel.id
                    self.logger.info(f'Found main channel: {channel.name} (ID: {channel.id})')
                elif channel.name == self.discord_config.detail_channel_name:
                    self.discord_config.detail_channel_id = channel.id
                    self.logger.info(f'Found detail channel: {channel.name} (ID: {channel.id})')
                    
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        if message.author == self.user:
            return
            
        # Bot への言及または質問チャンネルでの発言
        if (self.user.mentioned_in(message) or 
            (hasattr(message.channel, 'id') and 
             message.channel.id == self.discord_config.detail_channel_id)):
            
            await self._handle_movie_query(message)
            
        # コマンド処理
        await self.process_commands(message)
        
    async def _handle_movie_query(self, message):
        """映画関連の質問を処理"""
        try:
            # ハイブリッドシステム応答を試行
            if self.cinema_system and self.bot_config.enable_ai_responses:
                await self._handle_movie_query_with_hybrid(message)
            else:
                await self._handle_movie_query_fallback(message)
                
        except Exception as e:
            self.logger.error(f"Error handling movie query: {e}")
            await message.reply("申し訳ありません。エラーが発生しました。")
            
    async def _handle_movie_query_with_hybrid(self, message):
        """ハイブリッドシステムを使用した映画質問処理"""
        try:
            # ユーザー情報とチャンネル情報を取得
            user_id = str(message.author.id)
            channel_info = {
                "channel_name": message.channel.name,
                "guild_name": message.guild.name if message.guild else "DM"
            }
            
            # ハイブリッドシステム応答生成
            response = await self.cinema_system.process_query(message.content)
            
            # 会話をログに記録
            metadata = {
                "user_id": user_id,
                "user_name": message.author.name,
                "channel_name": message.channel.name,
                "guild_name": message.guild.name if message.guild else "DM",
                "response_length": len(response) if response else 0,
                "system_type": "hybrid_cinema_system"
            }
            self.log_conversation(message.content, response, metadata)
            
            if response and response.strip():
                # 長いメッセージの場合は分割
                if len(response) > 2000:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)
                    
                self.logger.info(f"Hybrid system response sent to user {message.author.name}")
            else:
                await self._handle_movie_query_fallback(message)
                
        except Exception as e:
            self.logger.error(f"Hybrid system response failed: {e}")
            await self._handle_movie_query_fallback(message)
            
    async def _handle_movie_query_fallback(self, message):
        """フォールバック応答"""
        fallback_response = (
            "映画について質問いただき、ありがとうございます。\n"
            "現在、AI応答システムが利用できません。\n"
            "以下の映画館の情報について質問できます：\n"
            "• ケイズシネマ\n"
            "• 下高井戸シネマ\n"
            "• 早稲田松竹\n"
            "• 新宿武蔵野館\n\n"
            "例：「新宿武蔵野館の今日の上映予定は？」"
        )
        await message.reply(fallback_response)
        
    @commands.command(name='ping')
    async def ping(self, ctx):
        """接続テスト"""
        await ctx.send('Pong! Bot is running!')
        
    @commands.command(name='status')
    async def status(self, ctx):
        """Bot状態確認"""
        cinema_status = "✅ 利用可能" if self.cinema_system else "❌ 利用不可"
        status_message = (
            f"**Bot Status**\n"
            f"ハイブリッド映画システム: {cinema_status}\n"
            f"映画館データ: ✅ 35作品対応\n"
            f"設定されたチャンネル: {len([c for c in [self.discord_config.main_channel_id, self.discord_config.detail_channel_id] if c])}個\n"
            f"キーワード抽出: プログラム型 + LLM型フォールバック\n"
            f"ハルシネーション対策: 完全無効化"
        )
        await ctx.send(status_message)
        
    async def run_bot(self):
        """Bot実行"""
        if not self.discord_config.token:
            self.logger.error("Discord bot token not provided")
            print("Error: DISCORD_BOT_TOKEN environment variable is not set")
            return
            
        try:
            await self.start(self.discord_config.token)
        except discord.LoginFailure:
            self.logger.error("Invalid Discord bot token")
            print("Error: Invalid Discord bot token")
        except Exception as e:
            self.logger.error(f"Error running bot: {e}")
            print(f"Error: {e}")

def main():
    """メイン実行"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bot = SimpleMovieBot()
    
    try:
        asyncio.run(bot.run_bot())
    except KeyboardInterrupt:
        print("\nBot停止中...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()