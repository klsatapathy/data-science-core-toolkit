"""
validators.py
=============
Implements the full battery of data-quality checks required by the
application: missing values, duplicates, type mismatches, format
validation (email/phone/date), negative values, whitespace issues,
special characters, and per-column statistics.

Design
------
`DataValidator` is a stateless-ish orchestrator: each `check_*` method
takes (and returns) plain data structures so individual checks can be
unit-tested in isolation and reused outside the CLI (e.g. in notebooks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from . import config
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ColumnValidationResult:
    """Per-column validation findings."""

    column: str
    dtype: str
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    duplicate_value_count: int = 0
    is_empty: bool = False
    has_leading_trailing_whitespace: bool = False
    whitespace_row_count: int = 0
    special_character_row_count: int = 0
    negative_value_count: int | None = None
    invalid_email_count: int | None = None
    invalid_phone_count: int | None = None
    invalid_date_count: int | None = None
    suspected_type_mismatch_count: int = 0


@dataclass
class ValidationReport:
    """Aggregated results for an entire dataset."""

    total_rows: int
    total_columns: int
    duplicate_row_count: int = 0
    duplicate_row_percentage: float = 0.0
    duplicate_column_pairs: list[tuple[str, str]] = field(default_factory=list)
    empty_columns: list[str] = field(default_factory=list)
    columns: dict[str, ColumnValidationResult] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "duplicate_row_count": self.duplicate_row_count,
            "duplicate_row_percentage": round(self.duplicate_row_percentage, 2),
            "duplicate_column_pairs": self.duplicate_column_pairs,
            "empty_columns": self.empty_columns,
            "columns": {
                name: {
                    "dtype": r.dtype,
                    "null_count": r.null_count,
                    "null_percentage": round(r.null_percentage, 2),
                    "unique_count": r.unique_count,
                    "duplicate_value_count": r.duplicate_value_count,
                    "is_empty": r.is_empty,
                    "has_leading_trailing_whitespace": r.has_leading_trailing_whitespace,
                    "whitespace_row_count": r.whitespace_row_count,
                    "special_character_row_count": r.special_character_row_count,
                    "negative_value_count": r.negative_value_count,
                    "invalid_email_count": r.invalid_email_count,
                    "invalid_phone_count": r.invalid_phone_count,
                    "invalid_date_count": r.invalid_date_count,
                    "suspected_type_mismatch_count": r.suspected_type_mismatch_count,
                }
                for name, r in self.columns.items()
            },
        }


class DataValidator:
    """Runs configurable data-quality checks against a pandas DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run_all(self) -> ValidationReport:
        """Execute every validation check and return an aggregated report."""
        logger.info("Starting full validation suite...")
        rows, cols = self.df.shape
        report = ValidationReport(total_rows=rows, total_columns=cols)

        report.duplicate_row_count = self.check_duplicate_rows()
        report.duplicate_row_percentage = (
            (report.duplicate_row_count / rows) * 100 if rows else 0.0
        )
        report.duplicate_column_pairs = self.check_duplicate_columns()
        report.empty_columns = self.check_empty_columns()

        for column in self.df.columns:
            report.columns[column] = self._validate_column(column)

        logger.info("Validation suite completed.")
        return report

    # ------------------------------------------------------------------
    # Row / column level checks
    # ------------------------------------------------------------------
    def check_duplicate_rows(self) -> int:
        """Return the count of fully duplicated rows."""
        return int(self.df.duplicated(keep="first").sum())

    def check_duplicate_columns(self) -> list[tuple[str, str]]:
        """Return pairs of columns whose values are identical throughout."""
        duplicates: list[tuple[str, str]] = []
        columns = list(self.df.columns)
        for i, col_a in enumerate(columns):
            for col_b in columns[i + 1:]:
                try:
                    if self.df[col_a].equals(self.df[col_b]):
                        duplicates.append((col_a, col_b))
                except Exception:  # pragma: no cover - defensive
                    continue
        return duplicates

    def check_empty_columns(self) -> list[str]:
        """Return columns where every value is null."""
        return [col for col in self.df.columns if self.df[col].isna().all()]

    # ------------------------------------------------------------------
    # Column-level validation
    # ------------------------------------------------------------------
    def _validate_column(self, column: str) -> ColumnValidationResult:
        series = self.df[column]
        rows = len(series)
        null_count = int(series.isna().sum())

        result = ColumnValidationResult(
            column=column,
            dtype=str(series.dtype),
            null_count=null_count,
            null_percentage=(null_count / rows * 100) if rows else 0.0,
            unique_count=int(series.nunique(dropna=True)),
            is_empty=bool(series.isna().all()),
        )

        value_counts = series.value_counts(dropna=True)
        result.duplicate_value_count = int((value_counts[value_counts > 1]).sum())

        non_null = series.dropna()
        if non_null.empty:
            return result

        # pandas 3.x defaults text columns to a dedicated "str" dtype rather
        # than legacy "object", so we detect string-like columns robustly
        # across pandas versions instead of comparing dtype == object.
        is_text = pd.api.types.is_string_dtype(non_null) or pd.api.types.is_object_dtype(non_null)

        if is_text:
            str_series = non_null.astype(str)
            result.has_leading_trailing_whitespace = bool(
                str_series.str.contains(config.WHITESPACE_REGEX).any()
            )
            result.whitespace_row_count = int(
                str_series.str.contains(config.WHITESPACE_REGEX).sum()
            )
            result.special_character_row_count = int(
                str_series.str.contains(config.SPECIAL_CHAR_REGEX).sum()
            )

            lowered = column.lower()
            if any(hint in lowered for hint in config.EMAIL_COLUMN_HINTS):
                result.invalid_email_count = self._count_invalid(
                    str_series, config.EMAIL_REGEX
                )
            if any(hint in lowered for hint in config.PHONE_COLUMN_HINTS):
                result.invalid_phone_count = self._count_invalid(
                    str_series, config.PHONE_REGEX
                )
            if any(hint in lowered for hint in config.DATE_COLUMN_HINTS):
                result.invalid_date_count = self._count_invalid_dates(str_series)
            else:
                # Even without a hint, detect columns that look date-like.
                if self._looks_like_dates(str_series):
                    result.invalid_date_count = self._count_invalid_dates(str_series)

            result.suspected_type_mismatch_count = self._count_type_mismatches(str_series)
        else:
            if pd.api.types.is_numeric_dtype(non_null):
                result.negative_value_count = int((non_null < 0).sum())

        return result

    # ------------------------------------------------------------------
    # Format-specific helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _count_invalid(series: pd.Series, pattern) -> int:
        stripped = series.str.strip()
        matches = stripped.str.match(pattern)
        return int((~matches.fillna(False)).sum())

    @staticmethod
    def _count_invalid_dates(series: pd.Series) -> int:
        def is_valid(value: str) -> bool:
            value = value.strip()
            if not value:
                return False
            for fmt in config.CANDIDATE_DATE_FORMATS:
                try:
                    pd.to_datetime(value, format=fmt)
                    return True
                except (ValueError, TypeError):
                    continue
            # Fall back to pandas' flexible parser as a last resort.
            try:
                pd.to_datetime(value)
                return True
            except (ValueError, TypeError):
                return False

        invalid = series.map(lambda v: not is_valid(v))
        return int(invalid.sum())

    @staticmethod
    def _looks_like_dates(series: pd.Series, sample_size: int = 20) -> bool:
        sample = series.head(sample_size)
        if sample.empty:
            return False
        hits = 0
        for value in sample:
            try:
                pd.to_datetime(str(value), errors="raise")
                hits += 1
            except (ValueError, TypeError):
                continue
        return (hits / len(sample)) > 0.7

    @staticmethod
    def _count_type_mismatches(series: pd.Series) -> int:
        """Detect numeric-looking strings mixed into an otherwise text column.

        This flags rows that are ambiguous — e.g. a "name" column where some
        rows accidentally contain pure numbers — which often indicates a
        misaligned CSV or data-entry error.
        """
        numeric_like = series.str.strip().str.match(r"^-?\d+(\.\d+)?$").fillna(False)
        ratio = numeric_like.mean()
        # Only flag as mismatch if numeric rows are a small minority
        # (i.e. the column is predominantly text but has stray numbers).
        if 0 < ratio < 0.5:
            return int(numeric_like.sum())
        return 0
