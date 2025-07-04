#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - UI Components Package

Reusable UI components for the Easy Genie Desktop application.
"""

# Import all components
from .base_components import *
from .reusable_dialogs import *
from .widget_factory import *

__all__ = [
    # Base components
    'BaseFrame',
    'BaseDialog',
    'BaseToolWindow',
    
    # Dialogs
    'BaseDialog',
    'show_confirmation',
    'show_input',
    'show_message',
    
    # Widgets
    'WidgetFactory',
    'get_widget_factory',
    'create_button',
    'create_label',
    'create_entry',
    'create_frame'
]