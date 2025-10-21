"""
Schedule Delay Analysis Application
Interactive web application for construction schedule delay analysis
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import tempfile
import os

# Import analyzers
from src.analyzers import (
    get_available_methods,
    create_analyzer,
    DelayAnalysisResult
)

# Import parsers
from src.parsers.p6_parser import P6Parser, parse_xer_file
from src.parsers.msp_parser import MSProjectParser, parse_msp_file

# Import utilities
from src.utils.schedule_utils import Schedule

# Import exporters and visualizers
from src.exporters.excel_exporter import ExcelExporter
from src.visualizers.gantt_visualizer import GanttVisualizer

# Page configuration
st.set_page_config(
    page_title="Schedule Delay Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'baseline_schedule' not in st.session_state:
        st.session_state.baseline_schedule = None
    if 'current_schedule' not in st.session_state:
        st.session_state.current_schedule = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'schedule_updates' not in st.session_state:
        st.session_state.schedule_updates = {}


def parse_uploaded_file(uploaded_file, file_type: str) -> Schedule:
    """Parse uploaded schedule file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        if file_type == 'xer':
            parser = P6Parser()
            schedule = parser.parse(tmp_path)
        else:  # xml or mpp
            parser = MSProjectParser()
            schedule = parser.parse(tmp_path)

        return schedule
    finally:
        os.unlink(tmp_path)


def display_schedule_summary(schedule: Schedule, title: str):
    """Display schedule summary"""
    st.markdown(f'<div class="sub-header">{title}</div>', unsafe_allow_html=True)

    stats = schedule.get_summary_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Activities", stats['total_activities'])
    with col2:
        st.metric("Critical Activities", stats['critical_activities'])
    with col3:
        st.metric("Completed", stats['completed_activities'])
    with col4:
        st.metric("Avg Completion", f"{stats['avg_completion']:.1f}%")

    # Additional info
    if stats['project_start'] and stats['project_finish']:
        duration = (stats['project_finish'] - stats['project_start']).days
        st.info(f"📅 Project Duration: {duration} days "
               f"({stats['project_start'].strftime('%Y-%m-%d')} to "
               f"{stats['project_finish'].strftime('%Y-%m-%d')})")


def main():
    """Main application"""
    init_session_state()

    # Header
    st.markdown('<div class="main-header">📊 Schedule Delay Analysis</div>',
               unsafe_allow_html=True)
    st.markdown("**Analyse les retards de planning avec 6 méthodes professionnelles**")

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Delay+Analysis",
                use_column_width=True)

        st.markdown("### 📂 Navigation")
        page = st.radio(
            "Sélectionnez une page:",
            ["🏠 Accueil", "📁 Upload Fichiers", "📊 Analyse", "📈 Visualisations", "💾 Export"]
        )

        st.markdown("---")
        st.markdown("### ℹ️ À propos")
        st.markdown("""
        Cette application permet d'analyser les retards de planning avec 6 méthodes:
        - As-Planned vs As-Built
        - Impacted As-Planned
        - Collapsed As-Built
        - Time Impact Analysis
        - Windows Analysis
        - Contemporaneous Analysis
        """)

    # Main content
    if page == "🏠 Accueil":
        show_home_page()
    elif page == "📁 Upload Fichiers":
        show_upload_page()
    elif page == "📊 Analyse":
        show_analysis_page()
    elif page == "📈 Visualisations":
        show_visualizations_page()
    elif page == "💾 Export":
        show_export_page()


def show_home_page():
    """Show home page"""
    st.markdown('<div class="sub-header">Bienvenue</div>', unsafe_allow_html=True)

    st.markdown("""
    ### Comment utiliser cette application

    1. **Upload Fichiers** : Importez vos fichiers de planning (.xer ou .xml/.mpp)
    2. **Analyse** : Choisissez une méthode d'analyse parmi les 6 disponibles
    3. **Visualisations** : Consultez les diagrammes de Gantt et analyses
    4. **Export** : Exportez les résultats en Excel

    ### Méthodes d'analyse disponibles
    """)

    methods = get_available_methods()

    for i, method in enumerate(methods, 1):
        with st.expander(f"{i}. {method['name']}"):
            st.write(method['description'])

    st.markdown('<div class="info-box">💡 Commencez par uploader vos fichiers de planning dans l\'onglet "Upload Fichiers"</div>',
               unsafe_allow_html=True)


