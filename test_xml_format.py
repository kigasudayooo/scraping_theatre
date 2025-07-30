#!/usr/bin/env python3
"""
Test XML formatting for LLM hallucination prevention
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "discord_bot"))

from prompt_templates import PromptBuilder
import json

def test_xml_movie_formatting():
    """Test XML formatting for movie data"""
    
    # Sample movie data (similar to what would come from JSON)
    movie_data = {
        "title": "ソングライン",
        "director": "カリオ・サレム",
        "cast": ["エイドリアン・バーボー", "ジェレミー・キャンプ"],
        "genre": "ドラマ",
        "duration": "112分",
        "synopsis": "実話に基づく感動的な物語",
        "theater_name": "ケイズシネマ",
        "theater_address": "東京都新宿区",
        "schedules": [
            {"date": "2025-07-30", "times": ["14:30", "17:00", "19:30"], "screen": "スクリーン1"},
            {"date": "2025-07-31", "times": ["12:00", "16:30"], "screen": "スクリーン2"}
        ]
    }
    
    builder = PromptBuilder()
    
    print("=== JSON Format (Original) ===")
    json_formatted = builder._format_movie_data(movie_data)
    print(json_formatted)
    
    print("\n=== XML Format (New Anti-Hallucination) ===")
    xml_formatted = builder._format_movie_data_xml(movie_data)
    print(xml_formatted)
    
    print("\n=== Movie Info Prompt with XML ===")
    prompt = builder.build_movie_info_prompt(
        movie_title="ソングライン",
        movie_data=movie_data,
        user_query="ソングラインについて教えて",
        use_xml_format=True
    )
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

def test_xml_theater_formatting():
    """Test XML formatting for theater data"""
    
    # Sample theater data
    theater_data = {
        "name": "ケイズシネマ",
        "address": "東京都新宿区歌舞伎町1-1-1",
        "url": "https://kscine.com",
        "movies": [
            {
                "title": "ソングライン",
                "director": "カリオ・サレム",
                "schedules": [
                    {"date": "2025-07-30", "times": ["14:30", "17:00"], "screen": "スクリーン1"}
                ]
            },
            {
                "title": "Another Movie",
                "director": "監督名",
                "schedules": [
                    {"date": "2025-07-30", "times": ["12:00", "19:00"], "screen": "スクリーン2"}
                ]
            }
        ]
    }
    
    builder = PromptBuilder()
    
    print("\n=== Theater XML Format ===")
    xml_formatted = builder._format_theater_data_xml(theater_data)
    print(xml_formatted)

if __name__ == "__main__":
    print("Testing XML formatting for LLM hallucination prevention")
    print("=" * 60)
    
    test_xml_movie_formatting()
    test_xml_theater_formatting()
    
    print("\n" + "=" * 60)
    print("XML formatting test completed successfully!")
    print("Key improvements:")
    print("1. Clear XML structure with explicit tags")
    print("2. Strict data boundaries prevent hallucination")
    print("3. Structured hierarchy for better LLM comprehension")