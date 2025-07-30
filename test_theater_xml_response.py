#!/usr/bin/env python3
"""
Test theater XML response with ultra-strict prompt
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "discord_bot"))

from llm_responder import LLMResponder
import asyncio

async def test_theater_xml_response():
    """Test theater schedule XML response"""
    
    responder = LLMResponder()
    
    print("=== Testing Theater XML LLM Response ===")
    print("Testing query: 'ケイズシネマで観られる映画は？'")
    print()
    
    try:
        # Generate actual response 
        response = await responder.generate_response(
            user_query="ケイズシネマで観られる映画は？",
            user_id="test_user",
            channel_info={"channel_name": "test", "guild_name": "test"}
        )
        
        print("=" * 50)
        print("ACTUAL LLM RESPONSE:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # Check for hallucination indicators
        hallucination_indicators = [
            "ビヨンド",
            "サバイバルアドベンチャーズ", 
            "パレロポレ東中野",
            "ユーロスペース",
            "ハイセラターキン",
            "電子車",
            "トロフィック"
        ]
        
        found_hallucinations = []
        for indicator in hallucination_indicators:
            if indicator in response:
                found_hallucinations.append(indicator)
        
        if found_hallucinations:
            print(f"⚠️  HALLUCINATION DETECTED: {found_hallucinations}")
        else:
            print("✅ No obvious hallucination detected")
            
        # Check if actual movie titles are mentioned
        actual_movies = ["また逢いましょう", "台湾巨匠傑作選2025", "Pinocchio"]
        found_actual = []
        for movie in actual_movies:
            if movie in response:
                found_actual.append(movie)
        
        if found_actual:
            print(f"✅ Actual movies mentioned: {found_actual}")
        else:
            print("⚠️  No actual movie titles found")
            
    except Exception as e:
        print(f"❌ Error testing live response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_theater_xml_response())