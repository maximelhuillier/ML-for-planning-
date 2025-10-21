"""
Parser for Primavera P6 XER files
"""
import tempfile
from typing import Optional
from pathlib import Path
import pandas as pd

try:
    from xerparser import Xer
    XER_AVAILABLE = True
except ImportError:
    XER_AVAILABLE = False

from ..utils.schedule_utils import Schedule, ScheduleActivity
from ..utils.date_utils import parse_date


class P6Parser:
    """Parser for Primavera P6 XER files"""

    def __init__(self):
        if not XER_AVAILABLE:
            raise ImportError(
                "xerparser library is not installed. "
                "Install it with: pip install xerparser"
            )

    def parse(self, file_path: str) -> Schedule:
        """
        Parse XER file and return Schedule object

        Args:
            file_path: Path to XER file

        Returns:
            Schedule object with activities and relationships
        """
        try:
            # Parse XER file
            xer = Xer.reader(file_path)

            # Get the first project (or allow selection later)
            if not xer.projects:
                raise ValueError("No projects found in XER file")

            project = xer.projects[0]
            schedule = Schedule(project_name=project.proj_short_name or project.proj_id)

            # Set project dates
            if hasattr(project, 'plan_start_date'):
                schedule.project_start = project.plan_start_date
            if hasattr(project, 'plan_end_date'):
                schedule.project_finish = project.plan_end_date
            if hasattr(project, 'last_recalc_date'):
                schedule.data_date = project.last_recalc_date

            # Parse activities
            for task in project.tasks:
                activity = self._parse_activity(task)
                schedule.add_activity(activity)

            # Parse relationships
            for task in project.tasks:
                if hasattr(task, 'predecessors'):
                    for pred in task.predecessors:
                        rel_type = self._get_relationship_type(pred)
                        lag = getattr(pred, 'lag_hr_cnt', 0) / 8  # Convert hours to days
                        schedule.add_relationship(
                            predecessor=pred.predecessor_task_id,
                            successor=task.task_id,
                            rel_type=rel_type,
                            lag=int(lag)
                        )

            return schedule

        except Exception as e:
            raise Exception(f"Error parsing XER file: {str(e)}")

    def _parse_activity(self, task) -> ScheduleActivity:
        """
        Convert XER task to ScheduleActivity

        Args:
            task: XER task object

        Returns:
            ScheduleActivity object
        """
        # Get dates
        start_date = getattr(task, 'target_start_date', None) or getattr(task, 'early_start_date', None)
        finish_date = getattr(task, 'target_end_date', None) or getattr(task, 'early_end_date', None)
        early_start = getattr(task, 'early_start_date', None)
        early_finish = getattr(task, 'early_end_date', None)
        late_start = getattr(task, 'late_start_date', None)
        late_finish = getattr(task, 'late_end_date', None)
        actual_start = getattr(task, 'act_start_date', None)
        actual_finish = getattr(task, 'act_end_date', None)

        # Get duration
        duration = getattr(task, 'target_drtn_hr_cnt', 0) / 8  # Convert hours to days

        # Get float
        total_float = getattr(task, 'total_float_hr_cnt', 0) / 8 if hasattr(task, 'total_float_hr_cnt') else 0
        free_float = getattr(task, 'free_float_hr_cnt', 0) / 8 if hasattr(task, 'free_float_hr_cnt') else 0

        # Get percent complete
        percent_complete = getattr(task, 'phys_complete_pct', 0) or 0

        # Get WBS
        wbs = getattr(task, 'wbs_id', '')

        # Get calendar
        calendar = getattr(task, 'clndr_id', 'Standard')

        activity = ScheduleActivity(
            activity_id=task.task_id,
            name=task.task_name or task.task_code or task.task_id,
            duration=duration,
            start_date=start_date,
            finish_date=finish_date,
            early_start=early_start,
            early_finish=early_finish,
            late_start=late_start,
            late_finish=late_finish,
            total_float=total_float,
            free_float=free_float,
            actual_start=actual_start,
            actual_finish=actual_finish,
            percent_complete=percent_complete,
            wbs=wbs,
            calendar=calendar
        )

        return activity

    def _get_relationship_type(self, relationship) -> str:
        """
        Get relationship type from XER relationship object

        Args:
            relationship: XER relationship object

        Returns:
            Relationship type string (FS, SS, FF, SF)
        """
        pred_type = getattr(relationship, 'pred_type', 'PR_FS')

        type_map = {
            'PR_FS': 'FS',  # Finish-to-Start
            'PR_SS': 'SS',  # Start-to-Start
            'PR_FF': 'FF',  # Finish-to-Finish
            'PR_SF': 'SF',  # Start-to-Finish
        }

        return type_map.get(pred_type, 'FS')

    def get_available_projects(self, file_path: str) -> list:
        """
        Get list of available projects in XER file

        Args:
            file_path: Path to XER file

        Returns:
            List of project dictionaries with id and name
        """
        try:
            xer = Xer.reader(file_path)
            projects = []

            for project in xer.projects:
                projects.append({
                    'id': project.proj_id,
                    'name': project.proj_short_name or project.proj_id,
                    'start': getattr(project, 'plan_start_date', None),
                    'finish': getattr(project, 'plan_end_date', None)
                })

            return projects

        except Exception as e:
            raise Exception(f"Error reading XER file: {str(e)}")


def parse_xer_file(file_path: str) -> Schedule:
    """
    Convenience function to parse XER file

    Args:
        file_path: Path to XER file

    Returns:
        Schedule object
    """
    parser = P6Parser()
    return parser.parse(file_path)
