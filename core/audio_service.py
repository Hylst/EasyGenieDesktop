#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Audio Service Manager

Manages text-to-speech, speech recognition, and audio feedback.
"""

import logging
import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from enum import Enum
import json

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pygame
except ImportError:
    pygame = None

try:
    import pyaudio
except ImportError:
    pyaudio = None


class AudioEvent(Enum):
    """Audio event types."""
    TASK_COMPLETED = "task_completed"
    FOCUS_START = "focus_start"
    FOCUS_END = "focus_end"
    BREAK_TIME = "break_time"
    NOTIFICATION = "notification"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"


class TTSEngine(Enum):
    """Text-to-speech engine types."""
    SYSTEM = "system"  # pyttsx3
    NONE = "none"


class AudioServiceManager:
    """Manages audio services for Easy Genie Desktop."""
    
    def __init__(self, settings_manager=None):
        """Initialize audio service manager."""
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        # TTS components
        self.tts_engine = None
        self.tts_enabled = True
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_running = False
        
        # Speech recognition components
        self.sr_recognizer = None
        self.sr_microphone = None
        self.sr_enabled = False
        
        # Audio feedback
        self.audio_enabled = True
        self.sound_effects = {}
        self.volume = 0.7
        
        # Voice settings
        self.voice_settings = {
            'rate': 200,
            'volume': 0.8,
            'voice_id': None,
            'language': 'fr-FR'
        }
        
        # Audio event callbacks
        self.event_callbacks = {}
        
        # Initialize components
        self._initialize_components()
        self._load_settings()
    
    def _initialize_components(self):
        """Initialize audio components."""
        try:
            # Initialize TTS
            if pyttsx3:
                self.tts_engine = pyttsx3.init()
                self._configure_tts()
                self.logger.info("TTS engine initialized")
            else:
                self.logger.warning("pyttsx3 not available - TTS disabled")
                self.tts_enabled = False
            
            # Initialize speech recognition
            if sr and pyaudio:
                self.sr_recognizer = sr.Recognizer()
                try:
                    self.sr_microphone = sr.Microphone()
                    # Adjust for ambient noise
                    with self.sr_microphone as source:
                        self.sr_recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.sr_enabled = True
                    self.logger.info("Speech recognition initialized")
                except Exception as e:
                    self.logger.warning(f"Speech recognition setup failed: {e}")
                    self.sr_enabled = False
            else:
                self.logger.warning("Speech recognition dependencies not available")
                self.sr_enabled = False
            
            # Initialize pygame for sound effects
            if pygame:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self._load_sound_effects()
                self.logger.info("Audio mixer initialized")
            else:
                self.logger.warning("pygame not available - sound effects disabled")
                self.audio_enabled = False
            
            # Start TTS worker thread
            if self.tts_enabled:
                self._start_tts_worker()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio components: {e}")
    
    def _configure_tts(self):
        """Configure TTS engine settings."""
        if not self.tts_engine:
            return
        
        try:
            # Set rate
            self.tts_engine.setProperty('rate', self.voice_settings['rate'])
            
            # Set volume
            self.tts_engine.setProperty('volume', self.voice_settings['volume'])
            
            # Set voice if specified
            if self.voice_settings['voice_id']:
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if voice.id == self.voice_settings['voice_id']:
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.logger.info("TTS engine configured")
            
        except Exception as e:
            self.logger.error(f"Failed to configure TTS: {e}")
    
    def _load_sound_effects(self):
        """Load sound effect files."""
        if not pygame:
            return
        
        # Define default sound effects (simple tones)
        sound_configs = {
            AudioEvent.TASK_COMPLETED: {'frequency': 800, 'duration': 0.3},
            AudioEvent.FOCUS_START: {'frequency': 600, 'duration': 0.5},
            AudioEvent.FOCUS_END: {'frequency': 400, 'duration': 0.5},
            AudioEvent.BREAK_TIME: {'frequency': 500, 'duration': 0.8},
            AudioEvent.NOTIFICATION: {'frequency': 700, 'duration': 0.2},
            AudioEvent.SUCCESS: {'frequency': 900, 'duration': 0.4},
            AudioEvent.WARNING: {'frequency': 300, 'duration': 0.6},
            AudioEvent.ERROR: {'frequency': 200, 'duration': 1.0}
        }
        
        try:
            for event, config in sound_configs.items():
                sound = self._generate_tone(
                    config['frequency'], 
                    config['duration']
                )
                self.sound_effects[event] = sound
            
            self.logger.info("Sound effects loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load sound effects: {e}")
    
    def _generate_tone(self, frequency: int, duration: float) -> pygame.mixer.Sound:
        """Generate a simple tone sound."""
        import numpy as np
        
        sample_rate = 22050
        frames = int(duration * sample_rate)
        
        # Generate sine wave
        wave_array = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
        
        # Apply fade in/out to avoid clicks
        fade_frames = int(0.01 * sample_rate)  # 10ms fade
        wave_array[:fade_frames] *= np.linspace(0, 1, fade_frames)
        wave_array[-fade_frames:] *= np.linspace(1, 0, fade_frames)
        
        # Convert to 16-bit integers
        wave_array = (wave_array * 32767).astype(np.int16)
        
        # Create stereo sound
        stereo_array = np.array([wave_array, wave_array]).T
        
        return pygame.sndarray.make_sound(stereo_array)
    
    def _load_settings(self):
        """Load audio settings from configuration."""
        if not self.settings_manager:
            return
        
        try:
            # Load TTS settings
            self.tts_enabled = self.settings_manager.get('audio.tts_enabled', True)
            self.voice_settings['rate'] = self.settings_manager.get('audio.tts_rate', 200)
            self.voice_settings['volume'] = self.settings_manager.get('audio.tts_volume', 0.8)
            self.voice_settings['voice_id'] = self.settings_manager.get('audio.tts_voice_id', None)
            self.voice_settings['language'] = self.settings_manager.get('audio.tts_language', 'fr-FR')
            
            # Load audio settings
            self.audio_enabled = self.settings_manager.get('audio.effects_enabled', True)
            self.volume = self.settings_manager.get('audio.volume', 0.7)
            
            # Load speech recognition settings
            self.sr_enabled = self.settings_manager.get('audio.speech_recognition_enabled', False)
            
            # Reconfigure TTS if needed
            if self.tts_engine:
                self._configure_tts()
            
            self.logger.info("Audio settings loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load audio settings: {e}")
    
    def _start_tts_worker(self):
        """Start TTS worker thread."""
        if self.tts_thread and self.tts_thread.is_alive():
            return
        
        self.tts_running = True
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        self.logger.info("TTS worker thread started")
    
    def _tts_worker(self):
        """TTS worker thread function."""
        while self.tts_running:
            try:
                # Get text from queue (blocking with timeout)
                text_data = self.tts_queue.get(timeout=1.0)
                
                if text_data is None:  # Shutdown signal
                    break
                
                text = text_data.get('text', '')
                callback = text_data.get('callback')
                
                if text and self.tts_enabled and self.tts_engine:
                    try:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                        
                        if callback:
                            callback(True, None)
                        
                        self.logger.debug(f"TTS completed: {text[:50]}...")
                        
                    except Exception as e:
                        self.logger.error(f"TTS error: {e}")
                        if callback:
                            callback(False, str(e))
                
                self.tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"TTS worker error: {e}")
    
    # Public API methods
    def speak(self, text: str, callback: Optional[Callable] = None, priority: bool = False):
        """Speak text using TTS."""
        if not self.tts_enabled or not text.strip():
            if callback:
                callback(False, "TTS disabled or empty text")
            return
        
        text_data = {
            'text': text.strip(),
            'callback': callback
        }
        
        try:
            if priority:
                # Clear queue and add high priority item
                while not self.tts_queue.empty():
                    try:
                        self.tts_queue.get_nowait()
                        self.tts_queue.task_done()
                    except queue.Empty:
                        break
            
            self.tts_queue.put(text_data)
            self.logger.debug(f"TTS queued: {text[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to queue TTS: {e}")
            if callback:
                callback(False, str(e))
    
    def stop_speaking(self):
        """Stop current TTS and clear queue."""
        try:
            # Clear queue
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break
            
            # Stop current TTS
            if self.tts_engine:
                self.tts_engine.stop()
            
            self.logger.info("TTS stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop TTS: {e}")
    
    def play_sound(self, event: AudioEvent, volume: Optional[float] = None):
        """Play a sound effect for an event."""
        if not self.audio_enabled or not pygame or event not in self.sound_effects:
            return
        
        try:
            sound = self.sound_effects[event]
            sound_volume = volume if volume is not None else self.volume
            sound.set_volume(sound_volume)
            sound.play()
            
            self.logger.debug(f"Sound played: {event.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to play sound: {e}")
    
    def listen(self, timeout: float = 5.0, phrase_timeout: float = 1.0) -> Optional[str]:
        """Listen for speech and return recognized text."""
        if not self.sr_enabled or not self.sr_recognizer or not self.sr_microphone:
            return None
        
        try:
            with self.sr_microphone as source:
                self.logger.debug("Listening for speech...")
                audio = self.sr_recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            # Recognize speech using Google's service
            text = self.sr_recognizer.recognize_google(
                audio, 
                language=self.voice_settings['language']
            )
            
            self.logger.info(f"Speech recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            self.logger.debug("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            self.logger.debug("Speech not understood")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None
    
    def listen_async(self, callback: Callable[[Optional[str]], None], 
                    timeout: float = 5.0, phrase_timeout: float = 1.0):
        """Listen for speech asynchronously."""
        def listen_worker():
            result = self.listen(timeout, phrase_timeout)
            callback(result)
        
        thread = threading.Thread(target=listen_worker, daemon=True)
        thread.start()
    
    def register_event_callback(self, event: AudioEvent, callback: Callable):
        """Register a callback for audio events."""
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)
    
    def trigger_event(self, event: AudioEvent, data: Any = None):
        """Trigger an audio event."""
        # Play sound effect
        self.play_sound(event)
        
        # Call registered callbacks
        if event in self.event_callbacks:
            for callback in self.event_callbacks[event]:
                try:
                    callback(event, data)
                except Exception as e:
                    self.logger.error(f"Event callback error: {e}")
    
    # Configuration methods
    def set_tts_enabled(self, enabled: bool):
        """Enable or disable TTS."""
        self.tts_enabled = enabled
        if self.settings_manager:
            self.settings_manager.set('audio.tts_enabled', enabled)
        self.logger.info(f"TTS {'enabled' if enabled else 'disabled'}")
    
    def set_audio_enabled(self, enabled: bool):
        """Enable or disable audio effects."""
        self.audio_enabled = enabled
        if self.settings_manager:
            self.settings_manager.set('audio.effects_enabled', enabled)
        self.logger.info(f"Audio effects {'enabled' if enabled else 'disabled'}")
    
    def set_speech_recognition_enabled(self, enabled: bool):
        """Enable or disable speech recognition."""
        self.sr_enabled = enabled and self.sr_recognizer is not None
        if self.settings_manager:
            self.settings_manager.set('audio.speech_recognition_enabled', enabled)
        self.logger.info(f"Speech recognition {'enabled' if self.sr_enabled else 'disabled'}")
    
    def set_volume(self, volume: float):
        """Set audio volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.settings_manager:
            self.settings_manager.set('audio.volume', self.volume)
        self.logger.info(f"Volume set to {self.volume}")
    
    def set_tts_rate(self, rate: int):
        """Set TTS speaking rate."""
        self.voice_settings['rate'] = rate
        if self.tts_engine:
            self.tts_engine.setProperty('rate', rate)
        if self.settings_manager:
            self.settings_manager.set('audio.tts_rate', rate)
        self.logger.info(f"TTS rate set to {rate}")
    
    def set_tts_volume(self, volume: float):
        """Set TTS volume."""
        self.voice_settings['volume'] = max(0.0, min(1.0, volume))
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.voice_settings['volume'])
        if self.settings_manager:
            self.settings_manager.set('audio.tts_volume', self.voice_settings['volume'])
        self.logger.info(f"TTS volume set to {self.voice_settings['volume']}")
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available TTS voices."""
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            self.logger.error(f"Failed to get voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set TTS voice by ID."""
        if not self.tts_engine:
            return False
        
        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if voice.id == voice_id:
                    self.tts_engine.setProperty('voice', voice_id)
                    self.voice_settings['voice_id'] = voice_id
                    if self.settings_manager:
                        self.settings_manager.set('audio.tts_voice_id', voice_id)
                    self.logger.info(f"Voice set to {voice.name}")
                    return True
            
            self.logger.warning(f"Voice not found: {voice_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current audio service status."""
        return {
            'tts_enabled': self.tts_enabled,
            'tts_available': self.tts_engine is not None,
            'audio_enabled': self.audio_enabled,
            'audio_available': pygame is not None,
            'speech_recognition_enabled': self.sr_enabled,
            'speech_recognition_available': self.sr_recognizer is not None,
            'volume': self.volume,
            'tts_settings': self.voice_settings.copy(),
            'queue_size': self.tts_queue.qsize() if self.tts_queue else 0
        }
    
    def test_audio(self):
        """Test audio functionality."""
        # Test TTS
        if self.tts_enabled:
            self.speak("Test de synthèse vocale", priority=True)
        
        # Test sound effects
        if self.audio_enabled:
            time.sleep(1)
            self.play_sound(AudioEvent.SUCCESS)
        
        self.logger.info("Audio test completed")
    
    def shutdown(self):
        """Shutdown audio services."""
        self.logger.info("Shutting down audio services")
        
        # Stop TTS
        self.tts_running = False
        if self.tts_queue:
            self.tts_queue.put(None)  # Shutdown signal
        
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_thread.join(timeout=5)
        
        # Stop pygame mixer
        if pygame and pygame.mixer.get_init():
            pygame.mixer.quit()
        
        self.logger.info("Audio services shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.shutdown()