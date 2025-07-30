#!/usr/bin/env python3
"""
Simple scraping test
"""
import json
from datetime import datetime
from pathlib import Path

# テスト用のダミーデータを生成
def create_test_data():
    """テスト用映画データ生成"""
    test_data = {
        "theaters": {
            "ケイズシネマ": {
                "address": "〒160-0022 東京都新宿区新宿3丁目35-13 3F TEL:03-3352-2471FAX:03-3352-2472",
                "url": "https://www.ks-cinema.com",
                "movies": [
                    {
                        "title": "また逢いましょう",
                        "director": "情報なし",
                        "cast": [],
                        "schedules": [
                            {
                                "date": "2025-07-29",
                                "times": ["10:00"],
                                "screen": "スクリーン1"
                            }
                        ]
                    },
                    {
                        "title": "Pinocchio√9647/26(土)～29(火)・7/31(木) 7/30(水)・8/1(金)",
                        "director": "情報なし",
                        "cast": [],
                        "schedules": [
                            {
                                "date": "2025-07-29",
                                "times": ["20:30", "20:00"],
                                "screen": "スクリーン1"
                            }
                        ]
                    }
                ]
            },
            "下高井戸シネマ": {
                "address": "東京都世田谷区松原3-27-26",
                "url": "http://shimotakaidocinema.com",
                "movies": [
                    {
                        "title": "Flow",
                        "director": "情報なし",
                        "cast": [],
                        "schedules": [
                            {
                                "date": "2025-07-26",
                                "times": ["16:05"],
                                "screen": "スクリーン1"
                            }
                        ]
                    }
                ]
            }
        },
        "generated_at": datetime.now().isoformat(),
        "total_theaters": 2,
        "total_movies": 3
    }
    
    return test_data

def main():
    """メイン実行"""
    print("🎬 テスト用映画データ生成中...")
    
    # 出力ディレクトリ作成
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # テストデータ生成
    test_data = create_test_data()
    
    # JSONファイル出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / "movies_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ テストデータ生成完了: {output_file}")
    print(f"📊 統計: {test_data['total_theaters']}映画館, {test_data['total_movies']}作品")
    
    return True

if __name__ == "__main__":
    main()