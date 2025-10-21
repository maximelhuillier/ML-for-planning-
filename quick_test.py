"""
Script de test rapide pour l'application d'analyse de retards
Execute ce script pour tester rapidement toutes les fonctionnalités
"""
from tests.test_sample_data import create_sample_baseline_schedule, create_sample_current_schedule
from src.analyzers import get_available_methods, create_analyzer
from src.exporters.excel_exporter import export_to_excel
from src.visualizers.gantt_visualizer import GanttVisualizer
from datetime import datetime

def print_separator(title=""):
    """Print a nice separator"""
    print(f"\n{'='*70}")
    if title:
        print(f"  {title}")
        print(f"{'='*70}")

def test_data_generation():
    """Test 1: Generate sample data"""
    print_separator("TEST 1: Génération de Données")

    baseline = create_sample_baseline_schedule()
    current = create_sample_current_schedule()

    print(f"✓ Baseline créé: {len(baseline.activities)} activités")
    print(f"✓ Current créé: {len(current.activities)} activités")

    return baseline, current


def test_analysis_methods(baseline, current):
    """Test 2: Test all analysis methods"""
    print_separator("TEST 2: Méthodes d'Analyse")

    results = {}

    # Test 1: As-Planned vs As-Built
    print("\n1. As-Planned vs As-Built...")
    analyzer = create_analyzer("As-Planned vs As-Built")
    result = analyzer.analyze(
        baseline_schedule=baseline,
        current_schedule=current
    )
    results['as_planned_vs_as_built'] = result
    print(f"   ✓ Retard total: {result.total_delay_days:.1f} jours")
    print(f"   ✓ Retard critique: {result.critical_delay_days:.1f} jours")

    # Test 2: Impacted As-Planned
    print("\n2. Impacted As-Planned...")
    delay_events = [
        {'activity_id': 'A2000', 'delay_days': 5,
         'event_date': datetime(2024, 1, 25), 'cause': 'Adverse Weather'},
        {'activity_id': 'A3000', 'delay_days': 7,
         'event_date': datetime(2024, 4, 1), 'cause': 'Material Delay'}
    ]
    analyzer = create_analyzer("Impacted As-Planned")
    result = analyzer.analyze(
        baseline_schedule=baseline,
        delay_events=delay_events
    )
    results['impacted_as_planned'] = result
    print(f"   ✓ Impact total: {result.total_delay_days:.1f} jours")

    # Test 3: Collapsed As-Built
    print("\n3. Collapsed As-Built...")
    analyzer = create_analyzer("Collapsed As-Built (But-For)")
    result = analyzer.analyze(
        as_built_schedule=current,
        delay_events=delay_events
    )
    results['collapsed_as_built'] = result
    print(f"   ✓ Retards retirés: {result.total_delay_days:.1f} jours")

    # Test 4: Time Impact Analysis
    print("\n4. Time Impact Analysis...")
    analyzer = create_analyzer("Time Impact Analysis (TIA)")
    result = analyzer.analyze(
        baseline_schedule=baseline,
        delay_events=delay_events
    )
    results['tia'] = result
    print(f"   ✓ Impact cumulatif: {result.total_delay_days:.1f} jours")

    # Test 5: Windows Analysis
    print("\n5. Windows Analysis...")
    updates = {
        datetime(2024, 1, 1): baseline,
        datetime(2024, 3, 1): current,
        datetime(2024, 4, 15): current,
    }
    analyzer = create_analyzer("Windows Analysis")
    result = analyzer.analyze(
        schedule_updates=updates
    )
    results['windows'] = result
    print(f"   ✓ Fenêtres analysées: {result.metadata.get('window_count', 0)}")
    print(f"   ✓ Retard total: {result.total_delay_days:.1f} jours")

    # Test 6: Contemporaneous Analysis
    print("\n6. Contemporaneous Period Analysis...")
    analyzer = create_analyzer("Contemporaneous Period Analysis")
    result = analyzer.analyze(
        schedule_updates=updates,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 4, 30)
    )
    results['contemporaneous'] = result
    print(f"   ✓ Score documentation: {result.metadata.get('documentation_score', 0):.1f}/100")
    print(f"   ✓ Retard total: {result.total_delay_days:.1f} jours")

    return results


