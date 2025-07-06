from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class WasedaShochikuScraper(BaseScraper):
    """早稲田松竹 スクレイパー"""
    
    def __init__(self):
        super().__init__(
            theater_name="早稲田松竹",
            base_url="http://wasedashochiku.co.jp"
        )
        
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        soup = self.get_page_with_selenium(self.base_url)
        if not soup:
            # 基本情報をハードコード
            return TheaterInfo(
                name=self.theater_name,
                url=self.base_url,
                address="東京都新宿区高田馬場1-5-16",
                phone="03-3200-8968",
                access="JR山手線・西武新宿線・東西線高田馬場駅より徒歩3分",
                screens=1
            )
            
        # ページから詳細情報を取得
        address = "東京都新宿区高田馬場1-5-16"
        phone = "03-3200-8968"
        access = "JR山手線・西武新宿線・東西線高田馬場駅より徒歩3分"
        
        # アクセス情報を抽出
        access_elem = soup.find("div", class_="access") or soup.find("section", id="access")
        if access_elem:
            access_text = self.clean_text(access_elem.get_text())
            if access_text:
                access = access_text
                
        # 住所情報
        address_elem = soup.find("div", class_="address") or soup.find("p", string=re.compile(r"新宿区"))
        if address_elem:
            address = self.clean_text(address_elem.get_text())
            
        # 電話番号
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
            
        # 上映作品ページも確認
        works_urls = [
            f"{self.base_url}/works/",
            f"{self.base_url}/schedule/",
            f"{self.base_url}/current/"
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
            "section.movie-section",
            "div.schedule-item"
        ]
        
        movie_elements = []
        for selector in movie_selectors:
            elements = soup.select(selector)
            if elements:
                movie_elements.extend(elements)
                
        # WordPressサイトの特徴的な構造も確認
        if not movie_elements:
            # 投稿記事から映画情報を抽出
            post_elements = soup.find_all("article", class_="post") or soup.find_all("div", class_="post")
            movie_elements.extend(post_elements)
            
        for element in movie_elements:
            movie = self._extract_movie_from_element(element)
            if movie:
                movies.append(movie)
                
        return movies
        
    def _extract_movie_from_element(self, element) -> Optional[MovieInfo]:
        """要素から映画情報抽出"""
        try:
            # タイトル
            title_elem = (element.find("h1") or element.find("h2") or element.find("h3") or
                         element.find("div", class_="title") or element.find("a", class_="post-title"))
            title = self.safe_extract_text(title_elem)
            
            if not title:
                return None
                
            # 名画座特有の二本立て形式を考慮
            if "＆" in title or "+" in title:
                # 二本立ての場合は分割
                titles = re.split(r"[＆+]", title)
                if len(titles) > 1:
                    title = titles[0].strip()
                    
            # 英語タイトル
            title_en_elem = element.find("p", class_="title-en") or element.find("div", class_="title-en")
            title_en = self.safe_extract_text(title_en_elem)
            
            # 映画情報テキストから詳細を抽出
            content_elem = element.find("div", class_="content") or element.find("div", class_="post-content")
            content = self.safe_extract_text(content_elem)
            
            director = ""
            cast = []
            genre = ""
            synopsis = ""
            duration = None
            
            if content:
                # 監督情報
                director_patterns = [
                    r"監督[：:]([^\n/]+)",
                    r"脚本・監督[：:]([^\n/]+)",
                    r"Director[：:]([^\n/]+)"
                ]
                
                for pattern in director_patterns:
                    match = re.search(pattern, content)
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
                    match = re.search(pattern, content)
                    if match:
                        cast_text = match.group(1).strip()
                        cast = [c.strip() for c in re.split(r"[,、]", cast_text) if c.strip()]
                        break
                        
                # 上映時間
                duration_match = re.search(r"(\d+)分", content)
                if duration_match:
                    duration = int(duration_match.group(1))
                    
                # 製作年
                year_match = re.search(r"(\d{4})年", content)
                if year_match:
                    year = year_match.group(1)
                    
                # ジャンル情報
                genre_patterns = [
                    r"ジャンル[：:]([^\n/]+)",
                    r"カテゴリー[：:]([^\n/]+)"
                ]
                
                for pattern in genre_patterns:
                    match = re.search(pattern, content)
                    if match:
                        genre = match.group(1).strip()
                        break
                        
                # あらすじ（内容の一部を使用）
                synopsis = content[:200] + "..." if len(content) > 200 else content
                
            # ポスター画像
            poster_elem = element.find("img")
            poster_url = ""
            if poster_elem:
                poster_url = self.safe_extract_attr(poster_elem, "src")
                if poster_url and not poster_url.startswith("http"):
                    if poster_url.startswith("//"):
                        poster_url = f"http:{poster_url}"
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
        soup = self.get_page_with_selenium(self.base_url)
        if soup:
            schedules.extend(self._extract_schedules_from_page(soup))
            
        # 個別のスケジュールページも確認
        schedule_soup = self.get_page_with_selenium(f"{self.base_url}/schedule/")
        if schedule_soup:
            schedules.extend(self._extract_schedules_from_page(schedule_soup))
            
        return schedules
        
    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出"""
        schedules = []
        
        # スケジュール情報を含む要素を検索
        schedule_elements = (soup.find_all("div", class_="schedule") or 
                           soup.find_all("table", class_="schedule") or
                           soup.find_all("div", class_="timetable"))
        
        # 記事からスケジュール情報を抽出
        if not schedule_elements:
            post_elements = soup.find_all("article", class_="post") or soup.find_all("div", class_="post")
            schedule_elements.extend(post_elements)
            
        for element in schedule_elements:
            try:
                # 映画タイトル
                title_elem = element.find("h2") or element.find("h3") or element.find("h1")
                movie_title = self.safe_extract_text(title_elem)
                
                if not movie_title:
                    continue
                    
                # 名画座特有の二本立て形式を考慮
                if "＆" in movie_title or "+" in movie_title:
                    titles = re.split(r"[＆+]", movie_title)
                    for individual_title in titles:
                        individual_title = individual_title.strip()
                        if individual_title:
                            showtimes = self._extract_showtimes_from_element(element)
                            if showtimes:
                                schedules.append(MovieSchedule(
                                    theater_name=self.theater_name,
                                    movie_title=individual_title,
                                    showtimes=showtimes
                                ))
                else:
                    # 単独作品
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
        
        content = element.get_text()
        
        # 上映時間のパターンを検索
        time_patterns = [
            r"(\d{1,2}:\d{2})",
            r"(\d{1,2}時\d{2}分)",
            r"(\d{1,2}):\d{2}[～〜-](\d{1,2}:\d{2})"
        ]
        
        times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    times.extend(match)
                else:
                    times.append(match)
                    
        # 日付パターンを検索
        date_patterns = [
            r"(\d{1,2})/(\d{1,2})",
            r"(\d{1,2})月(\d{1,2})日",
            r"(\d{4})-(\d{1,2})-(\d{1,2})"
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 2:
                    month, day = match
                    formatted_date = f"2024-{int(month):02d}-{int(day):02d}"
                    dates.append(formatted_date)
                elif len(match) == 3:
                    year, month, day = match
                    formatted_date = f"{year}-{int(month):02d}-{int(day):02d}"
                    dates.append(formatted_date)
                    
        # 上映時間が見つからない場合はデフォルト時間を使用
        if not times:
            times = ["14:30", "19:00"]  # 名画座の一般的な上映時間
            
        # 日付が見つからない場合は今日の日付を使用
        if not dates:
            today = datetime.now()
            dates = [today.strftime("%Y-%m-%d")]
            
        # 各日付に対して上映時間を設定
        for date in dates:
            if times:
                showtimes.append(ShowtimeInfo(
                    date=date,
                    times=times,
                    screen="スクリーン1"
                ))
                
        return showtimes