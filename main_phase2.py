"""Easy Genie Desktop - Phase 2 Main Application.

This is the main entry point for Phase 2 of Easy Genie Desktop, featuring:
- Advanced AI service with multiple providers and intelligent routing
- Comprehensive UI system with theming, navigation, and dialog management
- Voice command system for hands-free interaction
- Audio system for playback and recording
- Export system for various data formats
- Database system for data persistence
- Notification system for user alerts
- Analytics system for usage tracking
- Security system for authentication and data protection
"""

import sys
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# GUI imports
import customtkinter as ctk
from tkinter import messagebox

# Core system imports
from core.ai_service.advanced_service import (
    AdvancedAIService, AdvancedAIConfig, AIMode, LearningMode
)
from core.voice.voice_command_system import (
    VoiceCommandSystem, VoiceSettings, initialize_voice_system
)
from core.audio.audio_system import (
    AudioSystem, AudioConfig, initialize_audio_system
)
from core.export.export_system import (
    ExportSystem, ExportConfig, initialize_export_system
)
from core.database.database_system import (
    DatabaseSystem, DatabaseConfig, initialize_database_system
)
from core.notifications.notification_system import (
    NotificationSystem, NotificationSettings, initialize_notification_system
)
from core.analytics.analytics_system import (
    AnalyticsSystem, AnalyticsConfig, initialize_analytics
)
from core.security.security_system import (
    SecuritySystem, SecurityConfig, initialize_security, UserRole
)

# UI system imports
from ui.components.theme_manager import (
    ThemeManager, ThemeConfig, ThemeMode, get_theme_manager, set_theme
)
from ui.components.dialog_manager import (
    DialogManager, DialogType, DialogPriority
)
from ui.components.widget_factory import (
    WidgetFactory, WidgetConfig
)
from ui.components.navigation_manager import (
    NavigationManager, NavigationType, ViewType, get_navigation_manager
)

# Tool imports
from tools.ai_chat.ai_chat_tool import AIChatTool
from tools.voice_assistant.voice_assistant_tool import VoiceAssistantTool
from tools.document_processor.document_processor_tool import DocumentProcessorTool
from tools.media_converter.media_converter_tool import MediaConverterTool
from tools.system_optimizer.system_optimizer_tool import SystemOptimizerTool
from tools.automation_builder.automation_builder_tool import AutomationBuilderTool
from tools.smart_organizer.smart_organizer_tool import SmartOrganizerTool


