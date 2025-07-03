#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - AI Service Manager

Manages AI service providers, API calls, and intelligent features.
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import time
import threading
from pathlib import Path

from config.ai_config import AIProvider, AI_PROVIDERS, AI_MODELS, AI_FEATURES


@dataclass
class AIRequest:
    """Represents an AI request."""
    provider: AIProvider
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None


@dataclass
class AIResponse:
    """Represents an AI response."""
    content: str
    provider: AIProvider
    model: str
    usage: Optional[Dict] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class AIServiceManager:
    """Manages AI service providers and intelligent features."""
    
    def __init__(self, settings_manager=None):
        """Initialize AI service manager."""
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        # API configurations
        self.api_keys = {}
        self.api_bases = {}
        self.current_provider = AIProvider.NONE
        self.current_model = None
        
        # Rate limiting
        self.rate_limits = {
            AIProvider.OPENAI: {'requests_per_minute': 60, 'tokens_per_minute': 90000},
            AIProvider.ANTHROPIC: {'requests_per_minute': 50, 'tokens_per_minute': 40000},
            AIProvider.GEMINI: {'requests_per_minute': 60, 'tokens_per_minute': 32000},
            AIProvider.OLLAMA: {'requests_per_minute': 1000, 'tokens_per_minute': 1000000}
        }
        
        self.request_history = []
        self.lock = threading.Lock()
        
        # Cache for responses
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load AI configuration from settings."""
        if not self.settings_manager:
            return
        
        try:
            # Load API keys
            self.api_keys = {
                AIProvider.OPENAI: self.settings_manager.get('ai.openai_api_key', ''),
                AIProvider.ANTHROPIC: self.settings_manager.get('ai.anthropic_api_key', ''),
                AIProvider.GEMINI: self.settings_manager.get('ai.gemini_api_key', ''),
                AIProvider.OLLAMA: ''  # Ollama doesn't need API key
            }
            
            # Load API bases
            self.api_bases = {
                AIProvider.OPENAI: self.settings_manager.get('ai.openai_base_url', 'https://api.openai.com/v1'),
                AIProvider.ANTHROPIC: self.settings_manager.get('ai.anthropic_base_url', 'https://api.anthropic.com'),
                AIProvider.GEMINI: self.settings_manager.get('ai.gemini_base_url', 'https://generativelanguage.googleapis.com/v1beta'),
                AIProvider.OLLAMA: self.settings_manager.get('ai.ollama_base_url', 'http://localhost:11434')
            }
            
            # Load current provider and model
            provider_name = self.settings_manager.get('ai.current_provider', 'NONE')
            try:
                self.current_provider = AIProvider[provider_name]
            except KeyError:
                self.current_provider = AIProvider.NONE
            
            self.current_model = self.settings_manager.get('ai.current_model', None)
            
            self.logger.info(f"AI configuration loaded: {self.current_provider.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to load AI configuration: {e}")
    
    def configure_provider(self, provider: AIProvider, api_key: str = '', base_url: str = '') -> bool:
        """Configure an AI provider."""
        try:
            if provider != AIProvider.NONE:
                self.api_keys[provider] = api_key
                if base_url:
                    self.api_bases[provider] = base_url
            
            # Save to settings
            if self.settings_manager:
                if provider == AIProvider.OPENAI:
                    self.settings_manager.set('ai.openai_api_key', api_key)
                    if base_url:
                        self.settings_manager.set('ai.openai_base_url', base_url)
                elif provider == AIProvider.ANTHROPIC:
                    self.settings_manager.set('ai.anthropic_api_key', api_key)
                    if base_url:
                        self.settings_manager.set('ai.anthropic_base_url', base_url)
                elif provider == AIProvider.GEMINI:
                    self.settings_manager.set('ai.gemini_api_key', api_key)
                    if base_url:
                        self.settings_manager.set('ai.gemini_base_url', base_url)
                elif provider == AIProvider.OLLAMA:
                    if base_url:
                        self.settings_manager.set('ai.ollama_base_url', base_url)
            
            self.logger.info(f"Provider configured: {provider.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure provider: {e}")
            return False
    
    def set_current_provider(self, provider: AIProvider, model: str = None) -> bool:
        """Set the current AI provider and model."""
        try:
            # Validate provider configuration
            if provider != AIProvider.NONE:
                if not self._is_provider_configured(provider):
                    self.logger.error(f"Provider not configured: {provider.value}")
                    return False
                
                # Validate model
                if model and not self._is_model_available(provider, model):
                    self.logger.error(f"Model not available: {model} for {provider.value}")
                    return False
            
            self.current_provider = provider
            self.current_model = model
            
            # Save to settings
            if self.settings_manager:
                self.settings_manager.set('ai.current_provider', provider.value)
                self.settings_manager.set('ai.current_model', model or '')
            
            self.logger.info(f"Current provider set: {provider.value} ({model})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set current provider: {e}")
            return False
    
    def _is_provider_configured(self, provider: AIProvider) -> bool:
        """Check if a provider is properly configured."""
        if provider == AIProvider.NONE:
            return True
        elif provider == AIProvider.OLLAMA:
            return True  # Ollama doesn't need API key
        else:
            return bool(self.api_keys.get(provider, '').strip())
    
    def _is_model_available(self, provider: AIProvider, model: str) -> bool:
        """Check if a model is available for a provider."""
        provider_models = AI_MODELS.get(provider, {})
        return model in provider_models
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of configured providers."""
        available = [AIProvider.NONE]
        for provider in AIProvider:
            if provider != AIProvider.NONE and self._is_provider_configured(provider):
                available.append(provider)
        return available
    
    def get_available_models(self, provider: AIProvider = None) -> List[str]:
        """Get available models for a provider."""
        if provider is None:
            provider = self.current_provider
        
        if provider == AIProvider.NONE:
            return []
        
        return list(AI_MODELS.get(provider, {}).keys())
    
    def get_model_info(self, provider: AIProvider, model: str) -> Optional[Dict]:
        """Get information about a specific model."""
        provider_models = AI_MODELS.get(provider, {})
        return provider_models.get(model)
    
    def can_handle_feature(self, feature: str, intensity: str = 'magic') -> bool:
        """Check if current provider can handle a specific feature."""
        if self.current_provider == AIProvider.NONE:
            return False
        
        feature_config = AI_FEATURES.get(feature, {})
        intensity_config = feature_config.get(intensity, {})
        
        if not intensity_config.get('requires_ai', False):
            return True
        
        required_capabilities = intensity_config.get('capabilities', [])
        
        if not self.current_model:
            return False
        
        model_info = self.get_model_info(self.current_provider, self.current_model)
        if not model_info:
            return False
        
        model_capabilities = model_info.get('capabilities', [])
        
        return all(cap in model_capabilities for cap in required_capabilities)
    
    def estimate_cost(self, feature: str, intensity: str, input_tokens: int = 1000) -> float:
        """Estimate cost for a feature request."""
        if self.current_provider == AIProvider.NONE or not self.current_model:
            return 0.0
        
        model_info = self.get_model_info(self.current_provider, self.current_model)
        if not model_info:
            return 0.0
        
        pricing = model_info.get('pricing', {})
        input_cost = pricing.get('input_per_1k_tokens', 0.0)
        output_cost = pricing.get('output_per_1k_tokens', 0.0)
        
        # Estimate output tokens (usually 20-50% of input)
        estimated_output_tokens = input_tokens * 0.3
        
        total_cost = (input_tokens / 1000 * input_cost) + (estimated_output_tokens / 1000 * output_cost)
        return round(total_cost, 6)
    
    async def make_request(self, request: AIRequest) -> AIResponse:
        """Make an AI request."""
        if self.current_provider == AIProvider.NONE:
            return AIResponse(
                content="AI is disabled",
                provider=AIProvider.NONE,
                model="none",
                error="AI provider not configured"
            )
        
        # Check rate limits
        if not self._check_rate_limit(request.provider):
            return AIResponse(
                content="",
                provider=request.provider,
                model=request.model,
                error="Rate limit exceeded"
            )
        
        # Check cache
        cache_key = self._get_cache_key(request)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        try:
            # Make the actual API call
            response = await self._make_api_call(request)
            
            # Cache successful responses
            if not response.error:
                self._cache_response(cache_key, response)
            
            # Record request for rate limiting
            self._record_request(request.provider)
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return AIResponse(
                content="",
                provider=request.provider,
                model=request.model,
                error=str(e)
            )
    
    async def _make_api_call(self, request: AIRequest) -> AIResponse:
        """Make the actual API call to the provider."""
        if request.provider == AIProvider.OPENAI:
            return await self._call_openai(request)
        elif request.provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(request)
        elif request.provider == AIProvider.GEMINI:
            return await self._call_gemini(request)
        elif request.provider == AIProvider.OLLAMA:
            return await self._call_ollama(request)
        else:
            raise ValueError(f"Unsupported provider: {request.provider}")
    
    async def _call_openai(self, request: AIRequest) -> AIResponse:
        """Call OpenAI API."""
        headers = {
            'Authorization': f'Bearer {self.api_keys[AIProvider.OPENAI]}',
            'Content-Type': 'application/json'
        }
        
        # Prepare messages
        messages = request.messages.copy()
        if request.system_prompt:
            messages.insert(0, {'role': 'system', 'content': request.system_prompt})
        
        payload = {
            'model': request.model,
            'messages': messages,
            'max_tokens': request.max_tokens or 1000,
            'temperature': request.temperature or 0.7
        }
        
        if request.tools:
            payload['tools'] = request.tools
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_bases[AIProvider.OPENAI]}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return AIResponse(
                        content=data['choices'][0]['message']['content'],
                        provider=AIProvider.OPENAI,
                        model=request.model,
                        usage=data.get('usage'),
                        finish_reason=data['choices'][0].get('finish_reason')
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def _call_anthropic(self, request: AIRequest) -> AIResponse:
        """Call Anthropic API."""
        headers = {
            'x-api-key': self.api_keys[AIProvider.ANTHROPIC],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # Convert messages format
        messages = []
        system_prompt = request.system_prompt or ""
        
        for msg in request.messages:
            if msg['role'] == 'system':
                system_prompt += "\n" + msg['content']
            else:
                messages.append(msg)
        
        payload = {
            'model': request.model,
            'messages': messages,
            'max_tokens': request.max_tokens or 1000,
            'temperature': request.temperature or 0.7
        }
        
        if system_prompt.strip():
            payload['system'] = system_prompt.strip()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_bases[AIProvider.ANTHROPIC]}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return AIResponse(
                        content=data['content'][0]['text'],
                        provider=AIProvider.ANTHROPIC,
                        model=request.model,
                        usage=data.get('usage'),
                        finish_reason=data.get('stop_reason')
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
    
    async def _call_gemini(self, request: AIRequest) -> AIResponse:
        """Call Gemini API."""
        # Prepare messages for Gemini format
        contents = []
        system_instruction = request.system_prompt or ""
        
        for msg in request.messages:
            if msg['role'] == 'system':
                system_instruction += "\n" + msg['content']
            else:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append({
                    'role': role,
                    'parts': [{'text': msg['content']}]
                })
        
        payload = {
            'contents': contents,
            'generationConfig': {
                'maxOutputTokens': request.max_tokens or 1000,
                'temperature': request.temperature or 0.7
            }
        }
        
        if system_instruction.strip():
            payload['systemInstruction'] = {
                'parts': [{'text': system_instruction.strip()}]
            }
        
        url = f"{self.api_bases[AIProvider.GEMINI]}/models/{request.model}:generateContent"
        params = {'key': self.api_keys[AIProvider.GEMINI]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    return AIResponse(
                        content=content,
                        provider=AIProvider.GEMINI,
                        model=request.model,
                        usage=data.get('usageMetadata'),
                        finish_reason=data['candidates'][0].get('finishReason')
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
    
    async def _call_ollama(self, request: AIRequest) -> AIResponse:
        """Call Ollama API."""
        # Prepare messages
        messages = request.messages.copy()
        if request.system_prompt:
            messages.insert(0, {'role': 'system', 'content': request.system_prompt})
        
        payload = {
            'model': request.model,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': request.temperature or 0.7
            }
        }
        
        if request.max_tokens:
            payload['options']['num_predict'] = request.max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_bases[AIProvider.OLLAMA]}/api/chat",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return AIResponse(
                        content=data['message']['content'],
                        provider=AIProvider.OLLAMA,
                        model=request.model,
                        usage={
                            'prompt_tokens': data.get('prompt_eval_count', 0),
                            'completion_tokens': data.get('eval_count', 0)
                        },
                        finish_reason=data.get('done_reason')
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
    
    def _check_rate_limit(self, provider: AIProvider) -> bool:
        """Check if request is within rate limits."""
        if provider not in self.rate_limits:
            return True
        
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        with self.lock:
            self.request_history = [
                req for req in self.request_history
                if req['timestamp'] > minute_ago and req['provider'] == provider
            ]
            
            # Check limits
            recent_requests = len(self.request_history)
            limit = self.rate_limits[provider]['requests_per_minute']
            
            return recent_requests < limit
    
    def _record_request(self, provider: AIProvider):
        """Record a request for rate limiting."""
        with self.lock:
            self.request_history.append({
                'provider': provider,
                'timestamp': time.time()
            })
    
    def _get_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request."""
        key_data = {
            'provider': request.provider.value,
            'model': request.model,
            'messages': request.messages,
            'system_prompt': request.system_prompt,
            'temperature': request.temperature
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def _get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Get cached response if available and not expired."""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
            else:
                del self.response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: AIResponse):
        """Cache a response."""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        # Limit cache size
        if len(self.response_cache) > 100:
            oldest_key = min(self.response_cache.keys(), 
                           key=lambda k: self.response_cache[k]['timestamp'])
            del self.response_cache[oldest_key]
    
    # High-level AI features
    async def analyze_text(self, text: str, analysis_type: str = 'general') -> Dict:
        """Analyze text using AI."""
        if not self.can_handle_feature('brain_dump', 'genie'):
            return {'error': 'AI analysis not available'}
        
        prompts = {
            'general': "Analyze this text and provide insights about its content, tone, and key themes.",
            'sentiment': "Analyze the sentiment and emotional tone of this text.",
            'keywords': "Extract the main keywords and topics from this text.",
            'summary': "Provide a concise summary of this text."
        }
        
        prompt = prompts.get(analysis_type, prompts['general'])
        
        request = AIRequest(
            provider=self.current_provider,
            model=self.current_model,
            messages=[
                {'role': 'user', 'content': f"{prompt}\n\nText: {text}"}
            ],
            temperature=0.3
        )
        
        response = await self.make_request(request)
        
        if response.error:
            return {'error': response.error}
        
        return {
            'analysis': response.content,
            'type': analysis_type,
            'provider': response.provider.value,
            'model': response.model
        }
    
    async def break_down_task(self, task: str, context: str = '') -> Dict:
        """Break down a complex task into subtasks."""
        if not self.can_handle_feature('task_breaker', 'genie'):
            return {'error': 'AI task breakdown not available'}
        
        prompt = f"""Break down this task into smaller, actionable subtasks. 
        Provide a clear hierarchy and estimated time for each subtask.
        
        Task: {task}
        {f'Context: {context}' if context else ''}
        
        Format your response as a structured breakdown with:
        - Main subtasks
        - Time estimates
        - Dependencies if any
        - Priority levels"""
        
        request = AIRequest(
            provider=self.current_provider,
            model=self.current_model,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.4
        )
        
        response = await self.make_request(request)
        
        if response.error:
            return {'error': response.error}
        
        return {
            'breakdown': response.content,
            'original_task': task,
            'provider': response.provider.value,
            'model': response.model
        }
    
    async def optimize_routine(self, routine_steps: List[str], goals: List[str] = None) -> Dict:
        """Optimize a routine using AI."""
        if not self.can_handle_feature('routine_builder', 'genie'):
            return {'error': 'AI routine optimization not available'}
        
        steps_text = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(routine_steps)])
        goals_text = '\n'.join(goals) if goals else 'General productivity and well-being'
        
        prompt = f"""Optimize this routine to better achieve the specified goals.
        Suggest improvements, reordering, timing, and additional steps if needed.
        
        Current routine:
        {steps_text}
        
        Goals:
        {goals_text}
        
        Provide:
        - Optimized routine with timing
        - Explanation of changes
        - Expected benefits"""
        
        request = AIRequest(
            provider=self.current_provider,
            model=self.current_model,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.5
        )
        
        response = await self.make_request(request)
        
        if response.error:
            return {'error': response.error}
        
        return {
            'optimization': response.content,
            'original_steps': routine_steps,
            'goals': goals,
            'provider': response.provider.value,
            'model': response.model
        }
    
    def get_status(self) -> Dict:
        """Get current AI service status."""
        return {
            'current_provider': self.current_provider.value,
            'current_model': self.current_model,
            'available_providers': [p.value for p in self.get_available_providers()],
            'configured_providers': [
                p.value for p in AIProvider 
                if p != AIProvider.NONE and self._is_provider_configured(p)
            ],
            'cache_size': len(self.response_cache),
            'recent_requests': len([
                req for req in self.request_history 
                if time.time() - req['timestamp'] < 60
            ])
        }
    
    def clear_cache(self):
        """Clear response cache."""
        self.response_cache.clear()
        self.logger.info("AI response cache cleared")