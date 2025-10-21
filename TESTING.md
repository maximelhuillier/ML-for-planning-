# Guide de Test - Application d'Analyse de Retards

Ce guide vous explique comment tester l'application étape par étape.

## 🚀 Démarrage Rapide

### Option 1 : Test avec Données Générées (Recommandé pour débuter)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Tester la génération de données d'exemple
python tests/test_sample_data.py

# 3. Lancer l'application
streamlit run app.py
```

### Option 2 : Test avec Vos Propres Fichiers

Si vous avez des fichiers .xer ou .xml/.mpp :

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
streamlit run app.py

# 3. Uploader vos fichiers dans l'interface
```

## 📋 Tests Détaillés

### Test 1 : Installation et Dépendances

```bash
# Vérifier la version de Python (minimum 3.8)
python --version

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Windows:
venv\Scripts\activate
# Sur macOS/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Vérifier l'installation
python -c "import streamlit; import pandas; import plotly; print('✓ All imports successful')"
```

**Résultat attendu :** Toutes les bibliothèques s'installent sans erreur.

### Test 2 : Génération de Données d'Exemple

```bash
python tests/test_sample_data.py
```

**Résultat attendu :**
```
Generating sample schedules...

Baseline Schedule:
  Project: Sample Construction Project - Baseline
  Activities: 11
  Duration: 2024-01-01 to 2024-06-30

Current Schedule:
  Project: Sample Construction Project - Current
  Activities: 11
  Duration: 2024-01-01 to 2024-07-20

--- Quick Test Analysis ---

Total Delay: XX.X days
Critical Delay: XX.X days
Affected Activities: X

Top 5 Delayed Activities:
  1. Activity Name: XX.X days
  ...

✓ Sample data generation successful!
```

### Test 3 : Lancement de l'Application

```bash
streamlit run app.py
```

**Résultat attendu :**
- L'application s'ouvre dans votre navigateur
- URL : http://localhost:8501
- Page d'accueil s'affiche avec le titre "📊 Schedule Delay Analysis"

### Test 4 : Test des Parsers (Avec Code)

#### Test du Parser Programmatiquement

```python
# test_parsers.py
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule

# Tester la création de schedules
baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

print(f"Baseline activities: {len(baseline.activities)}")
print(f"Current activities: {len(current.activities)}")

# Vérifier les données
for act_id, activity in list(baseline.activities.items())[:3]:
    print(f"\n{activity.name}:")
    print(f"  Start: {activity.start_date}")
    print(f"  Finish: {activity.finish_date}")
    print(f"  Duration: {activity.duration} days")
    print(f"  Critical: {activity.is_critical}")
```

### Test 5 : Test de Chaque Méthode d'Analyse

#### 5.1 As-Planned vs As-Built

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import create_analyzer

baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

analyzer = create_analyzer("As-Planned vs As-Built")
result = analyzer.analyze(
    baseline_schedule=baseline,
    current_schedule=current,
    include_non_critical=True
)

print(f"Total Delay: {result.total_delay_days:.1f} days")
print(f"Critical Delay: {result.critical_delay_days:.1f} days")
print(f"\nRecommendations:")
for rec in result.recommendations:
    print(f"  - {rec}")
```

#### 5.2 Impacted As-Planned

```python
from tests.test_sample_data import create_sample_baseline_schedule
from src.analyzers import create_analyzer
from datetime import datetime

baseline = create_sample_baseline_schedule()

# Créer des événements de retard
delay_events = [
    {
        'activity_id': 'A2000',
        'delay_days': 5,
        'event_date': datetime(2024, 1, 25),
        'cause': 'Adverse Weather'
    },
    {
        'activity_id': 'A3000',
        'delay_days': 7,
        'event_date': datetime(2024, 4, 1),
        'cause': 'Material Delay'
    }
]

analyzer = create_analyzer("Impacted As-Planned")
result = analyzer.analyze(
    baseline_schedule=baseline,
    delay_events=delay_events
)

