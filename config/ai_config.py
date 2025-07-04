#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - AI Configuration

Manages AI service providers, models, and configuration settings.
"""

from typing import Dict, List, Optional, Any
import logging
from enum import Enum


class AIProvider(Enum):
    """Supported AI providers."""
    NONE = "none"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class AIConfig:
    """Manages AI service configuration and provider settings."""
    
    def __init__(self):
        """Initialize AI configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Provider configurations
        self.providers = {
            AIProvider.OPENAI: {
                "name": "OpenAI",
                "description": "GPT models from OpenAI",
                "api_base": "https://api.openai.com/v1",
                "models": {
                    "gpt-3.5-turbo": {
                        "name": "GPT-3.5 Turbo",
                        "max_tokens": 4096,
                        "cost_per_1k_tokens": 0.002,
                        "capabilities": ["text", "conversation"]
                    },
                    "gpt-4": {
                        "name": "GPT-4",
                        "max_tokens": 8192,
                        "cost_per_1k_tokens": 0.03,
                        "capabilities": ["text", "conversation", "analysis"]
                    },
                    "gpt-4-turbo": {
                        "name": "GPT-4 Turbo",
                        "max_tokens": 128000,
                        "cost_per_1k_tokens": 0.01,
                        "capabilities": ["text", "conversation", "analysis", "long_context"]
                    }
                },
                "required_fields": ["api_key"],
                "optional_fields": ["organization"]
            },
            
            AIProvider.ANTHROPIC: {
                "name": "Anthropic",
                "description": "Claude models from Anthropic",
                "api_base": "https://api.anthropic.com/v1",
                "models": {
                    "claude-3-haiku": {
                        "name": "Claude 3 Haiku",
                        "max_tokens": 200000,
                        "cost_per_1k_tokens": 0.00025,
                        "capabilities": ["text", "conversation", "fast"]
                    },
                    "claude-3-sonnet": {
                        "name": "Claude 3 Sonnet",
                        "max_tokens": 200000,
                        "cost_per_1k_tokens": 0.003,
                        "capabilities": ["text", "conversation", "analysis"]
                    },
                    "claude-3-opus": {
                        "name": "Claude 3 Opus",
                        "max_tokens": 200000,
                        "cost_per_1k_tokens": 0.015,
                        "capabilities": ["text", "conversation", "analysis", "complex_reasoning"]
                    }
                },
                "required_fields": ["api_key"],
                "optional_fields": []
            },
            
            AIProvider.GEMINI: {
                "name": "Google Gemini",
                "description": "Gemini models from Google",
                "api_base": "https://generativelanguage.googleapis.com/v1",
                "models": {
                    "gemini-pro": {
                        "name": "Gemini Pro",
                        "max_tokens": 32768,
                        "cost_per_1k_tokens": 0.0005,
                        "capabilities": ["text", "conversation"]
                    },
                    "gemini-pro-vision": {
                        "name": "Gemini Pro Vision",
                        "max_tokens": 16384,
                        "cost_per_1k_tokens": 0.0025,
                        "capabilities": ["text", "conversation", "vision"]
                    }
                },
                "required_fields": ["api_key"],
                "optional_fields": []
            },
            
            AIProvider.OLLAMA: {
                "name": "Ollama (Local)",
                "description": "Local models via Ollama",
                "api_base": "http://localhost:11434/api",
                "models": {
                    "llama2": {
                        "name": "Llama 2",
                        "max_tokens": 4096,
                        "cost_per_1k_tokens": 0.0,
                        "capabilities": ["text", "conversation"]
                    },
                    "mistral": {
                        "name": "Mistral",
                        "max_tokens": 8192,
                        "cost_per_1k_tokens": 0.0,
                        "capabilities": ["text", "conversation"]
                    },
                    "codellama": {
                        "name": "Code Llama",
                        "max_tokens": 4096,
                        "cost_per_1k_tokens": 0.0,
                        "capabilities": ["text", "code", "conversation"]
                    }
                },
                "required_fields": [],
                "optional_fields": ["base_url"]
            }
        }
        
        # AI feature configurations for different tools
        self.tool_features = {
            "task_breaker": {
                "magic_level": {
                    "description": "Basic task breakdown suggestions",
                    "required_capabilities": ["text"]
                },
                "genie_level": {
                    "description": "Advanced AI task decomposition with time estimation",
                    "required_capabilities": ["text", "analysis"]
                }
            },
            "time_focus": {
                "magic_level": {
                    "description": "Simple timer functionality",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI-powered productivity analysis and suggestions",
                    "required_capabilities": ["text", "analysis"]
                }
            },
            "priority_grid": {
                "magic_level": {
                    "description": "Manual priority matrix",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI-assisted priority scoring and recommendations",
                    "required_capabilities": ["text", "analysis"]
                }
            },
            "brain_dump": {
                "magic_level": {
                    "description": "Simple text editor",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI analysis of thoughts, emotion detection, task extraction",
                    "required_capabilities": ["text", "analysis"]
                }
            },
            "formalizer": {
                "magic_level": {
                    "description": "Basic text formatting",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI-powered text transformation and style adaptation",
                    "required_capabilities": ["text", "conversation"]
                }
            },
            "routine_builder": {
                "magic_level": {
                    "description": "Simple routine creation",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI-optimized routine suggestions and habit analysis",
                    "required_capabilities": ["text", "analysis"]
                }
            },
            "immersive_reader": {
                "magic_level": {
                    "description": "Basic text-to-speech",
                    "required_capabilities": []
                },
                "genie_level": {
                    "description": "AI text simplification and comprehension assistance",
                    "required_capabilities": ["text", "conversation"]
                }
            }
        }
        
        # Rate limiting defaults
        self.rate_limits = {
            "requests_per_minute": 20,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
            "tokens_per_minute": 10000,
            "tokens_per_hour": 50000
        }
    
    def get_provider_info(self, provider: AIProvider) -> Dict[str, Any]:
        """Get information about a specific AI provider."""
        return self.providers.get(provider, {})
    
    def get_available_models(self, provider: AIProvider) -> Dict[str, Dict[str, Any]]:
        """Get available models for a provider."""
        provider_info = self.get_provider_info(provider)
        return provider_info.get("models", {})
    
    def get_model_info(self, provider: AIProvider, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        models = self.get_available_models(provider)
        return models.get(model_name, {})
    
    def validate_provider_config(self, provider: AIProvider, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate provider configuration."""
        provider_info = self.get_provider_info(provider)
        if not provider_info:
            return False, [f"Unknown provider: {provider}"]
        
        errors = []
        required_fields = provider_info.get("required_fields", [])
        
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    def get_tool_ai_requirements(self, tool_name: str, intensity_level: int) -> Dict[str, Any]:
        """Get AI requirements for a tool at a specific intensity level."""
        tool_config = self.tool_features.get(tool_name, {})
        
        if intensity_level <= 2:
            return tool_config.get("magic_level", {})
        else:
            return tool_config.get("genie_level", {})
    
    def is_provider_suitable(self, provider: AIProvider, tool_name: str, intensity_level: int) -> bool:
        """Check if a provider is suitable for a tool at a specific intensity level."""
        requirements = self.get_tool_ai_requirements(tool_name, intensity_level)
        required_capabilities = requirements.get("required_capabilities", [])
        
        if not required_capabilities:  # No AI required
            return True
        
        provider_info = self.get_provider_info(provider)
        models = provider_info.get("models", {})
        
        # Check if any model from this provider supports the required capabilities
        for model_info in models.values():
            model_capabilities = model_info.get("capabilities", [])
            if all(cap in model_capabilities for cap in required_capabilities):
                return True
        
        return False
    
    def get_recommended_model(self, provider: AIProvider, tool_name: str, intensity_level: int) -> Optional[str]:
        """Get recommended model for a tool at a specific intensity level."""
        requirements = self.get_tool_ai_requirements(tool_name, intensity_level)
        required_capabilities = requirements.get("required_capabilities", [])
        
        if not required_capabilities:
            return None
        
        models = self.get_available_models(provider)
        
        # Find the most cost-effective model that meets requirements
        suitable_models = []
        for model_name, model_info in models.items():
            model_capabilities = model_info.get("capabilities", [])
            if all(cap in model_capabilities for cap in required_capabilities):
                suitable_models.append((model_name, model_info.get("cost_per_1k_tokens", 0)))
        
        if suitable_models:
            # Sort by cost and return the cheapest suitable model
            suitable_models.sort(key=lambda x: x[1])
            return suitable_models[0][0]
        
        return None
    
    def estimate_cost(self, provider: AIProvider, model_name: str, estimated_tokens: int) -> float:
        """Estimate cost for a request."""
        model_info = self.get_model_info(provider, model_name)
        cost_per_1k = model_info.get("cost_per_1k_tokens", 0)
        return (estimated_tokens / 1000) * cost_per_1k
    
    def get_fallback_behavior(self, tool_name: str) -> Dict[str, Any]:
        """Get fallback behavior when AI is unavailable."""
        fallbacks = {
            "task_breaker": {
                "mode": "manual",
                "description": "Manual task breakdown with predefined templates"
            },
            "time_focus": {
                "mode": "basic_timer",
                "description": "Basic timer functionality without AI insights"
            },
            "priority_grid": {
                "mode": "manual_matrix",
                "description": "Manual priority matrix without AI suggestions"
            },
            "brain_dump": {
                "mode": "simple_editor",
                "description": "Simple text editor without AI analysis"
            },
            "formalizer": {
                "mode": "basic_formatting",
                "description": "Basic text formatting without AI transformation"
            },
            "routine_builder": {
                "mode": "manual_routines",
                "description": "Manual routine creation without AI optimization"
            },
            "immersive_reader": {
                "mode": "basic_tts",
                "description": "Basic text-to-speech without AI simplification"
            }
        }
        
        return fallbacks.get(tool_name, {
            "mode": "disabled",
            "description": "Feature disabled without AI"
        })


# Global instances and constants for backward compatibility
_ai_config = AIConfig()

# Export provider configurations as constants
AI_PROVIDERS = _ai_config.providers
AI_MODELS = {provider: config["models"] for provider, config in _ai_config.providers.items()}
AI_FEATURES = _ai_config.tool_features

# Export the main configuration instance
ai_config = _ai_config