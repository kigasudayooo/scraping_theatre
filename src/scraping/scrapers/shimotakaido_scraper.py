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
            base_url="https://shimotakaido-cinema.stores.jp"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        # Storesサイトは403エラーが発生するため、Seleniumを使用
        soup = self.get_page_with_selenium(self.base_url)
        if not soup:
            # 基本情報をハードコード
            return TheaterInfo(
                name=self.theater_name,
                url=self.base_url,
                address="東京都世田谷区松原3-27-26",
                phone="03-3321-0684",
                access="京王線下高井戸駅より徒歩3分",
                screens=1
            )
            
        # ページから詳細情報を取得
        address = "東京都世田谷区松原3-27-26"
        phone = "03-3321-0684"
        access = "京王線下高井戸駅より徒歩3分"
        
        # 動的に情報を取得
        address_elem = soup.find("div", class_="address") or soup.find("p", string=re.compile(r"世田谷区"))
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
            screens=1
        )
        
    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得"""
        movies = []
        
        # メインページから映画情報取得
        soup = self.get_page_with_selenium(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
            
        # 商品ページも確認（Storesサイトの特徴）
        items_soup = self.get_page_with_selenium(f"{self.base_url}/items")
        if items_soup:
            movies.extend(self._extract_movies_from_items_page(items_soup))
            
        return movies
        
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出"""
        movies = []
        
        # Storesサイトの映画アイテム
        movie_selectors = [
            "div.item",
            "div.product",
            "div.movie-item",
            "article.item",
            "div.stores-item"
        ]
        
        movie_elements = []
        for selector in movie_selectors:
            elements = soup.select(selector)
            if elements:
                movie_elements.extend(elements)
                
        for element in movie_elements:
            movie = self._extract_movie_from_element(element)
            if movie:
                movies.append(movie)
                
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
        
        # スケジュール情報は商品ページの詳細に含まれる可能性
        soup = self.get_page_with_selenium(self.base_url)
        if soup:
            schedules.extend(self._extract_schedules_from_page(soup))
            
        # 個別の映画ページも確認
        movie_links = soup.find_all("a", href=re.compile(r"/items/")) if soup else []
        
        for link in movie_links:
            item_url = link.get("href")
            if not item_url.startswith("http"):
                item_url = f"{self.base_url}{item_url}"
                
            item_soup = self.get_page_with_selenium(item_url)
            if item_soup:
                schedules.extend(self._extract_schedules_from_item_page(item_soup))
                
        return schedules
        
    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出"""
        schedules = []
        
        # スケジュール情報を含む可能性のある要素
        schedule_elements = soup.find_all("div", class_="schedule") or soup.find_all("div", class_="timetable")
        
        for element in schedule_elements:
            try:
                # 映画タイトル
                title_elem = element.find("h3") or element.find("h2")
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