# -*- coding: utf-8 -*-
"""
Language Selector Component for Easy Genie Desktop
Created by: Geoffroy Streit

Reusable UI component for language selection (French/English).
"""

import customtkinter as ctk
from typing import Callable, Optional
import logging
from core.i18n import get_text, set_language, get_current_language, get_translation_manager

logger = logging.getLogger(__name__)

class LanguageSelector(ctk.CTkFrame):
    """A reusable language selector component."""
    
    def __init__(self, 
                 parent,
                 on_language_change: Optional[Callable[[str], None]] = None,
                 show_flags: bool = True,
                 show_labels: bool = True,
                 orientation: str = "horizontal",
                 **kwargs):
        """
        Initialize the language selector.
        
        Args:
            parent: Parent widget
            on_language_change: Callback function when language changes
            show_flags: Whether to show flag emojis
            show_labels: Whether to show language labels
            orientation: Layout orientation ('horizontal' or 'vertical')
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.on_language_change = on_language_change
        self.show_flags = show_flags
        self.show_labels = show_labels
        self.orientation = orientation
        
        # Get translation manager
        self.translation_manager = get_translation_manager()
        
        # Language information
        self.languages = {
            'en': {
                'name': 'English',
                'flag': '🇺🇸',
                'display': 'English' if show_labels else '🇺🇸'
            },
            'fr': {
                'name': 'Français', 
                'flag': '🇫🇷',
                'display': 'Français' if show_labels else '🇫🇷'
            }
        }
        
        # Update display text based on flags and labels settings
        self._update_display_text()
        
        # Current language
        self.current_language = get_current_language()
        
        # Create UI
        self._create_widgets()
        self._setup_layout()
        
        # Update initial selection
        self._update_selection()
    
    def _update_display_text(self):
        """Update display text based on show_flags and show_labels settings."""
        for lang_code, lang_info in self.languages.items():
            if self.show_flags and self.show_labels:
                lang_info['display'] = f"{lang_info['flag']} {lang_info['name']}"
            elif self.show_flags:
                lang_info['display'] = lang_info['flag']
            elif self.show_labels:
                lang_info['display'] = lang_info['name']
            else:
                lang_info['display'] = lang_code.upper()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Language selection variable
        self.language_var = ctk.StringVar(value=self.current_language)
        
        # Create radio buttons for each language
        self.language_buttons = {}
        
        for lang_code, lang_info in self.languages.items():
            button = ctk.CTkRadioButton(
                self,
                text=lang_info['display'],
                variable=self.language_var,
                value=lang_code,
                command=self._on_language_selected,
                font=ctk.CTkFont(size=12)
            )
            self.language_buttons[lang_code] = button
    
    def _setup_layout(self):
        """Setup the layout of widgets."""
        if self.orientation == "horizontal":
            # Horizontal layout
            for i, (lang_code, button) in enumerate(self.language_buttons.items()):
                button.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        else:
            # Vertical layout
            for i, (lang_code, button) in enumerate(self.language_buttons.items()):
                button.grid(row=i, column=0, padx=5, pady=2, sticky="w")
    
    def _on_language_selected(self):
        """Handle language selection."""
        selected_language = self.language_var.get()
        
        if selected_language != self.current_language:
            logger.info(f"Language changed from {self.current_language} to {selected_language}")
            
            # Update current language
            self.current_language = selected_language
            
            # Set language in translation manager
            success = set_language(selected_language)
            
            if success:
                # Call callback if provided
                if self.on_language_change:
                    try:
                        self.on_language_change(selected_language)
                    except Exception as e:
                        logger.error(f"Error in language change callback: {e}")
                
                # Update display text if needed
                self._update_display_text()
                self._update_button_text()
                
                logger.info(f"Language successfully changed to {selected_language}")
            else:
                logger.error(f"Failed to change language to {selected_language}")
                # Revert selection
                self.language_var.set(self.current_language)
    
    def _update_button_text(self):
        """Update button text after language change."""
        for lang_code, button in self.language_buttons.items():
            button.configure(text=self.languages[lang_code]['display'])
    
    def _update_selection(self):
        """Update the current selection."""
        self.language_var.set(self.current_language)
    
    def set_language(self, language_code: str) -> bool:
        """Programmatically set the language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            bool: True if language was set successfully
        """
        if language_code in self.languages:
            self.language_var.set(language_code)
            self._on_language_selected()
            return True
        return False
    
    def get_current_language(self) -> str:
        """Get the currently selected language.
        
        Returns:
            str: Current language code
        """
        return self.current_language
    
    def refresh_translations(self):
        """Refresh the component with updated translations."""
        # This method can be called when translations are updated
        self._update_display_text()
        self._update_button_text()
        logger.debug("Language selector translations refreshed")


class LanguageDropdown(ctk.CTkFrame):
    """A dropdown-style language selector component."""
    
    def __init__(self, 
                 parent,
                 on_language_change: Optional[Callable[[str], None]] = None,
                 show_flags: bool = True,
                 **kwargs):
        """
        Initialize the language dropdown.
        
        Args:
            parent: Parent widget
            on_language_change: Callback function when language changes
            show_flags: Whether to show flag emojis
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.on_language_change = on_language_change
        self.show_flags = show_flags
        
        # Get translation manager
        self.translation_manager = get_translation_manager()
        
        # Language information
        self.languages = {
            'en': {'name': 'English', 'flag': '🇺🇸'},
            'fr': {'name': 'Français', 'flag': '🇫🇷'}
        }
        
        # Current language
        self.current_language = get_current_language()
        
        # Create UI
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Create dropdown options
        self.dropdown_options = []
        for lang_code, lang_info in self.languages.items():
            if self.show_flags:
                option = f"{lang_info['flag']} {lang_info['name']}"
            else:
                option = lang_info['name']
            self.dropdown_options.append(option)
        
        # Create dropdown
        self.language_dropdown = ctk.CTkOptionMenu(
            self,
            values=self.dropdown_options,
            command=self._on_language_selected,
            font=ctk.CTkFont(size=12)
        )
        
        # Set initial value
        current_option = self._get_option_for_language(self.current_language)
        self.language_dropdown.set(current_option)
    
    def _setup_layout(self):
        """Setup the layout of widgets."""
        self.language_dropdown.pack(padx=5, pady=5, fill="x")
    
    def _get_option_for_language(self, language_code: str) -> str:
        """Get dropdown option text for a language code.
        
        Args:
            language_code: Language code
            
        Returns:
            str: Dropdown option text
        """
        if language_code in self.languages:
            lang_info = self.languages[language_code]
            if self.show_flags:
                return f"{lang_info['flag']} {lang_info['name']}"
            else:
                return lang_info['name']
        return ""
    
    def _get_language_for_option(self, option: str) -> str:
        """Get language code for a dropdown option.
        
        Args:
            option: Dropdown option text
            
        Returns:
            str: Language code
        """
        for lang_code, lang_info in self.languages.items():
            expected_option = self._get_option_for_language(lang_code)
            if option == expected_option:
                return lang_code
        return 'en'  # Default fallback
    
    def _on_language_selected(self, selected_option: str):
        """Handle language selection from dropdown.
        
        Args:
            selected_option: Selected dropdown option
        """
        selected_language = self._get_language_for_option(selected_option)
        
        if selected_language != self.current_language:
            logger.info(f"Language changed from {self.current_language} to {selected_language}")
            
            # Update current language
            self.current_language = selected_language
            
            # Set language in translation manager
            success = set_language(selected_language)
            
            if success:
                # Call callback if provided
                if self.on_language_change:
                    try:
                        self.on_language_change(selected_language)
                    except Exception as e:
                        logger.error(f"Error in language change callback: {e}")
                
                logger.info(f"Language successfully changed to {selected_language}")
            else:
                logger.error(f"Failed to change language to {selected_language}")
                # Revert selection
                current_option = self._get_option_for_language(self.current_language)
                self.language_dropdown.set(current_option)
    
    def set_language(self, language_code: str) -> bool:
        """Programmatically set the language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            bool: True if language was set successfully
        """
        if language_code in self.languages:
            option = self._get_option_for_language(language_code)
            self.language_dropdown.set(option)
            self._on_language_selected(option)
            return True
        return False
    
    def get_current_language(self) -> str:
        """Get the currently selected language.
        
        Returns:
            str: Current language code
        """
        return self.current_language