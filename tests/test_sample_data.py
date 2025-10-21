"""
Generate sample schedule data for testing
"""
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.schedule_utils import Schedule, ScheduleActivity


def create_sample_baseline_schedule() -> Schedule:
    """Create a sample baseline schedule for testing"""
    schedule = Schedule(project_name="Sample Construction Project - Baseline")

    # Project dates
    schedule.project_start = datetime(2024, 1, 1)
    schedule.project_finish = datetime(2024, 6, 30)
    schedule.data_date = datetime(2024, 1, 1)

    # Create sample activities
    activities_data = [
        {
            'activity_id': 'A1000',
            'name': 'Site Mobilization',
            'duration': 5,
            'start_date': datetime(2024, 1, 1),
            'finish_date': datetime(2024, 1, 5),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A1010',
            'name': 'Site Survey and Layout',
            'duration': 10,
            'start_date': datetime(2024, 1, 8),
            'finish_date': datetime(2024, 1, 19),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A2000',
            'name': 'Excavation',
            'duration': 15,
            'start_date': datetime(2024, 1, 22),
            'finish_date': datetime(2024, 2, 9),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A2010',
            'name': 'Foundation Formwork',
            'duration': 20,
            'start_date': datetime(2024, 2, 12),
            'finish_date': datetime(2024, 3, 8),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A2020',
            'name': 'Foundation Concrete',
            'duration': 10,
            'start_date': datetime(2024, 3, 11),
            'finish_date': datetime(2024, 3, 22),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A3000',
            'name': 'Structural Steel Erection',
            'duration': 30,
            'start_date': datetime(2024, 3, 25),
            'finish_date': datetime(2024, 5, 3),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A3010',
            'name': 'Roof Structure',
            'duration': 15,
            'start_date': datetime(2024, 5, 6),
            'finish_date': datetime(2024, 5, 24),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A4000',
            'name': 'Exterior Cladding',
            'duration': 20,
            'start_date': datetime(2024, 5, 27),
            'finish_date': datetime(2024, 6, 21),
            'total_float': 0,
            'is_critical': True
        },
        {
            'activity_id': 'A5000',
            'name': 'MEP Rough-in',
            'duration': 25,
            'start_date': datetime(2024, 4, 1),
            'finish_date': datetime(2024, 5, 3),
            'total_float': 10,
            'is_critical': False
        },
        {
            'activity_id': 'A5010',
            'name': 'Interior Finishes',
            'duration': 20,
            'start_date': datetime(2024, 5, 20),
            'finish_date': datetime(2024, 6, 14),
            'total_float': 5,
            'is_critical': False
        },
        {
            'activity_id': 'A6000',
            'name': 'Final Inspections',
            'duration': 5,
            'start_date': datetime(2024, 6, 24),
            'finish_date': datetime(2024, 6, 28),
            'total_float': 0,
            'is_critical': True
        }
    ]

    for act_data in activities_data:
        activity = ScheduleActivity(
            activity_id=act_data['activity_id'],
            name=act_data['name'],
            duration=act_data['duration'],
            start_date=act_data['start_date'],
            finish_date=act_data['finish_date'],
            early_start=act_data['start_date'],
            early_finish=act_data['finish_date'],
            late_start=act_data['start_date'],
            late_finish=act_data['finish_date'],
            total_float=act_data['total_float'],
            percent_complete=0
        )
        schedule.add_activity(activity)

    # Add relationships
    relationships = [
        ('A1000', 'A1010', 'FS', 0),
        ('A1010', 'A2000', 'FS', 0),
        ('A2000', 'A2010', 'FS', 0),
        ('A2010', 'A2020', 'FS', 0),
        ('A2020', 'A3000', 'FS', 0),
        ('A3000', 'A3010', 'FS', 0),
        ('A3010', 'A4000', 'FS', 0),
        ('A4000', 'A6000', 'FS', 0),
        ('A2020', 'A5000', 'FS', 0),
        ('A5000', 'A5010', 'FS', 0),
    ]

    for pred, succ, rel_type, lag in relationships:
        schedule.add_relationship(pred, succ, rel_type, lag)

    return schedule


