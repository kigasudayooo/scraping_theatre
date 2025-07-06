from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class ShinjukuMusashinoScraper(BaseScraper):
    """新宿武蔵野館 スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="新宿武蔵野館",
            base_url="https://shinjuku.musashino-k.jp"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        soup = self.get_page(self.base_url)
        if not soup:
            soup = self.get_page_with_selenium(self.base_url)
            
        if not soup:
            # 基本情報をハードコード
            return TheaterInfo(
                name=self.theater_name,
                url=self.base_url,
                address="東京都新宿区新宿3-27-10",
                phone="03-3354-5670",
                access="JR新宿駅東口より徒歩5分",
                screens=2
            )
            
        # ページから詳細情報を取得
        address = "東京都新宿区新宿3-27-10"
        phone = "03-3354-5670"
        access = "JR新宿駅東口より徒歩5分"
        
        # アクセス情報ページから詳細取得
        access_soup = self.get_page(f"{self.base_url}/access/") or self.get_page_with_selenium(f"{self.base_url}/access/")
        
        if access_soup:
            # 住所情報
            address_elem = access_soup.find("div", class_="address") or access_soup.find("p", string=re.compile(r"新宿区"))
            if address_elem:
                address = self.clean_text(address_elem.get_text())
                
            # 電話番号
            phone_elem = access_soup.find("a", href=re.compile(r"tel:")) or access_soup.find("div", class_="tel")
            if phone_elem:
                phone_text = phone_elem.get("href", "") if phone_elem.name == "a" else phone_elem.get_text()
                phone = phone_text.replace("tel:", "").strip()
                
            # アクセス情報
            access_elem = access_soup.find("div", class_="access-info") or access_soup.find("section", id="access")
            if access_elem:
                access = self.clean_text(access_elem.get_text())
                
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
        soup = self.get_page(self.base_url) or self.get_page_with_selenium(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
            
        # 上映作品ページも確認
        works_urls = [
            f"{self.base_url}/works/",
            f"{self.base_url}/movies/",
            f"{self.base_url}/schedule/"
        ]
        
        for url in works_urls:
            works_soup = self.get_page(url) or self.get_page_with_selenium(url)
            if works_soup:
                movies.extend(self._extract_movies_from_page(works_soup))
                
        return movies
        
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出"""
        movies = []
        
        # 映画情報を含む要素を検索
        movie_selectors = [
            "div.movie-card",
            "div.movie-item",
            "article.movie",
            "div.film-info",
            "section.movie-section",
            "div.movies-list li",
            "div.work-item"
        ]
        
        movie_elements = []
        for selector in movie_selectors:
            elements = soup.select(selector)
            if elements:
                movie_elements.extend(elements)
                
        # 武蔵野館特有の構造も確認
        if not movie_elements:
            # ニュース記事から映画情報を抽出
            news_elements = soup.find_all("div", class_="news-item") or soup.find_all("article", class_="news")
            movie_elements.extend(news_elements)
            
        for element in movie_elements:
            movie = self._extract_movie_from_element(element)
            if movie:
                movies.append(movie)
                
        return movies
        
    def _extract_movie_from_element(self, element) -> Optional[MovieInfo]:
        """要素から映画情報抽出"""
        try:
            # タイトル
            title_elem = (element.find("h2") or element.find("h3") or element.find("h4") or
                         element.find("div", class_="title") or element.find("a", class_="movie-title"))
            title = self.safe_extract_text(title_elem)
            
            if not title:
                return None
                
            # 英語タイトル
            title_en_elem = element.find("p", class_="title-en") or element.find("div", class_="title-en")
            title_en = self.safe_extract_text(title_en_elem)
            
            # 映画情報から詳細を抽出
            info_elem = element.find("div", class_="movie-info") or element.find("div", class_="film-details")
            info_text = self.safe_extract_text(info_elem) if info_elem else element.get_text()
            
            director = ""
            cast = []
            genre = ""
            synopsis = ""
            duration = None
            
            if info_text:
                # 監督情報
                director_patterns = [
                    r"監督[：:]([^\n/]+)",
                    r"脚本・監督[：:]([^\n/]+)",
                    r"Director[：:]([^\n/]+)"
                ]
                
                for pattern in director_patterns:
                    match = re.search(pattern, info_text)
                    if match:
                        director = match.group(1).strip()
                        break
                        
                # 出演者情報
                cast_patterns = [
                    r"出演[：:]([^\n/]+)",
                    r"キャスト[：:]([^\n/]+)",
                    r"Cast[：:]([^\n/]+)"
                ]
                
                for pattern in cast_patterns:
                    match = re.search(pattern, info_text)
                    if match:
                        cast_text = match.group(1).strip()
                        cast = [c.strip() for c in re.split(r"[,、]", cast_text) if c.strip()]
                        break
                        
                # 上映時間
                duration_match = re.search(r"(\d+)分", info_text)
                if duration_match:
                    duration = int(duration_match.group(1))
                    
                # ジャンル情報
                genre_patterns = [
                    r"ジャンル[：:]([^\n/]+)",
                    r"カテゴリー[：:]([^\n/]+)"
                ]
                
                for pattern in genre_patterns:
                    match = re.search(pattern, info_text)
                    if match:
                        genre = match.group(1).strip()
                        break
                        
            # あらすじ
            synopsis_elem = element.find("div", class_="synopsis") or element.find("p", class_="description")
            if synopsis_elem:
                synopsis = self.safe_extract_text(synopsis_elem)
            elif info_text and len(info_text) > 100:
                synopsis = info_text[:200] + "..." if len(info_text) > 200 else info_text
                
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
        
        # スケジュールページを取得
        schedule_soup = self.get_page(f"{self.base_url}/schedule/") or self.get_page_with_selenium(f"{self.base_url}/schedule/")
        if schedule_soup:
            schedules.extend(self._extract_schedules_from_page(schedule_soup))
            
        # メインページからもスケジュール情報を確認
        main_soup = self.get_page(self.base_url) or self.get_page_with_selenium(self.base_url)
        if main_soup:
            schedules.extend(self._extract_schedules_from_page(main_soup))
            
        return schedules
        
    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出"""
        schedules = []
        
        # スケジュール情報を含む要素を検索
        schedule_elements = (soup.find_all("div", class_="schedule") or 
                           soup.find_all("table", class_="schedule") or
                           soup.find_all("div", class_="timetable") or
                           soup.find_all("section", class_="schedule-section"))
        
        # スケジュールテーブルも確認
        schedule_tables = soup.find_all("table")
        for table in schedule_tables:
            if "schedule" in table.get("class", []) or "timetable" in table.get("class", []):
                schedule_elements.append(table)
                
        for element in schedule_elements:
            try:
                # 映画タイトル
                title_elem = (element.find("h2") or element.find("h3") or 
                             element.find("caption") or element.find("div", class_="movie-title"))
                movie_title = self.safe_extract_text(title_elem)
                
                if not movie_title:
                    continue
                    
                # 上映時間情報
                showtimes = self._extract_showtimes_from_element(element)
                
                if showtimes:
                    schedules.append(MovieSchedule(
                        theater_name=self.theater_name,
                        movie_title=movie_title,
                        showtimes=showtimes
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error extracting schedule info: {e}")
                continue
                
        return schedules
        
    def _extract_showtimes_from_element(self, element) -> List[ShowtimeInfo]:
        """要素からスケジュール情報抽出"""
        showtimes = []
        
        # テーブル形式のスケジュール
        if element.name == "table":
            rows = element.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    # 日付セル
                    date_text = self.safe_extract_text(cells[0])
                    # 時間セル
                    time_cells = cells[1:]
                    times = [self.safe_extract_text(cell) for cell in time_cells if self.safe_extract_text(cell)]
                    
                    if date_text and times:
                        formatted_date = self._format_date(date_text)
                        if formatted_date:
                            showtimes.append(ShowtimeInfo(
                                date=formatted_date,
                                times=times,
                                screen="スクリーン1"
                            ))
        else:
            # div形式のスケジュール
            date_blocks = element.find_all("div", class_="date-block") or element.find_all("div", class_="schedule-day")
            
            for block in date_blocks:
                # 日付
                date_elem = block.find("div", class_="date") or block.find("span", class_="date")
                date_text = self.safe_extract_text(date_elem)
                
                # 時刻
                time_elems = block.find_all("span", class_="time") or block.find_all("div", class_="time")
                times = [self.safe_extract_text(elem) for elem in time_elems if self.safe_extract_text(elem)]
                
                # スクリーン情報
                screen_elem = block.find("span", class_="screen") or block.find("div", class_="screen")
                screen = self.safe_extract_text(screen_elem) if screen_elem else "スクリーン1"
                
                if date_text and times:
                    formatted_date = self._format_date(date_text)
                    if formatted_date:
                        showtimes.append(ShowtimeInfo(
                            date=formatted_date,
                            times=times,
                            screen=screen
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
                        
            return ""
            
        except Exception:
            return ""