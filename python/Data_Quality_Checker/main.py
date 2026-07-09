#!/usr/bin/env python3
"""
main.py
=======
Entry point for the Data Quality Checker & CSV Validator CLI.

    python main.py --input sample_data/sample.csv --formats console html json csv --visualize
"""

from data_quality_checker.cli import main

if __name__ == "__main__":
    main()
