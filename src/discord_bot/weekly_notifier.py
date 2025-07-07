"""
週次通知システム
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
import discord
from discord.ext import commands, tasks

from ..scraping.main import TheaterScrapingOrchestrator
from .discord_models import WeeklyMovieSchedule, create_weekly_schedule_from_data
from .discord_config import load_config

class WeeklyNotifier:
    """週次通知管理クラス"""
    
    def __init__(self):
        self.discord_config, self.schedule_config, self.bot_config = load_config()
        self.orchestrator = TheaterScrapingOrchestrator()
        self.logger = logging.getLogger(__name__)
        
        # Discord Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # イベントハンドラー設定
        self.setup_bot_events()
        
    def setup_bot_events(self):
        """Bot イベントハンドラー設定"""
        
        @self.bot.event
        async def on_ready():
            self.logger.info(f'Bot logged in as {self.bot.user}')
            
            # チャンネルID取得（名前から）
            if not self.discord_config.main_channel_id:
                await self._find_channels()
                
            # 週次タスク開始
            self.weekly_task.start()
            
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
                
            # 詳細チャンネルでの質問対応は後で実装
            await self.bot.process_commands(message)
            
    async def _find_channels(self):
        """チャンネル名からIDを取得"""
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.name == self.discord_config.main_channel_name:
                    self.discord_config.main_channel_id = channel.id
                elif channel.name == self.discord_config.detail_channel_name:
                    self.discord_config.detail_channel_id = channel.id
                    
    @tasks.loop(time=datetime.strptime("07:30", "%H:%M").time())
    async def weekly_task(self):
        """週次タスク（毎週月曜日実行）"""
        now = datetime.now()
        if now.weekday() == 0:  # 月曜日
            await self.send_weekly_report()
            
    async def send_weekly_report(self):
        """週次レポート送信"""
        try:
            self.logger.info("Starting weekly report generation")
            
            # データ取得（既存データファイルから）
            all_results = self._load_latest_theater_data()
            if not all_results:
                self.logger.error("No theater data available for weekly report")
                return
            
            # 週次スケジュール生成
            current_week_start = self._get_monday_of_week(datetime.now().date())
            next_week_start = current_week_start + timedelta(days=7)
            
            theater_data_list = []
            for theater_key, result in all_results.items():
                if result:
                    theater_data_list.append(self._convert_result_to_theater_data(result))
                    
            weekly_schedule = create_weekly_schedule_from_data(
                theater_data_list, current_week_start, next_week_start
            )
            
            # Discord Embed作成
            embed = self._create_weekly_embed(weekly_schedule)
            
            # 送信
            if self.discord_config.main_channel_id:
                channel = self.bot.get_channel(self.discord_config.main_channel_id)
                if channel:
                    await channel.send(embed=embed)
                    self.logger.info("Weekly report sent successfully")
                else:
                    self.logger.error(f"Channel not found: {self.discord_config.main_channel_id}")
            else:
                self.logger.error("Main channel ID not configured")
                
        except Exception as e:
            self.logger.error(f"Error sending weekly report: {e}")
            
    def _get_monday_of_week(self, date_obj: date) -> date:
        """指定日の週の月曜日を取得"""
        days_since_monday = date_obj.weekday()
        monday = date_obj - timedelta(days=days_since_monday)
        return monday
    
    def _load_latest_theater_data(self) -> dict:
        """最新の映画館データファイルを読み込み"""
        try:
            import json
            import glob
            import os
            
            output_dir = "output"
            if not os.path.exists(output_dir):
                self.logger.error(f"Output directory {output_dir} not found")
                return {}
                
            json_files = glob.glob(os.path.join(output_dir, "all_theaters_*.json"))
            if not json_files:
                self.logger.error("No theater data files found")
                return {}
                
            latest_file = max(json_files, key=os.path.getctime)
            self.logger.info(f"Using data from: {latest_file}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading theater data: {e}")
            return {}
        
    def _convert_result_to_theater_data(self, result: dict):
        """辞書データをTheaterDataオブジェクトに変換"""
        from ..scraping.models import TheaterInfo, MovieInfo, MovieSchedule, ShowtimeInfo, TheaterData
        
        # 映画館情報
        theater_info_dict = result.get("theater_info", {})
        theater_info = TheaterInfo(
            name=theater_info_dict.get("name", ""),
            url=theater_info_dict.get("url", ""),
            address=theater_info_dict.get("address"),
            phone=theater_info_dict.get("phone"),
            access=theater_info_dict.get("access"),
            screens=theater_info_dict.get("screens")
        )
        
        # 映画情報
        movies = []
        for movie_dict in result.get("movies", []):
            movie = MovieInfo(
                title=movie_dict.get("title", ""),
                title_en=movie_dict.get("title_en"),
                director=movie_dict.get("director"),
                cast=movie_dict.get("cast", []),
                genre=movie_dict.get("genre"),
                duration=movie_dict.get("duration"),
                rating=movie_dict.get("rating"),
                synopsis=movie_dict.get("synopsis"),
                poster_url=movie_dict.get("poster_url")
            )
            movies.append(movie)
            
        # スケジュール情報
        schedules = []
        for schedule_dict in result.get("schedules", []):
            showtimes = []
            for showtime_dict in schedule_dict.get("showtimes", []):
                showtime = ShowtimeInfo(
                    date=showtime_dict.get("date", ""),
                    times=showtime_dict.get("times", []),
                    screen=showtime_dict.get("screen"),
                    ticket_url=showtime_dict.get("ticket_url")
                )
                showtimes.append(showtime)
                
            schedule = MovieSchedule(
                theater_name=schedule_dict.get("theater_name", ""),
                movie_title=schedule_dict.get("movie_title", ""),
                showtimes=showtimes
            )
            schedules.append(schedule)
            
        return TheaterData(
            theater_info=theater_info,
            movies=movies,
            schedules=schedules
        )
        
    def _create_weekly_embed(self, weekly_schedule: WeeklyMovieSchedule) -> discord.Embed:
        """週次レポート用Embed作成"""
        title = f"🎬 【今週・来週の上映映画】{weekly_schedule.week_start.strftime('%m/%d')}〜{weekly_schedule.week_end.strftime('%m/%d')}"
        
        embed = discord.Embed(
            title=title,
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        # 映画情報を追加
        description_parts = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
        
        for movie_info in weekly_schedule.movies[:10]:  # 最大10件
            movie_part = f"🎭 **『{movie_info.movie.title}』**\n"
            movie_part += f"📍 上映館: {', '.join(movie_info.theaters)}\n"
            movie_part += f"📅 期間: {movie_info.schedule_period}\n"
            
            # あらすじ（150文字まで）
            if movie_info.movie.synopsis:
                synopsis = movie_info.movie.synopsis[:150]
                if len(movie_info.movie.synopsis) > 150:
                    synopsis += "..."
                movie_part += f"💭 {synopsis}\n"
                
            description_parts.append(movie_part + "\n")
            
        # 統計情報
        description_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        description_parts.append(f"📊 合計: {weekly_schedule.total_movies}作品 | {weekly_schedule.total_theaters}映画館\n")
        description_parts.append("🤖 詳細情報は #映画-質問 で「映画名について教えて」と質問してください")
        
        embed.description = "".join(description_parts)
        
        # フッター
        embed.set_footer(text="東京独立系映画館情報 | 毎週月曜更新")
        
        return embed
        
    def run(self):
        """Bot実行"""
        if not self.discord_config.token:
            self.logger.error("Discord bot token not provided")
            return
            
        self.bot.run(self.discord_config.token)

def main():
    """メイン実行"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    notifier = WeeklyNotifier()
    notifier.run()

if __name__ == "__main__":
    main()