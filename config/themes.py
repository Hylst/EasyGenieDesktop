#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Visual Themes

Defines color schemes and visual themes for the application,
including accessibility-focused themes.
"""

from typing import Dict, Any


class ThemeManager:
    """Manages visual themes and color schemes."""
    
    def __init__(self):
        """Initialize theme manager with predefined themes."""
        self.themes = {
            "light": {
                "name": "Clair",
                "description": "Thème clair avec couleurs douces",
                "colors": {
                    # Primary colors (soft blues and teal accents)
                    "primary": "#4A90E2",
                    "primary_dark": "#357ABD",
                    "primary_light": "#7BB3F0",
                    "accent": "#5DADE2",
                    "accent_secondary": "#48C9B0",
                    
                    # Background colors
                    "bg_primary": "#FFFFFF",
                    "bg_secondary": "#F8F9FA",
                    "bg_tertiary": "#E9ECEF",
                    "bg_sidebar": "#F1F3F4",
                    "bg_card": "#FFFFFF",
                    "bg_hover": "#E3F2FD",
                    "bg_selected": "#BBDEFB",
                    
                    # Text colors
                    "text_primary": "#212529",
                    "text_secondary": "#6C757D",
                    "text_muted": "#ADB5BD",
                    "text_inverse": "#FFFFFF",
                    "text_link": "#4A90E2",
                    
                    # Border colors
                    "border_light": "#DEE2E6",
                    "border_medium": "#CED4DA",
                    "border_dark": "#ADB5BD",
                    
                    # Status colors
                    "success": "#28A745",
                    "warning": "#FFC107",
                    "error": "#DC3545",
                    "info": "#17A2B8",
                    
                    # Tool-specific colors
                    "task_breaker": "#E8F5E8",
                    "time_focus": "#FFF3E0",
                    "priority_grid": "#F3E5F5",
                    "brain_dump": "#E1F5FE",
                    "formalizer": "#FFF8E1",
                    "routine_builder": "#E8F5E8",
                    "immersive_reader": "#F1F8E9"
                }
            },
            
            "dark": {
                "name": "Sombre",
                "description": "Thème sombre avec contrastes préservés",
                "colors": {
                    # Primary colors
                    "primary": "#64B5F6",
                    "primary_dark": "#42A5F5",
                    "primary_light": "#90CAF9",
                    "accent": "#81C784",
                    "accent_secondary": "#4DB6AC",
                    
                    # Background colors
                    "bg_primary": "#121212",
                    "bg_secondary": "#1E1E1E",
                    "bg_tertiary": "#2D2D2D",
                    "bg_sidebar": "#1A1A1A",
                    "bg_card": "#1E1E1E",
                    "bg_hover": "#333333",
                    "bg_selected": "#404040",
                    
                    # Text colors
                    "text_primary": "#FFFFFF",
                    "text_secondary": "#B3B3B3",
                    "text_muted": "#666666",
                    "text_inverse": "#000000",
                    "text_link": "#64B5F6",
                    
                    # Border colors
                    "border_light": "#404040",
                    "border_medium": "#555555",
                    "border_dark": "#666666",
                    
                    # Status colors
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "info": "#2196F3",
                    
                    # Tool-specific colors
                    "task_breaker": "#1B5E20",
                    "time_focus": "#E65100",
                    "priority_grid": "#4A148C",
                    "brain_dump": "#01579B",
                    "formalizer": "#F57F17",
                    "routine_builder": "#2E7D32",
                    "immersive_reader": "#33691E"
                }
            },
            
            "sepia": {
                "name": "Sépia",
                "description": "Thème sépia pour lecture prolongée",
                "colors": {
                    # Primary colors (warm browns and golds)
                    "primary": "#8D6E63",
                    "primary_dark": "#5D4037",
                    "primary_light": "#A1887F",
                    "accent": "#FF8A65",
                    "accent_secondary": "#FFAB91",
                    
                    # Background colors (warm, paper-like)
                    "bg_primary": "#FDF6E3",
                    "bg_secondary": "#F5EFDC",
                    "bg_tertiary": "#EDE7D3",
                    "bg_sidebar": "#F0E9D6",
                    "bg_card": "#FEFBF0",
                    "bg_hover": "#F3EDD8",
                    "bg_selected": "#E8DCC0",
                    
                    # Text colors (dark browns)
                    "text_primary": "#3E2723",
                    "text_secondary": "#5D4037",
                    "text_muted": "#8D6E63",
                    "text_inverse": "#FDF6E3",
                    "text_link": "#6D4C41",
                    
                    # Border colors
                    "border_light": "#D7CCC8",
                    "border_medium": "#BCAAA4",
                    "border_dark": "#A1887F",
                    
                    # Status colors (muted)
                    "success": "#689F38",
                    "warning": "#F57C00",
                    "error": "#D32F2F",
                    "info": "#1976D2",
                    
                    # Tool-specific colors
                    "task_breaker": "#E8F5E8",
                    "time_focus": "#FFF8E1",
                    "priority_grid": "#F3E5F5",
                    "brain_dump": "#E1F5FE",
                    "formalizer": "#FFFDE7",
                    "routine_builder": "#F1F8E9",
                    "immersive_reader": "#F9FBE7"
                }
            },
            
            "high_contrast": {
                "name": "Contraste Élevé",
                "description": "Thème à contraste élevé pour accessibilité",
                "colors": {
                    # High contrast colors
                    "primary": "#0000FF",
                    "primary_dark": "#000080",
                    "primary_light": "#4040FF",
                    "accent": "#FF0000",
                    "accent_secondary": "#00FF00",
                    
                    # Background colors (pure contrast)
                    "bg_primary": "#FFFFFF",
                    "bg_secondary": "#F0F0F0",
                    "bg_tertiary": "#E0E0E0",
                    "bg_sidebar": "#F8F8F8",
                    "bg_card": "#FFFFFF",
                    "bg_hover": "#FFFF00",
                    "bg_selected": "#0000FF",
                    
                    # Text colors (maximum contrast)
                    "text_primary": "#000000",
                    "text_secondary": "#000000",
                    "text_muted": "#404040",
                    "text_inverse": "#FFFFFF",
                    "text_link": "#0000FF",
                    
                    # Border colors (strong)
                    "border_light": "#808080",
                    "border_medium": "#404040",
                    "border_dark": "#000000",
                    
                    # Status colors (high contrast)
                    "success": "#008000",
                    "warning": "#FF8000",
                    "error": "#FF0000",
                    "info": "#0000FF",
                    
                    # Tool-specific colors (high contrast)
                    "task_breaker": "#E0FFE0",
                    "time_focus": "#FFE0E0",
                    "priority_grid": "#E0E0FF",
                    "brain_dump": "#E0FFFF",
                    "formalizer": "#FFFFE0",
                    "routine_builder": "#F0FFE0",
                    "immersive_reader": "#F8FFF8"
                }
            }
        }
        
        # Accessibility presets
        self.accessibility_presets = {
            "dyslexia": {
                "font_family": "OpenDyslexic",
                "letter_spacing": 1.2,
                "line_height": 1.6,
                "word_spacing": 1.3,
                "background_tint": "#FFFEF7"  # Slight cream tint
            },
            "adhd": {
                "reduced_animations": True,
                "simplified_ui": True,
                "focus_indicators": True,
                "distraction_free": True
            },
            "low_vision": {
                "font_size_multiplier": 1.5,
                "high_contrast": True,
                "bold_text": True,
                "cursor_size": "large"
            }
        }
    
    def get_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get a theme by name."""
        return self.themes.get(theme_name, self.themes["light"])
    
    def get_color(self, theme_name: str, color_key: str) -> str:
        """Get a specific color from a theme."""
        theme = self.get_theme(theme_name)
        return theme["colors"].get(color_key, "#000000")
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes with their display names."""
        return {name: theme["name"] for name, theme in self.themes.items()}
    
    def apply_accessibility_preset(self, theme_name: str, preset_name: str) -> Dict[str, Any]:
        """Apply accessibility preset to a theme."""
        theme = self.get_theme(theme_name).copy()
        preset = self.accessibility_presets.get(preset_name, {})
        
        # Merge preset settings with theme
        if preset:
            theme["accessibility"] = preset
        
        return theme
    
    def create_custom_theme(self, base_theme: str, modifications: Dict[str, str]) -> Dict[str, Any]:
        """Create a custom theme based on an existing theme with modifications."""
        theme = self.get_theme(base_theme).copy()
        
        # Apply color modifications
        for color_key, color_value in modifications.items():
            if color_key in theme["colors"]:
                theme["colors"][color_key] = color_value
        
        return theme
    
    def get_tool_color(self, theme_name: str, tool_name: str) -> str:
        """Get the specific color for a tool in the given theme."""
        return self.get_color(theme_name, tool_name)
    
    def is_dark_theme(self, theme_name: str) -> bool:
        """Check if a theme is considered dark."""
        return theme_name in ["dark"]
    
    def get_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors (simplified)."""
        # This is a simplified implementation
        # In a real application, you'd want a proper color contrast calculation
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def luminance(rgb):
            r, g, b = [x/255.0 for x in rgb]
            return 0.299 * r + 0.587 * g + 0.114 * b
        
        try:
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            lum1 = luminance(rgb1)
            lum2 = luminance(rgb2)
            
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            
            return (lighter + 0.05) / (darker + 0.05)
        except:
            return 1.0  # Default to minimum contrast if calculation fails