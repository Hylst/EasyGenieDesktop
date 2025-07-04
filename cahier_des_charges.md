# Cahier des Charges - Application Desktop "Easy Genie" Python

## 1. Introduction et Principe Fondamental

**Nom de l'application :** Easy Genie Desktop

**Principe :** "Easy Genie" est une suite d'outils desktop conçue pour assister les individus, en particulier ceux neurodivergents (TDAH, dyslexie, etc.) et toute personne luttant contre la procrastination ou la surcharge mentale. L'application fournit des utilitaires simples, épurés et enrichis par une intelligence artificielle bienveillante pour aider à l'organisation des pensées, la gestion des tâches et le maintien de la concentration.

**Philosophie :**
- **Simplicité :** Interfaces minimalistes, réduisant la charge cognitive
- **Assistance IA :** Le "Génie" offre une aide contextuelle et adaptative
- **Autonomisation :** Les outils sont conçus pour structurer les pensées de l'utilisateur, pas pour penser à sa place
- **Esthétique Calme :** Un design apaisant avec des couleurs douces pour ne pas créer de stress visuel
- **Accessibilité :** Support natif pour les raccourcis clavier et les technologies d'assistance

---

## 2. Architecture Technique

### 2.1. Technologies Principales
- **Framework GUI :** Tkinter (interface native) avec CustomTkinter pour un design moderne
- **Langage :** Python 3.9+
- **Base de Données :** SQLite3 (fichier local)
- **Intelligence Artificielle :** 
  - Intégration API OpenAI/Anthropic/Gemini (configurable)
  - Modèles locaux via Ollama (optionnel)
- **Synthèse Vocale :** pyttsx3 (TTS natif multi-plateforme)
- **Reconnaissance Vocale :** speech_recognition + pyaudio
- **Audio :** pygame pour la génération de sons d'ambiance
- **Export :** reportlab (PDF), python-docx (Word)

### 2.2. Structure de l'Application
```
easy_genie/
├── main.py                 # Point d'entrée principal
├── config/
│   ├── settings.py        # Configuration globale
│   ├── themes.py          # Thèmes visuels
│   └── ai_config.py       # Configuration IA
├── core/
│   ├── database.py        # Gestionnaire SQLite
│   ├── ai_service.py      # Service IA unifié
│   ├── audio_service.py   # Synthèse vocale et reconnaissance
│   └── export_service.py  # Services d'export
├── tools/
│   ├── task_breaker/      # Décomposeur de tâches
│   ├── time_focus/        # TimeFocus
│   ├── priority_grid/     # Grille des priorités
│   ├── brain_dump/        # Décharge de pensées
│   ├── formalizer/        # Formaliseur
│   ├── routine_builder/   # Constructeur de routines
│   └── immersive_reader/  # Lecteur immersif
├── ui/
│   ├── main_window.py     # Fenêtre principale
│   ├── components/        # Composants UI réutilisables
│   └── dialogs/           # Boîtes de dialogue
└── assets/
    ├── icons/             # Icônes
    ├── sounds/            # Sons d'ambiance
    └── fonts/             # Polices (OpenDyslexic)
```

---

## 3. Fonctionnalités Transversales et Systémiques

### 3.1. Niveaux d'Intensité ("Énergie Magique")
- **Implémentation :** Slider horizontal avec 5 niveaux
- **Persistance :** Sauvegarde du niveau par outil et par utilisateur
- **Comportement :**
  - **Niveau 1-2 (Magique - Minimal/Modéré) :** Version simplifiée, IA légère ou désactivée
  - **Niveau 3 (Standard) :** Comportement équilibré, suggestions structurées
  - **Niveau 4-5 (Génie - Intensif/Maximum) :** Version complète avec IA avancée

### 3.2. Système de Profils Utilisateur
- **Création de Profils :** Nom, préférences, paramètres d'accessibilité
- **Gestion Multi-Utilisateurs :** Changement de profil sans redémarrage
- **Paramètres Personnalisables :**
  - Thème visuel (clair, sombre, sépia, contraste élevé)
  - Taille de police globale
  - Vitesse de synthèse vocale
  - Paramètres d'accessibilité (dyslexie, TDAH)
  - Configuration IA (fournisseur, modèle, clé API)

