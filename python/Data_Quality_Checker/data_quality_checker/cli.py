"""
cli.py
======
Command-line interface for the Data Quality Checker & CSV Validator.

Example usage
-------------
    python main.py --input data/sample.csv --output-dir reports/ \
        --formats console csv json html --visualize

    python main.py -i data.csv --clean --remove-duplicates --trim-whitespace \
        --fill-strategy median --export-cleaned cleaned.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .cleaner import DataCleaner
from .exceptions import DataQualityCheckerError
from .loader import CSVLoader
from .logger import get_logger, setup_logging
from .profiler import DataProfiler
from .report_generator import ReportGenerator
from .validators import DataValidator
from .visualizer import Visualizer


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-quality-checker",
        description="Analyze, validate, clean, and report on CSV data quality.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-i", "--input", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "-o", "--output-dir", default=str(config.DEFAULT_OUTPUT_DIR),
        help="Directory where reports (and optional charts) will be written.",
    )
    parser.add_argument(
        "-f", "--formats", nargs="+", choices=config.SUPPORTED_REPORT_FORMATS,
        default=["console"], help="One or more report formats to generate.",
    )
    parser.add_argument(
        "-v", "--verbosity", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity level.",
    )
    parser.add_argument(
        "--visualize", action="store_true",
        help="Generate PNG charts (missing-value heatmap, null % bar chart, etc.).",
    )

    cleaning = parser.add_argument_group("cleaning options")
    cleaning.add_argument("--clean", action="store_true", help="Enable the data-cleaning pipeline.")
    cleaning.add_argument("--remove-duplicates", action="store_true", help="Drop fully duplicated rows.")
    cleaning.add_argument("--trim-whitespace", action="store_true", help="Trim leading/trailing whitespace on text columns.")
    cleaning.add_argument(
        "--standardize-case", choices=["lower", "upper", "title", "none"], default=None,
        help="Standardize text casing on text columns.",
    )
    cleaning.add_argument(
        "--fill-strategy", choices=config.FILL_STRATEGIES, default=None,
        help="Strategy used to fill missing values.",
    )
    cleaning.add_argument(
        "--fill-constant", default=None,
        help="Constant value to use when --fill-strategy=constant.",
    )
    cleaning.add_argument(
        "--export-cleaned", default=None,
        help="File path to export the cleaned dataset to (requires --clean).",
    )

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    setup_logging(verbosity=args.verbosity)
    logger = get_logger("cli")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load ---------------------------------------------------------
        loader = CSVLoader(args.input)
        df, load_metadata = loader.load()

        # 2. Validate -------------------------------------------------------
        validator = DataValidator(df)
        validation_report = validator.run_all()

        # 3. Profile ----------------------------------------------------
        profiler = DataProfiler(df)
        profile = profiler.profile()

        # 4. Clean (optional) --------------------------------------------
        cleaning_log: list[str] = []
        if args.clean:
            cleaner = DataCleaner(df)
            if args.remove_duplicates:
                cleaner.remove_duplicate_rows()
            if args.trim_whitespace:
                cleaner.trim_whitespace()
            if args.standardize_case and args.standardize_case != "none":
                cleaner.standardize_text_case(case=args.standardize_case)
            if args.fill_strategy:
                cleaner.fill_missing_values(
                    strategy=args.fill_strategy, constant_value=args.fill_constant
                )
            cleaning_log = cleaner.get_cleaning_log()

            export_path = args.export_cleaned or (output_dir / "cleaned_dataset.csv")
            cleaner.export(export_path)
            logger.info("Cleaned dataset available at: %s", export_path)

        # 5. Report -------------------------------------------------------
        reporter = ReportGenerator(
            validation_report=validation_report,
            profile=profile,
            source_file=args.input,
            cleaning_log=cleaning_log,
        )

        for fmt in args.formats:
            if fmt == "console":
                reporter.to_console()
            elif fmt == "csv":
                reporter.to_csv(output_dir / f"{config.REPORT_FILENAME_STEM}.csv")
            elif fmt == "json":
                reporter.to_json(output_dir / f"{config.REPORT_FILENAME_STEM}.json")
            elif fmt == "html":
                reporter.to_html(output_dir / f"{config.REPORT_FILENAME_STEM}.html")

        # 6. Visualize (optional) -----------------------------------------
        if args.visualize:
            charts_dir = output_dir / "charts"
            visualizer = Visualizer(df, validation_report, charts_dir)
            chart_paths = visualizer.generate_all()
            logger.info("Generated %s chart(s) in '%s'.", len(chart_paths), charts_dir)

        logger.info("Data quality check completed successfully.")
        return 0

    except DataQualityCheckerError as exc:
        logger.error("Application error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - safety net for unexpected errors
        logger.exception("Unexpected error occurred: %s", exc)
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
