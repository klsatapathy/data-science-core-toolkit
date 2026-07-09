"""
tests/test_validators.py
=========================
Unit tests for the DataValidator class.

Run with:  python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_quality_checker.validators import DataValidator


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "email": ["a@example.com", "bad-email", "  c@example.com  ", None],
        "phone": ["+1-555-123-4567", "123", "555-987-6543", None],
        "signup_date": ["2023-01-01", "not-a-date", "2023-03-15", "2023-04-01"],
        "age": [25, -5, 40, None],
        "name": ["Alice", "Alice", "Bob", "  Carol  "],
    })


def test_duplicate_rows_detected():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    validator = DataValidator(df)
    assert validator.check_duplicate_rows() == 1


def test_duplicate_columns_detected():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [4, 5, 6]})
    validator = DataValidator(df)
    pairs = validator.check_duplicate_columns()
    assert ("a", "b") in pairs
    assert ("a", "c") not in pairs


def test_empty_columns_detected():
    df = pd.DataFrame({"a": [1, 2], "b": [None, None]})
    validator = DataValidator(df)
    assert validator.check_empty_columns() == ["b"]


def test_null_percentage(sample_df: pd.DataFrame):
    report = DataValidator(sample_df).run_all()
    assert report.columns["email"].null_count == 1
    assert report.columns["email"].null_percentage == 25.0


def test_invalid_email_detection(sample_df: pd.DataFrame):
    report = DataValidator(sample_df).run_all()
    # "bad-email" is invalid; the rest (after strip) are valid.
    assert report.columns["email"].invalid_email_count == 1


def test_invalid_phone_detection(sample_df: pd.DataFrame):
    report = DataValidator(sample_df).run_all()
    assert report.columns["phone"].invalid_phone_count == 1


def test_negative_value_detection(sample_df: pd.DataFrame):
    report = DataValidator(sample_df).run_all()
    assert report.columns["age"].negative_value_count == 1


def test_whitespace_detection(sample_df: pd.DataFrame):
    report = DataValidator(sample_df).run_all()
    assert report.columns["name"].whitespace_row_count == 1
