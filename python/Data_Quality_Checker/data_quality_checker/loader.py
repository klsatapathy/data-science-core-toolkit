"""
loader.py
=========
Robust CSV ingestion.

Responsibilities
-----------------
* Validate that the input file exists and has a supported extension.
* Auto-detect file encoding using `charset-normalizer` / `chardet`
  with a safe fallback chain.
* Efficiently load large files via chunked reads.
* Surface corrupted / malformed files as clear, typed exceptions
  instead of letting raw pandas tracebacks leak to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import pandas as pd

from . import config
from .exceptions import (
    CorruptedFileError,
    EmptyFileError,
    EncodingDetectionError,
    FileNotFoundInProjectError,
    UnsupportedFileFormatError,
)
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class LoadMetadata:
    """Metadata captured while loading a CSV file."""

    file_path: Path
    detected_encoding: str
    file_size_bytes: int
    is_large_file: bool
    delimiter: str = ","
    chunked: bool = False
    row_count: int = 0
    column_count: int = 0
    warnings: list[str] = field(default_factory=list)


class CSVLoader:
    """Loads CSV files into pandas DataFrames with strong safety guarantees."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.metadata: LoadMetadata | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load(self) -> tuple[pd.DataFrame, LoadMetadata]:
        """Validate, detect encoding, and load the file into a DataFrame.

        Returns:
            A tuple of (DataFrame, LoadMetadata).

        Raises:
            FileNotFoundInProjectError: If the path does not exist.
            UnsupportedFileFormatError: If the extension is not allowed.
            EmptyFileError: If the file has no rows/columns.
            CorruptedFileError: If the file cannot be parsed as CSV.
            EncodingDetectionError: If no encoding could decode the file.
        """
        self._validate_file_exists()
        self._validate_extension()

        file_size = self.file_path.stat().st_size
        is_large = file_size > config.LARGE_FILE_THRESHOLD_BYTES
        encoding = self._detect_encoding()
        delimiter = self._sniff_delimiter(encoding)

        logger.info(
            "Loading '%s' (%.2f MB, encoding=%s, delimiter=%r, large_file=%s)",
            self.file_path.name,
            file_size / (1024 * 1024),
            encoding,
            delimiter,
            is_large,
        )

        metadata = LoadMetadata(
            file_path=self.file_path,
            detected_encoding=encoding,
            file_size_bytes=file_size,
            is_large_file=is_large,
            delimiter=delimiter,
            chunked=is_large,
        )

        try:
            if is_large:
                df = self._load_in_chunks(encoding, delimiter)
            else:
                df = pd.read_csv(
                    self.file_path,
                    encoding=encoding,
                    sep=delimiter,
                    engine="python",
                    on_bad_lines="warn",
                )
        except UnicodeDecodeError as exc:
            raise EncodingDetectionError(
                f"Could not decode '{self.file_path}' using encoding '{encoding}'."
            ) from exc
        except pd.errors.EmptyDataError as exc:
            raise EmptyFileError(f"File '{self.file_path}' contains no data.") from exc
        except pd.errors.ParserError as exc:
            raise CorruptedFileError(
                f"File '{self.file_path}' could not be parsed as valid CSV: {exc}"
            ) from exc

        if df.empty or df.shape[1] == 0:
            raise EmptyFileError(f"File '{self.file_path}' loaded but has no usable data.")

        metadata.row_count, metadata.column_count = df.shape
        self.metadata = metadata

        logger.info(
            "Successfully loaded %s rows x %s columns.",
            metadata.row_count,
            metadata.column_count,
        )
        return df, metadata

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_file_exists(self) -> None:
        if not self.file_path.exists():
            raise FileNotFoundInProjectError(f"File not found: '{self.file_path}'")
        if not self.file_path.is_file():
            raise FileNotFoundInProjectError(f"Path is not a file: '{self.file_path}'")

    def _validate_extension(self) -> None:
        if self.file_path.suffix.lower() not in config.ALLOWED_EXTENSIONS:
            raise UnsupportedFileFormatError(
                f"Unsupported file extension '{self.file_path.suffix}'. "
                f"Allowed: {config.ALLOWED_EXTENSIONS}"
            )

    def _detect_encoding(self) -> str:
        """Detect file encoding using charset-normalizer, with fallbacks."""
        try:
            from charset_normalizer import from_path

            result = from_path(str(self.file_path)).best()
            if result is not None and result.encoding:
                logger.debug("charset-normalizer detected encoding: %s", result.encoding)
                return result.encoding
        except ImportError:
            logger.debug("charset-normalizer not installed; falling back to chardet.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("charset-normalizer failed: %s", exc)

        try:
            import chardet

            with open(self.file_path, "rb") as fh:
                raw = fh.read(config.ENCODING_DETECTION_SAMPLE_SIZE)
            result = chardet.detect(raw)
            encoding = result.get("encoding")
            if encoding:
                logger.debug("chardet detected encoding: %s", encoding)
                return encoding
        except ImportError:
            logger.debug("chardet not installed; using fallback encoding chain.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("chardet failed: %s", exc)

        # Last resort: try each fallback encoding until one decodes cleanly.
        for enc in config.FALLBACK_ENCODINGS:
            try:
                with open(self.file_path, encoding=enc) as fh:
                    fh.read(4096)
                logger.debug("Fallback encoding succeeded: %s", enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

        raise EncodingDetectionError(
            f"Unable to detect a usable encoding for '{self.file_path}'."
        )

    def _sniff_delimiter(self, encoding: str) -> str:
        """Guess the field delimiter using csv.Sniffer, defaulting to comma."""
        import csv

        try:
            with open(self.file_path, encoding=encoding, errors="replace") as fh:
                sample = fh.read(8192)
            if not sample.strip():
                raise EmptyFileError(f"File '{self.file_path}' appears to be empty.")
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            return dialect.delimiter
        except csv.Error:
            logger.debug("Delimiter sniffing failed; defaulting to comma.")
            return ","

    def _load_in_chunks(self, encoding: str, delimiter: str) -> pd.DataFrame:
        """Stream a large file in chunks and concatenate, to bound memory use."""
        chunks: Iterator[pd.DataFrame] = pd.read_csv(
            self.file_path,
            encoding=encoding,
            sep=delimiter,
            engine="python",
            on_bad_lines="warn",
            chunksize=config.CSV_CHUNK_SIZE,
        )
        pieces = []
        total_rows = 0
        for i, chunk in enumerate(chunks, start=1):
            pieces.append(chunk)
            total_rows += len(chunk)
            logger.debug("Loaded chunk %s (%s rows so far).", i, total_rows)
        return pd.concat(pieces, ignore_index=True)
