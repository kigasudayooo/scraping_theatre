from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class ShimotakaidoCinemaScraper(BaseScraper):
    """下高井戸シネマ スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="下高井戸シネマ",
            base_url="http://shimotakaidocinema.com"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        # 基本情報を返す（実際のサイトにアクセス情報は少ない）
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都世田谷区松原3-27-26",
            phone="03-3321-0684",
            access="京王線下高井戸駅より徒歩3分",
            screens=1
        )
        
    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得"""
        movies = []
        
        # メインページから映画情報取得
        soup = self.get_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
            
        return movies
        
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出"""
        movies = []
        
        # 下高井戸シネマサイトから映画タイトルを抽出
        # タイトルは大きなフォントで表示されている
        body_text = soup.get_text()
        
        # 既知の映画タイトルパターンを検索
        lines = body_text.split('\n')
        movie_titles = []
        
        for line in lines:
            line = line.strip()
            # 映画タイトルらしい行を特定
            if (line and 
                len(line) > 2 and 
                not any(skip in line for skip in [
                    '年', '月', '日', '時', '分', '～', ':', 
                    'http', 'www', '.com', '@', 'トップ',
                    'お知らせ', '上映', '開催', 'トーク', '監督',
                    '先着', 'プレゼント', '決定', '追加'
                ]) and
                not line.isdigit() and
                not re.match(r'^\d{1,2}[/:\-]\d{1,2}', line) and
                not re.match(r'^(終|開)', line) and
                len(line) < 50):  # 長すぎる行は除外
                
                # 特定の映画タイトルパターンを検出
                if any(char in line for char in ['！', '？', '♪', '☆']) or \
                   re.search(r'[ァ-ヴ]+', line) or \
                   re.search(r'[A-Za-z]{2,}', line):
                    
                    # 重複チェック
                    if line not in movie_titles:
                        movie_titles.append(line)
        
        # 明示的に映画タイトルを抽出（実際のサイトから観察したもの）
        known_movies = [
            "旅するローマ教皇",
            "ドマーニ！愛のことづて", 
            "シンシン／SING SING",
            "カップルズ 4Kレストア版",
            "井口奈己監督特集"
        ]
        
        for known_movie in known_movies:
            if known_movie in body_text and known_movie not in movie_titles:
                movie_titles.append(known_movie)
        
        # MovieInfoオブジェクトを作成
        for title in movie_titles[:10]:  # 最大10作品
            movies.append(MovieInfo(
                title=title,
                title_en=None,
                director=None,
                cast=[],
                duration=None,
                synopsis=None,
                poster_url=None
            ))
                    
        return movies
        
    def _extract_movies_from_items_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """アイテムページから映画情報抽出"""
        movies = []
        
        # Storesサイトの商品一覧
        item_cards = soup.find_all("div", class_="item-card") or soup.find_all("div", class_="product-card")
        
        for card in item_cards:
            movie = self._extract_movie_from_element(card)
            if movie:
                movies.append(movie)
                
        return movies
        
    def _extract_movie_from_element(self, element) -> Optional[MovieInfo]:
        """要素から映画情報抽出"""
        try:
            # タイトル
            title_elem = (element.find("h2") or element.find("h3") or 
                         element.find("div", class_="title") or 
                         element.find("a", class_="item-title"))
            title = self.safe_extract_text(title_elem)
            
            if not title:
                return None
                
            # 英語タイトル
            title_en_elem = element.find("p", class_="title-en") or element.find("div", class_="subtitle")
            title_en = self.safe_extract_text(title_en_elem)
            
            # 説明文から監督・出演者情報を抽出
            description_elem = element.find("div", class_="description") or element.find("p", class_="item-description")
            description = self.safe_extract_text(description_elem)
            
            director = ""
            cast = []
            genre = ""
            synopsis = ""
            
            if description:
                # 監督情報
                director_match = re.search(r"監督[：:]([^/\n]+)", description)
                if director_match:
                    director = director_match.group(1).strip()
                    
                # 出演者情報
                cast_match = re.search(r"出演[：:]([^/\n]+)", description)
                if cast_match:
                    cast_text = cast_match.group(1).strip()
                    cast = [c.strip() for c in cast_text.split(",") if c.strip()]
                    
                # ジャンル
                genre_match = re.search(r"ジャンル[：:]([^/\n]+)", description)
                if genre_match:
                    genre = genre_match.group(1).strip()
                    
                # あらすじ（説明文をそのまま使用）
                synopsis = description
                
            # 上映時間
            duration = None
            if description:
                duration_match = re.search(r"(\d+)分", description)
                if duration_match:
                    duration = int(duration_match.group(1))
                    
            # ポスター画像
            poster_elem = element.find("img")
            poster_url = ""
            if poster_elem:
                poster_url = self.safe_extract_attr(poster_elem, "src")
                if poster_url and not poster_url.startswith("http"):
                    if poster_url.startswith("//"):
                        poster_url = f"https:{poster_url}"
                    else:
                        poster_url = f"{self.base_url}{poster_url}"
                        
            return MovieInfo(
                title=title,
                title_en=title_en if title_en else None,
                director=director if director else None,
                cast=cast,
                genre=genre if genre else None,
                duration=duration,
                synopsis=synopsis if synopsis else None,
                poster_url=poster_url if poster_url else None
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting movie info: {e}")
            return None
            
    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得"""
        schedules = []
        
        # メインページからスケジュール情報取得
        soup = self.get_page(self.base_url)
        if soup:
            schedules.extend(self._extract_schedules_from_page(soup))
                
        return schedules
        
    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出"""
        schedules = []
        
        # 下高井戸シネマサイトのスケジュール解析
        body_text = soup.get_text()
        
        # 既知の映画と上映時間のパターンを解析
        schedule_patterns = [
            (r"旅するローマ教皇\s*.*?(\d{1,2}/\d{1,2}\(.\)～\d{1,2}/\d{1,2}\(.\))\s+(\d{1,2}:\d{2}～)", "旅するローマ教皇"),
            (r"ドマーニ！愛のことづて\s*.*?(\d{1,2}/\d{1,2}\(.\)～\d{1,2}/\d{1,2}\(.\))\s*(\d{1,2}：\d{2}～)", "ドマーニ！愛のことづて"),
            (r"シンシン／SING SING\s*.*?(\d{1,2}/\d{1,2}\(.\)～\d{1,2}/\d{1,2}\(.\))\s*(\d{1,2}:\d{2}～)", "シンシン／SING SING"),
            (r"カップルズ 4Kレストア版\s*.*?(\d{1,2}/\d{1,2}\(.\)～\d{1,2}/\d{1,2}\(.\))\s*(\d{1,2}:\d{2}～)", "カップルズ 4Kレストア版"),
            (r"井口奈己監督特集.*?(\d{1,2}/\d{1,2}\(.\)～\d{1,2}/\d{1,2}\(.\))\s*(\d{1,2}:\d{2})", "井口奈己監督特集")
        ]
        
        for pattern, movie_title in schedule_patterns:
            matches = re.findall(pattern, body_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    date_range = match[0]
                    showtime = match[1]
                    
                    # 日付範囲から開始日を抽出
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})', date_range)
                    if date_match:
                        month, day = date_match.groups()
                        formatted_date = f"2025-{int(month):02d}-{int(day):02d}"
                        
                        # 時間を正規化
                        time_normalized = showtime.replace('：', ':').replace('～', '').strip()
                        
                        schedules.append(MovieSchedule(
                            theater_name=self.theater_name,
                            movie_title=movie_title,
                            showtimes=[ShowtimeInfo(
                                date=formatted_date,
                                times=[time_normalized],
                                screen="スクリーン1"
                            )]
                        ))
        
        # フォールバック: テキストから時間パターンを検索
        if not schedules:
            # より一般的なスケジュールパターン検索
            lines = body_text.split('\n')
            current_movie = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 映画タイトルを検出
                if (line and len(line) > 3 and len(line) < 30 and
                    not any(skip in line for skip in ['年', '月', '日', '時', '～', ':', 'お知らせ', 'トーク']) and
                    (any(char in line for char in ['！', '？', '♪', '☆']) or 
                     re.search(r'[A-Za-z]{2,}', line) or
                     re.search(r'[ァ-ヴ]+', line))):
                    current_movie = line
                
                # スケジュール情報を検出
                if current_movie and re.search(r'\d{1,2}/\d{1,2}.*?\d{1,2}:\d{2}', line):
                    # 日付と時間を抽出
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})', line)
                    time_matches = re.findall(r'(\d{1,2}:\d{2})', line)
                    
                    if date_match and time_matches:
                        month, day = date_match.groups()
                        formatted_date = f"2025-{int(month):02d}-{int(day):02d}"
                        
                        schedules.append(MovieSchedule(
                            theater_name=self.theater_name,
                            movie_title=current_movie,
                            showtimes=[ShowtimeInfo(
                                date=formatted_date,
                                times=time_matches,
                                screen="スクリーン1"
                            )]
                        ))
                        current_movie = None  # リセット
                
        return schedules
        
    def _extract_schedules_from_item_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """アイテムページからスケジュール情報抽出"""
        schedules = []
        
        # 映画タイトル
        title_elem = soup.find("h1") or soup.find("h2", class_="item-title")
        movie_title = self.safe_extract_text(title_elem)
        
        if not movie_title:
            return schedules
            
        # 説明文からスケジュール情報を抽出
        description_elem = soup.find("div", class_="item-description") or soup.find("div", class_="description")
        description = self.safe_extract_text(description_elem)
        
        if description:
            showtimes = self._extract_showtimes_from_text(description)
            
            if showtimes:
                schedules.append(MovieSchedule(
                    theater_name=self.theater_name,
                    movie_title=movie_title,
                    showtimes=showtimes
                ))
                
        return schedules
        
    def _extract_showtimes_from_element(self, element) -> List[ShowtimeInfo]:
        """要素からスケジュール情報抽出"""
        showtimes = []
        
        # 日付と時間の組み合わせを検索
        date_time_pairs = element.find_all("div", class_="date-time") or element.find_all("li")
        
        for pair in date_time_pairs:
            # 日付
            date_elem = pair.find("span", class_="date") or pair.find("div", class_="date")
            date_text = self.safe_extract_text(date_elem)
            
            # 時刻
            time_elems = pair.find_all("span", class_="time") or pair.find_all("div", class_="time")
            times = [self.safe_extract_text(elem) for elem in time_elems if self.safe_extract_text(elem)]
            
            if date_text and times:
                formatted_date = self._format_date(date_text)
                
                showtimes.append(ShowtimeInfo(
                    date=formatted_date,
                    times=times,
                    screen="スクリーン1"
                ))
                
        return showtimes
        
    def _extract_showtimes_from_text(self, text: str) -> List[ShowtimeInfo]:
        """テキストからスケジュール情報抽出"""
        showtimes = []
        
        # 日付と時間のパターンを検索
        date_time_pattern = r"(\d{1,2}[/月]\d{1,2}[日]?)[^\d]*(\d{1,2}:\d{2})"
        matches = re.findall(date_time_pattern, text)
        
        current_date = None
        current_times = []
        
        for date_str, time_str in matches:
            formatted_date = self._format_date(date_str)
            
            if current_date and current_date != formatted_date:
                # 前の日付のデータを保存
                if current_times:
                    showtimes.append(ShowtimeInfo(
                        date=current_date,
                        times=current_times,
                        screen="スクリーン1"
                    ))
                current_times = []
                
            current_date = formatted_date
            current_times.append(time_str)
            
        # 最後のデータを保存
        if current_date and current_times:
            showtimes.append(ShowtimeInfo(
                date=current_date,
                times=current_times,
                screen="スクリーン1"
            ))
            
        return showtimes
        
    def _format_date(self, date_text: str) -> str:
        """日付フォーマット変換"""
        try:
            # 様々な日付形式に対応
            date_patterns = [
                r"(\d{1,2})/(\d{1,2})",  # MM/DD
                r"(\d{1,2})月(\d{1,2})日",  # MM月DD日
                r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
                r"(\d{1,2})\.(\d{1,2})",  # MM.DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    if len(match.groups()) == 2:
                        month, day = match.groups()
                        return f"2024-{int(month):02d}-{int(day):02d}"
                    elif len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                        
            return date_text
            
        except Exception:
            return date_text