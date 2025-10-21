"""
Contemporaneous Period Analysis
Analyzes delays using contemporary project records and conditions
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta

from .base_analyzer import BaseDelayAnalyzer, DelayAnalysisResult, DelayAnalyzerFactory
from ..utils.schedule_utils import Schedule


@DelayAnalyzerFactory.register
class ContemporaneousAnalyzer(BaseDelayAnalyzer):
    """
    Contemporaneous Period Analysis uses contemporary project records,
    daily logs, and progress reports to analyze delays as they occurred
    """

    def __init__(self):
        super().__init__(
            name="Contemporaneous Period Analysis",
            description="Analyzes delays using contemporary project documentation, daily logs, and real-time records to understand delays as they occurred"
        )
        self.required_inputs = ['schedule_updates', 'period_start', 'period_end']
        self.optional_inputs = ['daily_logs', 'progress_reports', 'weather_data']

        self.questions = [
            {
                'question': 'Which period should be analyzed?',
                'key': 'analysis_period',
                'type': 'select',
                'options': ['Full Project', 'Specific Period', 'Claim Period'],
                'default': 'Full Project',
                'help': 'Contemporaneous analysis typically focuses on a specific time period'
            },
            {
                'question': 'Do you have daily progress logs?',
                'key': 'has_daily_logs',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'No',
                'help': 'Daily logs provide detailed contemporary evidence of delays and causes'
            },
            {
                'question': 'Are there external factors to consider (weather, strikes, etc.)?',
                'key': 'has_external_factors',
                'type': 'select',
                'options': ['Yes', 'No'],
                'default': 'No',
                'help': 'External factors may explain delays and affect responsibility'
            }
        ]

    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform Contemporaneous Period Analysis

        Required kwargs:
            schedule_updates: Dict[datetime, Schedule] - Contemporary schedule snapshots
            period_start: datetime - Analysis period start
            period_end: datetime - Analysis period end

        Optional kwargs:
            daily_logs: List[Dict] - Daily progress logs
            progress_reports: List[Dict] - Periodic progress reports
            weather_data: Dict[datetime, Dict] - Weather conditions

        Returns:
            DelayAnalysisResult
        """
        is_valid, error = self.validate_inputs(**kwargs)
        if not is_valid:
            raise ValueError(error)

        schedule_updates: Dict[datetime, Schedule] = kwargs['schedule_updates']
        period_start: datetime = kwargs['period_start']
        period_end: datetime = kwargs['period_end']
        daily_logs: List[Dict] = kwargs.get('daily_logs', [])
        progress_reports: List[Dict] = kwargs.get('progress_reports', [])
        weather_data: Dict[datetime, Dict] = kwargs.get('weather_data', {})

        result = DelayAnalysisResult(self.name)
        result.metadata['period_start'] = period_start
        result.metadata['period_end'] = period_end
        result.metadata['has_daily_logs'] = len(daily_logs) > 0
        result.metadata['has_weather_data'] = len(weather_data) > 0

        # Get schedules for period
        period_schedules = {
            date: sched for date, sched in schedule_updates.items()
            if period_start <= date <= period_end
        }

        if len(period_schedules) < 2:
            raise ValueError(
                "Need at least 2 schedule updates within the analysis period"
            )

        # Analyze based on contemporary records
        delays_by_date = {}
        total_delay = 0
        critical_delay = 0

        # Get first and last schedules in period
        sorted_dates = sorted(period_schedules.keys())
        start_schedule = period_schedules[sorted_dates[0]]
        end_schedule = period_schedules[sorted_dates[-1]]

        # Compare schedules and correlate with contemporary records
        for activity_id in end_schedule.activities:
            if activity_id not in start_schedule.activities:
                continue

            start_act = start_schedule.activities[activity_id]
            end_act = end_schedule.activities[activity_id]

            # Calculate delay during period
            delay_days = 0

            if start_act.finish_date and end_act.finish_date:
                delay_days = (end_act.finish_date - start_act.finish_date).days

            if delay_days > 0:
                # Determine cause from contemporary records
                cause = self._determine_cause_from_records(
                    activity_id, end_act, period_start, period_end,
                    daily_logs, progress_reports, weather_data
                )

                # Determine responsibility
                responsibility = self._determine_responsibility(
                    cause, end_act, weather_data
                )

                result.add_activity_delay(
                    activity_id=activity_id,
                    activity_name=end_act.name,
                    delay_days=delay_days,
                    cause=cause,
                    is_critical=end_act.is_critical,
                    responsibility=responsibility,
                    documented_in_logs=self._is_documented_in_logs(
                        activity_id, end_act.name, daily_logs
                    ),
                    start_status=f"{start_act.percent_complete}%",
                    end_status=f"{end_act.percent_complete}%"
                )

                total_delay += delay_days
                if end_act.is_critical:
                    critical_delay += delay_days

        result.total_delay_days = total_delay
        result.critical_delay_days = critical_delay

        # Analyze contemporary documentation quality
        result.metadata['documentation_score'] = self._assess_documentation_quality(
            daily_logs, progress_reports, period_start, period_end
        )

        # Generate recommendations
        result.recommendations = self._generate_recommendations(
            result, period_schedules, daily_logs, progress_reports
        )

        # Create summary
        result.summary = self._create_summary(result, period_start, period_end)

        result.detailed_report = pd.DataFrame(result.delays_by_activity)

        return result

    def get_suggestions(self, **kwargs) -> List[str]:
        """Get analysis suggestions"""
        suggestions = []

        period_start = kwargs.get('period_start')
        period_end = kwargs.get('period_end')

        if period_start and period_end:
            period_days = (period_end - period_start).days
            suggestions.append(
                f"Analysis period: {period_days} days. "
                f"Contemporaneous records for this period are crucial."
            )

        daily_logs = kwargs.get('daily_logs', [])
        if daily_logs:
            suggestions.append(
                f"✓ {len(daily_logs)} daily logs available. "
                "These provide strong contemporary evidence."
            )
        else:
            suggestions.append(
                "⚠️ No daily logs provided. Consider adding progress reports, "
                "meeting minutes, or RFIs for contemporary documentation."
            )

        weather_data = kwargs.get('weather_data', {})
        if weather_data:
            suggestions.append(
                f"✓ Weather data available for {len(weather_data)} days. "
                "This helps establish excusable delays."
            )

        schedule_updates = kwargs.get('schedule_updates', {})
        if schedule_updates and period_start and period_end:
            period_updates = [
                d for d in schedule_updates.keys()
                if period_start <= d <= period_end
            ]
            if len(period_updates) < 4:
                suggestions.append(
                    f"💡 Only {len(period_updates)} updates in analysis period. "
                    "More frequent updates improve contemporaneous analysis accuracy."
                )

        return suggestions

    def _determine_cause_from_records(self, activity_id: str, activity,
                                      period_start: datetime, period_end: datetime,
                                      daily_logs: List[Dict],
                                      progress_reports: List[Dict],
                                      weather_data: Dict) -> str:
        """
        Determine delay cause from contemporary records

        Args:
            activity_id: Activity ID
            activity: Activity object
            period_start: Period start
            period_end: Period end
            daily_logs: Daily logs
            progress_reports: Progress reports
            weather_data: Weather data

        Returns:
            Identified cause
        """
        # Check daily logs for mentions
        activity_name_lower = activity.name.lower()

        for log in daily_logs:
            log_date = log.get('date')
            if not log_date or not (period_start <= log_date <= period_end):
                continue

            log_text = str(log.get('notes', '')).lower()

            # Check for specific causes mentioned
            if activity_id.lower() in log_text or activity_name_lower in log_text:
                if any(word in log_text for word in ['weather', 'rain', 'storm', 'wind']):
                    return "Weather Delay"
                elif any(word in log_text for word in ['rfi', 'clarification', 'design']):
                    return "Design Issue"
                elif any(word in log_text for word in ['material', 'delivery', 'supplier']):
                    return "Material Delay"
                elif any(word in log_text for word in ['labor', 'crew', 'manpower']):
                    return "Labor Issue"
                elif any(word in log_text for word in ['change', 'variation', 'extra']):
                    return "Change Order"

        # Check weather data
        if weather_data:
            bad_weather_days = sum(
                1 for date, conditions in weather_data.items()
                if period_start <= date <= period_end
                and conditions.get('adverse', False)
            )
            if bad_weather_days > 3:
                return "Adverse Weather"

        # Check progress reports
        for report in progress_reports:
            report_date = report.get('date')
            if not report_date or not (period_start <= report_date <= period_end):
                continue

            issues = report.get('issues', [])
            for issue in issues:
                if activity_id in str(issue) or activity.name in str(issue):
                    return issue.get('type', 'Progress Issue')

        # Default
        return "Progress Delay"

    def _determine_responsibility(self, cause: str, activity, weather_data: Dict) -> str:
        """
        Determine responsibility for delay based on cause

        Args:
            cause: Delay cause
            activity: Activity object
            weather_data: Weather data

        Returns:
            Responsibility party
        """
        # Simplified responsibility matrix
        excusable_causes = [
            'Weather Delay', 'Adverse Weather', 'Force Majeure'
        ]

        owner_causes = [
            'Design Issue', 'Change Order', 'Late Information', 'RFI Delay'
        ]

        contractor_causes = [
            'Labor Issue', 'Progress Delay', 'Quality Issue', 'Rework'
        ]

        if cause in excusable_causes:
            return "Excusable (Neither Party)"
        elif cause in owner_causes:
            return "Owner"
        elif cause in contractor_causes:
            return "Contractor"
        else:
            return "To Be Determined"

    def _is_documented_in_logs(self, activity_id: str, activity_name: str,
                               daily_logs: List[Dict]) -> bool:
        """Check if delay is documented in daily logs"""
        activity_name_lower = activity_name.lower()

        for log in daily_logs:
            log_text = str(log.get('notes', '')).lower()
            if activity_id.lower() in log_text or activity_name_lower in log_text:
                return True

        return False

    def _assess_documentation_quality(self, daily_logs: List[Dict],
                                      progress_reports: List[Dict],
                                      period_start: datetime,
                                      period_end: datetime) -> float:
        """
        Assess quality of contemporary documentation

        Args:
            daily_logs: Daily logs
            progress_reports: Progress reports
            period_start: Period start
            period_end: Period end

        Returns:
            Score from 0-100
        """
        score = 0
        period_days = (period_end - period_start).days

        # Daily logs coverage
        if period_days > 0:
            log_coverage = min(100, (len(daily_logs) / period_days) * 100)
            score += log_coverage * 0.5

        # Progress reports
        expected_reports = max(1, period_days / 7)  # Weekly reports expected
        report_score = min(100, (len(progress_reports) / expected_reports) * 100)
        score += report_score * 0.3

        # Completeness (simplified - check if logs have key fields)
        if daily_logs:
            complete_logs = sum(
                1 for log in daily_logs
                if log.get('date') and log.get('notes')
            )
            completeness = (complete_logs / len(daily_logs)) * 100
            score += completeness * 0.2

        return min(100, score)

    def _generate_recommendations(self, result: DelayAnalysisResult,
                                  period_schedules: Dict[datetime, Schedule],
                                  daily_logs: List[Dict],
                                  progress_reports: List[Dict]) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        # Documentation quality
        doc_score = result.metadata.get('documentation_score', 0)
        if doc_score < 50:
            recommendations.append(
                f"⚠️ Documentation quality score: {doc_score:.0f}/100. "
                "Strengthen contemporary record-keeping for future analysis."
            )
        elif doc_score >= 80:
            recommendations.append(
                f"✓ Excellent documentation (score: {doc_score:.0f}/100). "
                "This provides strong evidence for delay claims."
            )

        # Responsibility analysis
        if result.delays_by_activity:
            responsibilities = {}
            for delay in result.delays_by_activity:
                resp = delay.get('responsibility', 'Unknown')
                responsibilities[resp] = responsibilities.get(resp, 0) + delay['delay_days']

            if responsibilities:
                main_resp = max(responsibilities.items(), key=lambda x: x[1])
                recommendations.append(
                    f"Primary responsibility: {main_resp[0]} ({main_resp[1]:.1f} days)"
                )

        # Documentation gaps
        undocumented = [
            d for d in result.delays_by_activity
            if not d.get('documented_in_logs', False)
        ]
        if undocumented:
            recommendations.append(
                f"{len(undocumented)} delays lack contemporary documentation. "
                "Review progress reports and meeting minutes for evidence."
            )

        return recommendations

    def _create_summary(self, result: DelayAnalysisResult,
                       period_start: datetime, period_end: datetime) -> str:
        """Create summary text"""
        summary = f"""
Contemporaneous Period Analysis Summary:

Analysis Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}
Total Delays: {result.total_delay_days:.1f} days
Critical Path Delays: {result.critical_delay_days:.1f} days
Documentation Quality: {result.metadata.get('documentation_score', 0):.0f}/100

Delays by Responsibility:
"""
        # Group by responsibility
        resp_totals = {}
        for delay in result.delays_by_activity:
            resp = delay.get('responsibility', 'Unknown')
            resp_totals[resp] = resp_totals.get(resp, 0) + delay['delay_days']

        for resp, days in sorted(resp_totals.items(), key=lambda x: x[1], reverse=True):
            summary += f"  - {resp}: {days:.1f} days\n"

        summary += "\nTop Delay Causes:\n"
        for cause, days in sorted(result.delays_by_cause.items(),
                                 key=lambda x: x[1], reverse=True)[:5]:
            summary += f"  - {cause}: {days:.1f} days\n"

        return summary
