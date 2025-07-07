"""
Discord Bot統合実行スクリプト
"""
import asyncio
import logging
import sys
import datetime
from typing import Optional
import discord
from discord.ext import commands, tasks

from .weekly_notifier import WeeklyNotifier
from .interactive_bot import InteractiveBot, MovieQueryParser, MovieDataSearcher, PlaywrightSearcher
from .discord_config import load_config

class CombinedMovieBot(commands.Bot):
    """週次通知＋インタラクティブ機能統合Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.discord_config, self.schedule_config, self.bot_config = load_config()
        
        # 各機能コンポーネント初期化
        self.weekly_notifier = WeeklyNotifier()
        self.query_parser = MovieQueryParser()
        self.data_searcher = MovieDataSearcher()
        self.playwright_searcher = PlaywrightSearcher()
        
        self.logger = logging.getLogger(__name__)
        
        # チャンネルID保存用
        self.main_channel_id: Optional[int] = None
        self.detail_channel_id: Optional[int] = None
        
    async def setup_hook(self):
        """Bot起動時のセットアップ"""
        # 週次タスク開始
        self.weekly_report_task.start()
        self.weekly_scraping_task.start()
        self.logger.info("Weekly report and scraping tasks started")
        
    async def on_ready(self):
        """Bot準備完了"""
        self.logger.info(f'Combined Movie Bot logged in as {self.user}')
        
        # チャンネルID取得
        await self._find_channels()
        
        # ステータス設定
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="東京の映画館情報 | !help でコマンド一覧"
            )
        )
        
    async def _find_channels(self):
        """チャンネル名からIDを取得"""
        for guild in self.guilds:
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if channel.name == self.discord_config.main_channel_name:
                        self.main_channel_id = channel.id
                        self.logger.info(f"Found main channel: {channel.name} ({channel.id})")
                    elif channel.name == self.discord_config.detail_channel_name:
                        self.detail_channel_id = channel.id
                        self.logger.info(f"Found detail channel: {channel.name} ({channel.id})")
                        
    @tasks.loop(hours=1)  # 1時間毎にチェック
    async def weekly_report_task(self):
        """週次レポートタスク"""
        import datetime
        now = datetime.datetime.now()
        
        # 月曜日の7時台に実行（30分の余裕を持つ）
        if now.weekday() == 0 and now.hour == 7:
            await self._send_weekly_report()
    
    @tasks.loop(hours=1)  # 1時間毎にチェック
    async def weekly_scraping_task(self):
        """週次スクレイピングタスク（月曜日6時台に実行）"""
        import datetime
        now = datetime.datetime.now()
        
        # 月曜日の6時台にスクレイピング実行（レポート送信の1時間前）
        if now.weekday() == 0 and now.hour == 6:
            await self._perform_weekly_scraping()
            
    async def _perform_weekly_scraping(self):
        """週次スクレイピング実行"""
        try:
            self.logger.info("Starting weekly scraping...")
            
            # スクレイピング実行
            from ..scraping.main import TheaterScrapingOrchestrator
            orchestrator = TheaterScrapingOrchestrator()
            results = orchestrator.scrape_all_theaters()
            
            if results:
                self.logger.info("Weekly scraping completed successfully")
            else:
                self.logger.warning("Weekly scraping completed but no results")
                
        except Exception as e:
            self.logger.error(f"Error in weekly scraping: {e}")
            
    async def _send_weekly_report(self):
        """週次レポート送信"""
        try:
            self.logger.info("Sending weekly report...")
            
            if not self.main_channel_id:
                self.logger.error("Main channel not found")
                return
                
            channel = self.get_channel(self.main_channel_id)
            if not channel:
                self.logger.error(f"Channel not found: {self.main_channel_id}")
                return
                
            # WeeklyNotifierのメソッドを使用
            await self.weekly_notifier.send_weekly_report()
            
        except Exception as e:
            self.logger.error(f"Error sending weekly report: {e}")
            
    async def on_message(self, message):
        """メッセージ処理"""
        if message.author == self.user:
            return
            
        # 詳細チャンネルでの映画質問処理
        if (self.detail_channel_id and 
            message.channel.id == self.detail_channel_id and
            not message.content.startswith('!')):
            await self._handle_movie_query(message)
            return
            
        # コマンド処理
        await self.process_commands(message)
        
    async def _handle_movie_query(self, message):
        """映画質問の処理（InteractiveBotから移植）"""
        try:
            # 入力中表示
            async with message.channel.typing():
                # クエリ解析
                query = self.query_parser.parse_query(message.content)
                
                # 検索実行
                if query.query_type == "movie_info":
                    await self._handle_movie_info_query(message, query)
                elif query.query_type == "theater_schedule":
                    await self._handle_theater_schedule_query(message, query)
                elif query.query_type == "director_works":
                    await self._handle_director_works_query(message, query)
                else:
                    await message.reply(
                        "申し訳ございませんが、その質問は理解できませんでした。\n\n"
                        "**使用例:**\n"
                        "• 「映画タイトル」について教えて\n"
                        "• ケイズシネマの今週の上映予定は？\n"
                        "• 監督「山田太郎」の作品を教えて"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error handling query: {e}")
            await message.reply("🚫 エラーが発生しました。しばらくしてからもう一度お試しください。")
            
    async def _handle_movie_info_query(self, message, query):
        """映画情報クエリ処理"""
        movie_result = await self.data_searcher.search_movie_info(query.target)
        
        if not movie_result:
            await message.reply(f"「{query.target}」の情報が見つかりませんでした。\n映画タイトルを正確に入力してください。")
            return
            
        # 外部情報検索
        external_info = None
        if self.bot_config.enable_playwright_search:
            external_info = await self.playwright_searcher.search_external_movie_info(query.target)
            
        # Embed作成（InteractiveBotのメソッドを使用）
        interactive_bot = InteractiveBot()
        embed = interactive_bot._create_movie_info_embed(movie_result, external_info)
        await message.reply(embed=embed)
        
    async def _handle_theater_schedule_query(self, message, query):
        """映画館スケジュールクエリ処理"""
        results = await self.data_searcher.search_theater_schedule(query.target)
        
        if not results:
            await message.reply(f"「{query.target}」のスケジュール情報が見つかりませんでした。\n映画館名を正確に入力してください。")
            return
            
        interactive_bot = InteractiveBot()
        embed = interactive_bot._create_theater_schedule_embed(query.target, results)
        await message.reply(embed=embed)
        
    async def _handle_director_works_query(self, message, query):
        """監督作品クエリ処理"""
        results = await self.data_searcher.search_by_director(query.target)
        
        if not results:
            await message.reply(f"監督「{query.target}」の作品が見つかりませんでした。\n監督名を正確に入力してください。")
            return
            
        interactive_bot = InteractiveBot()
        embed = interactive_bot._create_director_works_embed(query.target, results)
        await message.reply(embed=embed)
        
    # Bot コマンド定義
    @commands.command(name='help', aliases=['h'])
    async def help_command(self, ctx):
        """ヘルプコマンド"""
        embed = discord.Embed(
            title="🤖 映画館Bot ヘルプ",
            color=0x7289da,
            description="東京の独立系映画館情報をお届けします"
        )
        
        embed.add_field(
            name="📅 週次通知",
            value="毎週月曜日 7:30 に今週・来週の上映映画をお知らせ",
            inline=False
        )
        
        embed.add_field(
            name="💬 映画質問（#映画-質問チャンネル）",
            value=(
                "• 「映画タイトル」について教えて\n"
                "• 映画館名の今週の上映予定は？\n"
                "• 監督「監督名」の作品を教えて"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎭 対応映画館",
            value=(
                "ケイズシネマ、ポレポレ東中野、ユーロスペース\n"
                "下高井戸シネマ、早稲田松竹、新宿武蔵野館"
            ),
            inline=False
        )
        
        embed.set_footer(text="Powered by 映画館スクレイピングシステム")
        
        await ctx.send(embed=embed)
        
    @commands.command(name='status', aliases=['s'])
    async def status_command(self, ctx):
        """ステータスコマンド"""
        embed = discord.Embed(
            title="📊 Bot ステータス",
            color=0x00ff00,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="🤖 Bot", value="✅ 稼働中", inline=True)
        embed.add_field(name="📅 週次通知", value="✅ アクティブ", inline=True)
        embed.add_field(name="💬 質問対応", value="✅ アクティブ", inline=True)
        
        if self.main_channel_id:
            embed.add_field(name="📢 メインチャンネル", value=f"<#{self.main_channel_id}>", inline=True)
        if self.detail_channel_id:
            embed.add_field(name="❓ 質問チャンネル", value=f"<#{self.detail_channel_id}>", inline=True)
            
        embed.add_field(name="🎬 対応映画館", value="6館", inline=True)
        
        await ctx.send(embed=embed)
        
    @commands.command(name='update', aliases=['u'])
    async def manual_update_command(self, ctx):
        """手動データ更新コマンド"""
        await ctx.send("📡 データを更新中...")
        
        try:
            # データ更新実行
            from ..scraping.main import TheaterScrapingOrchestrator
            orchestrator = TheaterScrapingOrchestrator()
            results = orchestrator.scrape_all_theaters()
            
            success_count = sum(1 for result in results.values() if result)
            total_count = len(results)
            
            embed = discord.Embed(
                title="✅ データ更新完了",
                color=0x00ff00,
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(name="📊 結果", value=f"{success_count}/{total_count} 映画館のデータを更新", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Manual update error: {e}")
            await ctx.send("❌ データ更新中にエラーが発生しました。")

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('discord_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """メイン実行"""
    setup_logging()
    
    discord_config, _, _ = load_config()
    
    if not discord_config.token:
        print("❌ Discord bot token not provided")
        print("環境変数 DISCORD_BOT_TOKEN を設定してください")
        return
        
    bot = CombinedMovieBot()
    
    try:
        bot.run(discord_config.token)
    except Exception as e:
        logging.error(f"Bot run error: {e}")

if __name__ == "__main__":
    main()