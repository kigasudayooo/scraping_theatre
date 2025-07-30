"""
LLM Response Generation Logic for Discord Bot

This module integrates Ollama client with prompt templates and movie data
to generate contextual responses for cinema-related queries.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ollama_client import OllamaClient, OllamaResponse
from prompt_templates import PromptBuilder, CinemaPromptTemplates
sys.path.insert(0, str(Path(__file__).parent.parent))
from scraping.json_exporter import CinemaJSONExporter

logger = logging.getLogger(__name__)

class QueryType:
    """Query type constants"""
    MOVIE_INFO = "movie_info"
    THEATER_SCHEDULE = "theater_schedule"  
    DIRECTOR_WORKS = "director_works"
    GENERAL_CINEMA = "general_cinema"
    HELP_INFO = "help_info"
    UNKNOWN = "unknown"

class MovieQueryParser:
    """Parse user queries to determine intent and extract relevant information"""
    
    def __init__(self):
        """Initialize query parser with pattern definitions"""
        # Query patterns for different types of questions
        self.patterns = {
            QueryType.MOVIE_INFO: [
                r'「(.+?)」について.*教え.*',
                r'映画.*「(.+?)」.*情報',
                r'「(.+?)」.*映画.*詳細',
                r'「(.+?)」.*どんな.*映画',
                r'(.+?).*映画.*について',
                r'(.+?)について.*教え.*',  # For movies without quotes
                r'(.+?).*情報.*教え.*',    # Additional pattern
            ],
            QueryType.THEATER_SCHEDULE: [
                r'(.+?)(?:の|が).*(?:今週|来週|スケジュール|上映予定|上映時間)',
                r'(.+?)(?:の|が).*(?:映画館|シネマ|劇場).*(?:予定|時間|スケジュール)',
                r'(.+?)(?:の|では).*何.*(?:上映|やっ)',
                r'(.+?)(?:映画館|シネマ|劇場).*(?:予定|時間|スケジュール)',
            ],
            QueryType.DIRECTOR_WORKS: [
                r'監督.*「(.+?)」.*作品',
                r'「(.+?)」.*監督.*映画',
                r'(.+?).*監督.*何.*作品',
            ],
            QueryType.HELP_INFO: [
                r'(?:ヘルプ|使い方|機能|できること|コマンド)',
                r'(?:どう|何).*(?:使う|質問|聞け)',
            ]
        }
    
    def parse_query(self, query: str) -> Tuple[str, str]:
        """
        Parse user query to determine type and extract key information
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (query_type, extracted_target)
        """
        query = query.strip()
        
        # Check each pattern type
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    target = match.group(1) if match.groups() else ""
                    return query_type, target.strip()
        
        # Default to general cinema query
        return QueryType.GENERAL_CINEMA, query

class MovieDataSearcher:
    """Search movie data for relevant information"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize data searcher
        
        Args:
            data_dir: Directory containing JSON movie data
        """
        self.data_dir = Path(data_dir)
        self.exporter = CinemaJSONExporter(data_dir)
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def load_movie_data(self, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Load movie data from JSON file
        
        Args:
            force_reload: Force reload even if data is cached
            
        Returns:
            Movie database dictionary or None if failed
        """
        try:
            # Check if we need to reload
            if not force_reload and self._cached_data is not None:
                return self._cached_data
            
            # Load fresh data
            data = self.exporter.load_cinema_database()
            if data:
                self._cached_data = data
                self._cache_timestamp = datetime.now()
                logger.info("Movie data loaded successfully")
            else:
                logger.warning("No movie data available")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load movie data: {e}")
            return None
    
    async def search_movie_info(self, movie_title: str) -> Optional[Dict[str, Any]]:
        """
        Search for specific movie information with improved matching
        
        Args:
            movie_title: Movie title to search for
            
        Returns:
            Movie data dictionary or None if not found
        """
        data = await self.load_movie_data()
        if not data or 'theaters' not in data:
            return None
        
        movie_title_clean = movie_title.strip('「」『』""\'\'').lower()
        
        # Search through all theaters with multiple matching strategies
        best_match = None
        exact_match = None
        
        for theater_id, theater_data in data['theaters'].items():
            movies = theater_data.get('movies', [])
            for movie in movies:
                title = movie.get('title', '').lower()
                title_clean = title.strip('「」『』""\'\'')
                
                # Skip entries that look like metadata (starting with ■)
                if title.startswith('■'):
                    continue
                
                # Exact match (highest priority)
                if movie_title_clean == title_clean:
                    movie_with_context = movie.copy()
                    movie_with_context['theater_name'] = theater_data.get('name', theater_id)
                    movie_with_context['theater_id'] = theater_id
                    movie_with_context['theater_url'] = theater_data.get('url', '')
                    movie_with_context['theater_address'] = theater_data.get('address', '')
                    return movie_with_context
                
                # Partial match (fallback)
                if (movie_title_clean in title_clean or title_clean in movie_title_clean) and len(title_clean) > 3:
                    if not best_match:
                        best_match = movie.copy()
                        best_match['theater_name'] = theater_data.get('name', theater_id)
                        best_match['theater_id'] = theater_id
                        best_match['theater_url'] = theater_data.get('url', '')
                        best_match['theater_address'] = theater_data.get('address', '')
        
        return best_match
    
    async def search_theater_schedule(self, theater_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for theater schedule information with improved matching
        
        Args:
            theater_name: Theater name to search for
            
        Returns:
            Theater data dictionary or None if not found
        """
        data = await self.load_movie_data()
        if not data or 'theaters' not in data:
            return None
        
        theater_name_clean = theater_name.lower().strip()
        
        # Try exact and partial matches
        for theater_id, theater_data in data['theaters'].items():
            name = theater_data.get('name', '').lower()
            
            # Exact match
            if theater_name_clean == name:
                return theater_data
            
            # Partial match (both directions)
            if theater_name_clean in name or name in theater_name_clean:
                # Additional filtering to avoid false positives
                if len(theater_name_clean) > 2 and len(name) > 2:
                    return theater_data
        
        return None
    
    async def search_by_director(self, director_name: str) -> List[Dict[str, Any]]:
        """
        Search for movies by director
        
        Args:
            director_name: Director name to search for
            
        Returns:
            List of movie dictionaries with director's works
        """
        data = await self.load_movie_data()
        if not data or 'theaters' not in data:
            return []
        
        director_name_lower = director_name.lower()
        director_works = []
        
        # Search through all theaters and movies
        for theater_id, theater_data in data['theaters'].items():
            movies = theater_data.get('movies', [])
            theater_name = theater_data.get('name', theater_id)
            
            for movie in movies:
                director = movie.get('director')
                if director:  # Check if director exists and is not None
                    director_lower = director.lower()
                    if director_name_lower in director_lower:
                        work = movie.copy()
                        work['theater'] = theater_name
                        work['theater_id'] = theater_id
                        director_works.append(work)
        
        return director_works
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """
        Get summary of available data
        
        Returns:
            Summary dictionary with data statistics
        """
        data = await self.load_movie_data()
        if not data:
            return {"error": "No data available"}
        
        return {
            "theaters": len(data.get('theaters', {})),
            "total_movies": data.get('summary', {}).get('total_movies', 0),
            "last_updated": data.get('last_updated', 'Unknown'),
            "cache_timestamp": self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }

class LLMResponder:
    """Main class for generating LLM responses to cinema queries"""
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        data_dir: str = "data",
        model: str = "qwen2.5:0.5b",
        temperature: float = 0.7,
        max_tokens: int = 512
    ):
        """
        Initialize LLM responder
        
        Args:
            ollama_client: Ollama client instance (will create if None)
            data_dir: Directory containing movie data
            model: LLM model to use
            temperature: Response randomness
            max_tokens: Maximum response length
        """
        self.ollama_client = ollama_client or OllamaClient(model=model)
        self.data_searcher = MovieDataSearcher(data_dir)
        self.query_parser = MovieQueryParser()
        self.prompt_builder = PromptBuilder()
        
        # Generation parameters
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Response caching
        self._response_cache: Dict[str, str] = {}
        self._cache_max_size = 100
    
    async def generate_response(
        self,
        user_query: str,
        user_id: Optional[str] = None,
        channel_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response to user query
        
        Args:
            user_query: User's question
            user_id: Discord user ID (for logging)
            channel_info: Channel context information
            
        Returns:
            Generated response string
        """
        try:
            # Parse query to determine intent
            query_type, target = self.query_parser.parse_query(user_query)
            
            logger.info(f"Query from {user_id}: '{user_query}' -> Type: {query_type}, Target: '{target}'")
            
            # Generate response based on query type
            if query_type == QueryType.MOVIE_INFO:
                response = await self._handle_movie_info_query(target, user_query)
            elif query_type == QueryType.THEATER_SCHEDULE:
                response = await self._handle_theater_schedule_query(target, user_query)
            elif query_type == QueryType.DIRECTOR_WORKS:
                response = await self._handle_director_works_query(target, user_query)
            elif query_type == QueryType.HELP_INFO:
                response = await self._handle_help_query(user_query)
            else:
                response = await self._handle_general_query(user_query)
            
            # Post-process response
            response = self._post_process_response(response)
            
            logger.info(f"Generated response length: {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_error_response(str(e))
    
    async def _handle_movie_info_query(self, movie_title: str, user_query: str) -> str:
        """Handle movie information queries"""
        movie_data = await self.data_searcher.search_movie_info(movie_title)
        
        if not movie_data:
            return f"申し訳ございませんが、映画「{movie_title}」の情報が見つかりませんでした。映画タイトルを正確に入力してください。"
        
        # Build prompt with XML format to prevent hallucination
        prompt = self.prompt_builder.build_movie_info_prompt(
            movie_title=movie_title,
            movie_data=movie_data,
            user_query=user_query,
            use_xml_format=True  # XML format for better LLM data comprehension
        )
        
        # Generate response
        return await self._generate_with_ollama(prompt, user_query)
    
    async def _handle_theater_schedule_query(self, theater_name: str, user_query: str) -> str:
        """Handle theater schedule queries"""
        theater_data = await self.data_searcher.search_theater_schedule(theater_name)
        
        if not theater_data:
            return f"申し訳ございませんが、映画館「{theater_name}」の情報が見つかりませんでした。映画館名を正確に入力してください。"
        
        # Build prompt with XML format to prevent hallucination
        prompt = self.prompt_builder.build_theater_schedule_prompt(
            theater_name=theater_name,
            theater_data=theater_data,
            user_query=user_query,
            use_xml_format=True  # XML format for better LLM data comprehension
        )
        
        # Generate response
        return await self._generate_with_ollama(prompt, user_query)
    
    async def _handle_director_works_query(self, director_name: str, user_query: str) -> str:
        """Handle director works queries"""
        director_works = await self.data_searcher.search_by_director(director_name)
        
        if not director_works:
            return f"申し訳ございませんが、監督「{director_name}」の作品が見つかりませんでした。監督名を正確に入力してください。"
        
        # Build prompt
        prompt = self.prompt_builder.build_director_works_prompt(
            director_name=director_name,
            director_works=director_works,
            user_query=user_query
        )
        
        # Generate response
        return await self._generate_with_ollama(prompt, user_query)
    
    async def _handle_help_query(self, user_query: str) -> str:
        """Handle help and usage queries"""
        data_summary = await self.data_searcher.get_data_summary()
        
        # Build prompt
        prompt = self.prompt_builder.build_help_prompt(
            theater_count=data_summary.get('theaters', 0),
            last_updated=data_summary.get('last_updated', 'Unknown'),
            user_query=user_query
        )
        
        # Generate response
        return await self._generate_with_ollama(prompt, user_query)
    
    async def _handle_general_query(self, user_query: str) -> str:
        """Handle general cinema queries"""
        cinema_data = await self.data_searcher.load_movie_data()
        
        if not cinema_data:
            return "申し訳ございませんが、現在映画データが利用できません。しばらくしてからもう一度お試しください。"
        
        # Build prompt
        prompt = self.prompt_builder.build_general_prompt(
            cinema_data=cinema_data,
            user_query=user_query
        )
        
        # Generate response
        return await self._generate_with_ollama(prompt, user_query)
    
    async def _generate_with_ollama(self, prompt: str, original_query: str) -> str:
        """
        Generate response using Ollama
        
        Args:
            prompt: Formatted prompt for LLM
            original_query: Original user query for cache key
            
        Returns:
            Generated response string
        """
        # Check cache
        cache_key = f"{hash(original_query)}_{hash(prompt)}"
        if cache_key in self._response_cache:
            logger.debug("Using cached response")
            return self._response_cache[cache_key]
        
        # Build system prompt
        data_summary = await self.data_searcher.get_data_summary()
        system_prompt = self.prompt_builder.build_system_prompt(
            last_updated=data_summary.get('last_updated', 'Unknown')
        )
        
        # Generate response
        async with self.ollama_client as client:
            ollama_response = await client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        
        if not ollama_response.success:
            logger.error(f"Ollama generation failed: {ollama_response.error_message}")
            return self._get_error_response(ollama_response.error_message)
        
        response_text = ollama_response.content.strip()
        
        # Cache response
        self._cache_response(cache_key, response_text)
        
        return response_text
    
    def _cache_response(self, key: str, response: str):
        """Cache response with size limit"""
        if len(self._response_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._response_cache))
            del self._response_cache[oldest_key]
        
        self._response_cache[key] = response
    
    def _post_process_response(self, response: str) -> str:
        """Post-process generated response"""
        # Clean up response
        response = response.strip()
        
        # Remove potential prompt artifacts
        if response.startswith("回答:"):
            response = response[3:].strip()
        
        # Ensure reasonable length
        if len(response) > 1500:  # Discord message limit consideration
            response = response[:1400] + "..."
        
        return response
    
    def _get_error_response(self, error_message: Optional[str] = None) -> str:
        """Generate fallback error response"""
        base_message = "申し訳ございませんが、現在回答を生成できません。"
        
        if error_message and "connection" in error_message.lower():
            return base_message + "AI回答システムに接続できませんでした。しばらくしてからもう一度お試しください。"
        
        return base_message + "しばらくしてからもう一度お試しください。"
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get responder status information
        
        Returns:
            Status dictionary
        """
        data_summary = await self.data_searcher.get_data_summary()
        
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "cache_size": len(self._response_cache),
            "data_summary": data_summary,
            "ollama_client": self.ollama_client.get_client_info()
        }