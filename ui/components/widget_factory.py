"""Widget Factory for Reusable UI Components.

This module provides a factory system for creating consistent, themed UI components
that can be reused across the application with standardized behavior and styling.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .theme_manager import get_theme_manager, FontSize, get_color, get_font, get_spacing


class WidgetType(Enum):
    """Types of widgets that can be created."""
    BUTTON = "button"
    LABEL = "label"
    ENTRY = "entry"
    TEXT = "text"
    FRAME = "frame"
    SCROLLABLE_FRAME = "scrollable_frame"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    COMBOBOX = "combobox"
    SLIDER = "slider"
    PROGRESS_BAR = "progress_bar"
    SWITCH = "switch"
    TABVIEW = "tabview"
    SEGMENTED_BUTTON = "segmented_button"
    OPTION_MENU = "option_menu"
    TEXTBOX = "textbox"
    SCROLLBAR = "scrollbar"
    SEPARATOR = "separator"
    TOOLTIP = "tooltip"
    CARD = "card"
    PANEL = "panel"
    TOOLBAR = "toolbar"
    STATUS_BAR = "status_bar"
    NOTIFICATION = "notification"
    BADGE = "badge"
    AVATAR = "avatar"
    ICON_BUTTON = "icon_button"
    SEARCH_BOX = "search_box"
    TAG = "tag"
    BREADCRUMB = "breadcrumb"


class ButtonStyle(Enum):
    """Button style variants."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    OUTLINE = "outline"
    GHOST = "ghost"
    LINK = "link"


class FrameStyle(Enum):
    """Frame style variants."""
    DEFAULT = "default"
    CARD = "card"
    PANEL = "panel"
    SIDEBAR = "sidebar"
    HEADER = "header"
    FOOTER = "footer"
    MODAL = "modal"
    POPUP = "popup"


class TextStyle(Enum):
    """Text style variants."""
    BODY = "body"
    CAPTION = "caption"
    SUBTITLE = "subtitle"
    TITLE = "title"
    HEADER = "header"
    DISPLAY = "display"
    CODE = "code"
    LINK = "link"


@dataclass
class WidgetConfig:
    """Configuration for widget creation."""
    widget_type: WidgetType
    
    # Common properties
    width: Optional[int] = None
    height: Optional[int] = None
    padding: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = None
    margin: Union[int, Tuple[int, int], Tuple[int, int, int, int]] = None
    
    # Text properties
    text: str = ""
    font_size: FontSize = FontSize.MEDIUM
    font_weight: str = "normal"
    font_style: str = "normal"
    text_color: Optional[str] = None
    
    # Background and border
    bg_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: int = 0
    corner_radius: Optional[int] = None
    
    # State properties
    enabled: bool = True
    visible: bool = True
    
    # Event handlers
    on_click: Optional[Callable] = None
    on_change: Optional[Callable] = None
    on_focus: Optional[Callable] = None
    on_blur: Optional[Callable] = None
    
    # Style variants
    style: Optional[str] = None
    
    # Custom properties
    custom_props: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.custom_props is None:
            self.custom_props = {}


