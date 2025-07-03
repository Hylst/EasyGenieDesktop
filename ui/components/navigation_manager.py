"""Navigation Manager for Application Routing.

This module provides a centralized navigation system for managing views,
routing between different tools, and handling navigation state.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from pathlib import Path

from .theme_manager import get_theme_manager, get_color, get_font, get_spacing
from .widget_factory import get_widget_factory, ButtonStyle, FrameStyle, TextStyle


class NavigationType(Enum):
    """Types of navigation."""
    PUSH = "push"  # Add new view to stack
    REPLACE = "replace"  # Replace current view
    POP = "pop"  # Remove current view
    RESET = "reset"  # Clear stack and set new view
    MODAL = "modal"  # Show as modal


class ViewType(Enum):
    """Types of views."""
    TOOL = "tool"  # Productivity tool
    SETTINGS = "settings"  # Settings page
    HELP = "help"  # Help/documentation
    ABOUT = "about"  # About page
    DASHBOARD = "dashboard"  # Main dashboard
    CUSTOM = "custom"  # Custom view


class NavigationEvent(Enum):
    """Navigation events."""
    BEFORE_NAVIGATE = "before_navigate"
    AFTER_NAVIGATE = "after_navigate"
    VIEW_LOADED = "view_loaded"
    VIEW_UNLOADED = "view_unloaded"
    NAVIGATION_ERROR = "navigation_error"


@dataclass
class NavigationItem:
    """Navigation item configuration."""
    id: str
    title: str
    icon: Optional[str] = None
    description: str = ""
    view_type: ViewType = ViewType.CUSTOM
    view_class: Optional[type] = None
    view_factory: Optional[Callable] = None
    
    # Navigation properties
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    order: int = 0
    
    # Visibility and access
    visible: bool = True
    enabled: bool = True
    requires_auth: bool = False
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    category: str = ""
    
    # Custom properties
    custom_props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationState:
    """Current navigation state."""
    current_view_id: Optional[str] = None
    view_stack: List[str] = field(default_factory=list)
    modal_stack: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    
    # View data
    view_data: Dict[str, Any] = field(default_factory=dict)
    
    # Navigation metadata
    last_navigation_time: Optional[datetime] = None
    navigation_count: int = 0


@dataclass
class NavigationContext:
    """Context for navigation operations."""
    from_view_id: Optional[str] = None
    to_view_id: str = ""
    navigation_type: NavigationType = NavigationType.PUSH
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Navigation options
    animated: bool = True
    save_state: bool = True
    clear_history: bool = False


class BaseView:
    """Base class for all views."""
    
    def __init__(self, parent, navigation_manager, view_id: str):
        """Initialize base view.
        
        Args:
            parent: Parent widget
            navigation_manager: Navigation manager instance
            view_id: View identifier
        """
        self.parent = parent
        self.navigation_manager = navigation_manager
        self.view_id = view_id
        self.widget = None
        self.is_loaded = False
        self.is_visible = False
        
        # View state
        self.view_data = {}
        
        # Create main widget
        self.create_widget()
    
    def create_widget(self):
        """Create the main widget for this view. Override in subclasses."""
        self.widget = ctk.CTkFrame(self.parent)
    
    def on_load(self, context: NavigationContext):
        """Called when view is loaded. Override in subclasses.
        
        Args:
            context: Navigation context
        """
        self.is_loaded = True
    
    def on_unload(self, context: NavigationContext):
        """Called when view is unloaded. Override in subclasses.
        
        Args:
            context: Navigation context
        """
        self.is_loaded = False
    
    def on_show(self, context: NavigationContext):
        """Called when view is shown. Override in subclasses.
        
        Args:
            context: Navigation context
        """
        if self.widget:
            self.widget.pack(fill="both", expand=True)
        self.is_visible = True
    
    def on_hide(self, context: NavigationContext):
        """Called when view is hidden. Override in subclasses.
        
        Args:
            context: Navigation context
        """
        if self.widget:
            self.widget.pack_forget()
        self.is_visible = False
    
    def on_data_changed(self, data: Dict[str, Any]):
        """Called when view data changes. Override in subclasses.
        
        Args:
            data: Updated view data
        """
        self.view_data.update(data)
    
    def get_widget(self):
        """Get the main widget for this view.
        
        Returns:
            Widget: Main widget
        """
        return self.widget
    
    def get_data(self) -> Dict[str, Any]:
        """Get view data.
        
        Returns:
            Dict[str, Any]: View data
        """
        return self.view_data.copy()
    
    def set_data(self, data: Dict[str, Any]):
        """Set view data.
        
        Args:
            data: View data to set
        """
        self.view_data = data.copy()
        self.on_data_changed(data)
    
    def update_data(self, data: Dict[str, Any]):
        """Update view data.
        
        Args:
            data: Data to update
        """
        self.view_data.update(data)
        self.on_data_changed(data)
    
    def destroy(self):
        """Destroy the view."""
        if self.widget:
            self.widget.destroy()
        self.is_loaded = False
        self.is_visible = False


class DashboardView(BaseView):
    """Default dashboard view."""
    
    def create_widget(self):
        """Create dashboard widget."""
        self.widget = ctk.CTkFrame(self.parent)
        
        # Welcome message
        welcome_label = ctk.CTkLabel(
            self.widget,
            text="Welcome to Easy Genie Desktop",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_label.pack(pady=20)
        
        # Description
        desc_label = ctk.CTkLabel(
            self.widget,
            text="Your AI-powered productivity companion",
            font=ctk.CTkFont(size=14),
            text_color=get_color("text_secondary")
        )
        desc_label.pack(pady=(0, 30))
        
        # Quick access buttons
        self.create_quick_access()
    
    def create_quick_access(self):
        """Create quick access buttons."""
        quick_frame = ctk.CTkFrame(self.widget)
        quick_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            quick_frame,
            text="Quick Access",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Button grid
        button_frame = ctk.CTkFrame(quick_frame)
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tools = [
            ("Task Breaker", "task_breaker"),
            ("TimeFocus", "time_focus"),
            ("Priority Grid", "priority_grid"),
            ("Brain Dump", "brain_dump"),
            ("Formalizer", "formalizer"),
            ("Routine Builder", "routine_builder"),
            ("Immersive Reader", "immersive_reader")
        ]
        
        for i, (title, tool_id) in enumerate(tools):
            row = i // 3
            col = i % 3
            
            button = ctk.CTkButton(
                button_frame,
                text=title,
                command=lambda tid=tool_id: self.navigation_manager.navigate_to(tid)
            )
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid weights
        for i in range(3):
            button_frame.grid_columnconfigure(i, weight=1)


class SettingsView(BaseView):
    """Settings view."""
    
    def create_widget(self):
        """Create settings widget."""
        self.widget = ctk.CTkScrollableFrame(self.parent)
        
        # Title
        title_label = ctk.CTkLabel(
            self.widget,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Theme settings
        self.create_theme_settings()
        
        # General settings
        self.create_general_settings()
    
    def create_theme_settings(self):
        """Create theme settings section."""
        theme_frame = ctk.CTkFrame(self.widget)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        theme_label.pack(pady=(10, 5))
        
        # Theme selector
        theme_manager = get_theme_manager()
        themes = theme_manager.get_available_themes()
        
        self.theme_var = tk.StringVar(value=theme_manager.current_theme.name if theme_manager.current_theme else "Dark Default")
        
        theme_combo = ctk.CTkComboBox(
            theme_frame,
            values=themes,
            variable=self.theme_var,
            command=self.on_theme_changed
        )
        theme_combo.pack(pady=5, padx=10, fill="x")
    
    def create_general_settings(self):
        """Create general settings section."""
        general_frame = ctk.CTkFrame(self.widget)
        general_frame.pack(fill="x", padx=10, pady=5)
        
        general_label = ctk.CTkLabel(
            general_frame,
            text="General",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        general_label.pack(pady=(10, 5))
        
        # Auto-save setting
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_check = ctk.CTkCheckBox(
            general_frame,
            text="Auto-save data",
            variable=self.auto_save_var
        )
        auto_save_check.pack(pady=5, padx=10, anchor="w")
        
        # Notifications setting
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_check = ctk.CTkCheckBox(
            general_frame,
            text="Enable notifications",
            variable=self.notifications_var
        )
        notifications_check.pack(pady=5, padx=10, anchor="w")
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change.
        
        Args:
            theme_name: Selected theme name
        """
        theme_manager = get_theme_manager()
        theme_manager.set_theme(theme_name)


