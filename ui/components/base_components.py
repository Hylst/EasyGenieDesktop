#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Base UI Components

Base classes for UI components providing common functionality.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod
import threading
from datetime import datetime


class BaseFrame(ctk.CTkFrame):
    """Base frame class with common functionality."""
    
    def __init__(self, parent, settings_manager=None, **kwargs):
        """Initialize base frame."""
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings_manager = settings_manager
        self.parent = parent
        
        # Common attributes
        self.is_loading = False
        self.callbacks = {}
        
        # Setup common bindings
        self._setup_bindings()
    
    def _setup_bindings(self):
        """Setup common event bindings."""
        self.bind("<Button-3>", self._show_context_menu)  # Right click
    
    def _show_context_menu(self, event):
        """Show context menu (override in subclasses)."""
        pass
    
    def set_loading(self, loading: bool, message: str = "Chargement..."):
        """Set loading state."""
        self.is_loading = loading
        # Override in subclasses to show loading indicator
    
    def add_callback(self, event: str, callback: Callable):
        """Add event callback."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def trigger_callback(self, event: str, *args, **kwargs):
        """Trigger event callbacks."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in callback for {event}: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get setting value."""
        if self.settings_manager:
            return self.settings_manager.get(key, default)
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set setting value."""
        if self.settings_manager:
            self.settings_manager.set(key, value)


class BaseDialog(ctk.CTkToplevel):
    """Base dialog class with common functionality."""
    
    def __init__(self, parent, title: str = "Dialog", size: tuple = (400, 300), 
                 resizable: bool = True, modal: bool = True, **kwargs):
        """Initialize base dialog."""
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent = parent
        self.result = None
        
        # Configure dialog
        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")
        
        if not resizable:
            self.resizable(False, False)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        if modal:
            self.transient(parent)
            self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.bind("<Return>", lambda e: self._on_ok())
    
    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    @abstractmethod
    def _setup_dialog(self):
        """Setup dialog content (implement in subclasses)."""
        pass
    
    def _on_ok(self):
        """Handle OK button (override in subclasses)."""
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and wait for result."""
        self.wait_window()
        return self.result


class BaseToolWindow(BaseFrame):
    """Base class for tool windows."""
    
    def __init__(self, parent, tool_name: str, magic_energy_level: str = 'magic',
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize base tool window."""
        super().__init__(parent, settings_manager, **kwargs)
        
        # Tool properties
        self.tool_name = tool_name
        self.magic_energy_level = magic_energy_level
        
        # Services
        self.ai_service = ai_service
        self.audio_service = audio_service
        self.database_manager = database_manager
        
        # Tool state
        self.is_ai_enabled = magic_energy_level == 'genie' and ai_service and ai_service.is_configured()
        self.tool_data = {}
        self.unsaved_changes = False
        
        # UI components
        self.header_frame = None
        self.content_frame = None
        self.footer_frame = None
        self.loading_overlay = None
        
        # Setup tool window
        self._setup_tool_window()
        
        self.logger.info(f"Tool window initialized: {tool_name} ({magic_energy_level})")
    
    def _setup_tool_window(self):
        """Setup the tool window layout."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create header
        self._create_header()
        
        # Create content area
        self._create_content()
        
        # Create footer
        self._create_footer()
        
        # Setup tool-specific content
        self._setup_tool_content()
    
    def _create_header(self):
        """Create tool header with title and controls."""
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Tool title and icon
        title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # Get tool info
        tool_icons = {
            'Task Breaker': '🔨',
            'TimeFocus': '⏰',
            'Priority Grid': '📊',
            'Décharge de Pensées': '🧠',
            'Formaliseur': '✍️',
            'RoutineBuilder': '🔄',
            'Lecteur Immersif': '📖'
        }
        
        icon = tool_icons.get(self.tool_name, '🔧')
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=f"{icon} {self.tool_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left")
        
        # Energy level indicator
        energy_color = "#4ECDC4" if self.magic_energy_level == 'genie' else "#FF6B6B"
        energy_text = "🔮 Genie" if self.magic_energy_level == 'genie' else "✨ Magic"
        
        energy_label = ctk.CTkLabel(
            title_frame,
            text=energy_text,
            font=ctk.CTkFont(size=12),
            text_color=energy_color
        )
        energy_label.pack(side="left", padx=(10, 0))
        
        # Tool controls
        controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            controls_frame,
            text="💾 Sauvegarder",
            width=100,
            height=30,
            command=self._save_data,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=2)
        
        # Export button
        export_btn = ctk.CTkButton(
            controls_frame,
            text="📤 Exporter",
            width=80,
            height=30,
            command=self._export_data
        )
        export_btn.pack(side="left", padx=2)
        
        # Help button
        help_btn = ctk.CTkButton(
            controls_frame,
            text="❓",
            width=30,
            height=30,
            command=self._show_help
        )
        help_btn.pack(side="left", padx=2)
    
    def _create_content(self):
        """Create main content area."""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _create_footer(self):
        """Create footer with status and additional controls."""
        self.footer_frame = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.footer_frame.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            text="Prêt",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # AI status (if applicable)
        if self.is_ai_enabled:
            ai_status_label = ctk.CTkLabel(
                self.footer_frame,
                text="🤖 IA Activée",
                font=ctk.CTkFont(size=10),
                text_color="green"
            )
            ai_status_label.grid(row=0, column=2, sticky="e", padx=10, pady=10)
    
    @abstractmethod
    def _setup_tool_content(self):
        """Setup tool-specific content (implement in subclasses)."""
        pass
    
    def _save_data(self):
        """Save tool data (override in subclasses)."""
        try:
            # Default implementation
            self.unsaved_changes = False
            self.save_btn.configure(state="disabled")
            self.set_status("Données sauvegardées", 2000)
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('save')
                
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def _export_data(self):
        """Export tool data (override in subclasses)."""
        messagebox.showinfo("Info", "Export en développement")
    
    def _show_help(self):
        """Show tool help (override in subclasses)."""
        help_text = f"Aide pour {self.tool_name}\n\nCet outil est en cours de développement."
        messagebox.showinfo("Aide", help_text)
    
    def set_status(self, message: str, duration: int = 0):
        """Set status message."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            
            if duration > 0:
                self.after(duration, lambda: self.status_label.configure(text="Prêt"))
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes."""
        self.unsaved_changes = True
        if hasattr(self, 'save_btn'):
            self.save_btn.configure(state="normal")
    
    def show_loading(self, message: str = "Chargement..."):
        """Show loading overlay."""
        if not self.loading_overlay:
            self.loading_overlay = LoadingOverlay(self, message)
        else:
            self.loading_overlay.set_message(message)
        
        self.loading_overlay.show()
    
    def hide_loading(self):
        """Hide loading overlay."""
        if self.loading_overlay:
            self.loading_overlay.hide()
    
    def run_ai_task(self, task_func: Callable, *args, **kwargs):
        """Run AI task in background thread."""
        if not self.is_ai_enabled:
            messagebox.showwarning("IA Non Disponible", 
                                 "L'IA n'est pas configurée ou le mode Genie n'est pas activé.")
            return
        
        def task_wrapper():
            try:
                self.show_loading("Traitement IA en cours...")
                result = task_func(*args, **kwargs)
                self.after(0, lambda: self._handle_ai_result(result))
            except Exception as e:
                self.after(0, lambda: self._handle_ai_error(e))
            finally:
                self.after(0, self.hide_loading)
        
        thread = threading.Thread(target=task_wrapper, daemon=True)
        thread.start()
    
    def _handle_ai_result(self, result):
        """Handle AI task result (override in subclasses)."""
        self.set_status("Traitement IA terminé", 2000)
    
    def _handle_ai_error(self, error):
        """Handle AI task error."""
        self.logger.error(f"AI task error: {error}")
        messagebox.showerror("Erreur IA", f"Erreur lors du traitement IA: {error}")
        self.set_status("Erreur IA", 3000)