def create_sample_current_schedule() -> Schedule:
    """Create a sample current schedule with delays for testing"""
    schedule = Schedule(project_name="Sample Construction Project - Current")

    # Project dates (delayed)
    schedule.project_start = datetime(2024, 1, 1)
    schedule.project_finish = datetime(2024, 7, 20)  # 20 days delayed
    schedule.data_date = datetime(2024, 4, 15)

    # Create sample activities with delays
    activities_data = [
        {
            'activity_id': 'A1000',
            'name': 'Site Mobilization',
            'duration': 5,
            'start_date': datetime(2024, 1, 1),
            'finish_date': datetime(2024, 1, 5),
            'actual_start': datetime(2024, 1, 1),
            'actual_finish': datetime(2024, 1, 5),
            'percent_complete': 100,
            'total_float': 0
        },
        {
            'activity_id': 'A1010',
            'name': 'Site Survey and Layout',
            'duration': 12,  # 2 days delayed
            'start_date': datetime(2024, 1, 8),
            'finish_date': datetime(2024, 1, 23),
            'actual_start': datetime(2024, 1, 8),
            'actual_finish': datetime(2024, 1, 23),
            'percent_complete': 100,
            'total_float': 0
        },
        {
            'activity_id': 'A2000',
            'name': 'Excavation',
            'duration': 20,  # 5 days delayed due to weather
            'start_date': datetime(2024, 1, 24),
            'finish_date': datetime(2024, 2, 16),
            'actual_start': datetime(2024, 1, 24),
            'actual_finish': datetime(2024, 2, 16),
            'percent_complete': 100,
            'total_float': 0
        },
        {
            'activity_id': 'A2010',
            'name': 'Foundation Formwork',
            'duration': 25,  # 5 days delayed
            'start_date': datetime(2024, 2, 19),
            'finish_date': datetime(2024, 3, 22),
            'actual_start': datetime(2024, 2, 19),
            'actual_finish': datetime(2024, 3, 22),
            'percent_complete': 100,
            'total_float': 0
        },
        {
            'activity_id': 'A2020',
            'name': 'Foundation Concrete',
            'duration': 12,  # 2 days delayed
            'start_date': datetime(2024, 3, 25),
            'finish_date': datetime(2024, 4, 9),
            'actual_start': datetime(2024, 3, 25),
            'actual_finish': datetime(2024, 4, 9),
            'percent_complete': 100,
            'total_float': 0
        },
        {
            'activity_id': 'A3000',
            'name': 'Structural Steel Erection',
            'duration': 35,  # 5 days delayed - material delay
            'start_date': datetime(2024, 4, 10),
            'finish_date': datetime(2024, 5, 24),
            'actual_start': datetime(2024, 4, 10),
            'percent_complete': 35,
            'total_float': 0
        },
        {
            'activity_id': 'A3010',
            'name': 'Roof Structure',
            'duration': 15,
            'start_date': datetime(2024, 5, 27),
            'finish_date': datetime(2024, 6, 14),
            'percent_complete': 0,
            'total_float': 0
        },
        {
            'activity_id': 'A4000',
            'name': 'Exterior Cladding',
            'duration': 20,
            'start_date': datetime(2024, 6, 17),
            'finish_date': datetime(2024, 7, 12),
            'percent_complete': 0,
            'total_float': 0
        },
        {
            'activity_id': 'A5000',
            'name': 'MEP Rough-in',
            'duration': 25,
            'start_date': datetime(2024, 4, 15),
            'finish_date': datetime(2024, 5, 17),
            'actual_start': datetime(2024, 4, 15),
            'percent_complete': 20,
            'total_float': 8
        },
        {
            'activity_id': 'A5010',
            'name': 'Interior Finishes',
            'duration': 20,
            'start_date': datetime(2024, 6, 10),
            'finish_date': datetime(2024, 7, 5),
            'percent_complete': 0,
            'total_float': 5
        },
        {
            'activity_id': 'A6000',
            'name': 'Final Inspections',
            'duration': 5,
            'start_date': datetime(2024, 7, 15),
            'finish_date': datetime(2024, 7, 19),
            'percent_complete': 0,
            'total_float': 0
        }
    ]

    for act_data in activities_data:
        activity = ScheduleActivity(
            activity_id=act_data['activity_id'],
            name=act_data['name'],
            duration=act_data['duration'],
            start_date=act_data['start_date'],
            finish_date=act_data['finish_date'],
            actual_start=act_data.get('actual_start'),
            actual_finish=act_data.get('actual_finish'),
            early_start=act_data['start_date'],
            early_finish=act_data['finish_date'],
            late_start=act_data['start_date'],
            late_finish=act_data['finish_date'],
            total_float=act_data['total_float'],
            percent_complete=act_data['percent_complete']
        )
        schedule.add_activity(activity)

    # Add relationships
    relationships = [
        ('A1000', 'A1010', 'FS', 0),
        ('A1010', 'A2000', 'FS', 0),
        ('A2000', 'A2010', 'FS', 0),
        ('A2010', 'A2020', 'FS', 0),
        ('A2020', 'A3000', 'FS', 0),
        ('A3000', 'A3010', 'FS', 0),
        ('A3010', 'A4000', 'FS', 0),
        ('A4000', 'A6000', 'FS', 0),
        ('A2020', 'A5000', 'FS', 0),
        ('A5000', 'A5010', 'FS', 0),
    ]

    for pred, succ, rel_type, lag in relationships:
        schedule.add_relationship(pred, succ, rel_type, lag)

    return schedule


if __name__ == "__main__":
    print("Generating sample schedules...")

    baseline = create_sample_baseline_schedule()
    current = create_sample_current_schedule()

    print(f"\nBaseline Schedule:")
    print(f"  Project: {baseline.project_name}")
    print(f"  Activities: {len(baseline.activities)}")
    print(f"  Duration: {baseline.project_start} to {baseline.project_finish}")

    print(f"\nCurrent Schedule:")
    print(f"  Project: {current.project_name}")
    print(f"  Activities: {len(current.activities)}")
    print(f"  Duration: {current.project_start} to {current.project_finish}")

    # Quick test analysis
    print("\n--- Quick Test Analysis ---")
    from src.analyzers import create_analyzer

    analyzer = create_analyzer("As-Planned vs As-Built")
    result = analyzer.analyze(
        baseline_schedule=baseline,
        current_schedule=current,
        include_non_critical=True
    )

    print(f"\nTotal Delay: {result.total_delay_days:.1f} days")
    print(f"Critical Delay: {result.critical_delay_days:.1f} days")
    print(f"Affected Activities: {len(result.delays_by_activity)}")

    print("\nTop 5 Delayed Activities:")
    sorted_delays = sorted(result.delays_by_activity,
                          key=lambda x: x['delay_days'], reverse=True)[:5]
    for i, delay in enumerate(sorted_delays, 1):
        print(f"  {i}. {delay['activity_name']}: {delay['delay_days']:.1f} days")

    print("\n✓ Sample data generation successful!")
    print("\nYou can now use these schedules for testing the application.")
