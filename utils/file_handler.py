"""
File handler utility — manages uploads, downloads, and temp file cleanup.
"""
import os
import time
from pathlib import Path
from typing import Optional

from utils.logger import log


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "uploads") -> str:
    """
    Save uploaded file content to the uploads directory.

    Args:
        file_content: Raw file bytes
        filename: Original filename
        upload_dir: Directory to save in

    Returns:
        Full path to the saved file
    """
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    log.info(f"File saved: {file_path} ({len(file_content)} bytes)")
    return file_path


def get_output_path(
    input_path: str,
    suffix: str = "",
    new_extension: Optional[str] = None,
    output_dir: str = "outputs",
) -> str:
    """
    Generate an output file path based on the input path.

    Args:
        input_path: Original file path
        suffix: Suffix to add to filename (e.g., '_modified')
        new_extension: New file extension (e.g., '.pdf')
        output_dir: Output directory

    Returns:
        Generated output file path
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    p = Path(input_path)
    extension = new_extension if new_extension else p.suffix
    new_name = f"{p.stem}{suffix}{extension}"
    return os.path.join(output_dir, new_name)


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Remove files older than max_age_hours from directory.

    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours

    Returns:
        Number of files deleted
    """
    deleted = 0
    cutoff = time.time() - (max_age_hours * 3600)

    for file_path in Path(directory).iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            file_path.unlink()
            deleted += 1

    if deleted > 0:
        log.info(f"Cleaned up {deleted} old files from {directory}")

    return deleted
