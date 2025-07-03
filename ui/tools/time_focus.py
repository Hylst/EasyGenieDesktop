#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - TimeFocus Tool

Tool for time management and focus sessions using Pomodoro technique.
Supports both Magic (simple) and Genie (AI-powered) modes.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable
import json
from datetime import datetime, timedelta
import threading
import time
import uuid

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class TimeFocusTool(BaseToolWindow):
    """TimeFocus tool for time management and focus sessions."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize TimeFocus tool."""
        super().__init__(
            parent, 
            "TimeFocus", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Timer state
        self.current_session = None
        self.timer_thread = None
        self.is_running = False
        self.is_paused = False
        self.remaining_time = 0
        self.session_start_time = None
        
        # Session data
        self.sessions_history = []
        self.current_task = None
        self.daily_stats = {
            'focus_sessions': 0,
            'break_sessions': 0,
            'total_focus_time': 0,
            'total_break_time': 0,
            'interruptions': 0
        }
        
        # Settings
        self.focus_duration = 25 * 60  # 25 minutes
        self.short_break_duration = 5 * 60  # 5 minutes
        self.long_break_duration = 15 * 60  # 15 minutes
        self.sessions_until_long_break = 4
        
        # Callbacks
        self.timer_callbacks = []
        
        self.logger.info("TimeFocus tool initialized")
    
    def _setup_tool_content(self):
        """Setup TimeFocus specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Create main container
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Left panel - Timer and controls
        self._create_timer_panel(main_container)
        
        # Right panel - Task and statistics
        self._create_info_panel(main_container)
        
        # Bottom panel - Session history
        self._create_history_panel(main_container)
    
    def _create_timer_panel(self, parent):
        """Create timer panel."""
        timer_panel = ctk.CTkFrame(parent, width=400)
        timer_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5), pady=0)
        timer_panel.grid_propagate(False)
        
        # Panel title
        title_label = ctk.CTkLabel(
            timer_panel,
            text="⏰ Session de Focus",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Session type indicator
        self.session_type_label = ctk.CTkLabel(
            timer_panel,
            text="Prêt à commencer",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.session_type_label.pack(pady=(0, 20))
        
        # Timer display
        timer_frame = ctk.CTkFrame(timer_panel, height=200, corner_radius=100)
        timer_frame.pack(pady=20, padx=40)
        timer_frame.pack_propagate(False)
        
        self.timer_display = ctk.CTkLabel(
            timer_frame,
            text="25:00",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#2ECC71"
        )
        self.timer_display.pack(expand=True)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            timer_panel,
            width=300,
            height=8,
            progress_color="#2ECC71"
        )
        self.progress_bar.pack(pady=(10, 20))
        self.progress_bar.set(0)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(timer_panel, fg_color="transparent")
        controls_frame.pack(pady=20)
        
        self.start_btn = ctk.CTkButton(
            controls_frame,
            text="▶️ Démarrer",
            height=50,
            width=120,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self._start_timer
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = ctk.CTkButton(
            controls_frame,
            text="⏸️ Pause",
            height=50,
            width=120,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#F39C12",
            hover_color="#E67E22",
            command=self._pause_timer,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹️ Arrêter",
            height=50,
            width=120,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._stop_timer,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Session settings
        settings_frame = ctk.CTkFrame(timer_panel)
        settings_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            settings_frame,
            text="⚙️ Paramètres de Session",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Focus duration
        focus_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        focus_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(focus_frame, text="Focus:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.focus_duration_var = ctk.StringVar(value="25")
        focus_menu = ctk.CTkOptionMenu(
            focus_frame,
            variable=self.focus_duration_var,
            values=["15", "20", "25", "30", "45", "60"],
            width=80,
            command=self._update_focus_duration
        )
        focus_menu.pack(side="right")
        
        ctk.CTkLabel(focus_frame, text="minutes", font=ctk.CTkFont(size=11)).pack(side="right", padx=(5, 10))
        
        # Break duration
        break_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        break_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(break_frame, text="Pause courte:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.break_duration_var = ctk.StringVar(value="5")
        break_menu = ctk.CTkOptionMenu(
            break_frame,
            variable=self.break_duration_var,
            values=["3", "5", "10", "15"],
            width=80,
            command=self._update_break_duration
        )
        break_menu.pack(side="right")
        
        ctk.CTkLabel(break_frame, text="minutes", font=ctk.CTkFont(size=11)).pack(side="right", padx=(5, 10))
        
        # Auto-start breaks
        auto_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        auto_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.auto_start_var = ctk.BooleanVar(value=True)
        auto_checkbox = ctk.CTkCheckBox(
            auto_frame,
            text="Démarrer automatiquement les pauses",
            variable=self.auto_start_var,
            font=ctk.CTkFont(size=11)
        )
        auto_checkbox.pack(anchor="w")
    
    def _create_info_panel(self, parent):
        """Create information panel."""
        info_panel = ctk.CTkFrame(parent)
        info_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        info_panel.grid_columnconfigure(0, weight=1)
        info_panel.grid_rowconfigure(2, weight=1)
        
        # Current task section
        task_frame = ctk.CTkFrame(info_panel)
        task_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            task_frame,
            text="📋 Tâche Actuelle",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Task input
        self.task_entry = ctk.CTkEntry(
            task_frame,
            placeholder_text="Sur quoi travaillez-vous ?",
            height=35
        )
        self.task_entry.pack(fill="x", padx=10, pady=(0, 5))
        
        # Task selection from database
        if self.database_manager:
            select_task_btn = ctk.CTkButton(
                task_frame,
                text="📝 Choisir une tâche",
                height=30,
                command=self._select_task_from_db
            )
            select_task_btn.pack(pady=(0, 10))
        
        # Statistics section
        stats_frame = ctk.CTkFrame(info_panel)
        stats_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(
            stats_frame,
            text="📊 Statistiques du Jour",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Stats grid
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=10, pady=(0, 10))
        stats_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Focus sessions
        self.focus_sessions_label = ctk.CTkLabel(
            stats_grid,
            text="🎯 Sessions: 0",
            font=ctk.CTkFont(size=12)
        )
        self.focus_sessions_label.grid(row=0, column=0, sticky="w", pady=2)
        
        # Total focus time
        self.focus_time_label = ctk.CTkLabel(
            stats_grid,
            text="⏱️ Focus: 0h 0m",
            font=ctk.CTkFont(size=12)
        )
        self.focus_time_label.grid(row=0, column=1, sticky="w", pady=2)
        
        # Break sessions
        self.break_sessions_label = ctk.CTkLabel(
            stats_grid,
            text="☕ Pauses: 0",
            font=ctk.CTkFont(size=12)
        )
        self.break_sessions_label.grid(row=1, column=0, sticky="w", pady=2)
        
        # Interruptions
        self.interruptions_label = ctk.CTkLabel(
            stats_grid,
            text="⚠️ Interruptions: 0",
            font=ctk.CTkFont(size=12)
        )
        self.interruptions_label.grid(row=1, column=1, sticky="w", pady=2)
        
        # AI insights (Genie mode only)
        if self.is_ai_enabled:
            insights_frame = ctk.CTkFrame(info_panel)
            insights_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
            
            ctk.CTkLabel(
                insights_frame,
                text="🤖 Insights IA",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 5))
            
            self.insights_text = ctk.CTkTextbox(
                insights_frame,
                height=150,
                wrap="word"
            )
            self.insights_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # AI actions
            ai_actions_frame = ctk.CTkFrame(insights_frame, fg_color="transparent")
            ai_actions_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            analyze_btn = ctk.CTkButton(
                ai_actions_frame,
                text="📈 Analyser Performance",
                height=30,
                command=self._analyze_performance
            )
            analyze_btn.pack(side="left", padx=(0, 5))
            
            suggest_btn = ctk.CTkButton(
                ai_actions_frame,
                text="💡 Suggestions",
                height=30,
                command=self._get_ai_suggestions
            )
            suggest_btn.pack(side="left", padx=5)
    
    def _create_history_panel(self, parent):
        """Create session history panel."""
        history_panel = ctk.CTkFrame(parent, height=200)
        history_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(5, 0))
        history_panel.grid_columnconfigure(0, weight=1)
        history_panel.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(history_panel, height=40, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📜 Historique des Sessions",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # Clear history button
        clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑️ Effacer",
            height=25,
            width=80,
            command=self._clear_history
        )
        clear_btn.grid(row=0, column=1, sticky="e", padx=15, pady=10)
        
        # History list
        self.history_frame = ctk.CTkScrollableFrame(history_panel)
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Empty state
        self._show_empty_history()
    
    def _update_focus_duration(self, value):
        """Update focus duration setting."""
        self.focus_duration = int(value) * 60
        if not self.is_running:
            self._update_timer_display()
    
    def _update_break_duration(self, value):
        """Update break duration setting."""
        self.short_break_duration = int(value) * 60
    
    def _start_timer(self):
        """Start the timer."""
        if self.is_paused:
            # Resume from pause
            self.is_paused = False
            self._resume_timer()
        else:
            # Start new session
            task_name = self.task_entry.get().strip() or "Tâche sans nom"
            self._start_new_session('focus', task_name)
        
        self._update_control_buttons()
    
    def _pause_timer(self):
        """Pause the timer."""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self._update_control_buttons()
            
            # Record interruption
            self.daily_stats['interruptions'] += 1
            self._update_stats_display()
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('timer_paused')
    
    def _stop_timer(self):
        """Stop the timer."""
        if self.is_running:
            self._end_current_session(completed=False)
        
        self._reset_timer()
        self._update_control_buttons()
    
    def _start_new_session(self, session_type: str, task_name: str = ""):
        """Start a new timer session."""
        # Determine session duration
        if session_type == 'focus':
            duration = self.focus_duration
            self.session_type_label.configure(text="🎯 Session de Focus", text_color="#2ECC71")
            self.timer_display.configure(text_color="#2ECC71")
            self.progress_bar.configure(progress_color="#2ECC71")
        elif session_type == 'short_break':
            duration = self.short_break_duration
            self.session_type_label.configure(text="☕ Pause Courte", text_color="#F39C12")
            self.timer_display.configure(text_color="#F39C12")
            self.progress_bar.configure(progress_color="#F39C12")
        else:  # long_break
            duration = self.long_break_duration
            self.session_type_label.configure(text="🛋️ Pause Longue", text_color="#9B59B6")
            self.timer_display.configure(text_color="#9B59B6")
            self.progress_bar.configure(progress_color="#9B59B6")
        
        # Create session
        self.current_session = {
            'id': str(uuid.uuid4()),
            'type': session_type,
            'task_name': task_name,
            'duration': duration,
            'start_time': datetime.now(),
            'completed': False
        }
        
        # Initialize timer
        self.remaining_time = duration
        self.session_start_time = time.time()
        self.is_running = True
        self.is_paused = False
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
        self.timer_thread.start()
        
        # Play audio feedback
        if self.audio_service:
            self.audio_service.play_sound('timer_started')
        
        self.logger.info(f"Started {session_type} session: {task_name}")
    
    def _timer_worker(self):
        """Timer worker thread."""
        while self.is_running and self.remaining_time > 0:
            if not self.is_paused:
                self.remaining_time -= 1
                
                # Update UI in main thread
                self.after(0, self._update_timer_display)
                self.after(0, self._update_progress_bar)
                
                # Call timer callbacks
                for callback in self.timer_callbacks:
                    try:
                        callback(self.remaining_time, self.current_session)
                    except Exception as e:
                        self.logger.error(f"Timer callback error: {e}")
            
            time.sleep(1)
        
        # Timer finished
        if self.is_running and self.remaining_time <= 0:
            self.after(0, self._timer_finished)
    
    def _timer_finished(self):
        """Handle timer completion."""
        if self.current_session:
            self._end_current_session(completed=True)
            
            # Play completion sound
            if self.audio_service:
                self.audio_service.play_sound('timer_completed')
            
            # Show notification
            session_type = self.current_session['type']
            if session_type == 'focus':
                messagebox.showinfo("Session Terminée", "🎯 Session de focus terminée !\n\nTemps pour une pause.")
                self._suggest_next_session()
            else:
                messagebox.showinfo("Pause Terminée", "☕ Pause terminée !\n\nPrêt pour une nouvelle session ?")
        
        self._reset_timer()
        self._update_control_buttons()
    
    def _end_current_session(self, completed: bool):
        """End the current session and record it."""
        if not self.current_session:
            return
        
        # Calculate actual duration
        actual_duration = self.current_session['duration'] - self.remaining_time
        
        # Update session data
        self.current_session.update({
            'end_time': datetime.now(),
            'actual_duration': actual_duration,
            'completed': completed
        })
        
        # Add to history
        self.sessions_history.append(self.current_session.copy())
        
        # Update daily stats
        session_type = self.current_session['type']
        if session_type == 'focus':
            if completed:
                self.daily_stats['focus_sessions'] += 1
            self.daily_stats['total_focus_time'] += actual_duration
        else:
            if completed:
                self.daily_stats['break_sessions'] += 1
            self.daily_stats['total_break_time'] += actual_duration
        
        # Save to database
        if self.database_manager:
            try:
                self.database_manager.save_focus_session(
                    session_type=session_type,
                    task_name=self.current_session['task_name'],
                    planned_duration=self.current_session['duration'],
                    actual_duration=actual_duration,
                    completed=completed,
                    start_time=self.current_session['start_time']
                )
            except Exception as e:
                self.logger.error(f"Failed to save session: {e}")
        
        # Update displays
        self._update_stats_display()
        self._update_history_display()
        
        # Clear current session
        self.current_session = None
    
    def _suggest_next_session(self):
        """Suggest the next session type."""
        focus_sessions_today = self.daily_stats['focus_sessions']
        
        if focus_sessions_today > 0 and focus_sessions_today % self.sessions_until_long_break == 0:
            # Time for long break
            if self.auto_start_var.get():
                self.after(2000, lambda: self._start_new_session('long_break'))
            else:
                messagebox.showinfo("Pause Longue", "🛋️ Temps pour une pause longue !")
        else:
            # Time for short break
            if self.auto_start_var.get():
                self.after(2000, lambda: self._start_new_session('short_break'))
            else:
                messagebox.showinfo("Pause Courte", "☕ Temps pour une pause courte !")
    
    def _resume_timer(self):
        """Resume paused timer."""
        if self.is_paused and self.timer_thread and not self.timer_thread.is_alive():
            # Restart timer thread
            self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
            self.timer_thread.start()
    
    def _reset_timer(self):
        """Reset timer to initial state."""
        self.is_running = False
        self.is_paused = False
        self.remaining_time = self.focus_duration
        self.session_start_time = None
        
        self.session_type_label.configure(text="Prêt à commencer", text_color="gray")
        self.timer_display.configure(text_color="#2ECC71")
        self.progress_bar.configure(progress_color="#2ECC71")
        self.progress_bar.set(0)
        
        self._update_timer_display()
    
    def _update_timer_display(self):
        """Update timer display."""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        self.timer_display.configure(text=time_text)
    
    def _update_progress_bar(self):
        """Update progress bar."""
        if self.current_session:
            total_duration = self.current_session['duration']
            elapsed = total_duration - self.remaining_time
            progress = elapsed / total_duration if total_duration > 0 else 0
            self.progress_bar.set(progress)
    
    def _update_control_buttons(self):
        """Update control button states."""
        if self.is_running:
            if self.is_paused:
                self.start_btn.configure(text="▶️ Reprendre", state="normal")
                self.pause_btn.configure(state="disabled")
            else:
                self.start_btn.configure(state="disabled")
                self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
        else:
            self.start_btn.configure(text="▶️ Démarrer", state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
    
    def _update_stats_display(self):
        """Update statistics display."""
        stats = self.daily_stats
        
        self.focus_sessions_label.configure(text=f"🎯 Sessions: {stats['focus_sessions']}")
        
        focus_hours = stats['total_focus_time'] // 3600
        focus_minutes = (stats['total_focus_time'] % 3600) // 60
        self.focus_time_label.configure(text=f"⏱️ Focus: {focus_hours}h {focus_minutes}m")
        
        self.break_sessions_label.configure(text=f"☕ Pauses: {stats['break_sessions']}")
        self.interruptions_label.configure(text=f"⚠️ Interruptions: {stats['interruptions']}")
    
    def _update_history_display(self):
        """Update session history display."""
        # Clear existing widgets
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        if not self.sessions_history:
            self._show_empty_history()
            return
        
        # Show recent sessions (last 10)
        recent_sessions = self.sessions_history[-10:]
        
        for session in reversed(recent_sessions):
            self._create_session_widget(session)
    
    def _show_empty_history(self):
        """Show empty history state."""
        empty_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        empty_frame.pack(expand=True, fill="both")
        
        empty_icon = ctk.CTkLabel(
            empty_frame,
            text="📜",
            font=ctk.CTkFont(size=32)
        )
        empty_icon.pack(pady=(20, 5))
        
        empty_text = ctk.CTkLabel(
            empty_frame,
            text="Aucune session encore\n\nVos sessions apparaîtront ici",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center"
        )
        empty_text.pack(pady=5)
    
    def _create_session_widget(self, session: Dict):
        """Create widget for a session."""
        session_frame = ctk.CTkFrame(self.history_frame)
        session_frame.pack(fill="x", padx=5, pady=2)
        
        content_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Session type icon
        type_icons = {
            'focus': '🎯',
            'short_break': '☕',
            'long_break': '🛋️'
        }
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=type_icons.get(session['type'], '⏱️'),
            font=ctk.CTkFont(size=16),
            width=30
        )
        icon_label.grid(row=0, column=0, sticky="w")
        
        # Session info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Task name and time
        if session['type'] == 'focus':
            task_text = session.get('task_name', 'Tâche sans nom')
        else:
            task_text = "Pause" + (" longue" if session['type'] == 'long_break' else " courte")
        
        task_label = ctk.CTkLabel(
            info_frame,
            text=task_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        task_label.pack(fill="x", anchor="w")
        
        # Duration and completion
        duration_minutes = session['actual_duration'] // 60
        duration_seconds = session['actual_duration'] % 60
        
        status_text = "✅ Terminée" if session['completed'] else "❌ Interrompue"
        time_text = f"{duration_minutes}m {duration_seconds}s"
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=f"{status_text} • {time_text}",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        details_label.pack(fill="x", anchor="w")
        
        # Timestamp
        start_time = session['start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        time_label = ctk.CTkLabel(
            content_frame,
            text=start_time.strftime("%H:%M"),
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=50
        )
        time_label.grid(row=0, column=2, sticky="e")
    
    def _select_task_from_db(self):
        """Select task from database."""
        if not self.database_manager:
            return
        
        try:
            tasks = self.database_manager.get_user_tasks()
            if not tasks:
                messagebox.showinfo("Aucune Tâche", "Aucune tâche trouvée dans la base de données.")
                return
            
            # Create task selection dialog
            dialog = TaskSelectionDialog(self, tasks)
            result = dialog.show()
            
            if result and dialog.selected_task:
                task = dialog.selected_task
                self.task_entry.delete(0, 'end')
                self.task_entry.insert(0, task['title'])
                self.current_task = task
                
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les tâches: {e}")
    
    def _clear_history(self):
        """Clear session history."""
        if self.sessions_history and messagebox.askyesno("Confirmer", "Effacer tout l'historique ?"):
            self.sessions_history.clear()
            self._update_history_display()
    
    def _analyze_performance(self):
        """Analyze performance with AI."""
        if not self.is_ai_enabled or not self.sessions_history:
            return
        
        def ai_task():
            # Prepare session data for analysis
            session_data = []
            for session in self.sessions_history[-20:]:  # Last 20 sessions
                session_data.append({
                    'type': session['type'],
                    'duration': session['actual_duration'],
                    'completed': session['completed'],
                    'time': session['start_time'].strftime('%H:%M') if isinstance(session['start_time'], datetime) else session['start_time']
                })
            
            prompt = f"""
Analyse ces données de sessions de focus et fournis des insights:

Statistiques du jour:
- Sessions de focus: {self.daily_stats['focus_sessions']}
- Temps de focus total: {self.daily_stats['total_focus_time'] // 60} minutes
- Interruptions: {self.daily_stats['interruptions']}

Dernières sessions:
{json.dumps(session_data, indent=2)}

Fournis une analyse concise avec:
1. Points forts observés
2. Zones d'amélioration
3. Recommandations spécifiques

Réponds en français, de manière encourageante et constructive.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='performance_analysis',
                max_tokens=400
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _get_ai_suggestions(self):
        """Get AI suggestions for productivity."""
        if not self.is_ai_enabled:
            return
        
        def ai_task():
            current_time = datetime.now().strftime('%H:%M')
            
            prompt = f"""
Il est {current_time}. Donne 3-5 suggestions courtes pour optimiser la productivité:

1. Suggestions basées sur l'heure actuelle
2. Conseils pour maintenir la concentration
3. Techniques de gestion du temps
4. Optimisation de l'environnement de travail

Réponds de manière concise et actionnable, en français.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='productivity_suggestions',
                max_tokens=300
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _handle_ai_result(self, result):
        """Handle AI analysis result."""
        if result and hasattr(self, 'insights_text'):
            self.insights_text.delete("1.0", "end")
            self.insights_text.insert("1.0", result)
    
    def add_timer_callback(self, callback: Callable):
        """Add a callback function to be called every second during timer."""
        self.timer_callbacks.append(callback)
    
    def remove_timer_callback(self, callback: Callable):
        """Remove a timer callback."""
        if callback in self.timer_callbacks:
            self.timer_callbacks.remove(callback)
    
    def get_current_session_info(self) -> Optional[Dict]:
        """Get information about the current session."""
        if self.current_session:
            return {
                'type': self.current_session['type'],
                'task_name': self.current_session.get('task_name', ''),
                'remaining_time': self.remaining_time,
                'is_running': self.is_running,
                'is_paused': self.is_paused
            }
        return None
    
    def _save_data(self):
        """Save current data."""
        try:
            # Save settings and session data
            data = {
                'daily_stats': self.daily_stats,
                'sessions_history': self.sessions_history,
                'settings': {
                    'focus_duration': self.focus_duration,
                    'short_break_duration': self.short_break_duration,
                    'long_break_duration': self.long_break_duration,
                    'auto_start_breaks': self.auto_start_var.get()
                }
            }
            
            # TODO: Implement actual saving
            super()._save_data()
            
        except Exception as e:
            self.logger.error(f"Failed to save TimeFocus data: {e}")
    
    def _export_data(self):
        """Export session data."""
        if not self.sessions_history:
            messagebox.showinfo("Aucune Donnée", "Aucune session à exporter.")
            return
        
        # TODO: Implement export functionality
        messagebox.showinfo("Info", "Export en développement")
    
    def cleanup(self):
        """Cleanup when closing the tool."""
        # Stop timer if running
        if self.is_running:
            self._stop_timer()
        
        # Wait for timer thread to finish
        if self.timer_thread and self.timer_thread.is_alive():
            self.is_running = False
            self.timer_thread.join(timeout=1)
        
        super().cleanup()


class TaskSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting a task from database."""
    
    def __init__(self, parent, tasks: List[Dict]):
        """Initialize task selection dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.tasks = tasks
        self.selected_task = None
        self.result = False
        
        # Configure dialog
        self.title("Choisir une Tâche")
        self.geometry("500x400")
        self.resizable(False, False)
        
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
            text="📋 Sélectionner une Tâche",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Tasks list
        tasks_frame = ctk.CTkScrollableFrame(main_frame, height=250)
        tasks_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        for task in self.tasks:
            self._create_task_widget(tasks_frame, task)
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        select_btn = ctk.CTkButton(
            buttons_frame,
            text="Sélectionner",
            command=self._on_select
        )
        select_btn.pack(side="right")
    
    def _create_task_widget(self, parent, task: Dict):
        """Create widget for a task."""
        task_frame = ctk.CTkFrame(parent)
        task_frame.pack(fill="x", padx=5, pady=2)
        
        # Make clickable
        task_frame.bind("<Button-1>", lambda e: self._select_task(task))
        
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=8)
        
        # Task title
        title_label = ctk.CTkLabel(
            content_frame,
            text=task.get('title', 'Tâche sans titre'),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", anchor="w")
        title_label.bind("<Button-1>", lambda e: self._select_task(task))
        
        # Task details
        details = []
        if task.get('category'):
            details.append(f"📁 {task['category']}")
        if task.get('priority'):
            priority_icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}
            priority_icon = priority_icons.get(task['priority'], "⚪")
            details.append(f"{priority_icon} Priorité {task['priority']}")
        
        if details:
            details_label = ctk.CTkLabel(
                content_frame,
                text=" • ".join(details),
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w"
            )
            details_label.pack(fill="x", anchor="w")
            details_label.bind("<Button-1>", lambda e: self._select_task(task))
    
    def _select_task(self, task: Dict):
        """Select a task."""
        self.selected_task = task
        
        # Visual feedback (highlight selected task)
        # TODO: Implement visual selection feedback
    
    def _on_select(self):
        """Handle select button."""
        if not self.selected_task:
            messagebox.showwarning("Sélection Requise", "Veuillez sélectionner une tâche.")
            return
        
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result