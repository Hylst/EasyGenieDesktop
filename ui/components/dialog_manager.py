"""Dialog Manager for Advanced UI Components.

This module provides a centralized system for managing complex dialogs,
modal windows, and user interactions in Phase 2.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from datetime import datetime


class DialogType(Enum):
    """Types of dialogs supported by the manager."""
    CONFIRMATION = "confirmation"
    INPUT = "input"
    SELECTION = "selection"
    SETTINGS = "settings"
    PROGRESS = "progress"
    CUSTOM = "custom"
    WIZARD = "wizard"
    NOTIFICATION = "notification"
    FILE_BROWSER = "file_browser"
    COLOR_PICKER = "color_picker"


class DialogResult(Enum):
    """Dialog result types."""
    OK = "ok"
    CANCEL = "cancel"
    YES = "yes"
    NO = "no"
    RETRY = "retry"
    IGNORE = "ignore"
    ABORT = "abort"
    CUSTOM = "custom"


class DialogPriority(Enum):
    """Dialog priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DialogConfig:
    """Configuration for dialog creation."""
    title: str
    message: str = ""
    dialog_type: DialogType = DialogType.CONFIRMATION
    priority: DialogPriority = DialogPriority.NORMAL
    
    # Appearance
    width: int = 400
    height: int = 300
    resizable: bool = False
    modal: bool = True
    
    # Buttons
    buttons: List[str] = None
    default_button: str = "OK"
    cancel_button: str = "Cancel"
    
    # Content
    icon: Optional[str] = None
    content_widget: Optional[tk.Widget] = None
    
    # Behavior
    auto_close: bool = False
    auto_close_delay: int = 5000  # milliseconds
    callback: Optional[Callable] = None
    
    # Validation
    validator: Optional[Callable] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.buttons is None:
            if self.dialog_type == DialogType.CONFIRMATION:
                self.buttons = ["OK", "Cancel"]
            elif self.dialog_type == DialogType.INPUT:
                self.buttons = ["OK", "Cancel"]
            elif self.dialog_type == DialogType.NOTIFICATION:
                self.buttons = ["OK"]
            else:
                self.buttons = ["OK", "Cancel"]


@dataclass
class DialogState:
    """State information for active dialogs."""
    dialog_id: str
    config: DialogConfig
    window: Optional[tk.Toplevel] = None
    result: Optional[DialogResult] = None
    data: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.data is None:
            self.data = {}
        if self.created_at is None:
            self.created_at = datetime.now()


