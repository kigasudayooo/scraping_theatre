#!/usr/bin/env python3
"""
Test live XML response with Ollama to verify hallucination prevention
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "discord_bot"))

from llm_responder import LLMResponder
import asyncio

async def test_live_xml_response():
    """Test actual LLM response with XML format"""
    
    responder = LLMResponder()
    
    print("=== Testing Live XML LLM Response ===")
    print("Testing query: 'また逢いましょうについて教えて'")
    print()
    
    try:
        # Generate actual response 
        response = await responder.generate_response(
            user_query="また逢いましょうについて教えて",
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
            "サバイバルアドベンチャーズ",
            "ポリティフル・オール・エンド", 
            "アイドルの女・アラモード",
            "推測",
            "想像",
            "おそらく",
            "と思われます"
        ]
        
        found_hallucinations = []
        for indicator in hallucination_indicators:
            if indicator in response:
                found_hallucinations.append(indicator)
        
        if found_hallucinations:
            print(f"⚠️  HALLUCINATION DETECTED: {found_hallucinations}")
        else:
            print("✅ No obvious hallucination detected")
            
        # Check if XML data is being used properly
        if "情報なし" in response or "XMLデータ" in response:
            print("✅ XML format appears to be working (shows '情報なし' for missing data)")
        else:
            print("⚠️  XML format might not be working properly")
            
    except Exception as e:
        print(f"❌ Error testing live response: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_xml_response())