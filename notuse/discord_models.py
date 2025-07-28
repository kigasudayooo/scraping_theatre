"""
Discord Bot用データモデル
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from ..scraping.models import MovieInfo, TheaterInfo, ShowtimeInfo

@dataclass
class WeeklyMovieSchedule:
    """週次映画スケジュール"""
    week_start: date
    week_end: date
    movies: List['WeeklyMovieInfo']
    total_movies: int
    total_theaters: int
    
@dataclass
class WeeklyMovieInfo:
    """週次映画情報"""
    movie: MovieInfo
    theaters: List[str]  # 上映映画館名のリスト
    schedule_period: str  # "7/8(月)〜7/14(日)"
    showtimes_summary: str  # "平日: 14:30, 19:00 / 土日: 10:00, 14:30, 19:00"
    
@dataclass
class MovieSearchResult:
    """映画検索結果"""
    movie: MovieInfo
    theaters: List[str]
    current_showtimes: List[ShowtimeInfo]
    external_info: Optional['ExternalMovieInfo'] = None
    
@dataclass
class ExternalMovieInfo:
    """外部サイトからの映画情報"""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    awards: List[str] = None
    additional_synopsis: Optional[str] = None
    official_site: Optional[str] = None
    trailer_url: Optional[str] = None
    
    def __post_init__(self):
        if self.awards is None:
            self.awards = []
            
@dataclass
class BotQuery:
    """Bot質問解析結果"""
    query_type: str  # "movie_info", "theater_schedule", "search", "director_works"
    target: str  # 映画名、監督名、映画館名など
    filters: Dict[str, Any]  # 追加フィルター（ジャンル、期間など）
    
@dataclass
class BotResponse:
    """Bot応答データ"""
    title: str
    content: str
    embed_data: Optional[Dict[str, Any]] = None
    has_external_search: bool = False
    
def create_weekly_schedule_from_data(theater_data_list: List[Any], 
                                   current_week_start: date,
                                   next_week_start: date) -> WeeklyMovieSchedule:
    """スクレイピングデータから週次スケジュールを作成"""
    movies_dict = {}  # movie_title -> WeeklyMovieInfo
    
    for theater_data in theater_data_list:
        theater_name = theater_data.theater_info.name
        
        for schedule in theater_data.schedules:
            movie_title = schedule.movie_title
            
            # 今週・来週の上映があるかチェック
            current_week_showtimes = []
            for showtime in schedule.showtimes:
                showtime_date = datetime.strptime(showtime.date, "%Y-%m-%d").date()
                if current_week_start <= showtime_date < next_week_start + datetime.timedelta(days=7):
                    current_week_showtimes.append(showtime)
                    
            if not current_week_showtimes:
                continue
                
            # 対応する映画情報を取得
            movie_info = None
            for movie in theater_data.movies:
                if movie.title == movie_title:
                    movie_info = movie
                    break
                    
            if not movie_info:
                # 映画情報がない場合は基本情報のみ作成
                movie_info = MovieInfo(title=movie_title)
                
            # WeeklyMovieInfoに追加
            if movie_title not in movies_dict:
                movies_dict[movie_title] = WeeklyMovieInfo(
                    movie=movie_info,
                    theaters=[theater_name],
                    schedule_period=_format_schedule_period(current_week_showtimes),
                    showtimes_summary=_format_showtimes_summary(current_week_showtimes)
                )
            else:
                # 既存の映画に映画館を追加
                if theater_name not in movies_dict[movie_title].theaters:
                    movies_dict[movie_title].theaters.append(theater_name)
                    
    movies_list = list(movies_dict.values())
    theaters_set = set()
    for movie_info in movies_list:
        theaters_set.update(movie_info.theaters)
        
    return WeeklyMovieSchedule(
        week_start=current_week_start,
        week_end=next_week_start + datetime.timedelta(days=6),
        movies=movies_list,
        total_movies=len(movies_list),
        total_theaters=len(theaters_set)
    )

def _format_schedule_period(showtimes: List[ShowtimeInfo]) -> str:
    """上映期間をフォーマット"""
    if not showtimes:
        return ""
        
    dates = [datetime.strptime(st.date, "%Y-%m-%d").date() for st in showtimes]
    min_date = min(dates)
    max_date = max(dates)
    
    if min_date == max_date:
        return f"{min_date.month}/{min_date.day}({_get_weekday_jp(min_date)})"
    else:
        return f"{min_date.month}/{min_date.day}({_get_weekday_jp(min_date)})〜{max_date.month}/{max_date.day}({_get_weekday_jp(max_date)})"

def _format_showtimes_summary(showtimes: List[ShowtimeInfo]) -> str:
    """上映時間サマリーをフォーマット"""
    if not showtimes:
        return ""
        
    # 平日と土日で分ける
    weekday_times = set()
    weekend_times = set()
    
    for showtime in showtimes:
        showtime_date = datetime.strptime(showtime.date, "%Y-%m-%d").date()
        times = showtime.times
        
        if showtime_date.weekday() >= 5:  # 土日
            weekend_times.update(times)
        else:  # 平日
            weekday_times.update(times)
            
    summary_parts = []
    if weekday_times:
        summary_parts.append(f"平日: {', '.join(sorted(weekday_times))}")
    if weekend_times:
        summary_parts.append(f"土日: {', '.join(sorted(weekend_times))}")
        
    return " / ".join(summary_parts)

def _get_weekday_jp(date_obj: date) -> str:
    """日本語曜日を取得"""
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    return weekdays[date_obj.weekday()]