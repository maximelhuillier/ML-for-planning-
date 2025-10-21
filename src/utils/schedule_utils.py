"""
Schedule utilities for critical path and network analysis
"""
from typing import Dict, List, Tuple, Set
from datetime import datetime, timedelta
import networkx as nx
import pandas as pd


class ScheduleActivity:
    """Represents a single activity in a schedule"""

    def __init__(self, activity_id: str, name: str, **kwargs):
        self.activity_id = activity_id
        self.name = name
        self.duration = kwargs.get('duration', 0)
        self.start_date = kwargs.get('start_date')
        self.finish_date = kwargs.get('finish_date')
        self.early_start = kwargs.get('early_start')
        self.early_finish = kwargs.get('early_finish')
        self.late_start = kwargs.get('late_start')
        self.late_finish = kwargs.get('late_finish')
        self.total_float = kwargs.get('total_float', 0)
        self.free_float = kwargs.get('free_float', 0)
        self.actual_start = kwargs.get('actual_start')
        self.actual_finish = kwargs.get('actual_finish')
        self.percent_complete = kwargs.get('percent_complete', 0)
        self.predecessors = kwargs.get('predecessors', [])
        self.successors = kwargs.get('successors', [])
        self.calendar = kwargs.get('calendar', 'Standard')
        self.wbs = kwargs.get('wbs', '')
        self.resource_names = kwargs.get('resource_names', [])

    @property
    def is_critical(self) -> bool:
        """Check if activity is on critical path"""
        return self.total_float is not None and self.total_float <= 0

    @property
    def is_started(self) -> bool:
        """Check if activity has started"""
        return self.actual_start is not None

    @property
    def is_finished(self) -> bool:
        """Check if activity is finished"""
        return self.actual_finish is not None

    @property
    def remaining_duration(self) -> float:
        """Calculate remaining duration"""
        if self.is_finished:
            return 0
        return self.duration * (1 - self.percent_complete / 100.0)

    def to_dict(self) -> dict:
        """Convert activity to dictionary"""
        return {
            'activity_id': self.activity_id,
            'name': self.name,
            'duration': self.duration,
            'start_date': self.start_date,
            'finish_date': self.finish_date,
            'early_start': self.early_start,
            'early_finish': self.early_finish,
            'late_start': self.late_start,
            'late_finish': self.late_finish,
            'total_float': self.total_float,
            'free_float': self.free_float,
            'actual_start': self.actual_start,
            'actual_finish': self.actual_finish,
            'percent_complete': self.percent_complete,
            'is_critical': self.is_critical,
            'wbs': self.wbs,
            'calendar': self.calendar
        }


class Schedule:
    """Represents a complete project schedule"""

    def __init__(self, project_name: str = ""):
        self.project_name = project_name
        self.activities: Dict[str, ScheduleActivity] = {}
        self.relationships: List[Tuple[str, str, str, int]] = []  # (pred, succ, type, lag)
        self.data_date = None
        self.project_start = None
        self.project_finish = None

    def add_activity(self, activity: ScheduleActivity):
        """Add activity to schedule"""
        self.activities[activity.activity_id] = activity

    def add_relationship(self, predecessor: str, successor: str,
                        rel_type: str = 'FS', lag: int = 0):
        """
        Add relationship between activities

        Args:
            predecessor: Predecessor activity ID
            successor: Successor activity ID
            rel_type: Relationship type (FS, SS, FF, SF)
            lag: Lag in days
        """
        self.relationships.append((predecessor, successor, rel_type, lag))

        if predecessor in self.activities:
            if successor not in self.activities[predecessor].successors:
                self.activities[predecessor].successors.append(successor)

        if successor in self.activities:
            if predecessor not in self.activities[successor].predecessors:
                self.activities[successor].predecessors.append(predecessor)

    def get_critical_path(self) -> List[str]:
        """
        Calculate critical path using forward and backward pass

        Returns:
            List of activity IDs on critical path
        """
        if not self.activities:
            return []

        # Build network graph
        G = nx.DiGraph()

        for act_id, activity in self.activities.items():
            G.add_node(act_id, duration=activity.duration)

        for pred, succ, rel_type, lag in self.relationships:
            if pred in G and succ in G:
                G.add_edge(pred, succ, type=rel_type, lag=lag)

        # Find all paths from start to end activities
        start_activities = [act_id for act_id, act in self.activities.items()
                          if not act.predecessors]
        end_activities = [act_id for act_id, act in self.activities.items()
                        if not act.successors]

        if not start_activities or not end_activities:
            # Fallback: find activities with total_float == 0
            return [act_id for act_id, act in self.activities.items() if act.is_critical]

        # Find longest path (critical path)
        critical_path = []
        max_duration = 0

        for start in start_activities:
            for end in end_activities:
                try:
                    for path in nx.all_simple_paths(G, start, end):
                        path_duration = sum(self.activities[act_id].duration for act_id in path)
                        if path_duration > max_duration:
                            max_duration = path_duration
                            critical_path = path
                except nx.NetworkXNoPath:
                    continue

        return critical_path

    def get_activities_by_float(self, max_float: float = 0) -> List[ScheduleActivity]:
        """
        Get activities with total float less than or equal to threshold

        Args:
            max_float: Maximum total float

        Returns:
            List of activities
        """
        return [act for act in self.activities.values()
                if act.total_float is not None and act.total_float <= max_float]

    def get_delayed_activities(self) -> List[ScheduleActivity]:
        """
        Get activities that are delayed (actual dates exceed planned dates)

        Returns:
            List of delayed activities
        """
        delayed = []
        for activity in self.activities.values():
            if activity.actual_finish and activity.finish_date:
                if activity.actual_finish > activity.finish_date:
                    delayed.append(activity)
            elif activity.actual_start and activity.start_date:
                if activity.actual_start > activity.start_date:
                    delayed.append(activity)
        return delayed

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert schedule to pandas DataFrame

        Returns:
            DataFrame with all activities
        """
        data = [act.to_dict() for act in self.activities.values()]
        return pd.DataFrame(data)

    def get_summary_stats(self) -> dict:
        """
        Get summary statistics for the schedule

        Returns:
            Dictionary with summary statistics
        """
        df = self.to_dataframe()

        return {
            'total_activities': len(self.activities),
            'critical_activities': len([a for a in self.activities.values() if a.is_critical]),
            'completed_activities': len([a for a in self.activities.values() if a.is_finished]),
            'in_progress_activities': len([a for a in self.activities.values()
                                          if a.is_started and not a.is_finished]),
            'not_started_activities': len([a for a in self.activities.values() if not a.is_started]),
            'total_duration': df['duration'].sum() if 'duration' in df else 0,
            'avg_completion': df['percent_complete'].mean() if 'percent_complete' in df else 0,
            'project_start': self.project_start,
            'project_finish': self.project_finish,
            'data_date': self.data_date
        }


def calculate_float(activity: ScheduleActivity) -> Tuple[float, float]:
    """
    Calculate total float and free float for an activity

    Args:
        activity: Activity to calculate float for

    Returns:
        Tuple of (total_float, free_float)
    """
    total_float = 0
    free_float = 0

    if activity.late_start and activity.early_start:
        total_float = (activity.late_start - activity.early_start).days

    # Free float calculation requires successor information
    # Simplified for now
    free_float = total_float

    return total_float, free_float
