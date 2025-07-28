#!/usr/bin/env python3
"""
Ollama Integration Test Suite

Tests the complete Ollama integration pipeline including:
- Ollama client communication
- Prompt template system
- LLM responder functionality
- Error handling and retry mechanisms
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.discord_bot.ollama_client import OllamaClient, OllamaConnectionError, OllamaAPIError
from src.discord_bot.prompt_templates import PromptBuilder, CinemaPromptTemplates
from src.discord_bot.llm_responder import LLMResponder, QueryType
from src.scraping.json_exporter import CinemaJSONExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaIntegrationTester:
    """Comprehensive integration tester for Ollama components"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.prompt_builder = PromptBuilder()
        self.llm_responder = LLMResponder()
        self.data_dir = Path("data")
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("=" * 60)
        logger.info("Ollama Integration Test Suite Starting")
        logger.info("=" * 60)
        
        tests = [
            ("Ollama Health Check", self.test_ollama_health),
            ("Ollama Model Availability", self.test_ollama_models),
            ("Basic Response Generation", self.test_basic_generation),
            ("Prompt Template System", self.test_prompt_templates),
            ("Movie Data Loading", self.test_movie_data_loading),
            ("Query Parsing", self.test_query_parsing),
            ("Movie Info Queries", self.test_movie_info_queries),
            ("Theater Schedule Queries", self.test_theater_schedule_queries),
            ("Director Works Queries", self.test_director_works_queries),
            ("Help Queries", self.test_help_queries),
            ("General Queries", self.test_general_queries),
            ("Error Handling", self.test_error_handling),
            ("Japanese Text Processing", self.test_japanese_text),
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
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed > 0:
            logger.info("\nFailed Tests:")
            for test_name, result in self.test_results.items():
                if not result:
                    logger.info(f"  - {test_name}")
        
        await self.cleanup()
        return failed == 0
    
    async def test_ollama_health(self):
        """Test Ollama server connectivity"""
        try:
            async with self.ollama_client as client:
                health = await client.health_check()
                logger.info(f"Ollama health status: {health}")
                return health
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def test_ollama_models(self):
        """Test model availability"""
        try:
            async with self.ollama_client as client:
                models = await client.list_models()
                logger.info(f"Available models: {models}")
                
                # Check if our target model is available
                target_model = "qwen2.5:0.5b"
                has_target = any(target_model in model for model in models)
                logger.info(f"Target model '{target_model}' available: {has_target}")
                
                return len(models) > 0 and has_target
        except Exception as e:
            logger.error(f"Model listing failed: {e}")
            return False
    
    async def test_basic_generation(self):
        """Test basic response generation"""
        try:
            test_prompt = "こんにちは。あなたは映画館の案内をするAIですか？"
            
            async with self.ollama_client as client:
                response = await client.generate_response(
                    prompt=test_prompt,
                    system_prompt="あなたは映画館の案内をするAIアシスタントです。",
                    temperature=0.3,
                    max_tokens=100
                )
                
                logger.info(f"Generated response: {response.content[:100]}...")
                logger.info(f"Response success: {response.success}")
                
                return response.success and len(response.content) > 0
        except Exception as e:
            logger.error(f"Basic generation failed: {e}")
            return False
    
    async def test_prompt_templates(self):
        """Test prompt template system"""
        try:
            # Test system prompt
            system_prompt = self.prompt_builder.build_system_prompt("2025-01-28T10:00:00")
            logger.info(f"System prompt length: {len(system_prompt)}")
            
            # Test movie info prompt
            mock_movie_data = {
                "title": "テスト映画",
                "director": "テスト監督",
                "schedules": [{"date": "2025-01-28", "times": ["19:00"]}]
            }
            
            movie_prompt = self.prompt_builder.build_movie_info_prompt(
                movie_title="テスト映画",
                movie_data=mock_movie_data,
                user_query="この映画について教えて"
            )
            logger.info(f"Movie prompt length: {len(movie_prompt)}")
            
            # Verify prompts contain expected content
            has_movie_title = "テスト映画" in movie_prompt
            has_system_content = "映画館の案内" in system_prompt
            
            return has_movie_title and has_system_content and len(system_prompt) > 0
        except Exception as e:
            logger.error(f"Prompt template test failed: {e}")
            return False
    
    async def test_movie_data_loading(self):
        """Test movie data loading from JSON"""
        try:
            data = await self.llm_responder.data_searcher.load_movie_data()
            
            if data:
                logger.info(f"Loaded data from {len(data.get('theaters', {}))} theaters")
                logger.info(f"Total movies: {data.get('summary', {}).get('total_movies', 0)}")
                return True
            else:
                logger.warning("No movie data available")
                return False
        except Exception as e:
            logger.error(f"Movie data loading failed: {e}")
            return False
    
    async def test_query_parsing(self):
        """Test query parsing functionality"""
        try:
            test_queries = [
                ("「また逢いましょう」について教えて", QueryType.MOVIE_INFO, "また逢いましょう"),
                ("ケイズシネマの上映予定は？", QueryType.THEATER_SCHEDULE, "ケイズシネマ"),
                ("監督「テスト監督」の作品を教えて", QueryType.DIRECTOR_WORKS, "テスト監督"),
                ("使い方を教えて", QueryType.HELP_INFO, ""),
                ("おすすめの映画は？", QueryType.GENERAL_CINEMA, "おすすめの映画は？"),
            ]
            
            all_passed = True
            for query, expected_type, expected_target in test_queries:
                query_type, target = self.llm_responder.query_parser.parse_query(query)
                logger.info(f"Query: '{query}' -> Type: {query_type}, Target: '{target}'")
                
                if query_type != expected_type:
                    logger.error(f"Expected type {expected_type}, got {query_type}")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            logger.error(f"Query parsing test failed: {e}")
            return False
    
    async def test_movie_info_queries(self):
        """Test movie information queries"""
        try:
            # Test with actual movie data
            response = await self.llm_responder.generate_response(
                "「また逢いましょう」について教えて",
                user_id="test_user"
            )
            
            logger.info(f"Movie query response: {response[:150]}...")
            
            # Check if response contains movie information
            has_movie_info = "また逢いましょう" in response
            is_reasonable_length = 50 < len(response) < 1500
            
            return has_movie_info and is_reasonable_length
        except Exception as e:
            logger.error(f"Movie info query test failed: {e}")
            return False
    
    async def test_theater_schedule_queries(self):
        """Test theater schedule queries"""
        try:
            response = await self.llm_responder.generate_response(
                "ケイズシネマの上映予定は？",
                user_id="test_user"
            )
            
            logger.info(f"Theater query response: {response[:150]}...")
            
            # Check if response contains theater information
            has_theater_info = "ケイズシネマ" in response
            is_reasonable_length = 50 < len(response) < 1500
            
            return has_theater_info and is_reasonable_length
        except Exception as e:
            logger.error(f"Theater schedule query test failed: {e}")
            return False
    
    async def test_director_works_queries(self):
        """Test director works queries"""
        try:
            response = await self.llm_responder.generate_response(
                "監督「テスト監督」の作品を教えて",
                user_id="test_user"
            )
            
            logger.info(f"Director query response: {response[:150]}...")
            
            # Should handle unknown director gracefully
            has_appropriate_response = len(response) > 20
            
            return has_appropriate_response
        except Exception as e:
            logger.error(f"Director works query test failed: {e}")
            return False
    
    async def test_help_queries(self):
        """Test help queries"""
        try:
            response = await self.llm_responder.generate_response(
                "使い方を教えて",
                user_id="test_user"
            )
            
            logger.info(f"Help query response: {response[:150]}...")
            
            # Should provide helpful information
            has_help_content = len(response) > 50
            
            return has_help_content
        except Exception as e:
            logger.error(f"Help query test failed: {e}")
            return False
    
    async def test_general_queries(self):
        """Test general queries"""
        try:
            response = await self.llm_responder.generate_response(
                "おすすめの映画はありますか？",
                user_id="test_user"
            )
            
            logger.info(f"General query response: {response[:150]}...")
            
            # Should provide reasonable response
            has_content = len(response) > 30
            
            return has_content
        except Exception as e:
            logger.error(f"General query test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        try:
            # Test with invalid movie
            response = await self.llm_responder.generate_response(
                "「存在しない映画」について教えて",
                user_id="test_user"
            )
            
            logger.info(f"Error handling response: {response[:100]}...")
            
            # Should provide appropriate error message
            has_error_handling = "見つかりませんでした" in response or "申し訳" in response
            
            return has_error_handling
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    async def test_japanese_text(self):
        """Test Japanese text processing"""
        try:
            # Test Japanese input and output
            response = await self.llm_responder.generate_response(
                "今日はいい天気ですね。映画を見に行きたいです。",
                user_id="test_user"
            )
            
            logger.info(f"Japanese text response: {response[:100]}...")
            
            # Should handle Japanese text properly
            has_japanese = any(ord(char) > 127 for char in response)
            has_content = len(response) > 20
            
            return has_japanese and has_content
        except Exception as e:
            logger.error(f"Japanese text test failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.ollama_client.close()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

async def main():
    """Main test runner"""
    tester = OllamaIntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! Ollama integration is ready.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Please check the logs.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        await tester.cleanup()
        return 130
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        await tester.cleanup()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)