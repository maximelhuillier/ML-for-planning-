# Guide de Démarrage Rapide ⚡

Testez l'application en **3 minutes** !

## Étape 1 : Installation (1 minute)

```bash
# Installer les dépendances
pip install streamlit pandas numpy plotly networkx openpyxl xerparser python-dateutil matplotlib xlsxwriter scikit-learn tqdm pathlib2 typing-extensions
```

## Étape 2 : Tester les Données (30 secondes)

```bash
# Générer et tester les données d'exemple
python tests/test_sample_data.py
```

**Vous devriez voir :**
```
✓ Sample data generation successful!
Total Delay: 162.0 days
Critical Delay: 127.0 days
```

## Étape 3 : Lancer l'Application (30 secondes)

```bash
# Démarrer l'application
streamlit run app.py
```

**L'application s'ouvrira automatiquement dans votre navigateur** à `http://localhost:8501`

## Utilisation Immédiate (1 minute)

### Option A : Test avec Interface (Sans fichiers)

1. **Accueil** : Explorez les 6 méthodes disponibles
2. **Upload Fichiers** : Interface prête pour vos fichiers .xer ou .xml
3. **Visualisations** : Explorez l'interface

### Option B : Test Programmatique (Avec données)

Créez un fichier `quick_test.py` :

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import create_analyzer
from src.exporters.excel_exporter import export_to_excel

# Générer les données
baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

# Analyser
analyzer = create_analyzer("As-Planned vs As-Built")
result = analyzer.analyze(
    baseline_schedule=baseline,
    current_schedule=current
)

# Afficher les résultats
print(f"\n{'='*50}")
print(f"RÉSULTATS DE L'ANALYSE")
print(f"{'='*50}")
print(f"Retard Total: {result.total_delay_days:.1f} jours")
print(f"Retard Critique: {result.critical_delay_days:.1f} jours")
print(f"Activités Affectées: {len(result.delays_by_activity)}")

print(f"\n📋 RECOMMANDATIONS:")
for i, rec in enumerate(result.recommendations, 1):
    print(f"{i}. {rec}")

# Exporter en Excel
export_to_excel(result, "rapport_test.xlsx")
print(f"\n✓ Rapport Excel généré: rapport_test.xlsx")
```

Puis exécutez :
```bash
python quick_test.py
```

## Test des 6 Méthodes d'Analyse

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import get_available_methods, create_analyzer
from datetime import datetime

baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

# Tester toutes les méthodes
methods = get_available_methods()

for method in methods:
    print(f"\n{'='*60}")
    print(f"Test: {method['name']}")
    print(f"{'='*60}")

    analyzer = create_analyzer(method['name'])

    # Adapter les paramètres selon la méthode
    try:
        if method['name'] == "As-Planned vs As-Built":
            result = analyzer.analyze(
                baseline_schedule=baseline,
                current_schedule=current
            )
        elif method['name'] == "Impacted As-Planned":
            delay_events = [
                {'activity_id': 'A2000', 'delay_days': 5,
                 'event_date': datetime(2024, 1, 25), 'cause': 'Weather'}
            ]
            result = analyzer.analyze(
                baseline_schedule=baseline,
                delay_events=delay_events
            )
        elif method['name'] == "Collapsed As-Built (But-For)":
            delay_events = [
                {'activity_id': 'A2000', 'delay_days': 5,
                 'event_date': datetime(2024, 1, 25), 'cause': 'Weather'}
            ]
            result = analyzer.analyze(
                as_built_schedule=current,
                delay_events=delay_events
            )
        elif method['name'] == "Time Impact Analysis (TIA)":
            delay_events = [
                {'activity_id': 'A2000', 'delay_days': 5,
                 'event_date': datetime(2024, 1, 25), 'cause': 'Weather'}
            ]
            result = analyzer.analyze(
                baseline_schedule=baseline,
                delay_events=delay_events
            )
        elif method['name'] == "Windows Analysis":
            updates = {
                datetime(2024, 1, 1): baseline,
                datetime(2024, 3, 1): current,
            }
            result = analyzer.analyze(
                schedule_updates=updates
            )
        elif method['name'] == "Contemporaneous Period Analysis":
            updates = {
                datetime(2024, 1, 1): baseline,
                datetime(2024, 3, 1): current,
            }
            result = analyzer.analyze(
                schedule_updates=updates,
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 3, 31)
            )

        print(f"✓ Total Delay: {result.total_delay_days:.1f} days")
        print(f"✓ Critical Delay: {result.critical_delay_days:.1f} days")

    except Exception as e:
        print(f"⚠️  Error: {str(e)}")
```

## 🎨 Visualisations

```python
from tests.test_sample_data import create_sample_baseline_schedule
from src.visualizers.gantt_visualizer import GanttVisualizer

schedule = create_sample_baseline_schedule()
viz = GanttVisualizer()

# Créer un Gantt chart
fig = viz.create_gantt(
    schedule,
    title="Mon Planning de Test",
    show_critical_only=False,
    max_activities=50
)

# Sauvegarder en HTML pour visualiser dans le navigateur
fig.write_html("gantt_test.html")
print("✓ Gantt chart sauvegardé dans gantt_test.html")
```

## 📊 Export Excel Complet

```python
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import create_analyzer
from src.exporters.excel_exporter import ExcelExporter

# Analyser
baseline = create_sample_baseline_schedule()
current = create_sample_current_schedule()

analyzer = create_analyzer("As-Planned vs As-Built")
result = analyzer.analyze(
    baseline_schedule=baseline,
    current_schedule=current
)

# Export Excel avec graphiques
exporter = ExcelExporter()
exporter.export(
    result,
    output_path="rapport_complet.xlsx",
    include_charts=True
)

print("✓ Rapport Excel complet généré: rapport_complet.xlsx")
print("\nContenu du rapport:")
print("  - Summary (Résumé exécutif)")
print("  - Detailed Analysis (Analyse détaillée)")
print("  - By Cause (Retards par cause)")
print("  - Charts (Graphiques)")
```

## ✅ Checklist de Vérification

- [ ] `pip install` sans erreur
- [ ] `python tests/test_sample_data.py` affiche ✓
- [ ] `streamlit run app.py` ouvre le navigateur
- [ ] Page d'accueil s'affiche correctement
- [ ] Les 6 méthodes sont listées
- [ ] Un test d'analyse fonctionne
- [ ] Export Excel généré avec succès

## 🚨 Problèmes Courants

### Erreur : "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Erreur : "Command 'streamlit' not found"
```bash
pip install --upgrade streamlit
```

### Erreur : Port 8501 déjà utilisé
```bash
streamlit run app.py --server.port 8502
```

### Application ne démarre pas
```bash
# Vérifier l'installation
streamlit --version
python --version

# Réinstaller si nécessaire
pip uninstall streamlit
pip install streamlit
```

## 📚 Étapes Suivantes

1. **Testez avec vos fichiers** : Importez vos fichiers .xer ou .xml
2. **Explorez les méthodes** : Testez les 6 méthodes d'analyse
3. **Personnalisez** : Adaptez le code à vos besoins
4. **Documentation** : Consultez README.md et TESTING.md pour plus de détails

## 🎯 Objectif : En Production

Pour utiliser en production :

1. ✅ Testez avec vos données réelles
2. ✅ Vérifiez les résultats d'analyse
3. ✅ Validez les exports Excel
4. ✅ Formez les utilisateurs
5. ✅ Déployez (Streamlit Cloud, serveur interne, etc.)

---

**Temps total : ~3 minutes** ⚡

Vous êtes prêt à analyser des retards de planning ! 🚀
