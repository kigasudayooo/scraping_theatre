#!/usr/bin/env python3
"""
簡素化されたDiscord Bot
相対インポートの問題を回避してBot機能を提供
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_config import load_config
from llm_responder import LLMResponder

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
        
        # LLM応答システム初期化
        try:
            self.llm_responder = LLMResponder()
            self.logger = logging.getLogger(__name__)
            self.logger.info("LLM responder initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM responder: {e}")
            self.llm_responder = None
            
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
            # LLM応答を試行
            if self.llm_responder and self.bot_config.enable_ai_responses:
                await self._handle_movie_query_with_llm(message)
            else:
                await self._handle_movie_query_fallback(message)
                
        except Exception as e:
            self.logger.error(f"Error handling movie query: {e}")
            await message.reply("申し訳ありません。エラーが発生しました。")
            
    async def _handle_movie_query_with_llm(self, message):
        """LLMを使用した映画質問処理"""
        try:
            # ユーザー情報とチャンネル情報を取得
            user_id = str(message.author.id)
            channel_info = {
                "channel_name": message.channel.name,
                "guild_name": message.guild.name if message.guild else "DM"
            }
            
            # LLM応答生成
            response = await self.llm_responder.generate_response(
                user_query=message.content,
                user_id=user_id,
                channel_info=channel_info
            )
            
            if response and response.strip():
                # 長いメッセージの場合は分割
                if len(response) > 2000:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)
                    
                self.logger.info(f"LLM response sent to user {message.author.name}")
            else:
                await self._handle_movie_query_fallback(message)
                
        except Exception as e:
            self.logger.error(f"LLM response failed: {e}")
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
        llm_status = "✅ 利用可能" if self.llm_responder else "❌ 利用不可"
        status_message = (
            f"**Bot Status**\n"
            f"LLM応答: {llm_status}\n"
            f"映画館データ: ✅ 35作品対応\n"
            f"設定されたチャンネル: {len([c for c in [self.discord_config.main_channel_id, self.discord_config.detail_channel_id] if c])}個"
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