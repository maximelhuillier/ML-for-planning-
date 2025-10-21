"""
Date utilities for schedule analysis
"""
from datetime import datetime, timedelta
from typing import Optional, Union
import pandas as pd


def parse_date(date_input: Union[str, datetime, pd.Timestamp]) -> Optional[datetime]:
    """
    Parse various date formats into datetime object

    Args:
        date_input: Date in various formats

    Returns:
        datetime object or None if parsing fails
    """
    if date_input is None:
        return None

    if isinstance(date_input, datetime):
        return date_input

    if isinstance(date_input, pd.Timestamp):
        return date_input.to_pydatetime()

    if isinstance(date_input, str):
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue

    return None


def calculate_duration_days(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate duration in calendar days between two dates

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of days
    """
    if not start_date or not end_date:
        return 0

    return (end_date - start_date).days


def calculate_working_days(start_date: datetime, end_date: datetime,
                          holidays: list = None) -> int:
    """
    Calculate working days between two dates (excluding weekends and holidays)

    Args:
        start_date: Start date
        end_date: End date
        holidays: List of holiday dates

    Returns:
        Number of working days
    """
    if not start_date or not end_date:
        return 0

    holidays = holidays or []
    working_days = 0
    current_date = start_date

    while current_date <= end_date:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5 and current_date not in holidays:
            working_days += 1
        current_date += timedelta(days=1)

    return working_days


def add_working_days(start_date: datetime, days: int, holidays: list = None) -> datetime:
    """
    Add working days to a date

    Args:
        start_date: Starting date
        days: Number of working days to add
        holidays: List of holiday dates

    Returns:
        Resulting date
    """
    holidays = holidays or []
    current_date = start_date
    days_added = 0

    while days_added < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5 and current_date not in holidays:
            days_added += 1

    return current_date


def format_date(date: datetime, format_str: str = '%Y-%m-%d') -> str:
    """
    Format datetime to string

    Args:
        date: Datetime object
        format_str: Format string

    Returns:
        Formatted date string
    """
    if not date:
        return ""
    return date.strftime(format_str)


def get_date_range(start_date: datetime, end_date: datetime) -> list:
    """
    Get list of all dates in a range

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of datetime objects
    """
    if not start_date or not end_date:
        return []

    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates
