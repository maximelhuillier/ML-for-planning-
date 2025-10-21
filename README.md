# Schedule Delay Analysis Application

Application web interactive pour l'analyse de retards de planning de construction utilisant 6 méthodes professionnelles reconnues.

## Description

Cette application permet d'analyser les retards de planning en important des fichiers Primavera P6 (.xer) ou Microsoft Project (.xml/.mpp) et en appliquant l'une des 6 méthodes d'analyse de retard reconnues dans l'industrie de la construction.

## Fonctionnalités

### Formats de fichiers supportés
- **Primavera P6** : Fichiers .xer
- **MS Project** : Fichiers .xml (recommandé) et .mpp

### 6 Méthodes d'analyse de retard

1. **As-Planned vs As-Built**
   - Compare le planning baseline avec le planning réalisé
   - Identifie les retards et leur magnitude
   - Idéal pour une vue d'ensemble des retards

2. **Impacted As-Planned**
   - Insert des événements de retard dans le planning baseline
   - Démontre l'impact sur la date de fin du projet
   - Utile pour les réclamations de retard

3. **Collapsed As-Built (But-For)**
   - Retire les retards du planning réalisé
   - Montre quand le projet aurait été terminé "sans" ces retards
   - Utilisé pour déterminer la responsabilité

4. **Time Impact Analysis (TIA)**
   - Mesure l'impact temporel d'événements de retard spécifiques
   - Insert les retards dans le planning contemporain
   - Méthode privilégiée pour l'analyse contractuelle

5. **Windows Analysis**
   - Divise le projet en fenêtres temporelles
   - Analyse les retards dans chaque fenêtre
   - Excellent pour les projets de longue durée

6. **Contemporaneous Period Analysis**
   - Utilise les enregistrements contemporains du projet
   - Analyse basée sur les logs quotidiens et rapports de progrès
   - Fournit les preuves les plus solides pour les litiges

### Fonctionnalités additionnelles

- **Questions interactives** : L'application pose des questions pertinentes selon la méthode choisie
- **Suggestions intelligentes** : Recommandations basées sur les données du planning
- **Visualisations Gantt** : Diagrammes interactifs avec Plotly
- **Comparaisons** : Visualisation côte à côte baseline vs actuel
- **Export Excel** : Rapports détaillés avec graphiques et analyses
- **Analyse du chemin critique** : Identification automatique des activités critiques

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)

### Installation des dépendances

```bash
# Cloner le repository
git clone <repository-url>
cd ML-for-planning-

# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows:
venv\Scripts\activate
# Sur macOS/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvrira dans votre navigateur par défaut à l'adresse `http://localhost:8501`

### Guide d'utilisation

#### 1. Upload des fichiers

1. Naviguez vers l'onglet **"Upload Fichiers"**
2. Uploadez votre planning **baseline** (as-planned)
3. Uploadez votre planning **actuel** (as-built) si nécessaire
4. Vérifiez le résumé des plannings parsés

**Note pour les fichiers .mpp** : Pour une meilleure compatibilité, exportez vos fichiers MS Project en format XML :
- Ouvrez le fichier dans MS Project
- Fichier > Enregistrer sous > Choisir "XML Format (*.xml)"
- Uploadez le fichier XML

#### 2. Effectuer une analyse

1. Allez dans l'onglet **"Analyse"**
2. Choisissez une méthode d'analyse parmi les 6 disponibles
3. Lisez la description de la méthode
4. Répondez aux questions de configuration
5. Consultez les suggestions de l'application
6. Cliquez sur **"Lancer l'analyse"**

#### 3. Visualisations

1. Naviguez vers **"Visualisations"**
2. Consultez les diagrammes de Gantt :
   - Planning baseline
   - Planning actuel
   - Comparaison
3. Visualisez la timeline des retards

#### 4. Export

1. Allez dans **"Export"**
2. Configurez les options d'export
3. Téléchargez le rapport Excel complet avec :
   - Résumé exécutif
   - Analyse détaillée par activité
   - Retards par cause
   - Graphiques et visualisations

## Structure du projet