def test_visualizations(baseline, current):
    """Test 3: Test visualizations"""
    print_separator("TEST 3: Visualisations")

    viz = GanttVisualizer()

    # Test Gantt chart
    print("\n1. Gantt Chart Baseline...")
    fig1 = viz.create_gantt(baseline, title="Baseline Schedule", max_activities=20)
    fig1.write_html("test_gantt_baseline.html")
    print("   ✓ Sauvegardé: test_gantt_baseline.html")

    # Test comparison
    print("\n2. Comparaison Baseline vs Current...")
    fig2 = viz.create_comparison_gantt(baseline, current)
    fig2.write_html("test_gantt_comparison.html")
    print("   ✓ Sauvegardé: test_gantt_comparison.html")

    # Test critical path
    print("\n3. Chemin Critique...")
    fig3 = viz.create_critical_path_viz(baseline)
    fig3.write_html("test_critical_path.html")
    print("   ✓ Sauvegardé: test_critical_path.html")


def test_excel_export(results):
    """Test 4: Test Excel export"""
    print_separator("TEST 4: Export Excel")

    # Export main result
    print("\n1. Export rapport principal...")
    export_to_excel(
        results['as_planned_vs_as_built'],
        output_path="test_rapport_principal.xlsx",
        include_charts=True
    )
    print("   ✓ Sauvegardé: test_rapport_principal.xlsx")

    # Export TIA result
    print("\n2. Export Time Impact Analysis...")
    export_to_excel(
        results['tia'],
        output_path="test_rapport_tia.xlsx",
        include_charts=True
    )
    print("   ✓ Sauvegardé: test_rapport_tia.xlsx")


def show_detailed_results(results):
    """Show detailed results"""
    print_separator("RÉSULTATS DÉTAILLÉS")

    result = results['as_planned_vs_as_built']

    print("\n📊 STATISTIQUES:")
    print(f"   Retard Total: {result.total_delay_days:.1f} jours")
    print(f"   Retard Critique: {result.critical_delay_days:.1f} jours")
    print(f"   Activités Affectées: {len(result.delays_by_activity)}")

    print("\n📋 TOP 5 ACTIVITÉS RETARDÉES:")
    sorted_delays = sorted(result.delays_by_activity,
                          key=lambda x: x['delay_days'], reverse=True)[:5]
    for i, delay in enumerate(sorted_delays, 1):
        critical = "🔴" if delay['is_critical'] else "🟢"
        print(f"   {i}. {critical} {delay['activity_name']}: {delay['delay_days']:.1f} jours")

    if result.delays_by_cause:
        print("\n🎯 RETARDS PAR CAUSE:")
        for cause, days in sorted(result.delays_by_cause.items(),
                                 key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {cause}: {days:.1f} jours")

    if result.recommendations:
        print("\n💡 RECOMMANDATIONS:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  APPLICATION D'ANALYSE DE RETARDS - TEST COMPLET")
    print("="*70)

    try:
        # Test 1: Data generation
        baseline, current = test_data_generation()

        # Test 2: Analysis methods
        results = test_analysis_methods(baseline, current)

        # Test 3: Visualizations
        test_visualizations(baseline, current)

        # Test 4: Excel export
        test_excel_export(results)

        # Show detailed results
        show_detailed_results(results)

        # Final summary
        print_separator("RÉSUMÉ FINAL")
        print("\n✅ TOUS LES TESTS RÉUSSIS!")
        print("\nFichiers générés:")
        print("   📊 test_gantt_baseline.html")
        print("   📊 test_gantt_comparison.html")
        print("   📊 test_critical_path.html")
        print("   📄 test_rapport_principal.xlsx")
        print("   📄 test_rapport_tia.xlsx")

        print("\n🚀 L'application est prête à l'emploi!")
        print("\nPour lancer l'interface web:")
        print("   streamlit run app.py")

        print("\n" + "="*70 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
