#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - UI Package

User interface components for the Easy Genie Desktop application.
"""

# UI Components
from .main_window import MainWindow
from .components import *
from .tools import *

__all__ = [
    'MainWindow',
    # Components will be added as they're created
]