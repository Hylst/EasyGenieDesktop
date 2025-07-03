# -*- coding: utf-8 -*-
"""
Language Detector for Easy Genie Desktop
Created by: Geoffroy Streit

Detects user's preferred language based on system settings.
"""

import locale
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Detects user's preferred language from system settings."""
    
    def __init__(self):
        """Initialize the language detector."""
        self.supported_languages = ['en', 'fr']
        self.language_mappings = {
            # English variants
            'en': 'en',
            'en_US': 'en',
            'en_GB': 'en',
            'en_CA': 'en',
            'en_AU': 'en',
            'english': 'en',
            
            # French variants
            'fr': 'fr',
            'fr_FR': 'fr',
            'fr_CA': 'fr',
            'fr_BE': 'fr',
            'fr_CH': 'fr',
            'french': 'fr',
            'français': 'fr',
            'francais': 'fr'
        }
    
    def detect_system_language(self) -> str:
        """Detect the system's preferred language.
        
        Returns:
            str: Detected language code ('en' or 'fr'), defaults to 'en'
        """
        detected_lang = 'en'  # Default fallback
        
        try:
            # Method 1: Try to get from locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                detected_lang = self._map_language_code(system_locale)
                if detected_lang:
                    logger.info(f"Detected language from locale: {system_locale} -> {detected_lang}")
                    return detected_lang
        except Exception as e:
            logger.warning(f"Error getting locale: {e}")
        
        try:
            # Method 2: Try to get from environment variables
            env_lang = (os.environ.get('LANG') or 
                       os.environ.get('LANGUAGE') or 
                       os.environ.get('LC_ALL') or 
                       os.environ.get('LC_MESSAGES'))
            
            if env_lang:
                detected_lang = self._map_language_code(env_lang)
                if detected_lang:
                    logger.info(f"Detected language from environment: {env_lang} -> {detected_lang}")
                    return detected_lang
        except Exception as e:
            logger.warning(f"Error getting environment language: {e}")
        
        try:
            # Method 3: Windows-specific detection
            if os.name == 'nt':
                import ctypes
                windll = ctypes.windll.kernel32
                language_id = windll.GetUserDefaultUILanguage()
                
                # Common Windows language IDs
                windows_lang_map = {
                    1033: 'en',  # English (US)
                    2057: 'en',  # English (UK)
                    1036: 'fr',  # French (France)
                    3084: 'fr',  # French (Canada)
                }
                
                if language_id in windows_lang_map:
                    detected_lang = windows_lang_map[language_id]
                    logger.info(f"Detected language from Windows: {language_id} -> {detected_lang}")
                    return detected_lang
        except Exception as e:
            logger.warning(f"Error getting Windows language: {e}")
        
        logger.info(f"Using default language: {detected_lang}")
        return detected_lang
    
    def _map_language_code(self, lang_code: str) -> Optional[str]:
        """Map a language code to a supported language.
        
        Args:
            lang_code (str): Language code to map
            
        Returns:
            Optional[str]: Mapped language code or None
        """
        if not lang_code:
            return None
        
        # Clean the language code
        lang_code = lang_code.lower().strip()
        
        # Remove encoding suffix (e.g., 'fr_FR.UTF-8' -> 'fr_FR')
        if '.' in lang_code:
            lang_code = lang_code.split('.')[0]
        
        # Direct mapping
        if lang_code in self.language_mappings:
            return self.language_mappings[lang_code]
        
        # Try just the language part (e.g., 'fr_FR' -> 'fr')
        if '_' in lang_code:
            base_lang = lang_code.split('_')[0]
            if base_lang in self.language_mappings:
                return self.language_mappings[base_lang]
        
        # Try partial matching
        for key, value in self.language_mappings.items():
            if lang_code.startswith(key.lower()):
                return value
        
        return None
    
    def detect_preferred_language(self, user_preference: Optional[str] = None) -> str:
        """Detect the user's preferred language.
        
        Args:
            user_preference (Optional[str]): User's explicit language preference
            
        Returns:
            str: Preferred language code
        """
        # Priority 1: User's explicit preference
        if user_preference:
            mapped_lang = self._map_language_code(user_preference)
            if mapped_lang:
                logger.info(f"Using user preference: {user_preference} -> {mapped_lang}")
                return mapped_lang
        
        # Priority 2: System language
        system_lang = self.detect_system_language()
        logger.info(f"Using detected system language: {system_lang}")
        return system_lang
    
    def is_supported_language(self, lang_code: str) -> bool:
        """Check if a language code is supported.
        
        Args:
            lang_code (str): Language code to check
            
        Returns:
            bool: True if supported
        """
        mapped_lang = self._map_language_code(lang_code)
        return mapped_lang in self.supported_languages
    
    def get_supported_languages(self) -> list:
        """Get list of supported language codes.
        
        Returns:
            list: List of supported language codes
        """
        return self.supported_languages.copy()
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Get the display name for a language code.
        
        Args:
            lang_code (str): Language code
            
        Returns:
            str: Display name for the language
        """
        display_names = {
            'en': 'English',
            'fr': 'Français'
        }
        return display_names.get(lang_code, lang_code)