class BaseWidget:
    """Base class for all factory-created widgets."""
    
    def __init__(self, parent, config: WidgetConfig):
        """Initialize base widget.
        
        Args:
            parent: Parent widget
            config: Widget configuration
        """
        self.parent = parent
        self.config = config
        self.widget = None
        self.theme_manager = get_theme_manager()
        
        # Create the actual widget
        self._create_widget()
        
        # Apply styling
        self._apply_styling()
        
        # Bind events
        self._bind_events()
        
        # Apply state
        self._apply_state()
    
    def _create_widget(self):
        """Create the actual widget. Override in subclasses."""
        pass
    
    def _apply_styling(self):
        """Apply styling to the widget."""
        if not self.widget:
            return
        
        # Apply dimensions
        if self.config.width is not None:
            self.widget.configure(width=self.config.width)
        if self.config.height is not None:
            self.widget.configure(height=self.config.height)
        
        # Apply colors
        if self.config.bg_color:
            try:
                self.widget.configure(fg_color=self.config.bg_color)
            except:
                try:
                    self.widget.configure(bg=self.config.bg_color)
                except:
                    pass
        
        if self.config.text_color:
            try:
                self.widget.configure(text_color=self.config.text_color)
            except:
                try:
                    self.widget.configure(fg=self.config.text_color)
                except:
                    pass
        
        # Apply border
        if self.config.border_width > 0:
            try:
                self.widget.configure(border_width=self.config.border_width)
            except:
                pass
        
        if self.config.border_color:
            try:
                self.widget.configure(border_color=self.config.border_color)
            except:
                pass
        
        # Apply corner radius
        if self.config.corner_radius is not None:
            try:
                self.widget.configure(corner_radius=self.config.corner_radius)
            except:
                pass
        
        # Apply font
        if hasattr(self.widget, 'configure') and 'font' in self.widget.configure():
            font_config = get_font(self.config.font_size, self.config.font_weight, self.config.font_style)
            try:
                self.widget.configure(font=ctk.CTkFont(family=font_config[0], size=font_config[1]))
            except:
                pass
    
    def _bind_events(self):
        """Bind event handlers."""
        if not self.widget:
            return
        
        if self.config.on_click:
            try:
                self.widget.configure(command=self.config.on_click)
            except:
                try:
                    self.widget.bind("<Button-1>", lambda e: self.config.on_click())
                except:
                    pass
        
        if self.config.on_focus:
            try:
                self.widget.bind("<FocusIn>", lambda e: self.config.on_focus())
            except:
                pass
        
        if self.config.on_blur:
            try:
                self.widget.bind("<FocusOut>", lambda e: self.config.on_blur())
            except:
                pass
    
    def _apply_state(self):
        """Apply widget state."""
        if not self.widget:
            return
        
        # Apply enabled state
        if not self.config.enabled:
            try:
                self.widget.configure(state="disabled")
            except:
                pass
        
        # Apply visibility
        if not self.config.visible:
            try:
                self.widget.pack_forget()
            except:
                try:
                    self.widget.grid_forget()
                except:
                    pass
    
    def get_widget(self):
        """Get the underlying widget.
        
        Returns:
            Widget: The actual widget instance
        """
        return self.widget
    
    def pack(self, **kwargs):
        """Pack the widget.
        
        Args:
            **kwargs: Pack options
        """
        if self.widget:
            self.widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the widget.
        
        Args:
            **kwargs: Grid options
        """
        if self.widget:
            self.widget.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the widget.
        
        Args:
            **kwargs: Place options
        """
        if self.widget:
            self.widget.place(**kwargs)
    
    def configure(self, **kwargs):
        """Configure the widget.
        
        Args:
            **kwargs: Configuration options
        """
        if self.widget:
            self.widget.configure(**kwargs)
    
    def destroy(self):
        """Destroy the widget."""
        if self.widget:
            self.widget.destroy()


class ButtonWidget(BaseWidget):
    """Factory-created button widget."""
    
    def _create_widget(self):
        """Create button widget."""
        self.widget = ctk.CTkButton(
            self.parent,
            text=self.config.text
        )
        
        # Apply button style
        if self.config.style:
            self._apply_button_style(self.config.style)
    
    def _apply_button_style(self, style: str):
        """Apply button style.
        
        Args:
            style: Button style name
        """
        if style == ButtonStyle.PRIMARY.value:
            self.widget.configure(
                fg_color=get_color("primary"),
                hover_color=get_color("primary_hover")
            )
        elif style == ButtonStyle.SECONDARY.value:
            self.widget.configure(
                fg_color=get_color("secondary"),
                hover_color=get_color("secondary_hover")
            )
        elif style == ButtonStyle.SUCCESS.value:
            self.widget.configure(
                fg_color=get_color("success"),
                hover_color=get_color("success")
            )
        elif style == ButtonStyle.WARNING.value:
            self.widget.configure(
                fg_color=get_color("warning"),
                hover_color=get_color("warning")
            )
        elif style == ButtonStyle.ERROR.value:
            self.widget.configure(
                fg_color=get_color("error"),
                hover_color=get_color("error")
            )
        elif style == ButtonStyle.OUTLINE.value:
            self.widget.configure(
                fg_color="transparent",
                border_width=2,
                border_color=get_color("primary"),
                text_color=get_color("primary")
            )
        elif style == ButtonStyle.GHOST.value:
            self.widget.configure(
                fg_color="transparent",
                hover_color=get_color("bg_hover"),
                text_color=get_color("text_primary")
            )


