"""
Input validation utilities for the AI Agent.
"""
import os
from pathlib import Path
from typing import Optional

from utils.logger import log

# Maximum file size in MB (read from env, default 50)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

SUPPORTED_DOCUMENT_TYPES = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_TEXT_TYPES = {".txt", ".md", ".csv", ".html", ".htm"}
SUPPORTED_PDF_INPUT_TYPES = (
    SUPPORTED_DOCUMENT_TYPES | SUPPORTED_IMAGE_TYPES | SUPPORTED_TEXT_TYPES | {".pdf"}
)


def validate_file_exists(file_path: str) -> bool:
    """Check that a file exists and is a regular file."""
    exists = Path(file_path).is_file()
    if not exists:
        log.warning(f"File does not exist: {file_path}")
    return exists


def validate_file_size(file_path: str, max_mb: Optional[int] = None) -> bool:
    """
    Validate that a file does not exceed the maximum size.

    Args:
        file_path: Path to the file
        max_mb: Max allowed size in MB. Defaults to MAX_FILE_SIZE_MB env var.

    Returns:
        True if file size is within limit
    """
    limit = max_mb or MAX_FILE_SIZE_MB
    size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    if size_mb > limit:
        log.warning(f"File too large: {size_mb:.1f} MB (limit {limit} MB)")
        return False
    return True


def validate_file_extension(file_path: str, allowed: set) -> bool:
    """
    Check that the file has an allowed extension.

    Args:
        file_path: Path to the file
        allowed: Set of allowed extensions (lowercase with leading dot)

    Returns:
        True if the extension is in allowed
    """
    ext = Path(file_path).suffix.lower()
    valid = ext in allowed
    if not valid:
        log.warning(f"Unsupported file extension '{ext}'. Allowed: {allowed}")
    return valid


def validate_non_empty_string(value: str, field_name: str = "value") -> bool:
    """Return True if value is a non-empty, non-whitespace string."""
    if not isinstance(value, str) or not value.strip():
        log.warning(f"'{field_name}' must be a non-empty string.")
        return False
    return True
