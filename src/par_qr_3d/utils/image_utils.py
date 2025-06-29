"""Image processing utilities."""

from __future__ import annotations

from PIL import Image

from ..logging_config import get_logger

logger = get_logger(__name__)


def ensure_grayscale(image: Image.Image) -> Image.Image:
    """Ensure image is in grayscale mode.

    Args:
        image: PIL Image object

    Returns:
        Image in grayscale mode ('L')
    """
    if image.mode == "L":
        return image
    logger.debug(f"Converting image from {image.mode} to grayscale")
    return image.convert("L")


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is in RGB mode.

    Args:
        image: PIL Image object

    Returns:
        Image in RGB mode
    """
    if image.mode == "RGB":
        return image
    logger.debug(f"Converting image from {image.mode} to RGB")
    return image.convert("RGB")


def ensure_mode(image: Image.Image, mode: str) -> Image.Image:
    """Ensure image is in the specified mode.

    Args:
        image: PIL Image object
        mode: Target image mode ('L', 'RGB', 'RGBA', etc.)

    Returns:
        Image in the specified mode
    """
    if image.mode == mode:
        return image
    logger.debug(f"Converting image from {image.mode} to {mode}")
    return image.convert(mode)
