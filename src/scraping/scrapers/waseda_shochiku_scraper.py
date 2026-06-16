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
            base_url="https://wasedashochiku.co.jp"
        )

    def get_theater_info(self) -> TheaterInfo:
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都新宿区高田馬場1-5-16",
            phone="03-3200-8968",
            access="JR山手線・西武新宿線・東西線高田馬場駅より徒歩3分",
            screens=1
        )

    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得
        トップページのh3タグにスケジュールページリンクがあり、
        各スケジュールページのh3.sakuhin-titleに映画タイトルが記載されている。
        """
        movies = []
        seen_titles = set()

        schedule_links = self._get_schedule_links()
        for link in schedule_links:
            try:
                soup = self.get_page(link)
                if not soup:
                    continue
                for movie in self._extract_movies_from_schedule_page(soup):
                    if movie.title not in seen_titles:
                        seen_titles.add(movie.title)
                        movies.append(movie)
                self.delay(0.5)
            except Exception as e:
                self.logger.error(f"Error fetching schedule page {link}: {e}")

        return movies

    def _get_schedule_links(self) -> List[str]:
        """トップページからスケジュールページのURLを収集"""
        soup = self.get_page(self.base_url)
        if not soup:
            return []

        links = []
        seen = set()
        for h3 in soup.find_all("h3"):
            a = h3.find("a")
            if not a:
                continue
            href = a.get("href", "")
            if "/archives/schedule/" in href and href not in seen:
                seen.add(href)
                links.append(href)

        return links

    def _extract_movies_from_schedule_page(self, soup: BeautifulSoup) -> List[MovieInfo]:
        """スケジュール詳細ページから映画情報を抽出
        HTML構造:
          div.sakuhinjoho-box > h3.sakuhin-title(タイトル + span英題) + div.sakuhin-time(時刻)
        """
        movies = []

        for box in soup.find_all("div", class_="sakuhinjoho-box"):
            try:
                # h3.sakuhin-titleにタイトル（span内に英語タイトル）
                title_elem = box.find("h3", class_="sakuhin-title")
                if not title_elem:
                    continue

                en_span = title_elem.find("span")
                title_en = en_span.get_text(strip=True) if en_span else None
                if en_span:
                    en_span.decompose()

                title = title_elem.get_text(separator="", strip=True)
                if not title:
                    continue

                # ポスター画像
                poster_url = None
                img = box.find("img")
                if img:
                    src = img.get("src", "")
                    if src:
                        poster_url = src if src.startswith("http") else f"{self.base_url}{src}"

                # 監督・上映時間等の情報テキスト
                director = None
                duration = None
                info_elem = box.find("div", class_="intro-textarea")
                if info_elem:
                    info_text = info_elem.get_text()
                    director_match = re.search(r'監督[：:]\s*([^\n/]+)', info_text)
                    if director_match:
                        director = director_match.group(1).strip()
                    duration_match = re.search(r'(\d+)分', info_text)
                    if duration_match:
                        duration = int(duration_match.group(1))

                movies.append(MovieInfo(
                    title=title,
                    title_en=title_en,
                    director=director,
                    duration=duration,
                    poster_url=poster_url
                ))

            except Exception as e:
                self.logger.error(f"Error extracting movie from schedule page: {e}")
                continue

        return movies

    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得
        各スケジュールページのdiv.sakuhin-timeに時刻情報がある。
        """
        schedules = []

        schedule_links = self._get_schedule_links()
        for link in schedule_links:
            try:
                soup = self.get_page(link)
                if not soup:
                    continue

                date_range = self._extract_date_range_from_page(soup)

                for box in soup.find_all("div", class_="sakuhinjoho-box"):
                    try:
                        title_elem = box.find("h3", class_="sakuhin-title")
                        if not title_elem:
                            continue

                        en_span = title_elem.find("span")
                        if en_span:
                            en_span.decompose()
                        movie_title = title_elem.get_text(separator="", strip=True)
                        if not movie_title:
                            continue

                        # div.sakuhin-time から時刻取得
                        # 形式: 「開映時間　10:30／15:15／20:00(～終映21:35)」
                        time_elem = box.find("div", class_="sakuhin-time")
                        times = []
                        if time_elem:
                            time_text = time_elem.get_text()
                            # 開映時刻のみ抽出（「／」区切り）
                            times = re.findall(r'(\d{1,2}:\d{2})', time_text)
                            # 終映時刻を除外（直前に「終映」や「終」が来るもの）
                            clean_text = time_text
                            end_times = re.findall(r'(?:終映|終)\s*(\d{1,2}:\d{2})', clean_text)
                            times = [t for t in times if t not in end_times]

                        showtimes = [ShowtimeInfo(
                            date=date_range["start"] if date_range else datetime.now().strftime("%Y-%m-%d"),
                            times=times,
                            screen="スクリーン1"
                        )]

                        schedules.append(MovieSchedule(
                            theater_name=self.theater_name,
                            movie_title=movie_title,
                            showtimes=showtimes
                        ))

                    except Exception as e:
                        self.logger.error(f"Error extracting schedule from box: {e}")
                        continue

                self.delay(0.5)

            except Exception as e:
                self.logger.error(f"Error fetching schedule page {link}: {e}")

        return schedules

    def _extract_date_range_from_page(self, soup: BeautifulSoup) -> Optional[dict]:
        """ページから上映期間を抽出
        トップページのh3に「6/13.sat - 6/16.tue」形式で日程が記載されている。
        """
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text()
            matches = re.findall(r'(\d{1,2})[/\.](\d{1,2})', text)
            if matches:
                year = datetime.now().year
                start_month, start_day = int(matches[0][0]), int(matches[0][1])
                start_date = f"{year}-{start_month:02d}-{start_day:02d}"
                if len(matches) >= 2:
                    end_month, end_day = int(matches[1][0]), int(matches[1][1])
                    end_date = f"{year}-{end_month:02d}-{end_day:02d}"
                else:
                    end_date = start_date
                return {"start": start_date, "end": end_date}

        return None
