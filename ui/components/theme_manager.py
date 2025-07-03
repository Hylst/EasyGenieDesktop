"""Theme Manager for Advanced UI Customization.

This module provides comprehensive theming capabilities for Easy Genie Desktop,
including dark/light modes, custom color schemes, and dynamic theme switching.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
from datetime import datetime


class ThemeMode(Enum):
    """Theme mode options."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Based on system preference
    CUSTOM = "custom"


class ColorScheme(Enum):
    """Predefined color schemes."""
    DEFAULT = "default"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    ORANGE = "orange"
    RED = "red"
    PINK = "pink"
    TEAL = "teal"
    CUSTOM = "custom"


class FontSize(Enum):
    """Font size options."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class AnimationSpeed(Enum):
    """Animation speed options."""
    DISABLED = "disabled"
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


@dataclass
class ColorPalette:
    """Color palette definition."""
    # Primary colors
    primary: str = "#1f538d"
    primary_hover: str = "#14375e"
    primary_disabled: str = "#7a7a7a"
    
    # Secondary colors
    secondary: str = "#2cc985"
    secondary_hover: str = "#25a572"
    secondary_disabled: str = "#7a7a7a"
    
    # Background colors
    bg_primary: str = "#212121"
    bg_secondary: str = "#2b2b2b"
    bg_tertiary: str = "#343434"
    bg_hover: str = "#3d3d3d"
    
    # Text colors
    text_primary: str = "#ffffff"
    text_secondary: str = "#b0b0b0"
    text_disabled: str = "#6a6a6a"
    text_accent: str = "#1f538d"
    
    # Border colors
    border_primary: str = "#565b5e"
    border_secondary: str = "#3d3d3d"
    border_focus: str = "#1f538d"
    
    # Status colors
    success: str = "#2cc985"
    warning: str = "#ff9500"
    error: str = "#ff3b30"
    info: str = "#007aff"
    
    # Special colors
    shadow: str = "#000000"
    overlay: str = "#00000080"
    transparent: str = "transparent"


@dataclass
class FontConfig:
    """Font configuration."""
    family: str = "Segoe UI"
    size_small: int = 10
    size_medium: int = 12
    size_large: int = 14
    size_extra_large: int = 16
    size_title: int = 18
    size_header: int = 20
    
    # Font weights
    weight_normal: str = "normal"
    weight_bold: str = "bold"
    
    # Font styles
    style_normal: str = "normal"
    style_italic: str = "italic"


@dataclass
class AnimationConfig:
    """Animation configuration."""
    enabled: bool = True
    duration_fast: int = 150
    duration_normal: int = 250
    duration_slow: int = 400
    easing: str = "ease-out"


@dataclass
class SpacingConfig:
    """Spacing and layout configuration."""
    # Padding
    padding_xs: int = 2
    padding_sm: int = 5
    padding_md: int = 10
    padding_lg: int = 15
    padding_xl: int = 20
    
    # Margins
    margin_xs: int = 2
    margin_sm: int = 5
    margin_md: int = 10
    margin_lg: int = 15
    margin_xl: int = 20
    
    # Border radius
    radius_sm: int = 4
    radius_md: int = 6
    radius_lg: int = 8
    radius_xl: int = 12
    
    # Border width
    border_thin: int = 1
    border_medium: int = 2
    border_thick: int = 3


@dataclass
class ThemeConfig:
    """Complete theme configuration."""
    name: str
    mode: ThemeMode
    color_scheme: ColorScheme
    colors: ColorPalette = field(default_factory=ColorPalette)
    fonts: FontConfig = field(default_factory=FontConfig)
    animations: AnimationConfig = field(default_factory=AnimationConfig)
    spacing: SpacingConfig = field(default_factory=SpacingConfig)
    
    # Theme metadata
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    # Custom properties
    custom_properties: Dict[str, Any] = field(default_factory=dict)


class ThemeManager:
    """Centralized theme management system."""
    
    def __init__(self, config_dir: str = None):
        """Initialize theme manager.
        
        Args:
            config_dir: Directory for theme configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config" / "themes"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Current theme
        self.current_theme: Optional[ThemeConfig] = None
        self.current_mode = ThemeMode.DARK
        
        # Available themes
        self.themes: Dict[str, ThemeConfig] = {}
        
        # Theme change callbacks
        self.theme_change_callbacks: List[Callable[[ThemeConfig], None]] = []
        
        # Load built-in themes
        self._load_builtin_themes()
        
        # Load custom themes
        self._load_custom_themes()
        
        # Set default theme
        self.set_theme("Dark Default")
    
    def _load_builtin_themes(self):
        """Load built-in themes."""
        # Dark themes
        self.themes["Dark Default"] = self._create_dark_theme("Dark Default", ColorScheme.DEFAULT)
        self.themes["Dark Blue"] = self._create_dark_theme("Dark Blue", ColorScheme.BLUE)
        self.themes["Dark Green"] = self._create_dark_theme("Dark Green", ColorScheme.GREEN)
        self.themes["Dark Purple"] = self._create_dark_theme("Dark Purple", ColorScheme.PURPLE)
        self.themes["Dark Orange"] = self._create_dark_theme("Dark Orange", ColorScheme.ORANGE)
        
        # Light themes
        self.themes["Light Default"] = self._create_light_theme("Light Default", ColorScheme.DEFAULT)
        self.themes["Light Blue"] = self._create_light_theme("Light Blue", ColorScheme.BLUE)
        self.themes["Light Green"] = self._create_light_theme("Light Green", ColorScheme.GREEN)
        self.themes["Light Purple"] = self._create_light_theme("Light Purple", ColorScheme.PURPLE)
        self.themes["Light Orange"] = self._create_light_theme("Light Orange", ColorScheme.ORANGE)
    
    def _create_dark_theme(self, name: str, color_scheme: ColorScheme) -> ThemeConfig:
        """Create a dark theme.
        
        Args:
            name: Theme name
            color_scheme: Color scheme
            
        Returns:
            ThemeConfig: Dark theme configuration
        """
        colors = ColorPalette()
        
        # Adjust colors based on scheme
        if color_scheme == ColorScheme.BLUE:
            colors.primary = "#007aff"
            colors.primary_hover = "#0056cc"
            colors.text_accent = "#007aff"
            colors.border_focus = "#007aff"
        elif color_scheme == ColorScheme.GREEN:
            colors.primary = "#2cc985"
            colors.primary_hover = "#25a572"
            colors.text_accent = "#2cc985"
            colors.border_focus = "#2cc985"
        elif color_scheme == ColorScheme.PURPLE:
            colors.primary = "#af52de"
            colors.primary_hover = "#8e44ad"
            colors.text_accent = "#af52de"
            colors.border_focus = "#af52de"
        elif color_scheme == ColorScheme.ORANGE:
            colors.primary = "#ff9500"
            colors.primary_hover = "#cc7700"
            colors.text_accent = "#ff9500"
            colors.border_focus = "#ff9500"
        
        return ThemeConfig(
            name=name,
            mode=ThemeMode.DARK,
            color_scheme=color_scheme,
            colors=colors,
            description=f"Dark theme with {color_scheme.value} accent"
        )
    
    def _create_light_theme(self, name: str, color_scheme: ColorScheme) -> ThemeConfig:
        """Create a light theme.
        
        Args:
            name: Theme name
            color_scheme: Color scheme
            
        Returns:
            ThemeConfig: Light theme configuration
        """
        colors = ColorPalette(
            # Background colors (light)
            bg_primary="#ffffff",
            bg_secondary="#f5f5f5",
            bg_tertiary="#eeeeee",
            bg_hover="#e0e0e0",
            
            # Text colors (dark)
            text_primary="#000000",
            text_secondary="#666666",
            text_disabled="#999999",
            
            # Border colors
            border_primary="#cccccc",
            border_secondary="#e0e0e0",
            
            # Shadow
            shadow="#00000020",
            overlay="#00000040"
        )
        
        # Adjust colors based on scheme
        if color_scheme == ColorScheme.BLUE:
            colors.primary = "#007aff"
            colors.primary_hover = "#0056cc"
            colors.text_accent = "#007aff"
            colors.border_focus = "#007aff"
        elif color_scheme == ColorScheme.GREEN:
            colors.primary = "#2cc985"
            colors.primary_hover = "#25a572"
            colors.text_accent = "#2cc985"
            colors.border_focus = "#2cc985"
        elif color_scheme == ColorScheme.PURPLE:
            colors.primary = "#af52de"
            colors.primary_hover = "#8e44ad"
            colors.text_accent = "#af52de"
            colors.border_focus = "#af52de"
        elif color_scheme == ColorScheme.ORANGE:
            colors.primary = "#ff9500"
            colors.primary_hover = "#cc7700"
            colors.text_accent = "#ff9500"
            colors.border_focus = "#ff9500"
        
        return ThemeConfig(
            name=name,
            mode=ThemeMode.LIGHT,
            color_scheme=color_scheme,
            colors=colors,
            description=f"Light theme with {color_scheme.value} accent"
        )
    
    def _load_custom_themes(self):
        """Load custom themes from files."""
        try:
            for theme_file in self.config_dir.glob("*.json"):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    theme = self._deserialize_theme(theme_data)
                    if theme:
                        self.themes[theme.name] = theme
        except Exception as e:
            print(f"Error loading custom themes: {e}")
    
    def _serialize_theme(self, theme: ThemeConfig) -> Dict[str, Any]:
        """Serialize theme to dictionary.
        
        Args:
            theme: Theme configuration
            
        Returns:
            Dict[str, Any]: Serialized theme data
        """
        return {
            "name": theme.name,
            "mode": theme.mode.value,
            "color_scheme": theme.color_scheme.value,
            "colors": {
                "primary": theme.colors.primary,
                "primary_hover": theme.colors.primary_hover,
                "primary_disabled": theme.colors.primary_disabled,
                "secondary": theme.colors.secondary,
                "secondary_hover": theme.colors.secondary_hover,
                "secondary_disabled": theme.colors.secondary_disabled,
                "bg_primary": theme.colors.bg_primary,
                "bg_secondary": theme.colors.bg_secondary,
                "bg_tertiary": theme.colors.bg_tertiary,
                "bg_hover": theme.colors.bg_hover,
                "text_primary": theme.colors.text_primary,
                "text_secondary": theme.colors.text_secondary,
                "text_disabled": theme.colors.text_disabled,
                "text_accent": theme.colors.text_accent,
                "border_primary": theme.colors.border_primary,
                "border_secondary": theme.colors.border_secondary,
                "border_focus": theme.colors.border_focus,
                "success": theme.colors.success,
                "warning": theme.colors.warning,
                "error": theme.colors.error,
                "info": theme.colors.info,
                "shadow": theme.colors.shadow,
                "overlay": theme.colors.overlay,
                "transparent": theme.colors.transparent
            },
            "fonts": {
                "family": theme.fonts.family,
                "size_small": theme.fonts.size_small,
                "size_medium": theme.fonts.size_medium,
                "size_large": theme.fonts.size_large,
                "size_extra_large": theme.fonts.size_extra_large,
                "size_title": theme.fonts.size_title,
                "size_header": theme.fonts.size_header,
                "weight_normal": theme.fonts.weight_normal,
                "weight_bold": theme.fonts.weight_bold,
                "style_normal": theme.fonts.style_normal,
                "style_italic": theme.fonts.style_italic
            },
            "animations": {
                "enabled": theme.animations.enabled,
                "duration_fast": theme.animations.duration_fast,
                "duration_normal": theme.animations.duration_normal,
                "duration_slow": theme.animations.duration_slow,
                "easing": theme.animations.easing
            },
            "spacing": {
                "padding_xs": theme.spacing.padding_xs,
                "padding_sm": theme.spacing.padding_sm,
                "padding_md": theme.spacing.padding_md,
                "padding_lg": theme.spacing.padding_lg,
                "padding_xl": theme.spacing.padding_xl,
                "margin_xs": theme.spacing.margin_xs,
                "margin_sm": theme.spacing.margin_sm,
                "margin_md": theme.spacing.margin_md,
                "margin_lg": theme.spacing.margin_lg,
                "margin_xl": theme.spacing.margin_xl,
                "radius_sm": theme.spacing.radius_sm,
                "radius_md": theme.spacing.radius_md,
                "radius_lg": theme.spacing.radius_lg,
                "radius_xl": theme.spacing.radius_xl,
                "border_thin": theme.spacing.border_thin,
                "border_medium": theme.spacing.border_medium,
                "border_thick": theme.spacing.border_thick
            },
            "description": theme.description,
            "author": theme.author,
            "version": theme.version,
            "created_at": theme.created_at.isoformat(),
            "custom_properties": theme.custom_properties
        }
    
    def _deserialize_theme(self, data: Dict[str, Any]) -> Optional[ThemeConfig]:
        """Deserialize theme from dictionary.
        
        Args:
            data: Serialized theme data
            
        Returns:
            Optional[ThemeConfig]: Theme configuration or None if invalid
        """
        try:
            # Create color palette
            colors_data = data.get("colors", {})
            colors = ColorPalette(**colors_data)
            
            # Create font config
            fonts_data = data.get("fonts", {})
            fonts = FontConfig(**fonts_data)
            
            # Create animation config
            animations_data = data.get("animations", {})
            animations = AnimationConfig(**animations_data)
            
            # Create spacing config
            spacing_data = data.get("spacing", {})
            spacing = SpacingConfig(**spacing_data)
            
            # Parse datetime
            created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
            
            return ThemeConfig(
                name=data["name"],
                mode=ThemeMode(data.get("mode", "dark")),
                color_scheme=ColorScheme(data.get("color_scheme", "default")),
                colors=colors,
                fonts=fonts,
                animations=animations,
                spacing=spacing,
                description=data.get("description", ""),
                author=data.get("author", ""),
                version=data.get("version", "1.0.0"),
                created_at=created_at,
                custom_properties=data.get("custom_properties", {})
            )
        except Exception as e:
            print(f"Error deserializing theme: {e}")
            return None
    
    def set_theme(self, theme_name: str) -> bool:
        """Set current theme.
        
        Args:
            theme_name: Name of theme to set
            
        Returns:
            bool: True if theme was set successfully
        """
        if theme_name not in self.themes:
            return False
        
        self.current_theme = self.themes[theme_name]
        self.current_mode = self.current_theme.mode
        
        # Apply theme to CustomTkinter
        self._apply_ctk_theme()
        
        # Notify callbacks
        for callback in self.theme_change_callbacks:
            try:
                callback(self.current_theme)
            except Exception as e:
                print(f"Error in theme change callback: {e}")
        
        return True
    
    def _apply_ctk_theme(self):
        """Apply current theme to CustomTkinter."""
        if not self.current_theme:
            return
        
        # Set appearance mode
        if self.current_theme.mode == ThemeMode.DARK:
            ctk.set_appearance_mode("dark")
        elif self.current_theme.mode == ThemeMode.LIGHT:
            ctk.set_appearance_mode("light")
        
        # Set color theme (simplified for CustomTkinter)
        if self.current_theme.color_scheme == ColorScheme.BLUE:
            ctk.set_default_color_theme("blue")
        elif self.current_theme.color_scheme == ColorScheme.GREEN:
            ctk.set_default_color_theme("green")
        else:
            ctk.set_default_color_theme("blue")  # Default fallback
    
    def get_current_theme(self) -> Optional[ThemeConfig]:
        """Get current theme.
        
        Returns:
            Optional[ThemeConfig]: Current theme or None
        """
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names.
        
        Returns:
            List[str]: Available theme names
        """
        return list(self.themes.keys())
    
    def get_themes_by_mode(self, mode: ThemeMode) -> List[str]:
        """Get themes by mode.
        
        Args:
            mode: Theme mode to filter by
            
        Returns:
            List[str]: Theme names matching the mode
        """
        return [name for name, theme in self.themes.items() if theme.mode == mode]
    
    def create_custom_theme(self, name: str, base_theme: str = None, **kwargs) -> bool:
        """Create a custom theme.
        
        Args:
            name: Theme name
            base_theme: Base theme to copy from
            **kwargs: Theme properties to override
            
        Returns:
            bool: True if theme was created successfully
        """
        try:
            # Start with base theme or default
            if base_theme and base_theme in self.themes:
                theme = self._copy_theme(self.themes[base_theme], name)
            else:
                theme = self._create_dark_theme(name, ColorScheme.DEFAULT)
            
            # Apply overrides
            for key, value in kwargs.items():
                if hasattr(theme, key):
                    setattr(theme, key, value)
                elif hasattr(theme.colors, key):
                    setattr(theme.colors, key, value)
                elif hasattr(theme.fonts, key):
                    setattr(theme.fonts, key, value)
                elif hasattr(theme.animations, key):
                    setattr(theme.animations, key, value)
                elif hasattr(theme.spacing, key):
                    setattr(theme.spacing, key, value)
                else:
                    theme.custom_properties[key] = value
            
            # Add to themes
            self.themes[name] = theme
            
            return True
        except Exception as e:
            print(f"Error creating custom theme: {e}")
            return False
    
    def _copy_theme(self, source: ThemeConfig, new_name: str) -> ThemeConfig:
        """Copy a theme with a new name.
        
        Args:
            source: Source theme to copy
            new_name: New theme name
            
        Returns:
            ThemeConfig: Copied theme
        """
        # Serialize and deserialize to create a deep copy
        data = self._serialize_theme(source)
        data["name"] = new_name
        data["created_at"] = datetime.now().isoformat()
        return self._deserialize_theme(data)
    
    def save_theme(self, theme_name: str) -> bool:
        """Save a theme to file.
        
        Args:
            theme_name: Name of theme to save
            
        Returns:
            bool: True if theme was saved successfully
        """
        if theme_name not in self.themes:
            return False
        
        try:
            theme = self.themes[theme_name]
            data = self._serialize_theme(theme)
            
            # Save to file
            filename = f"{theme_name.lower().replace(' ', '_')}.json"
            filepath = self.config_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving theme: {e}")
            return False
    
    def delete_theme(self, theme_name: str) -> bool:
        """Delete a custom theme.
        
        Args:
            theme_name: Name of theme to delete
            
        Returns:
            bool: True if theme was deleted successfully
        """
        if theme_name not in self.themes:
            return False
        
        # Don't allow deletion of built-in themes
        if theme_name.startswith(("Dark ", "Light ")):
            return False
        
        try:
            # Remove from memory
            del self.themes[theme_name]
            
            # Remove file if exists
            filename = f"{theme_name.lower().replace(' ', '_')}.json"
            filepath = self.config_dir / filename
            if filepath.exists():
                filepath.unlink()
            
            return True
        except Exception as e:
            print(f"Error deleting theme: {e}")
            return False
    
    def add_theme_change_callback(self, callback: Callable[[ThemeConfig], None]):
        """Add a callback for theme changes.
        
        Args:
            callback: Callback function to add
        """
        if callback not in self.theme_change_callbacks:
            self.theme_change_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback: Callable[[ThemeConfig], None]):
        """Remove a theme change callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.theme_change_callbacks:
            self.theme_change_callbacks.remove(callback)
    
    def get_color(self, color_name: str) -> str:
        """Get a color from the current theme.
        
        Args:
            color_name: Name of the color
            
        Returns:
            str: Color value or default
        """
        if not self.current_theme:
            return "#000000"
        
        return getattr(self.current_theme.colors, color_name, "#000000")
    
    def get_font(self, size: FontSize = FontSize.MEDIUM, weight: str = "normal", 
                style: str = "normal") -> Tuple[str, int, str]:
        """Get font configuration.
        
        Args:
            size: Font size
            weight: Font weight
            style: Font style
            
        Returns:
            Tuple[str, int, str]: Font family, size, and style
        """
        if not self.current_theme:
            return ("Segoe UI", 12, "normal")
        
        fonts = self.current_theme.fonts
        
        # Get size
        if size == FontSize.SMALL:
            font_size = fonts.size_small
        elif size == FontSize.LARGE:
            font_size = fonts.size_large
        elif size == FontSize.EXTRA_LARGE:
            font_size = fonts.size_extra_large
        else:
            font_size = fonts.size_medium
        
        # Combine weight and style
        font_style = f"{weight} {style}".strip()
        
        return (fonts.family, font_size, font_style)
    
    def get_spacing(self, spacing_name: str) -> int:
        """Get spacing value from current theme.
        
        Args:
            spacing_name: Name of the spacing value
            
        Returns:
            int: Spacing value or default
        """
        if not self.current_theme:
            return 10
        
        return getattr(self.current_theme.spacing, spacing_name, 10)
    
    def is_dark_mode(self) -> bool:
        """Check if current theme is dark mode.
        
        Returns:
            bool: True if dark mode
        """
        return self.current_mode == ThemeMode.DARK
    
    def is_light_mode(self) -> bool:
        """Check if current theme is light mode.
        
        Returns:
            bool: True if light mode
        """
        return self.current_mode == ThemeMode.LIGHT
    
    def toggle_mode(self) -> bool:
        """Toggle between light and dark mode.
        
        Returns:
            bool: True if mode was toggled successfully
        """
        if not self.current_theme:
            return False
        
        # Find corresponding theme in opposite mode
        current_scheme = self.current_theme.color_scheme.value
        
        if self.is_dark_mode():
            # Switch to light
            target_theme = f"Light {current_scheme.title()}"
            if "Default" in self.current_theme.name:
                target_theme = "Light Default"
        else:
            # Switch to dark
            target_theme = f"Dark {current_scheme.title()}"
            if "Default" in self.current_theme.name:
                target_theme = "Dark Default"
        
        return self.set_theme(target_theme)
    
    def export_theme(self, theme_name: str, filepath: str) -> bool:
        """Export a theme to a file.
        
        Args:
            theme_name: Name of theme to export
            filepath: Path to export file
            
        Returns:
            bool: True if theme was exported successfully
        """
        if theme_name not in self.themes:
            return False
        
        try:
            theme = self.themes[theme_name]
            data = self._serialize_theme(theme)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting theme: {e}")
            return False
    
    def import_theme(self, filepath: str) -> Optional[str]:
        """Import a theme from a file.
        
        Args:
            filepath: Path to theme file
            
        Returns:
            Optional[str]: Theme name if imported successfully
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            theme = self._deserialize_theme(data)
            if theme:
                # Ensure unique name
                original_name = theme.name
                counter = 1
                while theme.name in self.themes:
                    theme.name = f"{original_name} ({counter})"
                    counter += 1
                
                self.themes[theme.name] = theme
                return theme.name
            
            return None
        except Exception as e:
            print(f"Error importing theme: {e}")
            return None


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance.
    
    Returns:
        ThemeManager: Global theme manager
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def set_theme(theme_name: str) -> bool:
    """Set current theme (convenience function).
    
    Args:
        theme_name: Name of theme to set
        
    Returns:
        bool: True if theme was set successfully
    """
    return get_theme_manager().set_theme(theme_name)


def get_color(color_name: str) -> str:
    """Get color from current theme (convenience function).
    
    Args:
        color_name: Name of the color
        
    Returns:
        str: Color value
    """
    return get_theme_manager().get_color(color_name)


def get_font(size: FontSize = FontSize.MEDIUM, weight: str = "normal", 
            style: str = "normal") -> Tuple[str, int, str]:
    """Get font configuration (convenience function).
    
    Args:
        size: Font size
        weight: Font weight
        style: Font style
        
    Returns:
        Tuple[str, int, str]: Font family, size, and style
    """
    return get_theme_manager().get_font(size, weight, style)


def get_spacing(spacing_name: str) -> int:
    """Get spacing value (convenience function).
    
    Args:
        spacing_name: Name of the spacing value
        
    Returns:
        int: Spacing value
    """
    return get_theme_manager().get_spacing(spacing_name)