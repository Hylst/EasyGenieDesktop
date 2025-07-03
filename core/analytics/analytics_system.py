"""Analytics System for User Behavior and Performance Tracking.

This module provides comprehensive analytics capabilities including user behavior tracking,
performance monitoring, usage statistics, and reporting.
"""

import threading
import time
import json
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict, deque
import sqlite3
from contextlib import contextmanager
import psutil
import platform
import sys


class EventType(Enum):
    """Analytics event types."""
    # User interaction events
    USER_ACTION = "user_action"
    BUTTON_CLICK = "button_click"
    MENU_SELECT = "menu_select"
    TOOL_OPEN = "tool_open"
    TOOL_CLOSE = "tool_close"
    FEATURE_USE = "feature_use"
    
    # Application events
    APP_START = "app_start"
    APP_CLOSE = "app_close"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    
    # Performance events
    PERFORMANCE = "performance"
    ERROR = "error"
    CRASH = "crash"
    SLOW_OPERATION = "slow_operation"
    
    # AI interaction events
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    
    # Custom events
    CUSTOM = "custom"


class MetricType(Enum):
    """Metric types for analytics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SET = "set"


class AggregationType(Enum):
    """Aggregation types for metrics."""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"


class ReportPeriod(Enum):
    """Report time periods."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    CUSTOM = "custom"


@dataclass
class AnalyticsEvent:
    """Analytics event data."""
    # Basic properties
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    name: str = ""
    
    # Event data
    properties: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None  # seconds
    
    # Context
    tool_name: Optional[str] = None
    view_name: Optional[str] = None
    category: str = "general"
    
    # Technical details
    platform_info: Dict[str, Any] = field(default_factory=dict)
    app_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'name': self.name,
            'properties': self.properties,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'tool_name': self.tool_name,
            'view_name': self.view_name,
            'category': self.category,
            'platform_info': self.platform_info,
            'app_version': self.app_version
        }


@dataclass
class Metric:
    """Analytics metric."""
    name: str
    metric_type: MetricType
    value: Union[int, float, str, List[Any]]
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary.
        
        Returns:
            Dict[str, Any]: Metric data
        """
        return {
            'name': self.name,
            'type': self.metric_type.value,
            'value': self.value,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    
    # Memory metrics
    memory_percent: float = 0.0
    memory_used: int = 0  # bytes
    memory_total: int = 0  # bytes
    
    # Disk metrics
    disk_usage_percent: float = 0.0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    
    # Network metrics
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0
    
    # Application metrics
    app_memory_rss: int = 0  # bytes
    app_memory_vms: int = 0  # bytes
    app_cpu_percent: float = 0.0
    thread_count: int = 0
    
    # Timing metrics
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary.
        
        Returns:
            Dict[str, Any]: Metrics data
        """
        return asdict(self)


@dataclass
class UserSession:
    """User session tracking."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Session data
    events_count: int = 0
    tools_used: List[str] = field(default_factory=list)
    features_used: List[str] = field(default_factory=list)
    
    # Performance data
    avg_response_time: float = 0.0
    errors_count: int = 0
    
    # Platform info
    platform: str = ""
    app_version: str = ""
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get session duration.
        
        Returns:
            Optional[timedelta]: Session duration or None if not ended
        """
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def end_session(self):
        """End the session."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.
        
        Returns:
            Dict[str, Any]: Session data
        """
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration.total_seconds() if self.duration else None,
            'events_count': self.events_count,
            'tools_used': self.tools_used,
            'features_used': self.features_used,
            'avg_response_time': self.avg_response_time,
            'errors_count': self.errors_count,
            'platform': self.platform,
            'app_version': self.app_version
        }


