"""
visualizer.py
=============
Optional matplotlib/seaborn visualizations for data-quality findings:
a missing-value heatmap, a null-percentage bar chart, distribution plots
for numeric columns, and a duplicate-rows summary chart.

These are opt-in (triggered via the `--visualize` CLI flag) since chart
generation is not required for the core validation workflow.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe backend for servers / CI
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .logger import get_logger
from .validators import ValidationReport

logger = get_logger(__name__)

sns.set_theme(style="whitegrid")


class Visualizer:
    """Generates and saves data-quality charts as PNG files."""

    def __init__(self, df: pd.DataFrame, validation_report: ValidationReport, output_dir: str | Path) -> None:
        self.df = df
        self.validation_report = validation_report
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> list[Path]:
        """Generate every available chart and return their file paths."""
        paths = []
        paths.append(self.missing_value_heatmap())
        paths.append(self.null_percentage_bar_chart())
        paths.append(self.duplicate_summary_chart())
        dist_paths = self.numeric_distribution_plots()
        paths.extend(dist_paths)
        return [p for p in paths if p is not None]

    def missing_value_heatmap(self) -> Path | None:
        if self.df.empty:
            return None
        fig, ax = plt.subplots(figsize=(min(14, 1 + 0.5 * self.df.shape[1]), 6))
        sns.heatmap(self.df.isna(), cbar=False, cmap="rocket_r", yticklabels=False, ax=ax)
        ax.set_title("Missing Value Heatmap")
        ax.set_xlabel("Columns")
        path = self.output_dir / "missing_value_heatmap.png"
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        logger.info("Saved missing value heatmap to '%s'.", path)
        return path

    def null_percentage_bar_chart(self) -> Path | None:
        data = {
            col: res.null_percentage for col, res in self.validation_report.columns.items()
        }
        if not data:
            return None
        series = pd.Series(data).sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(min(14, 1 + 0.5 * len(series)), 6))
        sns.barplot(x=series.index, y=series.values, hue=series.index, palette="magma", legend=False, ax=ax)
        ax.set_ylabel("Null Percentage (%)")
        ax.set_xlabel("Column")
        ax.set_title("Null Percentage by Column")
        ax.tick_params(axis="x", rotation=45)
        for label in ax.get_xticklabels():
            label.set_ha("right")
        path = self.output_dir / "null_percentage_bar_chart.png"
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        logger.info("Saved null percentage bar chart to '%s'.", path)
        return path

    def duplicate_summary_chart(self) -> Path | None:
        unique_rows = self.validation_report.total_rows - self.validation_report.duplicate_row_count
        labels = ["Unique Rows", "Duplicate Rows"]
        values = [unique_rows, self.validation_report.duplicate_row_count]
        if sum(values) == 0:
            return None
        fig, ax = plt.subplots(figsize=(5, 5))
        colors = ["#2563eb", "#dc2626"]
        ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
        ax.set_title("Duplicate Row Summary")
        path = self.output_dir / "duplicate_summary_chart.png"
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        logger.info("Saved duplicate summary chart to '%s'.", path)
        return path

    def numeric_distribution_plots(self, max_columns: int = 6) -> list[Path]:
        numeric_df = self.df.select_dtypes(include="number")
        paths: list[Path] = []
        for col in list(numeric_df.columns)[:max_columns]:
            series = numeric_df[col].dropna()
            if series.empty:
                continue
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.histplot(series, kde=True, color="#2563eb", ax=ax)
            ax.set_title(f"Distribution: {col}")
            safe_name = "".join(c if c.isalnum() else "_" for c in col)
            path = self.output_dir / f"distribution_{safe_name}.png"
            fig.tight_layout()
            fig.savefig(path, dpi=150)
            plt.close(fig)
            paths.append(path)
            logger.info("Saved distribution plot for '%s' to '%s'.", col, path)
        return paths
