from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..base_scraper import BaseScraper
from ..models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo

class PolePoleHigashinakanoScraper(BaseScraper):
    """ポレポレ東中野 スクレイパー

    Nuxt.js SPAのためSeleniumを使用する。
    スケジュールはdiv.movie-schedule-info.flex-row に含まれる。
    デフォルトで本日選択されている日付のスケジュールを取得する。
    """

    def __init__(self):
        super().__init__(
            theater_name="ポレポレ東中野",
            base_url="https://pole2.co.jp"
        )

    def get_theater_info(self) -> TheaterInfo:
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都中野区東中野4-4-1 ポレポレ坐ビル地下",
            phone="03-3371-0088",
            access="JR中央線・総武線・都営大江戸線東中野駅より徒歩1分",
            screens=1
        )

    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得（Seleniumでレンダリングしてから解析）"""
        movies = []
        soup = self._get_rendered_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_schedule(soup))
        return movies

    def _get_rendered_page(self, url: str, wait_seconds: int = 5) -> Optional[BeautifulSoup]:
        """Seleniumでページを取得してBeautifulSoupを返す"""
        import time
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(wait_seconds)
            html = driver.page_source
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            self.logger.error(f"Selenium error for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def _extract_movies_from_schedule(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """div.movie-schedule-info から映画情報を抽出
        HTML構造:
          div.movie-schedule-info.flex-row
            div.movie-name > span (タイトル)
            img.movie-image (ポスター)
        """
        movies = []
        seen_titles = set()

        for row in soup.find_all("div", class_="movie-schedule-info flex-row"):
            try:
                # タイトル
                name_div = row.find("div", class_="movie-name")
                if not name_div:
                    continue
                span = name_div.find("span")
                if not span:
                    continue
                title = span.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # ポスター画像
                poster_url = None
                img = row.find("img", class_="movie-image")
                if img:
                    src = img.get("src", "")
                    if src:
                        poster_url = src

                movies.append(MovieInfo(
                    title=title,
                    poster_url=poster_url
                ))

            except Exception as e:
                self.logger.error(f"Error extracting movie info: {e}")
                continue

        return movies

    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得
        div.movie-schedule-head の p.date で本日日付を取得し、
        div.movie-schedule-body の各 div.movie-schedule-info から
        タイトル・開始時刻を取得する。
        """
        schedules = []
        soup = self._get_rendered_page(self.base_url)
        if not soup:
            return schedules

        # 選択中の日付を取得（swiper-slide-activeのp.date）
        active_date = self._get_active_date(soup)
        today = active_date or datetime.now().strftime("%Y-%m-%d")

        for row in soup.find_all("div", class_="movie-schedule-info flex-row"):
            try:
                # タイトル
                name_div = row.find("div", class_="movie-name")
                if not name_div:
                    continue
                span = name_div.find("span")
                if not span:
                    continue
                title = span.get_text(strip=True)
                if not title:
                    continue

                # 開始時刻（div.time > h2）
                time_div = row.find("div", class_="time")
                start_time = ""
                if time_div:
                    h2 = time_div.find("h2")
                    if h2:
                        start_time = h2.get_text(strip=True).replace("~", "").strip()

                # スクリーン情報
                room_div = row.find("div", class_="room")
                screen = "ポレポレ東中野（地下）"
                if room_div:
                    name_p = room_div.find("p", class_="name")
                    if name_p:
                        screen = name_p.get_text(strip=True)

                schedules.append(MovieSchedule(
                    theater_name=self.theater_name,
                    movie_title=title,
                    showtimes=[ShowtimeInfo(
                        date=today,
                        times=[start_time] if start_time else [],
                        screen=screen
                    )]
                ))

            except Exception as e:
                self.logger.error(f"Error extracting schedule info: {e}")
                continue

        return schedules

    def _get_active_date(self, soup: BeautifulSoup) -> Optional[str]:
        """スケジュールカレンダーのアクティブな日付を取得"""
        active_item = soup.find("div", class_="calender-head-item active")
        if not active_item:
            return None

        date_p = active_item.find("p", class_="date")
        if not date_p:
            return None

        date_text = date_p.get_text(strip=True)
        match = re.match(r'(\d{2})/(\d{2})', date_text)
        if match:
            year = datetime.now().year
            month, day = int(match.group(1)), int(match.group(2))
            return f"{year}-{month:02d}-{day:02d}"

        return None
