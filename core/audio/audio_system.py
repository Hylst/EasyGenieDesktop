"""Audio System for Playback, Recording, and Processing.

This module provides comprehensive audio capabilities including playback,
recording, format conversion, and audio processing features.
"""

import threading
import queue
import time
import wave
import json
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import io

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    AudioSegment = None
    play = None

try:
    import librosa
except ImportError:
    librosa = None


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    AAC = "aac"


class AudioQuality(Enum):
    """Audio quality presets."""
    LOW = "low"  # 22kHz, 64kbps
    MEDIUM = "medium"  # 44kHz, 128kbps
    HIGH = "high"  # 48kHz, 256kbps
    LOSSLESS = "lossless"  # 48kHz, uncompressed


class PlaybackState(Enum):
    """Audio playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class RecordingState(Enum):
    """Audio recording states."""
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    ERROR = "error"


class AudioEffect(Enum):
    """Audio effects."""
    NORMALIZE = "normalize"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SPEED_UP = "speed_up"
    SLOW_DOWN = "slow_down"
    PITCH_SHIFT = "pitch_shift"
    NOISE_REDUCTION = "noise_reduction"
    ECHO = "echo"
    REVERB = "reverb"
    BASS_BOOST = "bass_boost"
    TREBLE_BOOST = "treble_boost"


@dataclass
class AudioConfig:
    """Audio configuration."""
    # Format settings
    sample_rate: int = 44100
    channels: int = 2  # 1 = mono, 2 = stereo
    sample_width: int = 2  # bytes per sample
    format: AudioFormat = AudioFormat.WAV
    
    # Quality settings
    quality: AudioQuality = AudioQuality.MEDIUM
    bitrate: Optional[int] = None  # Auto-determined from quality
    
    # Device settings
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None
    
    # Buffer settings
    chunk_size: int = 1024
    buffer_size: int = 4096
    
    # Processing settings
    enable_noise_reduction: bool = True
    auto_gain_control: bool = True
    echo_cancellation: bool = True


@dataclass
class AudioMetadata:
    """Audio file metadata."""
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    year: Optional[int] = None
    duration: float = 0.0
    
    # Technical metadata
    sample_rate: int = 0
    channels: int = 0
    bitrate: int = 0
    format: str = ""
    file_size: int = 0
    
    # Custom metadata
    custom_tags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioTrack:
    """Audio track information."""
    id: str
    file_path: Path
    metadata: AudioMetadata
    
    # Playback info
    start_time: float = 0.0
    end_time: Optional[float] = None
    volume: float = 1.0
    
    # Processing
    effects: List[Tuple[AudioEffect, Dict[str, Any]]] = field(default_factory=list)
    
    # State
    is_loaded: bool = False
    last_played: Optional[datetime] = None


@dataclass
class RecordingSession:
    """Recording session information."""
    id: str
    start_time: datetime
    config: AudioConfig
    
    # Recording data
    audio_data: List[bytes] = field(default_factory=list)
    duration: float = 0.0
    
    # State
    state: RecordingState = RecordingState.IDLE
    output_path: Optional[Path] = None
    
    # Metadata
    metadata: AudioMetadata = field(default_factory=AudioMetadata)
    notes: str = ""


class AudioDevice:
    """Audio device information."""
    
    def __init__(self, index: int, name: str, channels: int, sample_rate: float, is_input: bool):
        """Initialize audio device.
        
        Args:
            index: Device index
            name: Device name
            channels: Number of channels
            sample_rate: Sample rate
            is_input: True if input device
        """
        self.index = index
        self.name = name
        self.channels = channels
        self.sample_rate = sample_rate
        self.is_input = is_input
    
    def __str__(self):
        """String representation."""
        device_type = "Input" if self.is_input else "Output"
        return f"{device_type}: {self.name} ({self.channels}ch, {self.sample_rate}Hz)"


class AudioPlayer:
    """Audio playback manager."""
    
    def __init__(self, config: AudioConfig):
        """Initialize audio player.
        
        Args:
            config: Audio configuration
        """
        self.config = config
        self.state = PlaybackState.STOPPED
        
        # PyAudio instance
        self.audio = None
        self.stream = None
        
        # Current track
        self.current_track: Optional[AudioTrack] = None
        self.audio_segment: Optional[AudioSegment] = None
        
        # Playback control
        self.position = 0.0  # Current position in seconds
        self.volume = 1.0
        self.is_muted = False
        
        # Threading
        self.playback_thread = None
        self.stop_event = threading.Event()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "playback_started": [],
            "playback_stopped": [],
            "playback_paused": [],
            "playback_resumed": [],
            "position_changed": [],
            "track_finished": [],
            "error_occurred": []
        }
        
        # Initialize PyAudio
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize PyAudio."""
        if pyaudio is not None:
            try:
                self.audio = pyaudio.PyAudio()
            except Exception as e:
                print(f"Error initializing PyAudio: {e}")
    
    def load_track(self, file_path: Union[str, Path]) -> bool:
        """Load audio track.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                print(f"Audio file not found: {file_path}")
                return False
            
            self._set_state(PlaybackState.LOADING)
            
            # Load with pydub if available
            if AudioSegment is not None:
                self.audio_segment = AudioSegment.from_file(str(file_path))
                
                # Create metadata
                metadata = AudioMetadata(
                    title=file_path.stem,
                    duration=len(self.audio_segment) / 1000.0,
                    sample_rate=self.audio_segment.frame_rate,
                    channels=self.audio_segment.channels,
                    format=file_path.suffix[1:].lower(),
                    file_size=file_path.stat().st_size
                )
                
                # Create track
                self.current_track = AudioTrack(
                    id=str(file_path),
                    file_path=file_path,
                    metadata=metadata
                )
                self.current_track.is_loaded = True
                
                self.position = 0.0
                self._set_state(PlaybackState.STOPPED)
                
                return True
            else:
                # Fallback to wave for WAV files
                if file_path.suffix.lower() == '.wav':
                    return self._load_wav_file(file_path)
                else:
                    print("Audio format not supported without pydub")
                    return False
                    
        except Exception as e:
            print(f"Error loading audio track: {e}")
            self._set_state(PlaybackState.ERROR)
            self._emit_event("error_occurred", {"error": str(e), "type": "load"})
            return False
    
    def _load_wav_file(self, file_path: Path) -> bool:
        """Load WAV file using wave module.
        
        Args:
            file_path: Path to WAV file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                duration = frames / sample_rate
                
                # Create metadata
                metadata = AudioMetadata(
                    title=file_path.stem,
                    duration=duration,
                    sample_rate=sample_rate,
                    channels=channels,
                    format="wav",
                    file_size=file_path.stat().st_size
                )
                
                # Create track
                self.current_track = AudioTrack(
                    id=str(file_path),
                    file_path=file_path,
                    metadata=metadata
                )
                self.current_track.is_loaded = True
                
                self.position = 0.0
                self._set_state(PlaybackState.STOPPED)
                
                return True
                
        except Exception as e:
            print(f"Error loading WAV file: {e}")
            return False
    
    def play(self) -> bool:
        """Start playback.
        
        Returns:
            bool: True if playback started
        """
        if not self.current_track or not self.current_track.is_loaded:
            print("No track loaded")
            return False
        
        if self.state == PlaybackState.PLAYING:
            print("Already playing")
            return True
        
        try:
            # Resume if paused
            if self.state == PlaybackState.PAUSED:
                self._set_state(PlaybackState.PLAYING)
                self._emit_event("playback_resumed", {"track": self.current_track})
                return True
            
            # Start new playback
            self.stop_event.clear()
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()
            
            self._set_state(PlaybackState.PLAYING)
            self._emit_event("playback_started", {"track": self.current_track})
            
            return True
            
        except Exception as e:
            print(f"Error starting playback: {e}")
            self._set_state(PlaybackState.ERROR)
            self._emit_event("error_occurred", {"error": str(e), "type": "playback"})
            return False
    
    def pause(self):
        """Pause playback."""
        if self.state == PlaybackState.PLAYING:
            self._set_state(PlaybackState.PAUSED)
            self._emit_event("playback_paused", {"track": self.current_track, "position": self.position})
    
    def stop(self):
        """Stop playback."""
        if self.state in [PlaybackState.PLAYING, PlaybackState.PAUSED]:
            self.stop_event.set()
            
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=1.0)
            
            self.position = 0.0
            self._set_state(PlaybackState.STOPPED)
            self._emit_event("playback_stopped", {"track": self.current_track})
    
    def seek(self, position: float):
        """Seek to position.
        
        Args:
            position: Position in seconds
        """
        if self.current_track and self.current_track.is_loaded:
            max_position = self.current_track.metadata.duration
            self.position = max(0.0, min(position, max_position))
            self._emit_event("position_changed", {"position": self.position})
    
    def set_volume(self, volume: float):
        """Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
    
    def mute(self):
        """Mute audio."""
        self.is_muted = True
    
    def unmute(self):
        """Unmute audio."""
        self.is_muted = False
    
    def _playback_loop(self):
        """Main playback loop."""
        try:
            if AudioSegment is not None and self.audio_segment:
                self._playback_with_pydub()
            else:
                self._playback_with_pyaudio()
                
        except Exception as e:
            print(f"Error in playback loop: {e}")
            self._set_state(PlaybackState.ERROR)
            self._emit_event("error_occurred", {"error": str(e), "type": "playback_loop"})
    
    def _playback_with_pydub(self):
        """Playback using pydub."""
        if not self.audio_segment:
            return
        
        # Apply volume
        audio = self.audio_segment
        if self.is_muted:
            audio = audio - 60  # Effectively mute
        elif self.volume != 1.0:
            # Convert volume to dB
            db_change = 20 * np.log10(self.volume) if np else 0
            audio = audio + db_change
        
        # Seek to position
        if self.position > 0:
            start_ms = int(self.position * 1000)
            audio = audio[start_ms:]
        
        # Play audio
        try:
            play(audio)
            
            # Update position
            self.position = self.current_track.metadata.duration
            
            # Track finished
            if not self.stop_event.is_set():
                self._emit_event("track_finished", {"track": self.current_track})
                self._set_state(PlaybackState.STOPPED)
                
        except Exception as e:
            print(f"Pydub playback error: {e}")
    
    def _playback_with_pyaudio(self):
        """Playback using PyAudio (WAV files only)."""
        if not self.audio or not self.current_track:
            return
        
        try:
            with wave.open(str(self.current_track.file_path), 'rb') as wav_file:
                # Open stream
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True,
                    output_device_index=self.config.output_device_index
                )
                
                # Seek to position
                if self.position > 0:
                    frame_position = int(self.position * wav_file.getframerate())
                    wav_file.setpos(frame_position)
                
                # Read and play data
                chunk_size = self.config.chunk_size
                data = wav_file.readframes(chunk_size)
                
                while data and not self.stop_event.is_set():
                    if self.state == PlaybackState.PLAYING:
                        # Apply volume if needed
                        if self.is_muted or self.volume != 1.0:
                            data = self._apply_volume(data, wav_file.getsampwidth())
                        
                        stream.write(data)
                        
                        # Update position
                        frames_played = len(data) // (wav_file.getnchannels() * wav_file.getsampwidth())
                        self.position += frames_played / wav_file.getframerate()
                        
                        # Emit position update periodically
                        if int(self.position * 10) % 5 == 0:  # Every 0.5 seconds
                            self._emit_event("position_changed", {"position": self.position})
                        
                        data = wav_file.readframes(chunk_size)
                    else:
                        # Paused - wait
                        time.sleep(0.1)
                
                stream.stop_stream()
                stream.close()
                
                # Track finished
                if not self.stop_event.is_set() and self.state == PlaybackState.PLAYING:
                    self._emit_event("track_finished", {"track": self.current_track})
                    self._set_state(PlaybackState.STOPPED)
                    
        except Exception as e:
            print(f"PyAudio playback error: {e}")
    
    def _apply_volume(self, data: bytes, sample_width: int) -> bytes:
        """Apply volume to audio data.
        
        Args:
            data: Audio data
            sample_width: Sample width in bytes
            
        Returns:
            bytes: Modified audio data
        """
        if np is None:
            return data
        
        try:
            # Convert to numpy array
            if sample_width == 1:
                audio_array = np.frombuffer(data, dtype=np.uint8)
                audio_array = audio_array.astype(np.float32) / 128.0 - 1.0
            elif sample_width == 2:
                audio_array = np.frombuffer(data, dtype=np.int16)
                audio_array = audio_array.astype(np.float32) / 32768.0
            else:
                return data  # Unsupported sample width
            
            # Apply volume
            if self.is_muted:
                audio_array *= 0.0
            else:
                audio_array *= self.volume
            
            # Convert back to bytes
            if sample_width == 1:
                audio_array = ((audio_array + 1.0) * 128.0).astype(np.uint8)
            elif sample_width == 2:
                audio_array = (audio_array * 32768.0).astype(np.int16)
            
            return audio_array.tobytes()
            
        except Exception as e:
            print(f"Error applying volume: {e}")
            return data
    
    def _set_state(self, new_state: PlaybackState):
        """Set playback state.
        
        Args:
            new_state: New state
        """
        if self.state != new_state:
            self.state = new_state
    
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
    
    def get_current_track(self) -> Optional[AudioTrack]:
        """Get current track.
        
        Returns:
            Optional[AudioTrack]: Current track or None
        """
        return self.current_track
    
    def get_position(self) -> float:
        """Get current position.
        
        Returns:
            float: Position in seconds
        """
        return self.position
    
    def get_duration(self) -> float:
        """Get track duration.
        
        Returns:
            float: Duration in seconds
        """
        if self.current_track:
            return self.current_track.metadata.duration
        return 0.0
    
    def destroy(self):
        """Destroy audio player."""
        self.stop()
        
        if self.audio:
            self.audio.terminate()
        
        self.event_handlers.clear()


class AudioRecorder:
    """Audio recording manager."""
    
    def __init__(self, config: AudioConfig):
        """Initialize audio recorder.
        
        Args:
            config: Audio configuration
        """
        self.config = config
        self.state = RecordingState.IDLE
        
        # PyAudio instance
        self.audio = None
        self.stream = None
        
        # Current session
        self.current_session: Optional[RecordingSession] = None
        
        # Recording data
        self.audio_queue = queue.Queue()
        
        # Threading
        self.recording_thread = None
        self.stop_event = threading.Event()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "recording_started": [],
            "recording_stopped": [],
            "recording_paused": [],
            "recording_resumed": [],
            "data_recorded": [],
            "session_saved": [],
            "error_occurred": []
        }
        
        # Initialize PyAudio
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize PyAudio."""
        if pyaudio is not None:
            try:
                self.audio = pyaudio.PyAudio()
            except Exception as e:
                print(f"Error initializing PyAudio: {e}")
    
    def start_recording(self, session_id: str = None, output_path: Path = None) -> bool:
        """Start recording.
        
        Args:
            session_id: Session identifier
            output_path: Output file path
            
        Returns:
            bool: True if recording started
        """
        if self.state == RecordingState.RECORDING:
            print("Already recording")
            return True
        
        if not self.audio:
            print("Audio system not available")
            return False
        
        try:
            # Create new session
            if not session_id:
                session_id = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.current_session = RecordingSession(
                id=session_id,
                start_time=datetime.now(),
                config=self.config,
                output_path=output_path
            )
            
            # Resume if paused
            if self.state == RecordingState.PAUSED:
                self._set_state(RecordingState.RECORDING)
                self._emit_event("recording_resumed", {"session": self.current_session})
                return True
            
            # Start new recording
            self.stop_event.clear()
            self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
            self.recording_thread.start()
            
            self._set_state(RecordingState.RECORDING)
            self._emit_event("recording_started", {"session": self.current_session})
            
            return True
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self._set_state(RecordingState.ERROR)
            self._emit_event("error_occurred", {"error": str(e), "type": "recording"})
            return False
    
    def pause_recording(self):
        """Pause recording."""
        if self.state == RecordingState.RECORDING:
            self._set_state(RecordingState.PAUSED)
            self._emit_event("recording_paused", {"session": self.current_session})
    
    def stop_recording(self, save: bool = True) -> Optional[Path]:
        """Stop recording.
        
        Args:
            save: Whether to save the recording
            
        Returns:
            Optional[Path]: Path to saved file or None
        """
        if self.state not in [RecordingState.RECORDING, RecordingState.PAUSED]:
            return None
        
        # Stop recording thread
        self.stop_event.set()
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        self._set_state(RecordingState.PROCESSING)
        
        saved_path = None
        if save and self.current_session:
            saved_path = self._save_recording()
        
        self._set_state(RecordingState.IDLE)
        self._emit_event("recording_stopped", {
            "session": self.current_session,
            "saved_path": saved_path
        })
        
        return saved_path
    
    def _recording_loop(self):
        """Main recording loop."""
        try:
            # Open stream
            stream = self.audio.open(
                format=pyaudio.paInt16,  # 16-bit
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.input_device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            start_time = time.time()
            
            while not self.stop_event.is_set():
                if self.state == RecordingState.RECORDING:
                    # Read audio data
                    data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                    
                    # Store data
                    if self.current_session:
                        self.current_session.audio_data.append(data)
                        self.current_session.duration = time.time() - start_time
                    
                    # Emit data event
                    self._emit_event("data_recorded", {
                        "data": data,
                        "duration": time.time() - start_time
                    })
                else:
                    # Paused - wait
                    time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Error in recording loop: {e}")
            self._set_state(RecordingState.ERROR)
            self._emit_event("error_occurred", {"error": str(e), "type": "recording_loop"})
    
    def _save_recording(self) -> Optional[Path]:
        """Save current recording.
        
        Returns:
            Optional[Path]: Path to saved file or None
        """
        if not self.current_session or not self.current_session.audio_data:
            return None
        
        try:
            # Determine output path
            if self.current_session.output_path:
                output_path = self.current_session.output_path
            else:
                output_path = Path(f"{self.current_session.id}.wav")
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as WAV file
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(self.config.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.config.sample_rate)
                
                # Write all audio data
                for data in self.current_session.audio_data:
                    wav_file.writeframes(data)
            
            # Update metadata
            self.current_session.metadata.duration = self.current_session.duration
            self.current_session.metadata.sample_rate = self.config.sample_rate
            self.current_session.metadata.channels = self.config.channels
            self.current_session.metadata.format = "wav"
            self.current_session.metadata.file_size = output_path.stat().st_size
            
            self._emit_event("session_saved", {
                "session": self.current_session,
                "path": output_path
            })
            
            return output_path
            
        except Exception as e:
            print(f"Error saving recording: {e}")
            self._emit_event("error_occurred", {"error": str(e), "type": "save"})
            return None
    
    def _set_state(self, new_state: RecordingState):
        """Set recording state.
        
        Args:
            new_state: New state
        """
        if self.state != new_state:
            self.state = new_state
    
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
    
    def get_current_session(self) -> Optional[RecordingSession]:
        """Get current recording session.
        
        Returns:
            Optional[RecordingSession]: Current session or None
        """
        return self.current_session
    
    def destroy(self):
        """Destroy audio recorder."""
        self.stop_recording(save=False)
        
        if self.audio:
            self.audio.terminate()
        
        self.event_handlers.clear()


class AudioSystem:
    """Main audio system manager."""
    
    def __init__(self, config: AudioConfig = None):
        """Initialize audio system.
        
        Args:
            config: Audio configuration
        """
        self.config = config or AudioConfig()
        
        # Components
        self.player = AudioPlayer(self.config)
        self.recorder = AudioRecorder(self.config)
        
        # Device management
        self.audio_devices: List[AudioDevice] = []
        self._scan_audio_devices()
    
    def _scan_audio_devices(self):
        """Scan for available audio devices."""
        if pyaudio is None:
            return
        
        try:
            audio = pyaudio.PyAudio()
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                
                # Input device
                if device_info['maxInputChannels'] > 0:
                    device = AudioDevice(
                        index=i,
                        name=device_info['name'],
                        channels=device_info['maxInputChannels'],
                        sample_rate=device_info['defaultSampleRate'],
                        is_input=True
                    )
                    self.audio_devices.append(device)
                
                # Output device
                if device_info['maxOutputChannels'] > 0:
                    device = AudioDevice(
                        index=i,
                        name=device_info['name'],
                        channels=device_info['maxOutputChannels'],
                        sample_rate=device_info['defaultSampleRate'],
                        is_input=False
                    )
                    self.audio_devices.append(device)
            
            audio.terminate()
            
        except Exception as e:
            print(f"Error scanning audio devices: {e}")
    
    def get_audio_devices(self, input_only: bool = False, output_only: bool = False) -> List[AudioDevice]:
        """Get available audio devices.
        
        Args:
            input_only: Return only input devices
            output_only: Return only output devices
            
        Returns:
            List[AudioDevice]: Available devices
        """
        devices = self.audio_devices
        
        if input_only:
            devices = [d for d in devices if d.is_input]
        elif output_only:
            devices = [d for d in devices if not d.is_input]
        
        return devices
    
    def set_input_device(self, device_index: int):
        """Set input device.
        
        Args:
            device_index: Device index
        """
        self.config.input_device_index = device_index
    
    def set_output_device(self, device_index: int):
        """Set output device.
        
        Args:
            device_index: Device index
        """
        self.config.output_device_index = device_index
    
    def is_available(self) -> bool:
        """Check if audio system is available.
        
        Returns:
            bool: True if available
        """
        return pyaudio is not None
    
    def get_player(self) -> AudioPlayer:
        """Get audio player.
        
        Returns:
            AudioPlayer: Audio player instance
        """
        return self.player
    
    def get_recorder(self) -> AudioRecorder:
        """Get audio recorder.
        
        Returns:
            AudioRecorder: Audio recorder instance
        """
        return self.recorder
    
    def destroy(self):
        """Destroy audio system."""
        self.player.destroy()
        self.recorder.destroy()
        self.audio_devices.clear()


# Global audio system instance
_audio_system: Optional[AudioSystem] = None


def get_audio_system() -> Optional[AudioSystem]:
    """Get global audio system instance.
    
    Returns:
        Optional[AudioSystem]: Global audio system or None
    """
    return _audio_system


def set_audio_system(system: AudioSystem):
    """Set global audio system instance.
    
    Args:
        system: Audio system to set
    """
    global _audio_system
    _audio_system = system


# Convenience functions
def initialize_audio(config: AudioConfig = None) -> bool:
    """Initialize audio system (convenience function).
    
    Args:
        config: Audio configuration
        
    Returns:
        bool: True if initialized successfully
    """
    global _audio_system
    
    try:
        _audio_system = AudioSystem(config)
        return _audio_system.is_available()
    except Exception as e:
        print(f"Error initializing audio system: {e}")
        return False


def play_audio(file_path: Union[str, Path]) -> bool:
    """Play audio file (convenience function).
    
    Args:
        file_path: Path to audio file
        
    Returns:
        bool: True if playback started
    """
    if _audio_system:
        player = _audio_system.get_player()
        if player.load_track(file_path):
            return player.play()
    
    return False


def start_recording(output_path: Path = None) -> bool:
    """Start audio recording (convenience function).
    
    Args:
        output_path: Output file path
        
    Returns:
        bool: True if recording started
    """
    if _audio_system:
        recorder = _audio_system.get_recorder()
        return recorder.start_recording(output_path=output_path)
    
    return False


def stop_recording() -> Optional[Path]:
    """Stop audio recording (convenience function).
    
    Returns:
        Optional[Path]: Path to saved file or None
    """
    if _audio_system:
        recorder = _audio_system.get_recorder()
        return recorder.stop_recording()
    
    return None