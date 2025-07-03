# -*- coding: utf-8 -*-
"""
Internationalization (i18n) System for Easy Genie Desktop
Created by: Geoffroy Streit

This module provides bilingual support (French/English) for the application.
"""

from .translation_manager import TranslationManager, get_text, set_language, get_current_language
from .language_detector import LanguageDetector

__all__ = [
    'TranslationManager',
    'LanguageDetector', 
    'get_text',
    'set_language',
    'get_current_language'
]

# Global translation manager instance
_translation_manager = None

def initialize_i18n(default_language='en'):
    """Initialize the internationalization system.
    
    Args:
        default_language (str): Default language code ('en' or 'fr')
    """
    global _translation_manager
    _translation_manager = TranslationManager(default_language)
    return _translation_manager

def get_translation_manager():
    """Get the global translation manager instance.
    
    Returns:
        TranslationManager: The global translation manager
    """
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager