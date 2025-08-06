#!/usr/bin/env python3
"""
おしゃべり専用Discord Bot
映画情報とは独立した一般的な会話を行うBot
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
from ollama_client import OllamaClient

# 環境変数読み込み
load_dotenv()

class ChatBot(commands.Bot):
    """おしゃべり専用Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!chat', intents=intents)
        
        # 設定読み込み
        self.discord_config, _, self.bot_config = load_config()
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_conversation_logging()
        
        # Ollamaクライアント初期化
        try:
            self.ollama_client = OllamaClient(
                base_url=self.bot_config.ollama_base_url,
                model="llama3.2:3b",
                timeout=30
            )
            self.logger.info("Ollama client initialized for chat bot")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None
            
        # 会話履歴（メモリ内保持、セッション毎）
        self.conversation_history = {}
        
        # チャット設定
        self.chat_config = {
            "max_history": 10,  # 保持する会話履歴数
            "system_prompt": (
                "あなたは親しみやすい日本語のチャットボットです。"
                "自然で楽しい会話を心がけ、相手の話に興味を持って応答してください。"
                "簡潔で分かりやすい返答を心がけてください。"
            ),
            "temperature": 0.8,
            "max_tokens": 300
        }
    
    def _setup_conversation_logging(self):
        """会話ログの設定"""
        # 会話ログ用のディレクトリ作成
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # 会話ログファイルパス
        today = datetime.now().strftime("%Y-%m-%d")
        self.conversation_log_file = self.logs_dir / f"chat_bot_conversations_{today}.jsonl"
        
        # 会話ログ用logger
        self.conversation_logger = logging.getLogger("chat_conversation")
        handler = logging.FileHandler(self.conversation_log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.conversation_logger.addHandler(handler)
        self.conversation_logger.setLevel(logging.INFO)
        self.conversation_logger.propagate = False
    
    def log_conversation(self, user_id, user_message, bot_response, metadata=None):
        """会話をログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "metadata": metadata or {}
        }
        self.conversation_logger.info(json.dumps(log_entry, ensure_ascii=False))
        
    def get_user_history(self, user_id):
        """ユーザーの会話履歴を取得"""
        return self.conversation_history.get(user_id, [])
        
    def add_to_history(self, user_id, user_message, bot_response):
        """会話履歴に追加"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        history = self.conversation_history[user_id]
        history.append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 履歴数制限
        if len(history) > self.chat_config["max_history"]:
            history.pop(0)
            
    async def on_ready(self):
        """Bot準備完了時の処理"""
        self.logger.info(f'{self.user} (Chat Bot) としてログインしました')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # ステータス設定
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="おしゃべり | !chathelp でヘルプ"
            )
        )
        
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        if message.author == self.user:
            return
            
        # チャットボットへの直接言及、またはDM
        if (self.user.mentioned_in(message) or 
            isinstance(message.channel, discord.DMChannel)):
            await self._handle_chat_message(message)
            
        # コマンド処理
        await self.process_commands(message)
        
    async def _handle_chat_message(self, message):
        """チャットメッセージを処理"""
        try:
            # typing状態表示
            async with message.channel.typing():
                user_id = str(message.author.id)
                user_message = message.content
                
                # メンションを除去
                if self.user.mentioned_in(message):
                    user_message = user_message.replace(f'<@{self.user.id}>', '').strip()
                
                if self.ollama_client:
                    response = await self._generate_chat_response(user_id, user_message)
                else:
                    response = await self._generate_fallback_response(user_message)
                
                # 応答送信
                if response:
                    await message.reply(response)
                    
                    # 履歴に追加
                    self.add_to_history(user_id, user_message, response)
                    
                    # ログに記録
                    metadata = {
                        "user_name": message.author.name,
                        "channel_name": message.channel.name if hasattr(message.channel, 'name') else "DM",
                        "guild_name": message.guild.name if message.guild else "DM",
                        "response_length": len(response),
                        "has_history": len(self.get_user_history(user_id)) > 0
                    }
                    self.log_conversation(user_id, user_message, response, metadata)
                    
                else:
                    await message.reply("すみません、今は返答できません。")
                    
        except Exception as e:
            self.logger.error(f"Error handling chat message: {e}")
            await message.reply("エラーが発生しました。後でもう一度お試しください。")
            
    async def _generate_chat_response(self, user_id, user_message):
        """Ollamaを使用してチャット応答を生成"""
        try:
            # 会話履歴を取得
            history = self.get_user_history(user_id)
            
            # プロンプト構築
            conversation_context = []
            conversation_context.append({
                "role": "system",
                "content": self.chat_config["system_prompt"]
            })
            
            # 履歴を追加（最新のものから制限数まで）
            for h in history[-5:]:  # 最新5件の履歴
                conversation_context.append({
                    "role": "user", 
                    "content": h["user"]
                })
                conversation_context.append({
                    "role": "assistant", 
                    "content": h["bot"]
                })
            
            # 現在のメッセージを追加
            conversation_context.append({
                "role": "user",
                "content": user_message
            })
            
            # Ollama呼び出し
            response = await self.ollama_client.chat_completion(
                messages=conversation_context,
                temperature=self.chat_config["temperature"],
                max_tokens=self.chat_config["max_tokens"]
            )
            
            return response.strip() if response else None
            
        except Exception as e:
            self.logger.error(f"Error generating chat response: {e}")
            return None
            
    async def _generate_fallback_response(self, user_message):
        """フォールバック応答"""
        responses = [
            "面白いですね！もう少し詳しく教えてください。",
            "なるほど、そうなんですね。",
            "それは興味深いお話ですね。",
            "いいですね！他にも何かありますか？",
            "そういうことがあるんですね。",
            "ありがとうございます！勉強になります。"
        ]
        
        # 簡単なキーワードマッチング
        if any(word in user_message.lower() for word in ['こんにちは', 'おはよう', 'こんばんは']):
            return f"こんにちは！今日はいかがお過ごしですか？"
        elif any(word in user_message.lower() for word in ['ありがとう', 'サンキュー']):
            return "どういたしまして！何かお手伝いできることがあれば遠慮なくどうぞ。"
        elif '？' in user_message or '?' in user_message:
            return "申し訳ございませんが、今はAI機能が利用できません。でも、お話を聞かせてください！"
        else:
            import random
            return random.choice(responses)
    
    @commands.command(name='chathelp', aliases=['ch'])
    async def chat_help(self, ctx):
        """チャットボットヘルプ"""
        embed = discord.Embed(
            title="🤖 チャットボット ヘルプ",
            color=0x7289da,
            description="気軽におしゃべりしましょう！"
        )
        
        embed.add_field(
            name="💬 基本的な使い方",
            value=(
                "• ボットにメンション（@チャットボット）してメッセージを送る\n"
                "• DMでメッセージを送る\n"
                "• 自然な会話を楽しんでください"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 コマンド",
            value=(
                "• `!chathelp` - このヘルプを表示\n"
                "• `!chatstatus` - ボットの状態確認\n"
                "• `!chatclear` - あなたの会話履歴をクリア"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ 注意",
            value="このボットは映画情報には特化していません。一般的なおしゃべりを楽しむためのボットです。",
            inline=False
        )
        
        embed.set_footer(text="Powered by Ollama LLM")
        await ctx.send(embed=embed)
        
    @commands.command(name='chatstatus', aliases=['cs'])
    async def chat_status(self, ctx):
        """チャットボット状態確認"""
        embed = discord.Embed(
            title="📊 チャットボット ステータス",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Ollama接続状態確認
        ollama_status = "❌ 利用不可"
        if self.ollama_client:
            try:
                health = await self.ollama_client.health_check()
                ollama_status = "✅ 接続済み" if health else "⚠️ 接続不安定"
            except Exception:
                ollama_status = "❌ 接続エラー"
        
        embed.add_field(name="🤖 Bot", value="✅ 稼働中", inline=True)
        embed.add_field(name="🧠 AI機能", value=ollama_status, inline=True)
        embed.add_field(name="💾 会話履歴", value=f"{len(self.conversation_history)}名のユーザー", inline=True)
        
        user_id = str(ctx.author.id)
        user_history_count = len(self.get_user_history(user_id))
        embed.add_field(name="📝 あなたの履歴", value=f"{user_history_count}件", inline=True)
        
        await ctx.send(embed=embed)
        
    @commands.command(name='chatclear', aliases=['cc'])
    async def clear_chat_history(self, ctx):
        """ユーザーの会話履歴をクリア"""
        user_id = str(ctx.author.id)
        
        if user_id in self.conversation_history:
            history_count = len(self.conversation_history[user_id])
            del self.conversation_history[user_id]
            await ctx.send(f"✅ あなたの会話履歴（{history_count}件）をクリアしました。")
        else:
            await ctx.send("📝 あなたの会話履歴は既に空です。")

def main():
    """メイン実行"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bot = ChatBot()
    
    # Discord設定から環境変数またはトークンを取得
    discord_config, _, _ = load_config()
    
    if not discord_config.token:
        print("Error: DISCORD_BOT_TOKEN environment variable is not set")
        return
        
    try:
        bot.run(discord_config.token)
    except discord.LoginFailure:
        print("Error: Invalid Discord bot token")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()