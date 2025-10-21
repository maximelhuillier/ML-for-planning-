"""
As-Planned vs As-Built Analysis Method
Compares the original baseline schedule with the actual progress
"""
from typing import Dict, Any
import pandas as pd
from datetime import datetime

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule


@DelayAnalyzerFactory.register
class AsPlannedVsAsBuiltAnalyzer(BaseDelayAnalyzer):
    """
    As-Planned vs As-Built analysis compares the baseline schedule
    with actual performance to identify delays
    """

    def __init__(self):
        super().__init__(
            name="As-Planned vs As-Built",
            description="Compares the baseline (as-planned) schedule with actual progress (as-built) to identify delays and their magnitude"
        )
        self.required_inputs = ['baseline_schedule', 'current_schedule']
        self.optional_inputs = ['analysis_date', 'include_non_critical']

        self.questions = [
            {
                'question': 'Do you want to include non-critical activities in the analysis?',
                'key': 'include_non_critical',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'Yes',
                'help': 'Including non-critical activities provides more detail but may dilute focus on critical delays'
            },
            {
                'question': 'What date should be used for the analysis?',
                'key': 'analysis_date',
                'type': 'date',
                'default': None,
                'help': 'Leave blank to use the current date'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform As-Planned vs As-Built analysis

        Required kwargs:
            baseline_schedule: Schedule - The original baseline schedule
            current_schedule: Schedule - The current/actual schedule

        Optional kwargs:
            analysis_date: datetime - Date for analysis (default: now)
            include_non_critical: bool - Include non-critical activities

        Returns:
            DelayAnalysisResult
        """
        # Validate inputs
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        baseline: Schedule = kwargs['baseline_schedule']
        current: Schedule = kwargs['current_schedule']
        analysis_date = kwargs.get('analysis_date', datetime.now())
        include_non_critical = kwargs.get('include_non_critical', True)

        # Create result object
        result = DelayAnalysisResult(self.name)
        result.metadata['analysis_date'] = analysis_date
        result.metadata['baseline_project'] = baseline.project_name
        result.metadata['current_project'] = current.project_name

        # Compare schedules
        comparison_df = self._compare_schedules(baseline, current)

        # Analyze delays
        total_delay = 0
        critical_delay = 0

        for _, row in comparison_df.iterrows():
            activity_id = row['activity_id']

            # Get baseline and current activities
            baseline_act = baseline.activities.get(activity_id)
            current_act = current.activities.get(activity_id)

            if not baseline_act or not current_act:
                continue

            # Skip non-critical if requested
            if not include_non_critical and not baseline_act.is_critical:
                continue

            # Calculate finish date delay
            delay_days = 0
            if baseline_act.finish_date and current_act.finish_date:
                delay_days = self._calculate_delay(
                    baseline_act.finish_date,
                    current_act.finish_date
                )
            elif baseline_act.finish_date and current_act.actual_finish:
                delay_days = self._calculate_delay(
                    baseline_act.finish_date,
                    current_act.actual_finish
                )

            if delay_days > 0:
                # Determine cause (simplified - could be enhanced)
                cause = self._determine_delay_cause(baseline_act, current_act)

                result.add_activity_delay(
                    activity_id=activity_id,
                    activity_name=current_act.name,
                    delay_days=delay_days,
                    cause=cause,
                    is_critical=baseline_act.is_critical,
                    baseline_finish=baseline_act.finish_date,
                    actual_finish=current_act.actual_finish or current_act.finish_date,
                    baseline_duration=baseline_act.duration,
                    actual_duration=current_act.duration
                )

                total_delay += delay_days
                if baseline_act.is_critical:
                    critical_delay += delay_days

        result.total_delay_days = total_delay
        result.critical_delay_days = critical_delay

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, baseline, current)

        # Create summary
        result.summary = self._create_summary(result)

        # Create detailed report DataFrame
        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> list:
        """Get suggestions based on inputs"""
        suggestions = []

        if 'baseline_schedule' in kwargs and 'current_schedule' in kwargs:
            baseline = kwargs['baseline_schedule']
            current = kwargs['current_schedule']

            baseline_critical = len([a for a in baseline.activities.values() if a.is_critical])
            current_critical = len([a for a in current.activities.values() if a.is_critical])

            if current_critical > baseline_critical * 1.2:
                suggestions.append(
                    f"⚠️ Critical path has grown from {baseline_critical} to {current_critical} activities. "
                    "This suggests significant schedule pressure."
                )

            baseline_complete = baseline.get_summary_stats()['avg_completion']
            current_complete = current.get_summary_stats()['avg_completion']

            if current_complete < baseline_complete:
                suggestions.append(
                    "📊 Project is behind schedule in terms of completion percentage. "
                    "Consider focusing on critical path acceleration."
                )

            delayed = current.get_delayed_activities()
            if len(delayed) > len(current.activities) * 0.3:
                suggestions.append(
                    f"🔴 {len(delayed)} activities ({len(delayed)/len(current.activities)*100:.1f}%) are delayed. "
                    "Consider reviewing resource allocation and potential bottlenecks."
                )

        return suggestions

    def _determine_delay_cause(self, baseline_act, current_act) -> str:
        """Determine likely cause of delay (simplified)"""
        # Check if duration increased
        if current_act.duration > baseline_act.duration * 1.1:
            return "Productivity Loss"

        # Check if start was delayed
        if baseline_act.start_date and current_act.actual_start:
            if current_act.actual_start > baseline_act.start_date:
                return "Late Start"

        # Check if percent complete is low
        if current_act.percent_complete < 50:
            return "Slow Progress"

        return "General Delay"

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                 baseline: Schedule, current: Schedule) -> list:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Critical path delays
        if result.critical_delay_days > 0:
            recommendations.append(
                f"Focus on critical path: {result.critical_delay_days:.1f} days of delay on critical activities"
            )

        # Top delay causes
        if result.delays_by_cause:
            top_cause = max(result.delays_by_cause.items(), key=lambda x: x[1])
            recommendations.append(
                f"Address '{top_cause[0]}' which accounts for {top_cause[1]:.1f} days of delay"
            )

        # Most delayed activities
        if result.delays_by_activity:
            sorted_delays = sorted(result.delays_by_activity,
                                 key=lambda x: x['delay_days'], reverse=True)[:3]
            recommendations.append(
                "Prioritize recovery for most delayed activities: " +
                ", ".join([f"{d['activity_name']} ({d['delay_days']:.1f}d)"
                          for d in sorted_delays])
            )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult) -> str:
        """Create summary text"""
        summary = f"""
As-Planned vs As-Built Analysis Summary:

Total Delay: {result.total_delay_days:.1f} days
Critical Path Delay: {result.critical_delay_days:.1f} days
Affected Activities: {len(result.delays_by_activity)}

Top Delay Causes:
"""
        for cause, days in sorted(result.delays_by_cause.items(),
                                 key=lambda x: x[1], reverse=True)[:5]:
            summary += f"  - {cause}: {days:.1f} days\n"

        return summary
