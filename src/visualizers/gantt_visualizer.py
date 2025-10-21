"""
Gantt Chart Visualizer for Schedules
"""
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

from ..utils.schedule_utils import Schedule, ScheduleActivity


class GanttVisualizer:
    """Create Gantt charts for schedule visualization"""

    def __init__(self):
        self.colors = {
            'critical': 'rgb(255, 65, 54)',      # Red
            'completed': 'rgb(99, 186, 100)',    # Green
            'in_progress': 'rgb(255, 185, 0)',   # Orange
            'not_started': 'rgb(66, 133, 244)',  # Blue
            'delayed': 'rgb(255, 0, 0)',         # Dark red
        }

    def create_gantt(self, schedule: Schedule, title: str = "Project Schedule",
                    show_critical_only: bool = False,
                    max_activities: int = 50) -> go.Figure:
        """
        Create a Gantt chart from schedule

        Args:
            schedule: Schedule object
            title: Chart title
            show_critical_only: Only show critical path activities
            max_activities: Maximum number of activities to show

        Returns:
            Plotly figure
        """
        activities = list(schedule.activities.values())

        # Filter critical only if requested
        if show_critical_only:
            activities = [a for a in activities if a.is_critical]

        # Sort by start date
        activities = sorted(
            activities,
            key=lambda x: x.start_date if x.start_date else datetime.max
        )

        # Limit number of activities
        if len(activities) > max_activities:
            activities = activities[:max_activities]

        # Prepare data for Gantt chart
        gantt_data = []

        for activity in activities:
            if not activity.start_date or not activity.finish_date:
                continue

            # Determine color
            if activity.is_critical:
                color = self.colors['critical']
            elif activity.is_finished:
                color = self.colors['completed']
            elif activity.is_started:
                color = self.colors['in_progress']
            else:
                color = self.colors['not_started']

            gantt_data.append(dict(
                Task=activity.name[:50] if len(activity.name) > 50 else activity.name,
                Start=activity.start_date,
                Finish=activity.finish_date,
                Resource=f"{'Critical' if activity.is_critical else 'Normal'}",
                Complete=activity.percent_complete,
                Color=color
            ))

        if not gantt_data:
            # Return empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No activities with valid dates to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create figure using graph_objects for more control
        fig = go.Figure()

        # Add bars for each activity
        for i, task in enumerate(gantt_data):
            # Calculate duration in milliseconds for Plotly
            duration_ms = (task['Finish'] - task['Start']).total_seconds() * 1000
            duration_days = (task['Finish'] - task['Start']).days

            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[task['Task']],
                base=task['Start'],
                orientation='h',
                marker=dict(color=task['Color']),
                name=task['Resource'],
                showlegend=(i == 0 or (i > 0 and task['Resource'] != gantt_data[i-1]['Resource'])),
                hovertemplate=(
                    f"<b>{task['Task']}</b><br>"
                    f"Start: {task['Start'].strftime('%Y-%m-%d')}<br>"
                    f"Finish: {task['Finish'].strftime('%Y-%m-%d')}<br>"
                    f"Duration: {duration_days} days<br>"
                    f"Progress: {task['Complete']:.0f}%<br>"
                    "<extra></extra>"
                )
            ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis=dict(
                title='Date',
                type='date'
            ),
            yaxis=dict(
                title='Activities',
                autorange='reversed'  # Reverse to show first activity at top
            ),
            barmode='overlay',
            height=max(400, len(gantt_data) * 25),
            showlegend=True,
            hovermode='closest'
        )

        return fig

    def create_comparison_gantt(self, baseline: Schedule, current: Schedule,
                               title: str = "Baseline vs Current Schedule") -> go.Figure:
        """
        Create comparison Gantt chart

        Args:
            baseline: Baseline schedule
            current: Current schedule
            title: Chart title

        Returns:
            Plotly figure
        """
        # Get common activities
        common_ids = set(baseline.activities.keys()) & set(current.activities.keys())

        data = []

        for act_id in common_ids:
            baseline_act = baseline.activities[act_id]
            current_act = current.activities[act_id]

            if not baseline_act.start_date or not baseline_act.finish_date:
                continue

            # Baseline bar
            data.append(dict(
                Task=f"{baseline_act.name} (Baseline)",
                Start=baseline_act.start_date,
                Finish=baseline_act.finish_date,
                Type='Baseline'
            ))

            # Current/actual bar
            if current_act.start_date and current_act.finish_date:
                data.append(dict(
                    Task=f"{current_act.name} (Current)",
                    Start=current_act.start_date,
                    Finish=current_act.finish_date,
                    Type='Current'
                ))

        if not data:
            fig = go.Figure()
            fig.add_annotation(
                text="No common activities to compare",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        df = pd.DataFrame(data)

        # Create figure
        fig = go.Figure()

        # Add baseline bars
        baseline_df = df[df['Type'] == 'Baseline']
        for idx, row in baseline_df.iterrows():
            # Calculate duration in milliseconds for Plotly
            duration_ms = (row['Finish'] - row['Start']).total_seconds() * 1000

            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[row['Task']],
                base=row['Start'],
                orientation='h',
                marker=dict(color='rgba(100, 100, 255, 0.5)'),
                name='Baseline',
                showlegend=bool(idx == baseline_df.index[0]),
                hovertemplate=(
                    f"<b>Baseline</b><br>"
                    f"{row['Task']}<br>"
                    f"Start: {row['Start'].strftime('%Y-%m-%d')}<br>"
                    f"Finish: {row['Finish'].strftime('%Y-%m-%d')}<br>"
                    "<extra></extra>"
                )
            ))

        # Add current bars
        current_df = df[df['Type'] == 'Current']
        for idx, row in current_df.iterrows():
            # Calculate duration in milliseconds for Plotly
            duration_ms = (row['Finish'] - row['Start']).total_seconds() * 1000

            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[row['Task']],
                base=row['Start'],
                orientation='h',
                marker=dict(color='rgba(255, 100, 100, 0.5)'),
                name='Current',
                showlegend=bool(idx == current_df.index[0]),
                hovertemplate=(
                    f"<b>Current</b><br>"
                    f"{row['Task']}<br>"
                    f"Start: {row['Start'].strftime('%Y-%m-%d')}<br>"
                    f"Finish: {row['Finish'].strftime('%Y-%m-%d')}<br>"
                    "<extra></extra>"
                )
            ))

        fig.update_layout(
            title=title,
            xaxis=dict(title='Date', type='date'),
            yaxis=dict(title='Activities', autorange='reversed'),
            barmode='overlay',
            height=max(400, len(data) * 15),
            showlegend=True
        )

        return fig

    def create_critical_path_viz(self, schedule: Schedule,
                                title: str = "Critical Path") -> go.Figure:
        """
        Create critical path visualization

        Args:
            schedule: Schedule object
            title: Chart title

        Returns:
            Plotly figure
        """
        critical_path = schedule.get_critical_path()

        if not critical_path:
            fig = go.Figure()
            fig.add_annotation(
                text="No critical path found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Get critical activities
        critical_activities = [
            schedule.activities[act_id]
            for act_id in critical_path
            if act_id in schedule.activities
        ]

        # Sort by start date
        critical_activities = sorted(
            critical_activities,
            key=lambda x: x.start_date if x.start_date else datetime.max
        )

        gantt_data = []

        for activity in critical_activities:
            if not activity.start_date or not activity.finish_date:
                continue

            gantt_data.append(dict(
                Task=activity.name,
                Start=activity.start_date,
                Finish=activity.finish_date,
                Float=activity.total_float if activity.total_float else 0
            ))

        if not gantt_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No valid critical activities to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Create figure
        fig = go.Figure()

        for task in gantt_data:
            # Calculate duration in milliseconds for Plotly
            duration_ms = (task['Finish'] - task['Start']).total_seconds() * 1000

            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[task['Task']],
                base=task['Start'],
                orientation='h',
                marker=dict(color=self.colors['critical']),
                name='Critical',
                showlegend=False,
                hovertemplate=(
                    f"<b>{task['Task']}</b><br>"
                    f"Start: {task['Start'].strftime('%Y-%m-%d')}<br>"
                    f"Finish: {task['Finish'].strftime('%Y-%m-%d')}<br>"
                    f"Float: {task['Float']:.1f} days<br>"
                    "<extra></extra>"
                )
            ))

        fig.update_layout(
            title=title,
            xaxis=dict(title='Date', type='date'),
            yaxis=dict(title='Critical Activities', autorange='reversed'),
            height=max(400, len(gantt_data) * 30),
        )

        return fig

    def create_delay_timeline(self, delays: List[Dict],
                            title: str = "Delay Timeline") -> go.Figure:
        """
        Create timeline visualization of delays

        Args:
            delays: List of delay dictionaries with dates and magnitudes
            title: Chart title

        Returns:
            Plotly figure
        """
        if not delays:
            fig = go.Figure()
            fig.add_annotation(
                text="No delays to visualize",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Sort by date
        delays_with_dates = [d for d in delays if 'event_date' in d or 'window_start' in d]
        delays_with_dates = sorted(
            delays_with_dates,
            key=lambda x: x.get('event_date') or x.get('window_start') or datetime.min
        )

        fig = go.Figure()

        # Create scatter plot for delay events
        dates = []
        magnitudes = []
        labels = []

        for delay in delays_with_dates:
            date = delay.get('event_date') or delay.get('window_start')
            if date:
                dates.append(date)
                magnitudes.append(delay.get('delay_days', 0))
                labels.append(delay.get('activity_name', 'Unknown'))

        fig.add_trace(go.Scatter(
            x=dates,
            y=magnitudes,
            mode='markers+lines',
            marker=dict(
                size=[min(50, max(10, d)) for d in magnitudes],
                color=magnitudes,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Delay (days)")
            ),
            text=labels,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Date: %{x}<br>"
                "Delay: %{y:.1f} days<br>"
                "<extra></extra>"
            )
        ))

        fig.update_layout(
            title=title,
            xaxis=dict(title='Date'),
            yaxis=dict(title='Delay (days)'),
            height=500,
            showlegend=False
        )

        return fig


def create_schedule_gantt(schedule: Schedule, **kwargs) -> go.Figure:
    """
    Convenience function to create Gantt chart

    Args:
        schedule: Schedule object
        **kwargs: Additional arguments for GanttVisualizer.create_gantt()

    Returns:
        Plotly figure
    """
    viz = GanttVisualizer()
    return viz.create_gantt(schedule, **kwargs)
