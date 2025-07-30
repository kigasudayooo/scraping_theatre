#!/usr/bin/env python3
"""
実際の映画館スクレイピング実行スクリプト
"""
import json
import logging
import sys
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# プロジェクトパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# スクレイパークラスのインポート
from src.scraping.scrapers.ks_cinema_scraper import KsCinemaScraper
from src.scraping.scrapers.shimotakaido_scraper import ShimotakaidoCinemaScraper
from src.scraping.scrapers.waseda_shochiku_scraper import WasedaShochikuScraper
from src.scraping.scrapers.shinjuku_musashino_scraper import ShinjukuMusashinoScraper
from src.scraping.models import TheaterData

class TheaterScrapingOrchestrator:
    """映画館スクレイピング統合管理クラス"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # ログ設定
        self.setup_logging()
        
        # スクレイパーの初期化
        self.scrapers = {
            "ks_cinema": KsCinemaScraper(),
            "shimotakaido": ShimotakaidoCinemaScraper(),
            "waseda_shochiku": WasedaShochikuScraper(),
            "shinjuku_musashino": ShinjukuMusashinoScraper()
        }
        
    def setup_logging(self):
        """ログ設定"""
        log_file = self.output_dir / "scraping.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def scrape_theater(self, theater_key: str) -> Dict[str, Any]:
        """個別映画館のスクレイピング実行"""
        if theater_key not in self.scrapers:
            self.logger.error(f"Unknown theater: {theater_key}")
            return {}
            
        scraper = self.scrapers[theater_key]
        self.logger.info(f"🎬 スクレイピング開始: {scraper.theater_name}")
        
        try:
            # 全データ取得
            theater_data = scraper.scrape_all()
            
            # データをJSON形式に変換
            result = self._theater_data_to_dict(theater_data)
            
            self.logger.info(f"✅ スクレイピング完了: {scraper.theater_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ スクレイピングエラー {scraper.theater_name}: {e}")
            import traceback
            traceback.print_exc()
            return {}
            
    def scrape_all_theaters(self) -> Dict[str, Dict[str, Any]]:
        """全映画館のスクレイピング実行"""
        all_results = {}
        theaters_data = {}
        
        self.logger.info("🚀 全映画館スクレイピング開始")
        
        for theater_key in self.scrapers.keys():
            self.logger.info(f"📍 処理中: {theater_key}")
            result = self.scrape_theater(theater_key)
            all_results[theater_key] = result
            
            # ハイブリッドシステム用のデータ形式に変換
            if result and result.get("theater_info"):
                theater_name = result["theater_info"]["name"]
                theaters_data[theater_name] = {
                    "address": result["theater_info"].get("address", ""),
                    "url": result["theater_info"].get("url", ""),
                    "movies": []
                }
                
                # 映画とスケジュール情報を統合
                for movie in result.get("movies", []):
                    movie_data = {
                        "title": movie.get("title", ""),
                        "director": movie.get("director"),
                        "cast": movie.get("cast", []),
                        "schedules": []
                    }
                    
                    # 対応するスケジュールを検索
                    for schedule in result.get("schedules", []):
                        if schedule.get("movie_title") == movie.get("title"):
                            for showtime in schedule.get("showtimes", []):
                                movie_data["schedules"].append({
                                    "date": showtime.get("date"),
                                    "times": showtime.get("times", []),
                                    "screen": showtime.get("screen")
                                })
                    
                    theaters_data[theater_name]["movies"].append(movie_data)
            
            # 各映画館の処理後に少し待機
            import time
            time.sleep(2)
            
        # ハイブリッドシステム用の統合データを保存
        hybrid_data = {
            "theaters": theaters_data,
            "generated_at": datetime.now().isoformat(),
            "total_theaters": len(theaters_data),
            "total_movies": sum(len(theater["movies"]) for theater in theaters_data.values())
        }
        
        self._save_hybrid_data(hybrid_data)
        
        # 従来の形式も保存
        self._save_combined_results(all_results)
        
        self.logger.info(f"🎯 全映画館スクレイピング完了: {len(theaters_data)}館, {hybrid_data['total_movies']}作品")
        return all_results
        
    def _theater_data_to_dict(self, theater_data: TheaterData) -> Dict[str, Any]:
        """TheaterDataオブジェクトを辞書に変換"""
        return {
            "theater_info": {
                "name": theater_data.theater_info.name,
                "url": theater_data.theater_info.url,
                "address": theater_data.theater_info.address,
                "phone": theater_data.theater_info.phone,
                "access": theater_data.theater_info.access,
                "screens": theater_data.theater_info.screens
            },
            "movies": [
                {
                    "title": movie.title,
                    "title_en": movie.title_en,
                    "director": movie.director,
                    "cast": movie.cast,
                    "genre": movie.genre,
                    "duration": movie.duration,
                    "rating": movie.rating,
                    "synopsis": movie.synopsis,
                    "poster_url": movie.poster_url
                }
                for movie in theater_data.movies
            ],
            "schedules": [
                {
                    "theater_name": schedule.theater_name,
                    "movie_title": schedule.movie_title,
                    "showtimes": [
                        {
                            "date": showtime.date,
                            "times": showtime.times,
                            "screen": showtime.screen,
                            "ticket_url": showtime.ticket_url
                        }
                        for showtime in schedule.showtimes
                    ]
                }
                for schedule in theater_data.schedules
            ],
            "scraped_at": datetime.now().isoformat()
        }
        
    def _save_hybrid_data(self, data: Dict[str, Any]):
        """ハイブリッドシステム用データの保存"""
        filename = "movies_data.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"💾 ハイブリッドデータ保存: {filepath}")
        
    def _save_combined_results(self, all_results: Dict[str, Dict[str, Any]]):
        """統合結果の保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_theaters_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"💾 統合データ保存: {filepath}")

def main():
    """メイン実行"""
    print("🎬 東京独立系映画館スクレイピングシステム")
    print("対象映画館: ケイズシネマ、下高井戸シネマ、早稲田松竹、新宿武蔵野館")
    
    orchestrator = TheaterScrapingOrchestrator()
    
    try:
        # 全映画館スクレイピング実行
        results = orchestrator.scrape_all_theaters()
        
        # 結果統計表示
        total_theaters = len(results)
        successful_scrapes = len([r for r in results.values() if r])
        
        print(f"\n📊 スクレイピング結果:")
        print(f"   対象映画館数: {total_theaters}")
        print(f"   成功数: {successful_scrapes}")
        print(f"   成功率: {(successful_scrapes/total_theaters*100):.1f}%")
        
        if successful_scrapes > 0:
            print(f"✅ スクレイピング完了 - data/movies_data.json に保存")
        else:
            print(f"❌ 全映画館でスクレイピング失敗")
            
    except Exception as e:
        print(f"❌ システムエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()