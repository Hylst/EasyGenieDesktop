"""Security System for Authentication, Authorization, and Data Protection.

This module provides comprehensive security capabilities including user authentication,
authorization, encryption, secure storage, and security monitoring.
"""

import hashlib
import secrets
import base64
import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import jwt
import sqlite3
from contextlib import contextmanager
import os
import re


class AuthenticationMethod(Enum):
    """Authentication methods."""
    PASSWORD = "password"
    PIN = "pin"
    BIOMETRIC = "biometric"
    TOKEN = "token"
    TWO_FACTOR = "two_factor"
    OAUTH = "oauth"


class UserRole(Enum):
    """User roles for authorization."""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(Enum):
    """System permissions."""
    # Basic permissions
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    
    # Tool permissions
    USE_AI_CHAT = "use_ai_chat"
    USE_VOICE_ASSISTANT = "use_voice_assistant"
    USE_DOCUMENT_PROCESSOR = "use_document_processor"
    USE_MEDIA_CONVERTER = "use_media_converter"
    USE_SYSTEM_OPTIMIZER = "use_system_optimizer"
    USE_AUTOMATION_BUILDER = "use_automation_builder"
    USE_SMART_ORGANIZER = "use_smart_organizer"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SECURITY = "manage_security"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    
    # System permissions
    SYSTEM_ACCESS = "system_access"
    DEBUG_MODE = "debug_mode"
    DEVELOPER_TOOLS = "developer_tools"


