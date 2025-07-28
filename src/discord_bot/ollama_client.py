"""
Ollama API Client for Discord Bot Integration

This module provides a comprehensive client for communicating with the local Ollama API
to generate AI responses for cinema information queries.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Ollama API response structure"""
    content: str
    model: str
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

class OllamaConnectionError(Exception):
    """Ollama connection related errors"""
    pass

class OllamaAPIError(Exception):
    """Ollama API related errors"""
    pass

class OllamaClient:
    """
    Asynchronous client for Ollama API communication
    
    Handles connection management, request formatting, response parsing,
    and error recovery for local Ollama instances.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:0.5b",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server base URL
            model: Default model to use for generation
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # API endpoints
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
        self.health_url = f"{self.base_url}"
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is available
        
        Returns:
            True if server is responding, False otherwise
        """
        try:
            await self._ensure_session()
            async with self._session.get(self.health_url) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        Get list of available models
        
        Returns:
            List of model names
            
        Raises:
            OllamaConnectionError: If unable to connect to Ollama
            OllamaAPIError: If API returns an error
        """
        try:
            await self._ensure_session()
            async with self._session.get(self.tags_url) as response:
                if response.status != 200:
                    raise OllamaAPIError(f"Failed to list models: HTTP {response.status}")
                
                data = await response.json()
                models = [model.get('name', '') for model in data.get('models', [])]
                return [m for m in models if m]  # Filter empty names
                
        except aiohttp.ClientError as e:
            raise OllamaConnectionError(f"Connection error: {e}") from e
        except json.JSONDecodeError as e:
            raise OllamaAPIError(f"Invalid JSON response: {e}") from e
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> OllamaResponse:
        """
        Generate response using Ollama API
        
        Args:
            prompt: User prompt/question
            model: Model to use (defaults to instance model)
            system_prompt: System prompt for context
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            stream: Whether to stream response (not implemented)
            
        Returns:
            OllamaResponse object with generated content
            
        Raises:
            OllamaConnectionError: If unable to connect to Ollama
            OllamaAPIError: If API returns an error
        """
        model_name = model or self.model
        
        # Build request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,  # Always false for now
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Execute request with retries
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                await self._ensure_session()
                
                logger.debug(f"Generating response (attempt {attempt + 1}/{self.max_retries + 1})")
                
                async with self._session.post(self.generate_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OllamaAPIError(f"HTTP {response.status}: {error_text}")
                    
                    response_data = await response.json()
                    
                    # Check for API-level errors
                    if "error" in response_data:
                        raise OllamaAPIError(f"API error: {response_data['error']}")
                    
                    # Parse successful response
                    return OllamaResponse(
                        content=response_data.get("response", ""),
                        model=response_data.get("model", model_name),
                        total_duration=response_data.get("total_duration"),
                        load_duration=response_data.get("load_duration"),
                        prompt_eval_count=response_data.get("prompt_eval_count"),
                        eval_count=response_data.get("eval_count"),
                        success=True
                    )
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = OllamaConnectionError(f"Connection error: {e}")
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
            except json.JSONDecodeError as e:
                last_exception = OllamaAPIError(f"Invalid JSON response: {e}")
                logger.error(f"JSON decode error: {e}")
                break  # Don't retry JSON errors
                
            except OllamaAPIError as e:
                last_exception = e
                logger.error(f"API error: {e}")
                break  # Don't retry API errors
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All retries failed - return error response
        error_msg = str(last_exception) if last_exception else "Unknown error"
        logger.error(f"Failed to generate response after {self.max_retries + 1} attempts: {error_msg}")
        
        return OllamaResponse(
            content="",
            model=model_name,
            success=False,
            error_message=error_msg
        )
    
    async def generate_with_context(
        self,
        prompt: str,
        context_data: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> OllamaResponse:
        """
        Generate response with structured context data
        
        Args:
            prompt: User prompt/question
            context_data: Structured context (e.g., movie data)
            system_prompt: System prompt template
            **kwargs: Additional arguments for generate_response
            
        Returns:
            OllamaResponse object
        """
        # Format context data for inclusion in prompt
        context_str = self._format_context(context_data)
        
        # Combine system prompt with context
        full_system_prompt = system_prompt or "あなたは映画館の案内をするAIアシスタントです。"
        if context_str:
            full_system_prompt += f"\n\n利用可能な映画データ:\n{context_str}"
        
        return await self.generate_response(
            prompt=prompt,
            system_prompt=full_system_prompt,
            **kwargs
        )
    
    def _format_context(self, context_data: Dict[str, Any]) -> str:
        """
        Format context data for LLM consumption
        
        Args:
            context_data: Context dictionary (usually movie database)
            
        Returns:
            Formatted context string
        """
        if not context_data:
            return ""
        
        try:
            # Handle cinema database format
            if 'theaters' in context_data:
                theaters = context_data['theaters']
                context_lines = []
                
                for theater_id, theater_data in theaters.items():
                    theater_name = theater_data.get('name', theater_id)
                    movies = theater_data.get('movies', [])
                    
                    context_lines.append(f"## {theater_name}")
                    
                    for movie in movies:
                        title = movie.get('title', 'Unknown')
                        director = movie.get('director')
                        schedules = movie.get('schedules', [])
                        
                        movie_line = f"- {title}"
                        if director:
                            movie_line += f" (監督: {director})"
                        
                        if schedules:
                            schedule_info = []
                            for schedule in schedules:
                                date = schedule.get('date', '')
                                times = schedule.get('times', [])
                                if date and times:
                                    schedule_info.append(f"{date}: {', '.join(times)}")
                            
                            if schedule_info:
                                movie_line += f" [上映: {'; '.join(schedule_info)}]"
                        
                        context_lines.append(movie_line)
                    
                    context_lines.append("")  # Empty line between theaters
                
                return "\n".join(context_lines)
            
            # Fallback: JSON string
            return json.dumps(context_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.warning(f"Failed to format context: {e}")
            return str(context_data)
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get client configuration information
        
        Returns:
            Dictionary with client settings
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "session_active": self._session is not None and not self._session.closed
        }