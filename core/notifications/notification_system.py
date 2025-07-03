"""Notification System for User Alerts and Messages.

This module provides comprehensive notification capabilities including toast notifications,
system tray alerts, email notifications, and in-app messaging.
"""

import threading
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
import uuid
from queue import Queue, Empty
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from plyer import notification as plyer_notification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class NotificationType(Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"
    UPDATE = "update"
    SYSTEM = "system"


class NotificationPriority(Enum):
    """Notification priorities."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    TOAST = "toast"  # System toast notifications
    TRAY = "tray"    # System tray notifications
    INAPP = "inapp"  # In-app notifications
    EMAIL = "email"  # Email notifications
    SOUND = "sound"  # Sound alerts
    POPUP = "popup"  # Modal popup dialogs


class NotificationStatus(Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DISMISSED = "dismissed"
    FAILED = "failed"


@dataclass
class NotificationAction:
    """Notification action configuration."""
    id: str
    label: str
    callback: Optional[Callable] = None
    url: Optional[str] = None
    is_primary: bool = False
    icon: Optional[str] = None


@dataclass
class NotificationConfig:
    """Notification configuration."""
    # Basic properties
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Delivery settings
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.INAPP])
    auto_dismiss: bool = True
    dismiss_timeout: int = 5000  # milliseconds
    
    # Visual settings
    icon: Optional[str] = None
    image: Optional[str] = None
    color: Optional[str] = None
    
    # Interaction settings
    actions: List[NotificationAction] = field(default_factory=list)
    clickable: bool = True
    persistent: bool = False
    
    # Scheduling
    schedule_time: Optional[datetime] = None
    repeat_interval: Optional[timedelta] = None
    max_repeats: int = 1
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Notification instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: NotificationConfig = field(default_factory=NotificationConfig)
    status: NotificationStatus = NotificationStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    
    # Delivery tracking
    delivery_attempts: int = 0
    delivery_channels: Dict[NotificationChannel, bool] = field(default_factory=dict)
    error_message: str = ""
    
    # Interaction tracking
    click_count: int = 0
    action_clicks: Dict[str, int] = field(default_factory=dict)
    
    def mark_sent(self):
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
    
    def mark_delivered(self):
        """Mark notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_read(self):
        """Mark notification as read."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()
    
    def mark_dismissed(self):
        """Mark notification as dismissed."""
        self.status = NotificationStatus.DISMISSED
        self.dismissed_at = datetime.now()
    
    def mark_failed(self, error: str):
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED
        self.error_message = error
    
    def record_click(self, action_id: str = None):
        """Record notification click.
        
        Args:
            action_id: Optional action ID that was clicked
        """
        self.click_count += 1
        
        if action_id:
            self.action_clicks[action_id] = self.action_clicks.get(action_id, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary.
        
        Returns:
            Dict[str, Any]: Notification data
        """
        return {
            'id': self.id,
            'title': self.config.title,
            'message': self.config.message,
            'type': self.config.notification_type.value,
            'priority': self.config.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'category': self.config.category,
            'tags': self.config.tags,
            'data': self.config.data
        }


@dataclass
class EmailConfig:
    """Email notification configuration."""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = "Easy Genie Desktop"
    use_tls: bool = True
    use_ssl: bool = False


@dataclass
class NotificationSettings:
    """Notification system settings."""
    # Global settings
    enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    
    # Channel settings
    toast_enabled: bool = True
    tray_enabled: bool = True
    inapp_enabled: bool = True
    email_enabled: bool = False
    sound_enabled: bool = True
    popup_enabled: bool = True
    
    # Display settings
    max_concurrent_notifications: int = 5
    default_timeout: int = 5000
    animation_enabled: bool = True
    
    # Priority filtering
    min_priority: NotificationPriority = NotificationPriority.LOW
    
    # Email settings
    email_config: EmailConfig = field(default_factory=EmailConfig)
    
    # Sound settings
    sound_volume: float = 0.5
    sound_file: Optional[str] = None
    
    # Category filters
    enabled_categories: List[str] = field(default_factory=lambda: ["general"])
    disabled_categories: List[str] = field(default_factory=list)


class ToastNotificationHandler:
    """Handler for toast notifications."""
    
    def __init__(self):
        """Initialize toast handler."""
        self.active_notifications: Dict[str, Any] = {}
    
    def send_notification(self, notification: Notification) -> bool:
        """Send toast notification.
        
        Args:
            notification: Notification to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Map notification type to icon
            icon_map = {
                NotificationType.INFO: "info",
                NotificationType.SUCCESS: "success",
                NotificationType.WARNING: "warning",
                NotificationType.ERROR: "error",
                NotificationType.REMINDER: "reminder",
                NotificationType.ACHIEVEMENT: "achievement",
                NotificationType.UPDATE: "update",
                NotificationType.SYSTEM: "system"
            }
            
            # Send system notification
            plyer_notification.notify(
                title=notification.config.title,
                message=notification.config.message,
                app_name="Easy Genie Desktop",
                app_icon=notification.config.icon,
                timeout=notification.config.dismiss_timeout / 1000,
                toast=True
            )
            
            self.active_notifications[notification.id] = notification
            return True
            
        except Exception as e:
            logging.error(f"Toast notification error: {e}")
            return False
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss toast notification.
        
        Args:
            notification_id: Notification ID to dismiss
        """
        self.active_notifications.pop(notification_id, None)


class InAppNotificationHandler:
    """Handler for in-app notifications."""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        """Initialize in-app handler.
        
        Args:
            parent_window: Parent window for notifications
        """
        self.parent_window = parent_window
        self.active_notifications: Dict[str, ctk.CTkToplevel] = {}
        self.notification_queue: Queue = Queue()
        self.max_concurrent = 5
        self.notification_spacing = 10
        self.notification_width = 350
        self.notification_height = 100
    
    def send_notification(self, notification: Notification) -> bool:
        """Send in-app notification.
        
        Args:
            notification: Notification to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            if len(self.active_notifications) >= self.max_concurrent:
                self.notification_queue.put(notification)
                return True
            
            self._create_notification_window(notification)
            return True
            
        except Exception as e:
            logging.error(f"In-app notification error: {e}")
            return False
    
    def _create_notification_window(self, notification: Notification):
        """Create notification window.
        
        Args:
            notification: Notification to display
        """
        # Create notification window
        window = ctk.CTkToplevel(self.parent_window)
        window.title("")
        window.geometry(f"{self.notification_width}x{self.notification_height}")
        window.resizable(False, False)
        window.attributes("-topmost", True)
        window.overrideredirect(True)
        
        # Position window
        self._position_notification_window(window)
        
        # Configure appearance based on type
        colors = self._get_notification_colors(notification.config.notification_type)
        
        # Main frame
        main_frame = ctk.CTkFrame(window, fg_color=colors['bg'])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Header frame
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Type icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text=self._get_notification_icon(notification.config.notification_type),
            font=("Arial", 16),
            text_color=colors['icon']
        )
        icon_label.pack(side="left")
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=notification.config.title,
            font=("Arial", 12, "bold"),
            text_color=colors['title']
        )
        title_label.pack(side="left", padx=(10, 0))
        
        # Close button
        close_button = ctk.CTkButton(
            header_frame,
            text="×",
            width=20,
            height=20,
            font=("Arial", 14),
            command=lambda: self._dismiss_notification(notification.id, window)
        )
        close_button.pack(side="right")
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=notification.config.message,
            font=("Arial", 10),
            text_color=colors['message'],
            wraplength=self.notification_width - 40
        )
        message_label.pack(fill="x", padx=10, pady=(0, 10))
        
        # Actions frame
        if notification.config.actions:
            actions_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            for action in notification.config.actions:
                action_button = ctk.CTkButton(
                    actions_frame,
                    text=action.label,
                    height=25,
                    command=lambda a=action: self._handle_action_click(notification, a, window)
                )
                action_button.pack(side="left", padx=(0, 5))
        
        # Store notification
        self.active_notifications[notification.id] = window
        
        # Auto-dismiss if configured
        if notification.config.auto_dismiss:
            window.after(
                notification.config.dismiss_timeout,
                lambda: self._dismiss_notification(notification.id, window)
            )
        
        # Click handler
        if notification.config.clickable:
            window.bind("<Button-1>", lambda e: self._handle_notification_click(notification))
            main_frame.bind("<Button-1>", lambda e: self._handle_notification_click(notification))
    
    def _position_notification_window(self, window: ctk.CTkToplevel):
        """Position notification window.
        
        Args:
            window: Window to position
        """
        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position (bottom-right corner)
        x = screen_width - self.notification_width - 20
        y = screen_height - self.notification_height - 50
        
        # Adjust for existing notifications
        existing_count = len(self.active_notifications)
        y -= existing_count * (self.notification_height + self.notification_spacing)
        
        window.geometry(f"+{x}+{y}")
    
    def _get_notification_colors(self, notification_type: NotificationType) -> Dict[str, str]:
        """Get colors for notification type.
        
        Args:
            notification_type: Type of notification
            
        Returns:
            Dict[str, str]: Color configuration
        """
        color_map = {
            NotificationType.INFO: {
                'bg': '#E3F2FD',
                'icon': '#1976D2',
                'title': '#0D47A1',
                'message': '#424242'
            },
            NotificationType.SUCCESS: {
                'bg': '#E8F5E8',
                'icon': '#4CAF50',
                'title': '#2E7D32',
                'message': '#424242'
            },
            NotificationType.WARNING: {
                'bg': '#FFF3E0',
                'icon': '#FF9800',
                'title': '#E65100',
                'message': '#424242'
            },
            NotificationType.ERROR: {
                'bg': '#FFEBEE',
                'icon': '#F44336',
                'title': '#C62828',
                'message': '#424242'
            },
            NotificationType.REMINDER: {
                'bg': '#F3E5F5',
                'icon': '#9C27B0',
                'title': '#6A1B9A',
                'message': '#424242'
            },
            NotificationType.ACHIEVEMENT: {
                'bg': '#FFF8E1',
                'icon': '#FFC107',
                'title': '#F57F17',
                'message': '#424242'
            },
            NotificationType.UPDATE: {
                'bg': '#E0F2F1',
                'icon': '#009688',
                'title': '#00695C',
                'message': '#424242'
            },
            NotificationType.SYSTEM: {
                'bg': '#FAFAFA',
                'icon': '#607D8B',
                'title': '#37474F',
                'message': '#424242'
            }
        }
        
        return color_map.get(notification_type, color_map[NotificationType.INFO])
    
    def _get_notification_icon(self, notification_type: NotificationType) -> str:
        """Get icon for notification type.
        
        Args:
            notification_type: Type of notification
            
        Returns:
            str: Icon character
        """
        icon_map = {
            NotificationType.INFO: "ℹ",
            NotificationType.SUCCESS: "✓",
            NotificationType.WARNING: "⚠",
            NotificationType.ERROR: "✗",
            NotificationType.REMINDER: "🔔",
            NotificationType.ACHIEVEMENT: "🏆",
            NotificationType.UPDATE: "🔄",
            NotificationType.SYSTEM: "⚙"
        }
        
        return icon_map.get(notification_type, "ℹ")
    
    def _handle_notification_click(self, notification: Notification):
        """Handle notification click.
        
        Args:
            notification: Clicked notification
        """
        notification.record_click()
        
        # Execute default action if available
        if notification.config.actions:
            primary_action = next(
                (a for a in notification.config.actions if a.is_primary),
                notification.config.actions[0]
            )
            self._execute_action(notification, primary_action)
    
    def _handle_action_click(self, notification: Notification, action: NotificationAction, window: ctk.CTkToplevel):
        """Handle action button click.
        
        Args:
            notification: Notification instance
            action: Clicked action
            window: Notification window
        """
        notification.record_click(action.id)
        self._execute_action(notification, action)
        self._dismiss_notification(notification.id, window)
    
    def _execute_action(self, notification: Notification, action: NotificationAction):
        """Execute notification action.
        
        Args:
            notification: Notification instance
            action: Action to execute
        """
        try:
            if action.callback:
                action.callback(notification, action)
            elif action.url:
                import webbrowser
                webbrowser.open(action.url)
        except Exception as e:
            logging.error(f"Action execution error: {e}")
    
    def _dismiss_notification(self, notification_id: str, window: ctk.CTkToplevel):
        """Dismiss notification.
        
        Args:
            notification_id: Notification ID
            window: Notification window
        """
        try:
            window.destroy()
            self.active_notifications.pop(notification_id, None)
            
            # Show next queued notification
            if not self.notification_queue.empty():
                try:
                    next_notification = self.notification_queue.get_nowait()
                    self._create_notification_window(next_notification)
                except Empty:
                    pass
                    
        except Exception as e:
            logging.error(f"Notification dismissal error: {e}")
    
    def dismiss_all(self):
        """Dismiss all active notifications."""
        for notification_id, window in list(self.active_notifications.items()):
            self._dismiss_notification(notification_id, window)


class EmailNotificationHandler:
    """Handler for email notifications."""
    
    def __init__(self, config: EmailConfig):
        """Initialize email handler.
        
        Args:
            config: Email configuration
        """
        self.config = config
    
    def send_notification(self, notification: Notification, recipient: str) -> bool:
        """Send email notification.
        
        Args:
            notification: Notification to send
            recipient: Email recipient
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = recipient
            msg['Subject'] = notification.config.title
            
            # Create HTML body
            html_body = self._create_html_body(notification)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to SMTP server
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port)
            else:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                if self.config.use_tls:
                    server.starttls()
            
            # Login and send
            server.login(self.config.username, self.config.password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logging.error(f"Email notification error: {e}")
            return False
    
    def _create_html_body(self, notification: Notification) -> str:
        """Create HTML email body.
        
        Args:
            notification: Notification instance
            
        Returns:
            str: HTML body
        """
        # Get colors for notification type
        color_map = {
            NotificationType.INFO: '#1976D2',
            NotificationType.SUCCESS: '#4CAF50',
            NotificationType.WARNING: '#FF9800',
            NotificationType.ERROR: '#F44336',
            NotificationType.REMINDER: '#9C27B0',
            NotificationType.ACHIEVEMENT: '#FFC107',
            NotificationType.UPDATE: '#009688',
            NotificationType.SYSTEM: '#607D8B'
        }
        
        accent_color = color_map.get(notification.config.notification_type, '#1976D2')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: {accent_color}; color: white; padding: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 20px; }}
                .message {{ font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 20px; }}
                .actions {{ margin-top: 20px; }}
                .action-button {{ display: inline-block; padding: 10px 20px; background-color: {accent_color}; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px 20px; font-size: 12px; color: #666; border-top: 1px solid #e9ecef; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{notification.config.title}</h1>
                </div>
                <div class="content">
                    <div class="message">
                        {notification.config.message}
                    </div>
        """
        
        # Add actions if available
        if notification.config.actions:
            html += '<div class="actions">'
            for action in notification.config.actions:
                if action.url:
                    html += f'<a href="{action.url}" class="action-button">{action.label}</a>'
            html += '</div>'
        
        html += f"""
                </div>
                <div class="footer">
                    Sent by Easy Genie Desktop at {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html


class NotificationSystem:
    """Main notification system manager."""
    
    def __init__(self, settings: NotificationSettings = None, parent_window: Optional[tk.Tk] = None):
        """Initialize notification system.
        
        Args:
            settings: Notification settings
            parent_window: Parent window for in-app notifications
        """
        self.settings = settings or NotificationSettings()
        self.parent_window = parent_window
        
        # Handlers
        self.toast_handler = ToastNotificationHandler()
        self.inapp_handler = InAppNotificationHandler(parent_window)
        self.email_handler = EmailNotificationHandler(self.settings.email_config)
        
        # Storage
        self.notifications: Dict[str, Notification] = {}
        self.notification_history: List[Notification] = []
        
        # Processing
        self.notification_queue: Queue = Queue()
        self.processing_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'notification_sent': [],
            'notification_delivered': [],
            'notification_clicked': [],
            'notification_dismissed': []
        }
        
        # Statistics
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_clicked': 0,
            'total_dismissed': 0,
            'channel_stats': {channel.value: 0 for channel in NotificationChannel}
        }
        
        # Start processing
        self.start()
    
    def start(self):
        """Start notification processing."""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_notifications, daemon=True)
            self.processing_thread.start()
    
    def stop(self):
        """Stop notification processing."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def send_notification(self, config: Union[NotificationConfig, Dict[str, Any]]) -> str:
        """Send notification.
        
        Args:
            config: Notification configuration
            
        Returns:
            str: Notification ID
        """
        # Convert dict to config if needed
        if isinstance(config, dict):
            config = NotificationConfig(**config)
        
        # Create notification
        notification = Notification(config=config)
        
        # Store notification
        self.notifications[notification.id] = notification
        
        # Queue for processing
        self.notification_queue.put(notification)
        
        return notification.id
    
    def send_simple(self, title: str, message: str, 
                   notification_type: NotificationType = NotificationType.INFO,
                   channels: List[NotificationChannel] = None) -> str:
        """Send simple notification (convenience method).
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: Delivery channels
            
        Returns:
            str: Notification ID
        """
        config = NotificationConfig(
            title=title,
            message=message,
            notification_type=notification_type,
            channels=channels or [NotificationChannel.INAPP]
        )
        
        return self.send_notification(config)
    
    def send_with_actions(self, title: str, message: str, actions: List[NotificationAction],
                         notification_type: NotificationType = NotificationType.INFO) -> str:
        """Send notification with actions.
        
        Args:
            title: Notification title
            message: Notification message
            actions: Notification actions
            notification_type: Type of notification
            
        Returns:
            str: Notification ID
        """
        config = NotificationConfig(
            title=title,
            message=message,
            notification_type=notification_type,
            actions=actions,
            channels=[NotificationChannel.INAPP]
        )
        
        return self.send_notification(config)
    
    def schedule_notification(self, config: Union[NotificationConfig, Dict[str, Any]], 
                            schedule_time: datetime) -> str:
        """Schedule notification for later delivery.
        
        Args:
            config: Notification configuration
            schedule_time: When to send notification
            
        Returns:
            str: Notification ID
        """
        if isinstance(config, dict):
            config = NotificationConfig(**config)
        
        config.schedule_time = schedule_time
        return self.send_notification(config)
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss specific notification.
        
        Args:
            notification_id: Notification ID to dismiss
        """
        notification = self.notifications.get(notification_id)
        if notification:
            notification.mark_dismissed()
            
            # Dismiss from handlers
            self.toast_handler.dismiss_notification(notification_id)
            
            # Update statistics
            self.stats['total_dismissed'] += 1
            
            # Trigger callbacks
            self._trigger_event('notification_dismissed', notification)
    
    def dismiss_all(self):
        """Dismiss all active notifications."""
        for notification_id in list(self.notifications.keys()):
            self.dismiss_notification(notification_id)
        
        self.inapp_handler.dismiss_all()
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Optional[Notification]: Notification if found
        """
        return self.notifications.get(notification_id)
    
    def get_notifications(self, status: NotificationStatus = None, 
                         notification_type: NotificationType = None,
                         category: str = None) -> List[Notification]:
        """Get notifications with filters.
        
        Args:
            status: Filter by status
            notification_type: Filter by type
            category: Filter by category
            
        Returns:
            List[Notification]: Matching notifications
        """
        notifications = list(self.notifications.values())
        
        if status:
            notifications = [n for n in notifications if n.status == status]
        
        if notification_type:
            notifications = [n for n in notifications if n.config.notification_type == notification_type]
        
        if category:
            notifications = [n for n in notifications if n.config.category == category]
        
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)
    
    def mark_as_read(self, notification_id: str):
        """Mark notification as read.
        
        Args:
            notification_id: Notification ID
        """
        notification = self.notifications.get(notification_id)
        if notification:
            notification.mark_read()
    
    def add_event_callback(self, event: str, callback: Callable):
        """Add event callback.
        
        Args:
            event: Event name
            callback: Callback function
        """
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def remove_event_callback(self, event: str, callback: Callable):
        """Remove event callback.
        
        Args:
            event: Event name
            callback: Callback function
        """
        if event in self.event_callbacks and callback in self.event_callbacks[event]:
            self.event_callbacks[event].remove(callback)
    
    def update_settings(self, settings: NotificationSettings):
        """Update notification settings.
        
        Args:
            settings: New settings
        """
        self.settings = settings
        self.email_handler = EmailNotificationHandler(settings.email_config)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        # Calculate additional stats
        active_count = len([n for n in self.notifications.values() 
                           if n.status in [NotificationStatus.PENDING, NotificationStatus.SENT]])
        
        unread_count = len([n for n in self.notifications.values() 
                           if n.status == NotificationStatus.DELIVERED])
        
        return {
            **self.stats,
            'active_notifications': active_count,
            'unread_notifications': unread_count,
            'total_notifications': len(self.notifications),
            'history_size': len(self.notification_history)
        }
    
    def clear_history(self, older_than: timedelta = None):
        """Clear notification history.
        
        Args:
            older_than: Clear notifications older than this duration
        """
        if older_than:
            cutoff_time = datetime.now() - older_than
            self.notification_history = [
                n for n in self.notification_history 
                if n.created_at > cutoff_time
            ]
        else:
            self.notification_history.clear()
    
    def _process_notifications(self):
        """Process notification queue."""
        while self.running:
            try:
                # Get notification from queue
                notification = self.notification_queue.get(timeout=1.0)
                
                # Check if system is enabled
                if not self.settings.enabled:
                    continue
                
                # Check quiet hours
                if self._is_quiet_hours():
                    # Reschedule for later unless urgent
                    if notification.config.priority != NotificationPriority.URGENT:
                        notification.config.schedule_time = self._get_next_active_time()
                        self.notification_queue.put(notification)
                        continue
                
                # Check if scheduled
                if (notification.config.schedule_time and 
                    notification.config.schedule_time > datetime.now()):
                    # Reschedule
                    time.sleep(1)
                    self.notification_queue.put(notification)
                    continue
                
                # Process notification
                self._deliver_notification(notification)
                
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Notification processing error: {e}")
    
    def _deliver_notification(self, notification: Notification):
        """Deliver notification through configured channels.
        
        Args:
            notification: Notification to deliver
        """
        notification.mark_sent()
        delivery_success = False
        
        # Deliver through each channel
        for channel in notification.config.channels:
            try:
                success = False
                
                if channel == NotificationChannel.TOAST and self.settings.toast_enabled:
                    success = self.toast_handler.send_notification(notification)
                elif channel == NotificationChannel.INAPP and self.settings.inapp_enabled:
                    success = self.inapp_handler.send_notification(notification)
                elif channel == NotificationChannel.EMAIL and self.settings.email_enabled:
                    # Email requires recipient - skip for now
                    success = False
                elif channel == NotificationChannel.POPUP and self.settings.popup_enabled:
                    success = self._send_popup_notification(notification)
                
                notification.delivery_channels[channel] = success
                if success:
                    delivery_success = True
                    self.stats['channel_stats'][channel.value] += 1
                
            except Exception as e:
                logging.error(f"Channel delivery error ({channel.value}): {e}")
                notification.delivery_channels[channel] = False
        
        # Update notification status
        if delivery_success:
            notification.mark_delivered()
            self.stats['total_delivered'] += 1
            self._trigger_event('notification_delivered', notification)
        else:
            notification.mark_failed("All delivery channels failed")
        
        # Update statistics
        self.stats['total_sent'] += 1
        
        # Trigger callbacks
        self._trigger_event('notification_sent', notification)
        
        # Move to history if configured
        if notification.status in [NotificationStatus.DELIVERED, NotificationStatus.FAILED]:
            self.notification_history.append(notification)
            
            # Limit history size
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-500:]
    
    def _send_popup_notification(self, notification: Notification) -> bool:
        """Send popup notification.
        
        Args:
            notification: Notification to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Map notification type to messagebox type
            if notification.config.notification_type == NotificationType.ERROR:
                messagebox.showerror(notification.config.title, notification.config.message)
            elif notification.config.notification_type == NotificationType.WARNING:
                messagebox.showwarning(notification.config.title, notification.config.message)
            else:
                messagebox.showinfo(notification.config.title, notification.config.message)
            
            return True
            
        except Exception as e:
            logging.error(f"Popup notification error: {e}")
            return False
    
    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours.
        
        Returns:
            bool: True if in quiet hours
        """
        if not self.settings.quiet_hours_enabled:
            return False
        
        now = datetime.now().time()
        start_time = datetime.strptime(self.settings.quiet_hours_start, "%H:%M").time()
        end_time = datetime.strptime(self.settings.quiet_hours_end, "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time
    
    def _get_next_active_time(self) -> datetime:
        """Get next active time after quiet hours.
        
        Returns:
            datetime: Next active time
        """
        now = datetime.now()
        end_time = datetime.strptime(self.settings.quiet_hours_end, "%H:%M").time()
        
        next_active = datetime.combine(now.date(), end_time)
        if next_active <= now:
            next_active += timedelta(days=1)
        
        return next_active
    
    def _trigger_event(self, event: str, notification: Notification):
        """Trigger event callbacks.
        
        Args:
            event: Event name
            notification: Notification instance
        """
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(notification)
            except Exception as e:
                logging.error(f"Event callback error ({event}): {e}")


# Global notification system instance
_notification_system: Optional[NotificationSystem] = None


def get_notification_system() -> Optional[NotificationSystem]:
    """Get global notification system instance.
    
    Returns:
        Optional[NotificationSystem]: Global notification system or None
    """
    return _notification_system


def set_notification_system(system: NotificationSystem):
    """Set global notification system instance.
    
    Args:
        system: Notification system to set
    """
    global _notification_system
    _notification_system = system


# Convenience functions
def initialize_notifications(settings: NotificationSettings = None, 
                           parent_window: Optional[tk.Tk] = None) -> NotificationSystem:
    """Initialize notification system (convenience function).
    
    Args:
        settings: Notification settings
        parent_window: Parent window for in-app notifications
        
    Returns:
        NotificationSystem: Initialized notification system
    """
    global _notification_system
    _notification_system = NotificationSystem(settings, parent_window)
    return _notification_system


def notify(title: str, message: str, notification_type: NotificationType = NotificationType.INFO) -> Optional[str]:
    """Send simple notification (convenience function).
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        
    Returns:
        Optional[str]: Notification ID if sent successfully
    """
    if _notification_system:
        return _notification_system.send_simple(title, message, notification_type)
    return None


def notify_success(title: str, message: str) -> Optional[str]:
    """Send success notification (convenience function).
    
    Args:
        title: Notification title
        message: Notification message
        
    Returns:
        Optional[str]: Notification ID if sent successfully
    """
    return notify(title, message, NotificationType.SUCCESS)


def notify_error(title: str, message: str) -> Optional[str]:
    """Send error notification (convenience function).
    
    Args:
        title: Notification title
        message: Notification message
        
    Returns:
        Optional[str]: Notification ID if sent successfully
    """
    return notify(title, message, NotificationType.ERROR)


def notify_warning(title: str, message: str) -> Optional[str]:
    """Send warning notification (convenience function).
    
    Args:
        title: Notification title
        message: Notification message
        
    Returns:
        Optional[str]: Notification ID if sent successfully
    """
    return notify(title, message, NotificationType.WARNING)