# Easy Genie Desktop - Phase 2

🚀 **Advanced AI-Powered Desktop Assistant with Enhanced UI and Voice Control**

## 🌟 What's New in Phase 2

Phase 2 introduces a complete overhaul of Easy Genie Desktop with advanced AI capabilities, sophisticated UI systems, and comprehensive backend infrastructure:

### 🤖 Advanced AI Service
- **Multi-Provider Support**: OpenAI, Anthropic, Hugging Face, and local models
- **Intelligent Routing**: Automatic provider selection based on task requirements
- **Learning System**: Adaptive AI that learns from user interactions
- **Context Management**: Advanced conversation memory and context switching
- **Performance Optimization**: Caching, load balancing, and response optimization

### 🎨 Enhanced UI System
- **Theme Manager**: Dark/Light/System themes with custom theme support
- **Dialog Manager**: Advanced modal dialogs with priority queuing
- **Widget Factory**: Consistent, themed UI components across the application
- **Navigation Manager**: Sophisticated view management with history and modals
- **Responsive Design**: Adaptive layouts for different screen sizes

### 🎙️ Voice Command System
- **Multi-Engine Support**: Google Speech Recognition, Azure Speech, local engines
- **Wake Word Detection**: "Hey Genie" activation
- **Natural Language Processing**: Advanced command interpretation
- **Text-to-Speech**: Multiple TTS engines with voice customization
- **Hands-Free Operation**: Complete voice control of all features

### 🔊 Audio System
- **High-Quality Playback**: Support for multiple audio formats
- **Professional Recording**: Multi-channel recording with real-time processing
- **Audio Effects**: Built-in audio processing and enhancement
- **Device Management**: Automatic audio device detection and switching

### 📊 Export System
- **Multiple Formats**: PDF, Excel, CSV, JSON, XML, and more
- **Template Engine**: Customizable export templates
- **Batch Processing**: Export multiple files simultaneously
- **Quality Control**: Configurable export quality and compression

### 🗄️ Database System
- **SQLite Integration**: Robust data persistence with migrations
- **Model System**: Object-relational mapping for easy data management
- **Transaction Support**: ACID compliance with rollback capabilities
- **Backup & Recovery**: Automated backup and restore functionality

### 🔔 Notification System
- **Multi-Channel Delivery**: Toast, system tray, in-app, email notifications
- **Priority Management**: Urgent, high, normal, low priority levels
- **Scheduling**: Delayed and recurring notifications
- **Action Support**: Interactive notifications with custom actions

### 📈 Analytics System
- **Usage Tracking**: Comprehensive user behavior analytics
- **Performance Monitoring**: Real-time system performance metrics
- **Custom Events**: Track application-specific events
- **Reporting**: Detailed analytics reports and insights

### 🔒 Security System
- **User Authentication**: Secure login with multiple authentication methods
- **Role-Based Access**: Granular permissions for different user roles
- **Data Encryption**: End-to-end encryption for sensitive data
- **Security Monitoring**: Intrusion detection and security event logging

## 🛠️ Installation

### Prerequisites

1. **Python 3.9 or higher**
2. **Windows 10/11** (primary platform)
3. **Visual C++ Build Tools** (for some dependencies)
4. **FFmpeg** (for media processing)
5. **PortAudio** (for audio processing)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/easy-genie-desktop.git
cd easy-genie-desktop

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install Phase 2 dependencies
pip install -r requirements_phase2.txt

# Run Phase 2
python main_phase2.py
```

### Detailed Installation

#### 1. System Dependencies

**FFmpeg** (for media processing):
```bash
# Download from https://ffmpeg.org/download.html
# Add to system PATH
```

**PortAudio** (for audio processing):
```bash
# Usually installed automatically with PyAudio
# If issues occur, download from http://www.portaudio.com/
```

#### 2. Python Dependencies

```bash
# Core dependencies
pip install customtkinter>=5.2.0
pip install openai>=1.3.0
pip install speech-recognition>=3.10.0
pip install pyttsx3>=2.90

# Or install all at once
pip install -r requirements_phase2.txt
```

#### 3. Configuration

Create a `.env` file in the project root:

```env
# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Voice Service Configuration
GOOGLE_CLOUD_CREDENTIALS=path/to/credentials.json
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security Configuration
SECRET_KEY=your_secret_key_for_jwt
ENCRYPTION_KEY=your_encryption_key
```

## 🚀 Usage

### Starting the Application

```bash
# Activate virtual environment
venv\Scripts\activate

