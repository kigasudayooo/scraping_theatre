#!/usr/bin/env python3
"""
Debug theater prompt generation for XML format
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "discord_bot"))

from llm_responder import LLMResponder
import asyncio

async def debug_theater_prompt():
    """Debug theater prompt generation"""
    
    responder = LLMResponder()
    
    print("=== Debugging Theater XML Prompt ===")
    
    try:
        # Get theater data
        theater_data = await responder.data_searcher.search_theater_schedule("ケイズシネマ")
        if theater_data:
            print("1. Theater Data Found:")
            print(f"Movies count: {len(theater_data.get('movies', []))}")
            for i, movie in enumerate(theater_data.get('movies', [])[:3], 1):
                print(f"  {i}. {movie.get('title', 'No title')}")
            
            print("\n2. XML Formatted Theater Data:")
            xml_data = responder.prompt_builder._format_theater_data_xml(theater_data)
            print(xml_data[:1000])
            
            print("\n3. Full Theater XML Prompt (first 800 chars):")
            prompt = responder.prompt_builder.build_theater_schedule_prompt(
                theater_name="ケイズシネマ",
                theater_data=theater_data,
                user_query="ケイズシネマで観られる映画は？",
                use_xml_format=True
            )
            print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
            
        else:
            print("❌ No theater data found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_theater_prompt())