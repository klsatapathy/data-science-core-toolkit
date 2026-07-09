"""
logger.py
=========
Application-wide logging configuration.

Provides a single `get_logger` factory so every module logs consistently
to both the console and a rotating log file.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config

_CONFIGURED = False


def setup_logging(log_file: Path | None = None, verbosity: str = "INFO") -> None:
    """Configure the root application logger.

    Args:
        log_file: Path to the log file. Defaults to config.DEFAULT_LOG_FILE.
        verbosity: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_file = log_file or config.DEFAULT_LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, verbosity.upper(), logging.INFO)

    root_logger = logging.getLogger("data_quality_checker")
    root_logger.setLevel(level)
    root_logger.propagate = False

    formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # keep full detail in the file

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the application's root logger."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(f"data_quality_checker.{name}")
