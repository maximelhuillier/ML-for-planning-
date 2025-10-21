"""
Parser for Microsoft Project files (MPP, XML)
Note: For best compatibility, export MS Project files to XML format
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional
import warnings

from ..utils.schedule_utils import Schedule, ScheduleActivity
from ..utils.date_utils import parse_date


class MSProjectParser:
    """Parser for Microsoft Project XML files"""

    def __init__(self):
        self.namespaces = {
            'ns': 'http://schemas.microsoft.com/project'
        }

    def parse(self, file_path: str) -> Schedule:
        """
        Parse MS Project XML file and return Schedule object

        Args:
            file_path: Path to MS Project XML file

        Returns:
            Schedule object with activities and relationships
        """
        file_path_lower = file_path.lower()

        if file_path_lower.endswith('.mpp'):
            return self._parse_mpp(file_path)
        elif file_path_lower.endswith('.xml'):
            return self._parse_xml(file_path)
        else:
            raise ValueError("Unsupported file format. Use .xml or .mpp")

    def _parse_mpp(self, file_path: str) -> Schedule:
        """
        Parse MPP file (binary format)

        Note: This requires external tools or libraries.
        Users should export to XML format for best compatibility.

        Args:
            file_path: Path to MPP file

        Returns:
            Schedule object
        """
        # Try using jpype1 with MPXJ if available
        try:
            import jpype
            import jpype.imports

            if not jpype.isJVMStarted():
                # Try to find mpxj jar
                # Users will need to download mpxj jar separately
                warnings.warn(
                    "MPP parsing requires MPXJ library. "
                    "For best results, export MS Project to XML format."
                )
                raise ImportError("MPXJ not configured")

            # MPXJ parsing code would go here
            # This is a placeholder for future implementation
            raise NotImplementedError(
                "Direct MPP parsing is not yet implemented. "
                "Please export your MS Project file to XML format:\n"
                "1. Open the file in MS Project\n"
                "2. File > Save As > Choose 'XML Format (*.xml)'\n"
                "3. Upload the XML file instead"
            )

        except ImportError:
            raise NotImplementedError(
                "Direct MPP parsing requires additional setup. "
                "Please export your MS Project file to XML format:\n"
                "1. Open the file in MS Project\n"
                "2. File > Save As > Choose 'XML Format (*.xml)'\n"
                "3. Upload the XML file instead"
            )

    def _parse_xml(self, file_path: str) -> Schedule:
        """
        Parse MS Project XML file

        Args:
            file_path: Path to XML file

        Returns:
            Schedule object
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Determine namespace
            ns = ''
            if root.tag.startswith('{'):
                ns = root.tag[1:root.tag.index('}')]
                self.namespaces['ns'] = ns

            # Create schedule
            schedule = Schedule()

            # Get project properties
            project_name = root.find('.//ns:Name', self.namespaces)
            if project_name is not None and project_name.text:
                schedule.project_name = project_name.text

            start_date = root.find('.//ns:StartDate', self.namespaces)
            if start_date is not None and start_date.text:
                schedule.project_start = self._parse_ms_date(start_date.text)

            finish_date = root.find('.//ns:FinishDate', self.namespaces)
            if finish_date is not None and finish_date.text:
                schedule.project_finish = self._parse_ms_date(finish_date.text)

            status_date = root.find('.//ns:StatusDate', self.namespaces)
            if status_date is not None and status_date.text:
                schedule.data_date = self._parse_ms_date(status_date.text)

            # Parse tasks
            tasks = root.findall('.//ns:Task', self.namespaces)
            task_map = {}  # Map UID to activity

            for task in tasks:
                activity = self._parse_task(task)
                if activity:
                    schedule.add_activity(activity)
                    uid = task.find('ns:UID', self.namespaces)
                    if uid is not None:
                        task_map[uid.text] = activity.activity_id

            # Parse predecessors
            for task in tasks:
                uid = task.find('ns:UID', self.namespaces)
                if uid is None:
                    continue

                current_id = task_map.get(uid.text)
                if not current_id:
                    continue

                predecessors = task.findall('.//ns:PredecessorLink', self.namespaces)
                for pred in predecessors:
                    pred_uid = pred.find('ns:PredecessorUID', self.namespaces)
                    if pred_uid is None:
                        continue

                    pred_id = task_map.get(pred_uid.text)
                    if not pred_id:
                        continue

                    # Get relationship type
                    rel_type_elem = pred.find('ns:Type', self.namespaces)
                    rel_type = self._get_relationship_type(
                        rel_type_elem.text if rel_type_elem is not None else '1'
                    )

                    # Get lag
                    lag_elem = pred.find('ns:LinkLag', self.namespaces)
                    lag = 0
                    if lag_elem is not None and lag_elem.text:
                        # LinkLag is in tenths of minutes
                        lag = int(lag_elem.text) / 4800  # Convert to days

                    schedule.add_relationship(pred_id, current_id, rel_type, int(lag))

            return schedule

        except ET.ParseError as e:
            raise Exception(f"Error parsing XML file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing MS Project file: {str(e)}")

    def _parse_task(self, task_elem) -> Optional[ScheduleActivity]:
        """
        Parse task element into ScheduleActivity

        Args:
            task_elem: XML task element

        Returns:
            ScheduleActivity or None if summary task
        """
        # Skip summary tasks (optional)
        summary = task_elem.find('ns:Summary', self.namespaces)
        if summary is not None and summary.text == '1':
            # You can choose to include or exclude summary tasks
            pass

        # Get UID (unique identifier)
        uid_elem = task_elem.find('ns:UID', self.namespaces)
        if uid_elem is None:
            return None
        activity_id = uid_elem.text

        # Get name
        name_elem = task_elem.find('ns:Name', self.namespaces)
        name = name_elem.text if name_elem is not None else f"Task {activity_id}"

        # Get dates
        start_elem = task_elem.find('ns:Start', self.namespaces)
        start_date = self._parse_ms_date(start_elem.text) if start_elem is not None else None

        finish_elem = task_elem.find('ns:Finish', self.namespaces)
        finish_date = self._parse_ms_date(finish_elem.text) if finish_elem is not None else None

        # Actual dates
        actual_start_elem = task_elem.find('ns:ActualStart', self.namespaces)
        actual_start = self._parse_ms_date(actual_start_elem.text) if actual_start_elem is not None else None

        actual_finish_elem = task_elem.find('ns:ActualFinish', self.namespaces)
        actual_finish = self._parse_ms_date(actual_finish_elem.text) if actual_finish_elem is not None else None

        # Duration (in minutes for MS Project XML)
        duration_elem = task_elem.find('ns:Duration', self.namespaces)
        duration = 0
        if duration_elem is not None and duration_elem.text:
            # MS Project stores duration in format PT[hours]H[minutes]M
            duration = self._parse_duration(duration_elem.text)

        # Percent complete
        percent_elem = task_elem.find('ns:PercentComplete', self.namespaces)
        percent_complete = float(percent_elem.text) if percent_elem is not None and percent_elem.text else 0

        # Total slack/float (in minutes)
        slack_elem = task_elem.find('ns:TotalSlack', self.namespaces)
        total_float = 0
        if slack_elem is not None and slack_elem.text:
            total_float = self._parse_duration(slack_elem.text)

        # Free slack
        free_slack_elem = task_elem.find('ns:FreeSlack', self.namespaces)
        free_float = 0
        if free_slack_elem is not None and free_slack_elem.text:
            free_float = self._parse_duration(free_slack_elem.text)

        # WBS
        wbs_elem = task_elem.find('ns:WBS', self.namespaces)
        wbs = wbs_elem.text if wbs_elem is not None else ''

        activity = ScheduleActivity(
            activity_id=activity_id,
            name=name,
            duration=duration,
            start_date=start_date,
            finish_date=finish_date,
            actual_start=actual_start,
            actual_finish=actual_finish,
            percent_complete=percent_complete,
            total_float=total_float,
            free_float=free_float,
            wbs=wbs
        )

        return activity

    def _parse_ms_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse MS Project date string

        Args:
            date_str: Date string in ISO format

        Returns:
            datetime object
        """
        if not date_str or date_str == 'NA':
            return None

        try:
            # MS Project uses ISO 8601 format
            # Handle both with and without timezone
            if 'T' in date_str:
                if '+' in date_str or date_str.endswith('Z'):
                    # With timezone
                    date_str = date_str.replace('Z', '+00:00')
                    return datetime.fromisoformat(date_str.split('+')[0])
                else:
                    # Without timezone
                    return datetime.fromisoformat(date_str)
            else:
                return datetime.fromisoformat(date_str)
        except ValueError:
            return parse_date(date_str)

    def _parse_duration(self, duration_str: str) -> float:
        """
        Parse MS Project duration string (PT format)

        Args:
            duration_str: Duration in PT format (e.g., PT8H0M0S or just minutes)

        Returns:
            Duration in days
        """
        if not duration_str:
            return 0

        try:
            # If it's just a number, it's in minutes
            if duration_str.isdigit():
                minutes = int(duration_str)
                return minutes / 480  # 8 hours per day

            # Parse PT format
            if duration_str.startswith('PT'):
                duration_str = duration_str[2:]  # Remove PT
                hours = 0
                minutes = 0

                if 'H' in duration_str:
                    parts = duration_str.split('H')
                    hours = int(parts[0])
                    duration_str = parts[1] if len(parts) > 1 else ''

                if 'M' in duration_str:
                    minutes = int(duration_str.split('M')[0])

                total_minutes = hours * 60 + minutes
                return total_minutes / 480  # 8 hours per day

            return 0

        except (ValueError, AttributeError):
            return 0

    def _get_relationship_type(self, type_code: str) -> str:
        """
        Convert MS Project relationship type code to standard format

        Args:
            type_code: MS Project type code

        Returns:
            Relationship type (FS, SS, FF, SF)
        """
        type_map = {
            '0': 'FF',  # Finish-to-Finish
            '1': 'FS',  # Finish-to-Start
            '2': 'SS',  # Start-to-Start
            '3': 'SF',  # Start-to-Finish
        }
        return type_map.get(str(type_code), 'FS')


def parse_msp_file(file_path: str) -> Schedule:
    """
    Convenience function to parse MS Project file

    Args:
        file_path: Path to MS Project file (.xml or .mpp)

    Returns:
        Schedule object
    """
    parser = MSProjectParser()
    return parser.parse(file_path)
