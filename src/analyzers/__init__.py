"""
Delay Analysis Methods

This module provides implementations of the six main delay analysis methods
used in construction schedule analysis.
"""

from .base_analyzer import (
    BaseDelayAnalyzer,
    DelayAnalysisResult,
    DelayAnalyzerFactory
)

from .as_planned_vs_as_built import AsPlannedVsAsBuiltAnalyzer
from .impacted_as_planned import ImpactedAsPlannedAnalyzer
from .collapsed_as_built import CollapsedAsBuiltAnalyzer
from .time_impact_analysis import TimeImpactAnalyzer
from .windows_analysis import WindowsAnalyzer
from .contemporaneous_analysis import ContemporaneousAnalyzer

__all__ = [
    'BaseDelayAnalyzer',
    'DelayAnalysisResult',
    'DelayAnalyzerFactory',
    'AsPlannedVsAsBuiltAnalyzer',
    'ImpactedAsPlannedAnalyzer',
    'CollapsedAsBuiltAnalyzer',
    'TimeImpactAnalyzer',
    'WindowsAnalyzer',
    'ContemporaneousAnalyzer',
]


def get_available_methods():
    """
    Get list of all available delay analysis methods

    Returns:
        List of dictionaries with method name and description
    """
    return DelayAnalyzerFactory.get_available_methods()


def create_analyzer(method_name: str) -> BaseDelayAnalyzer:
    """
    Create an analyzer instance by method name

    Args:
        method_name: Name of the analysis method

    Returns:
        Analyzer instance

    Raises:
        ValueError: If method name is not recognized
    """
    analyzer = DelayAnalyzerFactory.create(method_name)
    if not analyzer:
        available = [m['name'] for m in get_available_methods()]
        raise ValueError(
            f"Unknown analysis method: {method_name}. "
            f"Available methods: {', '.join(available)}"
        )
    return analyzer