class LoadingOverlay(ctk.CTkFrame):
    """Loading overlay widget."""
    
    def __init__(self, parent, message: str = "Chargement..."):
        """Initialize loading overlay."""
        super().__init__(parent, fg_color=("gray75", "gray25"))
        
        self.parent = parent
        self.message = message
        
        # Configure overlay
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Loading animation (simple text for now)
        self.loading_label = ctk.CTkLabel(
            content_frame,
            text="⏳ " + message,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.loading_label.pack(padx=30, pady=20)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(content_frame, mode="indeterminate")
        self.progress_bar.pack(padx=30, pady=(0, 20))
        
        # Start animation
        self.progress_bar.start()
        self._animate_text()
    
    def _animate_text(self):
        """Animate loading text."""
        current_text = self.loading_label.cget("text")
        if current_text.endswith("..."):
            new_text = current_text[:-3]
        elif current_text.endswith(".."):
            new_text = current_text + "."
        elif current_text.endswith("."):
            new_text = current_text + "."
        else:
            new_text = current_text + "."
        
        self.loading_label.configure(text=new_text)
        
        # Continue animation if still visible
        if self.winfo_viewable():
            self.after(500, self._animate_text)
    
    def set_message(self, message: str):
        """Update loading message."""
        self.message = message
        self.loading_label.configure(text="⏳ " + message)
    
    def show(self):
        """Show loading overlay."""
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.lift()
    
    def hide(self):
        """Hide loading overlay."""
        self.place_forget()
        self.progress_bar.stop()


class ResponsiveFrame(BaseFrame):
    """Frame that adapts to different screen sizes."""
    
    def __init__(self, parent, breakpoints: Dict[str, int] = None, **kwargs):
        """Initialize responsive frame."""
        super().__init__(parent, **kwargs)
        
        # Default breakpoints (width in pixels)
        self.breakpoints = breakpoints or {
            'small': 600,
            'medium': 900,
            'large': 1200
        }
        
        self.current_size = 'large'
        
        # Bind resize event
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event):
        """Handle resize event."""
        if event.widget == self:
            width = self.winfo_width()
            new_size = self._get_size_category(width)
            
            if new_size != self.current_size:
                self.current_size = new_size
                self._on_size_change(new_size)
    
    def _get_size_category(self, width: int) -> str:
        """Get size category based on width."""
        if width < self.breakpoints['small']:
            return 'small'
        elif width < self.breakpoints['medium']:
            return 'medium'
        elif width < self.breakpoints['large']:
            return 'large'
        else:
            return 'xlarge'
    
    def _on_size_change(self, new_size: str):
        """Handle size change (override in subclasses)."""
        pass
    
    def is_small(self) -> bool:
        """Check if current size is small."""
        return self.current_size == 'small'
    
    def is_medium(self) -> bool:
        """Check if current size is medium."""
        return self.current_size == 'medium'
    
    def is_large(self) -> bool:
        """Check if current size is large or xlarge."""
        return self.current_size in ['large', 'xlarge']