#!/usr/bin/env python3
"""
Easy Genie Desktop - Phase 2 Startup Script

This script provides a user-friendly way to start Phase 2 with:
- Environment validation
- Dependency checking
- Configuration validation
- Error handling and recovery
- First-time setup assistance
"""

import sys
import os
import subprocess
import json
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import importlib.util
from datetime import datetime

# Color codes for console output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(message: str, color: str = Colors.WHITE, bold: bool = False):
    """Print colored message to console."""
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{message}{Colors.END}")

def print_header():
    """Print application header."""
    print_colored("\n" + "="*60, Colors.CYAN, bold=True)
    print_colored("🚀 Easy Genie Desktop - Phase 2 Startup", Colors.CYAN, bold=True)
    print_colored("   Advanced AI-Powered Desktop Assistant", Colors.BLUE)
    print_colored("="*60 + "\n", Colors.CYAN, bold=True)

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    print_colored("🐍 Checking Python version...", Colors.BLUE)
    
    version = sys.version_info
    required_major, required_minor = 3, 9
    
    if version.major < required_major or (version.major == required_major and version.minor < required_minor):
        print_colored(f"❌ Python {required_major}.{required_minor}+ required, found {version.major}.{version.minor}", Colors.RED)
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible", Colors.GREEN)
    return True

def check_virtual_environment() -> bool:
    """Check if running in virtual environment."""
    print_colored("🔧 Checking virtual environment...", Colors.BLUE)
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print_colored("⚠️  Not running in virtual environment", Colors.YELLOW)
        print_colored("   Recommendation: Use virtual environment for better isolation", Colors.YELLOW)
        return True  # Not critical, just a warning
    
    print_colored("✅ Running in virtual environment", Colors.GREEN)
    return True

def check_required_packages() -> Tuple[bool, List[str]]:
    """Check if required packages are installed."""
    print_colored("📦 Checking required packages...", Colors.BLUE)
    
    required_packages = [
        'customtkinter',
        'openai',
        'speech_recognition',
        'pyttsx3',
        'requests',
        'pyyaml',
        'cryptography',
        'psutil',
        'plyer'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_colored(f"  ✅ {package}", Colors.GREEN)
        except ImportError:
            print_colored(f"  ❌ {package} - Missing", Colors.RED)
            missing_packages.append(package)
    
    if missing_packages:
        print_colored(f"\n❌ Missing {len(missing_packages)} required packages", Colors.RED)
        return False, missing_packages
    
    print_colored("✅ All required packages installed", Colors.GREEN)
    return True, []

def install_missing_packages(packages: List[str]) -> bool:
    """Install missing packages."""
    print_colored(f"\n🔧 Installing missing packages: {', '.join(packages)}", Colors.BLUE)
    
    try:
        # Try to install from requirements_phase2.txt first
        requirements_file = Path("requirements_phase2.txt")
        if requirements_file.exists():
            print_colored("📋 Installing from requirements_phase2.txt...", Colors.BLUE)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print_colored("✅ Packages installed successfully", Colors.GREEN)
                return True
            else:
                print_colored(f"❌ Installation failed: {result.stderr}", Colors.RED)
        
        # Fallback: install individual packages
        print_colored("📦 Installing individual packages...", Colors.BLUE)
        for package in packages:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print_colored(f"  ✅ {package} installed", Colors.GREEN)
            else:
                print_colored(f"  ❌ {package} failed: {result.stderr}", Colors.RED)
                return False
        
        return True
        
    except Exception as e:
        print_colored(f"❌ Installation error: {str(e)}", Colors.RED)
        return False

def check_system_dependencies() -> bool:
    """Check system-level dependencies."""
    print_colored("🖥️  Checking system dependencies...", Colors.BLUE)
    
    # Check for FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("  ✅ FFmpeg - Available", Colors.GREEN)
        else:
            print_colored("  ⚠️  FFmpeg - Not found (media conversion may not work)", Colors.YELLOW)
    except FileNotFoundError:
        print_colored("  ⚠️  FFmpeg - Not found (media conversion may not work)", Colors.YELLOW)
    
    # Check for audio devices
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        p.terminate()
        
        if device_count > 0:
            print_colored(f"  ✅ Audio devices - {device_count} found", Colors.GREEN)
        else:
            print_colored("  ⚠️  Audio devices - None found", Colors.YELLOW)
    except Exception:
        print_colored("  ⚠️  Audio system - Cannot check (voice features may not work)", Colors.YELLOW)
    
    return True

def check_configuration() -> bool:
    """Check configuration files."""
    print_colored("⚙️  Checking configuration...", Colors.BLUE)
    
    config_file = Path("config_phase2.yaml")
    
    if not config_file.exists():
        print_colored("  ⚠️  config_phase2.yaml not found, using defaults", Colors.YELLOW)
        return True
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Basic validation
        required_sections = ['app', 'ui', 'ai', 'voice', 'audio']
        for section in required_sections:
            if section not in config:
                print_colored(f"  ❌ Missing configuration section: {section}", Colors.RED)
                return False
        
        print_colored("  ✅ Configuration file valid", Colors.GREEN)
        return True
        
    except yaml.YAMLError as e:
        print_colored(f"  ❌ Configuration file invalid: {str(e)}", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"  ❌ Configuration error: {str(e)}", Colors.RED)
        return False

def check_environment_variables() -> bool:
    """Check environment variables."""
    print_colored("🔑 Checking environment variables...", Colors.BLUE)
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print_colored("  ⚠️  .env file not found", Colors.YELLOW)
        print_colored("     AI services may not work without API keys", Colors.YELLOW)
        return True
    
    # Check for common API keys
    api_keys = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'HUGGINGFACE_API_KEY'
    ]
    
    found_keys = 0
    for key in api_keys:
        if os.getenv(key):
            print_colored(f"  ✅ {key} - Set", Colors.GREEN)
            found_keys += 1
        else:
            print_colored(f"  ⚠️  {key} - Not set", Colors.YELLOW)
    
    if found_keys == 0:
        print_colored("  ⚠️  No AI API keys found - AI features will be limited", Colors.YELLOW)
    
    return True

