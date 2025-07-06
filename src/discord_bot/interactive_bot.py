"""
インタラクティブDiscord Bot
"""
import asyncio
import logging
import re
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import discord
from discord.ext import commands

from .discord_models import BotQuery, BotResponse, MovieSearchResult, ExternalMovieInfo
from .discord_config import load_config
from ..scraping.main import TheaterScrapingOrchestrator
from .weekly_notifier import WeeklyNotifier

class MovieQueryParser:
    """映画クエリ解析器"""
    
    def __init__(self):
        # クエリパターン定義
        self.patterns = {
            "movie_info": [
                r"「(.+?)」について教えて",
                r"(.+?)について教えて",
                r"(.+?)の情報",
                r"(.+?)とは"
            ],
            "theater_schedule": [
                r"(.+?)の今週の上映予定",
                r"(.+?)のスケジュール",
                r"(.+?)で上映中の映画"
            ],
            "director_works": [
                r"監督「(.+?)」の作品",
                r"(.+?)監督の映画",
                r"(.+?)の監督作品"
            ],
            "genre_search": [
                r"(.+?)ジャンルの映画",
                r"(.+?)系の映画",
                r"(.+?)映画"
            ]
        }
        
    def parse_query(self, message: str) -> BotQuery:
        """クエリを解析"""
        message = message.strip()
        
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    target = match.group(1).strip()
                    return BotQuery(
                        query_type=query_type,
                        target=target,
                        filters={}
                    )
                    
        # パターンにマッチしない場合は一般検索
        return BotQuery(
            query_type="general_search",
            target=message,
            filters={}
        )

