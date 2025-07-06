from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_scraper import BaseScraper
from models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class KsCinemaScraper(BaseScraper):
    """ケイズシネマ スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="ケイズシネマ",
            base_url="https://www.ks-cinema.com"
        )
        self.schedule_url = f"{self.base_url}/schedule/"
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        soup = self.get_page(self.base_url)
        if not soup:
            return TheaterInfo(name=self.theater_name, url=self.base_url)
            
        # アクセス情報ページから詳細取得
        access_soup = self.get_page(f"{self.base_url}/access/")
        
        address = ""
        phone = ""
        access = ""
        
        if access_soup:
            # 住所情報
            address_elem = access_soup.find("div", class_="address")
            if address_elem:
                address = self.clean_text(address_elem.get_text())
                
            # 電話番号
            phone_elem = access_soup.find("a", href=re.compile(r"tel:"))
            if phone_elem:
                phone = phone_elem.get("href").replace("tel:", "")
                
            # アクセス情報
            access_elem = access_soup.find("div", class_="access-info")
            if access_elem:
                access = self.clean_text(access_elem.get_text())
                
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address=address,
            phone=phone,
            access=access,
            screens=1  # 基本的に1スクリーン
        )
        
    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得"""
        movies = []
        
        # 現在上映中の映画
        soup = self.get_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
            
        # 近日公開の映画
        coming_soup = self.get_page(f"{self.base_url}/coming/")
        if coming_soup:
            movies.extend(self._extract_movies_from_page(coming_soup))
            
        return movies
        
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出"""
        movies = []
        
        # 映画カード要素を取得
        movie_cards = soup.find_all("div", class_="movie-card") or soup.find_all("article", class_="movie")
        
        for card in movie_cards:
            try:
                # タイトル
                title_elem = card.find("h2") or card.find("h3") or card.find("div", class_="title")
                title = self.safe_extract_text(title_elem)
                
                if not title:
                    continue
                    
                # 英語タイトル
                title_en_elem = card.find("p", class_="title-en")
                title_en = self.safe_extract_text(title_en_elem)
                
                # 監督
                director_elem = card.find("div", class_="director") or card.find("p", class_="director")
                director = self.safe_extract_text(director_elem)
                
                # 出演者
                cast_elem = card.find("div", class_="cast") or card.find("p", class_="cast")
                cast_text = self.safe_extract_text(cast_elem)
                cast = [c.strip() for c in cast_text.split(",") if c.strip()] if cast_text else []
                
                # 上映時間
                duration_elem = card.find("div", class_="duration")
                duration = None
                if duration_elem:
                    duration_text = self.safe_extract_text(duration_elem)
                    duration_match = re.search(r"(\d+)分", duration_text)
                    if duration_match:
                        duration = int(duration_match.group(1))
                        
                # あらすじ
                synopsis_elem = card.find("div", class_="synopsis") or card.find("p", class_="description")
                synopsis = self.safe_extract_text(synopsis_elem)
                
                # ポスター画像
                poster_elem = card.find("img")
                poster_url = ""
                if poster_elem:
                    poster_url = self.safe_extract_attr(poster_elem, "src")
                    if poster_url and not poster_url.startswith("http"):
                        poster_url = f"{self.base_url}{poster_url}"
                        
                movies.append(MovieInfo(
                    title=title,
                    title_en=title_en if title_en else None,
                    director=director if director else None,
                    cast=cast,
                    duration=duration,
                    synopsis=synopsis if synopsis else None,
                    poster_url=poster_url if poster_url else None
                ))
                
            except Exception as e:
                self.logger.error(f"Error extracting movie info: {e}")
                continue
                
        return movies
        
    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得"""
        schedules = []
        
        soup = self.get_page(self.schedule_url)
        if not soup:
            return schedules
            
        # スケジュール情報を抽出
        schedule_sections = soup.find_all("div", class_="schedule-section") or soup.find_all("section", class_="movie-schedule")
        
        for section in schedule_sections:
            try:
                # 映画タイトル
                title_elem = section.find("h3") or section.find("h2")
                movie_title = self.safe_extract_text(title_elem)
                
                if not movie_title:
                    continue
                    
                # 上映時間情報
                showtimes = []
                date_blocks = section.find_all("div", class_="date-block") or section.find_all("tr")
                
                for date_block in date_blocks:
                    # 日付
                    date_elem = date_block.find("div", class_="date") or date_block.find("td", class_="date")
                    date_text = self.safe_extract_text(date_elem)
                    
                    # 時刻
                    time_elems = date_block.find_all("span", class_="time") or date_block.find_all("td", class_="time")
                    times = [self.safe_extract_text(elem) for elem in time_elems if self.safe_extract_text(elem)]
                    
                    if date_text and times:
                        # 日付フォーマット変換
                        formatted_date = self._format_date(date_text)
                        
                        showtimes.append(ShowtimeInfo(
                            date=formatted_date,
                            times=times,
                            screen="スクリーン1"
                        ))
                        
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
        
    def _format_date(self, date_text: str) -> str:
        """日付フォーマット変換"""
        try:
            # 様々な日付形式に対応
            date_patterns = [
                r"(\d{1,2})/(\d{1,2})",  # MM/DD
                r"(\d{1,2})月(\d{1,2})日",  # MM月DD日
                r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
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