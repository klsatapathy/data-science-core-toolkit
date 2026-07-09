"""
streamlit_utils/pipeline.py
============================
Session-aware wrappers around the existing backend classes.

Every function below simply instantiates and calls a class that already
exists in `data_quality_checker` (CSVLoader, DataValidator, DataProfiler,
DataCleaner, ReportGenerator, Visualizer). No validation, profiling,
cleaning, or reporting logic is reimplemented here -- this module only
handles the plumbing needed to run that logic inside a Streamlit app:

* Persisting an uploaded file to a per-session temp directory (the
  backend's CSVLoader reads from a real file path, both for encoding
  detection and to safely support chunked reads of large files).
* Caching results in `st.session_state` so re-rendering a page does not
  needlessly recompute validation/profiling/cleaning.
* Small format-adaptation helpers (e.g. turning a ValidationReport into
  a flat DataFrame for `st.dataframe`).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from data_quality_checker.cleaner import DataCleaner
from data_quality_checker.loader import CSVLoader, LoadMetadata
from data_quality_checker.profiler import DataProfiler, DatasetProfile
from data_quality_checker.report_generator import ReportGenerator
from data_quality_checker.validators import DataValidator, ValidationReport
from data_quality_checker.visualizer import Visualizer

SAMPLE_DATASET_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "sample_customers.csv"


# --------------------------------------------------------------------------
# Session workspace
# --------------------------------------------------------------------------
def get_workdir() -> Path:
    """Return (creating if necessary) a per-session temp directory.

    Every uploaded file, cleaned export, generated report, and chart for
    this browser session lives under here so concurrent users never
    collide on disk.
    """
    if "workdir" not in st.session_state:
        st.session_state.workdir = Path(tempfile.mkdtemp(prefix="dqc_session_"))
    return st.session_state.workdir


def reset_session(keep_workdir: bool = False) -> None:
    """Clear all cached pipeline results (called when a new file is loaded)."""
    keys_to_clear = [
        "df", "load_metadata", "source_file_label", "source_key",
        "validation_report", "profile",
        "cleaned_df", "cleaning_log", "cleaned_export_path",
        "chart_paths", "report_paths",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    if not keep_workdir:
        workdir = st.session_state.pop("workdir", None)
        if workdir and Path(workdir).exists():
            shutil.rmtree(workdir, ignore_errors=True)


# --------------------------------------------------------------------------
# 1. Loading
# --------------------------------------------------------------------------
def load_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, LoadMetadata]:
    """Persist a Streamlit `UploadedFile` to disk and load it via CSVLoader.

    Raises whatever `data_quality_checker.exceptions.DataQualityCheckerError`
    subclass CSVLoader raises -- callers should catch and display it.
    """
    workdir = get_workdir()
    uploads_dir = workdir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    dest_path = uploads_dir / uploaded_file.name
    with open(dest_path, "wb") as fh:
        fh.write(uploaded_file.getbuffer())

    loader = CSVLoader(dest_path)
    df, metadata = loader.load()
    return df, metadata


def load_sample_dataset() -> tuple[pd.DataFrame, LoadMetadata]:
    """Load the bundled sample dataset via the same CSVLoader used everywhere else."""
    loader = CSVLoader(SAMPLE_DATASET_PATH)
    return loader.load()


# --------------------------------------------------------------------------
# 2. Validation
# --------------------------------------------------------------------------
def run_validation(df: pd.DataFrame) -> ValidationReport:
    return DataValidator(df).run_all()


def validation_report_to_dataframe(report: ValidationReport) -> pd.DataFrame:
    """Flatten a ValidationReport's per-column results into a display table."""
    rows: list[dict[str, Any]] = []
    for name, res in report.columns.items():
        rows.append({
            "Column": name,
            "Dtype": res.dtype,
            "Null Count": res.null_count,
            "Null %": round(res.null_percentage, 2),
            "Unique": res.unique_count,
            "Dup. Values": res.duplicate_value_count,
            "Empty": res.is_empty,
            "Whitespace Rows": res.whitespace_row_count,
            "Special Char Rows": res.special_character_row_count,
            "Negative Values": res.negative_value_count,
            "Invalid Emails": res.invalid_email_count,
            "Invalid Phones": res.invalid_phone_count,
            "Invalid Dates": res.invalid_date_count,
            "Type Mismatches": res.suspected_type_mismatch_count,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 3. Profiling
# --------------------------------------------------------------------------
def run_profiling(df: pd.DataFrame) -> DatasetProfile:
    return DataProfiler(df).profile()


def numeric_summary_to_dataframe(profile: DatasetProfile) -> pd.DataFrame:
    if not profile.numeric_summary:
        return pd.DataFrame()
    return pd.DataFrame(profile.numeric_summary).T


def categorical_summary_to_dataframe(profile: DatasetProfile) -> pd.DataFrame:
    if not profile.categorical_summary:
        return pd.DataFrame()
    return pd.DataFrame(profile.categorical_summary).T


def missing_values_to_dataframe(profile: DatasetProfile) -> pd.DataFrame:
    total = profile.total_rows or 1
    rows = [
        {
            "Column": col,
            "Missing Count": count,
            "Missing %": round(count / total * 100, 2),
            "Unique Values": profile.unique_value_counts.get(col, 0),
        }
        for col, count in profile.missing_value_totals.items()
    ]
    return pd.DataFrame(rows).sort_values("Missing %", ascending=False).reset_index(drop=True)


def most_frequent_values_to_dataframe(profile: DatasetProfile) -> pd.DataFrame:
    rows = []
    for col, items in profile.most_frequent_values.items():
        for value, count in items:
            rows.append({"Column": col, "Value": value, "Frequency": count})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 4. Cleaning
# --------------------------------------------------------------------------
def run_cleaning(
    df: pd.DataFrame,
    remove_duplicates: bool,
    trim_whitespace: bool,
    text_case: str,
    date_columns: list[str],
    date_format: str,
    fill_strategy: str,
    fill_constant: str | None,
) -> DataCleaner:
    """Run the requested cleaning steps through the existing DataCleaner API.

    The order mirrors the CLI (`cli.py`): dedupe -> trim -> case ->
    date conversion -> fill missing values.
    """
    cleaner = DataCleaner(df)

    if remove_duplicates:
        cleaner.remove_duplicate_rows()
    if trim_whitespace:
        cleaner.trim_whitespace()
    if text_case and text_case != "none":
        cleaner.standardize_text_case(case=text_case)
    if date_columns:
        cleaner.convert_date_formats(columns=date_columns, target_format=date_format)
    if fill_strategy and fill_strategy != "none":
        cleaner.fill_missing_values(strategy=fill_strategy, constant_value=fill_constant)

    return cleaner


def export_cleaned_dataset(cleaner: DataCleaner, filename: str = "cleaned_dataset.csv") -> Path:
    workdir = get_workdir()
    output_dir = workdir / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return cleaner.export(output_dir / filename)


# --------------------------------------------------------------------------
# 5. Reporting
# --------------------------------------------------------------------------
def generate_reports(
    validation_report: ValidationReport,
    profile: DatasetProfile,
    source_file: str,
    cleaning_log: list[str] | None = None,
) -> dict[str, Path]:
    workdir = get_workdir()
    output_dir = workdir / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    reporter = ReportGenerator(
        validation_report=validation_report,
        profile=profile,
        source_file=source_file,
        cleaning_log=cleaning_log or [],
    )

    return {
        "csv": reporter.to_csv(output_dir / "data_quality_report.csv"),
        "json": reporter.to_json(output_dir / "data_quality_report.json"),
        "html": reporter.to_html(output_dir / "data_quality_report.html"),
    }


# --------------------------------------------------------------------------
# 6. Visualization
# --------------------------------------------------------------------------
def generate_charts(df: pd.DataFrame, validation_report: ValidationReport) -> list[Path]:
    workdir = get_workdir()
    charts_dir = workdir / "charts"
    visualizer = Visualizer(df, validation_report, charts_dir)
    return visualizer.generate_all()


# --------------------------------------------------------------------------
# Misc helpers
# --------------------------------------------------------------------------
def human_readable_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
