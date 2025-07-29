#!/usr/bin/env python3
"""
Accuracy Improvement Test Script

Test specific queries to verify the improvements in JSON data processing
and schedule accuracy.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.discord_bot.llm_responder import LLMResponder
from src.discord_bot.ollama_client import OllamaClient
from src.discord_bot.discord_config import load_config

async def test_specific_queries():
    """Test specific queries that should show improved accuracy"""
    
    print("🧪 Testing Improved Accuracy")
    print("=" * 50)
    
    # Initialize components
    _, _, bot_config = load_config()
    
    ollama_client = OllamaClient(
        base_url=bot_config.ollama_base_url,
        model=bot_config.ollama_model
    )
    
    llm_responder = LLMResponder(
        ollama_client=ollama_client,
        data_dir="data",
        temperature=0.5,  # Lower temperature for more accurate responses
        max_tokens=512
    )
    
    # Test queries with expected improvements
    test_queries = [
        {
            "query": "「また逢いましょう」について教えて",
            "expected_improvements": ["正確なスケジュール情報", "映画館名", "上映時間"]
        },
        {
            "query": "ケイズシネマの今日の上映予定は？", 
            "expected_improvements": ["今日以降のスケジュール", "詳細な時間情報", "スクリーン情報"]
        },
        {
            "query": "台湾巨匠傑作選2025について教えて",
            "expected_improvements": ["映画の基本情報", "上映館情報", "正確なデータ読み取り"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🎬 Test {i}: {test_case['query']}")
        print("-" * 30)
        
        try:
            response = await llm_responder.generate_response(
                user_query=test_case['query'],
                user_id="accuracy_test"
            )
            
            print(f"Response ({len(response)} chars):")
            print(response)
            print()
            
            # Simple accuracy checks
            improvements_found = []
            for improvement in test_case['expected_improvements']:
                if any(keyword in response for keyword in improvement.split()):
                    improvements_found.append(improvement)
            
            accuracy_score = len(improvements_found) / len(test_case['expected_improvements'])
            results.append({
                "query": test_case['query'],
                "accuracy_score": accuracy_score,
                "improvements_found": improvements_found,
                "response_length": len(response)
            })
            
            print(f"✅ Accuracy Score: {accuracy_score:.1%}")
            print(f"Found improvements: {', '.join(improvements_found)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "query": test_case['query'],
                "accuracy_score": 0.0,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ACCURACY IMPROVEMENT SUMMARY")
    print("=" * 50)
    
    total_score = sum(r.get('accuracy_score', 0) for r in results)
    average_accuracy = total_score / len(results) if results else 0
    
    print(f"Average Accuracy Score: {average_accuracy:.1%}")
    print(f"Tests Completed: {len(results)}")
    
    successful_tests = [r for r in results if 'error' not in r]
    if successful_tests:
        avg_response_length = sum(r['response_length'] for r in successful_tests) / len(successful_tests)
        print(f"Average Response Length: {avg_response_length:.0f} characters")
    
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        if 'error' in result:
            print(f"  {i}. ❌ {result['query']} - Error: {result['error']}")
        else:
            print(f"  {i}. {'✅' if result['accuracy_score'] > 0.5 else '⚠️ '} {result['query']} - {result['accuracy_score']:.1%}")
    
    # Cleanup
    await ollama_client.close()
    
    return average_accuracy >= 0.7  # 70% accuracy threshold

async def main():
    """Main test runner"""
    try:
        success = await test_specific_queries()
        
        if success:
            print("\n🎉 Accuracy improvement test PASSED!")
            print("The LLM system shows significant improvement in data processing.")
            return 0
        else:
            print("\n⚠️  Accuracy improvement test needs more work.")
            print("Some areas still need refinement.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)