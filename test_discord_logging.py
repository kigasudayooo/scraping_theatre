#!/usr/bin/env python3
"""
Discord Bot Logging Test

Test the conversation logging functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.discord_bot.simple_discord_bot import SimpleMovieBot

async def test_conversation_logging():
    """Test conversation logging functionality"""
    
    print("🔍 Testing Discord Bot Logging")
    print("=" * 50)
    
    # Create bot instance (without actually connecting to Discord)
    bot = SimpleMovieBot()
    
    # Test conversation logging
    test_conversations = [
        {
            "user_message": "「また逢いましょう」について教えて",
            "bot_response": "Test response about また逢いましょう",
            "metadata": {"test": True, "user_name": "test_user"}
        },
        {
            "user_message": "ケイズシネマの上映予定は？",
            "bot_response": "Test response about ケイズシネマ schedule",
            "metadata": {"test": True, "user_name": "test_user"}
        }
    ]
    
    print("💬 Logging test conversations...")
    for i, conv in enumerate(test_conversations, 1):
        bot.log_conversation(
            conv["user_message"],
            conv["bot_response"], 
            conv["metadata"]
        )
        print(f"   {i}. Logged: {conv['user_message'][:30]}...")
    
    # Check log file
    log_file = bot.conversation_log_file
    if log_file.exists():
        print(f"\n📁 Log file created: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   Lines in log: {len(lines)}")
        
        # Show first log entry
        if lines:
            import json
            first_entry = json.loads(lines[0])
            print(f"   First entry timestamp: {first_entry['timestamp']}")
            print(f"   First entry user message: {first_entry['user_message']}")
    else:
        print("❌ Log file not created")
        return False
    
    print("\n✅ Conversation logging test completed successfully")
    return True

async def main():
    """Main test runner"""
    try:
        success = await test_conversation_logging()
        
        if success:
            print("\n🎉 Discord logging test PASSED!")
            print("Conversation logging is working correctly.")
            return 0
        else:
            print("\n⚠️  Discord logging test FAILED!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)