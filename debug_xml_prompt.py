#!/usr/bin/env python3
"""
Debug XML prompt generation to verify hallucination prevention
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "discord_bot"))

from prompt_templates import PromptBuilder
from llm_responder import LLMResponder, MovieDataSearcher
import asyncio
import json

async def debug_xml_prompt():
    """Debug XML prompt generation"""
    
    # Initialize components
    responder = LLMResponder()
    
    print("=== Testing XML Prompt Generation ===")
    
    # Test movie query
    try:
        movie_data = await responder.data_searcher.search_movie_info("また逢いましょう")
        if movie_data:
            print("\n1. Movie Data Found:")
            print(json.dumps(movie_data, ensure_ascii=False, indent=2)[:500])
            
            print("\n2. XML Formatted Data:")
            xml_data = responder.prompt_builder._format_movie_data_xml(movie_data)
            print(xml_data[:800])
            
            print("\n3. Full XML Prompt:")
            prompt = responder.prompt_builder.build_movie_info_prompt(
                movie_title="また逢いましょう",
                movie_data=movie_data,
                user_query="また逢いましょうについて教えて",
                use_xml_format=True
            )
            print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
        else:
            print("❌ No movie data found for 'また逢いましょう'")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test theater query
    try:
        print("\n" + "="*50)
        print("=== Testing Theater XML Prompt ===")
        
        theater_data = await responder.data_searcher.search_theater_schedule("ケイズシネマ")
        if theater_data:
            print("\n1. Theater Data Found:")
            print(json.dumps(theater_data, ensure_ascii=False, indent=2)[:500])
            
            print("\n2. Theater XML Formatted:")
            xml_data = responder.prompt_builder._format_theater_data_xml(theater_data)
            print(xml_data[:800])
            
        else:
            print("❌ No theater data found for 'ケイズシネマ'")
            
    except Exception as e:
        print(f"❌ Theater Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_xml_prompt())