@dataclass
class AnalyticsConfig:
    """Analytics system configuration."""
    # Data collection settings
    enabled: bool = True
    collect_user_events: bool = True
    collect_performance_metrics: bool = True
    collect_error_events: bool = True
    
    # Privacy settings
    anonymize_user_data: bool = True
    collect_personal_info: bool = False
    
    # Storage settings
    database_path: Path = Path("analytics.db")
    max_events_in_memory: int = 1000
    batch_size: int = 100
    flush_interval: int = 60  # seconds
    
    # Performance monitoring
    performance_sample_rate: float = 0.1  # 10% sampling
    performance_collection_interval: int = 30  # seconds
    
    # Data retention
    retention_days: int = 90
    auto_cleanup: bool = True
    cleanup_interval: int = 86400  # seconds (daily)
    
    # Export settings
    export_enabled: bool = False
    export_endpoint: Optional[str] = None
    export_api_key: Optional[str] = None
    export_batch_size: int = 500


class AnalyticsDatabase:
    """Analytics database manager."""
    
    def __init__(self, database_path: Path):
        """Initialize analytics database.
        
        Args:
            database_path: Path to database file
        """
        self.database_path = database_path
        self.connection: Optional[sqlite3.Connection] = None
        self.lock = threading.Lock()
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    properties TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    duration REAL,
                    tool_name TEXT,
                    view_name TEXT,
                    category TEXT,
                    platform_info TEXT,
                    app_version TEXT
                )
            """)
            
            # Metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    tags TEXT,
                    timestamp TIMESTAMP NOT NULL
                )
            """)
            
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    events_count INTEGER DEFAULT 0,
                    tools_used TEXT,
                    features_used TEXT,
                    avg_response_time REAL DEFAULT 0.0,
                    errors_count INTEGER DEFAULT 0,
                    platform TEXT,
                    app_version TEXT
                )
            """)
            
            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used INTEGER,
                    memory_total INTEGER,
                    disk_usage_percent REAL,
                    app_memory_rss INTEGER,
                    app_cpu_percent REAL,
                    thread_count INTEGER
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        with self.lock:
            if not self.connection:
                self.database_path.parent.mkdir(parents=True, exist_ok=True)
                self.connection = sqlite3.connect(
                    str(self.database_path),
                    check_same_thread=False
                )
                self.connection.row_factory = sqlite3.Row
            
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
    
    def store_event(self, event: AnalyticsEvent):
        """Store analytics event.
        
        Args:
            event: Event to store
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO events (
                    event_id, event_type, name, properties, user_id, session_id,
                    timestamp, duration, tool_name, view_name, category,
                    platform_info, app_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.name,
                json.dumps(event.properties),
                event.user_id,
                event.session_id,
                event.timestamp,
                event.duration,
                event.tool_name,
                event.view_name,
                event.category,
                json.dumps(event.platform_info),
                event.app_version
            ))
    
    def store_metric(self, metric: Metric):
        """Store metric.
        
        Args:
            metric: Metric to store
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO metrics (name, type, value, tags, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.metric_type.value,
                json.dumps(metric.value),
                json.dumps(metric.tags),
                metric.timestamp
            ))
    
    def store_session(self, session: UserSession):
        """Store or update user session.
        
        Args:
            session: Session to store
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, user_id, start_time, end_time, events_count,
                    tools_used, features_used, avg_response_time, errors_count,
                    platform, app_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.start_time,
                session.end_time,
                session.events_count,
                json.dumps(session.tools_used),
                json.dumps(session.features_used),
                session.avg_response_time,
                session.errors_count,
                session.platform,
                session.app_version
            ))
    
    def store_performance_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics.
        
        Args:
            metrics: Performance metrics to store
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO performance_metrics (
                    timestamp, cpu_percent, memory_percent, memory_used,
                    memory_total, disk_usage_percent, app_memory_rss,
                    app_cpu_percent, thread_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.memory_used,
                metrics.memory_total,
                metrics.disk_usage_percent,
                metrics.app_memory_rss,
                metrics.app_cpu_percent,
                metrics.thread_count
            ))
    
    def get_events(self, start_time: datetime = None, end_time: datetime = None,
                  event_type: EventType = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get events with filters.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            event_type: Event type filter
            limit: Result limit
            
        Returns:
            List[Dict[str, Any]]: Events
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_metrics(self, name: str = None, start_time: datetime = None,
                   end_time: datetime = None) -> List[Dict[str, Any]]:
        """Get metrics with filters.
        
        Args:
            name: Metric name filter
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List[Dict[str, Any]]: Metrics
        """
        query = "SELECT * FROM metrics WHERE 1=1"
        params = []
        
        if name:
            query += " AND name = ?"
            params.append(name)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, retention_days: int):
        """Clean up old data.
        
        Args:
            retention_days: Number of days to retain
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with self._get_connection() as conn:
            # Clean up events
            conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_date,))
            
            # Clean up metrics
            conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_date,))
            
            # Clean up performance metrics
            conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
            
            # Clean up old sessions
            conn.execute("DELETE FROM sessions WHERE start_time < ?", (cutoff_date,))
    
    def close(self):
        """Close database connection."""
        with self.lock:
            if self.connection:
                self.connection.close()
                self.connection = None


class PerformanceMonitor:
    """System performance monitor."""
    
    def __init__(self, sample_rate: float = 0.1):
        """Initialize performance monitor.
        
        Args:
            sample_rate: Sampling rate (0.0 to 1.0)
        """
        self.sample_rate = sample_rate
        self.process = psutil.Process()
        self.last_disk_io = None
        self.last_network_io = None
    
    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics.
        
        Returns:
            PerformanceMetrics: Current metrics
        """
        metrics = PerformanceMetrics()
        
        try:
            # System CPU
            metrics.cpu_percent = psutil.cpu_percent()
            metrics.cpu_count = psutil.cpu_count()
            
            # System memory
            memory = psutil.virtual_memory()
            metrics.memory_percent = memory.percent
            metrics.memory_used = memory.used
            metrics.memory_total = memory.total
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics.disk_usage_percent = (disk.used / disk.total) * 100
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.disk_read_bytes = disk_io.read_bytes
                metrics.disk_write_bytes = disk_io.write_bytes
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.network_sent_bytes = network_io.bytes_sent
                metrics.network_recv_bytes = network_io.bytes_recv
            
            # Application metrics
            memory_info = self.process.memory_info()
            metrics.app_memory_rss = memory_info.rss
            metrics.app_memory_vms = memory_info.vms
            metrics.app_cpu_percent = self.process.cpu_percent()
            metrics.thread_count = self.process.num_threads()
            
        except Exception as e:
            logging.error(f"Performance metrics collection error: {e}")
        
        return metrics
    
    def should_sample(self) -> bool:
        """Check if should sample based on sample rate.
        
        Returns:
            bool: True if should sample
        """
        import random
        return random.random() < self.sample_rate


