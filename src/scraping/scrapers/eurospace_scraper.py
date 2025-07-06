from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class EurospaceScraper(BaseScraper):
    """ユーロスペース スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="ユーロスペース",
            base_url="https://www.eurospace.co.jp"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        # SSL問題の可能性があるため、Seleniumを使用
        soup = self.get_page_with_selenium(self.base_url)
        if not soup:
            # 基本情報をハードコード
            return TheaterInfo(
                name=self.theater_name,
                url=self.base_url,
                address="東京都渋谷区円山町1-5 キノハウス地下2階",
                phone="03-3461-0211",
                access="JR渋谷駅より徒歩5分",
                screens=2
            )
            
        # アクセス情報を抽出
        address = "東京都渋谷区円山町1-5 キノハウス地下2階"
        phone = "03-3461-0211"
        access = "JR渋谷駅より徒歩5分"
        
        # ページから詳細情報を取得
        address_elem = soup.find("div", class_="address") or soup.find("p", string=re.compile(r"渋谷区"))
        if address_elem:
            address = self.clean_text(address_elem.get_text())
            
        phone_elem = soup.find("a", href=re.compile(r"tel:")) or soup.find("div", class_="tel")
        if phone_elem:
            phone_text = phone_elem.get("href", "") if phone_elem.name == "a" else phone_elem.get_text()
            phone = phone_text.replace("tel:", "").strip()
            
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
            movies.extend(self._extract_movies_from_page(soup))
            
        # 作品一覧ページも確認
        works_urls = [
            f"{self.base_url}/works/",
            f"{self.base_url}/current/",
            f"{self.base_url}/coming/"
        ]
        
        for url in works_urls:
            works_soup = self.get_page_with_selenium(url)
            if works_soup:
                movies.extend(self._extract_movies_from_page(works_soup))
                
        return movies
        
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出"""
        movies = []
        
        # 映画情報を含む要素を検索
        movie_selectors = [
            "div.movie-item",
            "div.work-item",
            "article.movie",
            "div.film-info",
            "section.movie-section"
        ]
        
        movie_elements = []
        for selector in movie_selectors:
            elements = soup.select(selector)
            if elements:
                movie_elements.extend(elements)
                
        # 汎用的な検索も実行
        if not movie_elements:
            # h2, h3タグから映画タイトルを推定
            title_elements = soup.find_all(["h2", "h3"])
            for elem in title_elements:
                parent = elem.parent
                if parent and self._is_movie_element(parent):
                    movie_elements.append(parent)
                    
        for element in movie_elements:
            movie = self._extract_movie_from_element(element)
            if movie:
                movies.append(movie)
                
        return movies
        
    def _is_movie_element(self, element) -> bool:
        """要素が映画情報を含むかチェック"""
        text = element.get_text().lower()
        movie_indicators = ["監督", "出演", "分", "上映", "劇場", "作品", "映画"]
        return any(indicator in text for indicator in movie_indicators)
        
    def _extract_movie_from_element(self, element) -> Optional[MovieInfo]:
        """要素から映画情報抽出"""
        try:
            # タイトル
            title_elem = element.find(["h2", "h3", "h4"]) or element.find("div", class_="title")
            title = self.safe_extract_text(title_elem)
            
            if not title:
                return None
                
            # 英語タイトル
            title_en_elem = element.find("p", class_="title-en") or element.find("div", class_="title-en")
            title_en = self.safe_extract_text(title_en_elem)
            
            # 監督情報
            director = self._extract_info_by_label(element, "監督")
            
            # 出演者情報
            cast_text = self._extract_info_by_label(element, "出演")
            cast = [c.strip() for c in cast_text.split(",") if c.strip()] if cast_text else []
            
            # 上映時間
            duration = self._extract_duration(element)
            
            # ジャンル
            genre = self._extract_info_by_label(element, "ジャンル")
            
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
            
    def _extract_info_by_label(self, element, label: str) -> str:
        """ラベルによる情報抽出"""
        # ラベル付きの情報を検索
        label_patterns = [
            f"{label}：",
            f"{label}:",
            f"<strong>{label}</strong>",
            f"<b>{label}</b>"
        ]
        
        text = element.get_text()
        for pattern in label_patterns:
            if pattern in text:
                # パターンの後の文字列を取得
                parts = text.split(pattern, 1)
                if len(parts) > 1:
                    info = parts[1].split("\n")[0].strip()
                    return info
                    
        return ""
        
    def _extract_duration(self, element) -> Optional[int]:
        """上映時間抽出"""
        text = element.get_text()
        duration_match = re.search(r"(\d+)分", text)
        if duration_match:
            return int(duration_match.group(1))
        return None
        
    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得"""
        schedules = []
        
        # スケジュールページを取得
        schedule_urls = [
            f"{self.base_url}/schedule/",
            f"{self.base_url}/timetable/"
        ]
        
        for url in schedule_urls:
            soup = self.get_page_with_selenium(url)
            if soup:
                schedules.extend(self._extract_schedules_from_page(soup))
                
        return schedules
        
    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出"""
        schedules = []
        
        # スケジュールテーブルを検索
        schedule_tables = soup.find_all("table", class_="schedule") or soup.find_all("div", class_="schedule")
        
        for table in schedule_tables:
            try:
                # 映画タイトル
                title_elem = table.find("h3") or table.find("h2") or table.find("caption")
                movie_title = self.safe_extract_text(title_elem)
                
                if not movie_title:
                    continue
                    
                # 上映時間情報
                showtimes = []
                
                # 行ごとに処理
                rows = table.find_all("tr") if table.name == "table" else table.find_all("div", class_="schedule-row")
                
                for row in rows:
                    # 日付
                    date_elem = row.find("td", class_="date") or row.find("div", class_="date")
                    date_text = self.safe_extract_text(date_elem)
                    
                    # 時刻
                    time_elems = row.find_all("td", class_="time") or row.find_all("span", class_="time")
                    times = [self.safe_extract_text(elem) for elem in time_elems if self.safe_extract_text(elem)]
                    
                    if date_text and times:
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