class BaseDialog(ctk.CTkToplevel):
    """Base class for all managed dialogs."""
    
    def __init__(self, parent, config: DialogConfig, dialog_id: str):
        """Initialize base dialog.
        
        Args:
            parent: Parent window
            config: Dialog configuration
            dialog_id: Unique dialog identifier
        """
        super().__init__(parent)
        
        self.config = config
        self.dialog_id = dialog_id
        self.result = None
        self.data = {}
        
        # Configure window
        self.title(config.title)
        self.geometry(f"{config.width}x{config.height}")
        self.resizable(config.resizable, config.resizable)
        
        if config.modal:
            self.transient(parent)
            self.grab_set()
        
        # Center on parent
        self.center_on_parent(parent)
        
        # Setup UI
        self.setup_ui()
        
        # Auto-close if configured
        if config.auto_close:
            self.after(config.auto_close_delay, self.auto_close)
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def center_on_parent(self, parent):
        """Center dialog on parent window.
        
        Args:
            parent: Parent window
        """
        self.update_idletasks()
        
        # Get parent geometry
        parent.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - self.config.width) // 2
        y = parent_y + (parent_height - self.config.height) // 2
        
        self.geometry(f"{self.config.width}x{self.config.height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup dialog UI. Override in subclasses."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        # Message label
        if self.config.message:
            self.message_label = ctk.CTkLabel(
                self.content_frame,
                text=self.config.message,
                wraplength=self.config.width - 60,
                justify="left"
            )
            self.message_label.pack(pady=10)
        
        # Custom content widget
        if self.config.content_widget:
            self.config.content_widget.pack(in_=self.content_frame, fill="both", expand=True)
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Create buttons
        self.create_buttons()
    
    def create_buttons(self):
        """Create dialog buttons."""
        for i, button_text in enumerate(self.config.buttons):
            button = ctk.CTkButton(
                self.button_frame,
                text=button_text,
                command=lambda text=button_text: self.on_button_click(text)
            )
            button.pack(side="right", padx=(5, 0))
            
            # Set default button appearance
            if button_text == self.config.default_button:
                button.configure(fg_color=("#1f538d", "#14375e"))
    
    def on_button_click(self, button_text: str):
        """Handle button click.
        
        Args:
            button_text: Text of clicked button
        """
        # Validate if needed
        if button_text == self.config.default_button and self.config.validator:
            if not self.config.validator(self.get_data()):
                return
        
        # Set result
        if button_text.lower() == "ok":
            self.result = DialogResult.OK
        elif button_text.lower() == "cancel":
            self.result = DialogResult.CANCEL
        elif button_text.lower() == "yes":
            self.result = DialogResult.YES
        elif button_text.lower() == "no":
            self.result = DialogResult.NO
        else:
            self.result = DialogResult.CUSTOM
        
        # Get data before closing
        self.data = self.get_data()
        
        # Call callback if provided
        if self.config.callback:
            self.config.callback(self.result, self.data)
        
        # Close dialog
        self.destroy()
    
    def get_data(self) -> Dict[str, Any]:
        """Get data from dialog. Override in subclasses.
        
        Returns:
            Dict[str, Any]: Dialog data
        """
        return {}
    
    def auto_close(self):
        """Auto-close dialog."""
        self.result = DialogResult.CANCEL
        self.destroy()
    
    def on_close(self):
        """Handle window close event."""
        self.result = DialogResult.CANCEL
        self.destroy()


class InputDialog(BaseDialog):
    """Dialog for text input."""
    
    def __init__(self, parent, config: DialogConfig, dialog_id: str, 
                 prompt: str = "Enter value:", default_value: str = "",
                 input_type: str = "text", validation_regex: str = None):
        """Initialize input dialog.
        
        Args:
            parent: Parent window
            config: Dialog configuration
            dialog_id: Dialog identifier
            prompt: Input prompt
            default_value: Default input value
            input_type: Type of input (text, password, number)
            validation_regex: Regex for validation
        """
        self.prompt = prompt
        self.default_value = default_value
        self.input_type = input_type
        self.validation_regex = validation_regex
        
        super().__init__(parent, config, dialog_id)
    
    def setup_ui(self):
        """Setup input dialog UI."""
        super().setup_ui()
        
        # Remove default message label
        if hasattr(self, 'message_label'):
            self.message_label.destroy()
        
        # Prompt label
        self.prompt_label = ctk.CTkLabel(self.content_frame, text=self.prompt)
        self.prompt_label.pack(pady=(10, 5))
        
        # Input entry
        if self.input_type == "password":
            self.input_entry = ctk.CTkEntry(self.content_frame, show="*")
        else:
            self.input_entry = ctk.CTkEntry(self.content_frame)
        
        self.input_entry.pack(fill="x", padx=20, pady=5)
        self.input_entry.insert(0, self.default_value)
        self.input_entry.focus()
        
        # Bind Enter key
        self.input_entry.bind("<Return>", lambda e: self.on_button_click(self.config.default_button))
    
    def get_data(self) -> Dict[str, Any]:
        """Get input data.
        
        Returns:
            Dict[str, Any]: Input data
        """
        return {"value": self.input_entry.get()}


class SelectionDialog(BaseDialog):
    """Dialog for selecting from options."""
    
    def __init__(self, parent, config: DialogConfig, dialog_id: str,
                 options: List[str], default_selection: str = None,
                 multiple_selection: bool = False):
        """Initialize selection dialog.
        
        Args:
            parent: Parent window
            config: Dialog configuration
            dialog_id: Dialog identifier
            options: List of options to select from
            default_selection: Default selected option
            multiple_selection: Allow multiple selections
        """
        self.options = options
        self.default_selection = default_selection
        self.multiple_selection = multiple_selection
        
        super().__init__(parent, config, dialog_id)
    
    def setup_ui(self):
        """Setup selection dialog UI."""
        super().setup_ui()
        
        # Remove default message label if no message
        if not self.config.message and hasattr(self, 'message_label'):
            self.message_label.destroy()
        
        # Selection frame
        self.selection_frame = ctk.CTkScrollableFrame(self.content_frame)
        self.selection_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create selection widgets
        if self.multiple_selection:
            self.selection_vars = {}
            for option in self.options:
                var = tk.BooleanVar()
                if option == self.default_selection:
                    var.set(True)
                
                checkbox = ctk.CTkCheckBox(self.selection_frame, text=option, variable=var)
                checkbox.pack(anchor="w", pady=2)
                self.selection_vars[option] = var
        else:
            self.selection_var = tk.StringVar(value=self.default_selection or self.options[0])
            for option in self.options:
                radio = ctk.CTkRadioButton(
                    self.selection_frame,
                    text=option,
                    variable=self.selection_var,
                    value=option
                )
                radio.pack(anchor="w", pady=2)
    
    def get_data(self) -> Dict[str, Any]:
        """Get selection data.
        
        Returns:
            Dict[str, Any]: Selection data
        """
        if self.multiple_selection:
            selected = [option for option, var in self.selection_vars.items() if var.get()]
            return {"selected": selected}
        else:
            return {"selected": self.selection_var.get()}


class ProgressDialog(BaseDialog):
    """Dialog for showing progress."""
    
    def __init__(self, parent, config: DialogConfig, dialog_id: str,
                 max_value: int = 100, show_percentage: bool = True,
                 show_eta: bool = False, cancellable: bool = False):
        """Initialize progress dialog.
        
        Args:
            parent: Parent window
            config: Dialog configuration
            dialog_id: Dialog identifier
            max_value: Maximum progress value
            show_percentage: Show percentage text
            show_eta: Show estimated time remaining
            cancellable: Allow cancellation
        """
        self.max_value = max_value
        self.show_percentage = show_percentage
        self.show_eta = show_eta
        self.cancellable = cancellable
        self.current_value = 0
        self.start_time = datetime.now()
        self.cancelled = False
        
        # Modify config for progress dialog
        if not cancellable:
            config.buttons = []
        else:
            config.buttons = ["Cancel"]
        
        super().__init__(parent, config, dialog_id)
    
    def setup_ui(self):
        """Setup progress dialog UI."""
        super().setup_ui()
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.content_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        # Progress label
        if self.show_percentage:
            self.progress_label = ctk.CTkLabel(self.content_frame, text="0%")
            self.progress_label.pack(pady=5)
        
        # ETA label
        if self.show_eta:
            self.eta_label = ctk.CTkLabel(self.content_frame, text="Calculating...")
            self.eta_label.pack(pady=5)
    
    def update_progress(self, value: int, message: str = None):
        """Update progress.
        
        Args:
            value: Current progress value
            message: Optional status message
        """
        self.current_value = value
        progress_ratio = value / self.max_value
        
        # Update progress bar
        self.progress_bar.set(progress_ratio)
        
        # Update percentage
        if self.show_percentage:
            percentage = int(progress_ratio * 100)
            self.progress_label.configure(text=f"{percentage}%")
        
        # Update ETA
        if self.show_eta and value > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            estimated_total = elapsed * self.max_value / value
            remaining = estimated_total - elapsed
            
            if remaining > 0:
                eta_text = f"ETA: {int(remaining)}s"
            else:
                eta_text = "Almost done..."
            
            self.eta_label.configure(text=eta_text)
        
        # Update message
        if message and hasattr(self, 'message_label'):
            self.message_label.configure(text=message)
        
        # Update display
        self.update()
    
    def on_button_click(self, button_text: str):
        """Handle button click.
        
        Args:
            button_text: Text of clicked button
        """
        if button_text.lower() == "cancel":
            self.cancelled = True
            self.result = DialogResult.CANCEL
        
        super().on_button_click(button_text)


class WizardDialog(BaseDialog):
    """Multi-step wizard dialog."""
    
    def __init__(self, parent, config: DialogConfig, dialog_id: str, steps: List[Dict[str, Any]]):
        """Initialize wizard dialog.
        
        Args:
            parent: Parent window
            config: Dialog configuration
            dialog_id: Dialog identifier
            steps: List of wizard steps
        """
        self.steps = steps
        self.current_step = 0
        self.step_data = {}
        
        # Modify config for wizard
        config.buttons = ["< Back", "Next >", "Cancel"]
        config.width = max(config.width, 500)
        config.height = max(config.height, 400)
        
        super().__init__(parent, config, dialog_id)
    
    def setup_ui(self):
        """Setup wizard dialog UI."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Step indicator
        self.step_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Step {self.current_step + 1} of {len(self.steps)}"
        )
        self.step_label.pack(side="left", padx=10, pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.header_frame)
        self.progress_bar.pack(side="right", padx=10, pady=10, fill="x", expand=True)
        self.update_progress()
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Create buttons
        self.back_button = ctk.CTkButton(
            self.button_frame,
            text="< Back",
            command=self.go_back,
            state="disabled"
        )
        self.back_button.pack(side="left", padx=(0, 5))
        
        self.next_button = ctk.CTkButton(
            self.button_frame,
            text="Next >",
            command=self.go_next
        )
        self.next_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=lambda: self.on_button_click("Cancel")
        )
        self.cancel_button.pack(side="right")
        
        # Load first step
        self.load_step()
    
    def update_progress(self):
        """Update wizard progress."""
        progress = (self.current_step + 1) / len(self.steps)
        self.progress_bar.set(progress)
        self.step_label.configure(text=f"Step {self.current_step + 1} of {len(self.steps)}")
    
    def load_step(self):
        """Load current step content."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        step = self.steps[self.current_step]
        
        # Step title
        title_label = ctk.CTkLabel(
            self.content_frame,
            text=step.get("title", f"Step {self.current_step + 1}"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Step description
        if "description" in step:
            desc_label = ctk.CTkLabel(
                self.content_frame,
                text=step["description"],
                wraplength=self.config.width - 60
            )
            desc_label.pack(pady=5)
        
        # Step content
        if "content_widget" in step:
            step["content_widget"](self.content_frame, self.step_data)
        
        # Update button states
        self.back_button.configure(state="normal" if self.current_step > 0 else "disabled")
        
        if self.current_step == len(self.steps) - 1:
            self.next_button.configure(text="Finish")
        else:
            self.next_button.configure(text="Next >")
    
    def go_back(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_progress()
            self.load_step()
    
    def go_next(self):
        """Go to next step or finish."""
        # Validate current step
        step = self.steps[self.current_step]
        if "validator" in step:
            if not step["validator"](self.step_data):
                return
        
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_progress()
            self.load_step()
        else:
            # Finish wizard
            self.result = DialogResult.OK
            self.data = self.step_data
            if self.config.callback:
                self.config.callback(self.result, self.data)
            self.destroy()
    
    def get_data(self) -> Dict[str, Any]:
        """Get wizard data.
        
        Returns:
            Dict[str, Any]: Wizard data
        """
        return self.step_data


class DialogManager:
    """Centralized dialog management system."""
    
    def __init__(self, parent_window):
        """Initialize dialog manager.
        
        Args:
            parent_window: Main application window
        """
        self.parent_window = parent_window
        self.active_dialogs: Dict[str, DialogState] = {}
        self.dialog_queue: List[DialogState] = []
        self.dialog_counter = 0
        
        # Configuration
        self.max_concurrent_dialogs = 3
        self.auto_queue_management = True
    
    def create_dialog(self, config: DialogConfig, **kwargs) -> str:
        """Create and show a dialog.
        
        Args:
            config: Dialog configuration
            **kwargs: Additional arguments for specific dialog types
            
        Returns:
            str: Dialog ID
        """
        # Generate unique dialog ID
        self.dialog_counter += 1
        dialog_id = f"dialog_{self.dialog_counter}_{config.dialog_type.value}"
        
        # Create dialog state
        dialog_state = DialogState(
            dialog_id=dialog_id,
            config=config
        )
        
        # Check if we can show dialog immediately
        if len(self.active_dialogs) < self.max_concurrent_dialogs:
            self._show_dialog(dialog_state, **kwargs)
        else:
            # Add to queue
            self.dialog_queue.append(dialog_state)
            if config.priority == DialogPriority.CRITICAL:
                # Move critical dialogs to front
                self.dialog_queue.sort(key=lambda d: d.config.priority.value, reverse=True)
        
        return dialog_id
    
    def _show_dialog(self, dialog_state: DialogState, **kwargs):
        """Show a dialog.
        
        Args:
            dialog_state: Dialog state
            **kwargs: Additional arguments
        """
        config = dialog_state.config
        
        try:
            # Create appropriate dialog type
            if config.dialog_type == DialogType.INPUT:
                dialog = InputDialog(
                    self.parent_window,
                    config,
                    dialog_state.dialog_id,
                    **kwargs
                )
            elif config.dialog_type == DialogType.SELECTION:
                dialog = SelectionDialog(
                    self.parent_window,
                    config,
                    dialog_state.dialog_id,
                    **kwargs
                )
            elif config.dialog_type == DialogType.PROGRESS:
                dialog = ProgressDialog(
                    self.parent_window,
                    config,
                    dialog_state.dialog_id,
                    **kwargs
                )
            elif config.dialog_type == DialogType.WIZARD:
                dialog = WizardDialog(
                    self.parent_window,
                    config,
                    dialog_state.dialog_id,
                    **kwargs
                )
            else:
                # Default to base dialog
                dialog = BaseDialog(
                    self.parent_window,
                    config,
                    dialog_state.dialog_id
                )
            
            # Store dialog reference
            dialog_state.window = dialog
            self.active_dialogs[dialog_state.dialog_id] = dialog_state
            
            # Bind destroy event to cleanup
            dialog.bind("<Destroy>", lambda e: self._on_dialog_destroyed(dialog_state.dialog_id))
            
        except Exception as e:
            print(f"Error creating dialog: {e}")
    
    def _on_dialog_destroyed(self, dialog_id: str):
        """Handle dialog destruction.
        
        Args:
            dialog_id: Dialog identifier
        """
        if dialog_id in self.active_dialogs:
            dialog_state = self.active_dialogs[dialog_id]
            
            # Store result
            if dialog_state.window:
                dialog_state.result = getattr(dialog_state.window, 'result', DialogResult.CANCEL)
                dialog_state.data = getattr(dialog_state.window, 'data', {})
            
            # Remove from active dialogs
            del self.active_dialogs[dialog_id]
            
            # Process queue if auto-management is enabled
            if self.auto_queue_management and self.dialog_queue:
                next_dialog = self.dialog_queue.pop(0)
                self._show_dialog(next_dialog)
    
    def close_dialog(self, dialog_id: str, result: DialogResult = DialogResult.CANCEL):
        """Close a specific dialog.
        
        Args:
            dialog_id: Dialog identifier
            result: Dialog result
        """
        if dialog_id in self.active_dialogs:
            dialog_state = self.active_dialogs[dialog_id]
            if dialog_state.window:
                dialog_state.window.result = result
                dialog_state.window.destroy()
    
    def close_all_dialogs(self):
        """Close all active dialogs."""
        for dialog_id in list(self.active_dialogs.keys()):
            self.close_dialog(dialog_id)
    
    def get_dialog_result(self, dialog_id: str) -> Tuple[Optional[DialogResult], Dict[str, Any]]:
        """Get result from a dialog.
        
        Args:
            dialog_id: Dialog identifier
            
        Returns:
            Tuple[Optional[DialogResult], Dict[str, Any]]: Result and data
        """
        if dialog_id in self.active_dialogs:
            dialog_state = self.active_dialogs[dialog_id]
            return dialog_state.result, dialog_state.data
        
        return None, {}
    
    def update_progress_dialog(self, dialog_id: str, value: int, message: str = None):
        """Update progress dialog.
        
        Args:
            dialog_id: Dialog identifier
            value: Progress value
            message: Optional message
        """
        if dialog_id in self.active_dialogs:
            dialog_state = self.active_dialogs[dialog_id]
            if isinstance(dialog_state.window, ProgressDialog):
                dialog_state.window.update_progress(value, message)
    
    def is_dialog_active(self, dialog_id: str) -> bool:
        """Check if dialog is active.
        
        Args:
            dialog_id: Dialog identifier
            
        Returns:
            bool: True if dialog is active
        """
        return dialog_id in self.active_dialogs
    
    def get_active_dialog_count(self) -> int:
        """Get number of active dialogs.
        
        Returns:
            int: Number of active dialogs
        """
        return len(self.active_dialogs)
    
    def get_queued_dialog_count(self) -> int:
        """Get number of queued dialogs.
        
        Returns:
            int: Number of queued dialogs
        """
        return len(self.dialog_queue)
    
    # Convenience methods for common dialog types
    
    def show_confirmation(self, title: str, message: str, callback: Callable = None) -> str:
        """Show confirmation dialog.
        
        Args:
            title: Dialog title
            message: Confirmation message
            callback: Optional callback function
            
        Returns:
            str: Dialog ID
        """
        config = DialogConfig(
            title=title,
            message=message,
            dialog_type=DialogType.CONFIRMATION,
            buttons=["Yes", "No"],
            default_button="Yes",
            callback=callback
        )
        return self.create_dialog(config)
    
    def show_input(self, title: str, prompt: str, default_value: str = "", callback: Callable = None) -> str:
        """Show input dialog.
        
        Args:
            title: Dialog title
            prompt: Input prompt
            default_value: Default input value
            callback: Optional callback function
            
        Returns:
            str: Dialog ID
        """
        config = DialogConfig(
            title=title,
            dialog_type=DialogType.INPUT,
            callback=callback
        )
        return self.create_dialog(config, prompt=prompt, default_value=default_value)
    
    def show_selection(self, title: str, message: str, options: List[str], 
                      default_selection: str = None, multiple: bool = False, 
                      callback: Callable = None) -> str:
        """Show selection dialog.
        
        Args:
            title: Dialog title
            message: Selection message
            options: List of options
            default_selection: Default selected option
            multiple: Allow multiple selections
            callback: Optional callback function
            
        Returns:
            str: Dialog ID
        """
        config = DialogConfig(
            title=title,
            message=message,
            dialog_type=DialogType.SELECTION,
            callback=callback
        )
        return self.create_dialog(
            config,
            options=options,
            default_selection=default_selection,
            multiple_selection=multiple
        )
    
    def show_progress(self, title: str, message: str, max_value: int = 100, 
                     cancellable: bool = False, callback: Callable = None) -> str:
        """Show progress dialog.
        
        Args:
            title: Dialog title
            message: Progress message
            max_value: Maximum progress value
            cancellable: Allow cancellation
            callback: Optional callback function
            
        Returns:
            str: Dialog ID
        """
        config = DialogConfig(
            title=title,
            message=message,
            dialog_type=DialogType.PROGRESS,
            callback=callback
        )
        return self.create_dialog(
            config,
            max_value=max_value,
            cancellable=cancellable
        )
    
    def show_notification(self, title: str, message: str, auto_close: bool = True, 
                         delay: int = 3000, callback: Callable = None) -> str:
        """Show notification dialog.
        
        Args:
            title: Dialog title
            message: Notification message
            auto_close: Auto-close dialog
            delay: Auto-close delay in milliseconds
            callback: Optional callback function
            
        Returns:
            str: Dialog ID
        """
        config = DialogConfig(
            title=title,
            message=message,
            dialog_type=DialogType.NOTIFICATION,
            buttons=["OK"],
            auto_close=auto_close,
            auto_close_delay=delay,
            callback=callback
        )
        return self.create_dialog(config)