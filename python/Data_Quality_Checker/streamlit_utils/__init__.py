"""
streamlit_utils
===============
Thin orchestration layer that connects the Streamlit frontend to the
existing `data_quality_checker` backend package.

IMPORTANT: This package contains **no business logic**. Every function
here is a wrapper that calls into `data_quality_checker` classes
(CSVLoader, DataValidator, DataProfiler, DataCleaner, ReportGenerator,
Visualizer) and adapts their inputs/outputs for use in a Streamlit
session (temp-file handling, session_state caching, download-bytes
helpers, etc.).
"""
