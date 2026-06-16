from typing import List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup, NavigableString, Comment, Tag
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
            base_url="http://shimotakaidocinema.com"
        )

    def get_theater_info(self) -> TheaterInfo:
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都世田谷区松原3-27-26",
            phone="03-3321-0684",
            access="京王線下高井戸駅より徒歩3分",
            screens=1
        )

    def get_movies(self) -> List[MovieInfo]:
        movies = []
        soup = self.get_page(self.base_url)
        if soup:
            movies.extend(self._extract_movies_from_page(soup))
        return movies

    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """ページから映画情報抽出
        HTML構造:
          ul.slider > li.float > a > img + p.top_jouei
            p.top_jouei > span.eiga-title (タイトル) + span.day (日程・時刻)
        """
        movies = []
        seen_titles = set()

        for li in soup.find_all("li", class_="float"):
            try:
                title_elem = li.find("span", class_="eiga-title")
                if not title_elem:
                    continue

                # ブロック要素(br, font)を除いてタイトルを取得
                title = self._extract_title_text(title_elem)
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # ポスター画像
                poster_url = None
                img = li.find("img")
                if img:
                    src = img.get("src", "")
                    if src:
                        poster_url = src if src.startswith("http") else f"{self.base_url}/{src}"

                movies.append(MovieInfo(
                    title=title,
                    poster_url=poster_url
                ))

            except Exception as e:
                self.logger.error(f"Error extracting movie info: {e}")
                continue

        return movies

    def _extract_title_text(self, title_elem) -> str:
        """span.eiga-titleからタイトルテキストを抽出
        メインタイトル + サブタイトル（fontタグ内）を結合する。
        """
        parts = []
        for content in title_elem.contents:
            if isinstance(content, Comment):
                continue
            elif isinstance(content, NavigableString):
                text = str(content).strip()
                if text:
                    parts.append(text)
            elif isinstance(content, Tag):
                if content.name == 'br':
                    continue
                elif content.name == 'font':
                    sub = content.get_text(strip=True)
                    # 注釈系テキストは除外（HELLO!MOVIEなど）
                    if sub and not sub.startswith('＊') and not sub.startswith('*') and '対応' not in sub:
                        parts.append(sub)

        return " ".join(parts).strip()

    def get_schedules(self) -> List[MovieSchedule]:
        schedules = []
        soup = self.get_page(self.base_url)
        if soup:
            schedules.extend(self._extract_schedules_from_page(soup))
        return schedules

    def _extract_schedules_from_page(self, soup: BeautifulSoup) -> List[MovieSchedule]:
        """ページからスケジュール情報抽出
        HTML構造:
          li.float > a > p.top_jouei
            span.eiga-title: タイトル
            span.day: 「MM/DD(曜)～MM/DD(曜)\nHH：MM～(終HH：MM)」
        """
        schedules = []

        for li in soup.find_all("li", class_="float"):
            try:
                title_elem = li.find("span", class_="eiga-title")
                if not title_elem:
                    continue
                title = self._extract_title_text(title_elem)
                if not title:
                    continue

                day_elem = li.find("span", class_="day")
                if not day_elem:
                    continue

                day_text = day_elem.get_text(separator="\n", strip=True)
                # 全角コロンを半角に正規化
                day_text = day_text.replace('：', ':')

                # 日付範囲を抽出: MM/DD(曜)～MM/DD(曜)
                date_range_match = re.search(
                    r'(\d{1,2})/(\d{1,2})[^~〜]*[~〜].*?(\d{1,2})/(\d{1,2})',
                    day_text
                )

                # 開始時刻を抽出（終了時刻を除く）
                # 「9:30～(終11:00)」から9:30を取得
                start_time_match = re.search(r'(\d{1,2}:\d{2})～', day_text)
                start_time = start_time_match.group(1) if start_time_match else ""

                year = datetime.now().year
                if date_range_match:
                    start_month = int(date_range_match.group(1))
                    start_day = int(date_range_match.group(2))
                    end_month = int(date_range_match.group(3))
                    end_day = int(date_range_match.group(4))
                    start_date = f"{year}-{start_month:02d}-{start_day:02d}"
                    end_date = f"{year}-{end_month:02d}-{end_day:02d}"
                else:
                    start_date = datetime.now().strftime("%Y-%m-%d")
                    end_date = start_date

                schedules.append(MovieSchedule(
                    theater_name=self.theater_name,
                    movie_title=title,
                    showtimes=[ShowtimeInfo(
                        date=start_date,
                        times=[start_time] if start_time else [],
                        screen="スクリーン1"
                    )]
                ))

            except Exception as e:
                self.logger.error(f"Error extracting schedule info: {e}")
                continue

        return schedules
