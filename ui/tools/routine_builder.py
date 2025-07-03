#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Routine Builder Tool

Tool for creating, managing, and optimizing daily routines.
Supports both Magic (simple) and Genie (AI-powered) modes.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, time, timedelta
import threading
import uuid

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class RoutineBuilderTool(BaseToolWindow):
    """Routine Builder tool for creating and managing routines."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Routine Builder tool."""
        super().__init__(
            parent, 
            "Constructeur de Routines", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Current routine data
        self.current_routine = {
            'id': None,
            'name': '',
            'description': '',
            'category': 'personal',
            'frequency': 'daily',
            'time_slots': [],
            'steps': [],
            'duration': 0,
            'difficulty': 'medium',
            'tags': [],
            'active': True,
            'created_date': None,
            'last_modified': None
        }
        
        # Routine categories
        self.categories = {
            'personal': '👤 Personnel',
            'work': '💼 Travail',
            'health': '🏥 Santé',
            'fitness': '💪 Fitness',
            'learning': '📚 Apprentissage',
            'creative': '🎨 Créatif',
            'social': '👥 Social',
            'spiritual': '🧘 Spirituel',
            'household': '🏠 Maison',
            'other': '📋 Autre'
        }
        
        # Frequency options
        self.frequencies = {
            'daily': 'Quotidien',
            'weekly': 'Hebdomadaire',
            'monthly': 'Mensuel',
            'custom': 'Personnalisé'
        }
        
        # Predefined routine templates
        self.routine_templates = {
            'morning_routine': {
                'name': 'Routine Matinale',
                'description': 'Routine pour bien commencer la journée',
                'category': 'personal',
                'steps': [
                    {'name': 'Réveil', 'duration': 5, 'description': 'Se lever et s\'étirer'},
                    {'name': 'Hydratation', 'duration': 2, 'description': 'Boire un verre d\'eau'},
                    {'name': 'Méditation', 'duration': 10, 'description': 'Méditation ou respiration'},
                    {'name': 'Exercice', 'duration': 20, 'description': 'Exercices physiques légers'},
                    {'name': 'Douche', 'duration': 15, 'description': 'Douche et hygiène'},
                    {'name': 'Petit-déjeuner', 'duration': 20, 'description': 'Repas équilibré'},
                    {'name': 'Planification', 'duration': 10, 'description': 'Réviser les objectifs du jour'}
                ]
            },
            'evening_routine': {
                'name': 'Routine du Soir',
                'description': 'Routine pour terminer la journée en douceur',
                'category': 'personal',
                'steps': [
                    {'name': 'Bilan du jour', 'duration': 10, 'description': 'Réfléchir sur la journée'},
                    {'name': 'Préparation lendemain', 'duration': 15, 'description': 'Préparer le jour suivant'},
                    {'name': 'Lecture', 'duration': 30, 'description': 'Lecture relaxante'},
                    {'name': 'Hygiène', 'duration': 15, 'description': 'Routine d\'hygiène du soir'},
                    {'name': 'Relaxation', 'duration': 10, 'description': 'Exercices de relaxation'},
                    {'name': 'Coucher', 'duration': 5, 'description': 'Se mettre au lit'}
                ]
            },
            'workout_routine': {
                'name': 'Routine d\'Entraînement',
                'description': 'Routine de fitness complète',
                'category': 'fitness',
                'steps': [
                    {'name': 'Échauffement', 'duration': 10, 'description': 'Échauffement général'},
                    {'name': 'Cardio', 'duration': 20, 'description': 'Exercices cardiovasculaires'},
                    {'name': 'Musculation', 'duration': 30, 'description': 'Exercices de renforcement'},
                    {'name': 'Étirements', 'duration': 10, 'description': 'Étirements et récupération'},
                    {'name': 'Hydratation', 'duration': 5, 'description': 'Boire et récupérer'}
                ]
            },
            'study_routine': {
                'name': 'Routine d\'Étude',
                'description': 'Routine pour optimiser l\'apprentissage',
                'category': 'learning',
                'steps': [
                    {'name': 'Préparation', 'duration': 5, 'description': 'Organiser l\'espace de travail'},
                    {'name': 'Révision', 'duration': 15, 'description': 'Réviser les concepts précédents'},
                    {'name': 'Apprentissage', 'duration': 45, 'description': 'Étudier nouveau contenu'},
                    {'name': 'Pause', 'duration': 10, 'description': 'Pause active'},
                    {'name': 'Pratique', 'duration': 30, 'description': 'Exercices et applications'},
                    {'name': 'Synthèse', 'duration': 10, 'description': 'Résumer et noter les points clés'}
                ]
            }
        }
        
        # Loaded routines
        self.routines = []
        
        self.logger.info("Routine Builder tool initialized")
    
    def _setup_tool_content(self):
        """Setup Routine Builder specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Top panel - Routine management
        self._create_management_panel()
        
        # Main content area - Routine editor
        self._create_editor_area()
        
        # Bottom panel - Actions and templates
        self._create_actions_panel()
        
        # Load existing routines
        self._load_routines()
    
    def _create_management_panel(self):
        """Create routine management panel."""
        management_panel = ctk.CTkFrame(self.content_frame, height=80)
        management_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        management_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - Routine selection
        selection_frame = ctk.CTkFrame(management_panel, fg_color="transparent")
        selection_frame.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        ctk.CTkLabel(
            selection_frame,
            text="📋 Routine:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 5))
        
        self.routine_var = ctk.StringVar(value="Nouvelle Routine")
        self.routine_menu = ctk.CTkOptionMenu(
            selection_frame,
            variable=self.routine_var,
            values=["Nouvelle Routine"],
            width=200,
            command=self._on_routine_select
        )
        self.routine_menu.pack(side="left", padx=5)
        
        # Center - Quick info
        info_frame = ctk.CTkFrame(management_panel, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="", padx=15, pady=15)
        
        self.routine_info_label = ctk.CTkLabel(
            info_frame,
            text="💡 Créez une nouvelle routine ou sélectionnez-en une existante",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.routine_info_label.pack()
        
        # Right side - Management actions
        actions_frame = ctk.CTkFrame(management_panel, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        new_btn = ctk.CTkButton(
            actions_frame,
            text="➕ Nouveau",
            height=30,
            command=self._new_routine
        )
        new_btn.pack(side="left", padx=(0, 5))
        
        save_btn = ctk.CTkButton(
            actions_frame,
            text="💾 Sauver",
            height=30,
            command=self._save_routine
        )
        save_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️ Supprimer",
            height=30,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._delete_routine
        )
        delete_btn.pack(side="left", padx=(5, 0))
    
    def _create_editor_area(self):
        """Create routine editor area."""
        editor_area = ctk.CTkFrame(self.content_frame)
        editor_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        editor_area.grid_columnconfigure(0, weight=1)
        editor_area.grid_columnconfigure(1, weight=2)
        editor_area.grid_rowconfigure(0, weight=1)
        
        # Left side - Routine details
        details_frame = ctk.CTkFrame(editor_area)
        details_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Details header
        ctk.CTkLabel(
            details_frame,
            text="📝 Détails de la Routine",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))
        
        # Routine name
        name_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            name_frame,
            text="Nom:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Nom de la routine",
            font=ctk.CTkFont(size=12)
        )
        self.name_entry.pack(fill="x", pady=(2, 0))
        self.name_entry.bind("<KeyRelease>", self._on_details_change)
        
        # Description
        desc_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            desc_frame,
            text="Description:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.description_text = ctk.CTkTextbox(
            desc_frame,
            height=60,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.description_text.pack(fill="x", pady=(2, 0))
        self.description_text.bind("<KeyRelease>", self._on_details_change)
        
        # Category and frequency
        settings_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=15, pady=5)
        
        # Category
        cat_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            cat_frame,
            text="Catégorie:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.category_var = ctk.StringVar(value="personal")
        category_menu = ctk.CTkOptionMenu(
            cat_frame,
            variable=self.category_var,
            values=list(self.categories.values()),
            command=self._on_category_change
        )
        category_menu.pack(fill="x", pady=(2, 0))
        
        # Frequency
        freq_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        freq_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            freq_frame,
            text="Fréquence:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.frequency_var = ctk.StringVar(value="daily")
        frequency_menu = ctk.CTkOptionMenu(
            freq_frame,
            variable=self.frequency_var,
            values=list(self.frequencies.values()),
            command=self._on_frequency_change
        )
        frequency_menu.pack(fill="x", pady=(2, 0))
        
        # Difficulty
        diff_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        diff_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            diff_frame,
            text="Difficulté:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.difficulty_var = ctk.StringVar(value="medium")
        difficulty_menu = ctk.CTkOptionMenu(
            diff_frame,
            variable=self.difficulty_var,
            values=["Facile", "Moyen", "Difficile"],
            command=self._on_difficulty_change
        )
        difficulty_menu.pack(fill="x", pady=(2, 0))
        
        # Tags
        tags_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            tags_frame,
            text="Tags (séparés par des virgules):",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")
        
        self.tags_entry = ctk.CTkEntry(
            tags_frame,
            placeholder_text="ex: matin, santé, productivité",
            font=ctk.CTkFont(size=11)
        )
        self.tags_entry.pack(fill="x", pady=(2, 0))
        self.tags_entry.bind("<KeyRelease>", self._on_details_change)
        
        # Duration and status
        status_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=10)
        
        self.duration_label = ctk.CTkLabel(
            status_frame,
            text="⏱️ Durée totale: 0 min",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.duration_label.pack(anchor="w", pady=2)
        
        self.steps_count_label = ctk.CTkLabel(
            status_frame,
            text="📋 Étapes: 0",
            font=ctk.CTkFont(size=11)
        )
        self.steps_count_label.pack(anchor="w", pady=2)
        
        self.active_var = ctk.BooleanVar(value=True)
        active_check = ctk.CTkCheckBox(
            status_frame,
            text="Routine active",
            variable=self.active_var,
            command=self._on_details_change
        )
        active_check.pack(anchor="w", pady=5)
        
        # Right side - Steps editor
        steps_frame = ctk.CTkFrame(editor_area)
        steps_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_rowconfigure(1, weight=1)
        
        # Steps header
        steps_header = ctk.CTkFrame(steps_frame, height=50, fg_color="transparent")
        steps_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        steps_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            steps_header,
            text="🔄 Étapes de la Routine",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Steps actions
        steps_actions = ctk.CTkFrame(steps_header, fg_color="transparent")
        steps_actions.grid(row=0, column=1, sticky="e")
        
        add_step_btn = ctk.CTkButton(
            steps_actions,
            text="➕ Ajouter",
            height=30,
            command=self._add_step
        )
        add_step_btn.pack(side="left", padx=(0, 5))
        
        if self.is_ai_enabled:
            optimize_btn = ctk.CTkButton(
                steps_actions,
                text="🤖 Optimiser",
                height=30,
                command=self._optimize_routine
            )
            optimize_btn.pack(side="left")
        
        # Steps list
        self.steps_frame = ctk.CTkScrollableFrame(steps_frame)
        self.steps_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Initialize empty steps list
        self._update_steps_display()
    
    def _create_actions_panel(self):
        """Create actions panel."""
        actions_panel = ctk.CTkFrame(self.content_frame, height=80)
        actions_panel.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        actions_panel.grid_columnconfigure(1, weight=1)
        
        # Left actions
        left_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        templates_btn = ctk.CTkButton(
            left_actions,
            text="📋 Modèles",
            height=35,
            command=self._show_templates
        )
        templates_btn.pack(side="left", padx=(0, 5))
        
        import_btn = ctk.CTkButton(
            left_actions,
            text="📥 Importer",
            height=35,
            command=self._import_routine
        )
        import_btn.pack(side="left", padx=5)
        
        # Center - AI suggestions (if available)
        if self.is_ai_enabled:
            suggestions_frame = ctk.CTkFrame(actions_panel, fg_color="transparent")
            suggestions_frame.grid(row=0, column=1, sticky="", padx=15, pady=15)
            
            self.suggestions_label = ctk.CTkLabel(
                suggestions_frame,
                text="🤖 Suggestions IA disponibles après optimisation",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            self.suggestions_label.pack()
        
        # Right actions
        right_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        right_actions.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        preview_btn = ctk.CTkButton(
            right_actions,
            text="👁️ Aperçu",
            height=35,
            command=self._preview_routine
        )
        preview_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(
            right_actions,
            text="📤 Exporter",
            height=35,
            command=self._export_routine
        )
        export_btn.pack(side="left", padx=(5, 0))
    
    def _load_routines(self):
        """Load existing routines from database."""
        try:
            if self.database_manager:
                # TODO: Load routines from database
                # For now, use empty list
                self.routines = []
            
            # Update routine menu
            routine_names = ["Nouvelle Routine"] + [r.get('name', 'Sans nom') for r in self.routines]
            self.routine_menu.configure(values=routine_names)
            
        except Exception as e:
            self.logger.error(f"Failed to load routines: {e}")
    
    def _new_routine(self):
        """Create a new routine."""
        if self._has_unsaved_changes():
            if not messagebox.askyesno("Changements Non Sauvés", 
                                     "Vous avez des changements non sauvés. Continuer ?"):
                return
        
        # Reset current routine
        self.current_routine = {
            'id': None,
            'name': '',
            'description': '',
            'category': 'personal',
            'frequency': 'daily',
            'time_slots': [],
            'steps': [],
            'duration': 0,
            'difficulty': 'medium',
            'tags': [],
            'active': True,
            'created_date': None,
            'last_modified': None
        }
        
        # Update UI
        self._update_routine_display()
        self.routine_var.set("Nouvelle Routine")
        self._update_routine_info()
    
    def _save_routine(self):
        """Save current routine."""
        # Validate routine
        if not self._validate_routine():
            return
        
        try:
            # Update current routine data
            self._update_routine_from_ui()
            
            # Set timestamps
            now = datetime.now().isoformat()
            if not self.current_routine['created_date']:
                self.current_routine['created_date'] = now
            self.current_routine['last_modified'] = now
            
            # Generate ID if new routine
            if not self.current_routine['id']:
                self.current_routine['id'] = str(uuid.uuid4())
            
            # TODO: Save to database
            if self.database_manager:
                # Save routine to database
                pass
            
            # Update routines list
            existing_index = None
            for i, routine in enumerate(self.routines):
                if routine.get('id') == self.current_routine['id']:
                    existing_index = i
                    break
            
            if existing_index is not None:
                self.routines[existing_index] = self.current_routine.copy()
            else:
                self.routines.append(self.current_routine.copy())
            
            # Update UI
            self._load_routines()
            self.routine_var.set(self.current_routine['name'])
            
            messagebox.showinfo("Succès", "Routine sauvée avec succès.")
            
        except Exception as e:
            self.logger.error(f"Failed to save routine: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def _delete_routine(self):
        """Delete current routine."""
        if not self.current_routine.get('id'):
            messagebox.showwarning("Aucune Routine", "Aucune routine à supprimer.")
            return
        
        if not messagebox.askyesno("Confirmer Suppression", 
                                 f"Supprimer la routine '{self.current_routine['name']}' ?"):
            return
        
        try:
            # TODO: Delete from database
            if self.database_manager:
                # Delete routine from database
                pass
            
            # Remove from routines list
            self.routines = [r for r in self.routines if r.get('id') != self.current_routine['id']]
            
            # Reset to new routine
            self._new_routine()
            
            messagebox.showinfo("Succès", "Routine supprimée avec succès.")
            
        except Exception as e:
            self.logger.error(f"Failed to delete routine: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def _on_routine_select(self, value):
        """Handle routine selection."""
        if value == "Nouvelle Routine":
            self._new_routine()
            return
        
        # Find selected routine
        selected_routine = None
        for routine in self.routines:
            if routine.get('name') == value:
                selected_routine = routine
                break
        
        if selected_routine:
            if self._has_unsaved_changes():
                if not messagebox.askyesno("Changements Non Sauvés", 
                                         "Vous avez des changements non sauvés. Continuer ?"):
                    # Revert selection
                    self.routine_var.set(self.current_routine.get('name', 'Nouvelle Routine'))
                    return
            
            # Load selected routine
            self.current_routine = selected_routine.copy()
            self._update_routine_display()
            self._update_routine_info()
    
    def _update_routine_display(self):
        """Update UI with current routine data."""
        # Update details
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.current_routine.get('name', ''))
        
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", self.current_routine.get('description', ''))
        
        # Update category
        category = self.current_routine.get('category', 'personal')
        category_display = self.categories.get(category, self.categories['personal'])
        self.category_var.set(category_display)
        
        # Update frequency
        frequency = self.current_routine.get('frequency', 'daily')
        frequency_display = self.frequencies.get(frequency, self.frequencies['daily'])
        self.frequency_var.set(frequency_display)
        
        # Update difficulty
        difficulty = self.current_routine.get('difficulty', 'medium')
        difficulty_map = {'easy': 'Facile', 'medium': 'Moyen', 'hard': 'Difficile'}
        difficulty_display = difficulty_map.get(difficulty, 'Moyen')
        self.difficulty_var.set(difficulty_display)
        
        # Update tags
        tags = self.current_routine.get('tags', [])
        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ', '.join(tags))
        
        # Update active status
        self.active_var.set(self.current_routine.get('active', True))
        
        # Update steps
        self._update_steps_display()
        
        # Update info
        self._update_routine_info()
    
    def _update_routine_from_ui(self):
        """Update current routine data from UI."""
        self.current_routine['name'] = self.name_entry.get().strip()
        self.current_routine['description'] = self.description_text.get("1.0", "end-1c").strip()
        
        # Category
        category_display = self.category_var.get()
        for key, value in self.categories.items():
            if value == category_display:
                self.current_routine['category'] = key
                break
        
        # Frequency
        frequency_display = self.frequency_var.get()
        for key, value in self.frequencies.items():
            if value == frequency_display:
                self.current_routine['frequency'] = key
                break
        
        # Difficulty
        difficulty_display = self.difficulty_var.get()
        difficulty_map = {'Facile': 'easy', 'Moyen': 'medium', 'Difficile': 'hard'}
        self.current_routine['difficulty'] = difficulty_map.get(difficulty_display, 'medium')
        
        # Tags
        tags_text = self.tags_entry.get().strip()
        self.current_routine['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Active status
        self.current_routine['active'] = self.active_var.get()
        
        # Calculate total duration
        total_duration = sum(step.get('duration', 0) for step in self.current_routine['steps'])
        self.current_routine['duration'] = total_duration
    
    def _update_steps_display(self):
        """Update steps display."""
        # Clear existing steps
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        steps = self.current_routine.get('steps', [])
        
        if not steps:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.steps_frame,
                text="📝 Aucune étape définie\n\nCliquez sur 'Ajouter' pour commencer",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                justify="center"
            )
            empty_label.pack(expand=True, pady=50)
        else:
            # Show steps
            for i, step in enumerate(steps):
                self._create_step_widget(i, step)
        
        # Update duration and count
        self._update_routine_info()
    
    def _create_step_widget(self, index: int, step: Dict[str, Any]):
        """Create a step widget."""
        step_frame = ctk.CTkFrame(self.steps_frame)
        step_frame.pack(fill="x", pady=5)
        step_frame.grid_columnconfigure(1, weight=1)
        
        # Step number and drag handle
        number_frame = ctk.CTkFrame(step_frame, width=40, fg_color="transparent")
        number_frame.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(10, 5), pady=10)
        
        step_number = ctk.CTkLabel(
            number_frame,
            text=f"{index + 1}",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=30,
            height=30,
            fg_color="#3498DB",
            corner_radius=15
        )
        step_number.pack(pady=(0, 5))
        
        # Drag handle (visual only for now)
        drag_label = ctk.CTkLabel(
            number_frame,
            text="⋮⋮",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        drag_label.pack()
        
        # Step content
        content_frame = ctk.CTkFrame(step_frame, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Step name and duration
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        step_name = ctk.CTkLabel(
            header_frame,
            text=step.get('name', 'Étape sans nom'),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        step_name.grid(row=0, column=0, sticky="ew")
        
        duration_label = ctk.CTkLabel(
            header_frame,
            text=f"⏱️ {step.get('duration', 0)} min",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        duration_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        # Step description
        if step.get('description'):
            desc_label = ctk.CTkLabel(
                content_frame,
                text=step['description'],
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w",
                justify="left"
            )
            desc_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Step actions
        actions_frame = ctk.CTkFrame(step_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=2, rowspan=2, sticky="ns", padx=(5, 10), pady=10)
        
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=30,
            height=25,
            command=lambda idx=index: self._edit_step(idx)
        )
        edit_btn.pack(pady=(0, 2))
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=30,
            height=25,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda idx=index: self._delete_step(idx)
        )
        delete_btn.pack(pady=2)
        
        # Move buttons
        if index > 0:
            up_btn = ctk.CTkButton(
                actions_frame,
                text="⬆️",
                width=30,
                height=25,
                command=lambda idx=index: self._move_step(idx, -1)
            )
            up_btn.pack(pady=2)
        
        if index < len(self.current_routine['steps']) - 1:
            down_btn = ctk.CTkButton(
                actions_frame,
                text="⬇️",
                width=30,
                height=25,
                command=lambda idx=index: self._move_step(idx, 1)
            )
            down_btn.pack(pady=2)
    
    def _add_step(self):
        """Add a new step."""
        dialog = StepDialog(self)
        result = dialog.show()
        
        if result and dialog.step_data:
            self.current_routine['steps'].append(dialog.step_data)
            self._update_steps_display()
    
    def _edit_step(self, index: int):
        """Edit a step."""
        if 0 <= index < len(self.current_routine['steps']):
            step = self.current_routine['steps'][index]
            dialog = StepDialog(self, step)
            result = dialog.show()
            
            if result and dialog.step_data:
                self.current_routine['steps'][index] = dialog.step_data
                self._update_steps_display()
    
    def _delete_step(self, index: int):
        """Delete a step."""
        if 0 <= index < len(self.current_routine['steps']):
            step = self.current_routine['steps'][index]
            if messagebox.askyesno("Confirmer Suppression", 
                                 f"Supprimer l'étape '{step.get('name', 'Sans nom')}' ?"):
                del self.current_routine['steps'][index]
                self._update_steps_display()
    
    def _move_step(self, index: int, direction: int):
        """Move a step up or down."""
        steps = self.current_routine['steps']
        new_index = index + direction
        
        if 0 <= new_index < len(steps):
            steps[index], steps[new_index] = steps[new_index], steps[index]
            self._update_steps_display()
    
    def _update_routine_info(self):
        """Update routine info display."""
        steps = self.current_routine.get('steps', [])
        total_duration = sum(step.get('duration', 0) for step in steps)
        
        self.duration_label.configure(text=f"⏱️ Durée totale: {total_duration} min")
        self.steps_count_label.configure(text=f"📋 Étapes: {len(steps)}")
        
        # Update routine info in management panel
        if self.current_routine.get('name'):
            info_text = f"📋 {self.current_routine['name']} - {total_duration} min - {len(steps)} étapes"
        else:
            info_text = "💡 Créez une nouvelle routine ou sélectionnez-en une existante"
        
        self.routine_info_label.configure(text=info_text)
    
    def _validate_routine(self) -> bool:
        """Validate current routine."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom de la routine est requis.")
            return False
        
        if not self.current_routine.get('steps'):
            messagebox.showerror("Erreur", "La routine doit contenir au moins une étape.")
            return False
        
        return True
    
    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        # Simple check - compare current UI with saved routine
        # This is a simplified implementation
        current_name = self.name_entry.get().strip()
        saved_name = self.current_routine.get('name', '')
        
        return current_name != saved_name or len(self.current_routine.get('steps', [])) > 0
    
    def _on_details_change(self, event=None):
        """Handle details change."""
        # Update routine info when details change
        self.after_idle(self._update_routine_info)
    
    def _on_category_change(self, value):
        """Handle category change."""
        self._on_details_change()
    
    def _on_frequency_change(self, value):
        """Handle frequency change."""
        self._on_details_change()
    
    def _on_difficulty_change(self, value):
        """Handle difficulty change."""
        self._on_details_change()
    
    def _show_templates(self):
        """Show routine templates."""
        dialog = TemplateSelectionDialog(self, self.routine_templates)
        result = dialog.show()
        
        if result and dialog.selected_template:
            if self._has_unsaved_changes():
                if not messagebox.askyesno("Changements Non Sauvés", 
                                         "Appliquer le modèle effacera les changements actuels. Continuer ?"):
                    return
            
            # Apply template
            template = dialog.selected_template
            self.current_routine.update({
                'name': template['name'],
                'description': template['description'],
                'category': template['category'],
                'steps': template['steps'].copy(),
                'id': None,  # New routine
                'created_date': None,
                'last_modified': None
            })
            
            self._update_routine_display()
    
    def _import_routine(self):
        """Import routine from file."""
        # TODO: Implement routine import
        messagebox.showinfo("Info", "Import en développement")
    
    def _optimize_routine(self):
        """Optimize routine using AI."""
        if not self.is_ai_enabled:
            return
        
        steps = self.current_routine.get('steps', [])
        if not steps:
            messagebox.showwarning("Aucune Étape", "Ajoutez des étapes avant d'optimiser.")
            return
        
        # TODO: Implement AI optimization
        messagebox.showinfo("Info", "Optimisation IA en développement")
    
    def _preview_routine(self):
        """Preview routine execution."""
        if not self.current_routine.get('steps'):
            messagebox.showwarning("Aucune Étape", "Aucune étape à prévisualiser.")
            return
        
        dialog = RoutinePreviewDialog(self, self.current_routine)
        dialog.show()
    
    def _export_routine(self):
        """Export routine to file."""
        if not self.current_routine.get('steps'):
            messagebox.showwarning("Aucune Étape", "Aucune routine à exporter.")
            return
        
        # TODO: Implement routine export
        messagebox.showinfo("Info", "Export en développement")


