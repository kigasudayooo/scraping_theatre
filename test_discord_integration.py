#!/usr/bin/env python3
"""
Discord Bot LLM Integration Test

This script tests the Discord Bot's LLM integration functionality
without actually connecting to Discord. It simulates the bot's
response generation and configuration loading.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.discord_bot.discord_config import load_config
from src.discord_bot.llm_responder import LLMResponder
from src.discord_bot.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscordBotIntegrationTester:
    """Test Discord Bot's LLM integration capabilities"""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run comprehensive Discord Bot integration tests"""
        logger.info("=" * 60)
        logger.info("Discord Bot LLM Integration Test Suite")
        logger.info("=" * 60)
        
        tests = [
            ("Configuration Loading", self.test_config_loading),
            ("LLM Components Initialization", self.test_llm_initialization),
            ("Movie Query Processing", self.test_movie_query_processing),
            ("Response Generation Pipeline", self.test_response_pipeline),
            ("Error Handling", self.test_error_handling),
            ("Memory Management", self.test_memory_management),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running: {test_name} ---")
            try:
                result = await test_func()
                if result:
                    logger.info(f"✅ PASSED: {test_name}")
                    passed += 1
                else:
                    logger.error(f"❌ FAILED: {test_name}")
                    failed += 1
                self.test_results[test_name] = result
            except Exception as e:
                logger.error(f"💥 ERROR in {test_name}: {e}")
                failed += 1
                self.test_results[test_name] = False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("DISCORD BOT INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        return failed == 0
    
    async def test_config_loading(self):
        """Test Discord Bot configuration loading"""
        try:
            discord_config, schedule_config, bot_config = load_config()
            
            logger.info(f"Discord config loaded: {bool(discord_config)}")
            logger.info(f"Schedule config loaded: {bool(schedule_config)}")
            logger.info(f"Bot config loaded: {bool(bot_config)}")
            logger.info(f"AI responses enabled: {bot_config.enable_ai_responses}")
            logger.info(f"Ollama model: {bot_config.ollama_model}")
            logger.info(f"LLM temperature: {bot_config.llm_temperature}")
            
            # Basic validation
            has_required_configs = all([discord_config, schedule_config, bot_config])
            has_llm_settings = hasattr(bot_config, 'ollama_model') and hasattr(bot_config, 'llm_temperature')
            
            return has_required_configs and has_llm_settings
            
        except Exception as e:
            logger.error(f"Config loading failed: {e}")
            return False
    
    async def test_llm_initialization(self):
        """Test LLM components initialization"""
        try:
            # Load config
            _, _, bot_config = load_config()
            
            # Initialize Ollama client
            ollama_client = OllamaClient(
                base_url=bot_config.ollama_base_url,
                model=bot_config.ollama_model
            )
            
            # Initialize LLM responder
            llm_responder = LLMResponder(
                ollama_client=ollama_client,
                temperature=bot_config.llm_temperature,
                max_tokens=bot_config.llm_max_tokens
            )
            
            logger.info("LLM components initialized successfully")
            
            # Test basic functionality
            status = await llm_responder.get_status()
            logger.info(f"LLM responder status: {status}")
            
            # Cleanup
            await ollama_client.close()
            
            return True
            
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            return False
    
    async def test_movie_query_processing(self):
        """Test movie query processing pipeline"""
        try:
            # Load config
            _, _, bot_config = load_config()
            
            # Initialize components
            ollama_client = OllamaClient(
                base_url=bot_config.ollama_base_url,
                model=bot_config.ollama_model
            )
            
            llm_responder = LLMResponder(
                ollama_client=ollama_client,
                temperature=bot_config.llm_temperature,
                max_tokens=bot_config.llm_max_tokens
            )
            
            # Test queries
            test_queries = [
                "「また逢いましょう」について教えて",
                "ケイズシネマの上映予定は？",
                "こんにちは、おすすめの映画はありますか？"
            ]
            
            success_count = 0
            for query in test_queries:
                try:
                    response = await llm_responder.generate_response(
                        user_query=query,
                        user_id="test_user"
                    )
                    
                    logger.info(f"Query: '{query}' -> Response length: {len(response)}")
                    
                    if len(response) > 10:  # Reasonable response
                        success_count += 1
                        
                except Exception as e:
                    logger.warning(f"Query failed: {query} - {e}")
            
            # Cleanup
            await ollama_client.close()
            
            success_rate = success_count / len(test_queries)
            logger.info(f"Query processing success rate: {success_rate:.1%}")
            
            return success_rate >= 0.6  # At least 60% success
            
        except Exception as e:
            logger.error(f"Movie query processing test failed: {e}")
            return False
    
    async def test_response_pipeline(self):
        """Test complete response generation pipeline"""
        try:
            # Simulate Discord Bot response processing
            from unittest.mock import Mock
            
            # Mock message object
            mock_message = Mock()
            mock_message.content = "「また逢いましょう」について教えて"
            mock_message.author.id = 12345
            mock_message.channel.name = "movie-questions"
            mock_message.guild.name = "Test Guild"
            
            # Load config and initialize components
            _, _, bot_config = load_config()
            
            ollama_client = OllamaClient(
                base_url=bot_config.ollama_base_url,
                model=bot_config.ollama_model
            )
            
            llm_responder = LLMResponder(
                ollama_client=ollama_client,
                temperature=bot_config.llm_temperature,
                max_tokens=bot_config.llm_max_tokens
            )
            
            # Simulate the bot's query processing
            user_id = str(mock_message.author.id)
            channel_info = {
                "channel_name": mock_message.channel.name,
                "guild_name": mock_message.guild.name
            }
            
            response = await llm_responder.generate_response(
                user_query=mock_message.content,
                user_id=user_id,
                channel_info=channel_info
            )
            
            logger.info(f"Pipeline test - Response: {response[:100]}...")
            
            # Validate response
            is_valid_response = (
                len(response) > 20 and
                len(response) < 2000 and  # Discord limit
                "また逢いましょう" in response
            )
            
            # Cleanup
            await ollama_client.close()
            
            return is_valid_response
            
        except Exception as e:
            logger.error(f"Response pipeline test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling in LLM integration"""
        try:
            # Test with invalid Ollama URL
            invalid_client = OllamaClient(base_url="http://invalid:11434")
            
            llm_responder = LLMResponder(
                ollama_client=invalid_client,
                temperature=0.7,
                max_tokens=512
            )
            
            # This should handle errors gracefully
            response = await llm_responder.generate_response(
                user_query="Test query with invalid client",
                user_id="test_user"
            )
            
            logger.info(f"Error handling response: {response}")
            
            # Should return error message, not crash
            has_error_message = "申し訳" in response or "エラー" in response or "回答を生成できません" in response
            
            # Cleanup
            await invalid_client.close()
            
            return has_error_message
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    async def test_memory_management(self):
        """Test memory management and resource cleanup"""
        try:
            # Create and destroy multiple clients
            for i in range(3):
                _, _, bot_config = load_config()
                
                ollama_client = OllamaClient(
                    base_url=bot_config.ollama_base_url,
                    model=bot_config.ollama_model
                )
                
                llm_responder = LLMResponder(
                    ollama_client=ollama_client,
                    temperature=bot_config.llm_temperature,
                    max_tokens=bot_config.llm_max_tokens
                )
                
                # Use the client briefly
                status = await llm_responder.get_status()
                logger.info(f"Memory test iteration {i+1}: {status['model']}")
                
                # Cleanup
                await ollama_client.close()
            
            logger.info("Memory management test completed")
            return True
            
        except Exception as e:
            logger.error(f"Memory management test failed: {e}")
            return False

async def main():
    """Main test runner"""
    tester = DiscordBotIntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All Discord Bot integration tests passed!")
            print("The bot is ready for LLM-powered responses.")
            return 0
        else:
            print("\n⚠️  Some integration tests failed.")
            print("Please check the configuration and Ollama service.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)