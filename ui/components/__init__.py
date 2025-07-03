#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - UI Components Package

Reusable UI components for the Easy Genie Desktop application.
"""

# Import all components
from .base_components import *
from .dialogs import *
from .widgets import *

__all__ = [
    # Base components
    'BaseFrame',
    'BaseDialog',
    'BaseToolWindow',
    
    # Dialogs
    'SettingsDialog',
    'ExportDialog',
    'ProfileDialog',
    
    # Widgets
    'EnergyIndicator',
    'StatusBar',
    'ToolCard',
    'TaskCard',
    'ProgressIndicator'
]