def create_directories() -> bool:
    """Create necessary directories."""
    print_colored("📁 Creating directories...", Colors.BLUE)
    
    directories = [
        'data',
        'logs',
        'exports',
        'temp',
        'themes',
        'templates'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print_colored(f"  ✅ Created {directory}/", Colors.GREEN)
            except Exception as e:
                print_colored(f"  ❌ Failed to create {directory}/: {str(e)}", Colors.RED)
                return False
        else:
            print_colored(f"  ✅ {directory}/ exists", Colors.GREEN)
    
    return True

def run_diagnostics() -> bool:
    """Run comprehensive diagnostics."""
    print_colored("\n🔍 Running diagnostics...", Colors.BLUE, bold=True)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("System Dependencies", check_system_dependencies),
        ("Configuration", check_configuration),
        ("Environment Variables", check_environment_variables),
        ("Directories", create_directories)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print_colored(f"❌ {check_name} check failed: {str(e)}", Colors.RED)
            all_passed = False
    
    # Check packages last (might need installation)
    packages_ok, missing_packages = check_required_packages()
    
    if not packages_ok:
        print_colored("\n🔧 Attempting to install missing packages...", Colors.BLUE)
        if install_missing_packages(missing_packages):
            print_colored("✅ Package installation completed", Colors.GREEN)
        else:
            print_colored("❌ Package installation failed", Colors.RED)
            all_passed = False
    
    return all_passed

def show_startup_menu() -> str:
    """Show startup menu and get user choice."""
    print_colored("\n🚀 Startup Options:", Colors.CYAN, bold=True)
    print_colored("1. Start Easy Genie Desktop Phase 2", Colors.WHITE)
    print_colored("2. Run diagnostics only", Colors.WHITE)
    print_colored("3. Install/update dependencies", Colors.WHITE)
    print_colored("4. Create sample configuration", Colors.WHITE)
    print_colored("5. Exit", Colors.WHITE)
    
    while True:
        choice = input(f"\n{Colors.CYAN}Enter your choice (1-5): {Colors.END}").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print_colored("Invalid choice. Please enter 1-5.", Colors.RED)

def create_sample_config() -> bool:
    """Create sample configuration files."""
    print_colored("📝 Creating sample configuration...", Colors.BLUE)
    
    # Create sample .env file
    env_content = '''# Easy Genie Desktop - Phase 2 Environment Variables
# Copy this file to .env and fill in your actual API keys

# AI Service API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Voice Service Configuration
GOOGLE_CLOUD_CREDENTIALS=path/to/google_credentials.json
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security Configuration
SECRET_KEY=your_secret_key_for_jwt_tokens
ENCRYPTION_KEY=your_encryption_key_32_chars
'''
    
    try:
        env_file = Path(".env.example")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_colored("  ✅ Created .env.example", Colors.GREEN)
        print_colored("     Copy to .env and add your API keys", Colors.YELLOW)
        
        return True
        
    except Exception as e:
        print_colored(f"  ❌ Failed to create sample config: {str(e)}", Colors.RED)
        return False

def start_application() -> bool:
    """Start the main application."""
    print_colored("\n🚀 Starting Easy Genie Desktop Phase 2...", Colors.CYAN, bold=True)
    
    try:
        # Import and run the main application
        from main_phase2 import main
        main()
        return True
        
    except ImportError as e:
        print_colored(f"❌ Import error: {str(e)}", Colors.RED)
        print_colored("   Make sure all dependencies are installed", Colors.YELLOW)
        return False
    except Exception as e:
        print_colored(f"❌ Application error: {str(e)}", Colors.RED)
        return False

def main():
    """Main startup function."""
    try:
        print_header()
        
        # Show menu
        choice = show_startup_menu()
        
        if choice == '1':
            # Start application
            print_colored("\n🔍 Running pre-flight checks...", Colors.BLUE)
            if run_diagnostics():
                print_colored("\n✅ All checks passed!", Colors.GREEN, bold=True)
                start_application()
            else:
                print_colored("\n❌ Some checks failed. Please resolve issues before starting.", Colors.RED)
                return 1
        
        elif choice == '2':
            # Run diagnostics only
            if run_diagnostics():
                print_colored("\n✅ All diagnostics passed!", Colors.GREEN, bold=True)
            else:
                print_colored("\n⚠️  Some diagnostics failed. See details above.", Colors.YELLOW)
        
        elif choice == '3':
            # Install/update dependencies
            print_colored("\n📦 Installing/updating dependencies...", Colors.BLUE)
            requirements_file = Path("requirements_phase2.txt")
            if requirements_file.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--upgrade"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print_colored("✅ Dependencies updated successfully", Colors.GREEN)
                else:
                    print_colored(f"❌ Update failed: {result.stderr}", Colors.RED)
            else:
                print_colored("❌ requirements_phase2.txt not found", Colors.RED)
        
        elif choice == '4':
            # Create sample configuration
            create_sample_config()
        
        elif choice == '5':
            # Exit
            print_colored("\n👋 Goodbye!", Colors.CYAN)
            return 0
        
        return 0
        
    except KeyboardInterrupt:
        print_colored("\n\n👋 Startup cancelled by user", Colors.YELLOW)
        return 0
    except Exception as e:
        print_colored(f"\n❌ Startup error: {str(e)}", Colors.RED)
        return 1

if __name__ == "__main__":
    sys.exit(main())