# Run Phase 2
python main_phase2.py
```

### First-Time Setup

1. **Create User Account**: Set up your user profile and preferences
2. **Configure AI Services**: Add your API keys for AI providers
3. **Setup Voice**: Configure microphone and speaker settings
4. **Choose Theme**: Select your preferred UI theme
5. **Test Features**: Try each tool to ensure everything works

### Voice Commands

Activate voice control with "Hey Genie" or press F1:

```
"Hey Genie, open AI chat"
"Hey Genie, start voice assistant"
"Hey Genie, process document"
"Hey Genie, convert media"
"Hey Genie, optimize system"
"Hey Genie, build automation"
"Hey Genie, organize files"
"Hey Genie, show settings"
"Hey Genie, switch to dark theme"
```

### Keyboard Shortcuts

- `Ctrl+1-7`: Open tools 1-7
- `Ctrl+S`: Open settings
- `Ctrl+Q`: Quit application
- `F1`: Toggle voice assistant
- `Ctrl+Shift+T`: Switch theme
- `Ctrl+Shift+N`: New session

## 🔧 Tools Overview

### 🤖 AI Chat Tool
- Multi-provider AI conversations
- Context-aware responses
- Conversation history
- Export chat logs
- Custom AI personalities

### 🎙️ Voice Assistant Tool
- Natural voice interaction
- Voice-to-text transcription
- Text-to-speech responses
- Voice command execution
- Audio recording and playback

### 📄 Document Processor Tool
- AI-powered document analysis
- Text extraction and processing
- Document summarization
- Format conversion
- Batch processing

### 🎵 Media Converter Tool
- Audio/video format conversion
- Quality optimization
- Batch conversion
- Metadata editing
- Preview functionality

### ⚡ System Optimizer Tool
- Performance monitoring
- System cleanup
- Resource optimization
- Startup management
- Health diagnostics

### 🔧 Automation Builder Tool
- Visual automation designer
- Custom workflow creation
- Trigger and action setup
- Schedule management
- Automation library

### 📁 Smart Organizer Tool
- AI-powered file organization
- Duplicate detection
- Smart categorization
- Bulk operations
- Organization rules

## 🎨 Customization

### Themes

Create custom themes in the `themes/` directory:

```json
{
  "name": "Custom Theme",
  "mode": "dark",
  "colors": {
    "primary": "#007ACC",
    "secondary": "#1E1E1E",
    "background": "#252526",
    "surface": "#2D2D30",
    "text": "#CCCCCC"
  },
  "fonts": {
    "default": "Segoe UI",
    "monospace": "Consolas"
  }
}
```

### Voice Commands

Add custom voice commands in `core/voice/custom_commands.py`:

```python
from core.voice.voice_command_system import VoiceCommand, CommandType

custom_commands = [
    VoiceCommand(
        patterns=["open my project", "show project"],
        command_type=CommandType.CUSTOM,
        action="open_project",
        description="Open the current project"
    )
]
```

### UI Components

Create custom widgets using the Widget Factory:

```python
from ui.components.widget_factory import WidgetFactory, WidgetConfig

factory = WidgetFactory(WidgetConfig())
custom_button = factory.create_button(
    parent=parent_frame,
    text="Custom Button",
    command=my_function,
    style="primary"
)
```

## 📊 Analytics and Monitoring

### Usage Analytics

View detailed usage statistics:
- Tool usage frequency
- Session duration
- Feature adoption
- Performance metrics
- Error rates

### Performance Monitoring

Monitor system performance:
- CPU and memory usage
- Response times
- Database performance
- Network activity
- Error tracking

### Security Monitoring

Track security events:
- Login attempts
- Permission changes
- Data access
- Suspicious activity
- Security alerts

## 🔒 Security Features

### Data Protection
- End-to-end encryption
- Secure key management
- Data anonymization
- Secure storage
- Privacy controls

### Access Control
- User authentication
- Role-based permissions
- Session management
- API key security
- Audit logging

### Security Best Practices
- Regular security updates
- Vulnerability scanning
- Secure coding practices
- Data backup encryption
- Incident response

## 🐛 Troubleshooting

### Common Issues

**Voice recognition not working:**
```bash
# Check microphone permissions
# Install latest PyAudio
pip install --upgrade pyaudio

# Test microphone
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

**AI services not responding:**
```bash
# Check API keys in .env file
# Verify internet connection
# Check service status
```

**Database errors:**
```bash
# Reset database
python -c "from core.database.database_system import reset_database; reset_database()"
```

**Performance issues:**
```bash
# Clear cache
python -c "from core.cache import clear_all_cache; clear_all_cache()"

# Check system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%')"
```

### Log Files

Check log files for detailed error information:
- `logs/easy_genie_YYYYMMDD.log` - Application logs
- `logs/security_YYYYMMDD.log` - Security events
- `logs/analytics_YYYYMMDD.log` - Analytics data
- `logs/voice_YYYYMMDD.log` - Voice system logs

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/easy-genie-desktop.git
cd easy-genie-desktop

# Create development environment
python -m venv dev_env
dev_env\Scripts\activate

# Install development dependencies
pip install -r requirements_phase2.txt
pip install -r requirements_dev.txt

# Install pre-commit hooks
pre-commit install
```

### Code Style

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Run tests
pytest
```

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Submit pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CustomTkinter** - Modern UI framework
- **OpenAI** - Advanced AI capabilities
- **SpeechRecognition** - Voice input processing
- **PyTTSx3** - Text-to-speech functionality
- **SQLite** - Reliable data storage
- **All contributors** - Community support

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/easy-genie-desktop/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/easy-genie-desktop/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/easy-genie-desktop/discussions)
- **Email**: support@easygenie.com

---

**Easy Genie Desktop Phase 2** - Empowering productivity with advanced AI and intuitive design! 🚀