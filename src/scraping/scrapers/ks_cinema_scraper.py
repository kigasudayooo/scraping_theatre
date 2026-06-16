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
        access_soup = self.get_page(f"{self.base_url}/access/")

        address = ""
        phone = ""
        access = ""

        if access_soup:
            address_elem = access_soup.find("div", class_="address")
            if address_elem:
                address = self.clean_text(address_elem.get_text())

            phone_elem = access_soup.find("a", href=re.compile(r"tel:"))
            if phone_elem:
                phone = phone_elem.get("href").replace("tel:", "")

            access_elem = access_soup.find("div", class_="access-info")
            if access_elem:
                access = self.clean_text(access_elem.get_text())

        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address=address or "東京都新宿区新宿3-13-3",
            phone=phone or "03-3352-2471",
            access=access or "JR新宿駅東口より徒歩5分",
            screens=1
        )

    def get_movies(self) -> List[MovieInfo]:
        movies = []

        soup = self.get_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))

        coming_soup = self.get_page(f"{self.base_url}/coming/")
        if coming_soup:
            movies.extend(self._extract_movies_from_page(coming_soup))

        return movies

    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出
        HTML構造: div.movielist > div.box.clearfix > (h3タイトル + div.movietxt + img)
        """
        movies = []

        movielist = soup.find("div", class_="movielist")
        if not movielist:
            return movies

        movie_boxes = movielist.find_all("div", class_="box")

        seen_titles = set()
        for box in movie_boxes:
            try:
                # h3タグからタイトル取得
                title_elem = box.find("h3")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if not title or title in seen_titles:
                    continue

                seen_titles.add(title)

                # ポスター画像
                poster_url = None
                img = box.find("img")
                if img:
                    src = img.get("src", "")
                    if src:
                        poster_url = src if src.startswith("http") else f"{self.base_url}{src}"

                movies.append(MovieInfo(
                    title=title,
                    poster_url=poster_url
                ))

            except Exception as e:
                self.logger.error(f"Error extracting movie info: {e}")
                continue

        return movies

    def get_schedules(self) -> List[MovieSchedule]:
        schedules = []

        soup = self.get_page(self.base_url)
        if not soup:
            return schedules

        movielist = soup.find("div", class_="movielist")
        if not movielist:
            return schedules

        movie_boxes = movielist.find_all("div", class_="box")
        today = datetime.now().strftime("%Y-%m-%d")

        seen_titles = set()
        for box in movie_boxes:
            try:
                title_elem = box.find("h3")
                if not title_elem:
                    continue

                movie_title = title_elem.get_text(strip=True)
                if not movie_title:
                    continue

                movietxt = box.find("div", class_="movietxt")
                if not movietxt:
                    continue

                full_text = movietxt.get_text()

                # 「作品案内参照」の場合は時刻なしとして扱う
                if "作品案内参照" in full_text:
                    times = []
                else:
                    times = re.findall(r'\d{1,2}:\d{2}', full_text)

                if movie_title in seen_titles:
                    continue
                seen_titles.add(movie_title)

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
