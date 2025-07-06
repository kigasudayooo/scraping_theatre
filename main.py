#!/usr/bin/env python3
"""
映画館スクレイピングシステム - メイン実行ファイル
"""
import json
import logging
import sys
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# スクレイパークラスのインポート
from scrapers.ks_cinema_scraper import KsCinemaScraper
from scrapers.pole_pole_scraper import PolePoleHigashinakanoScraper
from scrapers.eurospace_scraper import EurospaceScraper
from scrapers.shimotakaido_scraper import ShimotakaidoCinemaScraper
from scrapers.waseda_shochiku_scraper import WasedaShochikuScraper
from scrapers.shinjuku_musashino_scraper import ShinjukuMusashinoScraper
from models import TheaterData

class TheaterScrapingOrchestrator:
    """映画館スクレイピング統合管理クラス"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # ログ設定
        self.setup_logging()
        
        # スクレイパーの初期化
        self.scrapers = {
            "ks_cinema": KsCinemaScraper(),
            "pole_pole": PolePoleHigashinakanoScraper(),
            "eurospace": EurospaceScraper(),
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
        self.logger.info(f"Starting scrape for {scraper.theater_name}")
        
        try:
            # 全データ取得
            theater_data = scraper.scrape_all()
            
            # データをJSON形式に変換
            result = self._theater_data_to_dict(theater_data)
            
            # ファイルに保存
            self._save_theater_data(theater_key, result)
            
            self.logger.info(f"Successfully scraped {scraper.theater_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error scraping {scraper.theater_name}: {e}")
            return {}
            
    def scrape_all_theaters(self) -> Dict[str, Dict[str, Any]]:
        """全映画館のスクレイピング実行"""
        all_results = {}
        
        self.logger.info("Starting scraping for all theaters")
        
        for theater_key in self.scrapers.keys():
            self.logger.info(f"Processing {theater_key}...")
            result = self.scrape_theater(theater_key)
            all_results[theater_key] = result
            
            # 各映画館の処理後に少し待機
            import time
            time.sleep(2)
            
        # 統合結果を保存
        self._save_combined_results(all_results)
        
        self.logger.info("Completed scraping for all theaters")
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
        
    def _save_theater_data(self, theater_key: str, data: Dict[str, Any]):
        """個別映画館データの保存"""
        filename = f"{theater_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"Saved {theater_key} data to {filepath}")
        
    def _save_combined_results(self, all_results: Dict[str, Dict[str, Any]]):
        """統合結果の保存"""
        filename = f"all_theaters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"Saved combined results to {filepath}")
        
    def generate_summary_report(self, results: Dict[str, Dict[str, Any]]):
        """サマリーレポート生成"""
        report = {
            "scraping_summary": {
                "total_theaters": len(results),
                "scraped_at": datetime.now().isoformat(),
                "theaters": {}
            }
        }
        
        for theater_key, data in results.items():
            if data:
                theater_summary = {
                    "theater_name": data.get("theater_info", {}).get("name", "Unknown"),
                    "total_movies": len(data.get("movies", [])),
                    "total_schedules": len(data.get("schedules", [])),
                    "success": True
                }
            else:
                theater_summary = {
                    "theater_name": theater_key,
                    "total_movies": 0,
                    "total_schedules": 0,
                    "success": False
                }
                
            report["scraping_summary"]["theaters"][theater_key] = theater_summary
            
        # レポート保存
        filename = f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"Generated summary report: {filepath}")
        return report

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="映画館スクレイピングシステム")
    parser.add_argument("--theater", type=str, help="特定の映画館のみスクレイピング")
    parser.add_argument("--output", type=str, default="output", help="出力ディレクトリ")
    parser.add_argument("--summary", action="store_true", help="サマリーレポートのみ生成")
    
    args = parser.parse_args()
    
    # オーケストレーター初期化
    orchestrator = TheaterScrapingOrchestrator(output_dir=args.output)
    
    if args.summary:
        # 既存データからサマリー生成
        # TODO: 既存JSONファイルからデータを読み込んでサマリー生成
        print("Summary generation from existing data is not implemented yet.")
        return
        
    if args.theater:
        # 特定映画館のみ
        if args.theater not in orchestrator.scrapers:
            print(f"Unknown theater: {args.theater}")
            print(f"Available theaters: {list(orchestrator.scrapers.keys())}")
            return
            
        result = orchestrator.scrape_theater(args.theater)
        if result:
            print(f"Successfully scraped {args.theater}")
        else:
            print(f"Failed to scrape {args.theater}")
    else:
        # 全映画館
        results = orchestrator.scrape_all_theaters()
        summary = orchestrator.generate_summary_report(results)
        
        # 結果表示
        print("\n=== スクレイピング結果サマリー ===")
        for theater_key, theater_data in summary["scraping_summary"]["theaters"].items():
            status = "SUCCESS" if theater_data["success"] else "FAILED"
            print(f"{theater_data['theater_name']}: {status} - 映画数: {theater_data['total_movies']}, スケジュール数: {theater_data['total_schedules']}")

if __name__ == "__main__":
    main()