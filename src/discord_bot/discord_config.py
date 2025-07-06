"""
Discord Bot設定ファイル
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DiscordConfig:
    """Discord Bot設定"""
    token: str
    main_channel_id: Optional[int] = None
    detail_channel_id: Optional[int] = None
    main_channel_name: str = "weekly-movies"
    detail_channel_name: str = "movie-questions"
    
@dataclass
class ScheduleConfig:
    """スケジュール設定"""
    weekly_report_time: str = "MON 07:30"  # 毎週月曜日 7:30
    data_update_interval: int = 6  # 6時間毎にデータ更新
    timezone: str = "Asia/Tokyo"
    
@dataclass
class BotConfig:
    """Bot機能設定"""
    enable_playwright_search: bool = True
    enable_ai_responses: bool = False
    cache_duration_hours: int = 24
    max_search_results: int = 10
    
def load_config() -> tuple[DiscordConfig, ScheduleConfig, BotConfig]:
    """設定を環境変数から読み込み"""
    discord_config = DiscordConfig(
        token=os.getenv("DISCORD_BOT_TOKEN", ""),
        main_channel_id=int(os.getenv("DISCORD_MAIN_CHANNEL_ID", "0")) or None,
        detail_channel_id=int(os.getenv("DISCORD_DETAIL_CHANNEL_ID", "0")) or None,
        main_channel_name=os.getenv("DISCORD_MAIN_CHANNEL_NAME", "weekly-movies"),
        detail_channel_name=os.getenv("DISCORD_DETAIL_CHANNEL_NAME", "movie-questions")
    )
    
    schedule_config = ScheduleConfig(
        weekly_report_time=os.getenv("WEEKLY_REPORT_TIME", "MON 07:30"),
        data_update_interval=int(os.getenv("DATA_UPDATE_INTERVAL", "6")),
        timezone=os.getenv("TIMEZONE", "Asia/Tokyo")
    )
    
    bot_config = BotConfig(
        enable_playwright_search=os.getenv("ENABLE_PLAYWRIGHT_SEARCH", "true").lower() == "true",
        enable_ai_responses=os.getenv("ENABLE_AI_RESPONSES", "false").lower() == "true",
        cache_duration_hours=int(os.getenv("CACHE_DURATION_HOURS", "24")),
        max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "10"))
    )
    
    return discord_config, schedule_config, bot_config