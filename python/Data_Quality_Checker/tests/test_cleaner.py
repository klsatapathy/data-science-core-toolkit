"""
tests/test_cleaner.py
======================
Unit tests for the DataCleaner class.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_quality_checker.cleaner import DataCleaner
from data_quality_checker.exceptions import InvalidCleaningStrategyError


@pytest.fixture
def messy_df() -> pd.DataFrame:
    return pd.DataFrame({
        "name": ["  Alice", "bob ", "Alice", None],
        "score": [10, None, 10, 30],
    })


def test_remove_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1, 2]})
    cleaner = DataCleaner(df).remove_duplicate_rows()
    assert len(cleaner.get_cleaned_data()) == 2


def test_trim_whitespace(messy_df: pd.DataFrame):
    cleaner = DataCleaner(messy_df).trim_whitespace()
    cleaned = cleaner.get_cleaned_data()
    assert cleaned["name"].iloc[0] == "Alice"
    assert cleaned["name"].iloc[1] == "bob"


def test_standardize_text_case(messy_df: pd.DataFrame):
    cleaner = DataCleaner(messy_df).trim_whitespace().standardize_text_case(case="upper")
    cleaned = cleaner.get_cleaned_data()
    assert cleaned["name"].iloc[1] == "BOB"


def test_invalid_case_raises(messy_df: pd.DataFrame):
    with pytest.raises(InvalidCleaningStrategyError):
        DataCleaner(messy_df).standardize_text_case(case="not_a_case")


def test_fill_missing_values_mode(messy_df: pd.DataFrame):
    cleaner = DataCleaner(messy_df).fill_missing_values(strategy="mode")
    cleaned = cleaner.get_cleaned_data()
    assert cleaned["score"].isna().sum() == 0


def test_fill_missing_values_drop(messy_df: pd.DataFrame):
    cleaner = DataCleaner(messy_df).fill_missing_values(strategy="drop")
    cleaned = cleaner.get_cleaned_data()
    assert cleaned.isna().sum().sum() == 0


def test_cleaning_log_records_operations(messy_df: pd.DataFrame):
    cleaner = DataCleaner(messy_df).remove_duplicate_rows().trim_whitespace()
    log = cleaner.get_cleaning_log()
    assert len(log) == 2
    assert "duplicate" in log[0].lower()
