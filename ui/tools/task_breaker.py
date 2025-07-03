#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Task Breaker Tool

Tool for decomposing complex tasks into manageable steps.
Supports both Magic (simple) and Genie (AI-powered) modes.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
import uuid

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class TaskBreakerTool(BaseToolWindow):
    """Task Breaker tool for decomposing complex tasks."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Task Breaker tool."""
        super().__init__(
            parent, 
            "Task Breaker", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Task data
        self.current_task = None
        self.subtasks = []
        self.templates = self._load_templates()
        
        # UI state
        self.selected_subtask = None
        
        self.logger.info("Task Breaker tool initialized")
    
    def _setup_tool_content(self):
        """Setup Task Breaker specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Create main container
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Left panel - Task input and templates
        self._create_input_panel(main_container)
        
        # Right panel - Subtasks breakdown
        self._create_breakdown_panel(main_container)
        
        # Bottom panel - Actions
        self._create_actions_panel(main_container)
    
    def _create_input_panel(self, parent):
        """Create task input panel."""
        input_panel = ctk.CTkFrame(parent, width=350)
        input_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5), pady=0)
        input_panel.grid_propagate(False)
        
        # Panel title
        title_label = ctk.CTkLabel(
            input_panel,
            text="📝 Tâche à Décomposer",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(15, 10))
        
        # Task title input
        title_frame = ctk.CTkFrame(input_panel, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(title_frame, text="Titre de la tâche:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        self.task_title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Ex: Organiser un événement d'entreprise",
            height=35
        )
        self.task_title_entry.pack(fill="x", pady=(5, 0))
        self.task_title_entry.bind("<KeyRelease>", self._on_task_input_change)
        
        # Task description
        desc_frame = ctk.CTkFrame(input_panel, fg_color="transparent")
        desc_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(desc_frame, text="Description détaillée:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        self.task_desc_text = ctk.CTkTextbox(
            desc_frame,
            height=120,
            placeholder_text="Décrivez votre tâche en détail...\n\nPlus vous donnez de détails, meilleure sera la décomposition."
        )
        self.task_desc_text.pack(fill="x", pady=(5, 0))
        self.task_desc_text.bind("<KeyRelease>", self._on_task_input_change)
        
        # Task properties
        props_frame = ctk.CTkFrame(input_panel, fg_color="transparent")
        props_frame.pack(fill="x", padx=15, pady=10)
        
        # Priority
        priority_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        priority_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(priority_frame, text="Priorité:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.priority_var = ctk.StringVar(value="Moyenne")
        priority_menu = ctk.CTkOptionMenu(
            priority_frame,
            variable=self.priority_var,
            values=["Faible", "Moyenne", "Élevée", "Urgente"],
            width=120
        )
        priority_menu.pack(side="right")
        
        # Estimated duration
        duration_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(duration_frame, text="Durée estimée:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.duration_var = ctk.StringVar(value="2-4 heures")
        duration_menu = ctk.CTkOptionMenu(
            duration_frame,
            variable=self.duration_var,
            values=["< 1 heure", "1-2 heures", "2-4 heures", "4-8 heures", "1-2 jours", "1 semaine+"],
            width=120
        )
        duration_menu.pack(side="right")
        
        # Category
        category_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        category_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(category_frame, text="Catégorie:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.category_var = ctk.StringVar(value="Travail")
        category_menu = ctk.CTkOptionMenu(
            category_frame,
            variable=self.category_var,
            values=["Travail", "Personnel", "Projet", "Apprentissage", "Créatif", "Administratif"],
            width=120
        )
        category_menu.pack(side="right")
        
        # Templates section
        templates_frame = ctk.CTkFrame(input_panel)
        templates_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            templates_frame,
            text="📋 Templates Prédéfinis",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Template buttons
        template_buttons_frame = ctk.CTkFrame(templates_frame, fg_color="transparent")
        template_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        for template_name in self.templates.keys():
            btn = ctk.CTkButton(
                template_buttons_frame,
                text=template_name,
                height=30,
                command=lambda name=template_name: self._apply_template(name)
            )
            btn.pack(fill="x", pady=2)
        
        # Decompose button
        self.decompose_btn = ctk.CTkButton(
            input_panel,
            text="🔨 Décomposer la Tâche",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._decompose_task
        )
        self.decompose_btn.pack(fill="x", padx=15, pady=15)
        
        # AI enhancement button (Genie mode only)
        if self.is_ai_enabled:
            self.ai_enhance_btn = ctk.CTkButton(
                input_panel,
                text="🤖 Améliorer avec l'IA",
                height=35,
                fg_color="#4ECDC4",
                hover_color="#45B7B8",
                command=self._ai_enhance_breakdown
            )
            self.ai_enhance_btn.pack(fill="x", padx=15, pady=(0, 15))
    
    def _create_breakdown_panel(self, parent):
        """Create subtasks breakdown panel."""
        breakdown_panel = ctk.CTkFrame(parent)
        breakdown_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        breakdown_panel.grid_columnconfigure(0, weight=1)
        breakdown_panel.grid_rowconfigure(1, weight=1)
        
        # Panel header
        header_frame = ctk.CTkFrame(breakdown_panel, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔧 Décomposition en Sous-tâches",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        # Subtask count
        self.subtask_count_label = ctk.CTkLabel(
            header_frame,
            text="0 sous-tâches",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtask_count_label.grid(row=0, column=1, sticky="e", padx=15, pady=15)
        
        # Subtasks list
        self.subtasks_frame = ctk.CTkScrollableFrame(breakdown_panel)
        self.subtasks_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Empty state
        self.empty_state_frame = ctk.CTkFrame(self.subtasks_frame, fg_color="transparent")
        self.empty_state_frame.pack(expand=True, fill="both")
        
        empty_icon = ctk.CTkLabel(
            self.empty_state_frame,
            text="📝",
            font=ctk.CTkFont(size=48)
        )
        empty_icon.pack(pady=(50, 10))
        
        empty_text = ctk.CTkLabel(
            self.empty_state_frame,
            text="Aucune décomposition encore\n\nSaisissez une tâche et cliquez sur 'Décomposer'",
            font=ctk.CTkFont(size=14),
            text_color="gray",
            justify="center"
        )
        empty_text.pack(pady=10)
    
    def _create_actions_panel(self, parent):
        """Create actions panel."""
        actions_panel = ctk.CTkFrame(parent, height=80)
        actions_panel.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(5, 0))
        actions_panel.grid_columnconfigure(1, weight=1)
        
        # Left actions
        left_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        add_subtask_btn = ctk.CTkButton(
            left_actions,
            text="➕ Ajouter Sous-tâche",
            height=35,
            command=self._add_subtask_manual
        )
        add_subtask_btn.pack(side="left", padx=(0, 5))
        
        clear_btn = ctk.CTkButton(
            left_actions,
            text="🗑️ Effacer Tout",
            height=35,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_breakdown
        )
        clear_btn.pack(side="left", padx=5)
        
        # Right actions
        right_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        right_actions.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        save_template_btn = ctk.CTkButton(
            right_actions,
            text="💾 Sauver Template",
            height=35,
            command=self._save_as_template
        )
        save_template_btn.pack(side="left", padx=5)
        
        create_tasks_btn = ctk.CTkButton(
            right_actions,
            text="✅ Créer les Tâches",
            height=35,
            fg_color="#27AE60",
            hover_color="#229954",
            command=self._create_tasks_from_breakdown
        )
        create_tasks_btn.pack(side="left", padx=(5, 0))
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load predefined templates."""
        return {
            "Projet Simple": [
                "Définir les objectifs et livrables",
                "Planifier les étapes principales",
                "Identifier les ressources nécessaires",
                "Exécuter le projet",
                "Réviser et finaliser"
            ],
            "Événement": [
                "Définir le concept et les objectifs",
                "Établir le budget",
                "Choisir la date et le lieu",
                "Planifier la logistique",
                "Promouvoir l'événement",
                "Gérer l'événement le jour J",
                "Faire le bilan post-événement"
            ],
            "Apprentissage": [
                "Définir les objectifs d'apprentissage",
                "Rechercher les ressources",
                "Créer un planning d'étude",
                "Étudier et pratiquer",
                "Évaluer les connaissances acquises",
                "Appliquer les connaissances"
            ],
            "Recherche": [
                "Définir la question de recherche",
                "Identifier les sources",
                "Collecter les informations",
                "Analyser les données",
                "Synthétiser les résultats",
                "Rédiger le rapport"
            ]
        }
    
    def _on_task_input_change(self, event=None):
        """Handle task input changes."""
        self.mark_unsaved_changes()
    
    def _apply_template(self, template_name: str):
        """Apply a predefined template."""
        if template_name in self.templates:
            # Clear existing subtasks
            self._clear_breakdown()
            
            # Add template subtasks
            for subtask_title in self.templates[template_name]:
                self._add_subtask(subtask_title)
            
            self.set_status(f"Template '{template_name}' appliqué")
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('template_applied')
    
    def _decompose_task(self):
        """Decompose the task into subtasks."""
        task_title = self.task_title_entry.get().strip()
        task_desc = self.task_desc_text.get("1.0", "end-1c").strip()
        
        if not task_title:
            messagebox.showwarning("Titre Requis", "Veuillez saisir un titre pour la tâche.")
            return
        
        # Create current task
        self.current_task = {
            'id': str(uuid.uuid4()),
            'title': task_title,
            'description': task_desc,
            'priority': self.priority_var.get(),
            'duration': self.duration_var.get(),
            'category': self.category_var.get(),
            'created_at': datetime.now().isoformat()
        }
        
        if self.magic_energy_level == 'magic':
            self._magic_decompose()
        else:
            self._genie_decompose()
    
    def _magic_decompose(self):
        """Simple decomposition based on task type and duration."""
        task_title = self.current_task['title'].lower()
        duration = self.current_task['duration']
        category = self.current_task['category']
        
        # Clear existing subtasks
        self._clear_breakdown()
        
        # Generate basic subtasks based on keywords and patterns
        subtasks = []
        
        # Always start with planning
        subtasks.append("Planifier et organiser la tâche")
        
        # Add category-specific steps
        if category == "Projet":
            subtasks.extend([
                "Définir les objectifs et livrables",
                "Identifier les ressources nécessaires",
                "Créer un planning détaillé"
            ])
        elif category == "Apprentissage":
            subtasks.extend([
                "Rechercher les ressources d'apprentissage",
                "Créer un plan d'étude",
                "Pratiquer et réviser"
            ])
        elif category == "Créatif":
            subtasks.extend([
                "Brainstormer et générer des idées",
                "Créer un concept initial",
                "Développer et raffiner"
            ])
        else:
            # Generic steps
            subtasks.extend([
                "Rechercher et collecter les informations",
                "Exécuter la tâche principale"
            ])
        
        # Add duration-based steps
        if "semaine" in duration or "jours" in duration:
            subtasks.append("Diviser en étapes quotidiennes")
            subtasks.append("Faire des points d'avancement réguliers")
        
        # Always end with review
        subtasks.append("Réviser et finaliser")
        
        # Add subtasks to UI
        for subtask_title in subtasks:
            self._add_subtask(subtask_title)
        
        self.set_status(f"Tâche décomposée en {len(subtasks)} sous-tâches")
        
        # Play audio feedback
        if self.audio_service:
            self.audio_service.play_sound('task_decomposed')
    
    def _genie_decompose(self):
        """AI-powered decomposition."""
        if not self.is_ai_enabled:
            self._magic_decompose()
            return
        
        def ai_task():
            prompt = f"""
Décompose cette tâche en sous-tâches détaillées et actionables:

Titre: {self.current_task['title']}
Description: {self.current_task['description']}
Priorité: {self.current_task['priority']}
Durée estimée: {self.current_task['duration']}
Catégorie: {self.current_task['category']}

Fournis une liste de 5-10 sous-tâches spécifiques et actionables.
Chaque sous-tâche doit être claire et réalisable.

Format de réponse:
1. [Titre de la sous-tâche]
2. [Titre de la sous-tâche]
...
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='task_breakdown',
                max_tokens=500
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _handle_ai_result(self, result):
        """Handle AI decomposition result."""
        if not result:
            messagebox.showerror("Erreur IA", "Aucune réponse de l'IA")
            return
        
        # Parse AI response
        lines = result.strip().split('\n')
        subtasks = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and clean up
                clean_line = line
                if '. ' in line:
                    clean_line = line.split('. ', 1)[1]
                elif '- ' in line:
                    clean_line = line.split('- ', 1)[1]
                elif '• ' in line:
                    clean_line = line.split('• ', 1)[1]
                
                if clean_line:
                    subtasks.append(clean_line)
        
        if subtasks:
            # Clear existing and add AI-generated subtasks
            self._clear_breakdown()
            for subtask_title in subtasks:
                self._add_subtask(subtask_title)
            
            self.set_status(f"IA: Tâche décomposée en {len(subtasks)} sous-tâches")
        else:
            messagebox.showwarning("Erreur de Parsing", "Impossible de parser la réponse de l'IA")
    
    def _ai_enhance_breakdown(self):
        """Enhance existing breakdown with AI suggestions."""
        if not self.subtasks:
            messagebox.showinfo("Aucune Décomposition", "Veuillez d'abord décomposer la tâche.")
            return
        
        def ai_task():
            current_subtasks = [subtask['title'] for subtask in self.subtasks]
            
            prompt = f"""
Améliore cette décomposition de tâche en ajoutant des détails et suggestions:

Tâche principale: {self.current_task['title']}
Sous-tâches actuelles:
{chr(10).join([f"- {subtask}" for subtask in current_subtasks])}

Suggestions d'amélioration:
1. Ajoute des détails manquants
2. Identifie les étapes oubliées
3. Propose des optimisations
4. Suggère des outils ou ressources

Format de réponse:
AMÉLIORATIONS:
- [Suggestion 1]
- [Suggestion 2]
...

NOUVELLES SOUS-TÂCHES:
- [Nouvelle sous-tâche 1]
- [Nouvelle sous-tâche 2]
...
"""
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='task_enhancement',
                max_tokens=600
            )
            
            return response.get('content', '')
        
        self.run_ai_task(ai_task)
    
    def _add_subtask(self, title: str, description: str = "", estimated_duration: int = 30):
        """Add a subtask to the breakdown."""
        subtask = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'estimated_duration': estimated_duration,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.subtasks.append(subtask)
        self._refresh_subtasks_display()
        self.mark_unsaved_changes()
    
    def _add_subtask_manual(self):
        """Add subtask manually via dialog."""
        dialog = SubtaskDialog(self, "Nouvelle Sous-tâche")
        result = dialog.show()
        
        if result and dialog.subtask_data:
            self._add_subtask(
                dialog.subtask_data['title'],
                dialog.subtask_data['description'],
                dialog.subtask_data['duration']
            )
    
    def _refresh_subtasks_display(self):
        """Refresh the subtasks display."""
        # Clear existing widgets
        for widget in self.subtasks_frame.winfo_children():
            widget.destroy()
        
        if not self.subtasks:
            # Show empty state
            self.empty_state_frame = ctk.CTkFrame(self.subtasks_frame, fg_color="transparent")
            self.empty_state_frame.pack(expand=True, fill="both")
            
            empty_icon = ctk.CTkLabel(
                self.empty_state_frame,
                text="📝",
                font=ctk.CTkFont(size=48)
            )
            empty_icon.pack(pady=(50, 10))
            
            empty_text = ctk.CTkLabel(
                self.empty_state_frame,
                text="Aucune sous-tâche\n\nCliquez sur 'Décomposer' ou 'Ajouter'",
                font=ctk.CTkFont(size=14),
                text_color="gray",
                justify="center"
            )
            empty_text.pack(pady=10)
        else:
            # Show subtasks
            for i, subtask in enumerate(self.subtasks):
                self._create_subtask_widget(subtask, i)
        
        # Update count
        self.subtask_count_label.configure(text=f"{len(self.subtasks)} sous-tâches")
    
    def _create_subtask_widget(self, subtask: Dict, index: int):
        """Create widget for a subtask."""
        subtask_frame = ctk.CTkFrame(self.subtasks_frame)
        subtask_frame.pack(fill="x", padx=5, pady=3)
        
        # Main content
        content_frame = ctk.CTkFrame(subtask_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=8)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Index number
        index_label = ctk.CTkLabel(
            content_frame,
            text=f"{index + 1}.",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=30
        )
        index_label.grid(row=0, column=0, sticky="nw", padx=(0, 10))
        
        # Title and description
        text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew")
        
        title_label = ctk.CTkLabel(
            text_frame,
            text=subtask['title'],
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            justify="left"
        )
        title_label.pack(fill="x", anchor="w")
        
        if subtask['description']:
            desc_label = ctk.CTkLabel(
                text_frame,
                text=subtask['description'],
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                justify="left"
            )
            desc_label.pack(fill="x", anchor="w", pady=(2, 0))
        
        # Duration
        duration_label = ctk.CTkLabel(
            text_frame,
            text=f"⏱️ {subtask['estimated_duration']} min",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        duration_label.pack(anchor="w", pady=(2, 0))
        
        # Actions
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="ne", padx=(10, 0))
        
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=30,
            height=25,
            command=lambda: self._edit_subtask(subtask['id'])
        )
        edit_btn.pack(side="top", pady=1)
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=30,
            height=25,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda: self._delete_subtask(subtask['id'])
        )
        delete_btn.pack(side="top", pady=1)
    
    def _edit_subtask(self, subtask_id: str):
        """Edit a subtask."""
        subtask = next((s for s in self.subtasks if s['id'] == subtask_id), None)
        if not subtask:
            return
        
        dialog = SubtaskDialog(self, "Modifier Sous-tâche", subtask)
        result = dialog.show()
        
        if result and dialog.subtask_data:
            # Update subtask
            subtask.update(dialog.subtask_data)
            self._refresh_subtasks_display()
            self.mark_unsaved_changes()
    
    def _delete_subtask(self, subtask_id: str):
        """Delete a subtask."""
        if messagebox.askyesno("Confirmer", "Supprimer cette sous-tâche ?"):
            self.subtasks = [s for s in self.subtasks if s['id'] != subtask_id]
            self._refresh_subtasks_display()
            self.mark_unsaved_changes()
    
    def _clear_breakdown(self):
        """Clear all subtasks."""
        if self.subtasks and not messagebox.askyesno("Confirmer", "Effacer toutes les sous-tâches ?"):
            return
        
        self.subtasks.clear()
        self._refresh_subtasks_display()
        self.mark_unsaved_changes()
    
    def _save_as_template(self):
        """Save current breakdown as template."""
        if not self.subtasks:
            messagebox.showinfo("Aucune Décomposition", "Aucune sous-tâche à sauvegarder.")
            return
        
        # TODO: Implement template saving
        messagebox.showinfo("Info", "Sauvegarde de template en développement")
    
    def _create_tasks_from_breakdown(self):
        """Create actual tasks from the breakdown."""
        if not self.subtasks:
            messagebox.showinfo("Aucune Décomposition", "Aucune sous-tâche à créer.")
            return
        
        if not self.database_manager:
            messagebox.showerror("Erreur", "Base de données non disponible.")
            return
        
        try:
            # Create main task
            main_task_id = self.database_manager.create_task(
                title=self.current_task['title'],
                description=self.current_task['description'],
                priority=self._priority_to_number(self.current_task['priority']),
                category=self.current_task['category']
            )
            
            # Create subtasks
            created_count = 0
            for subtask in self.subtasks:
                self.database_manager.create_task(
                    title=subtask['title'],
                    description=subtask['description'],
                    priority=self._priority_to_number(self.current_task['priority']),
                    category=self.current_task['category'],
                    estimated_duration=subtask['estimated_duration'],
                    parent_task_id=main_task_id
                )
                created_count += 1
            
            messagebox.showinfo(
                "Succès", 
                f"Tâche principale et {created_count} sous-tâches créées avec succès !"
            )
            
            # Clear the breakdown
            self.subtasks.clear()
            self._refresh_subtasks_display()
            
            # Play audio feedback
            if self.audio_service:
                self.audio_service.play_sound('tasks_created')
            
        except Exception as e:
            self.logger.error(f"Failed to create tasks: {e}")
            messagebox.showerror("Erreur", f"Impossible de créer les tâches: {e}")
    
    def _priority_to_number(self, priority_text: str) -> int:
        """Convert priority text to number."""
        priority_map = {
            "Faible": 1,
            "Moyenne": 2,
            "Élevée": 3,
            "Urgente": 4
        }
        return priority_map.get(priority_text, 2)
    
    def _save_data(self):
        """Save current breakdown data."""
        if not self.current_task:
            return
        
        try:
            # Save to database or file
            data = {
                'task': self.current_task,
                'subtasks': self.subtasks,
                'saved_at': datetime.now().isoformat()
            }
            
            # TODO: Implement actual saving
            super()._save_data()
            
        except Exception as e:
            self.logger.error(f"Failed to save breakdown: {e}")
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def _export_data(self):
        """Export breakdown data."""
        if not self.current_task or not self.subtasks:
            messagebox.showinfo("Aucune Donnée", "Aucune décomposition à exporter.")
            return
        
        # TODO: Implement export functionality
        messagebox.showinfo("Info", "Export en développement")


class SubtaskDialog(ctk.CTkToplevel):
    """Dialog for creating/editing subtasks."""
    
    def __init__(self, parent, title: str, subtask_data: Dict = None):
        """Initialize subtask dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.subtask_data = None
        self.result = False
        
        # Configure dialog
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Center on parent
        self._center_on_parent()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup dialog
        self._setup_dialog(subtask_data)
        
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
    
    def _setup_dialog(self, subtask_data: Dict = None):
        """Setup dialog content."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Titre de la sous-tâche:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))
        
        self.title_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Ex: Rechercher les fournisseurs",
            height=35
        )
        self.title_entry.pack(fill="x", pady=(0, 15))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Description (optionnelle):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        self.desc_text = ctk.CTkTextbox(
            main_frame,
            height=80,
            placeholder_text="Détails supplémentaires..."
        )
        self.desc_text.pack(fill="x", pady=(0, 15))
        
        # Duration
        duration_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=(0, 20))
        
        duration_label = ctk.CTkLabel(
            duration_frame,
            text="Durée estimée (minutes):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        duration_label.pack(side="left")
        
        self.duration_var = ctk.StringVar(value="30")
        duration_menu = ctk.CTkOptionMenu(
            duration_frame,
            variable=self.duration_var,
            values=["15", "30", "45", "60", "90", "120", "180"],
            width=100
        )
        duration_menu.pack(side="right")
        
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
        if subtask_data:
            self.title_entry.insert(0, subtask_data.get('title', ''))
            self.desc_text.insert("1.0", subtask_data.get('description', ''))
            self.duration_var.set(str(subtask_data.get('estimated_duration', 30)))
        
        # Focus on title
        self.title_entry.focus()
    
    def _on_ok(self):
        """Handle OK button."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Titre Requis", "Veuillez saisir un titre.")
            return
        
        self.subtask_data = {
            'title': title,
            'description': self.desc_text.get("1.0", "end-1c").strip(),
            'duration': int(self.duration_var.get())
        }
        
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button."""
        self.result = False
        self.destroy()
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result