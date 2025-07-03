# -*- coding: utf-8 -*-
"""
Reusable Dialog Components for Easy Genie Desktop
Created by: Geoffroy Streit

Collection of reusable dialog components with i18n support.
"""

import customtkinter as ctk
from typing import Optional, Callable, Any, Dict, List
import logging
from core.i18n import get_text as _

logger = logging.getLogger(__name__)

class BaseDialog(ctk.CTkToplevel):
    """Base class for all dialogs with common functionality."""
    
    def __init__(self, 
                 parent,
                 title: str = "",
                 width: int = 400,
                 height: int = 300,
                 resizable: bool = False,
                 modal: bool = True,
                 **kwargs):
        """
        Initialize the base dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width
            height: Dialog height
            resizable: Whether dialog is resizable
            modal: Whether dialog is modal
            **kwargs: Additional arguments
        """
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.result = None
        self.callback = None
        
        # Configure dialog
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        if not resizable:
            self.resizable(False, False)
        
        # Center dialog on parent
        self._center_on_parent()
        
        # Make modal if requested
        if modal:
            self.transient(parent)
            self.grab_set()
        
        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Focus on dialog
        self.focus()
    
    def _center_on_parent(self):
        """Center the dialog on its parent window."""
        self.update_idletasks()
        
        # Get parent geometry
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _on_close(self):
        """Handle dialog close event."""
        self.result = None
        self._cleanup()
        self.destroy()
    
    def _cleanup(self):
        """Cleanup before closing dialog."""
        pass
    
    def set_callback(self, callback: Callable[[Any], None]):
        """Set callback function for dialog result.
        
        Args:
            callback: Callback function
        """
        self.callback = callback
    
    def _finish_dialog(self, result: Any = None):
        """Finish dialog with result.
        
        Args:
            result: Dialog result
        """
        self.result = result
        
        if self.callback:
            try:
                self.callback(result)
            except Exception as e:
                logger.error(f"Error in dialog callback: {e}")
        
        self._cleanup()
        self.destroy()


class ConfirmationDialog(BaseDialog):
    """Confirmation dialog with Yes/No buttons."""
    
    def __init__(self, 
                 parent,
                 title: str = None,
                 message: str = "",
                 yes_text: str = None,
                 no_text: str = None,
                 icon: str = "question",
                 **kwargs):
        """
        Initialize the confirmation dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Confirmation message
            yes_text: Text for Yes button
            no_text: Text for No button
            icon: Icon type (question, warning, error, info)
            **kwargs: Additional arguments
        """
        # Set default texts with translations
        if title is None:
            title = _("buttons.confirm") if icon == "question" else _("status.warning")
        if yes_text is None:
            yes_text = _("buttons.ok")
        if no_text is None:
            no_text = _("buttons.cancel")
        
        super().__init__(parent, title=title, width=400, height=200, **kwargs)
        
        self.message = message
        self.yes_text = yes_text
        self.no_text = no_text
        self.icon = icon
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Icon and message frame
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Icon
        icon_symbols = {
            "question": "❓",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon_symbols.get(self.icon, "❓"),
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(10, 5))
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=(5, 20), padx=20)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons
        no_button = ctk.CTkButton(
            button_frame,
            text=self.no_text,
            command=self._on_no,
            width=100
        )
        no_button.pack(side="right", padx=(5, 10), pady=10)
        
        yes_button = ctk.CTkButton(
            button_frame,
            text=self.yes_text,
            command=self._on_yes,
            width=100
        )
        yes_button.pack(side="right", padx=5, pady=10)
        
        # Set focus on Yes button
        yes_button.focus()
    
    def _on_yes(self):
        """Handle Yes button click."""
        self._finish_dialog(True)
    
    def _on_no(self):
        """Handle No button click."""
        self._finish_dialog(False)


