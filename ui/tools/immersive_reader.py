"""Immersive Reader Tool for Easy Genie Desktop.

This module provides an immersive reading experience with features like:
- Text display with customizable formatting
- Reading speed control
- Focus modes (sentence, paragraph, full text)
- Text-to-speech integration
- Reading progress tracking
- Distraction-free environment
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable
import threading
import time
import re
from pathlib import Path

# Import base components
try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, parent_dir)
    from ui.components.base_components import BaseToolWindow


class ImmersiveReaderTool(BaseToolWindow):
    """Immersive Reader tool for distraction-free reading."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', **kwargs):
        """Initialize the Immersive Reader tool."""
        super().__init__(
            parent=parent,
            title="📖 Lecteur Immersif",
            magic_energy_level=magic_energy_level,
            **kwargs
        )
        
        # Reading state
        self.current_text = ""
        self.sentences = []
        self.paragraphs = []
        self.current_sentence_index = 0
        self.current_paragraph_index = 0
        self.is_reading = False
        self.reading_thread = None
        
        # Reading settings
        self.reading_speed = 200  # words per minute
        self.focus_mode = "sentence"  # sentence, paragraph, full
        self.auto_scroll = True
        self.highlight_current = True
        
        # UI elements
        self.text_display = None
        self.progress_bar = None
        self.speed_slider = None
        self.mode_var = None
        
        # Setup UI
        self._setup_ui()
        
        # Load sample text for demo
        self._load_sample_text()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Control panel
        self._setup_control_panel()
        
        # Text display area
        self._setup_text_display()
        
        # Progress and status
        self._setup_progress_panel()
        
        # Footer controls
        self._setup_footer_controls()
    
    def _setup_control_panel(self):
        """Setup the control panel."""
        control_frame = ctk.CTkFrame(self.content_frame)
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        control_frame.grid_columnconfigure(2, weight=1)
        
        # File operations
        file_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        file_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        load_btn = ctk.CTkButton(
            file_frame,
            text="📁 Charger",
            width=100,
            command=self._load_file
        )
        load_btn.pack(side="left", padx=(0, 5))
        
        paste_btn = ctk.CTkButton(
            file_frame,
            text="📋 Coller",
            width=100,
            command=self._paste_text
        )
        paste_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            file_frame,
            text="🗑️ Effacer",
            width=100,
            command=self._clear_text
        )
        clear_btn.pack(side="left", padx=5)
        
        # Reading controls
        reading_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        reading_frame.grid(row=0, column=1, padx=20, pady=10)
        
        self.play_btn = ctk.CTkButton(
            reading_frame,
            text="▶️ Lire",
            width=100,
            command=self._toggle_reading
        )
        self.play_btn.pack(side="left", padx=(0, 5))
        
        stop_btn = ctk.CTkButton(
            reading_frame,
            text="⏹️ Arrêter",
            width=100,
            command=self._stop_reading
        )
        stop_btn.pack(side="left", padx=5)
        
        restart_btn = ctk.CTkButton(
            reading_frame,
            text="⏮️ Début",
            width=100,
            command=self._restart_reading
        )
        restart_btn.pack(side="left", padx=5)
        
        # Settings
        settings_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        settings_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        settings_btn = ctk.CTkButton(
            settings_frame,
            text="⚙️ Paramètres",
            width=120,
            command=self._show_settings
        )
        settings_btn.pack(side="right")
    
    def _setup_text_display(self):
        """Setup the text display area."""
        display_frame = ctk.CTkFrame(self.content_frame)
        display_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        self.text_display = ctk.CTkTextbox(
            display_frame,
            font=ctk.CTkFont(size=16, family="Georgia"),
            wrap="word",
            state="disabled"
        )
        self.text_display.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configure text tags for highlighting
        self.text_display._textbox.tag_configure(
            "current_sentence",
            background="#3B82F6",
            foreground="white",
            font=("Georgia", 16, "bold")
        )
        
        self.text_display._textbox.tag_configure(
            "current_paragraph",
            background="#EFF6FF",
            foreground="#1E40AF"
        )
        
        self.text_display._textbox.tag_configure(
            "read_text",
            foreground="#6B7280"
        )
    
    def _setup_progress_panel(self):
        """Setup the progress panel."""
        progress_frame = ctk.CTkFrame(self.content_frame)
        progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(1, weight=1)
        
        # Progress info
        ctk.CTkLabel(
            progress_frame,
            text="Progression:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0 / 0",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.grid(row=0, column=2, padx=(10, 15), pady=10, sticky="e")
    
    def _setup_footer_controls(self):
        """Setup footer controls."""
        footer_frame = ctk.CTkFrame(self.content_frame)
        footer_frame.grid(row=3, column=0, sticky="ew")
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Speed control
        speed_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        speed_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        ctk.CTkLabel(
            speed_frame,
            text="Vitesse:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 5))
        
        self.speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=50,
            to=500,
            number_of_steps=45,
            width=150,
            command=self._on_speed_change
        )
        self.speed_slider.pack(side="left", padx=5)
        self.speed_slider.set(self.reading_speed)
        
        self.speed_label = ctk.CTkLabel(
            speed_frame,
            text=f"{self.reading_speed} mpm",
            font=ctk.CTkFont(size=11)
        )
        self.speed_label.pack(side="left", padx=(5, 0))
        
        # Focus mode
        mode_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        mode_frame.grid(row=0, column=1, padx=15, pady=10)
        
        ctk.CTkLabel(
            mode_frame,
            text="Mode:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 10))
        
        self.mode_var = ctk.StringVar(value=self.focus_mode)
        
        mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["sentence", "paragraph", "full"],
            variable=self.mode_var,
            command=self._on_mode_change,
            width=120
        )
        mode_menu.pack(side="left")
        
        # TTS toggle
        tts_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        tts_frame.grid(row=0, column=2, sticky="e", padx=15, pady=10)
        
        self.tts_var = ctk.BooleanVar(value=False)
        tts_check = ctk.CTkCheckBox(
            tts_frame,
            text="🔊 Synthèse vocale",
            variable=self.tts_var,
            font=ctk.CTkFont(size=11)
        )
        tts_check.pack(side="right")
    
    def _load_file(self):
        """Load text from file."""
        file_path = filedialog.askopenfilename(
            title="Charger un fichier texte",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                self._set_text(content)
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de charger le fichier:\n{str(e)}"
                )
    
    def _paste_text(self):
        """Paste text from clipboard."""
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text.strip():
                self._set_text(clipboard_text)
            else:
                messagebox.showwarning(
                    "Presse-papiers vide",
                    "Le presse-papiers ne contient pas de texte."
                )
        except tk.TclError:
            messagebox.showerror(
                "Erreur",
                "Impossible d'accéder au presse-papiers."
            )
    
    def _clear_text(self):
        """Clear all text."""
        if messagebox.askyesno(
            "Confirmer",
            "Êtes-vous sûr de vouloir effacer tout le texte?"
        ):
            self._set_text("")
    
    def _set_text(self, text: str):
        """Set text for reading."""
        self.current_text = text.strip()
        
        # Parse text into sentences and paragraphs
        self._parse_text()
        
        # Update display
        self._update_text_display()
        
        # Reset reading position
        self.current_sentence_index = 0
        self.current_paragraph_index = 0
        
        # Update progress
        self._update_progress()
        
        # Stop any current reading
        self._stop_reading()
    
    def _parse_text(self):
        """Parse text into sentences and paragraphs."""
        if not self.current_text:
            self.sentences = []
            self.paragraphs = []
            return
        
        # Split into paragraphs
        self.paragraphs = [p.strip() for p in self.current_text.split('\n\n') if p.strip()]
        
        # Split into sentences
        sentence_pattern = r'[.!?]+\s+'
        self.sentences = []
        
        for paragraph in self.paragraphs:
            # Split paragraph into sentences
            paragraph_sentences = re.split(sentence_pattern, paragraph)
            # Clean and add sentences
            for sentence in paragraph_sentences:
                sentence = sentence.strip()
                if sentence:
                    self.sentences.append(sentence)
    
    def _update_text_display(self):
        """Update the text display."""
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", "end")
        
        if self.current_text:
            self.text_display.insert("1.0", self.current_text)
        
        self.text_display.configure(state="disabled")
        
        # Apply highlighting if reading
        if self.is_reading:
            self._highlight_current()
    
    def _highlight_current(self):
        """Highlight current reading position."""
        if not self.highlight_current or not self.sentences:
            return
        
        # Clear previous highlights
        self.text_display._textbox.tag_remove("current_sentence", "1.0", "end")
        self.text_display._textbox.tag_remove("current_paragraph", "1.0", "end")
        self.text_display._textbox.tag_remove("read_text", "1.0", "end")
        
        if self.focus_mode == "sentence" and self.current_sentence_index < len(self.sentences):
            # Highlight current sentence
            current_sentence = self.sentences[self.current_sentence_index]
            start_pos = self.text_display._textbox.search(current_sentence, "1.0")
            
            if start_pos:
                end_pos = f"{start_pos}+{len(current_sentence)}c"
                self.text_display._textbox.tag_add("current_sentence", start_pos, end_pos)
                
                # Mark previous sentences as read
                for i in range(self.current_sentence_index):
                    prev_sentence = self.sentences[i]
                    prev_start = self.text_display._textbox.search(prev_sentence, "1.0")
                    if prev_start:
                        prev_end = f"{prev_start}+{len(prev_sentence)}c"
                        self.text_display._textbox.tag_add("read_text", prev_start, prev_end)
                
                # Auto-scroll to current sentence
                if self.auto_scroll:
                    self.text_display._textbox.see(start_pos)
    
    def _toggle_reading(self):
        """Toggle reading state."""
        if self.is_reading:
            self._pause_reading()
        else:
            self._start_reading()
    
    def _start_reading(self):
        """Start reading."""
        if not self.sentences:
            messagebox.showwarning(
                "Aucun texte",
                "Veuillez charger du texte avant de commencer la lecture."
            )
            return
        
        self.is_reading = True
        self.play_btn.configure(text="⏸️ Pause")
        
        # Start reading thread
        if self.reading_thread is None or not self.reading_thread.is_alive():
            self.reading_thread = threading.Thread(target=self._reading_loop, daemon=True)
            self.reading_thread.start()
    
    def _pause_reading(self):
        """Pause reading."""
        self.is_reading = False
        self.play_btn.configure(text="▶️ Lire")
    
    def _stop_reading(self):
        """Stop reading and reset position."""
        self.is_reading = False
        self.play_btn.configure(text="▶️ Lire")
        
        # Reset position
        self.current_sentence_index = 0
        self.current_paragraph_index = 0
        
        # Update display
        self._update_text_display()
        self._update_progress()
    
    def _restart_reading(self):
        """Restart reading from beginning."""
        self._stop_reading()
        if self.sentences:
            self._start_reading()
    
    def _reading_loop(self):
        """Main reading loop (runs in separate thread)."""
        while self.is_reading and self.current_sentence_index < len(self.sentences):
            # Get current sentence
            current_sentence = self.sentences[self.current_sentence_index]
            
            # Update UI in main thread
            self.after(0, self._highlight_current)
            self.after(0, self._update_progress)
            
            # Text-to-speech if enabled
            if self.tts_var.get() and self.audio_service:
                try:
                    self.audio_service.speak_text(current_sentence)
                except Exception as e:
                    print(f"TTS Error: {e}")
            
            # Calculate reading time based on speed
            word_count = len(current_sentence.split())
            reading_time = (word_count / self.reading_speed) * 60  # seconds
            
            # Wait for reading time (check for pause every 0.1 seconds)
            elapsed = 0
            while elapsed < reading_time and self.is_reading:
                time.sleep(0.1)
                elapsed += 0.1
            
            # Move to next sentence
            if self.is_reading:
                self.current_sentence_index += 1
        
        # Reading finished
        if self.is_reading:
            self.after(0, self._on_reading_finished)
    
    def _on_reading_finished(self):
        """Handle reading completion."""
        self.is_reading = False
        self.play_btn.configure(text="▶️ Lire")
        
        # Show completion message
        messagebox.showinfo(
            "Lecture terminée",
            "La lecture du texte est terminée!"
        )
        
        # Reset for next reading
        self._stop_reading()
    
    def _update_progress(self):
        """Update reading progress."""
        if not self.sentences:
            self.progress_bar.set(0)
            self.progress_label.configure(text="0 / 0")
            return
        
        progress = self.current_sentence_index / len(self.sentences)
        self.progress_bar.set(progress)
        
        self.progress_label.configure(
            text=f"{self.current_sentence_index} / {len(self.sentences)}"
        )
    
    def _on_speed_change(self, value):
        """Handle speed slider change."""
        self.reading_speed = int(value)
        self.speed_label.configure(text=f"{self.reading_speed} mpm")
    
    def _on_mode_change(self, value):
        """Handle focus mode change."""
        self.focus_mode = value
        if self.is_reading:
            self._highlight_current()
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = ReaderSettingsDialog(self)
        if dialog.show():
            # Apply settings
            settings = dialog.get_settings()
            self._apply_settings(settings)
    
    def _apply_settings(self, settings: Dict[str, Any]):
        """Apply reader settings."""
        # Font settings
        if 'font_family' in settings or 'font_size' in settings:
            font_family = settings.get('font_family', 'Georgia')
            font_size = settings.get('font_size', 16)
            self.text_display.configure(
                font=ctk.CTkFont(size=font_size, family=font_family)
            )
        
        # Reading settings
        if 'auto_scroll' in settings:
            self.auto_scroll = settings['auto_scroll']
        
        if 'highlight_current' in settings:
            self.highlight_current = settings['highlight_current']
        
        # Update display
        if self.is_reading:
            self._highlight_current()
    
    def _load_sample_text(self):
        """Load sample text for demonstration."""
        sample_text = """Bienvenue dans le Lecteur Immersif d'Easy Genie Desktop!

Cet outil vous permet de lire du texte de manière immersive et concentrée. Vous pouvez charger vos propres fichiers texte ou coller du contenu depuis le presse-papiers.

Le lecteur offre plusieurs modes de lecture : phrase par phrase, paragraphe par paragraphe, ou texte complet. Vous pouvez également ajuster la vitesse de lecture selon vos préférences.

La synthèse vocale peut être activée pour une expérience de lecture audio. Le surlignage automatique vous aide à suivre votre progression dans le texte.

Profitez de cette expérience de lecture optimisée pour améliorer votre concentration et votre compréhension!"""
        
        self._set_text(sample_text)


class ReaderSettingsDialog(ctk.CTkToplevel):
    """Dialog for reader settings."""
    
    def __init__(self, parent):
        """Initialize settings dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.result = False
        
        # Configure dialog
        self.title("Paramètres du Lecteur")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Settings variables
        self.font_family_var = ctk.StringVar(value="Georgia")
        self.font_size_var = ctk.IntVar(value=16)
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.highlight_var = ctk.BooleanVar(value=True)
        
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
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ Paramètres du Lecteur",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # Font settings
        font_frame = ctk.CTkFrame(main_frame)
        font_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        font_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            font_frame,
            text="🔤 Police et Taille",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(15, 10), sticky="w", padx=15)
        
        # Font family
        ctk.CTkLabel(
            font_frame,
            text="Police:"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        font_menu = ctk.CTkOptionMenu(
            font_frame,
            values=["Georgia", "Times New Roman", "Arial", "Helvetica", "Verdana"],
            variable=self.font_family_var
        )
        font_menu.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=5)
        
        # Font size
        ctk.CTkLabel(
            font_frame,
            text="Taille:"
        ).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        size_frame = ctk.CTkFrame(font_frame, fg_color="transparent")
        size_frame.grid(row=2, column=1, sticky="ew", padx=(10, 15), pady=5)
        
        size_slider = ctk.CTkSlider(
            size_frame,
            from_=10,
            to=24,
            number_of_steps=14,
            variable=self.font_size_var
        )
        size_slider.pack(side="left", fill="x", expand=True)
        
        size_label = ctk.CTkLabel(
            size_frame,
            textvariable=self.font_size_var,
            width=30
        )
        size_label.pack(side="right", padx=(10, 0))
        
        # Reading settings
        reading_frame = ctk.CTkFrame(main_frame)
        reading_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(
            reading_frame,
            text="📖 Options de Lecture",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Auto-scroll
        auto_scroll_check = ctk.CTkCheckBox(
            reading_frame,
            text="Défilement automatique",
            variable=self.auto_scroll_var
        )
        auto_scroll_check.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # Highlight current
        highlight_check = ctk.CTkCheckBox(
            reading_frame,
            text="Surligner le texte actuel",
            variable=self.highlight_var
        )
        highlight_check.grid(row=2, column=0, sticky="w", padx=15, pady=(5, 15))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, sticky="ew")
        
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
    
    def _on_apply(self):
        """Handle apply button."""
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
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return {
            'font_family': self.font_family_var.get(),
            'font_size': self.font_size_var.get(),
            'auto_scroll': self.auto_scroll_var.get(),
            'highlight_current': self.highlight_var.get()
        }


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
    root.title("Test Immersive Reader Tool")
    root.geometry("1200x800")
    
    # Create tool instance
    tool = ImmersiveReaderTool(
        parent=root,
        magic_energy_level='genie'  # Test with AI features
    )
    tool.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()