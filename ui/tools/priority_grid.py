#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Priority Grid Tool

Tool for task prioritization using Eisenhower Matrix.
Supports both Magic (simple) and Genie (AI-powered) modes.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
import uuid
import math

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class PriorityGridTool(BaseToolWindow):
    """Priority Grid tool for task prioritization using Eisenhower Matrix."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Priority Grid tool."""
        super().__init__(
            parent, 
            "Priority Grid", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Grid data
        self.tasks = {
            'urgent_important': [],      # Do First (Q1)
            'not_urgent_important': [],  # Schedule (Q2)
            'urgent_not_important': [],  # Delegate (Q3)
            'not_urgent_not_important': []  # Eliminate (Q4)
        }
        
        # UI state
        self.selected_task = None
        self.grid_widgets = {}
        self.drag_data = {'task': None, 'source_quadrant': None}
        
        # Grid colors
        self.quadrant_colors = {
            'urgent_important': '#E74C3C',      # Red - Crisis
            'not_urgent_important': '#2ECC71',  # Green - Goals
            'urgent_not_important': '#F39C12',  # Orange - Interruptions
            'not_urgent_not_important': '#95A5A6'  # Gray - Waste
        }
        
        self.logger.info("Priority Grid tool initialized")
    
    def _setup_tool_content(self):
        """Setup Priority Grid specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Top panel - Controls and task input
        self._create_controls_panel()
        
        # Main grid
        self._create_priority_grid()
        
        # Bottom panel - Actions and insights
        self._create_actions_panel()
    
    def _create_controls_panel(self):
        """Create controls panel."""
        controls_panel = ctk.CTkFrame(self.content_frame, height=120)
        controls_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        controls_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - Task input
        input_frame = ctk.CTkFrame(controls_panel)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            input_frame,
            text="➕ Nouvelle Tâche",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Task title
        self.task_title_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Titre de la tâche...",
            height=35
        )
        self.task_title_entry.pack(fill="x", padx=10, pady=(0, 5))
        self.task_title_entry.bind("<Return>", self._add_task_from_entry)
        
        # Quick add buttons
        quick_buttons_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        quick_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        add_btn = ctk.CTkButton(
            quick_buttons_frame,
            text="Ajouter",
            height=30,
            width=80,
            command=self._add_task_from_entry
        )
        add_btn.pack(side="left", padx=(0, 5))
        
        import_btn = ctk.CTkButton(
            quick_buttons_frame,
            text="📥 Importer",
            height=30,
            width=100,
            command=self._import_tasks
        )
        import_btn.pack(side="left", padx=5)
        
        # Right side - Grid legend and stats
        legend_frame = ctk.CTkFrame(controls_panel)
        legend_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=10)
        
        ctk.CTkLabel(
            legend_frame,
            text="📊 Matrice d'Eisenhower",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Legend grid
        legend_grid = ctk.CTkFrame(legend_frame, fg_color="transparent")
        legend_grid.pack(fill="x", padx=10, pady=(0, 10))
        legend_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Quadrant legends
        legends = [
            ("🔥 Faire d'abord", "urgent_important", 0, 0),
            ("📅 Planifier", "not_urgent_important", 0, 1),
            ("👥 Déléguer", "urgent_not_important", 1, 0),
            ("🗑️ Éliminer", "not_urgent_not_important", 1, 1)
        ]
        
        self.count_labels = {}
        for text, quadrant, row, col in legends:
            legend_item = ctk.CTkFrame(legend_grid, height=25)
            legend_item.grid(row=row, column=col, sticky="ew", padx=2, pady=1)
            
            # Color indicator
            color_frame = ctk.CTkFrame(
                legend_item,
                width=15,
                height=15,
                fg_color=self.quadrant_colors[quadrant],
                corner_radius=3
            )
            color_frame.pack(side="left", padx=(5, 5), pady=5)
            
            # Text and count
            text_label = ctk.CTkLabel(
                legend_item,
                text=text,
                font=ctk.CTkFont(size=10)
            )
            text_label.pack(side="left", pady=5)
            
            count_label = ctk.CTkLabel(
                legend_item,
                text="(0)",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            count_label.pack(side="right", padx=(0, 5), pady=5)
            
            self.count_labels[quadrant] = count_label
        
        # AI analysis button (Genie mode only)
        if self.is_ai_enabled:
            ai_frame = ctk.CTkFrame(controls_panel)
            ai_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
            
            ctk.CTkLabel(
                ai_frame,
                text="🤖 IA Assistant",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 5))
            
            ai_analyze_btn = ctk.CTkButton(
                ai_frame,
                text="📈 Analyser Priorités",
                height=35,
                fg_color="#4ECDC4",
                hover_color="#45B7B8",
                command=self._ai_analyze_priorities
            )
            ai_analyze_btn.pack(fill="x", padx=10, pady=(0, 5))
            
            ai_suggest_btn = ctk.CTkButton(
                ai_frame,
                text="💡 Suggestions",
                height=35,
                fg_color="#9B59B6",
                hover_color="#8E44AD",
                command=self._ai_suggest_improvements
            )
            ai_suggest_btn.pack(fill="x", padx=10, pady=(0, 10))
    
    def _create_priority_grid(self):
        """Create the main priority grid."""
        grid_frame = ctk.CTkFrame(self.content_frame)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        grid_frame.grid_rowconfigure((0, 1), weight=1)
        
        # Axis labels
        # Top label (Urgent/Not Urgent)
        urgent_label = ctk.CTkLabel(
            grid_frame,
            text="URGENT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E74C3C"
        )
        urgent_label.grid(row=0, column=0, sticky="n", pady=(5, 0))
        
        not_urgent_label = ctk.CTkLabel(
            grid_frame,
            text="PAS URGENT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#27AE60"
        )
        not_urgent_label.grid(row=0, column=1, sticky="n", pady=(5, 0))
        
        # Left labels (Important/Not Important)
        important_label = ctk.CTkLabel(
            grid_frame,
            text="IMPORTANT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ECC71",
            angle=90
        )
        important_label.grid(row=0, column=0, sticky="w", padx=(5, 0))
        
        not_important_label = ctk.CTkLabel(
            grid_frame,
            text="PAS IMPORTANT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#95A5A6",
            angle=90
        )
        not_important_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
        
        # Create quadrants
        quadrants = [
            ('urgent_important', 0, 0, "🔥 FAIRE D'ABORD", "Crises, urgences, problèmes"),
            ('not_urgent_important', 0, 1, "📅 PLANIFIER", "Prévention, développement, planification"),
            ('urgent_not_important', 1, 0, "👥 DÉLÉGUER", "Interruptions, certains appels/emails"),
            ('not_urgent_not_important', 1, 1, "🗑️ ÉLIMINER", "Distractions, activités inutiles")
        ]
        
        for quadrant_id, row, col, title, subtitle in quadrants:
            self._create_quadrant(grid_frame, quadrant_id, row, col, title, subtitle)
    
    def _create_quadrant(self, parent, quadrant_id: str, row: int, col: int, title: str, subtitle: str):
        """Create a single quadrant."""
        # Main quadrant frame
        quadrant_frame = ctk.CTkFrame(
            parent,
            fg_color=self.quadrant_colors[quadrant_id],
            corner_radius=10
        )
        quadrant_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        quadrant_frame.grid_columnconfigure(0, weight=1)
        quadrant_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(quadrant_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color="white",
            wraplength=200
        )
        subtitle_label.pack(pady=(2, 0))
        
        # Tasks container
        tasks_container = ctk.CTkScrollableFrame(
            quadrant_frame,
            fg_color="rgba(255, 255, 255, 0.1)",
            scrollbar_button_color="rgba(255, 255, 255, 0.3)",
            scrollbar_button_hover_color="rgba(255, 255, 255, 0.5)"
        )
        tasks_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Store reference
        self.grid_widgets[quadrant_id] = tasks_container
        
        # Enable drop functionality
        tasks_container.bind("<Button-1>", lambda e: self._on_quadrant_click(quadrant_id))
        
        # Add empty state
        self._show_empty_quadrant(quadrant_id)
    
    def _create_actions_panel(self):
        """Create actions panel."""
        actions_panel = ctk.CTkFrame(self.content_frame, height=80)
        actions_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        actions_panel.grid_columnconfigure(1, weight=1)
        
        # Left actions
        left_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        clear_btn = ctk.CTkButton(
            left_actions,
            text="🗑️ Effacer Tout",
            height=35,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_all_tasks
        )
        clear_btn.pack(side="left", padx=(0, 5))
        
        auto_sort_btn = ctk.CTkButton(
            left_actions,
            text="🎯 Tri Automatique",
            height=35,
            command=self._auto_sort_tasks
        )
        auto_sort_btn.pack(side="left", padx=5)
        
        # Center - Quick stats
        stats_frame = ctk.CTkFrame(actions_panel, fg_color="transparent")
        stats_frame.grid(row=0, column=1, sticky="", padx=15, pady=15)
        
        self.total_tasks_label = ctk.CTkLabel(
            stats_frame,
            text="📋 Total: 0 tâches",
            font=ctk.CTkFont(size=12)
        )
        self.total_tasks_label.pack()
        
        self.priority_score_label = ctk.CTkLabel(
            stats_frame,
            text="⭐ Score de priorité: 0%",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.priority_score_label.pack()
        
        # Right actions
        right_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        right_actions.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        export_btn = ctk.CTkButton(
            right_actions,
            text="📤 Exporter",
            height=35,
            command=self._export_grid
        )
        export_btn.pack(side="left", padx=5)
        
        create_tasks_btn = ctk.CTkButton(
            right_actions,
            text="✅ Créer Tâches",
            height=35,
            fg_color="#27AE60",
            hover_color="#229954",
            command=self._create_tasks_from_grid
        )
        create_tasks_btn.pack(side="left", padx=(5, 0))
    
    def _add_task_from_entry(self, event=None):
        """Add task from entry field."""
        title = self.task_title_entry.get().strip()
        if not title:
            return
        
        # Create task dialog for detailed input
        dialog = TaskDialog(self, "Nouvelle Tâche")
        dialog.title_entry.insert(0, title)
        result = dialog.show()
        
        if result and dialog.task_data:
            task_data = dialog.task_data
            
            # Determine quadrant based on urgency and importance
            quadrant = self._determine_quadrant(
                task_data['urgent'],
                task_data['important']
            )
            
            # Create task
            task = {
                'id': str(uuid.uuid4()),
                'title': task_data['title'],
                'description': task_data['description'],
                'urgent': task_data['urgent'],
                'important': task_data['important'],
                'deadline': task_data['deadline'],
                'estimated_duration': task_data['duration'],
                'category': task_data['category'],
                'created_at': datetime.now().isoformat()
            }
            
            # Add to quadrant
            self.tasks[quadrant].append(task)
            
            # Clear entry
            self.task_title_entry.delete(0, 'end')
            
            # Refresh display
            self._refresh_quadrant_display(quadrant)
            self._update_stats()
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('task_added')
    
    def _determine_quadrant(self, urgent: bool, important: bool) -> str:
        """Determine quadrant based on urgency and importance."""
        if urgent and important:
            return 'urgent_important'
        elif not urgent and important:
            return 'not_urgent_important'
        elif urgent and not important:
            return 'urgent_not_important'
        else:
            return 'not_urgent_not_important'
    
    def _import_tasks(self):
        """Import tasks from database or file."""
        if self.database_manager:
            try:
                tasks = self.database_manager.get_user_tasks()
                if not tasks:
                    messagebox.showinfo("Aucune Tâche", "Aucune tâche trouvée dans la base de données.")
                    return
                
                # Import dialog
                dialog = TaskImportDialog(self, tasks)
                result = dialog.show()
                
                if result and dialog.selected_tasks:
                    imported_count = 0
                    for task in dialog.selected_tasks:
                        # Convert to grid task format
                        grid_task = {
                            'id': str(task.get('id', uuid.uuid4())),
                            'title': task['title'],
                            'description': task.get('description', ''),
                            'urgent': self._assess_urgency(task),
                            'important': self._assess_importance(task),
                            'deadline': task.get('deadline'),
                            'estimated_duration': task.get('estimated_duration', 60),
                            'category': task.get('category', ''),
                            'created_at': task.get('created_at', datetime.now().isoformat())
                        }
                        
                        quadrant = self._determine_quadrant(
                            grid_task['urgent'],
                            grid_task['important']
                        )
                        
                        self.tasks[quadrant].append(grid_task)
                        imported_count += 1
                    
                    # Refresh all quadrants
                    for quadrant in self.tasks.keys():
                        self._refresh_quadrant_display(quadrant)
                    
                    self._update_stats()
                    
                    messagebox.showinfo("Import Réussi", f"{imported_count} tâches importées avec succès !")
                    
            except Exception as e:
                self.logger.error(f"Failed to import tasks: {e}")
                messagebox.showerror("Erreur d'Import", f"Impossible d'importer les tâches: {e}")
        else:
            # File import
            messagebox.showinfo("Info", "Import de fichier en développement")
    
    def _assess_urgency(self, task: Dict) -> bool:
        """Assess if a task is urgent based on deadline and priority."""
        # Check deadline
        deadline = task.get('deadline')
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline_date = datetime.fromisoformat(deadline)
                else:
                    deadline_date = deadline
                
                days_until_deadline = (deadline_date - datetime.now()).days
                if days_until_deadline <= 2:  # Due within 2 days
                    return True
            except:
                pass
        
        # Check priority
        priority = task.get('priority', 2)
        if priority >= 4:  # High priority
            return True
        
        return False
    
    def _assess_importance(self, task: Dict) -> bool:
        """Assess if a task is important based on category and priority."""
        # Check priority
        priority = task.get('priority', 2)
        if priority >= 3:  # Medium-high priority
            return True
        
        # Check category
        category = task.get('category', '').lower()
        important_categories = ['projet', 'travail', 'apprentissage']
        if any(cat in category for cat in important_categories):
            return True
        
        return False
    
    def _refresh_quadrant_display(self, quadrant_id: str):
        """Refresh the display of a specific quadrant."""
        container = self.grid_widgets[quadrant_id]
        
        # Clear existing widgets
        for widget in container.winfo_children():
            widget.destroy()
        
        tasks = self.tasks[quadrant_id]
        
        if not tasks:
            self._show_empty_quadrant(quadrant_id)
        else:
            for task in tasks:
                self._create_task_widget(container, task, quadrant_id)
        
        # Update count
        if quadrant_id in self.count_labels:
            self.count_labels[quadrant_id].configure(text=f"({len(tasks)})")
    
    def _show_empty_quadrant(self, quadrant_id: str):
        """Show empty state for a quadrant."""
        container = self.grid_widgets[quadrant_id]
        
        empty_frame = ctk.CTkFrame(container, fg_color="transparent")
        empty_frame.pack(expand=True, fill="both")
        
        empty_label = ctk.CTkLabel(
            empty_frame,
            text="Glissez des tâches ici\nou cliquez pour ajouter",
            font=ctk.CTkFont(size=11),
            text_color="rgba(255, 255, 255, 0.7)",
            justify="center"
        )
        empty_label.pack(expand=True)
        
        # Make clickable to add task
        empty_label.bind("<Button-1>", lambda e: self._add_task_to_quadrant(quadrant_id))
    
    def _create_task_widget(self, parent, task: Dict, quadrant_id: str):
        """Create widget for a task."""
        task_frame = ctk.CTkFrame(
            parent,
            fg_color="rgba(255, 255, 255, 0.9)",
            corner_radius=8
        )
        task_frame.pack(fill="x", padx=5, pady=3)
        
        # Make draggable
        task_frame.bind("<Button-1>", lambda e: self._start_drag(task, quadrant_id))
        task_frame.bind("<B1-Motion>", self._on_drag)
        task_frame.bind("<ButtonRelease-1>", self._end_drag)
        
        # Task content
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=8, pady=6)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=task['title'],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="black",
            anchor="w",
            justify="left"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        title_label.bind("<Button-1>", lambda e: self._start_drag(task, quadrant_id))
        
        # Details
        details = []
        if task.get('deadline'):
            try:
                deadline = task['deadline']
                if isinstance(deadline, str):
                    deadline_date = datetime.fromisoformat(deadline)
                else:
                    deadline_date = deadline
                details.append(f"📅 {deadline_date.strftime('%d/%m')}")
            except:
                pass
        
        if task.get('estimated_duration'):
            duration_hours = task['estimated_duration'] // 60
            duration_minutes = task['estimated_duration'] % 60
            if duration_hours > 0:
                details.append(f"⏱️ {duration_hours}h{duration_minutes:02d}m")
            else:
                details.append(f"⏱️ {duration_minutes}m")
        
        if task.get('category'):
            details.append(f"📁 {task['category']}")
        
        if details:
            details_label = ctk.CTkLabel(
                content_frame,
                text=" • ".join(details),
                font=ctk.CTkFont(size=9),
                text_color="gray",
                anchor="w"
            )
            details_label.grid(row=1, column=0, sticky="ew")
            details_label.bind("<Button-1>", lambda e: self._start_drag(task, quadrant_id))
        
        # Actions
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, rowspan=2, sticky="ne")
        
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=25,
            height=20,
            font=ctk.CTkFont(size=10),
            command=lambda: self._edit_task(task, quadrant_id)
        )
        edit_btn.pack(side="top", pady=1)
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=25,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda: self._delete_task(task, quadrant_id)
        )
        delete_btn.pack(side="top", pady=1)
    
    def _add_task_to_quadrant(self, quadrant_id: str):
        """Add task directly to a specific quadrant."""
        dialog = TaskDialog(self, "Nouvelle Tâche")
        
        # Pre-fill urgency and importance based on quadrant
        if quadrant_id == 'urgent_important':
            dialog.urgent_var.set(True)
            dialog.important_var.set(True)
        elif quadrant_id == 'not_urgent_important':
            dialog.urgent_var.set(False)
            dialog.important_var.set(True)
        elif quadrant_id == 'urgent_not_important':
            dialog.urgent_var.set(True)
            dialog.important_var.set(False)
        else:
            dialog.urgent_var.set(False)
            dialog.important_var.set(False)
        
        result = dialog.show()
        
        if result and dialog.task_data:
            task_data = dialog.task_data
            
            task = {
                'id': str(uuid.uuid4()),
                'title': task_data['title'],
                'description': task_data['description'],
                'urgent': task_data['urgent'],
                'important': task_data['important'],
                'deadline': task_data['deadline'],
                'estimated_duration': task_data['duration'],
                'category': task_data['category'],
                'created_at': datetime.now().isoformat()
            }
            
            # Add to specified quadrant
            self.tasks[quadrant_id].append(task)
            
            # Refresh display
            self._refresh_quadrant_display(quadrant_id)
            self._update_stats()
    
    def _edit_task(self, task: Dict, quadrant_id: str):
        """Edit a task."""
        dialog = TaskDialog(self, "Modifier Tâche", task)
        result = dialog.show()
        
        if result and dialog.task_data:
            # Update task
            task.update({
                'title': dialog.task_data['title'],
                'description': dialog.task_data['description'],
                'urgent': dialog.task_data['urgent'],
                'important': dialog.task_data['important'],
                'deadline': dialog.task_data['deadline'],
                'estimated_duration': dialog.task_data['duration'],
                'category': dialog.task_data['category']
            })
            
            # Check if quadrant should change
            new_quadrant = self._determine_quadrant(
                task['urgent'],
                task['important']
            )
            
            if new_quadrant != quadrant_id:
                # Move to new quadrant
                self.tasks[quadrant_id].remove(task)
                self.tasks[new_quadrant].append(task)
                
                # Refresh both quadrants
                self._refresh_quadrant_display(quadrant_id)
                self._refresh_quadrant_display(new_quadrant)
            else:
                # Refresh current quadrant
                self._refresh_quadrant_display(quadrant_id)
            
            self._update_stats()
    
    def _delete_task(self, task: Dict, quadrant_id: str):
        """Delete a task."""
        if messagebox.askyesno("Confirmer", f"Supprimer la tâche '{task['title']}' ?"):
            self.tasks[quadrant_id].remove(task)
            self._refresh_quadrant_display(quadrant_id)
            self._update_stats()
    
    def _start_drag(self, task: Dict, quadrant_id: str):
        """Start dragging a task."""
        self.drag_data = {
            'task': task,
            'source_quadrant': quadrant_id
        }
    
    def _on_drag(self, event):
        """Handle drag motion."""
        # Visual feedback could be added here
        pass
    
    def _end_drag(self, event):
        """End drag operation."""
        if not self.drag_data['task']:
            return
        
        # Determine target quadrant based on mouse position
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        target_quadrant = None
        
        # Find which quadrant the mouse is over
        for quadrant_id, container in self.grid_widgets.items():
            if widget == container or self._is_child_of(widget, container):
                target_quadrant = quadrant_id
                break
        
        if target_quadrant and target_quadrant != self.drag_data['source_quadrant']:
            # Move task to new quadrant
            task = self.drag_data['task']
            source_quadrant = self.drag_data['source_quadrant']
            
            # Update task urgency/importance based on new quadrant
            if target_quadrant == 'urgent_important':
                task['urgent'] = True
                task['important'] = True
            elif target_quadrant == 'not_urgent_important':
                task['urgent'] = False
                task['important'] = True
            elif target_quadrant == 'urgent_not_important':
                task['urgent'] = True
                task['important'] = False
            else:
                task['urgent'] = False
                task['important'] = False
            
            # Move task
            self.tasks[source_quadrant].remove(task)
            self.tasks[target_quadrant].append(task)
            
            # Refresh displays
            self._refresh_quadrant_display(source_quadrant)
            self._refresh_quadrant_display(target_quadrant)
            self._update_stats()
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('task_moved')
        
        # Clear drag data
        self.drag_data = {'task': None, 'source_quadrant': None}
    
    def _is_child_of(self, widget, parent):
        """Check if widget is a child of parent."""
        if not widget:
            return False
        
        current = widget
        while current:
            if current == parent:
                return True
            current = current.master
        return False
    
    def _on_quadrant_click(self, quadrant_id: str):
        """Handle quadrant click."""
        # Could be used for quadrant-specific actions
        pass
    
    def _auto_sort_tasks(self):
        """Automatically sort tasks based on AI or rules."""
        if self.is_ai_enabled:
            self._ai_auto_sort()
        else:
            self._rule_based_sort()
    
    def _rule_based_sort(self):
        """Sort tasks using predefined rules."""
        # Collect all tasks
        all_tasks = []
        for quadrant_tasks in self.tasks.values():
            all_tasks.extend(quadrant_tasks)
        
        if not all_tasks:
            messagebox.showinfo("Aucune Tâche", "Aucune tâche à trier.")
            return
        
        # Clear all quadrants
        for quadrant in self.tasks.keys():
            self.tasks[quadrant].clear()
        
        # Re-sort tasks
        for task in all_tasks:
            # Re-assess urgency and importance
            task['urgent'] = self._assess_urgency(task)
            task['important'] = self._assess_importance(task)
            
            quadrant = self._determine_quadrant(task['urgent'], task['important'])
            self.tasks[quadrant].append(task)
        
        # Refresh all displays
        for quadrant in self.tasks.keys():
            self._refresh_quadrant_display(quadrant)
        
        self._update_stats()
        
        messagebox.showinfo("Tri Terminé", "Tâches triées automatiquement !")
    
    def _ai_auto_sort(self):
        """Sort tasks using AI analysis."""
        # Collect all tasks
        all_tasks = []
        for quadrant_tasks in self.tasks.values():
            all_tasks.extend(quadrant_tasks)
        
        if not all_tasks:
            messagebox.showinfo("Aucune Tâche", "Aucune tâche à trier.")
            return
        
        def ai_task():
            tasks_data = []
            for task in all_tasks:
                tasks_data.append({
                    'title': task['title'],
                    'description': task.get('description', ''),
                    'deadline': task.get('deadline', ''),
                    'category': task.get('category', ''),
                    'duration': task.get('estimated_duration', 0)
                })
            
            prompt = f"""
Analyse ces tâches et classe-les dans la matrice d'Eisenhower:

{json.dumps(tasks_data, indent=2)}

Pour chaque tâche, détermine si elle est:
- Urgente (deadline proche, bloque d'autres tâches, etc.)
- Importante (impact élevé, objectifs stratégiques, etc.)

Réponds au format JSON:
{{
  "classifications": [
    {{
      "title": "titre de la tâche",
      "urgent": true/false,
      "important": true/false,
      "reasoning": "explication courte"
    }}
  ]
}}
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='task_classification',
                max_tokens=800
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _handle_ai_result(self, result):
        """Handle AI sorting result."""
        try:
            # Parse AI response
            import json
            data = json.loads(result)
            classifications = data.get('classifications', [])
            
            if not classifications:
                messagebox.showerror("Erreur IA", "Aucune classification reçue de l'IA")
                return
            
            # Apply classifications
            all_tasks = []
            for quadrant_tasks in self.tasks.values():
                all_tasks.extend(quadrant_tasks)
            
            # Clear all quadrants
            for quadrant in self.tasks.keys():
                self.tasks[quadrant].clear()
            
            # Apply AI classifications
            for task in all_tasks:
                # Find matching classification
                classification = None
                for cls in classifications:
                    if cls['title'].lower() in task['title'].lower() or task['title'].lower() in cls['title'].lower():
                        classification = cls
                        break
                
                if classification:
                    task['urgent'] = classification['urgent']
                    task['important'] = classification['important']
                else:
                    # Fallback to rule-based
                    task['urgent'] = self._assess_urgency(task)
                    task['important'] = self._assess_importance(task)
                
                quadrant = self._determine_quadrant(task['urgent'], task['important'])
                self.tasks[quadrant].append(task)
            
            # Refresh all displays
            for quadrant in self.tasks.keys():
                self._refresh_quadrant_display(quadrant)
            
            self._update_stats()
            
            messagebox.showinfo("Tri IA Terminé", "Tâches triées par l'IA avec succès !")
            
        except json.JSONDecodeError:
            messagebox.showerror("Erreur IA", "Impossible de parser la réponse de l'IA")
        except Exception as e:
            self.logger.error(f"AI sorting error: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du tri IA: {e}")
    
    def _ai_analyze_priorities(self):
        """Analyze priorities with AI."""
        if not self.is_ai_enabled:
            return
        
        # Collect all tasks
        all_tasks = []
        for quadrant_id, quadrant_tasks in self.tasks.items():
            for task in quadrant_tasks:
                all_tasks.append({
                    'quadrant': quadrant_id,
                    'title': task['title'],
                    'description': task.get('description', ''),
                    'deadline': task.get('deadline', ''),
                    'category': task.get('category', '')
                })
        
        if not all_tasks:
            messagebox.showinfo("Aucune Tâche", "Aucune tâche à analyser.")
            return
        
        def ai_task():
            prompt = f"""
Analyse cette matrice de priorités et fournis des insights:

Tâches par quadrant:
{json.dumps(all_tasks, indent=2)}

Fournis une analyse avec:
1. Distribution des tâches (équilibre entre quadrants)
2. Risques identifiés (trop de Q1, négligence de Q2, etc.)
3. Recommandations d'amélioration
4. Actions prioritaires suggérées

Réponds en français, de manière structurée et actionnable.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='priority_analysis',
                max_tokens=600
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _ai_suggest_improvements(self):
        """Get AI suggestions for improvement."""
        if not self.is_ai_enabled:
            return
        
        def ai_task():
            total_tasks = sum(len(tasks) for tasks in self.tasks.values())
            distribution = {
                quadrant: len(tasks) for quadrant, tasks in self.tasks.items()
            }
            
            prompt = f"""
Basé sur cette distribution de tâches dans la matrice d'Eisenhower:

Total: {total_tasks} tâches
Q1 (Urgent+Important): {distribution['urgent_important']}
Q2 (Important): {distribution['not_urgent_important']}
Q3 (Urgent): {distribution['urgent_not_important']}
Q4 (Ni urgent ni important): {distribution['not_urgent_not_important']}

Donne 5 suggestions concrètes pour:
1. Optimiser la gestion du temps
2. Réduire le stress (moins de Q1)
3. Augmenter l'efficacité (plus de Q2)
4. Éliminer les distractions (réduire Q4)

Réponds de manière concise et actionnable.
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='improvement_suggestions',
                max_tokens=400
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _update_stats(self):
        """Update statistics display."""
        total_tasks = sum(len(tasks) for tasks in self.tasks.values())
        self.total_tasks_label.configure(text=f"📋 Total: {total_tasks} tâches")
        
        # Calculate priority score
        if total_tasks > 0:
            q1_count = len(self.tasks['urgent_important'])
            q2_count = len(self.tasks['not_urgent_important'])
            q3_count = len(self.tasks['urgent_not_important'])
            q4_count = len(self.tasks['not_urgent_not_important'])
            
            # Ideal distribution: low Q1, high Q2, low Q3, very low Q4
            # Score based on Q2 focus and Q1/Q4 minimization
            q2_ratio = q2_count / total_tasks
            q1_penalty = q1_count / total_tasks * 0.5  # Some Q1 is normal
            q4_penalty = q4_count / total_tasks * 0.8  # Q4 should be minimal
            
            score = max(0, (q2_ratio - q1_penalty - q4_penalty) * 100)
            
            self.priority_score_label.configure(
                text=f"⭐ Score de priorité: {score:.0f}%",
                text_color="#2ECC71" if score >= 70 else "#F39C12" if score >= 40 else "#E74C3C"
            )
        else:
            self.priority_score_label.configure(text="⭐ Score de priorité: 0%", text_color="gray")
    
    def _clear_all_tasks(self):
        """Clear all tasks from the grid."""
        total_tasks = sum(len(tasks) for tasks in self.tasks.values())
        if total_tasks == 0:
            messagebox.showinfo("Aucune Tâche", "La grille est déjà vide.")
            return
        
        if messagebox.askyesno("Confirmer", f"Effacer toutes les {total_tasks} tâches ?"):
            for quadrant in self.tasks.keys():
                self.tasks[quadrant].clear()
                self._refresh_quadrant_display(quadrant)
            
            self._update_stats()
    
    def _export_grid(self):
        """Export the priority grid."""
        total_tasks = sum(len(tasks) for tasks in self.tasks.values())
        if total_tasks == 0:
            messagebox.showinfo("Aucune Tâche", "Aucune tâche à exporter.")
            return
        
        # TODO: Implement export functionality
        messagebox.showinfo("Info", "Export en développement")
    
    def _create_tasks_from_grid(self):
        """Create actual tasks from the grid."""
        if not self.database_manager:
            messagebox.showerror("Erreur", "Base de données non disponible.")
            return
        
        total_tasks = sum(len(tasks) for tasks in self.tasks.values())
        if total_tasks == 0:
            messagebox.showinfo("Aucune Tâche", "Aucune tâche à créer.")
            return
        
        try:
            created_count = 0
            for quadrant_id, tasks in self.tasks.items():
                for task in tasks:
                    # Convert urgency/importance to priority number
                    if task['urgent'] and task['important']:
                        priority = 4  # Highest
                    elif task['important']:
                        priority = 3  # High
                    elif task['urgent']:
                        priority = 2  # Medium
                    else:
                        priority = 1  # Low
                    
                    self.database_manager.create_task(
                        title=task['title'],
                        description=task['description'],
                        priority=priority,
                        category=task.get('category', ''),
                        estimated_duration=task.get('estimated_duration', 60),
                        deadline=task.get('deadline')
                    )
                    created_count += 1
            
            messagebox.showinfo(
                "Succès", 
                f"{created_count} tâches créées avec succès dans la base de données !"
            )
            
            # Clear the grid
            for quadrant in self.tasks.keys():
                self.tasks[quadrant].clear()
                self._refresh_quadrant_display(quadrant)
            
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to create tasks: {e}")
            messagebox.showerror("Erreur", f"Impossible de créer les tâches: {e}")
    
    def _save_data(self):
        """Save current grid data."""
        try:
            data = {
                'tasks': self.tasks,
                'saved_at': datetime.now().isoformat()
            }
            
            # TODO: Implement actual saving
            super()._save_data()
            
        except Exception as e:
            self.logger.error(f"Failed to save priority grid: {e}")
    
    def _export_data(self):
        """Export grid data."""
        self._export_grid()


class TaskDialog(ctk.CTkToplevel):
    """Dialog for creating/editing tasks."""
    
    def __init__(self, parent, title: str, task_data: Dict = None):
        """Initialize task dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.task_data = None
        self.result = False
        
        # Configure dialog
        self.title(title)
        self.geometry("450x500")
        self.resizable(False, False)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog(task_data)
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _center_on_parent(self):
        """Center dialog on parent."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_dialog(self, task_data: Dict = None):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📝 Détails de la Tâche",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Task title
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(title_frame, text="Titre:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Titre de la tâche...",
            height=35
        )
        self.title_entry.pack(fill="x", pady=(5, 0))
        
        # Description
        desc_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        desc_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(desc_frame, text="Description:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        self.desc_text = ctk.CTkTextbox(
            desc_frame,
            height=80,
            placeholder_text="Description détaillée..."
        )
        self.desc_text.pack(fill="x", pady=(5, 0))
        
        # Urgency and Importance
        priority_frame = ctk.CTkFrame(main_frame)
        priority_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            priority_frame,
            text="🎯 Classification",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        checkboxes_frame = ctk.CTkFrame(priority_frame, fg_color="transparent")
        checkboxes_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.urgent_var = ctk.BooleanVar()
        urgent_checkbox = ctk.CTkCheckBox(
            checkboxes_frame,
            text="🔥 Urgent (deadline proche, bloque d'autres tâches)",
            variable=self.urgent_var,
            font=ctk.CTkFont(size=11)
        )
        urgent_checkbox.pack(anchor="w", pady=2)
        
        self.important_var = ctk.BooleanVar()
        important_checkbox = ctk.CTkCheckBox(
            checkboxes_frame,
            text="⭐ Important (impact élevé, objectifs stratégiques)",
            variable=self.important_var,
            font=ctk.CTkFont(size=11)
        )
        important_checkbox.pack(anchor="w", pady=2)
        
        # Additional details
        details_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 10))
        
        # Category
        category_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        category_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(category_frame, text="Catégorie:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.category_var = ctk.StringVar(value="Travail")
        category_menu = ctk.CTkOptionMenu(
            category_frame,
            variable=self.category_var,
            values=["Travail", "Personnel", "Projet", "Apprentissage", "Créatif", "Administratif"],
            width=150
        )
        category_menu.pack(side="right")
        
        # Duration
        duration_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(duration_frame, text="Durée estimée:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.duration_var = ctk.StringVar(value="60")
        duration_menu = ctk.CTkOptionMenu(
            duration_frame,
            variable=self.duration_var,
            values=["15", "30", "45", "60", "90", "120", "180", "240"],
            width=100
        )
        duration_menu.pack(side="right")
        
        ctk.CTkLabel(duration_frame, text="minutes", font=ctk.CTkFont(size=11)).pack(side="right", padx=(5, 10))
        
        # Deadline
        deadline_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        deadline_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(deadline_frame, text="Échéance:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.deadline_entry = ctk.CTkEntry(
            deadline_frame,
            placeholder_text="YYYY-MM-DD (optionnel)",
            width=150
        )
        self.deadline_entry.pack(side="right")
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        ok_btn = ctk.CTkButton(
            buttons_frame,
            text="OK",
            command=self._on_ok
        )
        ok_btn.pack(side="right")
        
        # Fill with existing data if editing
        if task_data:
            self.title_entry.insert(0, task_data.get('title', ''))
            self.desc_text.insert("1.0", task_data.get('description', ''))
            self.urgent_var.set(task_data.get('urgent', False))
            self.important_var.set(task_data.get('important', False))
            self.category_var.set(task_data.get('category', 'Travail'))
            self.duration_var.set(str(task_data.get('estimated_duration', 60)))
            
            deadline = task_data.get('deadline')
            if deadline:
                try:
                    if isinstance(deadline, str):
                        deadline_date = datetime.fromisoformat(deadline)
                    else:
                        deadline_date = deadline
                    self.deadline_entry.insert(0, deadline_date.strftime('%Y-%m-%d'))
                except:
                    pass
    
    def _on_ok(self):
        """Handle OK button."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire.")
            return
        
        description = self.desc_text.get("1.0", "end").strip()
        
        # Parse deadline
        deadline = None
        deadline_str = self.deadline_entry.get().strip()
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide. Utilisez YYYY-MM-DD.")
                return
        
        # Parse duration
        try:
            duration = int(self.duration_var.get())
        except ValueError:
            duration = 60
        
        self.task_data = {
            'title': title,
            'description': description,
            'urgent': self.urgent_var.get(),
            'important': self.important_var.get(),
            'category': self.category_var.get(),
            'duration': duration,
            'deadline': deadline
        }
        
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result


class TaskImportDialog(ctk.CTkToplevel):
    """Dialog for importing tasks from database."""
    
    def __init__(self, parent, tasks: List[Dict]):
        """Initialize import dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.tasks = tasks
        self.selected_tasks = []
        self.result = False
        
        # Configure dialog
        self.title("Importer des Tâches")
        self.geometry("600x500")
        self.resizable(True, True)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _center_on_parent(self):
        """Center dialog on parent."""
        self.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _setup_dialog(self):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"📥 Importer des Tâches ({len(self.tasks)} disponibles)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Selection controls
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        select_all_btn = ctk.CTkButton(
            controls_frame,
            text="Tout Sélectionner",
            command=self._select_all,
            width=120
        )
        select_all_btn.pack(side="left")
        
        select_none_btn = ctk.CTkButton(
            controls_frame,
            text="Tout Désélectionner",
            command=self._select_none,
            width=140
        )
        select_none_btn.pack(side="left", padx=(10, 0))
        
        # Tasks list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.tasks_listbox = ctk.CTkScrollableFrame(list_frame)
        self.tasks_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create task checkboxes
        self.task_vars = []
        for i, task in enumerate(self.tasks):
            var = ctk.BooleanVar()
            self.task_vars.append(var)
            
            task_frame = ctk.CTkFrame(self.tasks_listbox, fg_color="transparent")
            task_frame.pack(fill="x", pady=2)
            
            checkbox = ctk.CTkCheckBox(
                task_frame,
                text="",
                variable=var,
                width=20
            )
            checkbox.pack(side="left", padx=(0, 10))
            
            # Task info
            info_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)
            
            title_label = ctk.CTkLabel(
                info_frame,
                text=task['title'],
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            title_label.pack(anchor="w")
            
            # Task details
            details = []
            if task.get('category'):
                details.append(f"📁 {task['category']}")
            if task.get('priority'):
                priority_text = ["Faible", "Moyenne", "Élevée", "Critique"][min(task['priority']-1, 3)]
                details.append(f"⭐ {priority_text}")
            if task.get('deadline'):
                try:
                    deadline = task['deadline']
                    if isinstance(deadline, str):
                        deadline_date = datetime.fromisoformat(deadline)
                    else:
                        deadline_date = deadline
                    details.append(f"📅 {deadline_date.strftime('%d/%m/%Y')}")
                except:
                    pass
            
            if details:
                details_label = ctk.CTkLabel(
                    info_frame,
                    text=" • ".join(details),
                    font=ctk.CTkFont(size=10),
                    text_color="gray",
                    anchor="w"
                )
                details_label.pack(anchor="w")
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        import_btn = ctk.CTkButton(
            buttons_frame,
            text="Importer Sélectionnées",
            command=self._on_import
        )
        import_btn.pack(side="right")
    
    def _select_all(self):
        """Select all tasks."""
        for var in self.task_vars:
            var.set(True)
    
    def _select_none(self):
        """Deselect all tasks."""
        for var in self.task_vars:
            var.set(False)
    
    def _on_import(self):
        """Handle import button."""
        self.selected_tasks = []
        for i, var in enumerate(self.task_vars):
            if var.get():
                self.selected_tasks.append(self.tasks[i])
        
        if not self.selected_tasks:
            messagebox.showwarning("Aucune Sélection", "Veuillez sélectionner au moins une tâche.")
            return
        
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result


if __name__ == "__main__":
    # Test the Priority Grid tool
    import sys
    sys.path.append('../..')
    
    app = ctk.CTk()
    app.geometry("1200x800")
    app.title("Priority Grid Test")
    
    tool = PriorityGridTool(app)
    tool.pack(fill="both", expand=True)
    
    app.mainloop()