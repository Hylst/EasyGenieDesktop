#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Genie Desktop - Formalizer Tool

Tool for transforming informal text into formal, professional content.
Supports both Magic (simple) and Genie (AI-powered) modes.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
import threading
import re

try:
    from ..components.base_components import BaseToolWindow
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../..')
    from ui.components.base_components import BaseToolWindow


class FormalizerTool(BaseToolWindow):
    """Formalizer tool for transforming informal text to formal."""
    
    def __init__(self, parent, magic_energy_level: str = 'magic', 
                 settings_manager=None, ai_service=None, audio_service=None, 
                 database_manager=None, **kwargs):
        """Initialize Formalizer tool."""
        super().__init__(
            parent, 
            "Formalisateur", 
            magic_energy_level,
            settings_manager,
            ai_service,
            audio_service,
            database_manager,
            **kwargs
        )
        
        # Formalization data
        self.current_session = {
            'input_text': '',
            'output_text': '',
            'formality_level': 'professional',
            'target_audience': 'general',
            'document_type': 'email',
            'transformations': [],
            'suggestions': []
        }
        
        # Formality rules for Magic mode
        self.formality_rules = {
            'contractions': {
                "can't": "cannot",
                "won't": "will not",
                "don't": "do not",
                "doesn't": "does not",
                "didn't": "did not",
                "isn't": "is not",
                "aren't": "are not",
                "wasn't": "was not",
                "weren't": "were not",
                "haven't": "have not",
                "hasn't": "has not",
                "hadn't": "had not",
                "shouldn't": "should not",
                "wouldn't": "would not",
                "couldn't": "could not",
                "mustn't": "must not",
                "I'm": "I am",
                "you're": "you are",
                "he's": "he is",
                "she's": "she is",
                "it's": "it is",
                "we're": "we are",
                "they're": "they are",
                "I've": "I have",
                "you've": "you have",
                "we've": "we have",
                "they've": "they have",
                "I'll": "I will",
                "you'll": "you will",
                "he'll": "he will",
                "she'll": "she will",
                "we'll": "we will",
                "they'll": "they will"
            },
            'informal_phrases': {
                'hey': 'hello',
                'hi there': 'hello',
                'what\'s up': 'how are you',
                'thanks': 'thank you',
                'thx': 'thank you',
                'ok': 'acceptable',
                'okay': 'acceptable',
                'yeah': 'yes',
                'yep': 'yes',
                'nope': 'no',
                'gonna': 'going to',
                'wanna': 'want to',
                'gotta': 'have to',
                'kinda': 'somewhat',
                'sorta': 'somewhat',
                'lots of': 'many',
                'a lot of': 'many',
                'tons of': 'numerous',
                'super': 'very',
                'really': 'very',
                'pretty': 'quite',
                'stuff': 'items',
                'things': 'matters',
                'guys': 'colleagues',
                'folks': 'individuals'
            },
            'professional_replacements': {
                'get': 'obtain',
                'give': 'provide',
                'show': 'demonstrate',
                'tell': 'inform',
                'ask': 'request',
                'help': 'assist',
                'fix': 'resolve',
                'check': 'verify',
                'look at': 'examine',
                'think about': 'consider',
                'talk about': 'discuss',
                'work on': 'address',
                'deal with': 'handle',
                'come up with': 'develop',
                'figure out': 'determine',
                'find out': 'ascertain'
            }
        }
        
        # Document type templates
        self.document_templates = {
            'email': {
                'greeting': 'Dear [Name],',
                'closing': 'Best regards,\n[Your Name]',
                'tone': 'professional'
            },
            'letter': {
                'greeting': 'Dear Sir/Madam,',
                'closing': 'Yours sincerely,\n[Your Name]',
                'tone': 'formal'
            },
            'report': {
                'greeting': '',
                'closing': '',
                'tone': 'academic'
            },
            'proposal': {
                'greeting': 'Dear [Title] [Name],',
                'closing': 'Thank you for your consideration.\n\nSincerely,\n[Your Name]',
                'tone': 'persuasive'
            },
            'memo': {
                'greeting': 'TO: [Recipients]\nFROM: [Your Name]\nDATE: [Date]\nSUBJECT: [Subject]',
                'closing': '',
                'tone': 'direct'
            }
        }
        
        self.logger.info("Formalizer tool initialized")
    
    def _setup_tool_content(self):
        """Setup Formalizer specific content."""
        # Configure content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # Top panel - Settings and controls
        self._create_settings_panel()
        
        # Main content area - Input/Output
        self._create_content_area()
        
        # Bottom panel - Actions and suggestions
        self._create_actions_panel()
    
    def _create_settings_panel(self):
        """Create settings panel."""
        settings_panel = ctk.CTkFrame(self.content_frame, height=120)
        settings_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        settings_panel.grid_columnconfigure(1, weight=1)
        
        # Left side - Document settings
        doc_settings_frame = ctk.CTkFrame(settings_panel)
        doc_settings_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            doc_settings_frame,
            text="📄 Type de Document",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        # Document type
        doc_frame = ctk.CTkFrame(doc_settings_frame, fg_color="transparent")
        doc_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(
            doc_frame,
            text="Type:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.doc_type_var = ctk.StringVar(value="email")
        doc_type_menu = ctk.CTkOptionMenu(
            doc_frame,
            variable=self.doc_type_var,
            values=["email", "letter", "report", "proposal", "memo"],
            width=120,
            command=self._on_doc_type_change
        )
        doc_type_menu.pack(side="right")
        
        # Target audience
        audience_frame = ctk.CTkFrame(doc_settings_frame, fg_color="transparent")
        audience_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            audience_frame,
            text="Public:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.audience_var = ctk.StringVar(value="general")
        audience_menu = ctk.CTkOptionMenu(
            audience_frame,
            variable=self.audience_var,
            values=["general", "academic", "business", "technical", "legal"],
            width=120,
            command=self._on_audience_change
        )
        audience_menu.pack(side="right")
        
        # Center - Formality settings
        formality_frame = ctk.CTkFrame(settings_panel)
        formality_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        
        ctk.CTkLabel(
            formality_frame,
            text="🎯 Niveau de Formalité",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5))
        
        # Formality level
        level_frame = ctk.CTkFrame(formality_frame, fg_color="transparent")
        level_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.formality_var = ctk.StringVar(value="professional")
        formality_levels = ["casual", "professional", "formal", "academic"]
        
        for level in formality_levels:
            radio = ctk.CTkRadioButton(
                level_frame,
                text=level.capitalize(),
                variable=self.formality_var,
                value=level,
                command=self._on_formality_change
            )
            radio.pack(side="left", padx=5)
        
        # Formality indicator
        self.formality_indicator = ctk.CTkProgressBar(
            formality_frame,
            width=200,
            height=10
        )
        self.formality_indicator.pack(pady=(5, 10))
        self._update_formality_indicator()
        
        # Right side - AI settings (Genie mode only)
        if self.is_ai_enabled:
            ai_settings_frame = ctk.CTkFrame(settings_panel)
            ai_settings_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
            
            ctk.CTkLabel(
                ai_settings_frame,
                text="🤖 IA Assistant",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=(10, 5))
            
            # AI options
            ai_options_frame = ctk.CTkFrame(ai_settings_frame, fg_color="transparent")
            ai_options_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            self.preserve_meaning_var = ctk.BooleanVar(value=True)
            preserve_check = ctk.CTkCheckBox(
                ai_options_frame,
                text="Préserver le sens",
                variable=self.preserve_meaning_var,
                font=ctk.CTkFont(size=10)
            )
            preserve_check.pack(anchor="w", pady=1)
            
            self.enhance_clarity_var = ctk.BooleanVar(value=True)
            clarity_check = ctk.CTkCheckBox(
                ai_options_frame,
                text="Améliorer la clarté",
                variable=self.enhance_clarity_var,
                font=ctk.CTkFont(size=10)
            )
            clarity_check.pack(anchor="w", pady=1)
            
            self.add_structure_var = ctk.BooleanVar(value=False)
            structure_check = ctk.CTkCheckBox(
                ai_options_frame,
                text="Ajouter structure",
                variable=self.add_structure_var,
                font=ctk.CTkFont(size=10)
            )
            structure_check.pack(anchor="w", pady=1)
    
    def _create_content_area(self):
        """Create main content area."""
        content_area = ctk.CTkFrame(self.content_frame)
        content_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content_area.grid_columnconfigure(0, weight=1)
        content_area.grid_columnconfigure(2, weight=1)
        content_area.grid_rowconfigure(0, weight=1)
        
        # Input area
        input_frame = ctk.CTkFrame(content_area)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(1, weight=1)
        
        # Input header
        input_header = ctk.CTkFrame(input_frame, height=40, fg_color="transparent")
        input_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        input_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            input_header,
            text="📝 Texte Informel",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Input word count
        self.input_word_count_label = ctk.CTkLabel(
            input_header,
            text="0 mots",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.input_word_count_label.grid(row=0, column=1, sticky="e")
        
        # Input actions
        input_actions = ctk.CTkFrame(input_header, fg_color="transparent")
        input_actions.grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        paste_btn = ctk.CTkButton(
            input_actions,
            text="📋",
            width=30,
            height=25,
            command=self._paste_text
        )
        paste_btn.pack(side="left", padx=(0, 2))
        
        clear_input_btn = ctk.CTkButton(
            input_actions,
            text="🗑️",
            width=30,
            height=25,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_input
        )
        clear_input_btn.pack(side="left")
        
        # Input text widget
        self.input_text = ctk.CTkTextbox(
            input_frame,
            font=ctk.CTkFont(size=12),
            wrap="word",
            placeholder_text="Collez ou tapez votre texte informel ici..."
        )
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.input_text.bind("<KeyRelease>", self._on_input_change)
        
        # Center - Transform button
        transform_frame = ctk.CTkFrame(content_area, width=100)
        transform_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=10)
        
        # Transform button
        self.transform_btn = ctk.CTkButton(
            transform_frame,
            text="➡️\nFormaliser",
            height=80,
            width=80,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self._transform_text
        )
        self.transform_btn.pack(expand=True, pady=20)
        
        # Quick transform options
        quick_frame = ctk.CTkFrame(transform_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=5, pady=(0, 20))
        
        quick_professional_btn = ctk.CTkButton(
            quick_frame,
            text="Pro",
            width=35,
            height=25,
            font=ctk.CTkFont(size=9),
            command=lambda: self._quick_transform('professional')
        )
        quick_professional_btn.pack(pady=2)
        
        quick_formal_btn = ctk.CTkButton(
            quick_frame,
            text="Formel",
            width=35,
            height=25,
            font=ctk.CTkFont(size=9),
            command=lambda: self._quick_transform('formal')
        )
        quick_formal_btn.pack(pady=2)
        
        # Output area
        output_frame = ctk.CTkFrame(content_area)
        output_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        # Output header
        output_header = ctk.CTkFrame(output_frame, height=40, fg_color="transparent")
        output_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        output_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            output_header,
            text="✨ Texte Formalisé",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Output word count
        self.output_word_count_label = ctk.CTkLabel(
            output_header,
            text="0 mots",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.output_word_count_label.grid(row=0, column=1, sticky="e")
        
        # Output actions
        output_actions = ctk.CTkFrame(output_header, fg_color="transparent")
        output_actions.grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        copy_btn = ctk.CTkButton(
            output_actions,
            text="📋",
            width=30,
            height=25,
            command=self._copy_output
        )
        copy_btn.pack(side="left", padx=(0, 2))
        
        clear_output_btn = ctk.CTkButton(
            output_actions,
            text="🗑️",
            width=30,
            height=25,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._clear_output
        )
        clear_output_btn.pack(side="left")
        
        # Output text widget
        self.output_text = ctk.CTkTextbox(
            output_frame,
            font=ctk.CTkFont(size=12),
            wrap="word",
            state="normal"
        )
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.output_text.bind("<KeyRelease>", self._on_output_change)
    
    def _create_actions_panel(self):
        """Create actions panel."""
        actions_panel = ctk.CTkFrame(self.content_frame, height=100)
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
        
        history_btn = ctk.CTkButton(
            left_actions,
            text="📚 Historique",
            height=35,
            command=self._show_history
        )
        history_btn.pack(side="left", padx=5)
        
        compare_btn = ctk.CTkButton(
            left_actions,
            text="🔍 Comparer",
            height=35,
            command=self._compare_texts
        )
        compare_btn.pack(side="left", padx=5)
        
        # Center - Suggestions (if available)
        suggestions_frame = ctk.CTkFrame(actions_panel, fg_color="transparent")
        suggestions_frame.grid(row=0, column=1, sticky="", padx=15, pady=15)
        
        self.suggestions_label = ctk.CTkLabel(
            suggestions_frame,
            text="💡 Suggestions disponibles après transformation",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.suggestions_label.pack()
        
        # Right actions
        right_actions = ctk.CTkFrame(actions_panel, fg_color="transparent")
        right_actions.grid(row=0, column=2, sticky="e", padx=15, pady=15)
        
        save_btn = ctk.CTkButton(
            right_actions,
            text="💾 Sauver",
            height=35,
            command=self._save_session
        )
        save_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(
            right_actions,
            text="📤 Exporter",
            height=35,
            command=self._export_result
        )
        export_btn.pack(side="left", padx=(5, 0))
    
    def _update_formality_indicator(self):
        """Update formality level indicator."""
        levels = {"casual": 0.25, "professional": 0.5, "formal": 0.75, "academic": 1.0}
        level = self.formality_var.get()
        progress = levels.get(level, 0.5)
        self.formality_indicator.set(progress)
    
    def _on_doc_type_change(self, value):
        """Handle document type change."""
        self.current_session['document_type'] = value
        # Could update suggestions or templates based on document type
    
    def _on_audience_change(self, value):
        """Handle target audience change."""
        self.current_session['target_audience'] = value
        # Could adjust formalization rules based on audience
    
    def _on_formality_change(self):
        """Handle formality level change."""
        self.current_session['formality_level'] = self.formality_var.get()
        self._update_formality_indicator()
    
    def _on_input_change(self, event=None):
        """Handle input text change."""
        content = self.input_text.get("1.0", "end-1c")
        self.current_session['input_text'] = content
        
        # Update word count
        words = content.split()
        word_count = len([word for word in words if word.strip()])
        self.input_word_count_label.configure(text=f"{word_count} mots")
        
        # Enable/disable transform button
        if content.strip():
            self.transform_btn.configure(state="normal")
        else:
            self.transform_btn.configure(state="disabled")
    
    def _on_output_change(self, event=None):
        """Handle output text change."""
        content = self.output_text.get("1.0", "end-1c")
        self.current_session['output_text'] = content
        
        # Update word count
        words = content.split()
        word_count = len([word for word in words if word.strip()])
        self.output_word_count_label.configure(text=f"{word_count} mots")
    
    def _paste_text(self):
        """Paste text from clipboard."""
        try:
            clipboard_content = self.clipboard_get()
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", clipboard_content)
            self._on_input_change()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de coller le texte: {e}")
    
    def _clear_input(self):
        """Clear input text."""
        if self.input_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("Confirmer", "Effacer le texte d'entrée ?"):
                self.input_text.delete("1.0", "end")
                self._on_input_change()
    
    def _clear_output(self):
        """Clear output text."""
        if self.output_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("Confirmer", "Effacer le texte de sortie ?"):
                self.output_text.delete("1.0", "end")
                self._on_output_change()
    
    def _copy_output(self):
        """Copy output text to clipboard."""
        try:
            content = self.output_text.get("1.0", "end-1c")
            if content.strip():
                self.clipboard_clear()
                self.clipboard_append(content)
                messagebox.showinfo("Copié", "Texte copié dans le presse-papiers.")
            else:
                messagebox.showwarning("Rien à Copier", "Aucun texte à copier.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier: {e}")
    
    def _quick_transform(self, level: str):
        """Quick transform with specific formality level."""
        self.formality_var.set(level)
        self._on_formality_change()
        self._transform_text()
    
    def _transform_text(self):
        """Transform input text to formal."""
        input_content = self.input_text.get("1.0", "end-1c").strip()
        
        if not input_content:
            messagebox.showwarning("Aucun Texte", "Veuillez saisir du texte à formaliser.")
            return
        
        # Show loading state
        self.transform_btn.configure(text="⏳\nTraitement...", state="disabled")
        
        if self.is_ai_enabled:
            # Use AI for transformation
            self._ai_transform_text(input_content)
        else:
            # Use Magic mode transformation
            self._magic_transform_text(input_content)
    
    def _magic_transform_text(self, text: str):
        """Transform text using Magic mode rules."""
        try:
            transformed_text = text
            transformations = []
            
            # Apply contractions replacement
            for contraction, expansion in self.formality_rules['contractions'].items():
                if contraction in transformed_text:
                    transformed_text = transformed_text.replace(contraction, expansion)
                    transformations.append(f"'{contraction}' → '{expansion}'")
            
            # Apply informal phrases replacement
            for informal, formal in self.formality_rules['informal_phrases'].items():
                pattern = r'\b' + re.escape(informal) + r'\b'
                if re.search(pattern, transformed_text, re.IGNORECASE):
                    transformed_text = re.sub(pattern, formal, transformed_text, flags=re.IGNORECASE)
                    transformations.append(f"'{informal}' → '{formal}'")
            
            # Apply professional replacements based on formality level
            if self.formality_var.get() in ['professional', 'formal', 'academic']:
                for casual, professional in self.formality_rules['professional_replacements'].items():
                    pattern = r'\b' + re.escape(casual) + r'\b'
                    if re.search(pattern, transformed_text, re.IGNORECASE):
                        transformed_text = re.sub(pattern, professional, transformed_text, flags=re.IGNORECASE)
                        transformations.append(f"'{casual}' → '{professional}'")
            
            # Apply document template if needed
            doc_type = self.doc_type_var.get()
            if doc_type in self.document_templates:
                template = self.document_templates[doc_type]
                if template['greeting'] and not transformed_text.startswith(('Dear', 'Hello', 'Hi')):
                    transformed_text = template['greeting'] + '\n\n' + transformed_text
                if template['closing'] and not any(closing in transformed_text.lower() for closing in ['regards', 'sincerely', 'yours']):
                    transformed_text = transformed_text + '\n\n' + template['closing']
            
            # Capitalize sentences
            sentences = re.split(r'(?<=[.!?])\s+', transformed_text)
            capitalized_sentences = []
            for sentence in sentences:
                if sentence.strip():
                    sentence = sentence.strip()
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    capitalized_sentences.append(sentence)
            
            if capitalized_sentences:
                transformed_text = ' '.join(capitalized_sentences)
            
            # Update output
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", transformed_text)
            self._on_output_change()
            
            # Store transformations
            self.current_session['transformations'] = transformations
            
            # Update suggestions
            self._update_suggestions(transformations)
            
            # Reset button
            self.transform_btn.configure(text="➡️\nFormaliser", state="normal")
            
        except Exception as e:
            self.logger.error(f"Magic transformation failed: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la transformation: {e}")
            self.transform_btn.configure(text="➡️\nFormaliser", state="normal")
    
    def _ai_transform_text(self, text: str):
        """Transform text using AI."""
        def ai_task():
            formality_level = self.formality_var.get()
            doc_type = self.doc_type_var.get()
            audience = self.audience_var.get()
            
            # Build AI prompt
            prompt = f"""
Transforme ce texte informel en texte {formality_level} adapté pour un {doc_type} destiné à un public {audience}.

Texte original:
{text}

Instructions:
1. Niveau de formalité: {formality_level}
2. Type de document: {doc_type}
3. Public cible: {audience}
"""
            
            if self.preserve_meaning_var.get():
                prompt += "\n4. Préserver exactement le sens original"
            
            if self.enhance_clarity_var.get():
                prompt += "\n5. Améliorer la clarté et la lisibilité"
            
            if self.add_structure_var.get():
                prompt += "\n6. Ajouter une structure appropriée (paragraphes, transitions)"
            
            prompt += "\n\nRéponds uniquement avec le texte transformé, sans explication."
            
            response = self.ai_service.make_request(
                prompt=prompt,
                feature='text_formalization',
                max_tokens=800
            )
            
            return response.get('content', '')
        
        # Run AI task in background
        def run_ai_task():
            try:
                result = ai_task()
                if result:
                    # Update UI in main thread
                    self.after(0, lambda: self._handle_ai_result(result))
                else:
                    self.after(0, lambda: self._handle_ai_error("Aucun résultat de l'IA"))
            except Exception as e:
                self.logger.error(f"AI transformation failed: {e}")
                self.after(0, lambda: self._handle_ai_error(str(e)))
        
        threading.Thread(target=run_ai_task, daemon=True).start()
    
    def _handle_ai_result(self, result: str):
        """Handle AI transformation result."""
        # Update output
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self._on_output_change()
        
        # Reset button
        self.transform_btn.configure(text="➡️\nFormaliser", state="normal")
        
        # Update suggestions
        suggestions = ["Transformation IA terminée avec succès"]
        self._update_suggestions([], suggestions)
    
    def _handle_ai_error(self, error: str):
        """Handle AI transformation error."""
        messagebox.showerror("Erreur IA", f"Erreur lors de la transformation IA: {error}")
        self.transform_btn.configure(text="➡️\nFormaliser", state="normal")
    
    def _update_suggestions(self, transformations: List[str] = None, ai_suggestions: List[str] = None):
        """Update suggestions display."""
        if transformations:
            suggestion_text = f"💡 {len(transformations)} transformations appliquées"
        elif ai_suggestions:
            suggestion_text = f"🤖 {', '.join(ai_suggestions)}"
        else:
            suggestion_text = "💡 Suggestions disponibles après transformation"
        
        self.suggestions_label.configure(text=suggestion_text)
        
        # Store suggestions
        self.current_session['suggestions'] = transformations or ai_suggestions or []
    
    def _show_templates(self):
        """Show document templates."""
        templates = {
            "Email Professionnel": "Objet: [Sujet]\n\nBonjour [Nom],\n\nJ'espère que ce message vous trouve en bonne santé.\n\n[Contenu principal]\n\nJe vous remercie pour votre attention et reste à votre disposition pour toute question.\n\nCordialement,\n[Votre nom]",
            "Lettre Formelle": "[Vos coordonnées]\n\n[Date]\n\n[Coordonnées destinataire]\n\nObjet: [Objet]\n\nMonsieur/Madame,\n\n[Contenu de la lettre]\n\nJe vous prie d'agréer, Monsieur/Madame, l'expression de mes salutations distinguées.\n\n[Signature]",
            "Rapport": "RAPPORT\n\nTitre: [Titre du rapport]\nDate: [Date]\nAuteur: [Nom]\n\n1. RÉSUMÉ EXÉCUTIF\n[Résumé]\n\n2. INTRODUCTION\n[Introduction]\n\n3. MÉTHODOLOGIE\n[Méthodologie]\n\n4. RÉSULTATS\n[Résultats]\n\n5. CONCLUSIONS\n[Conclusions]\n\n6. RECOMMANDATIONS\n[Recommandations]",
            "Proposition": "PROPOSITION\n\n[Titre de la proposition]\n\nPrésentée à: [Client/Organisation]\nPrésentée par: [Votre nom/organisation]\nDate: [Date]\n\n1. CONTEXTE\n[Contexte du projet]\n\n2. OBJECTIFS\n[Objectifs à atteindre]\n\n3. APPROCHE\n[Méthodologie proposée]\n\n4. LIVRABLES\n[Ce qui sera fourni]\n\n5. CALENDRIER\n[Planning]\n\n6. BUDGET\n[Coûts estimés]\n\nNous sommes convaincus que cette proposition répond à vos besoins et nous réjouissons de collaborer avec vous.\n\nCordialement,\n[Signature]"
        }
        
        dialog = TemplateDialog(self, templates)
        result = dialog.show()
        
        if result and dialog.selected_template:
            # Insert template in input
            if messagebox.askyesno("Appliquer Modèle", "Remplacer le contenu actuel par le modèle sélectionné ?"):
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", dialog.selected_template)
                self._on_input_change()
    
    def _show_history(self):
        """Show transformation history."""
        # TODO: Implement history functionality
        messagebox.showinfo("Info", "Historique en développement")
    
    def _compare_texts(self):
        """Compare input and output texts."""
        input_text = self.input_text.get("1.0", "end-1c").strip()
        output_text = self.output_text.get("1.0", "end-1c").strip()
        
        if not input_text or not output_text:
            messagebox.showwarning("Textes Manquants", "Les deux textes doivent être présents pour la comparaison.")
            return
        
        # Show comparison dialog
        dialog = ComparisonDialog(self, input_text, output_text, self.current_session.get('transformations', []))
        dialog.show()
    
    def _save_session(self):
        """Save current session."""
        # TODO: Implement session saving
        messagebox.showinfo("Info", "Sauvegarde en développement")
    
    def _export_result(self):
        """Export transformation result."""
        output_text = self.output_text.get("1.0", "end-1c").strip()
        
        if not output_text:
            messagebox.showwarning("Rien à Exporter", "Aucun texte formalisé à exporter.")
            return
        
        # TODO: Implement export functionality
        messagebox.showinfo("Info", "Export en développement")


class TemplateDialog(ctk.CTkToplevel):
    """Dialog for selecting document templates."""
    
    def __init__(self, parent, templates: Dict[str, str]):
        """Initialize template dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.templates = templates
        self.selected_template = None
        self.result = False
        
        # Configure dialog
        self.title("Modèles de Documents")
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
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📋 Choisir un Modèle",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        # Content area
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Templates list
        list_frame = ctk.CTkFrame(content_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        self.templates_listbox = ctk.CTkScrollableFrame(list_frame)
        self.templates_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Template preview
        preview_frame = ctk.CTkFrame(content_frame)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            preview_frame,
            text="👁️ Aperçu",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        self.preview_text = ctk.CTkTextbox(
            preview_frame,
            font=ctk.CTkFont(size=10),
            wrap="word",
            state="disabled"
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Create template items
        self.template_vars = []
        template_names = list(self.templates.keys())
        
        for i, template_name in enumerate(template_names):
            var = ctk.StringVar()
            self.template_vars.append(var)
            
            template_frame = ctk.CTkFrame(self.templates_listbox)
            template_frame.pack(fill="x", pady=3)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                template_frame,
                text=template_name,
                variable=var,
                value=str(i),
                command=lambda idx=i: self._select_template(idx)
            )
            radio.pack(anchor="w", padx=10, pady=5)
            
            # Bind click to select
            template_frame.bind("<Button-1>", lambda e, idx=i: self._select_template(idx))
        
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
        """Select a template and show preview."""
        for i, var in enumerate(self.template_vars):
            if i == index:
                var.set(str(i))
            else:
                var.set("")
        
        # Show preview
        template_names = list(self.templates.keys())
        template_name = template_names[index]
        template_content = self.templates[template_name]
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", template_content)
        self.preview_text.configure(state="disabled")
    
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
        
        template_names = list(self.templates.keys())
        template_name = template_names[selected_index]
        self.selected_template = self.templates[template_name]
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


class ComparisonDialog(ctk.CTkToplevel):
    """Dialog for comparing input and output texts."""
    
    def __init__(self, parent, input_text: str, output_text: str, transformations: List[str]):
        """Initialize comparison dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.input_text = input_text
        self.output_text = output_text
        self.transformations = transformations
        
        # Configure dialog
        self.title("Comparaison des Textes")
        self.geometry("900x600")
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
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔍 Comparaison des Textes",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        
        # Input text
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 15))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            input_frame,
            text="📝 Texte Original",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        input_textbox = ctk.CTkTextbox(
            input_frame,
            font=ctk.CTkFont(size=11),
            wrap="word",
            state="normal"
        )
        input_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        input_textbox.insert("1.0", self.input_text)
        input_textbox.configure(state="disabled")
        
        # Output text
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(0, 15))
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            output_frame,
            text="✨ Texte Formalisé",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        output_textbox = ctk.CTkTextbox(
            output_frame,
            font=ctk.CTkFont(size=11),
            wrap="word",
            state="normal"
        )
        output_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        output_textbox.insert("1.0", self.output_text)
        output_textbox.configure(state="disabled")
        
        # Transformations
        if self.transformations:
            transformations_frame = ctk.CTkFrame(main_frame)
            transformations_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
            transformations_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                transformations_frame,
                text="🔄 Transformations Appliquées",
                font=ctk.CTkFont(size=12, weight="bold")
            ).grid(row=0, column=0, pady=(10, 5), sticky="ew")
            
            transformations_text = "\n".join([f"• {t}" for t in self.transformations[:10]])  # Show first 10
            if len(self.transformations) > 10:
                transformations_text += f"\n... et {len(self.transformations) - 10} autres"
            
            transformations_label = ctk.CTkLabel(
                transformations_frame,
                text=transformations_text,
                font=ctk.CTkFont(size=10),
                justify="left",
                anchor="w"
            )
            transformations_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Statistics
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        input_words = len(self.input_text.split())
        output_words = len(self.output_text.split())
        word_change = output_words - input_words
        word_change_text = f"+{word_change}" if word_change > 0 else str(word_change)
        
        stats_text = f"📊 Statistiques: {input_words} → {output_words} mots ({word_change_text})"
        
        ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=ctk.CTkFont(size=11)
        ).pack(pady=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Fermer",
            command=self._on_close
        )
        close_btn.grid(row=4, column=0, columnspan=2, pady=(0, 0))
    
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
    root.title("Test Formalizer Tool")
    root.geometry("1400x900")
    
    # Create tool instance
    tool = FormalizerTool(
        parent=root,
        magic_energy_level='genie'  # Test with AI features
    )
    tool.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()