class SecurityLevel(Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EncryptionType(Enum):
    """Encryption types."""
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    HYBRID = "hybrid"


class SecurityEventType(Enum):
    """Security event types."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    ENCRYPTION_EVENT = "encryption_event"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_BREACH = "system_breach"


@dataclass
class User:
    """User account information."""
    user_id: str
    username: str
    email: str
    role: UserRole = UserRole.USER
    
    # Authentication
    password_hash: Optional[str] = None
    salt: Optional[str] = None
    pin_hash: Optional[str] = None
    
    # Security settings
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    
    # Account status
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    
    # Permissions
    permissions: List[Permission] = field(default_factory=list)
    custom_permissions: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Union[Permission, str]) -> bool:
        """Check if user has permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if user has permission
        """
        if isinstance(permission, Permission):
            return permission in self.permissions
        return permission in self.custom_permissions
    
    def add_permission(self, permission: Union[Permission, str]):
        """Add permission to user.
        
        Args:
            permission: Permission to add
        """
        if isinstance(permission, Permission):
            if permission not in self.permissions:
                self.permissions.append(permission)
        else:
            if permission not in self.custom_permissions:
                self.custom_permissions.append(permission)
        
        self.updated_at = datetime.now()
    
    def remove_permission(self, permission: Union[Permission, str]):
        """Remove permission from user.
        
        Args:
            permission: Permission to remove
        """
        if isinstance(permission, Permission):
            if permission in self.permissions:
                self.permissions.remove(permission)
        else:
            if permission in self.custom_permissions:
                self.custom_permissions.remove(permission)
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary.
        
        Returns:
            Dict[str, Any]: User data (excluding sensitive info)
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'two_factor_enabled': self.two_factor_enabled,
            'security_level': self.security_level.value,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'permissions': [p.value for p in self.permissions],
            'custom_permissions': self.custom_permissions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SecurityEvent:
    """Security event record."""
    event_id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    description: str
    
    # Event details
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    
    # Risk assessment
    risk_level: SecurityLevel = SecurityLevel.LOW
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'risk_level': self.risk_level.value,
            'timestamp': self.timestamp.isoformat(),
            'additional_data': self.additional_data
        }


@dataclass
class SecurityConfig:
    """Security system configuration."""
    # Authentication settings
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    
    # Account lockout settings
    max_failed_attempts: int = 5
    lockout_duration: int = 300  # seconds
    
    # Session settings
    session_timeout: int = 3600  # seconds
    remember_me_duration: int = 2592000  # 30 days
    
    # Encryption settings
    encryption_algorithm: str = "AES-256"
    key_derivation_iterations: int = 100000
    
    # Security monitoring
    enable_security_logging: bool = True
    enable_intrusion_detection: bool = True
    suspicious_activity_threshold: int = 10
    
    # Data protection
    enable_data_encryption: bool = True
    secure_delete: bool = True
    backup_encryption: bool = True
    
    # Database settings
    database_path: Path = Path("security.db")
    
    # JWT settings
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds


class PasswordValidator:
    """Password validation utility."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize password validator.
        
        Args:
            config: Security configuration
        """
        self.config = config
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against security policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check length
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters long")
        
        # Check uppercase
        if self.config.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase
        if self.config.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check numbers
        if self.config.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check symbols
        if self.config.password_require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check common passwords
        if self._is_common_password(password):
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    def _is_common_password(self, password: str) -> bool:
        """Check if password is commonly used.
        
        Args:
            password: Password to check
            
        Returns:
            bool: True if password is common
        """
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890", "abc123"
        }
        return password.lower() in common_passwords


class EncryptionManager:
    """Encryption and decryption manager."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize encryption manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self._symmetric_key: Optional[bytes] = None
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None
    
    def generate_symmetric_key(self, password: str = None) -> bytes:
        """Generate symmetric encryption key.
        
        Args:
            password: Optional password for key derivation
            
        Returns:
            bytes: Encryption key
        """
        if password:
            # Derive key from password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.key_derivation_iterations,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            # Generate random key
            key = Fernet.generate_key()
        
        self._symmetric_key = key
        return key
    
    def generate_asymmetric_keys(self) -> Tuple[bytes, bytes]:
        """Generate asymmetric key pair.
        
        Returns:
            Tuple[bytes, bytes]: (private_key, public_key)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self._private_key = private_key
        self._public_key = public_key
        
        return private_pem, public_pem
    
    def encrypt_symmetric(self, data: Union[str, bytes], key: bytes = None) -> bytes:
        """Encrypt data using symmetric encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key (uses default if None)
            
        Returns:
            bytes: Encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encryption_key = key or self._symmetric_key
        if not encryption_key:
            raise ValueError("No encryption key available")
        
        fernet = Fernet(encryption_key)
        return fernet.encrypt(data)
    
    def decrypt_symmetric(self, encrypted_data: bytes, key: bytes = None) -> bytes:
        """Decrypt data using symmetric encryption.
        
        Args:
            encrypted_data: Data to decrypt
            key: Decryption key (uses default if None)
            
        Returns:
            bytes: Decrypted data
        """
        decryption_key = key or self._symmetric_key
        if not decryption_key:
            raise ValueError("No decryption key available")
        
        fernet = Fernet(decryption_key)
        return fernet.decrypt(encrypted_data)
    
    def encrypt_asymmetric(self, data: Union[str, bytes], public_key: bytes = None) -> bytes:
        """Encrypt data using asymmetric encryption.
        
        Args:
            data: Data to encrypt
            public_key: Public key for encryption
            
        Returns:
            bytes: Encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if public_key:
            key = serialization.load_pem_public_key(public_key, backend=default_backend())
        else:
            key = self._public_key
        
        if not key:
            raise ValueError("No public key available")
        
        return key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_asymmetric(self, encrypted_data: bytes, private_key: bytes = None) -> bytes:
        """Decrypt data using asymmetric encryption.
        
        Args:
            encrypted_data: Data to decrypt
            private_key: Private key for decryption
            
        Returns:
            bytes: Decrypted data
        """
        if private_key:
            key = serialization.load_pem_private_key(
                private_key, password=None, backend=default_backend()
            )
        else:
            key = self._private_key
        
        if not key:
            raise ValueError("No private key available")
        
        return key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt.
        
        Args:
            password: Password to hash
            salt: Optional salt (generates if None)
            
        Returns:
            Tuple[str, str]: (password_hash, salt)
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=self.config.key_derivation_iterations,
            backend=default_backend()
        )
        
        password_hash = base64.b64encode(kdf.derive(password.encode())).decode()
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Password to verify
            password_hash: Stored password hash
            salt: Password salt
            
        Returns:
            bool: True if password is correct
        """
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return computed_hash == password_hash
        except Exception:
            return False


class SecurityDatabase:
    """Security database manager."""
    
    def __init__(self, database_path: Path):
        """Initialize security database.
        
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
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    password_hash TEXT,
                    salt TEXT,
                    pin_hash TEXT,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    two_factor_secret TEXT,
                    security_level TEXT DEFAULT 'medium',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_locked BOOLEAN DEFAULT FALSE,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_login TIMESTAMP,
                    permissions TEXT,
                    custom_permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Security events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    description TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource TEXT,
                    risk_level TEXT DEFAULT 'low',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    additional_data TEXT
                )
            """)
            
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
            
            # API keys table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_used TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id)")
    
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
    
    def create_user(self, user: User) -> bool:
        """Create new user.
        
        Args:
            user: User to create
            
        Returns:
            bool: True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (
                        user_id, username, email, role, password_hash, salt, pin_hash,
                        two_factor_enabled, two_factor_secret, security_level,
                        is_active, is_locked, failed_login_attempts, last_login,
                        permissions, custom_permissions, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.role.value,
                    user.password_hash, user.salt, user.pin_hash,
                    user.two_factor_enabled, user.two_factor_secret, user.security_level.value,
                    user.is_active, user.is_locked, user.failed_login_attempts, user.last_login,
                    json.dumps([p.value for p in user.permissions]),
                    json.dumps(user.custom_permissions),
                    user.created_at, user.updated_at
                ))
            return True
        except Exception as e:
            logging.error(f"Failed to create user: {e}")
            return False
    
    def get_user(self, user_id: str = None, username: str = None, email: str = None) -> Optional[User]:
        """Get user by ID, username, or email.
        
        Args:
            user_id: User ID
            username: Username
            email: Email
            
        Returns:
            Optional[User]: User if found
        """
        query = "SELECT * FROM users WHERE "
        params = []
        
        if user_id:
            query += "user_id = ?"
            params.append(user_id)
        elif username:
            query += "username = ?"
            params.append(username)
        elif email:
            query += "email = ?"
            params.append(email)
        else:
            return None
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
        
        return None
    
    def update_user(self, user: User) -> bool:
        """Update user.
        
        Args:
            user: User to update
            
        Returns:
            bool: True if successful
        """
        try:
            user.updated_at = datetime.now()
            
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE users SET
                        username = ?, email = ?, role = ?, password_hash = ?, salt = ?,
                        pin_hash = ?, two_factor_enabled = ?, two_factor_secret = ?,
                        security_level = ?, is_active = ?, is_locked = ?,
                        failed_login_attempts = ?, last_login = ?, permissions = ?,
                        custom_permissions = ?, updated_at = ?
                    WHERE user_id = ?
                """, (
                    user.username, user.email, user.role.value, user.password_hash, user.salt,
                    user.pin_hash, user.two_factor_enabled, user.two_factor_secret,
                    user.security_level.value, user.is_active, user.is_locked,
                    user.failed_login_attempts, user.last_login,
                    json.dumps([p.value for p in user.permissions]),
                    json.dumps(user.custom_permissions), user.updated_at, user.user_id
                ))
            return True
        except Exception as e:
            logging.error(f"Failed to update user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            return True
        except Exception as e:
            logging.error(f"Failed to delete user: {e}")
            return False
    
    def log_security_event(self, event: SecurityEvent) -> bool:
        """Log security event.
        
        Args:
            event: Security event to log
            
        Returns:
            bool: True if successful
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO security_events (
                        event_id, event_type, user_id, description, ip_address,
                        user_agent, resource, risk_level, timestamp, additional_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type.value, event.user_id,
                    event.description, event.ip_address, event.user_agent,
                    event.resource, event.risk_level.value, event.timestamp,
                    json.dumps(event.additional_data)
                ))
            return True
        except Exception as e:
            logging.error(f"Failed to log security event: {e}")
            return False
    
    def get_security_events(self, user_id: str = None, event_type: SecurityEventType = None,
                           start_time: datetime = None, end_time: datetime = None,
                           limit: int = 100) -> List[SecurityEvent]:
        """Get security events.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Start time filter
            end_time: End time filter
            limit: Result limit
            
        Returns:
            List[SecurityEvent]: Security events
        """
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        events = []
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                events.append(self._row_to_security_event(row))
        
        return events
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object.
        
        Args:
            row: Database row
            
        Returns:
            User: User object
        """
        permissions = []
        if row['permissions']:
            permission_values = json.loads(row['permissions'])
            permissions = [Permission(p) for p in permission_values if p in [e.value for e in Permission]]
        
        custom_permissions = []
        if row['custom_permissions']:
            custom_permissions = json.loads(row['custom_permissions'])
        
        return User(
            user_id=row['user_id'],
            username=row['username'],
            email=row['email'],
            role=UserRole(row['role']),
            password_hash=row['password_hash'],
            salt=row['salt'],
            pin_hash=row['pin_hash'],
            two_factor_enabled=bool(row['two_factor_enabled']),
            two_factor_secret=row['two_factor_secret'],
            security_level=SecurityLevel(row['security_level']),
            is_active=bool(row['is_active']),
            is_locked=bool(row['is_locked']),
            failed_login_attempts=row['failed_login_attempts'],
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            permissions=permissions,
            custom_permissions=custom_permissions,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def _row_to_security_event(self, row: sqlite3.Row) -> SecurityEvent:
        """Convert database row to SecurityEvent object.
        
        Args:
            row: Database row
            
        Returns:
            SecurityEvent: Security event object
        """
        additional_data = {}
        if row['additional_data']:
            additional_data = json.loads(row['additional_data'])
        
        return SecurityEvent(
            event_id=row['event_id'],
            event_type=SecurityEventType(row['event_type']),
            user_id=row['user_id'],
            description=row['description'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            resource=row['resource'],
            risk_level=SecurityLevel(row['risk_level']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            additional_data=additional_data
        )
    
    def close(self):
        """Close database connection."""
        with self.lock:
            if self.connection:
                self.connection.close()
                self.connection = None


class SecuritySystem:
    """Main security system manager."""
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize security system.
        
        Args:
            config: Security configuration
        """
        self.config = config or SecurityConfig()
        self.database = SecurityDatabase(self.config.database_path)
        self.password_validator = PasswordValidator(self.config)
        self.encryption_manager = EncryptionManager(self.config)
        
        # Current session
        self.current_user: Optional[User] = None
        self.current_session_id: Optional[str] = None
        
        # Security monitoring
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.suspicious_activities: Dict[str, int] = {}
        
        # JWT secret key
        if not self.config.jwt_secret_key:
            self.config.jwt_secret_key = secrets.token_urlsafe(32)
        
        # Initialize encryption keys
        self.encryption_manager.generate_symmetric_key()
        self.encryption_manager.generate_asymmetric_keys()
    
    def create_user(self, username: str, email: str, password: str,
                   role: UserRole = UserRole.USER) -> Tuple[bool, str, Optional[User]]:
        """Create new user account.
        
        Args:
            username: Username
            email: Email address
            password: Password
            role: User role
            
        Returns:
            Tuple[bool, str, Optional[User]]: (success, message, user)
        """
        # Validate password
        is_valid, errors = self.password_validator.validate_password(password)
        if not is_valid:
            return False, "; ".join(errors), None
        
        # Check if user exists
        if self.database.get_user(username=username):
            return False, "Username already exists", None
        
        if self.database.get_user(email=email):
            return False, "Email already exists", None
        
        # Hash password
        password_hash, salt = self.encryption_manager.hash_password(password)
        
        # Create user
        user = User(
            user_id=secrets.token_urlsafe(16),
            username=username,
            email=email,
            role=role,
            password_hash=password_hash,
            salt=salt
        )
        
        # Set default permissions based on role
        self._set_default_permissions(user)
        
        # Save user
        if self.database.create_user(user):
            # Log event
            self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                f"User account created: {username}",
                user.user_id
            )
            return True, "User created successfully", user
        else:
            return False, "Failed to create user", None
    
    def authenticate(self, username: str, password: str,
                    ip_address: str = None) -> Tuple[bool, str, Optional[str]]:
        """Authenticate user.
        
        Args:
            username: Username or email
            password: Password
            ip_address: Client IP address
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, session_token)
        """
        # Get user
        user = self.database.get_user(username=username)
        if not user:
            user = self.database.get_user(email=username)
        
        if not user:
            self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                f"Login attempt with invalid username: {username}",
                None,
                ip_address=ip_address
            )
            return False, "Invalid credentials", None
        
        # Check if account is locked
        if user.is_locked:
            self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                f"Login attempt on locked account: {username}",
                user.user_id,
                ip_address=ip_address
            )
            return False, "Account is locked", None
        
        # Check if account is active
        if not user.is_active:
            self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                f"Login attempt on inactive account: {username}",
                user.user_id,
                ip_address=ip_address
            )
            return False, "Account is inactive", None
        
        # Verify password
        if not self.encryption_manager.verify_password(password, user.password_hash, user.salt):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failures
            if user.failed_login_attempts >= self.config.max_failed_attempts:
                user.is_locked = True
                self._log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    f"Account locked due to too many failed attempts: {username}",
                    user.user_id,
                    ip_address=ip_address,
                    risk_level=SecurityLevel.HIGH
                )
            
            self.database.update_user(user)
            
            self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                f"Invalid password for user: {username}",
                user.user_id,
                ip_address=ip_address
            )
            return False, "Invalid credentials", None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.now()
        self.database.update_user(user)
        
        # Create session
        session_token = self._create_session(user, ip_address)
        
        # Set current user
        self.current_user = user
        
        # Log successful login
        self._log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            f"Successful login: {username}",
            user.user_id,
            ip_address=ip_address
        )
        
        return True, "Login successful", session_token
    
    def logout(self, session_token: str = None):
        """Logout user.
        
        Args:
            session_token: Session token to invalidate
        """
        if self.current_user:
            # Log logout
            self._log_security_event(
                SecurityEventType.LOGOUT,
                f"User logged out: {self.current_user.username}",
                self.current_user.user_id
            )
            
            # Clear current user
            self.current_user = None
            self.current_session_id = None
        
        # Invalidate session token if provided
        if session_token:
            self._invalidate_session(session_token)
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Get user
        user = self.database.get_user(user_id=user_id)
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.encryption_manager.verify_password(old_password, user.password_hash, user.salt):
            self._log_security_event(
                SecurityEventType.SECURITY_VIOLATION,
                f"Invalid old password in change attempt: {user.username}",
                user_id,
                risk_level=SecurityLevel.MEDIUM
            )
            return False, "Invalid current password"
        
        # Validate new password
        is_valid, errors = self.password_validator.validate_password(new_password)
        if not is_valid:
            return False, "; ".join(errors)
        
        # Hash new password
        password_hash, salt = self.encryption_manager.hash_password(new_password)
        
        # Update user
        user.password_hash = password_hash
        user.salt = salt
        user.updated_at = datetime.now()
        
        if self.database.update_user(user):
            # Log password change
            self._log_security_event(
                SecurityEventType.PASSWORD_CHANGE,
                f"Password changed: {user.username}",
                user_id
            )
            return True, "Password changed successfully"
        else:
            return False, "Failed to update password"
    
    def check_permission(self, user_id: str, permission: Union[Permission, str]) -> bool:
        """Check if user has permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            bool: True if user has permission
        """
        user = self.database.get_user(user_id=user_id)
        if not user or not user.is_active:
            return False
        
        # Super admin has all permissions
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Check specific permission
        has_permission = user.has_permission(permission)
        
        if not has_permission:
            # Log permission denied
            self._log_security_event(
                SecurityEventType.PERMISSION_DENIED,
                f"Permission denied: {permission} for user {user.username}",
                user_id,
                risk_level=SecurityLevel.LOW
            )
        
        return has_permission
    
    def encrypt_data(self, data: Union[str, bytes], encryption_type: EncryptionType = EncryptionType.SYMMETRIC) -> bytes:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
            encryption_type: Type of encryption
            
        Returns:
            bytes: Encrypted data
        """
        if encryption_type == EncryptionType.SYMMETRIC:
            return self.encryption_manager.encrypt_symmetric(data)
        elif encryption_type == EncryptionType.ASYMMETRIC:
            return self.encryption_manager.encrypt_asymmetric(data)
        else:
            raise ValueError(f"Unsupported encryption type: {encryption_type}")
    
    def decrypt_data(self, encrypted_data: bytes, encryption_type: EncryptionType = EncryptionType.SYMMETRIC) -> bytes:
        """Decrypt data.
        
        Args:
            encrypted_data: Data to decrypt
            encryption_type: Type of encryption
            
        Returns:
            bytes: Decrypted data
        """
        if encryption_type == EncryptionType.SYMMETRIC:
            return self.encryption_manager.decrypt_symmetric(encrypted_data)
        elif encryption_type == EncryptionType.ASYMMETRIC:
            return self.encryption_manager.decrypt_asymmetric(encrypted_data)
        else:
            raise ValueError(f"Unsupported encryption type: {encryption_type}")
    
    def get_security_events(self, user_id: str = None, event_type: SecurityEventType = None,
                           limit: int = 100) -> List[SecurityEvent]:
        """Get security events.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            limit: Result limit
            
        Returns:
            List[SecurityEvent]: Security events
        """
        return self.database.get_security_events(user_id, event_type, limit=limit)
    
    def generate_security_report(self, start_time: datetime = None,
                               end_time: datetime = None) -> Dict[str, Any]:
        """Generate security report.
        
        Args:
            start_time: Start time for report
            end_time: End time for report
            
        Returns:
            Dict[str, Any]: Security report
        """
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)  # Last 7 days
        
        # Get events
        events = self.database.get_security_events(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Analyze events
        report = {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_events': len(events),
            'event_types': {},
            'risk_levels': {},
            'failed_logins': 0,
            'successful_logins': 0,
            'password_changes': 0,
            'permission_denials': 0,
            'security_violations': 0,
            'top_users': {},
            'recommendations': []
        }
        
        # Count events by type and risk level
        for event in events:
            event_type = event.event_type.value
            risk_level = event.risk_level.value
            
            report['event_types'][event_type] = report['event_types'].get(event_type, 0) + 1
            report['risk_levels'][risk_level] = report['risk_levels'].get(risk_level, 0) + 1
            
            # Count specific events
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                report['failed_logins'] += 1
            elif event.event_type == SecurityEventType.LOGIN_SUCCESS:
                report['successful_logins'] += 1
            elif event.event_type == SecurityEventType.PASSWORD_CHANGE:
                report['password_changes'] += 1
            elif event.event_type == SecurityEventType.PERMISSION_DENIED:
                report['permission_denials'] += 1
            elif event.event_type == SecurityEventType.SECURITY_VIOLATION:
                report['security_violations'] += 1
            
            # Count by user
            if event.user_id:
                report['top_users'][event.user_id] = report['top_users'].get(event.user_id, 0) + 1
        
        # Generate recommendations
        if report['failed_logins'] > 10:
            report['recommendations'].append("High number of failed logins detected. Consider implementing additional security measures.")
        
        if report['security_violations'] > 0:
            report['recommendations'].append("Security violations detected. Review user access and permissions.")
        
        if report['risk_levels'].get('high', 0) > 5:
            report['recommendations'].append("Multiple high-risk events detected. Immediate security review recommended.")
        
        return report
    
    def _create_session(self, user: User, ip_address: str = None) -> str:
        """Create user session.
        
        Args:
            user: User
            ip_address: Client IP address
            
        Returns:
            str: Session token
        """
        # Generate session ID and token
        session_id = secrets.token_urlsafe(32)
        
        # Create JWT token
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role.value,
            'session_id': session_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + self.config.jwt_expiration
        }
        
        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
        
        # Store session in database
        with self.database._get_connection() as conn:
            conn.execute("""
                INSERT INTO sessions (
                    session_id, user_id, token, expires_at, ip_address
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                user.user_id,
                token,
                datetime.now() + timedelta(seconds=self.config.jwt_expiration),
                ip_address
            ))
        
        self.current_session_id = session_id
        return token
    
    def _invalidate_session(self, session_token: str):
        """Invalidate session.
        
        Args:
            session_token: Session token to invalidate
        """
        with self.database._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET is_active = FALSE WHERE token = ?",
                (session_token,)
            )
    
    def _set_default_permissions(self, user: User):
        """Set default permissions based on user role.
        
        Args:
            user: User to set permissions for
        """
        if user.role == UserRole.GUEST:
            # Guests have minimal permissions
            user.permissions = [Permission.READ]
        
        elif user.role == UserRole.USER:
            # Regular users can use all tools
            user.permissions = [
                Permission.READ,
                Permission.WRITE,
                Permission.USE_AI_CHAT,
                Permission.USE_VOICE_ASSISTANT,
                Permission.USE_DOCUMENT_PROCESSOR,
                Permission.USE_MEDIA_CONVERTER,
                Permission.USE_SYSTEM_OPTIMIZER,
                Permission.USE_AUTOMATION_BUILDER,
                Permission.USE_SMART_ORGANIZER,
                Permission.EXPORT_DATA
            ]
        
        elif user.role == UserRole.ADMIN:
            # Admins have most permissions
            user.permissions = [
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.EXECUTE,
                Permission.USE_AI_CHAT,
                Permission.USE_VOICE_ASSISTANT,
                Permission.USE_DOCUMENT_PROCESSOR,
                Permission.USE_MEDIA_CONVERTER,
                Permission.USE_SYSTEM_OPTIMIZER,
                Permission.USE_AUTOMATION_BUILDER,
                Permission.USE_SMART_ORGANIZER,
                Permission.MANAGE_USERS,
                Permission.MANAGE_SETTINGS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.IMPORT_DATA
            ]
        
        elif user.role == UserRole.SUPER_ADMIN:
            # Super admins have all permissions
            user.permissions = list(Permission)
    
    def _log_security_event(self, event_type: SecurityEventType, description: str,
                           user_id: str = None, ip_address: str = None,
                           user_agent: str = None, resource: str = None,
                           risk_level: SecurityLevel = SecurityLevel.LOW,
                           additional_data: Dict[str, Any] = None):
        """Log security event.
        
        Args:
            event_type: Type of event
            description: Event description
            user_id: User ID
            ip_address: Client IP address
            user_agent: User agent
            resource: Resource accessed
            risk_level: Risk level
            additional_data: Additional event data
        """
        if not self.config.enable_security_logging:
            return
        
        event = SecurityEvent(
            event_id=secrets.token_urlsafe(16),
            event_type=event_type,
            user_id=user_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            risk_level=risk_level,
            additional_data=additional_data or {}
        )
        
        self.database.log_security_event(event)
        
        # Check for suspicious activity
        if self.config.enable_intrusion_detection:
            self._check_suspicious_activity(event)
    
    def _check_suspicious_activity(self, event: SecurityEvent):
        """Check for suspicious activity patterns.
        
        Args:
            event: Security event to analyze
        """
        # Track failed login attempts by IP
        if event.event_type == SecurityEventType.LOGIN_FAILURE and event.ip_address:
            if event.ip_address not in self.failed_attempts:
                self.failed_attempts[event.ip_address] = []
            
            self.failed_attempts[event.ip_address].append(event.timestamp)
            
            # Remove old attempts (older than 1 hour)
            cutoff = event.timestamp - timedelta(hours=1)
            self.failed_attempts[event.ip_address] = [
                attempt for attempt in self.failed_attempts[event.ip_address]
                if attempt > cutoff
            ]
            
            # Check if threshold exceeded
            if len(self.failed_attempts[event.ip_address]) >= self.config.suspicious_activity_threshold:
                self._log_security_event(
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    f"Suspicious activity detected from IP: {event.ip_address}",
                    risk_level=SecurityLevel.HIGH,
                    additional_data={'failed_attempts': len(self.failed_attempts[event.ip_address])}
                )
    
    def close(self):
        """Close security system."""
        self.database.close()


# Global security system instance
_security_system: Optional[SecuritySystem] = None


def get_security_system() -> Optional[SecuritySystem]:
    """Get global security system instance.
    
    Returns:
        Optional[SecuritySystem]: Global security system or None
    """
    return _security_system


def set_security_system(system: SecuritySystem):
    """Set global security system instance.
    
    Args:
        system: Security system to set
    """
    global _security_system
    _security_system = system


# Convenience functions
def initialize_security(config: SecurityConfig = None) -> SecuritySystem:
    """Initialize security system (convenience function).
    
    Args:
        config: Security configuration
        
    Returns:
        SecuritySystem: Initialized security system
    """
    global _security_system
    _security_system = SecuritySystem(config)
    return _security_system


def authenticate_user(username: str, password: str, ip_address: str = None) -> Tuple[bool, str, Optional[str]]:
    """Authenticate user (convenience function).
    
    Args:
        username: Username or email
        password: Password
        ip_address: Client IP address
        
    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, session_token)
    """
    if _security_system:
        return _security_system.authenticate(username, password, ip_address)
    return False, "Security system not initialized", None


def check_permission(user_id: str, permission: Union[Permission, str]) -> bool:
    """Check user permission (convenience function).
    
    Args:
        user_id: User ID
        permission: Permission to check
        
    Returns:
        bool: True if user has permission
    """
    if _security_system:
        return _security_system.check_permission(user_id, permission)
    return False


def encrypt_data(data: Union[str, bytes], encryption_type: EncryptionType = EncryptionType.SYMMETRIC) -> Optional[bytes]:
    """Encrypt data (convenience function).
    
    Args:
        data: Data to encrypt
        encryption_type: Type of encryption
        
    Returns:
        Optional[bytes]: Encrypted data or None if failed
    """
    if _security_system:
        try:
            return _security_system.encrypt_data(data, encryption_type)
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
    return None


def decrypt_data(encrypted_data: bytes, encryption_type: EncryptionType = EncryptionType.SYMMETRIC) -> Optional[bytes]:
    """Decrypt data (convenience function).
    
    Args:
        encrypted_data: Data to decrypt
        encryption_type: Type of encryption
        
    Returns:
        Optional[bytes]: Decrypted data or None if failed
    """
    if _security_system:
        try:
            return _security_system.decrypt_data(encrypted_data, encryption_type)
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
    return None