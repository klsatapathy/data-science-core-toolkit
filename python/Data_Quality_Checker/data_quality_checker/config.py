"""
config.py
=========
Centralized, configurable constants for the Data Quality Checker.

Keeping these values in one place makes the application easy to tune
without touching business logic elsewhere in the codebase.
"""

from __future__ import annotations

import re
from pathlib import Path

# --------------------------------------------------------------------------
# Project paths
# --------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR: Path = PROJECT_ROOT / "reports"
DEFAULT_LOG_DIR: Path = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE: Path = DEFAULT_LOG_DIR / "data_quality_checker.log"

# --------------------------------------------------------------------------
# File handling
# --------------------------------------------------------------------------
ALLOWED_EXTENSIONS: tuple[str, ...] = (".csv", ".txt", ".tsv")
ENCODING_DETECTION_SAMPLE_SIZE: int = 1_048_576  # 1 MB sample for chardet
LARGE_FILE_THRESHOLD_BYTES: int = 50 * 1024 * 1024  # 50 MB -> use chunked reads
CSV_CHUNK_SIZE: int = 50_000  # rows per chunk when streaming large files
FALLBACK_ENCODINGS: tuple[str, ...] = ("utf-8", "utf-8-sig", "latin-1", "cp1252")

# --------------------------------------------------------------------------
# Validation regex patterns
# --------------------------------------------------------------------------
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Accepts formats such as: +1-555-123-4567, (555) 123-4567, 5551234567, 555.123.4567
PHONE_REGEX = re.compile(
    r"^\+?\d{0,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$"
)

SPECIAL_CHAR_REGEX = re.compile(r"[^a-zA-Z0-9\s.,@\-_/():'\"]")

WHITESPACE_REGEX = re.compile(r"^\s+|\s+$")

# Candidate date formats used when trying to auto-detect date columns
CANDIDATE_DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)

# Column-name hints used to decide which validators to apply
EMAIL_COLUMN_HINTS: tuple[str, ...] = ("email", "e-mail", "mail")
PHONE_COLUMN_HINTS: tuple[str, ...] = ("phone", "mobile", "contact", "tel")
DATE_COLUMN_HINTS: tuple[str, ...] = ("date", "dob", "created", "updated", "timestamp")

# --------------------------------------------------------------------------
# Data cleaning defaults
# --------------------------------------------------------------------------
FILL_STRATEGIES: tuple[str, ...] = ("mean", "median", "mode", "constant", "ffill", "bfill", "drop")
DEFAULT_FILL_STRATEGY: str = "mode"
DEFAULT_TEXT_CASE: str = "title"  # one of: lower, upper, title, none

# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
SUPPORTED_REPORT_FORMATS: tuple[str, ...] = ("console", "csv", "json", "html")
TOP_N_FREQUENT_VALUES: int = 5
REPORT_FILENAME_STEM: str = "data_quality_report"

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
