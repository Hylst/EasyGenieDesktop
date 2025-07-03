"""Enhanced AI Service Base Class for Phase 2 Development.

This module provides the foundation for advanced AI capabilities including
context management, prompt optimization, and multi-provider support.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import json
import hashlib

from .context_manager import ContextManager
from .prompt_optimizer import PromptOptimizer
from .response_analyzer import ResponseAnalyzer
from .learning_engine import LearningEngine


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ResponseQuality(Enum):
    """Response quality assessment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class UserContext:
    """User context information for personalized AI responses."""
    user_id: str
    preferences: Dict[str, Any]
    history: List[Dict[str, Any]]
    current_session: Dict[str, Any]
    timezone: str
    language: str = "en"
    expertise_level: str = "intermediate"
    

@dataclass
class AIRequest:
    """Structured AI request with context and metadata."""
    prompt: str
    context: UserContext
    tool_name: str
    operation: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 30
    require_explanation: bool = False
    

@dataclass
class AIResponse:
    """Structured AI response with metadata and quality metrics."""
    content: str
    confidence: float
    quality: ResponseQuality
    processing_time: float
    provider: AIProvider
    tokens_used: int
    explanation: Optional[str] = None
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None
    

@dataclass
class CacheEntry:
    """Cache entry for AI responses."""
    request_hash: str
    response: AIResponse
    timestamp: datetime
    access_count: int = 0
    last_accessed: datetime = None
    

class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class ProviderError(AIServiceError):
    """Exception for AI provider-specific errors."""
    pass


class RateLimitError(AIServiceError):
    """Exception for rate limiting errors."""
    pass