class MovieDataSearcher:
    """映画データ検索器"""
    
    def __init__(self):
        self.orchestrator = TheaterScrapingOrchestrator()
        self.logger = logging.getLogger(__name__)
        
    async def search_movie_info(self, movie_title: str) -> Optional[MovieSearchResult]:
        """映画情報検索"""
        try:
            # 最新データ取得
            all_results = self.orchestrator.scrape_all_theaters()
            
            for theater_key, result in all_results.items():
                if not result:
                    continue
                    
                # 映画情報から検索
                for movie_dict in result.get("movies", []):
                    if self._is_title_match(movie_dict.get("title", ""), movie_title):
                        # 対応するスケジュール情報を取得
                        theaters, showtimes = self._get_movie_schedule_info(
                            movie_title, all_results
                        )
                        
                        movie_info = self._dict_to_movie_info(movie_dict)
                        
                        return MovieSearchResult(
                            movie=movie_info,
                            theaters=theaters,
                            current_showtimes=showtimes
                        )
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching movie info: {e}")
            return None
            
    async def search_theater_schedule(self, theater_name: str) -> List[MovieSearchResult]:
        """映画館スケジュール検索"""
        try:
            all_results = self.orchestrator.scrape_all_theaters()
            results = []
            
            for theater_key, result in all_results.items():
                if not result:
                    continue
                    
                theater_info = result.get("theater_info", {})
                if self._is_theater_match(theater_info.get("name", ""), theater_name):
                    # この映画館のスケジュール取得
                    for schedule_dict in result.get("schedules", []):
                        movie_title = schedule_dict.get("movie_title", "")
                        
                        # 対応する映画情報を取得
                        movie_info = self._find_movie_info(movie_title, result.get("movies", []))
                        
                        if movie_info:
                            showtimes = self._dict_to_showtimes(schedule_dict.get("showtimes", []))
                            
                            results.append(MovieSearchResult(
                                movie=movie_info,
                                theaters=[theater_info.get("name", "")],
                                current_showtimes=showtimes
                            ))
                            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching theater schedule: {e}")
            return []
            
    async def search_by_director(self, director_name: str) -> List[MovieSearchResult]:
        """監督名で検索"""
        try:
            all_results = self.orchestrator.scrape_all_theaters()
            results = []
            
            for theater_key, result in all_results.items():
                if not result:
                    continue
                    
                for movie_dict in result.get("movies", []):
                    movie_director = movie_dict.get("director", "")
                    if director_name in movie_director:
                        theaters, showtimes = self._get_movie_schedule_info(
                            movie_dict.get("title", ""), all_results
                        )
                        
                        movie_info = self._dict_to_movie_info(movie_dict)
                        
                        results.append(MovieSearchResult(
                            movie=movie_info,
                            theaters=theaters,
                            current_showtimes=showtimes
                        ))
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching by director: {e}")
            return []
            
    def _is_title_match(self, stored_title: str, search_title: str) -> bool:
        """タイトルマッチング"""
        # 完全一致
        if stored_title == search_title:
            return True
            
        # 部分一致（両方向）
        if search_title in stored_title or stored_title in search_title:
            return True
            
        # 「」を除去して比較
        clean_stored = stored_title.replace("「", "").replace("」", "")
        clean_search = search_title.replace("「", "").replace("」", "")
        
        return clean_stored == clean_search or clean_search in clean_stored
        
    def _is_theater_match(self, stored_name: str, search_name: str) -> bool:
        """映画館名マッチング"""
        return search_name in stored_name or stored_name in search_name
        
    def _get_movie_schedule_info(self, movie_title: str, all_results: dict) -> tuple[List[str], List]:
        """映画のスケジュール情報を取得"""
        theaters = []
        all_showtimes = []
        
        for theater_key, result in all_results.items():
            if not result:
                continue
                
            theater_name = result.get("theater_info", {}).get("name", "")
            
            for schedule_dict in result.get("schedules", []):
                if self._is_title_match(schedule_dict.get("movie_title", ""), movie_title):
                    theaters.append(theater_name)
                    showtimes = self._dict_to_showtimes(schedule_dict.get("showtimes", []))
                    all_showtimes.extend(showtimes)
                    
        return theaters, all_showtimes
        
    def _find_movie_info(self, movie_title: str, movies_list: List[dict]):
        """映画リストから映画情報を検索"""
        for movie_dict in movies_list:
            if self._is_title_match(movie_dict.get("title", ""), movie_title):
                return self._dict_to_movie_info(movie_dict)
        return None
        
    def _dict_to_movie_info(self, movie_dict: dict):
        """辞書を MovieInfo オブジェクトに変換"""
        from ..scraping.models import MovieInfo
        return MovieInfo(
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
        
    def _dict_to_showtimes(self, showtimes_list: List[dict]):
        """辞書リストを ShowtimeInfo オブジェクトリストに変換"""
        from ..scraping.models import ShowtimeInfo
        return [
            ShowtimeInfo(
                date=st.get("date", ""),
                times=st.get("times", []),
                screen=st.get("screen"),
                ticket_url=st.get("ticket_url")
            )
            for st in showtimes_list
        ]

class PlaywrightSearcher:
    """Playwright外部検索器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def search_external_movie_info(self, movie_title: str) -> Optional[ExternalMovieInfo]:
        """外部サイトから映画情報を検索"""
        try:
            # ここでPlaywright MCPを使用して外部サイト検索
            # 現在は模擬実装
            self.logger.info(f"Searching external info for: {movie_title}")
            
            # TODO: 実際のPlaywright MCP実装
            # 映画.com、ぴあ、Filmarksなどから情報取得
            
            return ExternalMovieInfo(
                rating=4.2,
                review_count=156,
                awards=["東京国際映画祭 最優秀作品賞"],
                additional_synopsis="詳細なあらすじ情報...",
                official_site="https://example.com",
                trailer_url="https://youtube.com/watch?v=example"
            )
            
        except Exception as e:
            self.logger.error(f"Error searching external info: {e}")
            return None

class InteractiveBot(commands.Bot):
    """インタラクティブBot本体"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.discord_config, self.schedule_config, self.bot_config = load_config()
        self.query_parser = MovieQueryParser()
        self.data_searcher = MovieDataSearcher()
        self.playwright_searcher = PlaywrightSearcher()
        self.logger = logging.getLogger(__name__)
        
    async def on_ready(self):
        """Bot準備完了"""
        self.logger.info(f'Interactive bot logged in as {self.user}')
        
    async def on_message(self, message):
        """メッセージ処理"""
        if message.author == self.user:
            return
            
        # 詳細チャンネルでの質問のみ処理
        if (self.discord_config.detail_channel_id and 
            message.channel.id == self.discord_config.detail_channel_id):
            await self.handle_movie_query(message)
            
        await self.process_commands(message)
        
    async def handle_movie_query(self, message):
        """映画質問の処理"""
        try:
            # クエリ解析
            query = self.query_parser.parse_query(message.content)
            
            # 検索実行
            if query.query_type == "movie_info":
                await self.handle_movie_info_query(message, query)
            elif query.query_type == "theater_schedule":
                await self.handle_theater_schedule_query(message, query)
            elif query.query_type == "director_works":
                await self.handle_director_works_query(message, query)
            else:
                await message.reply("申し訳ございませんが、その質問は理解できませんでした。\n例: 「映画タイトルについて教えて」")
                
        except Exception as e:
            self.logger.error(f"Error handling query: {e}")
            await message.reply("エラーが発生しました。しばらくしてからもう一度お試しください。")
            
    async def handle_movie_info_query(self, message, query: BotQuery):
        """映画情報クエリ処理"""
        movie_result = await self.data_searcher.search_movie_info(query.target)
        
        if not movie_result:
            await message.reply(f"「{query.target}」の情報が見つかりませんでした。")
            return
            
        # 外部情報検索
        external_info = None
        if self.bot_config.enable_playwright_search:
            external_info = await self.playwright_searcher.search_external_movie_info(query.target)
            
        # Embed作成
        embed = self._create_movie_info_embed(movie_result, external_info)
        await message.reply(embed=embed)
        
    async def handle_theater_schedule_query(self, message, query: BotQuery):
        """映画館スケジュールクエリ処理"""
        results = await self.data_searcher.search_theater_schedule(query.target)
        
        if not results:
            await message.reply(f"「{query.target}」のスケジュール情報が見つかりませんでした。")
            return
            
        embed = self._create_theater_schedule_embed(query.target, results)
        await message.reply(embed=embed)
        
    async def handle_director_works_query(self, message, query: BotQuery):
        """監督作品クエリ処理"""
        results = await self.data_searcher.search_by_director(query.target)
        
        if not results:
            await message.reply(f"監督「{query.target}」の作品が見つかりませんでした。")
            return
            
        embed = self._create_director_works_embed(query.target, results)
        await message.reply(embed=embed)
        
    def _create_movie_info_embed(self, movie_result: MovieSearchResult, 
                                external_info: Optional[ExternalMovieInfo]) -> discord.Embed:
        """映画情報Embed作成"""
        movie = movie_result.movie
        
        embed = discord.Embed(
            title=f"🎬 『{movie.title}』について",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        # 基本情報
        info_lines = []
        if movie.director:
            info_lines.append(f"┣━ 監督: {movie.director}")
        if movie.cast:
            cast_str = ", ".join(movie.cast[:3])  # 最大3名
            if len(movie.cast) > 3:
                cast_str += "..."
            info_lines.append(f"┣━ 出演: {cast_str}")
        if movie.duration:
            info_lines.append(f"┣━ 上映時間: {movie.duration}分")
        if movie.genre:
            info_lines.append(f"┗━ ジャンル: {movie.genre}")
            
        if info_lines:
            embed.add_field(name="📋 基本情報", value="\n".join(info_lines), inline=False)
            
        # 上映情報
        if movie_result.theaters:
            theater_info = []
            for i, theater in enumerate(movie_result.theaters[:3]):  # 最大3館
                showtimes_for_theater = [st for st in movie_result.current_showtimes if theater in str(st)]
                if showtimes_for_theater:
                    times_str = ", ".join(showtimes_for_theater[0].times[:3])
                    theater_info.append(f"┣━ {theater}: {times_str}")
                else:
                    theater_info.append(f"┣━ {theater}")
                    
            if theater_info:
                theater_info[-1] = theater_info[-1].replace("┣━", "┗━")
                embed.add_field(name="📍 上映情報", value="\n".join(theater_info), inline=False)
                
        # あらすじ
        if movie.synopsis:
            synopsis = movie.synopsis[:300]
            if len(movie.synopsis) > 300:
                synopsis += "..."
            embed.add_field(name="💭 あらすじ", value=synopsis, inline=False)
            
        # 外部情報
        if external_info:
            external_lines = []
            if external_info.rating:
                external_lines.append(f"🎥 評価: {external_info.rating}/5")
            if external_info.awards:
                external_lines.append(f"🏆 受賞: {external_info.awards[0]}")
                
            if external_lines:
                embed.add_field(name="🌐 追加情報", value="\n".join(external_lines), inline=False)
                
        return embed
        
    def _create_theater_schedule_embed(self, theater_name: str, results: List[MovieSearchResult]) -> discord.Embed:
        """映画館スケジュールEmbed作成"""
        embed = discord.Embed(
            title=f"📍 {theater_name} 上映スケジュール",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        for i, result in enumerate(results[:10]):  # 最大10件
            movie = result.movie
            title_with_times = f"『{movie.title}』"
            
            if result.current_showtimes:
                times = result.current_showtimes[0].times[:3]  # 最初の日の最大3回
                times_str = ", ".join(times)
                title_with_times += f"\n⏰ {times_str}"
                
            embed.add_field(name=f"🎭 {i+1}.", value=title_with_times, inline=True)
            
        embed.set_footer(text=f"上映中の映画 {len(results)}作品")
        return embed
        
    def _create_director_works_embed(self, director_name: str, results: List[MovieSearchResult]) -> discord.Embed:
        """監督作品Embed作成"""
        embed = discord.Embed(
            title=f"🎬 監督「{director_name}」の作品",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        for i, result in enumerate(results[:5]):  # 最大5件
            movie = result.movie
            theaters_str = ", ".join(result.theaters[:2])  # 最大2館
            if len(result.theaters) > 2:
                theaters_str += "..."
                
            value = f"📍 {theaters_str}"
            if movie.synopsis:
                synopsis = movie.synopsis[:100]
                if len(movie.synopsis) > 100:
                    synopsis += "..."
                value += f"\n💭 {synopsis}"
                
            embed.add_field(name=f"🎭 『{movie.title}』", value=value, inline=False)
            
        embed.set_footer(text=f"上映中の作品 {len(results)}作品")
        return embed

def main():
    """メイン実行"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bot = InteractiveBot()
    
    discord_config, _, _ = load_config()
    if not discord_config.token:
        print("Discord bot token not provided")
        return
        
    bot.run(discord_config.token)

if __name__ == "__main__":
    main()