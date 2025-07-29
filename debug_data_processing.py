#!/usr/bin/env python3
"""
Debug Data Processing

Check if data is being processed correctly at each step
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.discord_bot.llm_responder import MovieDataSearcher, MovieQueryParser
from src.discord_bot.prompt_templates import PromptBuilder

async def debug_data_flow():
    """Debug the complete data processing flow"""
    
    print("🔍 Data Processing Debug")
    print("=" * 50)
    
    # Test 1: Data loading
    print("\n1. Testing Data Loading...")
    searcher = MovieDataSearcher("data")
    data = await searcher.load_movie_data()
    
    if data:
        print(f"✅ Data loaded successfully")
        print(f"   Theaters: {len(data.get('theaters', {}))}")
        print(f"   Total movies: {data.get('summary', {}).get('total_movies', 0)}")
        
        # Show first theater's first movie
        theaters = data.get('theaters', {})
        if theaters:
            first_theater_id = list(theaters.keys())[0]
            first_theater = theaters[first_theater_id]
            movies = first_theater.get('movies', [])
            if movies:
                print(f"   Sample movie: {movies[0].get('title', 'No title')}")
                print(f"   Has schedules: {bool(movies[0].get('schedules'))}")
                if movies[0].get('schedules'):
                    print(f"   First schedule: {movies[0]['schedules'][0]}")
    else:
        print("❌ Failed to load data!")
        return
    
    # Test 2: Movie search
    print("\n2. Testing Movie Search...")
    test_titles = ["また逢いましょう", "台湾巨匠傑作選2025"]
    
    for title in test_titles:
        result = await searcher.search_movie_info(title)
        if result:
            print(f"✅ Found '{title}':")
            print(f"   Theater: {result.get('theater_name', 'Unknown')}")
            print(f"   Director: {result.get('director', 'Unknown')}")
            print(f"   Schedules: {len(result.get('schedules', []))}")
            if result.get('schedules'):
                print(f"   First schedule: {result['schedules'][0]}")
        else:
            print(f"❌ Could not find '{title}'")
    
    # Test 3: Theater search
    print("\n3. Testing Theater Search...")
    theater_result = await searcher.search_theater_schedule("ケイズシネマ")
    if theater_result:
        print(f"✅ Found ケイズシネマ:")
        print(f"   Name: {theater_result.get('name', 'Unknown')}")
        print(f"   Movies: {len(theater_result.get('movies', []))}")
        movies = theater_result.get('movies', [])
        if movies:
            print(f"   First movie: {movies[0].get('title', 'Unknown')}")
            if movies[0].get('schedules'):
                print(f"   First movie schedules: {len(movies[0]['schedules'])}")
    else:
        print("❌ Could not find ケイズシネマ")
    
    # Test 4: Query parsing
    print("\n4. Testing Query Parsing...")
    parser = MovieQueryParser()
    test_queries = [
        "「また逢いましょう」について教えて",
        "ケイズシネマの上映予定は？",
        "台湾巨匠傑作選2025について教えて"
    ]
    
    for query in test_queries:
        query_type, target = parser.parse_query(query)
        print(f"Query: '{query}'")
        print(f"   Type: {query_type}, Target: '{target}'")
    
    # Test 5: Prompt building
    print("\n5. Testing Prompt Building...")
    builder = PromptBuilder()
    
    # Test movie info prompt
    movie_data = await searcher.search_movie_info("また逢いましょう")
    if movie_data:
        prompt = builder.build_movie_info_prompt(
            movie_title="また逢いましょう",
            movie_data=movie_data,
            user_query="「また逢いましょう」について教えて"
        )
        print(f"Movie info prompt length: {len(prompt)}")
        print("First 200 chars of prompt:")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    
    # Test theater schedule prompt
    if theater_result:
        theater_prompt = builder.build_theater_schedule_prompt(
            theater_name="ケイズシネマ",
            theater_data=theater_result,
            user_query="ケイズシネマの上映予定は？"
        )
        print(f"\nTheater schedule prompt length: {len(theater_prompt)}")
        print("First 200 chars of theater prompt:")
        print(theater_prompt[:200] + "..." if len(theater_prompt) > 200 else theater_prompt)

async def main():
    """Main debug runner"""
    try:
        await debug_data_flow()
        return 0
    except Exception as e:
        print(f"💥 Debug crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)