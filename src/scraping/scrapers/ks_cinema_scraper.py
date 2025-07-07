from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

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
        
        # ケイズシネマの実際の構造に合わせて修正
        movielist = soup.find("div", class_="movielist")
        if not movielist:
            return movies
            
        # div.box clearfix が個別の映画情報
        movie_boxes = movielist.find_all("div", class_="box")
        
        for box in movie_boxes:
            try:
                # movietxt内のテキストから情報を抽出
                movietxt = box.find("div", class_="movietxt")
                if not movietxt:
                    continue
                
                # 全テキストを取得
                full_text = movietxt.get_text(strip=True)
                if not full_text:
                    continue
                
                # タイトルを抽出（最初の行から時刻を除外）
                title_line = full_text.split('\n')[0].strip()
                
                # 時刻パターンを除去してタイトルを抽出
                title = re.sub(r'\d{1,2}:\d{2}', '', title_line).strip()
                
                # 特殊なケースの処理
                if '作品案内参照' in title:
                    # 特別上映などの場合はスキップするか簡略化
                    continue
                
                if not title:
                    continue
                
                # 上映時間を抽出
                times = re.findall(r'\d{1,2}:\d{2}', full_text)
                
                # 基本的な映画情報を作成
                title_en = None
                director = None
                cast = []
                duration = None
                synopsis = None
                
                # ポスター画像
                poster_elem = box.find("img")
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
        
        # メインページから情報を取得（ケイズシネマはメインページにスケジュールがある）
        soup = self.get_page(self.base_url)
        if not soup:
            return schedules
        
        movielist = soup.find("div", class_="movielist")
        if not movielist:
            return schedules
            
        # div.box clearfix からスケジュール情報を抽出
        movie_boxes = movielist.find_all("div", class_="box")
        
        for box in movie_boxes:
            try:
                # movietxt内のテキストから情報を抽出
                movietxt = box.find("div", class_="movietxt")
                if not movietxt:
                    continue
                
                # 全テキストを取得
                full_text = movietxt.get_text(strip=True)
                if not full_text:
                    continue
                
                # タイトルを抽出
                title_line = full_text.split('\n')[0].strip()
                movie_title = re.sub(r'\d{1,2}:\d{2}', '', title_line).strip()
                
                # 特殊なケースをスキップ
                if '作品案内参照' in movie_title:
                    continue
                
                if not movie_title:
                    continue
                
                # 上映時間を抽出
                times = re.findall(r'\d{1,2}:\d{2}', full_text)
                
                if times:
                    # 今日の日付でスケジュール作成（実際のサイトでは日付情報が限定的）
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    showtimes = [ShowtimeInfo(
                        date=today,
                        times=times,
                        screen="スクリーン1"
                    )]
                    
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