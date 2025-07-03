"""Context Manager for AI Service.

This module manages conversation context, user sessions, and contextual information
to provide personalized and coherent AI interactions across different tools.
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import sqlite3
import threading
from pathlib import Path


class ContextType(Enum):
    """Types of context information."""
    USER_PREFERENCE = "user_preference"
    CONVERSATION = "conversation"
    TASK_HISTORY = "task_history"
    TOOL_USAGE = "tool_usage"
    SESSION = "session"
    GLOBAL = "global"


class ContextScope(Enum):
    """Scope of context information."""
    SESSION = "session"  # Current session only
    DAILY = "daily"     # Current day
    WEEKLY = "weekly"   # Current week
    MONTHLY = "monthly" # Current month
    PERSISTENT = "persistent"  # Permanent storage


@dataclass
class ContextEntry:
    """Individual context entry."""
    id: str
    context_type: ContextType
    scope: ContextScope
    tool_name: str
    operation: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: str
    session_id: str
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['context_type'] = self.context_type.value
        result['scope'] = self.scope.value
        result['timestamp'] = self.timestamp.isoformat()
        if self.last_accessed:
            result['last_accessed'] = self.last_accessed.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEntry':
        """Create from dictionary."""
        data['context_type'] = ContextType(data['context_type'])
        data['scope'] = ContextScope(data['scope'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('last_accessed'):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    turn_id: str
    user_input: str
    ai_response: str
    tool_name: str
    operation: str
    timestamp: datetime
    context_used: List[str]  # IDs of context entries used
    feedback_score: Optional[float] = None
    

@dataclass
class UserSession:
    """User session information."""
    session_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    tools_used: List[str]
    operations_performed: List[str]
    conversation_turns: List[ConversationTurn]
    session_goals: List[str]
    productivity_metrics: Dict[str, Any]
    

class ContextManager:
    """Manages context information for personalized AI interactions."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the context manager.
        
        Args:
            db_path: Path to the context database file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Database setup
        if db_path is None:
            db_path = Path.home() / ".easy_genie" / "context.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # In-memory caches
        self.active_sessions: Dict[str, UserSession] = {}
        self.context_cache: Dict[str, ContextEntry] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_context_entries = 10000
        self.max_conversation_turns = 1000
        self.context_relevance_threshold = 0.3
        self.session_timeout = timedelta(hours=2)
        
        # Initialize database
        self._init_database()
        
        # Load recent context
        self._load_recent_context()
    
    def _init_database(self):
        """Initialize the context database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_entries (
                    id TEXT PRIMARY KEY,
                    context_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    relevance_score REAL DEFAULT 1.0,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    tools_used TEXT NOT NULL,
                    operations_performed TEXT NOT NULL,
                    conversation_turns TEXT NOT NULL,
                    session_goals TEXT NOT NULL,
                    productivity_metrics TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_user_tool ON context_entries(user_id, tool_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_timestamp ON context_entries(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_relevance ON context_entries(relevance_score)")
    
    def _load_recent_context(self):
        """Load recent context entries into memory cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load context entries from the last 24 hours
                cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
                
                cursor = conn.execute("""
                    SELECT * FROM context_entries 
                    WHERE timestamp > ? 
                    ORDER BY relevance_score DESC, timestamp DESC 
                    LIMIT 1000
                """, (cutoff_time,))
                
                for row in cursor.fetchall():
                    entry_data = {
                        'id': row[0],
                        'context_type': row[1],
                        'scope': row[2],
                        'tool_name': row[3],
                        'operation': row[4],
                        'data': json.loads(row[5]),
                        'timestamp': row[6],
                        'user_id': row[7],
                        'session_id': row[8],
                        'relevance_score': row[9],
                        'access_count': row[10],
                        'last_accessed': row[11]
                    }
                    
                    entry = ContextEntry.from_dict(entry_data)
                    self.context_cache[entry.id] = entry
                
                # Load user preferences
                cursor = conn.execute("SELECT user_id, preferences FROM user_preferences")
                for user_id, preferences_json in cursor.fetchall():
                    self.user_preferences[user_id] = json.loads(preferences_json)
                    
        except Exception as e:
            self.logger.error(f"Error loading recent context: {e}")
    
    def start_session(self, user_id: str, session_goals: List[str] = None) -> str:
        """Start a new user session.
        
        Args:
            user_id: The user identifier
            session_goals: Optional list of session goals
            
        Returns:
            str: The session ID
        """
        with self._lock:
            session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                tools_used=[],
                operations_performed=[],
                conversation_turns=[],
                session_goals=session_goals or [],
                productivity_metrics={}
            )
            
            self.active_sessions[session_id] = session
            
            self.logger.info(f"Started session {session_id} for user {user_id}")
            return session_id
    
    def end_session(self, session_id: str):
        """End a user session and save to database.
        
        Args:
            session_id: The session to end
        """
        with self._lock:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session {session_id} not found")
                return
            
            session = self.active_sessions[session_id]
            
            # Save session to database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO user_sessions 
                        (session_id, user_id, start_time, last_activity, tools_used, 
                         operations_performed, conversation_turns, session_goals, productivity_metrics)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session.session_id,
                        session.user_id,
                        session.start_time.isoformat(),
                        session.last_activity.isoformat(),
                        json.dumps(session.tools_used),
                        json.dumps(session.operations_performed),
                        json.dumps([asdict(turn) for turn in session.conversation_turns]),
                        json.dumps(session.session_goals),
                        json.dumps(session.productivity_metrics)
                    ))
                
                del self.active_sessions[session_id]
                self.logger.info(f"Ended session {session_id}")
                
            except Exception as e:
                self.logger.error(f"Error saving session {session_id}: {e}")
    
    def add_context(
        self,
        context_type: ContextType,
        scope: ContextScope,
        tool_name: str,
        operation: str,
        data: Dict[str, Any],
        user_id: str,
        session_id: str,
        relevance_score: float = 1.0
    ) -> str:
        """Add a new context entry.
        
        Args:
            context_type: Type of context
            scope: Scope of the context
            tool_name: Name of the tool
            operation: Operation being performed
            data: Context data
            user_id: User identifier
            session_id: Session identifier
            relevance_score: Relevance score (0.0 to 1.0)
            
        Returns:
            str: The context entry ID
        """
        with self._lock:
            entry_id = f"{context_type.value}_{tool_name}_{operation}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            entry = ContextEntry(
                id=entry_id,
                context_type=context_type,
                scope=scope,
                tool_name=tool_name,
                operation=operation,
                data=data,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                relevance_score=relevance_score
            )
            
            # Add to cache
            self.context_cache[entry_id] = entry
            
            # Save to database for persistent scopes
            if scope in [ContextScope.PERSISTENT, ContextScope.MONTHLY, ContextScope.WEEKLY]:
                self._save_context_entry(entry)
            
            # Update session activity
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.last_activity = datetime.now()
                
                if tool_name not in session.tools_used:
                    session.tools_used.append(tool_name)
                
                if operation not in session.operations_performed:
                    session.operations_performed.append(operation)
            
            # Clean up old entries if cache is too large
            self._cleanup_cache()
            
            return entry_id
    
    def get_relevant_context(
        self,
        tool_name: str,
        operation: str,
        user_id: str,
        session_id: str,
        max_entries: int = 10
    ) -> List[ContextEntry]:
        """Get relevant context entries for a request.
        
        Args:
            tool_name: Name of the tool
            operation: Operation being performed
            user_id: User identifier
            session_id: Session identifier
            max_entries: Maximum number of entries to return
            
        Returns:
            List[ContextEntry]: Relevant context entries
        """
        with self._lock:
            relevant_entries = []
            
            # Score and filter context entries
            for entry in self.context_cache.values():
                if entry.user_id != user_id:
                    continue
                
                # Calculate relevance score
                score = self._calculate_relevance_score(
                    entry, tool_name, operation, session_id
                )
                
                if score >= self.context_relevance_threshold:
                    entry.relevance_score = score
                    relevant_entries.append(entry)
                    
                    # Update access statistics
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
            
            # Sort by relevance score and recency
            relevant_entries.sort(
                key=lambda x: (x.relevance_score, x.timestamp),
                reverse=True
            )
            
            return relevant_entries[:max_entries]
    
    def _calculate_relevance_score(
        self,
        entry: ContextEntry,
        tool_name: str,
        operation: str,
        session_id: str
    ) -> float:
        """Calculate relevance score for a context entry.
        
        Args:
            entry: The context entry
            tool_name: Current tool name
            operation: Current operation
            session_id: Current session ID
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Tool match bonus
        if entry.tool_name == tool_name:
            score += 0.4
        
        # Operation match bonus
        if entry.operation == operation:
            score += 0.3
        
        # Session match bonus
        if entry.session_id == session_id:
            score += 0.2
        
        # Recency bonus (decay over time)
        time_diff = datetime.now() - entry.timestamp
        if time_diff < timedelta(minutes=30):
            score += 0.3
        elif time_diff < timedelta(hours=2):
            score += 0.2
        elif time_diff < timedelta(hours=24):
            score += 0.1
        
        # Access frequency bonus
        if entry.access_count > 5:
            score += 0.1
        elif entry.access_count > 2:
            score += 0.05
        
        # Context type bonuses
        if entry.context_type == ContextType.USER_PREFERENCE:
            score += 0.2
        elif entry.context_type == ContextType.TASK_HISTORY:
            score += 0.15
        
        return min(score, 1.0)
    
    def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """Update user preferences.
        
        Args:
            user_id: User identifier
            preferences: User preferences dictionary
        """
        with self._lock:
            self.user_preferences[user_id] = preferences
            
            # Save to database
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO user_preferences 
                        (user_id, preferences, last_updated)
                        VALUES (?, ?, ?)
                    """, (
                        user_id,
                        json.dumps(preferences),
                        datetime.now().isoformat()
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error saving user preferences: {e}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict[str, Any]: User preferences
        """
        return self.user_preferences.get(user_id, {})
    
    def add_conversation_turn(
        self,
        session_id: str,
        user_input: str,
        ai_response: str,
        tool_name: str,
        operation: str,
        context_used: List[str]
    ) -> str:
        """Add a conversation turn to the session.
        
        Args:
            session_id: Session identifier
            user_input: User's input
            ai_response: AI's response
            tool_name: Tool used
            operation: Operation performed
            context_used: List of context entry IDs used
            
        Returns:
            str: Turn ID
        """
        with self._lock:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session {session_id} not found")
                return ""
            
            turn_id = f"{session_id}_turn_{len(self.active_sessions[session_id].conversation_turns)}"
            
            turn = ConversationTurn(
                turn_id=turn_id,
                user_input=user_input,
                ai_response=ai_response,
                tool_name=tool_name,
                operation=operation,
                timestamp=datetime.now(),
                context_used=context_used
            )
            
            self.active_sessions[session_id].conversation_turns.append(turn)
            
            # Limit conversation history
            if len(self.active_sessions[session_id].conversation_turns) > self.max_conversation_turns:
                self.active_sessions[session_id].conversation_turns = \
                    self.active_sessions[session_id].conversation_turns[-self.max_conversation_turns:]
            
            return turn_id
    
    def get_conversation_history(
        self,
        session_id: str,
        max_turns: int = 10
    ) -> List[ConversationTurn]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of turns to return
            
        Returns:
            List[ConversationTurn]: Conversation history
        """
        with self._lock:
            if session_id not in self.active_sessions:
                return []
            
            turns = self.active_sessions[session_id].conversation_turns
            return turns[-max_turns:] if len(turns) > max_turns else turns
    
    def _save_context_entry(self, entry: ContextEntry):
        """Save context entry to database.
        
        Args:
            entry: Context entry to save
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO context_entries 
                    (id, context_type, scope, tool_name, operation, data, timestamp, 
                     user_id, session_id, relevance_score, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id,
                    entry.context_type.value,
                    entry.scope.value,
                    entry.tool_name,
                    entry.operation,
                    json.dumps(entry.data),
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.session_id,
                    entry.relevance_score,
                    entry.access_count,
                    entry.last_accessed.isoformat() if entry.last_accessed else None
                ))
                
        except Exception as e:
            self.logger.error(f"Error saving context entry: {e}")
    
    def _cleanup_cache(self):
        """Clean up the context cache to maintain size limits."""
        if len(self.context_cache) <= self.max_context_entries:
            return
        
        # Sort by relevance score and last accessed time
        entries = list(self.context_cache.values())
        entries.sort(
            key=lambda x: (x.relevance_score, x.last_accessed or x.timestamp),
            reverse=True
        )
        
        # Keep only the most relevant entries
        entries_to_keep = entries[:int(self.max_context_entries * 0.8)]
        
        # Update cache
        self.context_cache = {entry.id: entry for entry in entries_to_keep}
        
        self.logger.info(f"Cleaned up context cache, kept {len(entries_to_keep)} entries")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old context data from database.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete old context entries (except persistent ones)
                conn.execute("""
                    DELETE FROM context_entries 
                    WHERE timestamp < ? AND scope != ?
                """, (cutoff_date.isoformat(), ContextScope.PERSISTENT.value))
                
                # Delete old sessions
                conn.execute("""
                    DELETE FROM user_sessions 
                    WHERE last_activity < ?
                """, (cutoff_date.isoformat(),))
                
                conn.commit()
                
            self.logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get context manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics about context usage
        """
        with self._lock:
            stats = {
                "cache_size": len(self.context_cache),
                "active_sessions": len(self.active_sessions),
                "user_preferences_count": len(self.user_preferences),
                "context_types": {},
                "tools_used": {},
                "operations_performed": {}
            }
            
            # Analyze context entries
            for entry in self.context_cache.values():
                # Count by context type
                context_type = entry.context_type.value
                stats["context_types"][context_type] = stats["context_types"].get(context_type, 0) + 1
                
                # Count by tool
                tool_name = entry.tool_name
                stats["tools_used"][tool_name] = stats["tools_used"].get(tool_name, 0) + 1
                
                # Count by operation
                operation = entry.operation
                stats["operations_performed"][operation] = stats["operations_performed"].get(operation, 0) + 1
            
            return stats