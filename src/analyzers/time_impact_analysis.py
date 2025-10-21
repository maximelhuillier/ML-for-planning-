"""
Time Impact Analysis (TIA) Method
Inserts delays at specific points in time and measures forward impact
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import copy

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule


@DelayAnalyzerFactory.register
class TimeImpactAnalyzer(BaseDelayAnalyzer):
    """
    Time Impact Analysis inserts delay events into the contemporary schedule
    at the time they occurred and measures their forward impact
    """

    def __init__(self):
        super().__init__(
            name="Time Impact Analysis (TIA)",
            description="Measures the time impact of specific delay events by inserting them into the contemporary schedule and calculating forward impacts"
        )
        self.required_inputs = ['baseline_schedule', 'delay_events']
        self.optional_inputs = ['updated_schedules']

        self.questions = [
            {
                'question': 'Do you have schedule updates from different time periods?',
                'key': 'has_updates',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'No',
                'help': 'Schedule updates help show the contemporary conditions when delays occurred'
            },
            {
                'question': 'Should fragnet activities be added to show delay logic?',
                'key': 'add_fragnets',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'Yes',
                'help': 'Fragnets are small schedule fragments that represent the delay event logic'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform Time Impact Analysis

        Required kwargs:
            baseline_schedule: Schedule - Starting schedule
            delay_events: List[Dict] - Delay events with dates

        Optional kwargs:
            updated_schedules: Dict[datetime, Schedule] - Contemporary schedules

        Returns:
            DelayAnalysisResult
        """
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        baseline: Schedule = kwargs['baseline_schedule']
        delay_events: List[Dict] = kwargs['delay_events']
        updated_schedules: Dict[datetime, Schedule] = kwargs.get('updated_schedules', {})
        add_fragnets = kwargs.get('add_fragnets', True)

        result = DelayAnalysisResult(self.name)
        result.metadata['baseline_project'] = baseline.project_name

        # Sort events by date
        sorted_events = sorted(delay_events, key=lambda x: x.get('event_date', datetime.now()))

        # Analyze each delay event sequentially
        current_schedule = copy.deepcopy(baseline)
        cumulative_impact = 0

        for i, event in enumerate(sorted_events):
            activity_id = event['activity_id']
            delay_days = event['delay_days']
            event_date = event.get('event_date')
            cause = event.get('cause', 'Delay Event')

            # Use contemporary schedule if available
            if event_date and updated_schedules:
                contemporary = self._get_contemporary_schedule(event_date, updated_schedules)
                if contemporary:
                    current_schedule = copy.deepcopy(contemporary)

            # Measure impact before inserting delay
            before_finish = current_schedule.project_finish

            # Insert delay (with fragnet if requested)
            if add_fragnets:
                current_schedule = self._insert_delay_with_fragnet(
                    current_schedule, activity_id, delay_days, event_date
                )
            else:
                current_schedule = self._insert_delay_simple(
                    current_schedule, activity_id, delay_days
                )

            # Measure impact after inserting delay
            after_finish = current_schedule.project_finish

            # Calculate this event's impact
            if before_finish and after_finish:
                event_impact = (after_finish - before_finish).days
            else:
                event_impact = 0

            cumulative_impact += event_impact

            # Record delay
            activity = current_schedule.activities.get(activity_id)
            if activity:
                result.add_activity_delay(
                    activity_id=activity_id,
                    activity_name=activity.name,
                    delay_days=delay_days,
                    cause=cause,
                    is_critical=activity.is_critical,
                    event_date=event_date,
                    time_impact_days=event_impact,
                    cumulative_impact=cumulative_impact,
                    sequence_number=i + 1
                )

                if activity.is_critical and event_impact > 0:
                    result.critical_delay_days += event_impact

        result.total_delay_days = cumulative_impact

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, baseline, current_schedule)

        # Create summary
        result.summary = self._create_summary(result, baseline, current_schedule)

        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> List[str]:
        """Get analysis suggestions"""
        suggestions = []

        if 'delay_events' in kwargs:
            events = kwargs['delay_events']

            # Check if events have dates
            events_with_dates = [e for e in events if e.get('event_date')]
            if len(events_with_dates) < len(events):
                suggestions.append(
                    f"⚠️ {len(events) - len(events_with_dates)} events missing dates. "
                    "Event dates are crucial for TIA accuracy."
                )

            # Check for concurrent events
            if len(events) > 1:
                dates = [e.get('event_date') for e in events if e.get('event_date')]
                if len(dates) != len(set(dates)):
                    suggestions.append(
                        "📅 Multiple events on same dates detected. "
                        "Consider analyzing concurrent delays together."
                    )

        if 'updated_schedules' in kwargs:
            schedules = kwargs['updated_schedules']
            if schedules:
                suggestions.append(
                    f"✓ {len(schedules)} contemporary schedules available. "
                    "This improves TIA accuracy significantly."
                )
            else:
                suggestions.append(
                    "💡 Consider providing schedule updates from different time periods "
                    "to reflect contemporary conditions."
                )

        return suggestions

    def _get_contemporary_schedule(self, event_date: datetime,
                                   schedules: Dict[datetime, Schedule]) -> Schedule:
        """
        Find the contemporary schedule closest to event date

        Args:
            event_date: Date of delay event
            schedules: Dictionary of dated schedules

        Returns:
            Contemporary schedule or None
        """
        if not schedules:
            return None

        # Find closest schedule before or at event date
        valid_dates = [d for d in schedules.keys() if d <= event_date]
        if not valid_dates:
            return None

        closest_date = max(valid_dates)
        return schedules[closest_date]

    def _insert_delay_with_fragnet(self, schedule: Schedule, activity_id: str,
                                   delay_days: float, event_date: datetime = None) -> Schedule:
        """
        Insert delay using fragnet approach

        Args:
            schedule: Schedule to modify
            activity_id: Activity to delay
            delay_days: Days of delay
            event_date: When delay occurred

        Returns:
            Modified schedule
        """
        if activity_id not in schedule.activities:
            return schedule

        activity = schedule.activities[activity_id]

        # Create fragnet activity (simplified)
        fragnet_id = f"DELAY_{activity_id}_{event_date.strftime('%Y%m%d') if event_date else 'TIA'}"

        # Insert delay by extending activity
        if activity.finish_date:
            activity.finish_date = activity.finish_date + timedelta(days=delay_days)
        activity.duration += delay_days

        # Propagate forward
        self._forward_pass(schedule, activity_id)

        return schedule

    def _insert_delay_simple(self, schedule: Schedule, activity_id: str,
                            delay_days: float) -> Schedule:
        """
        Simple delay insertion without fragnet

        Args:
            schedule: Schedule to modify
            activity_id: Activity to delay
            delay_days: Days of delay

        Returns:
            Modified schedule
        """
        if activity_id not in schedule.activities:
            return schedule

        activity = schedule.activities[activity_id]

        # Extend activity duration and finish
        if activity.finish_date:
            activity.finish_date = activity.finish_date + timedelta(days=delay_days)
        activity.duration += delay_days

        # Update project finish
        self._forward_pass(schedule, activity_id)

        return schedule

    def _forward_pass(self, schedule: Schedule, start_activity_id: str):
        """
        Perform forward pass from starting activity

        Args:
            schedule: Schedule to update
            start_activity_id: Activity to start from
        """
        # Simplified forward pass
        visited = set()
        queue = [start_activity_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id not in schedule.activities:
                continue

            current = schedule.activities[current_id]

            # Update successors
            for succ_id in current.successors:
                if succ_id not in schedule.activities:
                    continue

                successor = schedule.activities[succ_id]

                # Update early dates based on predecessor
                if current.finish_date:
                    if not successor.start_date or successor.start_date < current.finish_date:
                        delay = (current.finish_date - successor.start_date).days if successor.start_date else 0
                        if delay > 0:
                            successor.start_date = current.finish_date
                            if successor.finish_date:
                                successor.finish_date = successor.finish_date + timedelta(days=delay)

                queue.append(succ_id)

        # Update project finish
        if schedule.activities:
            max_finish = max(
                (a.finish_date for a in schedule.activities.values()
                 if a.finish_date is not None),
                default=schedule.project_finish
            )
            schedule.project_finish = max_finish

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                  baseline: Schedule,
                                  final_schedule: Schedule) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        if result.total_delay_days > 0:
            recommendations.append(
                f"Cumulative time impact: {result.total_delay_days:.1f} days on project completion"
            )

        # Find events with disproportionate impact
        high_impact = [d for d in result.delays_by_activity
                      if d.get('time_impact_days', 0) > d['delay_days'] * 1.5]
        if high_impact:
            recommendations.append(
                f"{len(high_impact)} events had amplified impact due to critical path effects"
            )

        # Sequential analysis
        if len(result.delays_by_activity) > 1:
            recommendations.append(
                "Time impact varies by sequence. Earlier delays may have greater impact."
            )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult,
                       baseline: Schedule,
                       final_schedule: Schedule) -> str:
        """Create summary text"""
        baseline_finish = baseline.project_finish
        final_finish = final_schedule.project_finish

        summary = f"""
Time Impact Analysis Summary:

Delay Events Analyzed: {len(result.delays_by_activity)}
Cumulative Time Impact: {result.total_delay_days:.1f} days
Critical Path Impact: {result.critical_delay_days:.1f} days

Original Completion: {baseline_finish.strftime('%Y-%m-%d') if baseline_finish else 'Unknown'}
Final Completion: {final_finish.strftime('%Y-%m-%d') if final_finish else 'Unknown'}

Events by Impact:
"""
        sorted_delays = sorted(result.delays_by_activity,
                             key=lambda x: x.get('time_impact_days', 0),
                             reverse=True)[:5]

        for delay in sorted_delays:
            summary += f"  - {delay['activity_name']}: {delay.get('time_impact_days', 0):.1f} day impact\n"

        return summary