class StepDialog(ctk.CTkToplevel):
    """Dialog for creating/editing routine steps."""
    
    def __init__(self, parent, step_data: Dict[str, Any] = None):
        """Initialize step dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.step_data = step_data.copy() if step_data else {
            'name': '',
            'description': '',
            'duration': 5,
            'category': 'action',
            'required': True,
            'notes': ''
        }
        self.result = False
        
        # Configure dialog
        self.title("Éditer Étape" if step_data else "Nouvelle Étape")
        self.geometry("500x600")
        self.resizable(False, False)
        
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
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_text = "✏️ Éditer Étape" if self.step_data.get('name') else "➕ Nouvelle Étape"
        title_label = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # Step name
        name_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        name_frame.grid(row=1, column=0, sticky="ew", pady=5)
        name_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            name_frame,
            text="Nom de l'étape *",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="ex: Méditation matinale",
            font=ctk.CTkFont(size=12)
        )
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.name_entry.insert(0, self.step_data.get('name', ''))
        
        # Duration
        duration_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        duration_frame.grid(row=2, column=0, sticky="ew", pady=5)
        duration_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            duration_frame,
            text="Durée (minutes) *",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        duration_input_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        duration_input_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        duration_input_frame.grid_columnconfigure(0, weight=1)
        
        self.duration_var = ctk.IntVar(value=self.step_data.get('duration', 5))
        self.duration_entry = ctk.CTkEntry(
            duration_input_frame,
            textvariable=self.duration_var,
            width=100
        )
        self.duration_entry.grid(row=0, column=0, sticky="w")
        
        # Duration slider
        self.duration_slider = ctk.CTkSlider(
            duration_input_frame,
            from_=1,
            to=120,
            number_of_steps=119,
            variable=self.duration_var,
            command=self._on_duration_change
        )
        self.duration_slider.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Description
        desc_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        desc_frame.grid(row=3, column=0, sticky="ew", pady=5)
        desc_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            desc_frame,
            text="Description",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.description_text = ctk.CTkTextbox(
            desc_frame,
            height=80,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.description_text.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.description_text.insert("1.0", self.step_data.get('description', ''))
        
        # Category
        category_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        category_frame.grid(row=4, column=0, sticky="ew", pady=5)
        category_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            category_frame,
            text="Catégorie",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.category_var = ctk.StringVar(value=self.step_data.get('category', 'action'))
        category_menu = ctk.CTkOptionMenu(
            category_frame,
            variable=self.category_var,
            values=["action", "pause", "reflection", "exercise", "preparation", "cleanup"]
        )
        category_menu.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Options
        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.grid(row=5, column=0, sticky="ew", pady=5)
        
        self.required_var = ctk.BooleanVar(value=self.step_data.get('required', True))
        required_check = ctk.CTkCheckBox(
            options_frame,
            text="Étape obligatoire",
            variable=self.required_var
        )
        required_check.pack(anchor="w", pady=2)
        
        # Notes
        notes_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        notes_frame.grid(row=6, column=0, sticky="ew", pady=5)
        notes_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            notes_frame,
            text="Notes",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            height=60,
            font=ctk.CTkFont(size=10),
            wrap="word"
        )
        self.notes_text.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.notes_text.insert("1.0", self.step_data.get('notes', ''))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=7, column=0, sticky="ew", pady=(20, 0))
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Sauver",
            command=self._on_save
        )
        save_btn.pack(side="right")
    
    def _on_duration_change(self, value):
        """Handle duration slider change."""
        self.duration_var.set(int(value))
    
    def _on_save(self):
        """Handle save button."""
        # Validate input
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom de l'étape est requis.")
            return
        
        duration = self.duration_var.get()
        if duration < 1:
            messagebox.showerror("Erreur", "La durée doit être d'au moins 1 minute.")
            return
        
        # Update step data
        self.step_data.update({
            'name': name,
            'description': self.description_text.get("1.0", "end-1c").strip(),
            'duration': duration,
            'category': self.category_var.get(),
            'required': self.required_var.get(),
            'notes': self.notes_text.get("1.0", "end-1c").strip()
        })
        
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


class TemplateSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting routine templates."""
    
    def __init__(self, parent, templates: Dict[str, Dict]):
        """Initialize template selection dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.templates = templates
        self.selected_template = None
        self.result = False
        
        # Configure dialog
        self.title("Modèles de Routines")
        self.geometry("700x500")
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
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📋 Choisir un Modèle de Routine",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Templates grid
        templates_frame = ctk.CTkScrollableFrame(main_frame)
        templates_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        
        # Create template cards
        self.template_vars = []
        template_keys = list(self.templates.keys())
        
        for i, (template_key, template_data) in enumerate(self.templates.items()):
            var = ctk.StringVar()
            self.template_vars.append(var)
            
            # Template card
            card_frame = ctk.CTkFrame(templates_frame)
            card_frame.pack(fill="x", pady=5)
            card_frame.grid_columnconfigure(1, weight=1)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                card_frame,
                text="",
                variable=var,
                value=str(i),
                command=lambda idx=i: self._select_template(idx)
            )
            radio.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="n")
            
            # Template info
            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
            info_frame.grid_columnconfigure(0, weight=1)
            
            # Template name
            name_label = ctk.CTkLabel(
                info_frame,
                text=template_data['name'],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_label.grid(row=0, column=0, sticky="ew")
            
            # Template description
            desc_label = ctk.CTkLabel(
                info_frame,
                text=template_data['description'],
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                justify="left"
            )
            desc_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
            
            # Template stats
            steps_count = len(template_data.get('steps', []))
            total_duration = sum(step.get('duration', 0) for step in template_data.get('steps', []))
            
            stats_label = ctk.CTkLabel(
                info_frame,
                text=f"📋 {steps_count} étapes • ⏱️ {total_duration} min",
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w"
            )
            stats_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel
        )
        cancel_btn.pack(side="left")
        
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Appliquer",
            command=self._on_apply
        )
        apply_btn.pack(side="right")
    
    def _select_template(self, index: int):
        """Select a template."""
        for i, var in enumerate(self.template_vars):
            if i == index:
                var.set(str(i))
            else:
                var.set("")
    
    def _on_apply(self):
        """Handle apply button."""
        selected_index = None
        for i, var in enumerate(self.template_vars):
            if var.get() == str(i):
                selected_index = i
                break
        
        if selected_index is None:
            messagebox.showwarning("Aucune Sélection", "Veuillez sélectionner un modèle.")
            return
        
        template_keys = list(self.templates.keys())
        template_key = template_keys[selected_index]
        self.selected_template = self.templates[template_key]
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


class RoutinePreviewDialog(ctk.CTkToplevel):
    """Dialog for previewing routine execution."""
    
    def __init__(self, parent, routine_data: Dict[str, Any]):
        """Initialize routine preview dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.routine_data = routine_data
        
        # Configure dialog
        self.title(f"Aperçu - {routine_data.get('name', 'Routine')}")
        self.geometry("600x700")
        self.resizable(True, True)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())
    
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
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # Title and info
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"👁️ Aperçu - {self.routine_data.get('name', 'Routine')}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        
        # Routine summary
        summary_frame = ctk.CTkFrame(main_frame)
        summary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        steps = self.routine_data.get('steps', [])
        total_duration = sum(step.get('duration', 0) for step in steps)
        
        summary_text = (
            f"📋 {len(steps)} étapes • "
            f"⏱️ {total_duration} minutes • "
            f"🏷️ {self.routine_data.get('category', 'personnel').title()}"
        )
        
        ctk.CTkLabel(
            summary_frame,
            text=summary_text,
            font=ctk.CTkFont(size=12)
        ).pack(pady=15)
        
        # Steps timeline
        timeline_frame = ctk.CTkScrollableFrame(main_frame)
        timeline_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        
        current_time = 0
        for i, step in enumerate(steps):
            self._create_timeline_step(timeline_frame, i, step, current_time)
            current_time += step.get('duration', 0)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Fermer",
            command=self._on_close
        )
        close_btn.grid(row=3, column=0, pady=(0, 0))
    
    def _create_timeline_step(self, parent, index: int, step: Dict[str, Any], start_time: int):
        """Create a timeline step widget."""
        step_frame = ctk.CTkFrame(parent)
        step_frame.pack(fill="x", pady=5)
        step_frame.grid_columnconfigure(1, weight=1)
        
        # Time indicator
        time_frame = ctk.CTkFrame(step_frame, width=80)
        time_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        
        start_label = ctk.CTkLabel(
            time_frame,
            text=f"{start_time:02d}:{start_time%60:02d}",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        start_label.pack(pady=(5, 0))
        
        duration_label = ctk.CTkLabel(
            time_frame,
            text=f"{step.get('duration', 0)} min",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        duration_label.pack()
        
        # Step content
        content_frame = ctk.CTkFrame(step_frame, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Step name
        name_label = ctk.CTkLabel(
            content_frame,
            text=f"{index + 1}. {step.get('name', 'Étape sans nom')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="ew")
        
        # Step description
        if step.get('description'):
            desc_label = ctk.CTkLabel(
                content_frame,
                text=step['description'],
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w",
                justify="left"
            )
            desc_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Step category and required status
        meta_text = f"📂 {step.get('category', 'action')}"
        if not step.get('required', True):
            meta_text += " • 🔸 Optionnel"
        
        meta_label = ctk.CTkLabel(
            content_frame,
            text=meta_text,
            font=ctk.CTkFont(size=9),
            text_color="gray",
            anchor="w"
        )
        meta_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
    
    def _on_close(self):
        """Handle close."""
        self.destroy()
    
    def show(self):
        """Show dialog."""
        self.wait_window()


# Test block for direct execution
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directories to path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, parent_dir)
    
    # Create test application
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Test Routine Builder Tool")
    root.geometry("1400x900")
    
    # Create tool instance
    tool = RoutineBuilderTool(
        parent=root,
        magic_energy_level='genie'  # Test with AI features
    )
    tool.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()