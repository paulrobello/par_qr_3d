"""Color handling utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import ImageColor

from ..logging_config import get_logger

if TYPE_CHECKING:
    import lib3mf

logger = get_logger(__name__)


def parse_color(color_str: str, default_color: str = "black") -> tuple[int, int, int]:
    """Parse a color string into RGB tuple.

    Args:
        color_str: Color name or hex code
        default_color: Fallback color if parsing fails

    Returns:
        RGB tuple with values 0-255
    """
    try:
        rgb = ImageColor.getrgb(color_str)
        # Handle potential RGBA input
        if len(rgb) == 4:
            return (rgb[0], rgb[1], rgb[2])  # Return just RGB, ignore alpha
        return (rgb[0], rgb[1], rgb[2])  # Ensure it's a 3-tuple
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid color '{color_str}': {e}, using '{default_color}'")
        try:
            default_rgb = ImageColor.getrgb(default_color)
            if len(default_rgb) == 4:
                return (default_rgb[0], default_rgb[1], default_rgb[2])
            return (default_rgb[0], default_rgb[1], default_rgb[2])
        except (ValueError, AttributeError):
            # If even default fails, return black
            logger.error(f"Default color '{default_color}' also invalid, using black")
            return (0, 0, 0)


def normalize_rgb(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Normalize RGB values from 0-255 to 0.0-1.0 range.

    Args:
        rgb: RGB tuple with values 0-255

    Returns:
        RGB tuple with values 0.0-1.0
    """
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def color_to_3mf_format(rgb: tuple[int, int, int], wrapper: lib3mf.Wrapper) -> any:  # type: ignore[valid-type]
    """Convert RGB tuple to 3MF color format.

    Args:
        rgb: RGB tuple with values 0-255
        wrapper: lib3mf wrapper instance

    Returns:
        Color ID suitable for 3MF format
    """
    # 3MF uses RGBA with alpha=255 for opaque colors
    return wrapper.FloatRGBAToColor(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 1.0)
