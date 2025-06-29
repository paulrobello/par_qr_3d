"""Font loading and handling utilities."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from PIL import ImageFont

from ..logging_config import get_logger

logger = get_logger(__name__)

# Emoji-capable font paths (prioritized when emoji detected)
EMOJI_FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoEmoji-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Good Unicode coverage
    "/usr/share/fonts/truetype/unifont/unifont.ttf",
    "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
    # Windows
    "C:\\Windows\\Fonts\\Segoe UI Emoji.ttf",
    "C:\\Windows\\Fonts\\seguiemj.ttf",
    "C:\\Windows\\Fonts\\Arial Unicode MS.ttf",
]

# Default font paths for different platforms
DEFAULT_FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Avenir.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    # Windows
    "C:\\Windows\\Fonts\\Arial.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
    "C:\\Windows\\Fonts\\tahoma.ttf",
]

# Bold font paths for labels
BOLD_FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/truetype/roboto/Roboto-Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\Arial Bold.ttf",
]


def is_valid_font_file(font_path: str | Path) -> bool:
    """Check if a file is a valid font file.

    Args:
        font_path: Path to the font file

    Returns:
        True if the file exists and is a valid font
    """
    try:
        path = Path(font_path)
        if not path.exists():
            return False

        # Try to load the font to verify it's valid
        ImageFont.truetype(str(path), 12)  # Small size for quick test
        return True
    except Exception as e:
        logger.debug(f"Font validation failed for {font_path}: {e}")
        return False


def contains_emoji(text: str) -> bool:
    """Check if text contains emoji characters.

    Args:
        text: Text to check for emoji

    Returns:
        True if text contains emoji characters
    """
    for char in text:
        # Check Unicode categories that typically contain emoji
        category = unicodedata.category(char)
        if category in ("So", "Sk"):  # Symbol, Other; Symbol, Modifier
            return True
        # Check specific emoji code point ranges
        code_point = ord(char)
        if (
            # Emoticons
            (0x1F600 <= code_point <= 0x1F64F)
            or
            # Miscellaneous Symbols and Pictographs
            (0x1F300 <= code_point <= 0x1F5FF)
            or
            # Transport and Map Symbols
            (0x1F680 <= code_point <= 0x1F6FF)
            or
            # Supplemental Symbols and Pictographs
            (0x1F900 <= code_point <= 0x1F9FF)
            or
            # Symbols and Pictographs Extended-A
            (0x1FA70 <= code_point <= 0x1FAFF)
            or
            # Other common emoji ranges
            (0x2600 <= code_point <= 0x26FF)
            or (0x2700 <= code_point <= 0x27BF)
        ):
            return True
    return False


def load_font_with_fallbacks(
    font_size: int,
    font_name: str | None = None,
    fallback_paths: list[str] | None = None,
    use_bold: bool = False,
    text: str | None = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font with fallback options.

    Args:
        font_size: Font size in pixels
        font_name: Specific font name/path to try first
        fallback_paths: List of fallback font paths
        use_bold: Whether to prefer bold fonts
        text: Text to be rendered (used to detect emoji)

    Returns:
        Loaded font object, or default font if all else fails
    """
    # Get bundled fonts directory
    fonts_dir = Path(__file__).parent.parent / "fonts"

    # Build list of paths to try
    paths_to_try = []

    # First priority: bundled fonts
    if text and contains_emoji(text):
        # For emoji, prioritize bundled emoji fonts
        bundled_emoji = fonts_dir / "NotoEmoji-Regular.ttf"
        bundled_unicode = fonts_dir / "DejaVuSans.ttf"
        if is_valid_font_file(bundled_emoji):
            paths_to_try.append(str(bundled_emoji))
            logger.debug(f"Using bundled Noto Emoji font for text: '{text}'")
        if is_valid_font_file(bundled_unicode):
            paths_to_try.append(str(bundled_unicode))
            logger.debug("Added bundled DejaVu Sans as fallback")
    elif use_bold:
        # For bold text, use Roboto Black
        bundled_bold = fonts_dir / "Roboto-Black.ttf"
        if is_valid_font_file(bundled_bold):
            paths_to_try.append(str(bundled_bold))
            logger.debug("Using bundled Roboto Black font")
    else:
        # For regular text, use DejaVu Sans
        bundled_regular = fonts_dir / "DejaVuSans.ttf"
        if is_valid_font_file(bundled_regular):
            paths_to_try.append(str(bundled_regular))
            logger.debug("Using bundled DejaVu Sans font")

    # Second priority: user-specified font
    if font_name:
        paths_to_try.append(font_name)

    # Third priority: system fonts
    if fallback_paths is None:
        if text and contains_emoji(text):
            fallback_paths = EMOJI_FONT_PATHS + DEFAULT_FONT_PATHS
        elif use_bold:
            fallback_paths = BOLD_FONT_PATHS
        else:
            fallback_paths = DEFAULT_FONT_PATHS

    paths_to_try.extend(fallback_paths)

    # Try each font path
    for font_path in paths_to_try:
        try:
            # Convert to Path object for consistency
            path = Path(font_path)
            if path.exists() or not path.is_absolute():
                # Try to load the font
                font = ImageFont.truetype(str(font_path), font_size)
                logger.debug(f"Loaded font from: {font_path}")
                return font
        except Exception as e:
            logger.debug(f"Could not load font from {font_path}: {e}")
            continue

    # Fall back to default font
    logger.warning("Using default font - some characters may not render properly")
    try:
        return ImageFont.load_default()
    except Exception as e:
        logger.error(f"Could not load default font: {e}")
        raise RuntimeError("No fonts available") from e
