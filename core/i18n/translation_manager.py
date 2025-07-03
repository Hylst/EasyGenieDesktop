# -*- coding: utf-8 -*-
"""
Translation Manager for Easy Genie Desktop
Created by: Geoffroy Streit

Manages bilingual translations (French/English) for the application.
"""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TranslationManager:
    """Manages translations for the application."""
    
    def __init__(self, default_language: str = 'en'):
        """Initialize the translation manager.
        
        Args:
            default_language (str): Default language code ('en' or 'fr')
        """
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.supported_languages = ['en', 'fr']
        
        # Get the translations directory path
        self.translations_dir = Path(__file__).parent / 'translations'
        self.translations_dir.mkdir(exist_ok=True)
        
        # Load translations
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translation files for all supported languages."""
        for lang_code in self.supported_languages:
            translation_file = self.translations_dir / f'{lang_code}.json'
            
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                    logger.info(f"Loaded translations for language: {lang_code}")
                except Exception as e:
                    logger.error(f"Error loading translations for {lang_code}: {e}")
                    self.translations[lang_code] = {}
            else:
                logger.warning(f"Translation file not found: {translation_file}")
                self.translations[lang_code] = {}
                # Create empty translation file
                self._create_empty_translation_file(lang_code)
    
    def _create_empty_translation_file(self, lang_code: str) -> None:
        """Create an empty translation file for a language.
        
        Args:
            lang_code (str): Language code
        """
        translation_file = self.translations_dir / f'{lang_code}.json'
        try:
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logger.info(f"Created empty translation file: {translation_file}")
        except Exception as e:
            logger.error(f"Error creating translation file for {lang_code}: {e}")
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language.
        
        Args:
            language_code (str): Language code ('en' or 'fr')
            
        Returns:
            bool: True if language was set successfully
        """
        if language_code in self.supported_languages:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
            return True
        else:
            logger.warning(f"Unsupported language: {language_code}")
            return False
    
    def get_current_language(self) -> str:
        """Get the current language code.
        
        Returns:
            str: Current language code
        """
        return self.current_language
    
    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text for a key.
        
        Args:
            key (str): Translation key
            **kwargs: Variables for string formatting
            
        Returns:
            str: Translated text or key if translation not found
        """
        # Try to get translation for current language
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key)
            if text:
                try:
                    return text.format(**kwargs) if kwargs else text
                except KeyError as e:
                    logger.warning(f"Missing format variable {e} for key '{key}'")
                    return text
        
        # Fallback to default language
        if (self.default_language != self.current_language and 
            self.default_language in self.translations):
            text = self.translations[self.default_language].get(key)
            if text:
                try:
                    return text.format(**kwargs) if kwargs else text
                except KeyError as e:
                    logger.warning(f"Missing format variable {e} for key '{key}'")
                    return text
        
        # Return key if no translation found
        logger.warning(f"Translation not found for key: '{key}'")
        return key
    
    def add_translation(self, key: str, text: str, language_code: str) -> None:
        """Add or update a translation.
        
        Args:
            key (str): Translation key
            text (str): Translated text
            language_code (str): Language code
        """
        if language_code not in self.supported_languages:
            logger.warning(f"Unsupported language: {language_code}")
            return
        
        if language_code not in self.translations:
            self.translations[language_code] = {}
        
        self.translations[language_code][key] = text
        logger.debug(f"Added translation for '{key}' in {language_code}")
    
    def save_translations(self) -> None:
        """Save all translations to files."""
        for lang_code, translations in self.translations.items():
            translation_file = self.translations_dir / f'{lang_code}.json'
            try:
                with open(translation_file, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2, sort_keys=True)
                logger.info(f"Saved translations for language: {lang_code}")
            except Exception as e:
                logger.error(f"Error saving translations for {lang_code}: {e}")
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their display names.
        
        Returns:
            Dict[str, str]: Language codes mapped to display names
        """
        return {
            'en': 'English',
            'fr': 'Français'
        }
    
    def get_language_info(self, language_code: str) -> Optional[Dict[str, Any]]:
        """Get information about a language.
        
        Args:
            language_code (str): Language code
            
        Returns:
            Optional[Dict[str, Any]]: Language information or None
        """
        language_info = {
            'en': {
                'name': 'English',
                'native_name': 'English',
                'flag': '🇺🇸',
                'direction': 'ltr'
            },
            'fr': {
                'name': 'French',
                'native_name': 'Français',
                'flag': '🇫🇷',
                'direction': 'ltr'
            }
        }
        
        return language_info.get(language_code)


# Global translation manager instance
_global_manager: Optional[TranslationManager] = None

def get_translation_manager() -> TranslationManager:
    """Get the global translation manager instance.
    
    Returns:
        TranslationManager: The global translation manager
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = TranslationManager()
    return _global_manager

def get_text(key: str, **kwargs) -> str:
    """Get translated text using the global translation manager.
    
    Args:
        key (str): Translation key
        **kwargs: Variables for string formatting
        
    Returns:
        str: Translated text
    """
    return get_translation_manager().get_text(key, **kwargs)

def set_language(language_code: str) -> bool:
    """Set the current language using the global translation manager.
    
    Args:
        language_code (str): Language code
        
    Returns:
        bool: True if language was set successfully
    """
    return get_translation_manager().set_language(language_code)

def get_current_language() -> str:
    """Get the current language code using the global translation manager.
    
    Returns:
        str: Current language code
    """
    return get_translation_manager().get_current_language()

# Convenience alias
_ = get_text