class LabelWidget(BaseWidget):
    """Factory-created label widget."""
    
    def _create_widget(self):
        """Create label widget."""
        self.widget = ctk.CTkLabel(
            self.parent,
            text=self.config.text
        )
        
        # Apply text style
        if self.config.style:
            self._apply_text_style(self.config.style)
    
    def _apply_text_style(self, style: str):
        """Apply text style.
        
        Args:
            style: Text style name
        """
        if style == TextStyle.TITLE.value:
            font_config = get_font(FontSize.LARGE, "bold")
            self.widget.configure(
                font=ctk.CTkFont(family=font_config[0], size=font_config[1], weight="bold")
            )
        elif style == TextStyle.HEADER.value:
            font_config = get_font(FontSize.EXTRA_LARGE, "bold")
            self.widget.configure(
                font=ctk.CTkFont(family=font_config[0], size=font_config[1], weight="bold")
            )
        elif style == TextStyle.CAPTION.value:
            font_config = get_font(FontSize.SMALL)
            self.widget.configure(
                font=ctk.CTkFont(family=font_config[0], size=font_config[1]),
                text_color=get_color("text_secondary")
            )
        elif style == TextStyle.CODE.value:
            self.widget.configure(
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=get_color("text_accent")
            )
        elif style == TextStyle.LINK.value:
            self.widget.configure(
                text_color=get_color("primary"),
                cursor="hand2"
            )


class EntryWidget(BaseWidget):
    """Factory-created entry widget."""
    
    def _create_widget(self):
        """Create entry widget."""
        self.widget = ctk.CTkEntry(
            self.parent,
            placeholder_text=self.config.text
        )
    
    def _bind_events(self):
        """Bind entry-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.bind("<KeyRelease>", lambda e: self.config.on_change(self.widget.get()))


class FrameWidget(BaseWidget):
    """Factory-created frame widget."""
    
    def _create_widget(self):
        """Create frame widget."""
        self.widget = ctk.CTkFrame(self.parent)
        
        # Apply frame style
        if self.config.style:
            self._apply_frame_style(self.config.style)
    
    def _apply_frame_style(self, style: str):
        """Apply frame style.
        
        Args:
            style: Frame style name
        """
        if style == FrameStyle.CARD.value:
            self.widget.configure(
                corner_radius=get_spacing("radius_lg"),
                border_width=1,
                border_color=get_color("border_secondary")
            )
        elif style == FrameStyle.PANEL.value:
            self.widget.configure(
                fg_color=get_color("bg_secondary"),
                corner_radius=get_spacing("radius_md")
            )
        elif style == FrameStyle.SIDEBAR.value:
            self.widget.configure(
                fg_color=get_color("bg_tertiary"),
                corner_radius=0
            )
        elif style == FrameStyle.HEADER.value:
            self.widget.configure(
                fg_color=get_color("bg_secondary"),
                corner_radius=0,
                height=60
            )
        elif style == FrameStyle.MODAL.value:
            self.widget.configure(
                corner_radius=get_spacing("radius_xl"),
                border_width=2,
                border_color=get_color("border_primary")
            )


class ScrollableFrameWidget(BaseWidget):
    """Factory-created scrollable frame widget."""
    
    def _create_widget(self):
        """Create scrollable frame widget."""
        self.widget = ctk.CTkScrollableFrame(self.parent)


class CheckboxWidget(BaseWidget):
    """Factory-created checkbox widget."""
    
    def _create_widget(self):
        """Create checkbox widget."""
        self.widget = ctk.CTkCheckBox(
            self.parent,
            text=self.config.text
        )
    
    def _bind_events(self):
        """Bind checkbox-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.configure(command=lambda: self.config.on_change(self.widget.get()))


