"""Voice Command System for Hands-Free Interaction.

This module provides voice recognition, command processing, and text-to-speech
capabilities for hands-free interaction with the application.
"""

import threading
import queue
import time
import json
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import re

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pyaudio
except ImportError:
    pyaudio = None


class VoiceCommandState(Enum):
    """Voice command system states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    DISABLED = "disabled"


class CommandType(Enum):
    """Types of voice commands."""
    NAVIGATION = "navigation"  # Navigate to tools/views
    ACTION = "action"  # Perform actions
    QUERY = "query"  # Ask questions
    CONTROL = "control"  # Control application
    DICTATION = "dictation"  # Text input
    SYSTEM = "system"  # System commands


class RecognitionEngine(Enum):
    """Speech recognition engines."""
    GOOGLE = "google"
    SPHINX = "sphinx"
    WHISPER = "whisper"
    AZURE = "azure"
    IBM = "ibm"


class TTSEngine(Enum):
    """Text-to-speech engines."""
    PYTTSX3 = "pyttsx3"
    AZURE = "azure"
    GOOGLE = "google"
    AMAZON = "amazon"


@dataclass
class VoiceCommand:
    """Voice command definition."""
    id: str
    patterns: List[str]  # Regex patterns to match
    command_type: CommandType
    action: str  # Action to perform
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Command properties
    enabled: bool = True
    confidence_threshold: float = 0.7
    requires_confirmation: bool = False
    
    # Response
    response_template: str = ""
    success_message: str = ""
    error_message: str = ""
    
    # Metadata
    description: str = ""
    examples: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)


@dataclass
class VoiceRecognitionResult:
    """Voice recognition result."""
    text: str
    confidence: float
    engine: RecognitionEngine
    timestamp: datetime
    
    # Audio properties
    duration: float = 0.0
    sample_rate: int = 16000
    
    # Processing info
    processing_time: float = 0.0
    alternatives: List[Tuple[str, float]] = field(default_factory=list)


@dataclass
class CommandMatch:
    """Command match result."""
    command: VoiceCommand
    confidence: float
    matched_text: str
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    
    # Match details
    pattern_used: str = ""
    match_groups: List[str] = field(default_factory=list)


@dataclass
class VoiceSettings:
    """Voice system settings."""
    # Recognition settings
    recognition_engine: RecognitionEngine = RecognitionEngine.GOOGLE
    language: str = "en-US"
    timeout: float = 5.0
    phrase_timeout: float = 1.0
    
    # Audio settings
    microphone_index: Optional[int] = None
    energy_threshold: int = 300
    dynamic_energy_threshold: bool = True
    
    # TTS settings
    tts_engine: TTSEngine = TTSEngine.PYTTSX3
    tts_rate: int = 200
    tts_volume: float = 0.9
    tts_voice: Optional[str] = None
    
    # Command processing
    confidence_threshold: float = 0.7
    max_alternatives: int = 3
    enable_continuous_listening: bool = False
    
    # Wake word
    wake_word: str = "hey genie"
    wake_word_enabled: bool = True
    wake_word_timeout: float = 30.0
    
    # Feedback
    audio_feedback: bool = True
    visual_feedback: bool = True
    confirmation_required: bool = False


class VoiceCommandProcessor:
    """Processes voice commands and extracts parameters."""
    
    def __init__(self):
        """Initialize command processor."""
        self.commands: Dict[str, VoiceCommand] = {}
        self.command_patterns: List[Tuple[re.Pattern, VoiceCommand]] = []
        
        # Initialize default commands
        self._initialize_default_commands()
    
    def _initialize_default_commands(self):
        """Initialize default voice commands."""
        # Navigation commands
        navigation_commands = [
            VoiceCommand(
                id="nav_dashboard",
                patterns=[r"(?:go to|open|show) (?:dashboard|home|main)", r"take me home"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "dashboard"},
                response_template="Going to dashboard",
                description="Navigate to main dashboard",
                examples=["Go to dashboard", "Take me home", "Show main"]
            ),
            VoiceCommand(
                id="nav_task_breaker",
                patterns=[r"(?:go to|open|show) task breaker", r"break (?:down )?tasks?"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "task_breaker"},
                response_template="Opening Task Breaker",
                description="Navigate to Task Breaker tool",
                examples=["Go to task breaker", "Break down tasks", "Open task breaker"]
            ),
            VoiceCommand(
                id="nav_time_focus",
                patterns=[r"(?:go to|open|show) (?:time focus|timer|pomodoro)", r"start (?:focus|timer)"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "time_focus"},
                response_template="Opening TimeFocus",
                description="Navigate to TimeFocus tool",
                examples=["Go to time focus", "Open timer", "Start focus"]
            ),
            VoiceCommand(
                id="nav_priority_grid",
                patterns=[r"(?:go to|open|show) priority grid", r"prioritize tasks?"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "priority_grid"},
                response_template="Opening Priority Grid",
                description="Navigate to Priority Grid tool",
                examples=["Go to priority grid", "Prioritize tasks", "Open priority grid"]
            ),
            VoiceCommand(
                id="nav_brain_dump",
                patterns=[r"(?:go to|open|show) brain dump", r"(?:quick )?notes?"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "brain_dump"},
                response_template="Opening Brain Dump",
                description="Navigate to Brain Dump tool",
                examples=["Go to brain dump", "Quick notes", "Open brain dump"]
            ),
            VoiceCommand(
                id="nav_formalizer",
                patterns=[r"(?:go to|open|show) formalizer", r"formalize text"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "formalizer"},
                response_template="Opening Formalizer",
                description="Navigate to Formalizer tool",
                examples=["Go to formalizer", "Formalize text", "Open formalizer"]
            ),
            VoiceCommand(
                id="nav_routine_builder",
                patterns=[r"(?:go to|open|show) routine builder", r"build routines?"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "routine_builder"},
                response_template="Opening Routine Builder",
                description="Navigate to Routine Builder tool",
                examples=["Go to routine builder", "Build routines", "Open routine builder"]
            ),
            VoiceCommand(
                id="nav_immersive_reader",
                patterns=[r"(?:go to|open|show) (?:immersive )?reader", r"read (?:mode|text)"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "immersive_reader"},
                response_template="Opening Immersive Reader",
                description="Navigate to Immersive Reader tool",
                examples=["Go to reader", "Read mode", "Open immersive reader"]
            ),
            VoiceCommand(
                id="nav_settings",
                patterns=[r"(?:go to|open|show) settings", r"configure (?:app|application)"],
                command_type=CommandType.NAVIGATION,
                action="navigate",
                parameters={"view_id": "settings"},
                response_template="Opening Settings",
                description="Navigate to Settings",
                examples=["Go to settings", "Configure app", "Open settings"]
            )
        ]
        
        # Control commands
        control_commands = [
            VoiceCommand(
                id="go_back",
                patterns=[r"go back", r"previous (?:page|view)", r"back"],
                command_type=CommandType.CONTROL,
                action="go_back",
                response_template="Going back",
                description="Navigate to previous view",
                examples=["Go back", "Previous page", "Back"]
            ),
            VoiceCommand(
                id="help",
                patterns=[r"help", r"what can (?:you|i) do", r"show commands"],
                command_type=CommandType.QUERY,
                action="show_help",
                response_template="Here are the available commands",
                description="Show available voice commands",
                examples=["Help", "What can you do", "Show commands"]
            ),
            VoiceCommand(
                id="stop_listening",
                patterns=[r"stop listening", r"disable voice", r"quiet"],
                command_type=CommandType.SYSTEM,
                action="stop_listening",
                response_template="Voice commands disabled",
                description="Disable voice recognition",
                examples=["Stop listening", "Disable voice", "Quiet"]
            )
        ]
        
        # Register all commands
        for command in navigation_commands + control_commands:
            self.register_command(command)
    
    def register_command(self, command: VoiceCommand):
        """Register a voice command.
        
        Args:
            command: Voice command to register
        """
        self.commands[command.id] = command
        
        # Compile patterns
        for pattern in command.patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                self.command_patterns.append((compiled_pattern, command))
            except re.error as e:
                print(f"Invalid regex pattern '{pattern}' for command '{command.id}': {e}")
    
    def unregister_command(self, command_id: str):
        """Unregister a voice command.
        
        Args:
            command_id: ID of command to unregister
        """
        if command_id in self.commands:
            command = self.commands[command_id]
            
            # Remove patterns
            self.command_patterns = [
                (pattern, cmd) for pattern, cmd in self.command_patterns
                if cmd.id != command_id
            ]
            
            # Remove command
            del self.commands[command_id]
    
    def process_text(self, text: str) -> List[CommandMatch]:
        """Process text and find matching commands.
        
        Args:
            text: Text to process
            
        Returns:
            List[CommandMatch]: List of command matches
        """
        matches = []
        
        for pattern, command in self.command_patterns:
            if not command.enabled:
                continue
            
            match = pattern.search(text)
            if match:
                # Calculate confidence based on match quality
                confidence = self._calculate_match_confidence(text, match, command)
                
                if confidence >= command.confidence_threshold:
                    # Extract parameters from match groups
                    extracted_params = self._extract_parameters(match, command)
                    
                    command_match = CommandMatch(
                        command=command,
                        confidence=confidence,
                        matched_text=match.group(0),
                        extracted_params=extracted_params,
                        pattern_used=pattern.pattern,
                        match_groups=list(match.groups())
                    )
                    
                    matches.append(command_match)
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches
    
    def _calculate_match_confidence(self, text: str, match: re.Match, command: VoiceCommand) -> float:
        """Calculate match confidence.
        
        Args:
            text: Original text
            match: Regex match
            command: Voice command
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        # Base confidence from match coverage
        match_length = len(match.group(0))
        text_length = len(text.strip())
        coverage = match_length / text_length if text_length > 0 else 0.0
        
        # Bonus for exact matches
        exact_bonus = 0.2 if match.group(0).strip().lower() == text.strip().lower() else 0.0
        
        # Penalty for partial matches
        partial_penalty = 0.1 if coverage < 0.8 else 0.0
        
        confidence = min(1.0, coverage + exact_bonus - partial_penalty)
        
        return confidence
    
    def _extract_parameters(self, match: re.Match, command: VoiceCommand) -> Dict[str, Any]:
        """Extract parameters from regex match.
        
        Args:
            match: Regex match
            command: Voice command
            
        Returns:
            Dict[str, Any]: Extracted parameters
        """
        params = command.parameters.copy()
        
        # Extract named groups
        for name, value in match.groupdict().items():
            if value is not None:
                params[name] = value.strip()
        
        return params
    
    def get_commands_by_type(self, command_type: CommandType) -> List[VoiceCommand]:
        """Get commands by type.
        
        Args:
            command_type: Command type to filter by
            
        Returns:
            List[VoiceCommand]: Filtered commands
        """
        return [cmd for cmd in self.commands.values() if cmd.command_type == command_type]
    
    def get_command_help(self) -> str:
        """Get help text for all commands.
        
        Returns:
            str: Help text
        """
        help_text = "Available voice commands:\n\n"
        
        # Group by command type
        by_type = {}
        for command in self.commands.values():
            if command.enabled:
                if command.command_type not in by_type:
                    by_type[command.command_type] = []
                by_type[command.command_type].append(command)
        
        # Format help text
        for cmd_type, commands in by_type.items():
            help_text += f"{cmd_type.value.title()} Commands:\n"
            for command in commands:
                help_text += f"  • {command.description}\n"
                if command.examples:
                    help_text += f"    Examples: {', '.join(command.examples[:2])}\n"
            help_text += "\n"
        
        return help_text


