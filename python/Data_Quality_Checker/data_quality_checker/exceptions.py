"""
exceptions.py
=============
Custom exception hierarchy for the Data Quality Checker.

Using dedicated exception types (instead of bare Exception / ValueError)
makes error handling in the CLI and calling code precise and predictable.
"""


class DataQualityCheckerError(Exception):
    """Base class for all application-specific exceptions."""


class FileNotFoundInProjectError(DataQualityCheckerError):
    """Raised when the requested input file does not exist on disk."""


class UnsupportedFileFormatError(DataQualityCheckerError):
    """Raised when a file's extension is not supported by the loader."""


class EmptyFileError(DataQualityCheckerError):
    """Raised when a file exists but contains no usable data."""


class CorruptedFileError(DataQualityCheckerError):
    """Raised when a file cannot be parsed as valid CSV data."""


class EncodingDetectionError(DataQualityCheckerError):
    """Raised when the file's encoding cannot be determined or decoded."""


class InvalidCleaningStrategyError(DataQualityCheckerError):
    """Raised when a cleaning operation receives an unsupported strategy."""


class ReportGenerationError(DataQualityCheckerError):
    """Raised when a report fails to be generated or written to disk."""
