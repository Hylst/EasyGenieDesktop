"""Database System for Data Persistence and Management.

This module provides comprehensive database capabilities including SQLite operations,
data models, migrations, and query management for the application.
"""

import sqlite3
import json
import threading
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Type
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
import hashlib
import uuid
from contextlib import contextmanager


class DatabaseType(Enum):
    """Database types."""
    SQLITE = "sqlite"
    MEMORY = "memory"


class QueryType(Enum):
    """Query types."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"


class IndexType(Enum):
    """Index types."""
    UNIQUE = "unique"
    NORMAL = "normal"
    COMPOSITE = "composite"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    # Connection settings
    database_type: DatabaseType = DatabaseType.SQLITE
    database_path: Path = Path("app_data.db")
    
    # Connection pool settings
    max_connections: int = 10
    connection_timeout: float = 30.0
    
    # Performance settings
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    cache_size: int = 2000  # Pages
    
    # Backup settings
    auto_backup: bool = True
    backup_interval: int = 3600  # seconds
    backup_directory: Path = Path("backups")
    max_backups: int = 10
    
    # Security settings
    enable_encryption: bool = False
    encryption_key: str = ""
    
    # Logging settings
    log_queries: bool = False
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0  # seconds


@dataclass
class TableSchema:
    """Database table schema."""
    name: str
    columns: Dict[str, str]  # column_name: column_type
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # column: (table, column)
    indexes: Dict[str, Tuple[IndexType, List[str]]] = field(default_factory=dict)  # name: (type, columns)
    constraints: List[str] = field(default_factory=list)
    
    def get_create_sql(self) -> str:
        """Generate CREATE TABLE SQL.
        
        Returns:
            str: CREATE TABLE statement
        """
        columns_sql = []
        
        # Add columns
        for col_name, col_type in self.columns.items():
            column_def = f"{col_name} {col_type}"
            columns_sql.append(column_def)
        
        # Add primary key
        if self.primary_key:
            pk_sql = f"PRIMARY KEY ({', '.join(self.primary_key)})"
            columns_sql.append(pk_sql)
        
        # Add foreign keys
        for col, (ref_table, ref_col) in self.foreign_keys.items():
            fk_sql = f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
            columns_sql.append(fk_sql)
        
        # Add constraints
        columns_sql.extend(self.constraints)
        
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n  {',\n  '.join(columns_sql)}\n)"


@dataclass
class QueryResult:
    """Query execution result."""
    success: bool = False
    rows_affected: int = 0
    data: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    execution_time: float = 0.0
    query_type: Optional[QueryType] = None
    
    # Metadata
    query_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Migration:
    """Database migration."""
    version: int
    name: str
    up_sql: str
    down_sql: str = ""
    description: str = ""
    applied_at: Optional[datetime] = None
    
    def get_hash(self) -> str:
        """Get migration hash.
        
        Returns:
            str: Migration hash
        """
        content = f"{self.version}:{self.name}:{self.up_sql}"
        return hashlib.md5(content.encode()).hexdigest()


class BaseModel:
    """Base model class for database entities."""
    
    def __init__(self, **kwargs):
        """Initialize model with data.
        
        Args:
            **kwargs: Model data
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get table name for model.
        
        Returns:
            str: Table name
        """
        return cls.__name__.lower() + 's'
    
    @classmethod
    def get_schema(cls) -> TableSchema:
        """Get table schema for model.
        
        Returns:
            TableSchema: Table schema
        """
        raise NotImplementedError("Subclasses must implement get_schema")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Model data
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model from dictionary.
        
        Args:
            data: Model data
            
        Returns:
            BaseModel: Model instance
        """
        return cls(**data)


class UserSession(BaseModel):
    """User session model."""
    
    def __init__(self, **kwargs):
        """Initialize user session."""
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.session_data = kwargs.get('session_data', '{}')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.expires_at = kwargs.get('expires_at', datetime.now() + timedelta(days=30))
        self.is_active = kwargs.get('is_active', True)
    
    @classmethod
    def get_schema(cls) -> TableSchema:
        """Get user session schema.
        
        Returns:
            TableSchema: Schema definition
        """
        return TableSchema(
            name='user_sessions',
            columns={
                'id': 'TEXT PRIMARY KEY',
                'user_id': 'TEXT NOT NULL',
                'session_data': 'TEXT',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'expires_at': 'TIMESTAMP',
                'is_active': 'BOOLEAN DEFAULT 1'
            },
            indexes={
                'idx_user_sessions_user_id': (IndexType.NORMAL, ['user_id']),
                'idx_user_sessions_expires': (IndexType.NORMAL, ['expires_at'])
            }
        )


