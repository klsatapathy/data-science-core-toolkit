"""
cleaner.py
==========
Configurable, chainable data-cleaning operations.

`DataCleaner` operates on a copy of the input DataFrame and records every
operation performed so the transformation is fully auditable via
`get_cleaning_log()`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from . import config
from .exceptions import InvalidCleaningStrategyError
from .logger import get_logger

logger = get_logger(__name__)


class DataCleaner:
    """Applies opt-in cleaning operations to a DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.original_df = df
        self.df = df.copy(deep=True)
        self._log: list[str] = []

    # ------------------------------------------------------------------
    # Cleaning operations
    # ------------------------------------------------------------------
    def remove_duplicate_rows(self) -> "DataCleaner":
        before = len(self.df)
        self.df = self.df.drop_duplicates(keep="first").reset_index(drop=True)
        removed = before - len(self.df)
        self._record(f"Removed {removed} duplicate row(s).")
        return self

    def trim_whitespace(self, columns: list[str] | None = None) -> "DataCleaner":
        target_columns = columns or self._text_columns()
        for col in target_columns:
            if col in self.df.columns and self._is_text_column(col):
                self.df[col] = self.df[col].apply(
                    lambda v: v.strip() if isinstance(v, str) else v
                )
        self._record(f"Trimmed whitespace on columns: {target_columns}")
        return self

    def standardize_text_case(
        self, columns: list[str] | None = None, case: str = config.DEFAULT_TEXT_CASE
    ) -> "DataCleaner":
        valid_cases = {"lower", "upper", "title", "none"}
        if case not in valid_cases:
            raise InvalidCleaningStrategyError(
                f"Invalid text case '{case}'. Must be one of {valid_cases}."
            )
        if case == "none":
            return self

        target_columns = columns or self._text_columns()
        case_fn = {"lower": str.lower, "upper": str.upper, "title": str.title}[case]

        for col in target_columns:
            if col in self.df.columns and self._is_text_column(col):
                self.df[col] = self.df[col].apply(
                    lambda v: case_fn(v) if isinstance(v, str) else v
                )
        self._record(f"Standardized text case to '{case}' on columns: {target_columns}")
        return self

    def convert_date_formats(
        self, columns: list[str], target_format: str = "%Y-%m-%d"
    ) -> "DataCleaner":
        for col in columns:
            if col not in self.df.columns:
                continue
            parsed = pd.to_datetime(self.df[col], errors="coerce")
            self.df[col] = parsed.dt.strftime(target_format)
        self._record(f"Converted date columns {columns} to format '{target_format}'.")
        return self

    def fill_missing_values(
        self,
        strategy: str = config.DEFAULT_FILL_STRATEGY,
        columns: list[str] | None = None,
        constant_value: Any = None,
    ) -> "DataCleaner":
        if strategy not in config.FILL_STRATEGIES:
            raise InvalidCleaningStrategyError(
                f"Invalid fill strategy '{strategy}'. Must be one of {config.FILL_STRATEGIES}."
            )

        target_columns = columns or self.df.columns.tolist()

        if strategy == "drop":
            before = len(self.df)
            self.df = self.df.dropna(subset=target_columns).reset_index(drop=True)
            self._record(f"Dropped {before - len(self.df)} row(s) with missing values.")
            return self

        for col in target_columns:
            if col not in self.df.columns:
                continue
            series = self.df[col]
            if series.isna().sum() == 0:
                continue

            if strategy == "mean" and pd.api.types.is_numeric_dtype(series):
                self.df[col] = series.fillna(series.mean())
            elif strategy == "median" and pd.api.types.is_numeric_dtype(series):
                self.df[col] = series.fillna(series.median())
            elif strategy == "mode":
                mode_vals = series.mode(dropna=True)
                if not mode_vals.empty:
                    self.df[col] = series.fillna(mode_vals.iloc[0])
            elif strategy == "constant":
                self.df[col] = series.fillna(constant_value)
            elif strategy == "ffill":
                self.df[col] = series.ffill()
            elif strategy == "bfill":
                self.df[col] = series.bfill()
            else:
                # Numeric strategy requested on a non-numeric column: fall back to mode.
                mode_vals = series.mode(dropna=True)
                if not mode_vals.empty:
                    self.df[col] = series.fillna(mode_vals.iloc[0])

        self._record(f"Filled missing values using strategy '{strategy}' on {target_columns}.")
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def get_cleaned_data(self) -> pd.DataFrame:
        return self.df

    def get_cleaning_log(self) -> list[str]:
        return list(self._log)

    def export(self, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(output_path, index=False)
        logger.info("Cleaned dataset exported to '%s'.", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _text_columns(self) -> list[str]:
        """Return column names holding string-like data.

        Handles both legacy pandas "object" columns and pandas 3.x's
        dedicated string dtype.
        """
        return [col for col in self.df.columns if self._is_text_column(col)]

    def _is_text_column(self, col: str) -> bool:
        series = self.df[col]
        return bool(pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series))

    def _record(self, message: str) -> None:
        logger.debug(message)
        self._log.append(message)
