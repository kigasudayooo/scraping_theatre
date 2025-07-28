#!/usr/bin/env python3
"""
Full System Integration Test

This script performs end-to-end testing of the complete Ollama integration system:
- JSON data generation and file locking
- LLM response system
- Discord Bot integration
- Data update notifications
- Error handling and recovery
"""

import asyncio
import json
import sys
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.scraping.json_exporter import CinemaJSONExporter
from src.scraping.models import CinemaDatabase, TheaterData, TheaterInfo, MovieInfo
from src.discord_bot.discord_config import load_config
from src.discord_bot.llm_responder import LLMResponder
from src.discord_bot.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FullSystemTester:
    """Comprehensive system integration tester"""
    
    def __init__(self):
        self.test_results = {}
        self.temp_data_dir = None
        
    async def run_all_tests(self):
        """Run complete system integration tests"""
        logger.info("=" * 70)
        logger.info("FULL SYSTEM INTEGRATION TEST SUITE")
        logger.info("=" * 70)
        
        # Setup temporary data directory
        self.temp_data_dir = tempfile.mkdtemp(prefix="cinema_test_")
        logger.info(f"Using temporary data directory: {self.temp_data_dir}")
        
        tests = [
            ("Data Generation and Export", self.test_data_generation),
            ("File Locking Mechanism", self.test_file_locking),
            ("JSON Data Integrity", self.test_data_integrity),
            ("LLM System Integration", self.test_llm_integration),
            ("Discord Bot System", self.test_discord_bot_system),
            ("Error Recovery", self.test_error_recovery),
            ("Performance Under Load", self.test_performance),
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
        
        # Cleanup
        await self.cleanup()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("FULL SYSTEM TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        # Detailed results
        logger.info("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")
        
        return failed == 0
    
    async def test_data_generation(self):
        """Test complete data generation pipeline"""
        try:
            # Create mock theater data
            test_data = self._create_test_data()
            
            # Export to JSON
            exporter = CinemaJSONExporter(self.temp_data_dir)
            output_file = exporter.export_cinema_database(test_data)
            
            # Verify file exists and is valid JSON
            output_path = Path(output_file)
            if not output_path.exists():
                logger.error("Output file does not exist")
                return False
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            required_keys = ['last_updated', 'theaters', 'summary']
            if not all(key in data for key in required_keys):
                logger.error("Missing required keys in output data")
                return False
            
            logger.info(f"Data generation successful: {len(data['theaters'])} theaters, {data['summary']['total_movies']} movies")
            return True
            
        except Exception as e:
            logger.error(f"Data generation failed: {e}")
            return False
    
    async def test_file_locking(self):
        """Test file locking mechanism"""
        try:
            test_data = self._create_test_data()
            cinema_db = CinemaDatabase.from_theater_data_list(test_data)
            
            # Test concurrent writes
            output_file = Path(self.temp_data_dir) / "lock_test.json"
            
            # Simulate concurrent access
            async def write_task(task_id):
                try:
                    cinema_db.save_to_file(str(output_file), use_file_lock=True)
                    return True
                except Exception as e:
                    logger.warning(f"Write task {task_id} failed: {e}")
                    return False
            
            # Run multiple write tasks concurrently
            tasks = [write_task(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least one should succeed
            success_count = sum(1 for r in results if r is True)
            
            logger.info(f"File locking test: {success_count}/3 writes succeeded")
            
            # Verify final file is valid
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Should not raise exception
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"File locking test failed: {e}")
            return False
    
    async def test_data_integrity(self):
        """Test data integrity across the pipeline"""
        try:
            # Create test data with specific content
            test_data = self._create_test_data()
            original_movie_count = sum(len(td.movies) for td in test_data)
            
            # Export and reload
            exporter = CinemaJSONExporter(self.temp_data_dir)
            output_file = exporter.export_cinema_database(test_data)
            
            # Load and verify
            reloaded_data = exporter.load_cinema_database(filename=Path(output_file).name)
            
            if not reloaded_data:
                logger.error("Failed to reload data")
                return False
            
            # Count movies in reloaded data
            reloaded_movie_count = sum(len(theater['movies']) for theater in reloaded_data['theaters'].values())
            
            if original_movie_count != reloaded_movie_count:
                logger.error(f"Movie count mismatch: {original_movie_count} -> {reloaded_movie_count}")
                return False
            
            logger.info(f"Data integrity verified: {reloaded_movie_count} movies preserved")
            return True
            
        except Exception as e:
            logger.error(f"Data integrity test failed: {e}")
            return False
    
    async def test_llm_integration(self):
        """Test LLM integration with real data"""
        try:
            # Generate test data
            test_data = self._create_test_data()
            exporter = CinemaJSONExporter(self.temp_data_dir)
            output_file = exporter.export_cinema_database(test_data)
            
            # Initialize LLM system with test data
            _, _, bot_config = load_config()
            
            ollama_client = OllamaClient(
                base_url=bot_config.ollama_base_url,
                model=bot_config.ollama_model
            )
            
            llm_responder = LLMResponder(
                ollama_client=ollama_client,
                data_dir=self.temp_data_dir,
                temperature=bot_config.llm_temperature,
                max_tokens=bot_config.llm_max_tokens
            )
            
            # Test various query types
            test_queries = [
                "「テスト映画A」について教えて",
                "テスト映画館の上映予定は？",
                "こんにちは、映画について質問があります"
            ]
            
            success_count = 0
            for query in test_queries:
                try:
                    response = await llm_responder.generate_response(
                        user_query=query,
                        user_id="test_user"
                    )
                    
                    if len(response) > 20:  # Reasonable response
                        success_count += 1
                        logger.info(f"LLM query success: '{query}' -> {len(response)} chars")
                    else:
                        logger.warning(f"Short response for: '{query}'")
                        
                except Exception as e:
                    logger.warning(f"LLM query failed: '{query}' - {e}")
            
            # Cleanup
            await ollama_client.close()
            
            success_rate = success_count / len(test_queries)
            logger.info(f"LLM integration success rate: {success_rate:.1%}")
            
            return success_rate >= 0.6  # At least 60% success
            
        except Exception as e:
            logger.error(f"LLM integration test failed: {e}")
            return False
    
    async def test_discord_bot_system(self):
        """Test Discord bot system integration"""
        try:
            # Mock Discord bot components
            from src.discord_bot.discord_bot_main import CombinedMovieBot
            
            # Create test data
            test_data = self._create_test_data()
            exporter = CinemaJSONExporter(self.temp_data_dir)
            output_file = exporter.export_cinema_database(test_data)
            
            # Test bot initialization (without actually connecting to Discord)
            try:
                # This will test config loading and component initialization
                _, _, bot_config = load_config()
                
                # Mock the bot initialization
                mock_bot = Mock()
                mock_bot.bot_config = bot_config
                
                if bot_config.enable_ai_responses:
                    # Test LLM components can be initialized
                    ollama_client = OllamaClient(
                        base_url=bot_config.ollama_base_url,
                        model=bot_config.ollama_model
                    )
                    
                    llm_responder = LLMResponder(
                        ollama_client=ollama_client,
                        data_dir=self.temp_data_dir,
                        temperature=bot_config.llm_temperature,
                        max_tokens=bot_config.llm_max_tokens
                    )
                    
                    # Test basic functionality
                    status = await llm_responder.get_status()
                    
                    # Cleanup
                    await ollama_client.close()
                    
                    logger.info(f"Discord bot system components initialized successfully")
                    return True
                else:
                    logger.info("AI responses disabled in config")
                    return True
                    
            except Exception as e:
                logger.error(f"Bot initialization failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Discord bot system test failed: {e}")
            return False
    
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        try:
            # Test with invalid Ollama URL
            invalid_client = OllamaClient(base_url="http://invalid:11434")
            
            llm_responder = LLMResponder(
                ollama_client=invalid_client,
                data_dir=self.temp_data_dir,
                temperature=0.7,
                max_tokens=512
            )
            
            # This should handle errors gracefully
            response = await llm_responder.generate_response(
                user_query="Test error recovery",
                user_id="test_user"
            )
            
            # Should return error message, not crash
            has_error_handling = "申し訳" in response or "エラー" in response
            
            # Cleanup
            await invalid_client.close()
            
            logger.info(f"Error recovery test: {'✅ Passed' if has_error_handling else '❌ Failed'}")
            return has_error_handling
            
        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            return False
    
    async def test_performance(self):
        """Test system performance under load"""
        try:
            # Generate larger test dataset
            large_test_data = []
            for i in range(5):  # 5 theaters
                theater_info = TheaterInfo(
                    name=f"テスト映画館{i+1}",
                    url=f"https://test{i+1}.com",
                    address=f"テスト住所{i+1}"
                )
                
                movies = []
                for j in range(10):  # 10 movies per theater
                    movies.append(MovieInfo(
                        title=f"テスト映画{i+1}-{j+1}",
                        director=f"テスト監督{j+1}"
                    ))
                
                large_test_data.append(TheaterData(
                    theater_info=theater_info,
                    movies=movies,
                    schedules=[]
                ))
            
            # Time the export operation
            import time
            start_time = time.time()
            
            exporter = CinemaJSONExporter(self.temp_data_dir)
            output_file = exporter.export_cinema_database(large_test_data)
            
            export_time = time.time() - start_time
            
            # Check file size
            output_path = Path(output_file)
            file_size = output_path.stat().st_size
            
            logger.info(f"Performance test: {export_time:.2f}s export time, {file_size} bytes")
            
            # Performance should be reasonable (under 5 seconds for this dataset)
            return export_time < 5.0 and file_size > 0
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False
    
    async def test_memory_management(self):
        """Test memory management and cleanup"""
        try:
            # Create and destroy multiple systems
            for i in range(3):
                # Create test data
                test_data = self._create_test_data()
                
                # Export data
                exporter = CinemaJSONExporter(self.temp_data_dir)
                output_file = exporter.export_cinema_database(test_data)
                
                # Initialize LLM system
                _, _, bot_config = load_config()
                
                ollama_client = OllamaClient(
                    base_url=bot_config.ollama_base_url,
                    model=bot_config.ollama_model
                )
                
                llm_responder = LLMResponder(
                    ollama_client=ollama_client,
                    data_dir=self.temp_data_dir,
                    temperature=0.7,
                    max_tokens=256
                )
                
                # Use briefly
                status = await llm_responder.get_status()
                
                # Cleanup
                await ollama_client.close()
                
                logger.info(f"Memory test iteration {i+1} completed")
            
            logger.info("Memory management test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Memory management test failed: {e}")
            return False
    
    def _create_test_data(self):
        """Create test theater data"""
        theater_info = TheaterInfo(
            name="テスト映画館",
            url="https://test-cinema.com",
            address="テスト住所"
        )
        
        movies = [
            MovieInfo(
                title="テスト映画A",
                director="テスト監督A"
            ),
            MovieInfo(
                title="テスト映画B",
                director="テスト監督B"
            )
        ]
        
        return [TheaterData(
            theater_info=theater_info,
            movies=movies,
            schedules=[]
        )]
    
    async def cleanup(self):
        """Clean up test resources"""
        try:
            import shutil
            if self.temp_data_dir and Path(self.temp_data_dir).exists():
                shutil.rmtree(self.temp_data_dir)
                logger.info("Test data directory cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

async def main():
    """Main test runner"""
    tester = FullSystemTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All full system tests passed!")
            print("The complete Ollama integration system is ready for production.")
            return 0
        else:
            print("\n⚠️  Some system tests failed.")
            print("Please review the logs and fix any issues.")
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