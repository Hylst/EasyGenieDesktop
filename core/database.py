#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Database Manager

Manages SQLite database operations, schema creation, and data persistence.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
import time


class DatabaseManager:
    """Manages SQLite database operations for Easy Genie Desktop."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.logger = logging.getLogger(__name__)
        
        # Set database path
        if db_path is None:
            app_dir = Path.home() / ".easy_genie"
            app_dir.mkdir(exist_ok=True)
            self.db_path = app_dir / "easy_genie.db"
        else:
            self.db_path = db_path
        
        self.connection = None
        self.lock = threading.Lock()
        self.auto_save_thread = None
        self.auto_save_interval = 30  # seconds
        self.auto_save_running = False
        
        # Database schema version
        self.schema_version = 1
    
    def initialize(self) -> bool:
        """Initialize database connection and create tables."""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            self._create_tables()
            
            # Start auto-save thread
            self._start_auto_save()
            
            self.logger.info(f"Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _create_tables(self):
        """Create all required database tables."""
        with self.lock:
            cursor = self.connection.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT DEFAULT '{}',
                    accessibility_settings TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    parent_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 3,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    category TEXT,
                    tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    due_date TIMESTAMP,
                    quadrant INTEGER,
                    order_index INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (parent_id) REFERENCES tasks (id)
                )
            """)
            
            # Routines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    schedule_type TEXT DEFAULT 'daily',
                    schedule_data TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Routine steps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routine_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    routine_id INTEGER NOT NULL,
                    step_order INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    estimated_duration INTEGER,
                    is_optional BOOLEAN DEFAULT 0,
                    conditions TEXT DEFAULT '{}',
                    FOREIGN KEY (routine_id) REFERENCES routines (id) ON DELETE CASCADE
                )
            """)
            
            # Brain dumps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brain_dumps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    word_count INTEGER DEFAULT 0,
                    character_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT DEFAULT '[]',
                    analysis_data TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Presets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    preset_name TEXT NOT NULL,
                    preset_data TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # History table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_data TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tool_name TEXT,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Focus sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_type TEXT NOT NULL,
                    planned_duration INTEGER NOT NULL,
                    actual_duration INTEGER,
                    goal TEXT,
                    completed BOOLEAN DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks (parent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_routines_user_id ON routines (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_brain_dumps_user_id ON brain_dumps (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON history (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_user_tool ON settings (user_id, tool_name)")
            
            # Create default user if none exists
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                self._create_default_user(cursor)
            
            self.connection.commit()
    
    def _create_default_user(self, cursor):
        """Create default user profile."""
        cursor.execute("""
            INSERT INTO users (username, display_name, preferences)
            VALUES (?, ?, ?)
        """, (
            "default",
            "Utilisateur par défaut",
            json.dumps({
                "theme": "light",
                "font_size": 12,
                "language": "fr"
            })
        ))
        self.logger.info("Default user created")
    
    def _start_auto_save(self):
        """Start auto-save thread."""
        if self.auto_save_thread is None or not self.auto_save_thread.is_alive():
            self.auto_save_running = True
            self.auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
            self.auto_save_thread.start()
            self.logger.info("Auto-save thread started")
    
    def _auto_save_worker(self):
        """Auto-save worker thread."""
        while self.auto_save_running:
            try:
                time.sleep(self.auto_save_interval)
                if self.connection and self.auto_save_running:
                    with self.lock:
                        self.connection.commit()
                    self.logger.debug("Auto-save completed")
            except Exception as e:
                self.logger.error(f"Auto-save error: {e}")
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """Execute an INSERT query and return the new row ID."""
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
    
    # User management methods
    def create_user(self, username: str, display_name: str, preferences: Dict = None) -> Optional[int]:
        """Create a new user profile."""
        try:
            preferences = preferences or {}
            user_id = self.execute_insert(
                "INSERT INTO users (username, display_name, preferences) VALUES (?, ?, ?)",
                (username, display_name, json.dumps(preferences))
            )
            self.logger.info(f"User created: {username} (ID: {user_id})")
            return user_id
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        try:
            rows = self.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
            if rows:
                user = dict(rows[0])
                user['preferences'] = json.loads(user['preferences'])
                user['accessibility_settings'] = json.loads(user['accessibility_settings'])
                return user
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            rows = self.execute_query("SELECT * FROM users WHERE username = ?", (username,))
            if rows:
                user = dict(rows[0])
                user['preferences'] = json.loads(user['preferences'])
                user['accessibility_settings'] = json.loads(user['accessibility_settings'])
                return user
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user by username: {e}")
            return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Update user preferences."""
        try:
            affected = self.execute_update(
                "UPDATE users SET preferences = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(preferences), user_id)
            )
            return affected > 0
        except Exception as e:
            self.logger.error(f"Failed to update user preferences: {e}")
            return False
    
    # Task management methods
    def create_task(self, user_id: int, title: str, **kwargs) -> Optional[int]:
        """Create a new task."""
        try:
            # Prepare task data
            task_data = {
                'user_id': user_id,
                'title': title,
                'description': kwargs.get('description', ''),
                'parent_id': kwargs.get('parent_id'),
                'priority': kwargs.get('priority', 3),
                'category': kwargs.get('category', ''),
                'tags': json.dumps(kwargs.get('tags', [])),
                'quadrant': kwargs.get('quadrant'),
                'estimated_duration': kwargs.get('estimated_duration'),
                'metadata': json.dumps(kwargs.get('metadata', {}))
            }
            
            # Build query dynamically
            columns = [k for k, v in task_data.items() if v is not None]
            values = [task_data[k] for k in columns]
            placeholders = ','.join(['?' for _ in columns])
            
            query = f"INSERT INTO tasks ({','.join(columns)}) VALUES ({placeholders})"
            task_id = self.execute_insert(query, tuple(values))
            
            self.logger.info(f"Task created: {title} (ID: {task_id})")
            return task_id
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            return None
    
    def get_tasks(self, user_id: int, parent_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
        """Get tasks for a user."""
        try:
            query = "SELECT * FROM tasks WHERE user_id = ?"
            params = [user_id]
            
            if parent_id is not None:
                query += " AND parent_id = ?"
                params.append(parent_id)
            else:
                query += " AND parent_id IS NULL"
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY order_index, created_at"
            
            rows = self.execute_query(query, tuple(params))
            tasks = []
            for row in rows:
                task = dict(row)
                task['tags'] = json.loads(task['tags'])
                task['metadata'] = json.loads(task['metadata'])
                tasks.append(task)
            
            return tasks
        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            return []
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update a task."""
        try:
            # Prepare update data
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['tags', 'metadata'] and isinstance(value, (list, dict)):
                    value = json.dumps(value)
                updates.append(f"{key} = ?")
                values.append(value)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(task_id)
            
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            affected = self.execute_update(query, tuple(values))
            
            return affected > 0
        except Exception as e:
            self.logger.error(f"Failed to update task: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task and its subtasks."""
        try:
            # Delete subtasks first
            self.execute_update("DELETE FROM tasks WHERE parent_id = ?", (task_id,))
            # Delete main task
            affected = self.execute_update("DELETE FROM tasks WHERE id = ?", (task_id,))
            return affected > 0
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            return False
    
    # Brain dump methods
    def save_brain_dump(self, user_id: int, content: str, title: str = None, tags: List[str] = None) -> Optional[int]:
        """Save a brain dump entry."""
        try:
            word_count = len(content.split())
            character_count = len(content)
            tags = tags or []
            
            dump_id = self.execute_insert(
                "INSERT INTO brain_dumps (user_id, title, content, word_count, character_count, tags) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, title, content, word_count, character_count, json.dumps(tags))
            )
            
            self.logger.info(f"Brain dump saved (ID: {dump_id})")
            return dump_id
        except Exception as e:
            self.logger.error(f"Failed to save brain dump: {e}")
            return None
    
    def get_brain_dumps(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get brain dumps for a user."""
        try:
            rows = self.execute_query(
                "SELECT * FROM brain_dumps WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit)
            )
            
            dumps = []
            for row in rows:
                dump = dict(row)
                dump['tags'] = json.loads(dump['tags'])
                dump['analysis_data'] = json.loads(dump['analysis_data'])
                dumps.append(dump)
            
            return dumps
        except Exception as e:
            self.logger.error(f"Failed to get brain dumps: {e}")
            return []
    
    # Settings methods
    def save_setting(self, user_id: int, tool_name: str, setting_key: str, setting_value: Any) -> bool:
        """Save a setting value."""
        try:
            # Convert value to string
            if isinstance(setting_value, (dict, list)):
                value_str = json.dumps(setting_value)
            else:
                value_str = str(setting_value)
            
            # Try to update existing setting
            affected = self.execute_update(
                "UPDATE settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND tool_name = ? AND setting_key = ?",
                (value_str, user_id, tool_name, setting_key)
            )
            
            # If no existing setting, insert new one
            if affected == 0:
                self.execute_insert(
                    "INSERT INTO settings (user_id, tool_name, setting_key, setting_value) VALUES (?, ?, ?, ?)",
                    (user_id, tool_name, setting_key, value_str)
                )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save setting: {e}")
            return False
    
    def get_setting(self, user_id: int, tool_name: str, setting_key: str, default_value: Any = None) -> Any:
        """Get a setting value."""
        try:
            rows = self.execute_query(
                "SELECT setting_value FROM settings WHERE user_id = ? AND tool_name = ? AND setting_key = ?",
                (user_id, tool_name, setting_key)
            )
            
            if rows:
                value_str = rows[0]['setting_value']
                # Try to parse as JSON first
                try:
                    return json.loads(value_str)
                except json.JSONDecodeError:
                    return value_str
            
            return default_value
        except Exception as e:
            self.logger.error(f"Failed to get setting: {e}")
            return default_value
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            with self.lock:
                backup_conn = sqlite3.connect(backup_path)
                self.connection.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False
    
    def close(self):
        """Close database connection and stop auto-save."""
        self.auto_save_running = False
        
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            self.auto_save_thread.join(timeout=5)
        
        if self.connection:
            with self.lock:
                self.connection.commit()
                self.connection.close()
            self.logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()