### 3.3. Base de Données SQLite
- **Tables Principales :**
  - `users` : Profils utilisateurs
  - `tasks` : Tâches et sous-tâches
  - `routines` : Routines et étapes
  - `brain_dumps` : Décharges de pensées
  - `presets` : Modèles personnalisés
  - `history` : Historique des actions
  - `settings` : Paramètres par utilisateur/outil
- **Sauvegarde Automatique :** Toutes les 30 secondes + à chaque action critique
- **Backup :** Export/Import de la base complète

### 3.4. Service IA Unifié
- **Fournisseurs Supportés :**
  - OpenAI (GPT-3.5/4)
  - Anthropic (Claude)
  - Google (Gemini)
  - Ollama (modèles locaux)
- **Fallback :** Mode dégradé sans IA si service indisponible
- **Cache :** Mise en cache des réponses pour économiser les appels API
- **Limitation :** Contrôle du nombre de requêtes par jour/heure

### 3.5. Système Audio Avancé
- **Synthèse Vocale :**
  - Sélection de voix système
  - Contrôle vitesse, pitch, volume
  - Mise en pause/reprise
  - Surlignage synchronisé du texte lu
- **Reconnaissance Vocale :**
  - Activation par raccourci clavier
  - Détection automatique de fin de phrase
  - Correction orthographique post-reconnaissance
- **Sons d'Ambiance :**
  - Génération procédurale (bruit blanc, rose, brownien)
  - Sons naturels (pluie, vagues, forêt)
  - Tonalités binaurales configurables
  - Mixage de plusieurs sources

### 3.6. Système d'Export Unifié
- **Formats Supportés :**
  - Texte brut (.txt)
  - Markdown (.md)
  - PDF (mise en page)
  - Word (.docx)
  - JSON (données structurées)
- **Templates :** Modèles personnalisables pour chaque format
- **Aperçu :** Prévisualisation avant export

---

## 4. Détail des Outils

### 4.1. Décomposeur de Tâches

#### 4.1.1. Version Magique (Niveaux 1-2)
- **Interface Simplifiée :**
  - Champ de saisie pour la tâche principale
  - Bouton "Décomposer" manuel
  - Liste simple des sous-tâches
  - Cases à cocher pour marquer comme complété

#### 4.1.2. Version Génie (Niveaux 3-5)
- **Fonctionnalités Avancées :**
  - **Décomposition IA :** Analyse automatique et suggestion de sous-tâches
  - **Décomposition Récursive :** Arbre hiérarchique illimité
  - **Estimations Temporelles :** IA suggère durées, modification manuelle possible
  - **Barre de Progression :** Visuelle avec pourcentage global
  - **Calcul Temps Total :** Estimation automatique temps restant
  - **Catégorisation :** Attribution automatique de catégories/tags
  - **Priorisation :** Suggestion d'ordre d'exécution optimal

#### 4.1.3. Fonctionnalités Communes
- **Interface Hiérarchique :** Arbre expandable avec indentation visuelle
- **Drag & Drop :** Réorganisation des tâches par glisser-déposer
- **Recherche :** Filtrage rapide dans l'arbre de tâches
- **Modèles et Historique :**
  - **Suggestions Intelligentes :** Base de 50+ tâches courantes
  - **Modèles Personnalisés :** Sauvegarde/chargement de structures
  - **Tâches Pré-décomposées :** 20+ tâches complexes prêtes à l'emploi
  - **Historique Complet :** Toutes les décompositions sauvegardées avec recherche
- **Export Avancé :**
  - Tous formats avec structure préservée
  - Export calendrier (ICS)
  - Partage par email automatique
- **Statistiques :** Temps moyen par type de tâche, taux de complétion

### 4.2. TimeFocus

#### 4.2.1. Version Magique (Niveaux 1-2)
- **Minuteur Simple :**
  - Sélection durée (15min, 30min, 45min, 1h, personnalisé)
  - Boutons Play/Pause/Stop
  - Affichage temps restant
  - Notification sonore fin de session

#### 4.2.2. Version Génie (Niveaux 3-5)
- **Cycles Pomodoro Avancés :**
  - Configuration complète (travail/pause courte/pause longue)
  - Cycles personnalisés (ex: 52/17, 90/20)
  - Adaptation automatique selon l'heure
  - Suggestions IA de durées optimales
