#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Application Settings

Manages global application settings, user preferences, and configuration persistence.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class AppSettings:
    """Manages application settings and user preferences."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.logger = logging.getLogger(__name__)
        self.app_dir = Path.home() / ".easy_genie"
        self.settings_file = self.app_dir / "settings.json"
        
        # Default settings
        self.defaults = {
            # Appearance
            "theme": "light",  # light, dark, sepia, high_contrast
            "font_size": 12,
            "font_family": "Segoe UI",
            "zoom_level": 100,  # 80-200%
            "animations_enabled": True,
            "color_blind_mode": False,
            
            # Accessibility
            "dyslexia_friendly": False,
            "adhd_mode": False,
            "high_contrast": False,
            "reduced_motion": False,
            
            # Audio
            "tts_enabled": True,
            "tts_voice": "default",
            "tts_speed": 150,  # words per minute
            "tts_pitch": 50,   # 0-100
            "tts_volume": 80,  # 0-100
            "ambient_sounds_enabled": True,
            "ambient_volume": 30,
            
            # AI Configuration
            "ai_provider": "none",  # none, openai, anthropic, gemini, ollama
            "ai_model": "",
            "ai_api_key": "",
            "ai_requests_per_hour": 60,
            "ai_cache_enabled": True,
            
            # Tools Intensity (Magic Energy)
            "task_breaker_intensity": 1,
            "time_focus_intensity": 1,
            "priority_grid_intensity": 1,
            "brain_dump_intensity": 1,
            "formalizer_intensity": 1,
            "routine_builder_intensity": 1,
            "immersive_reader_intensity": 1,
            
            # User Profile
            "current_user": "default",
            "auto_save_interval": 30,  # seconds
            "backup_enabled": True,
            "startup_tool": "dashboard",
            
            # Window Settings
            "window_width": 1200,
            "window_height": 800,
            "window_maximized": False,
            "sidebar_width": 250,
            "sidebar_collapsed": False,
            
            # Keyboard Shortcuts
            "shortcuts": {
                "new": "Ctrl+N",
                "open": "Ctrl+O",
                "save": "Ctrl+S",
                "export": "Ctrl+E",
                "help": "Ctrl+/",
                "search": "Ctrl+F",
                "voice_input": "Ctrl+Shift+V",
                "focus_mode": "F11"
            }
        }
        
        self.settings = self.defaults.copy()
        self._ensure_app_directory()
    
    def _ensure_app_directory(self):
        """Ensure the application directory exists."""
        try:
            self.app_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Application directory: {self.app_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create app directory: {e}")
    
    def load(self) -> bool:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to handle new settings
                self.settings = self.defaults.copy()
                self.settings.update(loaded_settings)
                
                self.logger.info("Settings loaded successfully")
                return True
            else:
                self.logger.info("No settings file found, using defaults")
                return self.save()  # Create default settings file
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return False
    
    def save(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Alias for save() method for backward compatibility."""
        return self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings[key] = value
        self.logger.debug(f"Setting updated: {key} = {value}")
    
    def get_nested(self, path: str, default: Any = None) -> Any:
        """Get a nested setting value using dot notation (e.g., 'shortcuts.new')."""
        keys = path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_nested(self, path: str, value: Any) -> None:
        """Set a nested setting value using dot notation."""
        keys = path.split('.')
        setting = self.settings
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in setting:
                setting[key] = {}
            setting = setting[key]
        
        # Set the final value
        setting[keys[-1]] = value
        self.logger.debug(f"Nested setting updated: {path} = {value}")
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self.settings = self.defaults.copy()
        self.logger.info("Settings reset to defaults")
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings exported to: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Validate and merge settings
            self.settings = self.defaults.copy()
            self.settings.update(imported_settings)
            
            self.logger.info(f"Settings imported from: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False
    
    def get_app_directory(self) -> Path:
        """Get the application data directory."""
        return self.app_dir
    
    def is_accessibility_mode(self) -> bool:
        """Check if any accessibility features are enabled."""
        return any([
            self.get('dyslexia_friendly', False),
            self.get('adhd_mode', False),
            self.get('high_contrast', False),
            self.get('reduced_motion', False)
        ])
    
    def get_tool_intensity(self, tool_name: str) -> int:
        """Get the intensity level for a specific tool (1-5)."""
        key = f"{tool_name}_intensity"
        return max(1, min(5, self.get(key, 1)))
    
    def set_tool_intensity(self, tool_name: str, intensity: int) -> None:
        """Set the intensity level for a specific tool (1-5)."""
        intensity = max(1, min(5, intensity))
        key = f"{tool_name}_intensity"
        self.set(key, intensity)