class ToolData(BaseModel):
    """Tool data model."""
    
    def __init__(self, **kwargs):
        """Initialize tool data."""
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.tool_name = kwargs.get('tool_name', '')
        self.user_id = kwargs.get('user_id', '')
        self.data_type = kwargs.get('data_type', '')
        self.data_content = kwargs.get('data_content', '{}')
        self.metadata = kwargs.get('metadata', '{}')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.is_deleted = kwargs.get('is_deleted', False)
    
    @classmethod
    def get_schema(cls) -> TableSchema:
        """Get tool data schema.
        
        Returns:
            TableSchema: Schema definition
        """
        return TableSchema(
            name='tool_data',
            columns={
                'id': 'TEXT PRIMARY KEY',
                'tool_name': 'TEXT NOT NULL',
                'user_id': 'TEXT NOT NULL',
                'data_type': 'TEXT NOT NULL',
                'data_content': 'TEXT',
                'metadata': 'TEXT',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'is_deleted': 'BOOLEAN DEFAULT 0'
            },
            indexes={
                'idx_tool_data_tool_user': (IndexType.COMPOSITE, ['tool_name', 'user_id']),
                'idx_tool_data_created': (IndexType.NORMAL, ['created_at']),
                'idx_tool_data_type': (IndexType.NORMAL, ['data_type'])
            }
        )


class AIInteraction(BaseModel):
    """AI interaction model."""
    
    def __init__(self, **kwargs):
        """Initialize AI interaction."""
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.session_id = kwargs.get('session_id', '')
        self.tool_name = kwargs.get('tool_name', '')
        self.prompt = kwargs.get('prompt', '')
        self.response = kwargs.get('response', '')
        self.provider = kwargs.get('provider', '')
        self.model = kwargs.get('model', '')
        self.tokens_used = kwargs.get('tokens_used', 0)
        self.response_time = kwargs.get('response_time', 0.0)
        self.quality_score = kwargs.get('quality_score', 0.0)
        self.user_feedback = kwargs.get('user_feedback', '')
        self.created_at = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_schema(cls) -> TableSchema:
        """Get AI interaction schema.
        
        Returns:
            TableSchema: Schema definition
        """
        return TableSchema(
            name='ai_interactions',
            columns={
                'id': 'TEXT PRIMARY KEY',
                'session_id': 'TEXT',
                'tool_name': 'TEXT',
                'prompt': 'TEXT',
                'response': 'TEXT',
                'provider': 'TEXT',
                'model': 'TEXT',
                'tokens_used': 'INTEGER DEFAULT 0',
                'response_time': 'REAL DEFAULT 0.0',
                'quality_score': 'REAL DEFAULT 0.0',
                'user_feedback': 'TEXT',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            },
            foreign_keys={
                'session_id': ('user_sessions', 'id')
            },
            indexes={
                'idx_ai_interactions_session': (IndexType.NORMAL, ['session_id']),
                'idx_ai_interactions_tool': (IndexType.NORMAL, ['tool_name']),
                'idx_ai_interactions_created': (IndexType.NORMAL, ['created_at'])
            }
        )


class AppSettings(BaseModel):
    """Application settings model."""
    
    def __init__(self, **kwargs):
        """Initialize app settings."""
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.category = kwargs.get('category', '')
        self.key = kwargs.get('key', '')
        self.value = kwargs.get('value', '')
        self.data_type = kwargs.get('data_type', 'string')
        self.description = kwargs.get('description', '')
        self.is_user_configurable = kwargs.get('is_user_configurable', True)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    @classmethod
    def get_schema(cls) -> TableSchema:
        """Get app settings schema.
        
        Returns:
            TableSchema: Schema definition
        """
        return TableSchema(
            name='app_settings',
            columns={
                'id': 'TEXT PRIMARY KEY',
                'category': 'TEXT NOT NULL',
                'key': 'TEXT NOT NULL',
                'value': 'TEXT',
                'data_type': 'TEXT DEFAULT "string"',
                'description': 'TEXT',
                'is_user_configurable': 'BOOLEAN DEFAULT 1',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            },
            indexes={
                'idx_app_settings_category_key': (IndexType.UNIQUE, ['category', 'key']),
                'idx_app_settings_category': (IndexType.NORMAL, ['category'])
            }
        )