def show_upload_page():
    """Show file upload page"""
    st.markdown('<div class="sub-header">Upload de Fichiers</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Planning Baseline", "📋 Planning Actuel"])

    with tab1:
        st.markdown("#### Upload du planning baseline (as-planned)")

        baseline_file = st.file_uploader(
            "Sélectionnez un fichier .xer (P6) ou .xml (MS Project)",
            type=['xer', 'xml'],
            key='baseline_upload'
        )

        if baseline_file:
            file_type = baseline_file.name.split('.')[-1].lower()

            with st.spinner("Parsing du fichier..."):
                try:
                    schedule = parse_uploaded_file(baseline_file, file_type)
                    st.session_state.baseline_schedule = schedule

                    st.markdown('<div class="success-box">✓ Fichier parsé avec succès!</div>',
                               unsafe_allow_html=True)

                    display_schedule_summary(schedule, "Résumé du Planning Baseline")

                    # Show sample activities
                    if st.checkbox("Afficher les activités", key='show_baseline_activities'):
                        df = schedule.to_dataframe()
                        st.dataframe(df.head(20))

                except Exception as e:
                    st.error(f"Erreur lors du parsing: {str(e)}")

    with tab2:
        st.markdown("#### Upload du planning actuel (as-built)")

        current_file = st.file_uploader(
            "Sélectionnez un fichier .xer (P6) ou .xml (MS Project)",
            type=['xer', 'xml'],
            key='current_upload'
        )

        if current_file:
            file_type = current_file.name.split('.')[-1].lower()

            with st.spinner("Parsing du fichier..."):
                try:
                    schedule = parse_uploaded_file(current_file, file_type)
                    st.session_state.current_schedule = schedule

                    st.markdown('<div class="success-box">✓ Fichier parsé avec succès!</div>',
                               unsafe_allow_html=True)

                    display_schedule_summary(schedule, "Résumé du Planning Actuel")

                    if st.checkbox("Afficher les activités", key='show_current_activities'):
                        df = schedule.to_dataframe()
                        st.dataframe(df.head(20))

                except Exception as e:
                    st.error(f"Erreur lors du parsing: {str(e)}")


def show_analysis_page():
    """Show analysis page"""
    st.markdown('<div class="sub-header">Analyse de Retards</div>', unsafe_allow_html=True)

    # Check if schedules are uploaded
    if not st.session_state.baseline_schedule:
        st.warning("⚠️ Veuillez d'abord uploader un planning baseline")
        return

    # Select analysis method
    methods = get_available_methods()
    method_names = [m['name'] for m in methods]

    selected_method = st.selectbox(
        "Choisissez une méthode d'analyse:",
        method_names,
        help="Sélectionnez la méthode d'analyse la plus appropriée pour votre cas"
    )

    # Show method description
    method_info = next(m for m in methods if m['name'] == selected_method)
    st.info(f"ℹ️ {method_info['description']}")

    # Create analyzer
    analyzer = create_analyzer(selected_method)

    # Get analyzer questions
    questions = analyzer.get_questions()

    st.markdown("#### Configuration de l'analyse")

    user_inputs = {
        'baseline_schedule': st.session_state.baseline_schedule,
    }

    # Handle method-specific inputs
    if selected_method == "As-Planned vs As-Built":
        if not st.session_state.current_schedule:
            st.warning("⚠️ Cette méthode requiert aussi un planning actuel")
            return
        user_inputs['current_schedule'] = st.session_state.current_schedule

    # Ask questions
    for question in questions:
        key = question['key']
        q_text = question['question']
        q_type = question['type']
        help_text = question.get('help', '')

        if q_type == 'select':
            value = st.selectbox(q_text, question['options'], help=help_text)
            user_inputs[key] = (value == 'Yes') if value in ['Yes', 'No'] else value

        elif q_type == 'number':
            value = st.number_input(q_text, value=question.get('default', 30), help=help_text)
            user_inputs[key] = value

        elif q_type == 'date':
            value = st.date_input(q_text, help=help_text)
            if value:
                user_inputs[key] = datetime.combine(value, datetime.min.time())

    # Get suggestions
    st.markdown("#### 💡 Suggestions")
    suggestions = analyzer.get_suggestions(**user_inputs)

    if suggestions:
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")
    else:
        st.info("Aucune suggestion pour le moment")

    # Run analysis
    if st.button("🚀 Lancer l'analyse", type="primary"):
        with st.spinner("Analyse en cours..."):
            try:
                result = analyzer.analyze(**user_inputs)
                st.session_state.analysis_result = result

                st.markdown('<div class="success-box">✓ Analyse terminée avec succès!</div>',
                           unsafe_allow_html=True)

                # Show summary
                st.markdown("### Résultats de l'analyse")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Retard Total", f"{result.total_delay_days:.1f} jours")
                with col2:
                    st.metric("Retard Critique", f"{result.critical_delay_days:.1f} jours")
                with col3:
                    st.metric("Activités Affectées", len(result.delays_by_activity))
                with col4:
                    critical_count = len([d for d in result.delays_by_activity if d['is_critical']])
                    st.metric("Activités Critiques", critical_count)

                # Show summary text
                with st.expander("📝 Résumé détaillé"):
                    st.text(result.summary)

                # Show recommendations
                if result.recommendations:
                    st.markdown("### 📋 Recommandations")
                    for i, rec in enumerate(result.recommendations, 1):
                        st.markdown(f"{i}. {rec}")

                # Show delays by cause
                if result.delays_by_cause:
                    st.markdown("### 📊 Retards par Cause")

                    cause_df = pd.DataFrame([
                        {'Cause': cause, 'Jours': days}
                        for cause, days in sorted(result.delays_by_cause.items(),
                                                 key=lambda x: x[1], reverse=True)
                    ])

                    st.bar_chart(cause_df.set_index('Cause'))

            except Exception as e:
                st.error(f"Erreur lors de l'analyse: {str(e)}")
                st.exception(e)


def show_visualizations_page():
    """Show visualizations page"""
    st.markdown('<div class="sub-header">Visualisations</div>', unsafe_allow_html=True)

    viz = GanttVisualizer()

    tab1, tab2, tab3 = st.tabs(["📊 Gantt Baseline", "📊 Gantt Actuel", "📊 Comparaison"])

    with tab1:
        if st.session_state.baseline_schedule:
            st.markdown("#### Diagramme de Gantt - Planning Baseline")

            show_critical = st.checkbox("Afficher uniquement le chemin critique",
                                       key='baseline_critical')
            max_act = st.slider("Nombre max d'activités", 10, 100, 50,
                               key='baseline_max')

            fig = viz.create_gantt(
                st.session_state.baseline_schedule,
                title="Planning Baseline",
                show_critical_only=show_critical,
                max_activities=max_act
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Veuillez d'abord uploader un planning baseline")

    with tab2:
        if st.session_state.current_schedule:
            st.markdown("#### Diagramme de Gantt - Planning Actuel")

            show_critical = st.checkbox("Afficher uniquement le chemin critique",
                                       key='current_critical')
            max_act = st.slider("Nombre max d'activités", 10, 100, 50,
                               key='current_max')

            fig = viz.create_gantt(
                st.session_state.current_schedule,
                title="Planning Actuel",
                show_critical_only=show_critical,
                max_activities=max_act
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Veuillez d'abord uploader un planning actuel")

    with tab3:
        if st.session_state.baseline_schedule and st.session_state.current_schedule:
            st.markdown("#### Comparaison Baseline vs Actuel")

            fig = viz.create_comparison_gantt(
                st.session_state.baseline_schedule,
                st.session_state.current_schedule
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Veuillez uploader à la fois le planning baseline et actuel")

    # Delay timeline
    if st.session_state.analysis_result:
        st.markdown("### ⏱️ Timeline des Retards")

        fig = viz.create_delay_timeline(
            st.session_state.analysis_result.delays_by_activity,
            title="Timeline des Retards"
        )

        st.plotly_chart(fig, use_container_width=True)


def show_export_page():
    """Show export page"""
    st.markdown('<div class="sub-header">Export des Résultats</div>', unsafe_allow_html=True)

    if not st.session_state.analysis_result:
        st.warning("⚠️ Veuillez d'abord effectuer une analyse")
        return

    result = st.session_state.analysis_result

    st.markdown("#### Options d'export")

    include_charts = st.checkbox("Inclure les graphiques", value=True)
    file_name = st.text_input("Nom du fichier", value="delay_analysis_report")

    if st.button("📥 Télécharger le rapport Excel", type="primary"):
        with st.spinner("Génération du rapport..."):
            try:
                exporter = ExcelExporter()
                excel_bytes = exporter.export_to_bytes(result, include_charts)

                st.download_button(
                    label="💾 Télécharger",
                    data=excel_bytes,
                    file_name=f"{file_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.success("✓ Rapport généré avec succès!")

            except Exception as e:
                st.error(f"Erreur lors de la génération: {str(e)}")

    # Preview
    if st.checkbox("Prévisualiser les données"):
        st.markdown("### Aperçu des retards")
        if not result.detailed_report.empty:
            st.dataframe(result.detailed_report)
        else:
            df = pd.DataFrame(result.delays_by_activity)
            st.dataframe(df)


if __name__ == "__main__":
    main()