print(f"Total Impact: {result.total_delay_days:.1f} days")
```

#### 5.3 Windows Analysis

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import create_analyzer
from datetime import datetime

# Créer plusieurs versions du planning
schedule_updates = {
    datetime(2024, 1, 1): create_sample_baseline_schedule(),
    datetime(2024, 2, 1): create_sample_current_schedule(),
    datetime(2024, 3, 1): create_sample_current_schedule(),
}

analyzer = create_analyzer("Windows Analysis")
result = analyzer.analyze(
    schedule_updates=schedule_updates,
    window_method='Monthly'
)

print(f"Windows analyzed: {result.metadata['window_count']}")
print(f"Total delay: {result.total_delay_days:.1f} days")
```

### Test 6 : Test des Visualisations

```python
from tests.test_sample_data import create_sample_baseline_schedule
from src.visualizers.gantt_visualizer import GanttVisualizer

schedule = create_sample_baseline_schedule()
viz = GanttVisualizer()

# Créer Gantt chart
fig = viz.create_gantt(schedule, title="Test Gantt", max_activities=20)

# Afficher (nécessite un environnement avec display)
# fig.show()

print("✓ Gantt visualization created successfully")
```

### Test 7 : Test de l'Export Excel

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import create_analyzer
from src.exporters.excel_exporter import export_to_excel

baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

analyzer = create_analyzer("As-Planned vs As-Built")
result = analyzer.analyze(
    baseline_schedule=baseline,
    current_schedule=current
)

# Exporter
output_file = export_to_excel(
    result,
    output_path="test_report.xlsx",
    include_charts=True
)

print(f"✓ Report exported to: {output_file}")
```

### Test 8 : Test de l'Interface Streamlit (Manuel)

1. **Page Accueil**
   - ✅ Les 6 méthodes sont listées
   - ✅ Les descriptions s'affichent correctement

2. **Page Upload**
   - ✅ Sélectionner "📁 Upload Fichiers" dans la sidebar
   - ✅ Les deux onglets (Baseline et Actuel) sont visibles
   - Note : Sans fichiers réels, vous verrez juste l'uploader

3. **Page Analyse** (avec données générées)
   - Créer un script pour charger les données en session_state :

```python
# test_app_with_data.py
import streamlit as st
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule

st.session_state.baseline_schedule = create_sample_baseline_schedule()
st.session_state.current_schedule = create_sample_current_schedule()

st.success("✓ Test data loaded into session state")
st.write("Now navigate to the Analysis page")
```

4. **Page Visualisations**
   - ✅ Gantt charts s'affichent
   - ✅ Comparaison fonctionne
   - ✅ Interaction avec les graphiques

5. **Page Export**
   - ✅ Bouton de téléchargement apparaît
   - ✅ Fichier Excel se télécharge
   - ✅ Fichier s'ouvre dans Excel/LibreOffice

## 🐛 Dépannage

### Problème 1 : ModuleNotFoundError

```bash
# Solution
pip install -r requirements.txt
```

### Problème 2 : xerparser not found

```bash
# Installer xerparser
pip install xerparser
```

### Problème 3 : Streamlit ne démarre pas

```bash
# Vérifier que streamlit est installé
pip show streamlit

# Réinstaller si nécessaire
pip uninstall streamlit
pip install streamlit
```

### Problème 4 : "No module named 'src'"

```bash
# Assurez-vous d'être dans le bon répertoire
cd /path/to/ML-for-planning-

