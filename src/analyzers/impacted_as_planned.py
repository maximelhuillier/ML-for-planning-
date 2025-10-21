"""
Impacted As-Planned Analysis Method
Shows the effect of delay events on the original schedule
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import copy

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule, ScheduleActivity


@DelayAnalyzerFactory.register
class ImpactedAsPlannedAnalyzer(BaseDelayAnalyzer):
    """
    Impacted As-Planned analysis inserts delay events into the baseline
    to show their impact on the project completion
    """

    def __init__(self):
        super().__init__(
            name="Impacted As-Planned",
            description="Inserts specific delay events into the baseline schedule to demonstrate their impact on project completion"
        )
        self.required_inputs = ['baseline_schedule', 'delay_events']
        self.optional_inputs = ['recompute_logic']

        self.questions = [
            {
                'question': 'Should the schedule logic be recomputed after inserting delays?',
                'key': 'recompute_logic',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'Yes',
                'help': 'Recomputing allows the schedule to show realistic impacts of delays on successor activities'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform Impacted As-Planned analysis

        Required kwargs:
            baseline_schedule: Schedule - The original baseline schedule
            delay_events: List[Dict] - List of delay events with:
                - activity_id: str
                - delay_days: float
                - event_date: datetime
                - cause: str

        Optional kwargs:
            recompute_logic: bool - Recompute schedule logic

        Returns:
            DelayAnalysisResult
        """
        # Validate inputs
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        baseline: Schedule = kwargs['baseline_schedule']
        delay_events: List[Dict] = kwargs['delay_events']
        recompute_logic = kwargs.get('recompute_logic', True)

        # Create result object
        result = DelayAnalysisResult(self.name)
        result.metadata['baseline_project'] = baseline.project_name
        result.metadata['delay_events_count'] = len(delay_events)

        # Create impacted schedule (copy of baseline)
        impacted_schedule = self._create_impacted_schedule(baseline, delay_events)

        # Compare baseline with impacted
        baseline_finish = baseline.project_finish
        impacted_finish = impacted_schedule.project_finish

        if baseline_finish and impacted_finish:
            total_impact = (impacted_finish - baseline_finish).days
            result.total_delay_days = max(0, total_impact)

        # Analyze each delay event
        for event in delay_events:
            activity_id = event['activity_id']
            delay_days = event['delay_days']
            cause = event.get('cause', 'Delay Event')

            activity = baseline.activities.get(activity_id)
            if not activity:
                continue

            # Calculate impact on critical path
            is_on_critical = activity.is_critical
            impact_multiplier = self._calculate_impact_multiplier(
                activity, baseline, delay_days
            )

            result.add_activity_delay(
                activity_id=activity_id,
                activity_name=activity.name,
                delay_days=delay_days,
                cause=cause,
                is_critical=is_on_critical,
                event_date=event.get('event_date'),
                impact_multiplier=impact_multiplier,
                projected_impact=delay_days * impact_multiplier
            )

            if is_on_critical:
                result.critical_delay_days += delay_days

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, baseline, impacted_schedule)

        # Create summary
        result.summary = self._create_summary(result, baseline_finish, impacted_finish)

        # Create detailed report
        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> List[str]:
        """Get suggestions for delay events"""
        suggestions = []

        if 'baseline_schedule' in kwargs:
            baseline = kwargs['baseline_schedule']
            critical_activities = [a for a in baseline.activities.values() if a.is_critical]

            suggestions.append(
                f"💡 Critical path has {len(critical_activities)} activities. "
                "Delays to these will directly impact project completion."
            )

            # Suggest monitoring near-critical activities
            near_critical = [a for a in baseline.activities.values()
                           if 0 < a.total_float <= 5]
            if near_critical:
                suggestions.append(
                    f"⚠️ {len(near_critical)} activities have 5 or fewer days of float. "
                    "These could easily become critical if delayed."
                )

        if 'delay_events' in kwargs:
            events = kwargs['delay_events']
            if len(events) > 10:
                suggestions.append(
                    f"📊 {len(events)} delay events is quite high. "
                    "Consider grouping related events or focusing on the most significant ones."
                )

            total_delay = sum(e['delay_days'] for e in events)
            if total_delay > 30:
                suggestions.append(
                    f"🔴 Total delay of {total_delay:.1f} days may have compounding effects. "
                    "Review critical path carefully."
                )

        return suggestions

    def _create_impacted_schedule(self, baseline: Schedule,
                                  delay_events: List[Dict]) -> Schedule:
        """
        Create impacted schedule by inserting delay events

        Args:
            baseline: Baseline schedule
            delay_events: List of delay events

        Returns:
            Impacted schedule
        """
        # Deep copy baseline
        impacted = copy.deepcopy(baseline)

        # Apply each delay event
        for event in delay_events:
            activity_id = event['activity_id']
            delay_days = event['delay_days']

            if activity_id not in impacted.activities:
                continue

            activity = impacted.activities[activity_id]

            # Extend duration or delay start/finish
            if activity.start_date and activity.finish_date:
                activity.finish_date = activity.finish_date + timedelta(days=delay_days)
                activity.duration += delay_days

            # Update successors (simplified - full CPM would be more complex)
            self._propagate_delay(impacted, activity_id, delay_days)

        # Update project finish
        if impacted.activities:
            max_finish = max(
                (a.finish_date for a in impacted.activities.values()
                 if a.finish_date is not None),
                default=impacted.project_finish
            )
            impacted.project_finish = max_finish

        return impacted

    def _propagate_delay(self, schedule: Schedule, activity_id: str, delay_days: float):
        """
        Propagate delay to successor activities (simplified)

        Args:
            schedule: Schedule to update
            activity_id: ID of delayed activity
            delay_days: Days of delay
        """
        activity = schedule.activities[activity_id]

        for successor_id in activity.successors:
            if successor_id not in schedule.activities:
                continue

            successor = schedule.activities[successor_id]

            # Only propagate if successor starts after this activity finishes (FS relationship)
            if successor.start_date and activity.finish_date:
                if successor.start_date <= activity.finish_date:
                    successor.start_date = successor.start_date + timedelta(days=delay_days)
                    if successor.finish_date:
                        successor.finish_date = successor.finish_date + timedelta(days=delay_days)

                    # Recursively propagate (be careful of cycles)
                    self._propagate_delay(schedule, successor_id, delay_days)

    def _calculate_impact_multiplier(self, activity: ScheduleActivity,
                                     schedule: Schedule, delay_days: float) -> float:
        """
        Calculate impact multiplier (how delay affects project)

        Args:
            activity: Delayed activity
            schedule: Schedule
            delay_days: Days of delay

        Returns:
            Impact multiplier (1.0 = full impact on project)
        """
        if activity.is_critical:
            return 1.0  # Critical activities have 1:1 impact

        # Non-critical: impact depends on float
        if activity.total_float > delay_days:
            return 0.0  # No impact if delay absorbed by float

        # Partial impact
        impact = (delay_days - activity.total_float) / delay_days
        return max(0, min(1, impact))

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                  baseline: Schedule,
                                  impacted: Schedule) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        if result.total_delay_days > 0:
            recommendations.append(
                f"Project completion delayed by {result.total_delay_days:.1f} days due to inserted delay events"
            )

        # Identify events with highest impact
        high_impact = [d for d in result.delays_by_activity
                      if d.get('impact_multiplier', 0) >= 0.8]
        if high_impact:
            recommendations.append(
                f"{len(high_impact)} delay events have high impact (>80%). "
                "Prioritize mitigation for these activities."
            )

        # Suggest float monitoring
        recommendations.append(
            "Monitor activities with low float to prevent them from becoming critical"
        )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult,
                       baseline_finish, impacted_finish) -> str:
        """Create summary text"""
        summary = f"""
Impacted As-Planned Analysis Summary:

Delay Events Analyzed: {len(result.delays_by_activity)}
Total Project Impact: {result.total_delay_days:.1f} days
Critical Delays: {result.critical_delay_days:.1f} days

Original Completion: {baseline_finish.strftime('%Y-%m-%d') if baseline_finish else 'Unknown'}
Impacted Completion: {impacted_finish.strftime('%Y-%m-%d') if impacted_finish else 'Unknown'}

Delays by Cause:
"""
        for cause, days in sorted(result.delays_by_cause.items(),
                                 key=lambda x: x[1], reverse=True):
            summary += f"  - {cause}: {days:.1f} days\n"

        return summary
