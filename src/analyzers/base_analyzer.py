"""
Base class for delay analysis methods
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from ..utils.schedule_utils import Schedule, ScheduleActivity


class DelayAnalysisResult:
    """Container for delay analysis results"""

    def __init__(self, method_name: str):
        self.method_name = method_name
        self.analysis_date = datetime.now()
        self.total_delay_days = 0
        self.critical_delay_days = 0
        self.delays_by_activity: List[Dict] = []
        self.delays_by_cause: Dict[str, float] = {}
        self.critical_path_changes: List[Dict] = []
        self.recommendations: List[str] = []
        self.summary: str = ""
        self.detailed_report: pd.DataFrame = pd.DataFrame()
        self.metadata: Dict[str, Any] = {}

    def add_activity_delay(self, activity_id: str, activity_name: str,
                          delay_days: float, cause: str = "Unknown",
                          is_critical: bool = False, **kwargs):
        """Add delay for a specific activity"""
        delay_info = {
            'activity_id': activity_id,
            'activity_name': activity_name,
            'delay_days': delay_days,
            'cause': cause,
            'is_critical': is_critical,
            **kwargs
        }
        self.delays_by_activity.append(delay_info)

        # Update cause totals
        if cause not in self.delays_by_cause:
            self.delays_by_cause[cause] = 0
        self.delays_by_cause[cause] += delay_days

    def add_recommendation(self, recommendation: str):
        """Add a recommendation"""
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'method_name': self.method_name,
            'analysis_date': self.analysis_date,
            'total_delay_days': self.total_delay_days,
            'critical_delay_days': self.critical_delay_days,
            'delays_by_activity': self.delays_by_activity,
            'delays_by_cause': self.delays_by_cause,
            'critical_path_changes': self.critical_path_changes,
            'recommendations': self.recommendations,
            'summary': self.summary,
            'metadata': self.metadata
        }

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        return {
            'method': self.method_name,
            'total_delay': f"{self.total_delay_days:.1f} days",
            'critical_delay': f"{self.critical_delay_days:.1f} days",
            'affected_activities': len(self.delays_by_activity),
            'critical_activities': len([d for d in self.delays_by_activity if d['is_critical']]),
            'main_causes': dict(sorted(self.delays_by_cause.items(),
                                     key=lambda x: x[1], reverse=True)[:5])
        }


class BaseDelayAnalyzer(ABC):
    """Base class for delay analysis methods"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.required_inputs: List[str] = []
        self.optional_inputs: List[str] = []
        self.questions: List[Dict[str, Any]] = []

    @abstractmethod
    def analyze(self, **kwargs) -> DelayAnalysisResult:
        """
        Perform delay analysis

        Returns:
            DelayAnalysisResult object
        """
        pass

    def get_questions(self) -> List[Dict[str, Any]]:
        """
        Get questions to ask user before analysis

        Returns:
            List of question dictionaries with:
            - question: str (the question text)
            - key: str (parameter key)
            - type: str (input type: text, date, select, multiselect, number)
            - options: List[str] (for select/multiselect)
            - default: Any (default value)
            - help: str (help text)
        """
        return self.questions

    def get_suggestions(self, **kwargs) -> List[str]:
        """
        Get suggestions based on current inputs

        Returns:
            List of suggestion strings
        """
        return []

    def validate_inputs(self, **kwargs) -> tuple[bool, str]:
        """
        Validate required inputs

        Returns:
            Tuple of (is_valid, error_message)
        """
        for required in self.required_inputs:
            if required not in kwargs or kwargs[required] is None:
                return False, f"Missing required input: {required}"

        return True, ""

    def _calculate_delay(self, planned_date: datetime, actual_date: datetime) -> float:
        """
        Calculate delay in days between planned and actual dates

        Args:
            planned_date: Planned date
            actual_date: Actual date

        Returns:
            Delay in days (positive = delay, negative = early)
        """
        if not planned_date or not actual_date:
            return 0.0

        return (actual_date - planned_date).days

    def _identify_critical_path(self, schedule: Schedule) -> List[str]:
        """
        Identify critical path activities

        Args:
            schedule: Schedule object

        Returns:
            List of activity IDs on critical path
        """
        return schedule.get_critical_path()

    def _get_delayed_activities(self, schedule: Schedule) -> List[ScheduleActivity]:
        """
        Get activities that are delayed

        Args:
            schedule: Schedule object

        Returns:
            List of delayed activities
        """
        return schedule.get_delayed_activities()

    def _compare_schedules(self, baseline: Schedule, current: Schedule) -> pd.DataFrame:
        """
        Compare two schedules

        Args:
            baseline: Baseline schedule
            current: Current schedule

        Returns:
            DataFrame with comparison
        """
        baseline_df = baseline.to_dataframe()
        current_df = current.to_dataframe()

        # Merge on activity_id
        comparison = baseline_df.merge(
            current_df,
            on='activity_id',
            suffixes=('_baseline', '_current'),
            how='outer'
        )

        return comparison


class DelayAnalyzerFactory:
    """Factory to create delay analyzers"""

    _analyzers = {}

    @classmethod
    def register(cls, analyzer_class):
        """Register an analyzer class"""
        instance = analyzer_class()
        cls._analyzers[instance.name] = analyzer_class
        return analyzer_class

    @classmethod
    def create(cls, name: str) -> Optional[BaseDelayAnalyzer]:
        """Create an analyzer by name"""
        analyzer_class = cls._analyzers.get(name)
        if analyzer_class:
            return analyzer_class()
        return None

    @classmethod
    def get_available_methods(cls) -> List[Dict[str, str]]:
        """Get list of available analysis methods"""
        methods = []
        for name, analyzer_class in cls._analyzers.items():
            instance = analyzer_class()
            methods.append({
                'name': name,
                'description': instance.description
            })
        return methods
