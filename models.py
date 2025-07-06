from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

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