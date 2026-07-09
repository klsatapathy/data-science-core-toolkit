"""
Data Quality Checker & CSV Validator
=====================================

A professional-grade toolkit for validating, profiling, cleaning, and
reporting on the quality of CSV datasets.

Public API
----------
CSVLoader        -> Robust CSV loading with encoding detection.
DataValidator     -> Runs a battery of data-quality checks.
DataProfiler      -> Produces a statistical profile of a dataset.
DataCleaner       -> Applies configurable cleaning operations.
ReportGenerator   -> Emits console / CSV / JSON / HTML reports.
Visualizer        -> Optional matplotlib/seaborn charts.
"""

from .loader import CSVLoader
from .validators import DataValidator
from .profiler import DataProfiler
from .cleaner import DataCleaner
from .report_generator import ReportGenerator
from .visualizer import Visualizer

__all__ = [
    "CSVLoader",
    "DataValidator",
    "DataProfiler",
    "DataCleaner",
    "ReportGenerator",
    "Visualizer",
]

__version__ = "1.0.0"
