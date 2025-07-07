from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .models import MovieInfo, ShowtimeInfo, MovieSchedule, TheaterInfo, TheaterData

class BaseScraper(ABC):
    """映画館スクレイピング基底クラス"""
    
    def __init__(self, theater_name: str, base_url: str):
        self.theater_name = theater_name
        self.base_url = base_url
        self.session = requests.Session()
        self.setup_session()
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    def setup_session(self):
        """セッション設定"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(headers)
        
        # SSL設定の改善
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session.verify = False  # SSL証明書検証を無効化
        
        # リトライ設定
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def get_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """ページ取得"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to get page {url}: {e}")
            return None
            
    def get_page_with_selenium(self, url: str, wait_time: int = 10) -> Optional[BeautifulSoup]:
        """Selenium使用ページ取得"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # SSL関連のオプションを追加
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors-list')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-urlfetcher-cert-requests')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            html = driver.page_source
            driver.quit()
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to get page with Selenium {url}: {e}")
            # SSL エラーの場合、通常のrequestsセッションでも試行
            if "SSL" in str(e) or "certificate" in str(e).lower():
                self.logger.info(f"Trying with requests session for {url}")
                return self.get_page(url)
            return None
            
    def safe_extract_text(self, element, default: str = "") -> str:
        """安全なテキスト抽出"""
        if element:
            return element.get_text().strip()
        return default
        
    def safe_extract_attr(self, element, attr: str, default: str = "") -> str:
        """安全な属性抽出"""
        if element:
            return element.get(attr, default)
        return default
        
    def clean_text(self, text: str) -> str:
        """テキストクリーニング"""
        if not text:
            return ""
        return " ".join(text.split())
        
    def delay(self, seconds: float = 1.0):
        """リクエスト間隔調整"""
        time.sleep(seconds)
        
    @abstractmethod
    def get_theater_info(self) -> TheaterInfo:
        """映画館情報取得"""
        pass
        
    @abstractmethod
    def get_movies(self) -> List[MovieInfo]:
        """映画情報取得"""
        pass
        
    @abstractmethod
    def get_schedules(self) -> List[MovieSchedule]:
        """スケジュール情報取得"""
        pass
        
    def scrape_all(self) -> TheaterData:
        """全データ取得"""
        self.logger.info(f"Starting scrape for {self.theater_name}")
        
        theater_info = self.get_theater_info()
        movies = self.get_movies()
        schedules = self.get_schedules()
        
        return TheaterData(
            theater_info=theater_info,
            movies=movies,
            schedules=schedules
        )
        
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'session'):
            self.session.close()