class NavigationManager:
    """Centralized navigation management system."""
    
    def __init__(self, parent_widget):
        """Initialize navigation manager.
        
        Args:
            parent_widget: Parent widget for views
        """
        self.parent_widget = parent_widget
        self.theme_manager = get_theme_manager()
        self.widget_factory = get_widget_factory()
        
        # Navigation items
        self.navigation_items: Dict[str, NavigationItem] = {}
        
        # Views
        self.views: Dict[str, BaseView] = {}
        
        # Navigation state
        self.state = NavigationState()
        
        # Event handlers
        self.event_handlers: Dict[NavigationEvent, List[Callable]] = {
            event: [] for event in NavigationEvent
        }
        
        # Initialize default navigation items
        self._initialize_default_items()
    
    def _initialize_default_items(self):
        """Initialize default navigation items."""
        # Dashboard
        self.register_navigation_item(NavigationItem(
            id="dashboard",
            title="Dashboard",
            icon="🏠",
            description="Main dashboard",
            view_type=ViewType.DASHBOARD,
            view_class=DashboardView,
            order=0
        ))
        
        # Tools
        tools = [
            ("task_breaker", "Task Breaker", "🔨", "Break down complex tasks"),
            ("time_focus", "TimeFocus", "⏰", "Pomodoro timer with focus modes"),
            ("priority_grid", "Priority Grid", "📊", "Eisenhower matrix for prioritization"),
            ("brain_dump", "Brain Dump", "🧠", "Quick note capture"),
            ("formalizer", "Formalizer", "📝", "Transform informal text"),
            ("routine_builder", "Routine Builder", "🔄", "Build and track routines"),
            ("immersive_reader", "Immersive Reader", "📖", "Distraction-free reading")
        ]
        
        for i, (tool_id, title, icon, description) in enumerate(tools):
            self.register_navigation_item(NavigationItem(
                id=tool_id,
                title=title,
                icon=icon,
                description=description,
                view_type=ViewType.TOOL,
                order=i + 1,
                category="tools"
            ))
        
        # Settings
        self.register_navigation_item(NavigationItem(
            id="settings",
            title="Settings",
            icon="⚙️",
            description="Application settings",
            view_type=ViewType.SETTINGS,
            view_class=SettingsView,
            order=100
        ))
        
        # Help
        self.register_navigation_item(NavigationItem(
            id="help",
            title="Help",
            icon="❓",
            description="Help and documentation",
            view_type=ViewType.HELP,
            order=101
        ))
        
        # About
        self.register_navigation_item(NavigationItem(
            id="about",
            title="About",
            icon="ℹ️",
            description="About Easy Genie Desktop",
            view_type=ViewType.ABOUT,
            order=102
        ))
    
    def register_navigation_item(self, item: NavigationItem):
        """Register a navigation item.
        
        Args:
            item: Navigation item to register
        """
        self.navigation_items[item.id] = item
        
        # Handle parent-child relationships
        if item.parent_id and item.parent_id in self.navigation_items:
            parent = self.navigation_items[item.parent_id]
            if item.id not in parent.children:
                parent.children.append(item.id)
    
    def unregister_navigation_item(self, item_id: str):
        """Unregister a navigation item.
        
        Args:
            item_id: ID of item to unregister
        """
        if item_id in self.navigation_items:
            item = self.navigation_items[item_id]
            
            # Remove from parent's children
            if item.parent_id and item.parent_id in self.navigation_items:
                parent = self.navigation_items[item.parent_id]
                if item_id in parent.children:
                    parent.children.remove(item_id)
            
            # Remove children
            for child_id in item.children.copy():
                self.unregister_navigation_item(child_id)
            
            # Remove view if exists
            if item_id in self.views:
                self.views[item_id].destroy()
                del self.views[item_id]
            
            # Remove item
            del self.navigation_items[item_id]
    
    def get_navigation_items(self, category: str = None, parent_id: str = None) -> List[NavigationItem]:
        """Get navigation items.
        
        Args:
            category: Filter by category
            parent_id: Filter by parent ID
            
        Returns:
            List[NavigationItem]: Filtered navigation items
        """
        items = list(self.navigation_items.values())
        
        # Filter by category
        if category:
            items = [item for item in items if item.category == category]
        
        # Filter by parent
        if parent_id:
            items = [item for item in items if item.parent_id == parent_id]
        
        # Filter visible items
        items = [item for item in items if item.visible]
        
        # Sort by order
        items.sort(key=lambda x: x.order)
        
        return items
    
    def navigate_to(self, view_id: str, navigation_type: NavigationType = NavigationType.PUSH, 
                   data: Dict[str, Any] = None, **kwargs) -> bool:
        """Navigate to a view.
        
        Args:
            view_id: ID of view to navigate to
            navigation_type: Type of navigation
            data: Data to pass to view
            **kwargs: Additional navigation options
            
        Returns:
            bool: True if navigation was successful
        """
        if view_id not in self.navigation_items:
            self._emit_event(NavigationEvent.NAVIGATION_ERROR, {
                "error": f"View '{view_id}' not found",
                "view_id": view_id
            })
            return False
        
        # Create navigation context
        context = NavigationContext(
            from_view_id=self.state.current_view_id,
            to_view_id=view_id,
            navigation_type=navigation_type,
            data=data or {},
            **kwargs
        )
        
        # Emit before navigate event
        if not self._emit_event(NavigationEvent.BEFORE_NAVIGATE, context):
            return False
        
        try:
            # Handle current view
            if self.state.current_view_id:
                current_view = self.views.get(self.state.current_view_id)
                if current_view:
                    current_view.on_hide(context)
                    
                    if navigation_type in [NavigationType.REPLACE, NavigationType.RESET]:
                        current_view.on_unload(context)
            
            # Create or get target view
            target_view = self._get_or_create_view(view_id)
            if not target_view:
                return False
            
            # Load view if not loaded
            if not target_view.is_loaded:
                target_view.on_load(context)
                self._emit_event(NavigationEvent.VIEW_LOADED, {
                    "view_id": view_id,
                    "view": target_view
                })
            
            # Update view data
            if context.data:
                target_view.update_data(context.data)
            
            # Show target view
            target_view.on_show(context)
            
            # Update navigation state
            self._update_navigation_state(context)
            
            # Emit after navigate event
            self._emit_event(NavigationEvent.AFTER_NAVIGATE, context)
            
            return True
            
        except Exception as e:
            self._emit_event(NavigationEvent.NAVIGATION_ERROR, {
                "error": str(e),
                "view_id": view_id,
                "context": context
            })
            return False
    
    def _get_or_create_view(self, view_id: str) -> Optional[BaseView]:
        """Get or create a view.
        
        Args:
            view_id: View ID
            
        Returns:
            Optional[BaseView]: View instance or None
        """
        # Return existing view
        if view_id in self.views:
            return self.views[view_id]
        
        # Get navigation item
        nav_item = self.navigation_items.get(view_id)
        if not nav_item:
            return None
        
        # Create view
        try:
            if nav_item.view_class:
                view = nav_item.view_class(self.parent_widget, self, view_id)
            elif nav_item.view_factory:
                view = nav_item.view_factory(self.parent_widget, self, view_id)
            else:
                # Create default view based on type
                if nav_item.view_type == ViewType.TOOL:
                    view = self._create_tool_view(view_id, nav_item)
                else:
                    view = BaseView(self.parent_widget, self, view_id)
            
            self.views[view_id] = view
            return view
            
        except Exception as e:
            print(f"Error creating view '{view_id}': {e}")
            return None
    
    def _create_tool_view(self, view_id: str, nav_item: NavigationItem) -> BaseView:
        """Create a tool view.
        
        Args:
            view_id: View ID
            nav_item: Navigation item
            
        Returns:
            BaseView: Tool view
        """
        # Try to import and create tool view
        try:
            if view_id == "task_breaker":
                from ...tools.task_breaker import TaskBreakerTool
                tool_widget = TaskBreakerTool(self.parent_widget)
                
                # Create wrapper view
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "time_focus":
                from ...tools.time_focus import TimeFocusTool
                tool_widget = TimeFocusTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "priority_grid":
                from ...tools.priority_grid import PriorityGridTool
                tool_widget = PriorityGridTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "brain_dump":
                from ...tools.brain_dump import BrainDumpTool
                tool_widget = BrainDumpTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "formalizer":
                from ...tools.formalizer import FormalizerTool
                tool_widget = FormalizerTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "routine_builder":
                from ...tools.routine_builder import RoutineBuilderTool
                tool_widget = RoutineBuilderTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
            elif view_id == "immersive_reader":
                from ...tools.immersive_reader import ImmersiveReaderTool
                tool_widget = ImmersiveReaderTool(self.parent_widget)
                
                view = BaseView(self.parent_widget, self, view_id)
                view.widget = tool_widget
                return view
                
        except ImportError as e:
            print(f"Could not import tool '{view_id}': {e}")
        
        # Create placeholder view
        view = BaseView(self.parent_widget, self, view_id)
        
        # Add placeholder content
        placeholder_label = ctk.CTkLabel(
            view.widget,
            text=f"{nav_item.title}\n\nTool not available",
            font=ctk.CTkFont(size=16)
        )
        placeholder_label.pack(expand=True)
        
        return view
    
    def _update_navigation_state(self, context: NavigationContext):
        """Update navigation state.
        
        Args:
            context: Navigation context
        """
        # Update current view
        previous_view = self.state.current_view_id
        self.state.current_view_id = context.to_view_id
        
        # Update stacks based on navigation type
        if context.navigation_type == NavigationType.PUSH:
            if previous_view:
                self.state.view_stack.append(previous_view)
        elif context.navigation_type == NavigationType.REPLACE:
            # Stack remains the same
            pass
        elif context.navigation_type == NavigationType.POP:
            if self.state.view_stack:
                self.state.view_stack.pop()
        elif context.navigation_type == NavigationType.RESET:
            self.state.view_stack.clear()
            self.state.modal_stack.clear()
        elif context.navigation_type == NavigationType.MODAL:
            self.state.modal_stack.append(context.to_view_id)
        
        # Update history
        if context.to_view_id not in self.state.history:
            self.state.history.append(context.to_view_id)
        
        # Update metadata
        self.state.last_navigation_time = datetime.now()
        self.state.navigation_count += 1
        
        # Store view data
        if context.data:
            self.state.view_data[context.to_view_id] = context.data
    
    def go_back(self) -> bool:
        """Navigate back to previous view.
        
        Returns:
            bool: True if navigation was successful
        """
        if not self.state.view_stack:
            return False
        
        previous_view_id = self.state.view_stack[-1]
        return self.navigate_to(previous_view_id, NavigationType.POP)
    
    def go_home(self) -> bool:
        """Navigate to dashboard.
        
        Returns:
            bool: True if navigation was successful
        """
        return self.navigate_to("dashboard", NavigationType.RESET)
    
    def can_go_back(self) -> bool:
        """Check if can navigate back.
        
        Returns:
            bool: True if can go back
        """
        return len(self.state.view_stack) > 0
    
    def get_current_view(self) -> Optional[BaseView]:
        """Get current view.
        
        Returns:
            Optional[BaseView]: Current view or None
        """
        if self.state.current_view_id:
            return self.views.get(self.state.current_view_id)
        return None
    
    def get_current_view_id(self) -> Optional[str]:
        """Get current view ID.
        
        Returns:
            Optional[str]: Current view ID or None
        """
        return self.state.current_view_id
    
    def get_navigation_history(self) -> List[str]:
        """Get navigation history.
        
        Returns:
            List[str]: Navigation history
        """
        return self.state.history.copy()
    
    def clear_history(self):
        """Clear navigation history."""
        self.state.history.clear()
    
    def add_event_handler(self, event: NavigationEvent, handler: Callable):
        """Add event handler.
        
        Args:
            event: Navigation event
            handler: Event handler function
        """
        if handler not in self.event_handlers[event]:
            self.event_handlers[event].append(handler)
    
    def remove_event_handler(self, event: NavigationEvent, handler: Callable):
        """Remove event handler.
        
        Args:
            event: Navigation event
            handler: Event handler function
        """
        if handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)
    
    def _emit_event(self, event: NavigationEvent, data: Any = None) -> bool:
        """Emit navigation event.
        
        Args:
            event: Navigation event
            data: Event data
            
        Returns:
            bool: True if event was not cancelled
        """
        for handler in self.event_handlers[event]:
            try:
                result = handler(event, data)
                if result is False:  # Handler can cancel event
                    return False
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        return True
    
    def destroy(self):
        """Destroy navigation manager and all views."""
        # Destroy all views
        for view in self.views.values():
            view.destroy()
        
        # Clear state
        self.views.clear()
        self.navigation_items.clear()
        self.event_handlers.clear()
        self.state = NavigationState()


# Global navigation manager instance
_navigation_manager: Optional[NavigationManager] = None


def get_navigation_manager() -> Optional[NavigationManager]:
    """Get global navigation manager instance.
    
    Returns:
        Optional[NavigationManager]: Global navigation manager or None
    """
    return _navigation_manager


def set_navigation_manager(manager: NavigationManager):
    """Set global navigation manager instance.
    
    Args:
        manager: Navigation manager to set
    """
    global _navigation_manager
    _navigation_manager = manager


# Convenience functions
def navigate_to(view_id: str, **kwargs) -> bool:
    """Navigate to a view (convenience function).
    
    Args:
        view_id: View ID
        **kwargs: Navigation options
        
    Returns:
        bool: True if navigation was successful
    """
    manager = get_navigation_manager()
    if manager:
        return manager.navigate_to(view_id, **kwargs)
    return False


def go_back() -> bool:
    """Go back (convenience function).
    
    Returns:
        bool: True if navigation was successful
    """
    manager = get_navigation_manager()
    if manager:
        return manager.go_back()
    return False


def go_home() -> bool:
    """Go home (convenience function).
    
    Returns:
        bool: True if navigation was successful
    """
    manager = get_navigation_manager()
    if manager:
        return manager.go_home()
    return False