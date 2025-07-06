#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Brain Dump Tool

Tool for capturing and organizing thoughts, ideas, and mental notes.
Supports both Magic (simple) and Genie (AI-powered) modes.
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

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class BrainDumpTool(BaseToolWindow):
    """Brain Dump tool for capturing and organizing thoughts."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Brain Dump tool."""
        # Initialize tool-specific attributes BEFORE calling super()
        # Brain dump data
        self.current_dump = {
            'id': str(uuid.uuid4()),
            'title': '',
            'content': '',
            'tags': [],
            'category': 'Général',
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
        
        # Now call parent initialization
        super().__init__(
            parent, 
            "Décharge de Pensées", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        self.logger.info("Brain Dump tool initialized")
    
    def _setup_tool_content(self):
        """Setup Brain Dump specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Top panel - Controls and metadata
        self._create_controls_panel()
        
        # Main content area
        self._create_content_area()
        
        # Bottom panel - Actions and insights
        self._create_actions_panel()
        
        # Start auto-save timer
        self._start_auto_save_timer()
    
    def _create_controls_panel(self):
        """Create controls panel."""
        controls_panel = ctk.CTkFrame(self.content_frame, height=100)
        controls_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        controls_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - Title and metadata
        metadata_frame = ctk.CTkFrame(controls_panel)
        metadata_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Title
        title_frame = ctk.CTkFrame(metadata_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="📝 Titre:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            height=30
        )
        self.title_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.title_entry.bind("<KeyRelease>", self._on_title_change)
        
        # Category and tags
        meta_frame = ctk.CTkFrame(metadata_frame, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Category
        ctk.CTkLabel(
            meta_frame,
            text="📁 Catégorie:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.category_var = ctk.StringVar(value="Général")
        category_menu = ctk.CTkOptionMenu(
            meta_frame,
            variable=self.category_var,
            values=["Général", "Idées", "Projets", "Réflexions", "Notes", "Créatif", "Problèmes"],
            width=120,
            command=self._on_category_change
        )
        category_menu.pack(side="left", padx=(5, 15))
        
        # Tags
        ctk.CTkLabel(
            meta_frame,
            text="🏷️ Tags:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.tags_entry = ctk.CTkEntry(
            meta_frame,
            width=200
        )
        self.tags_entry.pack(side="left", padx=(5, 0))
        self.tags_entry.bind("<KeyRelease>", self._on_tags_change)
        
        # Center - Quick actions
        actions_frame = ctk.CTkFrame(controls_panel)
        actions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        
        ctk.CTkLabel(
            actions_frame,
            text="⚡ Actions Rapides",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        quick_actions = ctk.CTkFrame(actions_frame, fg_color="transparent")
        quick_actions.pack(fill="x", padx=10, pady=(0, 10))
        
        # Voice recording
        self.record_btn = ctk.CTkButton(
            quick_actions,
            text="🎤 Enregistrer",
            height=30,
            width=100,
            command=self._toggle_voice_recording
        )
        self.record_btn.pack(side="left", padx=(0, 5))
        
        # Quick save
        save_btn = ctk.CTkButton(
            quick_actions,
            text="💾 Sauver",
            height=30,
            width=80,
            command=self._save_dump
        )
        save_btn.pack(side="left", padx=5)
        
        # Clear
        clear_btn = ctk.CTkButton(
            quick_actions,
            text="🗑️ Effacer",
            height=30,
            width=80,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_dump
        )
        clear_btn.pack(side="left", padx=5)
        
        # Templates
        template_btn = ctk.CTkButton(
            quick_actions,
            text="📋 Modèles",
            height=30,
            width=90,
            command=self._show_templates
        )
        template_btn.pack(side="left", padx=(5, 0))
        
        # Right side - AI features (Genie mode only)
        if self.is_ai_enabled:
            ai_frame = ctk.CTkFrame(controls_panel)
            ai_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
            
            ctk.CTkLabel(
                ai_frame,
                text="🤖 IA Assistant",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=(10, 5))
            
            ai_actions = ctk.CTkFrame(ai_frame, fg_color="transparent")
            ai_actions.pack(fill="x", padx=10, pady=(0, 10))
            
            analyze_btn = ctk.CTkButton(
                ai_actions,
                text="🔍 Analyser",
                height=30,
                width=90,
                fg_color="#4ECDC4",
                hover_color="#45B7B8",
                command=self._ai_analyze_content
            )
            analyze_btn.pack(side="top", pady=(0, 5))
            
            organize_btn = ctk.CTkButton(
                ai_actions,
                text="📊 Organiser",
                height=30,
                width=90,
                fg_color="#9B59B6",
                hover_color="#8E44AD",
                command=self._ai_organize_content
            )
            organize_btn.pack(side="top")
    
    def _create_content_area(self):
        """Create main content area."""
        content_area = ctk.CTkFrame(self.content_frame)
        content_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content_area.grid_columnconfigure(0, weight=2)
        content_area.grid_columnconfigure(1, weight=1)
        content_area.grid_rowconfigure(0, weight=1)
        
        # Main text area
        text_frame = ctk.CTkFrame(content_area)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(1, weight=1)
        
        # Text area header
        text_header = ctk.CTkFrame(text_frame, height=40, fg_color="transparent")
        text_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        text_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            text_header,
            text="✍️ Votre Décharge de Pensées",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Word count
        self.word_count_label = ctk.CTkLabel(
            text_header,
            text="0 mots",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.word_count_label.grid(row=0, column=1, sticky="e")
        
        # Auto-save indicator
        self.auto_save_label = ctk.CTkLabel(
            text_header,
            text="💾 Auto-sauvegarde",
            font=ctk.CTkFont(size=10),
            text_color="green"
        )
        self.auto_save_label.grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        # Main text widget
        self.text_widget = ctk.CTkTextbox(
            text_frame,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.text_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.text_widget.bind("<KeyRelease>", self._on_text_change)
        self.text_widget.bind("<Button-1>", self._on_text_click)
        
        # Side panel - Analysis and insights
        side_panel = ctk.CTkFrame(content_area)
        side_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        side_panel.grid_columnconfigure(0, weight=1)
        side_panel.grid_rowconfigure(1, weight=1)
        
        # Side panel header
        side_header = ctk.CTkFrame(side_panel, height=40, fg_color="transparent")
        side_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            side_header,
            text="📊 Insights",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        
        # Insights content
        self.insights_frame = ctk.CTkScrollableFrame(side_panel)
        self.insights_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Initial insights
        self._show_initial_insights()
    
    def _create_actions_panel(self):
        """Create actions panel."""
        actions_panel = ctk.CTkFrame(self.content_frame, height=70)
        actions_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        actions_panel.grid_columnconfigure(1, weight=1)
        
        # Left actions
        left_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        new_btn = ctk.CTkButton(
            left_actions,
            text="📄 Nouveau",
            height=35,
            command=self._new_dump
        )
        new_btn.pack(side="left", padx=(0, 5))
        
        load_btn = ctk.CTkButton(
            left_actions,
            text="📂 Charger",
            height=35,
            command=self._load_dump
        )
        load_btn.pack(side="left", padx=5)
        
        history_btn = ctk.CTkButton(
            left_actions,
            text="📚 Historique",
            height=35,
            command=self._show_history
        )
        history_btn.pack(side="left", padx=5)
        
        # Center - Status
        status_frame = ctk.CTkFrame(actions_panel, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="", padx=15, pady=15)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✨ Prêt à capturer vos pensées",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack()
        
        # Right actions
        right_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        right_actions.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        export_btn = ctk.CTkButton(
            right_actions,
            text="📤 Exporter",
            height=35,
            command=self._export_dump
        )
        export_btn.pack(side="left", padx=5)
        
        share_btn = ctk.CTkButton(
            right_actions,
            text="🔗 Partager",
            height=35,
            command=self._share_dump
        )
        share_btn.pack(side="left", padx=(5, 0))
    
    def _show_initial_insights(self):
        """Show initial insights in the side panel."""
        # Clear existing insights
        for widget in self.insights_frame.winfo_children():
            widget.destroy()
        
        # Welcome message
        welcome_frame = ctk.CTkFrame(self.insights_frame, fg_color="transparent")
        welcome_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            welcome_frame,
            text="💡 Conseils",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack()
        
        tips = [
            "Écrivez librement sans vous censurer",
            "Utilisez des mots-clés pour retrouver vos idées",
            "L'IA peut analyser vos pensées",
            "Sauvegardez régulièrement vos réflexions"
        ]
        
        for tip in tips:
            tip_label = ctk.CTkLabel(
                welcome_frame,
                text=f"• {tip}",
                font=ctk.CTkFont(size=10),
                text_color="gray",
                wraplength=200,
                justify="left"
            )
            tip_label.pack(anchor="w", pady=1)
        
        # Quick stats
        stats_frame = ctk.CTkFrame(self.insights_frame)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(
            stats_frame,
            text="📈 Statistiques",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        self.stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="x", padx=10, pady=(0, 10))
        
        self._update_stats_display()
    
    def _update_stats_display(self):
        """Update statistics display."""
        # Clear existing stats
        for widget in self.stats_content.winfo_children():
            widget.destroy()
        
        # Word count
        word_count = len(self.text_widget.get("1.0", "end").split())
        
        stats = [
            ("📝", "Mots", str(word_count)),
            ("⏱️", "Temps", self._get_session_time()),
            ("🏷️", "Tags", str(len(self.current_dump['tags']))),
            ("📁", "Catégorie", self.current_dump['category'])
        ]
        
        for icon, label, value in stats:
            stat_frame = ctk.CTkFrame(self.stats_content, fg_color="transparent")
            stat_frame.pack(fill="x", pady=1)
            
            ctk.CTkLabel(
                stat_frame,
                text=f"{icon} {label}:",
                font=ctk.CTkFont(size=10),
                width=80
            ).pack(side="left")
            
            ctk.CTkLabel(
                stat_frame,
                text=value,
                font=ctk.CTkFont(size=10, weight="bold")
            ).pack(side="right")
    
    def _get_session_time(self) -> str:
        """Get current session time."""
        created_time = datetime.fromisoformat(self.current_dump['created_at'])
        session_duration = datetime.now() - created_time
        
        minutes = int(session_duration.total_seconds() // 60)
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}h{remaining_minutes:02d}m"
    
    def _on_title_change(self, event=None):
        """Handle title change."""
        self.current_dump['title'] = self.title_entry.get()
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._schedule_auto_save()
    
    def _on_category_change(self, value):
        """Handle category change."""
        self.current_dump['category'] = value
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._update_stats_display()
        self._schedule_auto_save()
    
    def _on_tags_change(self, event=None):
        """Handle tags change."""
        tags_text = self.tags_entry.get()
        # Parse tags (comma-separated)
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        self.current_dump['tags'] = tags
        self.current_dump['updated_at'] = datetime.now().isoformat()
        self._update_stats_display()
        self._schedule_auto_save()
    
    def _on_text_change(self, event=None):
        """Handle text content change."""
        content = self.text_widget.get("1.0", "end-1c")
        self.current_dump['content'] = content
        self.current_dump['updated_at'] = datetime.now().isoformat()
        
        # Update word count
        self._update_word_count()
        
        # Schedule auto-save
        self._schedule_auto_save()
        
        # Update insights if AI is enabled
        if self.is_ai_enabled and len(content.split()) > 10:
            self._schedule_ai_analysis()
    
    def _on_text_click(self, event=None):
        """Handle text widget click."""
        # Could be used for cursor position insights
        pass
    
    def _update_word_count(self):
        """Update word count display."""
        content = self.text_widget.get("1.0", "end-1c")
        words = content.split()
        word_count = len([word for word in words if word.strip()])
        
        self.current_dump['word_count'] = word_count
        self.word_count_label.configure(text=f"{word_count} mots")
        
        # Update stats
        self._update_stats_display()
    
    def _schedule_auto_save(self):
        """Schedule auto-save."""
        if not self.auto_save_enabled:
            return
        
        # Cancel existing timer
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        # Schedule new save
        self.auto_save_timer = threading.Timer(3.0, self._auto_save)
        self.auto_save_timer.start()
    
    def _auto_save(self):
        """Perform auto-save."""
        try:
            if self.database_manager:
                # Save to database
                self.database_manager.save_brain_dump(
                    dump_id=self.current_dump['id'],
                    title=self.current_dump['title'] or "Sans titre",
                    content=self.current_dump['content'],
                    category=self.current_dump['category'],
                    tags=','.join(self.current_dump['tags']),
                    analysis=json.dumps(self.current_dump['analysis']) if self.current_dump['analysis'] else None
                )
            
            # Update status
            self.auto_save_label.configure(
                text="💾 Sauvegardé",
                text_color="green"
            )
            
            # Reset status after 2 seconds
            self.after(2000, lambda: self.auto_save_label.configure(
                text="💾 Auto-sauvegarde",
                text_color="gray"
            ))
            
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
            self.auto_save_label.configure(
                text="❌ Erreur sauvegarde",
                text_color="red"
            )
    
    def _schedule_ai_analysis(self):
        """Schedule AI analysis of content."""
        if not self.is_ai_enabled:
            return
        
        # Cancel existing timer
        if hasattr(self, 'ai_analysis_timer') and self.ai_analysis_timer:
            self.ai_analysis_timer.cancel()
        
        # Schedule new analysis (debounced)
        self.ai_analysis_timer = threading.Timer(5.0, self._perform_ai_analysis)
        self.ai_analysis_timer.start()
    
    def _perform_ai_analysis(self):
        """Perform AI analysis of content."""
        content = self.current_dump['content']
        if len(content.split()) < 10:  # Minimum content for analysis
            return
        
        # Check cache
        content_hash = hash(content)
        if content_hash in self.analysis_cache:
            self._display_analysis(self.analysis_cache[content_hash])
            return
        
        def ai_task():
            prompt = f"""
Analyse ce texte de décharge de pensées et fournis des insights:

Texte:
{content}

Fournis une analyse JSON avec:
1. "themes": thèmes principaux identifiés
2. "emotions": émotions détectées
3. "keywords": mots-clés importants
4. "suggestions": suggestions d'amélioration ou d'action
5. "structure_score": score de structure (0-10)
6. "clarity_score": score de clarté (0-10)

Réponds uniquement en JSON valide.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='text_analysis',
                max_tokens=400
            )
            
            return response.get('content', '')
        
        # Run AI analysis in background
        threading.Thread(target=lambda: self._run_ai_analysis(ai_task, content_hash), daemon=True).start()
    
    def _run_ai_analysis(self, ai_task, content_hash):
        """Run AI analysis in background thread."""
        try:
            result = ai_task()
            analysis = json.loads(result)
            
            # Cache result
            self.analysis_cache[content_hash] = analysis
            
            # Update UI in main thread
            self.after(0, lambda: self._display_analysis(analysis))
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
    
    def _display_analysis(self, analysis: Dict):
        """Display AI analysis in insights panel."""
        # Clear existing insights
        for widget in self.insights_frame.winfo_children():
            widget.destroy()
        
        # Analysis header
        header_frame = ctk.CTkFrame(self.insights_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="🤖 Analyse IA",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack()
        
        # Themes
        if 'themes' in analysis:
            themes_frame = ctk.CTkFrame(self.insights_frame)
            themes_frame.pack(fill="x", pady=(0, 5))
            
            ctk.CTkLabel(
                themes_frame,
                text="🎯 Thèmes",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(pady=(5, 2))
            
            for theme in analysis['themes'][:3]:  # Show top 3
                ctk.CTkLabel(
                    themes_frame,
                    text=f"• {theme}",
                    font=ctk.CTkFont(size=10),
                    wraplength=180
                ).pack(anchor="w", padx=10, pady=1)
        
        # Emotions
        if 'emotions' in analysis:
            emotions_frame = ctk.CTkFrame(self.insights_frame)
            emotions_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                emotions_frame,
                text="😊 Émotions",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(pady=(5, 2))
            
            emotions_text = ", ".join(analysis['emotions'][:4])
            ctk.CTkLabel(
                emotions_frame,
                text=emotions_text,
                font=ctk.CTkFont(size=10),
                wraplength=180
            ).pack(padx=10, pady=(0, 5))
        
        # Scores
        if 'structure_score' in analysis or 'clarity_score' in analysis:
            scores_frame = ctk.CTkFrame(self.insights_frame)
            scores_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                scores_frame,
                text="📊 Scores",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(pady=(5, 2))
            
            if 'structure_score' in analysis:
                structure_score = analysis['structure_score']
                ctk.CTkLabel(
                    scores_frame,
                    text=f"Structure: {structure_score}/10",
                    font=ctk.CTkFont(size=10)
                ).pack(padx=10, pady=1)
            
            if 'clarity_score' in analysis:
                clarity_score = analysis['clarity_score']
                ctk.CTkLabel(
                    scores_frame,
                    text=f"Clarté: {clarity_score}/10",
                    font=ctk.CTkFont(size=10)
                ).pack(padx=10, pady=(1, 5))
        
        # Suggestions
        if 'suggestions' in analysis:
            suggestions_frame = ctk.CTkFrame(self.insights_frame)
            suggestions_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                suggestions_frame,
                text="💡 Suggestions",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(pady=(5, 2))
            
            for suggestion in analysis['suggestions'][:2]:  # Show top 2
                ctk.CTkLabel(
                    suggestions_frame,
                    text=f"• {suggestion}",
                    font=ctk.CTkFont(size=10),
                    wraplength=180
                ).pack(anchor="w", padx=10, pady=1)
            
            # Add padding at bottom
            ctk.CTkLabel(suggestions_frame, text="", height=5).pack()
        
        # Store analysis
        self.current_dump['analysis'] = analysis
    
    def _start_auto_save_timer(self):
        """Start the auto-save timer."""
        if self.auto_save_enabled:
            self._schedule_auto_save()
    
    def _toggle_voice_recording(self):
        """Toggle voice recording."""
        if not self.audio_service:
            messagebox.showerror("Erreur", "Service audio non disponible.")
            return
        
        if not self.is_recording:
            self._start_voice_recording()
        else:
            self._stop_voice_recording()
    
    def _start_voice_recording(self):
        """Start voice recording."""
        try:
            self.is_recording = True
            self.record_btn.configure(
                text="⏹️ Arrêter",
                fg_color="#E74C3C",
                hover_color="#C0392B"
            )
            
            self.status_label.configure(text="🎤 Enregistrement en cours...")
            
            # Start recording in background
            def record_task():
                try:
                    text = self.audio_service.listen_for_speech(timeout=30)
                    if text:
                        # Add to text widget
                        self.after(0, lambda: self._add_voice_text(text))
                    else:
                        self.after(0, lambda: self.status_label.configure(
                            text="❌ Aucun texte reconnu"
                        ))
                except Exception as e:
                    self.logger.error(f"Voice recording failed: {e}")
                    self.after(0, lambda: self.status_label.configure(
                        text="❌ Erreur d'enregistrement"
                    ))
                finally:
                    self.after(0, self._stop_voice_recording)
            
            threading.Thread(target=record_task, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            messagebox.showerror("Erreur", f"Impossible de démarrer l'enregistrement: {e}")
            self._stop_voice_recording()
    
    def _stop_voice_recording(self):
        """Stop voice recording."""
        self.is_recording = False
        self.record_btn.configure(
            text="🎤 Enregistrer",
            fg_color=None,
            hover_color=None
        )
        
        self.status_label.configure(text="✨ Prêt à capturer vos pensées")
    
    def _add_voice_text(self, text: str):
        """Add voice-recognized text to the content."""
        current_content = self.text_widget.get("1.0", "end-1c")
        
        # Add separator if there's existing content
        if current_content.strip():
            separator = "\n\n[Vocal] "
        else:
            separator = "[Vocal] "
        
        # Insert text
        self.text_widget.insert("end", separator + text)
        
        # Trigger change event
        self._on_text_change()
        
        self.status_label.configure(text="✅ Texte vocal ajouté")
    
    def _save_dump(self):
        """Manually save the current dump."""
        try:
            if not self.current_dump['title'] and not self.current_dump['content']:
                messagebox.showwarning("Rien à Sauver", "Ajoutez du contenu avant de sauvegarder.")
                return
            
            if self.database_manager:
                self.database_manager.save_brain_dump(
                    dump_id=self.current_dump['id'],
                    title=self.current_dump['title'] or "Sans titre",
                    content=self.current_dump['content'],
                    category=self.current_dump['category'],
                    tags=','.join(self.current_dump['tags']),
                    analysis=json.dumps(self.current_dump['analysis']) if self.current_dump['analysis'] else None
                )
                
                messagebox.showinfo("Succès", "Décharge sauvegardée avec succès !")
                self.status_label.configure(text="💾 Sauvegardé")
            else:
                messagebox.showerror("Erreur", "Base de données non disponible.")
                
        except Exception as e:
            self.logger.error(f"Failed to save dump: {e}")
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def _clear_dump(self):
        """Clear the current dump."""
        if self.current_dump['content'] or self.current_dump['title']:
            if not messagebox.askyesno("Confirmer", "Effacer tout le contenu ?"):
                return
        
        # Clear all fields
        self.title_entry.delete(0, 'end')
        self.tags_entry.delete(0, 'end')
        self.text_widget.delete("1.0", "end")
        self.category_var.set("Général")
        
        # Reset dump data
        self.current_dump = {
            'id': str(uuid.uuid4()),
            'title': '',
            'content': '',
            'tags': [],
            'category': 'Général',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'word_count': 0,
            'analysis': None
        }
        
        # Reset UI
        self._show_initial_insights()
        self._update_word_count()
        self.status_label.configure(text="🗑️ Contenu effacé")
    
    def _new_dump(self):
        """Create a new dump."""
        if self.current_dump['content'] or self.current_dump['title']:
            if not messagebox.askyesno("Nouveau", "Créer une nouvelle décharge ? Le contenu actuel sera perdu s'il n'est pas sauvegardé."):
                return
        
        self._clear_dump()
        self.status_label.configure(text="📄 Nouvelle décharge créée")
    
    def _load_dump(self):
        """Load an existing dump."""
        if not self.database_manager:
            messagebox.showerror("Erreur", "Base de données non disponible.")
            return
        
        try:
            dumps = self.database_manager.get_brain_dumps()
            if not dumps:
                messagebox.showinfo("Aucune Décharge", "Aucune décharge trouvée.")
                return
            
            # Show selection dialog
            dialog = DumpSelectionDialog(self, dumps)
            result = dialog.show()
            
            if result and dialog.selected_dump:
                self._load_dump_data(dialog.selected_dump)
                
        except Exception as e:
            self.logger.error(f"Failed to load dumps: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les décharges: {e}")
    
    def _load_dump_data(self, dump_data: Dict):
        """Load dump data into the interface."""
        # Clear current content
        self._clear_dump()
        
        # Load data
        self.current_dump.update({
            'id': dump_data.get('id', str(uuid.uuid4())),
            'title': dump_data.get('title', ''),
            'content': dump_data.get('content', ''),
            'category': dump_data.get('category', 'Général'),
            'created_at': dump_data.get('created_at', datetime.now().isoformat()),
            'updated_at': dump_data.get('updated_at', datetime.now().isoformat())
        })
        
        # Parse tags
        tags_str = dump_data.get('tags', '')
        if tags_str:
            self.current_dump['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # Parse analysis
        analysis_str = dump_data.get('analysis')
        if analysis_str:
            try:
                self.current_dump['analysis'] = json.loads(analysis_str)
            except:
                self.current_dump['analysis'] = None
        
        # Update UI
        self.title_entry.insert(0, self.current_dump['title'])
        self.tags_entry.insert(0, ', '.join(self.current_dump['tags']))
        self.text_widget.insert("1.0", self.current_dump['content'])
        self.category_var.set(self.current_dump['category'])
        
        # Update displays
        self._update_word_count()
        
        if self.current_dump['analysis']:
            self._display_analysis(self.current_dump['analysis'])
        else:
            self._show_initial_insights()
        
        self.status_label.configure(text="📂 Décharge chargée")
    
    def _show_history(self):
        """Show dump history."""
        # TODO: Implement history view
        messagebox.showinfo("Info", "Historique en développement")
    
    def _show_templates(self):
        """Show content templates."""
        templates = {
            "Brainstorming": "🧠 BRAINSTORMING\n\nSujet: \n\nIdées:\n• \n• \n• \n\nConnexions:\n\n\nActions à retenir:\n",
            "Réflexion": "🤔 RÉFLEXION\n\nQuestion/Problème: \n\nContexte:\n\n\nMes pensées:\n\n\nPerspectives différentes:\n\n\nConclusion:\n",
            "Journal": "📔 JOURNAL\n\nDate: {date}\n\nHumeur: \n\nÉvénements marquants:\n\n\nApprentissages:\n\n\nGratitude:\n",
            "Projet": "🚀 PROJET\n\nNom du projet: \n\nObjectif: \n\nIdées clés:\n• \n• \n• \n\nÉtapes suivantes:\n1. \n2. \n3. \n\nRessources nécessaires:\n",
            "Problème": "❓ RÉSOLUTION DE PROBLÈME\n\nProblème: \n\nCauses possibles:\n• \n• \n• \n\nSolutions envisagées:\n1. \n2. \n3. \n\nPlan d'action:\n"
        }
        
        dialog = TemplateSelectionDialog(self, templates)
        result = dialog.show()
        
        if result and dialog.selected_template:
            template_content = dialog.selected_template
            
            # Replace placeholders
            template_content = template_content.replace("{date}", datetime.now().strftime("%d/%m/%Y"))
            
            # Insert template
            current_content = self.text_widget.get("1.0", "end-1c")
            if current_content.strip():
                if not messagebox.askyesno("Remplacer", "Remplacer le contenu actuel par le modèle ?"):
                    return
            
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", template_content)
            self._on_text_change()
    
    def _ai_analyze_content(self):
        """Perform detailed AI analysis."""
        if not self.is_ai_enabled:
            return
        
        content = self.current_dump['content']
        if len(content.split()) < 5:
            messagebox.showwarning("Contenu Insuffisant", "Ajoutez plus de contenu pour l'analyse IA.")
            return
        
        def ai_task():
            prompt = f"""
Fais une analyse approfondie de cette décharge de pensées:

{content}

Fournis une analyse détaillée avec:
1. Résumé en 2-3 phrases
2. Thèmes principaux et sous-thèmes
3. Émotions et sentiments exprimés
4. Structure et cohérence du texte
5. Points forts et points à améliorer
6. Suggestions d'actions concrètes
7. Questions de réflexion pour approfondir

Réponds de manière structurée et bienveillante.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='detailed_analysis',
                max_tokens=600
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _ai_organize_content(self):
        """Organize content with AI."""
        if not self.is_ai_enabled:
            return
        
        content = self.current_dump['content']
        if len(content.split()) < 10:
            messagebox.showwarning("Contenu Insuffisant", "Ajoutez plus de contenu pour l'organisation IA.")
            return
        
        def ai_task():
            prompt = f"""
Réorganise et structure ce texte de décharge de pensées:

{content}

Objectifs:
1. Améliorer la structure et la lisibilité
2. Regrouper les idées similaires
3. Ajouter des titres et sous-titres appropriés
4. Conserver le sens et le style original
5. Ajouter des transitions fluides

Réponds avec le texte réorganisé, prêt à remplacer l'original.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='content_organization',
                max_tokens=800
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _handle_ai_result(self, result):
        """Handle AI analysis result."""
        if not result:
            return
        
        # Show result in a dialog
        dialog = AIResultDialog(self, "Résultat IA", result)
        dialog_result = dialog.show()
        
        if dialog_result and hasattr(dialog, 'apply_result') and dialog.apply_result:
            # Apply organized content if it was an organization task
            if "réorganise" in result.lower() or "structure" in result.lower():
                if messagebox.askyesno("Appliquer", "Remplacer le contenu actuel par la version organisée ?"):
                    self.text_widget.delete("1.0", "end")
                    self.text_widget.insert("1.0", result)
                    self._on_text_change()
    
    def _export_dump(self):
        """Export the current dump."""
        if not self.current_dump['content']:
            messagebox.showwarning("Rien à Exporter", "Aucun contenu à exporter.")
            return
        
        try:
            # Get save location
            filepath = filedialog.asksaveasfilename(
                title="Exporter Brain Dump",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Markdown files", "*.md"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if not filepath:
                return
            
            # Prepare export content
            export_content = f"""
Titre: {self.current_dump['title'] or 'Sans titre'}
Catégorie: {self.current_dump['category']}
Tags: {', '.join(self.current_dump['tags'])}
Date de création: {self.current_dump['created_at']}
Mots: {self.current_dump['word_count']}

{'='*50}

{self.current_dump['content']}
"""
            
            # Export based on file extension
            if filepath.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_dump, f, ensure_ascii=False, indent=2)
            elif filepath.endswith('.md'):
                md_content = f"# {self.current_dump['title'] or 'Brain Dump'}\n\n"
                md_content += f"**Catégorie:** {self.current_dump['category']}\n"
                md_content += f"**Tags:** {', '.join(self.current_dump['tags'])}\n"
                md_content += f"**Date:** {self.current_dump['created_at']}\n\n"
                md_content += "---\n\n"
                md_content += self.current_dump['content']
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(export_content)
            
            self.status_label.configure(text=f"📤 Exporté: {filepath.split('/')[-1]}")
            messagebox.showinfo("Export", f"Dump exporté avec succès:\n{filepath}")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            messagebox.showerror("Erreur", f"Échec de l'export: {e}")
    
    def _share_dump(self):
        """Share the current dump."""
        if not self.current_dump['content']:
            messagebox.showwarning("Rien à Partager", "Aucun contenu à partager.")
            return
        
        try:
            # Prepare share content
            share_content = f"""
📝 {self.current_dump['title'] or 'Brain Dump'}

📁 Catégorie: {self.current_dump['category']}
🏷️ Tags: {', '.join(self.current_dump['tags'])}
📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

{self.current_dump['content']}

---
Partagé depuis Easy Genie Desktop
"""
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(share_content)
            
            self.status_label.configure(text="📋 Copié dans le presse-papiers")
            messagebox.showinfo(
                "Partage", 
                "Contenu copié dans le presse-papiers.\n\nVous pouvez maintenant le coller dans:\n• Email\n• Chat\n• Document\n• Réseaux sociaux"
            )
            
        except Exception as e:
            self.logger.error(f"Share failed: {e}")
            messagebox.showerror("Erreur", f"Échec du partage: {e}")
    
    def _save_data(self):
        """Save current dump data."""
        try:
            self._save_dump()
            super()._save_data()
        except Exception as e:
            self.logger.error(f"Failed to save brain dump: {e}")
    
    def _export_data(self):
        """Export dump data."""
        self._export_dump()


class DumpSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting a brain dump to load."""
    
    def __init__(self, parent, dumps: List[Dict]):
        """Initialize dump selection dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.dumps = dumps
        self.selected_dump = None
        self.result = False
        
        # Configure dialog
        self.title("Charger une Décharge")
        self.geometry("600x400")
        self.resizable(True, True)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _center_on_parent(self):
        """Center dialog on parent."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_dialog(self):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"📂 Charger une Décharge ({len(self.dumps)} disponibles)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Dumps list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.dumps_listbox = ctk.CTkScrollableFrame(list_frame)
        self.dumps_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create dump items
        self.dump_vars = []
        for i, dump in enumerate(self.dumps):
            var = ctk.StringVar()
            self.dump_vars.append(var)
            
            dump_frame = ctk.CTkFrame(self.dumps_listbox)
            dump_frame.pack(fill="x", pady=3)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                dump_frame,
                text="",
                variable=var,
                value=str(i),
                width=20
            )
            radio.pack(side="left", padx=(10, 10), pady=10)
            
            # Dump info
            info_frame = ctk.CTkFrame(dump_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
            
            # Title
            title = dump.get('title', 'Sans titre')
            title_label = ctk.CTkLabel(
                info_frame,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            title_label.pack(anchor="w")
            
            # Details
            details = []
            if dump.get('category'):
                details.append(f"📁 {dump['category']}")
            
            # Word count
            content = dump.get('content', '')
            word_count = len(content.split())
            details.append(f"📝 {word_count} mots")
            
            # Date
            try:
                created_at = dump.get('created_at', '')
                if created_at:
                    date = datetime.fromisoformat(created_at)
                    details.append(f"📅 {date.strftime('%d/%m/%Y %H:%M')}")
            except:
                pass
            
            if details:
                details_label = ctk.CTkLabel(
                    info_frame,
                    text=" • ".join(details),
                    font=ctk.CTkFont(size=10),
                    text_color="gray",
                    anchor="w"
                )
                details_label.pack(anchor="w")
            
            # Preview
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                preview_label = ctk.CTkLabel(
                    info_frame,
                    text=preview,
                    font=ctk.CTkFont(size=9),
                    text_color="gray",
                    anchor="w",
                    wraplength=400
                )
                preview_label.pack(anchor="w", pady=(2, 0))
            
            # Bind click to select
            for widget in [dump_frame, info_frame, title_label]:
                widget.bind("<Button-1>", lambda e, idx=i: self._select_dump(idx))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        load_btn = ctk.CTkButton(
            buttons_frame,
            text="Charger",
            command=self._on_load
        )
        load_btn.pack(side="right")
    
    def _select_dump(self, index: int):
        """Select a dump."""
        for i, var in enumerate(self.dump_vars):
            if i == index:
                var.set(str(i))
            else:
                var.set("")
    
    def _on_load(self):
        """Handle load button."""
        selected_index = None
        for i, var in enumerate(self.dump_vars):
            if var.get() == str(i):
                selected_index = i
                break
        
        if selected_index is None:
            messagebox.showwarning("Aucune Sélection", "Veuillez sélectionner une décharge.")
            return
        
        self.selected_dump = self.dumps[selected_index]
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result


class TemplateSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting content templates."""
    
    def __init__(self, parent, templates: Dict[str, str]):
        """Initialize template selection dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.templates = templates
        self.selected_template = None
        self.result = False
        
        # Configure dialog
        self.title("Choisir un Modèle")
        self.geometry("500x400")
        self.resizable(True, True)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _center_on_parent(self):
        """Center dialog on parent."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_dialog(self):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📋 Choisir un Modèle",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Templates list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.templates_listbox = ctk.CTkScrollableFrame(list_frame)
        self.templates_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create template items
        self.template_vars = []
        template_names = list(self.templates.keys())
        
        for i, template_name in enumerate(template_names):
            var = ctk.StringVar()
            self.template_vars.append(var)
            
            template_frame = ctk.CTkFrame(self.templates_listbox)
            template_frame.pack(fill="x", pady=3)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                template_frame,
                text="",
                variable=var,
                value=str(i),
                width=20
            )
            radio.pack(side="left", padx=(10, 10), pady=10)
            
            # Template info
            info_frame = ctk.CTkFrame(template_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
            
            # Template name
            name_label = ctk.CTkLabel(
                info_frame,
                text=template_name,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            name_label.pack(anchor="w")
            
            # Template preview
            template_content = self.templates[template_name]
            preview = template_content[:150] + "..." if len(template_content) > 150 else template_content
            preview_label = ctk.CTkLabel(
                info_frame,
                text=preview,
                font=ctk.CTkFont(size=9),
                text_color="gray",
                anchor="w",
                wraplength=400
            )
            preview_label.pack(anchor="w", pady=(2, 0))
            
            # Bind click to select
            for widget in [template_frame, info_frame, name_label]:
                widget.bind("<Button-1>", lambda e, idx=i: self._select_template(idx))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Appliquer",
            command=self._on_apply
        )
        apply_btn.pack(side="right")
    
    def _select_template(self, index: int):
        """Select a template."""
        for i, var in enumerate(self.template_vars):
            if i == index:
                var.set(str(i))
            else:
                var.set("")
    
    def _on_apply(self):
        """Handle apply button."""
        selected_index = None
        for i, var in enumerate(self.template_vars):
            if var.get() == str(i):
                selected_index = i
                break
        
        if selected_index is None:
            messagebox.showwarning("Aucune Sélection", "Veuillez sélectionner un modèle.")
            return
        
        template_names = list(self.templates.keys())
        template_name = template_names[selected_index]
        self.selected_template = self.templates[template_name]
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result


class AIResultDialog(ctk.CTkToplevel):
    """Dialog for displaying AI analysis results."""
    
    def __init__(self, parent, title: str, content: str):
        """Initialize AI result dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.content = content
        self.apply_result = False
        self.result = False
        
        # Configure dialog
        self.title(title)
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
    def _center_on_parent(self):
        """Center dialog on parent."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_dialog(self):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🤖 Résultat de l'Analyse IA",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Content area
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Text widget for content
        self.content_text = ctk.CTkTextbox(
            content_frame,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.content_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Insert content
        self.content_text.insert("1.0", self.content)
        self.content_text.configure(state="disabled")
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew")
        
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="Fermer",
            command=self._on_close
        )
        close_btn.pack(side="left")
        
        copy_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Copier",
            command=self._on_copy
        )
        copy_btn.pack(side="left", padx=(10, 0))
        
        # Apply button (for organization results)
        if "réorganise" in self.content.lower() or "structure" in self.content.lower():
            apply_btn = ctk.CTkButton(
                buttons_frame,
                text="✅ Appliquer",
                fg_color="#27AE60",
                hover_color="#229954",
                command=self._on_apply
            )
            apply_btn.pack(side="right")
    
    def _on_copy(self):
        """Copy content to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.content)
            messagebox.showinfo("Copié", "Contenu copié dans le presse-papiers.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier: {e}")
    
    def _on_apply(self):
        """Apply the result."""
        self.apply_result = True
        self.result = True
        self.destroy()
    
    def _on_close(self):
        """Handle close."""
        self.result = True
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result


# Test block for direct execution
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directories to path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, parent_dir)
    
    # Create test application
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Test Brain Dump Tool")
    root.geometry("1200x800")
    
    # Create tool instance
    tool = BrainDumpTool(
        parent=root,
        magic_energy_level='genie'  # Test with AI features
    )
    tool.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()