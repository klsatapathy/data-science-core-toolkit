"""
report_generator.py
====================
Turns a `ValidationReport` + `DatasetProfile` into human- and
machine-readable output: a rich console summary, and CSV / JSON / HTML
files written to disk.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate

from . import config
from .exceptions import ReportGenerationError
from .logger import get_logger
from .profiler import DatasetProfile
from .validators import ValidationReport

logger = get_logger(__name__)

try:
    from rich.console import Console
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _RICH_AVAILABLE = False


class ReportGenerator:
    """Generates data-quality reports in multiple formats."""

    def __init__(
        self,
        validation_report: ValidationReport,
        profile: DatasetProfile,
        source_file: str | Path,
        cleaning_log: list[str] | None = None,
    ) -> None:
        self.validation_report = validation_report
        self.profile = profile
        self.source_file = str(source_file)
        self.cleaning_log = cleaning_log or []
        self.generated_at = datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------
    def to_console(self) -> None:
        """Print a formatted summary to the terminal."""
        if _RICH_AVAILABLE:
            self._console_rich()
        else:
            self._console_plain()

    def _console_rich(self) -> None:  # pragma: no cover - visual only
        console = Console()
        console.rule("[bold cyan]Data Quality Report")
        console.print(f"[bold]Source file:[/bold] {self.source_file}")
        console.print(f"[bold]Generated at:[/bold] {self.generated_at}\n")

        overview = Table(title="Dataset Overview")
        overview.add_column("Metric")
        overview.add_column("Value")
        overview.add_row("Total rows", str(self.profile.total_rows))
        overview.add_row("Total columns", str(self.profile.total_columns))
        overview.add_row("Memory usage", self.profile.memory_usage_human)
        overview.add_row("Duplicate rows", str(self.validation_report.duplicate_row_count))
        overview.add_row(
            "Duplicate row %", f"{self.validation_report.duplicate_row_percentage:.2f}%"
        )
        overview.add_row("Empty columns", ", ".join(self.validation_report.empty_columns) or "None")
        console.print(overview)

        col_table = Table(title="Column Quality Summary")
        for header in ("Column", "Dtype", "Null %", "Unique", "Whitespace", "Special Chars", "Neg.", "Bad Email", "Bad Phone", "Bad Date"):
            col_table.add_column(header)

        for name, res in self.validation_report.columns.items():
            col_table.add_row(
                name,
                res.dtype,
                f"{res.null_percentage:.1f}%",
                str(res.unique_count),
                str(res.whitespace_row_count),
                str(res.special_character_row_count),
                str(res.negative_value_count) if res.negative_value_count is not None else "-",
                str(res.invalid_email_count) if res.invalid_email_count is not None else "-",
                str(res.invalid_phone_count) if res.invalid_phone_count is not None else "-",
                str(res.invalid_date_count) if res.invalid_date_count is not None else "-",
            )
        console.print(col_table)

        if self.cleaning_log:
            console.rule("[bold green]Cleaning Operations")
            for entry in self.cleaning_log:
                console.print(f"  • {entry}")

    def _console_plain(self) -> None:
        print("=" * 78)
        print("DATA QUALITY REPORT")
        print("=" * 78)
        print(f"Source file : {self.source_file}")
        print(f"Generated at: {self.generated_at}\n")

        print(f"Total rows        : {self.profile.total_rows}")
        print(f"Total columns     : {self.profile.total_columns}")
        print(f"Memory usage      : {self.profile.memory_usage_human}")
        print(f"Duplicate rows    : {self.validation_report.duplicate_row_count} "
              f"({self.validation_report.duplicate_row_percentage:.2f}%)")
        print(f"Empty columns     : {', '.join(self.validation_report.empty_columns) or 'None'}")
        dup_cols = self.validation_report.duplicate_column_pairs
        print(f"Duplicate columns : {dup_cols if dup_cols else 'None'}\n")

        rows = []
        for name, res in self.validation_report.columns.items():
            rows.append([
                name,
                res.dtype,
                f"{res.null_percentage:.1f}%",
                res.unique_count,
                res.whitespace_row_count,
                res.special_character_row_count,
                res.negative_value_count if res.negative_value_count is not None else "-",
                res.invalid_email_count if res.invalid_email_count is not None else "-",
                res.invalid_phone_count if res.invalid_phone_count is not None else "-",
                res.invalid_date_count if res.invalid_date_count is not None else "-",
            ])
        headers = ["Column", "Dtype", "Null %", "Unique", "Whitespace", "Special", "Neg.", "Bad Email", "Bad Phone", "Bad Date"]
        print(tabulate(rows, headers=headers, tablefmt="grid"))

        if self.cleaning_log:
            print("\nCLEANING OPERATIONS PERFORMED")
            print("-" * 78)
            for entry in self.cleaning_log:
                print(f"  - {entry}")
        print("=" * 78)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    def to_json(self, output_path: str | Path) -> Path:
        output_path = self._resolve_path(output_path, "json")
        payload: dict[str, Any] = {
            "source_file": self.source_file,
            "generated_at": self.generated_at,
            "profile": self.profile.to_dict(),
            "validation": self.validation_report.to_dict(),
            "cleaning_log": self.cleaning_log,
        }
        try:
            output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        except OSError as exc:
            raise ReportGenerationError(f"Failed to write JSON report: {exc}") from exc
        logger.info("JSON report written to '%s'.", output_path)
        return output_path

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------
    def to_csv(self, output_path: str | Path) -> Path:
        output_path = self._resolve_path(output_path, "csv")
        rows = []
        for name, res in self.validation_report.columns.items():
            rows.append({
                "column": name,
                "dtype": res.dtype,
                "null_count": res.null_count,
                "null_percentage": round(res.null_percentage, 2),
                "unique_count": res.unique_count,
                "duplicate_value_count": res.duplicate_value_count,
                "is_empty": res.is_empty,
                "whitespace_row_count": res.whitespace_row_count,
                "special_character_row_count": res.special_character_row_count,
                "negative_value_count": res.negative_value_count,
                "invalid_email_count": res.invalid_email_count,
                "invalid_phone_count": res.invalid_phone_count,
                "invalid_date_count": res.invalid_date_count,
                "suspected_type_mismatch_count": res.suspected_type_mismatch_count,
            })
        try:
            pd.DataFrame(rows).to_csv(output_path, index=False)
        except OSError as exc:
            raise ReportGenerationError(f"Failed to write CSV report: {exc}") from exc
        logger.info("CSV report written to '%s'.", output_path)
        return output_path

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------
    def to_html(self, output_path: str | Path) -> Path:
        output_path = self._resolve_path(output_path, "html")

        col_rows = "".join(
            f"<tr>"
            f"<td>{name}</td><td>{res.dtype}</td>"
            f"<td>{res.null_percentage:.1f}%</td><td>{res.unique_count}</td>"
            f"<td>{res.duplicate_value_count}</td>"
            f"<td>{res.whitespace_row_count}</td><td>{res.special_character_row_count}</td>"
            f"<td>{self._dash(res.negative_value_count)}</td>"
            f"<td>{self._dash(res.invalid_email_count)}</td>"
            f"<td>{self._dash(res.invalid_phone_count)}</td>"
            f"<td>{self._dash(res.invalid_date_count)}</td>"
            f"</tr>"
            for name, res in self.validation_report.columns.items()
        )

        cleaning_items = "".join(f"<li>{entry}</li>" for entry in self.cleaning_log)
        cleaning_section = (
            f"<h2>Cleaning Operations</h2><ul>{cleaning_items}</ul>" if self.cleaning_log else ""
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 40px; color: #1f2937; background:#f9fafb; }}
  h1 {{ color: #111827; }}
  h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; background: #fff; }}
  th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; font-size: 14px; }}
  th {{ background-color: #111827; color: #fff; }}
  tr:nth-child(even) {{ background-color: #f3f4f6; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px; }}
  .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }}
  .card .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
  .card .value {{ font-size: 22px; font-weight: 700; color: #111827; }}
  footer {{ margin-top: 40px; font-size: 12px; color: #9ca3af; }}
</style>
</head>
<body>
  <h1>Data Quality Report</h1>
  <p><strong>Source file:</strong> {self.source_file}<br>
     <strong>Generated at:</strong> {self.generated_at}</p>

  <div class="summary-grid">
    <div class="card"><div class="label">Total Rows</div><div class="value">{self.profile.total_rows}</div></div>
    <div class="card"><div class="label">Total Columns</div><div class="value">{self.profile.total_columns}</div></div>
    <div class="card"><div class="label">Memory Usage</div><div class="value">{self.profile.memory_usage_human}</div></div>
    <div class="card"><div class="label">Duplicate Rows</div><div class="value">{self.validation_report.duplicate_row_count} ({self.validation_report.duplicate_row_percentage:.1f}%)</div></div>
  </div>

  <h2>Column Quality Summary</h2>
  <table>
    <tr>
      <th>Column</th><th>Dtype</th><th>Null %</th><th>Unique</th><th>Dup. Values</th>
      <th>Whitespace</th><th>Special Chars</th><th>Negative</th>
      <th>Bad Email</th><th>Bad Phone</th><th>Bad Date</th>
    </tr>
    {col_rows}
  </table>

  {cleaning_section}

  <footer>Generated by Data Quality Checker &amp; CSV Validator v1.0.0</footer>
</body>
</html>
"""
        try:
            output_path.write_text(html, encoding="utf-8")
        except OSError as exc:
            raise ReportGenerationError(f"Failed to write HTML report: {exc}") from exc
        logger.info("HTML report written to '%s'.", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _dash(value: Any) -> str:
        return "-" if value is None else str(value)

    @staticmethod
    def _resolve_path(output_path: str | Path, extension: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() != f".{extension}":
            path = path.with_suffix(f".{extension}")
        return path
