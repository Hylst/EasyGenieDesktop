#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Main Window

Main application window with tool navigation and central hub.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Callable
from pathlib import Path
import threading
import time
from datetime import datetime

# Import core services
try:
    from ..core.database import DatabaseManager
    from ..core.ai_service import AIServiceManager
    from ..core.audio_service import AudioServiceManager
    from ..core.export_service import ExportServiceManager
    from ..config.settings import AppSettings
    from ..config.themes import ThemeManager
    from ..config.ai_config import AIProvider
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('..')
    from core.database import DatabaseManager
    from core.ai_service import AIServiceManager
    from core.audio_service import AudioServiceManager
    from core.export_service import ExportServiceManager
    from config.settings import AppSettings
    from config.themes import ThemeManager
    from config.ai_config import AIProvider


class MainWindow:
    """Main application window for Easy Genie Desktop."""
    
    def __init__(self, database_manager: DatabaseManager, settings_manager: AppSettings):
        """Initialize main window."""
        self.logger = logging.getLogger(__name__)
        
        # Core services
        self.settings_manager = settings_manager
        self.database_manager = database_manager
        
        # Initialize other services
        self.ai_service = AIServiceManager(settings_manager)
        self.audio_service = AudioServiceManager(settings_manager)
        self.export_service = ExportServiceManager(settings_manager)
        
        # Theme manager
        self.theme_manager = ThemeManager()
        
        # Window state
        self.current_tool = None
        self.tool_windows = {}
        self.magic_energy_level = self.settings_manager.get('tools.magic_energy_level', 'magic')
        self.current_user = None
        
        # UI components
        self.root = None
        self.main_frame = None
        self.sidebar = None
        self.content_area = None
        self.status_bar = None
        self.energy_indicator = None
        
        # Tool definitions
        self.tools = {
            'task_breaker': {
                'name': 'Task Breaker',
                'description': 'Décompose les tâches complexes en étapes simples',
                'icon': '🔨',
                'category': 'Productivité',
                'magic_features': ['Décomposition simple', 'Templates prédéfinis'],
                'genie_features': ['Analyse IA', 'Suggestions intelligentes', 'Optimisation automatique']
            },
            'time_focus': {
                'name': 'TimeFocus',
                'description': 'Gestion du temps et sessions de focus',
                'icon': '⏰',
                'category': 'Productivité',
                'magic_features': ['Timer Pomodoro', 'Suivi basique'],
                'genie_features': ['Adaptation IA', 'Analyse des patterns', 'Recommandations personnalisées']
            },
            'priority_grid': {
                'name': 'Priority Grid',
                'description': 'Matrice de priorisation des tâches',
                'icon': '📊',
                'category': 'Organisation',
                'magic_features': ['Grille Eisenhower', 'Tri manuel'],
                'genie_features': ['Priorisation IA', 'Analyse contextuelle', 'Suggestions dynamiques']
            },
            'brain_dump': {
                'name': 'Décharge de Pensées',
                'description': 'Capture et organisation des idées',
                'icon': '🧠',
                'category': 'Créativité',
                'magic_features': ['Capture rapide', 'Organisation simple'],
                'genie_features': ['Analyse sémantique', 'Extraction d\'insights', 'Mind mapping IA']
            },
            'formalizer': {
                'name': 'Formaliseur',
                'description': 'Transformation et amélioration de textes',
                'icon': '✍️',
                'category': 'Communication',
                'magic_features': ['Styles prédéfinis', 'Correction basique'],
                'genie_features': ['Réécriture IA', 'Adaptation contextuelle', 'Optimisation stylistique']
            },
            'routine_builder': {
                'name': 'RoutineBuilder',
                'description': 'Création et gestion de routines',
                'icon': '🔄',
                'category': 'Habitudes',
                'magic_features': ['Templates de routines', 'Suivi simple'],
                'genie_features': ['Optimisation IA', 'Adaptation comportementale', 'Suggestions personnalisées']
            },
            'immersive_reader': {
                'name': 'Lecteur Immersif',
                'description': 'Lecture assistée et analyse de textes',
                'icon': '📖',
                'category': 'Apprentissage',
                'magic_features': ['Lecture basique', 'Annotations simples'],
                'genie_features': ['Analyse IA', 'Résumés automatiques', 'Questions de compréhension']
            }
        }
        
        # Initialize UI
        self._setup_ui()
        self._load_user_preferences()
        self._setup_keyboard_shortcuts()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the main user interface."""
        # Configure CustomTkinter
        ctk.set_appearance_mode(self.settings_manager.get('appearance.theme', 'dark'))
        ctk.set_default_color_theme(self.settings_manager.get('appearance.color_theme', 'blue'))
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Easy Genie Desktop")
        
        # Window configuration
        window_width = self.settings_manager.get('window.width', 1200)
        window_height = self.settings_manager.get('window.height', 800)
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main layout
        self._create_sidebar()
        self._create_content_area()
        self._create_status_bar()
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<Configure>", self._on_window_configure)
    
    def _create_sidebar(self):
        """Create the sidebar with navigation and controls."""
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(4, weight=1)  # Tools section expands
        
        # Header
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🧞 Easy Genie", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack()
        
        # Magic Energy Level Indicator
        self._create_energy_indicator()
        
        # User Profile Section
        self._create_user_section()
        
        # Quick Actions
        self._create_quick_actions()
        
        # Tools Navigation
        self._create_tools_navigation()
        
        # Settings and Help
        self._create_bottom_section()
    
    def _create_energy_indicator(self):
        """Create the Magic Energy level indicator."""
        energy_frame = ctk.CTkFrame(self.sidebar)
        energy_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        energy_label = ctk.CTkLabel(
            energy_frame, 
            text="Niveau d'Énergie Magique", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        energy_label.pack(pady=(10, 5))
        
        # Energy level switch
        self.energy_switch = ctk.CTkSwitch(
            energy_frame,
            text="Genie Mode" if self.magic_energy_level == 'genie' else "Magic Mode",
            command=self._toggle_energy_level,
            progress_color=("#FF6B6B" if self.magic_energy_level == 'magic' else "#4ECDC4")
        )
        
        if self.magic_energy_level == 'genie':
            self.energy_switch.select()
        
        self.energy_switch.pack(pady=5)
        
        # Energy description
        energy_desc = (
            "🔮 Mode Genie: IA avancée activée" if self.magic_energy_level == 'genie' 
            else "✨ Mode Magic: Fonctions simples"
        )
        
        self.energy_desc_label = ctk.CTkLabel(
            energy_frame, 
            text=energy_desc, 
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.energy_desc_label.pack(pady=(0, 10))
    
    def _create_user_section(self):
        """Create user profile section."""
        user_frame = ctk.CTkFrame(self.sidebar)
        user_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Load current user (simplified for now)
        # TODO: Implement proper user management
        self.current_user = None
        user_text = "👤 Utilisateur Invité"
        
        user_label = ctk.CTkLabel(
            user_frame, 
            text=user_text, 
            font=ctk.CTkFont(size=12)
        )
        user_label.pack(pady=10)
        
        # User actions
        user_actions_frame = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_actions_frame.pack(fill="x", padx=5, pady=(0, 10))
        
        profile_btn = ctk.CTkButton(
            user_actions_frame,
            text="Profil",
            width=70,
            height=25,
            font=ctk.CTkFont(size=10),
            command=self._open_profile_settings
        )
        profile_btn.pack(side="left", padx=2)
        
        stats_btn = ctk.CTkButton(
            user_actions_frame,
            text="Stats",
            width=70,
            height=25,
            font=ctk.CTkFont(size=10),
            command=self._show_user_stats
        )
        stats_btn.pack(side="right", padx=2)
    
    def _create_quick_actions(self):
        """Create quick action buttons."""
        actions_frame = ctk.CTkFrame(self.sidebar)
        actions_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        actions_label = ctk.CTkLabel(
            actions_frame, 
            text="Actions Rapides", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        actions_label.pack(pady=(10, 5))
        
        # Quick action buttons
        quick_actions = [
            ("📝 Nouvelle Tâche", self._quick_new_task),
            ("🧠 Décharge Rapide", self._quick_brain_dump),
            ("⏰ Focus Session", self._quick_focus_session),
            ("📊 Voir Statistiques", self._show_dashboard),
            ("🔧 Diagnostic", self._show_diagnostic)
        ]
        
        for text, command in quick_actions:
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                height=30,
                font=ctk.CTkFont(size=10),
                command=command
            )
            btn.pack(fill="x", padx=5, pady=2)
    
    def _create_tools_navigation(self):
        """Create tools navigation section."""
        tools_frame = ctk.CTkFrame(self.sidebar)
        tools_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        
        tools_label = ctk.CTkLabel(
            tools_frame, 
            text="Outils", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        tools_label.pack(pady=(10, 5))
        
        # Create scrollable frame for tools
        self.tools_scroll = ctk.CTkScrollableFrame(tools_frame, height=300)
        self.tools_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        # Group tools by category
        categories = {}
        for tool_id, tool_info in self.tools.items():
            category = tool_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((tool_id, tool_info))
        
        # Create tool buttons by category
        for category, tools in categories.items():
            # Category header
            cat_label = ctk.CTkLabel(
                self.tools_scroll,
                text=category,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray"
            )
            cat_label.pack(anchor="w", padx=5, pady=(10, 2))
            
            # Tool buttons
            for tool_id, tool_info in tools:
                self._create_tool_button(tool_id, tool_info)
    
    def _create_tool_button(self, tool_id: str, tool_info: Dict):
        """Create a button for a specific tool."""
        # Tool frame
        tool_frame = ctk.CTkFrame(self.tools_scroll, fg_color="transparent")
        tool_frame.pack(fill="x", padx=2, pady=1)
        
        # Main tool button
        btn_text = f"{tool_info['icon']} {tool_info['name']}"
        tool_btn = ctk.CTkButton(
            tool_frame,
            text=btn_text,
            height=35,
            font=ctk.CTkFont(size=11),
            command=lambda: self._open_tool(tool_id),
            anchor="w"
        )
        tool_btn.pack(fill="x", pady=1)
        
        # Add hover tooltip with description and features
        self._add_tooltip(tool_btn, tool_info)
    
    def _add_tooltip(self, widget, tool_info: Dict):
        """Add tooltip to widget with tool information."""
        def on_enter(event):
            # Create tooltip window
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="#2b2b2b")
            
            # Position tooltip
            x = widget.winfo_rootx() + widget.winfo_width() + 10
            y = widget.winfo_rooty()
            tooltip.geometry(f"+{x}+{y}")
            
            # Tooltip content
            frame = tk.Frame(tooltip, bg="#2b2b2b", padx=10, pady=8)
            frame.pack()
            
            # Title
            title_label = tk.Label(
                frame, 
                text=tool_info['name'], 
                font=("Arial", 12, "bold"),
                bg="#2b2b2b", 
                fg="white"
            )
            title_label.pack(anchor="w")
            
            # Description
            desc_label = tk.Label(
                frame, 
                text=tool_info['description'], 
                font=("Arial", 10),
                bg="#2b2b2b", 
                fg="#cccccc",
                wraplength=250
            )
            desc_label.pack(anchor="w", pady=(2, 5))
            
            # Features based on current energy level
            features = (
                tool_info['genie_features'] if self.magic_energy_level == 'genie' 
                else tool_info['magic_features']
            )
            
            features_label = tk.Label(
                frame, 
                text=f"Fonctionnalités ({self.magic_energy_level.title()}):", 
                font=("Arial", 9, "bold"),
                bg="#2b2b2b", 
                fg="#4ECDC4" if self.magic_energy_level == 'genie' else "#FF6B6B"
            )
            features_label.pack(anchor="w")
            
            for feature in features:
                feature_label = tk.Label(
                    frame, 
                    text=f"• {feature}", 
                    font=("Arial", 9),
                    bg="#2b2b2b", 
                    fg="#cccccc"
                )
                feature_label.pack(anchor="w", padx=(10, 0))
            
            # Store tooltip reference
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _create_bottom_section(self):
        """Create bottom section with settings and help."""
        bottom_frame = ctk.CTkFrame(self.sidebar)
        bottom_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️ Paramètres",
            height=30,
            font=ctk.CTkFont(size=10),
            command=self._open_settings
        )
        settings_btn.pack(fill="x", padx=5, pady=2)
        
        # Help button
        help_btn = ctk.CTkButton(
            bottom_frame,
            text="❓ Aide",
            height=30,
            font=ctk.CTkFont(size=10),
            command=self._show_help
        )
        help_btn.pack(fill="x", padx=5, pady=2)
        
        # Export button
        export_btn = ctk.CTkButton(
            bottom_frame,
            text="📤 Exporter",
            height=30,
            font=ctk.CTkFont(size=10),
            command=self._show_export_dialog
        )
        export_btn.pack(fill="x", padx=5, pady=(2, 10))
    
    def _create_content_area(self):
        """Create the main content area with responsive configuration."""
        self.content_area = ctk.CTkFrame(self.root, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Configure responsive grid weights
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
        
        # Configure main window grid for responsive behavior
        self.root.grid_columnconfigure(1, weight=1)  # Content area column
        self.root.grid_rowconfigure(0, weight=1)     # Main content row
        
        # Welcome screen
        self._show_welcome_screen()
    
    def _show_welcome_screen(self):
        """Show the welcome screen in the content area."""
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        welcome_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        welcome_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        welcome_frame.grid_columnconfigure(0, weight=1)
        welcome_frame.grid_rowconfigure(1, weight=1)
        
        # Welcome header
        header_frame = ctk.CTkFrame(welcome_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        welcome_title = ctk.CTkLabel(
            header_frame,
            text="🧞 Bienvenue dans Easy Genie Desktop",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        welcome_title.pack(pady=20)
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Votre suite d'outils intelligents pour l'organisation et la productivité",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 20))
        
        # Main content with responsive configuration
        main_content = ctk.CTkFrame(welcome_frame)
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_columnconfigure((0, 1), weight=1, minsize=300)
        main_content.grid_rowconfigure(1, weight=1)
        
        # Store reference for responsive adjustments
        self.welcome_main_content = main_content
        
        # Quick start section
        quick_start_frame = ctk.CTkFrame(main_content)
        quick_start_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        
        qs_title = ctk.CTkLabel(
            quick_start_frame,
            text="🚀 Démarrage Rapide",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        qs_title.pack(pady=(15, 10))
        
        quick_actions = [
            ("📝 Créer une nouvelle tâche", self._quick_new_task),
            ("🧠 Faire une décharge de pensées", self._quick_brain_dump),
            ("⏰ Démarrer une session de focus", self._quick_focus_session),
            ("📊 Voir mes statistiques", self._show_dashboard)
        ]
        
        for text, command in quick_actions:
            btn = ctk.CTkButton(
                quick_start_frame,
                text=text,
                height=40,
                font=ctk.CTkFont(size=12),
                command=command
            )
            btn.pack(fill="x", padx=15, pady=5)
        
        # Recent activity section
        recent_frame = ctk.CTkFrame(main_content)
        recent_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        
        recent_title = ctk.CTkLabel(
            recent_frame,
            text="📈 Activité Récente",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        recent_title.pack(pady=(15, 10))
        
        # Get recent tasks (simplified for now)
        # TODO: Implement proper task management
        recent_tasks = []  # Placeholder
        
        if recent_tasks:
            for task in recent_tasks:
                task_frame = ctk.CTkFrame(recent_frame, fg_color="transparent")
                task_frame.pack(fill="x", padx=15, pady=2)
                
                status_icon = "✅" if task.get('status') == 'completed' else "⏳"
                task_text = f"{status_icon} {task.get('title', 'Tâche')[:40]}..."
                
                task_label = ctk.CTkLabel(
                    task_frame,
                    text=task_text,
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                task_label.pack(fill="x")
        else:
            no_tasks_label = ctk.CTkLabel(
                recent_frame,
                text="Aucune tâche récente\n\nCommencez par créer votre première tâche !",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_tasks_label.pack(expand=True, pady=20)
        
        # Tips section
        tips_frame = ctk.CTkFrame(main_content)
        tips_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        tips_title = ctk.CTkLabel(
            tips_frame,
            text="💡 Conseil du Jour",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tips_title.pack(pady=(15, 5))
        
        # Random tip
        tips = [
            "Utilisez le mode Genie pour bénéficier de l'assistance IA avancée !",
            "Le Task Breaker peut vous aider à décomposer vos projets complexes.",
            "Essayez une session TimeFocus pour améliorer votre concentration.",
            "La Décharge de Pensées est parfaite pour vider votre esprit.",
            "Utilisez les raccourcis clavier pour naviguer plus rapidement."
        ]
        
        import random
        tip_text = random.choice(tips)
        
        tip_label = ctk.CTkLabel(
            tips_frame,
            text=tip_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=800
        )
        tip_label.pack(pady=(0, 15))
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(1, weight=1)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Prêt",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # AI status
        ai_configured = self.ai_service.current_provider.value != 'none'
        ai_status = "IA Connectée" if ai_configured else "IA Non Configurée"
        ai_color = "green" if ai_configured else "orange"
        
        self.ai_status_label = ctk.CTkLabel(
            self.status_bar,
            text=f"🤖 {ai_status}",
            font=ctk.CTkFont(size=10),
            text_color=ai_color
        )
        self.ai_status_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        # Time
        self.time_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=10)
        )
        self.time_label.grid(row=0, column=3, padx=10, pady=5, sticky="e")
        
        # Update time every minute
        self._update_time()
    
    def _update_time(self):
        """Update the time display."""
        current_time = datetime.now().strftime("%H:%M")
        self.time_label.configure(text=current_time)
        self.root.after(60000, self._update_time)  # Update every minute
    
    def _load_user_preferences(self):
        """Load user preferences and apply them."""
        try:
            # Apply theme
            theme = self.settings_manager.get('appearance.theme', 'dark')
            ctk.set_appearance_mode(theme)
            
            # Apply accessibility settings
            if self.settings_manager.get('accessibility.high_contrast', False):
                self.theme_manager.apply_accessibility_preset('high_contrast')
            
            self.logger.info("User preferences loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load user preferences: {e}")
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        shortcuts = self.settings_manager.get('shortcuts', {})
        
        # Default shortcuts
        default_shortcuts = {
            '<Control-n>': self._quick_new_task,
            '<Control-b>': self._quick_brain_dump,
            '<Control-f>': self._quick_focus_session,
            '<Control-s>': self._open_settings,
            '<Control-q>': self._on_closing,
            '<F1>': self._show_help
        }
        
        # Bind shortcuts
        for shortcut, command in default_shortcuts.items():
            self.root.bind(shortcut, lambda e, cmd=command: cmd())
        
        self.logger.info("Keyboard shortcuts configured")
    
    # Event handlers
    def _toggle_energy_level(self):
        """Toggle between Magic and Genie energy levels."""
        if self.energy_switch.get():
            self.magic_energy_level = 'genie'
            self.energy_switch.configure(text="Genie Mode")
            self.energy_desc_label.configure(text="🔮 Mode Genie: IA avancée activée")
        else:
            self.magic_energy_level = 'magic'
            self.energy_switch.configure(text="Magic Mode")
            self.energy_desc_label.configure(text="✨ Mode Magic: Fonctions simples")
        
        # Save setting
        self.settings_manager.set('tools.magic_energy_level', self.magic_energy_level)
        
        # Update status
        self.set_status(f"Mode {self.magic_energy_level.title()} activé")
        
        # Play audio feedback
        if self.audio_service:
            self.audio_service.play_sound('mode_change')
        
        self.logger.info(f"Energy level changed to: {self.magic_energy_level}")
    
    def _open_tool(self, tool_id: str):
        """Open a specific tool in the main content area."""
        try:
            self.set_status(f"Ouverture de {self.tools[tool_id]['name']}...")
            
            # Clear content area
            for widget in self.content_area.winfo_children():
                widget.destroy()
            
            # Import and instantiate the specific tool
            if tool_id == 'brain_dump':
                from ui.tools.brain_dump import BrainDumpTool
                tool = BrainDumpTool(
                    parent=self.content_area,
                    ai_service=self.ai_service,
                    database_manager=self.database_manager,
                    audio_service=self.audio_service,
                    settings_manager=self.settings_manager
                )
                tool.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            elif tool_id == 'task_breaker':
                from ui.tools.task_breaker import TaskBreakerTool
                tool = TaskBreakerTool(
                    parent=self.content_area,
                    magic_energy_level=self.magic_energy_level,
                    ai_service=self.ai_service,
                    database_manager=self.database_manager,
                    audio_service=self.audio_service,
                    settings_manager=self.settings_manager
                )
                tool.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            elif tool_id == 'priority_grid':
                self._create_integrated_priority_grid()
            elif tool_id == 'time_focus':
                self._create_integrated_time_focus()
            elif tool_id == 'formalizer':
                self._create_integrated_formalizer()
            elif tool_id == 'routine_builder':
                self._create_integrated_routine_builder()
            elif tool_id == 'immersive_reader':
                self._create_integrated_immersive_reader()
            else:
                # For other tools, show placeholder for now
                self._show_tool_placeholder(tool_id)
            
            self.current_tool = tool_id
            self.logger.info(f"Opened tool: {tool_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to open tool {tool_id}: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'outil: {e}")
    
    def _show_tool_placeholder(self, tool_id: str):
        """Show placeholder for tool (temporary)."""
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tool_info = self.tools[tool_id]
        
        placeholder_frame = ctk.CTkFrame(self.content_area)
        placeholder_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        placeholder_frame.grid_columnconfigure(0, weight=1)
        placeholder_frame.grid_rowconfigure(0, weight=1)
        
        content_frame = ctk.CTkFrame(placeholder_frame, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Tool icon and name
        title_label = ctk.CTkLabel(
            content_frame,
            text=f"{tool_info['icon']} {tool_info['name']}",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Description
        desc_label = ctk.CTkLabel(
            content_frame,
            text=tool_info['description'],
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        desc_label.pack(pady=10)
        
        # Current mode features
        features = (
            tool_info['genie_features'] if self.magic_energy_level == 'genie' 
            else tool_info['magic_features']
        )
        
        mode_label = ctk.CTkLabel(
            content_frame,
            text=f"Mode {self.magic_energy_level.title()} - Fonctionnalités disponibles:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        mode_label.pack(pady=(20, 10))
        
        for feature in features:
            feature_label = ctk.CTkLabel(
                content_frame,
                text=f"• {feature}",
                font=ctk.CTkFont(size=12)
            )
            feature_label.pack(anchor="w", padx=20)
        
        # Coming soon message
        coming_soon_label = ctk.CTkLabel(
            content_frame,
            text="🚧 Cet outil sera disponible dans une prochaine version",
            font=ctk.CTkFont(size=14),
            text_color="orange"
        )
        coming_soon_label.pack(pady=30)
        
        # Back button
        back_btn = ctk.CTkButton(
            content_frame,
            text="← Retour à l'accueil",
            command=self._show_welcome_screen
        )
        back_btn.pack(pady=10)
    
    # Quick action methods
    def _quick_new_task(self):
        """Quick new task creation."""
        self.set_status("Création d'une nouvelle tâche...")
        self._open_tool('task_breaker')
    
    def _quick_brain_dump(self):
        """Quick brain dump."""
        self.set_status("Ouverture de la décharge de pensées...")
        self._open_tool('brain_dump')
    
    def _quick_focus_session(self):
        """Quick focus session."""
        self.set_status("Démarrage d'une session de focus...")
        self._open_tool('time_focus')
    
    def _show_dashboard(self):
        """Show user dashboard with statistics."""
        self.set_status("Chargement du tableau de bord...")
        # TODO: Show dashboard
        messagebox.showinfo("Info", "Fonctionnalité en développement")
    
    def _open_profile_settings(self):
        """Open profile settings."""
        # TODO: Open profile settings dialog
        messagebox.showinfo("Info", "Paramètres de profil en développement")
    
    def _show_user_stats(self):
        """Show user statistics."""
        # TODO: Show user statistics
        messagebox.showinfo("Info", "Statistiques utilisateur en développement")
    
    def _create_integrated_priority_grid(self):
        """Create integrated Priority Grid tool in content area."""
        # Create main container
        tool_frame = ctk.CTkFrame(self.content_area)
        tool_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_rowconfigure(1, weight=1)
        
        # Header with back button
        header_frame = ctk.CTkFrame(tool_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Accueil",
            width=100,
            command=self._show_welcome_screen
        )
        back_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Matrice d'Eisenhower - Grille de Priorités",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Main content
        content_frame = ctk.CTkFrame(tool_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(2, weight=1)
        
        # Headers
        ctk.CTkLabel(content_frame, text="", width=120).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(content_frame, text="URGENT", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(content_frame, text="PAS URGENT", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=5)
        
        ctk.CTkLabel(content_frame, text="IMPORTANT", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=5, pady=5, sticky="n")
        ctk.CTkLabel(content_frame, text="PAS IMPORTANT", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=5, pady=5, sticky="n")
        
        # Quadrants
        q1 = ctk.CTkTextbox(content_frame, height=200)
        q1.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        q1.insert("1.0", "Q1: FAIRE\n- Crises\n- Urgences\n- Projets à échéance")
        
        q2 = ctk.CTkTextbox(content_frame, height=200)
        q2.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        q2.insert("1.0", "Q2: PLANIFIER\n- Prévention\n- Développement\n- Planification")
        
        q3 = ctk.CTkTextbox(content_frame, height=200)
        q3.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        q3.insert("1.0", "Q3: DÉLÉGUER\n- Interruptions\n- Certains appels\n- Certains emails")
        
        q4 = ctk.CTkTextbox(content_frame, height=200)
        q4.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")
        q4.insert("1.0", "Q4: ÉLIMINER\n- Distractions\n- Perte de temps\n- Activités inutiles")
        
        # Action buttons
        button_frame = ctk.CTkFrame(tool_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Sauvegarder",
            command=lambda: self.set_status("Grille sauvegardée avec succès!")
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        export_btn = ctk.CTkButton(
            button_frame,
            text="📤 Exporter",
            command=lambda: self.set_status("Fonctionnalité d'export disponible bientôt!")
        )
        export_btn.pack(side="left")
    
    def _create_integrated_time_focus(self):
        """Create integrated TimeFocus tool in content area."""
        # Create main container
        tool_frame = ctk.CTkFrame(self.content_area)
        tool_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_rowconfigure(1, weight=1)
        
        # Header with back button
        header_frame = ctk.CTkFrame(tool_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Accueil",
            width=100,
            command=self._show_welcome_screen
        )
        back_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="⏰ TimeFocus - Technique Pomodoro",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Main content
        content_frame = ctk.CTkFrame(tool_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Timer display
        timer_frame = ctk.CTkFrame(content_frame)
        timer_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        time_label = ctk.CTkLabel(
            timer_frame,
            text="25:00",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        time_label.pack(pady=20)
        
        status_label = ctk.CTkLabel(
            timer_frame,
            text="Prêt à commencer",
            font=ctk.CTkFont(size=14)
        )
        status_label.pack(pady=10)
        
        # Controls
        controls_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        controls_frame.grid(row=1, column=0, pady=20)
        
        start_btn = ctk.CTkButton(
            controls_frame,
            text="▶️ Démarrer",
            width=120,
            height=40,
            command=lambda: self.set_status("Timer démarré!")
        )
        start_btn.pack(side="left", padx=5)
        
        reset_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Reset",
            width=100,
            height=40,
            command=lambda: self.set_status("Timer remis à zéro")
        )
        reset_btn.pack(side="left", padx=5)
        
        # Session selector
        session_frame = ctk.CTkFrame(content_frame)
        session_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            session_frame,
            text="Type de session:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        session_menu = ctk.CTkOptionMenu(
            session_frame,
            values=["Travail (25 min)", "Pause courte (5 min)", "Pause longue (15 min)"]
        )
        session_menu.pack(pady=(0, 10))
        
        # Stats
        stats_frame = ctk.CTkFrame(content_frame)
        stats_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            stats_frame,
            text="📊 Sessions aujourd'hui: 0",
            font=ctk.CTkFont(size=12)
        ).pack(pady=10)
    
    def _create_integrated_formalizer(self):
        """Create integrated Formalizer tool in content area."""
        # Create main container
        tool_frame = ctk.CTkFrame(self.content_area)
        tool_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_rowconfigure(1, weight=1)
        
        # Header with back button
        header_frame = ctk.CTkFrame(tool_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Accueil",
            width=100,
            command=self._show_welcome_screen
        )
        back_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="✍️ Formaliseur de Texte",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Main content
        content_frame = ctk.CTkFrame(tool_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Input section
        input_frame = ctk.CTkFrame(content_frame)
        input_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(10, 5))
        
        ctk.CTkLabel(
            input_frame,
            text="Texte original:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        input_text = ctk.CTkTextbox(input_frame, height=200)
        input_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        input_frame.grid_rowconfigure(1, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Output section
        output_frame = ctk.CTkFrame(content_frame)
        output_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(10, 5))
        
        ctk.CTkLabel(
            output_frame,
            text="Texte formalisé:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        output_text = ctk.CTkTextbox(output_frame, height=200)
        output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # Controls
        controls_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        
        style_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["Professionnel", "Académique", "Décontracté", "Technique"]
        )
        style_menu.pack(side="left", padx=5)
        
        format_btn = ctk.CTkButton(
            controls_frame,
            text="✨ Formaliser",
            command=lambda: self.set_status("Texte formalisé avec succès!")
        )
        format_btn.pack(side="left", padx=5)
        
        copy_btn = ctk.CTkButton(
            controls_frame,
            text="📋 Copier",
            command=lambda: self.set_status("Texte copié dans le presse-papiers")
        )
        copy_btn.pack(side="left", padx=5)
    
    def _create_integrated_routine_builder(self):
        """Create integrated Routine Builder tool in content area."""
        # Create main container
        tool_frame = ctk.CTkFrame(self.content_area)
        tool_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_rowconfigure(1, weight=1)
        
        # Header with back button
        header_frame = ctk.CTkFrame(tool_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Accueil",
            width=100,
            command=self._show_welcome_screen
        )
        back_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔄 Constructeur de Routines",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Main content
        content_frame = ctk.CTkFrame(tool_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Routine list
        list_frame = ctk.CTkFrame(content_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ctk.CTkLabel(
            list_frame,
            text="Mes Routines:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        routine_list = ctk.CTkScrollableFrame(list_frame, height=300)
        routine_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Sample routines
        sample_routines = [
            "🌅 Routine Matinale",
            "💼 Routine Travail",
            "🌙 Routine Soirée",
            "🏃 Routine Sport"
        ]
        
        for routine in sample_routines:
            routine_btn = ctk.CTkButton(
                routine_list,
                text=routine,
                height=30,
                anchor="w"
            )
            routine_btn.pack(fill="x", pady=2)
        
        # Routine details
        details_frame = ctk.CTkFrame(content_frame)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(
            details_frame,
            text="Détails de la Routine:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        details_text = ctk.CTkTextbox(details_frame, height=250)
        details_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        details_text.insert("1.0", "Sélectionnez une routine pour voir ses détails...")
        
        # Controls
        controls_frame = ctk.CTkFrame(tool_frame, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        new_btn = ctk.CTkButton(
            controls_frame,
            text="➕ Nouvelle Routine",
            command=lambda: self.set_status("Création d'une nouvelle routine...")
        )
        new_btn.pack(side="left", padx=(0, 10))
        
        edit_btn = ctk.CTkButton(
            controls_frame,
            text="✏️ Modifier",
            command=lambda: self.set_status("Mode édition activé")
        )
        edit_btn.pack(side="left", padx=(0, 10))
        
        save_btn = ctk.CTkButton(
            controls_frame,
            text="💾 Sauvegarder",
            command=lambda: self.set_status("Routine sauvegardée!")
        )
        save_btn.pack(side="left")
    
    def _create_integrated_immersive_reader(self):
        """Create integrated Immersive Reader tool in content area."""
        # Create main container
        tool_frame = ctk.CTkFrame(self.content_area)
        tool_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_rowconfigure(1, weight=1)
        
        # Header with back button
        header_frame = ctk.CTkFrame(tool_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Accueil",
            width=100,
            command=self._show_welcome_screen
        )
        back_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📖 Lecteur Immersif",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Main content
        content_frame = ctk.CTkFrame(tool_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Reading controls
        controls_frame = ctk.CTkFrame(content_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        load_btn = ctk.CTkButton(
            controls_frame,
            text="📁 Charger Fichier",
            command=lambda: self.set_status("Sélection de fichier...")
        )
        load_btn.pack(side="left", padx=(0, 10))
        
        font_size_label = ctk.CTkLabel(controls_frame, text="Taille:")
        font_size_label.pack(side="left", padx=(0, 5))
        
        font_size_slider = ctk.CTkSlider(
            controls_frame,
            from_=10,
            to=24,
            number_of_steps=14
        )
        font_size_slider.pack(side="left", padx=(0, 10))
        font_size_slider.set(14)
        
        highlight_btn = ctk.CTkButton(
            controls_frame,
            text="🖍️ Surligner",
            width=100,
            command=lambda: self.set_status("Mode surlignage activé")
        )
        highlight_btn.pack(side="left", padx=(0, 10))
        
        # Reading area
        reading_frame = ctk.CTkFrame(content_frame)
        reading_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        reading_frame.grid_columnconfigure(0, weight=1)
        reading_frame.grid_rowconfigure(0, weight=1)
        
        text_area = ctk.CTkTextbox(reading_frame, font=ctk.CTkFont(size=14))
        text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_area.insert("1.0", "Bienvenue dans le Lecteur Immersif!\n\nChargez un fichier texte pour commencer la lecture.\n\nFonctionnalités disponibles:\n• Ajustement de la taille de police\n• Surlignage de texte\n• Annotations\n• Mode focus\n\nUtilisez les contrôles ci-dessus pour personnaliser votre expérience de lecture.")
        
        # Bottom controls
        bottom_controls = ctk.CTkFrame(tool_frame, fg_color="transparent")
        bottom_controls.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        notes_btn = ctk.CTkButton(
            bottom_controls,
            text="📝 Notes",
            command=lambda: self.set_status("Panneau de notes ouvert")
        )
        notes_btn.pack(side="left", padx=(0, 10))
        
        summary_btn = ctk.CTkButton(
            bottom_controls,
            text="📋 Résumé",
            command=lambda: self.set_status("Génération du résumé...")
        )
        summary_btn.pack(side="left", padx=(0, 10))
        
        focus_btn = ctk.CTkButton(
            bottom_controls,
            text="🎯 Mode Focus",
            command=lambda: self.set_status("Mode focus activé")
        )
        focus_btn.pack(side="left")
        # TODO: Show user statistics window
        messagebox.showinfo("Info", "Statistiques utilisateur en développement")
    
    def _open_settings(self):
        """Open application settings."""
        # TODO: Open settings window
        messagebox.showinfo("Info", "Paramètres en développement")
    
    def _show_help(self):
        """Show help and documentation."""
        # TODO: Open help window
        messagebox.showinfo("Aide", "Documentation en développement")
    
    def _show_diagnostic(self):
        """Show diagnostic tool."""
        try:
            from ui.tools.diagnostic_tool import DiagnosticTool
            diagnostic = DiagnosticTool(self)
            diagnostic.show_diagnostic_window()
        except Exception as e:
            self.logger.error(f"Erreur ouverture diagnostic: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le diagnostic: {e}")
    
    def _show_export_dialog(self):
        """Show export dialog."""
        # TODO: Open export dialog
        messagebox.showinfo("Info", "Export en développement")
    
    # Window event handlers
    def _on_window_configure(self, event):
        """Handle window resize/move events with responsive design."""
        if event.widget == self.root:
            # Save window size and position
            geometry = self.root.geometry()
            self.settings_manager.set('window.geometry', geometry)
            
            # Get current window dimensions
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # Apply responsive layout adjustments
            self._adjust_responsive_layout(width, height)
    
    def _adjust_responsive_layout(self, width: int, height: int):
        """Adjust layout based on window size for responsive design."""
        try:
            # Adjust sidebar width based on window width
            if width < 900:
                # Compact mode for smaller windows
                self.sidebar.configure(width=180)
                # Reduce padding in content area
                if hasattr(self, 'content_area'):
                    self.content_area.grid_configure(padx=5, pady=5)
            elif width < 1200:
                # Medium mode
                self.sidebar.configure(width=220)
                if hasattr(self, 'content_area'):
                    self.content_area.grid_configure(padx=8, pady=8)
            else:
                # Full mode for larger windows
                self.sidebar.configure(width=250)
                if hasattr(self, 'content_area'):
                    self.content_area.grid_configure(padx=10, pady=10)
            
            # Adjust tools scroll area height based on window height
            if hasattr(self, 'tools_scroll'):
                if height < 600:
                    self.tools_scroll.configure(height=150)
                elif height < 800:
                    self.tools_scroll.configure(height=200)
                else:
                    self.tools_scroll.configure(height=250)
            
            # Adjust quick actions layout for very small windows
            if hasattr(self, 'quick_actions_frame') and width < 800:
                # Stack quick action buttons vertically for small windows
                self._adjust_quick_actions_layout(compact=True)
            elif hasattr(self, 'quick_actions_frame'):
                # Use horizontal layout for larger windows
                self._adjust_quick_actions_layout(compact=False)
                
        except Exception as e:
            self.logger.warning(f"Error adjusting responsive layout: {e}")
    
    def _adjust_quick_actions_layout(self, compact: bool = False):
        """Adjust quick actions layout based on window size."""
        try:
            if not hasattr(self, 'quick_actions_frame'):
                return
                
            # This would adjust the layout of quick action buttons
            # Implementation depends on how quick_actions_frame is structured
            pass
        except Exception as e:
            self.logger.warning(f"Error adjusting quick actions layout: {e}")
    
    def _on_closing(self):
        """Handle window closing."""
        try:
            # Save settings
            self.settings_manager.save_settings()
            
            # Shutdown services
            if self.audio_service:
                self.audio_service.shutdown()
            
            # Close database
            if self.database_manager:
                self.database_manager.close()
            
            self.logger.info("Application closing")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        finally:
            self.root.destroy()
    
    # Utility methods
    def set_status(self, message: str, duration: int = 3000):
        """Set status bar message."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            
            # Clear status after duration
            if duration > 0:
                self.root.after(duration, lambda: self.status_label.configure(text="Prêt"))
    
    def run(self):
        """Start the main application loop."""
        try:
            self.logger.info("Starting main application loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
    
    def get_current_tool(self) -> Optional[str]:
        """Get the currently active tool."""
        return self.current_tool
    
    def get_magic_energy_level(self) -> str:
        """Get the current magic energy level."""
        return self.magic_energy_level
    
    def get_current_user(self) -> Optional[Dict]:
        """Get the current user."""
        return self.current_user