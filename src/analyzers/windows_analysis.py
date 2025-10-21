"""
Windows Analysis Method
Divides project into time windows and analyzes delays in each window
"""
from typing import Dict, Any, List, Tuple
import pandas as pd
from datetime import datetime, timedelta
import copy

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule


@DelayAnalyzerFactory.register
class WindowsAnalyzer(BaseDelayAnalyzer):
    """
    Windows Analysis divides the project timeline into discrete windows
    and analyzes delays that occurred within each window
    """

    def __init__(self):
        super().__init__(
            name="Windows Analysis",
            description="Divides the project into time windows and analyzes delays and their causes within each window period"
        )
        self.required_inputs = ['schedule_updates']
        self.optional_inputs = ['window_size_days', 'custom_windows']

        self.questions = [
            {
                'question': 'How should windows be defined?',
                'key': 'window_method',
                'type': 'select',
                'options': ['Monthly', 'Fixed Duration', 'Custom Windows', 'Schedule Updates'],
                'default': 'Monthly',
                'help': 'Monthly windows use calendar months, Fixed Duration uses specified days'
            },
            {
                'question': 'If using Fixed Duration, how many days per window?',
                'key': 'window_size_days',
                'type': 'number',
                'default': 30,
                'help': 'Number of days for each analysis window (e.g., 30, 60, 90)'
            },
            {
                'question': 'Include activities completed in each window?',
                'key': 'include_completed',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'Yes',
                'help': 'Analyze both in-progress and completed activities within window'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform Windows Analysis

        Required kwargs:
            schedule_updates: Dict[datetime, Schedule] - Schedule snapshots at different dates

        Optional kwargs:
            window_size_days: int - Size of each window in days
            custom_windows: List[Tuple[datetime, datetime]] - Custom window boundaries

        Returns:
            DelayAnalysisResult
        """
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        schedule_updates: Dict[datetime, Schedule] = kwargs['schedule_updates']
        window_size_days = kwargs.get('window_size_days', 30)
        custom_windows = kwargs.get('custom_windows')
        window_method = kwargs.get('window_method', 'Monthly')
        include_completed = kwargs.get('include_completed', True)

        result = DelayAnalysisResult(self.name)

        # Create windows
        if custom_windows:
            windows = custom_windows
        elif window_method == 'Schedule Updates':
            windows = self._create_windows_from_updates(schedule_updates)
        elif window_method == 'Monthly':
            windows = self._create_monthly_windows(schedule_updates)
        else:  # Fixed Duration
            windows = self._create_fixed_windows(schedule_updates, window_size_days)

        result.metadata['window_count'] = len(windows)
        result.metadata['window_method'] = window_method

        # Analyze each window
        window_results = []
        total_delay = 0
        total_critical_delay = 0

        for i, (window_start, window_end) in enumerate(windows):
            window_result = self._analyze_window(
                schedule_updates, window_start, window_end, i + 1, include_completed
            )

            window_results.append(window_result)
            total_delay += window_result['total_delay']
            total_critical_delay += window_result['critical_delay']

            # Add to overall result
            for delay in window_result['delays']:
                result.add_activity_delay(
                    activity_id=delay['activity_id'],
                    activity_name=delay['activity_name'],
                    delay_days=delay['delay_days'],
                    cause=delay['cause'],
                    is_critical=delay['is_critical'],
                    window_number=i + 1,
                    window_start=window_start,
                    window_end=window_end
                )

        result.total_delay_days = total_delay
        result.critical_delay_days = total_critical_delay
        result.metadata['windows'] = window_results

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, window_results)

        # Create summary
        result.summary = self._create_summary(result, windows, window_results)

        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> List[str]:
        """Get analysis suggestions"""
        suggestions = []

        if 'schedule_updates' in kwargs:
            updates = kwargs['schedule_updates']

            if len(updates) < 2:
                suggestions.append(
                    "⚠️ Windows Analysis requires multiple schedule updates. "
                    "Minimum 2 recommended, 3+ for better insights."
                )
            elif len(updates) >= 6:
                suggestions.append(
                    f"✓ {len(updates)} schedule updates available. "
                    "Excellent data for comprehensive windows analysis."
                )

            # Check update frequency
            dates = sorted(updates.keys())
            if len(dates) >= 2:
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_interval = sum(intervals) / len(intervals)
                suggestions.append(
                    f"📅 Average {avg_interval:.0f} days between updates. "
                    f"Consider {avg_interval:.0f}-day windows for alignment."
                )

        window_method = kwargs.get('window_method', 'Monthly')
        if window_method == 'Monthly':
            suggestions.append(
                "💡 Monthly windows align with typical reporting periods, "
                "making it easier to correlate with project reports."
            )

        return suggestions

    def _create_monthly_windows(self, schedule_updates: Dict[datetime, Schedule]) -> List[Tuple[datetime, datetime]]:
        """Create monthly windows"""
        if not schedule_updates:
            return []

        dates = sorted(schedule_updates.keys())
        start_date = dates[0]
        end_date = dates[-1]

        windows = []
        current = datetime(start_date.year, start_date.month, 1)

        while current <= end_date:
            # Get last day of month
            if current.month == 12:
                next_month = datetime(current.year + 1, 1, 1)
            else:
                next_month = datetime(current.year, current.month + 1, 1)

            window_end = next_month - timedelta(days=1)
            windows.append((current, min(window_end, end_date)))

            current = next_month

        return windows

    def _create_fixed_windows(self, schedule_updates: Dict[datetime, Schedule],
                             days: int) -> List[Tuple[datetime, datetime]]:
        """Create fixed-duration windows"""
        if not schedule_updates:
            return []

        dates = sorted(schedule_updates.keys())
        start_date = dates[0]
        end_date = dates[-1]

        windows = []
        current = start_date

        while current <= end_date:
            window_end = min(current + timedelta(days=days-1), end_date)
            windows.append((current, window_end))
            current = window_end + timedelta(days=1)

        return windows

    def _create_windows_from_updates(self, schedule_updates: Dict[datetime, Schedule]) -> List[Tuple[datetime, datetime]]:
        """Create windows based on update dates"""
        dates = sorted(schedule_updates.keys())

        if len(dates) < 2:
            return []

        windows = []
        for i in range(len(dates) - 1):
            windows.append((dates[i], dates[i+1] - timedelta(days=1)))

        return windows

    def _analyze_window(self, schedule_updates: Dict[datetime, Schedule],
                       window_start: datetime, window_end: datetime,
                       window_number: int, include_completed: bool) -> Dict:
        """Analyze delays within a specific window"""

        # Get schedules at window boundaries
        dates = sorted(schedule_updates.keys())
        start_schedule = None
        end_schedule = None

        # Find closest schedules
        for date in dates:
            if date <= window_start:
                start_schedule = schedule_updates[date]
            if date <= window_end:
                end_schedule = schedule_updates[date]

        if not start_schedule or not end_schedule:
            return {
                'window_number': window_number,
                'window_start': window_start,
                'window_end': window_end,
                'total_delay': 0,
                'critical_delay': 0,
                'delays': []
            }

        # Compare schedules
        delays = []
        total_delay = 0
        critical_delay = 0

        for activity_id in end_schedule.activities:
            if activity_id not in start_schedule.activities:
                continue

            start_act = start_schedule.activities[activity_id]
            end_act = end_schedule.activities[activity_id]

            # Check if activity was active in window
            if not include_completed and end_act.is_finished:
                continue

            # Calculate delay in this window
            delay_days = 0

            if start_act.finish_date and end_act.finish_date:
                delay_days = (end_act.finish_date - start_act.finish_date).days

            if delay_days > 0:
                cause = self._determine_window_cause(start_act, end_act, window_start, window_end)

                delays.append({
                    'activity_id': activity_id,
                    'activity_name': end_act.name,
                    'delay_days': delay_days,
                    'cause': cause,
                    'is_critical': end_act.is_critical
                })

                total_delay += delay_days
                if end_act.is_critical:
                    critical_delay += delay_days

        return {
            'window_number': window_number,
            'window_start': window_start,
            'window_end': window_end,
            'total_delay': total_delay,
            'critical_delay': critical_delay,
            'delays': delays,
            'activities_delayed': len(delays)
        }

    def _determine_window_cause(self, start_act, end_act,
                               window_start: datetime, window_end: datetime) -> str:
        """Determine cause of delay within window"""
        # Simplified cause determination
        if end_act.percent_complete < start_act.percent_complete + 10:
            return "Slow Progress"

        if end_act.duration > start_act.duration:
            return "Duration Extension"

        return "Schedule Slip"

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                  window_results: List[Dict]) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        # Find worst windows
        sorted_windows = sorted(window_results, key=lambda x: x['total_delay'], reverse=True)

        if sorted_windows and sorted_windows[0]['total_delay'] > 0:
            worst = sorted_windows[0]
            recommendations.append(
                f"Window {worst['window_number']} ({worst['window_start'].strftime('%Y-%m-%d')} to "
                f"{worst['window_end'].strftime('%Y-%m-%d')}) had highest delay: {worst['total_delay']:.1f} days"
            )

        # Identify trends
        if len(window_results) >= 3:
            recent_delays = [w['total_delay'] for w in window_results[-3:]]
            if all(recent_delays[i] > recent_delays[i-1] for i in range(1, len(recent_delays))):
                recommendations.append(
                    "⚠️ Delays are increasing in recent windows. Immediate action recommended."
                )

        # Critical path analysis
        critical_pct = (result.critical_delay_days / result.total_delay_days * 100
                       if result.total_delay_days > 0 else 0)
        if critical_pct > 70:
            recommendations.append(
                f"{critical_pct:.1f}% of delays affect critical path. Focus recovery efforts here."
            )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult,
                       windows: List[Tuple[datetime, datetime]],
                       window_results: List[Dict]) -> str:
        """Create summary text"""
        summary = f"""
Windows Analysis Summary:

Analysis Period: {windows[0][0].strftime('%Y-%m-%d')} to {windows[-1][1].strftime('%Y-%m-%d')}
Number of Windows: {len(windows)}
Total Delay Identified: {result.total_delay_days:.1f} days
Critical Path Delay: {result.critical_delay_days:.1f} days

Window Breakdown:
"""
        for window_result in window_results:
            summary += f"\nWindow {window_result['window_number']}: "
            summary += f"{window_result['window_start'].strftime('%Y-%m-%d')} to {window_result['window_end'].strftime('%Y-%m-%d')}\n"
            summary += f"  Delay: {window_result['total_delay']:.1f} days "
            summary += f"({window_result['activities_delayed']} activities)\n"

        return summary