class DatabaseConnection:
    """Database connection wrapper."""
    
    def __init__(self, database_path: Path, config: DatabaseConfig):
        """Initialize database connection.
        
        Args:
            database_path: Path to database file
            config: Database configuration
        """
        self.database_path = database_path
        self.config = config
        self.connection: Optional[sqlite3.Connection] = None
        self.lock = threading.Lock()
        
        # Query statistics
        self.query_count = 0
        self.total_execution_time = 0.0
        self.slow_queries = []
    
    def connect(self) -> bool:
        """Establish database connection.
        
        Returns:
            bool: True if connected successfully
        """
        try:
            with self.lock:
                if self.connection:
                    return True
                
                # Create database directory if needed
                self.database_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Connect to database
                self.connection = sqlite3.connect(
                    str(self.database_path),
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                
                # Configure connection
                self.connection.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                if self.config.enable_wal_mode:
                    self.connection.execute("PRAGMA journal_mode=WAL")
                
                # Enable foreign keys
                if self.config.enable_foreign_keys:
                    self.connection.execute("PRAGMA foreign_keys=ON")
                
                # Set cache size
                self.connection.execute(f"PRAGMA cache_size={self.config.cache_size}")
                
                return True
                
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        with self.lock:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def execute_query(self, query: str, params: Tuple = ()) -> QueryResult:
        """Execute database query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            QueryResult: Query execution result
        """
        result = QueryResult()
        start_time = datetime.now()
        
        try:
            with self.lock:
                if not self.connection:
                    if not self.connect():
                        result.error_message = "Database connection failed"
                        return result
                
                cursor = self.connection.cursor()
                
                # Execute query
                cursor.execute(query, params)
                
                # Determine query type
                query_lower = query.strip().lower()
                if query_lower.startswith('select'):
                    result.query_type = QueryType.SELECT
                    result.data = [dict(row) for row in cursor.fetchall()]
                elif query_lower.startswith('insert'):
                    result.query_type = QueryType.INSERT
                    result.rows_affected = cursor.rowcount
                elif query_lower.startswith('update'):
                    result.query_type = QueryType.UPDATE
                    result.rows_affected = cursor.rowcount
                elif query_lower.startswith('delete'):
                    result.query_type = QueryType.DELETE
                    result.rows_affected = cursor.rowcount
                else:
                    result.query_type = QueryType.CREATE
                    result.rows_affected = cursor.rowcount
                
                self.connection.commit()
                result.success = True
                
        except Exception as e:
            result.error_message = str(e)
            if self.connection:
                self.connection.rollback()
            logging.error(f"Query execution error: {e}")
        
        # Calculate execution time
        end_time = datetime.now()
        result.execution_time = (end_time - start_time).total_seconds()
        result.timestamp = start_time
        
        # Generate query hash
        result.query_hash = hashlib.md5(f"{query}:{params}".encode()).hexdigest()
        
        # Update statistics
        self.query_count += 1
        self.total_execution_time += result.execution_time
        
        # Log slow queries
        if (self.config.log_slow_queries and 
            result.execution_time > self.config.slow_query_threshold):
            self.slow_queries.append({
                'query': query,
                'params': params,
                'execution_time': result.execution_time,
                'timestamp': start_time
            })
        
        # Log queries if enabled
        if self.config.log_queries:
            logging.info(f"Query executed: {query[:100]}... ({result.execution_time:.3f}s)")
        
        return result
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> QueryResult:
        """Execute query with multiple parameter sets.
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
            
        Returns:
            QueryResult: Query execution result
        """
        result = QueryResult()
        start_time = datetime.now()
        
        try:
            with self.lock:
                if not self.connection:
                    if not self.connect():
                        result.error_message = "Database connection failed"
                        return result
                
                cursor = self.connection.cursor()
                cursor.executemany(query, params_list)
                
                result.rows_affected = cursor.rowcount
                self.connection.commit()
                result.success = True
                
        except Exception as e:
            result.error_message = str(e)
            if self.connection:
                self.connection.rollback()
            logging.error(f"Batch query execution error: {e}")
        
        # Calculate execution time
        end_time = datetime.now()
        result.execution_time = (end_time - start_time).total_seconds()
        result.timestamp = start_time
        
        return result
    
    @contextmanager
    def transaction(self):
        """Database transaction context manager."""
        with self.lock:
            if not self.connection:
                if not self.connect():
                    raise Exception("Database connection failed")
            
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        avg_time = (self.total_execution_time / self.query_count 
                   if self.query_count > 0 else 0.0)
        
        return {
            'query_count': self.query_count,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': avg_time,
            'slow_queries_count': len(self.slow_queries),
            'connection_active': self.connection is not None
        }


class MigrationManager:
    """Database migration manager."""
    
    def __init__(self, connection: DatabaseConnection):
        """Initialize migration manager.
        
        Args:
            connection: Database connection
        """
        self.connection = connection
        self.migrations: List[Migration] = []
        
        # Ensure migrations table exists
        self._create_migrations_table()
    
    def _create_migrations_table(self):
        """Create migrations tracking table."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            hash TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.connection.execute_query(create_sql)
    
    def add_migration(self, migration: Migration):
        """Add migration to manager.
        
        Args:
            migration: Migration to add
        """
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[int]:
        """Get list of applied migration versions.
        
        Returns:
            List[int]: Applied migration versions
        """
        result = self.connection.execute_query(
            "SELECT version FROM migrations ORDER BY version"
        )
        
        if result.success:
            return [row['version'] for row in result.data]
        return []
    
    def apply_migrations(self) -> bool:
        """Apply pending migrations.
        
        Returns:
            bool: True if all migrations applied successfully
        """
        applied_versions = set(self.get_applied_migrations())
        pending_migrations = [m for m in self.migrations if m.version not in applied_versions]
        
        if not pending_migrations:
            logging.info("No pending migrations")
            return True
        
        for migration in pending_migrations:
            if not self._apply_migration(migration):
                logging.error(f"Failed to apply migration {migration.version}: {migration.name}")
                return False
            
            logging.info(f"Applied migration {migration.version}: {migration.name}")
        
        return True
    
    def _apply_migration(self, migration: Migration) -> bool:
        """Apply single migration.
        
        Args:
            migration: Migration to apply
            
        Returns:
            bool: True if applied successfully
        """
        try:
            with self.connection.transaction():
                # Execute migration SQL
                result = self.connection.execute_query(migration.up_sql)
                if not result.success:
                    return False
                
                # Record migration
                record_sql = """
                INSERT INTO migrations (version, name, hash, applied_at)
                VALUES (?, ?, ?, ?)
                """
                
                record_result = self.connection.execute_query(
                    record_sql,
                    (migration.version, migration.name, migration.get_hash(), datetime.now())
                )
                
                return record_result.success
                
        except Exception as e:
            logging.error(f"Migration application error: {e}")
            return False
    
    def rollback_migration(self, version: int) -> bool:
        """Rollback specific migration.
        
        Args:
            version: Migration version to rollback
            
        Returns:
            bool: True if rolled back successfully
        """
        migration = next((m for m in self.migrations if m.version == version), None)
        if not migration:
            logging.error(f"Migration {version} not found")
            return False
        
        if not migration.down_sql:
            logging.error(f"Migration {version} has no rollback SQL")
            return False
        
        try:
            with self.connection.transaction():
                # Execute rollback SQL
                result = self.connection.execute_query(migration.down_sql)
                if not result.success:
                    return False
                
                # Remove migration record
                delete_sql = "DELETE FROM migrations WHERE version = ?"
                delete_result = self.connection.execute_query(delete_sql, (version,))
                
                return delete_result.success
                
        except Exception as e:
            logging.error(f"Migration rollback error: {e}")
            return False


class DatabaseSystem:
    """Main database system manager."""
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database system.
        
        Args:
            config: Database configuration
        """
        self.config = config or DatabaseConfig()
        self.connection = DatabaseConnection(self.config.database_path, self.config)
        self.migration_manager = MigrationManager(self.connection)
        
        # Model registry
        self.models: Dict[str, Type[BaseModel]] = {
            'user_sessions': UserSession,
            'tool_data': ToolData,
            'ai_interactions': AIInteraction,
            'app_settings': AppSettings
        }
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schemas and migrations."""
        # Connect to database
        if not self.connection.connect():
            raise Exception("Failed to connect to database")
        
        # Create initial migrations
        self._create_initial_migrations()
        
        # Apply migrations
        self.migration_manager.apply_migrations()
    
    def _create_initial_migrations(self):
        """Create initial database migrations."""
        # Migration 1: Create core tables
        migration_1 = Migration(
            version=1,
            name="create_core_tables",
            description="Create core application tables",
            up_sql=self._get_initial_schema_sql()
        )
        self.migration_manager.add_migration(migration_1)
        
        # Migration 2: Add indexes
        migration_2 = Migration(
            version=2,
            name="add_indexes",
            description="Add database indexes for performance",
            up_sql=self._get_indexes_sql()
        )
        self.migration_manager.add_migration(migration_2)
    
    def _get_initial_schema_sql(self) -> str:
        """Get initial schema SQL.
        
        Returns:
            str: Schema creation SQL
        """
        sql_statements = []
        
        for model_class in self.models.values():
            schema = model_class.get_schema()
            sql_statements.append(schema.get_create_sql())
        
        return ";\n\n".join(sql_statements) + ";"
    
    def _get_indexes_sql(self) -> str:
        """Get indexes creation SQL.
        
        Returns:
            str: Index creation SQL
        """
        sql_statements = []
        
        for model_class in self.models.values():
            schema = model_class.get_schema()
            
            for index_name, (index_type, columns) in schema.indexes.items():
                unique_clause = "UNIQUE " if index_type == IndexType.UNIQUE else ""
                columns_clause = ", ".join(columns)
                
                index_sql = f"CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} ON {schema.name} ({columns_clause})"
                sql_statements.append(index_sql)
        
        return ";\n".join(sql_statements) + ";" if sql_statements else ""
    
    def register_model(self, name: str, model_class: Type[BaseModel]):
        """Register custom model.
        
        Args:
            name: Model name
            model_class: Model class
        """
        self.models[name] = model_class
    
    def create_record(self, model_name: str, data: Dict[str, Any]) -> Optional[str]:
        """Create new record.
        
        Args:
            model_name: Model name
            data: Record data
            
        Returns:
            Optional[str]: Record ID if created successfully
        """
        if model_name not in self.models:
            logging.error(f"Unknown model: {model_name}")
            return None
        
        model_class = self.models[model_name]
        schema = model_class.get_schema()
        
        # Prepare data
        record = model_class(**data)
        record_data = record.to_dict()
        
        # Build INSERT query
        columns = list(record_data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = [record_data[col] for col in columns]
        
        insert_sql = f"INSERT INTO {schema.name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        result = self.connection.execute_query(insert_sql, tuple(values))
        
        if result.success:
            return record_data.get('id')
        else:
            logging.error(f"Failed to create record: {result.error_message}")
            return None
    
    def get_record(self, model_name: str, record_id: str) -> Optional[BaseModel]:
        """Get record by ID.
        
        Args:
            model_name: Model name
            record_id: Record ID
            
        Returns:
            Optional[BaseModel]: Record if found
        """
        if model_name not in self.models:
            return None
        
        model_class = self.models[model_name]
        schema = model_class.get_schema()
        
        select_sql = f"SELECT * FROM {schema.name} WHERE id = ?"
        result = self.connection.execute_query(select_sql, (record_id,))
        
        if result.success and result.data:
            return model_class.from_dict(result.data[0])
        
        return None
    
    def update_record(self, model_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update record.
        
        Args:
            model_name: Model name
            record_id: Record ID
            data: Updated data
            
        Returns:
            bool: True if updated successfully
        """
        if model_name not in self.models:
            return False
        
        model_class = self.models[model_name]
        schema = model_class.get_schema()
        
        # Add updated_at timestamp if column exists
        if 'updated_at' in schema.columns:
            data['updated_at'] = datetime.now()
        
        # Build UPDATE query
        set_clauses = [f"{col} = ?" for col in data.keys()]
        values = list(data.values()) + [record_id]
        
        update_sql = f"UPDATE {schema.name} SET {', '.join(set_clauses)} WHERE id = ?"
        
        result = self.connection.execute_query(update_sql, tuple(values))
        return result.success and result.rows_affected > 0
    
    def delete_record(self, model_name: str, record_id: str, soft_delete: bool = True) -> bool:
        """Delete record.
        
        Args:
            model_name: Model name
            record_id: Record ID
            soft_delete: Use soft delete if available
            
        Returns:
            bool: True if deleted successfully
        """
        if model_name not in self.models:
            return False
        
        model_class = self.models[model_name]
        schema = model_class.get_schema()
        
        # Check for soft delete support
        if soft_delete and 'is_deleted' in schema.columns:
            return self.update_record(model_name, record_id, {'is_deleted': True})
        else:
            # Hard delete
            delete_sql = f"DELETE FROM {schema.name} WHERE id = ?"
            result = self.connection.execute_query(delete_sql, (record_id,))
            return result.success and result.rows_affected > 0
    
    def query_records(self, model_name: str, conditions: Dict[str, Any] = None, 
                     limit: int = None, offset: int = None, 
                     order_by: str = None) -> List[BaseModel]:
        """Query records with conditions.
        
        Args:
            model_name: Model name
            conditions: Query conditions
            limit: Result limit
            offset: Result offset
            order_by: Order by clause
            
        Returns:
            List[BaseModel]: Matching records
        """
        if model_name not in self.models:
            return []
        
        model_class = self.models[model_name]
        schema = model_class.get_schema()
        
        # Build query
        query_parts = [f"SELECT * FROM {schema.name}"]
        params = []
        
        # Add conditions
        if conditions:
            where_clauses = []
            for col, value in conditions.items():
                if isinstance(value, (list, tuple)):
                    placeholders = ", ".join(["?" for _ in value])
                    where_clauses.append(f"{col} IN ({placeholders})")
                    params.extend(value)
                else:
                    where_clauses.append(f"{col} = ?")
                    params.append(value)
            
            if where_clauses:
                query_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # Add ordering
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        # Add limit and offset
        if limit:
            query_parts.append(f"LIMIT {limit}")
            if offset:
                query_parts.append(f"OFFSET {offset}")
        
        query = " ".join(query_parts)
        result = self.connection.execute_query(query, tuple(params))
        
        if result.success:
            return [model_class.from_dict(row) for row in result.data]
        
        return []
    
    def execute_raw_query(self, query: str, params: Tuple = ()) -> QueryResult:
        """Execute raw SQL query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            QueryResult: Query result
        """
        return self.connection.execute_query(query, params)
    
    def backup_database(self, backup_path: Path = None) -> bool:
        """Create database backup.
        
        Args:
            backup_path: Backup file path
            
        Returns:
            bool: True if backup created successfully
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"backup_{timestamp}.db"
                backup_path = self.config.backup_directory / backup_filename
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup using SQLite backup API
            with sqlite3.connect(str(backup_path)) as backup_conn:
                self.connection.connection.backup(backup_conn)
            
            logging.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Database backup error: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dict[str, Any]: Database statistics
        """
        stats = self.connection.get_statistics()
        
        # Add table statistics
        table_stats = {}
        for model_name, model_class in self.models.items():
            schema = model_class.get_schema()
            count_result = self.connection.execute_query(
                f"SELECT COUNT(*) as count FROM {schema.name}"
            )
            
            if count_result.success and count_result.data:
                table_stats[model_name] = count_result.data[0]['count']
            else:
                table_stats[model_name] = 0
        
        stats['table_counts'] = table_stats
        return stats
    
    def close(self):
        """Close database system."""
        self.connection.disconnect()


# Global database system instance
_database_system: Optional[DatabaseSystem] = None


def get_database_system() -> Optional[DatabaseSystem]:
    """Get global database system instance.
    
    Returns:
        Optional[DatabaseSystem]: Global database system or None
    """
    return _database_system


def set_database_system(system: DatabaseSystem):
    """Set global database system instance.
    
    Args:
        system: Database system to set
    """
    global _database_system
    _database_system = system


# Convenience functions
def initialize_database(config: DatabaseConfig = None) -> DatabaseSystem:
    """Initialize database system (convenience function).
    
    Args:
        config: Database configuration
        
    Returns:
        DatabaseSystem: Initialized database system
    """
    global _database_system
    _database_system = DatabaseSystem(config)
    return _database_system


def save_data(model_name: str, data: Dict[str, Any]) -> Optional[str]:
    """Save data to database (convenience function).
    
    Args:
        model_name: Model name
        data: Data to save
        
    Returns:
        Optional[str]: Record ID if saved successfully
    """
    if _database_system:
        return _database_system.create_record(model_name, data)
    return None


def load_data(model_name: str, record_id: str) -> Optional[BaseModel]:
    """Load data from database (convenience function).
    
    Args:
        model_name: Model name
        record_id: Record ID
        
    Returns:
        Optional[BaseModel]: Loaded record or None
    """
    if _database_system:
        return _database_system.get_record(model_name, record_id)
    return None


def query_data(model_name: str, **conditions) -> List[BaseModel]:
    """Query data from database (convenience function).
    
    Args:
        model_name: Model name
        **conditions: Query conditions
        
    Returns:
        List[BaseModel]: Matching records
    """
    if _database_system:
        return _database_system.query_records(model_name, conditions)
    return []