- **Fonctionnalités Avancées :**
  - **Objectifs Micro-Sessions :** Définition d'objectif avant démarrage
  - **Suggestions Pauses IA :** Activités contextuelles (étirement, respiration)
  - **Analyse Productivité :** Statistiques détaillées, graphiques
  - **Intégration Biologique :** Adaptation selon rythme circadien

#### 4.2.3. Fonctionnalités Communes
- **Contrôles Précis :**
  - Play/Pause : Reprise exacte
  - Suivant : Passage phase suivante
  - Réinitialiser : Retour état initial
- **Feedback Visuel :**
  - Barre de progression circulaire
  - Changement couleur selon phase
  - Affichage MM:SS avec millisecondes
- **Sons d'Ambiance Intégrés :**
  - 15+ ambiances générées (nature, urbain, abstrait)
  - Mixage en temps réel
  - Contrôle volume individuel par source
  - Égaliseur 5 bandes
- **Presets Intelligents :**
  - Modèles prédéfinis (Pomodoro, Ultradian, etc.)
  - Sauvegarde configurations personnelles
  - Import/Export presets
- **Notifications :**
  - Notifications système
  - Sons personnalisables
  - Alerte visuelle si fenêtre en arrière-plan

### 4.3. Grille des Priorités

#### 4.3.1. Version Magique (Niveaux 1-2)
- **Matrice Simple :**
  - 4 quadrants visuels
  - Ajout tâches par clic
  - Déplacement simple entre quadrants
  - Marquage complété/non-complété

#### 4.3.2. Version Génie (Niveaux 3-5)
- **Analyse IA Avancée :**
  - Suggestion automatique de quadrant
  - Analyse de charge par quadrant
  - Recommandations de rééquilibrage
  - Prédiction temps nécessaire par quadrant
- **Fonctionnalités Avancées :**
  - **Scoring Automatique :** Algorithme de priorisation
  - **Dépendances :** Liens entre tâches
  - **Récurrence Intelligente :** Gestion automatique tâches récurrentes
  - **Alertes Contextuelles :** Notifications selon urgence

#### 4.3.3. Fonctionnalités Communes
- **Interface Intuitive :**
  - Grille 2x2 redimensionnable
  - Couleurs distinctes par quadrant
  - Compteurs visuels par quadrant
- **Gestion Avancée :**
  - **Édition Inline :** Modification directe dans la grille
  - **Métadonnées :** Date, heure, récurrence, tags
  - **Recherche/Filtrage :** Par texte, quadrant, statut, date
- **Actions de Masse :**
  - Sélection multiple
  - Déplacement groupé
  - Archivage automatique tâches complétées
- **Presets Contextuels :**
  - Modèles par domaine (travail, personnel, urgence)
  - Sauvegarde états complets
  - Restauration rapide

### 4.4. Décharge de Pensées

#### 4.4.1. Version Magique (Niveaux 1-2)
- **Éditeur Simple :**
  - Zone de texte libre
  - Compteur de mots/caractères
  - Sauvegarde automatique
  - Historique simple

#### 4.4.2. Version Génie (Niveaux 3-5)
- **Analyse IA Complète :**
  - **Extraction Thématique :** Identification sujets principaux
  - **Détection Émotions :** Analyse sentiment et états émotionnels
  - **Identification Tâches :** Extraction automatique d'actions
  - **Suggestions Structuration :** Propositions d'organisation
- **Fonctionnalités Avancées :**
  - **Mindmapping Automatique :** Génération cartes mentales
  - **Détection Patterns :** Reconnaissance habitudes de pensée
  - **Suivi Évolution :** Comparaison analyses temporelles

#### 4.4.3. Fonctionnalités Communes
- **Éditeur Riche :**
  - Coloration syntaxique légère
  - Recherche/remplacement
  - Statistiques détaillées (mots, phrases, temps écriture)
- **Historique Avancé :**
  - **Snapshots Nommés :** Versions étiquetées
  - **Timeline :** Visualisation chronologique
  - **Comparaison :** Diff entre versions
- **Modes d'Écriture :**
  - Mode concentration (plein écran)
  - Mode structure (plan automatique)
  - Mode libre (distraction minimum)
- **Export Enrichi :**
  - Texte + analyse intégrée
  - Rapport complet avec statistiques
  - Export mindmap (image/PDF)

### 4.5. Formaliseur