```
ML-for-planning-/
├── app.py                      # Application Streamlit principale
├── requirements.txt            # Dépendances Python
├── README.md                   # Documentation
├── src/
│   ├── parsers/               # Parsers pour P6 et MS Project
│   │   ├── p6_parser.py       # Parser XER
│   │   └── msp_parser.py      # Parser MS Project
│   ├── analyzers/             # Méthodes d'analyse
│   │   ├── base_analyzer.py   # Classe de base
│   │   ├── as_planned_vs_as_built.py
│   │   ├── impacted_as_planned.py
│   │   ├── collapsed_as_built.py
│   │   ├── time_impact_analysis.py
│   │   ├── windows_analysis.py
│   │   └── contemporaneous_analysis.py
│   ├── exporters/
│   │   └── excel_exporter.py  # Export Excel
│   ├── visualizers/
│   │   └── gantt_visualizer.py # Visualisations Gantt
│   └── utils/
│       ├── schedule_utils.py   # Utilitaires de planning
│       └── date_utils.py       # Utilitaires de dates
├── tests/                      # Tests unitaires
└── data/
    └── sample_files/           # Fichiers d'exemple
```

## Exemples d'utilisation

### Exemple 1 : Analyse As-Planned vs As-Built

```python
from src.parsers.p6_parser import parse_xer_file
from src.analyzers import create_analyzer

# Parser les fichiers
baseline = parse_xer_file("baseline.xer")
current = parse_xer_file("current.xer")

# Créer l'analyseur
analyzer = create_analyzer("As-Planned vs As-Built")

# Lancer l'analyse
result = analyzer.analyze(
    baseline_schedule=baseline,
    current_schedule=current,
    include_non_critical=True
)

# Afficher les résultats
print(f"Retard total: {result.total_delay_days} jours")
print(f"Retard critique: {result.critical_delay_days} jours")
```

### Exemple 2 : Export Excel

```python
from src.exporters.excel_exporter import export_to_excel

# Exporter les résultats
export_to_excel(
    result,
    output_path="rapport_retards.xlsx",
    include_charts=True
)
```

## Dépendances principales

- **streamlit** : Interface web interactive
- **pandas** : Manipulation de données
- **plotly** : Visualisations interactives
- **openpyxl** : Export Excel
- **xerparser** : Parsing de fichiers P6 XER
- **networkx** : Analyse de réseau pour chemin critique

## Développement

### Ajouter une nouvelle méthode d'analyse

1. Créer une nouvelle classe héritant de `BaseDelayAnalyzer`
2. Implémenter la méthode `analyze()`
3. Décorer avec `@DelayAnalyzerFactory.register`
4. Ajouter les questions spécifiques à la méthode

Exemple :

```python
from src.analyzers.base_analyzer import BaseDelayAnalyzer, DelayAnalyzerFactory

@DelayAnalyzerFactory.register
class MyNewAnalyzer(BaseDelayAnalyzer):
    def __init__(self):
        super().__init__(
            name="Ma Nouvelle Méthode",
            description="Description de la méthode"
        )
        self.required_inputs = ['baseline_schedule']

    def analyze(self, **kwargs):
        # Implémentation
        pass
```

## Limitations connues

1. **Fichiers .mpp** : Le support direct des fichiers .mpp binaires est limité. Préférez l'export en XML.
2. **Taille des fichiers** : Les très gros projets (>10 000 activités) peuvent ralentir l'interface.
3. **Calendriers** : Les calendriers personnalisés complexes ne sont pas entièrement supportés.

## Roadmap

- [ ] Support ML pour prédiction de retards
- [ ] Import de multiples versions de planning
- [ ] Analyse comparative de plusieurs projets
- [ ] API REST pour intégration
- [ ] Support de formats additionnels (ASTA Powerproject)
- [ ] Analyse de ressources et coûts

## Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation dans le code
- Contactez les mainteneurs

## Références

Les méthodes d'analyse implémentées sont basées sur les standards de l'industrie :
- AACE International Recommended Practices
- SCL Delay and Disruption Protocol
- CIOB Guide to Good Practice in the Management of Time

## Auteurs

Développé avec Claude Code pour l'analyse professionnelle de retards de planning de construction.
