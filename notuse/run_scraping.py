#!/usr/bin/env python3
"""
映画館スクレイピング実行スクリプト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.scraping.main import TheaterScrapingOrchestrator

def run_single_theater_test():
    """単一映画館のテストスクレイピング"""
    print("=== 単一映画館テストスクレイピング ===")
    
    orchestrator = TheaterScrapingOrchestrator(output_dir="test_output")
    
    # ケイズシネマでテスト
    print("ケイズシネマをテスト中...")
    result = orchestrator.scrape_theater("ks_cinema")
    
    if result:
        print("✅ ケイズシネマのスクレイピング成功")
        print(f"映画数: {len(result.get('movies', []))}")
        print(f"スケジュール数: {len(result.get('schedules', []))}")
    else:
        print("❌ ケイズシネマのスクレイピング失敗")

def run_all_theaters():
    """全映画館のスクレイピング"""
    print("=== 全映画館スクレイピング ===")
    
    orchestrator = TheaterScrapingOrchestrator(output_dir="output")
    results = orchestrator.scrape_all_theaters()
    summary = orchestrator.generate_summary_report(results)
    
    print("\n=== スクレイピング結果サマリー ===")
    for theater_key, theater_data in summary["scraping_summary"]["theaters"].items():
        status = "✅ SUCCESS" if theater_data["success"] else "❌ FAILED"
        print(f"{theater_data['theater_name']}: {status}")
        print(f"  - 映画数: {theater_data['total_movies']}")
        print(f"  - スケジュール数: {theater_data['total_schedules']}")
        print()

def show_available_theaters():
    """利用可能な映画館一覧表示"""
    print("=== 利用可能な映画館一覧 ===")
    
    orchestrator = TheaterScrapingOrchestrator()
    
    theaters = [
        ("ks_cinema", "ケイズシネマ", "https://www.ks-cinema.com"),
        ("pole_pole", "ポレポレ東中野", "https://pole2.co.jp"),
        ("eurospace", "ユーロスペース", "https://www.eurospace.co.jp"),
        ("shimotakaido", "下高井戸シネマ", "https://shimotakaido-cinema.stores.jp"),
        ("waseda_shochiku", "早稲田松竹", "http://wasedashochiku.co.jp"),
        ("shinjuku_musashino", "新宿武蔵野館", "https://shinjuku.musashino-k.jp")
    ]
    
    for key, name, url in theaters:
        print(f"📽️  {name} ({key})")
        print(f"   URL: {url}")
        print()

def main():
    """メイン実行関数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            run_single_theater_test()
        elif command == "all":
            run_all_theaters()
        elif command == "list":
            show_available_theaters()
        elif command in ["ks_cinema", "pole_pole", "eurospace", "shimotakaido", "waseda_shochiku", "shinjuku_musashino"]:
            # 特定映画館のスクレイピング
            orchestrator = TheaterScrapingOrchestrator(output_dir="output")
            result = orchestrator.scrape_theater(command)
            if result:
                print(f"✅ {command} のスクレイピング成功")
            else:
                print(f"❌ {command} のスクレイピング失敗")
        else:
            print("使用方法:")
            print("  python run_scraping.py test          # 単一映画館テスト")
            print("  python run_scraping.py all           # 全映画館スクレイピング")
            print("  python run_scraping.py list          # 利用可能映画館一覧")
            print("  python run_scraping.py [theater_key] # 特定映画館スクレイピング")
    else:
        print("映画館スクレイピングシステム")
        print("使用方法:")
        print("  python run_scraping.py test          # 単一映画館テスト")
        print("  python run_scraping.py all           # 全映画館スクレイピング") 
        print("  python run_scraping.py list          # 利用可能映画館一覧")
        print("  python run_scraping.py [theater_key] # 特定映画館スクレイピング")

if __name__ == "__main__":
    main()