#### 4.5.1. Version Magique (Niveaux 1-2)
- **Transformations Basiques :**
  - Styles prédéfinis (professionnel, décontracté, concis)
  - Correction orthographique
  - Mise en forme simple

#### 4.5.2. Version Génie (Niveaux 3-5)
- **Transformation IA Avancée :**
  - **Styles Contextuels :** Adaptation automatique au public/contexte
  - **Analyse Tonalité :** Détection et modification ton original
  - **Optimisation Lisibilité :** Amélioration structure, vocabulaire
  - **Adaptation Culturelle :** Ajustement selon contexte géographique
- **Fonctionnalités Avancées :**
  - **Versions Multiples :** Génération plusieurs alternatives
  - **Feedback Explicatif :** Justification des modifications
  - **Apprentissage Style :** Mémorisation préférences utilisateur

#### 4.5.3. Fonctionnalités Communes
- **Interface Comparative :**
  - Vue côte-à-côte original/transformé
  - Surlignage des modifications
  - Historique des transformations
- **Styles Prédéfinis :**
  - Professionnel (email, rapport)
  - Académique (essai, mémoire)
  - Créatif (storytelling, marketing)
  - Simplification (ELI5, vulgarisation)
  - Formats spécifiques (lettre, CV, etc.)
- **Personnalisation :**
  - Création styles personnalisés
  - Paramètres de transformation
  - Glossaires personnels
- **Contrôle Qualité :**
  - Score de lisibilité
  - Analyse grammaticale
  - Suggestions d'amélioration

### 4.6. RoutineBuilder

#### 4.6.1. Version Magique (Niveaux 1-2)
- **Gestion Simple :**
  - Création routines nommées
  - Ajout/suppression étapes
  - Planification jours semaine
  - Suivi complétion basique

#### 4.6.2. Version Génie (Niveaux 3-5)
- **Optimisation IA :**
  - **Suggestions Personnalisées :** Routines basées sur objectifs
  - **Optimisation Temporelle :** Réorganisation pour efficacité
  - **Adaptation Dynamique :** Ajustement selon performance
  - **Analyse Habitudes :** Détection patterns comportementaux
- **Fonctionnalités Avancées :**
  - **Routines Conditionnelles :** Adaptation selon contexte
  - **Intégration Calendrier :** Synchronisation événements
  - **Suivi Biométrique :** Corrélation avec données santé

#### 4.6.3. Fonctionnalités Communes
- **Constructeur Visuel :**
  - Timeline interactive
  - Drag & Drop étapes
  - Durées estimées par étape
  - Visualisation charge hebdomadaire
- **Gestion Avancée :**
  - **Routines Multiples :** Matin, soir, travail, weekend
  - **Étapes Conditionnelles :** Si/alors logique
  - **Rappels Intelligents :** Notifications contextuelles
- **Suivi Performance :**
  - Statistiques complétion
  - Temps réel vs estimé
  - Analyse tendances
  - Identification points faibles
- **Bibliothèque Routines :**
  - 50+ routines prédéfinies
  - Catégorisation (santé, productivité, bien-être)
  - Personnalisation facile
  - Partage communautaire

### 4.7. Lecteur Immersif

#### 4.7.1. Version Magique (Niveaux 1-2)
- **Lecture Basique :**
  - Import texte (copier-coller, fichiers)
  - Synthèse vocale simple
  - Paramètres affichage basiques
  - Signets simples

#### 4.7.2. Version Génie (Niveaux 3-5)
- **Simplification IA :**
  - **Réécriture Intelligente :** Adaptation niveau lecture
  - **Résumé Automatique :** Synthèse points clés
  - **Définitions Contextuelles :** Explications mots complexes
  - **Structure Améliorée :** Réorganisation pour clarté
- **Fonctionnalités Avancées :**
  - **Analyse Compréhension :** Questions de vérification
  - **Annotations Automatiques :** Highlights intelligents
  - **Adaptation Dynamique :** Ajustement selon vitesse lecture

#### 4.7.3. Fonctionnalités Communes
- **Lecteur Avancé :**
  - **Surlignage Synchronisé :** Mot/phrase en cours
  - **Contrôles Précis :** Pause, vitesse, saut phrase/paragraphe
  - **Bookmarks Intelligents :** Sauvegarde position exacte
