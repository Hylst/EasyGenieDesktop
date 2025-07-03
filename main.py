#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Main Entry Point

A desktop suite of tools designed to assist individuals, particularly those who are
neurodivergent (ADHD, dyslexia, etc.) and anyone struggling with procrastination
or mental overload.

Author: Easy Genie Team
Version: 1.0.0 (Phase 1 - MVP)
Python: 3.9+
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import customtkinter as ctk
except ImportError:
    print("Error: CustomTkinter not found. Please install requirements:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Import application modules
try:
    from ui.main_window import MainWindow
    from core.database import DatabaseManager
    from config.settings import AppSettings
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Please ensure all required files are present.")
    sys.exit(1)


def setup_logging():
    """Configure logging for the application."""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "easy_genie.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pygame").setLevel(logging.WARNING)


def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        'customtkinter',
        'sqlite3',
        'requests',
        'pyttsx3',
        'speech_recognition',
        'pygame',
        'reportlab',
        'docx',
        'PIL',
        'numpy'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            if module == 'docx':
                __import__('docx')
            elif module == 'PIL':
                __import__('PIL')
            elif module == 'speech_recognition':
                __import__('speech_recognition')
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Easy Genie Desktop...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        if not db_manager.initialize():
            logger.error("Failed to initialize database")
            sys.exit(1)
        
        # Load application settings
        settings = AppSettings()
        settings.load()
        
        # Configure CustomTkinter appearance
        ctk.set_appearance_mode(settings.get('theme', 'light'))
        ctk.set_default_color_theme("blue")
        
        # Create and run main application window
        app = MainWindow(db_manager, settings)
        
        logger.info("Application started successfully")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application shutting down")


if __name__ == "__main__":
    main()