class ComboboxWidget(BaseWidget):
    """Factory-created combobox widget."""
    
    def _create_widget(self):
        """Create combobox widget."""
        values = self.config.custom_props.get("values", [])
        self.widget = ctk.CTkComboBox(
            self.parent,
            values=values
        )
    
    def _bind_events(self):
        """Bind combobox-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.configure(command=lambda value: self.config.on_change(value))


class SliderWidget(BaseWidget):
    """Factory-created slider widget."""
    
    def _create_widget(self):
        """Create slider widget."""
        from_value = self.config.custom_props.get("from_", 0)
        to_value = self.config.custom_props.get("to", 100)
        
        self.widget = ctk.CTkSlider(
            self.parent,
            from_=from_value,
            to=to_value
        )
    
    def _bind_events(self):
        """Bind slider-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.configure(command=lambda value: self.config.on_change(value))


class ProgressBarWidget(BaseWidget):
    """Factory-created progress bar widget."""
    
    def _create_widget(self):
        """Create progress bar widget."""
        self.widget = ctk.CTkProgressBar(self.parent)


class SwitchWidget(BaseWidget):
    """Factory-created switch widget."""
    
    def _create_widget(self):
        """Create switch widget."""
        self.widget = ctk.CTkSwitch(
            self.parent,
            text=self.config.text
        )
    
    def _bind_events(self):
        """Bind switch-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.configure(command=lambda: self.config.on_change(self.widget.get()))


class TabViewWidget(BaseWidget):
    """Factory-created tab view widget."""
    
    def _create_widget(self):
        """Create tab view widget."""
        self.widget = ctk.CTkTabview(self.parent)


class TextBoxWidget(BaseWidget):
    """Factory-created text box widget."""
    
    def _create_widget(self):
        """Create text box widget."""
        self.widget = ctk.CTkTextbox(self.parent)
    
    def _bind_events(self):
        """Bind textbox-specific events."""
        super()._bind_events()
        
        if self.config.on_change:
            self.widget.bind("<KeyRelease>", lambda e: self.config.on_change(self.widget.get("1.0", "end-1c")))


class WidgetFactory:
    """Factory for creating themed UI widgets."""
    
    def __init__(self):
        """Initialize widget factory."""
        self.theme_manager = get_theme_manager()
        
        # Widget class mapping
        self.widget_classes = {
            WidgetType.BUTTON: ButtonWidget,
            WidgetType.LABEL: LabelWidget,
            WidgetType.ENTRY: EntryWidget,
            WidgetType.FRAME: FrameWidget,
            WidgetType.SCROLLABLE_FRAME: ScrollableFrameWidget,
            WidgetType.CHECKBOX: CheckboxWidget,
            WidgetType.COMBOBOX: ComboboxWidget,
            WidgetType.SLIDER: SliderWidget,
            WidgetType.PROGRESS_BAR: ProgressBarWidget,
            WidgetType.SWITCH: SwitchWidget,
            WidgetType.TABVIEW: TabViewWidget,
            WidgetType.TEXTBOX: TextBoxWidget,
        }
    
    def create_widget(self, parent, config: WidgetConfig) -> BaseWidget:
        """Create a widget based on configuration.
        
        Args:
            parent: Parent widget
            config: Widget configuration
            
        Returns:
            BaseWidget: Created widget wrapper
        """
        widget_class = self.widget_classes.get(config.widget_type)
        if not widget_class:
            raise ValueError(f"Unsupported widget type: {config.widget_type}")
        
        return widget_class(parent, config)
    
    # Convenience methods for common widgets
    
    def create_button(self, parent, text: str, style: ButtonStyle = ButtonStyle.PRIMARY, 
                     on_click: Callable = None, **kwargs) -> BaseWidget:
        """Create a button widget.
        
        Args:
            parent: Parent widget
            text: Button text
            style: Button style
            on_click: Click handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Button widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.BUTTON,
            text=text,
            style=style.value,
            on_click=on_click,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_label(self, parent, text: str, style: TextStyle = TextStyle.BODY, **kwargs) -> BaseWidget:
        """Create a label widget.
        
        Args:
            parent: Parent widget
            text: Label text
            style: Text style
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Label widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.LABEL,
            text=text,
            style=style.value,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_entry(self, parent, placeholder: str = "", on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create an entry widget.
        
        Args:
            parent: Parent widget
            placeholder: Placeholder text
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Entry widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.ENTRY,
            text=placeholder,
            on_change=on_change,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_frame(self, parent, style: FrameStyle = FrameStyle.DEFAULT, **kwargs) -> BaseWidget:
        """Create a frame widget.
        
        Args:
            parent: Parent widget
            style: Frame style
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Frame widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.FRAME,
            style=style.value,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_scrollable_frame(self, parent, **kwargs) -> BaseWidget:
        """Create a scrollable frame widget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Scrollable frame widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.SCROLLABLE_FRAME,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_checkbox(self, parent, text: str, on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create a checkbox widget.
        
        Args:
            parent: Parent widget
            text: Checkbox text
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Checkbox widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.CHECKBOX,
            text=text,
            on_change=on_change,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_combobox(self, parent, values: List[str], on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create a combobox widget.
        
        Args:
            parent: Parent widget
            values: Combobox values
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Combobox widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.COMBOBOX,
            on_change=on_change,
            custom_props={"values": values},
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_slider(self, parent, from_: float = 0, to: float = 100, 
                     on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create a slider widget.
        
        Args:
            parent: Parent widget
            from_: Minimum value
            to: Maximum value
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Slider widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.SLIDER,
            on_change=on_change,
            custom_props={"from_": from_, "to": to},
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_progress_bar(self, parent, **kwargs) -> BaseWidget:
        """Create a progress bar widget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Progress bar widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.PROGRESS_BAR,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_switch(self, parent, text: str, on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create a switch widget.
        
        Args:
            parent: Parent widget
            text: Switch text
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Switch widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.SWITCH,
            text=text,
            on_change=on_change,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_tabview(self, parent, **kwargs) -> BaseWidget:
        """Create a tab view widget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Tab view widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.TABVIEW,
            **kwargs
        )
        return self.create_widget(parent, config)
    
    def create_textbox(self, parent, on_change: Callable = None, **kwargs) -> BaseWidget:
        """Create a textbox widget.
        
        Args:
            parent: Parent widget
            on_change: Change handler
            **kwargs: Additional configuration
            
        Returns:
            BaseWidget: Textbox widget
        """
        config = WidgetConfig(
            widget_type=WidgetType.TEXTBOX,
            on_change=on_change,
            **kwargs
        )
        return self.create_widget(parent, config)


# Global widget factory instance
_widget_factory: Optional[WidgetFactory] = None


def get_widget_factory() -> WidgetFactory:
    """Get global widget factory instance.
    
    Returns:
        WidgetFactory: Global widget factory
    """
    global _widget_factory
    if _widget_factory is None:
        _widget_factory = WidgetFactory()
    return _widget_factory


# Convenience functions
def create_button(parent, text: str, style: ButtonStyle = ButtonStyle.PRIMARY, 
                 on_click: Callable = None, **kwargs) -> BaseWidget:
    """Create a button widget (convenience function)."""
    return get_widget_factory().create_button(parent, text, style, on_click, **kwargs)


def create_label(parent, text: str, style: TextStyle = TextStyle.BODY, **kwargs) -> BaseWidget:
    """Create a label widget (convenience function)."""
    return get_widget_factory().create_label(parent, text, style, **kwargs)


def create_entry(parent, placeholder: str = "", on_change: Callable = None, **kwargs) -> BaseWidget:
    """Create an entry widget (convenience function)."""
    return get_widget_factory().create_entry(parent, placeholder, on_change, **kwargs)


def create_frame(parent, style: FrameStyle = FrameStyle.DEFAULT, **kwargs) -> BaseWidget:
    """Create a frame widget (convenience function)."""
    return get_widget_factory().create_frame(parent, style, **kwargs)