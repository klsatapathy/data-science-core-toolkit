"""
tests/test_loader.py
=====================
Unit tests for the CSVLoader class.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_quality_checker.exceptions import (
    EmptyFileError,
    FileNotFoundInProjectError,
    UnsupportedFileFormatError,
)
from data_quality_checker.loader import CSVLoader


def test_missing_file_raises(tmp_path: Path):
    loader = CSVLoader(tmp_path / "does_not_exist.csv")
    with pytest.raises(FileNotFoundInProjectError):
        loader.load()


def test_unsupported_extension_raises(tmp_path: Path):
    bad_file = tmp_path / "data.xyz"
    bad_file.write_text("a,b\n1,2\n")
    loader = CSVLoader(bad_file)
    with pytest.raises(UnsupportedFileFormatError):
        loader.load()


def test_empty_file_raises(tmp_path: Path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    loader = CSVLoader(empty_file)
    with pytest.raises(EmptyFileError):
        loader.load()


def test_valid_csv_loads_successfully(tmp_path: Path):
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text("id,name\n1,Alice\n2,Bob\n")
    loader = CSVLoader(csv_file)
    df, metadata = loader.load()
    assert df.shape == (2, 2)
    assert metadata.row_count == 2
    assert metadata.column_count == 2


def test_delimiter_detection_semicolon(tmp_path: Path):
    csv_file = tmp_path / "semi.csv"
    csv_file.write_text("id;name\n1;Alice\n2;Bob\n")
    loader = CSVLoader(csv_file)
    df, metadata = loader.load()
    assert list(df.columns) == ["id", "name"]
    assert metadata.delimiter == ";"