class AnalyticsSystem:
    """Main analytics system manager."""
    
    def __init__(self, config: AnalyticsConfig = None):
        """Initialize analytics system.
        
        Args:
            config: Analytics configuration
        """
        self.config = config or AnalyticsConfig()
        self.database = AnalyticsDatabase(self.config.database_path)
        self.performance_monitor = PerformanceMonitor(self.config.performance_sample_rate)
        
        # Current session
        self.current_session: Optional[UserSession] = None
        self.current_user_id: Optional[str] = None
        
        # Event buffer
        self.event_buffer: deque = deque(maxlen=self.config.max_events_in_memory)
        self.metrics_buffer: deque = deque(maxlen=self.config.max_events_in_memory)
        
        # Threading
        self.flush_thread: Optional[threading.Thread] = None
        self.performance_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Platform info
        self.platform_info = self._get_platform_info()
        
        # Timers for tracking operation durations
        self.active_timers: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            'events_collected': 0,
            'events_stored': 0,
            'metrics_collected': 0,
            'errors_count': 0,
            'sessions_count': 0
        }
        
        # Start background tasks
        if self.config.enabled:
            self.start()
    
    def start(self):
        """Start analytics system."""
        if not self.running:
            self.running = True
            
            # Start flush thread
            self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
            self.flush_thread.start()
            
            # Start performance monitoring
            if self.config.collect_performance_metrics:
                self.performance_thread = threading.Thread(target=self._performance_loop, daemon=True)
                self.performance_thread.start()
            
            # Start cleanup thread
            if self.config.auto_cleanup:
                self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
                self.cleanup_thread.start()
    
    def stop(self):
        """Stop analytics system."""
        self.running = False
        
        # End current session
        if self.current_session:
            self.end_session()
        
        # Flush remaining data
        self._flush_buffers()
        
        # Wait for threads
        for thread in [self.flush_thread, self.performance_thread, self.cleanup_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
        
        # Close database
        self.database.close()
    
    def start_session(self, user_id: str = None) -> str:
        """Start new user session.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            str: Session ID
        """
        # End previous session if exists
        if self.current_session:
            self.end_session()
        
        # Create new session
        self.current_session = UserSession(
            user_id=user_id,
            platform=self.platform_info.get('platform', ''),
            app_version=self.platform_info.get('app_version', '')
        )
        self.current_user_id = user_id
        
        # Track session start event
        self.track_event(
            EventType.SESSION_START,
            "session_started",
            {
                'session_id': self.current_session.session_id,
                'user_id': user_id
            }
        )
        
        self.stats['sessions_count'] += 1
        
        return self.current_session.session_id
    
    def end_session(self):
        """End current session."""
        if self.current_session:
            self.current_session.end_session()
            
            # Track session end event
            self.track_event(
                EventType.SESSION_END,
                "session_ended",
                {
                    'session_id': self.current_session.session_id,
                    'duration_seconds': self.current_session.duration.total_seconds() if self.current_session.duration else 0
                }
            )
            
            # Store session
            self.database.store_session(self.current_session)
            self.current_session = None
    
    def track_event(self, event_type: EventType, name: str, properties: Dict[str, Any] = None,
                   duration: float = None, tool_name: str = None, view_name: str = None,
                   category: str = "general"):
        """Track analytics event.
        
        Args:
            event_type: Type of event
            name: Event name
            properties: Event properties
            duration: Event duration in seconds
            tool_name: Associated tool name
            view_name: Associated view name
            category: Event category
        """
        if not self.config.enabled or not self.config.collect_user_events:
            return
        
        # Create event
        event = AnalyticsEvent(
            event_type=event_type,
            name=name,
            properties=properties or {},
            user_id=self.current_user_id if not self.config.anonymize_user_data else None,
            session_id=self.current_session.session_id if self.current_session else None,
            duration=duration,
            tool_name=tool_name,
            view_name=view_name,
            category=category,
            platform_info=self.platform_info,
            app_version=self.platform_info.get('app_version')
        )
        
        # Add to buffer
        self.event_buffer.append(event)
        
        # Update session
        if self.current_session:
            self.current_session.events_count += 1
            
            if tool_name and tool_name not in self.current_session.tools_used:
                self.current_session.tools_used.append(tool_name)
            
            if name not in self.current_session.features_used:
                self.current_session.features_used.append(name)
        
        self.stats['events_collected'] += 1
    
    def track_user_action(self, action: str, properties: Dict[str, Any] = None,
                         tool_name: str = None):
        """Track user action (convenience method).
        
        Args:
            action: Action name
            properties: Action properties
            tool_name: Associated tool name
        """
        self.track_event(
            EventType.USER_ACTION,
            action,
            properties,
            tool_name=tool_name,
            category="user_interaction"
        )
    
    def track_button_click(self, button_name: str, tool_name: str = None,
                          view_name: str = None):
        """Track button click (convenience method).
        
        Args:
            button_name: Button name
            tool_name: Associated tool name
            view_name: Associated view name
        """
        self.track_event(
            EventType.BUTTON_CLICK,
            "button_clicked",
            {'button_name': button_name},
            tool_name=tool_name,
            view_name=view_name,
            category="ui_interaction"
        )
    
    def track_tool_usage(self, tool_name: str, action: str, properties: Dict[str, Any] = None):
        """Track tool usage (convenience method).
        
        Args:
            tool_name: Tool name
            action: Action performed
            properties: Additional properties
        """
        event_type = EventType.TOOL_OPEN if action == "open" else EventType.TOOL_CLOSE if action == "close" else EventType.FEATURE_USE
        
        self.track_event(
            event_type,
            f"tool_{action}",
            properties or {},
            tool_name=tool_name,
            category="tool_usage"
        )
    
    def track_ai_interaction(self, provider: str, model: str, tokens_used: int,
                           response_time: float, success: bool, error: str = None):
        """Track AI interaction (convenience method).
        
        Args:
            provider: AI provider
            model: AI model
            tokens_used: Tokens consumed
            response_time: Response time in seconds
            success: Whether interaction was successful
            error: Error message if failed
        """
        event_type = EventType.AI_RESPONSE if success else EventType.AI_ERROR
        
        properties = {
            'provider': provider,
            'model': model,
            'tokens_used': tokens_used,
            'response_time': response_time,
            'success': success
        }
        
        if error:
            properties['error'] = error
        
        self.track_event(
            event_type,
            "ai_interaction",
            properties,
            duration=response_time,
            category="ai"
        )
    
    def track_error(self, error_type: str, error_message: str, stack_trace: str = None,
                   tool_name: str = None):
        """Track error event (convenience method).
        
        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace
            tool_name: Associated tool name
        """
        properties = {
            'error_type': error_type,
            'error_message': error_message
        }
        
        if stack_trace:
            properties['stack_trace'] = stack_trace
        
        self.track_event(
            EventType.ERROR,
            "error_occurred",
            properties,
            tool_name=tool_name,
            category="error"
        )
        
        # Update session error count
        if self.current_session:
            self.current_session.errors_count += 1
        
        self.stats['errors_count'] += 1
    
    def start_timer(self, timer_name: str):
        """Start operation timer.
        
        Args:
            timer_name: Timer name
        """
        self.active_timers[timer_name] = datetime.now()
    
    def end_timer(self, timer_name: str, event_name: str = None, properties: Dict[str, Any] = None):
        """End operation timer and track event.
        
        Args:
            timer_name: Timer name
            event_name: Event name (defaults to timer name)
            properties: Event properties
        """
        if timer_name in self.active_timers:
            start_time = self.active_timers.pop(timer_name)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Track timing event
            self.track_event(
                EventType.PERFORMANCE,
                event_name or timer_name,
                {**(properties or {}), 'duration': duration},
                duration=duration,
                category="performance"
            )
            
            # Check for slow operations
            if duration > 5.0:  # 5 seconds threshold
                self.track_event(
                    EventType.SLOW_OPERATION,
                    "slow_operation",
                    {
                        'operation': timer_name,
                        'duration': duration
                    },
                    duration=duration,
                    category="performance"
                )
    
    def record_metric(self, name: str, value: Union[int, float, str, List[Any]],
                     metric_type: MetricType = MetricType.GAUGE, tags: Dict[str, str] = None):
        """Record custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Metric tags
        """
        if not self.config.enabled:
            return
        
        metric = Metric(
            name=name,
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )
        
        self.metrics_buffer.append(metric)
        self.stats['metrics_collected'] += 1
    
    def get_events(self, start_time: datetime = None, end_time: datetime = None,
                  event_type: EventType = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events from database.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            event_type: Event type filter
            limit: Result limit
            
        Returns:
            List[Dict[str, Any]]: Events
        """
        return self.database.get_events(start_time, end_time, event_type, limit)
    
    def get_metrics(self, name: str = None, start_time: datetime = None,
                   end_time: datetime = None) -> List[Dict[str, Any]]:
        """Get metrics from database.
        
        Args:
            name: Metric name filter
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List[Dict[str, Any]]: Metrics
        """
        return self.database.get_metrics(name, start_time, end_time)
    
    def generate_report(self, period: ReportPeriod, start_time: datetime = None,
                       end_time: datetime = None) -> Dict[str, Any]:
        """Generate analytics report.
        
        Args:
            period: Report period
            start_time: Custom start time
            end_time: Custom end time
            
        Returns:
            Dict[str, Any]: Analytics report
        """
        # Calculate time range
        if period == ReportPeriod.CUSTOM:
            if not start_time or not end_time:
                raise ValueError("Custom period requires start_time and end_time")
        else:
            end_time = datetime.now()
            if period == ReportPeriod.HOUR:
                start_time = end_time - timedelta(hours=1)
            elif period == ReportPeriod.DAY:
                start_time = end_time - timedelta(days=1)
            elif period == ReportPeriod.WEEK:
                start_time = end_time - timedelta(weeks=1)
            elif period == ReportPeriod.MONTH:
                start_time = end_time - timedelta(days=30)
            elif period == ReportPeriod.YEAR:
                start_time = end_time - timedelta(days=365)
        
        # Get events
        events = self.get_events(start_time, end_time)
        
        # Analyze events
        report = {
            'period': period.value,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_events': len(events),
            'event_types': {},
            'tools_usage': {},
            'features_usage': {},
            'error_rate': 0.0,
            'avg_session_duration': 0.0,
            'unique_users': 0,
            'total_sessions': 0
        }
        
        # Count event types
        for event in events:
            event_type = event['event_type']
            report['event_types'][event_type] = report['event_types'].get(event_type, 0) + 1
        
        # Count tool usage
        for event in events:
            if event['tool_name']:
                tool = event['tool_name']
                report['tools_usage'][tool] = report['tools_usage'].get(tool, 0) + 1
        
        # Count feature usage
        for event in events:
            name = event['name']
            report['features_usage'][name] = report['features_usage'].get(name, 0) + 1
        
        # Calculate error rate
        error_events = report['event_types'].get('error', 0)
        if report['total_events'] > 0:
            report['error_rate'] = error_events / report['total_events']
        
        # Get session data
        with self.database._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count, AVG(
                    CASE WHEN end_time IS NOT NULL 
                    THEN (julianday(end_time) - julianday(start_time)) * 86400 
                    ELSE NULL END
                ) as avg_duration,
                COUNT(DISTINCT user_id) as unique_users
                FROM sessions 
                WHERE start_time >= ? AND start_time <= ?
            """, (start_time, end_time))
            
            session_data = cursor.fetchone()
            if session_data:
                report['total_sessions'] = session_data['count']
                report['avg_session_duration'] = session_data['avg_duration'] or 0.0
                report['unique_users'] = session_data['unique_users']
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        return {
            **self.stats,
            'buffer_size': len(self.event_buffer),
            'metrics_buffer_size': len(self.metrics_buffer),
            'active_timers': len(self.active_timers),
            'current_session_id': self.current_session.session_id if self.current_session else None,
            'system_running': self.running
        }
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform information.
        
        Returns:
            Dict[str, Any]: Platform info
        """
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': sys.version,
            'app_version': "2.0.0"  # This should come from app config
        }
    
    def _flush_buffers(self):
        """Flush event and metrics buffers to database."""
        try:
            # Flush events
            events_to_flush = []
            while self.event_buffer and len(events_to_flush) < self.config.batch_size:
                events_to_flush.append(self.event_buffer.popleft())
            
            for event in events_to_flush:
                self.database.store_event(event)
                self.stats['events_stored'] += 1
            
            # Flush metrics
            metrics_to_flush = []
            while self.metrics_buffer and len(metrics_to_flush) < self.config.batch_size:
                metrics_to_flush.append(self.metrics_buffer.popleft())
            
            for metric in metrics_to_flush:
                self.database.store_metric(metric)
            
        except Exception as e:
            logging.error(f"Buffer flush error: {e}")
    
    def _flush_loop(self):
        """Background flush loop."""
        while self.running:
            try:
                time.sleep(self.config.flush_interval)
                if self.event_buffer or self.metrics_buffer:
                    self._flush_buffers()
            except Exception as e:
                logging.error(f"Flush loop error: {e}")
    
    def _performance_loop(self):
        """Background performance monitoring loop."""
        while self.running:
            try:
                if self.performance_monitor.should_sample():
                    metrics = self.performance_monitor.collect_metrics()
                    self.database.store_performance_metrics(metrics)
                
                time.sleep(self.config.performance_collection_interval)
            except Exception as e:
                logging.error(f"Performance monitoring error: {e}")
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.running:
            try:
                time.sleep(self.config.cleanup_interval)
                self.database.cleanup_old_data(self.config.retention_days)
            except Exception as e:
                logging.error(f"Cleanup loop error: {e}")


# Global analytics system instance
_analytics_system: Optional[AnalyticsSystem] = None


def get_analytics_system() -> Optional[AnalyticsSystem]:
    """Get global analytics system instance.
    
    Returns:
        Optional[AnalyticsSystem]: Global analytics system or None
    """
    return _analytics_system


def set_analytics_system(system: AnalyticsSystem):
    """Set global analytics system instance.
    
    Args:
        system: Analytics system to set
    """
    global _analytics_system
    _analytics_system = system


# Convenience functions
def initialize_analytics(config: AnalyticsConfig = None) -> AnalyticsSystem:
    """Initialize analytics system (convenience function).
    
    Args:
        config: Analytics configuration
        
    Returns:
        AnalyticsSystem: Initialized analytics system
    """
    global _analytics_system
    _analytics_system = AnalyticsSystem(config)
    return _analytics_system


def track(event_type: EventType, name: str, properties: Dict[str, Any] = None, **kwargs):
    """Track event (convenience function).
    
    Args:
        event_type: Type of event
        name: Event name
        properties: Event properties
        **kwargs: Additional event parameters
    """
    if _analytics_system:
        _analytics_system.track_event(event_type, name, properties, **kwargs)


def track_action(action: str, properties: Dict[str, Any] = None, tool_name: str = None):
    """Track user action (convenience function).
    
    Args:
        action: Action name
        properties: Action properties
        tool_name: Associated tool name
    """
    if _analytics_system:
        _analytics_system.track_user_action(action, properties, tool_name)


def track_click(button_name: str, tool_name: str = None, view_name: str = None):
    """Track button click (convenience function).
    
    Args:
        button_name: Button name
        tool_name: Associated tool name
        view_name: Associated view name
    """
    if _analytics_system:
        _analytics_system.track_button_click(button_name, tool_name, view_name)


def track_error(error_type: str, error_message: str, stack_trace: str = None, tool_name: str = None):
    """Track error (convenience function).
    
    Args:
        error_type: Type of error
        error_message: Error message
        stack_trace: Stack trace
        tool_name: Associated tool name
    """
    if _analytics_system:
        _analytics_system.track_error(error_type, error_message, stack_trace, tool_name)


def start_timer(timer_name: str):
    """Start timer (convenience function).
    
    Args:
        timer_name: Timer name
    """
    if _analytics_system:
        _analytics_system.start_timer(timer_name)


def end_timer(timer_name: str, event_name: str = None, properties: Dict[str, Any] = None):
    """End timer (convenience function).
    
    Args:
        timer_name: Timer name
        event_name: Event name
        properties: Event properties
    """
    if _analytics_system:
        _analytics_system.end_timer(timer_name, event_name, properties)