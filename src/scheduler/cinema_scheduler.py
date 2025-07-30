#!/usr/bin/env python3
"""
Cinema Scraping Scheduler
完全自動化スケジューラー - スクレイピング実行からDiscord通知まで
"""

import asyncio
import logging
import sys
import subprocess
from datetime import datetime, time
from pathlib import Path
from typing import Optional
import schedule
import time as time_module
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "discord_bot"))

# 相対インポートをコメントアウト（サブプロセスで実行）
# from scraping.json_exporter import CinemaJSONExporter
# from scraping.main_scraper import main as run_scraping
from discord_bot.weekly_notifier import WeeklyNotifier

class CinemaScheduler:
    """映画館データ完全自動化スケジューラー"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scheduler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # ログディレクトリ作成
        Path('logs').mkdir(exist_ok=True)
    
    def run_scraping_job(self):
        """スクレイピングジョブ実行"""
        try:
            self.logger.info("🚀 スクレイピングジョブ開始")
            
            # 実際のスクレイピング実行
            result = subprocess.run([
                sys.executable, "run_scraping.py"
            ], capture_output=True, text=True, cwd=project_root.parent)
            
            if result.returncode == 0:
                self.logger.info("✅ スクレイピング完了")
                self.logger.info(f"出力: {result.stdout}")
            else:
                self.logger.error(f"❌ スクレイピングエラー: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"❌ スクレイピングジョブ実行エラー: {e}")
    
    def run_discord_notification(self):
        """Discord通知ジョブ実行"""
        try:
            self.logger.info("📢 Discord通知ジョブ開始")
            
            # WeeklyNotifierを一回だけ実行
            asyncio.run(self._send_weekly_notification())
            
        except Exception as e:
            self.logger.error(f"❌ Discord通知エラー: {e}")
    
    async def _send_weekly_notification(self):
        """週次通知を一度だけ送信"""
        try:
            # 環境変数から直接取得
            import os
            token = os.getenv('DISCORD_BOT_TOKEN')
            channel_name = os.getenv('DISCORD_MAIN_CHANNEL_NAME', 'weekly-movies')
            
            if not token:
                self.logger.error("❌ DISCORD_BOT_TOKEN が設定されていません")
                return
                
            self.logger.info(f"🔑 Discord token確認: {token[:20]}...")
            self.logger.info(f"📺 対象チャンネル: {channel_name}")
            
            import discord
            
            # 一時的なBotクライアントを作成
            intents = discord.Intents.default()
            intents.message_content = True
            bot = discord.Client(intents=intents)
            
            @bot.event
            async def on_ready():
                try:
                    self.logger.info(f"✅ Bot接続完了: {bot.user}")
                    
                    # チャンネル検索
                    target_channel = None
                    for guild in bot.guilds:
                        self.logger.info(f"🏠 ギルド検索: {guild.name}")
                        for channel in guild.channels:
                            if channel.name == channel_name:
                                target_channel = channel
                                self.logger.info(f"📺 チャンネル発見: {channel.name} (ID: {channel.id})")
                                break
                        if target_channel:
                            break
                    
                    if target_channel:
                        # WeeklyNotifierを使用して週次レポート送信
                        notifier = WeeklyNotifier()
                        await notifier.send_weekly_report_to_channel(target_channel)
                        self.logger.info("✅ Discord通知送信完了")
                    else:
                        self.logger.error(f"❌ チャンネル '{channel_name}' が見つかりません")
                        # 利用可能なチャンネル一覧を表示
                        for guild in bot.guilds:
                            for channel in guild.channels:
                                if hasattr(channel, 'send'):  # テキストチャンネルのみ
                                    self.logger.info(f"   - {channel.name}")
                        
                except Exception as e:
                    self.logger.error(f"❌ 通知送信エラー: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    await bot.close()
            
            # Bot起動
            await bot.start(token)
                        
        except Exception as e:
            self.logger.error(f"❌ Discord通知実行エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_schedule(self):
        """スケジュール設定"""
        
        # 毎週日曜日 23:00 - スクレイピング実行
        schedule.every().sunday.at("23:00").do(self.run_scraping_job)
        
        # 毎週月曜日 07:30 - Discord通知
        schedule.every().monday.at("07:30").do(self.run_discord_notification)
        
        # テスト用: 毎日12:00にスクレイピング（開発時のみ）
        # schedule.every().day.at("12:00").do(self.run_scraping_job)
        
        self.logger.info("📅 スケジュール設定完了:")
        self.logger.info("  - 毎週日曜日 23:00: スクレイピング実行")
        self.logger.info("  - 毎週月曜日 07:30: Discord通知送信")
    
    def run(self):
        """スケジューラー実行"""
        self.logger.info("🎬 Cinema Scheduler 開始")
        self.setup_schedule()
        
        # 初回実行確認
        next_run = schedule.next_run()
        if next_run:
            self.logger.info(f"⏰ 次回実行予定: {next_run}")
        
        try:
            while True:
                schedule.run_pending()
                time_module.sleep(60)  # 1分間隔でチェック
                
        except KeyboardInterrupt:
            self.logger.info("🛑 スケジューラー停止")
        except Exception as e:
            self.logger.error(f"❌ スケジューラーエラー: {e}")

class TestScheduler:
    """テスト用スケジューラー（即座に実行）"""
    
    def __init__(self):
        self.scheduler = CinemaScheduler()
    
    def test_scraping(self):
        """スクレイピングテスト"""
        print("🧪 スクレイピングテスト実行")
        self.scheduler.run_scraping_job()
    
    def test_notification(self):
        """通知テスト"""
        print("🧪 Discord通知テスト実行")
        self.scheduler.run_discord_notification()
    
    def test_full_pipeline(self):
        """完全パイプラインテスト"""
        print("🧪 完全パイプラインテスト実行")
        self.test_scraping()
        print("⏳ 5秒待機...")
        time_module.sleep(5)
        self.test_notification()

def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cinema Scheduler')
    parser.add_argument('--test', choices=['scraping', 'notification', 'full'], 
                       help='テスト実行モード')
    parser.add_argument('--daemon', action='store_true', 
                       help='デーモンモードで実行')
    
    args = parser.parse_args()
    
    if args.test:
        test_scheduler = TestScheduler()
        if args.test == 'scraping':
            test_scheduler.test_scraping()
        elif args.test == 'notification':
            test_scheduler.test_notification()
        elif args.test == 'full':
            test_scheduler.test_full_pipeline()
    else:
        scheduler = CinemaScheduler()
        scheduler.run()

if __name__ == "__main__":
    main()