"""
Collapsed As-Built (But-For) Analysis Method
Removes delay events from actual schedule to show "but-for" completion date
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import copy

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule


@DelayAnalyzerFactory.register
class CollapsedAsBuiltAnalyzer(BaseDelayAnalyzer):
    """
    Collapsed As-Built (But-For) analysis removes specific delay events
    from the actual schedule to determine when the project would have
    completed "but for" those delays
    """

    def __init__(self):
        super().__init__(
            name="Collapsed As-Built (But-For)",
            description="Removes specific delays from the actual schedule to show when the project would have completed without those delays"
        )
        self.required_inputs = ['as_built_schedule', 'delay_events']
        self.optional_inputs = ['baseline_schedule']

        self.questions = [
            {
                'question': 'Do you have a baseline schedule for comparison?',
                'key': 'has_baseline',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'No',
                'help': 'A baseline helps validate the collapsed schedule'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform Collapsed As-Built analysis

        Required kwargs:
            as_built_schedule: Schedule - The actual/as-built schedule
            delay_events: List[Dict] - Delay events to remove

        Optional kwargs:
            baseline_schedule: Schedule - Original baseline for comparison

        Returns:
            DelayAnalysisResult
        """
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        as_built: Schedule = kwargs['as_built_schedule']
        delay_events: List[Dict] = kwargs['delay_events']
        baseline: Schedule = kwargs.get('baseline_schedule')

        result = DelayAnalysisResult(self.name)
        result.metadata['as_built_project'] = as_built.project_name
        result.metadata['delay_events_removed'] = len(delay_events)

        # Create collapsed schedule by removing delays
        collapsed_schedule = self._create_collapsed_schedule(as_built, delay_events)

        # Calculate impact
        as_built_finish = as_built.project_finish
        collapsed_finish = collapsed_schedule.project_finish

        if as_built_finish and collapsed_finish:
            delay_responsibility = (as_built_finish - collapsed_finish).days
            result.total_delay_days = max(0, delay_responsibility)

        # Analyze each removed delay
        for event in delay_events:
            activity_id = event['activity_id']
            delay_days = event['delay_days']
            cause = event.get('cause', 'Excusable Delay')

            activity = as_built.activities.get(activity_id)
            if not activity:
                continue

            result.add_activity_delay(
                activity_id=activity_id,
                activity_name=activity.name,
                delay_days=delay_days,
                cause=cause,
                is_critical=activity.is_critical,
                original_finish=activity.finish_date,
                collapsed_finish=activity.finish_date - timedelta(days=delay_days) if activity.finish_date else None
            )

            if activity.is_critical:
                result.critical_delay_days += delay_days

        # Generate recommendations
        result.recommendations = self._generate_recommendations(
            result, as_built, collapsed_schedule, baseline
        )

        # Create summary
        result.summary = self._create_summary(result, as_built_finish, collapsed_finish, baseline)

        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> List[str]:
        """Get analysis suggestions"""
        suggestions = []

        if 'as_built_schedule' in kwargs and 'delay_events' in kwargs:
            as_built = kwargs['as_built_schedule']
            events = kwargs['delay_events']

            # Check if delays are substantial
            total_delay = sum(e['delay_days'] for e in events)
            project_duration = 0
            if as_built.project_start and as_built.project_finish:
                project_duration = (as_built.project_finish - as_built.project_start).days

            if project_duration > 0:
                delay_ratio = total_delay / project_duration
                if delay_ratio > 0.2:
                    suggestions.append(
                        f"⚠️ Removing {total_delay:.1f} days of delays ({delay_ratio*100:.1f}% of project duration). "
                        "Ensure all delays are properly documented and excusable."
                    )

            # Check critical path
            critical_delays = [e for e in events
                             if as_built.activities.get(e['activity_id'], None)
                             and as_built.activities[e['activity_id']].is_critical]

            if critical_delays:
                suggestions.append(
                    f"🔴 {len(critical_delays)} delays are on the critical path. "
                    "These will have direct impact on project completion."
                )

        if 'baseline_schedule' in kwargs:
            suggestions.append(
                "✓ Baseline available for comparison. This strengthens the analysis."
            )

        return suggestions

    def _create_collapsed_schedule(self, as_built: Schedule,
                                   delay_events: List[Dict]) -> Schedule:
        """
        Create collapsed schedule by removing delays

        Args:
            as_built: As-built schedule
            delay_events: Delays to remove

        Returns:
            Collapsed schedule
        """
        collapsed = copy.deepcopy(as_built)

        # Remove each delay event
        for event in delay_events:
            activity_id = event['activity_id']
            delay_days = event['delay_days']

            if activity_id not in collapsed.activities:
                continue

            activity = collapsed.activities[activity_id]

            # Remove delay by reducing duration/dates
            if activity.finish_date:
                activity.finish_date = activity.finish_date - timedelta(days=delay_days)

            if activity.duration >= delay_days:
                activity.duration -= delay_days

            # Pull in successors
            self._pull_in_successors(collapsed, activity_id, delay_days)

        # Update project finish
        if collapsed.activities:
            max_finish = max(
                (a.finish_date for a in collapsed.activities.values()
                 if a.finish_date is not None),
                default=collapsed.project_finish
            )
            collapsed.project_finish = max_finish

        return collapsed

    def _pull_in_successors(self, schedule: Schedule, activity_id: str, days: float):
        """
        Pull in successor activities after removing delay

        Args:
            schedule: Schedule to update
            activity_id: ID of activity with removed delay
            days: Days of delay removed
        """
        activity = schedule.activities[activity_id]

        for successor_id in activity.successors:
            if successor_id not in schedule.activities:
                continue

            successor = schedule.activities[successor_id]

            # Pull in dates
            if successor.start_date:
                successor.start_date = successor.start_date - timedelta(days=days)
            if successor.finish_date:
                successor.finish_date = successor.finish_date - timedelta(days=days)

            # Recursively pull in
            self._pull_in_successors(schedule, successor_id, days)

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                  as_built: Schedule,
                                  collapsed: Schedule,
                                  baseline: Schedule = None) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        if result.total_delay_days > 0:
            recommendations.append(
                f"Removed delays account for {result.total_delay_days:.1f} days of project delay"
            )

        if baseline and collapsed.project_finish and baseline.project_finish:
            remaining_delay = (collapsed.project_finish - baseline.project_finish).days
            if remaining_delay > 0:
                recommendations.append(
                    f"After removing excusable delays, {remaining_delay:.1f} days of delay remain. "
                    "Investigate other causes."
                )
            elif remaining_delay < 0:
                recommendations.append(
                    f"Collapsed schedule finishes {abs(remaining_delay):.1f} days before baseline. "
                    "Review delay event magnitudes."
                )

        # Analyze delay causes
        if result.delays_by_cause:
            recommendations.append(
                "Document each delay cause thoroughly for contractual/legal purposes"
            )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult,
                       as_built_finish, collapsed_finish, baseline) -> str:
        """Create summary text"""
        summary = f"""
Collapsed As-Built (But-For) Analysis Summary:

Delay Events Removed: {len(result.delays_by_activity)}
Total Delay Removed: {result.total_delay_days:.1f} days

As-Built Completion: {as_built_finish.strftime('%Y-%m-%d') if as_built_finish else 'Unknown'}
But-For Completion: {collapsed_finish.strftime('%Y-%m-%d') if collapsed_finish else 'Unknown'}
"""

        if baseline and baseline.project_finish:
            summary += f"Baseline Completion: {baseline.project_finish.strftime('%Y-%m-%d')}\n"

        summary += "\nDelays Removed by Cause:\n"
        for cause, days in sorted(result.delays_by_cause.items(),
                                 key=lambda x: x[1], reverse=True):
            summary += f"  - {cause}: {days:.1f} days\n"

        return summary
