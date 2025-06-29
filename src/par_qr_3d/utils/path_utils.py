"""File path handling utilities."""

from __future__ import annotations

from pathlib import Path

from ..logging_config import get_logger

logger = get_logger(__name__)


def ensure_file_extension(path: Path | str, extension: str) -> Path:
    """Ensure file has the specified extension.

    Args:
        path: File path
        extension: Desired extension (with or without leading dot)

    Returns:
        Path with correct extension
    """
    path = Path(path)
    # Ensure extension starts with a dot
    if not extension.startswith("."):
        extension = f".{extension}"

    # Check if current extension matches (case-insensitive)
    if path.suffix.lower() != extension.lower():
        path = path.with_suffix(extension)
        logger.debug(f"Changed file extension to {extension}")

    return path


def prepare_output_path(path: Path | str, extension: str) -> Path:
    """Prepare output path with proper extension and parent directories.

    Args:
        path: Output file path
        extension: Desired file extension

    Returns:
        Prepared Path object with extension and existing parent directories
    """
    # Ensure proper extension
    output_path = ensure_file_extension(path, extension)

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Prepared output path: {output_path}")

    return output_path
