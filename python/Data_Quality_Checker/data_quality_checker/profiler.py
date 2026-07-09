"""
profiler.py
===========
Generates a statistical profile of a dataset: shape, memory footprint,
per-column data types, missing-value statistics, most-frequent values,
and separate numeric / categorical summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from . import config
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetProfile:
    """Complete profiling result for a dataset."""

    total_rows: int
    total_columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    memory_usage_bytes: int
    memory_usage_human: str
    missing_value_totals: dict[str, int]
    unique_value_counts: dict[str, int]
    most_frequent_values: dict[str, list[tuple[Any, int]]]
    numeric_summary: dict[str, dict[str, float]] = field(default_factory=dict)
    categorical_summary: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "column_names": self.column_names,
            "dtypes": self.dtypes,
            "memory_usage_bytes": self.memory_usage_bytes,
            "memory_usage_human": self.memory_usage_human,
            "missing_value_totals": self.missing_value_totals,
            "unique_value_counts": self.unique_value_counts,
            "most_frequent_values": {
                col: [[str(val), int(count)] for val, count in items]
                for col, items in self.most_frequent_values.items()
            },
            "numeric_summary": self.numeric_summary,
            "categorical_summary": self.categorical_summary,
        }


class DataProfiler:
    """Builds a `DatasetProfile` from a pandas DataFrame."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def profile(self) -> DatasetProfile:
        logger.info("Generating dataset profile...")
        df = self.df
        rows, cols = df.shape
        memory_bytes = int(df.memory_usage(deep=True).sum())

        result = DatasetProfile(
            total_rows=rows,
            total_columns=cols,
            column_names=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            memory_usage_bytes=memory_bytes,
            memory_usage_human=self._human_readable_bytes(memory_bytes),
            missing_value_totals={col: int(df[col].isna().sum()) for col in df.columns},
            unique_value_counts={col: int(df[col].nunique(dropna=True)) for col in df.columns},
            most_frequent_values=self._most_frequent_values(),
        )

        result.numeric_summary = self._numeric_summary()
        result.categorical_summary = self._categorical_summary()

        logger.info("Profiling complete: %s rows x %s columns.", rows, cols)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _most_frequent_values(self) -> dict[str, list[tuple[Any, int]]]:
        result: dict[str, list[tuple[Any, int]]] = {}
        for col in self.df.columns:
            counts = self.df[col].value_counts(dropna=True).head(config.TOP_N_FREQUENT_VALUES)
            result[col] = list(zip(counts.index.tolist(), counts.values.tolist()))
        return result

    def _numeric_summary(self) -> dict[str, dict[str, float]]:
        numeric_df = self.df.select_dtypes(include="number")
        summary: dict[str, dict[str, float]] = {}
        if numeric_df.empty:
            return summary
        described = numeric_df.describe().to_dict()
        for col, stats in described.items():
            summary[col] = {
                "count": stats.get("count", 0.0),
                "mean": round(stats.get("mean", 0.0), 4),
                "std": round(stats.get("std", 0.0), 4) if pd.notna(stats.get("std")) else 0.0,
                "min": stats.get("min", 0.0),
                "25%": stats.get("25%", 0.0),
                "50%": stats.get("50%", 0.0),
                "75%": stats.get("75%", 0.0),
                "max": stats.get("max", 0.0),
            }
        return summary

    def _categorical_summary(self) -> dict[str, dict[str, Any]]:
        # Include legacy "object" columns, pandas "category" columns, and
        # pandas 3.x's dedicated string dtype (not picked up by "object").
        text_like_cols = [
            col for col in self.df.columns
            if pd.api.types.is_object_dtype(self.df[col])
            or isinstance(self.df[col].dtype, pd.CategoricalDtype)
            or pd.api.types.is_string_dtype(self.df[col])
        ]
        cat_df = self.df[text_like_cols]
        summary: dict[str, dict[str, Any]] = {}
        for col in cat_df.columns:
            series = cat_df[col].dropna()
            if series.empty:
                summary[col] = {"unique_count": 0, "top_value": None, "top_frequency": 0}
                continue
            counts = series.value_counts()
            summary[col] = {
                "unique_count": int(series.nunique()),
                "top_value": str(counts.index[0]),
                "top_frequency": int(counts.iloc[0]),
                "avg_length": round(series.astype(str).str.len().mean(), 2),
            }
        return summary

    @staticmethod
    def _human_readable_bytes(num_bytes: int) -> str:
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