class BaseAIService(ABC):
    """Enhanced base AI service with advanced capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the AI service with configuration.
        
        Args:
            config: Service configuration including API keys, settings, etc.
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize core components
        self.context_manager = ContextManager()
        self.prompt_optimizer = PromptOptimizer()
        self.response_analyzer = ResponseAnalyzer()
        self.learning_engine = LearningEngine()
        
        # Cache and performance tracking
        self.response_cache: Dict[str, CacheEntry] = {}
        self.performance_metrics: Dict[str, List[float]] = {
            "response_times": [],
            "token_usage": [],
            "cache_hit_rate": []
        }
        
        # Rate limiting
        self.request_timestamps: List[datetime] = []
        self.max_requests_per_minute = config.get("max_requests_per_minute", 60)
        
        # Provider management
        self.primary_provider = AIProvider(config.get("primary_provider", "openai"))
        self.fallback_providers = [AIProvider(p) for p in config.get("fallback_providers", [])]
        self.provider_instances: Dict[AIProvider, Any] = {}
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AI provider instances."""
        try:
            # Import and initialize providers based on configuration
            if self.primary_provider == AIProvider.OPENAI:
                from .providers.openai_provider import OpenAIProvider
                self.provider_instances[AIProvider.OPENAI] = OpenAIProvider(self.config)
            
            if self.primary_provider == AIProvider.ANTHROPIC:
                from .providers.anthropic_provider import AnthropicProvider
                self.provider_instances[AIProvider.ANTHROPIC] = AnthropicProvider(self.config)
            
            # Initialize fallback providers
            for provider in self.fallback_providers:
                if provider not in self.provider_instances:
                    if provider == AIProvider.OPENAI:
                        from .providers.openai_provider import OpenAIProvider
                        self.provider_instances[provider] = OpenAIProvider(self.config)
                    elif provider == AIProvider.ANTHROPIC:
                        from .providers.anthropic_provider import AnthropicProvider
                        self.provider_instances[provider] = AnthropicProvider(self.config)
                        
        except ImportError as e:
            self.logger.warning(f"Failed to initialize some AI providers: {e}")
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process an AI request with full pipeline.
        
        Args:
            request: The AI request to process
            
        Returns:
            AIResponse: The processed response with metadata
            
        Raises:
            AIServiceError: If processing fails
        """
        start_time = datetime.now()
        
        try:
            # Check rate limiting
            await self._check_rate_limit()
            
            # Generate request hash for caching
            request_hash = self._generate_request_hash(request)
            
            # Check cache first
            cached_response = self._get_cached_response(request_hash)
            if cached_response:
                self.logger.debug(f"Cache hit for request: {request.operation}")
                return cached_response
            
            # Optimize prompt using context and user preferences
            optimized_prompt = await self.prompt_optimizer.optimize(
                request.prompt,
                request.context,
                request.tool_name,
                request.operation
            )
            
            # Process with primary provider
            response = await self._process_with_provider(
                self.primary_provider,
                optimized_prompt,
                request
            )
            
            # Analyze response quality
            quality_assessment = await self.response_analyzer.analyze(
                response,
                request
            )
            response.quality = quality_assessment.quality
            response.confidence = quality_assessment.confidence
            
            # Cache the response
            self._cache_response(request_hash, response)
            
            # Update learning engine
            await self.learning_engine.update_from_interaction(
                request,
                response,
                quality_assessment
            )
            
            # Update performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            response.processing_time = processing_time
            self._update_performance_metrics(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing AI request: {e}")
            
            # Try fallback providers
            for fallback_provider in self.fallback_providers:
                try:
                    self.logger.info(f"Trying fallback provider: {fallback_provider}")
                    response = await self._process_with_provider(
                        fallback_provider,
                        request.prompt,
                        request
                    )
                    response.provider = fallback_provider
                    return response
                except Exception as fallback_error:
                    self.logger.warning(f"Fallback provider {fallback_provider} failed: {fallback_error}")
                    continue
            
            # If all providers fail, raise the original error
            raise AIServiceError(f"All AI providers failed: {e}")
    
    async def _process_with_provider(
        self,
        provider: AIProvider,
        prompt: str,
        request: AIRequest
    ) -> AIResponse:
        """Process request with specific provider.
        
        Args:
            provider: The AI provider to use
            prompt: The optimized prompt
            request: The original request
            
        Returns:
            AIResponse: The provider response
        """
        if provider not in self.provider_instances:
            raise ProviderError(f"Provider {provider} not available")
        
        provider_instance = self.provider_instances[provider]
        
        # Call provider-specific processing
        response = await provider_instance.generate_response(
            prompt,
            request.parameters,
            request.timeout
        )
        
        return AIResponse(
            content=response["content"],
            confidence=response.get("confidence", 0.8),
            quality=ResponseQuality.GOOD,  # Will be updated by analyzer
            processing_time=0.0,  # Will be updated
            provider=provider,
            tokens_used=response.get("tokens_used", 0),
            explanation=response.get("explanation"),
            suggestions=response.get("suggestions", []),
            metadata=response.get("metadata", {})
        )
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < timedelta(minutes=1)
        ]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            raise RateLimitError("Rate limit exceeded")
        
        # Add current timestamp
        self.request_timestamps.append(now)
    
    def _generate_request_hash(self, request: AIRequest) -> str:
        """Generate a hash for request caching.
        
        Args:
            request: The AI request
            
        Returns:
            str: The request hash
        """
        # Create a string representation of the request for hashing
        request_data = {
            "prompt": request.prompt,
            "tool_name": request.tool_name,
            "operation": request.operation,
            "parameters": request.parameters,
            "user_preferences": request.context.preferences
        }
        
        request_string = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_string.encode()).hexdigest()
    
    def _get_cached_response(self, request_hash: str) -> Optional[AIResponse]:
        """Get cached response if available and valid.
        
        Args:
            request_hash: The request hash
            
        Returns:
            Optional[AIResponse]: Cached response if available
        """
        if request_hash not in self.response_cache:
            return None
        
        cache_entry = self.response_cache[request_hash]
        
        # Check if cache entry is still valid (e.g., not older than 1 hour)
        cache_ttl = timedelta(hours=1)
        if datetime.now() - cache_entry.timestamp > cache_ttl:
            del self.response_cache[request_hash]
            return None
        
        # Update access statistics
        cache_entry.access_count += 1
        cache_entry.last_accessed = datetime.now()
        
        return cache_entry.response
    
    def _cache_response(self, request_hash: str, response: AIResponse):
        """Cache an AI response.
        
        Args:
            request_hash: The request hash
            response: The response to cache
        """
        cache_entry = CacheEntry(
            request_hash=request_hash,
            response=response,
            timestamp=datetime.now(),
            last_accessed=datetime.now()
        )
        
        self.response_cache[request_hash] = cache_entry
        
        # Implement cache size limit (keep only 1000 most recent entries)
        if len(self.response_cache) > 1000:
            # Remove oldest entries
            sorted_entries = sorted(
                self.response_cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            # Keep only the 800 most recent entries
            entries_to_keep = dict(sorted_entries[-800:])
            self.response_cache = entries_to_keep
    
    def _update_performance_metrics(self, response: AIResponse):
        """Update performance tracking metrics.
        
        Args:
            response: The AI response with timing information
        """
        self.performance_metrics["response_times"].append(response.processing_time)
        self.performance_metrics["token_usage"].append(response.tokens_used)
        
        # Calculate cache hit rate
        total_requests = len(self.performance_metrics["response_times"])
        cache_hits = sum(1 for entry in self.response_cache.values() if entry.access_count > 0)
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        self.performance_metrics["cache_hit_rate"].append(cache_hit_rate)
        
        # Keep only last 1000 metrics
        for metric_list in self.performance_metrics.values():
            if len(metric_list) > 1000:
                metric_list[:] = metric_list[-1000:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics.
        
        Returns:
            Dict[str, Any]: Performance statistics
        """
        stats = {}
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                stats[metric_name] = {
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
            else:
                stats[metric_name] = {
                    "average": 0,
                    "min": 0,
                    "max": 0,
                    "count": 0
                }
        
        stats["cache_size"] = len(self.response_cache)
        stats["active_providers"] = list(self.provider_instances.keys())
        
        return stats
    
    def clear_cache(self):
        """Clear the response cache."""
        self.response_cache.clear()
        self.logger.info("Response cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers.
        
        Returns:
            Dict[str, Any]: Health status of all providers
        """
        health_status = {
            "overall": "healthy",
            "providers": {},
            "performance": self.get_performance_stats()
        }
        
        for provider, instance in self.provider_instances.items():
            try:
                # Simple health check request
                test_response = await instance.health_check()
                health_status["providers"][provider.value] = {
                    "status": "healthy",
                    "response_time": test_response.get("response_time", 0),
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_status["providers"][provider.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                health_status["overall"] = "degraded"
        
        return health_status
    
    @abstractmethod
    async def analyze_task_complexity(self, task_description: str, context: UserContext) -> TaskComplexity:
        """Analyze the complexity of a task.
        
        Args:
            task_description: Description of the task
            context: User context for personalized analysis
            
        Returns:
            TaskComplexity: The assessed complexity level
        """
        pass
    
    @abstractmethod
    async def generate_contextual_suggestions(
        self,
        input_text: str,
        context: UserContext,
        suggestion_type: str
    ) -> List[str]:
        """Generate contextual suggestions based on input and user context.
        
        Args:
            input_text: The input text to analyze
            context: User context for personalization
            suggestion_type: Type of suggestions to generate
            
        Returns:
            List[str]: Generated suggestions
        """
        pass
    
    @abstractmethod
    async def extract_insights(
        self,
        data: Dict[str, Any],
        context: UserContext
    ) -> Dict[str, Any]:
        """Extract insights from user data.
        
        Args:
            data: User data to analyze
            context: User context for personalized insights
            
        Returns:
            Dict[str, Any]: Extracted insights and recommendations
        """
        pass