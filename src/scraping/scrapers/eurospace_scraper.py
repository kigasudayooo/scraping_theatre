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
    """ユーロスペース スクレイパー

    注意: https://www.eurospace.co.jp はSSLエラーのため、
    http://www.eurospace.co.jp を使用する。
    """

    def __init__(self):
        super().__init__(
            theater_name="ユーロスペース",
            base_url="http://www.eurospace.co.jp"
        )

    def get_theater_info(self) -> TheaterInfo:
        return TheaterInfo(
            name=self.theater_name,
            url=self.base_url,
            address="東京都渋谷区円山町1-5 キノハウス地下2階",
            phone="03-3461-0211",
            access="JR渋谷駅より徒歩5分",
            screens=2
        )

    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得
        トップページ div.item > p > a のリンクから詳細ページへアクセス。
        詳細ページ(section#workDetail)のh2にタイトル、p.work-captionに監督・出演情報。
        """
        movies = []
        soup = self.get_page(self.base_url)
        if not soup:
            return movies

        # div.itemから映画詳細ページのリンクを収集
        work_links = []
        seen_links = set()
        for item in soup.find_all("div", class_="item"):
            link = item.find("a")
            if link:
                href = link.get("href", "")
                if href and "/works/detail.php" in href and href not in seen_links:
                    seen_links.add(href)
                    full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                    work_links.append(full_url)

        for url in work_links:
            try:
                movie = self._scrape_movie_detail(url)
                if movie:
                    movies.append(movie)
                self.delay(0.5)
            except Exception as e:
                self.logger.error(f"Error scraping movie detail {url}: {e}")

        return movies

    def _scrape_movie_detail(self, url: str) -> Optional[MovieInfo]:
        """作品詳細ページから映画情報を抽出
        HTML構造: section#workDetail > h2(タイトル) + p.work-caption(出演・監督等)
        """
        soup = self.get_page(url)
        if not soup:
            return None

        detail = soup.find("section", id="workDetail")
        if not detail:
            return None

        # タイトル
        title_elem = detail.find("h2")
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)
        if not title:
            return None

        # ポスター画像
        poster_url = None
        img_div = detail.find("div", class_="work-image")
        if img_div:
            img = img_div.find("img")
            if img:
                src = img.get("src", "")
                if src:
                    poster_url = src if src.startswith("http") else f"{self.base_url}{src}"

        # 監督・出演情報 (p.work-caption)
        director = None
        cast = []
        duration = None
        caption = detail.find("p", class_="work-caption")
        if caption:
            cap_text = caption.get_text()
            # 監督（撮影・音楽・出演・脚本・製作などで終わる前の名前のみ）
            director_match = re.search(r'監督[・脚本]*[：:]?\s*([^撮影出演音楽編集製作配給脚本\n/　・]+?)(?:撮影|出演|音楽|編集|製作|配給|脚本|\n|　|$)', cap_text)
            if director_match:
                director = director_match.group(1).strip()
            # 出演
            cast_match = re.search(r'出演[：:]\s*([^\n]+)', cap_text)
            if cast_match:
                cast_text = cast_match.group(1)
                cast = [c.strip() for c in re.split(r'[/、,，・ ]', cast_text) if c.strip()]
            # 上映時間
            duration_match = re.search(r'(\d+)分', cap_text)
            if duration_match:
                duration = int(duration_match.group(1))

        return MovieInfo(
            title=title,
            director=director,
            cast=cast,
            duration=duration,
            poster_url=poster_url
        )

    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得
        トップページのdiv.scrolltable > table に本日のスケジュールが入っている。
        tr.time > td で時刻、次のtrのtd > aで映画タイトルを取得。
        """
        schedules = []
        soup = self.get_page(self.base_url)
        if not soup:
            return schedules

        today = datetime.now().strftime("%Y-%m-%d")

        # scrolltable内のtableを解析
        for scrolltable in soup.find_all("div", class_="scrolltable"):
            table = scrolltable.find("table")
            if not table:
                continue

            rows = table.find_all("tr")
            if not rows:
                continue

            # 最初のtr.timeに時刻が並んでいる
            time_row = None
            movie_row = None
            for row in rows:
                if "time" in row.get("class", []):
                    time_row = row
                else:
                    movie_row = row

            if not time_row or not movie_row:
                continue

            times = [td.get_text(strip=True) for td in time_row.find_all("td")]
            movie_tds = movie_row.find_all("td")

            # 各tdに映画タイトル+時刻が対応
            for i, td in enumerate(movie_tds):
                a = td.find("a")
                if not a:
                    continue
                movie_title = a.get_text(strip=True)
                if not movie_title:
                    continue

                # 対応する時刻
                showtime = times[i] if i < len(times) else ""

                # 既存のスケジュールに追加または新規作成
                existing = next(
                    (s for s in schedules if s.movie_title == movie_title), None
                )
                if existing:
                    if showtime and showtime not in existing.showtimes[0].times:
                        existing.showtimes[0].times.append(showtime)
                else:
                    schedules.append(MovieSchedule(
                        theater_name=self.theater_name,
                        movie_title=movie_title,
                        showtimes=[ShowtimeInfo(
                            date=today,
                            times=[showtime] if showtime else [],
                            screen="ユーロスペース"
                        )]
                    ))

        return schedules
