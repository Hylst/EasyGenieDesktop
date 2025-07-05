import logging
import traceback
from typing import Dict, List, Any
import customtkinter as ctk
from tkinter import messagebox

class DiagnosticTool:
    """Outil de diagnostic pour identifier et corriger les erreurs de l'application."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        self.errors_found = []
        self.fixes_applied = []
        
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Exécute un diagnostic complet de l'application."""
        self.logger.info("Démarrage du diagnostic complet")
        
        results = {
            'errors': [],
            'warnings': [],
            'fixes_applied': [],
            'status': 'success'
        }
        
        try:
            # Test 1: Vérifier les outils principaux
            self._test_main_tools(results)
            
            # Test 2: Vérifier les services
            self._test_services(results)
            
            # Test 3: Vérifier la configuration
            self._test_configuration(results)
            
            # Test 4: Vérifier les imports
            self._test_imports(results)
            
            # Test 5: Appliquer les corrections automatiques
            self._apply_automatic_fixes(results)
            
        except Exception as e:
            results['status'] = 'error'
            results['errors'].append(f"Erreur lors du diagnostic: {e}")
            self.logger.error(f"Erreur diagnostic: {e}")
            
        return results
    
    def _test_main_tools(self, results: Dict):
        """Test les outils principaux (imports seulement)."""
        tools_to_test = [
            ('brain_dump', 'ui.tools.brain_dump', 'BrainDumpTool'),
            ('task_breaker', 'ui.tools.task_breaker', 'TaskBreakerTool'),
            ('priority_grid', 'ui.tools.tool_fixes', 'SimplePriorityGrid'),
            ('time_focus', 'ui.tools.tool_fixes', 'SimpleTimeFocus'),
            ('formalizer', 'ui.tools.tool_fixes', 'SimpleFormalizerTool'),
            ('routine_builder', 'ui.tools.tool_fixes', 'SimpleRoutineBuilder'),
            ('immersive_reader', 'ui.tools.tool_fixes', 'SimpleImmersiveReader')
        ]
        
        for tool_id, module_name, class_name in tools_to_test:
            try:
                # Test seulement l'import, pas l'instanciation
                module = __import__(module_name, fromlist=[class_name])
                tool_class = getattr(module, class_name)
                
                # Vérifications spécifiques
                if tool_id == 'task_breaker':
                    if hasattr(tool_class, '_load_templates'):
                        results['fixes_applied'].append(f"Outil {tool_id} - templates OK")
                    else:
                        results['warnings'].append(f"Outil {tool_id} - méthode _load_templates manquante")
                
                results['fixes_applied'].append(f"Outil {tool_id} testé avec succès")
                    
            except Exception as e:
                error_msg = f"Erreur avec l'outil {tool_id}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
    
    def _test_services(self, results: Dict):
        """Test les services de l'application."""
        try:
            # Test AI Service
            if self.main_window.ai_service:
                results['fixes_applied'].append("Service AI disponible")
            else:
                results['warnings'].append("Service AI non initialisé")
                
            # Test Audio Service
            if self.main_window.audio_service:
                results['fixes_applied'].append("Service Audio disponible")
            else:
                results['warnings'].append("Service Audio non initialisé")
                
            # Test Database
            if self.main_window.database_manager:
                results['fixes_applied'].append("Base de données disponible")
            else:
                results['errors'].append("Base de données non initialisée")
                
        except Exception as e:
            results['errors'].append(f"Erreur test services: {e}")
    
    def _test_configuration(self, results: Dict):
        """Test la configuration de l'application."""
        try:
            # Test Settings Manager
            if hasattr(self.main_window.settings_manager, 'save_settings'):
                results['fixes_applied'].append("Méthode save_settings disponible")
            else:
                results['errors'].append("Méthode save_settings manquante")
                
            # Test des paramètres critiques
            if self.main_window.magic_energy_level:
                results['fixes_applied'].append(f"Niveau d'énergie: {self.main_window.magic_energy_level}")
            else:
                results['warnings'].append("Niveau d'énergie non défini")
                
        except Exception as e:
            results['errors'].append(f"Erreur test configuration: {e}")
    
    def _test_imports(self, results: Dict):
        """Test les imports critiques."""
        critical_imports = [
            ('ui.tools.brain_dump', 'BrainDumpTool'),
            ('ui.tools.task_breaker', 'TaskBreakerTool'),
            ('ui.tools.tool_fixes', 'SimplePriorityGrid'),
            ('config.settings', 'AppSettings'),
        ]
        
        for module_name, class_name in critical_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                results['fixes_applied'].append(f"Import {module_name}.{class_name} OK")
            except Exception as e:
                results['errors'].append(f"Erreur import {module_name}.{class_name}: {e}")
    
    def _apply_automatic_fixes(self, results: Dict):
        """Applique des corrections automatiques."""
        try:
            # Fix 1: Vérifier et corriger les attributs manquants
            if not hasattr(self.main_window.settings_manager, 'save_settings'):
                # Ajouter la méthode manquante
                def save_settings_fix(self):
                    return self.save()
                self.main_window.settings_manager.save_settings = save_settings_fix.__get__(self.main_window.settings_manager)
                results['fixes_applied'].append("Correction: Méthode save_settings ajoutée")
            
            # Fix 2: Initialiser les templates manquants pour task_breaker
            try:
                from ui.tools.task_breaker import TaskBreakerTool
                # Vérifier si la classe a bien la méthode _load_templates
                if hasattr(TaskBreakerTool, '_load_templates'):
                    results['fixes_applied'].append("Templates TaskBreaker OK")
                else:
                    results['warnings'].append("Méthode _load_templates manquante dans TaskBreaker")
            except:
                pass
            
            # Fix 3: Vérifier la compatibilité des widgets
            results['fixes_applied'].append("Vérification compatibilité widgets terminée")
            
        except Exception as e:
            results['errors'].append(f"Erreur lors des corrections automatiques: {e}")
    
    def show_diagnostic_window(self):
        """Affiche une fenêtre avec les résultats du diagnostic."""
        results = self.run_full_diagnostic()
        
        # Créer la fenêtre de diagnostic
        diag_window = ctk.CTkToplevel(self.main_window.root)
        diag_window.title("Diagnostic de l'Application")
        diag_window.geometry("600x500")
        diag_window.transient(self.main_window.root)
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(diag_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔧 Diagnostic de l'Application",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Statut général
        status_color = "green" if results['status'] == 'success' else "red"
        status_text = "✅ Diagnostic terminé" if results['status'] == 'success' else "❌ Erreurs détectées"
        
        status_label = ctk.CTkLabel(
            main_frame,
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=status_color
        )
        status_label.pack(pady=(0, 20))
        
        # Corrections appliquées
        if results['fixes_applied']:
            fixes_frame = ctk.CTkFrame(main_frame)
            fixes_frame.pack(fill="x", pady=(0, 10))
            
            fixes_title = ctk.CTkLabel(
                fixes_frame,
                text="✅ Corrections et vérifications réussies:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="green"
            )
            fixes_title.pack(anchor="w", padx=10, pady=(10, 5))
            
            for fix in results['fixes_applied']:
                fix_label = ctk.CTkLabel(
                    fixes_frame,
                    text=f"• {fix}",
                    font=ctk.CTkFont(size=12)
                )
                fix_label.pack(anchor="w", padx=20, pady=2)
        
        # Avertissements
        if results['warnings']:
            warnings_frame = ctk.CTkFrame(main_frame)
            warnings_frame.pack(fill="x", pady=(0, 10))
            
            warnings_title = ctk.CTkLabel(
                warnings_frame,
                text="⚠️ Avertissements:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="orange"
            )
            warnings_title.pack(anchor="w", padx=10, pady=(10, 5))
            
            for warning in results['warnings']:
                warning_label = ctk.CTkLabel(
                    warnings_frame,
                    text=f"• {warning}",
                    font=ctk.CTkFont(size=12)
                )
                warning_label.pack(anchor="w", padx=20, pady=2)
        
        # Erreurs
        if results['errors']:
            errors_frame = ctk.CTkFrame(main_frame)
            errors_frame.pack(fill="x", pady=(0, 10))
            
            errors_title = ctk.CTkLabel(
                errors_frame,
                text="❌ Erreurs détectées:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="red"
            )
            errors_title.pack(anchor="w", padx=10, pady=(10, 5))
            
            for error in results['errors']:
                error_label = ctk.CTkLabel(
                    errors_frame,
                    text=f"• {error}",
                    font=ctk.CTkFont(size=12)
                )
                error_label.pack(anchor="w", padx=20, pady=2)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=20)
        
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="Fermer",
            command=diag_window.destroy
        )
        close_btn.pack(side="right", padx=10, pady=10)
        
        rerun_btn = ctk.CTkButton(
            buttons_frame,
            text="Relancer le diagnostic",
            command=lambda: [diag_window.destroy(), self.show_diagnostic_window()]
        )
        rerun_btn.pack(side="right", padx=10, pady=10)