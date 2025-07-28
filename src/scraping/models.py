from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class MovieInfo:
    """映画基本情報"""
    title: str
    title_en: Optional[str] = None
    director: Optional[str] = None
    cast: List[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    rating: Optional[str] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None
    
    def __post_init__(self):
        if self.cast is None:
            self.cast = []

@dataclass
class ShowtimeInfo:
    """上映時間情報"""
    date: str
    times: List[str]
    screen: Optional[str] = None
    ticket_url: Optional[str] = None
    
    def __post_init__(self):
        if self.times is None:
            self.times = []

@dataclass
class MovieSchedule:
    """映画スケジュール"""
    theater_name: str
    movie_title: str
    showtimes: List[ShowtimeInfo]
    
    def __post_init__(self):
        if self.showtimes is None:
            self.showtimes = []

@dataclass
class TheaterInfo:
    """映画館情報"""
    name: str
    url: str
    address: Optional[str] = None
    phone: Optional[str] = None
    access: Optional[str] = None
    screens: Optional[int] = None

@dataclass
class TheaterData:
    """映画館の全データ"""
    theater_info: TheaterInfo
    movies: List[MovieInfo]
    schedules: List[MovieSchedule]
    
    def __post_init__(self):
        if self.movies is None:
            self.movies = []
        if self.schedules is None:
            self.schedules = []
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON出力用の辞書形式に変換"""
        return asdict(self)

@dataclass
class MovieWithSchedules:
    """スケジュール統合済み映画情報（JSON出力用）"""
    title: str
    title_en: Optional[str] = None
    director: Optional[str] = None
    cast: List[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None
    rating: Optional[str] = None
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None
    schedules: List[ShowtimeInfo] = None
    
    def __post_init__(self):
        if self.cast is None:
            self.cast = []
        if self.schedules is None:
            self.schedules = []

@dataclass
class TheaterMoviesData:
    """JSON出力用の映画館統合データ"""
    name: str
    url: str
    address: Optional[str] = None
    phone: Optional[str] = None
    access: Optional[str] = None
    screens: Optional[int] = None
    movies: List[MovieWithSchedules] = None
    
    def __post_init__(self):
        if self.movies is None:
            self.movies = []
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON出力用の辞書形式に変換"""
        return asdict(self)

@dataclass
class CinemaDatabase:
    """全映画館統合データベース（JSON出力最上位）"""
    last_updated: str
    theaters: Dict[str, TheaterMoviesData]
    summary: Dict[str, Any]
    
    def __post_init__(self):
        if self.theaters is None:
            self.theaters = {}
        if self.summary is None:
            self.summary = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON出力用の辞書形式に変換"""
        data = asdict(self)
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def save_to_file(self, filepath: str, indent: int = 2, use_file_lock: bool = True) -> None:
        """
        JSONファイルに保存（ファイルロック対応）
        
        Args:
            filepath: 保存先パス
            indent: JSONインデント数
            use_file_lock: ファイルロックを使用するかどうか
        """
        if use_file_lock:
            # ファイルロックを使用した安全な書き込み
            import tempfile
            import fcntl
            from pathlib import Path
            
            # 一時ファイルに書き込み後、アトミックに移動
            output_path = Path(filepath)
            temp_file = None
            
            try:
                # 一時ファイル作成
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    encoding='utf-8', 
                    dir=output_path.parent,
                    delete=False,
                    suffix='.tmp',
                    prefix=f'{output_path.stem}_'
                ) as temp_file:
                    
                    # ファイルロック取得
                    fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)
                    
                    # JSON書き込み
                    json.dump(self.to_dict(), temp_file, ensure_ascii=False, indent=indent)
                    temp_file.flush()
                
                # アトミックに移動
                import os
                os.rename(temp_file.name, filepath)
                
            except Exception as e:
                # エラー時は一時ファイルを削除
                if temp_file and Path(temp_file.name).exists():
                    Path(temp_file.name).unlink()
                raise e
        else:
            # 従来の書き込み方法
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_theater_data_list(cls, theater_data_list: List[TheaterData]) -> 'CinemaDatabase':
        """TheaterDataのリストからCinemaDatabaseを構築"""
        theaters = {}
        total_movies = 0
        active_theaters = 0
        
        for theater_data in theater_data_list:
            if not theater_data.movies:
                continue
                
            # 映画とスケジュールを統合
            movies_with_schedules = []
            for movie in theater_data.movies:
                # 該当する映画のスケジュールを検索
                movie_schedules = []
                for schedule in theater_data.schedules:
                    if schedule.movie_title == movie.title:
                        movie_schedules.extend(schedule.showtimes)
                
                movie_with_schedule = MovieWithSchedules(
                    title=movie.title,
                    title_en=movie.title_en,
                    director=movie.director,
                    cast=movie.cast,
                    genre=movie.genre,
                    duration=movie.duration,
                    rating=movie.rating,
                    synopsis=movie.synopsis,
                    poster_url=movie.poster_url,
                    schedules=movie_schedules
                )
                movies_with_schedules.append(movie_with_schedule)
            
            # 映画館IDを生成（名前から）
            theater_id = theater_data.theater_info.name.lower().replace(' ', '_').replace('（', '').replace('）', '')
            
            theater_movies_data = TheaterMoviesData(
                name=theater_data.theater_info.name,
                url=theater_data.theater_info.url,
                address=theater_data.theater_info.address,
                phone=theater_data.theater_info.phone,
                access=theater_data.theater_info.access,
                screens=theater_data.theater_info.screens,
                movies=movies_with_schedules
            )
            
            theaters[theater_id] = theater_movies_data
            total_movies += len(movies_with_schedules)
            active_theaters += 1
        
        summary = {
            "total_theaters": len(theater_data_list),
            "active_theaters": active_theaters,
            "total_movies": total_movies,
            "generated_at": datetime.now().isoformat()
        }
        
        return cls(
            last_updated=datetime.now().isoformat(),
            theaters=theaters,
            summary=summary
        )