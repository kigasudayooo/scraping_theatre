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
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都新宿区新宿3-27-10",
            phone="03-3354-5670",
            access="JR新宿駅東口より徒歩5分",
            screens=2
        )

    def get_movies(self) -> List[MovieInfo]:
        movies = []
        soup = self.get_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
        return movies

    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出
        HTML構造: article.movies.flex-item > a(リンク) > div.description > div.label(上映期限) + タイトルテキスト
        """
        movies = []
        seen_titles = set()

        for article in soup.find_all("article", class_="movies"):
            try:
                text = article.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                # ラベル（上映期限テキスト）を除去してタイトルを取得
                # 「X月X旬まで（予定）」「X月XH（曜）まで」のような行を除く
                title = None
                for line in lines:
                    if re.search(r'まで|上映期限|予定', line):
                        continue
                    if len(line) > 1:
                        title = line
                        break

                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # 映画詳細ページURL
                link = article.find("a")
                movie_url = None
                if link:
                    href = link.get("href", "")
                    if href:
                        movie_url = href if href.startswith("http") else f"{self.base_url}{href}"

                # ポスター画像（bgimgスタイルから取得）
                poster_url = None
                bgimg = article.find("div", class_="bgimg")
                if bgimg:
                    style = bgimg.get("style", "")
                    img_match = re.search(r"url\(['\"]?([^'\"]+)['\"]?\)", str(style))
                    if img_match:
                        poster_url = img_match.group(1)

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
        新宿武蔵野館の詳細な上映時刻は外部システム(cineticket.jp)で管理されているため、
        このサイトから取得できる情報（映画タイトル・上映期限）のみを返す。
        """
        schedules = []
        soup = self.get_page(self.base_url)
        if not soup:
            return schedules

        today = datetime.now().strftime("%Y-%m-%d")

        for article in soup.find_all("article", class_="movies"):
            try:
                text = article.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                title = None
                for line in lines:
                    if re.search(r'まで|上映期限|予定', line):
                        continue
                    if len(line) > 1:
                        title = line
                        break

                if not title:
                    continue

                # 上映時刻はページから取得不可のため空リストで記録
                schedules.append(MovieSchedule(
                    theater_name=self.theater_name,
                    movie_title=title,
                    showtimes=[ShowtimeInfo(
                        date=today,
                        times=[],
                        screen="スクリーン"
                    )]
                ))

            except Exception as e:
                self.logger.error(f"Error extracting schedule info: {e}")
                continue

        return schedules