# Vérifier la structure
ls -la src/
```

### Problème 5 : Erreur avec openpyxl ou xlsxwriter

```bash
# Installer manuellement
pip install openpyxl xlsxwriter
```

## 📊 Résultats Attendus

### Après Test Complet

✅ **Installation** : Toutes les dépendances installées
✅ **Données** : Schedules d'exemple générés
✅ **Parsers** : Données lues correctement
✅ **Analyseurs** : 6 méthodes fonctionnent
✅ **Visualisations** : Gantt charts s'affichent
✅ **Export** : Fichiers Excel générés
✅ **Application** : Interface Streamlit opérationnelle

## 🎯 Scénarios de Test Complets

### Scénario 1 : Analyse As-Planned vs As-Built

1. Générer les données : `python tests/test_sample_data.py`
2. Lancer l'app : `streamlit run app.py`
3. Charger les schedules (ou utiliser le code ci-dessus)
4. Aller dans "Analyse"
5. Sélectionner "As-Planned vs As-Built"
6. Répondre aux questions
7. Cliquer "Lancer l'analyse"
8. Vérifier les résultats
9. Aller dans "Export"
10. Télécharger le rapport

### Scénario 2 : Test avec Fichiers Réels

Si vous avez des fichiers .xer ou .xml :

1. Lancer l'app : `streamlit run app.py`
2. Aller dans "Upload Fichiers"
3. Upload baseline.xer
4. Vérifier le parsing
5. Upload current.xer
6. Vérifier le parsing
7. Aller dans "Visualisations"
8. Voir les Gantt charts
9. Aller dans "Analyse"
10. Choisir une méthode
11. Exporter les résultats

## 📝 Checklist de Test

- [ ] Python 3.8+ installé
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Script de test exécuté avec succès
- [ ] Application Streamlit démarre
- [ ] Page d'accueil s'affiche
- [ ] Données d'exemple générées
- [ ] Au moins une méthode d'analyse testée
- [ ] Visualisations fonctionnent
- [ ] Export Excel fonctionne
- [ ] Aucune erreur dans la console

## 💡 Tests Avancés

### Test de Performance

```python
import time
from tests.test_sample_data import create_sample_baseline_schedule

# Créer un grand planning
schedule = create_sample_baseline_schedule()

# Dupliquer les activités pour créer un gros planning
original_activities = list(schedule.activities.values())
for i in range(10):  # Créer 110 activités
    for act in original_activities:
        new_id = f"{act.activity_id}_{i}"
        new_act = ScheduleActivity(
            activity_id=new_id,
            name=f"{act.name} - Copy {i}",
            duration=act.duration,
            start_date=act.start_date,
            finish_date=act.finish_date
        )
        schedule.add_activity(new_act)

start_time = time.time()
df = schedule.to_dataframe()
end_time = time.time()

print(f"Processed {len(schedule.activities)} activities in {end_time - start_time:.2f}s")
```

### Test d'Intégrité des Données

```python
def test_schedule_integrity(schedule):
    """Vérifier l'intégrité d'un schedule"""
    errors = []

    # Vérifier que toutes les activités ont des dates
    for act_id, act in schedule.activities.items():
        if not act.start_date:
            errors.append(f"{act_id}: Missing start date")
        if not act.finish_date:
            errors.append(f"{act_id}: Missing finish date")

        # Vérifier cohérence des dates
        if act.start_date and act.finish_date:
            if act.finish_date < act.start_date:
                errors.append(f"{act_id}: Finish before start")

    # Vérifier les relations
    for pred, succ, rel_type, lag in schedule.relationships:
        if pred not in schedule.activities:
            errors.append(f"Relationship: Unknown predecessor {pred}")
        if succ not in schedule.activities:
            errors.append(f"Relationship: Unknown successor {succ}")

    return errors

# Test
from tests.test_sample_data import create_sample_baseline_schedule
schedule = create_sample_baseline_schedule()
errors = test_schedule_integrity(schedule)

if errors:
    print("❌ Errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Schedule integrity check passed")
```

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifiez ce guide de dépannage
2. Consultez les logs dans la console
3. Vérifiez que tous les fichiers sont présents
4. Ouvrez une issue sur GitHub avec :
   - Version de Python
   - Système d'exploitation
   - Message d'erreur complet
   - Étapes pour reproduire

---

**Bonne chance avec vos tests !** 🚀
