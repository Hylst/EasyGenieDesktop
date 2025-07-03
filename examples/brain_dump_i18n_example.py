#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Brain Dump Tool with i18n Support
Created by: Geoffroy Streit

This example shows how to integrate the i18n system into existing tools.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
import uuid
import re
import threading

# Import i18n system
from core.i18n import get_text as _, get_current_language, set_language
from ui.components.language_selector import LanguageSelector
from ui.components.reusable_dialogs import show_confirmation, show_input, show_message

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class BrainDumpToolI18n(BaseToolWindow):
    """Brain Dump tool with internationalization support."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Brain Dump tool with i18n support."""
        # Initialize with translated title
        super().__init__(
            parent, 
            _("tools.brain_dump"),  # Translated title
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Brain dump data
        self.current_dump = {
            'id': str(uuid.uuid4()),
            'title': '',
            'content': '',
            'tags': [],
            'category': _("categories.general"),  # Translated default category
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'word_count': 0,
            'analysis': None
        }
        
        # UI state
        self.auto_save_enabled = True
        self.auto_save_timer = None
        self.is_recording = False
        self.word_count_update_timer = None
        
        # Analysis cache
        self.last_analysis = None
        self.analysis_cache = {}
        
        # Language change callback
        self.language_change_callbacks = []
        
        self.logger.info("Brain Dump tool with i18n initialized")
    
    def _setup_tool_content(self):
        """Setup Brain Dump specific content with i18n support."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Language selector at the top
        self._create_language_selector()
        
        # Top panel - Controls and metadata
        self._create_controls_panel()
        
        # Main content area
        self._create_content_area()
        
        # Bottom panel - Actions and insights
        self._create_actions_panel()
        
        # Start auto-save timer
        self._start_auto_save_timer()
    
    def _create_language_selector(self):
        """Create language selector at the top of the tool."""
        lang_frame = ctk.CTkFrame(self.content_frame, height=40)
        lang_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        lang_frame.grid_columnconfigure(0, weight=1)
        
        # Language selector
        self.language_selector = LanguageSelector(
            lang_frame,
            on_language_change=self._on_language_change,
            show_flags=True,
            show_labels=True,
            orientation="horizontal"
        )
        self.language_selector.pack(side="right", padx=10, pady=5)
        
        # Tool description
        desc_label = ctk.CTkLabel(
            lang_frame,
            text=_("tools.brain_dump_desc"),
            font=ctk.CTkFont(size=11, style="italic")
        )
        desc_label.pack(side="left", padx=10, pady=5)
    
    def _create_controls_panel(self):
        """Create controls panel with translated labels."""
        controls_panel = ctk.CTkFrame(self.content_frame, height=100)
        controls_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        controls_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - Title and metadata
        metadata_frame = ctk.CTkFrame(controls_panel)
        metadata_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Title
        title_frame = ctk.CTkFrame(metadata_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=f"📝 {_("ui_components.title")}:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.title_label.pack(side="left")
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text=_("brain_dump.title_placeholder"),
            height=30
        )
        self.title_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.title_entry.bind("<KeyRelease>", self._on_title_change)
        
        # Category and tags
        meta_frame = ctk.CTkFrame(metadata_frame, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Category
        self.category_label = ctk.CTkLabel(
            meta_frame,
            text=f"📁 {_("ui_components.category")}:",
            font=ctk.CTkFont(size=11)
        )
        self.category_label.pack(side="left")
        
        self.category_var = ctk.StringVar(value=_("categories.general"))
        self.category_menu = ctk.CTkOptionMenu(
            meta_frame,
            variable=self.category_var,
            values=self._get_translated_categories(),
            width=120,
            command=self._on_category_change
        )
        self.category_menu.pack(side="left", padx=(5, 15))
        
        # Tags
        self.tags_label = ctk.CTkLabel(
            meta_frame,
            text=f"🏷️ {_("ui_components.tags")}:",
            font=ctk.CTkFont(size=11)
        )
        self.tags_label.pack(side="left")
        
        self.tags_entry = ctk.CTkEntry(
            meta_frame,
            placeholder_text=_("brain_dump.tags_placeholder"),
            width=200
        )
        self.tags_entry.pack(side="left", padx=(5, 0))
        self.tags_entry.bind("<KeyRelease>", self._on_tags_change)
        
        # Center - Quick actions
        actions_frame = ctk.CTkFrame(controls_panel)
        actions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        
        self.quick_actions_label = ctk.CTkLabel(
            actions_frame,
            text=f"⚡ {_("brain_dump.quick_actions")}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.quick_actions_label.pack(pady=(10, 5))
        
        quick_actions = ctk.CTkFrame(actions_frame, fg_color="transparent")
        quick_actions.pack(fill="x", padx=10, pady=(0, 10))
        
        # Voice recording
        self.record_btn = ctk.CTkButton(
            quick_actions,
            text=f"🎤 {_("voice.record")}",
            height=30,
            width=100,
            command=self._toggle_voice_recording
        )
        self.record_btn.pack(side="left", padx=(0, 5))
        
        # Quick save
        self.save_btn = ctk.CTkButton(
            quick_actions,
            text=f"💾 {_("buttons.save")}",
            height=30,
            width=80,
            command=self._save_dump
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Clear
        self.clear_btn = ctk.CTkButton(
            quick_actions,
            text=f"🗑️ {_("buttons.clear")}",
            height=30,
            width=80,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_dump
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def _create_content_area(self):
        """Create main content area with translated labels."""
        content_area = ctk.CTkFrame(self.content_frame)
        content_area.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        content_area.grid_columnconfigure(0, weight=1)
        content_area.grid_rowconfigure(1, weight=1)
        
        # Content header
        content_header = ctk.CTkFrame(content_area, height=40)
        content_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        content_header.grid_columnconfigure(1, weight=1)
        
        self.content_label = ctk.CTkLabel(
            content_header,
            text=f"✍️ {_("brain_dump.content")}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.content_label.pack(side="left", padx=10, pady=10)
        
        # Word count
        self.word_count_label = ctk.CTkLabel(
            content_header,
            text=_("brain_dump.word_count", count=0),
            font=ctk.CTkFont(size=11)
        )
        self.word_count_label.pack(side="right", padx=10, pady=10)
        
        # Text area
        self.content_text = ctk.CTkTextbox(
            content_area,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.content_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.content_text.bind("<KeyRelease>", self._on_content_change)
    
    def _create_actions_panel(self):
        """Create actions panel with translated labels."""
        actions_panel = ctk.CTkFrame(self.content_frame, height=80)
        actions_panel.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        actions_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - File operations
        file_frame = ctk.CTkFrame(actions_panel)
        file_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.file_ops_label = ctk.CTkLabel(
            file_frame,
            text=f"📁 {_("brain_dump.file_operations")}",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.file_ops_label.pack(pady=(5, 2))
        
        file_buttons = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_buttons.pack(fill="x", padx=5, pady=(0, 5))
        
        self.load_btn = ctk.CTkButton(
            file_buttons,
            text=_("buttons.load"),
            height=25,
            width=70,
            command=self._load_dump
        )
        self.load_btn.pack(side="left", padx=(0, 5))
        
        self.export_btn = ctk.CTkButton(
            file_buttons,
            text=_("export.export_data"),
            height=25,
            width=70,
            command=self._export_dump
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Right side - AI Analysis (if available)
        if self.magic_energy_level == 'genie' and self.ai_service:
            ai_frame = ctk.CTkFrame(actions_panel)
            ai_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
            
            self.ai_label = ctk.CTkLabel(
                ai_frame,
                text=f"🤖 {_("brain_dump.ai_analysis")}",
                font=ctk.CTkFont(size=11, weight="bold")
            )
            self.ai_label.pack(pady=(5, 2))
            
            ai_buttons = ctk.CTkFrame(ai_frame, fg_color="transparent")
            ai_buttons.pack(fill="x", padx=5, pady=(0, 5))
            
            self.analyze_btn = ctk.CTkButton(
                ai_buttons,
                text=_("brain_dump.analyze"),
                height=25,
                width=80,
                command=self._analyze_content
            )
            self.analyze_btn.pack(side="left", padx=(0, 5))
            
            self.organize_btn = ctk.CTkButton(
                ai_buttons,
                text=_("brain_dump.organize"),
                height=25,
                width=80,
                command=self._organize_content
            )
            self.organize_btn.pack(side="left", padx=5)
    
    def _get_translated_categories(self) -> List[str]:
        """Get list of translated categories.
        
        Returns:
            List[str]: Translated category names
        """
        return [
            _("categories.general"),
            _("categories.ideas"),
            _("categories.projects"),
            _("categories.reflections"),
            _("categories.notes"),
            _("categories.creative"),
            _("categories.problems")
        ]
    
    def _on_language_change(self, language_code: str):
        """Handle language change event.
        
        Args:
            language_code: New language code
        """
        self.logger.info(f"Language changed to: {language_code}")
        
        # Update window title
        self.title(_("tools.brain_dump"))
        
        # Update all UI labels
        self._update_ui_labels()
        
        # Update category options
        self.category_menu.configure(values=self._get_translated_categories())
        
        # Update placeholders
        self.title_entry.configure(placeholder_text=_("brain_dump.title_placeholder"))
        self.tags_entry.configure(placeholder_text=_("brain_dump.tags_placeholder"))
        
        # Call registered callbacks
        for callback in self.language_change_callbacks:
            try:
                callback(language_code)
            except Exception as e:
                self.logger.error(f"Error in language change callback: {e}")
    
    def _update_ui_labels(self):
        """Update all UI labels with current language."""
        # Update labels
        self.title_label.configure(text=f"📝 {_("ui_components.title")}:")
        self.category_label.configure(text=f"📁 {_("ui_components.category")}:")
        self.tags_label.configure(text=f"🏷️ {_("ui_components.tags")}:")
        self.quick_actions_label.configure(text=f"⚡ {_("brain_dump.quick_actions")}")
        self.content_label.configure(text=f"✍️ {_("brain_dump.content")}")
        
        # Update buttons
        self.record_btn.configure(text=f"🎤 {_("voice.record")}")
        self.save_btn.configure(text=f"💾 {_("buttons.save")}")
        self.clear_btn.configure(text=f"🗑️ {_("buttons.clear")}")
        self.load_btn.configure(text=_("buttons.load"))
        self.export_btn.configure(text=_("export.export_data"))
        
        if hasattr(self, 'file_ops_label'):
            self.file_ops_label.configure(text=f"📁 {_("brain_dump.file_operations")}")
        
        if hasattr(self, 'ai_label'):
            self.ai_label.configure(text=f"🤖 {_("brain_dump.ai_analysis")}")
            self.analyze_btn.configure(text=_("brain_dump.analyze"))
            self.organize_btn.configure(text=_("brain_dump.organize"))
        
        # Update word count
        current_count = self.current_dump.get('word_count', 0)
        self.word_count_label.configure(text=_("brain_dump.word_count", count=current_count))
    
    def _on_title_change(self, event=None):
        """Handle title change."""
        self.current_dump['title'] = self.title_entry.get()
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._schedule_auto_save()
    
    def _on_category_change(self, value):
        """Handle category change."""
        self.current_dump['category'] = value
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._schedule_auto_save()
    
    def _on_tags_change(self, event=None):
        """Handle tags change."""
        tags_text = self.tags_entry.get()
        self.current_dump['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._schedule_auto_save()
    
    def _on_content_change(self, event=None):
        """Handle content change."""
        content = self.content_text.get("1.0", "end-1c")
        self.current_dump['content'] = content
        self.current_dump['updated_at'] = datetime.now().isoformat()
        
        # Update word count
        word_count = len(content.split()) if content.strip() else 0
        self.current_dump['word_count'] = word_count
        self.word_count_label.configure(text=_("brain_dump.word_count", count=word_count))
        
        self._schedule_auto_save()
    
    def _toggle_voice_recording(self):
        """Toggle voice recording."""
        if not self.audio_service:
            show_message(self, _("voice.microphone_error"), message_type="error")
            return
        
        if not self.is_recording:
            self._start_voice_recording()
        else:
            self._stop_voice_recording()
    
    def _start_voice_recording(self):
        """Start voice recording."""
        self.is_recording = True
        self.record_btn.configure(
            text=f"⏹️ {_("voice.stop_recording")}",
            fg_color="#E74C3C",
            hover_color="#C0392B"
        )
        
        # Show status
        show_message(self, _("voice.listening"), message_type="info")
        
        # Start recording in background
        threading.Thread(target=self._record_voice, daemon=True).start()
    
    def _stop_voice_recording(self):
        """Stop voice recording."""
        self.is_recording = False
        self.record_btn.configure(
            text=f"🎤 {_("voice.record")}",
            fg_color=None,
            hover_color=None
        )
    
    def _record_voice(self):
        """Record voice in background thread."""
        try:
            # Simulate voice recording (replace with actual implementation)
            import time
            time.sleep(2)  # Simulate recording time
            
            if self.is_recording:
                # Simulate transcription
                transcribed_text = _("voice.sample_transcription")
                
                # Add to content
                current_content = self.content_text.get("1.0", "end-1c")
                if current_content.strip():
                    new_content = current_content + "\n\n" + transcribed_text
                else:
                    new_content = transcribed_text
                
                # Update UI in main thread
                self.after(0, lambda: self.content_text.delete("1.0", "end"))
                self.after(0, lambda: self.content_text.insert("1.0", new_content))
                self.after(0, self._stop_voice_recording)
                
        except Exception as e:
            self.logger.error(f"Voice recording error: {e}")
            self.after(0, lambda: show_message(self, _("voice.microphone_error"), message_type="error"))
            self.after(0, self._stop_voice_recording)
    
    def _save_dump(self):
        """Save current brain dump."""
        try:
            if self.database_manager:
                # Save to database
                self.database_manager.save_brain_dump(self.current_dump)
                show_message(self, _("messages.save_success"), message_type="success")
            else:
                # Save to file
                filename = filedialog.asksaveasfilename(
                    title=_("brain_dump.save_title"),
                    defaultextension=".json",
                    filetypes=[(_("brain_dump.json_files"), "*.json"), (_("ui_components.all_files"), "*.*")]
                )
                
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.current_dump, f, ensure_ascii=False, indent=2)
                    show_message(self, _("messages.save_success"), message_type="success")
                    
        except Exception as e:
            self.logger.error(f"Save error: {e}")
            show_message(self, _("messages.save_error"), message_type="error")
    
    def _load_dump(self):
        """Load a brain dump."""
        try:
            filename = filedialog.askopenfilename(
                title=_("brain_dump.load_title"),
                filetypes=[(_("brain_dump.json_files"), "*.json"), (_("ui_components.all_files"), "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    loaded_dump = json.load(f)
                
                # Update UI
                self.current_dump = loaded_dump
                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, loaded_dump.get('title', ''))
                self.category_var.set(loaded_dump.get('category', _("categories.general")))
                self.tags_entry.delete(0, "end")
                self.tags_entry.insert(0, ', '.join(loaded_dump.get('tags', [])))
                self.content_text.delete("1.0", "end")
                self.content_text.insert("1.0", loaded_dump.get('content', ''))
                
                show_message(self, _("messages.load_success"), message_type="success")
                
        except Exception as e:
            self.logger.error(f"Load error: {e}")
            show_message(self, _("messages.load_error"), message_type="error")
    
    def _export_dump(self):
        """Export brain dump to various formats."""
        # Implementation would go here
        show_message(self, _("brain_dump.export_feature_coming_soon"), message_type="info")
    
    def _clear_dump(self):
        """Clear current brain dump."""
        if show_confirmation(self, _("messages.clear_confirm")):
            self.current_dump = {
                'id': str(uuid.uuid4()),
                'title': '',
                'content': '',
                'tags': [],
                'category': _("categories.general"),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'word_count': 0,
                'analysis': None
            }
            
            # Clear UI
            self.title_entry.delete(0, "end")
            self.category_var.set(_("categories.general"))
            self.tags_entry.delete(0, "end")
            self.content_text.delete("1.0", "end")
            self.word_count_label.configure(text=_("brain_dump.word_count", count=0))
    
    def _analyze_content(self):
        """Analyze content with AI."""
        if not self.ai_service:
            show_message(self, _("messages.ai_service_error"), message_type="error")
            return
        
        content = self.current_dump.get('content', '').strip()
        if not content:
            show_message(self, _("brain_dump.no_content_to_analyze"), message_type="warning")
            return
        
        # Implementation would go here
        show_message(self, _("brain_dump.analysis_feature_coming_soon"), message_type="info")
    
    def _organize_content(self):
        """Organize content with AI."""
        if not self.ai_service:
            show_message(self, _("messages.ai_service_error"), message_type="error")
            return
        
        content = self.current_dump.get('content', '').strip()
        if not content:
            show_message(self, _("brain_dump.no_content_to_organize"), message_type="warning")
            return
        
        # Implementation would go here
        show_message(self, _("brain_dump.organize_feature_coming_soon"), message_type="info")
    
    def _schedule_auto_save(self):
        """Schedule auto-save."""
        if self.auto_save_enabled:
            if self.auto_save_timer:
                self.after_cancel(self.auto_save_timer)
            self.auto_save_timer = self.after(5000, self._auto_save)  # 5 seconds
    
    def _auto_save(self):
        """Perform auto-save."""
        try:
            if self.database_manager:
                self.database_manager.auto_save_brain_dump(self.current_dump)
                self.logger.debug("Auto-saved brain dump")
        except Exception as e:
            self.logger.error(f"Auto-save error: {e}")
    
    def _start_auto_save_timer(self):
        """Start the auto-save timer."""
        if self.auto_save_enabled:
            self._schedule_auto_save()


# Additional translations needed for this example
# These would be added to the translation files:
"""
Additional translations for en.json:
{
  "brain_dump": {
    "title_placeholder": "Title of your brain dump...",
    "tags_placeholder": "tag1, tag2, tag3...",
    "quick_actions": "Quick Actions",
    "content": "Content",
    "word_count": "Words: {count}",
    "file_operations": "File Operations",
    "ai_analysis": "AI Analysis",
    "analyze": "Analyze",
    "organize": "Organize",
    "save_title": "Save Brain Dump",
    "load_title": "Load Brain Dump",
    "json_files": "JSON Files",
    "no_content_to_analyze": "No content to analyze",
    "no_content_to_organize": "No content to organize",
    "analysis_feature_coming_soon": "Analysis feature coming soon!",
    "organize_feature_coming_soon": "Organize feature coming soon!",
    "export_feature_coming_soon": "Export feature coming soon!"
  },
  "categories": {
    "general": "General",
    "ideas": "Ideas",
    "projects": "Projects",
    "reflections": "Reflections",
    "notes": "Notes",
    "creative": "Creative",
    "problems": "Problems"
  },
  "voice": {
    "record": "Record",
    "stop_recording": "Stop",
    "sample_transcription": "This is a sample transcription from voice input."
  },
  "ui_components": {
    "title": "Title",
    "category": "Category",
    "tags": "Tags",
    "all_files": "All Files",
    "input_dialog": "Input"
  },
  "buttons": {
    "clear": "Clear",
    "confirm": "Confirm"
  },
  "messages": {
    "clear_confirm": "Are you sure you want to clear all content?"
  }
}

Corresponding French translations for fr.json:
{
  "brain_dump": {
    "title_placeholder": "Titre de votre décharge...",
    "tags_placeholder": "tag1, tag2, tag3...",
    "quick_actions": "Actions Rapides",
    "content": "Contenu",
    "word_count": "Mots : {count}",
    "file_operations": "Opérations de Fichier",
    "ai_analysis": "Analyse IA",
    "analyze": "Analyser",
    "organize": "Organiser",
    "save_title": "Sauvegarder la Décharge",
    "load_title": "Charger une Décharge",
    "json_files": "Fichiers JSON",
    "no_content_to_analyze": "Aucun contenu à analyser",
    "no_content_to_organize": "Aucun contenu à organiser",
    "analysis_feature_coming_soon": "Fonctionnalité d'analyse bientôt disponible !",
    "organize_feature_coming_soon": "Fonctionnalité d'organisation bientôt disponible !",
    "export_feature_coming_soon": "Fonctionnalité d'export bientôt disponible !"
  },
  "categories": {
    "general": "Général",
    "ideas": "Idées",
    "projects": "Projets",
    "reflections": "Réflexions",
    "notes": "Notes",
    "creative": "Créatif",
    "problems": "Problèmes"
  },
  "voice": {
    "record": "Enregistrer",
    "stop_recording": "Arrêter",
    "sample_transcription": "Ceci est un exemple de transcription d'entrée vocale."
  },
  "ui_components": {
    "title": "Titre",
    "category": "Catégorie",
    "tags": "Étiquettes",
    "all_files": "Tous les Fichiers",
    "input_dialog": "Saisie"
  },
  "buttons": {
    "clear": "Effacer",
    "confirm": "Confirmer"
  },
  "messages": {
    "clear_confirm": "Êtes-vous sûr de vouloir effacer tout le contenu ?"
  }
}
"""

if __name__ == "__main__":
    # Example usage
    import customtkinter as ctk
    from core.i18n import initialize_i18n
    
    # Initialize i18n system
    initialize_i18n('fr')  # Start with French
    
    # Create main window
    root = ctk.CTk()
    root.title("Brain Dump i18n Example")
    root.geometry("800x600")
    
    # Create tool
    tool = BrainDumpToolI18n(root, magic_energy_level='genie')
    tool.pack(fill="both", expand=True)
    
    # Run
    root.mainloop()