- **Personnalisation Visuelle :**
  - **Polices Accessibles :** OpenDyslexic incluse
  - **Thèmes Lecture :** Clair, sombre, sépia, contraste élevé
  - **Espacement Configurable :** Lettres, mots, lignes
  - **Régleur Largeur :** Colonne optimale par utilisateur
- **Presets Accessibilité :**
  - Dyslexie (police, espacement, couleurs)
  - Malvoyance (contraste, taille)
  - TDAH (structure, distractions minimales)
  - Personnalisés utilisateur
- **Formats Supportés :**
  - Texte brut, RTF, PDF, Word
  - Pages web (via URL)
  - Markdown avec rendu
  - EPUB (basique)

---

## 5. Interface Utilisateur

### 5.1. Fenêtre Principale
- **Layout Adaptatif :**
  - Barre latérale outils (collapsible)
  - Zone principale dynamique
  - Barre statut informative
  - Barre outils contextuelle
- **Navigation :**
  - Onglets pour outils multiples
  - Raccourcis clavier configurables
  - Menu contextuel clic-droit
  - Recherche globale (Ctrl+F)

### 5.2. Thèmes et Accessibilité
- **Thèmes Intégrés :**
  - Clair (bleus doux, accent vert d'eau)
  - Sombre (contrastes préservés)
  - Sépia (lecture prolongée)
  - Contraste élevé (accessibilité)
- **Paramètres Visuels :**
  - Zoom global (80% à 200%)
  - Animations réduites (option)
  - Indicateurs visuels renforcés
  - Mode daltonisme

### 5.3. Raccourcis Clavier
- **Globaux :**
  - Ctrl+N : Nouveau
  - Ctrl+O : Ouvrir
  - Ctrl+S : Sauvegarder
  - Ctrl+E : Export
  - Ctrl+/ : Aide contextuelle
- **Par Outil :** Raccourcis spécifiques configurables

---

## 6. Fonctionnalités Système

### 6.1. Performance et Optimisation
- **Démarrage Rapide :** < 3 secondes
- **Mémoire Optimisée :** < 100MB utilisation normale
- **Responsive :** Interface fluide même sur matériel modeste
- **Threading :** Opérations IA en arrière-plan

### 6.2. Sécurité et Confidentialité
- **Données Locales :** Tout stocké localement
- **Chiffrement :** Base SQLite chiffrée (optionnel)
- **Clés API :** Stockage sécurisé local
- **Aucune Télémétrie :** Respect complet vie privée

### 6.3. Portabilité
- **Multi-OS :** Windows, macOS, Linux
- **Version Portable :** Exécutable sans installation
- **Sauvegarde Cloud :** Export/import manuel
- **Migration Facile :** Assistant transfert données

### 6.4. Maintenance et Mise à Jour
- **Auto-Update :** Vérification optionnelle
- **Backup Automatique :** Sauvegarde avant MAJ
- **Rollback :** Retour version précédente
- **Logs Détaillés :** Débogage facilité

---

## 7. Exigences Techniques

### 7.1. Configuration Minimale
- **OS :** Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **RAM :** 4GB (8GB recommandé)
- **Stockage :** 500MB espace libre
- **Réseau :** Connexion pour IA (optionnel)

### 7.2. Dépendances Python
```
customtkinter>=5.0.0
sqlite3 (intégré)
requests>=2.28.0
pyttsx3>=2.90
SpeechRecognition>=3.10.0
pygame>=2.5.0
reportlab>=3.6.0
python-docx>=0.8.11
Pillow>=9.0.0
numpy>=1.24.0
```

### 7.3. Packaging
- **Exécutable :** PyInstaller pour chaque OS
- **Installeur :** NSIS (Windows), DMG (macOS), AppImage (Linux)
- **Distribution :** GitHub Releases + site web

---

## 8. Plan de Développement

### 8.1. Phase 1 (MVP)
- Architecture de base et database
- Version Magique des 7 outils
- Interface utilisateur de base
- Système de profils

### 8.2. Phase 2 (Enrichissement)
- Versions Génie avec IA
- Système audio complet
- Export avancé
- Personnalisation interface

### 8.3. Phase 3 (Optimisation)
- Performance et stabilité
- Accessibilité avancée
- Documentation complète
- Tests utilisateurs

### 8.4. Phase 4 (Finalisation)
- Packaging multi-OS
- Distribution
- Support utilisateur
- Maintenance continue