class EasyGeniePhase2:
    """Main application class for Easy Genie Desktop Phase 2."""
    
    def __init__(self):
        """Initialize the application."""
        # Setup logging
        self._setup_logging()
        
        # Application state
        self.running = False
        self.current_user = None
        
        # Core systems
        self.ai_service: Optional[AdvancedAIService] = None
        self.voice_system: Optional[VoiceCommandSystem] = None
        self.audio_system: Optional[AudioSystem] = None
        self.export_system: Optional[ExportSystem] = None
        self.database_system: Optional[DatabaseSystem] = None
        self.notification_system: Optional[NotificationSystem] = None
        self.analytics_system: Optional[AnalyticsSystem] = None
        self.security_system: Optional[SecuritySystem] = None
        
        # UI systems
        self.theme_manager: Optional[ThemeManager] = None
        self.dialog_manager: Optional[DialogManager] = None
        self.widget_factory: Optional[WidgetFactory] = None
        self.navigation_manager: Optional[NavigationManager] = None
        
        # Main window
        self.root: Optional[ctk.CTk] = None
        
        # Tools
        self.tools = {}
        
        logging.info("Easy Genie Desktop Phase 2 initialized")
    
    def _setup_logging(self):
        """Setup application logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"easy_genie_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def initialize_systems(self):
        """Initialize all core systems."""
        try:
            logging.info("Initializing core systems...")
            
            # Initialize security system first
            security_config = SecurityConfig(
                database_path=Path("data/security.db"),
                enable_security_logging=True,
                enable_intrusion_detection=True
            )
            self.security_system = initialize_security(security_config)
            logging.info("Security system initialized")
            
            # Initialize database system
            database_config = DatabaseConfig(
                database_path=Path("data/main.db"),
                enable_wal_mode=True,
                enable_foreign_keys=True
            )
            self.database_system = initialize_database_system(database_config)
            logging.info("Database system initialized")
            
            # Initialize analytics system
            analytics_config = AnalyticsConfig(
                database_path=Path("data/analytics.db"),
                enabled=True,
                collect_user_events=True,
                collect_performance_metrics=True
            )
            self.analytics_system = initialize_analytics(analytics_config)
            logging.info("Analytics system initialized")
            
            # Initialize notification system
            notification_settings = NotificationSettings(
                enable_toast=True,
                enable_sound=True,
                enable_email=False  # Disabled by default
            )
            self.notification_system = initialize_notification_system(notification_settings)
            logging.info("Notification system initialized")
            
            # Initialize export system
            export_config = ExportConfig(
                default_output_dir=Path("exports"),
                enable_compression=True,
                enable_encryption=True
            )
            self.export_system = initialize_export_system(export_config)
            logging.info("Export system initialized")
            
            # Initialize audio system
            audio_config = AudioConfig(
                enable_recording=True,
                enable_playback=True,
                default_sample_rate=44100
            )
            self.audio_system = initialize_audio_system(audio_config)
            logging.info("Audio system initialized")
            
            # Initialize voice system
            voice_settings = VoiceSettings(
                recognition_engine="google",
                tts_engine="pyttsx3",
                enable_wake_word=True,
                wake_word="hey genie"
            )
            self.voice_system = initialize_voice_system(voice_settings)
            logging.info("Voice system initialized")
            
            # Initialize AI service
            ai_config = AdvancedAIConfig(
                default_mode=AIMode.HYBRID,
                learning_mode=LearningMode.ACTIVE,
                enable_caching=True,
                enable_analytics=True
            )
            self.ai_service = AdvancedAIService(ai_config)
            logging.info("AI service initialized")
            
            logging.info("All core systems initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize core systems: {e}")
            raise
    
    def initialize_ui_systems(self):
        """Initialize UI systems."""
        try:
            logging.info("Initializing UI systems...")
            
            # Initialize theme manager
            theme_config = ThemeConfig(
                mode=ThemeMode.SYSTEM,
                custom_themes_dir=Path("themes")
            )
            self.theme_manager = ThemeManager(theme_config)
            logging.info("Theme manager initialized")
            
            # Initialize widget factory
            widget_config = WidgetConfig()
            self.widget_factory = WidgetFactory(widget_config)
            logging.info("Widget factory initialized")
            
            # Initialize dialog manager (will be set after root window)
            self.dialog_manager = None
            
            # Initialize navigation manager (will be set after root window)
            self.navigation_manager = None
            
            logging.info("UI systems initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize UI systems: {e}")
            raise
    
    def create_main_window(self):
        """Create the main application window."""
        try:
            logging.info("Creating main window...")
            
            # Set CustomTkinter appearance
            ctk.set_appearance_mode("system")
            ctk.set_default_color_theme("blue")
            
            # Create main window
            self.root = ctk.CTk()
            self.root.title("Easy Genie Desktop - Phase 2")
            self.root.geometry("1400x900")
            self.root.minsize(1000, 700)
            
            # Set window icon (if available)
            try:
                icon_path = Path("assets/icon.ico")
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            except Exception:
                pass  # Icon not critical
            
            # Apply theme
            if self.theme_manager:
                self.theme_manager.apply_theme(self.root)
            
            # Initialize dialog manager with root window
            self.dialog_manager = DialogManager(self.root)
            
            # Initialize navigation manager with root window
            self.navigation_manager = NavigationManager(self.root)
            
            # Setup window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logging.info("Main window created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create main window: {e}")
            raise
    
    def initialize_tools(self):
        """Initialize all tools."""
        try:
            logging.info("Initializing tools...")
            
            # Initialize tools with their dependencies
            self.tools = {
                'ai_chat': AIChatTool(
                    ai_service=self.ai_service,
                    analytics_system=self.analytics_system
                ),
                'voice_assistant': VoiceAssistantTool(
                    voice_system=self.voice_system,
                    ai_service=self.ai_service,
                    audio_system=self.audio_system
                ),
                'document_processor': DocumentProcessorTool(
                    ai_service=self.ai_service,
                    export_system=self.export_system
                ),
                'media_converter': MediaConverterTool(
                    audio_system=self.audio_system,
                    notification_system=self.notification_system
                ),
                'system_optimizer': SystemOptimizerTool(
                    analytics_system=self.analytics_system,
                    notification_system=self.notification_system
                ),
                'automation_builder': AutomationBuilderTool(
                    voice_system=self.voice_system,
                    notification_system=self.notification_system
                ),
                'smart_organizer': SmartOrganizerTool(
                    ai_service=self.ai_service,
                    database_system=self.database_system
                )
            }
            
            # Register tools with navigation manager
            if self.navigation_manager:
                for tool_name, tool in self.tools.items():
                    self.navigation_manager.register_tool_view(tool_name, tool)
            
            logging.info("All tools initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize tools: {e}")
            raise
    
    def setup_main_interface(self):
        """Setup the main user interface."""
        try:
            logging.info("Setting up main interface...")
            
            # Create main container
            main_container = ctk.CTkFrame(self.root)
            main_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create header
            self._create_header(main_container)
            
            # Create navigation sidebar
            self._create_sidebar(main_container)
            
            # Create main content area
            self._create_content_area(main_container)
            
            # Create status bar
            self._create_status_bar(main_container)
            
            # Setup keyboard shortcuts
            self._setup_keyboard_shortcuts()
            
            # Show welcome screen
            self._show_welcome_screen()
            
            logging.info("Main interface setup completed")
            
        except Exception as e:
            logging.error(f"Failed to setup main interface: {e}")
            raise
    
    def _create_header(self, parent):
        """Create application header."""
        header_frame = ctk.CTkFrame(parent, height=60)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # App title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Easy Genie Desktop - Phase 2",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Header buttons
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20, pady=10)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            button_frame,
            text="Settings",
            width=100,
            command=self._open_settings
        )
        settings_btn.pack(side="right", padx=(10, 0))
        
        # Profile button
        profile_btn = ctk.CTkButton(
            button_frame,
            text="Profile",
            width=100,
            command=self._open_profile
        )
        profile_btn.pack(side="right", padx=(10, 0))
        
        # Voice toggle button
        voice_btn = ctk.CTkButton(
            button_frame,
            text="🎤 Voice",
            width=100,
            command=self._toggle_voice
        )
        voice_btn.pack(side="right", padx=(10, 0))
    
    def _create_sidebar(self, parent):
        """Create navigation sidebar."""
        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(parent, width=250)
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="Tools",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        sidebar_title.pack(pady=(20, 10))
        
        # Tool buttons
        tool_configs = [
            ("🤖 AI Chat", "ai_chat", "Chat with advanced AI assistants"),
            ("🎙️ Voice Assistant", "voice_assistant", "Voice-controlled AI assistant"),
            ("📄 Document Processor", "document_processor", "Process and analyze documents"),
            ("🎵 Media Converter", "media_converter", "Convert audio and video files"),
            ("⚡ System Optimizer", "system_optimizer", "Optimize system performance"),
            ("🔧 Automation Builder", "automation_builder", "Build custom automations"),
            ("📁 Smart Organizer", "smart_organizer", "Organize files intelligently")
        ]
        
        self.tool_buttons = {}
        for icon_text, tool_id, description in tool_configs:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=icon_text,
                width=220,
                height=50,
                font=ctk.CTkFont(size=14),
                command=lambda t=tool_id: self._open_tool(t)
            )
            btn.pack(pady=5, padx=15)
            self.tool_buttons[tool_id] = btn
            
            # Add tooltip (description)
            self._add_tooltip(btn, description)
    
    def _create_content_area(self, parent):
        """Create main content area."""
        self.content_frame = ctk.CTkFrame(parent)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # This will be managed by the navigation manager
        if self.navigation_manager:
            self.navigation_manager.set_content_frame(self.content_frame)
    
    def _create_status_bar(self, parent):
        """Create status bar."""
        self.status_frame = ctk.CTkFrame(parent, height=30)
        self.status_frame.pack(side="bottom", fill="x", pady=(10, 0))
        self.status_frame.pack_propagate(False)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # System info
        info_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        info_frame.pack(side="right", padx=10, pady=5)
        
        # User info
        user_text = f"User: {self.current_user.username if self.current_user else 'Guest'}"
        user_label = ctk.CTkLabel(info_frame, text=user_text, font=ctk.CTkFont(size=12))
        user_label.pack(side="right", padx=(10, 0))
        
        # Time
        time_label = ctk.CTkLabel(
            info_frame,
            text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=12)
        )
        time_label.pack(side="right", padx=(10, 0))
        
        # Update time periodically
        self._update_time(time_label)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Global shortcuts
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        self.root.bind("<Control-s>", lambda e: self._open_settings())
        self.root.bind("<Control-1>", lambda e: self._open_tool("ai_chat"))
        self.root.bind("<Control-2>", lambda e: self._open_tool("voice_assistant"))
        self.root.bind("<Control-3>", lambda e: self._open_tool("document_processor"))
        self.root.bind("<Control-4>", lambda e: self._open_tool("media_converter"))
        self.root.bind("<Control-5>", lambda e: self._open_tool("system_optimizer"))
        self.root.bind("<Control-6>", lambda e: self._open_tool("automation_builder"))
        self.root.bind("<Control-7>", lambda e: self._open_tool("smart_organizer"))
        
        # Voice activation
        self.root.bind("<F1>", lambda e: self._toggle_voice())
    
    def _show_welcome_screen(self):
        """Show welcome screen."""
        if self.navigation_manager:
            self.navigation_manager.navigate_to(ViewType.DASHBOARD)
    
    def _open_tool(self, tool_id: str):
        """Open a specific tool."""
        try:
            if tool_id in self.tools:
                # Track tool usage
                if self.analytics_system:
                    self.analytics_system.track_tool_usage(tool_id, "open")
                
                # Navigate to tool
                if self.navigation_manager:
                    self.navigation_manager.navigate_to_tool(tool_id)
                
                # Update status
                self._update_status(f"Opened {tool_id.replace('_', ' ').title()}")
                
                # Show notification
                if self.notification_system:
                    self.notification_system.show_info(
                        f"Opened {tool_id.replace('_', ' ').title()}",
                        f"The {tool_id.replace('_', ' ')} tool is now active."
                    )
            else:
                logging.warning(f"Tool not found: {tool_id}")
                
        except Exception as e:
            logging.error(f"Failed to open tool {tool_id}: {e}")
            if self.notification_system:
                self.notification_system.show_error(
                    "Tool Error",
                    f"Failed to open {tool_id.replace('_', ' ')}: {str(e)}"
                )
    
    def _open_settings(self):
        """Open settings dialog."""
        if self.navigation_manager:
            self.navigation_manager.navigate_to(ViewType.SETTINGS)
    
    def _open_profile(self):
        """Open user profile."""
        if self.dialog_manager:
            # Show profile dialog
            result = self.dialog_manager.show_input_dialog(
                "User Profile",
                "Enter your profile information:",
                fields=[
                    ("Username", self.current_user.username if self.current_user else ""),
                    ("Email", self.current_user.email if self.current_user else ""),
                    ("Display Name", "")
                ]
            )
            
            if result.confirmed and result.data:
                # Update profile
                self._update_status("Profile updated")
    
    def _toggle_voice(self):
        """Toggle voice assistant."""
        if self.voice_system:
            if self.voice_system.is_listening():
                self.voice_system.stop_listening()
                self._update_status("Voice assistant stopped")
            else:
                self.voice_system.start_listening()
                self._update_status("Voice assistant started")
    
    def _update_status(self, message: str):
        """Update status bar message."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            # Reset to "Ready" after 3 seconds
            self.root.after(3000, lambda: self.status_label.configure(text="Ready"))
    
    def _update_time(self, time_label):
        """Update time display."""
        current_time = datetime.now().strftime("%H:%M")
        time_label.configure(text=current_time)
        # Update every minute
        self.root.after(60000, lambda: self._update_time(time_label))
    
    def _add_tooltip(self, widget, text):
        """Add tooltip to widget."""
        def on_enter(event):
            # Create tooltip (simplified implementation)
            pass
        
        def on_leave(event):
            # Hide tooltip
            pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def start_session(self, username: str = None):
        """Start user session."""
        try:
            # Start analytics session
            if self.analytics_system:
                session_id = self.analytics_system.start_session(username)
                logging.info(f"Analytics session started: {session_id}")
            
            # Set current user (simplified - in real app, this would come from authentication)
            if username and self.security_system:
                user = self.security_system.database.get_user(username=username)
                if user:
                    self.current_user = user
            
            # Track session start
            if self.analytics_system:
                self.analytics_system.track_event(
                    self.analytics_system.EventType.SESSION_START,
                    "application_started",
                    {'username': username}
                )
            
            logging.info(f"Session started for user: {username or 'Guest'}")
            
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
    
    def run(self):
        """Run the application."""
        try:
            logging.info("Starting Easy Genie Desktop Phase 2...")
            
            # Initialize all systems
            self.initialize_systems()
            self.initialize_ui_systems()
            
            # Create main window
            self.create_main_window()
            
            # Initialize tools
            self.initialize_tools()
            
            # Setup interface
            self.setup_main_interface()
            
            # Start session
            self.start_session("demo_user")  # Demo user for Phase 2
            
            # Show startup notification
            if self.notification_system:
                self.notification_system.show_success(
                    "Welcome to Easy Genie Desktop Phase 2!",
                    "All systems are ready. Enjoy the enhanced experience!"
                )
            
            # Set running flag
            self.running = True
            
            logging.info("Application started successfully")
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logging.error(f"Application startup failed: {e}")
            messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")
            sys.exit(1)
    
    def on_closing(self):
        """Handle application closing."""
        try:
            logging.info("Shutting down Easy Genie Desktop Phase 2...")
            
            # Show confirmation dialog
            if self.dialog_manager:
                result = self.dialog_manager.show_confirmation_dialog(
                    "Exit Application",
                    "Are you sure you want to exit Easy Genie Desktop?"
                )
                if not result.confirmed:
                    return
            
            # Track session end
            if self.analytics_system:
                self.analytics_system.track_event(
                    self.analytics_system.EventType.SESSION_END,
                    "application_closed"
                )
            
            # Stop all systems
            self._shutdown_systems()
            
            # Set running flag
            self.running = False
            
            # Destroy window
            if self.root:
                self.root.destroy()
            
            logging.info("Application shutdown completed")
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            # Force exit if there's an error
            if self.root:
                self.root.destroy()
    
    def _shutdown_systems(self):
        """Shutdown all systems gracefully."""
        try:
            # Stop voice system
            if self.voice_system:
                self.voice_system.stop()
                logging.info("Voice system stopped")
            
            # Stop audio system
            if self.audio_system:
                self.audio_system.stop()
                logging.info("Audio system stopped")
            
            # Stop analytics system
            if self.analytics_system:
                self.analytics_system.stop()
                logging.info("Analytics system stopped")
            
            # Stop notification system
            if self.notification_system:
                self.notification_system.stop()
                logging.info("Notification system stopped")
            
            # Close database connections
            if self.database_system:
                self.database_system.close()
                logging.info("Database system closed")
            
            if self.security_system:
                self.security_system.close()
                logging.info("Security system closed")
            
        except Exception as e:
            logging.error(f"Error shutting down systems: {e}")


def main():
    """Main entry point."""
    try:
        # Create and run application
        app = EasyGeniePhase2()
        app.run()
        
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()