class InputDialog(BaseDialog):
    """Input dialog for getting text input from user."""
    
    def __init__(self, 
                 parent,
                 title: str = None,
                 prompt: str = "",
                 default_value: str = "",
                 placeholder: str = "",
                 multiline: bool = False,
                 password: bool = False,
                 **kwargs):
        """
        Initialize the input dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            prompt: Input prompt text
            default_value: Default input value
            placeholder: Placeholder text
            multiline: Whether to use multiline input
            password: Whether to hide input (password mode)
            **kwargs: Additional arguments
        """
        if title is None:
            title = _("ui_components.input_dialog")
        
        height = 300 if multiline else 200
        super().__init__(parent, title=title, width=450, height=height, **kwargs)
        
        self.prompt = prompt
        self.default_value = default_value
        self.placeholder = placeholder
        self.multiline = multiline
        self.password = password
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Content frame
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Prompt label
        if self.prompt:
            prompt_label = ctk.CTkLabel(
                content_frame,
                text=self.prompt,
                font=ctk.CTkFont(size=14),
                wraplength=400
            )
            prompt_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        # Input field
        if self.multiline:
            self.input_field = ctk.CTkTextbox(
                content_frame,
                height=100,
                font=ctk.CTkFont(size=12)
            )
            if self.default_value:
                self.input_field.insert("1.0", self.default_value)
        else:
            self.input_field = ctk.CTkEntry(
                content_frame,
                font=ctk.CTkFont(size=12),
                placeholder_text=self.placeholder,
                show="*" if self.password else None
            )
            if self.default_value:
                self.input_field.insert(0, self.default_value)
        
        self.input_field.pack(fill="x", padx=10, pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons
        cancel_button = ctk.CTkButton(
            button_frame,
            text=_("buttons.cancel"),
            command=self._on_cancel,
            width=100
        )
        cancel_button.pack(side="right", padx=(5, 10), pady=10)
        
        ok_button = ctk.CTkButton(
            button_frame,
            text=_("buttons.ok"),
            command=self._on_ok,
            width=100
        )
        ok_button.pack(side="right", padx=5, pady=10)
        
        # Set focus on input field
        self.input_field.focus()
        
        # Bind Enter key for single-line input
        if not self.multiline:
            self.input_field.bind("<Return>", lambda e: self._on_ok())
    
    def _on_ok(self):
        """Handle OK button click."""
        if self.multiline:
            value = self.input_field.get("1.0", "end-1c")
        else:
            value = self.input_field.get()
        
        self._finish_dialog(value)
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self._finish_dialog(None)


class ProgressDialog(BaseDialog):
    """Progress dialog for showing operation progress."""
    
    def __init__(self, 
                 parent,
                 title: str = None,
                 message: str = "",
                 cancellable: bool = False,
                 **kwargs):
        """
        Initialize the progress dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Progress message
            cancellable: Whether operation can be cancelled
            **kwargs: Additional arguments
        """
        if title is None:
            title = _("status.processing")
        
        super().__init__(parent, title=title, width=400, height=150, **kwargs)
        
        self.message = message
        self.cancellable = cancellable
        self.cancelled = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Content frame
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Message label
        self.message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=ctk.CTkFont(size=14)
        )
        self.message_label.pack(pady=(20, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            content_frame,
            width=300
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Cancel button (if cancellable)
        if self.cancellable:
            self.cancel_button = ctk.CTkButton(
                content_frame,
                text=_("buttons.cancel"),
                command=self._on_cancel,
                width=100
            )
            self.cancel_button.pack(pady=(10, 20))
    
    def update_progress(self, value: float, message: str = None):
        """Update progress bar and message.
        
        Args:
            value: Progress value (0.0 to 1.0)
            message: Optional new message
        """
        self.progress_bar.set(value)
        
        if message:
            self.message_label.configure(text=message)
        
        self.update()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        self._finish_dialog("cancelled")
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled.
        
        Returns:
            bool: True if cancelled
        """
        return self.cancelled


class MessageDialog(BaseDialog):
    """Simple message dialog for displaying information."""
    
    def __init__(self, 
                 parent,
                 title: str = None,
                 message: str = "",
                 message_type: str = "info",
                 **kwargs):
        """
        Initialize the message dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Message text
            message_type: Type of message (info, warning, error, success)
            **kwargs: Additional arguments
        """
        if title is None:
            title_map = {
                "info": _("status.info"),
                "warning": _("status.warning"),
                "error": _("status.error"),
                "success": _("status.success")
            }
            title = title_map.get(message_type, _("status.info"))
        
        super().__init__(parent, title=title, width=400, height=200, **kwargs)
        
        self.message = message
        self.message_type = message_type
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Content frame
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Icon
        icon_symbols = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon_symbols.get(self.message_type, "ℹ️"),
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(20, 10))
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=(0, 20), padx=20)
        
        # OK button
        ok_button = ctk.CTkButton(
            content_frame,
            text=_("buttons.ok"),
            command=self._on_ok,
            width=100
        )
        ok_button.pack(pady=(0, 20))
        
        # Set focus on OK button
        ok_button.focus()
    
    def _on_ok(self):
        """Handle OK button click."""
        self._finish_dialog(True)


# Convenience functions for showing dialogs
def show_confirmation(parent, message: str, title: str = None, **kwargs) -> bool:
    """Show a confirmation dialog.
    
    Args:
        parent: Parent window
        message: Confirmation message
        title: Dialog title
        **kwargs: Additional arguments
        
    Returns:
        bool: True if user confirmed, False otherwise
    """
    dialog = ConfirmationDialog(parent, title=title, message=message, **kwargs)
    parent.wait_window(dialog)
    return dialog.result or False

def show_input(parent, prompt: str, title: str = None, **kwargs) -> Optional[str]:
    """Show an input dialog.
    
    Args:
        parent: Parent window
        prompt: Input prompt
        title: Dialog title
        **kwargs: Additional arguments
        
    Returns:
        Optional[str]: User input or None if cancelled
    """
    dialog = InputDialog(parent, title=title, prompt=prompt, **kwargs)
    parent.wait_window(dialog)
    return dialog.result

def show_message(parent, message: str, title: str = None, message_type: str = "info", **kwargs):
    """Show a message dialog.
    
    Args:
        parent: Parent window
        message: Message text
        title: Dialog title
        message_type: Type of message
        **kwargs: Additional arguments
    """
    dialog = MessageDialog(parent, title=title, message=message, message_type=message_type, **kwargs)
    parent.wait_window(dialog)
    return dialog.result

def show_progress(parent, message: str, title: str = None, cancellable: bool = False, **kwargs) -> ProgressDialog:
    """Show a progress dialog.
    
    Args:
        parent: Parent window
        message: Progress message
        title: Dialog title
        cancellable: Whether operation can be cancelled
        **kwargs: Additional arguments
        
    Returns:
        ProgressDialog: Progress dialog instance
    """
    return ProgressDialog(parent, title=title, message=message, cancellable=cancellable, **kwargs)