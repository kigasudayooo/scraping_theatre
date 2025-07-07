from typing import List, Optional
from datetime import datetime
import re
import json
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class PolePoleHigashinakanoScraper(BaseScraper):
    """ポレポレ東中野 スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="ポレポレ東中野",
            base_url="https://pole2.co.jp"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        # Nuxt.jsアプリケーションのため、Seleniumを使用
        soup = self.get_page_with_selenium(self.base_url)
        if not soup:
            return TheaterInfo(name=self.theater_name, url=self.base_url)
            
        # アクセス情報
        access_soup = self.get_page_with_selenium(f"{self.base_url}/access")
        
        address = "東京都中野区東中野4-4-1 ポレポレ坐ビル地下"
        phone = "03-3371-0088"
        access = "JR中央線・総武線・都営大江戸線東中野駅より徒歩1分"
        
        if access_soup:
            # 詳細情報があれば更新
            address_elem = access_soup.find("div", class_="address")
            if address_elem:
                address = self.clean_text(address_elem.get_text())
                
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address=address,
            phone=phone,
            access=access,
            screens=2
        )
        
    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得"""
        movies = []
        
        # メインページから映画情報取得
        soup = self.get_page_with_selenium(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_main_page(soup))
            
        # 作品一覧ページも確認
        works_soup = self.get_page_with_selenium(f"{self.base_url}/works")
        if works_soup:
            movies.extend(self._extract_movies_from_works_page(works_soup))
            
        return movies
        
    def _extract_movies_from_main_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """メインページから映画情報抽出（Nuxt.jsレンダリング後）"""
        movies = []
        
        # Seleniumで取得したページからテキストを解析
        body_text = soup.get_text()
        
        # 映画タイトルをテキストから抽出
        lines = body_text.split('\n')
        movie_titles = []
        
        # スケジュール部分から映画タイトルを抽出
        in_schedule_section = False
        for line in lines:
            line = line.strip()
            
            if '上映スケジュール' in line:
                in_schedule_section = True
                continue
            
            if in_schedule_section and line:
                # 日付やその他の情報をスキップして映画タイトルを抽出
                if not any(keyword in line for keyword in [
                    '月', '火', '水', '木', '金', '土', '日',
                    'ポレポレ東中野', '座席表', '購入', '2D', '字幕',
                    'もっとみる', ':', '〜'
                ]) and len(line) > 3 and not line.isdigit():
                    # レーティングや記号を除去
                    clean_title = re.sub(r'\s*[GR12+]\s*$', '', line)
                    clean_title = re.sub(r'【.*?】', '', clean_title)
                    clean_title = clean_title.strip()
                    
                    if clean_title and clean_title not in movie_titles:
                        movie_titles.append(clean_title)
        
        # MovieInfoオブジェクトを作成
        for title in movie_titles:
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
        
    def _extract_movies_from_works_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """作品ページから映画情報抽出"""
        movies = []
        
        movie_cards = soup.find_all("div", class_="work-card") or soup.find_all("div", class_="movie-card")
        
        for card in movie_cards:
            movie = self._extract_movie_from_element(card)
            if movie:
                movies.append(movie)
                
        return movies
        
    def _extract_movie_from_element(self, element) -> Optional[MovieInfo]:
        """要素から映画情報抽出"""
        try:
            # タイトル
            title_elem = element.find("h2") or element.find("h3") or element.find("div", class_="title")
            title = self.safe_extract_text(title_elem)
            
            if not title:
                return None
                
            # 英語タイトル
            title_en_elem = element.find("p", class_="title-en") or element.find("div", class_="title-en")
            title_en = self.safe_extract_text(title_en_elem)
            
            # 監督
            director_elem = element.find("div", class_="director") or element.find("p", class_="director")
            director = self.safe_extract_text(director_elem)
            if director.startswith("監督："):
                director = director[3:]
                
            # 出演者
            cast_elem = element.find("div", class_="cast") or element.find("p", class_="cast")
            cast_text = self.safe_extract_text(cast_elem)
            if cast_text.startswith("出演："):
                cast_text = cast_text[3:]
            cast = [c.strip() for c in cast_text.split(",") if c.strip()] if cast_text else []
            
            # 上映時間
            duration_elem = element.find("div", class_="duration") or element.find("span", class_="runtime")
            duration = None
            if duration_elem:
                duration_text = self.safe_extract_text(duration_elem)
                duration_match = re.search(r"(\d+)分", duration_text)
                if duration_match:
                    duration = int(duration_match.group(1))
                    
            # ジャンル
            genre_elem = element.find("div", class_="genre") or element.find("span", class_="genre")
            genre = self.safe_extract_text(genre_elem)
            
            # あらすじ
            synopsis_elem = element.find("div", class_="synopsis") or element.find("p", class_="description")
            synopsis = self.safe_extract_text(synopsis_elem)
            
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
        """スケジュール情報取得（テキスト解析）"""
        schedules = []
        
        # メインページから取得（スケジュール情報が含まれている）
        soup = self.get_page_with_selenium(self.base_url)
        if not soup:
            return schedules
        
        body_text = soup.get_text()
        lines = body_text.split('\n')
        
        # スケジュール情報をパース
        current_movie = None
        current_date = None
        current_times = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 日付の検出 (MM/DD形式)
            date_match = re.match(r'(\d{2})/(\d{2})', line)
            if date_match:
                # 前の映画のスケジュールを保存
                if current_movie and current_times:
                    schedules.append(MovieSchedule(
                        theater_name=self.theater_name,
                        movie_title=current_movie,
                        showtimes=[ShowtimeInfo(
                            date=current_date,
                            times=current_times,
                            screen="ポレポレ東中野（地下）"
                        )]
                    ))
                
                # 新しい日付
                month, day = date_match.groups()
                current_date = f"2025-{month}-{day}"
                current_times = []
                continue
            
            # 映画タイトルの検出（特定の除外条件）
            if (line and 
                len(line) > 3 and
                not any(keyword in line for keyword in [
                    '月', '火', '水', '木', '金', '土', '日',
                    'ポレポレ東中野', '座席表', '購入', '2D', '字幕',
                    'もっとみる', ':', '〜', 'バリアフリー'
                ]) and 
                not line.isdigit() and
                not re.match(r'^\d{1,2}:\d{2}', line)):
                
                # 前の映画のスケジュールを保存
                if current_movie and current_times and current_date:
                    schedules.append(MovieSchedule(
                        theater_name=self.theater_name,
                        movie_title=current_movie,
                        showtimes=[ShowtimeInfo(
                            date=current_date,
                            times=current_times,
                            screen="ポレポレ東中野（地下）"
                        )]
                    ))
                
                # 新しい映画
                current_movie = re.sub(r'\s*[GR12+]\s*$', '', line)
                current_movie = re.sub(r'【.*?】', '', current_movie).strip()
                current_times = []
                continue
            
            # 時刻の検出
            time_match = re.match(r'^(\d{1,2}:\d{2})$', line)
            if time_match and current_movie:
                current_times.append(time_match.group(1))
        
        # 最後の映画のスケジュールを保存
        if current_movie and current_times and current_date:
            schedules.append(MovieSchedule(
                theater_name=self.theater_name,
                movie_title=current_movie,
                showtimes=[ShowtimeInfo(
                    date=current_date,
                    times=current_times,
                    screen="ポレポレ東中野（地下）"
                )]
            ))
        
        return schedules
        
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