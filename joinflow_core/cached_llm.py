"""
Cached LLM Wrapper
==================

Wraps LLM calls with vector-based caching to reduce token consumption.
Similar queries will return cached responses instead of calling the LLM.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    from_cache: bool = False
    latency_ms: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "from_cache": self.from_cache,
            "latency_ms": self.latency_ms
        }


class CachedLLM:
    """
    LLM wrapper with vector-based response caching.
    
    Significantly reduces token consumption by:
    1. Caching responses for similar queries
    2. Using semantic similarity to find cached responses
    3. Tracking token usage and savings
    
    Example:
        ```python
        from joinflow_core.cached_llm import CachedLLM
        
        # Wrap your LLM function
        cached_llm = CachedLLM(your_llm_function)
        
        # First call - hits LLM
        response = cached_llm("What is Python?")
        
        # Similar call - returns cached response
        response = cached_llm("Tell me about Python")  # Cache hit!
        ```
    """
    
    def __init__(
        self,
        llm_func: Callable[[str], str],
        model_name: str = "default",
        cache_enabled: bool = True,
        similarity_threshold: float = 0.92,
        estimate_tokens: bool = True
    ):
        """
        Initialize cached LLM.
        
        Args:
            llm_func: The underlying LLM function (query -> response)
            model_name: Model identifier for cache separation
            cache_enabled: Enable/disable caching
            similarity_threshold: Minimum similarity for cache hits (0.0-1.0)
            estimate_tokens: Estimate token counts if not provided
        """
        self.llm_func = llm_func
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        self.similarity_threshold = similarity_threshold
        self.estimate_tokens = estimate_tokens
        
        # Get Qdrant service
        self._qdrant_service = None
        self._init_service()
    
    def _init_service(self):
        """Initialize Qdrant service"""
        try:
            from joinflow_core.qdrant_service import get_qdrant_service
            self._qdrant_service = get_qdrant_service()
        except Exception as e:
            logger.warning(f"Qdrant service not available: {e}")
            self._qdrant_service = None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        if not text:
            return 0
        # Rough estimate: 1 token ≈ 4 characters for English, 2 for Chinese
        chars = len(text)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = chars - chinese_chars
        return int(english_chars / 4 + chinese_chars / 2)
    
    def __call__(
        self,
        prompt: str,
        system_prompt: str = None,
        **kwargs
    ) -> LLMResponse:
        """
        Call the LLM with caching.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional arguments for the LLM
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        # Combine prompts for cache key
        cache_key = f"{system_prompt or ''}|{prompt}"
        
        # Try to get cached response
        if self.cache_enabled and self._qdrant_service:
            cached = self._qdrant_service.get_cached_response(
                query=cache_key,
                model=self.model_name,
                similarity_threshold=self.similarity_threshold
            )
            
            if cached:
                response_text, tokens_saved = cached
                latency = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    content=response_text,
                    model=self.model_name,
                    prompt_tokens=self._estimate_tokens(prompt) if self.estimate_tokens else 0,
                    completion_tokens=self._estimate_tokens(response_text) if self.estimate_tokens else 0,
                    total_tokens=tokens_saved,
                    from_cache=True,
                    latency_ms=latency
                )
        
        # Call the actual LLM
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response_text = self.llm_func(full_prompt, **kwargs)
            
            # Estimate tokens
            prompt_tokens = self._estimate_tokens(full_prompt) if self.estimate_tokens else 0
            completion_tokens = self._estimate_tokens(response_text) if self.estimate_tokens else 0
            
            # Cache the response
            if self.cache_enabled and self._qdrant_service:
                self._qdrant_service.cache_response(
                    query=cache_key,
                    response=response_text,
                    model=self.model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )
            
            latency = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response_text,
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                from_cache=False,
                latency_ms=latency
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def query(self, prompt: str, **kwargs) -> str:
        """Simple query interface returning just the response text"""
        response = self(prompt, **kwargs)
        return response.content
    
    def get_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        if self._qdrant_service:
            return self._qdrant_service.get_token_stats()
        return {}
    
    def clear_cache(self, older_than_days: int = None) -> int:
        """Clear cache entries"""
        if self._qdrant_service:
            return self._qdrant_service.clear_cache(older_than_days)
        return 0


def cached_llm_call(
    model_name: str = "default",
    similarity_threshold: float = 0.92,
    cache_enabled: bool = True
):
    """
    Decorator to add caching to any LLM function.
    
    Example:
        ```python
        @cached_llm_call(model_name="gpt-4")
        def my_llm(prompt: str) -> str:
            # Your LLM call here
            return openai.chat(prompt)
        ```
    """
    def decorator(func: Callable):
        cached = CachedLLM(
            func,
            model_name=model_name,
            similarity_threshold=similarity_threshold,
            cache_enabled=cache_enabled
        )
        
        @wraps(func)
        def wrapper(prompt: str, **kwargs) -> str:
            response = cached(prompt, **kwargs)
            return response.content
        
        # Attach stats method
        wrapper.get_stats = cached.get_stats
        wrapper.clear_cache = cached.clear_cache
        wrapper.cached_call = cached
        
        return wrapper
    
    return decorator


class SmartLLMRouter:
    """
    Intelligent LLM router with caching and fallback.
    
    Features:
    - Routes queries to appropriate models based on complexity
    - Uses caching aggressively for simple queries
    - Falls back to cheaper models when appropriate
    """
    
    def __init__(
        self,
        primary_llm: Callable,
        fallback_llm: Callable = None,
        complexity_threshold: int = 100  # Character count threshold
    ):
        self.primary = CachedLLM(primary_llm, model_name="primary", similarity_threshold=0.90)
        self.fallback = CachedLLM(fallback_llm, model_name="fallback", similarity_threshold=0.95) if fallback_llm else None
        self.complexity_threshold = complexity_threshold
    
    def __call__(self, prompt: str, **kwargs) -> LLMResponse:
        """Route query to appropriate model"""
        # Use fallback for simple queries
        if self.fallback and len(prompt) < self.complexity_threshold:
            try:
                response = self.fallback(prompt, **kwargs)
                if response.content:
                    return response
            except Exception:
                pass
        
        # Use primary for complex queries
        return self.primary(prompt, **kwargs)
    
    def get_combined_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all models"""
        stats = {
            "primary": self.primary.get_stats(),
        }
        if self.fallback:
            stats["fallback"] = self.fallback.get_stats()
        return stats

