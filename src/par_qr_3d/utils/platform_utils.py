"""Platform-specific utilities."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from ..logging_config import get_logger

logger = get_logger(__name__)


def open_file_in_default_app(file_path: Path | str) -> bool:
    """Open file in the system's default application.

    Args:
        file_path: Path to the file to open

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False

    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
        elif system == "Windows":
            subprocess.run(["start", "", str(file_path)], shell=True, check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(file_path)], check=True)

        logger.info(f"Opened {file_path.name} in default application")
        return True

    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not open {file_path.name} automatically: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return False