class VoiceCommandSystem:
    """Main voice command system."""
    
    def __init__(self, settings: VoiceSettings = None):
        """Initialize voice command system.
        
        Args:
            settings: Voice system settings
        """
        self.settings = settings or VoiceSettings()
        self.state = VoiceCommandState.IDLE
        
        # Components
        self.processor = VoiceCommandProcessor()
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        
        # Threading
        self.listening_thread = None
        self.command_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "command_recognized": [],
            "command_executed": [],
            "state_changed": [],
            "error_occurred": [],
            "listening_started": [],
            "listening_stopped": []
        }
        
        # Statistics
        self.stats = {
            "commands_processed": 0,
            "successful_recognitions": 0,
            "failed_recognitions": 0,
            "average_confidence": 0.0,
            "session_start_time": datetime.now()
        }
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize voice recognition and TTS components."""
        try:
            # Initialize speech recognition
            if sr is not None:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = self.settings.energy_threshold
                self.recognizer.dynamic_energy_threshold = self.settings.dynamic_energy_threshold
                
                # Initialize microphone
                if pyaudio is not None:
                    if self.settings.microphone_index is not None:
                        self.microphone = sr.Microphone(device_index=self.settings.microphone_index)
                    else:
                        self.microphone = sr.Microphone()
                    
                    # Calibrate for ambient noise
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source)
            
            # Initialize TTS
            if pyttsx3 is not None and self.settings.tts_engine == TTSEngine.PYTTSX3:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', self.settings.tts_rate)
                self.tts_engine.setProperty('volume', self.settings.tts_volume)
                
                if self.settings.tts_voice:
                    voices = self.tts_engine.getProperty('voices')
                    for voice in voices:
                        if self.settings.tts_voice.lower() in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
            
            self._set_state(VoiceCommandState.IDLE)
            
        except Exception as e:
            print(f"Error initializing voice components: {e}")
            self._set_state(VoiceCommandState.ERROR)
    
    def start_listening(self, continuous: bool = None):
        """Start voice recognition.
        
        Args:
            continuous: Enable continuous listening (overrides settings)
        """
        if self.state == VoiceCommandState.ERROR:
            print("Cannot start listening: Voice system is in error state")
            return
        
        if self.recognizer is None or self.microphone is None:
            print("Cannot start listening: Voice recognition not available")
            return
        
        if self.listening_thread and self.listening_thread.is_alive():
            print("Already listening")
            return
        
        # Update settings
        if continuous is not None:
            self.settings.enable_continuous_listening = continuous
        
        # Start listening thread
        self.stop_event.clear()
        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self.listening_thread.start()
        
        self._emit_event("listening_started", {})
        print("Voice recognition started")
    
    def stop_listening(self):
        """Stop voice recognition."""
        if self.listening_thread and self.listening_thread.is_alive():
            self.stop_event.set()
            self.listening_thread.join(timeout=2.0)
        
        self._set_state(VoiceCommandState.IDLE)
        self._emit_event("listening_stopped", {})
        print("Voice recognition stopped")
    
    def _listening_loop(self):
        """Main listening loop."""
        wake_word_detected = not self.settings.wake_word_enabled
        last_activity = datetime.now()
        
        while not self.stop_event.is_set():
            try:
                self._set_state(VoiceCommandState.LISTENING)
                
                # Listen for audio
                with self.microphone as source:
                    # Adjust timeout based on wake word state
                    timeout = self.settings.timeout if wake_word_detected else 1.0
                    
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=self.settings.phrase_timeout
                    )
                
                # Process audio
                self._set_state(VoiceCommandState.PROCESSING)
                result = self._recognize_speech(audio)
                
                if result:
                    # Check for wake word if needed
                    if not wake_word_detected:
                        if self.settings.wake_word.lower() in result.text.lower():
                            wake_word_detected = True
                            last_activity = datetime.now()
                            self.speak("Yes?")
                            continue
                    else:
                        # Process command
                        self._process_voice_input(result)
                        last_activity = datetime.now()
                        
                        # Reset wake word if not continuous
                        if not self.settings.enable_continuous_listening:
                            wake_word_detected = False
                
                # Check wake word timeout
                if (wake_word_detected and 
                    datetime.now() - last_activity > timedelta(seconds=self.settings.wake_word_timeout)):
                    wake_word_detected = False
                    print("Wake word session timed out")
                
                self._set_state(VoiceCommandState.IDLE)
                
            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                continue
            except sr.UnknownValueError:
                # Could not understand audio
                self.stats["failed_recognitions"] += 1
                continue
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                self._emit_event("error_occurred", {"error": str(e), "type": "recognition"})
                time.sleep(1)  # Brief pause before retrying
            except Exception as e:
                print(f"Unexpected error in listening loop: {e}")
                self._emit_event("error_occurred", {"error": str(e), "type": "unexpected"})
                break
        
        self._set_state(VoiceCommandState.IDLE)
    
    def _recognize_speech(self, audio) -> Optional[VoiceRecognitionResult]:
        """Recognize speech from audio.
        
        Args:
            audio: Audio data
            
        Returns:
            Optional[VoiceRecognitionResult]: Recognition result or None
        """
        start_time = time.time()
        
        try:
            # Use selected recognition engine
            if self.settings.recognition_engine == RecognitionEngine.GOOGLE:
                text = self.recognizer.recognize_google(audio, language=self.settings.language)
                confidence = 0.8  # Google doesn't provide confidence
            elif self.settings.recognition_engine == RecognitionEngine.SPHINX:
                text = self.recognizer.recognize_sphinx(audio)
                confidence = 0.7  # Sphinx doesn't provide confidence
            else:
                # Default to Google
                text = self.recognizer.recognize_google(audio, language=self.settings.language)
                confidence = 0.8
            
            processing_time = time.time() - start_time
            
            result = VoiceRecognitionResult(
                text=text,
                confidence=confidence,
                engine=self.settings.recognition_engine,
                timestamp=datetime.now(),
                processing_time=processing_time
            )
            
            self.stats["successful_recognitions"] += 1
            return result
            
        except sr.UnknownValueError:
            self.stats["failed_recognitions"] += 1
            return None
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            self.stats["failed_recognitions"] += 1
            return None
    
    def _process_voice_input(self, result: VoiceRecognitionResult):
        """Process voice recognition result.
        
        Args:
            result: Voice recognition result
        """
        print(f"Recognized: '{result.text}' (confidence: {result.confidence:.2f})")
        
        # Find matching commands
        matches = self.processor.process_text(result.text)
        
        if matches:
            best_match = matches[0]
            
            # Update statistics
            self.stats["commands_processed"] += 1
            self.stats["average_confidence"] = (
                (self.stats["average_confidence"] * (self.stats["commands_processed"] - 1) + 
                 best_match.confidence) / self.stats["commands_processed"]
            )
            
            # Emit event
            self._emit_event("command_recognized", {
                "result": result,
                "match": best_match,
                "all_matches": matches
            })
            
            # Execute command
            self._execute_command(best_match, result)
        else:
            print(f"No matching commands found for: '{result.text}'")
            self.speak("I didn't understand that command. Say 'help' for available commands.")
    
    def _execute_command(self, match: CommandMatch, result: VoiceRecognitionResult):
        """Execute a matched command.
        
        Args:
            match: Command match
            result: Voice recognition result
        """
        command = match.command
        
        try:
            # Check if confirmation is required
            if command.requires_confirmation:
                confirmation_text = f"Execute {command.description}?"
                if not self._get_confirmation(confirmation_text):
                    self.speak("Command cancelled")
                    return
            
            # Execute based on action type
            success = False
            
            if command.action == "navigate":
                success = self._execute_navigation(match)
            elif command.action == "go_back":
                success = self._execute_go_back(match)
            elif command.action == "show_help":
                success = self._execute_show_help(match)
            elif command.action == "stop_listening":
                success = self._execute_stop_listening(match)
            else:
                # Custom command - emit event for handling
                self._emit_event("command_executed", {
                    "match": match,
                    "result": result,
                    "action": command.action
                })
                success = True
            
            # Provide feedback
            if success:
                if command.success_message:
                    self.speak(command.success_message)
                elif command.response_template:
                    self.speak(command.response_template)
            else:
                if command.error_message:
                    self.speak(command.error_message)
                else:
                    self.speak("Command failed")
            
        except Exception as e:
            print(f"Error executing command: {e}")
            self.speak("An error occurred while executing the command")
            self._emit_event("error_occurred", {
                "error": str(e),
                "type": "command_execution",
                "command": command.id
            })
    
    def _execute_navigation(self, match: CommandMatch) -> bool:
        """Execute navigation command.
        
        Args:
            match: Command match
            
        Returns:
            bool: True if successful
        """
        try:
            from ...ui.components.navigation_manager import get_navigation_manager
            
            nav_manager = get_navigation_manager()
            if nav_manager:
                view_id = match.extracted_params.get("view_id")
                if view_id:
                    return nav_manager.navigate_to(view_id)
            
            return False
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    def _execute_go_back(self, match: CommandMatch) -> bool:
        """Execute go back command.
        
        Args:
            match: Command match
            
        Returns:
            bool: True if successful
        """
        try:
            from ...ui.components.navigation_manager import get_navigation_manager
            
            nav_manager = get_navigation_manager()
            if nav_manager:
                return nav_manager.go_back()
            
            return False
        except Exception as e:
            print(f"Go back error: {e}")
            return False
    
    def _execute_show_help(self, match: CommandMatch) -> bool:
        """Execute show help command.
        
        Args:
            match: Command match
            
        Returns:
            bool: True if successful
        """
        help_text = self.processor.get_command_help()
        print(help_text)
        
        # Speak abbreviated help
        abbreviated_help = "Available commands include: navigation, control, and system commands. Check the console for details."
        self.speak(abbreviated_help)
        
        return True
    
    def _execute_stop_listening(self, match: CommandMatch) -> bool:
        """Execute stop listening command.
        
        Args:
            match: Command match
            
        Returns:
            bool: True if successful
        """
        self.stop_listening()
        return True
    
    def _get_confirmation(self, message: str) -> bool:
        """Get voice confirmation.
        
        Args:
            message: Confirmation message
            
        Returns:
            bool: True if confirmed
        """
        self.speak(f"{message} Say yes or no.")
        
        # Listen for confirmation
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=2.0)
            
            text = self.recognizer.recognize_google(audio, language=self.settings.language)
            text = text.lower().strip()
            
            return text in ["yes", "yeah", "yep", "confirm", "ok", "okay"]
            
        except Exception:
            return False
    
    def speak(self, text: str):
        """Speak text using TTS.
        
        Args:
            text: Text to speak
        """
        if not self.settings.audio_feedback:
            return
        
        if self.tts_engine is None:
            print(f"TTS: {text}")
            return
        
        try:
            self._set_state(VoiceCommandState.SPEAKING)
            
            # Speak in separate thread to avoid blocking
            def speak_thread():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    print(f"TTS error: {e}")
                finally:
                    if self.state == VoiceCommandState.SPEAKING:
                        self._set_state(VoiceCommandState.IDLE)
            
            threading.Thread(target=speak_thread, daemon=True).start()
            
        except Exception as e:
            print(f"Error speaking text: {e}")
            self._set_state(VoiceCommandState.IDLE)
    
    def process_text_command(self, text: str) -> bool:
        """Process text command directly (for testing/debugging).
        
        Args:
            text: Command text
            
        Returns:
            bool: True if command was processed
        """
        result = VoiceRecognitionResult(
            text=text,
            confidence=1.0,
            engine=RecognitionEngine.GOOGLE,
            timestamp=datetime.now()
        )
        
        self._process_voice_input(result)
        return True
    
    def _set_state(self, new_state: VoiceCommandState):
        """Set system state.
        
        Args:
            new_state: New state
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            self._emit_event("state_changed", {
                "old_state": old_state,
                "new_state": new_state
            })
    
    def add_event_handler(self, event: str, handler: Callable):
        """Add event handler.
        
        Args:
            event: Event name
            handler: Event handler function
        """
        if event in self.event_handlers:
            if handler not in self.event_handlers[event]:
                self.event_handlers[event].append(handler)
    
    def remove_event_handler(self, event: str, handler: Callable):
        """Remove event handler.
        
        Args:
            event: Event name
            handler: Event handler function
        """
        if event in self.event_handlers:
            if handler in self.event_handlers[event]:
                self.event_handlers[event].remove(handler)
    
    def _emit_event(self, event: str, data: Any):
        """Emit event to handlers.
        
        Args:
            event: Event name
            data: Event data
        """
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(event, data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        stats = self.stats.copy()
        stats["current_state"] = self.state.value
        stats["uptime"] = (datetime.now() - stats["session_start_time"]).total_seconds()
        stats["recognition_rate"] = (
            stats["successful_recognitions"] / 
            (stats["successful_recognitions"] + stats["failed_recognitions"])
            if (stats["successful_recognitions"] + stats["failed_recognitions"]) > 0 else 0.0
        )
        
        return stats
    
    def is_available(self) -> bool:
        """Check if voice system is available.
        
        Returns:
            bool: True if available
        """
        return (sr is not None and 
                self.recognizer is not None and 
                self.microphone is not None and 
                self.state != VoiceCommandState.ERROR)
    
    def destroy(self):
        """Destroy voice command system."""
        self.stop_listening()
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception:
                pass
        
        self.event_handlers.clear()
        self._set_state(VoiceCommandState.DISABLED)


# Global voice command system instance
_voice_system: Optional[VoiceCommandSystem] = None


def get_voice_system() -> Optional[VoiceCommandSystem]:
    """Get global voice command system instance.
    
    Returns:
        Optional[VoiceCommandSystem]: Global voice system or None
    """
    return _voice_system


def set_voice_system(system: VoiceCommandSystem):
    """Set global voice command system instance.
    
    Args:
        system: Voice system to set
    """
    global _voice_system
    _voice_system = system


# Convenience functions
def start_voice_commands(settings: VoiceSettings = None) -> bool:
    """Start voice command system (convenience function).
    
    Args:
        settings: Voice settings
        
    Returns:
        bool: True if started successfully
    """
    global _voice_system
    
    if _voice_system is None:
        _voice_system = VoiceCommandSystem(settings)
    
    if _voice_system.is_available():
        _voice_system.start_listening()
        return True
    
    return False


def stop_voice_commands():
    """Stop voice command system (convenience function)."""
    if _voice_system:
        _voice_system.stop_listening()


def speak(text: str):
    """Speak text (convenience function).
    
    Args:
        text: Text to speak
    """
    if _voice_system:
        _voice_system.speak(text)