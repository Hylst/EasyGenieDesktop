"""Advanced AI Service for Phase 2.

This module provides enhanced AI capabilities including context-aware responses,
prompt optimization, response analysis, and multi-provider support.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .base_service import BaseAIService, AIRequest, AIResponse, AIProvider, ResponseQuality
from .context_manager import ContextManager, UserSession, ContextType
from .prompt_optimizer import PromptOptimizer, OptimizationStrategy
from .response_analyzer import ResponseAnalyzer, QualityAssessment


class AIMode(Enum):
    """AI operation modes."""
    MAGIC = "magic"  # Simple, fast responses
    GENIE = "genie"  # Advanced, context-aware responses
    HYBRID = "hybrid"  # Adaptive mode selection


class LearningMode(Enum):
    """Learning and adaptation modes."""
    PASSIVE = "passive"  # Learn from interactions but don't adapt
    ACTIVE = "active"  # Actively adapt based on feedback
    AGGRESSIVE = "aggressive"  # Rapid adaptation with experimentation


@dataclass
class AdvancedAIRequest:
    """Enhanced AI request with additional context and preferences."""
    # Base request information
    prompt: str
    tool_name: str
    operation: str
    user_id: str
    
    # Enhanced features
    mode: AIMode = AIMode.MAGIC
    preferred_provider: Optional[AIProvider] = None
    context_scope: List[ContextType] = None
    optimization_strategies: List[OptimizationStrategy] = None
    quality_requirements: Dict[str, float] = None
    
    # User preferences
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    response_format: Optional[str] = None
    language: str = "en"
    
    # Session information
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # Metadata
    priority: int = 1  # 1-5, 1 being highest
    timeout: Optional[float] = None
    retry_count: int = 3
    
    def __post_init__(self):
        """Initialize default values."""
        if self.context_scope is None:
            self.context_scope = [ContextType.CURRENT_TOOL, ContextType.USER_PREFERENCES]
        
        if self.optimization_strategies is None:
            if self.mode == AIMode.GENIE:
                self.optimization_strategies = [
                    OptimizationStrategy.CONTEXT_INJECTION,
                    OptimizationStrategy.PERSONA_ADAPTATION,
                    OptimizationStrategy.EXAMPLE_ENHANCEMENT
                ]
            else:
                self.optimization_strategies = [OptimizationStrategy.BASIC_FORMATTING]
        
        if self.quality_requirements is None:
            if self.mode == AIMode.GENIE:
                self.quality_requirements = {
                    "relevance": 0.8,
                    "completeness": 0.7,
                    "clarity": 0.8
                }
            else:
                self.quality_requirements = {
                    "relevance": 0.6,
                    "clarity": 0.6
                }


@dataclass
class AdvancedAIResponse:
    """Enhanced AI response with quality assessment and metadata."""
    # Base response
    content: str
    provider: AIProvider
    tokens_used: int
    processing_time: float
    
    # Quality assessment
    quality_assessment: Optional[QualityAssessment] = None
    meets_requirements: bool = True
    
    # Enhanced metadata
    optimization_applied: List[OptimizationStrategy] = None
    context_used: List[ContextType] = None
    confidence_score: float = 0.8
    
    # Learning data
    feedback_score: Optional[float] = None
    user_satisfaction: Optional[int] = None  # 1-5 scale
    
    # Performance metrics
    cache_hit: bool = False
    retry_count: int = 0
    fallback_used: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.optimization_applied is None:
            self.optimization_applied = []
        if self.context_used is None:
            self.context_used = []


class AdvancedAIService:
    """Advanced AI service with enhanced capabilities for Phase 2."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the advanced AI service.
        
        Args:
            config: Service configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize core components
        self.base_service = BaseAIService()
        self.context_manager = ContextManager()
        self.prompt_optimizer = PromptOptimizer()
        self.response_analyzer = ResponseAnalyzer()
        
        # Service configuration
        self.learning_mode = LearningMode(self.config.get("learning_mode", "active"))
        self.default_mode = AIMode(self.config.get("default_mode", "magic"))
        self.quality_threshold = self.config.get("quality_threshold", 0.6)
        self.max_retries = self.config.get("max_retries", 3)
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "average_quality_score": 0.0,
            "cache_hit_rate": 0.0,
            "provider_usage": {provider.value: 0 for provider in AIProvider},
            "mode_usage": {mode.value: 0 for mode in AIMode}
        }
        
        # Active sessions
        self.active_sessions: Dict[str, UserSession] = {}
        
        # Provider health monitoring
        self.provider_health = {provider: True for provider in AIProvider}
        self.last_health_check = datetime.now()
        
        # Learning and adaptation
        self.adaptation_data = {
            "successful_patterns": {},
            "failed_patterns": {},
            "user_preferences": {},
            "quality_trends": []
        }
    
    async def process_request(self, request: AdvancedAIRequest) -> AdvancedAIResponse:
        """Process an advanced AI request with full enhancement pipeline.
        
        Args:
            request: Enhanced AI request
            
        Returns:
            AdvancedAIResponse: Enhanced AI response
        """
        start_time = datetime.now()
        
        try:
            # Update metrics
            self.performance_metrics["total_requests"] += 1
            self.performance_metrics["mode_usage"][request.mode.value] += 1
            
            # Start or get user session
            session = await self._get_or_create_session(request)
            
            # Determine optimal provider
            provider = await self._select_provider(request)
            
            # Build context for the request
            context = await self._build_request_context(request, session)
            
            # Optimize the prompt
            optimized_prompt, optimization_metadata = await self._optimize_prompt(
                request, context
            )
            
            # Check cache first
            cached_response = await self._check_cache(optimized_prompt, provider)
            if cached_response:
                return await self._enhance_cached_response(cached_response, request)
            
            # Create base AI request
            base_request = AIRequest(
                prompt=optimized_prompt,
                tool_name=request.tool_name,
                operation=request.operation,
                user_id=request.user_id,
                provider=provider,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                context=context
            )
            
            # Process with base service
            base_response = await self.base_service.process_request(base_request)
            
            # Analyze response quality
            quality_assessment = await self.response_analyzer.analyze(
                base_response, base_request
            )
            
            # Check if response meets requirements
            meets_requirements = self._check_quality_requirements(
                quality_assessment, request.quality_requirements
            )
            
            # Retry if quality is insufficient
            retry_count = 0
            while not meets_requirements and retry_count < request.retry_count:
                retry_count += 1
                self.logger.info(f"Retrying request due to quality issues (attempt {retry_count})")
                
                # Try different provider or optimization strategy
                if retry_count == 1:
                    provider = await self._select_fallback_provider(provider)
                elif retry_count == 2:
                    # Add more aggressive optimization
                    request.optimization_strategies.append(OptimizationStrategy.CHAIN_OF_THOUGHT)
                    optimized_prompt, optimization_metadata = await self._optimize_prompt(
                        request, context
                    )
                
                base_request.provider = provider
                base_request.prompt = optimized_prompt
                base_response = await self.base_service.process_request(base_request)
                quality_assessment = await self.response_analyzer.analyze(
                    base_response, base_request
                )
                meets_requirements = self._check_quality_requirements(
                    quality_assessment, request.quality_requirements
                )
            
            # Create enhanced response
            enhanced_response = AdvancedAIResponse(
                content=base_response.content,
                provider=base_response.provider,
                tokens_used=base_response.tokens_used,
                processing_time=(datetime.now() - start_time).total_seconds(),
                quality_assessment=quality_assessment,
                meets_requirements=meets_requirements,
                optimization_applied=request.optimization_strategies,
                context_used=request.context_scope,
                confidence_score=quality_assessment.confidence,
                retry_count=retry_count,
                fallback_used=retry_count > 0
            )
            
            # Update session context
            await self._update_session_context(session, request, enhanced_response)
            
            # Cache successful response
            if meets_requirements:
                await self._cache_response(optimized_prompt, enhanced_response)
            
            # Learn from interaction
            await self._learn_from_interaction(request, enhanced_response)
            
            # Update performance metrics
            self._update_performance_metrics(enhanced_response)
            
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Error processing advanced AI request: {e}")
            self.performance_metrics["failed_requests"] += 1
            
            # Return fallback response
            return AdvancedAIResponse(
                content=f"I apologize, but I encountered an error processing your request. Please try again.",
                provider=AIProvider.OPENAI,  # Default fallback
                tokens_used=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                meets_requirements=False,
                confidence_score=0.1,
                retry_count=0,
                fallback_used=True
            )
    
    async def _get_or_create_session(self, request: AdvancedAIRequest) -> UserSession:
        """Get existing session or create new one.
        
        Args:
            request: AI request
            
        Returns:
            UserSession: User session
        """
        session_id = request.session_id or f"{request.user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Create new session
        session = await self.context_manager.start_session(
            user_id=request.user_id,
            session_id=session_id
        )
        
        self.active_sessions[session_id] = session
        return session
    
    async def _select_provider(self, request: AdvancedAIRequest) -> AIProvider:
        """Select optimal AI provider for the request.
        
        Args:
            request: AI request
            
        Returns:
            AIProvider: Selected provider
        """
        # Use preferred provider if specified and healthy
        if request.preferred_provider and self.provider_health.get(request.preferred_provider, False):
            return request.preferred_provider
        
        # Select based on mode and tool requirements
        if request.mode == AIMode.GENIE:
            # For Genie mode, prefer more capable providers
            for provider in [AIProvider.ANTHROPIC, AIProvider.OPENAI, AIProvider.GEMINI]:
                if self.provider_health.get(provider, False):
                    return provider
        else:
            # For Magic mode, prefer faster providers
            for provider in [AIProvider.OPENAI, AIProvider.GEMINI, AIProvider.ANTHROPIC]:
                if self.provider_health.get(provider, False):
                    return provider
        
        # Fallback to any available provider
        for provider, is_healthy in self.provider_health.items():
            if is_healthy:
                return provider
        
        # Last resort
        return AIProvider.OPENAI
    
    async def _select_fallback_provider(self, current_provider: AIProvider) -> AIProvider:
        """Select fallback provider different from current.
        
        Args:
            current_provider: Current provider
            
        Returns:
            AIProvider: Fallback provider
        """
        available_providers = [
            provider for provider, is_healthy in self.provider_health.items()
            if is_healthy and provider != current_provider
        ]
        
        if available_providers:
            return available_providers[0]
        
        return current_provider  # No alternative available
    
    async def _build_request_context(self, request: AdvancedAIRequest, session: UserSession) -> Dict[str, Any]:
        """Build comprehensive context for the request.
        
        Args:
            request: AI request
            session: User session
            
        Returns:
            Dict[str, Any]: Request context
        """
        context = {}
        
        for context_type in request.context_scope:
            if context_type == ContextType.USER_PREFERENCES:
                user_prefs = await self.context_manager.get_user_preferences(request.user_id)
                context["user_preferences"] = user_prefs
            
            elif context_type == ContextType.CONVERSATION_HISTORY:
                history = await self.context_manager.get_conversation_history(
                    session.session_id, limit=10
                )
                context["conversation_history"] = [turn.to_dict() for turn in history]
            
            elif context_type == ContextType.CURRENT_TOOL:
                tool_context = await self.context_manager.get_relevant_context(
                    request.user_id, context_type, {"tool_name": request.tool_name}
                )
                context["tool_context"] = [entry.to_dict() for entry in tool_context]
            
            elif context_type == ContextType.RECENT_ACTIVITY:
                recent_context = await self.context_manager.get_relevant_context(
                    request.user_id, context_type, {"hours": 24}
                )
                context["recent_activity"] = [entry.to_dict() for entry in recent_context]
        
        return context
    
    async def _optimize_prompt(self, request: AdvancedAIRequest, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Optimize the prompt using available strategies.
        
        Args:
            request: AI request
            context: Request context
            
        Returns:
            Tuple[str, Dict[str, Any]]: Optimized prompt and metadata
        """
        optimization_result = await self.prompt_optimizer.optimize_prompt(
            prompt=request.prompt,
            tool_name=request.tool_name,
            operation=request.operation,
            user_context=context,
            strategies=request.optimization_strategies,
            language=request.language
        )
        
        return optimization_result.optimized_prompt, {
            "strategies_applied": optimization_result.strategies_applied,
            "confidence_score": optimization_result.confidence_score,
            "estimated_tokens": optimization_result.estimated_tokens
        }
    
    async def _check_cache(self, prompt: str, provider: AIProvider) -> Optional[AdvancedAIResponse]:
        """Check if response is cached.
        
        Args:
            prompt: Optimized prompt
            provider: AI provider
            
        Returns:
            Optional[AdvancedAIResponse]: Cached response if available
        """
        # This would integrate with the base service cache
        # For now, return None (no cache hit)
        return None
    
    async def _enhance_cached_response(self, cached_response: Any, request: AdvancedAIRequest) -> AdvancedAIResponse:
        """Enhance cached response with current request context.
        
        Args:
            cached_response: Cached response
            request: Current request
            
        Returns:
            AdvancedAIResponse: Enhanced cached response
        """
        # Convert cached response to enhanced format
        return AdvancedAIResponse(
            content=cached_response.content,
            provider=cached_response.provider,
            tokens_used=0,  # No tokens used for cached response
            processing_time=0.1,  # Minimal processing time
            cache_hit=True,
            meets_requirements=True,
            confidence_score=0.9  # High confidence for cached responses
        )
    
    def _check_quality_requirements(self, assessment: QualityAssessment, requirements: Dict[str, float]) -> bool:
        """Check if response meets quality requirements.
        
        Args:
            assessment: Quality assessment
            requirements: Quality requirements
            
        Returns:
            bool: True if requirements are met
        """
        for metric_name, required_score in requirements.items():
            # Map requirement names to assessment metrics
            if metric_name == "relevance" and assessment.metric_scores.get("relevance", 0) < required_score:
                return False
            elif metric_name == "completeness" and assessment.metric_scores.get("completeness", 0) < required_score:
                return False
            elif metric_name == "clarity" and assessment.metric_scores.get("clarity", 0) < required_score:
                return False
        
        # Also check overall score
        return assessment.overall_score >= self.quality_threshold
    
    async def _update_session_context(self, session: UserSession, request: AdvancedAIRequest, response: AdvancedAIResponse):
        """Update session context with new interaction.
        
        Args:
            session: User session
            request: AI request
            response: AI response
        """
        # Add conversation turn
        await self.context_manager.add_conversation_turn(
            session_id=session.session_id,
            user_message=request.prompt,
            assistant_message=response.content,
            metadata={
                "tool_name": request.tool_name,
                "operation": request.operation,
                "quality_score": response.quality_assessment.overall_score if response.quality_assessment else 0.5,
                "provider": response.provider.value
            }
        )
        
        # Add context entry for tool usage
        await self.context_manager.add_context(
            user_id=request.user_id,
            context_type=ContextType.CURRENT_TOOL,
            content={
                "tool_name": request.tool_name,
                "operation": request.operation,
                "success": response.meets_requirements,
                "quality_score": response.quality_assessment.overall_score if response.quality_assessment else 0.5
            },
            metadata={
                "session_id": session.session_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _cache_response(self, prompt: str, response: AdvancedAIResponse):
        """Cache successful response.
        
        Args:
            prompt: Optimized prompt
            response: AI response
        """
        # This would integrate with the base service cache
        # Implementation depends on caching strategy
        pass
    
    async def _learn_from_interaction(self, request: AdvancedAIRequest, response: AdvancedAIResponse):
        """Learn from the interaction for future improvements.
        
        Args:
            request: AI request
            response: AI response
        """
        if self.learning_mode == LearningMode.PASSIVE:
            return
        
        # Record successful patterns
        if response.meets_requirements and response.quality_assessment:
            pattern_key = f"{request.tool_name}_{request.operation}_{request.mode.value}"
            
            if pattern_key not in self.adaptation_data["successful_patterns"]:
                self.adaptation_data["successful_patterns"][pattern_key] = {
                    "count": 0,
                    "avg_quality": 0.0,
                    "best_strategies": [],
                    "preferred_provider": None
                }
            
            pattern = self.adaptation_data["successful_patterns"][pattern_key]
            pattern["count"] += 1
            
            # Update average quality
            current_avg = pattern["avg_quality"]
            new_quality = response.quality_assessment.overall_score
            pattern["avg_quality"] = ((current_avg * (pattern["count"] - 1)) + new_quality) / pattern["count"]
            
            # Track successful strategies
            for strategy in response.optimization_applied:
                if strategy.value not in pattern["best_strategies"]:
                    pattern["best_strategies"].append(strategy.value)
            
            # Track preferred provider
            pattern["preferred_provider"] = response.provider.value
        
        # Record quality trends
        if response.quality_assessment:
            self.adaptation_data["quality_trends"].append({
                "timestamp": datetime.now().isoformat(),
                "tool": request.tool_name,
                "mode": request.mode.value,
                "quality_score": response.quality_assessment.overall_score,
                "provider": response.provider.value
            })
            
            # Keep only recent trends (last 1000 interactions)
            if len(self.adaptation_data["quality_trends"]) > 1000:
                self.adaptation_data["quality_trends"] = self.adaptation_data["quality_trends"][-1000:]
    
    def _update_performance_metrics(self, response: AdvancedAIResponse):
        """Update performance metrics.
        
        Args:
            response: AI response
        """
        if response.meets_requirements:
            self.performance_metrics["successful_requests"] += 1
        
        # Update provider usage
        self.performance_metrics["provider_usage"][response.provider.value] += 1
        
        # Update average response time
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        new_avg = ((current_avg * (total_requests - 1)) + response.processing_time) / total_requests
        self.performance_metrics["average_response_time"] = new_avg
        
        # Update average quality score
        if response.quality_assessment:
            current_avg = self.performance_metrics["average_quality_score"]
            new_quality = response.quality_assessment.overall_score
            new_avg = ((current_avg * (total_requests - 1)) + new_quality) / total_requests
            self.performance_metrics["average_quality_score"] = new_avg
        
        # Update cache hit rate
        if response.cache_hit:
            cache_hits = sum(1 for _ in range(total_requests) if response.cache_hit)  # Simplified
            self.performance_metrics["cache_hit_rate"] = cache_hits / total_requests
    
    async def provide_feedback(self, response_id: str, feedback_score: float, user_satisfaction: int):
        """Provide feedback on a response for learning.
        
        Args:
            response_id: Response identifier
            feedback_score: Feedback score (0.0 to 1.0)
            user_satisfaction: User satisfaction (1-5)
        """
        # This would update the learning system with user feedback
        # Implementation depends on how responses are tracked
        pass
    
    async def get_recommendations(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """Get AI recommendations for improving user experience.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            Dict[str, Any]: Recommendations
        """
        recommendations = {
            "mode_suggestion": self._suggest_optimal_mode(user_id, tool_name),
            "provider_suggestion": self._suggest_optimal_provider(user_id, tool_name),
            "optimization_suggestions": self._suggest_optimization_strategies(user_id, tool_name),
            "quality_insights": await self._get_quality_insights(user_id, tool_name)
        }
        
        return recommendations
    
    def _suggest_optimal_mode(self, user_id: str, tool_name: str) -> str:
        """Suggest optimal AI mode for user and tool.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            str: Suggested mode
        """
        # Analyze user's historical success with different modes
        pattern_key = f"{tool_name}_*_{AIMode.GENIE.value}"
        genie_success = self.adaptation_data["successful_patterns"].get(pattern_key, {}).get("avg_quality", 0.5)
        
        pattern_key = f"{tool_name}_*_{AIMode.MAGIC.value}"
        magic_success = self.adaptation_data["successful_patterns"].get(pattern_key, {}).get("avg_quality", 0.5)
        
        if genie_success > magic_success + 0.1:
            return AIMode.GENIE.value
        elif magic_success > genie_success + 0.1:
            return AIMode.MAGIC.value
        else:
            return AIMode.HYBRID.value
    
    def _suggest_optimal_provider(self, user_id: str, tool_name: str) -> str:
        """Suggest optimal provider for user and tool.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            str: Suggested provider
        """
        # Find most successful provider for this tool
        best_provider = None
        best_quality = 0.0
        
        for pattern_key, pattern_data in self.adaptation_data["successful_patterns"].items():
            if tool_name in pattern_key:
                if pattern_data["avg_quality"] > best_quality:
                    best_quality = pattern_data["avg_quality"]
                    best_provider = pattern_data.get("preferred_provider")
        
        return best_provider or AIProvider.OPENAI.value
    
    def _suggest_optimization_strategies(self, user_id: str, tool_name: str) -> List[str]:
        """Suggest optimization strategies for user and tool.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            List[str]: Suggested strategies
        """
        # Find most successful strategies for this tool
        successful_strategies = set()
        
        for pattern_key, pattern_data in self.adaptation_data["successful_patterns"].items():
            if tool_name in pattern_key:
                successful_strategies.update(pattern_data.get("best_strategies", []))
        
        return list(successful_strategies)
    
    async def _get_quality_insights(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """Get quality insights for user and tool.
        
        Args:
            user_id: User identifier
            tool_name: Tool name
            
        Returns:
            Dict[str, Any]: Quality insights
        """
        # Analyze quality trends for this tool
        tool_trends = [
            trend for trend in self.adaptation_data["quality_trends"]
            if trend["tool"] == tool_name
        ]
        
        if not tool_trends:
            return {"message": "No quality data available yet"}
        
        avg_quality = sum(trend["quality_score"] for trend in tool_trends) / len(tool_trends)
        recent_trends = tool_trends[-10:]  # Last 10 interactions
        recent_avg = sum(trend["quality_score"] for trend in recent_trends) / len(recent_trends)
        
        return {
            "average_quality": avg_quality,
            "recent_quality": recent_avg,
            "trend": "improving" if recent_avg > avg_quality else "declining" if recent_avg < avg_quality else "stable",
            "total_interactions": len(tool_trends)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service.
        
        Returns:
            Dict[str, Any]: Health status
        """
        # Check provider health
        for provider in AIProvider:
            try:
                is_healthy = await self.base_service.health_check(provider)
                self.provider_health[provider] = is_healthy
            except Exception as e:
                self.logger.error(f"Health check failed for {provider.value}: {e}")
                self.provider_health[provider] = False
        
        self.last_health_check = datetime.now()
        
        return {
            "status": "healthy" if any(self.provider_health.values()) else "unhealthy",
            "providers": {provider.value: status for provider, status in self.provider_health.items()},
            "last_check": self.last_health_check.isoformat(),
            "performance_metrics": self.performance_metrics,
            "active_sessions": len(self.active_sessions)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        return self.performance_metrics.copy()
    
    def get_adaptation_data(self) -> Dict[str, Any]:
        """Get adaptation and learning data.
        
        Returns:
            Dict[str, Any]: Adaptation data
        """
        return {
            "learning_mode": self.learning_mode.value,
            "successful_patterns_count": len(self.adaptation_data["successful_patterns"]),
            "quality_trends_count": len(self.adaptation_data["quality_trends"]),
            "top_patterns": self._get_top_patterns()
        }
    
    def _get_top_patterns(self) -> List[Dict[str, Any]]:
        """Get top performing patterns.
        
        Returns:
            List[Dict[str, Any]]: Top patterns
        """
        patterns = []
        for pattern_key, pattern_data in self.adaptation_data["successful_patterns"].items():
            if pattern_data["count"] >= 5:  # Only patterns with sufficient data
                patterns.append({
                    "pattern": pattern_key,
                    "quality": pattern_data["avg_quality"],
                    "count": pattern_data["count"],
                    "strategies": pattern_data["best_strategies"],
                    "provider": pattern_data["preferred_provider"]
                })
        
        # Sort by quality score
        patterns.sort(key=lambda x: x["quality"], reverse=True)
        return patterns[:10]  # Top 10 patterns